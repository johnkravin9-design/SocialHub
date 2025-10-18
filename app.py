from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from database.models import Database, User, Post, Poke, Notification, Invite
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production-2024')
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize database
db = Database()

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def get_current_user():
    if 'user_id' in session:
        return User.get_by_id(session['user_id'])
    return None

def time_ago(timestamp):
    """Convert timestamp to relative time"""
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp.replace('Z', ''))
        except:
            return timestamp
    
    now = datetime.now()
    diff = now - timestamp
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "Just now"
    elif seconds < 3600:
        mins = int(seconds / 60)
        return f"{mins}m"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours}h"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days}d"
    else:
        return timestamp.strftime('%b %d')

app.jinja_env.filters['time_ago'] = time_ago

# Routes
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    invite_code = request.args.get('invite')
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        full_name = request.form['full_name']
        invite = request.form.get('invite_code')
        
        user_id = User.create(username, email, password, full_name, invite)
        
        if user_id:
            flash('🎉 Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('❌ Username or email already exists!', 'error')
    
    return render_template('register.html', invite_code=invite_code)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.verify_password(username, password)
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(f'👋 Welcome back, {user["full_name"]}!', 'success')
            return redirect(url_for('home'))
        else:
            flash('❌ Invalid credentials!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('👋 Logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = get_current_user()
    posts = Post.get_feed(session['user_id'])
    notifications_count = Notification.get_unread_count(session['user_id'])
    pokes = Poke.get_recent_pokes(session['user_id'], limit=5)
    
    return render_template('home.html', 
                         user=user, 
                         posts=posts, 
                         notifications_count=notifications_count,
                         pokes=pokes)

@app.route('/profile/<username>')
def profile(username):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    current_user = get_current_user()
    profile_user = User.get_by_username(username)
    
    if not profile_user:
        flash('❌ User not found!', 'error')
        return redirect(url_for('home'))
    
    wall_posts = Post.get_wall_posts(profile_user['id'])
    poke_count = profile_user.get('poke_count', 0)
    
    return render_template('profile.html', 
                         user=current_user, 
                         profile_user=profile_user,
                         wall_posts=wall_posts,
                         poke_count=poke_count)

@app.route('/profile/<username>/edit', methods=['GET', 'POST'])
def edit_profile(username):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = get_current_user()
    
    if user['username'] != username:
        flash('❌ You can only edit your own profile!', 'error')
        return redirect(url_for('profile', username=username))
    
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        bio = request.form.get('bio', '')
        
        profile_pic = user['profile_pic']
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"profile_{session['user_id']}_{int(datetime.now().timestamp())}_{file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'profiles', filename)
                file.save(filepath)
                profile_pic = filename
        
        User.update(session['user_id'], full_name=full_name, bio=bio, profile_pic=profile_pic)
        
        flash('✅ Profile updated successfully!', 'success')
        return redirect(url_for('profile', username=username))
    
    return render_template('edit_profile.html', user=user)

# POST ROUTES
@app.route('/post/create', methods=['POST'])
def create_post():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    content = request.form.get('content')
    wall_owner_id = request.form.get('wall_owner_id')
    tagged_users = request.form.get('tagged_users')
    
    image = None
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{session['user_id']}_{datetime.now().timestamp()}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'posts', filename)
            file.save(filepath)
            image = f"posts/{filename}"
    
    post_id = Post.create(session['user_id'], content, image, wall_owner_id, tagged_users)
    
    # Emit real-time notification via WebSocket
    if wall_owner_id:
        socketio.emit('new_notification', {
            'type': 'wall_post',
            'message': f'{get_current_user()["full_name"]} posted on your wall'
        }, room=f'user_{wall_owner_id}')
    
    return jsonify({'success': True, 'post_id': post_id})

@app.route('/post/<int:post_id>/like', methods=['POST'])
def like_post(post_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    result = Post.toggle_like(post_id, session['user_id'])
    return jsonify(result)

@app.route('/post/<int:post_id>/comment', methods=['POST'])
def comment_post(post_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    content = request.json.get('content')
    comment_id = Post.add_comment(post_id, session['user_id'], content)
    
    return jsonify({'success': True, 'comment_id': comment_id})

@app.route('/post/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    comments = Post.get_comments(post_id)
    return jsonify(comments)

# POKE ROUTES - Zuckerberg's feature!
@app.route('/poke/<int:user_id>', methods=['POST'])
def poke_user(user_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    success = Poke.send_poke(session['user_id'], user_id)
    
    if success:
        # Send real-time notification
        current_user = get_current_user()
        socketio.emit('new_poke', {
            'from_user': current_user['full_name'],
            'from_username': current_user['username'],
            'from_pic': current_user['profile_pic']
        }, room=f'user_{user_id}')
        
        return jsonify({'success': True, 'message': '👋 Poke sent!'})
    else:
        return jsonify({'success': False, 'message': 'Already poked recently'})

@app.route('/pokes')
def view_pokes():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = get_current_user()
    pokes = Poke.get_recent_pokes(session['user_id'], limit=20)
    
    return render_template('pokes.html', user=user, pokes=pokes)

# NOTIFICATION ROUTES
@app.route('/notifications')
def notifications():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = get_current_user()
    notifications = Notification.get_recent(session['user_id'])
    
    return render_template('notifications.html', user=user, notifications=notifications)

@app.route('/notifications/mark-read/<int:notif_id>', methods=['POST'])
def mark_notification_read(notif_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    Notification.mark_read(notif_id)
    return jsonify({'success': True})

@app.route('/notifications/mark-all-read', methods=['POST'])
def mark_all_notifications_read():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    Notification.mark_all_read(session['user_id'])
    return jsonify({'success': True})

@app.route('/api/notifications/count')
def notifications_count():
    if 'user_id' not in session:
        return jsonify({'count': 0})
    
    count = Notification.get_unread_count(session['user_id'])
    return jsonify({'count': count})

# INVITE ROUTES - Viral growth!
@app.route('/invite', methods=['GET', 'POST'])
def invite_friends():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = get_current_user()
    
    if request.method == 'POST':
        email = request.form.get('email')
        invite_code = Invite.create(session['user_id'], email)
        
        if invite_code:
            invite_url = url_for('register', invite=invite_code, _external=True)
            flash(f'✅ Invite created! Share this link: {invite_url}', 'success')
        else:
            flash('❌ Error creating invite', 'error')
    
    invites = Invite.get_user_invites(session['user_id'])
    successful_invites = Invite.count_successful(session['user_id'])
    
    return render_template('invite.html', 
                         user=user, 
                         invites=invites,
                         successful_invites=successful_invites,
                         invite_code=user['invite_code'])

# SEARCH ROUTE
@app.route('/search')
def search():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    query = request.args.get('q', '')
    results = []
    
    if query:
        results = User.search(query)
    
    user = get_current_user()
    return render_template('search.html', user=user, results=results, query=query)

# MESSAGES ROUTE (from before)
@app.route('/messages')
def messages():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = get_current_user()
    return render_template('messages.html', user=user)

@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    db = Database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, username, full_name, profile_pic
        FROM users
        WHERE id != ?
        ORDER BY username
    ''', (session['user_id'],))
    
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(users)

@app.route('/api/messages/<int:friend_id>', methods=['GET'])
def get_messages_api(friend_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    db = Database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT m.*, u.username, u.full_name, u.profile_pic
        FROM messages m
        JOIN users u ON m.sender_id = u.id
        WHERE (m.sender_id = ? AND m.receiver_id = ?) 
           OR (m.sender_id = ? AND m.receiver_id = ?)
        ORDER BY m.created_at ASC
        LIMIT 100
    ''', (session['user_id'], friend_id, friend_id, session['user_id']))
    
    messages = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(messages)

# WEBSOCKET EVENTS
@socketio.on('connect')
def handle_connect():
    if 'user_id' in session:
        join_room(f'user_{session["user_id"]}')
        print(f'✅ User {session["user_id"]} connected')

@socketio.on('disconnect')
def handle_disconnect():
    if 'user_id' in session:
        leave_room(f'user_{session["user_id"]}')
        print(f'👋 User {session["user_id"]} disconnected')

@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)

@socketio.on('send_message')
def handle_message(data):
    if 'user_id' not in session:
        return
    
    receiver_id = data['receiver_id']
    message = data['message']
    
    db = Database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO messages (sender_id, receiver_id, content)
        VALUES (?, ?, ?)
    ''', (session['user_id'], receiver_id, message))
    conn.commit()
    message_id = cursor.lastrowid
    
    cursor.execute('SELECT username, full_name, profile_pic FROM users WHERE id = ?', 
                   (session['user_id'],))
    sender = dict(cursor.fetchone())
    conn.close()
    
    room = f"chat_{min(session['user_id'], receiver_id)}_{max(session['user_id'], receiver_id)}"
    
    emit('receive_message', {
        'id': message_id,
        'sender_id': session['user_id'],
        'receiver_id': receiver_id,
        'content': message,
        'username': sender['username'],
        'full_name': sender['full_name'],
        'profile_pic': sender['profile_pic'],
        'timestamp': datetime.now().strftime('%H:%M'),
        'created_at': datetime.now().isoformat()
    }, room=room, include_self=True)

@socketio.on('typing')
def handle_typing(data):
    receiver_id = data['receiver_id']
    room = f"chat_{min(session['user_id'], receiver_id)}_{max(session['user_id'], receiver_id)}"
    
    emit('user_typing', {
        'user_id': session['user_id'],
        'username': session.get('username')
    }, room=room, include_self=False)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    print("🚀 Starting SocialHub V2 - The Zuckerberg Edition")
    print(f"📱 Running on port {port}")
    print("✨ Features: Wall, Pokes, Photo Tags, Viral Invites, Real-time Notifications")
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)

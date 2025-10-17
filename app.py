from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_socketio import SocketIO, emit, join_room
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from database.models import Database, User, Post
# from database.models import Message  # Uncomment if you add a Message model

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize database
db = Database()

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

def get_current_user():
    if 'user_id' in session:
        return User.get_by_id(session['user_id'])
    return None
def time_ago(timestamp):
    """Convert timestamp to relative time (e.g., '2 hours ago')"""
    from datetime import datetime, timedelta
    
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    
    now = datetime.now()
    diff = now - timestamp
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "Just now"
    elif seconds < 3600:
        mins = int(seconds / 60)
        return f"{mins} minute{'s' if mins != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        weeks = int(seconds / 604800)
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"

# Make function available in templates
app.jinja_env.filters['time_ago'] = time_ago
# Routes
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        full_name = request.form['full_name']
        
        user_id = User.create(username, email, password, full_name)
        
        if user_id:
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username or email already exists!', 'error')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.verify_password(username, password)
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = get_current_user()
    posts = Post.get_feed(session['user_id'])
    
    return render_template('home.html', user=user, posts=posts)

@app.route('/messages')
def messages():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = get_current_user()
    # messages = Message.get_for_user(session['user_id'])  # Add this if you implement Message model
    messages = []  # Placeholder: empty list until DB query is added
    
    return render_template('messages.html', user=user, messages=messages)

@app.route('/profile/<username>')
def profile(username):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    profile_user = User.get_by_username(username)
    if not profile_user:
        flash('User not found', 'error')
        return redirect(url_for('home'))

    # Stats
    posts_count = Post.count_by_user(profile_user['id'])

    # Recent photos come from that user's posts that have images
    db_local = Database()
    conn = db_local.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT image FROM posts WHERE user_id = ? AND image IS NOT NULL ORDER BY created_at DESC LIMIT 9', (profile_user['id'],))
    photos = [row['image'] for row in cursor.fetchall()]
    conn.close()

    # Current user for navbar
    current_user = get_current_user()

    return render_template('profile.html', user=current_user, profile_user=profile_user, posts_count=posts_count, photos=photos)


@app.route('/profile/<username>/edit', methods=['GET', 'POST'])
def edit_profile(username):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = get_current_user()
    
    # Check if user is editing their own profile
    if user['username'] != username:
        flash('You can only edit your own profile!', 'error')
        return redirect(url_for('profile', username=username))
    
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        bio = request.form.get('bio')
        
        # Ensure upload directories exist
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'profiles'), exist_ok=True)

        # Handle profile picture upload
        profile_pic = user['profile_pic']
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"profile_{session['user_id']}_{int(datetime.now().timestamp())}_{file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'profiles', filename)
                file.save(filepath)
                profile_pic = filename
        
        # Update database
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users 
            SET full_name = ?, bio = ?, profile_pic = ?
            WHERE id = ?
        ''', (full_name, bio, profile_pic, session['user_id']))
        conn.commit()
        conn.close()
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile', username=username))
    
    return render_template('edit_profile.html', user=user)

@app.route('/post/create', methods=['POST'])
def create_post():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    content = request.form.get('content')
    image = None
    
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{session['user_id']}_{datetime.now().timestamp()}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'posts', filename)
            file.save(filepath)
            image = f"posts/{filename}"
    
    post_id = Post.create(session['user_id'], content, image)
    
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

# WebSocket for real-time messaging
@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    emit('status', {'msg': f"User {session.get('username')} joined"}, room=room)

@socketio.on('send_message')
def handle_message(data):
    room = data['room']
    message = data['message']
    username = session.get('username')
    
    emit('receive_message', {
        'username': username,
        'message': message,
        'timestamp': datetime.now().strftime('%H:%M')
    }, room=room)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    print("🚀 Starting SocialHub...")
    print(f"📱 Running on port {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)

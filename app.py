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
    
    current_user = get_current_user()
    profile_user = User.get_by_username(username)
    
    if not profile_user:
        flash('User not found!', 'error')
        return redirect(url_for('home'))
    
    return render_template('profile.html', user=current_user, profile_user=profile_user)

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

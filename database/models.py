from datetime import datetime
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

class Database:
    def __init__(self, db_path='database/socialhub.db'):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                bio TEXT,
                profile_pic TEXT DEFAULT 'default.jpg',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Posts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                image TEXT,
                likes_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Comments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES posts(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Likes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(post_id, user_id),
                FOREIGN KEY (post_id) REFERENCES posts(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Friendships table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS friendships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                friend_id INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (friend_id) REFERENCES users(id)
            )
        ''')
        
        # Messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                read BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES users(id),
                FOREIGN KEY (receiver_id) REFERENCES users(id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully!")

# User operations
class User:
    @staticmethod
    def create(username, email, password, full_name):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        password_hash = generate_password_hash(password)
        
        try:
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, full_name)
                VALUES (?, ?, ?, ?)
            ''', (username, email, password_hash, full_name))
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return user_id
        except sqlite3.IntegrityError:
            conn.close()
            return None
    
    @staticmethod
    def get_by_username(username):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None
    
    @staticmethod
    def get_by_id(user_id):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None
    
    @staticmethod
    def verify_password(username, password):
        user = User.get_by_username(username)
        if user and check_password_hash(user['password_hash'], password):
            return user
        return None
    
    @staticmethod
    def get_user_stats(user_id):
        """Get real statistics for a user"""
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get posts count
        cursor.execute('SELECT COUNT(*) as count FROM posts WHERE user_id = ?', (user_id,))
        posts_count = cursor.fetchone()['count']
        
        # Get friends count (accepted friendships)
        cursor.execute('''
            SELECT COUNT(*) as count FROM friendships 
            WHERE (user_id = ? OR friend_id = ?) AND status = 'accepted'
        ''', (user_id, user_id))
        friends_count = cursor.fetchone()['count']
        
        conn.close()
        
        return {
            'posts_count': posts_count,
            'friends_count': friends_count
        }

# Post operations
class Post:
    @staticmethod
    def create(user_id, content, image=None):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO posts (user_id, content, image)
            VALUES (?, ?, ?)
        ''', (user_id, content, image))
        conn.commit()
        post_id = cursor.lastrowid
        conn.close()
        return post_id
    
    @staticmethod
    def get_feed(user_id, limit=50):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.*, u.username, u.full_name, u.profile_pic,
                   (SELECT COUNT(*) FROM likes WHERE post_id = p.id) as likes_count,
                   (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comments_count,
                   EXISTS(SELECT 1 FROM likes WHERE post_id = p.id AND user_id = ?) as user_liked
            FROM posts p
            JOIN users u ON p.user_id = u.id
            ORDER BY p.created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        posts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return posts
    
    @staticmethod
    def toggle_like(post_id, user_id):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Check if already liked
        cursor.execute('SELECT id FROM likes WHERE post_id = ? AND user_id = ?', (post_id, user_id))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute('DELETE FROM likes WHERE post_id = ? AND user_id = ?', (post_id, user_id))
            action = 'unliked'
        else:
            cursor.execute('INSERT INTO likes (post_id, user_id) VALUES (?, ?)', (post_id, user_id))
            action = 'liked'
        
        conn.commit()
        
        # Get new count
        cursor.execute('SELECT COUNT(*) as count FROM likes WHERE post_id = ?', (post_id,))
        count = cursor.fetchone()['count']
        conn.close()
        
        return {'action': action, 'count': count}
    
    @staticmethod
    def add_comment(post_id, user_id, content):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO comments (post_id, user_id, content)
            VALUES (?, ?, ?)
        ''', (post_id, user_id, content))
        conn.commit()
        comment_id = cursor.lastrowid
        conn.close()
        return comment_id
    
    @staticmethod
    def get_comments(post_id):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.*, u.username, u.full_name, u.profile_pic
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.post_id = ?
            ORDER BY c.created_at ASC
        ''', (post_id,))
        
        comments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return comments
    
    @staticmethod
    def get_user_posts(user_id, limit=50):
        """Get all posts by a specific user"""
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.*, u.username, u.full_name, u.profile_pic,
                   (SELECT COUNT(*) FROM likes WHERE post_id = p.id) as likes_count,
                   (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comments_count
            FROM posts p
            JOIN users u ON p.user_id = u.id
            WHERE p.user_id = ?
            ORDER BY p.created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        posts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return posts

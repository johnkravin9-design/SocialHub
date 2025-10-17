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
        
        # Admin users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT DEFAULT 'admin',
                permissions TEXT DEFAULT 'all',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Support tickets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS support_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT DEFAULT 'open',
                priority TEXT DEFAULT 'medium',
                assigned_to INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (assigned_to) REFERENCES admin_users(id)
            )
        ''')
        
        # Support messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS support_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                sender_id INTEGER NOT NULL,
                sender_type TEXT NOT NULL, -- 'user' or 'admin'
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticket_id) REFERENCES support_tickets(id)
            )
        ''')
        
        # Stories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                content TEXT,
                image TEXT,
                video TEXT,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Video calls table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                caller_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                started_at TIMESTAMP,
                ended_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (caller_id) REFERENCES users(id),
                FOREIGN KEY (receiver_id) REFERENCES users(id)
            )
        ''')
        
        # Notifications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                read BOOLEAN DEFAULT 0,
                data TEXT, -- JSON data for additional info
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Analytics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    def count_by_user(user_id):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM posts WHERE user_id = ?', (user_id,))
        count = cursor.fetchone()['count']
        conn.close()
        return count
    
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
    def get_by_user(user_id, limit=50):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.*, u.username, u.full_name, u.profile_pic,
                   (SELECT COUNT(*) FROM likes WHERE post_id = p.id) as likes_count,
                   (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comments_count,
                   EXISTS(SELECT 1 FROM likes WHERE post_id = p.id AND user_id = u.id) as user_liked
            FROM posts p
            JOIN users u ON p.user_id = u.id
            WHERE p.user_id = ?
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

# Admin operations
class AdminUser:
    @staticmethod
    def create(username, email, password, full_name, role='admin', permissions='all'):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        password_hash = generate_password_hash(password)
        
        try:
            cursor.execute('''
                INSERT INTO admin_users (username, email, password_hash, full_name, role, permissions)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, email, password_hash, full_name, role, permissions))
            conn.commit()
            admin_id = cursor.lastrowid
            conn.close()
            return admin_id
        except sqlite3.IntegrityError:
            conn.close()
            return None
    
    @staticmethod
    def verify_password(username, password):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM admin_users WHERE username = ?', (username,))
        admin = cursor.fetchone()
        conn.close()
        
        if admin and check_password_hash(admin['password_hash'], password):
            return dict(admin)
        return None
    
    @staticmethod
    def get_by_id(admin_id):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM admin_users WHERE id = ?', (admin_id,))
        admin = cursor.fetchone()
        conn.close()
        return dict(admin) if admin else None

# Support ticket operations
class SupportTicket:
    @staticmethod
    def create(user_id, subject, description, priority='medium'):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO support_tickets (user_id, subject, description, priority)
            VALUES (?, ?, ?, ?)
        ''', (user_id, subject, description, priority))
        conn.commit()
        ticket_id = cursor.lastrowid
        conn.close()
        return ticket_id
    
    @staticmethod
    def get_by_user(user_id):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT st.*, u.username, u.full_name
            FROM support_tickets st
            JOIN users u ON st.user_id = u.id
            WHERE st.user_id = ?
            ORDER BY st.created_at DESC
        ''', (user_id,))
        
        tickets = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return tickets
    
    @staticmethod
    def get_all():
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT st.*, u.username, u.full_name, au.username as assigned_admin
            FROM support_tickets st
            JOIN users u ON st.user_id = u.id
            LEFT JOIN admin_users au ON st.assigned_to = au.id
            ORDER BY st.created_at DESC
        ''')
        
        tickets = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return tickets
    
    @staticmethod
    def update_status(ticket_id, status, assigned_to=None):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE support_tickets 
            SET status = ?, assigned_to = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, assigned_to, ticket_id))
        conn.commit()
        conn.close()
        return True

# Support message operations
class SupportMessage:
    @staticmethod
    def create(ticket_id, sender_id, sender_type, content):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO support_messages (ticket_id, sender_id, sender_type, content)
            VALUES (?, ?, ?, ?)
        ''', (ticket_id, sender_id, sender_type, content))
        conn.commit()
        message_id = cursor.lastrowid
        conn.close()
        return message_id
    
    @staticmethod
    def get_by_ticket(ticket_id):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT sm.*, u.username, u.full_name, au.username as admin_username
            FROM support_messages sm
            LEFT JOIN users u ON sm.sender_id = u.id AND sm.sender_type = 'user'
            LEFT JOIN admin_users au ON sm.sender_id = au.id AND sm.sender_type = 'admin'
            WHERE sm.ticket_id = ?
            ORDER BY sm.created_at ASC
        ''', (ticket_id,))
        
        messages = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return messages

# Story operations
class Story:
    @staticmethod
    def create(user_id, content=None, image=None, video=None, expires_hours=24):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        from datetime import datetime, timedelta
        expires_at = datetime.now() + timedelta(hours=expires_hours)
        
        cursor.execute('''
            INSERT INTO stories (user_id, content, image, video, expires_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, content, image, video, expires_at))
        conn.commit()
        story_id = cursor.lastrowid
        conn.close()
        return story_id
    
    @staticmethod
    def get_active_stories():
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT s.*, u.username, u.full_name, u.profile_pic
            FROM stories s
            JOIN users u ON s.user_id = u.id
            WHERE s.expires_at > datetime('now')
            ORDER BY s.created_at DESC
        ''')
        
        stories = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return stories

# Notification operations
class Notification:
    @staticmethod
    def create(user_id, type, title, message, data=None):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        import json
        data_json = json.dumps(data) if data else None
        
        cursor.execute('''
            INSERT INTO notifications (user_id, type, title, message, data)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, type, title, message, data_json))
        conn.commit()
        notification_id = cursor.lastrowid
        conn.close()
        return notification_id
    
    @staticmethod
    def get_by_user(user_id, limit=50):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM notifications
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        notifications = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return notifications
    
    @staticmethod
    def mark_as_read(notification_id):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE notifications SET read = 1 WHERE id = ?
        ''', (notification_id,))
        conn.commit()
        conn.close()
        return True

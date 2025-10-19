from datetime import datetime
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

class Database:
    def __init__(self, db_path='database/socialhub.db'):
        os.makedirs('database', exist_ok=True)
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                bio TEXT,
                profile_pic TEXT DEFAULT 'https://ui-avatars.com/api/?name=User&size=200',
                cover_photo TEXT DEFAULT 'default_cover.jpg',
                poke_count INTEGER DEFAULT 0,
                invite_code TEXT UNIQUE,
                invited_by INTEGER,
                premium BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (invited_by) REFERENCES users(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                wall_owner_id INTEGER,
                content TEXT NOT NULL,
                image TEXT,
                tagged_users TEXT,
                privacy TEXT DEFAULT 'public',
                likes_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (wall_owner_id) REFERENCES users(id)
            )
        ''')
        
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
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pokes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                poker_id INTEGER NOT NULL,
                poked_id INTEGER NOT NULL,
                read BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (poker_id) REFERENCES users(id),
                FOREIGN KEY (poked_id) REFERENCES users(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS photo_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                x_position REAL,
                y_position REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES posts(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                related_id INTEGER,
                from_user_id INTEGER,
                read BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (from_user_id) REFERENCES users(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inviter_id INTEGER NOT NULL,
                invitee_email TEXT NOT NULL,
                invite_code TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'pending',
                bonus_unlocked BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (inviter_id) REFERENCES users(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                activity_type TEXT NOT NULL,
                activity_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        conn.commit()
        conn.close()

class User:
    @staticmethod
    def create(username, email, password, full_name, invite_code=None):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        password_hash = generate_password_hash(password)
        import secrets
        user_invite_code = secrets.token_urlsafe(8)
        invited_by = None
        if invite_code:
            cursor.execute('SELECT inviter_id FROM invites WHERE invite_code = ? AND status = "pending"', (invite_code,))
            invite = cursor.fetchone()
            if invite:
                invited_by = invite['inviter_id']
        try:
            cursor.execute('INSERT INTO users (username, email, password_hash, full_name, invite_code, invited_by) VALUES (?, ?, ?, ?, ?, ?)', (username, email, password_hash, full_name, user_invite_code, invited_by))
            conn.commit()
            user_id = cursor.lastrowid
            if invite_code and invited_by:
                cursor.execute('UPDATE invites SET status = "accepted", bonus_unlocked = 1 WHERE invite_code = ?', (invite_code,))
                cursor.execute('UPDATE users SET premium = 1 WHERE id = ?', (invited_by,))
                cursor.execute('INSERT INTO notifications (user_id, type, content, from_user_id) VALUES (?, ?, ?, ?)', (invited_by, 'invite_accepted', 'Someone joined using your invite!', user_id))
            cursor.execute('INSERT INTO notifications (user_id, type, content) VALUES (?, ?, ?)', (user_id, 'welcome', 'Welcome to SocialHub!'))
            conn.commit()
            conn.close()
            return user_id
        except:
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
    def search(query, limit=20):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, full_name, profile_pic, bio FROM users WHERE username LIKE ? OR full_name LIKE ? LIMIT ?', (f'%{query}%', f'%{query}%', limit))
        users = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return users
    
    @staticmethod
    def update(user_id, full_name=None, bio=None, profile_pic=None):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        updates = []
        values = []
        if full_name:
            updates.append('full_name = ?')
            values.append(full_name)
        if bio is not None:
            updates.append('bio = ?')
            values.append(bio)
        if profile_pic:
            updates.append('profile_pic = ?')
            values.append(profile_pic)
        if updates:
            values.append(user_id)
            cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", values)
            conn.commit()
        conn.close()

class Post:
    @staticmethod
    def create(user_id, content, image=None, wall_owner_id=None, tagged_users=None):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO posts (user_id, content, image, wall_owner_id, tagged_users) VALUES (?, ?, ?, ?, ?)', (user_id, content, image, wall_owner_id, tagged_users))
        conn.commit()
        post_id = cursor.lastrowid
        conn.close()
        return post_id
    
    @staticmethod
    def get_feed(user_id, limit=50):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''SELECT p.*, u.username, u.full_name, u.profile_pic, wo.username as wall_owner_username, wo.full_name as wall_owner_name,
            (SELECT COUNT(*) FROM likes WHERE post_id = p.id) as likes_count, (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comments_count,
            EXISTS(SELECT 1 FROM likes WHERE post_id = p.id AND user_id = ?) as user_liked FROM posts p JOIN users u ON p.user_id = u.id
            LEFT JOIN users wo ON p.wall_owner_id = wo.id ORDER BY p.created_at DESC LIMIT ?''', (user_id, limit))
        posts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return posts
    
    @staticmethod
    def get_wall_posts(wall_owner_id, limit=20):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''SELECT p.*, u.username, u.full_name, u.profile_pic, (SELECT COUNT(*) FROM likes WHERE post_id = p.id) as likes_count,
            (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comments_count FROM posts p JOIN users u ON p.user_id = u.id
            WHERE p.wall_owner_id = ? OR (p.user_id = ? AND p.wall_owner_id IS NULL) ORDER BY p.created_at DESC LIMIT ?''', (wall_owner_id, wall_owner_id, limit))
        posts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return posts
    
    @staticmethod
    def toggle_like(post_id, user_id):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM likes WHERE post_id = ? AND user_id = ?', (post_id, user_id))
        if cursor.fetchone():
            cursor.execute('DELETE FROM likes WHERE post_id = ? AND user_id = ?', (post_id, user_id))
            action = 'unliked'
        else:
            cursor.execute('INSERT INTO likes (post_id, user_id) VALUES (?, ?)', (post_id, user_id))
            action = 'liked'
        conn.commit()
        cursor.execute('SELECT COUNT(*) as count FROM likes WHERE post_id = ?', (post_id,))
        count = cursor.fetchone()['count']
        conn.close()
        return {'action': action, 'count': count}
    
    @staticmethod
    def add_comment(post_id, user_id, content):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO comments (post_id, user_id, content) VALUES (?, ?, ?)', (post_id, user_id, content))
        conn.commit()
        comment_id = cursor.lastrowid
        conn.close()
        return comment_id
    
    @staticmethod
    def get_comments(post_id):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT c.*, u.username, u.full_name, u.profile_pic FROM comments c JOIN users u ON c.user_id = u.id WHERE c.post_id = ? ORDER BY c.created_at ASC', (post_id,))
        comments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return comments

class Poke:
    @staticmethod
    def send_poke(poker_id, poked_id):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM pokes WHERE poker_id = ? AND poked_id = ? AND created_at > datetime('now', '-1 hour')", (poker_id, poked_id))
        if cursor.fetchone():
            conn.close()
            return False
        cursor.execute('INSERT INTO pokes (poker_id, poked_id) VALUES (?, ?)', (poker_id, poked_id))
        cursor.execute('UPDATE users SET poke_count = poke_count + 1 WHERE id = ?', (poked_id,))
        cursor.execute('INSERT INTO notifications (user_id, type, content, from_user_id) VALUES (?, ?, ?, ?)', (poked_id, 'poke', 'poked you!', poker_id))
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def get_recent_pokes(user_id, limit=10):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT p.*, u.username, u.full_name, u.profile_pic FROM pokes p JOIN users u ON p.poker_id = u.id WHERE p.poked_id = ? ORDER BY p.created_at DESC LIMIT ?', (user_id, limit))
        pokes = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return pokes

class Notification:
    @staticmethod
    def get_recent(user_id, limit=20):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT n.*, u.username, u.full_name, u.profile_pic FROM notifications n LEFT JOIN users u ON n.from_user_id = u.id WHERE n.user_id = ? ORDER BY n.created_at DESC LIMIT ?', (user_id, limit))
        notifications = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return notifications
    
    @staticmethod
    def get_unread_count(user_id):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM notifications WHERE user_id = ? AND read = 0', (user_id,))
        count = cursor.fetchone()['count']
        conn.close()
        return count
    
    @staticmethod
    def mark_read(notification_id):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE notifications SET read = 1 WHERE id = ?', (notification_id,))
        conn.commit()
        conn.close()
    
    @staticmethod
    def mark_all_read(user_id):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE notifications SET read = 1 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()

class Invite:
    @staticmethod
    def create(inviter_id, invitee_email):
        import secrets
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        invite_code = secrets.token_urlsafe(12)
        try:
            cursor.execute('INSERT INTO invites (inviter_id, invitee_email, invite_code) VALUES (?, ?, ?)', (inviter_id, invitee_email, invite_code))
            conn.commit()
            conn.close()
            return invite_code
        except:
            conn.close()
            return None
    
    @staticmethod
    def get_user_invites(user_id):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM invites WHERE inviter_id = ? ORDER BY created_at DESC', (user_id,))
        invites = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return invites
    
    @staticmethod
    def count_successful(user_id):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM invites WHERE inviter_id = ? AND status = "accepted"', (user_id,))
        count = cursor.fetchone()['count']
        conn.close()
        return count

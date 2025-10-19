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
        
        # Users table
        cursor.execute(''' CREATE TABLE IF NOT EXISTS users ( 
                id INTEGER PRIMARY KEY AUTOINCREMENT, username 
                TEXT UNIQUE NOT NULL, email TEXT UNIQUE NOT 
                NULL, password_hash TEXT NOT NULL, full_name 
                TEXT NOT NULL, bio TEXT, profile_pic TEXT 
                DEFAULT 
                'https://ui-avatars.com/api/?name=User&size=200', 
                cover_photo TEXT DEFAULT 'default_cover.jpg', 
                poke_count INTEGER DEFAULT 0, invite_code TEXT 
                UNIQUE, invited_by INTEGER, premium BOOLEAN 
                DEFAULT 0, created_at TIMESTAMP DEFAULT 
                CURRENT_TIMESTAMP, FOREIGN KEY (invited_by) 
                REFERENCES users(id)
            ) ''')
        
        # Posts table
        cursor.execute(''' CREATE TABLE IF NOT EXISTS posts ( 
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id 
                INTEGER NOT NULL, wall_owner_id INTEGER, 
                content TEXT NOT NULL, image TEXT, 
                tagged_users TEXT, privacy TEXT DEFAULT 
                'public', likes_count INTEGER DEFAULT 0, 
                created_at TIMESTAMP DEFAULT 
                CURRENT_TIMESTAMP, FOREIGN KEY (user_id) 
                REFERENCES users(id), FOREIGN KEY 
                (wall_owner_id) REFERENCES users(id)
            ) ''')
        
        # Comments table
        cursor.execute(''' CREATE TABLE IF NOT EXISTS comments 
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT, post_id 
                INTEGER NOT NULL, user_id INTEGER NOT NULL, 
                content TEXT NOT NULL, created_at TIMESTAMP 
                DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY 
                (post_id) REFERENCES posts(id), FOREIGN KEY 
                (user_id) REFERENCES users(id)
            ) ''')
        
        # Likes table
        cursor.execute(''' CREATE TABLE IF NOT EXISTS likes ( 
                id INTEGER PRIMARY KEY AUTOINCREMENT, post_id 
                INTEGER NOT NULL, user_id INTEGER NOT NULL, 
                created_at TIMESTAMP DEFAULT 
                CURRENT_TIMESTAMP, UNIQUE(post_id, user_id), 
                FOREIGN KEY (post_id) REFERENCES posts(id), 
                FOREIGN KEY (user_id) REFERENCES users(id)
            ) ''')
        
        # Friendships table
        cursor.execute(''' CREATE TABLE IF NOT EXISTS 
            friendships (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id 
                INTEGER NOT NULL, friend_id INTEGER NOT NULL, 
                status TEXT DEFAULT 'pending', created_at 
                TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN 
                KEY (user_id) REFERENCES users(id), FOREIGN 
                KEY (friend_id) REFERENCES users(id)
            ) ''')
        
        # Messages table
        cursor.execute(''' CREATE TABLE IF NOT EXISTS messages 
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                sender_id INTEGER NOT NULL, receiver_id 
                INTEGER NOT NULL, content TEXT NOT NULL, read 
                BOOLEAN DEFAULT 0, created_at TIMESTAMP 
                DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY 
                (sender_id) REFERENCES users(id), FOREIGN KEY 
                (receiver_id) REFERENCES users(id)
            ) ''')
        
        # Pokes table
        cursor.execute(''' CREATE TABLE IF NOT EXISTS pokes ( 
                id INTEGER PRIMARY KEY AUTOINCREMENT, poker_id 
                INTEGER NOT NULL, poked_id INTEGER NOT NULL, 
                read BOOLEAN DEFAULT 0, created_at TIMESTAMP 
                DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY 
                (poker_id) REFERENCES users(id), FOREIGN KEY 
                (poked_id) REFERENCES users(id)
            ) ''')
        
        # Photo tags table
        cursor.execute(''' CREATE TABLE IF NOT EXISTS 
            photo_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT, post_id 
                INTEGER NOT NULL, user_id INTEGER NOT NULL, 
                x_position REAL, y_position REAL, created_at 
                TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES posts(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            ) ''')
        
        # Notifications table
        cursor.execute(''' CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                related_id INTEGER,
                read BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            ) ''')
        
        conn.commit()
        conn.close()


class User:
    @staticmethod
    def create(db, username, email, password, full_name, invite_code=None, invited_by=None):
        conn = db.get_connection()
        cursor = conn.cursor()
        password_hash = generate_password_hash(password)
        
        try:
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, full_name, invite_code, invited_by)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, email, password_hash, full_name, invite_code, invited_by))
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return user_id
        except Exception as e:
            conn.close()
            raise e
    
    @staticmethod
    def get_by_id(db, user_id):
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return user
    
    @staticmethod
    def get_by_username(db, username):
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        return user
    
    @staticmethod
    def get_by_email(db, email):
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        return user
    
    @staticmethod
    def verify_password(password_hash, password):
        return check_password_hash(password_hash, password)


class Post:
    @staticmethod
    def create(db, user_id, content, wall_owner_id=None, image=None, privacy='public'):
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO posts (user_id, content, wall_owner_id, image, privacy)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, content, wall_owner_id, image, privacy))
        conn.commit()
        post_id = cursor.lastrowid
        conn.close()
        return post_id
    
    @staticmethod
    def get_by_id(db, post_id):
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM posts WHERE id = ?', (post_id,))
        post = cursor.fetchone()
        conn.close()
        return post


class Poke:
    @staticmethod
    def create(db, poker_id, poked_id):
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO pokes (poker_id, poked_id)
            VALUES (?, ?)
        ''', (poker_id, poked_id))
        conn.commit()
        poke_id = cursor.lastrowid
        
        # Update poke count
        cursor.execute('''
            UPDATE users SET poke_count = poke_count + 1
            WHERE id = ?
        ''', (poked_id,))
        conn.commit()
        conn.close()
        return poke_id


class Notification:
    @staticmethod
    def create(db, user_id, notification_type, content, related_id=None):
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO notifications (user_id, type, content, related_id)
            VALUES (?, ?, ?, ?)
        ''', (user_id, notification_type, content, related_id))
        conn.commit()
        notification_id = cursor.lastrowid
        conn.close()
        return notification_id
    
    @staticmethod
    def get_unread(db, user_id):
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM notifications 
            WHERE user_id = ? AND read = 0
            ORDER BY created_at DESC
        ''', (user_id,))
        notifications = cursor.fetchall()
        conn.close()
        return notifications


class Invite:
    @staticmethod
    def generate_code(username):
        import hashlib
        import time
        return hashlib.md5(f"{username}{time.time()}".encode()).hexdigest()[:8]
    
    @staticmethod
    def validate(db, invite_code):
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE invite_code = ?', (invite_code,))
        user = cursor.fetchone()
        conn.close()
        return user is not None

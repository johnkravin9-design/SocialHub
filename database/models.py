from datetime import datetime import sqlite3 import os from 
werkzeug.security import generate_password_hash, 
check_password_hash class Database:
    def __init__(self, db_path='database/socialhub.db'): 
        os.makedirs('database', exist_ok=True) self.db_path = 
        db_path self.init_db()
    
    def get_connection(self): conn = 
        sqlite3.connect(self.db_path) conn.row_factory = 
        sqlite3.Row return conn
    
    def init_db(self): conn = self.get_connection() cursor = 
        conn.cursor()
        
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
                FOREIGN KEY (post_id

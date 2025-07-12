from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

DB_NAME = 'swap_skills.db'

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # USERS table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            is_banned INTEGER DEFAULT 0,
            profile_pic TEXT
        )
    ''')
    
    # SKILLS table
    c.execute('''
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            skill_offered TEXT,
            skill_wanted TEXT,
            availability TEXT,
            is_public INTEGER DEFAULT 1,
            location TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # SWAP REQUESTS table
    c.execute('''
        CREATE TABLE IF NOT EXISTS swap_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER,
            receiver_id INTEGER,
            skill TEXT,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (sender_id) REFERENCES users(id),
            FOREIGN KEY (receiver_id) REFERENCES users(id)
        )
    ''')

    # FEEDBACK table
    c.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            swap_id INTEGER,
            rating INTEGER,
            comment TEXT,
            FOREIGN KEY (swap_id) REFERENCES swap_requests(id)
        )
    ''')

    conn.commit()
    conn.close()

def create_user(name, email, password):
    hashed = generate_password_hash(password)
    conn = get_connection()
    c = conn.cursor()
    c.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)', (name, email, hashed))
    conn.commit()
    conn.close()
    
def validate_user(email, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, name, email, password, role FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    conn.close()
    if user and check_password_hash(user[3], password):
        return user  # Tuple: (id, name, email, password, role)
    return None

def get_user_profile(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM skills WHERE user_id = ?', (user_id,))
    profile = c.fetchone()  # Expecting one profile per user
    conn.close()
    return profile

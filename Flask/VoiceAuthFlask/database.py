import sqlite3
import os

DB_NAME = 'users.db'

def init_db():
    """Initialize SQLite database."""
    try:
        # Ensure directory exists if DB is in a folder (optional)
        os.makedirs(os.path.dirname(DB_NAME), exist_ok=True) if os.path.dirname(DB_NAME) else None

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                voice_data BLOB,
                phrase_data BLOB,
                key_data BLOB
            )
        ''')
        conn.commit()
    except sqlite3.Error as e:
        print(f"[DB ERROR] Failed to initialize DB: {e}")
    finally:
        if conn:
            conn.close()

def save_user_data(email, voice_data, phrase_data, key_data):
    """Save or update user data in the database."""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''
            INSERT OR REPLACE INTO users (email, voice_data, phrase_data, key_data)
            VALUES (?, ?, ?, ?)
        ''', (email, voice_data, phrase_data, key_data))
        conn.commit()
    except sqlite3.Error as e:
        print(f"[DB ERROR] Failed to save data for {email}: {e}")
    finally:
        if conn:
            conn.close()

def get_user_data(email):
    """Retrieve user data by email."""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT voice_data, phrase_data, key_data FROM users WHERE email = ?', (email,))
        result = c.fetchone()
        return result  # May be None if user not found
    except sqlite3.Error as e:
        print(f"[DB ERROR] Failed to fetch data for {email}: {e}")
        return None
    finally:
        if conn:
            conn.close()

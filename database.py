# database.py
import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.check_reset_trigger_stats()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS forward_permissions (
                chat_id TEXT,
                user_id INTEGER,
                PRIMARY KEY (chat_id, user_id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS triggers (
                chat_id TEXT,
                trigger_word TEXT,
                response TEXT,
                PRIMARY KEY (chat_id, trigger_word)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS top_shops (
                chat_id TEXT,
                username TEXT,
                description TEXT,
                PRIMARY KEY (chat_id, username)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS bans (
                chat_id TEXT,
                user_id INTEGER,
                PRIMARY KEY (chat_id, user_id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS trigger_stats (
                trigger_word TEXT PRIMARY KEY,
                count INTEGER DEFAULT 0
            )
        """)
        self.conn.commit()

    def check_reset_trigger_stats(self):
        today = datetime.now()
        if today.day == 1:
            self.cursor.execute("DELETE FROM trigger_stats")
            self.conn.commit()
            print(f"📊 Статистика триггеров очищена {today.strftime('%Y-%m-%d')}")

    def add_forward_permission(self, chat_id, user_id):
        self.cursor.execute(
            "INSERT OR REPLACE INTO forward_permissions (chat_id, user_id) VALUES (?, ?)",
            (str(chat_id), user_id)
        )
        self.conn.commit()

    def check_forward_permission(self, chat_id, user_id):
        self.cursor.execute(
            "SELECT 1 FROM forward_permissions WHERE chat_id = ? AND user_id = ?",
            (str(chat_id), user_id)
        )
        return bool(self.cursor.fetchone())

    def remove_forward_permission(self, chat_id, user_id):
        self.cursor.execute(
            "DELETE FROM forward_permissions WHERE chat_id = ? AND user_id = ?",
            (str(chat_id), user_id)
        )
        self.conn.commit()

    def add_ban(self, chat_id, user_id):
        self.cursor.execute(
            "INSERT OR REPLACE INTO bans (chat_id, user_id) VALUES (?, ?)",
            (str(chat_id), user_id)
        )
        self.conn.commit()

    def remove_ban(self, chat_id, user_id):
        self.cursor.execute(
            "DELETE FROM bans WHERE chat_id = ? AND user_id = ?",
            (str(chat_id), user_id)
        )
        self.conn.commit()

    def add_trigger(self, chat_id, trigger_word, response):
        self.cursor.execute(
            "INSERT OR REPLACE INTO triggers (chat_id, trigger_word, response) VALUES (?, ?, ?)",
            (str(chat_id), trigger_word, response)
        )
        self.conn.commit()

    def delete_trigger(self, chat_id, trigger_word):
        self.cursor.execute(
            "DELETE FROM triggers WHERE chat_id = ? AND trigger_word = ?",
            (str(chat_id), trigger_word)
        )
        self.conn.commit()

    def get_triggers(self, chat_id):
        self.cursor.execute(
            "SELECT trigger_word, response FROM triggers WHERE chat_id = ?",
            (str(chat_id),)
        )
        return self.cursor.fetchall()

    def add_top_shop(self, chat_id, username, description):
        self.cursor.execute(
            "INSERT OR REPLACE INTO top_shops (chat_id, username, description) VALUES (?, ?, ?)",
            (str(chat_id), username, description)
        )
        self.conn.commit()

    def delete_top_shop(self, chat_id, username):
        self.cursor.execute(
            "DELETE FROM top_shops WHERE chat_id = ? AND username = ?",
            (str(chat_id), username)
        )
        self.conn.commit()

    def get_top_shops(self, chat_id):
        self.cursor.execute(
            "SELECT username, description FROM top_shops WHERE chat_id = ?",
            (str(chat_id),)
        )
        return self.cursor.fetchall()

    def add_user(self, user_id, username):
        self.cursor.execute(
            "INSERT OR REPLACE INTO users (user_id, username) VALUES (?, ?)",
            (user_id, username)
        )
        self.conn.commit()

    def get_user_id_by_username(self, username):
        self.cursor.execute(
            "SELECT user_id FROM users WHERE username = ? OR username = ?",
            (username, f"@{username}")
        )
        result = self.cursor.fetchone()
        return result[0] if result else None

    def increment_trigger_stat(self, trigger_word):
        self.cursor.execute(
            "INSERT OR IGNORE INTO trigger_stats (trigger_word, count) VALUES (?, 0)",
            (trigger_word,)
        )
        self.cursor.execute(
            "UPDATE trigger_stats SET count = count + 1 WHERE trigger_word = ?",
            (trigger_word,)
        )
        self.conn.commit()

    def get_trigger_stats(self):
        self.cursor.execute("SELECT trigger_word, count FROM trigger_stats")
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()
# database.py
import psycopg2
from psycopg2 import pool
from config import DATABASE_URL
import time
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Инициализация пула соединений
try:
    connection_pool = psycopg2.pool.SimpleConnectionPool(
        1, 20, dsn=DATABASE_URL
    )
    if connection_pool:
        logger.info("Пул соединений с базой данных успешно создан")
except Exception as e:
    logger.error(f"Ошибка инициализации пула: {e}")
    raise

def get_connection():
    retries = 3
    while retries > 0:
        try:
            conn = connection_pool.getconn()
            return conn
        except Exception as e:
            logger.error(f"Ошибка подключения: {e}")
            retries -= 1
            time.sleep(1)
    raise Exception("Не удалось подключиться к базе данных")

def release_connection(conn):
    connection_pool.putconn(conn)

def init_db():
    conn = get_connection()
    try:
        cur = conn.cursor()
        # Таблица для чатов
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                chat_id BIGINT PRIMARY KEY
            );
        """)
        # Таблица для админов
        cur.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                chat_id BIGINT,
                user_id BIGINT,
                PRIMARY KEY (chat_id, user_id)
            );
        """)
        # Таблица для триггеров
        cur.execute("""
            CREATE TABLE IF NOT EXISTS triggers (
                chat_id BIGINT,
                trigger_text TEXT,
                response_text TEXT,
                PRIMARY KEY (chat_id, trigger_text)
            );
        """)
        # Таблица для прав на пересылку
        cur.execute("""
            CREATE TABLE IF NOT EXISTS send_permissions (
                chat_id BIGINT,
                source_id BIGINT,
                PRIMARY KEY (chat_id, source_id)
            );
        """)
        # Таблица для вип-участников
        cur.execute("""
            CREATE TABLE IF NOT EXISTS vips (
                chat_id BIGINT,
                user_id TEXT,
                username TEXT,
                PRIMARY KEY (chat_id, user_id)
            );
        """)
        # Таблица для последнего чата владельца
        cur.execute("""
            CREATE TABLE IF NOT EXISTS owner_last_chat (
                owner_id BIGINT PRIMARY KEY,
                chat_id BIGINT
            );
        """)
        conn.commit()
        cur.close()
        logger.info("База данных успешно инициализирована")
    except Exception as e:
        logger.error(f"Ошибка инициализации базы: {e}")
        raise
    finally:
        release_connection(conn)

def is_chat_registered(chat_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM chats WHERE chat_id = %s", (chat_id,))
        result = cur.fetchone()
        cur.close()
        return bool(result)
    except Exception as e:
        logger.error(f"Ошибка проверки чата {chat_id}: {e}")
        raise
    finally:
        release_connection(conn)

def register_chat(chat_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO chats (chat_id) VALUES (%s) ON CONFLICT DO NOTHING", (chat_id,))
        conn.commit()
        cur.close()
        logger.info(f"Чат {chat_id} зарегистрирован")
    except Exception as e:
        logger.error(f"Ошибка регистрации чата {chat_id}: {e}")
        raise
    finally:
        release_connection(conn)

def set_owner_last_chat(owner_id, chat_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO owner_last_chat (owner_id, chat_id) VALUES (%s, %s) "
            "ON CONFLICT (owner_id) DO UPDATE SET chat_id = %s",
            (owner_id, chat_id, chat_id)
        )
        conn.commit()
        cur.close()
        logger.info(f"Последний чат {chat_id} установлен для владельца {owner_id}")
    except Exception as e:
        logger.error(f"Ошибка установки последнего чата для {owner_id}: {e}")
        raise
    finally:
        release_connection(conn)

def get_owner_last_chat(owner_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT chat_id FROM owner_last_chat WHERE owner_id = %s", (owner_id,))
        result = cur.fetchone()
        cur.close()
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Ошибка получения последнего чата для {owner_id}: {e}")
        raise
    finally:
        release_connection(conn)

def is_admin(chat_id, user_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM admins WHERE chat_id = %s AND user_id = %s", (chat_id, user_id))
        result = cur.fetchone()
        cur.close()
        return bool(result)
    except Exception as e:
        logger.error(f"Ошибка проверки админа {user_id} в чате {chat_id}: {e}")
        raise
    finally:
        release_connection(conn)

def add_admin(chat_id, user_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO admins (chat_id, user_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (chat_id, user_id))
        conn.commit()
        cur.close()
        logger.info(f"Админ {user_id} добавлен в чат {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка добавления админа {user_id} в чат {chat_id}: {e}")
        raise
    finally:
        release_connection(conn)

def remove_admin(chat_id, user_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM admins WHERE chat_id = %s AND user_id = %s", (chat_id, user_id))
        conn.commit()
        cur.close()
        logger.info(f"Админ {user_id} удалён из чата {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка удаления админа {user_id} из чата {chat_id}: {e}")
        raise
    finally:
        release_connection(conn)

def add_trigger(chat_id, trigger_text, response_text):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO triggers (chat_id, trigger_text, response_text) VALUES (%s, %s, %s) "
            "ON CONFLICT (chat_id, trigger_text) DO UPDATE SET response_text = EXCLUDED.response_text",
            (chat_id, trigger_text.lower(), response_text)
        )
        conn.commit()
        cur.close()
        logger.info(f"Триггер {trigger_text} добавлен для чата {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка добавления триггера {trigger_text} в чат {chat_id}: {e}")
        raise
    finally:
        release_connection(conn)

def delete_trigger(chat_id, trigger_text):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM triggers WHERE chat_id = %s AND trigger_text = %s", (chat_id, trigger_text.lower()))
        conn.commit()
        cur.close()
        logger.info(f"Триггер {trigger_text} удалён из чата {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка удаления триггера {trigger_text} из чата {chat_id}: {e}")
        raise
    finally:
        release_connection(conn)

def get_trigger_response(chat_id, trigger_text):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT response_text FROM triggers WHERE chat_id = %s AND trigger_text = %s",
            (chat_id, trigger_text.lower())
        )
        result = cur.fetchone()
        cur.close()
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Ошибка получения ответа триггера {trigger_text} в чате {chat_id}: {e}")
        raise
    finally:
        release_connection(conn)

def add_send_permission(chat_id, source_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO send_permissions (chat_id, source_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (chat_id, source_id)
        )
        conn.commit()
        cur.close()
        logger.info(f"Права на пересылку для {source_id} добавлены в чат {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка добавления прав на пересылку для {source_id} в чат {chat_id}: {e}")
        raise
    finally:
        release_connection(conn)

def remove_send_permission(chat_id, source_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM send_permissions WHERE chat_id = %s AND source_id = %s",
            (chat_id, source_id)
        )
        conn.commit()
        cur.close()
        logger.info(f"Права на пересылку для {source_id} удалены из чата {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка удаления прав на пересылку для {source_id} в чат {chat_id}: {e}")
        raise
    finally:
        release_connection(conn)

def has_send_permission(chat_id, source_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM send_permissions WHERE chat_id = %s AND source_id = %s",
            (chat_id, source_id)
        )
        result = cur.fetchone()
        cur.close()
        return bool(result)
    except Exception as e:
        logger.error(f"Ошибка проверки прав на пересылку для {source_id} в чате {chat_id}: {e}")
        raise
    finally:
        release_connection(conn)

def add_vip(chat_id, user_id, username):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO vips (chat_id, user_id, username) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
            (chat_id, str(user_id), username)
        )
        conn.commit()
        cur.close()
        logger.info(f"VIP {user_id} добавлен в чат {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка добавления VIP {user_id} в чат {chat_id}: {e}")
        raise
    finally:
        release_connection(conn)

def remove_vip(chat_id, user_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM vips WHERE chat_id = %s AND user_id = %s", (chat_id, str(user_id)))
        conn.commit()
        cur.close()
        logger.info(f"VIP {user_id} удалён из чата {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка удаления VIP {user_id} в чате {chat_id}: {e}")
        raise
    finally:
        release_connection(conn)

def get_vips(chat_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT user_id, username FROM vips WHERE chat_id = %s", (chat_id,))
        result = cur.fetchall()
        cur.close()
        return result
    except Exception as e:
        logger.error(f"Ошибка получения VIP-списка для чата {chat_id}: {e}")
        raise
    finally:
        release_connection(conn)

def transfer_chat_data(old_chat_id, new_chat_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        # Перенос триггеров
        cur.execute("""
            INSERT INTO triggers (chat_id, trigger_text, response_text)
            SELECT %s, trigger_text, response_text
            FROM triggers WHERE chat_id = %s
            ON CONFLICT DO NOTHING
        """, (new_chat_id, old_chat_id))
        # Перенос админов
        cur.execute("""
            INSERT INTO admins (chat_id, user_id)
            SELECT %s, user_id
            FROM admins WHERE chat_id = %s
            ON CONFLICT DO NOTHING
        """, (new_chat_id, old_chat_id))
        # Перенос прав на пересылку
        cur.execute("""
            INSERT INTO send_permissions (chat_id, source_id)
            SELECT %s, source_id
            FROM send_permissions WHERE chat_id = %s
            ON CONFLICT DO NOTHING
        """, (new_chat_id, old_chat_id))
        # Перенос VIP
        cur.execute("""
            INSERT INTO vips (chat_id, user_id, username)
            SELECT %s, user_id, username
            FROM vips WHERE chat_id = %s
            ON CONFLICT DO NOTHING
        """, (new_chat_id, old_chat_id))
        # Регистрация нового чата
        cur.execute("INSERT INTO chats (chat_id) VALUES (%s) ON CONFLICT DO NOTHING", (new_chat_id,))
        conn.commit()
        cur.close()
        logger.info(f"Данные перенесены из чата {old_chat_id} в чат {new_chat_id}")
    except Exception as e:
        logger.error(f"Ошибка переноса данных из чата {old_chat_id} в чат {new_chat_id}: {e}")
        raise
    finally:
        release_connection(conn)

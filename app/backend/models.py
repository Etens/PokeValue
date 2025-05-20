import sqlite3


def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            search_query TEXT NOT NULL,
            image_url TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS collections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            card_name TEXT NOT NULL,
            card_number TEXT NOT NULL,
            image_url TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    try:
        cursor.execute("ALTER TABLE searches ADD COLUMN price TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE collections ADD COLUMN price TEXT")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

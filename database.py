import sqlite3

DATABASE = "data/adoption.db"


def connect_db():
    return sqlite3.connect(DATABASE)


def create_tables():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            age INTEGER NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS animals (
            animal_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            species TEXT NOT NULL,
            age INTEGER NOT NULL,
            breed TEXT,
            size TEXT,
            activity_level TEXT,
            description TEXT,
            image_path TEXT
        )
    """)

    conn.commit()
    conn.close()
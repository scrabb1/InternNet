import sqlite3

# Don't run this unless database breaks

def initiate():
    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users(
            username TEXT PRIMARY KEY,
            password TEXT,
            first_name TEXT,
            last_name TEXT,
            school TEXT,
            email_personal TEXT,
            email_school TEXT,
            age INTEGER,
            grade INTEGER,
            extracurriculars TEXT,
            interests TEXT,
            gpa REAL,
            courses TEXT,
            auth_token TEXT UNIQUE
        )
        """
    )

initiate()
import sqlite3
import pandas as pd

# Don't run this unless database breaks

def initiate():

    df = pd.read_csv(r"/database/fixed_jobs_data.csv")
    df_cut = df.iloc[272:341]
    connection = sqlite3.connect("internships.db")
    cursor = connection.cursor()
    
    organization = df["Institution Name"]
    name = df["Program Name"]
    Url = df["Website Address"]
    Category = df["AI_Category"]
    Location = 0
    Age = df["Age Eligibility"]


    cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS internships(
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        organization TEXT NOT NULL,
        Url TEXT,
        contact TEXT NOT NULL,
        deadline TEXT NOT NULL,
        category TEXT NOT NULL,
        location TEXT NOT NULL,
        creatorId TEXT NOT NULL,
        createdAt TEXT DEFAULT CURRENT_TIMESTAMP,
        updatedAt TEXT DEFAULT CURRENT_TIMESTAMP
    """)

    connection.commit()
    connection.close()

def add_internship(data):
    connection = sqlite3.connect("internships.db")
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO internships (
            id, name, organization, Url, contact, deadline,
            category, location, description, creatorId
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["id"],
        data["name"],
        data["organization"],
        data.get("Url"),
        data["contact"],
        data["deadline"],
        data["category"],
        data["location"],
        data["description"],
        data["creatorId"]
    ))

    connection.commit()
    connection.close()

def get_all_internships():
    connection = sqlite3.connect("internships.db")
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM internships")
    rows = cursor.fetchall()

    connection.close()
    return rows

def search_internships(keyword):
    connection = sqlite3.connect("internships.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM internships
        WHERE 
            name LIKE ? OR 
            organization LIKE ? OR 
            description LIKE ?
    """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))

    rows = cursor.fetchall()
    connection.close()
    return rows

def filter_internships(category):
    connection = sqlite3.connect("internships.db")
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM internships WHERE category = ?", (category,))
    rows = cursor.fetchall()

    connection.close()
    return rows

initiate()
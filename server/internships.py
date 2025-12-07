import sqlite3
import pandas as pd
import uuid

# Database filename constant
DB_NAME = "internships.db"

def initiate():
    """
    Creates the table and populates it with data from the CSV file.
    """
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    # 1. Create Table (Fixed syntax and added missing 'Description' column)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS internships(
        id TEXT PRIMARY KEY,
        Organization TEXT,
        Name TEXT,
        Url TEXT,
        Contact TEXT,
        Deadline TEXT,
        Category TEXT,
        Location TEXT,
        Cost TEXT,
        Age TEXT,
        Description TEXT
    )
    """)

    # 2. Read CSV and Insert Data
    try:
        df = pd.read_csv(r"fixed_jobs_data.csv")
        
        # Optional: Select specific rows like in your original code
        # df = df.iloc[271:341] 

        # Loop through the dataframe and insert each row
        for index, row in df.iterrows():
            cursor.execute("""
                INSERT INTO internships (
                    id, Organization, Name, Url, Contact, Deadline, Category, Location, Cost, Age, Description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),                # Generate a unique ID
                row.get("Institution Name", ""),  # Use .get() to avoid errors if col is missing
                row.get("Program Name", ""),
                row.get("Website Address", ""),
                "N/A",                            # Placeholder for Contact (not in CSV)
                row.get("Deadline", ""),
                row.get("AI_Category", ""),
                row.get("Geographic Location", ""),
                row.get("Cost Type", ""),
                row.get("Age Category", ""),
                "N/A"                             # Placeholder for Description (not in CSV)
            ))
        
        print(f"Successfully loaded {len(df)} rows from CSV.")

    except FileNotFoundError:
        print("CSV file not found. Database created but empty.")
    except Exception as e:
        print(f"An error occurred loading the CSV: {e}")

    connection.commit()
    connection.close()

def add_internship(data):
    """
    Adds a single internship from a dictionary.
    """
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    # Fixed column count (11 columns = 11 placeholders)
    cursor.execute("""
        INSERT INTO internships (
            id, Name, Organization, Url, Contact, Deadline, Category, Location, Cost, Age, Description
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("id", str(uuid.uuid4())), # Generate ID if one isn't provided
        data.get("name"),
        data.get("organization"),
        data.get("Url"),
        data.get("contact"),
        data.get("deadline"),
        data.get("category"),
        data.get("location"),
        data.get("cost"),         # Fixed mapping
        data.get("age"),          # Fixed mapping
        data.get("description")
    ))

    connection.commit()
    connection.close()

def get_all_internships():
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM internships")
    rows = cursor.fetchall()
    connection.close()
    return rows

def search_internships(keyword):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    # Added wildcards to ensure partial matching works correctly
    search_term = f"%{keyword}%"
    
    cursor.execute("""
        SELECT * FROM internships
        WHERE 
            Name LIKE ? OR 
            Organization LIKE ? OR 
            Description LIKE ?
    """, (search_term, search_term, search_term))

    rows = cursor.fetchall()
    connection.close()
    return rows

def filter_internships(category):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM internships WHERE Category = ?", (category,))
    rows = cursor.fetchall()
    connection.close()
    return rows

if __name__ == '__main__':
    # This block runs only when you execute the file directly
    initiate()
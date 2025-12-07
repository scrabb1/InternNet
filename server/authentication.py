import sqlite3
import json
import os
import logging
import secrets
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('authentication.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

normal_auth = ["username", "password", "first_name", "last_name", "school", "email_personal", "email_school", "age", "grade", "extracurriculars", "interests", "gpa", "courses"]

'''
Users Table:
username TEXT PRIMARY KEY,
password TEXT,
first_name TEXT,
last_name TEXT,
school TEXT,
email_personal TEXT,
email_school TEXT,
age INTEGER,
grade INTEGER,
auth_token TEXT UNIQUE,

Admins Table:
id TEXT PRIMARY KEY,
username TEXT UNIQUE,
password TEXT,
school_name TEXT,
email TEXT,
auth_token TEXT UNIQUE,
createdAt TEXT DEFAULT CURRENT_TIMESTAMP,
'''

def init_admins_table():
    """Create admins table if it doesn't exist."""
    try:
        connection = sqlite3.connect('users.db')
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins(
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                school_name TEXT NOT NULL,
                email TEXT NOT NULL,
                auth_token TEXT UNIQUE,
                createdAt TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        connection.commit()
        connection.close()
        logger.info('Admins table ready')
    except Exception as e:
        logger.error(f'Error initializing admins table: {str(e)}', exc_info=True)

init_admins_table()

def generate_auth_token():
    """
    Generate a unique authentication token for the user
    """
    try:
        token = secrets.token_urlsafe(32)
        logger.debug("Generated new authentication token")
        return token
    except Exception as e:
        logger.error(f"Error generating auth token: {str(e)}", exc_info=True)
        return None

def verify_structure(data):
    try:
        for element in normal_auth:
            if data.get(element):
                logger.debug(f"Verified field: {element} = {data.get(element)}")
                continue
            else:
                logger.warning(f"Missing required field: {element}")
                return False
        
        logger.info("Data structure verification passed")
        return True
    except Exception as e:
        logger.error(f"Error verifying data structure: {str(e)}", exc_info=True)
        return False

def username_exists(username):
    try:
        connection = sqlite3.connect('users.db')
        cursor = connection.cursor()

        cursor.execute(
            """
                SELECT * FROM users WHERE username = ?
            """,(username,)
        )

        exists = cursor.fetchone()
        connection.close()
        
        if exists:
            logger.info(f"Username '{username}' already exists in database")
            return True
        else:
            logger.debug(f"Username '{username}' is available")
            return False
    except sqlite3.Error as e:
        logger.error(f"Database error checking username '{username}': {str(e)}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking username '{username}': {str(e)}", exc_info=True)
        return False


def signup_user(data):
    try:
        connection = sqlite3.connect('users.db')
        cursor = connection.cursor()

        username = data.get("username")

        if username_exists(username):
            logger.warning(f"Signup attempt failed: username '{username}' already exists")
            return False, None
        
        password = data.get("password")
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        school = data.get("school")
        email_personal = data.get("email_personal")
        email_school = data.get("email_school")
        age = data.get("age")
        grade = data.get("grade")
        extracurriculars = data.get("extracurriculars")
        interests = data.get("interests")
        gpa = data.get("gpa")
        courses = data.get("courses")

        # Generate authentication token
        auth_token = generate_auth_token()
        if not auth_token:
            logger.error("Failed to generate authentication token during signup")
            return False, None

        cursor.execute(
            """
                INSERT INTO users (username, password, first_name, last_name, school, email_personal, email_school, age, grade, extracurriculars, interests, gpa, courses, auth_token)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (username, password, first_name, last_name, school, email_personal, email_school, int(age), int(grade), extracurriculars, interests, float(gpa) if gpa not in (None, '') else None, courses, auth_token)
        )

        connection.commit()
        connection.close()

        logger.info(f"Successfully added user: {username}")
        return True, auth_token
    except sqlite3.IntegrityError as e:
        logger.error(f"Database integrity error during signup: {str(e)}", exc_info=True)
        return False, None
    except sqlite3.Error as e:
        logger.error(f"Database error during signup: {str(e)}", exc_info=True)
        return False, None
    except ValueError as e:
        logger.error(f"Invalid data type during signup: {str(e)}", exc_info=True)
        return False, None
    except Exception as e:
        logger.error(f"Unexpected error during signup: {str(e)}", exc_info=True)
        return False, None

def initiate_signup(data):
    try:
        if verify_structure(data):
            success, auth_token = signup_user(data)
            if success:
                logger.info("Signup process completed successfully")
                return True, auth_token
            else:
                logger.warning("Signup process failed at signup_user stage")
                return False, None
        else:
            logger.warning("Signup process failed at data verification stage")
            return False, None
    except Exception as e:
        logger.error(f"Unexpected error during signup initiation: {str(e)}", exc_info=True)
        return False, None

def verify_password(stored_password, provided_password):
    """
    Verify if the provided password matches the stored password.
    In production, you should use password hashing (bcrypt, argon2, etc.)
    """
    try:
        return stored_password == provided_password
    except Exception as e:
        logger.error(f"Error verifying password: {str(e)}", exc_info=True)
        return False

def login_user(username, password):
    try:
        connection = sqlite3.connect('users.db')
        cursor = connection.cursor()

        cursor.execute(
            """
                SELECT username, password, first_name, last_name, school, auth_token FROM users WHERE username = ?
            """, (username,)
        )

        user = cursor.fetchone()
        connection.close()

        if not user:
            logger.warning(f"Login attempt failed: username '{username}' not found")
            return False, None

        stored_username, stored_password, first_name, last_name, school, auth_token = user

        if not verify_password(stored_password, password):
            logger.warning(f"Login attempt failed: incorrect password for username '{username}'")
            return False, None

        logger.info(f"Successful login for user: {username}")
        return True, {
            "username": stored_username,
            "first_name": first_name,
            "last_name": last_name,
            "school": school,
            "auth_token": auth_token
        }
    except sqlite3.Error as e:
        logger.error(f"Database error during login: {str(e)}", exc_info=True)
        return False, None
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}", exc_info=True)
        return False, None

def initiate_login(username, password):
    try:
        if not username or not password:
            logger.warning("Login attempt with missing credentials")
            return False, None

        success, user_data = login_user(username, password)

        if success:
            logger.info(f"Login process completed successfully for user: {username}")
            return True, user_data
        else:
            logger.warning(f"Login process failed for user: {username}")
            return False, None
    except Exception as e:
        logger.error(f"Unexpected error during login initiation: {str(e)}", exc_info=True)
        return False, None


def get_user_by_token(auth_token):
    """Return user row/dict for given auth_token, or None. Checks both users and admins tables."""
    try:
        if not auth_token:
            return None
        connection = sqlite3.connect('users.db')
        cursor = connection.cursor()

        # First check users table
        cursor.execute(
            """
                SELECT username, first_name, last_name, school, email_personal, email_school, age, grade, extracurriculars, interests, gpa, courses
                FROM users WHERE auth_token = ?
            """, (auth_token,)
        )
        row = cursor.fetchone()

        if row:
            (username, first_name, last_name, school, email_personal, email_school, age, grade, extracurriculars, interests, gpa, courses) = row
            connection.close()
            return {
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "school": school,
                "email_personal": email_personal,
                "email_school": email_school,
                "age": age,
                "grade": grade,
                "extracurriculars": extracurriculars,
                "interests": interests,
                "gpa": gpa,
                "courses": courses
            }

        # If not found in users table, check admins table
        cursor.execute(
            """
                SELECT username, school_name, email FROM admins WHERE auth_token = ?
            """, (auth_token,)
        )
        admin_row = cursor.fetchone()
        connection.close()

        if admin_row:
            (username, school_name, email) = admin_row
            logger.debug(f"Admin found for token: {username}")
            return {
                "username": username,
                "school_name": school_name,
                "email": email,
                "is_admin": True
            }

        logger.debug(f"No user or admin found for token")
        return None
    except sqlite3.Error as e:
        logger.error(f"Database error looking up token: {str(e)}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Unexpected error looking up token: {str(e)}", exc_info=True)
        return None


def admin_signup(data):
    """Create a new admin account for school/institution."""
    try:
        connection = sqlite3.connect('users.db')
        cursor = connection.cursor()

        username = data.get("username")
        password = data.get("password")
        school_name = data.get("school_name")
        email = data.get("email")

        if not all([username, password, school_name, email]):
            logger.warning("Admin signup missing required fields")
            return False, None

        # Check if admin exists
        cursor.execute("SELECT * FROM admins WHERE username = ?", (username,))
        if cursor.fetchone():
            logger.warning(f"Admin signup failed: username '{username}' already exists")
            connection.close()
            return False, None

        auth_token = generate_auth_token()
        if not auth_token:
            connection.close()
            return False, None

        admin_id = str(secrets.token_hex(8))
        cursor.execute("""
            INSERT INTO admins (id, username, password, school_name, email, auth_token)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (admin_id, username, password, school_name, email, auth_token))

        connection.commit()
        connection.close()
        logger.info(f"Admin account created: {username} ({school_name})")
        return True, auth_token
    except sqlite3.IntegrityError as e:
        logger.error(f"Admin signup integrity error: {str(e)}", exc_info=True)
        return False, None
    except Exception as e:
        logger.error(f"Admin signup error: {str(e)}", exc_info=True)
        return False, None


def admin_login(username, password):
    """Login admin and return auth token."""
    try:
        connection = sqlite3.connect('users.db')
        cursor = connection.cursor()

        cursor.execute("""
            SELECT username, password, school_name, email, auth_token FROM admins WHERE username = ?
        """, (username,))

        admin = cursor.fetchone()
        connection.close()

        if not admin:
            logger.warning(f"Admin login failed: username '{username}' not found")
            return False, None

        stored_username, stored_password, school_name, email, auth_token = admin

        if not verify_password(stored_password, password):
            logger.warning(f"Admin login failed: incorrect password for username '{username}'")
            return False, None

        logger.info(f"Admin login successful: {username}")
        return True, {
            "username": stored_username,
            "school_name": school_name,
            "email": email,
            "auth_token": auth_token
        }
    except sqlite3.Error as e:
        logger.error(f"Admin login database error: {str(e)}", exc_info=True)
        return False, None
    except Exception as e:
        logger.error(f"Admin login error: {str(e)}", exc_info=True)
        return False, None


def update_user_by_token(auth_token, data):
    """Update allowed user fields for the user identified by auth_token."""
    try:
        if not auth_token:
            return False
        allowed = {"first_name", "last_name", "school", "email_personal", "email_school", "age", "grade", "extracurriculars", "interests", "gpa", "courses"}
        to_set = {}
        for k, v in data.items():
            if k in allowed:
                to_set[k] = v

        if not to_set:
            return False

        connection = sqlite3.connect('users.db')
        cursor = connection.cursor()
        parts = []
        params = []
        for k, v in to_set.items():
            parts.append(f"{k} = ?")
            # Convert numeric fields where appropriate
            if k in ("age", "grade"):
                params.append(int(v) if v not in (None, '') else None)
            elif k == "gpa":
                params.append(float(v) if v not in (None, '') else None)
            else:
                params.append(v)

        params.append(auth_token)
        sql = f"UPDATE users SET {', '.join(parts)} WHERE auth_token = ?"
        cursor.execute(sql, tuple(params))
        connection.commit()
        connection.close()

        # After updating DB, write a JSON copy of the user's profile to disk
        try:
            user = get_user_by_token(auth_token)
            if user and user.get('username'):
                os.makedirs('profile_data', exist_ok=True)
                path = os.path.join('profile_data', f"{user['username']}.json")
                with open(path, 'w', encoding='utf-8') as fh:
                    json.dump(user, fh, ensure_ascii=False, indent=2)
                logger.info(f'Wrote profile JSON for user {user.get("username")} to {path}')
        except Exception:
            logger.exception('Failed to write profile JSON file')

        return True
    except Exception as e:
        logger.error(f"Error updating user by token: {str(e)}", exc_info=True)
        return False


def get_admin_by_token(auth_token):
    """Return admin data by auth token."""
    try:
        if not auth_token:
            return None
        connection = sqlite3.connect('users.db')
        cursor = connection.cursor()

        cursor.execute("""
            SELECT username, school_name, email FROM admins WHERE auth_token = ?
        """, (auth_token,))

        row = cursor.fetchone()
        connection.close()

        if not row:
            logger.debug("No admin found for token")
            return None

        username, school_name, email = row
        return {
            "username": username,
            "school_name": school_name,
            "email": email
        }
    except sqlite3.Error as e:
        logger.error(f"Error looking up admin token: {str(e)}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Unexpected error looking up admin token: {str(e)}", exc_info=True)
        return None
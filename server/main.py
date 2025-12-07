from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import authentication
import logging
import database.internships as internships_module
import uuid
from datetime import datetime
from llamaquery_ai import get_student_recommendations

app = Flask(__name__)
CORS(app)

# Configure logging
logger = logging.getLogger(__name__)


def ensure_users_schema():
    try:
        conn = sqlite3.connect('users.db')
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(users)")
        cols = [r[1] for r in cur.fetchall()]
        # Ensure required profile columns exist; add any that are missing.
        required = {
            'auth_token': "TEXT",
            'extracurriculars': "TEXT",
            'interests': "TEXT",
            'gpa': "REAL",
            'courses': "TEXT"
        }
        for col, col_type in required.items():
            if col not in cols:
                try:
                    cur.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")
                    conn.commit()
                    logger.info(f'Added {col} column to users table')
                except Exception:
                    logger.exception(f'Failed to add column {col}')
        conn.close()
    except Exception:
        logger.exception('Error ensuring users schema')

ensure_users_schema()


@app.route('/api/signup', methods=['POST'])
def authenticate():
    try:
        data = request.get_json()
        
        if not data:
            logger.warning("Malformed request: No JSON data provided")
            return jsonify({
                "success": False,
                "error": "Malformed request",
                "details": "No JSON data provided in request body"
            }), 400

        # Verify all required fields are present (including profile fields)
        required_fields = ["username", "password", "first_name", "last_name", "school", "email_personal", "email_school", "age", "grade", "extracurriculars", "interests", "gpa", "courses"]
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        
        if missing_fields:
            logger.warning(f"Signup attempt with missing fields: {missing_fields}")
            return jsonify({
                "success": False,
                "error": "Missing required fields",
                "details": f"The following fields are required: {', '.join(missing_fields)}"
            }), 400

        # Attempt signup
        success, auth_token = authentication.initiate_signup(data)

        if success:
            logger.info(f"Successful signup for user: {data.get('username')}")
            return jsonify({
                "success": True,
                "message": "Signup completed successfully",
                "auth_token": auth_token
            }), 201
        else:
            # Check if username exists
            if authentication.username_exists(data.get('username')):
                logger.warning(f"Signup failed: Username '{data.get('username')}' already exists")
                return jsonify({
                    "success": False,
                    "error": "Signup failed",
                    "details": f"Username '{data.get('username')}' is already taken. Please choose a different username."
                }), 409
            else:
                logger.warning(f"Signup failed for user: {data.get('username')}")
                return jsonify({
                    "success": False,
                    "error": "Signup failed",
                    "details": "An error occurred during signup. Please try again later."
                }), 500
                
    except ValueError as e:
        logger.error(f"Invalid data type in signup request: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Invalid data format",
            "details": f"One or more fields have invalid data types. Age and grade must be numbers."
        }), 400
    except Exception as e:
        logger.error(f"Unexpected error during signup: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": "Server error",
            "details": "An unexpected error occurred. Please try again later."
        }), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data:
            logger.warning("Malformed login request: No JSON data provided")
            return jsonify({
                "success": False,
                "error": "Malformed request",
                "details": "No JSON data provided in request body"
            }), 400

        username = data.get('username')
        password = data.get('password')

        # Verify required fields are present
        if not username or not password:
            logger.warning("Login attempt with missing credentials")
            return jsonify({
                "success": False,
                "error": "Missing credentials",
                "details": "Both username and password are required"
            }), 400

        # Attempt login
        success, user_data = authentication.initiate_login(username, password)

        if success:
            logger.info(f"Successful login for user: {username}")
            return jsonify({
                "success": True,
                "message": "Login successful",
                "auth_token": user_data["auth_token"],
                "user": {
                    "username": user_data["username"],
                    "first_name": user_data["first_name"],
                    "last_name": user_data["last_name"],
                    "school": user_data["school"]
                }
            }), 200
        else:
            logger.warning(f"Login failed for user: {username}")
            return jsonify({
                "success": False,
                "error": "Login failed",
                "details": "Invalid username or password. Please try again."
            }), 401
                
    except ValueError as e:
        logger.error(f"Invalid data type in login request: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Invalid data format",
            "details": "One or more fields have invalid data types."
        }), 400
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": "Server error",
            "details": "An unexpected error occurred. Please try again later."
        }), 500


@app.route('/api/profile', methods=['GET', 'PATCH'])
def profile():
    try:
        auth = request.headers.get('Authorization')
        token = None
        if auth and auth.startswith('Bearer '):
            token = auth.split(' ', 1)[1]

        user = authentication.get_user_by_token(token)
        if not user:
            return jsonify({"success": False, "error": "Unauthorized", "details": "Invalid or missing auth token"}), 401

        if request.method == 'GET':
            return jsonify({"success": True, "user": user}), 200

        # PATCH: update allowed profile fields
        payload = request.get_json()
        if not payload:
            return jsonify({"success": False, "error": "Malformed request", "details": "No JSON provided"}), 400

        ok = authentication.update_user_by_token(token, payload)
        if ok:
            return jsonify({"success": True}), 200
        else:
            return jsonify({"success": False, "error": "Update failed"}), 400
    except Exception as e:
        logger.error(f"Profile error: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": "Server error", "details": "Profile error"}), 500


@app.route('/api/admin/signup', methods=['POST'])
def admin_signup():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Malformed request", "details": "No JSON data provided"}), 400

        required_fields = ["username", "password", "school_name", "email"]
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            return jsonify({"success": False, "error": "Missing fields", "details": f"Required: {', '.join(missing)}"}), 400

        success, auth_token = authentication.admin_signup(data)
        if success:
            logger.info(f"Admin signup successful for {data.get('username')}")
            return jsonify({"success": True, "message": "Admin account created", "auth_token": auth_token}), 201
        else:
            return jsonify({"success": False, "error": "Admin signup failed", "details": "Username may already exist"}), 409
    except Exception as e:
        logger.error(f"Admin signup error: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": "Server error", "details": "Could not create admin account"}), 500


@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Malformed request"}), 400

        username = data.get('username')
        password = data.get('password')
        if not username or not password:
            return jsonify({"success": False, "error": "Missing credentials"}), 400

        success, admin_data = authentication.admin_login(username, password)
        if success:
            logger.info(f"Admin login successful: {username}")
            return jsonify({"success": True, "message": "Admin login successful", "auth_token": admin_data["auth_token"], "admin": {"username": admin_data["username"], "school_name": admin_data["school_name"], "email": admin_data["email"]}}), 200
        else:
            return jsonify({"success": False, "error": "Invalid credentials"}), 401
    except Exception as e:
        logger.error(f"Admin login error: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": "Server error"}), 500


@app.route('/api/recommendations', methods=['GET'])
def get_recommendations():
    """
    Get AI-powered internship recommendations for the logged-in student.
    Requires valid auth token.
    """
    try:
        auth = request.headers.get('Authorization')
        token = None
        if auth and auth.startswith('Bearer '):
            token = auth.split(' ', 1)[1]

        user = authentication.get_user_by_token(token)
        if not user:
            return jsonify({"success": False, "error": "Unauthorized", "details": "Invalid or missing auth token"}), 401
        
        # Only students can get recommendations (admins have is_admin flag)
        if user.get('is_admin'):
            return jsonify({"success": False, "error": "Forbidden", "details": "Only students can receive recommendations"}), 403
        
        username = user.get('username')
        
        # Get recommendations from AI
        result = get_student_recommendations(username)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Recommendations error: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": "Server error", "details": str(e)}), 500


@app.route('/api/internships', methods=['GET'])
def list_internships():
    try:
        q = request.args.get('q')
        category = request.args.get('category')

        if q:
            rows = internships_module.search_internships(q)
        elif category:
            rows = internships_module.filter_internships(category)
        else:
            rows = internships_module.get_all_internships()

        # Convert rows to dicts (assuming columns order from internships table)
        internships = []
        for r in rows:
            internships.append({
                "id": r[0],
                "name": r[1],
                "organization": r[2],
                "Url": r[3],
                "contact": r[4],
                "deadline": r[5],
                "category": r[6],
                "location": r[7],
                "description": r[8],
                "creatorId": r[9],
                "createdAt": r[10],
                "updatedAt": r[11]
            })

        return jsonify({"success": True, "internships": internships}), 200
    except Exception as e:
        logger.error(f"Error listing internships: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": "Server error", "details": "Could not list internships"}), 500


@app.route('/api/internships', methods=['POST'])
def create_internship():
    try:
        # Require Authorization header with admin bearer token
        auth = request.headers.get('Authorization')
        token = None
        if auth and auth.startswith('Bearer '):
            token = auth.split(' ', 1)[1]

        admin = authentication.get_admin_by_token(token)
        if not admin:
            return jsonify({"success": False, "error": "Unauthorized", "details": "Admin auth token required"}), 401

        data = request.get_json()
        # minimal validation
        required = ['name', 'organization', 'contact', 'deadline', 'category', 'location', 'description']
        missing = [f for f in required if not data.get(f)]
        if missing:
            return jsonify({"success": False, "error": "Missing fields", "details": f"Missing: {', '.join(missing)}"}), 400

        internship = {
            "id": str(uuid.uuid4()),
            "name": data.get('name'),
            "organization": data.get('organization'),
            "Url": data.get('Url'),
            "contact": data.get('contact'),
            "deadline": data.get('deadline'),
            "category": data.get('category'),
            "location": data.get('location'),
            "description": data.get('description'),
            "creatorId": admin['username']
        }

        internships_module.add_internship(internship)
        logger.info(f"Internship created by {admin['username']}: {internship['name']}")
        return jsonify({"success": True, "internship": internship}), 201
    except Exception as e:
        logger.error(f"Error creating internship: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": "Server error", "details": "Could not create internship"}), 500


@app.route('/api/tracker', methods=['GET', 'POST', 'PATCH'])
def tracker():

    try:
        # simple tracker storage in trackers.db
        auth = request.headers.get('Authorization')
        token = None
        if auth and auth.startswith('Bearer '):
            token = auth.split(' ', 1)[1]

        user = authentication.get_user_by_token(token)
        if not user:
            return jsonify({"success": False, "error": "Unauthorized", "details": "Invalid or missing auth token"}), 401

        username = user['username']
        connection = sqlite3.connect('trackers.db')
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trackers(
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                internshipId TEXT NOT NULL,
                status TEXT NOT NULL,
                notes TEXT,
                updatedAt TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        connection.commit()

        if request.method == 'POST':
            payload = request.get_json()
            internshipId = payload.get('internshipId')
            status_field = payload.get('status') or 'interested'
            notes = payload.get('notes') or ''
            if not internshipId:
                connection.close()
                return jsonify({"success": False, "error": "Missing fields", "details": "internshipId required"}), 400

            tracker_id = str(uuid.uuid4())
            cursor.execute("INSERT INTO trackers (id, username, internshipId, status, notes) VALUES (?,?,?,?,?)",
                           (tracker_id, username, internshipId, status_field, notes))
            connection.commit()
            connection.close()
            return jsonify({"success": True, "id": tracker_id}), 201

        elif request.method == 'PATCH':
            payload = request.get_json()
            tracker_id = payload.get('id')
            status_field = payload.get('status')
            notes = payload.get('notes')
            if not tracker_id:
                connection.close()
                return jsonify({"success": False, "error": "Missing fields", "details": "tracker id required"}), 400
            # Only allow update if tracker belongs to user
            cursor.execute("SELECT username FROM trackers WHERE id = ?", (tracker_id,))
            row = cursor.fetchone()
            if not row or row[0] != username:
                connection.close()
                return jsonify({"success": False, "error": "Unauthorized", "details": "Tracker not found or not owned by user"}), 403
            # Update status and/or notes
            if status_field is not None:
                cursor.execute("UPDATE trackers SET status = ?, updatedAt = CURRENT_TIMESTAMP WHERE id = ?", (status_field, tracker_id))
            if notes is not None:
                cursor.execute("UPDATE trackers SET notes = ?, updatedAt = CURRENT_TIMESTAMP WHERE id = ?", (notes, tracker_id))
            connection.commit()
            connection.close()
            return jsonify({"success": True}), 200

        else:
            cursor.execute("SELECT id, internshipId, status, notes, updatedAt FROM trackers WHERE username = ?", (username,))
            rows = cursor.fetchall()
            connection.close()
            trackers = []
            for r in rows:
                trackers.append({"id": r[0], "internshipId": r[1], "status": r[2], "notes": r[3], "updatedAt": r[4]})
            return jsonify({"success": True, "trackers": trackers}), 200

    except Exception as e:
        logger.error(f"Tracker error: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": "Server error", "details": "Tracker error"}), 500

if __name__ == "__main__":
    app.run(debug=True)
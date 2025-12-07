import pandas as pd
from groq import Groq
import json
import os
import sqlite3
GROQ_API_KEY = "api key here"

INTERNSHIPS_AVALIABLE_CSV = r"/server/internships.db"

# The specific student we are helping
STUDENT_PROFILE = r"/server/authentication.py"

# Where to save the results
OUTPUT_FILE = r"/server/final_reccomendation"
# =================================================

# Initialize Client
client = Groq(api_key=GROQ_API_KEY)


def build_student_bio(user_data):
    """
    Build a comprehensive bio string from user profile data.
    """
    bio_parts = []
    if user_data.get('first_name'):
        bio_parts.append(f"Name: {user_data.get('first_name')} {user_data.get('last_name', '')}")
    if user_data.get('school'):
        bio_parts.append(f"School: {user_data.get('school')}")
    if user_data.get('grade'):
        bio_parts.append(f"Grade: {user_data.get('grade')}")
    if user_data.get('gpa'):
        bio_parts.append(f"GPA: {user_data.get('gpa')}")
    if user_data.get('interests'):
        bio_parts.append(f"Interests: {user_data.get('interests')}")
    if user_data.get('extracurriculars'):
        bio_parts.append(f"Extracurriculars: {user_data.get('extracurriculars')}")
    if user_data.get('courses'):
        bio_parts.append(f"Courses: {user_data.get('courses')}")
    
    return " | ".join(bio_parts) if bio_parts else "Student seeking internship opportunities"

def get_student_categories(student_bio):
    """
    Step 1: Analyze Student Bio to get their Interest Categories.
    """
    system_prompt = """
    You are a career counselor. Based on the student's bio: {STUDENT_PROFILE}, identify the top most relevant internship opportunities from this list: 
    {INTERNSHIPS_AVALIABLE_CSV}.
    Output JSON only: {"categories": ["Category1", "Category2"]}
    """
    
    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": student_bio}
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)['categories']
    except Exception as e:
        print(f"Error categorizing student: {e}")
        return ["STEM"] # Fallback

def rank_jobs_with_ai(student_bio, candidate_jobs):
    """
    Step 2: Send the filtered jobs to AI and ask for the Top 5 matches + Reasoning.
    """
    # Convert the dataframe to a simple text list to save tokens
    # We pass the index so we can look it up later
    jobs_text = ""
    for index, row in candidate_jobs.iterrows():
        # Truncate description to 200 chars to fit more jobs in context
        desc = str(row.get('description', ''))[:200]
        jobs_text += f"ID: {index} | Name: {row.get('name', 'N/A')} | Desc: {desc}...\n"

    system_prompt = f"""
    You are a helpful internship matchmaker. 
    1. Read the Student Bio below.
    2. Read the List of Jobs provided.
    3. Return the IDs of the TOP 5 jobs that match the student's interests.
    4. For each match, write a short "Why" sentence explaining the match.
    
    Student Bio: "{student_bio}"

    Output JSON ONLY in this format:
    {{
        "matches": [
            {{"id": 123, "reason": "Good for coding skills"}},
            {{"id": 456, "reason": "Matches interest in helping people"}}
        ]
    }}
    """

    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": jobs_text}
            ],
            model="llama-3.3-70b-versatile", 
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)['matches']
    except Exception as e:
        print(f"Error ranking jobs: {e}")
        return []


def get_student_recommendations(username):
    """
    Main API function to get internship recommendations for a student.
    Fetches student profile from users DB, gets all internships, and ranks them.
    Returns top 5 recommendations with AI reasoning.
    """
    try:
        # 1. Get student profile from users database
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT username, first_name, last_name, school, grade, gpa, 
                   interests, extracurriculars, courses 
            FROM users WHERE username = ?
        """, (username,))
        user_row = cursor.fetchone()
        conn.close()
        
        if not user_row:
            return {"success": False, "error": "User not found"}
        
        # Build user dict
        user_data = {
            'username': user_row[0],
            'first_name': user_row[1],
            'last_name': user_row[2],
            'school': user_row[3],
            'grade': user_row[4],
            'gpa': user_row[5],
            'interests': user_row[6],
            'extracurriculars': user_row[7],
            'courses': user_row[8]
        }
        
        # Build bio from student profile
        student_bio = build_student_bio(user_data)
        
        # 2. Load all internships from internships database
        conn = sqlite3.connect('internships.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM internships")
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        
        # Convert to dataframe for AI processing
        df_jobs = pd.DataFrame(rows, columns=columns)
        
        if df_jobs.empty:
            return {"success": False, "error": "No internships available"}
        
        # 3. Limit to top 100 internships to save tokens
        candidates = df_jobs.head(100)
        
        # 4. Get AI recommendations
        top_matches = rank_jobs_with_ai(student_bio, candidates)
        
        if not top_matches:
            return {"success": False, "error": "Could not generate recommendations"}
        
        # 5. Build recommendation results with full job details
        recommendations = []
        for match in top_matches:
            try:
                job_id = int(match['id'])
                reason = match.get('reason', '')
                
                # Find the job in dataframe
                if job_id < len(df_jobs):
                    job = df_jobs.iloc[job_id].to_dict()
                    # Use the actual database ID (UUID) instead of row index
                    db_id = job.get('id', str(job_id))
                    recommendations.append({
                        'id': db_id,
                        'program_name': job.get('name', 'N/A'),
                        'company': job.get('organization', 'N/A'),
                        'location': job.get('location', 'N/A'),
                        'description': job.get('description', 'N/A'),
                        'url': job.get('Url', 'N/A'),
                        'ai_reason': reason
                    })
            except Exception as e:
                print(f"Error processing match {match}: {e}")
                continue
        
        return {
            "success": True,
            "student": user_data.get('first_name', 'Student'),
            "bio_summary": student_bio,
            "recommendations": recommendations
        }
    
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        return {"success": False, "error": str(e)}

# ================= MAIN LOGIC =================
# This section runs only when llamaquery_ai.py is executed directly, not when imported
if __name__ == "__main__":
    # 1. Load Data
    print(f"Loading jobs from {INTERNSHIPS_AVALIABLE_CSV}...")
    df_jobs = pd.read_csv(INTERNSHIPS_AVALIABLE_CSV)

    print(f"Loading student from {STUDENT_PROFILE}...")
    with open(STUDENT_PROFILE, 'r') as f:
        student_data = json.load(f)
        student_bio = student_data['bio']

    print(f"Student: {student_data.get('name', 'Student')}")
    print(f"Bio: {student_bio}")

    # 2. Get Categories
    print("\nAnalyzing student interests...")
    target_categories = get_student_categories(student_bio)
    print(f"Target Categories: {target_categories}")

    # 3. Filter Database 
    # We only look at jobs that match the categories Llama found to save time/tokens
    # Check if 'AI_Category' exists (it should from the previous script)
    if 'AI_Category' in df_jobs.columns:
        candidates = df_jobs[df_jobs['AI_Category'].isin(target_categories)]
    else:
        print("Warning: 'AI_Category' column missing. Scanning top 50 rows instead.")
        candidates = df_jobs

    # Limit to 50 candidates max so we don't crash the API context limit
    if len(candidates) > 50:
        candidates = candidates.head(50)

    # Handle empty case
    if candidates.empty:
        print("No exact category matches found. Fallback to top 20 jobs.")
        candidates = df_jobs.head(20)

    print(f"Found {len(candidates)} potential candidates. Asking AI to rank the best 5...")

    # 4. Rank with AI
    top_matches = rank_jobs_with_ai(student_bio, candidates)

    # 5. Build Final CSV
    results = []
    for match in top_matches:
        job_id = int(match['id'])
        reason = match['reason']
        
        # Get the original job row using the ID (Index)
        if job_id in df_jobs.index:
            original_row = df_jobs.loc[job_id].to_dict()
            
            # Add the AI's "Why" reasoning
            original_row['AI_Reason'] = reason
            results.append(original_row)

    # Save to file
    matches_df = pd.DataFrame(results)
    matches_df.to_csv(OUTPUT_FILE, index=False)

    print("\n" + "="*40)
    print(f"SUCCESS! Recommendations saved to:\n{OUTPUT_FILE}")
    print("="*40)
    # Print a preview
    if not matches_df.empty:
        print(matches_df[['Program Name', 'AI_Reason']])
    else:
        print("No matches found.")
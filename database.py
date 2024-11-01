import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_db_connection():
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    return conn


def is_database_empty():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM users;")
            count = cursor.fetchone()[0]
            return count == 0  # Returns True if the table is empty


def add_to_leaderboard(challenge_name: str, username: str, submission_order: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO leaderboard (challenge_id, username, submission_order) VALUES (%s, %s, %s)",
        (challenge_name, username, submission_order)
    )
    conn.commit()
    conn.close()


def get_leaderboard(challenge_name: str):
    if is_database_empty():
        return []
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT username FROM leaderboard WHERE question = %s ORDER BY submission_order ASC LIMIT 5", (challenge_name,)
    )
    leaderboard = cursor.fetchall()
    conn.close()
    return [entry[0] for entry in leaderboard]


def get_overall_leaderboard():
    if is_database_empty():
        return []
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT username, SUM(COALESCE(total_score, 0)) as total_score
                FROM score
                GROUP BY username
                ORDER BY total_score DESC
                LIMIT 5;
            """)
            leaderboard = cursor.fetchall()
            return leaderboard


def get_user_score(username: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT total_score FROM score WHERE username = %s", (username,)
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0


def update_user_score(username: str, score: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT total_score FROM score WHERE username = %s", (username,)
    )
    result = cursor.fetchone()

    if result:
        new_score = result[0] + score
        cursor.execute(
            "UPDATE score SET total_score = %s WHERE username = %s", (new_score, username)
        )
    else:
        cursor.execute(
            "INSERT INTO score (username, total_score) VALUES (%s, %s)", (username, score)
        )

    conn.commit()
    conn.close()


def delete_user_info(username):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM leaderboard WHERE username = %s;", (username,))
            cursor.execute("DELETE FROM score WHERE username = %s;", (username,))
            conn.commit()


# def get_all_challenges():
#     from responses import answers  # Import here to avoid circular import
#     return ', '.join(answers.keys())


def get_all_challenges():
    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()
    # Query to get challenge details
    cursor.execute("""
        SELECT name, challenge_id, max_points, 
               CASE WHEN status = 1 THEN 'Open' ELSE 'Closed' END AS status
        FROM challenges;
    """)
    challenges = cursor.fetchall()

    # Close the connection
    cursor.close()
    conn.close()

    # Format the message
    if not challenges:
        return "No challenges are currently available."

    formatted_challenges = ["📜 CTF Challenges Available", "─────────────────────────────"]
    for challenge in challenges:
        name, challenge_id, points, status = challenge
        formatted_challenges.extend([
            f"{name}",
            f"   🆔 ID: {challenge_id}",
            f"   🏅 Points: {points} pts",
            f"   🚩 Status: {status}",
            ""
        ])
    formatted_challenges.append("─────────────────────────────\n⚠️ More challenges will be unlocked as teams progress!")

    return '\n'.join(formatted_challenges)


def get_challenge_info(challenge_id: str):
    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Query for challenge details and submission counts
    cursor.execute("""
        SELECT c.challenge_id, c.name, c.max_points, 
               CASE WHEN c.status = 1 THEN 'Open' ELSE 'Closed' END AS status,
               c.difficulty, c.description, c.file_link, 
               COALESCE((SELECT COUNT(*) FROM submissions s WHERE s.challenge_id = %s AND s.verdict = TRUE), 0) AS correct_submissions,
               COALESCE((SELECT COUNT(*) FROM submissions s WHERE s.challenge_id = %s), 0) AS total_submissions
        FROM challenges c
        WHERE c.challenge_id = %s;
    """, (challenge_id, challenge_id, challenge_id))

    challenge = cursor.fetchone()

    # Close the connection
    cursor.close()
    conn.close()

    if not challenge:
        return "Challenge not found."

    # Destructure challenge details
    challenge_id, name, max_points, status, difficulty, description, file_link, correct_subs, total_subs = challenge

    # Format the message
    formatted_info = [
        "🔍 Challenge Details",
        "─────────────────────────────",
        f"ID: {challenge_id}",
        f"Name: {name}",
        f"Points: {max_points} pts",
        f"Difficulty: {difficulty}",
        "Time Limit: None",  # Update if you have a time limit field
        "",
        "Description:",
        f"  {description}",
        "",
        f"📂 Files: [{file_link}]" if file_link else "📂 Files: None",
        "🔎 Hint: Check all user inputs, they might not be as safe as they seem. 💡",  # Update if hints exist
        "",
        f"🚩 Status: {status}",
        f"🔥 Submissions: {correct_subs}/{total_subs}",
        "─────────────────────────────"
    ]

    return '\n'.join(formatted_info)


def get_user_solved_questions(username: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT question, points
        FROM leaderboard
        WHERE username = %s
        ORDER BY submission_order ASC
        """,
        (username,)
    )
    questions_with_scores = cursor.fetchall()
    conn.close()
    return questions_with_scores

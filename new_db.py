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


def submit_flag(user_name: str, challenge_id: str, flag: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check challenge status and answer
        cursor.execute(
            "SELECT answer, status, max_points FROM challenges WHERE challenge_id = %s",
            (challenge_id,)
        )
        result = cursor.fetchone()
        if not result:
            return "Challenge not found."

        answer, status, max_points = result

        if status != 1:
            return "Challenge is currently closed."

        # Check if the submitted flag is correct
        is_correct = (flag == answer)

        # Record submission
        cursor.execute(
            """
            INSERT INTO submissions (user_name, challenge_id, time, flag_submitted, verdict, points_awarded)
            VALUES (%s, %s, NOW(), %s, %s, %s) RETURNING id
            """,
            (user_name, challenge_id, flag, is_correct, max_points if is_correct else 0)
        )
        submission_id = cursor.fetchone()[0]

        # Update leaderboard if correct
        if is_correct:
            # Calculate submission order for leaderboard (1st, 2nd, etc.)
            cursor.execute(
                "SELECT COUNT(*) + 1 FROM leaderboard WHERE challenge_id = %s",
                (challenge_id,)
            )
            submission_order = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO leaderboard (challenge_id, user_name, submission_order, points)
                VALUES (%s, %s, %s, %s)
                """,
                (challenge_id, user_name, submission_order, max_points)
            )

            # Update user stats if correct
            cursor.execute(
                """
                UPDATE users
                SET points = points + %s, correct_submissions = correct_submissions + 1, 
                    last_active = NOW()
                WHERE user_name = %s
                """,
                (max_points, user_name)
            )
        else:
            # Increment incorrect submissions count
            cursor.execute(
                "UPDATE users SET incorrect_submissions = incorrect_submissions + 1, last_active = NOW() WHERE user_name = %s",
                (user_name,)
            )

        # Update score table
        cursor.execute(
            """
            INSERT INTO score (username, challenge_id, score)
            VALUES (%s, %s, %s)
            ON CONFLICT (username, challenge_id)
            DO UPDATE SET score = score + EXCLUDED.score
            """,
            (user_name, challenge_id, max_points if is_correct else 0)
        )

        conn.commit()
        return "Flag submission recorded successfully."

    except Exception as e:
        conn.rollback()
        return f"An error occurred: {e}"

    finally:
        cursor.close()
        conn.close()


def add_to_leaderboard(challenge_id: str, user_name: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get max_points for the challenge
        cursor.execute("SELECT max_points FROM challenges WHERE challenge_id = %s", (challenge_id,))
        max_points = cursor.fetchone()[0]

        # Calculate submission order for leaderboard (1st, 2nd, etc.)
        cursor.execute("SELECT COUNT(*) + 1 FROM leaderboard WHERE challenge_id = %s", (challenge_id,))
        submission_order = cursor.fetchone()[0]

        # Insert into leaderboard with the points awarded
        cursor.execute(
            """
            INSERT INTO leaderboard (challenge_id, user_name, submission_order, points)
            VALUES (%s, %s, %s, %s)
            """,
            (challenge_id, user_name, submission_order, max_points)
        )

        conn.commit()
        return "Added to leaderboard."

    except Exception as e:
        conn.rollback()
        return f"Error adding to leaderboard: {e}"

    finally:
        cursor.close()
        conn.close()

def get_leaderboard(challenge_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT user_name, points
        FROM leaderboard
        WHERE challenge_id = %s
        ORDER BY submission_order ASC LIMIT 5
        """,
        (challenge_id,)
    )
    leaderboard = cursor.fetchall()
    conn.close()
    return leaderboard if leaderboard else "No submissions for this challenge yet."


def get_overall_leaderboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT user_name, SUM(points) AS total_score
        FROM leaderboard
        GROUP BY user_name
        ORDER BY total_score DESC
        LIMIT 5
        """
    )
    overall_leaderboard = cursor.fetchall()
    conn.close()
    return overall_leaderboard if overall_leaderboard else "No leaderboard data available."


def get_user_score(user_name: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT SUM(points) FROM leaderboard WHERE user_name = %s", (user_name,)
    )
    total_score = cursor.fetchone()[0] or 0
    conn.close()
    return total_score


def get_challenge_info(challenge_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT c.challenge_id, c.name, c.max_points,
               CASE WHEN c.status = 1 THEN 'Open' ELSE 'Closed' END AS status,
               c.difficulty, c.description, c.file_link, c.hints_visible,
               SUM(CASE WHEN s.verdict = TRUE THEN 1 ELSE 0 END) AS correct_submissions,
               COUNT(s.id) AS total_submissions
        FROM challenges c
        LEFT JOIN submissions s ON c.challenge_id = s.challenge_id
        WHERE c.challenge_id = %s
        GROUP BY c.challenge_id
        """,
        (challenge_id,)
    )
    challenge_info = cursor.fetchone()
    conn.close()

    if not challenge_info:
        return "Challenge not found."

    # Destructure challenge details
    challenge_id, name, max_points, status, difficulty, description, file_link, hints_visible, correct_subs, total_subs = challenge_info

    # Check if the challenge is open
    if status == 'Closed':
        return "This challenge is currently closed."

    # Format hints as numbered list
    hints_formatted = (
        "\n".join([f"🔎 Hint {i + 1}: {hint}" for i, hint in enumerate(hints_visible)])
        if hints_visible else "🔎 No hints available."
    )

    # Format the message
    formatted_info = [
        "🔍 Challenge Details",
        "─────────────────────────────",
        f"🆔 ID: {challenge_id}",
        f"📝 Name: {name}",
        f"🏅 Points: {max_points} pts",
        f"🎯 Difficulty: {difficulty}",
        "⏳ Time Limit: None",  # Update if you have a time limit field
        "",
        "📜 Description:",
        f"  {description}",
        "",
        f"📂 Files: [{file_link}]" if file_link else "📂 Files: None",
        hints_formatted,
        "",
        f"🚩 Status: {status}",
        f"🔥 Submissions: {correct_subs}/{total_subs}",
        "─────────────────────────────"
    ]

    return '\n'.join(formatted_info)


def get_all_challenges():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT name, challenge_id, max_points
        FROM challenges
        WHERE status = 1  -- Only select open challenges
        """
    )
    challenges = cursor.fetchall()
    conn.close()

    if not challenges:
        return "No challenges are currently available."

    formatted_challenges = ["📜 CTF Challenges Available", "─────────────────────────────"]
    for name, challenge_id, max_points in challenges:
        formatted_challenges.extend([
            f"{name}",
            f"   🆔 ID: {challenge_id}",
            f"   🏅 Points: {max_points} pts",
            ""
        ])
    formatted_challenges.append("─────────────────────────────\n⚠️ More challenges will be unlocked as teams progress!")

    return '\n'.join(formatted_challenges)


def delete_user_info(user_name: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM leaderboard WHERE user_name = %s", (user_name,))
        cursor.execute("DELETE FROM submissions WHERE user_name = %s", (user_name,))
        cursor.execute("DELETE FROM users WHERE user_name = %s", (user_name,))
        conn.commit()

    except Exception as e:
        conn.rollback()
        return f"Error deleting user: {e}"

    finally:
        cursor.close()
        conn.close()
    return f"User {user_name} data deleted successfully."


def get_user_solved_questions(user_name: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT l.challenge_id, l.points
        FROM leaderboard l
        WHERE l.user_name = %s
        ORDER BY l.submission_order ASC
        """,
        (user_name,)
    )
    solved_challenges = cursor.fetchall()
    conn.close()
    return solved_challenges

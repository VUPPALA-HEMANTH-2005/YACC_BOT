import datetime

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
            cursor.execute("SELECT COUNT(*) FROM users_table;")
            count = cursor.fetchone()[0]
            return count == 0  # Returns True if the table is empty


def is_valid_challenge_id(challenge_id: str) -> bool:
    """
    Checks if a given challenge_id exists in the challenges_table.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM challenges_table WHERE challenge_id = %s", (challenge_id,))
    result = cursor.fetchone()
    exists = result is not None
    cursor.close()
    conn.close()
    return exists


def is_user_in_leaderboard(user_name: str) -> bool:
    # Get a database connection
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Query to check if the user exists in the leaderboard_table
        cursor.execute(
            """
            SELECT 1 FROM leaderboard_table
            WHERE user_name = %s
            """,
            (user_name,)
        )
        # Fetch one result
        result = cursor.fetchone()

        # If result is found, user exists in the leaderboard
        return result is not None

    except Exception as e:
        print(f"An error occurred while checking the leaderboard: {e}")
        return False

    finally:
        cursor.close()
        conn.close()


def has_user_answered_challenge(user_name: str, challenge_id: str) -> bool:
    # Get a database connection
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Query to check if the user has correctly answered the specified challenge
        cursor.execute(
            """
            SELECT 1 FROM leaderboard_table
            WHERE user_name = %s AND challenge_id = %s
            """,
            (user_name, challenge_id)
        )
        # Fetch one result
        result = cursor.fetchone()

        # If result is found, user has answered the challenge correctly
        return result is not None

    except Exception as e:
        print(f"An error occurred while checking the leaderboard: {e}")
        return False

    finally:
        cursor.close()
        conn.close()


def calculate_score(challenge_id):
    print(f'score calculation starts')
    conn = get_db_connection()
    cursor = conn.cursor()
    delta = 1
    try:
        # Code for database operations
        cursor.execute("""
            SELECT max_points, time
            FROM challenges_table
            WHERE challenge_id = %s
        """, (challenge_id,))

        result = cursor.fetchone()
        if result is None:
            # print("Challenge not found.")
            return "Challenge not found."

        max_score, challenge_time = result
        print(f'time in challenges_table {challenge_time}')
        if challenge_time is None:
            return max_score
        current_time = datetime.datetime.now()

        # Calculate time difference in seconds
        time_difference = (current_time - challenge_time).total_seconds()

        # Calculate the assigned score
        assigned_score = max(max_score / 2, max_score - int(delta * time_difference))
        print(f'score calculation ends')
        return assigned_score
        conn.commit()

    except Exception as e:
        print(f"An error occurred in calculate_score function: {e}")
        conn.rollback()  # Rollback if any error occurs

    finally:
        # Ensure cursor and connection are closed
        cursor.close()
        conn.close()


def check_challenge_status(challenge_id):
    if not is_valid_challenge_id(challenge_id):
        return "Invalid challenge ID."
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
                "SELECT status FROM challenges_table WHERE challenge_id = %s",
                (challenge_id,)
            )
        status = cursor.fetchone()[0]
        print(f'checking status success')
        if status != 1:
            return 0
        else:
            return 1
    except Exception as e:
        conn.rollback()
        return f"An error occurred: {e}"

    finally:
        cursor.close()
        conn.close()


def submit_flag(user_name: str, challenge_id: str, flag: str):
    if not is_valid_challenge_id(challenge_id):
        return "Invalid challenge ID.", None
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Ensure user exists in users_table, insert if not present
        cursor.execute(
            "SELECT 1 FROM users_table WHERE user_name = %s",
            (user_name,)
        )
        user_exists = cursor.fetchone()
        if not user_exists:
            print(f'{user_name} added')
            cursor.execute(
                """  
                INSERT INTO users_table (user_name, last_active, points, rank, correct_submissions, incorrect_submissions)
                VALUES (%s, NOW(), 0, 0, 0, 0)
                """,
                (user_name,)
            )

        # Check challenge status and answer
        cursor.execute(
            "SELECT answer, status, max_points, time FROM challenges_table WHERE challenge_id = %s",
            (challenge_id,)
        )
        result = cursor.fetchone()
        print(result)
        if not result:
            return "Challenge not found.", None

        answer, status, max_points, first_correct_time = result
        if status != 1:
            return "Challenge is currently closed.", None

        print(answer, status, max_points, first_correct_time)
        # max_points = datetime.time

        print(f'db {flag}, {answer}')
        is_correct = (flag == answer)

        # Update leaderboard if correct
        if is_correct:
            # Check and update the first correct submission time
            if first_correct_time is None:
                cursor.execute(
                    "UPDATE challenges_table SET time = NOW() WHERE challenge_id = %s",
                    (challenge_id,)
                )

            # cursor.execute(
            #     "SELECT COUNT(*) + 1 FROM leaderboard_table WHERE challenge_id = %s",
            #     (challenge_id,)
            # )
            # submission_order = cursor.fetchone()[0]
            #
            # cursor.execute(
            #     """
            #     INSERT INTO leaderboard_table (challenge_id, user_name, submission_order, points)
            #     VALUES (%s, %s, %s, %s)
            #     """,
            #     (challenge_id, user_name, submission_order, max_points)
            # )

            # Update user stats if correct and not answered the same question earlier
            max_points = calculate_score(challenge_id=challenge_id)
            if not has_user_answered_challenge(user_name=user_name, challenge_id=challenge_id):
                cursor.execute(
                    """
                    UPDATE users_table
                    SET points = points + %s, correct_submissions = correct_submissions + 1
                    WHERE user_name = %s
                    """,
                    (max_points, user_name)
                )
        else:
            if not has_user_answered_challenge(user_name=user_name, challenge_id=challenge_id):
                cursor.execute(
                    "UPDATE users_table SET incorrect_submissions = incorrect_submissions + 1 WHERE user_name = %s",
                    (user_name,)
                )

        cursor.execute(
                    "UPDATE users_table SET last_active = NOW() WHERE user_name = %s",
                    (user_name,)
                )

        # Record submission
        cursor.execute(
            """
            INSERT INTO submissions_table (user_name, challenge_id, time, flag_submitted, verdict, points_awarded)
            VALUES (%s, %s, NOW(), %s, %s, %s) RETURNING id
            """,
            (user_name, challenge_id, flag, is_correct, max_points if is_correct else 0)
        )
        print(f'added to submitted ')
        submission_id = cursor.fetchone()[0]

        # Update score table
        if not has_user_answered_challenge(user_name=user_name, challenge_id=challenge_id):
            cursor.execute(
                """
                INSERT INTO scores_table (username, challenge_id, score)
                VALUES (%s, %s, %s)
                ON CONFLICT (username, challenge_id)
                DO UPDATE SET score = scores_table.score + EXCLUDED.score
                """,
                (user_name, challenge_id, max_points if is_correct else 0)
            )

        conn.commit()
        print('submit function done')
        return "Flag submission recorded successfully.", is_correct

    except Exception as e:
        conn.rollback()
        return f"An error occurred in submit_flag function: {e}", None

    finally:
        cursor.close()
        conn.close()


def add_to_leaderboard(challenge_id: str, user_name: str):
    if not is_valid_challenge_id(challenge_id):
        return "Invalid challenge ID."

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # cursor.execute("SELECT max_points FROM challenges_table WHERE challenge_id = %s", (challenge_id,))
        # max_points = cursor.fetchone()[0]
        max_points = calculate_score(challenge_id=challenge_id)
        cursor.execute("SELECT COUNT(*) + 1 FROM leaderboard_table WHERE challenge_id = %s", (challenge_id,))
        submission_order = cursor.fetchone()[0]

        cursor.execute(
            """
            INSERT INTO leaderboard_table (challenge_id, user_name, submission_order, points)
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
    if not is_valid_challenge_id(challenge_id):
        return "Invalid challenge ID."

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT user_name, points
        FROM leaderboard_table
        WHERE challenge_id = %s
        ORDER BY submission_order ASC LIMIT 5
        """,
        (challenge_id,)
    )
    leaderboard = cursor.fetchall()
    conn.close()
    return leaderboard if leaderboard else []


def get_overall_leaderboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT user_name, SUM(points) AS total_score
        FROM leaderboard_table
        GROUP BY user_name
        ORDER BY total_score DESC
        LIMIT 5
        """
    )
    overall_leaderboard = cursor.fetchall()
    conn.close()
    return overall_leaderboard if overall_leaderboard else []


def get_user_score(user_name: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT SUM(points) FROM leaderboard_table WHERE user_name = %s", (user_name,)
    )
    total_score = cursor.fetchone()[0] or 0
    conn.close()
    return total_score


def get_challenge_info(challenge_id: str):
    if not is_valid_challenge_id(challenge_id):
        return "Invalid challenge ID."

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT c.challenge_id, c.name, c.max_points,
               CASE WHEN c.status = 1 THEN 'Open' ELSE 'Closed' END AS status,
               c.difficulty, c.description, c.file_link, c.hints_visible,
               SUM(CASE WHEN s.verdict = TRUE THEN 1 ELSE 0 END) AS correct_submissions,
               COUNT(s.id) AS total_submissions
        FROM challenges_table c
        LEFT JOIN submissions_table s ON c.challenge_id = s.challenge_id
        WHERE c.challenge_id = %s
        GROUP BY c.challenge_id
        """,
        (challenge_id,)
    )
    challenge_info = cursor.fetchone()
    conn.close()

    if not challenge_info:
        return "Challenge not found."

    challenge_id, name, max_points, status, difficulty, description, file_link, hints_visible, correct_subs, total_subs = challenge_info

    if status == 'Closed':
        return "This challenge is currently closed."

    hints_formatted = (
        "\n".join([f"🔎 Hint {i + 1}: {hint}" for i, hint in enumerate(hints_visible)])
        if hints_visible else "🔎 No hints available."
    )

    formatted_info = [
        "🔍 Challenge Details",
        "─────────────────────────────",
        f"🆔 ID: {challenge_id}",
        f"📝 Name: {name}",
        f"🏅 Points: {max_points} pts",
        f"🎯 Difficulty: {difficulty}",
        "⏳ Time Limit: None",
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
        FROM challenges_table
        WHERE status = 1
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
        cursor.execute("DELETE FROM leaderboard_table WHERE user_name = %s", (user_name,))
        cursor.execute("DELETE FROM submissions_table WHERE user_name = %s", (user_name,))
        cursor.execute("DELETE FROM users_table WHERE user_name = %s", (user_name,))
        cursor.execute("DELETE FROM scores_table WHERE user_name = %s", (user_name,))
        conn.commit()
        return "User data deleted successfully."

    except Exception as e:
        conn.rollback()
        return f"Error deleting user data: {e}"

    finally:
        cursor.close()
        conn.close()


def get_user_solved_questions(user_name: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT l.challenge_id, l.points
        FROM leaderboard_table l
        WHERE l.user_name = %s
        ORDER BY l.submission_order ASC
        """,
        (user_name,)
    )
    solved_challenges = cursor.fetchall()
    conn.close()
    return solved_challenges

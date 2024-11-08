import random

# from database import add_to_leaderboard, get_leaderboard, get_user_score, update_user_score, get_challenge_info
# from database import delete_user_info, get_all_challenges, get_overall_leaderboard, get_user_solved_questions

from new_db_ import submit_flag, add_to_leaderboard, get_leaderboard, get_user_score, get_challenge_info, is_user_in_leaderboard
from new_db_ import delete_user_info, get_all_challenges, get_overall_leaderboard, get_user_solved_questions, is_valid_challenge_id
from new_db_ import has_user_answered_challenge, check_challenge_status


def get_response(interaction, challenge_id=None, flag=None, text=None) -> str:
    # Use the command name from the interaction
    command_name = interaction.command.name
    print(f'command name {command_name}')
    # Handle different commands based on the name
    if command_name == 'leaderboard':
        overall_leaderboard = get_overall_leaderboard()
        if overall_leaderboard:
            return '\n'.join([f"{i + 1}. {entry[0]} - {entry[1]} points" for i, entry in enumerate(overall_leaderboard)])
        else:
            return 'No scores available yet.'

    elif command_name == 'challengeleaderboard':
        if challenge_id:
            leaderboard = get_leaderboard(challenge_id)
            if leaderboard == "Invalid challenge ID.":
                return "The specified challenge ID does not exist. Please verify the challenge ID."
            elif leaderboard:
                return leaderboard
            else:
                return 'No one has guessed the correct answer yet.'
        return 'Challenge ID not provided.'

    elif command_name == 'myhacks':
        solved_questions_with_scores = get_user_solved_questions(interaction.user.name)
        if solved_questions_with_scores:
            challenges_list = '\n'.join(
                [f"ID: {question} | 🏅 Points: {points}" for question, points in solved_questions_with_scores]
            )
            return (
                f"😎  Hacks by @{interaction.user.name}\n"
                f"─────────────────────────────\n"
                f"🔑 Challenges Completed:\n"
                f"{challenges_list}"
            )
        else:
            return f"No challenges completed by @{interaction.user.name} yet."

    elif command_name == 'myscore':
        score = get_user_score(interaction.user.name)
        return f"{interaction.user.name}, your current score is: {score} points."

    elif command_name == 'challenges':
        challenges = get_all_challenges()
        return challenges

    elif command_name == 'info':
        challenge_info = get_challenge_info(challenge_id)
        if challenge_info == "Invalid challenge ID.":
            return "The specified challenge ID is invalid. Please check and try again."
        return challenge_info

    elif command_name == 'submit':
        try:
            if text == 'is_valid_challenge_id':
                if not is_valid_challenge_id(challenge_id):
                    return "Invalid challenge ID."
                elif not check_challenge_status(challenge_id=challenge_id):
                    return "status is closed."
                else:
                    return
            # Call the submit_flag function
            submission_result, is_correct, max_points = submit_flag(interaction.user.name, challenge_id, flag)
            print(f'responses {flag}')
            print(f'responses {submission_result}')
            if submission_result == "Challenge not found.":
                return "The specified challenge ID does not exist. Please verify the challenge ID."
            elif submission_result == "Challenge is currently closed.":
                return f"⚠️ Sorry, {interaction.user.name}, but this challenge is currently closed for submissions."
            elif submission_result == "Flag submission recorded successfully.":
                print(f'start')
                leaderboard = get_leaderboard(challenge_id)
                print(f'leaderboard {leaderboard}')
                # user_in_leaderboard = interaction.user.name in [entry[interaction.user.name] for entry in leaderboard]
                user_in_leaderboard = has_user_answered_challenge(interaction.user.name, challenge_id=challenge_id)
                print(f'end')
                if user_in_leaderboard:
                    if is_correct:
                        return "You've already guessed this question correctly!"
                    else:
                        return "Your guess is wrong now but, You've already guessed this question correctly! "
                else:
                    if is_correct:
                        added_to_leaderboard = add_to_leaderboard(challenge_id=challenge_id, max_points=max_points, user_name=interaction.user.name)
                        if added_to_leaderboard != "Added to leaderboard.":
                            print(f'error in add_to_leaderboard function')
                        submission_order = len(leaderboard) + 1
                        return f"🎉 Congrats {interaction.user.name}, you guessed it right! 🎉\n" \
                               f"You are submission number {submission_order} for this challenge."
                    else:
                        # Random incorrect flag messages
                        incorrect_flag_responses = [
                            f"❌ Oops, {interaction.user.name}! That’s not the correct flag 😬",
                            f"❌ Close, {interaction.user.name}, but not quite! That flag’s a miss. 😅",
                            f"⚠️ Uh-oh, {interaction.user.name}! That flag doesn’t fit. 👀",
                            f"💀 Mission failed, {interaction.user.name}! That flag doesn’t respawn here. 🕹️",
                            f"❌ Whoops, {interaction.user.name}! That flag is so far off it might be from another planet! 🪐"
                        ]
                        return random.choice(incorrect_flag_responses)
            else:
                pass

        except Exception as e:
            return f"An error occurred while processing your submission: {e}"

    elif command_name == 'deletemyinfo':
        delete_user_info(interaction.user.name)
        return f"{interaction.user.name}, your information has been deleted successfully."

    # For other commands not processed here
    unknowns = [
        "💥 Command failed!\nYou’ve taken damage! 🛡️\nBut don’t worry! Revive your command skills or try \\help!",
        "🚫 Oops! That command didn’t work.\nDouble-check your input, and give it another go! 🧐\nType \\help for a list of available commands.",
        "🦕 Roar! That command was extinct!\nPrehistoric errors happen to the best of us!\nDust off your command skills or try \\help! 🌋",
        "🐢 Oops! Slow down there!\nThat command didn’t make it out of its shell.\nTry again, and remember: even turtles win races! 🏁 or use \\help",
        "🕵️‍♀️ Case Closed!\nThat command is a mystery we can’t solve.\nConsult the evidence (\\help) and crack the code again! 🔍",
        "🌌 Command lost in space!\nThat one didn’t launch successfully.\nCheck your coordinates and try again, space explorer, or use \\help! 🚀"
    ]
    return random.choice(unknowns)

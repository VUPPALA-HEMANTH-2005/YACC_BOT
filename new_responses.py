import random

# from database import add_to_leaderboard, get_leaderboard, get_user_score, update_user_score, get_challenge_info
# from database import delete_user_info, get_all_challenges, get_overall_leaderboard, get_user_solved_questions

from new_db import submit_flag, add_to_leaderboard, get_leaderboard, get_user_score, get_challenge_info
from new_db import delete_user_info, get_all_challenges, get_overall_leaderboard, get_user_solved_questions

# answers = {
#     '1C1': 'secret1',
#     '1C2': 'secret2',
#     '1C3': 'secret3'
# }


def get_response(interaction, challenge_id=None, flag=None) -> str:
    # Use the command name from the interaction
    command_name = interaction.command.name

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
            if leaderboard:
                return leaderboard
                # return '\n'.join([f"{i + 1}. {user}" for i, user in enumerate(leaderboard)])
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
        # return f"Challenges:\n{challenges}\nFirst guess gets 6 points, second gets 4 points, third 3 points, " \
        #        f"and 2 points thereafter."
        return challenges
    elif command_name == 'info':
        challenge_info = get_challenge_info(challenge_id)
        return challenge_info

    elif command_name == 'submit':
        try:
            # Call the submit_flag function
            submission_result = submit_flag(interaction.user.name, challenge_id, flag)

            # Handle submission outcomes based on `submit_flag` results
            if submission_result == "Challenge not found.":
                return "The specified challenge ID does not exist. Please verify the challenge ID."
            elif submission_result == "Challenge is currently closed.":
                return f"⚠️ Sorry, {interaction.user.name}, but this challenge is currently closed for submissions."
            elif "Flag submission recorded successfully." in submission_result:
                leaderboard = get_leaderboard(challenge_id)
                user_in_leaderboard = interaction.user.name in [entry['username'] for entry in leaderboard]

                if user_in_leaderboard:
                    return "You've already guessed this question correctly!"
                else:
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
        except KeyError:
            return 'Invalid Challenge ID'
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

    # return "Unknown command"

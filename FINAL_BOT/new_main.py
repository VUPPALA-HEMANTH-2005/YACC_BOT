import os
import asyncio
from dotenv import load_dotenv
import discord
from discord import app_commands
from discord.ext import commands
from new_responses import get_response

# Load the Discord token from the environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# 1286287432542847006
# Define the permitted channels
channels_permitted = {1290344770442629183, 1286287432542847006}
# channels_permitted = {1286287432542847006}

# Create the bot instance with all intents
bot = commands.Bot(command_prefix='/', intents=discord.Intents.all())

# Sync the commands with Discord API when bot is ready


@bot.event
async def on_ready():
    await bot.tree.sync()  # Sync slash commands
    print(f'{bot.user} is now running! Slash commands have been synced.')

#
@bot.tree.command(name='whatscooking', description='first free flag')
async def whatscooking(interaction: discord.Interaction):
    if interaction.channel.id not in channels_permitted:
        # await interaction.response.send_message("This channel is not permitted.", ephemeral=True)
        await interaction.response.send_message("This channel is not permitted.", ephemeral=True)
        return

    try:
        demo = 'Here is your flag `flag{H4ck_th6_m4tr1x}`. Type `/submit 1C0` to submit'
        await interaction.response.send_message(demo, ephemeral=True)
        return
    except Exception as e:
        await interaction.response.send_message(f'exception {e}', ephemeral=True)
        return


# Slash command for /help
@bot.tree.command(name='help', description='Displays available commands')
async def help_command(interaction: discord.Interaction):
    if interaction.channel.id not in channels_permitted:
        # await interaction.response.send_message("This channel is not permitted.", ephemeral=True)
        await interaction.response.send_message("This channel is not permitted.", ephemeral=True)
        return
    help_message = (
        "🆘 Command List\n"
        "─────────────────────────────\n"
        "✨ /leaderboard - Points table for top scores! See who’s leading the charge!\n\n"
        "📊 /challengeleaderboard <flag-id> - Scoreboard for a particular challenge! Check out how everyone’s performing!\n\n"
        "🏆 /myscore - Individual score report! Find out how you stack up against the competition!\n\n"
        "📝 /myhacks - List of challenges you’ve solved or tried! Review your victories and learn from your attempts!\n\n"
        "📜 /challenges - List of active problems! Discover the challenges waiting for you to conquer!\n\n"
        "🚀 /submit <flag-id> - Submit your flag for evaluation! Give it your best shot!\n\n"
        "ℹ️ /info <flag-id> - Get detailed descriptions of the challenges! Learn what it takes to solve them!\n"
        "─────────────────────────────\n"
        "🎉 Dive in and start exploring! If you have any questions, just ask!"
    )

    await interaction.response.send_message(help_message, ephemeral=True)
    return


# Slash command for overall leaderboard
@bot.tree.command(name='leaderboard', description='Display the overall leaderboard')
async def leaderboard(interaction: discord.Interaction):
    if interaction.channel.id not in channels_permitted:
        await interaction.response.send_message("This channel is not permitted.", ephemeral=True)
        return

    # Retrieve the leaderboard response using get_response
    response = get_response(interaction)
    await interaction.response.send_message(response)


# Slash command for /myHacks
@bot.tree.command(name='myhacks', description='Shows the list of challenges completed by the user')
async def myhacks_command(interaction: discord.Interaction):
    # user = interaction.user.name
    # Assuming handle_myhacks_command is already defined in new_responses.py
    # Check if the channel is permitted
    if interaction.channel.id not in channels_permitted:
        # await interaction.response.send_message("This channel is not permitted.", ephemeral=True)
        await interaction.response.send_message("This channel is not permitted.", ephemeral=True)
        return
    else:
        response = get_response(interaction)
        await interaction.response.send_message(response)
        return


# Slash command for specific challenge leaderboard
@bot.tree.command(name='challengeleaderboard', description='Display leaderboard for a specific challenge')
async def challenge_leaderboard(interaction: discord.Interaction, flag_id: str):
    if interaction.channel.id not in channels_permitted:
        await interaction.response.send_message("This channel is not permitted.", ephemeral=True)
        return

    # Retrieve the challenge leaderboard response
    response = get_response(interaction, challenge_id=flag_id)
    await interaction.response.send_message(response)
    return


# Slash command for the user's individual score
@bot.tree.command(name='myscore', description='Get your individual score')
async def my_score(interaction: discord.Interaction):
    if interaction.channel.id not in channels_permitted:
        await interaction.response.send_message("This channel is not permitted.", ephemeral=True)
        return

    # Retrieve the user's score using get_response
    response = get_response(interaction)
    await interaction.response.send_message(response)
    return


# Slash command for listing all active challenges
@bot.tree.command(name='challenges', description='Get the list of active challenges')
async def challenges(interaction: discord.Interaction):
    if interaction.channel.id not in channels_permitted:
        await interaction.response.send_message("This channel is not permitted.", ephemeral=True)
        return

    # Retrieve the list of challenges
    response = get_response(interaction)
    await interaction.response.send_message(response)
    return


@bot.tree.command(name='info', description='Exclusive information regarding a question')
async def challenge_info(interaction: discord.Interaction, flag_id: str):
    if interaction.channel.id not in channels_permitted:
        await interaction.response.send_message("This channel is not permitted.", ephemeral=True)
        return
    try:
        # Acknowledge the interaction immediately with a "thinking" response
        # await interaction.response.defer(thinking=True)

        # Retrieve the list of challenges
        response = get_response(interaction, challenge_id=flag_id)
        await interaction.response.send_message(response)
        return
        # Send the actual response as a follow-up message
        # await interaction.followup.send(response)
    except Exception as e:
        await interaction.response.send_message(f'{e}')
        return


@bot.tree.command(name='submit', description='Submit a flag for a challenge')
async def submit(interaction: discord.Interaction, flag_id: str):
    await interaction.response.defer(ephemeral=True)
    if interaction.channel.id not in channels_permitted:
        await interaction.followup.send("This channel is not permitted.", ephemeral=True)
        return
    # Check if the channel is permitted
    # if interaction.channel.id not in channels_permitted:
    #     # await interaction.response.send_message("This channel is not permitted.", ephemeral=True)
    #     await interaction.followup.send("This channel is not permitted.", ephemeral=True)
    #     return

    # Check if the challenge ID exists
    challenge_exists = get_response(interaction, challenge_id=flag_id, text="is_valid_challenge_id")
    if challenge_exists == "Invalid flag ID.":
        # Respond immediately if the flag_id is invalid
        # await interaction.response.send_message("Invalid challenge ID. Please check and try again.", ephemeral=True)
        await interaction.followup.send("Invalid flag ID. Please check and try again.", ephemeral=True)
        return
    elif challenge_exists == "status is closed.":
        status_closed = f"⚠️ Sorry, {interaction.user.name}, but this challenge is currently closed for submissions."
        # await interaction.response.send_message(status_closed, ephemeral=True)
        await interaction.followup.send(status_closed, ephemeral=True)
        return
    did_already_submitted = get_response(interaction, challenge_id=flag_id, text='did_already_submitted')
    if did_already_submitted == 'True':
        await interaction.followup.send("You've already guessed this question correctly!", ephemeral=True)
        return
    # If the challenge ID is valid, let the user know to check their DMs
    # await interaction.response.send_message("Check your DMs to submit the flag.", ephemeral=True)
    await interaction.followup.send("Check your DMs to submit the flag.", ephemeral=True)

    try:
        # Send a DM to the user asking for the flag input
        await interaction.user.send(f"Please enter the flag for challenge `{flag_id}`:")

        # Define a check function to ensure we only process the user's response in DM
        def check(msg):
            return msg.author == interaction.user and isinstance(msg.channel, discord.DMChannel)

        # Wait for the user’s response in their DM (timeout after 5 minutes)
        msg = await bot.wait_for("message", check=check, timeout=300)  # Timeout after 5 minutes

        # Validate the flag
        response = get_response(interaction, challenge_id=flag_id, flag=msg.content)

        # Send the validation result back to the user in their DM
        await interaction.user.send(response)
        print(response[0:8])
        if response[0:8] == "Congrats":
            announce_in_group = f"Congrats {interaction.user.name} for guessing the {flag_id} right! 🎉"
            await interaction.followup.send(announce_in_group)

    except discord.Forbidden:
        # Handle if the bot cannot send a DM due to user privacy settings
        await interaction.followup.send("I couldn't send you a DM. Please check your privacy settings.", ephemeral=True)
    except asyncio.TimeoutError:
        # Handle if the user doesn't respond within the timeout
        await interaction.user.send("Flag submission timed out. Please try again.")


# @bot.tree.command(name='deletemyinfo', description='Delete your information from the database')
# async def delete_my_info(interaction: discord.Interaction):
#     if interaction.channel.id not in channels_permitted:
#         await interaction.response.send_message("This channel is not permitted.", ephemeral=True)
#         return
#
#     # Handle user info deletion
#     response = get_response(interaction)
#     await interaction.response.send_message(response)


# Main function to run the bot
def main():
    bot.run(TOKEN)


if __name__ == '__main__':
    main()

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

# Define the permitted channels
channels_permitted = {1286287432542847006}

# Create the bot instance with all intents
bot = commands.Bot(command_prefix='/', intents=discord.Intents.all())

# Sync the commands with Discord API when bot is ready
@bot.event
async def on_ready():
    await bot.tree.sync()  # Sync slash commands
    print(f'{bot.user} is now running! Slash commands have been synced.')

# Slash command for /help
@bot.tree.command(name='help', description='Displays available commands')
async def help_command(interaction: discord.Interaction):
    help_message = (
        "/leaderboard - Points table for top scores\n"
        "/challengeleaderboard <challenge-id> - Scoreboard for the particular challenge\n"
        "/myscore - Individual score\n"
        "/myhacks - Solved/tried challenges\n"
        "/challenges - List of active problems\n"
        "/submit <challenge-id> <flag> - Let the user submit flag\n"
        "/info <challenge-id> - Gives the description of challenge name"
    )
    await interaction.response.send_message(help_message)

# Slash command for overall leaderboard
@bot.tree.command(name='leaderboard', description='Display the overall leaderboard')
async def leaderboard(interaction: discord.Interaction):
    if interaction.channel.id not in channels_permitted:
        await interaction.response.send_message("This channel is not permitted.", ephemeral=True)
        return

    # Retrieve the leaderboard response using get_response
    response = get_response(interaction, 'leaderboard')
    await interaction.response.send_message(response)

# Slash command for /myHacks
@bot.tree.command(name='myhacks', description='Shows the list of challenges completed by the user')
async def myhacks_command(interaction: discord.Interaction):
    # user = interaction.user.name
    # Assuming handle_myhacks_command is already defined in new_responses.py
    response = get_response(interaction)
    await interaction.response.send_message(response)
# Slash command for specific challenge leaderboard
@bot.tree.command(name='challengeleaderboard', description='Display leaderboard for a specific challenge')
async def challenge_leaderboard(interaction: discord.Interaction, challenge_id: str):
    if interaction.channel.id not in channels_permitted:
        await interaction.response.send_message("This channel is not permitted.", ephemeral=True)
        return

    # Retrieve the challenge leaderboard response
    response = get_response(interaction, f'leaderboard {challenge_id}')
    await interaction.response.send_message(response)

# Slash command for the user's individual score
@bot.tree.command(name='myscore', description='Get your individual score')
async def my_score(interaction: discord.Interaction):
    if interaction.channel.id not in channels_permitted:
        await interaction.response.send_message("This channel is not permitted.", ephemeral=True)
        return

    # Retrieve the user's score using get_response
    response = get_response(interaction, 'myscore')
    await interaction.response.send_message(response)

# Slash command for listing all active challenges
@bot.tree.command(name='challenges', description='Get the list of active challenges')
async def challenges(interaction: discord.Interaction):
    if interaction.channel.id not in channels_permitted:
        await interaction.response.send_message("This channel is not permitted.", ephemeral=True)
        return

    # Retrieve the list of challenges
    response = get_response(interaction, 'challenges')
    await interaction.response.send_message(response)


# @bot.tree.command(name='info', description='Exclusive information regarding a question')
# async def challenge(interaction: discord.Interaction,  challenge_id: str):
#     if interaction.channel.id not in channels_permitted:
#         await interaction.response.send_message("This channel is not permitted.", ephemeral=True)
#         return
#
#     # Retrieve the list of challenges
#     response = get_response(interaction, challenge_id,  'info')
#     await interaction.response.send_message(response)


@bot.tree.command(name='info', description='Exclusive information regarding a question')
async def challenge_info(interaction: discord.Interaction, challenge_id: str):
    if interaction.channel.id not in channels_permitted:
        await interaction.response.send_message("This channel is not permitted.", ephemeral=True)
        return

    # Acknowledge the interaction immediately with a "thinking" response
    await interaction.response.defer(thinking=True)

    # Retrieve the list of challenges
    response = get_response(interaction, challenge_id, 'info')

    # Send the actual response as a follow-up message
    await interaction.followup.send(response)

# # Slash command to submit a flag for a challenge
# @bot.tree.command(name='submit', description='Submit a flag for a challenge')
# async def submit(interaction: discord.Interaction, challenge_id: str, flag: str):
#     if interaction.channel.id not in channels_permitted:
#         await interaction.response.send_message("This channel is not permitted.", ephemeral=True)
#         return
#
#     # Handle the flag submission
#     response = get_response(interaction, challenge_id, flag)
#     await interaction.response.send_message(response, ephemeral=True)


# Slash command to initiate flag submission
@bot.tree.command(name='submit', description='Submit a flag for a challenge')
async def submit(interaction: discord.Interaction, challenge_id: str):
    if interaction.channel.id not in channels_permitted:
        await interaction.response.send_message("This channel is not permitted.", ephemeral=True)
        return

    # Send an initial message, informing the user to check their DMs
    await interaction.response.send_message("Check your DMs to submit the flag.")

    # Try to send a DM to the user to request the flag
    try:
        await interaction.user.send(f"Please enter the flag for challenge `{challenge_id}`:")

        # Define a check function for the bot to wait for the user's response in DM
        def check(msg):
            return msg.author == interaction.user and isinstance(msg.channel, discord.DMChannel)

        # Wait for the user’s response in their DM (timeout after 5 minutes)
        msg = await bot.wait_for("message", check=check, timeout=300)  # Timeout after 5 minutes

        # Pass the `flag` to `get_response` to check if it's correct
        response = get_response(interaction, challenge_id, msg.content)

        # Send the result back to the user in the DM
        await interaction.user.send(response)

    except discord.Forbidden:
        # If bot cannot send a DM due to user settings
        await interaction.response.send_message("I couldn't send you a DM. Please check your privacy settings.", ephemeral=True)
    except asyncio.TimeoutError:
        # If the user does not respond within the timeout
        await interaction.user.send("Flag submission timed out. Please try again.")


# Slash command to delete the user's information from the database
@bot.tree.command(name='deletemyinfo', description='Delete your information from the database')
async def delete_my_info(interaction: discord.Interaction):
    if interaction.channel.id not in channels_permitted:
        await interaction.response.send_message("This channel is not permitted.", ephemeral=True)
        return

    # Handle user info deletion
    response = get_response(interaction, 'delete my info')
    await interaction.response.send_message(response)

# Main function to run the bot
def main():
    bot.run(TOKEN)

if __name__ == '__main__':
    main()

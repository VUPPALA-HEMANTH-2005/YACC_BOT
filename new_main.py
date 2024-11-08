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
    response = get_response(interaction)
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
    response = get_response(interaction, challenge_id=challenge_id)
    await interaction.response.send_message(response)


# Slash command for the user's individual score
@bot.tree.command(name='myscore', description='Get your individual score')
async def my_score(interaction: discord.Interaction):
    if interaction.channel.id not in channels_permitted:
        await interaction.response.send_message("This channel is not permitted.", ephemeral=True)
        return

    # Retrieve the user's score using get_response
    response = get_response(interaction)
    await interaction.response.send_message(response)


# Slash command for listing all active challenges
@bot.tree.command(name='challenges', description='Get the list of active challenges')
async def challenges(interaction: discord.Interaction):
    if interaction.channel.id not in channels_permitted:
        await interaction.response.send_message("This channel is not permitted.", ephemeral=True)
        return

    # Retrieve the list of challenges
    response = get_response(interaction)
    await interaction.response.send_message(response)


@bot.tree.command(name='info', description='Exclusive information regarding a question')
async def challenge_info(interaction: discord.Interaction, challenge_id: str):
    if interaction.channel.id not in channels_permitted:
        await interaction.response.send_message("This channel is not permitted.", ephemeral=True)
        return

    # Acknowledge the interaction immediately with a "thinking" response
    await interaction.response.defer(thinking=True)

    # Retrieve the list of challenges
    response = get_response(interaction, challenge_id=challenge_id)

    # Send the actual response as a follow-up message
    await interaction.followup.send(response)


@bot.tree.command(name='submit', description='Submit a flag for a challenge')
async def submit(interaction: discord.Interaction, flag_id: str):
    await interaction.response.defer(ephemeral=True)
    # Check if the channel is permitted
    if interaction.channel.id not in channels_permitted:
        # await interaction.response.send_message("This channel is not permitted.", ephemeral=True)
        await interaction.followup.send("This channel is not permitted.", ephemeral=True)
        return

    # Check if the challenge ID exists
    challenge_exists = get_response(interaction, challenge_id=flag_id, text="is_valid_challenge_id")
    if challenge_exists == "Invalid challenge ID.":
        # Respond immediately if the flag_id is invalid
        # await interaction.response.send_message("Invalid challenge ID. Please check and try again.", ephemeral=True)
        await interaction.followup.send("Invalid challenge ID. Please check and try again.", ephemeral=True)
        return
    elif challenge_exists == "status is closed.":
        status_closed = f"⚠️ Sorry, {interaction.user.name}, but this challenge is currently closed for submissions."
        # await interaction.response.send_message(status_closed, ephemeral=True)
        await interaction.followup.send(status_closed, ephemeral=True)
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

    except discord.Forbidden:
        # Handle if the bot cannot send a DM due to user privacy settings
        await interaction.followup.send("I couldn't send you a DM. Please check your privacy settings.", ephemeral=True)
    except asyncio.TimeoutError:
        # Handle if the user doesn't respond within the timeout
        await interaction.user.send("Flag submission timed out. Please try again.")


@bot.tree.command(name='deletemyinfo', description='Delete your information from the database')
async def delete_my_info(interaction: discord.Interaction):
    if interaction.channel.id not in channels_permitted:
        await interaction.response.send_message("This channel is not permitted.", ephemeral=True)
        return

    # Handle user info deletion
    response = get_response(interaction)
    await interaction.response.send_message(response)


# Main function to run the bot
def main():
    bot.run(TOKEN)


if __name__ == '__main__':
    main()

import discord
from discord.ext import commands
from discord import app_commands
import requests
from dotenv import load_dotenv
import os


DISCORD_BOT_TOKEN = 'CHANGEME'

# Replace with your Flask app URL
FLASK_APP_URL = 'http://192.168.1.6:5008' #CHANGE TO YOUR URL

# Set up the bot with required intents
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot is ready as {bot.user}')
    try:
        await bot.tree.sync()
        print("Commands synced.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.tree.command(name="add_dodge", description="Add a dodge for a friend")
async def add_dodge(interaction: discord.Interaction, name: str, reason: str, date: str):
    """Add a dodge for a friend."""
    response = requests.post(f'{FLASK_APP_URL}/add_dodge', data={
        'name': name,
        'reason': reason,
        'date': date
    })
    if response.status_code == 200:
        await interaction.response.send_message(f'Dodge added for {name}.')
    else:
        await interaction.response.send_message(f'Error adding dodge: {response.text}')

@bot.tree.command(name="remove_dodge", description="Remove a dodge by ID")
async def remove_dodge(interaction: discord.Interaction, dodge_id: int, name: str, password: str):
    """Remove a dodge by ID."""
    response = requests.post(f'{FLASK_APP_URL}/delete_dodge', data={
        'dodge_id': dodge_id,
        'name': name,
        'password': password
    })
    if response.status_code == 200:
        await interaction.response.send_message(f'Dodge {dodge_id} removed for {name}.')
    else:
        await interaction.response.send_message(f'Error removing dodge: {response.text}')

@bot.tree.command(name="list_dodges", description="List all dodges for a user")
async def list_dodges(interaction: discord.Interaction, name: str):
    """List all dodges for a user."""
    response = requests.get(f'{FLASK_APP_URL}/friend/{name}')
    if response.status_code == 200:
        dodges = response.json()  
        if dodges:
            message = "\n".join([f"**ID:** {dodge['id']}, **Reason:** {dodge['reason']}, **Date:** {dodge['date']}" for dodge in dodges])
            await interaction.response.send_message(f"Dodges for {name}:\n{message}")
        else:
            await interaction.response.send_message(f"No dodges found for {name}.")
    else:
        await interaction.response.send_message(f"Error retrieving dodges: {response.text}")

# Run the bot
bot.run(DISCORD_BOT_TOKEN)

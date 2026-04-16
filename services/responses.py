# Module Imports
import math
import random
from datetime import timedelta
import discord
from services.api import api_post


# Handle response
async def handle_response(message: discord.Message) -> str:
    # Ignore if message is sent by bot
    if message.author.bot:
        return None

    # Handle response
    banned = await handle_banned_words(message)
    custom_response = await handle_custom_response(message)

    # Return response if either function returned anything
    if banned != None:
        return banned
    elif custom_response != None:
        return custom_response
    else:
        return None
    
# Handle banned words
async def handle_banned_words(message: discord.Message) -> str:
    # List of all banned words
    banned_words = []

    # If message contains any of these words, delete message and send message from bot
    if message.content.lower() in banned_words:
        return "DELETE"
    
# Handle custom response
async def handle_custom_response(message: discord.Message) -> str:
    # Randomly make users lose or gain aura
    random_number = random.randint(1, 100)
    if random_number >= 90:
        data = {"discord_id": str(message.author.id), "currency_id": 1, "mode": "Add","amount": 10, "note": "Random aura gain"}
        await api_post("/economy/balances/modify", body=data)
    elif random_number <= 5:
        data = {"discord_id": str(message.author.id), "currency_id": 1, "mode": "Subtract","amount": 10, "note": "Random aura loss"}
        await api_post("/economy/balances/modify", body=data)

    # Custom responses
    content = message.content.lower()
    if content == "wafflehipponuts":
        return "Congrats! You found this very obscure response!"

    elif "i made mee7" in content:
        if message.author.id == "725251028999602239":
            return "yea"
        else:
            return "No you didn't"


# Format a timedelta into seconds, hours, mins, days
async def format_timedelta(delta: timedelta) -> str:
    seconds = delta.total_seconds()
    if 0 < seconds < 59:
        return f"{math.floor(seconds)} seconds"
    elif 60 < seconds < 119:
        return f"{math.floor(seconds / 60)} minute"
    elif 120 < seconds < 3599:
        return f"{math.floor(seconds / 60)} minutes"
    elif 3600 < seconds < 7199:
        return f"{math.floor(seconds / 3600)} hour"
    elif 7200 < seconds < 86399:
        return f"{math.floor(seconds / 3600)} hours"
    elif 86400 < seconds < 172799:
        return f"{math.floor(seconds / 86399)} day"
    else:
        return f"{math.floor(seconds / 86400)} days"

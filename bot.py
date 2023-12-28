# Module imports
import random

import discord
from discord.ext import commands

from constants import Constants


# Main function
def run_bot():
    # Load constants and token
    CONSTANTS = Constants()
    TOKEN = CONSTANTS.TOKEN

    # Pick random bot activity
    activity_type = random.randint(1, 3)
    activity = None
    match activity_type:
        case 1:
            activity = activity=discord.Activity(type=discord.ActivityType.playing, name=random.choice(CONSTANTS.STATUSES_PLAYING))
        case 2:
            activity = activity=discord.Activity(type=discord.ActivityType.watching, name=random.choice(CONSTANTS.STATUSES_WATCHING))
        case 3:
            activity = activity=discord.Activity(type=discord.ActivityType.listening, name=random.choice(CONSTANTS.STATUSES_LISTENING))

    # Create client and set intents
    client = commands.Bot(command_prefix="$", intents=discord.Intents.all(), activity=activity)

    # On ready event
    # Runs when the bot starts up
    @client.event
    async def on_ready():
        try:
            # Add cogs & sync commands
            await client.load_extension("cogs.general")
            await client.load_extension("cogs.servers")
            await client.load_extension("cogs.music")
            await client.load_extension("cogs.fun")
            await client.tree.sync()

        # Handle exceptions
        except Exception as e:
            print(e)

        print("Startup complete")
        print(f"{client.user} is now running!")


    client.run(TOKEN)
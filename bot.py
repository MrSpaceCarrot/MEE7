# Module imports
import random
import logging

import discord
from discord.ext import commands

import services.logs as logs
from config import settings


# Main function
def run_bot():
    # Setup logging
    root_logger: logging.Logger = logs.setup_logger(logging.getLogger(''), settings.LOG_LEVEL_ROOT)
    discord_logger: logging.Logger = logs.setup_logger(logging.getLogger('discord'), settings.LOG_LEVEL_DISCORD)
    commands_logger: logging.Logger = logs.setup_logger(logging.getLogger('commands'), settings.LOG_LEVEL_COMMANDS)
    wavelink_logger: logging.Logger = logs.setup_logger(logging.getLogger('wavelink'), settings.LOG_LEVEL_WAVELINK)
    economy_logger: logging.Logger = logs.setup_logger(logging.getLogger('economy'), settings.LOG_LEVEL_ECONOMY)

    # Pick random bot activity
    activity_type: int = random.randint(1, 3)
    activity: discord.Activity = None
    match activity_type:
        case 1: activity = activity=discord.Activity(type=discord.ActivityType.playing, name=random.choice(settings.STATUSES_PLAYING))
        case 2: activity = activity=discord.Activity(type=discord.ActivityType.watching, name=random.choice(settings.STATUSES_WATCHING))
        case 3: activity = activity=discord.Activity(type=discord.ActivityType.listening, name=random.choice(settings.STATUSES_LISTENING))

    # Create client and set intents
    client = commands.Bot(command_prefix="$", intents=discord.Intents.all(), activity=activity)

    # On ready event, runs when the bot starts up
    @client.event
    async def on_ready():
        try:
            # Add cogs & sync commands
            await client.load_extension("cogs.general")
            await client.load_extension("cogs.servers")
            await client.load_extension("cogs.music")
            await client.load_extension("cogs.fun")
            await client.load_extension("cogs.economy")
            await client.tree.sync()

        # Handle exceptions
        except Exception as e:
            root_logger.error(e)

        root_logger.info(f"{client.user} is now running!")


    client.run(settings.BOT_TOKEN, log_handler=None)

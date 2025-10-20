# Module imports
import random
import logging
import aiohttp

import discord
from discord.ext import commands

import services.logs as logs
from config import settings


# Main Bot Class
class Bot(commands.Bot):
    def __init__(self):
         # Setup logging
        self.root_logger: logging.Logger = logs.setup_logger(logging.getLogger(''), settings.LOG_LEVEL_ROOT)
        self.discord_logger: logging.Logger = logs.setup_logger(logging.getLogger('discord'), settings.LOG_LEVEL_DISCORD)
        self.commands_logger: logging.Logger = logs.setup_logger(logging.getLogger('commands'), settings.LOG_LEVEL_COMMANDS)
        self.wavelink_logger: logging.Logger = logs.setup_logger(logging.getLogger('wavelink'), settings.LOG_LEVEL_WAVELINK)
        self.economy_logger: logging.Logger = logs.setup_logger(logging.getLogger('economy'), settings.LOG_LEVEL_ECONOMY)

        # Pick random bot activity
        activity_type: int = random.randint(1, 3)
        activity: discord.Activity = None
        match activity_type:
            case 1: activity = activity=discord.Activity(type=discord.ActivityType.playing, name=random.choice(settings.STATUSES_PLAYING))
            case 2: activity = activity=discord.Activity(type=discord.ActivityType.watching, name=random.choice(settings.STATUSES_WATCHING))
            case 3: activity = activity=discord.Activity(type=discord.ActivityType.listening, name=random.choice(settings.STATUSES_LISTENING))

        # Create aiohttp session
        self.session: aiohttp.ClientSession | None = None

        # Setup bot
        super().__init__(command_prefix="$", intents=discord.Intents.all(), activity=activity)

    async def setup_hook(self):
        # Create aiohttp session
        self.session = aiohttp.ClientSession()

        # Load commands
        try:
            await self.load_extension("cogs.general")
            await self.load_extension("cogs.servers")
            await self.load_extension("cogs.music")
            await self.load_extension("cogs.fun")
            await self.load_extension("cogs.economy")
            await self.tree.sync()

        # Handle exceptions
        except Exception as e:
            self.root_logger.error(e)

        # Log startup
        self.root_logger.info(f"{self.user} is now running!")

    async def close(self):
        # Close aiohttp session
        if self.session and not self.session.closed:
            await self.session.close()
        await super().close()


# Create Bot
client = Bot()
def run_bot():
    client.run(settings.BOT_TOKEN, log_handler=None)

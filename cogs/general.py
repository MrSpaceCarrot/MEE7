# Module Imports
import logging

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

from config import settings
import services.responses as responses


# Main cog class
class General(commands.Cog):

    # Class init
    def __init__(self, client):
        self.client = client
        self.commands_logger: logging.Logger = logging.getLogger("commands")

    # Message listener
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> str | None:
        # Return if message was sent by the bot
        if message.author.id in [762864416734969866, 1165935746167885834]: 
            return

        # Get response from responses and send it
        try:
            response: str = await responses.handle_response(message)
            
            # Return if no response was found, send response otherwise
            if response == None:
                return
            elif response == "DELETE":
                await message.channel.send("That message was a bit cringe init")
                await message.delete()
            else:
                await message.channel.send(response)
        
        # Handle exceptions
        except Exception as e:
            self.commands_logger.error(e)

    # Help command
    @app_commands.command(name="help", description="Lists all available commands")
    async def help(self, interaction: discord.Interaction) -> None:
        # Log Command
        self.commands_logger.info(f"/help executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Send embed
        embed: discord.Embed = discord.Embed(title="Commands", description="All commands, sorted by type", color=settings.BLUE)
        embed.add_field(name="**General**", value="/help, /activity", inline=False)
        embed.add_field(name="**Servers**", value="/server-list, /server-start, /server-help", inline=False)
        embed.add_field(name="**Music**", value="/connect, /disconnect, /play, /skip, /pause, /resume, /queue", inline=False)
        embed.add_field(name="**Fun**", value="/catpic, /shu-todoroki, /slander", inline=False)
        embed.add_field(name="**Economy**", value="/balance, /blackjack, /exchange, /gift, /job, /leaderboard, /transactions, /work", inline=False)
        embed.set_footer(text=settings.FOOTER)
        await interaction.response.send_message(embed=embed)

    # Activity command
    @app_commands.command(name="activity", description="Sets the bot's activity")
    @app_commands.describe(type="Activity", text="Activity text")
    @app_commands.choices(type=[Choice(name="Playing", value="Playing"), 
                                Choice(name="Watching", value="Watching"), 
                                Choice(name="Listening to", value="Listening")])
    async def activity(self, interaction: discord.Interaction, type: str, text: str) -> None:
        # Log Command
        self.commands_logger.info(f"/activity {type} {text} executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Determine activity type, set bot activity
        match type.lower():
            case "playing": await self.client.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=text))
            case "watching": await self.client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=text))
            case "listening": await self.client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=text))

        # Send embed
        embed: discord.Embed = discord.Embed(title="✅ Bot activity has been changed", description="", color=settings.BLUE)
        embed.set_footer(text=settings.FOOTER)
        await interaction.response.send_message(embed=embed)
        

# Setup function
async def setup(client):
    await client.add_cog(General(client))

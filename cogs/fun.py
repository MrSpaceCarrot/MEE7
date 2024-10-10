# Module Imports
import os
import requests
import json
import random
import logging

import discord
from discord import app_commands
from discord.ext import commands

from constants import Constants


# Main cog class
class Fun(commands.Cog):

    # Class init
    def __init__(self, client):
        self.client = client
        self.CONSTANTS = Constants()
        self.commands_logger: logging.Logger = logging.getLogger("commands")

    # Catpic command
    @app_commands.command(name="catpic", description="Generates a random cat image")
    async def catpic(self, interaction: discord.Interaction) -> None:
        # Log Command
        self.commands_logger.info(f"/catpic executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Defer interaction
        await interaction.response.defer()

        # Get image from catapi
        api_key: str = self.CONSTANTS.CATAPIKEY
        request_url: str = "https://api.thecatapi.com/v1/images/search?&api_key=" + api_key
        request: requests.Response = requests.get(request_url)
        final_url = json.loads(request.text)[0]["url"]

        # Send embed
        embed = discord.Embed(title="", color=self.CONSTANTS.GREEN)
        embed.set_image(url=final_url)
        await interaction.followup.send(embed=embed)

    # Slander command
    @app_commands.command(name="slander", description="Sends a randomly generated slander to a user")
    @app_commands.describe(user="User that you want MEE7 to slander")
    async def slander(self, interaction: discord.Interaction, user: str) -> None:
        # Log Command
        self.commands_logger.info(f"/slander executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Defer interaction
        await interaction.response.defer()

        # Get insult from evilinsultapi and send
        request: requests.Response = requests.get("https://evilinsult.com/generate_insult.php?lang=en&type=json")
        insult = json.loads(request.text)["insult"]
        message: str = user + ", " + insult
        await interaction.followup.send(message)

    # Shu Todoroki command
    @app_commands.command(name="shu-todoroki", description="Shu Todoroki")
    async def insult(self, interaction: discord.Interaction) -> None:
        # Log Command
        self.commands_logger.info(f"/shu-todoroki executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Defer interaction
        await interaction.response.defer()

        # Get list of images, send random one
        images: list[str] = os.listdir("./shu-todoroki")
        image: int = random.randint(0, (len(images) - 1))
        await interaction.followup.send(file=discord.File(f'./shu-todoroki/{image}.png'))
        

# Setup function
async def setup(client):
    await client.add_cog(Fun(client))
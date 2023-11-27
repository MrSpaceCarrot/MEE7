# Module Imports
import os
import requests
import json
import re
import random

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

    # Catpic command
    @app_commands.command(name="catpic", description="Generates a random cat image")
    async def catpic(self, interaction: discord.Interaction) -> None:
        # Defer interaction
        await interaction.response.defer()

        # Get image from catapi
        api_key = self.CONSTANTS.CATAPIKEY
        request_url = "https://api.thecatapi.com/v1/images/search?&api_key=" + api_key
        request = requests.get(request_url)
        final_url = json.loads(request.text)[0]["url"]

        # Create embed
        embed = discord.Embed(title="", color=self.CONSTANTS.GREEN)
        embed.set_image(url=final_url)

        # Send embed
        print(f"/catpic executed by {interaction.user} in {interaction.guild} #{interaction.channel}")
        await interaction.followup.send(embed=embed)

    # Insult command
    @app_commands.command(name="insult", description="Sends a randomly generated insult to a user")
    @app_commands.describe(user="User that you want MEE7 to insult")
    async def insult(self, interaction: discord.Interaction, user: str) -> None:
        # Defer interaction
        await interaction.response.defer()

        # Get insult from evilinsultapi
        request = requests.get("https://evilinsult.com/generate_insult.php?lang=en&type=json")
        insult = json.loads(request.text)["insult"]
        message = user + ", " + insult

        # Send insult
        print(f"/insult executed by {interaction.user} in {interaction.guild} #{interaction.channel}")
        await interaction.followup.send(message)

    # Frame command
    @app_commands.command(name="frame", description="Generates a fake discord screenshot")
    @app_commands.describe(user="User who you want to say the message", message="Message that you want the user to say")
    async def frame(self, interaction: discord.Interaction, user: str, message: str) -> None:
        # Defer interaction
        await interaction.response.defer()

        try:
            # Get username from ping
            ping = interaction.data["options"][0]["value"]
            user_id_match = re.match(r"<@!?(\d+)>", ping)
            user_id = int(user_id_match.group(1))
            member = interaction.guild.get_member(user_id)
            displayname = member.display_name

            # Get highest role color
            highest_role = member.top_role
            role_color = highest_role.color

            # Download user's avatar
            avatar_url = member.avatar.url
            img_data = requests.get(avatar_url).content
            with open('pfp.png', 'wb') as handler:
                handler.write(img_data)

            # Generate image
            os.system(f'node nodejs/generatescreenshot.js "{displayname}" "[{role_color.r}, {role_color.g}, {role_color.b}]" "{message}"')
            
            # Send image
            await interaction.followup.send(file=discord.File('output.png'))
        except Exception as e:
            print(e)
            # If error occured, ping must be invalid, so error should be shown
            title = f"❌ {user} is not a valid user"
            description = "Please ping a specific user when using this command"
            embed_color = self.CONSTANTS.RED

            embed = discord.Embed(title=title, description=description, color=embed_color)
            await interaction.followup.send(embed=embed)
        
        # Log command
        print(f"/frame executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Delete leftover files
        if os.path.exists("pfp.png"):
            os.remove("pfp.png")
        if os.path.exists("output.png"):
            os.remove("output.png")

    # Shu Todoroki command
    @app_commands.command(name="shu-todoroki", description="Shu Todoroki")
    async def insult(self, interaction: discord.Interaction) -> None:
        # Defer interaction
        await interaction.response.defer()

        # Get list of images
        images = os.listdir("./shu-todoroki")
        image = random.randint(0, (len(images) - 1))

        # Send image
        print(f"/shu-todoroki executed by {interaction.user} in {interaction.guild} #{interaction.channel}")
        await interaction.followup.send(file=discord.File(f'./shu-todoroki/{image}.png'))
        

# Setup function
async def setup(client):
    await client.add_cog(Fun(client))
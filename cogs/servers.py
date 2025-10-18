# Module Imports
import logging

import discord
from discord import app_commands
from discord.ext import commands

from config import settings
from services.api import api_get, api_post


# Main cog class
class Servers(commands.Cog):

    # Class init
    def __init__(self, client):
        self.client = client
        self.commands_logger: logging.Logger = logging.getLogger("commands")

    # Server List Command
    @app_commands.command(name="server-list", description="Lists all available servers you can start up")
    async def serverlist(self, interaction: discord.Interaction) -> None:
        # Log Command
        self.commands_logger.info(f"/server-list executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Defer interaction
        await interaction.response.defer()

        # Define variables for embed
        title: str = f"❌ Error getting server list'"
        description: str = ""
        embed_color: discord.Color = settings.RED

        # Break out of loop if failure occurs
        success: bool = True
        while success:
            # Get server categories from api
            categories_response = api_get(f"/servers/categories", interaction.user.id)
            categories_content = categories_response.json()

            # If categories were not successfully gotten
            if not categories_response.ok:
                if categories_content["detail"]:
                    description = categories_content["detail"]
                    self.commands_logger.debug(f"Cannot get server list, {categories_response.status_code}")
                success = False

            # Get servers from api
            servers_response = api_get(f"/servers?order_by=id", interaction.user.id)
            servers_content = servers_response.json()

            # If servers were not successfully gotten
            if not servers_response.ok:
                if servers_content["detail"]:
                    description = categories_content["detail"]
                    self.commands_logger.debug(f"Cannot get servers, {servers_response.status_code}")
                success = False

            # If all information was successfully gotten, format embed
            embed: discord.Embed = discord.Embed(title="📜 Server List", description="All servers that can be run with the /start-server command. Use /server-help to find out more about each server", color=settings.BLUE)

            for category in categories_content["items"]:
                category_servers = []
                for server in servers_content["items"]:
                    if server["category_id"] == category["id"]:
                        category_servers.append(server["display_name"])
                embed.add_field(name=f"**{category['name']}**", value=", ".join(category_servers), inline=False)
            break
        
        if not success:
            embed: discord.Embed = discord.Embed(title=title, description=description, color=embed_color)
        
        # Send embed
        embed.set_footer(text=settings.FOOTER)
        await interaction.followup.send(embed=embed)

    # Start Server Command
    @app_commands.command(name="server-start", description="Starts a specified server")
    @app_commands.describe(server="Server name")
    async def serverstart(self, interaction: discord.Interaction, server: str) -> None:
        # Log Command
        self.commands_logger.info(f"/server-start executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Defer interaction
        await interaction.response.defer()

        # Define variables for embed
        description: str = ""
        
        # Attempt to start server through api
        response = api_post(f"/servers/start/{server.lower()}", interaction.user.id)
        content = response.json()

        if response.ok:
            title = f"✅ {response.json()}"
            embed_color = settings.GREEN
            self.commands_logger.debug("Successfully starting server")
        else:
            title = f"❌ Error starting server '{server}'"
            embed_color: discord.Color = settings.RED
            if content["detail"]:
                description = content["detail"]
            self.commands_logger.debug(f"Cannot start server, {response.status_code}")

        # Send embed
        embed: discord.Embed = discord.Embed(title=title, description=description, color=embed_color)
        embed.set_footer(text=settings.FOOTER)
        await interaction.followup.send(embed=embed)

    # Server help command
    @app_commands.command(name="server-help", description="Lists info about a specified server")
    @app_commands.describe(server="Server name")
    async def serverhelp(self, interaction: discord.Interaction, server: str) -> None:
        # Log Command
        self.commands_logger.info(f"/server-help executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Defer interaction
        await interaction.response.defer()

        # Define variables for embed
        description: str = ""

        # Get server from api
        response = api_get(f"/servers/{server.lower()}", interaction.user.id)
        content = response.json()

        if response.ok:
            embed: discord.Embed = discord.Embed(title=f"{content['emoji']} {content['display_name']}", description=content['description'], color=settings.BLUE)
            embed.add_field(name="**💻 Version**", value=f"{content['version']} {content['modloader']}", inline=False)
            embed.add_field(name="**✉️ How To Join**", value=content['domain'], inline=False)

            if content['modloader'] != "Vanilla":
                if content['modconditions'] != None:
                    embed.add_field(name="**⏬ Modpack Download: **", value=f"[{content['modconditions']}]({content['moddownload']})", inline=False)
                else:
                    embed.add_field(name="**📜 Modlist: **", value=f"{content['modlist']}", inline=False)
                    embed.add_field(name="**⏬ Modpack Download: **", value=f"[Google drive link]({content['moddownload']})", inline=False)

            if not content['is_active']:
                embed.add_field(name="**❗ Activity**", value="This server has been inactive for a long time, and can be considered dead", inline=False)

            if content["is_running"]:
                embed.add_field(name="**🟢 Status**", value="This server is currently online", inline=False)
            else:
                embed.add_field(name="**🔴 Status**", value="This server is currently offline", inline=False)

            self.commands_logger.debug("Successfully returned server information")
            
        else:
            if content["detail"]:
                description = content["detail"]

            if response.status_code == 404:
                description = description + "\nRun /server-list to get a list of valid servers"
                
            embed: discord.Embed = discord.Embed(title=f"❌ Error getting server '{server}'", description=description, color=settings.RED)
            self.commands_logger.debug(f"Cannot get server, {response.status_code}")

        # Send embed
        embed.set_footer(text=settings.FOOTER)
        await interaction.followup.send(embed=embed)


# Setup function
async def setup(client):
    await client.add_cog(Servers(client))

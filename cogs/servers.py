# Module Imports
import logging
import requests

import discord
from discord import app_commands
from discord.ext import commands

from constants import Constants
import database.operations
from database.models import Server


# Main cog class
class Servers(commands.Cog):

    # Class init
    def __init__(self, client):
        self.client = client
        self.CONSTANTS = Constants()
        self.commands_logger: logging.Logger = logging.getLogger("commands")

    # Function to see if server is running
    async def check_server_running(self, server) -> bool:
        # Get server uuid
        server_uuid: str = database.operations.get_server_property(server, "uuid")

        # Return false if server does not exist
        if not server_uuid : return None

        response: requests.Response = requests.get(f"{self.CONSTANTS.PPDOMAIN}api/client/servers/{server_uuid}/resources", headers={'Authorization': f'Bearer {self.CONSTANTS.PPAPIKEY}'})
        content = response.json()
        running: str = content["attributes"]["current_state"]

        # Return result
        return True if running == "running" else False

    # Server List Command
    @app_commands.command(name="server-list", description="Lists all available servers you can start up")
    async def serverlist(self, interaction: discord.Interaction) -> None:
        # Log Command
        self.commands_logger.info(f"/server-list executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Create embed
        embed: discord.Embed = discord.Embed(title="📜 Server List",
                              description="All servers that can be run with the /start-server command. Use /server-help to find out more about each server",
                              color=self.CONSTANTS.BLUE)
        
        categories: list = database.operations.get_server_categories()
        for category in categories:
            embed.add_field(name=f"**{category}**", value=", ".join(database.operations.get_server_names(category)), inline=False)
        embed.set_footer(text=self.CONSTANTS.FOOTER)

        # Send embed
        await interaction.response.send_message(embed=embed)

    # Start Server Command
    @app_commands.command(name="server-start", description="Starts a specified server")
    @app_commands.describe(server="Server name")
    async def serverstart(self, interaction: discord.Interaction, server: str) -> None:
        # Log Command
        self.commands_logger.info(f"/server-start executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Define variables for embed
        server: str = (server.lower()).capitalize()
        title: str = ""
        description: str = ""
        success: bool = False
        embed_color: discord.Color = None
        running: bool = await self.check_server_running(server)

        # Check if server is already running, fail if so
        if running == True or running == None:
            success = False
        else:
            # Try to start server
            server_info: dict = database.operations.get_server_information(server)
            response: requests.Response = requests.post(f"{self.CONSTANTS.PPDOMAIN}api/client/servers/{server_info.uuid}/power", 
                                     headers={'Authorization': f'Bearer {self.CONSTANTS.PPAPIKEY}'}, 
                                     json={'signal': 'start'})
            
            # Check response code
            request_code: int = response.status_code
            if request_code == 204:
                success = True

        # Set embed information
        if success == True:
            title = f"✅ Successfully starting the {server} server"
            description = ""
            embed_color = self.CONSTANTS.GREEN
            self.commands_logger.debug("Successfully starting server")

        else:
            # If running is true, server must already be online
            if running == True:
                title = f"❌ {server} is already online"
                description = ""
                embed_color = self.CONSTANTS.RED
                self.commands_logger.debug("Bot cannot start server, server already online")

            # If running is false, server must be invalid
            else:
                title = f"❌ {server} is not a valid server"
                description = "Run /server-list to get a list of valid servers"
                embed_color = self.CONSTANTS.RED
                self.commands_logger.debug("Bot cannot start server, server name is not valid")

        # Send embed
        embed: discord.Embed = discord.Embed(title=title, description=description, color=embed_color)
        embed.set_footer(text=self.CONSTANTS.FOOTER)
        await interaction.response.send_message(embed=embed)

    # Server help command
    @app_commands.command(name="server-help", description="Lists info about a specified server")
    @app_commands.describe(server="Server name")
    async def serverhelp(self, interaction: discord.Interaction, server: str) -> None:
        # Log Command
        self.commands_logger.info(f"/server-help executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Get server info and assign it to variables, set embed to error if no such server exists
        server_info: Server = database.operations.get_server_information(server)
        if not server_info:
            embed: discord.Embed = discord.Embed(title=f"❌ {server} is not a valid server",
                                  description="Run /server-list to get a list of valid servers", color=self.CONSTANTS.RED)
            self.commands_logger.debug("Bot cannot return server information, server name is not valid")
        else:
            # Create embed
            embed: discord.Embed = discord.Embed(title=f"{server_info.emoji} {server_info.name}", description=server_info.description, color=self.CONSTANTS.BLUE)
            embed.add_field(name="**💻 Version**", value=f"{server_info.version} {server_info.modloader}", inline=False)

            # Add domain to embed
            embed.add_field(name="**✉️ How To Join**", value=server_info.domain, inline=False)

            # Add mod download information to embed
            if server_info.modloader != "Vanilla":
                if server_info.modconditions != None:
                    embed.add_field(name="**⏬ Modpack Download: **", value=f"[{server_info.modconditions}]({server_info.moddownload})",
                                    inline=False)
                else:
                    embed.add_field(name="**📜 Modlist: **", value=f"{server_info.modlist}", inline=False)
                    embed.add_field(name="**⏬ Modpack Download: **", value=f"[Google drive link]({server_info.moddownload})",
                                    inline=False)

            # Add message if the server is no longer active
            if server_info.active == False:
                embed.add_field(name="**❗ Activity**",
                                value="This server has been inactive for a long time, and can be considered dead",
                                inline=False)

            # Add current activity status of the server
            is_running = await self.check_server_running(server.lower().capitalize())
            if is_running == True:
                embed.add_field(name="**🟢 Status**", value="This server is currently online", inline=False)
            else:
                embed.add_field(name="**🔴 Status**", value="This server is currently offline", inline=False)

            self.commands_logger.debug("Successfully returned server information")

        # Send embed
        embed.set_footer(text=self.CONSTANTS.FOOTER)
        await interaction.response.send_message(embed=embed)

    # Active servers command
    @app_commands.command(name="active-servers", description="Lists all currently running servers")
    async def activeservers(self, interaction: discord.Interaction) -> None:
        # Log Command
        self.commands_logger.info(f"/active-servers executed by {interaction.user} in #{interaction.guild}")

        # Defer interaction
        await interaction.response.defer()

        # Define variables for embed
        title: str = "🟢 Servers currently online"
        description: list = []
        description_final: str = ""

        # Loop through all servers, add running ones to the list
        servers: list = database.operations.get_server_names("All")
        for server in servers:
            if await self.check_server_running(server):
                description.append(server)

        # Add all running servers to a string
        for i in description:
            
            # If only one server is running, no comma needed
            if len(description_final) == 0:
                description_final = description_final + i

            # Add comma if more than one server running
            elif len(description_final):
                description_final = description_final + f", {i}"

        # Send embed
        embed: discord.Embed = discord.Embed(title=title, description=description_final, color=self.CONSTANTS.BLUE)
        embed.set_footer(text=self.CONSTANTS.FOOTER)
        await interaction.followup.send(embed=embed)


# Setup function
async def setup(client):
    await client.add_cog(Servers(client))
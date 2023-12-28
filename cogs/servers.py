# Module Imports
import requests

import discord
from discord import app_commands
from discord.ext import commands

from constants import Constants
import serversdb


# Main cog class
class Servers(commands.Cog):

    # Class init
    def __init__(self, client):
        self.client = client
        self.CONSTANTS = Constants()

    # Function to see if server is running
    async def check_server_running(self, server) -> bool:
        # Get server uuid
        serverInfo = serversdb.GetServerInformation(server)
        server_uuid = serverInfo[15]
        # Check serverdata for running
        response = requests.get(f"{self.CONSTANTS.PPDOMAIN}api/client/servers/{server_uuid}/resources", headers={'Authorization': f'Bearer {self.CONSTANTS.PPAPIKEY}'})
        content = response.json()
        running = content["attributes"]["current_state"]
        if running == "running":
            return True
        else:
            return False

    # IP command
    @app_commands.command(name="ip", description="Displays the server ips")
    async def ip(self, interaction: discord.Interaction) -> None:
        # Create embed
        embed = discord.Embed(title="✉️ Server IP", description="", color=self.CONSTANTS.GREEN)
        embed.add_field(name="", value=f"**Main Network IP:** {self.CONSTANTS.IP1}", inline=False)
        embed.add_field(name="", value=f"**Secondary Server IP:** {self.CONSTANTS.IP2}", inline=False)
        embed.set_footer(text=self.CONSTANTS.FOOTER)

        # Send embed
        print(f"/ip executed by {interaction.user} in {interaction.guild} #{interaction.channel}")
        await interaction.response.send_message(embed=embed)

    # Server List Command
    @app_commands.command(name="server-list", description="Lists all available servers you can start up")
    async def serverlist(self, interaction: discord.Interaction) -> None:
        # Create embed
        embed = discord.Embed(title="📜 Server List",
                              description="All servers that can be run with the /start-server command. Use /server-help to find out more about each server",
                              color=self.CONSTANTS.GREEN)

        embed.add_field(name="**General Servers**", value=", ".join(serversdb.GetServerNames("General")), inline=False)
        embed.add_field(name="**Survival Servers**", value=", ".join(serversdb.GetServerNames("SMP")), inline=False)
        embed.add_field(name="**Origins Servers**", value=", ".join(serversdb.GetServerNames("Origins")), inline=False)
        embed.add_field(name="**Pokemon Servers**", value=", ".join(serversdb.GetServerNames("Pokemon")), inline=False)
        embed.add_field(name="**Miscellaneous Servers**", value=", ".join(serversdb.GetServerNames("Misc")), inline=False)
        embed.add_field(name="**Non-MC Servers**", value=", ".join(serversdb.GetServerNames("Non-MC")), inline=False)
        embed.set_footer(text=self.CONSTANTS.FOOTER)

        # Send embed
        print(f"/server-list executed by {interaction.user} in {interaction.guild} #{interaction.channel}")
        await interaction.response.send_message(embed=embed)

    # Start Server Command
    @app_commands.command(name="server-start", description="Starts a specified server")
    @app_commands.describe(server="Server name")
    async def serverstart(self, interaction: discord.Interaction, server: str) -> None:
        # Define variables for embed
        server = server.lower()
        server = server.capitalize()
        title = None
        description = None
        success = False
        embed_color = None
        running = await self.check_server_running(server)

        # Check if server is already running, fail if so
        if running == True:
            success = False
        else:
            # Try to start server
            serverInfo = serversdb.GetServerInformation(server)
            server_uuid = serverInfo[15]
            response = requests.post(f"{self.CONSTANTS.PPDOMAIN}api/client/servers/{server_uuid}/power", 
                                     headers={'Authorization': f'Bearer {self.CONSTANTS.PPAPIKEY}'}, 
                                     json={'signal': 'start'})
            
            # Check response code
            request_code = response.status_code
            if request_code == 204:
                success = True

        # Set embed information
        if success == True:
            title = f"✅ Successfully starting the {server} server"
            description = ""
            embed_color = self.CONSTANTS.GREEN
        else:
            # If running is true, server must already be online
            if running == True:
                title = f"❌ {server} is already online"
                description = ""
                embed_color = self.CONSTANTS.RED
            # If running is false, server must be invalid
            else:
                title = f"❌ {server} is not a valid server"
                description = "Run /server-list to get a list of valid servers"
                embed_color = self.CONSTANTS.RED

        # Create embed
        embed = discord.Embed(title=title, description=description, color=embed_color)
        embed.set_footer(text=self.CONSTANTS.FOOTER)

        # Send embed
        print(f"/server-start executed by {interaction.user} in {interaction.guild} #{interaction.channel}")
        await interaction.response.send_message(embed=embed)

    # Server help command
    @app_commands.command(name="server-help", description="Lists info about a specified server")
    @app_commands.describe(server="Server name")
    async def serverhelp(self, interaction: discord.Interaction, server: str) -> None:
        # Get server info and assign it to variables, set embed to error if no such server exists
        serverInfo = serversdb.GetServerInformation(server)
        if serverInfo == None:
            embed = discord.Embed(title=f"❌ {server} is not a valid server",
                                  description="Run /server-list to get a list of valid servers", color=self.CONSTANTS.RED)
        else:
            name = serverInfo[1]
            description = serverInfo[2]
            category = serverInfo[3]
            version = serverInfo[4]
            modloader = serverInfo[5]
            modlist = serverInfo[6]
            moddownload = serverInfo[7]
            active = serverInfo[8]
            compatible = serverInfo[9]
            modconditions = serverInfo[10]
            port = serverInfo[13]
            emoji = serverInfo[14]
            server = server.lower().capitalize()

            # Create embed
            embed = discord.Embed(title=f"{emoji} {name}", description=description, color=self.CONSTANTS.GREEN)
            embed.add_field(name="**💻 Version**", value=f"{version} {modloader}", inline=False)

            # Add address and port to embed
            if category == "Non-MC":
                embed.add_field(name="**✉️ IP**", value=f"{self.CONSTANTS.IP1}:{port}", inline=False)
            else:
                if compatible == 1:
                    embed.add_field(name="**✉️ IP**", value=f"{self.CONSTANTS.IP1} (Main IP)", inline=False)
                if compatible == 0:
                    embed.add_field(name="**✉️ IP**", value=f"{self.CONSTANTS.IP2} (Secondary IP)", inline=False)

            # Add mod download information to embed
            if modloader != "Vanilla":
                if modconditions != None:
                    embed.add_field(name="**⏬ Modpack Download: **", value=f"[{modconditions}]({moddownload})",
                                    inline=False)
                else:
                    embed.add_field(name="**📜 Modlist: **", value=f"{modlist}", inline=False)
                    embed.add_field(name="**⏬ Modpack Download: **", value=f"[Google drive link]({moddownload})",
                                    inline=False)

            # Add message if the server is no longer active
            if active == 0:
                embed.add_field(name="**❗ Activity**",
                                value="This server has been inactive for a long time, and is now spectator only",
                                inline=False)

            # Add current activity status of the server
            is_running = await self.check_server_running(server)
            if is_running == True:
                embed.add_field(name="**🟢 Status**", value="This server is currently online", inline=False)
            else:
                embed.add_field(name="**🔴 Status**", value="This server is currently offline", inline=False)

        # Send embed
        embed.set_footer(text=self.CONSTANTS.FOOTER)
        print(f"/server-help executed by {interaction.user} in {interaction.guild} #{interaction.channel}")
        await interaction.response.send_message(embed=embed)

    # Active servers command
    @app_commands.command(name="active-servers", description="Lists all currently running servers")
    async def activeservers(self, interaction: discord.Interaction) -> None:
        # Define variables for embed
        title = "🟢 Servers currently online"
        description = []
        description_final = ""

        # Loop through all servers, add running ones to the list, check for hub as it is not in db
        servers = serversdb.GetServerNames("All")
        for server in servers:
            if await self.check_server_running(server):
                description.append(server)

        # Add all running servers to a string
        for i in description:
            if len(description_final) == 0:
                description_final = description_final + i
            elif len(description_final):
                description_final = description_final + f", {i}"

        # Create embed
        embed = discord.Embed(title=title, description=description_final, color=self.CONSTANTS.GREEN)
        embed.set_footer(text=self.CONSTANTS.FOOTER)

        # Send embed
        print(f"/active-servers executed by {interaction.user} in #{interaction.guild}")
        await interaction.response.send_message(embed=embed)


# Setup function
async def setup(client):
    await client.add_cog(Servers(client))
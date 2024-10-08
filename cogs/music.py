# Module Imports
import discord
from discord import app_commands
from discord.ext import commands

import wavelink

from constants import Constants


# Custom wavelink player class
class CustomPlayer(wavelink.Player):
    def __init__(self):
        super().__init__()
        self.queue = wavelink.Queue()


# Main cog class
class Music(commands.Cog):

    # Class init
    def __init__(self, client):
        self.client = client
        self.CONSTANTS = Constants()
        
        client.loop.create_task(self.connect_nodes())

    # Wavelink connect node function
    async def connect_nodes(self) -> None:
        await self.client.wait_until_ready()
        nodes = [wavelink.Node(uri=f"{self.CONSTANTS.WLHOST}:{self.CONSTANTS.WLPORT}", password=self.CONSTANTS.WLPASSWORD)]
        await wavelink.Pool.connect(nodes=nodes, client=self.client, cache_capacity=None)

    # Wavelink on node ready function
    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload) -> None:
        print(f"Wavelink Node {payload.node.identifier} is ready!")

    # Wavelink on song end function
    #@commands.Cog.listener()
    #async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
    #    print(f"Track started: {payload.track.title}, duration: {payload.track.length}")

    #Wavelink on song end function
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        #print(f"Track ended: {payload.track.title}, reason: {payload.reason}")
        player = payload.player
        if not player.queue.is_empty:
            next_track = player.queue.get()
            await player.play(next_track)

    # Make sure to disconnect bot if it has been forcefully kicked
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after) -> None:
        # Check that the bot has left a voice channel
        if member == self.client.user and before.channel is not None and after.channel is None:
            # Check if the bot still has an active voice client
            if member.guild.voice_client:
                # Kick bot
                await member.guild.voice_client.disconnect()

    # Connect command
    @app_commands.command(name="connect", description="Connects the bot to a voice channel")
    async def connect(self, interaction: discord.Interaction) -> None:
        # Define variables
        vc: CustomPlayer = interaction.guild.voice_client
        message = ""
        color = None

        # Main try/except block
        try:
            # If the bot is not in vc, create a new player and join the voice channel
            if not vc:
                await interaction.user.voice.channel.connect(cls=CustomPlayer())
                message = "✅ Connected to the voice channel"
                color = self.CONSTANTS.GREEN
            # If the bot is already in the vc, set embed as such
            else:
                message = "❌ Already connected to a voice channel"
                color = self.CONSTANTS.RED
        # If error, the user is not in a voice channel
        except AttributeError:
            message = "❌ Please join a voice channel first"
            color = self.CONSTANTS.RED

        # Create embed
        embed = discord.Embed(title=message, color=color)
        embed.set_footer(text=self.CONSTANTS.FOOTER)

        # Send embed
        print(f"/connect executed by {interaction.user} in {interaction.guild} #{interaction.channel}")
        await interaction.response.send_message(embed=embed)

    # Disconnect command
    @app_commands.command(name="disconnect", description="Disconnects the bot from the voice channel")
    async def disconnect(self, interaction: discord.Interaction) -> None:
        # Define variables
        vc: CustomPlayer = interaction.guild.voice_client
        message = ""
        color = None

        # If the bot is in vc, disconnect them, else show error
        if vc:
            await vc.disconnect()
            message = "✅ Disconnected from the voice channel"
            color = self.CONSTANTS.GREEN
        else:
            message = "❌ Not connected to a voice channel"
            color = self.CONSTANTS.RED

        # Create embed
        embed = discord.Embed(title=message, color=color)
        embed.set_footer(text=self.CONSTANTS.FOOTER)

        # Send embed
        print(f"/disconnect executed by {interaction.user} in {interaction.guild} #{interaction.channel}")
        await interaction.response.send_message(embed=embed)

    # Play command
    @app_commands.command(name="play", description="Plays a song in a voice channel")
    @app_commands.describe(song="Song that you want to play")
    async def play(self, interaction: discord.Interaction, song: str) -> None:
        # Search YouTube for song
        tracks = await wavelink.Playable.search(song, source=wavelink.TrackSource.YouTube)
        track = tracks[0]

        # Define variables
        vc = interaction.guild.voice_client
        title = ""
        color = None
        url = None

        # Add bot to vc if not already present
        try:
            if not vc:
                custom_player = CustomPlayer()
                vc: CustomPlayer = await interaction.user.voice.channel.connect(cls=custom_player)
                vc.autoplay = wavelink.AutoPlayMode.disabled
        except Exception as e:
            title = "❌ Please join a voice channel first"
            color = self.CONSTANTS.RED

        # Main try/except block
        try:
            # If vc still does not exist by this point, the user must not be in vc, error is shown
            if vc == None:
                raise Exception
            
            # Adds song to queue if song already present
            if vc.playing:
                await vc.queue.put_wait(track)
                title = "✅ Added song to queue"

            # Play song if no songs are present in queue
            else:
                await vc.play(track, replace=False)
                title = "▶️ Now Playing"

            description = f"{track.title}"
            color = self.CONSTANTS.GREEN
            url = track.uri

        # Handle exceptions
        except Exception as e:
            title = "❌ Please join a voice channel first"
            color = self.CONSTANTS.RED
            print(e)

        # Create embed
        embed = discord.Embed(title=title, description=description, color=color, url=url)
        embed.set_footer(text=self.CONSTANTS.FOOTER)

        # Send embed
        print(f"/play {song} executed by {interaction.user} in {interaction.guild} #{interaction.channel}")
        await interaction.response.send_message(embed=embed)

    # Skip command
    @app_commands.command(name="skip", description="Skips the currently playing song")
    async def skip(self, interaction: discord.Interaction) -> None:
        # Define variables
        vc: CustomPlayer = interaction.guild.voice_client
        message = ""
        color = None

        # Check if bot is in a voice channel
        if vc:
            # Send error if nothing is playing
            if not vc.playing:
                message = "❌ Nothing is playing"
                color = self.CONSTANTS.RED

            # Stop playback if skip is applied while queue is empty
            if vc.queue.is_empty:
                await vc.stop()

            # Skip song, error will only be thrown if nothing is playing
            try:
                await vc.skip()
            except Exception as e:
                pass
            message = "⏭️ Song Skipped"
            color = self.CONSTANTS.GREEN

            # Resume playback after skip
            if vc.paused == True:
                await vc.pause(False)

        # Error if bot is not connected to voice channel
        else:
            message = "❌ Bot is not connected to voice channel"
            color = self.CONSTANTS.RED

        # Create embed
        embed = discord.Embed(title=message, color=color)
        embed.set_footer(text=self.CONSTANTS.FOOTER)

        # Send embed
        print(f"/skip executed by {interaction.user} in {interaction.guild} #{interaction.channel}")
        await interaction.response.send_message(embed=embed)

    # Pause command
    @app_commands.command(name="pause", description="Pauses music playback")
    async def pause(self, interaction: discord.Interaction) -> None:
        # Define variables
        vc: CustomPlayer = interaction.guild.voice_client
        message = ""
        color = None

        # Check if bot is connected to a voice channel
        if vc:
            # Pause playback if something is playing
            if vc.playing and not vc.paused:
                await vc.pause(True)
                message = "⏸️ Playback paused"
                color = self.CONSTANTS.GREEN
            # Error if nothing is already playing
            else:
                message = "❌ Nothing is playing"
                color = self.CONSTANTS.RED
        # Error if bot is not connected to a voice channel
        else:
            message = "❌ Bot is not connected to voice channel"
            color = self.CONSTANTS.RED

        # Create embed
        embed = discord.Embed(title=message, color=color)
        embed.set_footer(text=self.CONSTANTS.FOOTER)

        # Send embed
        print(f"/pause executed by {interaction.user} in {interaction.guild} #{interaction.channel}")
        await interaction.response.send_message(embed=embed)

    # Resume command
    @app_commands.command(name="resume", description="Resumes music playback")
    async def resume(self, interaction: discord.Interaction) -> None:
        # Define variables
        vc: CustomPlayer = interaction.guild.voice_client
        message = ""
        color = None

        # Check if bot is connected to a voice channel
        if vc:
            # Resume playback if nothing is playing
            if vc.paused:
                await vc.pause(False)
                message = "▶️ Playback resumed"
                color = self.CONSTANTS.GREEN
            # Error if something is already playing
            else:
                message = "❌ Nothing is playing"
                color = self.CONSTANTS.RED
        # Error if bot is not connected to a voice channel
        else:
            message = "❌ Bot is not connected to voice channel"
            color = self.CONSTANTS.RED

        # Create embed
        embed = discord.Embed(title=message, color=color)
        embed.set_footer(text=self.CONSTANTS.FOOTER)

        # Send embed
        print(f"/resume executed by {interaction.user} in {interaction.guild} #{interaction.channel}")
        await interaction.response.send_message(embed=embed)

    # Queue command
    @app_commands.command(name="queue", description="Shows the music queue")
    async def queue(self, interaction: discord.Interaction) -> None:
        # Defer interaction
        await interaction.response.defer()

        # Define variables
        vc: CustomPlayer = interaction.guild.voice_client
        embed = None
        embed_queue = ""

        # Adds bot to vc if not already present
        try:
            if not vc:
                custom_player = CustomPlayer()
                vc: CustomPlayer = await interaction.user.voice.channel.connect(cls=custom_player)

            # Create embed
            embed = discord.Embed(title="Music Queue", color=self.CONSTANTS.GREEN)
            embed.set_footer(text=self.CONSTANTS.FOOTER)

            # Sets embed element to be currently playing song, if any
            currently_playing = vc.current
            if currently_playing == None:
                embed.add_field(name=f"**▶️ Currently Playing**", value="Nothing Is Playing", inline=False)
            else:
                embed.add_field(name=f"**▶️ Currently Playing**", value=currently_playing, inline=False)

            # Collects songs in queue and adds them to the embed
            for item in vc.queue:
                embed_queue = embed_queue + str(item) + "\n"
            if embed_queue == "":
                embed_queue = "Nothing Is Queued"
            embed.add_field(name=f"**⏭️ Up Next**", value=embed_queue, inline=False)

        # Handles exception if user is not in a voice channel
        except Exception as e:
            embed = None
            embed = discord.Embed(title="❌ Please join a voice channel first", color=self.CONSTANTS.RED)

        # Send embed
        print(f"/queue executed by {interaction.user} in {interaction.guild} #{interaction.channel}")
        await interaction.followup.send(embed=embed)

    # Music playback error handling
    @play.error
    async def play_error(self, interaction: discord.Interaction, error) -> None:

        # Check if error
        message = ""
        if isinstance(error, commands.BadArgument):
            message = "❌ Could not find song"
        else:
            message = f"❌ Please join a voice channel"

        # Create embed
        embed = discord.Embed(title=message, color=self.CONSTANTS.RED)
        embed.set_footer(text=self.CONSTANTS.FOOTER)

        # Send embed
        await interaction.response.send_message(embed=embed)


# Setup function
async def setup(client):
    await client.add_cog(Music(client))
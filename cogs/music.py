# Module Imports
import logging

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

        self.commands_logger: logging.Logger = logging.getLogger("commands")
        self.wavelink_logger: logging.Logger = logging.getLogger("wavelink")
        
        client.loop.create_task(self.connect_nodes())

    # Wavelink connect node function
    async def connect_nodes(self) -> None:
        await self.client.wait_until_ready()
        nodes = [wavelink.Node(uri=f"{self.CONSTANTS.WLHOST}:{self.CONSTANTS.WLPORT}", password=self.CONSTANTS.WLPASSWORD)]
        await wavelink.Pool.connect(nodes=nodes, client=self.client, cache_capacity=None)

    # Wavelink on node ready function
    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload) -> None:
        self.wavelink_logger.info(f"Wavelink Node {payload.node.identifier} is ready!")

    # Wavelink on song end function
    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        self.wavelink_logger.debug(f"Track started: {payload.track.title}, duration: {payload.track.length}")

    #Wavelink on song end function
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        self.wavelink_logger.debug(f"Track ended: {payload.track.title}, reason: {payload.reason}")
        # If the queue is not empty, play the next track
        player: wavelink.Player  = payload.player
        if player and not player.queue.is_empty:
            next_track = player.queue.get()
            await player.play(next_track)

    # Make sure to disconnect bot if it has been forcefully kicked
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        self.wavelink_logger.debug(f"Voice state update: {before.channel} to {after.channel}")
        # Check that the bot has left a voice channel
        if member == self.client.user and before.channel is not None and after.channel is None:
            # Check if the bot still has an active voice client
            if member.guild.voice_client:
                # Kick bot
                await member.guild.voice_client.disconnect()

    # Function to convert milliseconds as given by wavelink playables into hh:mm:ss or mm:ss
    async def convert_milliseconds(self, length: int) -> str:
        total_seconds: int = length // 1000
        hours: int = total_seconds // 3600
        minutes: int = (total_seconds % 3600) // 60
        seconds: int = total_seconds % 60
        if hours > 0:
            final_length = f"{hours}:{minutes:02}:{seconds:02}"
        else:
            final_length = f"{minutes:02}:{seconds:02}"
        self.commands_logger.debug(f"Length of {final_length} returned")
        return final_length

    # Connect command
    @app_commands.command(name="connect", description="Connects the bot to a voice channel")
    async def connect(self, interaction: discord.Interaction) -> None:
        # Log Command
        self.commands_logger.info(f"/connect executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Define variables
        vc: CustomPlayer = interaction.guild.voice_client
        message: str = ""
        color: discord.Color = None

        # Main try/except block
        try:
            # If the bot is not in vc, create a new player and join the voice channel
            if not vc:
                await interaction.user.voice.channel.connect(cls=CustomPlayer())
                message = "✅ Connected to the voice channel"
                color = self.CONSTANTS.GREEN
                self.commands_logger.debug("Bot successfully connected to voice channel")
            # If the bot is already in the vc, set embed as such
            else:
                message = "❌ Already connected to a voice channel"
                color = self.CONSTANTS.RED
                self.commands_logger.debug("Bot is already connected to voice channel")
        # If error, the user is not in a voice channel
        except AttributeError:
            message = "❌ Please join a voice channel first"
            color = self.CONSTANTS.RED
            self.commands_logger.debug("Bot cannot connect to voice channel, user not in voice channel")

        # Send embed
        embed: discord.Embed = discord.Embed(title=message, color=color)
        embed.set_footer(text=self.CONSTANTS.FOOTER)
        await interaction.response.send_message(embed=embed)

    # Disconnect command
    @app_commands.command(name="disconnect", description="Disconnects the bot from the voice channel")
    async def disconnect(self, interaction: discord.Interaction) -> None:
        # Log Command
        self.commands_logger.info(f"/disconnect executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Define variables
        vc: CustomPlayer = interaction.guild.voice_client
        message: str = ""
        color: discord.Color = None

        # If the bot is in vc, disconnect
        if vc:
            await vc.disconnect()
            message = "✅ Disconnected from the voice channel"
            color = self.CONSTANTS.GREEN
            self.commands_logger.debug("Bot successfully disconnected from voice channel")

        # If bot not in vc, show error
        else:
            message = "❌ Not connected to a voice channel"
            color = self.CONSTANTS.RED
            self.commands_logger.debug("Bot cannot disconnect from voice channel, was not initially in voice channel")

        # Send embed
        embed: discord.Embed = discord.Embed(title=message, color=color)
        embed.set_footer(text=self.CONSTANTS.FOOTER)
        await interaction.response.send_message(embed=embed)

    # Play command
    @app_commands.command(name="play", description="Plays a song in a voice channel")
    @app_commands.describe(song="Song that you want to play")
    async def play(self, interaction: discord.Interaction, song: str) -> None:
        # Log Command
        self.commands_logger.info(f"/play {song} executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Define variables
        vc: CustomPlayer = interaction.guild.voice_client
        title: str = ""
        description: str = ""
        color: discord.Color = None
        url: str = None
        thumbnail_url: str = None
        results_found: bool = True

        # Main try/except block
        try:
            # Add bot to vc if not already present
            if not vc:
                custom_player = CustomPlayer()
                vc = await interaction.user.voice.channel.connect(cls=custom_player)
                vc.autoplay = wavelink.AutoPlayMode.disabled

            # Search YouTube for song
            tracks: wavelink.Search = await wavelink.Playable.search(song, source=wavelink.TrackSource.YouTube)

            # If no results are found raise an error
            if not tracks:
                results_found = False
                raise Exception
            
            track: wavelink.Playable = tracks[0]
            self.commands_logger.debug(f"{track.title} found")
            
            # Adds song to queue if song already present
            if vc.playing:
                await vc.queue.put_wait(track)
                title = "✅ Added song to queue"
                self.commands_logger.debug("Song successfully added to queue")

            # Play song if no songs are present in queue
            else:
                await vc.play(track, replace=False)
                title = "▶️ Now Playing"
                self.commands_logger.debug("Song successfully played")

            description = track.title
            color = self.CONSTANTS.GREEN
            url = track.uri
            thumbnail_url = track.artwork
                
        # Handle user not being in vc
        except Exception as e:
            color = self.CONSTANTS.RED
            if results_found == False:
                title = "❌ No song with that name could be found"
                self.commands_logger.debug("Bot cannot connect to find song, no results")
            else:
                title = "❌ Please join a voice channel first"
                self.commands_logger.debug("Bot cannot connect to voice channel, user not in voice channel")

        # Send embed
        embed: discord.Embed = discord.Embed(title=title, description=description, color=color, url=url)
        embed.set_thumbnail(url=thumbnail_url)
        embed.set_footer(text=self.CONSTANTS.FOOTER)
        await interaction.response.send_message(embed=embed)

    # Skip command
    @app_commands.command(name="skip", description="Skips the currently playing song")
    async def skip(self, interaction: discord.Interaction) -> None:
        # Log Command
        self.commands_logger.info(f"/skip executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Define variables
        vc: CustomPlayer = interaction.guild.voice_client
        message: str = ""
        color: discord.Color = None
        description: str = ""

        # Check if bot is in a voice channel
        if vc:
            # Send error if nothing is playing
            if not vc.playing:
                message = "❌ Nothing is playing"
                color = self.CONSTANTS.RED
                self.commands_logger.debug("Bot cannot skip song, nothing is playing")

            else:
                # Skip song
                await vc.skip()
                self.commands_logger.debug("Song successfully skipped")
                
                message = "⏭️ Song Skipped"
                color = self.CONSTANTS.GREEN

                if vc.playing:
                    description = f"Now Playing: [{vc.current.title}]({vc.current.uri})"

                # Resume playback after skip
                if vc.paused == True:
                    await vc.pause(False)

        # Error if bot is not connected to voice channel
        else:
            message = "❌ Bot is not connected to voice channel"
            color = self.CONSTANTS.RED
            self.commands_logger.debug("Bot cannot skip song, bot not in voice channel")

        # Send embed
        embed: discord.Embed = discord.Embed(title=message, description=description, color=color)
        embed.set_footer(text=self.CONSTANTS.FOOTER)
        await interaction.response.send_message(embed=embed)

    # Pause command
    @app_commands.command(name="pause", description="Pauses music playback")
    async def pause(self, interaction: discord.Interaction) -> None:
        # Log Command
        self.commands_logger.info(f"/pause executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Define variables
        vc: CustomPlayer = interaction.guild.voice_client
        message: str = ""
        color: discord.Color = None

        # Check if bot is connected to a voice channel
        if vc:
            # Pause playback if something is playing
            if vc.playing and not vc.paused:
                await vc.pause(True)
                message = "⏸️ Playback paused"
                color = self.CONSTANTS.GREEN
                self.commands_logger.debug("Playback successfully paused")

            # Error if nothing is already playing
            else:
                message = "❌ Nothing is playing"
                color = self.CONSTANTS.RED
                self.commands_logger.debug("Bot cannot pause playback, nothing is playing")

        # Error if bot is not connected to a voice channel
        else:
            message = "❌ Bot is not connected to voice channel"
            color = self.CONSTANTS.RED
            self.commands_logger.debug("Bot cannot pause playback, bot not in voice channel")

        # Send embed
        embed: discord.Embed = discord.Embed(title=message, color=color)
        embed.set_footer(text=self.CONSTANTS.FOOTER)
        await interaction.response.send_message(embed=embed)

    # Resume command
    @app_commands.command(name="resume", description="Resumes music playback")
    async def resume(self, interaction: discord.Interaction) -> None:
        # Log Command
        self.commands_logger.info(f"/resume executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Define variables
        vc: CustomPlayer = interaction.guild.voice_client
        message: str = ""
        color: discord.Color = None

        # Check if bot is connected to a voice channel
        if vc:
            # Resume playback if nothing is playing
            if vc.paused:
                await vc.pause(False)
                message = "▶️ Playback resumed"
                color = self.CONSTANTS.GREEN
                self.commands_logger.debug("Playback successfully resumed")

            # Error if something is already playing
            else:
                message = "❌ Nothing is playing"
                color = self.CONSTANTS.RED
                self.commands_logger.debug("Bot cannot resume playback, nothing is playing")

        # Error if bot is not connected to a voice channel
        else:
            message = "❌ Bot is not connected to voice channel"
            color = self.CONSTANTS.RED
            self.commands_logger.debug("Bot cannot resume playback, bot not in voice channel")

        # Send embed
        embed: discord.Embed = discord.Embed(title=message, color=color)
        embed.set_footer(text=self.CONSTANTS.FOOTER)
        await interaction.response.send_message(embed=embed)

    # Queue command
    @app_commands.command(name="queue", description="Shows the music queue")
    async def queue(self, interaction: discord.Interaction) -> None:
        # Log Command
        self.commands_logger.info(f"/queue executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Defer interaction
        await interaction.response.defer()

        # Define variables
        vc: CustomPlayer = interaction.guild.voice_client
        embed: discord.Embed = None
        embed_queue: str = ""

        # Adds bot to vc if not already present
        try:
            if not vc:
                custom_player = CustomPlayer()
                vc: CustomPlayer = await interaction.user.voice.channel.connect(cls=custom_player)

            # Create embed
            embed: discord.Embed = discord.Embed(title="Music Queue", color=self.CONSTANTS.GREEN)
            embed.set_footer(text=self.CONSTANTS.FOOTER)

            # Sets embed element to be currently playing song, if any
            if not vc.current:
                embed.add_field(name=f"**▶️ Currently Playing**", value="Nothing Is Playing", inline=False)
            else:
                current_position: str = await self.convert_milliseconds(vc.position)
                current_length: str = await self.convert_milliseconds(vc.current.length)
                embed.add_field(name=f"**▶️ Currently Playing**", value=f"[{vc.current.title}]({vc.current.uri}) `{current_position}`/`{current_length}`", inline=False)

            # Collects songs in queue and adds them to the embed
            queue_position: int = 1
            for item in vc.queue:
                current_length: str = await self.convert_milliseconds(item.length)
                embed_queue = embed_queue + f"{queue_position}) [{item.title}]({item.uri}) `{current_length}`\n"
                queue_position += 1
            if embed_queue == "":
                embed_queue = "Nothing Is Queued"
            embed.add_field(name=f"**⏭️ Up Next**", value=embed_queue, inline=False)
            
            self.commands_logger.debug("Queue successfully returned")

        # Handles exception if user is not in a voice channel
        except Exception as e:
            embed: discord.Embed = discord.Embed(title="❌ Please join a voice channel first", color=self.CONSTANTS.RED)
            self.commands_logger.debug("Bot cannot return queue, bot not in voice channel")
            self.commands_logger.error(e)

        # Send embed
        await interaction.followup.send(embed=embed)

    # Music playback error handling
    @play.error
    async def play_error(self, interaction: discord.Interaction, error) -> None:

        # Check if error
        message: str = ""
        if isinstance(error, commands.BadArgument):
            message = "❌ Could not find song"
            self.wavelink_logger.error("Could not find song")
        else:
            message = f"❌ Please join a voice channel"
            self.wavelink_logger.error(error)

        # Create embed
        embed: discord.Embed = discord.Embed(title=message, color=self.CONSTANTS.RED)
        embed.set_footer(text=self.CONSTANTS.FOOTER)

        # Send embed
        await interaction.response.send_message(embed=embed)


# Setup function
async def setup(client):
    await client.add_cog(Music(client))
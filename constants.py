# Module Imports
import json
import logging

import discord


# Constants class to store constants for use in other files
class Constants():
    def __init__(self):
        # Load config file
        data = json.load(open("config.json", "r"))

        # Keys
        self.TOKEN: str = data["KEYS"]["TOKEN"]
        self.CATAPIKEY: str = data["KEYS"]["CATAPIKEY"]

        # Database
        self.DBHOST: str = data["DATABASE"]["DBHOST"]
        self.DBPORT: str = data["DATABASE"]["DBPORT"]
        self.DBUSERNAME: str = data["DATABASE"]["DBUSERNAME"]
        self.DBPASSWORD: str = data["DATABASE"]["DBPASSWORD"]
        self.DBDATABASE: str = data["DATABASE"]["DBDATABASE"]

        # Wavelink
        self.WLHOST: str = data["WAVELINK"]["WLHOST"]
        self.WLPORT: str = data["WAVELINK"]["WLPORT"]
        self.WLPASSWORD: int = data["WAVELINK"]["WLPASSWORD"]

        # Pterodactyl Panel
        self.PPDOMAIN: str = data["PTERODACTYL"]["PPDOMAIN"]
        self.PPAPIKEY: str = data["PTERODACTYL"]["PPAPIKEY"]

        # Logging
        self.ROOTLOGLEVEL: str = data["LOGGING"]["ROOTLOGLEVEL"]
        self.DISCORDLOGLEVEL: str = data["LOGGING"]["DISCORDLOGLEVEL"]
        self.COMMANDSLOGLEVEL: str = data["LOGGING"]["COMMANDSLOGLEVEL"]
        self.WAVELINKLOGLEVEL: str = data["LOGGING"]["WAVELINKLOGLEVEL"]
        self.DATABASELOGLEVEL: str = data["LOGGING"]["DATABASELOGLEVEL"]
        self.ECONOMYLOGLEVEL: str = data["LOGGING"]["ECONOMYLOGLEVEL"]

        # Strings
        self.FOOTER: str = "Beep Boop"

        # Colors
        self.BLUE: discord.Color = discord.Color.from_rgb(37, 150, 190)
        self.RED: discord.Color = discord.Color.from_rgb(252, 0, 0)
        self.GREEN: discord.Color = discord.Color.from_rgb(0, 252, 0)
        self.YELLOW: discord.Color = discord.Color.from_rgb(252, 252, 0)

        # Bot statuses
        self.STATUSES_PLAYING: list[str] = [
            "Minecraft",
            "Roblox",
            "Terraria",
            "Birdgut",
            "Super friends party",
            "Farm Merge Valley",
            "Ronopoly",
        ]
        self.STATUSES_WATCHING: list[str] = [
            "Youtube",
            "Plane crashes",
            "Breaking Bad",
            "One Piece"
        ]
        self.STATUSES_LISTENING: list[str] = [
            "the purges",
            "the screams",
            "death metal",
            "EPIC The Musical"
        ]

# Module Imports
import json

import discord


# Constants class to store constants for use in other files
class Constants():
    def __init__(self):
        # Load config file
        data = json.load(open("config.json", "r"))

        # Keys
        self.TOKEN = data["KEYS"]["TOKEN"]
        self.CATAPIKEY = data["KEYS"]["CATAPIKEY"]

        # Database
        self.DBHOST = data["DATABASE"]["DBHOST"]
        self.DBUSERNAME = data["DATABASE"]["DBUSERNAME"]
        self.DBPASSWORD = data["DATABASE"]["DBPASSWORD"]
        self.DBDATABASE = data["DATABASE"]["DBDATABASE"]

        # Wavelink
        self.WLHOST = data["WAVELINK"]["WLHOST"]
        self.WLPORT = data["WAVELINK"]["WLPORT"]
        self.WLPASSWORD = data["WAVELINK"]["WLPASSWORD"]

        # Pterodactyl Panel
        self.PPDOMAIN = data["PTERODACTYL"]["PPDOMAIN"]
        self.PPAPIKEY = data["PTERODACTYL"]["PPAPIKEY"]

        # Strings
        self.FOOTER = "Beep Boop"

        # Colors
        self.RED = discord.Color.from_rgb(252, 0, 0)
        self.GREEN = discord.Color.from_rgb(0, 252, 0)

        # Bot statuses
        self.STATUSES_PLAYING = [
            "Minecraft",
            "Roblox",
        ]
        self.STATUSES_WATCHING = [
            "Youtube",
            "plane crashes"
        ]
        self.STATUSES_LISTENING = [
            "the purges",
            "the screams"
        ]

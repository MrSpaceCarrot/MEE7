# Module Imports
from pydantic_settings import BaseSettings, SettingsConfigDict
import discord


class Settings(BaseSettings):
    # Env file keys
    # Keys
    BOT_TOKEN: str
    CAT_API_KEY: str

    # DerpsCubedAPI
    API_BASE_URL: str
    API_KEY: str

    # Wavelink
    WAVELINK_HOST: str
    WAVELINK_PORT: int
    WAVELINK_PASSWORD: str

    # Logging
    LOG_LEVEL_ROOT: str = "INFO"
    LOG_LEVEL_DISCORD: str = "INFO"
    LOG_LEVEL_COMMANDS: str = "INFO"
    LOG_LEVEL_WAVELINK: str = "INFO"
    LOG_LEVEL_ECONOMY: str = "INFO"

    # Specify env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Other settings
    # Strings
    FOOTER: str = "Beep Boop"

    # Colors
    BLUE: discord.Color = discord.Color.from_rgb(37, 150, 190)
    RED: discord.Color = discord.Color.from_rgb(252, 0, 0)
    GREEN: discord.Color = discord.Color.from_rgb(0, 252, 0)
    YELLOW: discord.Color = discord.Color.from_rgb(252, 252, 0)

    # Statuses
    STATUSES_PLAYING: list[str] = [
        "Minecraft",
        "Roblox",
        "Terraria",
        "Birdgut",
        "Super friends party",
        "Farm Merge Valley",
        "Ronopoly",
        "League of Legends",
        "SPIKED"
    ]
    STATUSES_WATCHING: list[str] = [
        "Youtube",
        "Plane crashes",
        "Breaking Bad",
        "One Piece",
        "Paint dry"
    ]
    STATUSES_LISTENING: list[str] = [
        "the purges",
        "the screams",
        "death metal",
        "EPIC The Musical",
        "Hamilton",
        "Yap"
    ]

settings = Settings()
# Module Imports
import logging

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

from config import settings
from services.api import api_get, api_post


# Views
# Exchange view
class ExchangeView(discord.ui.View):
    def __init__(self, user: discord.User, exchange_dict: dict):
        super().__init__(timeout=300)
        self.user = user
        self.exchange_dict = exchange_dict
        self.economy_logger: logging.Logger = logging.getLogger("economy")

    # Check that user that started the interaction can interact
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id

    # Update embed
    async def refresh(self) -> discord.Embed:
        # Set embed fields
        # If code was provided, exchange has not been confirmed yet
        if "code" in self.exchange_dict:
            message = self.exchange_dict["return_text"].split(". ")
            title = message[0]
            description = f"{message[1]}\n{message[2]}"
            color = settings.YELLOW
        
        # If action was given, exchange has concluded
        else:
            if self.exchange_dict["action"] == "Confirmation":
                message = self.exchange_dict["return_text"].split(". ")
                title = message[0]
                description = f"{message[1]}\n{message[2]}"
                color = settings.GREEN
            else:
                title = self.exchange_dict["return_text"]
                description = ""
                color = settings.RED

            # Disable buttons
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    item.disabled = True

        # Create embed
        embed: discord.Embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text=settings.FOOTER)
        return embed
    
    # Confirm Button
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Send confirm request
        data = {"code": self.exchange_dict['code'],
                "action": "Confirm"}
        response = api_post(f"/economy/currencies/exchange", interaction.user.id, data)

        # Send new embed
        new_view = ExchangeView(self.user, response.json())
        embed = await new_view.refresh()
        await interaction.response.edit_message(embed=embed, view=new_view)
    
    # Cancel Button
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Send confirm request
        data = {"code": self.exchange_dict['code'],
                "action": "Cancel"}
        response = api_post(f"/economy/currencies/exchange", interaction.user.id, data)

        # Send new embed
        new_view = ExchangeView(self.user, response.json())
        embed = await new_view.refresh()
        await interaction.response.edit_message(embed=embed, view=new_view)


# Blackjack view
class BlackjackView(discord.ui.View):
    def __init__(self, user: discord.User, game_dict: dict):
        super().__init__(timeout=300)
        self.user = user
        self.game_dict = game_dict
        self.economy_logger: logging.Logger = logging.getLogger("economy")

    # Check that user that started the interaction can interact
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id
    
    # Game logic and update embed
    async def refresh(self) -> discord.Embed:
        # Set embed fields
        if self.game_dict["result"] != None:
            description = ""
            result_text = self.game_dict["result_text"].split(". ")
            for item in result_text:
                description = description + f"{item}\n"
            
            if self.game_dict["result"] == "Win":
                title = "You Win!"
                color = settings.GREEN
            elif self.game_dict["result"] == "Lose":
                title = "Dealer Wins!"
                color = settings.RED
            elif self.game_dict["result"] == "Tie":
                title = "You Tied!"
                color = settings.YELLOW

            # Disable buttons at game end
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    item.disabled = True
        else:
            title = "Blackjack"
            currency = self.game_dict["currency"]
            description = f"Bet: {currency['prefix']}{self.game_dict['bet']:.{currency['decimal_places']}f} {currency['display_name']}"
            color = settings.BLUE

        # Create embed
        embed: discord.Embed = discord.Embed(title=title, description=description, color=color)

        # User hand
        user_hand = ""
        for card in self.game_dict['user_hand']:
            user_hand = user_hand + f"{card} "
        embed.add_field(name=f"Your Hand ({self.game_dict['user_hand_value']})", value=user_hand, inline=False)
        
        # Dealer hand
        dealer_hand = ""
        for card in self.game_dict['dealer_hand']:
            dealer_hand = dealer_hand + f"{card} "
        
        if self.game_dict["result"] != None:
            embed.add_field(name=f"Dealer's Hand ({self.game_dict['dealer_hand_value']})", value=dealer_hand, inline=False)
        else:
            embed.add_field(name=f"Dealer's Hand (?)", value=dealer_hand, inline=False)

        embed.set_thumbnail(url=self.user.display_avatar.url)
        embed.set_footer(text=settings.FOOTER)
        return embed

    # Hit button
    @discord.ui.button(label="Hit", style=discord.ButtonStyle.primary)
    async def hit_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Send hit request
        data = {"code": self.game_dict['code'],
                "action": "Hit"}
        response = api_post(f"/economy/gambling/blackjack", interaction.user.id, data)

        # Send new embed
        new_view = BlackjackView(self.user, response.json())
        embed = await new_view.refresh()
        await interaction.response.edit_message(embed=embed, view=new_view)

    # Stand button
    @discord.ui.button(label="Stand", style=discord.ButtonStyle.primary)
    async def stand_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Send hit request
        data = {"code": self.game_dict['code'],
                "action": "Stand"}
        response = api_post(f"/economy/gambling/blackjack", interaction.user.id, data)

        # Send new embed
        new_view = BlackjackView(self.user, response.json())
        embed = await new_view.refresh()
        await interaction.response.edit_message(embed=embed, view=new_view)


# Job view
class JobView(discord.ui.View):
    def __init__(self, user: discord.User, job_response: dict, has_quit_job: bool = False):
        super().__init__(timeout=300)
        self.user = user
        self.job_response = job_response
        self.has_quit_job = has_quit_job

    # Check that user that started the interaction can interact
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id
    
    # Embed logic
    async def refresh(self) -> discord.Embed:
        # Disable both buttons if job was quit
        if self.has_quit_job == True:
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    item.disabled = True

        # Set embed fields
        # If user does not have a job
        if "detail" in self.job_response:
            # If a cooldown is present
            if ". " in self.job_response["detail"]:
                message = self.job_response["detail"].split(". ")
                title = message[0]
                description = message[1]

                # Disable get job button
                for item in self.children:
                    if isinstance(item, discord.ui.Button) and item.label == "Get Job":
                        item.disabled = True
            
            # If cooldown is not present
            else:
                title = self.job_response["detail"]
                description = ""
            color = settings.RED
            
            # Disable quit job button
            for item in self.children:
                if isinstance(item, discord.ui.Button) and item.label == "Quit Job":
                    item.disabled = True

        # If user has a job
        else:
            job = self.job_response["job"]
            currency = self.job_response["currency"]
            title = f"Job: {job['display_name']}"
            description = f"Salary: {currency['prefix']}{(job['min_pay'] / currency['value_multiplier']):.{currency['decimal_places']}f} - {currency['prefix']}{(job['max_pay'] / currency['value_multiplier']):.{currency['decimal_places']}f} per shift\nWork Cooldown: {job['cooldown']:.0f}s\nDo /work to work"
            color = settings.GREEN

            # Disable get job button
            for item in self.children:
                if isinstance(item, discord.ui.Button) and item.label == "Get Job":
                    item.disabled = True
        
        # Crete embed
        embed: discord.Embed = discord.Embed(title=title, description=description, color=color)
        embed.set_thumbnail(url=self.user.display_avatar.url)
        embed.set_footer(text=settings.FOOTER) 
        return embed
    
    # Get Job Button
    @discord.ui.button(label="Get Job", style=discord.ButtonStyle.primary)
    async def get_job_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Disable buttons
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

        # Send apply for job request to api
        response = api_post(f"/economy/jobs/apply", interaction.user.id)

        # Send new embed
        new_view = JobView(self.user, response.json())
        embed = await new_view.refresh()
        await interaction.response.edit_message(embed=embed, view=new_view)

    # Quit Job
    @discord.ui.button(label="Quit Job", style=discord.ButtonStyle.danger)
    async def quit_job_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Disable buttons
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

        # Send quit job request to api
        response = api_post(f"/economy/jobs/quit", interaction.user.id)

        # Send new embed
        new_view = JobView(self.user, response.json(), True)
        embed = await new_view.refresh()
        await interaction.response.edit_message(embed=embed, view=new_view)


# Main cog class
class Economy(commands.Cog):

    # Class init
    def __init__(self, client):
        self.client = client
        self.economy_logger: logging.Logger = logging.getLogger("economy")

    # Balance Command
    @app_commands.command(name="balance", description="Shows how much currency you currently have")
    async def balance(self, interaction: discord.Interaction) -> None:
        # Log Command
        self.economy_logger.info(f"/balance executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Defer interaction
        await interaction.response.defer()

        # Get balances from api
        response = api_get(f"/economy/balances/me", interaction.user.id)
        content = response.json()

        if response.ok:
            embed: discord.Embed = discord.Embed(title="Balance", color=settings.BLUE)
            embed.set_thumbnail(url=interaction.user.display_avatar.url)

            # Add all balances to a string
            balance_string = ""
            for balance in content['items']:
                amount = balance['balance']
                currency = balance['currency']
                balance_string = balance_string + f"{currency['display_name']}: {'' if currency['prefix'] == None else currency['prefix']}{amount:.{currency['decimal_places']}f}\n"

            embed.add_field(name="", value=balance_string)

        else:
            description = ""
            if content["detail"]:
                description = content["detail"]
            embed: discord.Embed = discord.Embed(title="Error getting balances", description=description, color=settings.RED)

        # Send embed
        embed.set_footer(text=settings.FOOTER)
        await interaction.followup.send(embed=embed)

    # Exchange command
    @app_commands.command(name="exchange", description="Exchange currency to a different currency")
    @app_commands.choices(currency_from=[Choice(name="Carrot Bucks", value="2"),
                                          Choice(name="Mansion Deeds", value="3"),
                                          Choice(name="Sheckles", value="4")],
                          currency_to=[Choice(name="Carrot Bucks", value="2"),
                                        Choice(name="Mansion Deeds", value="3"),
                                        Choice(name="Sheckles", value="4")])
    @app_commands.describe(currency_from="The currency you are converting from")
    @app_commands.describe(currency_to="The currency you are converting to")
    @app_commands.describe(amount="The amount of currency you are converting")
    async def exchange(self, interaction: discord.Interaction, currency_from: str, currency_to: str, amount: float) -> None:
        # Log Command
        self.economy_logger.info(f"/exchange executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Defer interaction
        await interaction.response.defer()

        # Send exchange request to api
        data = {"currency_from_id": int(currency_from),
                "currency_to_id": int(currency_to),
                "amount": int(amount)}
        response = api_post(f"/economy/currencies/exchange", interaction.user.id, data)
        content = response.json()

        if response.ok:
            view = ExchangeView(interaction.user, content)
            embed = await view.refresh()
            await interaction.followup.send(embed=embed, view=view)
        else:
            title = ""
            if content["detail"]:
                title = content["detail"]
            embed: discord.Embed = discord.Embed(title=title, description="", color=settings.RED)
            embed.set_footer(text=settings.FOOTER)
            await interaction.followup.send(embed=embed)

    # Leaderboard command
    @app_commands.command(name="leaderboard", description="Shows which users have the most currency")
    @app_commands.choices(currency=[Choice(name="Aura", value="1"),
                                    Choice(name="Carrot Bucks", value="2"), 
                                    Choice(name="Mansion Deeds", value="3"), 
                                    Choice(name="Sheckles", value="4")])
    @app_commands.describe(currency="The currency the leaderboard will be for")
    async def leaderboard(self, interaction: discord.Interaction, currency: str) -> None:
        # Log Command
        self.economy_logger.info(f"/leaderboard executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Defer interaction
        await interaction.response.defer()

        # Get balances from api
        response = api_get(f"/economy/balances?currency_id={currency}&order_by=-balance&size=10", interaction.user.id)
        content = response.json()

        if response.ok:
            # Get currency from the first balance (as they are all the same)
            currency = content['items'][0]['currency']

            embed: discord.Embed = discord.Embed(title=f"{currency['display_name']} Leaderboard", color=settings.BLUE)
            
            # Add all balances to a string
            user_positions_string = ""
            position = 1
            for balance in content['items']:
                amount = balance['balance']
                user_positions_string = user_positions_string + f":number_{position}: <@{balance['user']['discord_id']}> {'' if currency['prefix'] == None else currency['prefix']}{amount:.{currency['decimal_places']}f}\n"
                position += 1

            embed.add_field(name="", value=user_positions_string, inline=False)

        else:
            description = ""
            if content["detail"]:
                description = content["detail"]
            embed: discord.Embed = discord.Embed(title="Error getting leaderboard", description=description, color=settings.RED)

        # Send embed
        embed.set_footer(text=settings.FOOTER)
        await interaction.followup.send(embed=embed)

    # Blackjack Command
    @app_commands.command(name="blackjack", description="Play blackjack")
    @app_commands.describe(amount="Amount you want to bet")
    @app_commands.choices(currency=[Choice(name="Carrot Bucks", value="2"),
                                    Choice(name="Mansion Deeds", value="3"),
                                    Choice(name="Sheckles", value="4")])
    @app_commands.describe(currency="The currency you are betting")
    @app_commands.describe(amount="The amount of currency you are betting")
    async def blackjack(self, interaction: discord.Interaction, currency: str, amount: float) -> None:
        # Log Command
        self.economy_logger.info(f"/blackjack executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Defer interaction
        await interaction.response.defer()

        # Send blackjack request to api
        data = {"currency_id": int(currency),
                "bet": int(amount)}
        response = api_post(f"/economy/gambling/blackjack", interaction.user.id, data)
        content = response.json()

        if response.ok:
            view = BlackjackView(interaction.user, content)
            embed = await view.refresh()
            await interaction.followup.send(embed=embed, view=view)
        else:
            title = ""
            if content["detail"]:
                title = content["detail"]
            embed: discord.Embed = discord.Embed(title=title, description="", color=settings.RED)
            embed.set_footer(text=settings.FOOTER)
            await interaction.followup.send(embed=embed)

    # Job Command
    @app_commands.command(name="job", description="Manage your job")
    async def job(self, interaction: discord.Interaction) -> None:
        # Log Command
        self.economy_logger.info(f"/job executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Defer interaction
        await interaction.response.defer()

        # Send get job request to api
        response = api_get(f"/economy/jobs/me", interaction.user.id)
        content = response.json()

        if response.ok:
            view = JobView(interaction.user, content)
            embed = await view.refresh()
            await interaction.followup.send(embed=embed, view=view)
        else:
            description = ""
            if content["detail"]:
                description = content["detail"]
            embed: discord.Embed = discord.Embed(title="Error getting job", description=description, color=settings.RED)
            embed.set_footer(text=settings.FOOTER)
            await interaction.followup.send(embed=embed)

    # Work Command
    @app_commands.command(name="work", description="Work")
    async def work(self, interaction: discord.Interaction) -> None:
        # Log Command
        self.economy_logger.info(f"/work executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Defer interaction
        await interaction.response.defer()

        # Send work request to api
        response = api_post(f"/economy/jobs/work", interaction.user.id)
        content = response.json()

        if response.ok:
            # Split response into title and description
            message = content.split(". ")
            embed: discord.Embed = discord.Embed(title=message[0], description=f"{message[1]}", color=settings.GREEN)
        else:
            title = ""
            if content["detail"]:
                title = content["detail"]
            embed: discord.Embed = discord.Embed(title=title, description="", color=settings.RED)

        # Send embed
        embed.set_footer(text=settings.FOOTER)
        await interaction.followup.send(embed=embed)

    # Gift Command
    @app_commands.command(name="gift", description="Gift another user currency")
    @app_commands.describe(target_user="User you are gifting")
    @app_commands.describe(currency="Currency you are gifting")
    @app_commands.describe(amount="The amount of currency being gifted")
    @app_commands.choices(currency=[Choice(name="Carrot Bucks", value="2"),
                                    Choice(name="Mansion Deeds", value="3"),
                                    Choice(name="Sheckles", value="4")])
    async def gift(self, interaction: discord.Interaction, target_user: discord.User, currency: str, amount: float) -> None:
        # Log Command
        self.economy_logger.info(f"/gift executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Defer interaction
        await interaction.response.defer()

        # Send gift request to api
        data = {"discord_id": str(target_user.id),
                "currency_id": int(currency),
                "amount": amount}
        response = api_post(f"/economy/balances/gift", interaction.user.id, data)
        content = response.json()

        if response.ok:
            # Split response into title and description
            message = content.split(". ")
            embed: discord.Embed = discord.Embed(title=message[0], description=f"{message[1]}\n{message[2]}", color=settings.GREEN)
        else:
            description = ""
            if content["detail"]:
                description = content["detail"]
            embed: discord.Embed = discord.Embed(title="Error sending gift", description=description, color=settings.RED)

        # Send embed
        embed.set_footer(text=settings.FOOTER)
        await interaction.followup.send(embed=embed)


# Setup function
async def setup(client):
    await client.add_cog(Economy(client))

# Module Imports
import logging
from datetime import time
from zoneinfo import ZoneInfo
from typing import List
import time
import datetime
import random

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands
from discord.ext import tasks

import pydealer
from scipy.stats import truncnorm

from constants import Constants
import database.operations
from database.models import Currency, UserCurrency

# Format currency
def format_currency(currency):
    if currency == "carrot_bucks": return "Carrot Bucks"
    elif currency == "sheckles": return "Sheckles"
    elif currency == "aura": return "Aura"

# Format card for embed
def format_card(card):
    # Insert correct suit unicode character
    formatted_suit = ""
    match card.suit:
        case "Spades": formatted_suit = "♠"
        case "Hearts": formatted_suit = "♥"
        case "Diamonds": formatted_suit="♦"
        case "Clubs": formatted_suit="♣"
    
    # Insert correct letter for higher cards
    formatted_value = ""
    match card.value:
        case "Ace": formatted_value = "A"
        case "King": formatted_value = "K"
        case "Queen": formatted_value = "Q"
        case "Jack": formatted_value = "J"
        case _: formatted_value = card.value
    return f"{formatted_suit}{formatted_value}"

# Format card numerical value
def calculate_hand_value(deck):
    # Calculate hand value, leave aces
    deck_value = 0
    aces = 0
    for card in deck:
        if card.value in ["King", "Queen", "Jack"]:
            deck_value += 10
        elif card.value == "Ace":
            aces += 1
        else:
            deck_value += int(card.value)
    
    # Aces only worth one if adding 11 goes above 21
    for ace in range(aces):
        if deck_value + 11 > 21:
            deck_value += 1
        else:
            deck_value += 11

    return deck_value

# Views
# Exchange view
class ExchangeView(discord.ui.View):
    def __init__(self, user: discord.User, currency_start: UserCurrency, currency_end: UserCurrency, amount: float):
        super().__init__(timeout=300)
        self.CONSTANTS = Constants()
        self.user = user
        self.currency_start = currency_start
        self.currency_end = currency_end
        self.currency_end_amount_gained = 0
        self.amount = amount
        self.economy_logger: logging.Logger = logging.getLogger("economy")

    # Check that user that started the interaction can interact
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id

    # Update embed
    async def refresh(self) -> discord.Embed:
        # Get exchange rates
        currency_start_exchange_rate = self.currency_start.currency.exchange_rate
        currency_end_exchange_rate = self.currency_end.currency.exchange_rate

        # Calculate relative exchange rate
        relative_rate = currency_start_exchange_rate/currency_end_exchange_rate
        self.currency_end_amount_gained = self.amount * relative_rate
        embed: discord.Embed = discord.Embed(title=f"You are about to convert {self.currency_start.currency.prefix}{self.amount:.{self.currency_start.currency.decimal_places}f} {self.currency_start.currency.display_name} into {self.currency_end.currency.prefix}{self.currency_end_amount_gained:.{self.currency_end.currency.decimal_places}f} {self.currency_end.currency.display_name}", 
                                                description=f"{self.currency_start.currency.prefix}1 {self.currency_start.currency.display_name} is currently equal to {self.currency_end.currency.prefix}{relative_rate:.4f} {self.currency_end.currency.display_name}\nAre you sure you want to do this?",
                                                color=self.CONSTANTS.YELLOW)
        embed.set_footer(text=self.CONSTANTS.FOOTER)
        return embed
    
    # Confirm Button
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Get user balances
        user_balances = database.operations.get_user_balances(interaction.user.id)

        # Update balances
        currency_start_new_balance = 0
        currency_end_new_balance = 0
        for user_balance in user_balances:
            # Decrease currency start
            if user_balance.currency.currency_id == self.currency_start.currency.currency_id:
                currency_start_new_balance = user_balance.balance - self.amount
                database.operations.set_user_balance(interaction.user.id, user_balance.currency.currency_id, currency_start_new_balance)

            # Increase currency end
            if user_balance.currency.currency_id == self.currency_end.currency.currency_id:
                currency_end_new_balance = user_balance.balance + self.currency_end_amount_gained
                database.operations.set_user_balance(interaction.user.id, user_balance.currency.currency_id, currency_end_new_balance)

        # Disable buttons
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

        # Embed
        embed: discord.Embed = discord.Embed(title=f"Converted {self.currency_start.currency.prefix}{self.amount:.{self.currency_start.currency.decimal_places}f} {self.currency_start.currency.display_name} into {self.currency_end.currency.prefix}{self.currency_end_amount_gained:.{self.currency_end.currency.decimal_places}f} {self.currency_end.currency.display_name}", 
                                                description=f"Your {self.currency_start.currency.display_name} balance is now {self.currency_start.currency.prefix}{currency_start_new_balance:.{self.currency_start.currency.decimal_places}f}\nYour {self.currency_end.currency.display_name} balance is now {self.currency_end.currency.prefix}{currency_end_new_balance:.{self.currency_end.currency.decimal_places}f}",
                                                color=self.CONSTANTS.GREEN)
        embed.set_footer(text=self.CONSTANTS.FOOTER)
        await interaction.response.edit_message(embed=embed, view=self)
    
    # Cancel Button
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Disable buttons
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

        embed: discord.Embed = discord.Embed(title=f"Transaction Canceled", color=self.CONSTANTS.RED)
        embed.set_footer(text=self.CONSTANTS.FOOTER)
        await interaction.response.edit_message(embed=embed, view=self)

# Blackjack view
class BlackjackView(discord.ui.View):
    def __init__(self, user: discord.User, currency: Currency, amount: float, deck: dict, user_hand: dict, dealer_hand: dict, user_stood: bool):
        super().__init__(timeout=300)
        self.CONSTANTS = Constants()
        self.user = user
        self.currency = currency
        self.amount = amount
        self.deck = deck
        self.user_hand = user_hand
        self.dealer_hand = dealer_hand
        self.user_stood = user_stood
        self.economy_logger: logging.Logger = logging.getLogger("economy")

    # Check that user that started the interaction can interact
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id
    
    # Game logic and update embed
    async def refresh(self) -> discord.Embed:
        # Calculate hand values
        user_hand_value = calculate_hand_value(self.user_hand)
        dealer_hand_value = calculate_hand_value(self.dealer_hand)

        # If player has stood but dealer is under 17, keep hitting until at least 17
        if self.user_stood == True and dealer_hand_value < 17:
            while dealer_hand_value < 17:
                self.dealer_hand.add(self.deck.deal(1))
                dealer_hand_value = calculate_hand_value(self.dealer_hand)

        # Determine game outcome
        game_outcome = None
        if user_hand_value > 21:
            game_outcome = "Lose"
        elif user_hand_value == 21:
            if dealer_hand_value == 21:
                game_outcome = "Tie"
            else:
                game_outcome = "Win"
        else:
            if dealer_hand_value > 21:
                game_outcome = "Win"
            elif dealer_hand_value == 21:
                game_outcome = "Lose"
            elif dealer_hand_value > user_hand_value and self.user_stood == True:
                game_outcome = "Lose"
            elif user_hand_value > dealer_hand_value and self.user_stood == True and dealer_hand_value >= 17:
                game_outcome = "Win"
            elif user_hand_value == dealer_hand_value and self.user_stood == True:
                game_outcome = "Tie"

        # Format embed and payout user
        if game_outcome != None:
            user_balance = database.operations.get_user_balance(self.user.id, self.currency.currency_id)
            aura_balance = database.operations.get_user_balance(self.user.id, "aura")
            
            if game_outcome == "Win":
                new_currency_balance = user_balance.balance + self.amount
                new_aura_balance = aura_balance.balance + 10

                title = "You Win!"
                description = f"You won {self.currency.prefix}{self.amount:.{self.currency.decimal_places}f} {self.currency.display_name}\nNew balance: {self.currency.prefix}{(new_currency_balance):.{self.currency.decimal_places}f} {self.currency.display_name}"
                color=self.CONSTANTS.GREEN

                database.operations.set_user_balance(self.user.id, self.currency.currency_id, new_currency_balance)
                database.operations.set_user_balance(self.user.id, "aura", new_aura_balance)
                
            elif game_outcome == "Lose":
                new_currency_balance = user_balance.balance - self.amount
                new_aura_balance = aura_balance.balance - 10
                
                title = "Dealer Wins!"
                color=self.CONSTANTS.RED
                description = f"You lost {self.currency.prefix}{self.amount:.{self.currency.decimal_places}f} {self.currency.display_name}\nNew balance: {self.currency.prefix}{new_currency_balance:.{self.currency.decimal_places}f} {self.currency.display_name}"
                database.operations.set_user_balance(self.user.id, self.currency.currency_id, new_currency_balance)
                database.operations.set_user_balance(self.user.id, "aura", new_aura_balance)

            elif game_outcome == "Tie":
                title = "You Tied!"
                description = f"You were refunded {self.currency.prefix}{self.amount:.{self.currency.decimal_places}f} {self.currency.display_name}\nNew balance: ${user_balance.balance:.{self.currency.decimal_places}f} {self.currency.display_name}"
                color=self.CONSTANTS.YELLOW
        else:
            title = "Blackjack"
            description = f"Bet: {self.currency.prefix}{self.amount:.{self.currency.decimal_places}f} {self.currency.display_name}"
            color=self.CONSTANTS.BLUE
        
        # Disable buttons at game end
        if game_outcome != None:
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    item.disabled = True
        
        # Format user cards for embed
        user_hand_formatted = ""
        for user_card in self.user_hand:
            user_hand_formatted = user_hand_formatted + format_card(user_card) + " "

        # Only show dealer's first cards
        dealer_hand_formatted = ""
        if game_outcome != None:
            for dealer_card in self.dealer_hand:
                dealer_hand_formatted = dealer_hand_formatted + format_card(dealer_card) + " "
        else:
            for dealer_card in range(len(self.dealer_hand)):
                if dealer_card == 0:
                    dealer_hand_formatted = format_card(self.dealer_hand[0]) + " "
                else:
                    dealer_hand_formatted = dealer_hand_formatted + "[?]" + " "

        # Create and return embed
        embed: discord.Embed = discord.Embed(title=title, description=description, color=color)
        embed.add_field(name=f"Your Hand ({user_hand_value})", value=user_hand_formatted, inline=False)

        if game_outcome != None:
            embed.add_field(name=f"Dealer's Hand ({dealer_hand_value})", value=dealer_hand_formatted, inline=False)
        else:
            embed.add_field(name=f"Dealer's Hand (?)", value=dealer_hand_formatted, inline=False)
        
        embed.set_thumbnail(url=self.user.display_avatar.url)
        return embed

    # Hit button
    @discord.ui.button(label="Hit", style=discord.ButtonStyle.primary)
    async def hit_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # User Hits
        new_user_hand = self.user_hand
        new_user_hand.add(self.deck.deal(1))

        # Dealer only hits if below 17
        new_dealer_hand = self.dealer_hand
        if calculate_hand_value(self.dealer_hand) < 17:
            new_dealer_hand.add(self.deck.deal(1))
        
        new_view = BlackjackView(self.user, self.currency, self.amount, self.deck, new_user_hand, new_dealer_hand, False)
        embed = await new_view.refresh()
        await interaction.response.edit_message(embed=embed, view=new_view)

    # Stand button
    @discord.ui.button(label="Stand", style=discord.ButtonStyle.primary)
    async def stand_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Dealer only hits if below 17
        new_dealer_hand = self.dealer_hand
        if calculate_hand_value(self.dealer_hand) < 17:
            new_dealer_hand.add(self.deck.deal(1))
        
        new_view = BlackjackView(self.user, self.currency, self.amount, self.deck, self.user_hand, new_dealer_hand, True)
        embed = await new_view.refresh()
        await interaction.response.edit_message(embed=embed, view=new_view)

# Job view
class JobView(discord.ui.View):
    def __init__(self, user: discord.User):
        super().__init__(timeout=300)
        self.user = user
        self.CONSTANTS = Constants()

    # Check that user that started the interaction can interact
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id
    
    # Embed logic
    async def refresh(self) -> discord.Embed:
        # Get user job
        user_job = database.operations.get_user_job(self.user.id)

        if user_job:
            embed: discord.Embed = discord.Embed(title=f"Job: {user_job.job.display_name}", color=self.CONSTANTS.GREEN)
            embed.add_field(name="", value=f"Salary: {user_job.currency.prefix}{(user_job.job.min_pay/user_job.currency.value_multiplier):.{user_job.currency.decimal_places}f} - {user_job.currency.prefix}{(user_job.job.max_pay/user_job.currency.value_multiplier):.{user_job.currency.decimal_places}f} {user_job.currency.display_name} Per Shift\nWork Cooldown: {user_job.job.cooldown}s\nDo /work to work")
        
            # Disable get job button
            for item in self.children:
                if isinstance(item, discord.ui.Button) and item.label == "Get Job":
                    item.disabled = True
        else:
            embed: discord.Embed = discord.Embed(title=f"You do not currently have a job", color=self.CONSTANTS.RED)

            leave_job_cooldown = database.operations.check_cooldown(self.user.id, "leave_job_cooldown")
            if leave_job_cooldown:
                time_left = int((leave_job_cooldown.expiry_timestamp - datetime.datetime.now()).total_seconds())
                if time_left > 1:
                    embed.add_field(name="", value=f"You can apply for another job in {time_left}s")

            # Disable quit job button
            for item in self.children:
                if isinstance(item, discord.ui.Button) and item.label == "Quit Job":
                    item.disabled = True
                if isinstance(item, discord.ui.Button) and item.label == "Get Job" and leave_job_cooldown and time_left > 1:
                    item.disabled = True
        embed.set_thumbnail(url=self.user.display_avatar.url)
        embed.set_footer(text=self.CONSTANTS.FOOTER) 
        return embed
    
    # Get Job Button
    @discord.ui.button(label="Get Job", style=discord.ButtonStyle.primary)
    async def get_job_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Disable buttons
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

        # Give user random job
        database.operations.give_user_random_job(self.user.id)
        new_view = JobView(self.user)
        embed = await new_view.refresh()
        await interaction.response.edit_message(embed=embed, view=new_view)

    # Quit Job
    @discord.ui.button(label="Quit Job", style=discord.ButtonStyle.danger)
    async def quit_job_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Disable buttons
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

        # Remove user job
        database.operations.remove_user_job(self.user.id)

        # Remove previous work cooldown
        database.operations.remove_cooldown(self.user.id, "work_cooldown")

        # Create get job cooldown
        database.operations.create_cooldown(self.user.id, 300, "leave_job_cooldown")

        # Create view
        new_view = JobView(self.user)
        embed = await new_view.refresh()
        await interaction.response.edit_message(embed=embed, view=new_view)

# Main cog class
class Economy(commands.Cog):

    # Class init
    def __init__(self, client):
        self.client = client
        self.CONSTANTS = Constants()
        self.economy_logger: logging.Logger = logging.getLogger("economy")
        self.update_exchange_rates_task.start()

    # Generate a random exchange rate
    async def generate_exchange_rate(self):
        mean = 1
        low = 0.2
        high = 2
        std = 0.4
        a, b = (low - mean) / std, (high - mean) / std
        return truncnorm.rvs(a, b, loc=mean, scale=std)

    # Update currency exchange rates every date at 6 pm
    @tasks.loop(minutes=15)
    async def update_exchange_rates_task(self):
        # Get all currencies
        currencies = database.operations.get_currencies()

        # Update exchange rates
        for currency in currencies:
            if currency.can_exchange:
                new_exchange_rate = await self.generate_exchange_rate()
                database.operations.set_exchange_rate(currency.currency_id, new_exchange_rate * currency.value_multiplier)

    # Balance Command
    @app_commands.command(name="balance", description="Shows how much currency you currently have")
    async def balance(self, interaction: discord.Interaction) -> None:
        # Log Command
        self.economy_logger.info(f"/balance executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Get balance
        user_balances = database.operations.get_user_balances(interaction.user.id)

        # Format balance
        balance_string = ""
        for user_balance in user_balances:
            balance_string = balance_string + f"{user_balance.currency.display_name}: {'' if user_balance.currency.prefix == None else user_balance.currency.prefix}{user_balance.balance:.{user_balance.currency.decimal_places}f}\n"

        # Create embed
        embed: discord.Embed = discord.Embed(title=f"Balance", color=self.CONSTANTS.BLUE)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="", value=balance_string)
        embed.set_footer(text=self.CONSTANTS.FOOTER)

        # Send embed
        await interaction.response.send_message(embed=embed)

    # Exchange command
    @app_commands.command(name="exchange", description="Exchange currency to a different currency")
    @app_commands.choices(currency_start=[Choice(name="Carrot Bucks", value="carrot_bucks"), Choice(name="Sheckles", value="sheckles"), Choice(name="Mansion Deeds", value="mansion_deeds")],
                          currency_end=[Choice(name="Carrot Bucks", value="carrot_bucks"), Choice(name="Sheckles", value="sheckles"), Choice(name="Mansion Deeds", value="mansion_deeds")])
    @app_commands.describe(currency_start="The currency you are converting")
    @app_commands.describe(currency_end="The currency you are converting into")
    @app_commands.describe(amount="The amount of currency you are converting")
    async def exchange(self, interaction: discord.Interaction, currency_start: str, currency_end: str, amount: float) -> None:
        # Log Command
        self.economy_logger.info(f"/exchange executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Get balances
        currency_start = database.operations.get_user_balance(interaction.user.id, currency_start)
        currency_end = database.operations.get_user_balance(interaction.user.id, currency_end)

        # Check if user has enough to convert
        if currency_start.balance < amount:
            embed: discord.Embed = discord.Embed(title=f"Insufficent {currency_start.currency.display_name} balance (have {currency_start.currency.prefix}{currency_start.balance:.{currency_start.currency.decimal_places}f}, need {currency_start.currency.prefix}{amount:.{currency_start.currency.decimal_places}f})", color=self.CONSTANTS.RED)
            embed.set_footer(text=self.CONSTANTS.FOOTER)
            await interaction.response.send_message(embed=embed)
        # Check if user is trying to convert the same currency
        elif currency_start.currency.currency_id == currency_end.currency.currency_id:
            embed: discord.Embed = discord.Embed(title=f"You cannot convert {currency_start.currency.display_name} into {currency_end.currency.display_name}", color=self.CONSTANTS.RED)
            embed.set_footer(text=self.CONSTANTS.FOOTER)
            await interaction.response.send_message(embed=embed)
        else:
            view = ExchangeView(interaction.user, currency_start, currency_end, amount)
            embed = await view.refresh()
            await interaction.response.send_message(embed=embed, view=view)

    # Leaderboard command
    @app_commands.command(name="leaderboard", description="Shows which users have the most currency")
    @app_commands.choices(currency=[
                                    Choice(name="Aura", value="aura"),
                                    Choice(name="Carrot Bucks", value="carrot_bucks"), 
                                    Choice(name="Mansion Deeds", value="mansion_deeds"), 
                                    Choice(name="Sheckles", value="sheckles")
                                    ])
    @app_commands.describe(currency="The currency the leaderboard will be for")
    async def leaderboard(self, interaction: discord.Interaction, currency: str) -> None:
        # Log Command
        self.economy_logger.info(f"/leaderboard executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Get balances
        currency_info = database.operations.get_currency(currency)
        user_balances = database.operations.get_all_balances(currency)

        # Create embed
        embed: discord.Embed = discord.Embed(title=f"{currency_info.display_name} Leaderboard", color=self.CONSTANTS.BLUE)

        user_positions_string = ""
        position = 1
        for balance in user_balances:
            # Add user position to string, with proper prefix and rounding
            user_positions_string = user_positions_string + f":number_{position}: <@{balance.user_id}> {'' if currency_info.prefix == None else currency_info.prefix}{balance.balance:.{currency_info.decimal_places}f}\n"
            position += 1
            # Only show top 10
            if position  == 11:
                break
        embed.add_field(name="", value=user_positions_string, inline=False)
        embed.set_footer(text=self.CONSTANTS.FOOTER)

        # Send embed
        await interaction.response.send_message(embed=embed)

    # Bailout Command
    @app_commands.command(name="bailout", description="Gives you emergency funds if you're broke")
    async def bailout(self, interaction: discord.Interaction) -> None:
        # Log Command
        self.economy_logger.info(f"/bailout executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Get balances
        user_balances = database.operations.get_user_balances(interaction.user.id)

        # Give bailout if user is completely broke
        needs_bailout = True
        for balance in user_balances:
            if balance.balance > 1 and balance.currency.can_gamble == True:
                needs_bailout = False

        # Send embed and update balance if needed
        if needs_bailout:
            database.operations.set_user_balance(interaction.user.id, "carrot_bucks", 20)
            embed: discord.Embed = discord.Embed(title=f"¢20 Carrot Bucks Added To Balance", color=self.CONSTANTS.GREEN)
        else:
            embed: discord.Embed = discord.Embed(title=f"You're not broke enough for a bailout", color=self.CONSTANTS.RED)
        embed.set_footer(text=self.CONSTANTS.FOOTER)

        # Send embed
        await interaction.response.send_message(embed=embed)

    # Blackjack Command
    @app_commands.command(name="blackjack", description="Play blackjack")
    @app_commands.describe(amount="Amount you want to bet")
    @app_commands.choices(currency=[
                                    Choice(name="Carrot Bucks", value="carrot_bucks"), 
                                    Choice(name="Sheckles", value="sheckles"),
                                    Choice(name="Mansion Deeds", value="mansion_deeds"),
                                    ])
    @app_commands.describe(currency="The currency you are betting")
    @app_commands.describe(amount="The amount of currency you are betting")
    async def blackjack(self, interaction: discord.Interaction, currency: str, amount: float) -> None:
        # Log Command
        self.economy_logger.info(f"/blackjack executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Get balance
        user_balance = database.operations.get_user_balance(interaction.user.id, currency)
        
        # Check that user is able to make their bet
        if user_balance.balance < amount:
            embed: discord.Embed = discord.Embed(title=f"Insufficent {user_balance.currency.display_name} balance (have {user_balance.currency.prefix}{user_balance.balance:.{user_balance.currency.decimal_places}f}, need {user_balance.currency.prefix}{amount:.{user_balance.currency.decimal_places}f})", color=self.CONSTANTS.RED)
            embed.set_footer(text=self.CONSTANTS.FOOTER)
            await interaction.response.send_message(embed=embed)
        else:
            deck = pydealer.Deck()
            deck.shuffle()
            user_hand = deck.deal(2)
            dealer_hand = deck.deal(2)
            view = BlackjackView(interaction.user, user_balance.currency, amount, deck, user_hand, dealer_hand, False)
            embed = await view.refresh()
            await interaction.response.send_message(embed=embed, view=view)
    
    # Job Command
    @app_commands.command(name="job", description="Manage your job")
    async def job(self, interaction: discord.Interaction) -> None:
        # Log Command
        self.economy_logger.info(f"/job executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Send embed
        view = JobView(interaction.user)
        embed = await view.refresh()
        await interaction.response.send_message(embed=embed, view=view)

    # Work Command
    @app_commands.command(name="work", description="Work")
    async def work(self, interaction: discord.Interaction) -> None:
        # Log Command
        self.economy_logger.info(f"/work executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Check if user has job
        user_job = database.operations.get_user_job(interaction.user.id)

        if user_job:
            work_cooldown = database.operations.check_cooldown(interaction.user.id, "work_cooldown")

            if work_cooldown:
                time_left = int((work_cooldown.expiry_timestamp - datetime.datetime.now()).total_seconds())
                embed: discord.Embed = discord.Embed(title=f"You may work again in {time_left}s", color=self.CONSTANTS.RED)
            else:
                # Pay user
                user_balances = database.operations.get_user_balances(interaction.user.id)
                for balance in user_balances:
                    if balance.currency_id == user_job.currency_id:
                        pay_amount = random.randint(user_job.job.min_pay, user_job.job.max_pay) / user_job.currency.value_multiplier
                        database.operations.set_user_balance(interaction.user.id, balance.currency_id, balance.balance + pay_amount)
                    
                # Create Embed
                embed: discord.Embed = discord.Embed(title=f"You went to work and were paid {user_job.currency.prefix}{pay_amount} {user_job.currency.display_name}", description=f"You may work again in {user_job.job.cooldown}s", color=self.CONSTANTS.GREEN)
                database.operations.create_cooldown(user_id=interaction.user.id, duration=user_job.job.cooldown, cooldown_type="work_cooldown")
        else:
            embed: discord.Embed = discord.Embed(title=f"You do not currently have a job", description=f"You can get one using /job", color=self.CONSTANTS.RED)

        await interaction.response.send_message(embed=embed)


# Setup function
async def setup(client):
    await client.add_cog(Economy(client))
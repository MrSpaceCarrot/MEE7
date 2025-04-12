# Module Imports
import logging
from datetime import time
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands
from discord.ext import tasks

import pydealer
from scipy.stats import truncnorm

from constants import Constants
import dbmanager

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
    def __init__(self, user: discord.User, currency_start: str, currency_end: str, amount: float):
        super().__init__(timeout=300)
        self.CONSTANTS = Constants()
        self.user = user
        self.currency_start = currency_start
        self.currency_start_formatted = ""
        self.currency_end = currency_end
        self.currency_end_formatted = ""
        self.currency_end_amount_gained = 0
        self.amount = amount
        self.economy_logger: logging.Logger = logging.getLogger("economy")

    # Check that user that started the interaction can interact
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id

    # Update embed
    async def refresh(self) -> discord.Embed:
        # Get exchange rates
        exchange_rates = dbmanager.get_all_exchange_rates()

        # Format currencies
        self.currency_start_formatted = format_currency(self.currency_start)
        self.currency_end_formatted = format_currency(self.currency_end)
        
        # Get starting currency exchange rate
        currency_start_exchange_rate = 0
        for rate in exchange_rates:
            if rate["name"] == self.currency_start:
                currency_start_exchange_rate = rate["exchange_rate"]

        # Get exchange rate of currency being gained
        currency_end_exchange_rate = 0
        for rate in exchange_rates:
            if rate["name"] == self.currency_end:
                currency_end_exchange_rate = rate["exchange_rate"]

        # Calculate relative exchange rate
        relative_rate = currency_start_exchange_rate/currency_end_exchange_rate
        self.currency_end_amount_gained = self.amount * relative_rate
        embed: discord.Embed = discord.Embed(title=f"You are about to convert ${self.amount:.2f} {self.currency_start_formatted} into ${self.currency_end_amount_gained:.2f} {self.currency_end_formatted}", 
                                                description=f"$1 {self.currency_start_formatted} is currently equal to ${relative_rate:.2f} {self.currency_end_formatted}\nAre you sure you want to do this?",
                                                color=self.CONSTANTS.YELLOW)
        embed.set_footer(text=self.CONSTANTS.FOOTER)
        return embed
    
    # Confirm Button
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Make changes
        user_balance = dbmanager.get_user_balance(interaction.user.id)
        currency_start_new_balance = user_balance[self.currency_start] - self.amount
        dbmanager.set_user_balance(self.user.id, self.currency_start, currency_start_new_balance)

        currency_end_new_balance = user_balance[self.currency_end] + self.currency_end_amount_gained
        dbmanager.set_user_balance(self.user.id, self.currency_end, currency_end_new_balance)

        # Disable buttons
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

        # Embed
        embed: discord.Embed = discord.Embed(title=f"Converted ${self.amount:.2f} {self.currency_start_formatted} into ${self.currency_end_amount_gained:.2f} {self.currency_end_formatted}", 
                                                description=f"Your {self.currency_start_formatted} balance is now ${currency_start_new_balance:.2f}\nYour {self.currency_end_formatted} balance is now ${currency_end_new_balance:.2f}",
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
    def __init__(self, user: discord.User, currency: str, amount: float, deck: dict, user_hand: dict, dealer_hand: dict, user_stood: bool):
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

        formatted_currency = format_currency(self.currency)

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
            user_balance = dbmanager.get_user_balance(self.user.id)
            user_currency_amount = user_balance[self.currency]
            user_aura_amount = user_balance["aura"]
            if game_outcome == "Win":
                title = "You Win!"
                description = f"You won ${self.amount:.2f} {formatted_currency}\nNew balance: ${(user_currency_amount + self.amount):.2f} {formatted_currency}"
                color=self.CONSTANTS.GREEN
                dbmanager.set_user_balance(self.user.id, self.currency, user_balance[self.currency] + self.amount)
                dbmanager.set_user_balance(self.user.id, "aura", user_aura_amount + 10)

            elif game_outcome == "Lose":
                title = "Dealer Wins!"
                if user_currency_amount - self.amount > 0:
                    description = f"You lost ${self.amount:.2f} {formatted_currency}\nNew balance: ${(user_currency_amount - self.amount):.2f} {formatted_currency}"
                else:
                    description = f"You lost ${self.amount:.2f} {formatted_currency}\nNew balance: ${(user_currency_amount - self.amount):.2f} {formatted_currency}\nYou are now eligible for a bailout (/bailout)"
                color=self.CONSTANTS.RED
                dbmanager.set_user_balance(self.user.id, self.currency, user_currency_amount - self.amount)
                dbmanager.set_user_balance(self.user.id, "aura", user_aura_amount - 10)

            elif game_outcome == "Tie":
                title = "You Tied!"
                description = f"You were refunded ${self.amount:.2f} {formatted_currency}\nNew balance: ${user_currency_amount:.2f} {formatted_currency}"
                color=self.CONSTANTS.YELLOW
        else:
            title = "Blackjack"
            description = f"Bet: ${self.amount:.2f} {formatted_currency}"
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


# Main cog class
class Economy(commands.Cog):

    # Class init
    def __init__(self, client):
        self.client = client
        self.CONSTANTS = Constants()
        self.economy_logger: logging.Logger = logging.getLogger("economy")
        self.update_exchange_rate_task.start()

    # Update currency exchange rates every date at 6 pm
    @tasks.loop(name="update_exchange_rate_task", time=time(hour=18, minute=0, tzinfo=ZoneInfo("Pacific/Auckland")))
    async def update_exchange_rate_task(self):
        # Amount changed is generated using a normal distribution
        mean = 1
        low = 0.2
        high = 2
        std = 0.4
        a, b = (low - mean) / std, (high - mean) / std
        dbmanager.update_exchange_rate("carrot_bucks", truncnorm.rvs(a, b, loc=mean, scale=std))
        dbmanager.update_exchange_rate("sheckles", truncnorm.rvs(a, b, loc=mean, scale=std))

    # Balance Command
    @app_commands.command(name="balance", description="Shows how much currency you currently have")
    async def balance(self, interaction: discord.Interaction) -> None:
        # Log Command
        self.economy_logger.info(f"/balance executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Get balance
        user_balance = dbmanager.get_user_balance(interaction.user.id)

        # Create embed
        embed: discord.Embed = discord.Embed(title=f"Balance", color=self.CONSTANTS.BLUE)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="", value=f"Carrot Bucks: ${user_balance['carrot_bucks']:.2f}\nSheckles: ${user_balance['sheckles']:.2f}\nAura: {user_balance['aura']}")
        embed.set_footer(text=self.CONSTANTS.FOOTER)

        # Send embed
        await interaction.response.send_message(embed=embed)

    # Exchange command
    @app_commands.command(name="exchange", description="Exchange currency to a different currency")
    @app_commands.choices(currency_start=[Choice(name="Carrot Bucks", value="carrot_bucks"), Choice(name="Sheckles", value="sheckles")],
                          currency_end=[Choice(name="Carrot Bucks", value="carrot_bucks"), Choice(name="Sheckles", value="sheckles")])
    @app_commands.describe(currency_start="The currency you are converting")
    @app_commands.describe(currency_end="The currency you are converting into")
    @app_commands.describe(amount="The amount of currency you are converting")
    async def exchange(self, interaction: discord.Interaction, currency_start: str, currency_end: str, amount: float) -> None:
        # Log Command
        self.economy_logger.info(f"/exchange executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Get balance
        user_balance = dbmanager.get_user_balance(interaction.user.id)

        # Format currencies
        currency_start_formatted = format_currency(currency_start)
        currency_end_formatted = format_currency(currency_end)

        # Check if user has enough to convert
        if user_balance[currency_start] < amount:
            embed: discord.Embed = discord.Embed(title=f"Insufficent {currency_start_formatted} balance (have ${user_balance[currency_start]}, need ${amount})", color=self.CONSTANTS.RED)
            embed.set_footer(text=self.CONSTANTS.FOOTER)
            await interaction.response.send_message(embed=embed)
        # Check if user is trying to convert the same currency
        elif currency_start == currency_end:
            embed: discord.Embed = discord.Embed(title=f"You cannot convert {currency_start_formatted} into {currency_end_formatted}", color=self.CONSTANTS.RED)
            embed.set_footer(text=self.CONSTANTS.FOOTER)
            await interaction.response.send_message(embed=embed)
        else:
            view = ExchangeView(interaction.user, currency_start, currency_end, amount)
            embed = await view.refresh()
            await interaction.response.send_message(embed=embed, view=view)

    # Leaderboard command
    @app_commands.command(name="leaderboard", description="Shows which users have the most currency")
    @app_commands.choices(currency=[
                                    Choice(name="Carrot Bucks", value="carrot_bucks"), 
                                    Choice(name="Sheckles", value="sheckles"),
                                    Choice(name="Aura", value="aura")])
    @app_commands.describe(currency="The currency the leaderboard will be for")
    async def leaderboard(self, interaction: discord.Interaction, currency: str) -> None:
        # Log Command
        self.economy_logger.info(f"/leaderboard executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Get balances, sort
        user_balances = dbmanager.get_all_balances()
        user_balances = sorted(user_balances, key=lambda x: x[currency], reverse=True)

        # Create embed
        embed: discord.Embed = discord.Embed(title=f"{format_currency(currency)} Leaderboard", color=self.CONSTANTS.BLUE)

        user_positions = ""
        position = 1
        for user in user_balances:
            # Add user position to string, only add $ if not showing aura
            user_positions = user_positions + f":number_{position}: <@{user['user_id']}> {'$' if currency != 'aura' else ''}{user[currency]:.2f}\n"
            position += 1
            # Only show top 10
            if position  == 11:
                break
        embed.add_field(name="", value=user_positions, inline=False)
        embed.set_footer(text=self.CONSTANTS.FOOTER)

        # Send embed
        await interaction.response.send_message(embed=embed)

    # Bailout Command
    @app_commands.command(name="bailout", description="Gives you emergency funds if you're broke")
    async def bailout(self, interaction: discord.Interaction) -> None:
        # Log Command
        self.economy_logger.info(f"/bailout executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Bailout
        user_balance = dbmanager.get_user_balance(interaction.user.id)
        if user_balance["carrot_bucks"] < 1 and user_balance["sheckles"] < 1:
            dbmanager.set_user_balance(interaction.user.id, "carrot_bucks", user_balance["carrot_bucks"] + 20)
            embed: discord.Embed = discord.Embed(title=f"$20 Carrot Bucks Added To Balance", color=self.CONSTANTS.GREEN)
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
                                    Choice(name="Sheckles", value="sheckles")])
    @app_commands.describe(currency="The currency you are betting")
    @app_commands.describe(amount="The amount of currency you are betting")
    async def blackjack(self, interaction: discord.Interaction, currency: str, amount: float) -> None:
        # Log Command
        self.economy_logger.info(f"/blackjack executed by {interaction.user} in {interaction.guild} #{interaction.channel}")

        # Get balance
        user_balance = dbmanager.get_user_balance(interaction.user.id)
        
        # Check that user is able to make their bet
        if user_balance[currency] < amount:
            embed: discord.Embed = discord.Embed(title=f"Insufficent balance (have ${user_balance[currency]}, need {amount})", color=self.CONSTANTS.RED)
            embed.set_footer(text=self.CONSTANTS.FOOTER)
            await interaction.response.send_message(embed=embed)
        else:
            deck = pydealer.Deck()
            deck.shuffle()
            user_hand = deck.deal(2)
            dealer_hand = deck.deal(2)
            view = BlackjackView(interaction.user, currency, amount, deck, user_hand, dealer_hand, False)
            embed = await view.refresh()
            await interaction.response.send_message(embed=embed, view=view)
        

# Setup function
async def setup(client):
    await client.add_cog(Economy(client))
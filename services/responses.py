# Module Imports
import random
# Handle response function
def handle_response(message: str, userid: str) -> str:
    # Lower mesage
    message = message.lower()

    # Handle response
    banned: str = handle_banned_words(message, userid)
    custom_response: str = handle_custom_response(message, userid)

    # Return response if either function returned anything
    if banned != None:
        return banned
    elif custom_response != None:
        return custom_response
    else:
        return None
    
# Handle banned words function
def handle_banned_words(message: str, userid: str) -> str:
    # List of all banned words
    banned_words = []

    # If message contains any of these words, delete message and send message from bot
    if message in banned_words:
        return "DELETE"
    

# Handle custom response function
def handle_custom_response(message: str, userid: str) -> str:
    # RE-ADD RANDOM AURA GAIN / LOSS
    # TO DO
    """
    random_number = random.randint(1, 100)
    if random_number >= 80:
        database.operations.populate_user_currencies(user_id=userid)
        user_aura_balance = database.operations.get_user_balance(userid, "aura")
        database.operations.set_user_balance(userid, "aura", user_aura_balance.balance + 10)
    elif random_number <= 10:
        database.operations.populate_user_currencies(user_id=userid)
        user_aura_balance = database.operations.get_user_balance(userid, "aura")
        database.operations.set_user_balance(userid, "aura", user_aura_balance.balance - 10)
    """

    if message == "wafflehipponuts":
        return "Congrats! You found this very obscure response!"

    elif "i made mee7" in message:
        if userid == "725251028999602239":
            return "yea"
        else:
            return "No you didn't"
        
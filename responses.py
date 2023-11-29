# Handle response function
def handle_response(message, userid) -> str:
    # Lower mesage
    message = message.lower()

    # Handle response
    banned = handle_banned_words(message,userid)
    custom_response = handle_custom_response(message, userid)

    # Return response if either function returned anything
    if banned != None:
        return banned
    elif custom_response != None:
        return custom_response
    else:
        return None
    
# Handle banned words function
def handle_banned_words(message, userid) -> str:
    # List of all banned words
    banned_words = [
        "https://tenor.com/view/fnf-fridaynightfunkin-fnf-mod-fnf-players-be-like-furries-be-like-gif-25259051"
    ]

    # If message contains any of these words, delete message and send message from bot
    if message in banned_words:
        return "DELETE"
    

# Handle custom response function
def handle_custom_response(message, userid) -> str:
    # If/else of custom responses from bot
    if message == "wafflehipponuts":
        return "Congrats! You found this very obscure response!"

    elif "i made mee7" in message:
        if userid == "725251028999602239":
            return "yea"
        else:
            return "No you didn't"
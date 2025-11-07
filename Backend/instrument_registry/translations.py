from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password

# Translates password validation error messages
def translate_password_error(password, lang='en'):
    try:
        validate_password(password)
        return None  # No error
    except ValidationError as e:
        e_msg = e.messages[0]
        return map_password_error_message(e_msg, lang)


def map_password_error_message(message, lang='en'):
    message_lower = message.lower()

    if lang == 'fi':
        if "too short" in message_lower:
            return "Salasanan tulee sisältää vähintään 8 merkkiä"
        elif "too common" in message_lower:
            return "Salasana on liian yleinen"
        elif "entirely numeric" in message_lower:
            return "Salasana ei saa koostua pelkästään numeroista"
        elif "too similar" in message_lower:
            return "Salasana on liian samanlainen kuin käyttäjätunnus"
        else:
            return "Virhe salasanan vahvistuksessa."
    else:
        if "too short" in message_lower:
            return "Password must contain at least 8 characters"
        elif "too common" in message_lower:
            return "Password is too common"
        elif "entirely numeric" in message_lower:
            return "Password cannot be entirely numeric"
        elif "too similar" in message_lower:
            return "Password is too similar to the username"
        else:
            return "Error validating password."
import random
import string

def generate_random_id():
    """Generates a random 3 letter - 3 letter id like AAA-AAA"""
    letters = string.ascii_uppercase
    first_part = ''.join(random.choices(letters, k=3))
    second_part = ''.join(random.choices(letters, k=3))
    return f"{first_part}-{second_part}"

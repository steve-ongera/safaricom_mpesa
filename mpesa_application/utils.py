import random
import string

def generate_transaction_id():
    """Generate a unique 10-character alphanumeric transaction ID."""
    characters = string.ascii_uppercase + string.digits  # A-Z, 0-9
    return ''.join(random.choices(characters, k=10))

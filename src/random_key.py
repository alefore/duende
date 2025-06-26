import random
import string

def GenerateRandomKey(length: int = 20) -> str:
    """Generate a random key of specified length."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

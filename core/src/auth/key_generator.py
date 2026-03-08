"""API key generation and validation utilities."""

import hashlib
import secrets
import string

# Base62 alphabet (alphanumeric characters)
ALPHABET = string.ascii_letters + string.digits

# Key format constants
KEY_PREFIX = "convoy_sk_"
KEY_LENGTH = 32  # Random portion length
FULL_KEY_LENGTH = len(KEY_PREFIX) + KEY_LENGTH  # Total key length


def generate_api_key() -> tuple[str, str, str]:
    """
    Generate a new API key.
    
    Returns:
        tuple: (full_key, key_prefix, key_hash)
            - full_key: The complete API key to give to the user (only shown once)
            - key_prefix: First 12 chars for identification
            - key_hash: SHA-256 hash for storage
    
    Example:
        >>> full_key, prefix, hash = generate_api_key()
        >>> full_key
        'convoy_sk_7kB9mN2xP4qR8sT1vW3yZ6aD5eF0gH'
        >>> prefix
        'convoy_sk_7k'
        >>> len(hash)
        64
    """
    # Generate random portion using cryptographically secure random
    random_part = ''.join(secrets.choice(ALPHABET) for _ in range(KEY_LENGTH))
    
    # Construct full key
    full_key = f"{KEY_PREFIX}{random_part}"
    
    # Create prefix for identification (first 12 chars)
    key_prefix = full_key[:12]
    
    # Hash for storage using SHA-256
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    
    return full_key, key_prefix, key_hash


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key for lookup.
    
    Args:
        api_key: The full API key to hash
        
    Returns:
        SHA-256 hash of the API key as a hex string
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def validate_key_format(api_key: str) -> bool:
    """
    Validate that a key matches the expected format.
    
    Args:
        api_key: The API key to validate
        
    Returns:
        True if the key format is valid, False otherwise
    """
    if not api_key:
        return False
    
    if not api_key.startswith(KEY_PREFIX):
        return False
    
    if len(api_key) != FULL_KEY_LENGTH:
        return False
    
    # Check that the random portion only contains valid characters
    random_part = api_key[len(KEY_PREFIX):]
    return all(c in ALPHABET for c in random_part)

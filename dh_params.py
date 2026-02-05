"""
Common utilities and parameters for Diffie-Hellman Key Exchange demonstrations.
Contains safe primes and helper functions used across all scripts.
"""

import os
import hashlib

# RFC 3526 2048-bit MODP Group - This is a well-known safe prime
# Safe prime means p = 2q + 1 where q is also prime
# This makes the discrete logarithm problem computationally hard
PRIME_2048 = int(
    "FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD1"
    "29024E088A67CC74020BBEA63B139B22514A08798E3404DD"
    "EF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245"
    "E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7ED"
    "EE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3D"
    "C2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F"
    "83655D23DCA3AD961C62F356208552BB9ED529077096966D"
    "670C354E4ABC9804F1746C08CA18217C32905E462E36CE3B"
    "E39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9"
    "DE2BCBF6955817183995497CEA956AE515D2261898FA0510"
    "15728E5A8AACAA68FFFFFFFFFFFFFFFF", 16
)

# RFC 3526 1024-bit MODP Group - smaller for faster demos
PRIME_1024 = int(
    "FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD1"
    "29024E088A67CC74020BBEA63B139B22514A08798E3404DD"
    "EF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245"
    "E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7ED"
    "EE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3D"
    "C2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F"
    "83655D23DCA3AD961C62F356208552BB9ED529077096966D"
    "670C354E4ABC9804F1746C08CA237327FFFFFFFFFFFFFFFF", 16
)

# Small prime for demonstration of weak parameters
# With such a small prime, the discrete log problem is trivial to solve
PRIME_WEAK = 23

# Generator value - typically 2 or 5 for safe primes
GENERATOR = 2


def get_dh_params(bit_length=2048):
    """
    Returns standard Diffie-Hellman parameters (p, g).
    
    Args:
        bit_length: Size of prime in bits (1024, 2048, or 'weak')
    
    Returns:
        tuple: (prime modulus p, generator g)
    
    The security of DHKE relies on the discrete logarithm problem:
    Given g, p, and A = g^a mod p, it's computationally infeasible 
    to find 'a' when p is a large safe prime.
    """
    if bit_length == 2048:
        return PRIME_2048, GENERATOR
    elif bit_length == 1024:
        return PRIME_1024, GENERATOR
    elif bit_length == "weak":
        return PRIME_WEAK, 5  # Use g=5 for the small prime
    else:
        raise ValueError(f"Unsupported bit length: {bit_length}")


def generate_private_key(p, secure=True):
    """
    Generate a private key for DHKE.
    
    Args:
        p: Prime modulus
        secure: If True, uses os.urandom (cryptographically secure)
                If False, uses less secure random for demonstration
    
    Returns:
        int: Private key in range [1, p-2]
    
    Note: The private key must be kept secret! 
    Security depends on this value being unpredictable.
    """
    if secure:
        # Use cryptographically secure random number generator
        # This ensures the private key cannot be predicted
        random_bytes = os.urandom(256 // 8)  # 256 bits of entropy
        private_key = int.from_bytes(random_bytes, 'big')
        # Ensure key is in valid range [1, p-2]
        private_key = (private_key % (p - 2)) + 1
    else:
        # Less secure version for demonstration purposes only
        import random
        private_key = random.randint(1, p - 2)
    
    return private_key


def compute_public_key(g, private_key, p):
    """
    Compute public key from private key.
    
    Args:
        g: Generator
        private_key: Secret exponent
        p: Prime modulus
    
    Returns:
        int: Public key = g^private_key mod p
    
    This uses modular exponentiation which is efficient even for large numbers.
    Python's built-in pow() with three arguments uses fast exponentiation.
    """
    return pow(g, private_key, p)


def compute_shared_secret(public_key, private_key, p):
    """
    Compute the shared secret from other party's public key.
    
    Args:
        public_key: Other party's public value
        private_key: This party's private exponent
        p: Prime modulus
    
    Returns:
        int: Shared secret = public_key^private_key mod p
    
    Mathematical proof that both parties get the same value:
    Alice computes: B^a mod p = (g^b)^a mod p = g^(ab) mod p
    Bob computes: A^b mod p = (g^a)^b mod p = g^(ab) mod p
    Therefore both compute the same shared secret!
    """
    return pow(public_key, private_key, p)


def derive_key(shared_secret):
    """
    Derive a symmetric encryption key from the shared secret.
    
    Args:
        shared_secret: The agreed-upon secret value
    
    Returns:
        bytes: 32-byte key suitable for encryption
    
    We hash the shared secret to get a uniformly distributed key.
    SHA-256 ensures the key doesn't leak information about the secret.
    """
    secret_bytes = str(shared_secret).encode('utf-8')
    return hashlib.sha256(secret_bytes).digest()


def simple_encrypt(message, key):
    """
    Simple XOR-based encryption for demonstration purposes.
    
    Args:
        message: String message to encrypt
        key: Bytes key from derive_key()
    
    Returns:
        bytes: Encrypted message
    
    NOTE: This is for educational purposes only!
    In production, use proper authenticated encryption (AES-GCM, ChaCha20-Poly1305).
    We keep it simple to focus on the key exchange, not the encryption.
    """
    message_bytes = message.encode('utf-8')
    encrypted = bytearray()
    
    for i, byte in enumerate(message_bytes):
        # XOR each byte with corresponding key byte (cycling through key)
        encrypted.append(byte ^ key[i % len(key)])
    
    return bytes(encrypted)


def simple_decrypt(encrypted_message, key):
    """
    Decrypt XOR-encrypted message.
    
    XOR is its own inverse: (M XOR K) XOR K = M
    So decryption is the same operation as encryption.
    """
    decrypted = bytearray()
    
    for i, byte in enumerate(encrypted_message):
        decrypted.append(byte ^ key[i % len(key)])
    
    return decrypted.decode('utf-8')


def brute_force_discrete_log(g, public_key, p):
    """
    Solve discrete logarithm by brute force.
    
    Given g, public_key, and p, find x such that g^x mod p = public_key.
    This only works for small primes - demonstrating why large primes are needed!
    
    Args:
        g: Generator
        public_key: Target value
        p: Prime modulus
    
    Returns:
        int: Private key x, or None if not found
    
    Time complexity: O(p) - linear search through all possible exponents.
    For large primes (1024+ bits), this takes longer than the age of the universe!
    """
    for x in range(1, p):
        if pow(g, x, p) == public_key:
            return x
    return None


def validate_params(p, g):
    """
    Basic validation of DH parameters.
    
    Checks:
    - p is positive and large enough
    - g is in valid range [2, p-2]
    
    More thorough checks would verify p is prime and g is a generator,
    but we trust our pre-defined parameters.
    """
    if p < 2:
        raise ValueError("Prime must be at least 2")
    if g < 2 or g >= p - 1:
        raise ValueError(f"Generator must be in range [2, {p-2}]")
    return True


if __name__ == "__main__":
    # Quick test of the utilities
    print("Testing DH utilities...")
    
    # Test with 1024-bit parameters
    p, g = get_dh_params(1024)
    print(f"Prime (1024-bit): {p}")
    print(f"Generator: {g}")
    
    # Simulate a key exchange
    alice_private = generate_private_key(p)
    alice_public = compute_public_key(g, alice_private, p)
    
    bob_private = generate_private_key(p)
    bob_public = compute_public_key(g, bob_private, p)
    
    # Both compute shared secret
    alice_shared = compute_shared_secret(bob_public, alice_private, p)
    bob_shared = compute_shared_secret(alice_public, bob_private, p)
    
    print(f"\nAlice's shared secret matches Bob's: {alice_shared == bob_shared}")
    
    # Test encryption
    key = derive_key(alice_shared)
    message = "Hello from Alice!"
    encrypted = simple_encrypt(message, key)
    decrypted = simple_decrypt(encrypted, key)
    
    print(f"Original: {message}")
    print(f"Decrypted: {decrypted}")
    print(f"Encryption works: {message == decrypted}")
    
    # Test weak parameters
    print("\n--- Testing weak parameters ---")
    p_weak, g_weak = get_dh_params("weak")
    private_weak = 17
    public_weak = compute_public_key(g_weak, private_weak, p_weak)
    print(f"Weak prime: {p_weak}, generator: {g_weak}")
    print(f"Public key for private={private_weak}: {public_weak}")
    
    # Try to crack it
    cracked = brute_force_discrete_log(g_weak, public_weak, p_weak)
    print(f"Brute force found private key: {cracked}")
    print(f"Attack successful: {cracked == private_weak}")

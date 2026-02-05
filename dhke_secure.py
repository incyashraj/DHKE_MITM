"""
Secure Diffie-Hellman Key Exchange Demonstration

This script simulates a secure key exchange between Alice (client) and Bob (server)
over a network using sockets. It demonstrates how DHKE allows two parties to 
establish a shared secret over an insecure channel without prior shared secrets.

The protocol:
1. Alice and Bob agree on public parameters (p, g)
2. Alice generates private key 'a', computes public key A = g^a mod p
3. Bob generates private key 'b', computes public key B = g^b mod p
4. They exchange public keys over the network
5. Both compute shared secret: s = g^(ab) mod p
6. Use shared secret to encrypt/decrypt messages

Usage:
    Terminal 1 (Bob - server):  python dhke_secure.py --bob
    Terminal 2 (Alice - client): python dhke_secure.py --alice
"""

import socket
import json
import argparse
import sys
import time
from dh_params import (
    get_dh_params, generate_private_key, compute_public_key,
    compute_shared_secret, derive_key, simple_encrypt, simple_decrypt
)

# Network configuration
HOST = '127.0.0.1'  # localhost for simulation
PORT = 5000


class Alice:
    """
    Alice initiates the key exchange (client side).
    She wants to securely communicate with Bob.
    """
    
    def __init__(self, bit_length=2048):
        self.bit_length = bit_length
        self.p, self.g = get_dh_params(bit_length)
        self.private_key = None
        self.public_key = None
        self.shared_secret = None
        self.encryption_key = None
        
    def generate_keys(self):
        """Generate Alice's private and public keys."""
        print("[Alice] Generating private key...")
        self.private_key = generate_private_key(self.p, secure=True)
        print(f"[Alice] Private key generated (keeping it secret!)")
        
        print("[Alice] Computing public key...")
        self.public_key = compute_public_key(self.g, self.private_key, self.p)
        print(f"[Alice] Public key: {self.public_key}")
        
    def compute_shared(self, bob_public_key):
        """Compute shared secret using Bob's public key."""
        print(f"[Alice] Received Bob's public key: {bob_public_key}")
        print("[Alice] Computing shared secret...")
        
        # This is where the magic happens!
        # Alice computes: s = B^a mod p = (g^b)^a mod p = g^(ab) mod p
        self.shared_secret = compute_shared_secret(
            bob_public_key, self.private_key, self.p
        )
        
        print(f"[Alice] Shared secret computed: {self.shared_secret}")
        
        # Derive encryption key from shared secret
        self.encryption_key = derive_key(self.shared_secret)
        print(f"[Alice] Derived encryption key (32 bytes)")
        
    def send_encrypted_message(self, message):
        """Encrypt a message using the shared key."""
        encrypted = simple_encrypt(message, self.encryption_key)
        print(f"[Alice] Encrypted message: {encrypted.hex()}")
        return encrypted
    
    def receive_encrypted_message(self, encrypted):
        """Decrypt a message using the shared key."""
        decrypted = simple_decrypt(encrypted, self.encryption_key)
        print(f"[Alice] Decrypted message: {decrypted}")
        return decrypted
    
    def run(self):
        """Run Alice's side of the protocol."""
        print("=" * 60)
        print("ALICE - Starting Secure DHKE Demo")
        print("=" * 60)
        
        # Generate keys
        self.generate_keys()
        
        # Connect to Bob
        print(f"\n[Alice] Connecting to Bob at {HOST}:{PORT}...")
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        try:
            client_socket.connect((HOST, PORT))
            print("[Alice] Connected to Bob!")
            
            # Step 1: Send public parameters and Alice's public key to Bob
            print("\n--- Step 1: Sending public parameters and public key ---")
            message = {
                'p': self.p,
                'g': self.g,
                'public_key': self.public_key
            }
            client_socket.send(json.dumps(message).encode('utf-8'))
            print(f"[Alice] Sent (p, g, A) to Bob")
            
            # Step 2: Receive Bob's public key
            print("\n--- Step 2: Receiving Bob's public key ---")
            data = client_socket.recv(4096)
            response = json.loads(data.decode('utf-8'))
            bob_public_key = response['public_key']
            
            # Step 3: Compute shared secret
            print("\n--- Step 3: Computing shared secret ---")
            self.compute_shared(bob_public_key)
            
            # Step 4: Send encrypted message to Bob
            print("\n--- Step 4: Sending encrypted message ---")
            message_to_send = "Hello Bob! This is Alice. Our secret channel is established!"
            encrypted_msg = self.send_encrypted_message(message_to_send)
            
            client_socket.send(len(encrypted_msg).to_bytes(4, 'big'))
            client_socket.send(encrypted_msg)
            
            # Step 5: Receive encrypted response from Bob
            print("\n--- Step 5: Receiving encrypted response ---")
            msg_length = int.from_bytes(client_socket.recv(4), 'big')
            encrypted_response = client_socket.recv(msg_length)
            
            print(f"[Alice] Received encrypted message: {encrypted_response.hex()}")
            decrypted_response = self.receive_encrypted_message(encrypted_response)
            
            print("\n" + "=" * 60)
            print("SUCCESS! Alice and Bob established secure communication!")
            print(f"Original message sent: {message_to_send}")
            print(f"Message from Bob: {decrypted_response}")
            print("=" * 60)
            
        except ConnectionRefusedError:
            print("\n[ERROR] Could not connect to Bob. Make sure Bob is running first!")
            print("Run: python dhke_secure.py --bob")
            sys.exit(1)
        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
        finally:
            client_socket.close()
            print("\n[Alice] Connection closed.")


class Bob:
    """
    Bob receives the key exchange request (server side).
    He responds to Alice's request to establish secure communication.
    """
    
    def __init__(self):
        self.p = None
        self.g = None
        self.private_key = None
        self.public_key = None
        self.shared_secret = None
        self.encryption_key = None
        
    def receive_params_and_generate_keys(self, p, g):
        """Receive DH parameters and generate Bob's keys."""
        self.p = p
        self.g = g
        
        print(f"[Bob] Received parameters: p (length: {self.p.bit_length()} bits), g={self.g}")
        print("[Bob] Generating private key...")
        
        self.private_key = generate_private_key(self.p, secure=True)
        print(f"[Bob] Private key generated (keeping it secret!)")
        
        print("[Bob] Computing public key...")
        self.public_key = compute_public_key(self.g, self.private_key, self.p)
        print(f"[Bob] Public key: {self.public_key}")
        
    def compute_shared(self, alice_public_key):
        """Compute shared secret using Alice's public key."""
        print(f"[Bob] Received Alice's public key: {alice_public_key}")
        print("[Bob] Computing shared secret...")
        
        # Bob computes: s = A^b mod p = (g^a)^b mod p = g^(ab) mod p
        # This equals what Alice computes!
        self.shared_secret = compute_shared_secret(
            alice_public_key, self.private_key, self.p
        )
        
        print(f"[Bob] Shared secret computed: {self.shared_secret}")
        
        # Derive encryption key
        self.encryption_key = derive_key(self.shared_secret)
        print(f"[Bob] Derived encryption key (32 bytes)")
        
    def receive_encrypted_message(self, encrypted):
        """Decrypt a message from Alice."""
        decrypted = simple_decrypt(encrypted, self.encryption_key)
        print(f"[Bob] Decrypted message: {decrypted}")
        return decrypted
    
    def send_encrypted_message(self, message):
        """Encrypt and send message to Alice."""
        encrypted = simple_encrypt(message, self.encryption_key)
        print(f"[Bob] Encrypted message: {encrypted.hex()}")
        return encrypted
    
    def run(self):
        """Run Bob's side of the protocol."""
        print("=" * 60)
        print("BOB - Waiting for Alice to initiate DHKE")
        print("=" * 60)
        
        # Create server socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind((HOST, PORT))
            server_socket.listen(1)
            print(f"[Bob] Listening on {HOST}:{PORT}...")
            print("[Bob] Waiting for Alice to connect...\n")
            
            conn, addr = server_socket.accept()
            print(f"[Bob] Alice connected from {addr}")
            
            # Step 1: Receive parameters and Alice's public key
            print("\n--- Step 1: Receiving parameters and Alice's public key ---")
            data = conn.recv(4096)
            message = json.loads(data.decode('utf-8'))
            
            p = message['p']
            g = message['g']
            alice_public_key = message['public_key']
            
            # Generate Bob's keys
            self.receive_params_and_generate_keys(p, g)
            
            # Step 2: Compute shared secret
            print("\n--- Step 2: Computing shared secret ---")
            self.compute_shared(alice_public_key)
            
            # Step 3: Send public key to Alice
            print("\n--- Step 3: Sending public key to Alice ---")
            response = {'public_key': self.public_key}
            conn.send(json.dumps(response).encode('utf-8'))
            print(f"[Bob] Sent public key B to Alice")
            
            # Step 4: Receive encrypted message from Alice
            print("\n--- Step 4: Receiving encrypted message from Alice ---")
            msg_length = int.from_bytes(conn.recv(4), 'big')
            encrypted_msg = conn.recv(msg_length)
            
            print(f"[Bob] Received encrypted message: {encrypted_msg.hex()}")
            decrypted_msg = self.receive_encrypted_message(encrypted_msg)
            
            # Step 5: Send encrypted response
            print("\n--- Step 5: Sending encrypted response ---")
            response_msg = "Hello Alice! This is Bob. Message received loud and clear!"
            encrypted_response = self.send_encrypted_message(response_msg)
            
            conn.send(len(encrypted_response).to_bytes(4, 'big'))
            conn.send(encrypted_response)
            
            print("\n" + "=" * 60)
            print("SUCCESS! Bob established secure communication with Alice!")
            print(f"Message from Alice: {decrypted_msg}")
            print(f"Response sent: {response_msg}")
            print("=" * 60)
            
            conn.close()
            
        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
        finally:
            server_socket.close()
            print("\n[Bob] Server closed.")


def main():
    parser = argparse.ArgumentParser(
        description='Secure Diffie-Hellman Key Exchange Demonstration'
    )
    parser.add_argument(
        '--alice', action='store_true',
        help='Run as Alice (client)'
    )
    parser.add_argument(
        '--bob', action='store_true',
        help='Run as Bob (server)'
    )
    parser.add_argument(
        '--bits', type=int, default=2048, choices=[1024, 2048],
        help='Key size in bits (default: 2048)'
    )
    
    args = parser.parse_args()
    
    if args.alice:
        alice = Alice(bit_length=args.bits)
        alice.run()
    elif args.bob:
        bob = Bob()
        bob.run()
    else:
        print("Please specify --alice or --bob")
        print("\nUsage:")
        print("  Terminal 1: python dhke_secure.py --bob")
        print("  Terminal 2: python dhke_secure.py --alice")
        sys.exit(1)


if __name__ == "__main__":
    main()

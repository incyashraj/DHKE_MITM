"""
Man-in-the-Middle (MITM) Attack on Diffie-Hellman Key Exchange

This script demonstrates the vulnerability of unauthenticated DHKE.
Eve acts as a proxy between Alice and Bob, intercepting and modifying their
communication without either party knowing.

The Attack:
1. Alice thinks she's talking to Bob, but connects to Eve
2. Eve intercepts Alice's public key A
3. Eve generates her own key pairs (e1 with Alice, e2 with Bob)
4. Eve forwards her public key E1 to Bob, pretending to be Alice
5. Bob thinks E1 is from Alice, sends back his public key B to Eve
6. Eve sends her public key E2 to Alice, pretending to be Bob
7. Result: Alice and Eve share secret s1, Eve and Bob share secret s2
8. Eve can decrypt, read, modify, and re-encrypt all messages!

This demonstrates why authentication is critical in real protocols like TLS.

Usage:
    Terminal 1: python dhke_mitm.py --bob
    Terminal 2: python dhke_mitm.py --eve  
    Terminal 3: python dhke_mitm.py --alice
"""

import socket
import json
import argparse
import sys
import threading
import time
from dh_params import (
    get_dh_params, generate_private_key, compute_public_key,
    compute_shared_secret, derive_key, simple_encrypt, simple_decrypt
)

# Network configuration
HOST = '127.0.0.1'
PORT_EVE = 5000      # Eve listens here (Alice connects to this)
PORT_BOB = 5001      # Bob listens here (Eve connects to this)


class AliceMITM:
    """
    Alice - the victim who thinks she's securely talking to Bob.
    She doesn't know Eve is in the middle!
    """
    
    def __init__(self, bit_length=1024):
        # Use 1024-bit for faster demo
        self.bit_length = bit_length
        self.p, self.g = get_dh_params(bit_length)
        self.private_key = None
        self.public_key = None
        self.shared_secret = None
        self.encryption_key = None
        
    def generate_keys(self):
        print("[Alice] Generating private key...")
        self.private_key = generate_private_key(self.p, secure=True)
        self.public_key = compute_public_key(self.g, self.private_key, self.p)
        print(f"[Alice] Public key: {self.public_key}")
        
    def compute_shared(self, public_key):
        print(f"[Alice] Received public key (thinks it's from Bob): {public_key}")
        self.shared_secret = compute_shared_secret(public_key, self.private_key, self.p)
        self.encryption_key = derive_key(self.shared_secret)
        print(f"[Alice] Computed shared secret: {self.shared_secret}")
        
    def run(self):
        print("=" * 70)
        print("ALICE - Initiating key exchange (unknowingly with Eve!)")
        print("=" * 70)
        
        self.generate_keys()
        
        # Connect to Eve (but Alice thinks it's Bob!)
        print(f"\n[Alice] Connecting to 'Bob' at {HOST}:{PORT_EVE}...")
        time.sleep(1)  # Give Eve time to start
        
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        try:
            client_socket.connect((HOST, PORT_EVE))
            print("[Alice] Connected to 'Bob'! (actually Eve)")
            
            # Send public parameters and key
            message = {
                'p': self.p,
                'g': self.g,
                'public_key': self.public_key
            }
            client_socket.send(json.dumps(message).encode('utf-8'))
            print(f"[Alice] Sent (p, g, A) to 'Bob'")
            
            # Receive "Bob's" public key (actually Eve's)
            data = client_socket.recv(4096)
            response = json.loads(data.decode('utf-8'))
            bob_public_key = response['public_key']
            
            # Compute shared secret with Eve (thinking it's with Bob)
            self.compute_shared(bob_public_key)
            
            # Send encrypted message
            print("\n[Alice] Sending encrypted message...")
            secret_message = "Bob, let's meet at the secret location at midnight. -Alice"
            encrypted = simple_encrypt(secret_message, self.encryption_key)
            print(f"[Alice] Original message: '{secret_message}'")
            print(f"[Alice] Encrypted: {encrypted.hex()[:64]}...")
            
            client_socket.send(len(encrypted).to_bytes(4, 'big'))
            client_socket.send(encrypted)
            
            # Receive response
            msg_length = int.from_bytes(client_socket.recv(4), 'big')
            encrypted_response = client_socket.recv(msg_length)
            decrypted = simple_decrypt(encrypted_response, self.encryption_key)
            
            print(f"\n[Alice] Received message from 'Bob': '{decrypted}'")
            print("[Alice] Everything seems secure! (or is it?)")
            
        except Exception as e:
            print(f"[Alice ERROR] {e}")
            import traceback
            traceback.print_exc()
        finally:
            client_socket.close()
            print("[Alice] Connection closed.\n")


class BobMITM:
    """
    Bob - another victim who thinks he's talking to Alice.
    He also doesn't know about Eve!
    """
    
    def __init__(self):
        self.p = None
        self.g = None
        self.private_key = None
        self.public_key = None
        self.shared_secret = None
        self.encryption_key = None
        
    def receive_params_and_generate_keys(self, p, g):
        self.p = p
        self.g = g
        print(f"[Bob] Received parameters from 'Alice'")
        
        self.private_key = generate_private_key(self.p, secure=True)
        self.public_key = compute_public_key(self.g, self.private_key, self.p)
        print(f"[Bob] Generated public key: {self.public_key}")
        
    def compute_shared(self, alice_public_key):
        print(f"[Bob] Received public key (thinks it's from Alice): {alice_public_key}")
        self.shared_secret = compute_shared_secret(alice_public_key, self.private_key, self.p)
        self.encryption_key = derive_key(self.shared_secret)
        print(f"[Bob] Computed shared secret: {self.shared_secret}")
        
    def run(self):
        print("=" * 70)
        print("BOB - Waiting for Alice's key exchange request")
        print("=" * 70)
        
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind((HOST, PORT_BOB))
            server_socket.listen(1)
            print(f"[Bob] Listening on {HOST}:{PORT_BOB}...")
            print("[Bob] Waiting for 'Alice' to connect...\n")
            
            conn, addr = server_socket.accept()
            print(f"[Bob] 'Alice' connected! (actually Eve)")
            
            # Receive parameters and "Alice's" public key (actually Eve's)
            data = conn.recv(4096)
            message = json.loads(data.decode('utf-8'))
            
            self.receive_params_and_generate_keys(message['p'], message['g'])
            self.compute_shared(message['public_key'])
            
            # Send public key back
            response = {'public_key': self.public_key}
            conn.send(json.dumps(response).encode('utf-8'))
            print(f"[Bob] Sent public key to 'Alice'")
            
            # Receive encrypted message
            msg_length = int.from_bytes(conn.recv(4), 'big')
            encrypted = conn.recv(msg_length)
            decrypted = simple_decrypt(encrypted, self.encryption_key)
            
            print(f"\n[Bob] Received encrypted message from 'Alice': '{decrypted}'")
            
            # Send response
            response_msg = "Alice, confirmed. See you there! -Bob"
            encrypted_response = simple_encrypt(response_msg, self.encryption_key)
            
            conn.send(len(encrypted_response).to_bytes(4, 'big'))
            conn.send(encrypted_response)
            print(f"[Bob] Sent response: '{response_msg}'")
            print("[Bob] Secure communication established! (or so I think...)")
            
            conn.close()
            
        except Exception as e:
            print(f"[Bob ERROR] {e}")
            import traceback
            traceback.print_exc()
        finally:
            server_socket.close()
            print("[Bob] Server closed.\n")


class Eve:
    """
    Eve - the attacker performing MITM.
    She intercepts all communication and can read/modify everything!
    """
    
    def __init__(self):
        # Eve needs TWO key pairs - one for Alice, one for Bob
        self.p = None
        self.g = None
        
        # Keys for communicating with Alice
        self.private_key_alice = None
        self.public_key_alice = None
        self.shared_secret_alice = None
        self.key_alice = None
        
        # Keys for communicating with Bob
        self.private_key_bob = None
        self.public_key_bob = None
        self.shared_secret_bob = None
        self.key_bob = None
        
    def intercept_alice(self, alice_socket):
        """Handle Alice's connection - impersonate Bob to Alice."""
        try:
            print("\n[Eve] Intercepting Alice's message...")
            
            # Receive from Alice
            data = alice_socket.recv(4096)
            alice_message = json.loads(data.decode('utf-8'))
            
            self.p = alice_message['p']
            self.g = alice_message['g']
            alice_public_key = alice_message['public_key']
            
            print(f"[Eve] Intercepted Alice's public key: {alice_public_key}")
            print(f"[Eve] Parameters: p ({self.p.bit_length()} bits), g={self.g}")
            
            # Generate Eve's key pair for Alice
            print("[Eve] Generating keys to trick Alice...")
            self.private_key_alice = generate_private_key(self.p, secure=True)
            self.public_key_alice = compute_public_key(self.g, self.private_key_alice, self.p)
            
            # Compute shared secret with Alice
            self.shared_secret_alice = compute_shared_secret(
                alice_public_key, self.private_key_alice, self.p
            )
            self.key_alice = derive_key(self.shared_secret_alice)
            print(f"[Eve] Shared secret with Alice: {self.shared_secret_alice}")
            
            return alice_message
            
        except Exception as e:
            print(f"[Eve ERROR with Alice] {e}")
            raise
    
    def forward_to_bob(self, original_message):
        """Forward to Bob - impersonate Alice to Bob."""
        try:
            print("\n[Eve] Connecting to real Bob...")
            bob_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Give Bob time to start
            for i in range(5):
                try:
                    bob_socket.connect((HOST, PORT_BOB))
                    break
                except:
                    if i == 4:
                        raise
                    time.sleep(1)
            
            print("[Eve] Connected to Bob!")
            
            # Generate different key pair for Bob
            print("[Eve] Generating different keys to trick Bob...")
            self.private_key_bob = generate_private_key(self.p, secure=True)
            self.public_key_bob = compute_public_key(self.g, self.private_key_bob, self.p)
            
            # Send Eve's public key to Bob (pretending to be Alice)
            fake_message = {
                'p': self.p,
                'g': self.g,
                'public_key': self.public_key_bob  # Eve's key, not Alice's!
            }
            bob_socket.send(json.dumps(fake_message).encode('utf-8'))
            print(f"[Eve] Sent fake 'Alice' public key to Bob: {self.public_key_bob}")
            
            # Receive Bob's public key
            data = bob_socket.recv(4096)
            bob_response = json.loads(data.decode('utf-8'))
            bob_public_key = bob_response['public_key']
            
            print(f"[Eve] Intercepted Bob's public key: {bob_public_key}")
            
            # Compute shared secret with Bob
            self.shared_secret_bob = compute_shared_secret(
                bob_public_key, self.private_key_bob, self.p
            )
            self.key_bob = derive_key(self.shared_secret_bob)
            print(f"[Eve] Shared secret with Bob: {self.shared_secret_bob}")
            
            return bob_socket, bob_response
            
        except Exception as e:
            print(f"[Eve ERROR with Bob] {e}")
            raise
    
    def proxy_messages(self, alice_socket, bob_socket, bob_response):
        """Intercept and modify messages between Alice and Bob."""
        try:
            # Send "Bob's" public key to Alice (actually Eve's)
            fake_response = {'public_key': self.public_key_alice}
            alice_socket.send(json.dumps(fake_response).encode('utf-8'))
            print("[Eve] Sent fake 'Bob' public key to Alice")
            
            print("\n" + "=" * 70)
            print("ATTACK SUCCESSFUL! Eve has established two separate channels:")
            print(f"  - Alice <--[secret: {self.shared_secret_alice}]--> Eve")
            print(f"  - Eve <--[secret: {self.shared_secret_bob}]--> Bob")
            print("Eve can now intercept and modify all messages!")
            print("=" * 70)
            
            # Receive Alice's encrypted message
            print("\n[Eve] Waiting for Alice's message...")
            msg_length = int.from_bytes(alice_socket.recv(4), 'big')
            encrypted_from_alice = alice_socket.recv(msg_length)
            
            # Decrypt Alice's message
            decrypted_alice_msg = simple_decrypt(encrypted_from_alice, self.key_alice)
            print(f"\n[Eve] 🕵️  INTERCEPTED Alice's message: '{decrypted_alice_msg}'")
            
            # Eve can modify the message!
            modified_message = "Bob, plans have changed. Meet at the usual place at noon. -Alice"
            print(f"[Eve] 😈 MODIFIED message: '{modified_message}'")
            
            # Re-encrypt with Bob's key and forward
            encrypted_for_bob = simple_encrypt(modified_message, self.key_bob)
            bob_socket.send(len(encrypted_for_bob).to_bytes(4, 'big'))
            bob_socket.send(encrypted_for_bob)
            print("[Eve] Forwarded modified message to Bob")
            
            # Receive Bob's response
            msg_length = int.from_bytes(bob_socket.recv(4), 'big')
            encrypted_from_bob = bob_socket.recv(msg_length)
            
            # Decrypt Bob's response
            decrypted_bob_msg = simple_decrypt(encrypted_from_bob, self.key_bob)
            print(f"\n[Eve] 🕵️  INTERCEPTED Bob's response: '{decrypted_bob_msg}'")
            
            # Optionally modify Bob's response too
            # For now, forward it unmodified
            encrypted_for_alice = simple_encrypt(decrypted_bob_msg, self.key_alice)
            alice_socket.send(len(encrypted_for_alice).to_bytes(4, 'big'))
            alice_socket.send(encrypted_for_alice)
            print("[Eve] Forwarded Bob's response to Alice")
            
            print("\n" + "=" * 70)
            print("MITM ATTACK COMPLETE!")
            print("Alice and Bob think they communicated securely,")
            print("but Eve intercepted and modified everything!")
            print("=" * 70 + "\n")
            
        except Exception as e:
            print(f"[Eve ERROR during proxy] {e}")
            import traceback
            traceback.print_exc()
    
    def run(self):
        """Run Eve's MITM attack."""
        print("=" * 70)
        print("EVE - Starting Man-in-the-Middle Attack")
        print("=" * 70)
        print("[Eve] This demonstrates the vulnerability of unauthenticated DHKE")
        print("[Eve] Setting up proxy server...\n")
        
        # Create server socket for Alice
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind((HOST, PORT_EVE))
            server_socket.listen(1)
            print(f"[Eve] Listening on {HOST}:{PORT_EVE} (waiting for Alice)...")
            
            # Wait for Alice to connect
            alice_socket, addr = server_socket.accept()
            print(f"[Eve] Alice connected from {addr}!")
            
            # Intercept Alice's message
            original_message = self.intercept_alice(alice_socket)
            
            # Forward to Bob (with different key)
            bob_socket, bob_response = self.forward_to_bob(original_message)
            
            # Proxy messages between them
            self.proxy_messages(alice_socket, bob_socket, bob_response)
            
            # Clean up
            alice_socket.close()
            bob_socket.close()
            
        except Exception as e:
            print(f"[Eve ERROR] {e}")
            import traceback
            traceback.print_exc()
        finally:
            server_socket.close()
            print("[Eve] Proxy closed.")


def main():
    parser = argparse.ArgumentParser(
        description='MITM Attack on Diffie-Hellman Key Exchange'
    )
    parser.add_argument('--alice', action='store_true', help='Run as Alice')
    parser.add_argument('--bob', action='store_true', help='Run as Bob')
    parser.add_argument('--eve', action='store_true', help='Run as Eve (attacker)')
    
    args = parser.parse_args()
    
    if args.alice:
        alice = AliceMITM(bit_length=1024)
        alice.run()
    elif args.bob:
        bob = BobMITM()
        bob.run()
    elif args.eve:
        eve = Eve()
        eve.run()
    else:
        print("Man-in-the-Middle Attack Demonstration")
        print("\nThis demonstrates how DHKE fails without authentication!")
        print("\nUsage (start in this order):")
        print("  Terminal 1: python dhke_mitm.py --bob")
        print("  Terminal 2: python dhke_mitm.py --eve")
        print("  Terminal 3: python dhke_mitm.py --alice")
        print("\nEve will intercept and modify all communication between Alice and Bob!")
        sys.exit(1)


if __name__ == "__main__":
    main()

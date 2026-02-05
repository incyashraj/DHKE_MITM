#!/usr/bin/env python3
"""
Diffie-Hellman Key Exchange - Direct Communication
Two parties (Alice and Bob) establish shared secret securely
"""

import socket
import json
import sys
import argparse
from dh_params import (
    get_dh_params,
    generate_private_key,
    compute_public_key,
    compute_shared_secret,
    derive_key,
    simple_encrypt,
    simple_decrypt
)


def recv_msg(sock):
    """Receive a complete message (reads until newline)"""
    data = b''
    while True:
        chunk = sock.recv(1)
        if not chunk:
            return None
        data += chunk
        if chunk == b'\n':
            return data.decode().strip()


class Alice:
    def __init__(self, port=5000):
        self.port = port
        self.sock = None
        self.bits = None
        self.p = None
        self.g = None
        self.private_key = None
        self.public_key = None
        self.shared_secret = None
        self.aes_key = None
        self.bob_public_key = None
        
    def select_parameters(self):
        print("\n" + "="*60)
        print("Alice: Select Security Parameters")
        print("="*60)
        print("1. 23-bit   (weak - demo only)")
        print("2. 512-bit  (weak - deprecated)")
        print("3. 1024-bit (moderate)")
        print("4. 2048-bit (strong - recommended)")
        
        choice = input("\nChoice (1-4): ").strip()
        bits_map = {'1': 23, '2': 512, '3': 1024, '4': 2048}
        self.bits = bits_map.get(choice, 1024)
        self.p, self.g = get_dh_params(self.bits)
        
        print(f"\nUsing {self.bits}-bit parameters")
        print(f"Prime p: {hex(self.p)[:50]}...")
        print(f"Generator g: {self.g}")
        
    def connect(self):
        print(f"\nConnecting to Bob at localhost:{self.port}...")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect(('localhost', self.port))
            print("Connected.")
        except ConnectionRefusedError:
            print("ERROR: Cannot connect. Start Bob first!")
            sys.exit(1)
            
    def send_parameters(self):
        print("Sending parameters to Bob...")
        params = {'p': str(self.p), 'g': str(self.g), 'bits': str(self.bits)}
        self.sock.send((json.dumps(params) + '\n').encode())
        
    def generate_keys(self):
        print("\nGenerating Alice's keys...")
        self.private_key = generate_private_key(self.p)
        print(f"Private key (a): {self.private_key}")
        print(f"\nComputing public key: A = g^a mod p")
        print(f"  g = {self.g}")
        print(f"  a = {self.private_key}")
        print(f"  p = {self.p}")
        self.public_key = compute_public_key(self.g, self.private_key, self.p)
        print(f"  A = {self.g}^{self.private_key} mod {self.p}")
        print(f"  A = {self.public_key}")
        
    def exchange_keys(self):
        print("\nExchanging public keys...")
        self.sock.send((json.dumps({'public_key': str(self.public_key)}) + '\n').encode())
        data = recv_msg(self.sock)
        if not data:
            print("ERROR: No response from Bob")
            sys.exit(1)
        self.bob_public_key = int(json.loads(data)['public_key'])
        print(f"Received Bob's public key: {hex(self.bob_public_key)[:40]}...")
        
    def compute_secret(self):
        print("\nComputing shared secret...")
        print(f"Computing: s = B^a mod p")
        print(f"  B (Bob's public key) = {self.bob_public_key}")
        print(f"  a (Alice's private key) = {self.private_key}")
        print(f"  p = {self.p}")
        self.shared_secret = compute_shared_secret(self.bob_public_key, self.private_key, self.p)
        print(f"  s = {self.bob_public_key}^{self.private_key} mod {self.p}")
        print(f"  s = {self.shared_secret}")
        self.aes_key = derive_key(self.shared_secret)
        print(f"\nDeriving AES key: SHA-256(shared_secret)")
        print(f"  AES key: {self.aes_key.hex()}")
        
    def chat(self):
        print("\n" + "="*60)
        print("SECURE CHAT (type 'quit' to exit)")
        print("="*60)
        
        while True:
            # Send message
            message = input("\nYou: ").strip()
            if not message:
                continue
            if message.lower() == 'quit':
                print("Ending chat...")
                self.sock.send((json.dumps({'encrypted_message': 'QUIT'}) + '\n').encode())
                break
                
            print(f"\n--- Encryption Process ---")
            print(f"Plaintext: '{message}'")
            print(f"AES key: {self.aes_key.hex()}")
            encrypted = simple_encrypt(message, self.aes_key)
            encrypted_hex = encrypted.hex()
            print(f"Ciphertext (hex): {encrypted_hex}")
            print(f"Sending...")
            self.sock.send((json.dumps({'encrypted_message': encrypted_hex}) + '\n').encode())
            
            # Wait for reply
            print("\nWaiting for reply...")
            try:
                self.sock.settimeout(None)  # No timeout - wait indefinitely
                data = recv_msg(self.sock)
                if not data:
                    print("Connection closed.")
                    break
                    
                msg_data = json.loads(data)
                encrypted_hex = msg_data['encrypted_message']
                
                if encrypted_hex == 'QUIT':
                    print("\nBob ended the chat.")
                    break
                    
                print(f"\n--- Decryption Process ---")
                print(f"Received ciphertext (hex): {encrypted_hex}")
                print(f"AES key: {self.aes_key.hex()}")
                encrypted_bytes = bytes.fromhex(encrypted_hex)
                decrypted = simple_decrypt(encrypted_bytes, self.aes_key)
                print(f"Plaintext: '{decrypted}'")
                print(f"\nBob: {decrypted}")
            except Exception as e:
                print(f"Error: {e}")
                break
            
    def run(self):
        self.select_parameters()
        self.connect()
        self.send_parameters()
        self.generate_keys()
        self.exchange_keys()
        self.compute_secret()
        self.chat()
        self.sock.close()
        print("\nDone.")


class Bob:
    def __init__(self, port=5000):
        self.port = port
        self.sock = None
        self.conn = None
        self.bits = None
        self.p = None
        self.g = None
        self.private_key = None
        self.public_key = None
        self.shared_secret = None
        self.aes_key = None
        self.alice_public_key = None
        
    def setup_server(self):
        print("\n" + "="*60)
        print("Bob: Waiting for Connection")
        print("="*60)
        print(f"Listening on port {self.port}...")
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('localhost', self.port))
        self.sock.listen(1)
        
        self.conn, addr = self.sock.accept()
        print(f"Alice connected from {addr}")
        
    def receive_parameters(self):
        print("\nReceiving parameters...")
        data = recv_msg(self.conn)
        if not data:
            print("ERROR: No parameters received")
            sys.exit(1)
        params = json.loads(data)
        self.p = int(params['p'])
        self.g = int(params['g'])
        self.bits = int(params['bits'])
        print(f"Using {self.bits}-bit parameters")
        
    def generate_keys(self):
        print("\nGenerating Bob's keys...")
        self.private_key = generate_private_key(self.p)
        print(f"Private key (b): {self.private_key}")
        print(f"\nComputing public key: B = g^b mod p")
        print(f"  g = {self.g}")
        print(f"  b = {self.private_key}")
        print(f"  p = {self.p}")
        self.public_key = compute_public_key(self.g, self.private_key, self.p)
        print(f"  B = {self.g}^{self.private_key} mod {self.p}")
        print(f"  B = {self.public_key}")
        
    def exchange_keys(self):
        print("\nExchanging public keys...")
        data = recv_msg(self.conn)
        if not data:
            print("ERROR: No public key received")
            sys.exit(1)
        self.alice_public_key = int(json.loads(data)['public_key'])
        print(f"Received Alice's public key: {hex(self.alice_public_key)[:40]}...")
        self.conn.send((json.dumps({'public_key': str(self.public_key)}) + '\n').encode())
        
    def compute_secret(self):
        print("\nComputing shared secret...")
        print(f"Computing: s = A^b mod p")
        print(f"  A (Alice's public key) = {self.alice_public_key}")
        print(f"  b (Bob's private key) = {self.private_key}")
        print(f"  p = {self.p}")
        self.shared_secret = compute_shared_secret(self.alice_public_key, self.private_key, self.p)
        print(f"  s = {self.alice_public_key}^{self.private_key} mod {self.p}")
        print(f"  s = {self.shared_secret}")
        self.aes_key = derive_key(self.shared_secret)
        print(f"\nDeriving AES key: SHA-256(shared_secret)")
        print(f"  AES key: {self.aes_key.hex()}")
        
    def receive_message(self):
        print("\nWaiting for message...")
        data = recv_msg(self.conn)
        if not data:
            print("ERROR: No message received")
            return
        msg_data = json.loads(data)
        encrypted_hex = msg_data['encrypted_message']
        print(f"\n--- Decryption Process ---")
        print(f"Received ciphertext (hex): {encrypted_hex}")
        print(f"AES key: {self.aes_key.hex()}")
        encrypted_bytes = bytes.fromhex(encrypted_hex)  # Convert hex to bytes
        decrypted = simple_decrypt(encrypted_bytes, self.aes_key)
        print(f"Plaintext: '{decrypted}'")
        print(f"\nAlice says: '{decrypted}'")
        
    def send_reply(self):
        reply = input("\nYour reply: ").strip()
        if reply:
            print(f"\n--- Encryption Process ---")
            print(f"Plaintext: '{reply}'")
            print(f"AES key: {self.aes_key.hex()}")
            encrypted = simple_encrypt(reply, self.aes_key)
            encrypted_hex = encrypted.hex()  # Convert bytes to hex string
            print(f"Ciphertext (hex): {encrypted_hex}")
            print(f"Sending encrypted reply to Alice...")
            self.conn.send((json.dumps({'encrypted_message': encrypted_hex}) + '\n').encode())
    
    def chat(self):
        print("\n" + "="*60)
        print("SECURE CHAT (type 'quit' to exit)")
        print("="*60)
        
        while True:
            # Receive message from Alice
            print("\nWaiting for message from Alice...")
            try:
                self.conn.settimeout(None)  # No timeout - wait indefinitely
                data = recv_msg(self.conn)
                if not data:
                    print("Connection closed.")
                    break
                    
                msg_data = json.loads(data)
                encrypted_hex = msg_data['encrypted_message']
                
                if encrypted_hex == 'QUIT':
                    print("\nAlice ended the chat.")
                    break
                    
                print(f"\n--- Decryption Process ---")
                print(f"Received ciphertext (hex): {encrypted_hex}")
                print(f"AES key: {self.aes_key.hex()}")
                encrypted_bytes = bytes.fromhex(encrypted_hex)
                decrypted = simple_decrypt(encrypted_bytes, self.aes_key)
                print(f"Plaintext: '{decrypted}'")
                print(f"\nAlice: {decrypted}")
                
                # Send reply
                message = input("\nYou: ").strip()
                if not message:
                    continue
                if message.lower() == 'quit':
                    print("Ending chat...")
                    self.conn.send((json.dumps({'encrypted_message': 'QUIT'}) + '\n').encode())
                    break
                    
                print(f"\n--- Encryption Process ---")
                print(f"Plaintext: '{message}'")
                print(f"AES key: {self.aes_key.hex()}")
                encrypted = simple_encrypt(message, self.aes_key)
                encrypted_hex = encrypted.hex()
                print(f"Ciphertext (hex): {encrypted_hex}")
                print(f"Sending...")
                self.conn.send((json.dumps({'encrypted_message': encrypted_hex}) + '\n').encode())
                
            except Exception as e:
                print(f"Error: {e}")
                break
            
    def run(self):
        self.setup_server()
        self.receive_parameters()
        self.generate_keys()
        self.exchange_keys()
        self.compute_secret()
        self.chat()
        self.conn.close()
        self.sock.close()
        print("\nDone.")


def main():
    parser = argparse.ArgumentParser(description='Diffie-Hellman Key Exchange')
    parser.add_argument('--alice', action='store_true', help='Run as Alice')
    parser.add_argument('--bob', action='store_true', help='Run as Bob')
    parser.add_argument('--port', type=int, default=5000, help='Port number')
    
    args = parser.parse_args()
    
    try:
        if args.alice:
            alice = Alice(port=args.port)
            alice.run()
        elif args.bob:
            bob = Bob(port=args.port)
            bob.run()
        else:
            print("Usage:")
            print("  Terminal 1: python dhke.py --bob")
            print("  Terminal 2: python dhke.py --alice")
    except KeyboardInterrupt:
        print("\n\nInterrupted.")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Diffie-Hellman Key Exchange - Man-in-the-Middle Attack
Three parties: Alice, Bob, and Eve (attacker)
Eve intercepts and can modify all communication
"""

import socket
import json
import sys
import argparse
import time
from dh_params import (
    get_dh_params,
    generate_private_key,
    compute_public_key,
    compute_shared_secret,
    derive_key,
    simple_encrypt,
    simple_decrypt,
    brute_force_discrete_log
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
        print("1. 23-bit   (weak - breakable)")
        print("2. 512-bit  (weak - deprecated)")
        print("3. 1024-bit (moderate)")
        print("4. 2048-bit (strong)")
        
        choice = input("\nChoice (1-4): ").strip()
        bits_map = {'1': 23, '2': 512, '3': 1024, '4': 2048}
        self.bits = bits_map.get(choice, 1024)
        self.p, self.g = get_dh_params(self.bits)
        print(f"\nUsing {self.bits}-bit parameters")
        
    def run(self):
        self.select_parameters()
        
        print(f"\nConnecting to Bob at localhost:{self.port}...")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect(('localhost', self.port))
            print("Connected.")
        except ConnectionRefusedError:
            print("ERROR: Cannot connect!")
            sys.exit(1)
        
        # Send parameters
        print("Sending parameters...")
        params = {'p': str(self.p), 'g': str(self.g), 'bits': str(self.bits)}
        self.sock.send((json.dumps(params) + '\n').encode())
        
        # Generate keys
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
        
        # Exchange keys
        print("\nExchanging keys...")
        self.sock.send((json.dumps({'public_key': str(self.public_key)}) + '\n').encode())
        data = self.sock.recv(4096).decode().strip()
        self.bob_public_key = int(json.loads(data)['public_key'])
        
        # Compute secret
        print("\nComputing shared secret...")
        print(f"Computing: s = B^a mod p")
        print(f"  B (received public key) = {self.bob_public_key}")
        print(f"  a (Alice's private key) = {self.private_key}")
        print(f"  p = {self.p}")
        self.shared_secret = compute_shared_secret(self.bob_public_key, self.private_key, self.p)
        print(f"  s = {self.bob_public_key}^{self.private_key} mod {self.p}")
        print(f"  s = {self.shared_secret}")
        self.aes_key = derive_key(self.shared_secret)
        print(f"\nDeriving AES key: SHA-256(shared_secret)")
        print(f"  AES key: {self.aes_key.hex()}")
        
        # Send message
        message = input("\nYour message to Bob: ").strip()
        if not message:
            message = "Meet at the library"
        print(f"\n--- Encryption Process ---")
        print(f"Plaintext: '{message}'")
        print(f"AES key: {self.aes_key.hex()}")
        encrypted = simple_encrypt(message, self.aes_key)
        encrypted_hex = encrypted.hex()
        print(f"Ciphertext (hex): {encrypted_hex}")
        print(f"Sending encrypted message...")
        self.sock.send((json.dumps({'encrypted_message': encrypted_hex}) + '\n').encode())
        
        # Continuous chat
        print("\n" + "="*60)
        print("SECURE CHAT (type 'quit' to exit)")
        print("="*60)
        
        while True:
            # Wait for reply
            print("\nWaiting for reply...")
            try:
                self.sock.settimeout(None)  # No timeout
                data = recv_msg(self.sock)
                if not data:
                    print("Connection closed.")
                    break
                    
                msg_data = json.loads(data)
                encrypted_hex = msg_data['encrypted_message']
                
                if encrypted_hex == 'QUIT':
                    print("\nBob ended the chat.")
                    break
                    
                encrypted_bytes = bytes.fromhex(encrypted_hex)
                decrypted = simple_decrypt(encrypted_bytes, self.aes_key)
                print(f"\nBob: {decrypted}")
            except Exception as e:
                print(f"Error: {e}")
                break
            
            # Send message
            message = input("\nYou: ").strip()
            if not message:
                continue
            if message.lower() == 'quit':
                print("Ending chat...")
                self.sock.send((json.dumps({'encrypted_message': 'QUIT'}) + '\n').encode())
                break
                
            encrypted = simple_encrypt(message, self.aes_key)
            encrypted_hex = encrypted.hex()
            self.sock.send((json.dumps({'encrypted_message': encrypted_hex}) + '\n').encode())
            
        self.sock.close()
        print("\nDone.")


class Bob:
    def __init__(self, port=5001):
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
        
    def run(self):
        print("\n" + "="*60)
        print("Bob: Waiting for Connection")
        print("="*60)
        print(f"Listening on port {self.port}...")
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('localhost', self.port))
        self.sock.listen(1)
        
        self.conn, addr = self.sock.accept()
        print(f"Connected from {addr}")
        
        # Receive parameters
        print("\nReceiving parameters...")
        data = self.conn.recv(8192).decode().strip()
        params = json.loads(data)
        self.p = int(params['p'])
        self.g = int(params['g'])
        self.bits = int(params['bits'])
        print(f"Using {self.bits}-bit parameters")
        
        # Generate keys
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
        
        # Exchange keys
        print("\nExchanging keys...")
        data = self.conn.recv(4096).decode().strip()
        self.alice_public_key = int(json.loads(data)['public_key'])
        self.conn.send((json.dumps({'public_key': str(self.public_key)}) + '\n').encode())
        
        # Compute secret
        print("\nComputing shared secret...")
        print(f"Computing: s = A^b mod p")
        print(f"  A (received public key) = {self.alice_public_key}")
        print(f"  b (Bob's private key) = {self.private_key}")
        print(f"  p = {self.p}")
        self.shared_secret = compute_shared_secret(self.alice_public_key, self.private_key, self.p)
        print(f"  s = {self.alice_public_key}^{self.private_key} mod {self.p}")
        print(f"  s = {self.shared_secret}")
        self.aes_key = derive_key(self.shared_secret)
        print(f"\nDeriving AES key: SHA-256(shared_secret)")
        print(f"  AES key: {self.aes_key.hex()}")
        
        # Receive first message
        print("\nWaiting for message...")
        data = recv_msg(self.conn)
        msg_data = json.loads(data)
        encrypted_hex = msg_data['encrypted_message']
        print(f"\n--- Decryption Process ---")
        print(f"Received ciphertext (hex): {encrypted_hex}")
        print(f"AES key: {self.aes_key.hex()}")
        encrypted_bytes = bytes.fromhex(encrypted_hex)
        decrypted = simple_decrypt(encrypted_bytes, self.aes_key)
        print(f"Plaintext: '{decrypted}'")
        print(f"\nAlice: {decrypted}")
        
        # Continuous chat
        print("\n" + "="*60)
        print("SECURE CHAT (type 'quit' to exit)")
        print("="*60)
        
        while True:
            # Send reply
            reply = input("\nYou: ").strip()
            if not reply:
                continue
            if reply.lower() == 'quit':
                print("Ending chat...")
                self.conn.send((json.dumps({'encrypted_message': 'QUIT'}) + '\n').encode())
                break
                
            encrypted = simple_encrypt(reply, self.aes_key)
            encrypted_hex = encrypted.hex()
            self.conn.send((json.dumps({'encrypted_message': encrypted_hex}) + '\n').encode())
            
            # Receive message
            print("\nWaiting for message...")
            try:
                data = recv_msg(self.conn)
                if not data:
                    print("Connection closed.")
                    break
                    
                msg_data = json.loads(data)
                encrypted_hex = msg_data['encrypted_message']
                
                if encrypted_hex == 'QUIT':
                    print("\nAlice ended the chat.")
                    break
                    
                encrypted_bytes = bytes.fromhex(encrypted_hex)
                decrypted = simple_decrypt(encrypted_bytes, self.aes_key)
                print(f"\nAlice: {decrypted}")
            except Exception as e:
                print(f"Error: {e}")
                break
            
        self.conn.close()
        self.sock.close()
        print("\nDone.")


class Eve:
    def __init__(self, alice_port=5000, bob_port=5001):
        self.alice_port = alice_port
        self.bob_port = bob_port
        self.alice_conn = None
        self.bob_sock = None
        self.server_sock = None
        
        # Keys with Alice
        self.private_key_alice = None
        self.public_key_alice = None
        self.alice_public_key = None
        self.shared_secret_alice = None
        self.aes_key_alice = None
        
        # Keys with Bob
        self.private_key_bob = None
        self.public_key_bob = None
        self.bob_public_key = None
        self.shared_secret_bob = None
        self.aes_key_bob = None
        
        self.p = None
        self.g = None
        self.bits = None
        self.original_message = None
        self.modified_message = None
        
        # Track all intercepted messages
        self.intercepted_messages = []
        
    def run(self):
        print("\n" + "="*60)
        print("Eve: Man-in-the-Middle Attack")
        print("="*60)
        print(f"\nPositioning between Alice and Bob...")
        print(f"  Listening on port {self.alice_port} (pretending to be Bob)")
        print(f"  Connecting to real Bob on port {self.bob_port}")
        
        # Setup fake Bob for Alice
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_sock.bind(('localhost', self.alice_port))
        self.server_sock.listen(1)
        
        # Connect to real Bob
        self.bob_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.bob_sock.connect(('localhost', self.bob_port))
            print("  Connected to Bob")
        except ConnectionRefusedError:
            print("ERROR: Cannot connect to Bob!")
            sys.exit(1)
        
        # Wait for Alice
        print("  Waiting for Alice...")
        self.alice_conn, addr = self.server_sock.accept()
        print("  Alice connected! MITM active.")
        
        # Intercept parameters
        print("\nIntercepting parameters...")
        data = self.alice_conn.recv(8192).decode().strip()
        params = json.loads(data)
        self.p = int(params['p'])
        self.g = int(params['g'])
        self.bits = int(params['bits'])
        print(f"Parameters: {self.bits}-bit")
        self.bob_sock.send(data.encode())
        
        # Generate Eve's two key pairs
        print("\n--- Eve Generates TWO Key Pairs ---")
        print("\nFor Alice-Eve channel:")
        self.private_key_alice = generate_private_key(self.p)
        print(f"  Eve's private key (e1): {self.private_key_alice}")
        self.public_key_alice = compute_public_key(self.g, self.private_key_alice, self.p)
        print(f"  Eve's public key: E1 = {self.g}^{self.private_key_alice} mod {self.p} = {self.public_key_alice}")
        
        print("\nFor Eve-Bob channel:")
        self.private_key_bob = generate_private_key(self.p)
        print(f"  Eve's private key (e2): {self.private_key_bob}")
        self.public_key_bob = compute_public_key(self.g, self.private_key_bob, self.p)
        print(f"  Eve's public key: E2 = {self.g}^{self.private_key_bob} mod {self.p} = {self.public_key_bob}")
        
        # Intercept key exchange
        print("\nIntercepting keys...")
        # Get Alice's real key
        data = self.alice_conn.recv(4096).decode().strip()
        self.alice_public_key = int(json.loads(data)['public_key'])
        
        # Send Eve's key to Bob (pretending to be Alice)
        fake_alice = json.dumps({'public_key': str(self.public_key_bob)}) + '\n'
        self.bob_sock.send(fake_alice.encode())
        
        # Get Bob's real key
        data = self.bob_sock.recv(4096).decode().strip()
        self.bob_public_key = int(json.loads(data)['public_key'])
        
        # Send Eve's key to Alice (pretending to be Bob)
        fake_bob = json.dumps({'public_key': str(self.public_key_alice)}) + '\n'
        self.alice_conn.send(fake_bob.encode())
        print("\n--- Key Replacement Attack ---")
        print(f"  Alice thinks Bob's key is: {self.public_key_alice}")
        print(f"  Bob thinks Alice's key is: {self.public_key_bob}")
        print(f"  (Both are actually Eve's keys!)")
        
        # Compute both secrets
        print("\n--- Computing TWO Different Shared Secrets ---")
        print("\nWith Alice:")
        print(f"  s1 = A^e1 mod p = {self.alice_public_key}^{self.private_key_alice} mod {self.p}")
        self.shared_secret_alice = compute_shared_secret(
            self.alice_public_key, self.private_key_alice, self.p
        )
        print(f"  s1 = {self.shared_secret_alice}")
        self.aes_key_alice = derive_key(self.shared_secret_alice)
        print(f"  AES key (Alice-Eve): {self.aes_key_alice.hex()}")
        
        print("\nWith Bob:")
        print(f"  s2 = B^e2 mod p = {self.bob_public_key}^{self.private_key_bob} mod {self.p}")
        self.shared_secret_bob = compute_shared_secret(
            self.bob_public_key, self.private_key_bob, self.p
        )
        print(f"  s2 = {self.shared_secret_bob}")
        self.aes_key_bob = derive_key(self.shared_secret_bob)
        print(f"  AES key (Eve-Bob): {self.aes_key_bob.hex()}")
        print(f"\n  ⚠️  MITM SUCCESS: Eve has TWO DIFFERENT secrets!")
        
        # Intercept message
        print("\n--- Intercepting Alice's Message ---")
        data = recv_msg(self.alice_conn)
        msg_data = json.loads(data)
        encrypted_hex = msg_data['encrypted_message']
        print(f"Received ciphertext (hex): {encrypted_hex}")
        print(f"Decrypting with Alice-Eve key: {self.aes_key_alice.hex()}")
        encrypted_bytes = bytes.fromhex(encrypted_hex)
        self.original_message = simple_decrypt(encrypted_bytes, self.aes_key_alice)
        print(f"Plaintext: '{self.original_message}'")
        
        # Ask to modify
        print("\nOptions:")
        print("  1. Forward original")
        print("  2. Modify message")
        choice = input("Choice (1-2): ").strip()
        
        if choice == '2':
            modified = input("Modified message: ").strip()
            self.modified_message = modified if modified else self.original_message
            if modified:
                print(f"Changed to: '{self.modified_message}'")
        else:
            self.modified_message = self.original_message
        
        # Track for analysis
        self.intercepted_messages.append({
            'direction': 'Alice->Bob',
            'original': self.original_message,
            'forwarded': self.modified_message
        })
        
        # Forward to Bob
        print(f"\n--- Re-encrypting for Bob ---")
        print(f"Plaintext: '{self.modified_message}'")
        print(f"Encrypting with Eve-Bob key: {self.aes_key_bob.hex()}")
        new_encrypted = simple_encrypt(self.modified_message, self.aes_key_bob)
        new_encrypted_hex = new_encrypted.hex()
        print(f"New ciphertext (hex): {new_encrypted_hex}")
        self.bob_sock.send((json.dumps({'encrypted_message': new_encrypted_hex}) + '\n').encode())
        print("Forwarded to Bob")
        
        # Continuous interception loop
        print("\n" + "="*60)
        print("CONTINUOUS MITM INTERCEPTION (type 'quit' to stop)")
        print("="*60)
        
        while True:
            # Intercept Bob's reply
            print("\nWaiting for Bob's reply...")
            try:
                data = recv_msg(self.bob_sock)
                if not data:
                    print("Connection closed.")
                    break
                    
                msg_data = json.loads(data)
                encrypted_hex = msg_data['encrypted_message']
                
                if encrypted_hex == 'QUIT':
                    print("\nBob ended the chat.")
                    self.alice_conn.send((json.dumps({'encrypted_message': 'QUIT'}) + '\n').encode())
                    break
                    
                encrypted_bytes = bytes.fromhex(encrypted_hex)
                reply = simple_decrypt(encrypted_bytes, self.aes_key_bob)
                print(f"Bob -> Alice: '{reply}'")
                
                # Track for analysis
                self.intercepted_messages.append({
                    'direction': 'Bob->Alice',
                    'original': reply,
                    'forwarded': reply
                })
                
                # Forward to Alice
                new_encrypted = simple_encrypt(reply, self.aes_key_alice)
                new_encrypted_hex = new_encrypted.hex()
                self.alice_conn.send((json.dumps({'encrypted_message': new_encrypted_hex}) + '\n').encode())
                print("Forwarded to Alice")
            except Exception as e:
                print(f"Error: {e}")
                break
            
            # Intercept Alice's next message
            print("\nWaiting for Alice's message...")
            try:
                data = recv_msg(self.alice_conn)
                if not data:
                    print("Connection closed.")
                    break
                    
                msg_data = json.loads(data)
                encrypted_hex = msg_data['encrypted_message']
                
                if encrypted_hex == 'QUIT':
                    print("\nAlice ended the chat.")
                    self.bob_sock.send((json.dumps({'encrypted_message': 'QUIT'}) + '\n').encode())
                    break
                    
                encrypted_bytes = bytes.fromhex(encrypted_hex)
                message = simple_decrypt(encrypted_bytes, self.aes_key_alice)
                print(f"Alice -> Bob: '{message}'")
                
                # Ask to modify
                print("\nOptions: (1) Forward original (2) Modify (3) Drop")
                choice = input("Choice (1-3, default=1): ").strip()
                
                if choice == '3':
                    print("Message dropped! (Bob won't receive anything)")
                    self.intercepted_messages.append({
                        'direction': 'Alice->Bob',
                        'original': message,
                        'forwarded': '[DROPPED]'
                    })
                    # Skip waiting for Bob's reply since he didn't get a message
                    continue
                
                forward_message = message
                if choice == '2':
                    modified = input("Modified message: ").strip()
                    if modified:
                        forward_message = modified
                        print(f"Modified to: '{forward_message}'")
                
                # Track for analysis
                self.intercepted_messages.append({
                    'direction': 'Alice->Bob',
                    'original': message,
                    'forwarded': forward_message
                })
                
                # Forward to Bob
                new_encrypted = simple_encrypt(forward_message, self.aes_key_bob)
                new_encrypted_hex = new_encrypted.hex()
                self.bob_sock.send((json.dumps({'encrypted_message': new_encrypted_hex}) + '\n').encode())
                print("Forwarded to Bob")
            except Exception as e:
                print(f"Error: {e}")
                break
        
        # Show analysis
        print("\n" + "="*60)
        print("ATTACK ANALYSIS")
        print("="*60)
        print("\nShared secrets (should be same, but aren't):")
        print(f"  Alice's: {hex(self.shared_secret_alice)[:50]}...")
        print(f"  Bob's:   {hex(self.shared_secret_bob)[:50]}...")
        print(f"  Result:  DIFFERENT - Eve has separate secrets!")
        
        print(f"\nIntercepted {len(self.intercepted_messages)} messages:")
        modified_count = 0
        dropped_count = 0
        for i, msg in enumerate(self.intercepted_messages, 1):
            if msg['forwarded'] == '[DROPPED]':
                print(f"  {i}. {msg['direction']}: '{msg['original']}' -> [DROPPED]")
                dropped_count += 1
            elif msg['original'] != msg['forwarded']:
                print(f"  {i}. {msg['direction']}: '{msg['original']}' -> '{msg['forwarded']}'")
                modified_count += 1
            else:
                print(f"  {i}. {msg['direction']}: '{msg['original']}' [unmodified]")
        
        if modified_count > 0:
            print(f"\n  Result: {modified_count} message(s) MODIFIED!")
        if dropped_count > 0:
            print(f"  Result: {dropped_count} message(s) DROPPED!")
        if modified_count == 0 and dropped_count == 0:
            print(f"\n  Result: All messages forwarded unmodified (but Eve saw everything!)")
        
        print("\nDetection: IMPOSSIBLE without authentication")
        
        # Brute force if weak
        if self.bits <= 23:
            print("\n" + "="*60)
            print("BRUTE FORCE ATTACK")
            print("="*60)
            print(f"Attempting to crack {self.bits}-bit key...")
            start = time.time()
            found = brute_force_discrete_log(
                self.alice_public_key, self.g, self.p, max_attempts=2**25
            )
            elapsed = time.time() - start
            if found:
                print(f"SUCCESS! Cracked in {elapsed:.2f} seconds")
                print(f"Alice's private key: {hex(found)}")
            else:
                print(f"Failed in {elapsed:.2f} seconds")
        
        print("\n" + "="*60)
        print("Recommendations:")
        print("  1. Use 2048-bit or larger parameters")
        print("  2. Add authentication (certificates, signatures)")
        print("  3. Use TLS/SSL protocols")
        print("="*60)
        
        # Cleanup
        if self.alice_conn:
            self.alice_conn.close()
        if self.bob_sock:
            self.bob_sock.close()
        if self.server_sock:
            self.server_sock.close()
        print("\nDone.")


def main():
    parser = argparse.ArgumentParser(description='DHKE with MITM Attack')
    parser.add_argument('--alice', action='store_true')
    parser.add_argument('--bob', action='store_true')
    parser.add_argument('--eve', action='store_true')
    parser.add_argument('--alice-port', type=int, default=5000)
    parser.add_argument('--bob-port', type=int, default=5001)
    
    args = parser.parse_args()
    
    try:
        if args.alice:
            alice = Alice(port=args.alice_port)
            alice.run()
        elif args.bob:
            bob = Bob(port=args.bob_port)
            bob.run()
        elif args.eve:
            eve = Eve(alice_port=args.alice_port, bob_port=args.bob_port)
            eve.run()
        else:
            print("Usage:")
            print("  Terminal 1: python dhke_mitm.py --bob")
            print("  Terminal 2: python dhke_mitm.py --eve")
            print("  Terminal 3: python dhke_mitm.py --alice")
    except KeyboardInterrupt:
        print("\n\nInterrupted.")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == '__main__':
    main()

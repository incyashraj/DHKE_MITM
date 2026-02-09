#!/usr/bin/env python3
"""
Passive Eavesdropping Attack on DHKE
Eve captures public keys and tries to break the encryption via brute force DLP
"""

import socket
import json
import sys
import time
from dh_params import (
    get_dh_params,
    compute_shared_secret,
    derive_key,
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


class PassiveEve:
    """
    Eve as passive eavesdropper - captures traffic but doesn't modify
    """
    def __init__(self, alice_port=5000):
        self.alice_port = alice_port
        self.p = None
        self.g = None
        self.bits = None
        self.alice_public_key = None
        self.bob_public_key = None
        self.captured_messages = []
        self.alice_private_key = None
        self.bob_private_key = None
        self.shared_secret = None
        self.aes_key = None
        
    def estimate_brute_force_time(self):
        """
        Estimate time to brute force based on parameter size
        Assumes ~1 million attempts per second (modern CPU)
        """
        attempts_per_second = 1_000_000
        
        if self.bits == 23:
            max_attempts = self.p
            seconds = max_attempts / attempts_per_second
            return f"{seconds:.3f} seconds (FEASIBLE)"
        elif self.bits == 512:
            # 2^512 ≈ 10^154 attempts
            return f"~10^148 years (INFEASIBLE - longer than age of universe)"
        elif self.bits == 1024:
            # 2^1024 ≈ 10^308 attempts
            return f"~10^302 years (COMPLETELY INFEASIBLE)"
        elif self.bits == 2048:
            # 2^2048 ≈ 10^617 attempts
            return f"~10^611 years (ASTRONOMICALLY INFEASIBLE)"
        else:
            return "Unknown parameter size"
    
    def sniff_traffic(self):
        """
        Simulate packet sniffing - get captured data from user
        """
        print("What security parameters did they use?")
        print("1. 23-bit (weak)")
        print("2. 512-bit")
        print("3. 1024-bit")
        print("4. 2048-bit")
        choice = input("\nChoice (1-4): ").strip()
        bits_map = {'1': 23, '2': 512, '3': 1024, '4': 2048}
        self.bits = bits_map.get(choice, 23)
        self.p, self.g = get_dh_params(self.bits)
        
        print(f"\n Parameters: {self.bits}-bit (p={self.p}, g={self.g})")
        
        # Get Alice's public key
        print("\n")
        print("Capture Alice's Public Key A")
        alice_pub_input = input("Alice's A: ").strip()
        try:
            self.alice_public_key = int(alice_pub_input)
            print(f" Captured: {self.alice_public_key}")
        except ValueError:
            print("Invalid number")
            sys.exit(1)
        
        # Get Bob's public key
        print("\n")
        print("Capture Bob's Public Key B")
        print("\n")
        bob_pub_input = input("Bob's B: ").strip()
        try:
            self.bob_public_key = int(bob_pub_input)
            print(f" Captured: {self.bob_public_key}")
        except ValueError:
            print("Invalid number")
            sys.exit(1)
        
        # Get encrypted messages
        print("\n")
        print("Capture Encrypted Messages")
        print("Paste ciphertext (hex) - one per line, 'done' to finish:\n")
        
        while True:
            ciphertext = input("Ciphertext: ").strip()
            if ciphertext.lower() == 'done':
                break
            if ciphertext:
                self.captured_messages.append(ciphertext)
                print(f" Captured message {len(self.captured_messages)}")
        
        print(f"\n Total messages captured: {len(self.captured_messages)}")
    
    def analyze_security(self):
        """Analyze whether attack is feasible"""
        print("\n")
        print("ANALYZING SECURITY")
        
        print(f"\nParameter size: {self.bits}-bit")
        print(f"Search space: [1, {self.p-1}]")
        
        estimated_time = self.estimate_brute_force_time()
        print(f"Brute force time: {estimated_time}")
        
        if self.bits == 23:
            print("\n ATTACK IS FEASIBLE - Attempting brute force...")
            return True
        else:
            print("\n ATTACK IS INFEASIBLE - Cannot break strong parameters")
            return False
    
    def attempt_break(self):
        """Attempt to break encryption by finding private key via brute force"""
        feasible = self.analyze_security()
        
        if not feasible:
            print("\n" + "="*70)
            print("RESULT: ATTACK FAILED")
            print("="*70)
            print("\n Alice and Bob are SAFE!")
            print("   Large parameters protect against passive attacks.")
            print("   Eve cannot decrypt without solving DLP (infeasible).")
            return False
        
        # Attempt brute force (only for weak parameters)
        print("\n")
        print("ATTEMPTING BRUTE FORCE")
        
        print("\nSearching for Alice's private key 'a' where A = g^a mod p...")
        
        start_time = time.time()
        self.alice_private_key = brute_force_discrete_log(
            self.g,
            self.alice_public_key,
            self.p
        )
        elapsed = time.time() - start_time
        
        if not self.alice_private_key:
            print(f"\n Failed after {elapsed:.2f} seconds")
            return False
        
        print(f"\n FOUND! Alice's private key: a = {self.alice_private_key}")
        print(f"   Time taken: {elapsed:.3f} seconds")
        
        # Compute shared secret
        print(f"\nComputing shared secret: s = B^a mod p")
        self.shared_secret = compute_shared_secret(
            self.bob_public_key,
            self.alice_private_key,
            self.p
        )
        print(f"   s = {self.shared_secret}")
        
        # Derive encryption key
        self.aes_key = derive_key(self.shared_secret)
        print(f"   Key: {self.aes_key.hex()}")
        
        return True
    
    def decrypt_messages(self):
        """Decrypt all captured messages using stolen key"""
        if not self.aes_key:
            print("\n Cannot decrypt - no key available")
            return
        
        print("\n")
        print("DECRYPTING MESSAGES")
        
        if not self.captured_messages:
            print("\nNo messages captured.")
            return
        
        print(f"\nDecrypting {len(self.captured_messages)} message(s)...\n")
        
        for i, ciphertext_hex in enumerate(self.captured_messages, 1):
            try:
                encrypted_bytes = bytes.fromhex(ciphertext_hex)
                plaintext = simple_decrypt(encrypted_bytes, self.aes_key)
                
                print(f"Message {i}:")
                print(f"  Ciphertext: {ciphertext_hex}")
                print(f"  Plaintext:  '{plaintext}'")
                print(f"  DECRYPTED!\n")
            except Exception as e:
                print(f"Message {i}: Decryption failed - {e}\n")
    
    def show_summary(self):
        """Display attack summary"""
        print("\n")
        print("ATTACK SUMMARY")
        
        if self.alice_private_key:
            print(f"\n ATTACK SUCCESSFUL!")
            print(f"   Security: {self.bits}-bit (WEAK)")
            print(f"   Private key found: {self.alice_private_key}")
            print(f"   Decrypted: {len(self.captured_messages)} message(s)")
            print(f"\n LESSON: Weak parameters ({self.bits}-bit) are INSECURE")
            print(f"   Use 2048-bit minimum for real security!")
        else:
            print(f"\n ATTACK FAILED")
            print(f"   Security: {self.bits}-bit (STRONG)")
            print(f"   Brute force computationally infeasible")
            print(f"\n LESSON: Strong parameters prevent passive attacks")
            print(f"   Even with public keys + ciphertext, Eve cannot decrypt")
    
    def run(self):
        """Main execution flow"""
        try:
            self.sniff_traffic()
            success = self.attempt_break()
            if success:
                self.decrypt_messages()
            self.show_summary()
        except KeyboardInterrupt:
            print("\n\nInterrupted.")
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()


def main():
    print("\n" + "="*70)
    print("EVE: PASSIVE EAVESDROPPING ATTACK")
    print("="*70)
    print("\nAttempting to break Alice and Bob's encryption...")
    print("(Run dhke_secure.py in other terminals first)\n")
    
    eve = PassiveEve()
    eve.run()


if __name__ == '__main__':
    main()

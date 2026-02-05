"""
Analysis and Testing Suite for DHKE Implementation

This script provides comprehensive testing and analysis of the DHKE implementation:
1. Unit tests for correctness
2. Security analysis (parameter strength, randomness quality)
3. Performance benchmarks (1024-bit vs 2048-bit)
4. Weak parameter demonstration (small prime attack)
5. Integration tests

Run this to verify the implementation before presentation!
"""

import time
import os
import secrets
import random
from dh_params import (
    get_dh_params, generate_private_key, compute_public_key,
    compute_shared_secret, derive_key, simple_encrypt, simple_decrypt,
    brute_force_discrete_log, validate_params
)


class TestResults:
    """Simple class to track test results."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def add_test(self, name, passed, message=""):
        self.tests.append({
            'name': name,
            'passed': passed,
            'message': message
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def print_summary(self):
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        for test in self.tests:
            status = "✓ PASS" if test['passed'] else "✗ FAIL"
            print(f"{status}: {test['name']}")
            if test['message']:
                print(f"       {test['message']}")
        print(f"\nTotal: {self.passed + self.failed} tests")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print("=" * 70)


def test_parameter_validation(results):
    """Test that parameter validation works correctly."""
    print("\n--- Testing Parameter Validation ---")
    
    # Test valid parameters
    try:
        p, g = get_dh_params(2048)
        validate_params(p, g)
        results.add_test("Valid 2048-bit parameters", True)
        print("✓ Valid parameters accepted")
    except Exception as e:
        results.add_test("Valid 2048-bit parameters", False, str(e))
        print(f"✗ Error: {e}")
    
    # Test invalid generator
    try:
        validate_params(23, 1)  # g=1 is invalid
        results.add_test("Invalid generator detection", False, "Should have rejected g=1")
        print("✗ Failed to reject invalid generator")
    except ValueError:
        results.add_test("Invalid generator detection", True)
        print("✓ Invalid generator correctly rejected")
    
    # Test invalid prime
    try:
        validate_params(1, 2)  # p=1 is invalid
        results.add_test("Invalid prime detection", False, "Should have rejected p=1")
        print("✗ Failed to reject invalid prime")
    except ValueError:
        results.add_test("Invalid prime detection", True)
        print("✓ Invalid prime correctly rejected")


def test_shared_secret_matching(results):
    """Test that Alice and Bob compute the same shared secret."""
    print("\n--- Testing Shared Secret Agreement ---")
    
    for bit_length in [1024, 2048]:
        try:
            p, g = get_dh_params(bit_length)
            
            # Alice's side
            alice_private = generate_private_key(p)
            alice_public = compute_public_key(g, alice_private, p)
            
            # Bob's side
            bob_private = generate_private_key(p)
            bob_public = compute_public_key(g, bob_private, p)
            
            # Compute shared secrets
            alice_shared = compute_shared_secret(bob_public, alice_private, p)
            bob_shared = compute_shared_secret(alice_public, bob_private, p)
            
            # They should match!
            if alice_shared == bob_shared:
                results.add_test(f"Shared secret match ({bit_length}-bit)", True)
                print(f"✓ {bit_length}-bit: Secrets match (value: {str(alice_shared)[:20]}...)")
            else:
                results.add_test(f"Shared secret match ({bit_length}-bit)", False, 
                               "Alice and Bob computed different secrets!")
                print(f"✗ {bit_length}-bit: Secrets don't match!")
                
        except Exception as e:
            results.add_test(f"Shared secret match ({bit_length}-bit)", False, str(e))
            print(f"✗ {bit_length}-bit: Error - {e}")


def test_encryption_decryption(results):
    """Test that encryption and decryption work correctly."""
    print("\n--- Testing Encryption/Decryption ---")
    
    test_messages = [
        "Hello World!",
        "This is a test message with special chars: !@#$%^&*()",
        "A" * 1000,  # Long message
        "短信测试"  # Unicode
    ]
    
    p, g = get_dh_params(1024)
    private = generate_private_key(p)
    public = compute_public_key(g, private, p)
    shared = compute_shared_secret(public, private, p)  # Self-exchange for testing
    key = derive_key(shared)
    
    all_passed = True
    for msg in test_messages:
        try:
            encrypted = simple_encrypt(msg, key)
            decrypted = simple_decrypt(encrypted, key)
            
            if msg == decrypted:
                print(f"✓ Message encrypted/decrypted: '{msg[:30]}...'")
            else:
                print(f"✗ Decryption failed for: '{msg[:30]}'")
                all_passed = False
        except Exception as e:
            print(f"✗ Error with message '{msg[:30]}': {e}")
            all_passed = False
    
    results.add_test("Encryption/Decryption correctness", all_passed)


def test_mitm_vulnerability(results):
    """Demonstrate that without authentication, MITM is possible."""
    print("\n--- Testing MITM Vulnerability ---")
    
    # Setup
    p, g = get_dh_params(1024)
    
    # Alice's keys
    alice_private = generate_private_key(p)
    alice_public = compute_public_key(g, alice_private, p)
    
    # Bob's keys
    bob_private = generate_private_key(p)
    bob_public = compute_public_key(g, bob_private, p)
    
    # Eve's keys (two separate key pairs)
    eve_private_alice = generate_private_key(p)
    eve_public_alice = compute_public_key(g, eve_private_alice, p)
    
    eve_private_bob = generate_private_key(p)
    eve_public_bob = compute_public_key(g, eve_private_bob, p)
    
    # What happens in MITM:
    # Alice computes secret with Eve's key (thinking it's Bob's)
    alice_shared = compute_shared_secret(eve_public_alice, alice_private, p)
    
    # Bob computes secret with Eve's other key (thinking it's Alice's)
    bob_shared = compute_shared_secret(eve_public_bob, bob_private, p)
    
    # Eve can compute both secrets
    eve_shared_with_alice = compute_shared_secret(alice_public, eve_private_alice, p)
    eve_shared_with_bob = compute_shared_secret(bob_public, eve_private_bob, p)
    
    # Verify the attack works
    alice_bob_different = (alice_shared != bob_shared)
    eve_matches_alice = (eve_shared_with_alice == alice_shared)
    eve_matches_bob = (eve_shared_with_bob == bob_shared)
    
    mitm_successful = alice_bob_different and eve_matches_alice and eve_matches_bob
    
    if mitm_successful:
        results.add_test("MITM attack possible (as expected)", True)
        print("✓ MITM attack successful (this demonstrates the vulnerability)")
        print(f"  - Alice's secret: {str(alice_shared)[:20]}...")
        print(f"  - Bob's secret:   {str(bob_shared)[:20]}...")
        print(f"  - Secrets differ: {alice_shared != bob_shared}")
        print("  - Eve can decrypt both channels!")
    else:
        results.add_test("MITM attack possible (as expected)", False, 
                       "MITM didn't work as expected")
        print("✗ MITM attack failed (unexpected)")


def test_weak_parameters(results):
    """Test that weak parameters can be broken."""
    print("\n--- Testing Weak Parameter Attack ---")
    
    p, g = get_dh_params("weak")
    print(f"Using weak parameters: p={p}, g={g}")
    
    # Generate a key
    private_key = 17  # Fixed for reproducibility
    public_key = compute_public_key(g, private_key, p)
    
    print(f"Private key: {private_key}")
    print(f"Public key: {public_key}")
    
    # Try to crack it
    print("Attempting brute force attack...")
    start_time = time.perf_counter()
    cracked_key = brute_force_discrete_log(g, public_key, p)
    attack_time = time.perf_counter() - start_time
    
    if cracked_key == private_key:
        results.add_test("Weak parameter attack", True)
        print(f"✓ Successfully cracked! Found private key: {cracked_key}")
        print(f"  Attack took: {attack_time*1000:.2f} ms")
        print("  This shows why large primes are essential!")
    else:
        results.add_test("Weak parameter attack", False, 
                       f"Found {cracked_key} instead of {private_key}")
        print(f"✗ Attack failed")


def test_randomness_quality(results):
    """Test the quality of random number generation."""
    print("\n--- Testing Randomness Quality ---")
    
    p, g = get_dh_params(1024)
    
    # Generate multiple keys and check they're different
    keys = set()
    num_keys = 100
    
    print(f"Generating {num_keys} private keys...")
    for _ in range(num_keys):
        key = generate_private_key(p, secure=True)
        keys.add(key)
    
    uniqueness = len(keys) / num_keys
    print(f"Uniqueness: {uniqueness*100:.1f}% ({len(keys)}/{num_keys} unique)")
    
    if uniqueness > 0.99:  # Allow for tiny collision chance
        results.add_test("Random key uniqueness", True)
        print("✓ Good randomness - all keys are unique")
    else:
        results.add_test("Random key uniqueness", False, 
                       f"Only {uniqueness*100:.1f}% unique")
        print(f"✗ Poor randomness - only {uniqueness*100:.1f}% unique")
    
    # Test insecure random (for comparison)
    print("\nTesting insecure random (for comparison)...")
    random.seed(12345)  # Fixed seed
    insecure_keys = set()
    for _ in range(10):
        key = generate_private_key(p, secure=False)
        insecure_keys.add(key)
    
    # Reset and regenerate with same seed
    random.seed(12345)
    insecure_keys_2 = set()
    for _ in range(10):
        key = generate_private_key(p, secure=False)
        insecure_keys_2.add(key)
    
    predictable = (insecure_keys == insecure_keys_2)
    if predictable:
        print("✓ Insecure random is predictable (as expected with fixed seed)")
        print("  This demonstrates why secure random is critical!")
    else:
        print("✗ Unexpected: insecure random not predictable with fixed seed")


def benchmark_performance(results):
    """Benchmark performance of different key sizes."""
    print("\n--- Performance Benchmarks ---")
    
    key_sizes = [1024, 2048]
    iterations = 10
    
    for bit_length in key_sizes:
        print(f"\nBenchmarking {bit_length}-bit keys ({iterations} iterations)...")
        p, g = get_dh_params(bit_length)
        
        # Time key generation
        key_gen_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            private = generate_private_key(p)
            public = compute_public_key(g, private, p)
            key_gen_times.append(time.perf_counter() - start)
        
        avg_key_gen = sum(key_gen_times) / len(key_gen_times)
        
        # Time shared secret computation
        alice_private = generate_private_key(p)
        alice_public = compute_public_key(g, alice_private, p)
        bob_private = generate_private_key(p)
        bob_public = compute_public_key(g, bob_private, p)
        
        secret_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            shared = compute_shared_secret(bob_public, alice_private, p)
            secret_times.append(time.perf_counter() - start)
        
        avg_secret = sum(secret_times) / len(secret_times)
        
        print(f"  Key generation: {avg_key_gen*1000:.2f} ms")
        print(f"  Secret computation: {avg_secret*1000:.2f} ms")
        print(f"  Total exchange: {(avg_key_gen*2 + avg_secret*2)*1000:.2f} ms")
    
    results.add_test("Performance benchmarks completed", True)
    
    # Compare
    print("\nPerformance insights:")
    print("  - Larger keys are slower but much more secure")
    print("  - 2048-bit provides good security for most applications")
    print("  - For production, consider 3072-bit or 4096-bit")


def test_key_derivation(results):
    """Test that key derivation produces consistent results."""
    print("\n--- Testing Key Derivation ---")
    
    shared_secret = 123456789012345678901234567890
    
    # Derive key multiple times
    key1 = derive_key(shared_secret)
    key2 = derive_key(shared_secret)
    
    if key1 == key2 and len(key1) == 32:
        results.add_test("Key derivation consistency", True)
        print("✓ Key derivation is consistent")
        print(f"  Key length: {len(key1)} bytes")
        print(f"  Key (hex): {key1.hex()[:40]}...")
    else:
        results.add_test("Key derivation consistency", False)
        print("✗ Key derivation inconsistent or wrong length")
    
    # Test different secrets produce different keys
    key3 = derive_key(shared_secret + 1)
    if key1 != key3:
        print("✓ Different secrets produce different keys")
    else:
        print("✗ Warning: different secrets produced same key!")


def integration_test(results):
    """Full integration test simulating complete exchange."""
    print("\n--- Integration Test: Complete Key Exchange ---")
    
    try:
        # Setup
        p, g = get_dh_params(1024)
        
        # Alice
        alice_priv = generate_private_key(p)
        alice_pub = compute_public_key(g, alice_priv, p)
        
        # Bob
        bob_priv = generate_private_key(p)
        bob_pub = compute_public_key(g, bob_priv, p)
        
        # Exchange and compute secrets
        alice_secret = compute_shared_secret(bob_pub, alice_priv, p)
        bob_secret = compute_shared_secret(alice_pub, bob_priv, p)
        
        # Derive keys
        alice_key = derive_key(alice_secret)
        bob_key = derive_key(bob_secret)
        
        # Test message exchange
        message = "Integration test message!"
        
        # Alice encrypts
        encrypted = simple_encrypt(message, alice_key)
        
        # Bob decrypts
        decrypted = simple_decrypt(encrypted, bob_key)
        
        success = (decrypted == message)
        results.add_test("Full integration test", success)
        
        if success:
            print("✓ Complete key exchange and message transmission successful!")
            print(f"  Original: {message}")
            print(f"  Received: {decrypted}")
        else:
            print("✗ Integration test failed")
            print(f"  Expected: {message}")
            print(f"  Got: {decrypted}")
            
    except Exception as e:
        results.add_test("Full integration test", False, str(e))
        print(f"✗ Integration test error: {e}")
        import traceback
        traceback.print_exc()


def run_all_tests():
    """Run complete test suite."""
    print("=" * 70)
    print("DHKE IMPLEMENTATION - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print("Testing correctness, security, and performance...")
    
    results = TestResults()
    
    # Run all tests
    test_parameter_validation(results)
    test_shared_secret_matching(results)
    test_encryption_decryption(results)
    test_key_derivation(results)
    test_mitm_vulnerability(results)
    test_weak_parameters(results)
    test_randomness_quality(results)
    integration_test(results)
    benchmark_performance(results)
    
    # Print summary
    results.print_summary()
    
    # Educational insights
    print("\n" + "=" * 70)
    print("KEY INSIGHTS FOR YOUR PRESENTATION")
    print("=" * 70)
    print("""
1. DHKE Security:
   - Relies on discrete logarithm problem (DLP) being hard
   - Large safe primes (2048+ bits) make DLP computationally infeasible
   - With weak parameters (small primes), can be broken in milliseconds

2. MITM Vulnerability:
   - Without authentication, attacker can impersonate both parties
   - Eve establishes separate secrets with Alice and Bob
   - Can read and modify all messages without detection
   - Real protocols (TLS) add authentication via certificates

3. Performance Trade-offs:
   - Larger keys = more security but slower computation
   - 1024-bit: Fast but considered weak for long-term security
   - 2048-bit: Good balance, recommended minimum today
   - 4096-bit: Very secure but ~8x slower key generation

4. Implementation Security:
   - MUST use cryptographically secure random (os.urandom, secrets)
   - Predictable random = attacker can guess private keys
   - Key derivation (hashing) prevents secret leakage

5. Real-world Applications:
   - TLS/SSL handshakes for HTTPS
   - VPN key establishment (IPsec)
   - Signal, WhatsApp end-to-end encryption
   - SSH key exchange
    """)
    
    return results.failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! Implementation is ready for presentation.")
    else:
        print("\n⚠️  Some tests failed. Review the results above.")
        exit(1)

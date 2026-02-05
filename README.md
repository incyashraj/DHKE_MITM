# Diffie-Hellman Key Exchange (DHKE) with MITM Attack Demonstration

**SC6104 - Introduction to Cryptography | NTU Singapore**

A comprehensive implementation and security analysis of the Diffie-Hellman Key Exchange protocol, demonstrating both secure key agreement and its vulnerability to Man-in-the-Middle attacks when authentication is absent.

## 📋 Project Overview

This project demonstrates fundamental concepts in public-key cryptography:

- **Secure Key Exchange**: How two parties can establish a shared secret over an insecure channel
- **Discrete Logarithm Problem**: The mathematical foundation ensuring DHKE security
- **MITM Vulnerability**: Why authentication is critical in real-world protocols
- **Performance Analysis**: Trade-offs between key sizes and computational efficiency

### Why This Matters

DHKE is fundamental to modern internet security:
- **TLS/SSL**: Establishes HTTPS connections
- **VPN Protocols**: Secure IPsec tunnels
- **Messaging Apps**: Signal, WhatsApp end-to-end encryption
- **SSH**: Secure remote access

Understanding its strengths and weaknesses is crucial for implementing secure systems.

## 🗂️ Project Structure

```
.
├── dh_params.py          # Core cryptographic utilities and parameters
├── dhke_secure.py        # Secure two-party key exchange (Alice-Bob)
├── dhke_mitm.py          # Man-in-the-Middle attack simulation (Alice-Eve-Bob)
├── analysis.py           # Comprehensive testing and analysis suite
└── README.md             # This file
```

## 🔐 Cryptographic Background

### The Diffie-Hellman Protocol

**Public Parameters** (known to everyone):
- `p`: Large prime modulus (safe prime: p = 2q + 1)
- `g`: Generator (typically 2 or 5)

**Key Exchange Process**:

1. **Alice's Side**:
   - Chooses secret `a` (private key)
   - Computes `A = g^a mod p` (public key)
   - Sends `A` to Bob

2. **Bob's Side**:
   - Chooses secret `b` (private key)
   - Computes `B = g^b mod p` (public key)
   - Sends `B` to Alice

3. **Shared Secret Computation**:
   - Alice computes: `s = B^a mod p = (g^b)^a mod p = g^(ab) mod p`
   - Bob computes: `s = A^b mod p = (g^a)^b mod p = g^(ab) mod p`
   - Both arrive at the same secret!

**Security Foundation**: An eavesdropper sees `g`, `p`, `A`, and `B` but cannot compute `g^(ab) mod p` without knowing `a` or `b`. Finding `a` from `A = g^a mod p` is the **Discrete Logarithm Problem (DLP)**, which is computationally infeasible for large primes.

### Why It Can Be Attacked (MITM)

Without authentication, DHKE is vulnerable to active attacks:

**Normal Exchange**:
```
Alice <--[g^(ab)]-- Bob
```

**MITM Attack**:
```
Alice <--[g^(ae)]-- Eve <--[g^(eb)]-- Bob
      thinks: Bob            thinks: Alice
```

Eve establishes separate secrets with both parties and can decrypt/modify all traffic.

**Real-World Solution**: Protocols like TLS use digital certificates to authenticate public keys, preventing impersonation.

## 🚀 Getting Started

### Prerequisites

- Python 3.7 or higher
- No external dependencies (uses only standard library)

### Installation

```bash
# Clone or download the project
cd "Intro to Cryptography/Project"

# Verify files are present
ls -l
```

## 📖 Usage Guide

### 1. Running Tests (Start Here!)

Verify the implementation before running demonstrations:

```bash
python analysis.py
```

This will:
- Run unit tests on all cryptographic operations
- Verify shared secret agreement works correctly
- Demonstrate the weak parameter attack
- Benchmark performance (1024-bit vs 2048-bit)
- Test randomness quality
- Run integration tests

**Expected Output**: All tests should pass with performance metrics.

### 2. Secure Key Exchange Demo

Demonstrates successful secure communication between Alice and Bob.

**Terminal 1** (Start Bob first):
```bash
python dhke_secure.py --bob
```

**Terminal 2** (Then start Alice):
```bash
python dhke_secure.py --alice
```

**What Happens**:
1. Bob waits for Alice to connect
2. Alice initiates key exchange
3. Both compute the same shared secret
4. Alice sends encrypted message
5. Bob receives and decrypts successfully

**Key Observations**:
- Both parties compute identical shared secrets
- Messages are encrypted end-to-end
- Without private keys, eavesdropper sees only ciphertext

### 3. Man-in-the-Middle Attack Demo

Demonstrates how Eve intercepts and modifies communication.

**Terminal 1** (Start Bob):
```bash
python dhke_mitm.py --bob
```

**Terminal 2** (Start Eve - the attacker):
```bash
python dhke_mitm.py --eve
```

**Terminal 3** (Start Alice):
```bash
python dhke_mitm.py --alice
```

**What Happens**:
1. Alice thinks she's connecting to Bob, but connects to Eve
2. Eve intercepts Alice's public key
3. Eve generates TWO separate key pairs
4. Eve establishes secret with Alice using one key
5. Eve establishes secret with Bob using another key
6. Alice's message is decrypted, modified, and re-encrypted by Eve
7. Bob receives the modified message thinking it's from Alice

**Key Observations**:
- Alice and Bob have DIFFERENT shared secrets
- Eve can read and modify all messages
- Neither victim detects the attack
- This is why TLS requires certificate authentication!

### 4. 🎮 MANUAL MODE - Complete Control (NEW!)

**The most educational and demonstration-friendly mode!**

This gives you **complete manual control** over every single step:
- ✅ Choose security parameters (23/512/1024/2048-bit)
- ✅ See connection establishment details
- ✅ Press ENTER to advance each step
- ✅ Type your own messages
- ✅ Watch key generation step-by-step
- ✅ Control when Eve intercepts and modifies messages
- ✅ Attempt brute force on weak parameters

#### Direct Secure Communication:

**Terminal 1** (Bob - Receiver):
```bash
python dhke_manual.py --bob
```

**Terminal 2** (Alice - Sender):
```bash
python dhke_manual.py --alice
```

You'll be prompted to:
- Select security parameters (1-4)
- Press ENTER between each protocol step
- Type custom messages to send
- Watch encryption/decryption happen live

#### MITM Attack with Full Control:

**Terminal 1** (Bob on port 5001):
```bash
python dhke_manual.py --bob --bob-port 5001
```

**Terminal 2** (Eve - The attacker):
```bash
python dhke_manual.py --eve --alice-port 5000 --bob-port 5001
```

**Terminal 3** (Alice connects to Eve):
```bash
python dhke_manual.py --alice --alice-port 5000
```

In this mode, you can:
- **See Eve intercept parameters and keys**
- **Watch Eve generate TWO different key pairs**
- **Control when Eve decrypts messages**
- **Choose to modify messages or forward originals**
- **See attack summary with different secrets**
- **Attempt brute force if using weak parameters**

**Perfect for:**
- 🎓 Learning every detail of the protocol
- 🎤 Live demonstrations and presentations
- 🔬 Understanding MITM attack mechanics
- 🎯 Showing security parameter impact

**See [MANUAL_MODE_GUIDE.md](MANUAL_MODE_GUIDE.md) for detailed walkthrough!**

## 🔬 Technical Details

### Security Parameters

#### 2048-bit Prime (Default)
- **Prime**: RFC 3526 MODP Group 14
- **Security Level**: ~112-bit (equivalent to 2048-bit RSA)
- **Status**: Currently recommended minimum
- **Use Case**: Standard web security (HTTPS)

#### 1024-bit Prime (Fast Demo)
- **Prime**: RFC 3526 MODP Group 2
- **Security Level**: ~80-bit
- **Status**: Deprecated for production use
- **Use Case**: Fast demonstrations, testing

#### Weak Prime (23)
- **Purpose**: Educational - demonstrates DLP attack
- **Breakability**: Brute force in milliseconds
- **Lesson**: Shows why large primes are essential

### Key Functions (dh_params.py)

```python
# Get standard DH parameters
p, g = get_dh_params(2048)  # or 1024, or "weak"

# Generate secure private key
private_key = generate_private_key(p, secure=True)

# Compute public key
public_key = compute_public_key(g, private_key, p)

# Compute shared secret
shared_secret = compute_shared_secret(other_public, my_private, p)

# Derive encryption key
encryption_key = derive_key(shared_secret)
```

### Performance Benchmarks

Typical performance on modern hardware:

| Operation | 1024-bit | 2048-bit |
|-----------|----------|----------|
| Key Generation | ~2-5 ms | ~10-20 ms |
| Secret Computation | ~2-5 ms | ~10-20 ms |
| Full Exchange | ~8-20 ms | ~40-80 ms |

**Note**: 2048-bit is ~4x slower but provides significantly stronger security.

## 🎓 Educational Insights

### 1. The Discrete Logarithm Problem

**Easy Direction** (modular exponentiation):
```
Given g=2, p=23, a=17
Compute A = 2^17 mod 23 = 18    [Fast: O(log a)]
```

**Hard Direction** (discrete logarithm):
```
Given g=2, p=23, A=18
Find a such that 2^a mod 23 = 18    [Slow: O(√p) with best known algorithms]
```

For small p (like 23), we can brute force. For large p (2048 bits), this becomes computationally infeasible.

### 2. Why Safe Primes?

A **safe prime** has the form p = 2q + 1 where q is also prime.

**Benefits**:
- Prevents small subgroup attacks
- Ensures generator has large order
- Provides strong security guarantees

Our implementation uses standardized safe primes from RFC 3526.

### 3. Randomness Matters

**Secure Random** (os.urandom):
- Uses OS entropy pool
- Unpredictable even if previous values known
- Essential for security

**Insecure Random** (random.randint):
- Pseudo-random (deterministic with seed)
- Attacker who knows seed can predict all keys
- Never use for cryptography!

Run `analysis.py` to see the demonstration.

### 4. Authentication Prevents MITM

In TLS:
1. Server sends certificate (public key + signature from trusted CA)
2. Client verifies certificate signature
3. Client uses authenticated public key for DHKE
4. MITM impossible without valid certificate

Our implementation shows what happens WITHOUT this authentication.

## 🧪 Testing & Validation

### Test Coverage

The `analysis.py` script includes:

1. **Unit Tests**:
   - Parameter validation
   - Shared secret agreement
   - Encryption/decryption correctness
   - Key derivation consistency

2. **Security Tests**:
   - MITM vulnerability demonstration
   - Weak parameter attack
   - Randomness quality analysis

3. **Performance Tests**:
   - Key generation benchmarks
   - Secret computation benchmarks
   - Size vs. speed trade-offs

4. **Integration Tests**:
   - Full key exchange simulation
   - End-to-end message transmission

### Running Specific Tests

```bash
# Run all tests
python analysis.py

# Test individual components
python -c "from dh_params import *; p, g = get_dh_params('weak'); print(brute_force_discrete_log(5, 16, 23))"
```

## 🎯 Key Takeaways for Presentation

### Strengths of DHKE:
✅ Enables key agreement without prior shared secrets  
✅ Based on hard mathematical problem (DLP)  
✅ Efficient for large keys (O(log n) exponentiation)  
✅ Foundation of modern secure communications  

### Weaknesses Without Authentication:
❌ Vulnerable to active Man-in-the-Middle attacks  
❌ Cannot verify identity of communication partner  
❌ Attacker can impersonate both parties  
❌ All traffic can be read and modified  

### Real-World Solutions:
🔒 TLS: Certificates + authenticated key exchange  
🔒 SSH: Public key fingerprint verification  
🔒 Signal: Trust-on-first-use + safety numbers  
🔒 IPsec: Pre-shared keys or certificate infrastructure  

## 🔍 Common Questions

### Q: Why not just use RSA for key exchange?
**A**: DHKE has forward secrecy - even if long-term keys are compromised later, past sessions remain secure. RSA key exchange doesn't provide this.

### Q: Can we detect a MITM attack?
**A**: Not without authentication! That's the whole problem. In practice, we authenticate using:
- Digital certificates (TLS)
- Pre-shared keys (IPsec)
- Trust-on-first-use (SSH)
- Out-of-band verification (Signal safety numbers)

### Q: What's the difference between DHKE and ECDH?
**A**: ECDH uses elliptic curves instead of modular arithmetic. Provides same security with smaller keys (256-bit ECDH ≈ 3072-bit DH). More efficient but same principles.

### Q: Is the encryption in this project production-ready?
**A**: No! The simple XOR encryption is for demonstration only. Production code should use:
- AES-GCM (authenticated encryption)
- ChaCha20-Poly1305
- Other AEAD ciphers

We use simple encryption to keep focus on the key exchange, not the encryption algorithm.

## 📚 References & Further Reading

### Standards & RFCs:
- [RFC 3526](https://tools.ietf.org/html/rfc3526) - MODP Diffie-Hellman groups
- [RFC 7919](https://tools.ietf.org/html/rfc7919) - Finite Field Groups for TLS
- [RFC 5246](https://tools.ietf.org/html/rfc5246) - TLS 1.2 (uses DHE/ECDHE)

### Academic Resources:
- Diffie & Hellman's original paper (1976): "New Directions in Cryptography"
- Cryptography textbooks: Katz & Lindell, Boneh & Shoup
- NIST Special Publication 800-56A: Recommendation for Pair-Wise Key Establishment

### Course Connection:
This project directly implements concepts from:
- Week 5-6: Public Key Cryptography
- Key Agreement protocols
- Discrete Logarithm Problem
- Number theory foundations

## ⚠️ Security Disclaimer

This implementation is for **educational purposes only**:
- Uses simplified encryption (not production-grade)
- No protection against timing attacks
- No input validation for network data
- Meant for understanding concepts, not deployment

For production applications, use established libraries:
- OpenSSL / LibreSSL
- cryptography (Python)
- NaCl / libsodium
- Bouncy Castle

## 👥 Project Information

**Course**: SC6104 - Introduction to Cryptography  
**Institution**: Nanyang Technological University (NTU), Singapore  
**Topic**: Asymmetric Cryptography - Key Exchange Protocols  

**Learning Objectives Achieved**:
1. Implemented public-key cryptographic protocol from scratch
2. Demonstrated mathematical foundations (DLP, modular arithmetic)
3. Analyzed security properties and vulnerabilities
4. Explored real-world applications and attack scenarios
5. Understood importance of authentication in cryptographic protocols

## 🛠️ Troubleshooting

### Issue: "Connection Refused" error
**Solution**: Make sure you start the server (Bob/Eve) before the client (Alice).

### Issue: Test failures in analysis.py
**Solution**: Check Python version (3.7+ required). Verify all files are present.

### Issue: Slow performance on weak hardware
**Solution**: Use 1024-bit keys for demos: `python dhke_secure.py --alice --bits 1024`

### Issue: Import errors
**Solution**: Run scripts from the project directory: `cd "Intro to Cryptography/Project"`

## 📝 Quick Reference

### Run Secure Demo:
```bash
# Terminal 1
python dhke_secure.py --bob

# Terminal 2  
python dhke_secure.py --alice
```

### Run MITM Demo:
```bash
# Terminal 1
python dhke_mitm.py --bob

# Terminal 2
python dhke_mitm.py --eve

# Terminal 3
python dhke_mitm.py --alice
```

### Run All Tests:
```bash
python analysis.py
```

---

**Last Updated**: February 2026  
**Python Version**: 3.7+  
**License**: Educational Use

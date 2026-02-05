# Attack Comparison Guide

## Three Types of Attacks Demonstrated in This Project

---

## 1. ✅ SECURE COMMUNICATION (No Attack)
**Script:** `dhke_secure.py`

### Scenario:
- Alice and Bob communicate directly
- No attacker present
- Uses proper security parameters (1024/2048-bit)

### Result:
- ✅ **SECURE** - Messages are encrypted and safe
- Eve can see encrypted traffic but cannot decrypt
- Requires solving Discrete Logarithm Problem (computationally infeasible)

### When to use:
- Demonstrating how DHKE works correctly
- Showing secure key exchange process
- Baseline for comparison with attacks

---

## 2. 🔴 ACTIVE MITM ATTACK (Always Succeeds)
**Script:** `dhke_mitm.py`

### Scenario:
- Eve positions herself between Alice and Bob **BEFORE** key exchange
- Eve intercepts and modifies key exchange in real-time
- Eve impersonates both parties

### Attack Method:
```
1. Alice generates A, sends to "Bob" (actually Eve)
2. Eve intercepts A, generates own E1
3. Eve sends E1 to real Bob (pretending to be Alice)
4. Bob generates B, sends to "Alice" (actually Eve)
5. Eve intercepts B, generates own E2
6. Eve sends E2 to real Alice (pretending to be Bob)

Result:
- Alice has secret with Eve (not Bob)
- Bob has secret with Eve (not Alice)
- Eve can decrypt/modify everything
```

### Key Points:
- ❌ **Works regardless of parameter size** (23-bit or 2048-bit - doesn't matter!)
- ❌ **No cryptography is broken** (Eve doesn't solve DLP)
- ❌ **Pure impersonation attack** (replaces keys, not cracks them)
- ⚠️ **Undetectable without authentication**

### Defense:
- Digital signatures (TLS certificates)
- Pre-shared keys
- Out-of-band verification (phone call, QR code)

### Professor Explanation:
> "This attack demonstrates why authentication is critical. Eve doesn't need to break any math - she simply tricks both parties into thinking they're talking to each other when they're actually talking to her. This is why HTTPS uses certificate authorities - to prove that the server's public key really belongs to the server."

---

## 3. 🟡 PASSIVE EAVESDROPPING + BRUTE FORCE (Only Weak Params)
**Script:** `dhke_passive_attack.py`

### Scenario:
- Alice and Bob have **already established** secure connection
- Eve joins **AFTER** key exchange is complete
- Eve can only observe traffic (cannot modify)

### Attack Method:
```
1. Eve captures public parameters (p, g) from network
2. Eve captures public keys (A, B) from key exchange
3. Eve captures encrypted messages from chat
4. Eve attempts brute force to find private key:
   - Try a = 1: compute g^1 mod p, compare to A
   - Try a = 2: compute g^2 mod p, compare to A
   - Try a = 3: compute g^3 mod p, compare to A
   - ... continue until g^a mod p = A
5. If found: compute shared secret, decrypt messages
6. If not found: attack fails
```

### Key Points:
- ✅ **Success depends on parameter size:**
  - 23-bit: Succeeds in seconds ⚠️
  - 512-bit: Would take millions of years ✓
  - 1024-bit: Would take 10^300+ years ✓
  - 2048-bit: Would take 10^600+ years ✓

- 🔬 **Requires solving DLP** (discrete logarithm problem)
- 📊 **Demonstrates importance of parameter strength**
- 🛡️ **Strong params provide complete protection**

### Defense:
- Use strong parameters (2048-bit minimum)
- Safe primes (RFC 3526)
- No additional authentication needed if params are strong

### Professor Explanation:
> "This attack shows the mathematical foundation of DHKE security. With 23-bit parameters, Eve can try all possible private keys in seconds. But with 2048-bit parameters, the search space is so large that even all computers on Earth working together couldn't finish in the lifetime of the universe. This is the discrete logarithm problem - easy to compute forward (g^a mod p), but computationally infeasible to reverse (find a from A)."

---

## Comparison Table

| Feature | Secure (No Attack) | MITM Attack | Passive Attack |
|---------|-------------------|-------------|----------------|
| **Script** | `dhke_secure.py` | `dhke_mitm.py` | `dhke_passive_attack.py` |
| **Eve's Position** | Not present | Between A & B (active) | Observing network (passive) |
| **When Eve Joins** | N/A | During key exchange | After key exchange |
| **Eve Can Modify?** | No | Yes (impersonates both) | No (only observes) |
| **23-bit Parameters** | ✅ Secure from Eve | ❌ Eve succeeds | ❌ Eve succeeds (brute force) |
| **2048-bit Parameters** | ✅ Secure from Eve | ❌ Eve succeeds | ✅ Eve fails (infeasible) |
| **Attack Type** | None | Social engineering / impersonation | Cryptanalysis / brute force |
| **Breaks Crypto?** | N/A | No (doesn't need to) | Yes (if params weak) |
| **Defense** | N/A | Authentication (certificates) | Strong parameters |
| **Real-World** | DHKE with auth + strong params | Prevented by TLS certs | Prevented by 2048+ bit |

---

## Demo Flow for Professor

### 1️⃣ Start with Secure Communication
```bash
Terminal 1: python dhke_secure.py --bob
Terminal 2: python dhke_secure.py --alice (choose 2048-bit)
```
**Say:** "This is how DHKE works correctly. Both compute same secret, messages are encrypted. An eavesdropper sees only ciphertext."

---

### 2️⃣ Show Passive Attack Failure (Strong Params)
```bash
# Keep Alice and Bob running from above
Terminal 3: python dhke_passive_attack.py
# Provide captured data, watch it fail
```
**Say:** "Eve captured all the public keys and encrypted messages, but with 2048-bit parameters, she cannot break it. It would take 10^600 years to brute force - longer than the age of the universe. This is the DLP hardness protecting us."

---

### 3️⃣ Show Passive Attack Success (Weak Params)
```bash
Terminal 1: python dhke_secure.py --bob
Terminal 2: python dhke_secure.py --alice (choose 23-bit)
Terminal 3: python dhke_passive_attack.py
# Watch Eve succeed in seconds
```
**Say:** "But if Alice and Bob used weak 23-bit parameters, Eve can brute force the private key in seconds. This demonstrates why parameter size matters."

---

### 4️⃣ Show MITM Attack Success (Any Params)
```bash
Terminal 1: python dhke_mitm.py --bob
Terminal 2: python dhke_mitm.py --eve
Terminal 3: python dhke_mitm.py --alice (choose 2048-bit)
# Watch Eve intercept and modify messages
```
**Say:** "Now here's the critical vulnerability - even with strong 2048-bit parameters, if there's no authentication, Eve can perform a man-in-the-middle attack during the key exchange. She doesn't break any crypto - she just impersonates both parties. This is why TLS uses certificates to authenticate public keys."

---

## Key Takeaways for Presentation

### 1. **Two Different Security Problems:**
- **Parameter Strength:** Protects against passive eavesdropping
- **Authentication:** Protects against active impersonation

### 2. **Both Are Necessary:**
- Strong params alone won't stop MITM (dhke_mitm.py proves this)
- Authentication alone won't help if params are weak (dhke_passive_attack.py proves this)
- Real protocols need BOTH (TLS = strong DHKE + certificates)

### 3. **Attack Difficulty:**
- Passive attack: Depends on parameter size (hard math problem)
- MITM attack: Easy regardless of params (no math needed, just trickery)

### 4. **Real-World Lessons:**
- TLS solves both: 2048+ bit DHKE + certificate authentication
- SSH: Strong params + trust-on-first-use
- Signal: Strong params + safety number verification

---

## Expected Questions & Answers

**Q: "If MITM works with strong params, why bother with large primes?"**
**A:** "Because in real deployments, we add authentication to prevent MITM. But we still need strong parameters to prevent passive attacks. Defense in depth requires both."

**Q: "Can Eve do MITM after the key exchange is complete?"**
**A:** "No. MITM only works if Eve intercepts the key exchange itself. Once Alice and Bob have their shared secret, Eve cannot decrypt without breaking DLP (which is infeasible for strong params)."

**Q: "What's more dangerous - MITM or passive eavesdropping?"**
**A:** "MITM is more dangerous because it works regardless of parameter size and is undetectable without authentication. Passive attacks are only dangerous with weak parameters, and strong parameters completely prevent them."

**Q: "How does TLS prevent MITM?"**
**A:** "TLS requires servers to present certificates signed by trusted Certificate Authorities. The client verifies the signature before trusting the server's public key. Eve cannot forge a valid certificate, so the MITM attack fails."

---

Made by Yashraj Pardeshi and Zhu Ruiqi

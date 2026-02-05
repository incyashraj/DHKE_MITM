# Quick Reference Guide

## 🚀 Quick Commands

### Test Everything First
```bash
python analysis.py
```
Should show: "All tests passed! Implementation is ready for presentation."

---

## 📺 Demo Commands

### 1. Secure DHKE Demo (Need 2 Terminals)

**Terminal 1 - Bob (Server):**
```bash
python dhke_secure.py --bob
```

**Terminal 2 - Alice (Client):**
```bash
python dhke_secure.py --alice
```

**Optional: Use faster 1024-bit keys:**
```bash
python dhke_secure.py --bob --bits 1024
python dhke_secure.py --alice --bits 1024
```

---

### 2. MITM Attack Demo (Need 3 Terminals)

**Start in this exact order:**

**Terminal 1 - Bob (Victim Server):**
```bash
python dhke_mitm.py --bob
```

**Terminal 2 - Eve (Attacker):**
```bash
python dhke_mitm.py --eve
```

**Terminal 3 - Alice (Victim Client):**
```bash
python dhke_mitm.py --alice
```

---

## 🧪 Individual Component Tests

### Test Core Utilities
```bash
python dh_params.py
```

### Run Python Interactive Test
```python
from dh_params import *

# Get parameters
p, g = get_dh_params(1024)
print(f"Prime: {p}")
print(f"Generator: {g}")

# Simulate exchange
alice_priv = generate_private_key(p)
alice_pub = compute_public_key(g, alice_priv, p)
bob_priv = generate_private_key(p)
bob_pub = compute_public_key(g, bob_priv, p)

# Compute secrets
alice_secret = compute_shared_secret(bob_pub, alice_priv, p)
bob_secret = compute_shared_secret(alice_pub, bob_priv, p)

print(f"Secrets match: {alice_secret == bob_secret}")
```

---

## 🐛 Troubleshooting

### "Connection Refused" Error
**Problem**: Client started before server  
**Solution**: Always start Bob/Eve (servers) before Alice (client)

### "Address Already in Use" Error
**Problem**: Previous process still using port  
**Solution**: 
```bash
# Find and kill process on port 5000
lsof -ti:5000 | xargs kill -9
# Or wait 30 seconds and try again
```

### Import Errors
**Problem**: Running from wrong directory  
**Solution**: 
```bash
cd "/Users/yashrajpardeshi/MSBT/Intro to Cryptography/Project"
```

### Tests Failing
**Problem**: Python version or missing files  
**Solution**: 
```bash
# Check Python version (need 3.7+)
python --version

# Verify all files present
ls -l *.py
```

---

## 📊 Expected Outputs

### Secure Demo Success Indicators:
- ✓ "Connected to Bob!"
- ✓ "Shared secret computed" (same value for both)
- ✓ "SUCCESS! Alice and Bob established secure communication!"

### MITM Demo Success Indicators:
- ✓ "Alice connected from..." (on Eve)
- ✓ "ATTACK SUCCESSFUL! Eve has established two separate channels"
- ✓ Different shared secrets for Alice and Bob
- ✓ "INTERCEPTED Alice's message"
- ✓ "MODIFIED message"

### Analysis Success Indicators:
- ✓ All 12 tests pass
- ✓ "Secrets match" for both 1024 and 2048-bit
- ✓ "Successfully cracked!" for weak parameters
- ✓ "All tests passed! Implementation is ready for presentation."

---

## 🎯 Demo Flow for Presentation

### Recommended Order:

1. **Start with Analysis** (builds confidence)
   ```bash
   python analysis.py
   ```
   - Shows everything works
   - Demonstrates weak parameter attack
   - Shows performance metrics

2. **Secure Demo** (show it working)
   ```bash
   # Terminal 1
   python dhke_secure.py --bob
   
   # Terminal 2
   python dhke_secure.py --alice
   ```
   - Highlight matching secrets
   - Show encrypted message works

3. **MITM Demo** (show the vulnerability)
   ```bash
   # Terminal 1
   python dhke_mitm.py --bob
   
   # Terminal 2
   python dhke_mitm.py --eve
   
   # Terminal 3
   python dhke_mitm.py --alice
   ```
   - Point out different secrets
   - Highlight message modification
   - Emphasize undetectability

---

## 📱 One-Line Quick Tests

```bash
# Full test suite
python analysis.py

# Quick utility test
python dh_params.py

# Check all files exist
ls -l *.py *.md

# Count lines of code
wc -l *.py

# Search for specific function
grep -n "def compute_shared_secret" *.py
```

---

## 🎓 Key Talking Points During Demo

### During Secure Demo:
1. "Alice generates random private key - never transmitted"
2. "Public keys can be intercepted - doesn't matter!"
3. "Both compute identical shared secret - this is the magic!"
4. "Message encrypted end-to-end"

### During MITM Demo:
1. "Alice thinks she's connecting to Bob - actually Eve"
2. "Eve generates TWO separate key pairs"
3. "Look: Alice and Bob have DIFFERENT secrets!"
4. "Eve decrypts, modifies, re-encrypts - undetected!"

### During Analysis:
1. "Weak parameters cracked in microseconds"
2. "2048-bit would take billions of years"
3. "This confirms our MITM attack works"
4. "All tests pass - implementation correct"

---

## 📦 Project Files Overview

```
dh_params.py          - Core crypto utilities (400+ lines)
dhke_secure.py        - Secure demo (300+ lines)
dhke_mitm.py          - MITM attack (400+ lines)
analysis.py           - Test suite (500+ lines)
README.md             - Full documentation
PRESENTATION_NOTES.md - Speaking guide
DIAGRAMS.md           - Visual diagrams
quickstart.sh         - Interactive menu
```

**Total**: ~1600+ lines of well-commented Python code

---

## 🔑 Key Code Snippets to Highlight

### The Core DHKE Computation:
```python
# Alice computes
alice_shared = pow(bob_public, alice_private, p)  # B^a mod p

# Bob computes  
bob_shared = pow(alice_public, bob_private, p)    # A^b mod p

# They match!
assert alice_shared == bob_shared  # g^(ab) mod p
```

### The MITM Attack:
```python
# Eve intercepts and creates separate secrets
eve_secret_alice = pow(alice_public, eve_private1, p)
eve_secret_bob = pow(bob_public, eve_private2, p)

# Different secrets!
assert eve_secret_alice != eve_secret_bob

# Eve can decrypt both sides
alice_msg = decrypt(encrypted_from_alice, eve_secret_alice)
modified = "Modified message!"
send_to_bob(encrypt(modified, eve_secret_bob))
```

---

## ⏱️ Timing Guide

- Full Analysis: ~5-10 seconds
- Secure Demo: ~1-2 seconds per run
- MITM Demo: ~2-3 seconds per run
- Weak Parameter Attack: <1 millisecond

**Total demo time**: < 1 minute for all demos

---

## 🎬 Pre-Presentation Checklist

- [ ] Run `python analysis.py` - verify all pass
- [ ] Test secure demo once
- [ ] Test MITM demo once
- [ ] Close all unnecessary terminals
- [ ] Increase terminal font size
- [ ] Have README open in browser
- [ ] Have this quick reference handy
- [ ] Clear terminal histories (for clean demos)
- [ ] Test network/localhost connectivity

---

**Ready to impress! Good luck! 🚀**

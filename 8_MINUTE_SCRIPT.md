# ⚡ 8-MINUTE PRESENTATION SCRIPT
## DHKE with MITM Attack Demo

**Total Time: 8 minutes (6 min present + 2 min Q&A)**

---

## 🎯 EXACT TIMING BREAKDOWN

| Section | Person | Time | What to Say |
|---------|--------|------|-------------|
| Intro | Person 1 | 30s | Quick hook + project overview |
| DHKE Explanation | Person 1 | 45s | Protocol steps + why secure |
| Secure Demo | Person 1 | 1m | Show working exchange |
| **SWITCH** | - | 5s | Hand off to Person 2 |
| MITM Demo | Person 2 | 2m | Show attack working |
| Analysis | Person 2 | 45s | Test results + stats |
| Conclusion | Person 2 | 30s | Key takeaway |
| **Q&A** | Both | 2m | Answer questions |

---

## 📝 PERSON 1 SCRIPT (3 minutes)

### [0:00-0:30] Introduction (30 seconds)

**SAY EXACTLY**:

> "Good [morning/afternoon]. Today we're presenting Diffie-Hellman Key Exchange - the protocol that powers HTTPS, VPNs, and secure messaging. But there's a critical vulnerability without authentication.
>
> We've implemented DHKE from scratch in Python - about 1600 lines of code - and we'll demonstrate both how it works securely and how it fails with a Man-in-the-Middle attack. All code is tested with 12 unit tests."

**SHOW**: Title slide or terminal ready

---

### [0:30-1:15] DHKE Protocol Explanation (45 seconds)

**SAY EXACTLY**:

> "The protocol works like this:
> 
> 1. Alice and Bob agree on public parameters - a large prime p and generator g
> 2. Each generates a secret private key - Alice picks 'a', Bob picks 'b'
> 3. Each computes a public key - Alice: g to the power a mod p, Bob: g to the power b mod p
> 4. They exchange these public keys over the network - anyone can see them
> 5. Using the other's public key and their own private key, both compute the same shared secret: g to the power ab mod p
>
> This is secure because finding the private key from a public key requires solving the discrete logarithm problem - with a 2048-bit prime, this would take billions of years even with supercomputers."

**SHOW**: Nothing - just explain clearly

---

### [1:15-2:15] Secure Demo (1 minute)

**SAY EXACTLY**:

> "Let me show this working. I'm running Bob - the server - waiting for Alice to connect."

**DO**: Start `python dhke_secure.py --bob --bits 1024` (Terminal 1)

> "Now Alice connects..."

**DO**: In new terminal, run `python dhke_secure.py --alice --bits 1024`

> "Watch the output:
> - Both generate private keys - never transmitted over network
> - Both compute public keys - these are exchanged
> - **And look here** - both compute the SAME shared secret"

**POINT**: Show matching secret values on both screens

> "Alice encrypts a message, Bob decrypts it successfully. The exchange works perfectly - both have the same encryption key, eavesdroppers see only public values."

---

### [2:15-2:20] Transition (5 seconds)

**SAY EXACTLY**:

> "[Person 2 name] will now show what happens when there's no authentication."

**DO**: Switch presenters

---

## 📝 PERSON 2 SCRIPT (3 minutes)

### [2:20-4:20] MITM Attack Demo (2 minutes)

**SAY EXACTLY**:

> "The problem: How does Alice verify that public key actually came from Bob? Without authentication, an attacker can intercept.
>
> This is Eve - a Man-in-the-Middle attacker. I'm setting up three parties now."

**DO**: 
- Terminal 1: `python dhke_mitm.py --bob`
- Terminal 2: `python dhke_mitm.py --eve`

> "Bob is running - the real server. Eve is running - she's positioned between Alice and Bob, impersonating both. Now Alice connects..."

**DO**: Terminal 3: `python dhke_mitm.py --alice`

> "Watch what happens:
> 
> - Alice thinks she's connecting to Bob, but connects to Eve
> - Eve intercepts Alice's public key
> - Eve generates her OWN key pair just for Alice
> - Eve separately connects to real Bob with a DIFFERENT key pair
> - **Look at the secrets** - Alice and Bob have DIFFERENT shared secrets!"

**POINT**: Show the different secret values

> "Now watch the message flow:
> - Alice sends: 'Meet at the secret location at midnight'
> - Eve intercepts and decrypts this with her Alice-key
> - Eve modifies it to: 'Meet at the usual place at noon'  
> - Eve re-encrypts with her Bob-key and forwards it
> - Bob receives: 'Meet at noon' - thinks it's securely from Alice
>
> Neither Alice nor Bob can detect this! The encryption works perfectly - they just established secrets with the wrong party."

---

### [4:20-5:05] Analysis Results (45 seconds)

**SAY EXACTLY**:

> "We ran comprehensive tests on this implementation:
>
> **Testing** - We wrote 12 automated tests covering protocol correctness, security, and performance. All 12 pass.
>
> **Security Analysis** - With weak parameters like a 23-bit prime, we can brute-force crack the private key in under a millisecond. But with proper 2048-bit parameters, it would take billions of years.
>
> **Performance** - The full key exchange with 2048-bit keys takes about 8 milliseconds - fast enough for real-time use while maintaining strong security.
>
> **MITM Confirmation** - Our tests verify the attack works: Alice and Bob compute different secrets, and Eve can decrypt both channels."

**SHOW**: Screenshot of analysis.py output (pre-run)

---

### [5:05-5:35] Conclusion (30 seconds)

**SAY EXACTLY**:

> "So what did we build and learn?
>
> We implemented the complete Diffie-Hellman protocol from mathematical first principles - using standardized RFC parameters and secure random number generation. About 1600 lines of Python code.
>
> The key takeaway: DHKE brilliantly solves the key exchange problem using the hardness of discrete logarithms, but it REQUIRES authentication to prevent Man-in-the-Middle attacks. That's why real-world protocols like TLS use digital certificates - the server proves its identity before the key exchange happens.
>
> Questions?"

---

## ❓ Q&A PREPARATION (2 minutes)

### Expected Questions & Answers:

**Q: "Why not use the largest possible key size?"**

**A**: "It's a trade-off. 1024-bit is fast but deprecated. 2048-bit is the current standard - secure against known attacks and fast enough for real-time use, about 8ms. 4096-bit is more secure but 8 times slower. Future quantum threats may require moving to post-quantum algorithms entirely rather than just larger keys."

---

**Q: "How do real systems prevent this MITM attack?"**

**A**: "Authentication! TLS uses digital certificates - the server's public key is signed by a trusted Certificate Authority. The client verifies this signature before doing DHKE. SSH uses trust-on-first-use and key fingerprints. VPNs use pre-shared keys or certificates. Signal uses out-of-band verification with safety numbers. The key is verifying identity BEFORE exchanging keys."

---

**Q: "What about quantum computers?"**

**A**: "You're right - Shor's algorithm can solve discrete logarithm in polynomial time on quantum computers, breaking DHKE. That's why NIST is standardizing post-quantum algorithms now. Leading candidates use lattice-based cryptography or other hard problems that even quantum computers can't efficiently solve. The transition is already beginning."

---

**Q: "Is this code production-ready?"**

**A**: "No, this is educational. Production systems should use established libraries like OpenSSL or the Python cryptography library. Those include additional protections: timing attack resistance, proper memory management, side-channel defenses, and years of security audits. Our implementation demonstrates the concepts but skips those production-level hardening measures."

---

## ⚙️ TECHNICAL SETUP (Do 10 minutes before presenting)

### 1. Run Full Test (Screenshot This)
```bash
python analysis.py
```
Save output to show during presentation.

### 2. Open Terminals (Don't run yet, just prepare)

**Terminal 1** - Secure Bob:
```bash
cd "/Users/yashrajpardeshi/MSBT/Intro to Cryptography/Project"
# Ready to run: python dhke_secure.py --bob --bits 1024
```

**Terminal 2** - MITM Bob:
```bash
cd "/Users/yashrajpardeshi/MSBT/Intro to Cryptography/Project"
# Ready to run: python dhke_mitm.py --bob
```

**Terminal 3** - MITM Eve:
```bash
cd "/Users/yashrajpardeshi/MSBT/Intro to Cryptography/Project"
# Ready to run: python dhke_mitm.py --eve
```

**Terminal 4** - For Alice (will open during demo)

### 3. Setup Checklist
- [ ] All terminals open and in project directory
- [ ] Font size MAXIMIZED
- [ ] All other apps closed
- [ ] This script printed or on second screen
- [ ] Tested each demo runs in <2 seconds
- [ ] Network/localhost working
- [ ] Backup: screenshots of successful runs

---

## 🎯 KEY SUCCESS FACTORS

1. **SPEAK CLEARLY** - Project voice, don't rush words
2. **USE TIME WISELY** - Stick to script, don't ad-lib
3. **POINT TO SCREEN** - Show the matching/different secrets
4. **PRACTICE TRANSITIONS** - Smooth handoff between people
5. **HAVE BACKUP** - Screenshots if live demo fails
6. **CONFIDENCE** - You built this, you know it works!

---

## ⏰ TIMING CHECKPOINTS

- **At 1:00**: Should be starting secure demo
- **At 2:00**: Should be wrapping secure demo
- **At 2:20**: Should be starting MITM demo
- **At 4:20**: Should be starting analysis
- **At 5:35**: Should be saying "Questions?"
- **At 8:00**: Time's up, wrap any remaining question

---

## 🚨 IF DEMO FAILS (Backup Plan)

1. **Show screenshots** of successful runs
2. **Walk through code** instead of running
3. **Explain expected output** from memory
4. **Move to analysis results** (pre-run screenshot)
5. **Still hit time targets** - don't spend extra time debugging

---

## ✅ FINAL PRE-PRESENTATION CHECKLIST

30 minutes before:
- [ ] Practice full script once (should be ~6 min)
- [ ] Test all demos work
- [ ] Take screenshots of successful runs
- [ ] Prepare backup plan

10 minutes before:
- [ ] Set up all terminals
- [ ] Maximize font sizes
- [ ] Close other applications
- [ ] Do a quick timing check

Right before:
- [ ] Deep breath
- [ ] Smile
- [ ] Remember: You got this!

---

**Good luck! This is a solid project and you're well-prepared. Stick to the timing, speak clearly, and let the demos speak for themselves. 🚀**

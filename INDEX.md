# 📚 Project Index - DHKE Implementation

**Quick Navigation Guide for All Project Files**

---

## 🔴 START HERE

**First Time? Read These First:**
1. [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Complete project overview
2. [README.md](README.md) - Full documentation
3. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Command cheat sheet

**Ready to Run?**
```bash
python analysis.py
```

---

## 📂 File Guide

### 🐍 Python Implementation Files

#### [dh_params.py](dh_params.py) - Core Cryptographic Utilities
**What it does**: Foundation for all crypto operations  
**Key functions**:
- `get_dh_params()` - Get safe prime parameters
- `generate_private_key()` - Generate random private keys
- `compute_public_key()` - Calculate public values
- `compute_shared_secret()` - Derive shared secret
- `derive_key()` - Hash secret to encryption key
- `simple_encrypt/decrypt()` - Demo encryption
- `brute_force_discrete_log()` - Attack weak parameters

**When to use**: Imported by all other scripts  
**Run standalone**: `python dh_params.py` (runs self-test)  
**Size**: 8.7 KB, ~250 lines

---

#### [dhke_secure.py](dhke_secure.py) - Secure Key Exchange Demo
**What it does**: Demonstrates successful secure DHKE  
**Key components**:
- `Alice` class - Client implementation
- `Bob` class - Server implementation
- Socket-based network simulation
- Encrypted message exchange

**When to use**: Show DHKE working correctly  
**How to run**:
```bash
# Terminal 1
python dhke_secure.py --bob

# Terminal 2
python dhke_secure.py --alice
```
**Options**: `--bits 1024` or `--bits 2048`  
**Size**: 12 KB, ~300 lines  
**Demo time**: ~2 seconds

---

#### [dhke_mitm.py](dhke_mitm.py) - MITM Attack Simulation
**What it does**: Shows vulnerability without authentication  
**Key components**:
- `AliceMITM` class - Victim client
- `BobMITM` class - Victim server
- `Eve` class - Attacker/proxy
- Message interception and modification

**When to use**: Demonstrate security vulnerability  
**How to run**:
```bash
# Terminal 1
python dhke_mitm.py --bob

# Terminal 2
python dhke_mitm.py --eve

# Terminal 3
python dhke_mitm.py --alice
```
**Size**: 18 KB, ~400 lines  
**Demo time**: ~3 seconds

---

#### [analysis.py](analysis.py) - Comprehensive Test Suite
**What it does**: Tests everything and provides analysis  
**Key tests**:
- Parameter validation
- Shared secret agreement
- Encryption correctness
- MITM vulnerability confirmation
- Weak parameter attack
- Randomness quality
- Performance benchmarks
- Integration tests

**When to use**: Verify implementation, get insights  
**How to run**: `python analysis.py`  
**Size**: 17 KB, ~500 lines  
**Run time**: ~5-10 seconds  
**Expected result**: All 12 tests pass ✓

---

### 📖 Documentation Files

#### [README.md](README.md) - Complete Project Documentation
**What it covers**:
- Project overview
- Cryptographic background (DLP, DHKE)
- Installation and setup
- Usage guides for all demos
- Technical details
- Performance benchmarks
- Educational insights
- Troubleshooting
- Real-world applications
- References

**When to read**: For deep understanding  
**Size**: 13 KB, ~400 lines  
**Best for**: Learning crypto concepts, understanding implementation

---

#### [PRESENTATION_NOTES.md](PRESENTATION_NOTES.md) - Speaking Guide
**What it covers**:
- 15-20 minute presentation structure
- Section-by-section talking points
- Demo execution instructions
- Key points to highlight
- Anticipated questions with answers
- Time management tips
- Backup plans
- Speaking tips

**When to use**: Before and during presentation  
**Size**: 9.6 KB, ~350 lines  
**Best for**: Presentation preparation

---

#### [DIAGRAMS.md](DIAGRAMS.md) - Visual Explanations
**What it covers**:
- Protocol flow diagrams (secure & MITM)
- Security comparison visualizations
- DLP problem illustration
- Performance vs security trade-offs
- Component architecture
- Attack success metrics
- Test coverage map

**When to use**: Visual learning, presentation slides  
**Size**: 17 KB, ~300 lines  
**Best for**: Understanding flows, explaining to others

---

#### [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Command Cheat Sheet
**What it covers**:
- Quick command reference
- Troubleshooting solutions
- Expected outputs
- Demo flow recommendations
- One-line tests
- Key code snippets
- Pre-presentation checklist

**When to use**: During demos, quick lookup  
**Size**: 6.4 KB, ~200 lines  
**Best for**: Quick reference during presentation

---

#### [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Project Overview
**What it covers**:
- Complete deliverables list
- Technical specifications
- Learning objectives achieved
- Project statistics
- Demonstration readiness
- Highlights and achievements

**When to use**: Project overview, status check  
**Size**: 11 KB, ~350 lines  
**Best for**: Understanding project scope and completion

---

### 🔧 Utility Files

#### [quickstart.sh](quickstart.sh) - Interactive Menu
**What it does**: Interactive command menu  
**Options**:
1. Run comprehensive tests
2. Secure DHKE demo instructions
3. MITM attack demo instructions
4. Quick utility test
5. Show project structure

**How to run**: `./quickstart.sh`  
**Size**: 3.0 KB  
**Best for**: Beginners, quick navigation

---

## 🎯 Recommended Reading Order

### For First-Time Users:
1. **PROJECT_SUMMARY.md** - Get the big picture
2. **QUICK_REFERENCE.md** - Learn the commands
3. **Run `python analysis.py`** - Verify everything works
4. **README.md** - Deep dive into concepts

### For Presentation Prep:
1. **PRESENTATION_NOTES.md** - Read thoroughly
2. **DIAGRAMS.md** - Review visual aids
3. **QUICK_REFERENCE.md** - Keep handy during demo
4. **Practice all demos** - Run multiple times

### For Understanding Crypto:
1. **README.md** - Cryptographic background section
2. **DIAGRAMS.md** - Visual protocol flows
3. **dh_params.py** - Read comments in code
4. **analysis.py** - See tests and validations

### For Code Review:
1. **dh_params.py** - Core utilities
2. **dhke_secure.py** - Clean implementation
3. **dhke_mitm.py** - Attack methodology
4. **analysis.py** - Testing approaches

---

## 🔍 Quick File Finder

**Need to find...**

✅ **Commands**: QUICK_REFERENCE.md  
✅ **Crypto theory**: README.md  
✅ **Visual diagrams**: DIAGRAMS.md  
✅ **Speaking points**: PRESENTATION_NOTES.md  
✅ **Project stats**: PROJECT_SUMMARY.md  
✅ **Test results**: Run `python analysis.py`  
✅ **Code examples**: All .py files  
✅ **Troubleshooting**: README.md or QUICK_REFERENCE.md  

---

## 📊 File Statistics

| File | Type | Size | Lines | Purpose |
|------|------|------|-------|---------|
| dh_params.py | Python | 8.7 KB | ~250 | Core crypto |
| dhke_secure.py | Python | 12 KB | ~300 | Secure demo |
| dhke_mitm.py | Python | 18 KB | ~400 | Attack demo |
| analysis.py | Python | 17 KB | ~500 | Test suite |
| README.md | Docs | 13 KB | ~400 | Full docs |
| PRESENTATION_NOTES.md | Docs | 9.6 KB | ~350 | Speaking guide |
| DIAGRAMS.md | Docs | 17 KB | ~300 | Visual aids |
| QUICK_REFERENCE.md | Docs | 6.4 KB | ~200 | Quick help |
| PROJECT_SUMMARY.md | Docs | 11 KB | ~350 | Overview |
| quickstart.sh | Script | 3.0 KB | ~80 | Menu |
| **TOTAL** | - | **~115 KB** | **~3,130** | Complete |

---

## 🎓 Learning Path

### Beginner (Just Getting Started)
1. Read PROJECT_SUMMARY.md (5 min)
2. Run `python analysis.py` (1 min)
3. Review QUICK_REFERENCE.md (5 min)
4. Try secure demo (2 min)

**Time**: ~15 minutes to get started

### Intermediate (Understanding Implementation)
1. Read README.md fully (20 min)
2. Study DIAGRAMS.md (15 min)
3. Review dh_params.py code (15 min)
4. Run all demos (5 min)
5. Read dhke_secure.py (15 min)

**Time**: ~70 minutes for deep understanding

### Advanced (Presentation Ready)
1. Complete Intermediate path
2. Study PRESENTATION_NOTES.md (20 min)
3. Review dhke_mitm.py (20 min)
4. Practice demos 3x (10 min)
5. Prepare Q&A (20 min)

**Time**: ~2.5 hours for full preparation

---

## 🚀 Common Tasks

### "I want to test everything"
```bash
python analysis.py
```

### "I want to see it work"
```bash
# Terminal 1: python dhke_secure.py --bob
# Terminal 2: python dhke_secure.py --alice
```

### "I want to see the attack"
```bash
# Terminal 1: python dhke_mitm.py --bob
# Terminal 2: python dhke_mitm.py --eve
# Terminal 3: python dhke_mitm.py --alice
```

### "I want to understand the math"
Read: README.md → "Cryptographic Background" section

### "I want to prepare presentation"
Read: PRESENTATION_NOTES.md + DIAGRAMS.md

### "I need quick help"
Check: QUICK_REFERENCE.md

---

## 💡 Pro Tips

1. **Always start with**: `python analysis.py` to verify everything works
2. **For demos**: Start servers (Bob/Eve) before clients (Alice)
3. **For learning**: Read code comments - they explain the crypto
4. **For presentation**: Practice demos multiple times
5. **For debugging**: Check QUICK_REFERENCE.md troubleshooting section

---

## 📞 Emergency Quick Guide

**Something not working?**
1. Check QUICK_REFERENCE.md → Troubleshooting
2. Verify Python version: `python --version` (need 3.7+)
3. Verify in correct directory: `pwd`
4. Re-run tests: `python analysis.py`

**Presentation starting soon?**
1. Open PRESENTATION_NOTES.md
2. Open QUICK_REFERENCE.md  
3. Run `python analysis.py` once
4. Practice one run of each demo
5. Deep breath - you've got this! 💪

---

## ✅ Final Checklist

Before presentation:
- [ ] Read PRESENTATION_NOTES.md
- [ ] Run `python analysis.py` - all tests pass
- [ ] Practice secure demo
- [ ] Practice MITM demo
- [ ] Review QUICK_REFERENCE.md
- [ ] Have DIAGRAMS.md ready
- [ ] Increase terminal font size
- [ ] Clear terminal histories

---

**Everything you need is in these files. Good luck! 🎓🚀**

---

_Last updated: February 2026_  
_Total project size: ~115 KB, ~3,130 lines_  
_Status: Complete and ready ✅_

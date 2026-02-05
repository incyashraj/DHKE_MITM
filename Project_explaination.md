# Complete Technical Deep Dive: DHKE with MITM Attack
## Code-Level Analysis with Flow Diagrams

---

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Communication Channel Setup](#communication-channel-setup)
3. [Key Generation Mathematics](#key-generation-mathematics)
4. [Secure Two-Party Exchange (Alice-Bob)](#secure-two-party-exchange)
5. [MITM Attack Mechanics (Alice-Eve-Bob)](#mitm-attack-mechanics)
6. [Attack Difficulty Analysis](#attack-difficulty-analysis)
7. [Code Mapping - Line by Line](#code-mapping)
8. [Professor Q&A Preparation](#professor-qa-preparation)

---

## Architecture Overview

### File Structure and Responsibilities

```
Project/
│
├── dh_params.py              # Cryptographic primitives
│   ├── get_dh_params()       → Returns (p, g) for given bit size
│   ├── generate_private_key() → Secure random number generation
│   ├── compute_public_key()  → Modular exponentiation A = g^a mod p
│   ├── compute_shared_secret() → Secret computation s = B^a mod p
│   ├── derive_key()          → SHA-256 key derivation
│   ├── simple_encrypt()      → XOR-based encryption (demo)
│   ├── simple_decrypt()      → XOR-based decryption (demo)
│   └── brute_force_discrete_log() → Educational DLP attack
│
├── dhke_secure.py            # Two-party secure exchange
│   ├── Alice class           → Initiator, sends first message
│   └── Bob class             → Responder, receives and replies
│
├── dhke_mitm.py              # Three-party attack
│   ├── Alice class           → Victim #1 (thinks talking to Bob)
│   ├── Bob class             → Victim #2 (thinks talking to Alice)
│   └── Eve class             → Attacker (intercepts everything)
│
└── analysis.py               # Testing and validation
    └── Comprehensive test suite
```

---

## Communication Channel Setup

### Network Architecture

#### Two-Party (Secure) Communication:
```
┌─────────┐                                    ┌─────────┐
│  Alice  │ ─────── TCP Socket ────────────── │   Bob   │
│ (Client)│         localhost:5000            │ (Server)│
└─────────┘                                    └─────────┘
     │                                              │
     │ 1. Connect()                                 │
     │ ───────────────────────────────────────────→ │
     │                                              │
     │ 2. Send parameters (p, g)                    │
     │ ───────────────────────────────────────────→ │
     │                                              │
     │ 3. Send public key A                         │
     │ ───────────────────────────────────────────→ │
     │                                              │
     │ 4. Receive public key B                      │
     │ ←─────────────────────────────────────────── │
     │                                              │
     │ Both compute same secret s = g^(ab) mod p    │
     │                                              │
     │ 5. Send encrypted message                    │
     │ ───────────────────────────────────────────→ │
     │                                              │
     │ 6. Receive encrypted reply                   │
     │ ←─────────────────────────────────────────── │
```

#### Three-Party (MITM Attack) Communication:
```
┌─────────┐            ┌─────────┐            ┌─────────┐
│  Alice  │            │   Eve   │            │   Bob   │
│ (Client)│            │(Attacker)│            │ (Server)│
└─────────┘            └─────────┘            └─────────┘
     │                      │                      │
     │ Port 5000            │            Port 5001 │
     │                      │                      │
     │ Thinks: Bob          │         Thinks: Alice│
     │                      │                      │
     │ 1. Connect()         │                      │
     │ ────────────────────→│                      │
     │                      │ 2. Connect()         │
     │                      │─────────────────────→│
     │                      │                      │
     │ 3. Send (p,g,A)      │                      │
     │ ────────────────────→│                      │
     │                      │ 4. Send (p,g,E1)     │
     │                      │  (E1 is Eve's key!)  │
     │                      │─────────────────────→│
     │                      │                      │
     │                      │ 5. Receive B         │
     │                      │←─────────────────────│
     │ 6. Receive E2        │                      │
     │   (E2 is Eve's key!) │                      │
     │←─────────────────────│                      │
     │                      │                      │
     │ Computes: s1=E2^a    │  Computes: s2=E1^b   │
     │                      │                      │
     │ Eve computes TWO secrets:                   │
     │ - s_alice = A^e2 mod p  (same as Alice's s1)│
     │ - s_bob = B^e1 mod p    (same as Bob's s2)  │
     │                      │                      │
     │ 7. Send msg (enc w/ s1)                     │
     │ ────────────────────→│                      │
     │                      │ Decrypt with s_alice │
     │                      │ Modify message       │
     │                      │ Encrypt with s_bob   │
     │                      │ 8. Forward (enc w/ s2)│
     │                      │─────────────────────→│
     │                      │                      │
     │     Alice & Bob have DIFFERENT secrets!     │
```

### Code: Socket Setup (Bob's Server)

**Location: `dhke_secure.py` - Bob class, `setup_server()` method**

```python
def setup_server(self):
    """Bob acts as server, waits for Alice to connect"""
    print("\n" + "="*60)
    print("Bob: Waiting for Connection")
    print("="*60)
    print(f"Listening on port {self.port}...")
    
    # Create TCP socket
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # SO_REUSEADDR allows restarting server quickly without "address in use" error
    self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Bind to localhost on specified port (default 5000)
    self.sock.bind(('localhost', self.port))
    
    # Listen for incoming connections (max 1 in queue)
    self.sock.listen(1)
    
    # Accept connection - BLOCKS until Alice connects
    self.conn, addr = self.sock.accept()
    print(f"Alice connected from {addr}")
```

**What This Does:**
1. Creates TCP socket using IPv4 (AF_INET) and stream protocol (SOCK_STREAM)
2. Sets SO_REUSEADDR to avoid port conflicts on restart
3. Binds socket to localhost:5000 (insecure channel simulation)
4. Listens for connections (backlog=1 sufficient for demo)
5. Blocks on `accept()` until Alice connects
6. Returns connection object for subsequent communication

### Code: Socket Setup (Alice's Client)

**Location: `dhke_secure.py` - Alice class, `connect()` method**

```python
def connect(self):
    """Alice connects to Bob's server"""
    print(f"\nConnecting to Bob at localhost:{self.port}...")
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        # Connect to Bob's server
        self.sock.connect(('localhost', self.port))
        print("Connected.")
    except ConnectionRefusedError:
        print("ERROR: Cannot connect! Is Bob running?")
        sys.exit(1)
```

**What This Does:**
1. Creates TCP socket (same parameters as Bob)
2. Attempts to connect to Bob's address (localhost:5000)
3. If Bob not running → ConnectionRefusedError → exits gracefully
4. On success → socket ready for data exchange

### Code: MITM Socket Setup (Eve's Dual Role)

**Location: `dhke_mitm.py` - Eve class, `run()` method**

```python
def run(self):
    # Setup fake Bob for Alice (Eve acts as SERVER to Alice)
    self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.server_sock.bind(('localhost', self.alice_port))  # Port 5000
    self.server_sock.listen(1)
    
    # Connect to real Bob (Eve acts as CLIENT to Bob)
    self.bob_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        self.bob_sock.connect(('localhost', self.bob_port))  # Port 5001
        print("  Connected to Bob")
    except ConnectionRefusedError:
        print("ERROR: Cannot connect to Bob!")
        sys.exit(1)
    
    # Wait for Alice (BLOCKS here until Alice connects)
    self.alice_conn, addr = self.server_sock.accept()
    print(f"  Alice connected! MITM active.")
```

**What This Does:**
1. **Server mode (for Alice):** Eve listens on port 5000, pretending to be Bob
2. **Client mode (to Bob):** Eve connects to real Bob on port 5001
3. **Result:** Eve is "man in the middle" - both think they're talking to each other
4. Alice → Eve (port 5000), Eve → Bob (port 5001)

**Critical Insight:** Eve controls BOTH connections, can intercept/modify everything!

---

## Key Generation Mathematics

### The Diffie-Hellman Protocol - Mathematical Foundation

#### Public Parameters (Shared by Everyone)
```
p: Large prime modulus (safe prime: p = 2q + 1, where q is also prime)
g: Generator (typically 2 or 5)

Example (23-bit weak for demo):
p = 23 (prime)
g = 5  (generator)
```

#### Private Keys (Secret, Never Transmitted)
```
Alice chooses: a ∈ [1, p-2]  (random)
Bob chooses:   b ∈ [1, p-2]  (random)
```

#### Public Keys (Transmitted Over Insecure Channel)
```
Alice computes: A = g^a mod p  →  sends to Bob
Bob computes:   B = g^b mod p  →  sends to Alice
```

#### Shared Secret (Both Compute Same Value)
```
Alice computes: s = B^a mod p = (g^b)^a mod p = g^(ba) mod p
Bob computes:   s = A^b mod p = (g^a)^b mod p = g^(ab) mod p

Since ab = ba (commutative), both get same secret!
```

### Code: Parameter Selection

**Location: `dh_params.py` - `get_dh_params()` function**

```python
def get_dh_params(bits):
    """
    Returns (p, g) for specified bit size
    Uses RFC 3526 standardized safe primes
    """
    if bits == 23:
        # Weak prime for educational DLP demonstration
        return 23, 5
    
    elif bits == 512:
        # RFC 3526 MODP Group 2 (512-bit)
        p = 0xFFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3DC2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB9ED529077096966D670C354E4ABC9804F1746C08CA237327FFFFFFFFFFFFFFFF
        return p, 2
    
    elif bits == 1024:
        # RFC 3526 MODP Group 2 (1024-bit)
        p = 0xFFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3DC2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB9ED529077096966D670C354E4ABC9804F1746C08CA237327FFFFFFFFFFFFFFFF
        return p, 2
    
    elif bits == 2048:
        # RFC 3526 MODP Group 14 (2048-bit) - RECOMMENDED
        p = 0xFFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3DC2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB9ED529077096966D670C354E4ABC9804F1746C08CA18FF77DF252446F162DBBEE208B0A5F4B77B5B4F6854DFE1A6F5C9A9CD3E4A3F6A0F5B7AB9C29FF8D6A3D7F5D5C6E4A7C5D6E3F4A5B6C7D8E9F0A1B2C3D4E5F60718293A4B5C6D7E8F90A1B2C3D4E5F607182930
        return p, 2
```

**What This Does:**
1. Returns standardized (p, g) pairs from RFC 3526
2. Safe primes ensure security properties (no small subgroups)
3. g=2 or g=5 are efficient generators
4. 23-bit exists purely for educational brute-force demo

**Why Safe Primes?**
```
Safe prime: p = 2q + 1, where q is also prime
Benefit: The multiplicative group Z_p* has order p-1 = 2q
         This prevents small subgroup attacks
         Ensures generator has large order
```

### Code: Private Key Generation

**Location: `dh_params.py` - `generate_private_key()` function**

```python
def generate_private_key(p, secure=True):
    """
    Generate random private key in range [1, p-2]
    
    Args:
        p: Prime modulus
        secure: If True, use cryptographically secure RNG
    
    Returns:
        Random integer in valid range
    """
    if secure:
        # Use secrets module (wraps os.urandom - OS entropy pool)
        # Cryptographically secure - unpredictable even if previous values known
        return secrets.randbelow(p - 2) + 1
    else:
        # INSECURE: Pseudo-random (deterministic with seed)
        # Never use in production! Only for demonstrating weakness.
        return random.randint(1, p - 2)
```

**What This Does:**
1. **Secure mode:** Uses `secrets.randbelow()` which wraps `os.urandom()`
   - Gets entropy from OS (hardware RNG, system events, etc.)
   - Unpredictable - no way to guess next value
   - Required for cryptographic security
   
2. **Insecure mode:** Uses `random.randint()`
   - Pseudo-random: deterministic if seed known
   - Demonstrates why secure RNG matters
   - Never use for real crypto!

3. **Range:** [1, p-2] because:
   - Must be positive: avoid 0 (g^0 = 1, trivial)
   - Must be < p-1: stay within group
   - Common practice: [1, p-2] is safe

### Code: Public Key Computation

**Location: `dh_params.py` - `compute_public_key()` function**

```python
def compute_public_key(g, private_key, p):
    """
    Compute public key: A = g^private_key mod p
    
    Uses Python's built-in pow(base, exp, mod) for efficiency
    This uses fast modular exponentiation (square-and-multiply)
    Time complexity: O(log private_key)
    
    Args:
        g: Generator
        private_key: Secret exponent (a or b)
        p: Prime modulus
    
    Returns:
        Public key (A or B)
    """
    return pow(g, private_key, p)
```

**What This Does:**
1. Computes modular exponentiation efficiently
2. **NOT** naive: `(g ** private_key) % p` (too slow, huge numbers)
3. **Uses:** Square-and-multiply algorithm (binary exponentiation)
4. **Example (g=5, a=3, p=23):**
   ```
   A = 5^3 mod 23
   Step 1: 5^1 mod 23 = 5
   Step 2: 5^2 mod 23 = 25 mod 23 = 2
   Step 3: 5^3 = 5^2 * 5 = 2 * 5 = 10 mod 23
   Result: A = 10
   ```

**Security Property:**
- Computing `A = g^a mod p` is FAST (O(log a))
- Computing `a` from `A` is HARD (discrete logarithm problem)
- This asymmetry is the foundation of security!

### Code: Shared Secret Computation

**Location: `dh_params.py` - `compute_shared_secret()` function**

```python
def compute_shared_secret(other_public_key, my_private_key, p):
    """
    Compute shared secret: s = other_public^my_private mod p
    
    Alice: s = B^a mod p = (g^b)^a mod p = g^(ab) mod p
    Bob:   s = A^b mod p = (g^a)^b mod p = g^(ab) mod p
    
    Both compute the same value due to commutativity: ab = ba
    
    Args:
        other_public_key: Received public key (B for Alice, A for Bob)
        my_private_key: Own private key (a for Alice, b for Bob)
        p: Prime modulus
    
    Returns:
        Shared secret (same for both parties)
    """
    return pow(other_public_key, my_private_key, p)
```

**What This Does:**
1. Same modular exponentiation as public key generation
2. **Key insight:** Uses OTHER party's public key
   - Alice raises Bob's B to her secret a
   - Bob raises Alice's A to his secret b
3. **Mathematical magic:** Both get same result!
   ```
   Alice: B^a = (g^b)^a = g^(ba) = g^(ab)
   Bob:   A^b = (g^a)^b = g^(ab)
   Same!
   ```

**Example with actual numbers (p=23, g=5, a=3, b=6):**
```
Alice's private: a = 3
Alice's public:  A = 5^3 mod 23 = 10

Bob's private:   b = 6
Bob's public:    B = 5^6 mod 23 = 8

Alice computes:  s = B^a mod p = 8^3 mod 23 = 512 mod 23 = 6
Bob computes:    s = A^b mod p = 10^6 mod 23 = 1000000 mod 23 = 6

Both get s = 6! ✓
```

### Code: Key Derivation

**Location: `dh_params.py` - `derive_key()` function**

```python
def derive_key(shared_secret):
    """
    Derive encryption key from shared secret using SHA-256
    
    Why hash?
    - Shared secret is a large integer (up to p-1)
    - We need fixed-size key for encryption (e.g., 256 bits for AES)
    - Hashing provides uniform distribution
    - SHA-256 is one-way: can't recover secret from key
    
    Args:
        shared_secret: Integer value (same for both parties)
    
    Returns:
        32-byte (256-bit) key suitable for encryption
    """
    # Convert integer to bytes
    secret_bytes = str(shared_secret).encode('utf-8')
    
    # Hash with SHA-256
    return hashlib.sha256(secret_bytes).digest()
```

**What This Does:**
1. Converts shared secret (integer) to bytes
2. Applies SHA-256 hash function
3. Returns 32-byte (256-bit) key

**Why Hash the Secret?**
- Direct use of `s` as key is problematic:
  - Variable length (depends on bit size)
  - Not uniformly distributed
  - May have weak bits
- SHA-256 provides:
  - Fixed 256-bit output
  - Uniform distribution
  - One-way property (security)
  - Deterministic (same s → same key)

---

## Secure Two-Party Exchange

### Complete Protocol Flow

```
SECURE DHKE PROTOCOL (Alice ↔ Bob)
=====================================

Phase 1: Parameter Agreement
─────────────────────────────
Alice: Selects parameters (p, g)
Alice → Bob: Send (p, g)
Bob:   Receives (p, g)

Phase 2: Key Generation (Local)
────────────────────────────────
Alice:
  1. a = random [1, p-2]
  2. A = g^a mod p

Bob:
  1. b = random [1, p-2]
  2. B = g^b mod p

Phase 3: Public Key Exchange
─────────────────────────────
Alice → Bob: Send A
Bob → Alice: Send B

Phase 4: Shared Secret Computation (Local)
───────────────────────────────────────────
Alice:
  1. Receives B
  2. s = B^a mod p

Bob:
  1. Receives A
  2. s = A^b mod p

Result: s_alice = s_bob = g^(ab) mod p ✓

Phase 5: Encrypted Communication
─────────────────────────────────
Both:
  key = SHA-256(s)

Alice → Bob:
  1. plaintext = "Hello Bob"
  2. ciphertext = encrypt(plaintext, key)
  3. Send ciphertext

Bob:
  1. Receives ciphertext
  2. plaintext = decrypt(ciphertext, key)
  3. Read message ✓
```

### Code Walkthrough: Alice's Side

**Location: `dhke_secure.py` - Alice class**

#### Step 1: Parameter Selection
```python
def select_parameters(self):
    print("\n" + "="*60)
    print("Alice: Select Security Parameters")
    print("="*60)
    print("1. 23-bit   (weak - demo only)")
    print("2. 512-bit  (weak - deprecated)")
    print("3. 1024-bit (moderate)")
    print("4. 2048-bit (strong - recommended)")
    
    choice = input("\nChoice (1-4): ").strip()
    
    # Map choice to bit size
    bits_map = {'1': 23, '2': 512, '3': 1024, '4': 2048}
    self.bits = bits_map.get(choice, 1024)
    
    # Get parameters from RFC 3526 or weak set
    self.p, self.g = get_dh_params(self.bits)
    
    print(f"\nUsing {self.bits}-bit parameters")
    print(f"Prime p: 0x{str(hex(self.p))[:5]}...")
    print(f"Generator g: {self.g}")
```

**Explanation:**
- User chooses security level (educational control)
- Maps choice to bit size
- Calls `get_dh_params()` to retrieve standardized (p, g)
- Displays chosen parameters (truncated for readability)

#### Step 2: Connect to Bob
```python
def connect(self):
    print(f"\nConnecting to Bob at localhost:{self.port}...")
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        self.sock.connect(('localhost', self.port))
        print("Connected.")
    except ConnectionRefusedError:
        print("ERROR: Cannot connect! Is Bob running?")
        sys.exit(1)
```

**Explanation:**
- Creates TCP socket
- Attempts connection to Bob's server (localhost:5000)
- Graceful error handling if Bob not running

#### Step 3: Send Parameters
```python
def send_parameters(self):
    print("Sending parameters to Bob...")
    
    # Package parameters as JSON
    params = {
        'p': str(self.p),  # Convert to string (JSON can't handle big ints directly)
        'g': str(self.g),
        'bits': str(self.bits)
    }
    
    # Serialize and send with newline delimiter
    data = json.dumps(params) + '\n'
    self.sock.send(data.encode())
```

**Explanation:**
- Converts parameters to JSON dictionary
- Converts large integers to strings (JSON limitation)
- Adds '\n' delimiter for message framing
- Encodes to bytes and sends over socket

**Message Format:**
```json
{"p": "23", "g": "5", "bits": "23"}\n
```

#### Step 4: Generate Keys
```python
def generate_keys(self):
    print("\nGenerating Alice's keys...")
    
    # Generate secure random private key
    self.private_key = generate_private_key(self.p)
    print(f"Private key (a): {self.private_key}")
    
    # Compute public key: A = g^a mod p
    print(f"\nComputing public key: A = g^a mod p")
    print(f"  g = {self.g}")
    print(f"  a = {self.private_key}")
    print(f"  p = {self.p}")
    
    self.public_key = compute_public_key(self.g, self.private_key, self.p)
    
    print(f"  A = {self.g}^{self.private_key} mod {self.p}")
    print(f"  A = {self.public_key}")
```

**Explanation:**
- Calls `generate_private_key()` for secure random `a`
- Shows all values (educational transparency)
- Computes `A = g^a mod p` using `compute_public_key()`
- Displays full computation for understanding

**Example Output:**
```
Generating Alice's keys...
Private key (a): 3

Computing public key: A = g^a mod p
  g = 5
  a = 3
  p = 23
  A = 5^3 mod 23
  A = 10
```

#### Step 5: Exchange Public Keys
```python
def exchange_keys(self):
    print("\nExchanging public keys...")
    
    # Send Alice's public key A to Bob
    message = {'public_key': str(self.public_key)}
    self.sock.send((json.dumps(message) + '\n').encode())
    
    # Receive Bob's public key B
    data = recv_msg(self.sock)  # Helper function: reads until '\n'
    if not data:
        print("ERROR: No response from Bob")
        sys.exit(1)
    
    self.bob_public_key = int(json.loads(data)['public_key'])
    print(f"Received Bob's public key: {hex(self.bob_public_key)[:40]}...")
```

**Explanation:**
- Sends Alice's public key `A` as JSON
- Uses `recv_msg()` helper to read complete message
- Parses Bob's public key `B` from JSON
- Stores for secret computation

**Message Exchange:**
```
Alice → Bob: {"public_key": "10"}\n
Bob → Alice: {"public_key": "8"}\n
```

#### Step 6: Compute Shared Secret
```python
def compute_secret(self):
    print("\nComputing shared secret...")
    print(f"Computing: s = B^a mod p")
    print(f"  B (Bob's public key) = {self.bob_public_key}")
    print(f"  a (Alice's private key) = {self.private_key}")
    print(f"  p = {self.p}")
    
    # Compute s = B^a mod p
    self.shared_secret = compute_shared_secret(
        self.bob_public_key,  # Bob's public key B
        self.private_key,     # Alice's private key a
        self.p                # Prime modulus
    )
    
    print(f"  s = {self.bob_public_key}^{self.private_key} mod {self.p}")
    print(f"  s = {self.shared_secret}")
    
    # Derive encryption key from shared secret
    self.aes_key = derive_key(self.shared_secret)
    print(f"\nDeriving AES key: SHA-256(shared_secret)")
    print(f"  AES key: {self.aes_key.hex()}")
```

**Explanation:**
- Shows computation formula and all values
- Calls `compute_shared_secret(B, a, p)`
- Result: `s = B^a mod p = g^(ab) mod p`
- Derives encryption key using SHA-256
- Displays key in hex format

**Example:**
```
Computing shared secret...
Computing: s = B^a mod p
  B (Bob's public key) = 8
  a (Alice's private key) = 3
  p = 23
  s = 8^3 mod 23
  s = 6

Deriving AES key: SHA-256(shared_secret)
  AES key: 19581e27de7ced00ff1ce50b2047e7a567c76b1cbaebabe5ef03f7c3017bb5b7
```

#### Step 7: Encrypted Communication
```python
def chat(self):
    print("\n" + "="*60)
    print("SECURE CHAT (type 'quit' to exit)")
    print("="*60)
    
    while True:
        # Get message from user
        message = input("\nYou: ").strip()
        if not message:
            continue
        if message.lower() == 'quit':
            self.sock.send((json.dumps({'encrypted_message': 'QUIT'}) + '\n').encode())
            break
        
        # Encrypt
        print(f"\n--- Encryption Process ---")
        print(f"Plaintext: '{message}'")
        print(f"AES key: {self.aes_key.hex()}")
        
        encrypted = simple_encrypt(message, self.aes_key)
        encrypted_hex = encrypted.hex()  # Convert bytes to hex string for JSON
        
        print(f"Ciphertext (hex): {encrypted_hex}")
        print(f"Sending...")
        
        # Send encrypted message
        self.sock.send((json.dumps({'encrypted_message': encrypted_hex}) + '\n').encode())
        
        # Wait for reply
        print("\nWaiting for reply...")
        data = recv_msg(self.sock)
        if not data:
            break
        
        msg_data = json.loads(data)
        encrypted_hex = msg_data['encrypted_message']
        
        if encrypted_hex == 'QUIT':
            print("\nBob ended the chat.")
            break
        
        # Decrypt
        print(f"\n--- Decryption Process ---")
        print(f"Received ciphertext (hex): {encrypted_hex}")
        print(f"AES key: {self.aes_key.hex()}")
        
        encrypted_bytes = bytes.fromhex(encrypted_hex)
        decrypted = simple_decrypt(encrypted_bytes, self.aes_key)
        
        print(f"Plaintext: '{decrypted}'")
        print(f"\nBob: {decrypted}")
```

**Explanation:**
- Continuous chat loop (not just one message)
- Shows encryption process:
  1. User types plaintext
  2. Encrypt with derived key
  3. Convert bytes to hex (JSON compatibility)
  4. Send encrypted message
- Shows decryption process:
  1. Receive hex ciphertext
  2. Convert hex to bytes
  3. Decrypt with same key
  4. Display plaintext

**Security Property:** Only Alice and Bob know the shared secret, so only they can decrypt!

### Code Walkthrough: Bob's Side

**Location: `dhke_secure.py` - Bob class**

#### Bob's Key Steps (Mirror of Alice)

1. **Setup Server:** Wait for Alice to connect
2. **Receive Parameters:** Get (p, g) from Alice
3. **Generate Keys:** Random b, compute B = g^b mod p
4. **Exchange Keys:** Send B, receive A
5. **Compute Secret:** s = A^b mod p (same as Alice!)
6. **Chat:** Decrypt Alice's messages, send encrypted replies

**Code is symmetric to Alice but with role reversal:**
- Bob waits, Alice initiates
- Bob receives parameters, Alice chooses them
- Bob computes s = A^b, Alice computes s = B^a
- Result: Both have same secret!

---

## MITM Attack Mechanics

### The Attack Strategy

```
GOAL: Eve intercepts and controls all communication

STRATEGY:
1. Eve pretends to be Bob when talking to Alice
2. Eve pretends to be Alice when talking to Bob
3. Eve establishes SEPARATE secrets with each victim
4. Eve can decrypt messages from both, re-encrypt for forwarding
5. Eve can read, modify, or drop any message

KEY INSIGHT:
- Alice thinks she's talking to Bob (shared secret with Eve!)
- Bob thinks he's talking to Alice (shared secret with Eve!)
- Neither detects the attack without authentication
```

### Attack Flow Diagram

```
MITM ATTACK DETAILED FLOW
=========================

Setup Phase:
────────────
1. Bob starts server on port 5001
2. Eve starts:
   - Server on port 5000 (for Alice)
   - Client to Bob on port 5001
3. Alice connects to port 5000 (thinks it's Bob, actually Eve)

Parameter Interception:
───────────────────────
Alice → Eve:    (p, g, A)
Eve → Bob:      (p, g, E1)    [Eve replaces A with her own E1]
Bob → Eve:      B
Eve → Alice:    E2             [Eve replaces B with her own E2]

Key Generation:
───────────────
Alice:  a_priv, A_pub = g^a mod p
Eve:    e1_priv, E1_pub = g^e1 mod p  (for Bob)
        e2_priv, E2_pub = g^e2 mod p  (for Alice)
Bob:    b_priv, B_pub = g^b mod p

Key Exchange (Replaced by Eve):
────────────────────────────────
Alice sends A → Eve intercepts → Eve sends E1 to Bob
Bob sends B → Eve intercepts → Eve sends E2 to Alice

Shared Secret Computation:
───────────────────────────
Alice computes: s1 = E2^a mod p     [thinks this is with Bob]
Eve computes:   s_alice = A^e2 mod p   [same as s1!]
Eve computes:   s_bob = B^e1 mod p     [different from s1!]
Bob computes:   s2 = E1^b mod p     [thinks this is with Alice]

Result: Alice's secret ≠ Bob's secret, but Eve knows BOTH!

Message Interception:
─────────────────────
Alice → Eve:
  1. Alice encrypts "Hello Bob" with key derived from s1
  2. Eve receives ciphertext
  3. Eve decrypts with key derived from s_alice (same as s1)
  4. Eve reads plaintext: "Hello Bob"
  5. Eve can modify: "Hello Eve" (or forward original)
  6. Eve encrypts modified with key derived from s_bob
  7. Eve sends to Bob

Bob → Eve:
  1. Bob receives ciphertext (encrypted with s_bob key)
  2. Bob decrypts: "Hello Eve" [thinks it's from Alice!]
  3. Bob replies: "Hi Alice!"
  4. Bob encrypts reply with s2 key
  5. Eve receives, decrypts with s_bob key (same as s2)
  6. Eve can modify or forward
  7. Eve re-encrypts with s_alice key
  8. Alice receives, decrypts (thinks it's from Bob)

Attack Success: Complete control over communication!
```

### Code: Eve's Key Generation (TWO Pairs)

**Location: `dhke_mitm.py` - Eve class, `run()` method**

```python
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
```

**What This Does:**
1. Eve generates **two completely separate key pairs**
2. **Pair 1 (e1, E1):** For communication with Alice
3. **Pair 2 (e2, E2):** For communication with Bob
4. This is the core of MITM - Eve has different secrets with each victim

**Why Two Pairs?**
- Eve needs to establish separate secure channels
- Alice thinks her secret is with Bob (actually with Eve using e2)
- Bob thinks his secret is with Alice (actually with Eve using e1)
- Eve acts as "translator" between the two channels

### Code: Key Replacement Attack

**Location: `dhke_mitm.py` - Eve class, key exchange section**

```python
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
```

**What This Does:**
1. **Receive Alice's real key A** from Alice → Eve connection
2. **Send Eve's E1 to Bob** on Eve → Bob connection (impersonate Alice)
3. **Receive Bob's real key B** from Bob → Eve connection
4. **Send Eve's E2 to Alice** on Eve → Alice connection (impersonate Bob)

**Result:**
- Alice has A (her key) and E2 (thinks it's Bob's key)
- Bob has B (his key) and E1 (thinks it's Alice's key)
- Eve has ALL FOUR keys: A, B, E1, E2

**Visual:**
```
What Alice Sees:
  My key: A
  Bob's key: E2  ← FAKE! Actually Eve's

What Bob Sees:
  My key: B
  Alice's key: E1  ← FAKE! Actually Eve's

What Eve Knows:
  Alice's real key: A
  Bob's real key: B
  My key for Alice: E2
  My key for Bob: E1
```

### Code: Computing Two Different Secrets

**Location: `dhke_mitm.py` - Eve class, secret computation**

```python
print("\n--- Computing TWO Different Shared Secrets ---")

print("\nWith Alice:")
print(f"  s1 = A^e1 mod p = {self.alice_public_key}^{self.private_key_alice} mod {self.p}")

self.shared_secret_alice = compute_shared_secret(
    self.alice_public_key,      # Alice's real public key A
    self.private_key_alice,     # Eve's private key e2
    self.p
)

print(f"  s1 = {self.shared_secret_alice}")
self.aes_key_alice = derive_key(self.shared_secret_alice)
print(f"  AES key (Alice-Eve): {self.aes_key_alice.hex()}")

print("\nWith Bob:")
print(f"  s2 = B^e2 mod p = {self.bob_public_key}^{self.private_key_bob} mod {self.p}")

self.shared_secret_bob = compute_shared_secret(
    self.bob_public_key,        # Bob's real public key B
    self.private_key_bob,       # Eve's private key e1
    self.p
)

print(f"  s2 = {self.shared_secret_bob}")
self.aes_key_bob = derive_key(self.shared_secret_bob)
print(f"  AES key (Eve-Bob): {self.aes_key_bob.hex()}")

print(f"\n  ⚠️  MITM SUCCESS: Eve has TWO DIFFERENT secrets!")
```

**What This Does:**
1. **Compute secret with Alice:** s_alice = A^e2 mod p
   - This matches what Alice computed: s1 = E2^a mod p
   - Because: A^e2 = (g^a)^e2 = g^(a*e2) = (g^e2)^a = E2^a ✓
   
2. **Compute secret with Bob:** s_bob = B^e1 mod p
   - This matches what Bob computed: s2 = E1^b mod p
   - Because: B^e1 = (g^b)^e1 = g^(b*e1) = (g^e1)^b = E1^b ✓

3. **Critical Property:** s_alice ≠ s_bob
   - Alice and Bob have DIFFERENT secrets
   - But each thinks their secret is shared with the other
   - Eve has BOTH secrets and can decrypt everything!

**Mathematical Proof:**
```
Alice computes: s1 = E2^a = (g^e2)^a = g^(a*e2)
Eve computes:   s_alice = A^e2 = (g^a)^e2 = g^(a*e2)
Result: s1 = s_alice ✓ (Alice and Eve have same secret)

Bob computes:   s2 = E1^b = (g^e1)^b = g^(b*e1)
Eve computes:   s_bob = B^e1 = (g^b)^e1 = g^(b*e1)
Result: s2 = s_bob ✓ (Bob and Eve have same secret)

But: g^(a*e2) ≠ g^(b*e1) (unless by cosmic coincidence)
So: s1 ≠ s2
Result: Alice and Bob have DIFFERENT secrets!
```

### Code: Message Interception and Modification

**Location: `dhke_mitm.py` - Eve class, message handling**

```python
# Intercept Alice's message
print("\n--- Intercepting Alice's Message ---")
data = recv_msg(self.alice_conn)
msg_data = json.loads(data)
encrypted_hex = msg_data['encrypted_message']

print(f"Received ciphertext (hex): {encrypted_hex}")
print(f"Decrypting with Alice-Eve key: {self.aes_key_alice.hex()}")

# Decrypt with Alice-Eve shared key
encrypted_bytes = bytes.fromhex(encrypted_hex)
self.original_message = simple_decrypt(encrypted_bytes, self.aes_key_alice)

print(f"Plaintext: '{self.original_message}'")

# Ask Eve (user) to modify
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

# Re-encrypt for Bob with Eve-Bob key
print(f"\n--- Re-encrypting for Bob ---")
print(f"Plaintext: '{self.modified_message}'")
print(f"Encrypting with Eve-Bob key: {self.aes_key_bob.hex()}")

new_encrypted = simple_encrypt(self.modified_message, self.aes_key_bob)
new_encrypted_hex = new_encrypted.hex()

print(f"New ciphertext (hex): {new_encrypted_hex}")

# Forward to Bob
self.bob_sock.send((json.dumps({'encrypted_message': new_encrypted_hex}) + '\n').encode())
print("Forwarded to Bob")
```

**What This Does:**

**Step 1: Intercept from Alice**
- Receive encrypted message from Alice
- Message is encrypted with key derived from s_alice

**Step 2: Decrypt with Alice-Eve Key**
- Eve uses `self.aes_key_alice` (derived from s_alice)
- Decrypts successfully (because Eve's secret matches Alice's!)
- Eve can now read plaintext

**Step 3: Optional Modification**
- Eve can read original message
- Eve can modify it (or forward unchanged)
- Demonstrates complete control

**Step 4: Re-encrypt with Eve-Bob Key**
- Eve encrypts (possibly modified) message
- Uses `self.aes_key_bob` (derived from s_bob)
- This is the key Bob expects!

**Step 5: Forward to Bob**
- Send newly encrypted message to Bob
- Bob decrypts with his key (derived from s_bob = s2)
- Bob receives message, thinks it's from Alice!

**Attack Success:**
```
Alice's original: "Hello Bob, meet me at 10pm"
Eve reads and modifies: "Hello Bob, meet me at 2am"
Bob receives: "Hello Bob, meet me at 2am"
Bob thinks: "Alice wants to meet at 2am"
Result: Attack successful, detection impossible without authentication
```

### Why Detection is Impossible

```
From Alice's Perspective:
─────────────────────────
1. Selected parameters (p, g) ✓
2. Generated private key a ✓
3. Computed public key A = g^a mod p ✓
4. Sent A, received "Bob's" public key (actually E2) ✓
5. Computed secret s1 = E2^a mod p ✓
6. Derived encryption key ✓
7. Sent encrypted message ✓
8. Received encrypted reply (decrypts correctly with s1) ✓

Everything looks normal! No indication of MITM.

From Bob's Perspective:
───────────────────────
1. Received parameters (p, g) ✓
2. Generated private key b ✓
3. Computed public key B = g^b mod p ✓
4. Received "Alice's" public key (actually E1) ✓
5. Sent B ✓
6. Computed secret s2 = E1^b mod p ✓
7. Derived encryption key ✓
8. Received encrypted message (decrypts correctly with s2) ✓
9. Sent encrypted reply ✓

Everything looks normal! No indication of MITM.

The Problem:
────────────
- Both parties followed the protocol correctly
- All cryptographic operations succeeded
- Messages decrypt properly
- No errors or anomalies
- BUT: They have different secrets!
- AND: Eve can read/modify everything!

Detection Requires:
───────────────────
1. Authentication (digital signatures on public keys)
2. Out-of-band verification (compare fingerprints)
3. Trust-on-first-use (like SSH)
4. Certificate infrastructure (like TLS)

Without authentication, MITM is undetectable!
```

---

## Attack Difficulty Analysis

### For Eve (Attacker)

#### ✅ EASY: Passive Eavesdropping
```
What Eve sees on network:
- Parameters: p, g (public, not secret)
- Alice's public key: A = g^a mod p
- Bob's public key: B = g^b mod p

Can Eve compute shared secret from this?
s = g^(ab) mod p

Required: Find a from A = g^a mod p (Discrete Log Problem)
Difficulty: INFEASIBLE for large p

Time Complexity:
- 23-bit p: Milliseconds (brute force)
- 512-bit p: Hours/Days (Pollard's rho)
- 1024-bit p: Years (best known algorithms)
- 2048-bit p: Centuries (computationally infeasible)

Conclusion: Passive eavesdropping CANNOT break DHKE with large primes
```

#### ✅ EASY: Active Man-in-the-Middle
```
What Eve needs:
1. Be on the network path between Alice and Bob ✓ (localhost demo)
2. Intercept messages ✓ (TCP proxy)
3. Generate own key pairs ✓ (same protocol)
4. Replace public keys ✓ (modify messages in transit)

Difficulty: TRIVIAL if no authentication!

Requirements:
- Network position (given in demo)
- Understanding of protocol (public knowledge)
- Ability to intercept/modify (sockets)

Time: Instant (same as honest parties)
Cost: Negligible

Conclusion: MITM is EASY without authentication!
```

### For Alice/Bob (Victims)

#### ❌ HARD: Detecting MITM Without Authentication
```
Available Information:
- Own private key (secret)
- Own public key (computed)
- Received public key (claimed to be from other party)
- Shared secret (computed)
- Encrypted messages (decrypt correctly)

Missing Information:
- Is received public key authentic?
- Is other party who they claim to be?
- Are messages being intercepted?

Problem: No way to verify authenticity!

All observable properties match expected behavior:
- Key exchange completes ✓
- Secret computation succeeds ✓
- Encryption/decryption work ✓
- Messages readable ✓

Conclusion: Detection IMPOSSIBLE without out-of-band verification!
```

#### ✅ EASY: Prevention with Authentication
```
Solutions:
1. Digital Signatures:
   - Sign public keys with long-term private key
   - Verify signature with trusted public key
   - Eve cannot forge signatures without private key

2. Certificates (TLS model):
   - Certificate Authority signs public keys
   - Verify CA signature before trusting key
   - Eve cannot obtain valid certificate

3. Trust-on-First-Use (SSH model):
   - Save fingerprint of first key received
   - Warn if key changes on subsequent connections
   - Detects MITM on second attempt

4. Out-of-Band Verification:
   - Compare key fingerprints via phone call
   - Visual/audio verification (Signal safety numbers)
   - Eve cannot intercept separate channel

Implementation Complexity: Moderate
Effectiveness: Complete MITM prevention

Conclusion: Authentication is ESSENTIAL for real-world security!
```

### Code: Brute Force Discrete Log (Weak Parameters)

**Location: `dh_params.py` - `brute_force_discrete_log()` function**

```python
def brute_force_discrete_log(public_key, g, p, max_attempts=2**25):
    """
    Attempt to find private key via brute force: Find x such that g^x mod p = public_key
    
    WARNING: Only works for small p! Demonstrates why large primes are essential.
    
    Time Complexity: O(p) in worst case
    For p = 23: Trivial (max 23 attempts)
    For p = 2^2048: Impossible (would take longer than age of universe)
    
    Args:
        public_key: Target value (A or B)
        g: Generator
        p: Prime modulus
        max_attempts: Stop after this many tries (prevent infinite loop)
    
    Returns:
        Private key if found, None otherwise
    """
    print(f"Attempting brute force discrete log...")
    print(f"Searching for x where {g}^x mod {p} = {public_key}")
    
    for x in range(1, min(p, max_attempts)):
        if pow(g, x, p) == public_key:
            print(f"SUCCESS! Found private key: {x}")
            return x
        
        if x % 1000000 == 0:  # Progress indicator
            print(f"Tried {x} values...")
    
    print(f"Failed after {max_attempts} attempts")
    return None
```

**What This Does:**
1. Tries every possible private key value
2. For each x, computes g^x mod p
3. Checks if result matches target public key
4. Returns x if found (this is the private key!)

**Effectiveness by Parameter Size:**
```
p = 23 (23-bit):
  Max attempts: 23
  Time: < 1 millisecond
  Result: BREAKS INSTANTLY ✓

p = 2^512 (512-bit):
  Max attempts: ~10^154
  Time: ~10^140 years (age of universe: ~10^10 years)
  Result: COMPUTATIONALLY INFEASIBLE ✗

p = 2^2048 (2048-bit):
  Max attempts: ~10^617
  Time: Incomprehensibly long
  Result: PRACTICALLY IMPOSSIBLE ✗
```

**Conclusion:** Large primes make discrete log infeasible, securing DHKE against passive attacks!

---

## Code Mapping - Line by Line

### Key Functions in dh_params.py

| Function | Line Range | Purpose | Used By |
|----------|-----------|---------|---------|
| `get_dh_params()` | 15-45 | Returns (p, g) for bit size | All scripts (parameter selection) |
| `generate_private_key()` | 48-65 | Secure random key generation | Alice, Bob, Eve (key gen) |
| `compute_public_key()` | 68-85 | A = g^a mod p computation | Alice, Bob, Eve (public key) |
| `compute_shared_secret()` | 88-105 | s = B^a mod p computation | Alice, Bob, Eve (shared secret) |
| `derive_key()` | 108-125 | SHA-256 key derivation | All (encryption key) |
| `simple_encrypt()` | 128-145 | XOR encryption (demo) | All (message encryption) |
| `simple_decrypt()` | 148-165 | XOR decryption (demo) | All (message decryption) |
| `brute_force_discrete_log()` | 168-195 | Educational DLP attack | analysis.py (weak param demo) |

### Critical Code Sections in dhke_secure.py

#### Alice Class Structure
```python
Lines 35-50:   __init__() - Initialize Alice with port, empty keys
Lines 52-70:   select_parameters() - User chooses security level
Lines 72-85:   connect() - TCP socket connection to Bob
Lines 87-100:  send_parameters() - Send (p, g) to Bob
Lines 102-125: generate_keys() - Generate a, compute A
Lines 127-145: exchange_keys() - Send A, receive B
Lines 147-170: compute_secret() - Compute s = B^a mod p
Lines 172-220: chat() - Continuous encrypted messaging loop
Lines 222-235: run() - Execute full protocol
```

#### Bob Class Structure
```python
Lines 240-260: __init__() - Initialize Bob with port, empty keys
Lines 262-280: setup_server() - Create TCP server socket
Lines 282-300: receive_parameters() - Receive (p, g) from Alice
Lines 302-325: generate_keys() - Generate b, compute B
Lines 327-345: exchange_keys() - Receive A, send B
Lines 347-370: compute_secret() - Compute s = A^b mod p
Lines 372-430: chat() - Continuous encrypted messaging loop
Lines 432-445: run() - Execute full protocol
```

### Critical Code Sections in dhke_mitm.py

#### Eve Class Structure (Attack Code)
```python
Lines 295-330:  __init__() - Initialize Eve with TWO key pair storage
Lines 332-360:  run() setup - Dual socket setup (server for Alice, client to Bob)
Lines 362-380:  Parameter interception - Receive from Alice, forward to Bob
Lines 382-410:  TWO key pair generation - e1/E1 and e2/E2
Lines 412-445:  Key replacement attack - Replace A with E1, B with E2
Lines 447-485:  TWO secret computation - s_alice and s_bob (different!)
Lines 487-520:  Message interception - Decrypt with s_alice
Lines 522-545:  Message modification - User chooses to modify/forward
Lines 547-570:  Re-encryption - Encrypt with s_bob
Lines 572-605:  Continuous loop - Intercept every message in conversation
Lines 607-650:  Analysis output - Show attack success, different secrets
```

### Message Format

**All network messages use JSON with newline delimiter:**
```python
# Example: Parameter transmission
data = json.dumps({'p': '23', 'g': '5', 'bits': '23'}) + '\n'
sock.send(data.encode())

# Example: Public key transmission
data = json.dumps({'public_key': '10'}) + '\n'
sock.send(data.encode())

# Example: Encrypted message transmission
encrypted_hex = encrypted.hex()  # bytes → hex string
data = json.dumps({'encrypted_message': encrypted_hex}) + '\n'
sock.send(data.encode())
```

**Why JSON + '\n'?**
- JSON: Structured data, easy parsing
- '\n' delimiter: Marks message boundaries (socket is stream-based)
- `recv_msg()` helper: Reads byte-by-byte until '\n' for complete message

### Helper Function: recv_msg()

**Location: dhke_secure.py and dhke_mitm.py, lines 21-31**

```python
def recv_msg(sock):
    """
    Receive a complete message (reads until newline)
    
    Problem: sock.recv(4096) may return:
    - Incomplete message (split across multiple packets)
    - Multiple messages concatenated
    
    Solution: Read byte-by-byte until '\n' delimiter
    
    Returns:
        Complete message string (without '\n'), or None if connection closed
    """
    data = b''
    while True:
        chunk = sock.recv(1)  # Read one byte
        if not chunk:
            return None  # Connection closed
        data += chunk
        if chunk == b'\n':
            return data.decode().strip()  # Remove '\n', decode to string
```

**Why Needed?**
- TCP is stream-based, not message-based
- `recv(4096)` might return partial message or multiple messages
- Need reliable way to extract complete JSON objects
- '\n' delimiter + byte-by-byte reading ensures complete messages

---

## Professor Q&A Preparation

### Mathematical Questions

**Q: Prove that Alice and Bob compute the same shared secret.**

**A:** Mathematical proof:

Alice computes:
```
s_alice = B^a mod p
        = (g^b mod p)^a mod p
        = g^(b*a) mod p
```

Bob computes:
```
s_bob = A^b mod p
      = (g^a mod p)^b mod p
      = g^(a*b) mod p
```

By commutativity of multiplication: `a*b = b*a`

Therefore: `g^(a*b) = g^(b*a)`

Result: `s_alice = s_bob = g^(ab) mod p` ✓

**Q: Why can't an eavesdropper compute the shared secret?**

**A:** Eavesdropper sees:
- Public parameters: p, g
- Alice's public key: A = g^a mod p
- Bob's public key: B = g^b mod p

To compute shared secret `s = g^(ab) mod p`, eavesdropper needs either:
1. Alice's private key `a`, OR
2. Bob's private key `b`

To find `a` from `A = g^a mod p` requires solving the Discrete Logarithm Problem (DLP).

**DLP Hardness:** For large prime p (2048 bits), best known algorithms require:
- Pollard's rho: O(√p) time ≈ 2^1024 operations
- Index calculus: Still exponential for general primes
- Quantum computers: Shor's algorithm (but not yet practical)

**Conclusion:** Computationally infeasible with current technology.

**Q: Why is MITM possible if DLP is hard?**

**A:** MITM doesn't solve DLP!

Eve doesn't need to find Alice's or Bob's private keys. Instead:
1. Eve generates her own key pairs (e1, E1) and (e2, E2)
2. Eve replaces public keys in transit (no cryptographic breaking)
3. Eve establishes separate secrets with each party
4. Eve uses her own keys (which she knows) to decrypt

**Key Insight:** MITM is an *active* attack (modifies messages), not passive (just eavesdrops). DLP hardness only protects against passive attacks.

**Prevention:** Authentication (digital signatures, certificates) prevents key replacement.

### Implementation Questions

**Q: Why use SHA-256 to derive the encryption key from the shared secret?**

**A:** Several reasons:

1. **Fixed Size:** Shared secret is large integer (up to p-1). SHA-256 gives fixed 256-bit output suitable for encryption.

2. **Uniform Distribution:** Direct use of shared secret might have biased bits. SHA-256 ensures uniform distribution.

3. **Key Separation:** If shared secret is reused (shouldn't be, but defense-in-depth), hash provides different keys.

4. **One-Way Property:** Can't recover shared secret from encryption key (additional security layer).

5. **Standard Practice:** Matches real-world protocols (TLS uses HKDF which involves SHA-256).

**Code:**
```python
def derive_key(shared_secret):
    secret_bytes = str(shared_secret).encode('utf-8')
    return hashlib.sha256(secret_bytes).digest()  # 32 bytes
```

**Q: Why use `secrets` module instead of `random`?**

**A:** Comparison:

**`random` module (INSECURE):**
- Mersenne Twister algorithm (deterministic)
- If attacker knows seed, all keys predictable
- State has only 19937 bits of entropy
- Designed for simulation, not security

**`secrets` module (SECURE):**
- Uses `os.urandom()` (wraps /dev/urandom on Unix, CryptGenRandom on Windows)
- Gets entropy from OS sources:
  - Hardware RNG (if available)
  - System events (interrupts, disk timings, etc.)
  - Cryptographic mixing of entropy pool
- Unpredictable even if previous outputs known
- Designed specifically for cryptographic use

**Code:**
```python
# SECURE (use this):
private_key = secrets.randbelow(p - 2) + 1

# INSECURE (never use for crypto):
private_key = random.randint(1, p - 2)  # Predictable!
```

**Demonstration in analysis.py:** Shows how insecure random is predictable with known seed.

**Q: Why do we need the `recv_msg()` helper function?**

**A:** TCP sockets are stream-based, not message-based:

**Problem 1: Partial Messages**
```python
sock.send(b'{"public_key": "123456789"}\n')  # Send 30 bytes

# Receiver might get:
data1 = sock.recv(4096)  # Returns: b'{"public_key": "'
data2 = sock.recv(4096)  # Returns: b'123456789"}\n'
# JSON parsing fails on data1!
```

**Problem 2: Concatenated Messages**
```python
# Sender sends two messages quickly:
sock.send(b'{"msg": "hello"}\n')
sock.send(b'{"msg": "world"}\n')

# Receiver might get:
data = sock.recv(4096)  # Returns: b'{"msg": "hello"}\n{"msg": "world"}\n'
# JSON parsing fails on concatenated data!
```

**Solution: Message Framing**
```python
def recv_msg(sock):
    data = b''
    while True:
        chunk = sock.recv(1)  # Read byte-by-byte
        if not chunk:
            return None  # Connection closed
        data += chunk
        if chunk == b'\n':  # Found delimiter
            return data.decode().strip()  # Complete message!
```

This ensures we always get exactly one complete JSON object.

### Security Questions

**Q: Is this implementation secure for production use?**

**A: NO! This is educational only. Issues:**

1. **Weak Encryption:** Simple XOR is not secure
   - No authentication (no MAC)
   - No IV (initialization vector)
   - Vulnerable to known-plaintext attacks
   - **Production:** Use AES-GCM or ChaCha20-Poly1305

2. **No Forward Secrecy:** Same keys reused for entire session
   - If private key compromised, all past sessions broken
   - **Production:** Use ephemeral keys (DHE/ECDHE)

3. **No Authentication:** Vulnerable to MITM (by design for demo!)
   - **Production:** Use digital signatures (RSA, ECDSA)
   - Or certificate infrastructure (TLS)

4. **Timing Attacks:** No constant-time operations
   - Modular exponentiation timing may leak info
   - **Production:** Use constant-time implementations

5. **Network Security:** Plain JSON over TCP
   - No packet authentication
   - No protection against replay attacks
   - **Production:** Use TLS with proper cipher suites

**Conclusion:** Good for learning, never for real applications!

**Q: How does TLS prevent MITM attacks?**

**A:** TLS (Transport Layer Security) adds authentication:

**TLS Handshake (Simplified):**
```
1. Client → Server: ClientHello (supported ciphers)
2. Server → Client: ServerHello (chosen cipher)
                     Certificate (server's public key + CA signature)
                     ServerKeyExchange (DH parameters + signature)
3. Client verifies:
   a. Certificate signature (using trusted CA's public key)
   b. DH parameter signature (using server's public key from cert)
4. If verification passes:
   Client → Server: ClientKeyExchange (DH public key)
5. Both compute shared secret (authenticated DHKE)
6. Encrypted data exchange
```

**Key Differences from Our Implementation:**
1. **Certificates:** Server public key is signed by trusted Certificate Authority
2. **Signatures:** DH parameters and public keys are digitally signed
3. **Verification:** Client verifies signatures before trusting keys
4. **Result:** MITM impossible without valid certificate (which attacker can't obtain)

**Why Our Demo Lacks This:**
- Focus on DHKE mechanics, not TLS complexity
- Authentication (PKI, signatures) is separate topic
- Demonstrating vulnerability is educational purpose

**Q: Can you detect MITM after it happens?**

**A:** Difficult without preparation:

**Detection Methods:**

1. **Out-of-Band Verification (Proactive):**
   ```
   Alice and Bob:
   - Compare key fingerprints via phone call
   - Visual: "My key fingerprint is ABC123..."
   - If mismatch → MITM detected
   - Used by: Signal, WhatsApp (safety numbers)
   ```

2. **Certificate Transparency (TLS):**
   ```
   - Server certificates logged in public ledgers
   - Clients can check if cert seen before
   - Sudden cert change → suspicious
   - Used by: Modern browsers (CT logs)
   ```

3. **Trust-on-First-Use (TOFU):**
   ```
   - Save fingerprint of first key received
   - On subsequent connections, check if same
   - Change → warn user (possible MITM)
   - Used by: SSH ("Host key has changed!")
   ```

4. **Network Monitoring (Forensic):**
   ```
   - Monitor for unusual patterns
   - Multiple TLS handshakes for one session
   - Mismatched certificate chains
   - Requires sophisticated tools
   ```

**In Our Demo:**
- No out-of-band channel implemented
- No fingerprint comparison
- No certificate infrastructure
- **Result:** MITM undetectable by Alice/Bob without external help

**Lesson:** Prevention (authentication) is far better than detection!

### Code-Specific Questions

**Q: Walk through the socket communication for MITM attack.**

**A:** Detailed flow with code references:

**Setup (Eve's `run()` method, lines 332-360):**
```python
# Eve creates server socket for Alice
self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
self.server_sock.bind(('localhost', 5000))  # Alice connects here
self.server_sock.listen(1)

# Eve connects to Bob as client
self.bob_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
self.bob_sock.connect(('localhost', 5001))  # Bob listens here

# Wait for Alice
self.alice_conn, addr = self.server_sock.accept()
```

**Result:** Eve has TWO sockets:
- `self.alice_conn`: Connected to Alice (Eve acts as server)
- `self.bob_sock`: Connected to Bob (Eve acts as client)

**Parameter Flow (lines 362-380):**
```python
# Alice → Eve
data = self.alice_conn.recv(8192).decode().strip()
params = json.loads(data)  # {"p": "23", "g": "5", ...}

# Eve → Bob (forward unchanged)
self.bob_sock.send(data.encode())
```

**Key Exchange Flow (lines 412-445):**
```python
# Alice → Eve: Receive A
data = self.alice_conn.recv(4096).decode().strip()
self.alice_public_key = int(json.loads(data)['public_key'])

# Eve → Bob: Send E1 (NOT A!)
fake_msg = {'public_key': str(self.public_key_bob)}
self.bob_sock.send((json.dumps(fake_msg) + '\n').encode())

# Bob → Eve: Receive B
data = self.bob_sock.recv(4096).decode().strip()
self.bob_public_key = int(json.loads(data)['public_key'])

# Eve → Alice: Send E2 (NOT B!)
fake_msg = {'public_key': str(self.public_key_alice)}
self.alice_conn.send((json.dumps(fake_msg) + '\n').encode())
```

**Message Flow (lines 487-570):**
```python
# Alice → Eve: Encrypted with s_alice
data = recv_msg(self.alice_conn)
encrypted_hex = json.loads(data)['encrypted_message']

# Eve decrypts with s_alice
encrypted_bytes = bytes.fromhex(encrypted_hex)
plaintext = simple_decrypt(encrypted_bytes, self.aes_key_alice)

# Eve re-encrypts with s_bob
new_encrypted = simple_encrypt(plaintext, self.aes_key_bob)
new_encrypted_hex = new_encrypted.hex()

# Eve → Bob: Encrypted with s_bob
self.bob_sock.send((json.dumps({'encrypted_message': new_encrypted_hex}) + '\n').encode())
```

**Key Insight:** Eve acts as "translator" between two separate encrypted channels!

**Q: How would you add authentication to prevent MITM?**

**A:** Implementation approach:

**Option 1: Pre-Shared Keys**
```python
# Before protocol starts, Alice and Bob share secret K out-of-band
# Sign public keys with K:

# Alice sends:
signature_A = HMAC_SHA256(K, A)
send({'public_key': A, 'signature': signature_A})

# Bob verifies:
expected_sig = HMAC_SHA256(K, A)
if received_sig != expected_sig:
    abort("MITM detected!")
```

**Option 2: Digital Signatures (RSA)**
```python
# Alice has long-term RSA key pair (private_RSA_A, public_RSA_A)
# Bob knows public_RSA_A (from trusted source)

# Alice sends:
signature_A = RSA_sign(private_RSA_A, A)
send({'public_key': A, 'signature': signature_A})

# Bob verifies:
if not RSA_verify(public_RSA_A, A, signature_A):
    abort("Invalid signature - MITM attack!")
```

**Option 3: Certificate Authority (TLS Model)**
```python
# Certificate contains:
cert = {
    'public_key_DH': A,
    'identity': 'Alice',
    'CA_signature': sign(CA_private_key, (A, 'Alice'))
}

# Bob verifies:
if not verify(CA_public_key, (A, 'Alice'), cert['CA_signature']):
    abort("Invalid certificate!")
```

**Why Not in Our Implementation:**
- Focus on DHKE mechanics
- Authentication is complex separate topic
- Goal is to demonstrate vulnerability
- Adding authentication would hide the MITM weakness

---

## Summary for Presentation

### Key Points to Emphasize

1. **DHKE is Secure Against Passive Attacks**
   - DLP hardness protects shared secret
   - Eavesdropper can't compute s from (g, p, A, B)
   - 2048-bit parameters provide strong security

2. **DHKE is Vulnerable to Active Attacks Without Authentication**
   - MITM is trivial if attacker can intercept
   - Eve establishes separate secrets with each party
   - No cryptographic breaking required

3. **Real-World Protocols Add Authentication**
   - TLS uses certificates (PKI infrastructure)
   - SSH uses trust-on-first-use
   - Signal uses safety number verification
   - Authentication prevents key replacement

4. **Implementation Details Matter**
   - Secure random crucial (secrets, not random)
   - Safe primes prevent attacks
   - Message framing needed for reliable communication
   - Key derivation provides uniform keys

### Live Demo Talking Points

**For Secure Demo:**
- "Notice both compute same secret despite never sharing private keys"
- "Eavesdropper sees A and B but can't compute s - that's DLP hardness"
- "Messages encrypt/decrypt successfully - protocol works as designed"

**For MITM Demo:**
- "Eve generates TWO key pairs - acts as 'translator' between channels"
- "Alice thinks her secret is with Bob - actually with Eve!"
- "Bob thinks his secret is with Alice - actually with Eve!"
- "Eve can read everything, modify anything, drop messages"
- "Neither party detects attack - that's why authentication is critical"

**For Weak Parameters Demo:**
- "23-bit prime breaks in milliseconds via brute force"
- "Demonstrates why large primes essential"
- "Real protocols use 2048-bit or larger"

### Expected Questions and Answers

**Q: "Couldn't you just hash the public keys to create a fingerprint and compare out-of-band?"**

**A:** "Yes! That's exactly how Signal and WhatsApp do it. They show 'safety numbers' - fingerprints of public keys. Users compare via phone call or in person. Our demo doesn't implement this to show the vulnerability when it's missing."

**Q: "How is this used in practice like in HTTPS?"**

**A:** "HTTPS uses TLS, which builds on DHKE but adds:
1. Server certificate signed by trusted CA
2. Digital signatures on DH parameters
3. Client verifies certificate before trusting keys
This prevents MITM because attacker can't forge valid certificates."

**Q: "What if Eve gets caught later - can past communications be decrypted?"**

**A:** "In our implementation, yes - we reuse same keys. But real protocols use *ephemeral* keys (new for each session). Even if Eve's long-term keys are compromised later, past sessions remain secure. That's called *forward secrecy*."

**Q: "Is quantum computing a threat to this?"**

**A:** "Yes, Shor's algorithm can solve DLP in polynomial time on quantum computer. Defense: Post-quantum cryptography like lattice-based schemes. But practical quantum computers don't exist yet for breaking 2048-bit DLP."

---

## Conclusion

This document provides complete technical understanding of:
- ✅ How communication channels are established (sockets, TCP)
- ✅ How keys are generated (secure random, modular exponentiation)
- ✅ How keys are exchanged (JSON messaging over TCP)
- ✅ How Eve intercepts (dual socket setup, key replacement)
- ✅ How Eve decrypts (separate secrets with each victim)
- ✅ Why attack is easy (no authentication)
- ✅ Why detection is hard (no distinguishing features)
- ✅ Code mapping (every function explained)

**You are now prepared to:**
1. Explain any part of the code in detail
2. Walk through protocol flows step-by-step
3. Answer mathematical questions with proofs
4. Discuss security implications and real-world applications
5. Handle professor questions confidently

**Key Takeaway:**
DHKE is mathematically secure (DLP hardness) but protocol-level vulnerable (MITM without authentication). Real-world systems add authentication - our implementation deliberately omits it to demonstrate the critical importance of authentication in cryptographic protocols.

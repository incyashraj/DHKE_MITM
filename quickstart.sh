#!/bin/bash
# Quick Start Guide for DHKE Project Demonstrations
# This script helps you quickly run different demonstrations

echo "============================================"
echo "DHKE Project - Quick Start Menu"
echo "============================================"
echo ""
echo "Choose a demonstration:"
echo ""
echo "1. Run Comprehensive Tests (recommended first)"
echo "2. Secure DHKE Demo (2 terminals needed)"
echo "3. MITM Attack Demo (3 terminals needed)"
echo "4. Quick test of utilities"
echo "5. Show project structure"
echo ""
read -p "Enter choice (1-5): " choice

case $choice in
    1)
        echo ""
        echo "Running comprehensive test suite..."
        echo "===================================="
        python analysis.py
        ;;
    2)
        echo ""
        echo "SECURE DHKE DEMONSTRATION"
        echo "========================="
        echo ""
        echo "You need TWO terminal windows for this demo."
        echo ""
        echo "Terminal 1 - Run Bob (server):"
        echo "  python dhke_secure.py --bob"
        echo ""
        echo "Terminal 2 - Run Alice (client):"
        echo "  python dhke_secure.py --alice"
        echo ""
        echo "Options:"
        echo "  --bits 1024   Use 1024-bit keys (faster)"
        echo "  --bits 2048   Use 2048-bit keys (more secure, default)"
        echo ""
        read -p "Press Enter to continue..."
        ;;
    3)
        echo ""
        echo "MAN-IN-THE-MIDDLE ATTACK DEMONSTRATION"
        echo "======================================"
        echo ""
        echo "You need THREE terminal windows for this demo."
        echo ""
        echo "Start them IN THIS ORDER:"
        echo ""
        echo "Terminal 1 - Bob (victim server):"
        echo "  python dhke_mitm.py --bob"
        echo ""
        echo "Terminal 2 - Eve (attacker):"
        echo "  python dhke_mitm.py --eve"
        echo ""
        echo "Terminal 3 - Alice (victim client):"
        echo "  python dhke_mitm.py --alice"
        echo ""
        echo "Watch Eve intercept and modify the messages!"
        echo ""
        read -p "Press Enter to continue..."
        ;;
    4)
        echo ""
        echo "Running quick utility test..."
        echo "============================"
        python dh_params.py
        ;;
    5)
        echo ""
        echo "PROJECT STRUCTURE"
        echo "================="
        echo ""
        ls -lh *.py
        echo ""
        echo "Files:"
        echo "  dh_params.py     - Core cryptographic utilities"
        echo "  dhke_secure.py   - Secure key exchange demo"
        echo "  dhke_mitm.py     - MITM attack simulation"
        echo "  analysis.py      - Comprehensive test suite"
        echo "  README.md        - Full documentation"
        echo ""
        ;;
    *)
        echo "Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo ""
echo "============================================"
echo "For full documentation, see README.md"
echo "============================================"

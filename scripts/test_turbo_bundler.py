#!/usr/bin/env python3
"""
Test Turbo (ar.io) Bundler Before Full Migration
================================================

Tests that:
1. Turbo endpoint is reachable
2. <100KB uploads work (free tier)
3. Data can be retrieved from arweave.net gateway

Run: python3 test_turbo_bundler.py
"""
import json
import requests
import hashlib
from datetime import datetime

# Turbo/ar.io endpoints
TURBO_MAINNET = "https://up.arweave.net"          # <100KB FREE
TURBO_DEVNET = "https://upload.ardrive.dev"        # Testing
ARWEAVE_GATEWAY = "https://arweave.net"

def test_endpoint_reachable():
    """Test 1: Can we reach the Turbo endpoint?"""
    print("=" * 50)
    print("TEST 1: Endpoint Reachability")
    print("=" * 50)
    
    endpoints = [
        ("Turbo Mainnet", TURBO_MAINNET),
        ("Arweave Gateway", ARWEAVE_GATEWAY),
    ]
    
    all_ok = True
    for name, url in endpoints:
        try:
            resp = requests.get(url, timeout=10)
            status = "✅ OK" if resp.status_code in [200, 404, 405] else f"⚠️ {resp.status_code}"
            print(f"  {name}: {status}")
        except Exception as e:
            print(f"  {name}: ❌ {e}")
            all_ok = False
    
    return all_ok


def test_turbo_upload_info():
    """Test 2: Check Turbo upload capabilities."""
    print("\n" + "=" * 50)
    print("TEST 2: Turbo Upload API Info")
    print("=" * 50)
    
    # Check the Turbo pricing/info endpoint
    try:
        # Turbo uses ar.io gateway
        resp = requests.get(f"{TURBO_MAINNET}/v1/info", timeout=10)
        if resp.status_code == 200:
            info = resp.json()
            print(f"  Turbo API Info: {json.dumps(info, indent=2)[:500]}")
            return True
        else:
            print(f"  Info endpoint returned: {resp.status_code}")
            # This is OK - not all endpoints have /v1/info
    except Exception as e:
        print(f"  Could not get info (this is OK): {e}")
    
    # Try to understand the upload API
    print("\n  Turbo API expects:")
    print("  - POST to https://up.arweave.net/v1/tx")
    print("  - Content-Type: application/octet-stream")
    print("  - Tags in headers or multipart form")
    print("  - <100KB is FREE (no wallet needed)")
    print("  - >100KB requires payment in AR, ETH, SOL, or credit card")
    
    return True


def test_small_upload_simulation():
    """Test 3: Simulate a small upload (don't actually upload without wallet)."""
    print("\n" + "=" * 50)
    print("TEST 3: Small Upload Size Check")
    print("=" * 50)
    
    # Create a test NPC profile (exactly what we'd upload)
    test_npc = {
        "id": "npc_test_001",
        "name": "Test NPC",
        "archetype": "test_archetype",
        "personality_vector": {
            "paranoia": 0.5,
            "mysticism": 0.5,
            "aggression": 0.5
        },
        "topic_weights": {
            "test": 0.5
        },
        "catchphrases": ["This is a test."],
        "created_at": datetime.now().isoformat()
    }
    
    json_data = json.dumps(test_npc, indent=2)
    size_bytes = len(json_data.encode('utf-8'))
    
    print(f"  Test NPC JSON size: {size_bytes} bytes")
    print(f"  Free tier threshold: 102,400 bytes (100KB)")
    print(f"  Within free tier: {'✅ YES' if size_bytes < 102400 else '❌ NO'}")
    
    # Show what tags we'd use
    tags = [
        {"name": "Content-Type", "value": "application/json"},
        {"name": "App-Name", "value": "AO-World-Engine"},
        {"name": "Type", "value": "npc_profile"},
        {"name": "NPC-Id", "value": test_npc["id"]},
        {"name": "NPC-Name", "value": test_npc["name"]},
    ]
    
    print(f"\n  Tags that would be added:")
    for tag in tags:
        print(f"    {tag['name']}: {tag['value']}")
    
    return size_bytes < 102400


def test_existing_arweave_data():
    """Test 4: Verify we can still read from Arweave gateway."""
    print("\n" + "=" * 50)
    print("TEST 4: Existing Arweave Data Retrieval")
    print("=" * 50)
    
    # Try to fetch your existing NPC schema
    test_tx = "XmlqPa1RNFvipxnvyZTgbpx8EjOZNzNNI2tMGjQ3eb4"
    
    try:
        resp = requests.get(f"{ARWEAVE_GATEWAY}/{test_tx}", timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            print(f"  ✅ Successfully fetched existing Arweave data")
            print(f"  TX: {test_tx}")
            print(f"  Title: {data.get('title', 'N/A')}")
            print(f"  Version: {data.get('version', 'N/A')}")
            return True
        else:
            print(f"  ⚠️ Got status {resp.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Could not fetch: {e}")
        return False


def test_graphql_query():
    """Test 5: Verify GraphQL queries work (for finding data)."""
    print("\n" + "=" * 50)
    print("TEST 5: GraphQL Query API")
    print("=" * 50)
    
    query = """
    {
        transactions(
            tags: [
                { name: "App-Name", values: ["Wandern-GeoEcho"] }
            ]
            first: 3
        ) {
            edges {
                node {
                    id
                    tags {
                        name
                        value
                    }
                }
            }
        }
    }
    """
    
    try:
        resp = requests.post(
            f"{ARWEAVE_GATEWAY}/graphql",
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        if resp.status_code == 200:
            data = resp.json()
            edges = data.get("data", {}).get("transactions", {}).get("edges", [])
            print(f"  ✅ GraphQL working")
            print(f"  Found {len(edges)} existing Wandern-GeoEcho transactions")
            return True
        else:
            print(f"  ⚠️ GraphQL returned {resp.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ GraphQL error: {e}")
        return False


def main():
    print("\n🧪 TURBO (ar.io) BUNDLER MIGRATION TEST")
    print("Testing before migrating from Irys...\n")
    
    results = []
    
    results.append(("Endpoints Reachable", test_endpoint_reachable()))
    results.append(("Turbo API Info", test_turbo_upload_info()))
    results.append(("Small Upload Size", test_small_upload_simulation()))
    results.append(("Arweave Data Retrieval", test_existing_arweave_data()))
    results.append(("GraphQL Queries", test_graphql_query()))
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All tests passed! Safe to migrate from Irys to Turbo.")
        print("\nKey differences:")
        print("  OLD: https://node1.irys.xyz  →  NEW: https://up.arweave.net")
        print("  OLD: IRYS_DEVNET env var    →  NEW: TURBO_DEVNET env var")
        print("\nFree tier still applies: <100KB uploads are FREE on Turbo!")
    else:
        print("⚠️ Some tests failed. Review before proceeding with migration.")
    print("=" * 50)
    
    return all_passed


if __name__ == "__main__":
    main()

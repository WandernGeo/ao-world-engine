#!/usr/bin/env python3
"""
AO World Engine - Arweave Test Deployment

Deploys test and core files to Arweave using the existing wallet.
All files are <100KB so they qualify for the free tier.
"""
import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import arweave
except ImportError:
    print("❌ arweave-python-client not installed")
    print("   Run: pip install arweave-python-client")
    sys.exit(1)

# Paths
WALLET_PATH = "/Users/ram/Documents/wandern/wandern-back/arweave-wallet.json"
PROJECT_ROOT = Path(__file__).parent.parent

# Files to deploy (all under 100KB)
DEPLOY_FILES = [
    {
        "path": "docs/WHITEPAPER.md",
        "type": "Documentation", 
        "content_type": "text/markdown",
    },
    {
        "path": "schemas/action_dictionary.json",
        "type": "Schema",
        "content_type": "application/json",
    },
    {
        "path": "ao-processes/district.lua",
        "type": "AO-Process",
        "content_type": "text/x-lua",
    },
]


def create_tags(file_info: dict, content_hash: str) -> list:
    """Create Arweave tags for discoverability."""
    return [
        {"name": "App-Name", "value": "AO-World-Engine"},
        {"name": "App-Version", "value": "1.0"},
        {"name": "Content-Type", "value": file_info["content_type"]},
        {"name": "Type", "value": file_info["type"]},
        {"name": "Filename", "value": Path(file_info["path"]).name},
        {"name": "Date", "value": datetime.now().strftime("%Y-%m-%d")},
        {"name": "Content-Hash", "value": content_hash[:16]},
        {"name": "Ecosystem", "value": "Arweave,AO"},
    ]


def upload_file(wallet, file_info: dict) -> str:
    """Upload a file to Arweave and return transaction ID."""
    file_path = PROJECT_ROOT / file_info["path"]
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return None
    
    content = file_path.read_bytes()
    content_hash = hashlib.sha256(content).hexdigest()
    
    print(f"\n📁 {file_info['path']}")
    print(f"   Size: {len(content):,} bytes")
    print(f"   Hash: {content_hash[:16]}...")
    
    # Create transaction
    tx = arweave.Transaction(wallet, data=content)
    
    # Add tags
    tags = create_tags(file_info, content_hash)
    for tag in tags:
        tx.add_tag(tag["name"], tag["value"])
    
    # Sign and send
    print("   🔐 Signing...")
    tx.sign()
    
    print("   🚀 Uploading...")
    try:
        tx.send()
        print(f"   ✅ TX: {tx.id}")
        return tx.id
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return None


def upload_test():
    """Upload a minimal test payload first."""
    print("\n" + "=" * 50)
    print("🧪 TEST UPLOAD")
    print("=" * 50)
    
    # Load wallet
    wallet = arweave.Wallet(WALLET_PATH)
    print(f"💼 Wallet: {wallet.address[:20]}...")
    print(f"💰 Balance: {wallet.balance} AR")
    
    # Create minimal test data
    test_data = {
        "type": "test",
        "app": "AO-World-Engine",
        "version": "1.0",
        "timestamp": datetime.now().isoformat(),
        "message": "AO World Engine test deployment"
    }
    
    data_json = json.dumps(test_data, indent=2)
    print(f"\n📦 Test payload: {len(data_json)} bytes")
    
    # Create transaction
    tx = arweave.Transaction(wallet, data=data_json.encode())
    tx.add_tag("App-Name", "AO-World-Engine")
    tx.add_tag("Content-Type", "application/json")
    tx.add_tag("Type", "Test")
    tx.add_tag("Date", datetime.now().strftime("%Y-%m-%d"))
    
    # Sign and send
    print("🔐 Signing transaction...")
    tx.sign()
    
    print("🚀 Submitting to Arweave network...")
    try:
        tx.send()
        print(f"\n✅ SUCCESS!")
        print(f"   TX ID: {tx.id}")
        print(f"   View: https://arweave.net/{tx.id}")
        print(f"   Explorer: https://viewblock.io/arweave/tx/{tx.id}")
        return tx.id
    except Exception as e:
        print(f"\n❌ Upload failed: {e}")
        return None


def deploy_all():
    """Deploy all core files to Arweave."""
    print("\n" + "=" * 50)
    print("🚀 FULL DEPLOYMENT")
    print("=" * 50)
    
    # Load wallet
    wallet = arweave.Wallet(WALLET_PATH)
    print(f"💼 Wallet: {wallet.address[:20]}...")
    print(f"💰 Balance: {wallet.balance} AR")
    
    results = []
    
    for file_info in DEPLOY_FILES:
        tx_id = upload_file(wallet, file_info)
        results.append({
            "file": file_info["path"],
            "tx_id": tx_id,
            "success": tx_id is not None
        })
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 DEPLOYMENT SUMMARY")
    print("=" * 50)
    
    success_count = sum(1 for r in results if r["success"])
    print(f"Uploaded: {success_count}/{len(results)}")
    
    for r in results:
        status = "✅" if r["success"] else "❌"
        tx = r["tx_id"] or "failed"
        print(f"  {status} {r['file']}: {tx}")
    
    # Save results
    results_file = PROJECT_ROOT / "deployment_results.json"
    with open(results_file, "w") as f:
        json.dump({
            "deployed_at": datetime.now().isoformat(),
            "wallet": wallet.address,
            "files": results
        }, f, indent=2)
    print(f"\n💾 Results saved to: {results_file}")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Deploy AO World Engine to Arweave")
    parser.add_argument("--test", action="store_true", help="Run test upload only")
    parser.add_argument("--deploy", action="store_true", help="Deploy all core files")
    args = parser.parse_args()
    
    if args.test:
        upload_test()
    elif args.deploy:
        deploy_all()
    else:
        print("Usage:")
        print("  python deploy_to_arweave.py --test    # Test upload")
        print("  python deploy_to_arweave.py --deploy  # Full deployment")

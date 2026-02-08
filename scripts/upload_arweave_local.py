#!/usr/bin/env python3
"""
Upload simulation data directly to Arweave using local wallet.

This script uploads:
- Nature pack (wildlife, ecosystem)
- Utilities (power, water, gas, internet)
- Services (mail, delivery, food, news)
- World codec (base + extensions)

Usage:
    python3 scripts/upload_arweave_local.py

Requires:
    pip install arweave-python-client
    Wallet at $ARWEAVE_WALLET_PATH
"""
import os
import sys
import json
import glob
import hashlib
import tempfile
from datetime import datetime

# Configuration
WALLET_PATH = os.path.join(os.path.dirname(__file__), "../../$ARWEAVE_WALLET_PATH")
DATA_DIR = os.path.join(os.path.dirname(__file__), "../data")
RESULTS_FILE = os.path.join(os.path.dirname(__file__), "../data/arweave_uploads.json")

# Data categories to upload
DATA_CATEGORIES = {
    "nature": {
        "path": "nature",
        "type": "nature_data",
        "description": "Wildlife and ecosystem data"
    },
    "utilities": {
        "path": "utilities",
        "type": "utilities_data",
        "description": "Power, water, gas, internet infrastructure"
    },
    "services": {
        "path": "services",
        "type": "services_data",
        "description": "Mail, delivery, food, news systems"
    },
}

def load_existing_results():
    """Load previously uploaded transaction IDs."""
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'r') as f:
            return json.load(f)
    return {"uploads": {}, "version": "1.0.0", "last_upload": None}

def get_file_hash(filepath):
    """Get MD5 hash of file for detecting changes."""
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def upload_to_arweave(data: dict, tags: list, wallet) -> dict:
    """
    Upload JSON data to Arweave using local wallet.
    Returns {"success": bool, "tx_id": str, "error": str}
    """
    import arweave
    
    payload = json.dumps(data, separators=(',', ':')).encode('utf-8')
    payload_size = len(payload)
    
    print(f"      Payload: {payload_size} bytes")
    
    if payload_size > 100 * 1024:
        print(f"      ⚠️  Over 100KB free tier")
    
    try:
        # Create transaction
        tx = arweave.Transaction(wallet, data=payload)
        
        # Add default tags
        tx.add_tag("App-Name", "AO-World-Engine")
        tx.add_tag("Content-Type", "application/json")
        
        # Add custom tags
        for tag in tags:
            tx.add_tag(tag["name"], tag["value"])
        
        # Sign and submit
        tx.sign()
        tx.send()
        
        if tx.id:
            return {"success": True, "tx_id": tx.id}
        return {"success": False, "error": "No transaction ID returned"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def upload_file(filepath: str, category: str, existing: dict, wallet) -> dict:
    """Upload a single JSON file to Arweave."""
    filename = os.path.basename(filepath)
    file_key = f"{category}/{filename}"
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    file_hash = get_file_hash(filepath)
    
    # Check if already uploaded with same hash
    prev = existing.get("uploads", {}).get(file_key, {})
    if prev.get("hash") == file_hash and prev.get("tx_id"):
        print(f"  ⏭️  {filename} (unchanged, skipping)")
        return {
            "file_key": file_key,
            "filename": filename,
            "skipped": True,
            "success": True,
            "tx_id": prev["tx_id"],
            "hash": file_hash
        }
    
    # Build tags
    cat_info = DATA_CATEGORIES.get(category, {})
    tags = [
        {"name": "Type", "value": cat_info.get("type", "simulation_data")},
        {"name": "Category", "value": category},
        {"name": "Filename", "value": filename},
        {"name": "Hash", "value": file_hash},
        {"name": "Version", "value": "2.0.0"},
        {"name": "Uploaded-At", "value": datetime.now().isoformat()},
    ]
    
    if prev.get("tx_id"):
        tags.append({"name": "Previous-Version", "value": prev["tx_id"]})
    
    print(f"  📤 Uploading {filename} ({os.path.getsize(filepath) / 1024:.1f}KB)...")
    result = upload_to_arweave(data, tags, wallet)
    
    if result["success"]:
        print(f"     ✅ TX: {result['tx_id']}")
        print(f"        https://viewblock.io/arweave/tx/{result['tx_id']}")
    else:
        print(f"     ❌ Error: {result.get('error')}")
    
    return {
        "file_key": file_key,
        "filename": filename,
        "category": category,
        "size_bytes": os.path.getsize(filepath),
        "hash": file_hash,
        "previous_tx": prev.get("tx_id"),
        **result
    }

def main():
    print("=" * 60)
    print("AO World Engine - Direct Arweave Upload")
    print("=" * 60)
    
    # Check for arweave library
    try:
        import arweave
    except ImportError:
        print("\n❌ arweave-python-client not installed")
        print("   Run: pip install arweave-python-client")
        sys.exit(1)
    
    # Check for wallet
    if not os.path.exists(WALLET_PATH):
        print(f"\n❌ Wallet not found: {WALLET_PATH}")
        sys.exit(1)
    
    # Load wallet
    wallet = arweave.Wallet(WALLET_PATH)
    print(f"\n🔑 Wallet: {wallet.address}")
    print(f"   Balance: {wallet.balance} AR")
    
    if wallet.balance == 0:
        print("\n⚠️  Wallet has 0 balance. Uploads under 100KB are free via bundlers.")
    
    # Load existing
    existing = load_existing_results()
    print(f"\n📌 Previous upload: {existing.get('last_upload', 'never')}")
    
    all_results = {
        "version": "2.0.0",
        "uploaded_at": datetime.now().isoformat(),
        "wallet": wallet.address,
        "uploads": {}
    }
    
    total_files = 0
    total_uploaded = 0
    total_skipped = 0
    
    # Process each category
    for category, info in DATA_CATEGORIES.items():
        category_path = os.path.join(DATA_DIR, info["path"])
        
        if not os.path.exists(category_path):
            print(f"\n⚠️  Category '{category}' not found: {category_path}")
            continue
        
        json_files = glob.glob(os.path.join(category_path, "*.json"))
        if not json_files:
            continue
        
        print(f"\n📦 {category.upper()}: {info['description']}")
        print(f"   Found {len(json_files)} files")
        
        for filepath in sorted(json_files):
            result = upload_file(filepath, category, existing, wallet)
            all_results["uploads"][result["file_key"]] = result
            total_files += 1
            
            if result.get("skipped"):
                total_skipped += 1
            elif result.get("success"):
                total_uploaded += 1
    
    # Also upload the world_codec.json
    world_codec_path = os.path.join(DATA_DIR, "world_codec.json")
    if os.path.exists(world_codec_path):
        print(f"\n📦 WORLD CODEC")
        result = upload_file(world_codec_path, "codec", existing, wallet)
        all_results["uploads"][result["file_key"]] = result
        total_files += 1
        if result.get("skipped"):
            total_skipped += 1
        elif result.get("success"):
            total_uploaded += 1
    
    # Save results
    all_results["last_upload"] = datetime.now().isoformat()
    with open(RESULTS_FILE, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\n💾 Saved results to: {RESULTS_FILE}")
    
    # Summary
    failed = total_files - total_uploaded - total_skipped
    
    print("\n" + "=" * 60)
    print("UPLOAD SUMMARY")
    print("=" * 60)
    print(f"Wallet:          {wallet.address}")
    print(f"Total files:     {total_files}")
    print(f"Uploaded:        {total_uploaded}")
    print(f"Skipped (cache): {total_skipped}")
    if failed > 0:
        print(f"Failed:          {failed}")
    print("=" * 60)
    
    # List successful TXs
    if total_uploaded > 0:
        print("\n📝 Transactions:")
        for key, data in all_results["uploads"].items():
            if data.get("success") and not data.get("skipped"):
                print(f"   {key}: {data.get('tx_id', 'N/A')}")

if __name__ == "__main__":
    main()

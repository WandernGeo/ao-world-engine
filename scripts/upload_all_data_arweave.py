#!/usr/bin/env python3
"""
Upload ALL simulation data to Arweave.

This script uploads:
- Nature pack (wildlife, ecosystem)
- Utilities (power, water, gas, internet)
- Services (mail, delivery, food, news)
- World codec (base + extensions)

Usage:
    python3 scripts/upload_all_data_arweave.py

Requires:
    - arweave-uploader service running
"""
import os
import sys
import json
import glob
import hashlib
import requests
from datetime import datetime

# Configuration
UPLOADER_URL = "https://arweave-uploader-zdku5kri5a-uc.a.run.app/upload"
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
    "behaviors": {
        "path": "behaviors",
        "type": "behaviors_data",
        "description": "NPC behavior patterns"
    }
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

def upload_to_arweave(data: dict, tags: list) -> dict:
    """
    Upload JSON data to Arweave.
    Returns {"success": bool, "tx_id": str, "error": str}
    """
    try:
        response = requests.post(
            UPLOADER_URL,
            json={
                "data": data,
                "tags": tags
            },
            timeout=60
        )
        result = response.json()
        if result.get("id"):
            return {"success": True, "tx_id": result["id"]}
        return {"success": False, "error": result.get("error", "Unknown error")}
    except Exception as e:
        return {"success": False, "error": str(e)}

def upload_file(filepath: str, category: str, existing: dict) -> dict:
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
            "tx_id": prev["tx_id"],
            "hash": file_hash
        }
    
    # Build tags
    cat_info = DATA_CATEGORIES.get(category, {})
    tags = [
        {"name": "Content-Type", "value": "application/json"},
        {"name": "App-Name", "value": "AO-World-Engine"},
        {"name": "Type", "value": cat_info.get("type", "simulation_data")},
        {"name": "Category", "value": category},
        {"name": "Filename", "value": filename},
        {"name": "Hash", "value": file_hash},
        {"name": "Uploaded-At", "value": datetime.now().isoformat()},
    ]
    
    if prev.get("tx_id"):
        tags.append({"name": "Previous-Version", "value": prev["tx_id"]})
    
    print(f"  📤 Uploading {filename} ({os.path.getsize(filepath) / 1024:.1f}KB)...")
    result = upload_to_arweave(data, tags)
    
    if result["success"]:
        print(f"     ✅ TX: {result['tx_id']}")
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
    print("AO World Engine - Full Data Upload to Arweave")
    print("=" * 60)
    
    # Load existing
    existing = load_existing_results()
    print(f"\n📌 Previous upload: {existing.get('last_upload', 'never')}")
    
    all_results = {
        "version": "2.0.0",
        "uploaded_at": datetime.now().isoformat(),
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
            result = upload_file(filepath, category, existing)
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
        result = upload_file(world_codec_path, "codec", existing)
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
    print(f"Total files:     {total_files}")
    print(f"Uploaded:        {total_uploaded}")
    print(f"Skipped (cache): {total_skipped}")
    if failed > 0:
        print(f"Failed:          {failed}")
    print("=" * 60)
    
    # Generate GraphQL query
    print("""
📝 GraphQL Query (all uploads):
```graphql
{
  transactions(
    tags: [
      { name: "App-Name", values: ["AO-World-Engine"] }
    ]
    first: 100
  ) {
    edges {
      node {
        id
        tags { name value }
      }
    }
  }
}
```
""")

if __name__ == "__main__":
    main()

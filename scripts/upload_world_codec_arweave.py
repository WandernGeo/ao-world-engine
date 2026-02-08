#!/usr/bin/env python3
"""
Upload ALL World Codec chunks to Arweave with versioning support.

Each upload:
1. Creates a new transaction with version tags
2. References previous version (if exists)
3. Updates the manifest/index

Usage:
    python3 scripts/upload_world_codec_arweave.py

Requires:
    - Arweave wallet at $ARWEAVE_WALLET_PATH
    - arweave-uploader service running or use bundlr/turbo
"""
import os
import sys
import json
import glob
import hashlib
import requests
from datetime import datetime

# Configuration
WALLET_PATH = os.path.join(os.path.dirname(__file__), "../../$ARWEAVE_WALLET_PATH")
UPLOADER_URL = "https://arweave-uploader-zdku5kri5a-uc.a.run.app/upload"
CHUNKS_DIR = os.path.join(os.path.dirname(__file__), "../data/codec_chunks")
TRANSACTION_LOG = os.path.join(os.path.dirname(__file__), "../docs/ARWEAVE_TRANSACTION_LOG.md")
RESULTS_FILE = os.path.join(os.path.dirname(__file__), "../data/world_codec_arweave.json")

# Arweave gateways
GATEWAYS = [
    "https://arweave.net",
    "https://g8way.io",
    "https://ar-io.dev"
]

def load_existing_results():
    """Load previously uploaded transaction IDs."""
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'r') as f:
            return json.load(f)
    return {"chunks": {}, "manifest": None, "version": "0.0.0"}

def get_next_version(current):
    """Increment patch version."""
    parts = current.split(".")
    parts[-1] = str(int(parts[-1]) + 1)
    return ".".join(parts)

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

def upload_chunk(filepath: str, existing: dict, version: str) -> dict:
    """Upload a single chunk file to Arweave."""
    filename = os.path.basename(filepath)
    chunk_key = filename.replace(".json", "")
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Get previous version reference
    prev_tx = existing.get("chunks", {}).get(chunk_key, {}).get("tx_id")
    
    # Build tags
    tags = [
        {"name": "Content-Type", "value": "application/json"},
        {"name": "App-Name", "value": "AO-World-Engine"},
        {"name": "Type", "value": "world_codec_chunk"},
        {"name": "Chunk-Name", "value": chunk_key},
        {"name": "Version", "value": version},
        {"name": "Uploaded-At", "value": datetime.now().isoformat()},
    ]
    
    if prev_tx:
        tags.append({"name": "Previous-Version", "value": prev_tx})
    
    # Add category from manifest if available
    manifest_path = os.path.join(CHUNKS_DIR, "manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        for chunk in manifest.get("chunks", []):
            if chunk.get("id") == chunk_key.replace("world_codec_", "chunk_"):
                tags.append({"name": "Category", "value": chunk.get("category", "unknown")})
                break
    
    print(f"  📤 Uploading {filename} ({os.path.getsize(filepath) / 1024:.1f}KB)...")
    result = upload_to_arweave(data, tags)
    
    if result["success"]:
        print(f"     ✅ TX: {result['tx_id']}")
    else:
        print(f"     ❌ Error: {result.get('error')}")
    
    return {
        "chunk_key": chunk_key,
        "filename": filename,
        "size_bytes": os.path.getsize(filepath),
        "version": version,
        "previous_tx": prev_tx,
        **result
    }

def update_transaction_log(results: dict):
    """Append new uploads to the transaction log."""
    log_entry = f"""
---

## World Codec Chunks (Uploaded {datetime.now().strftime('%Y-%m-%d %H:%M')})

Version: **{results['version']}**

| Chunk | Category | Size | TX ID |
|-------|----------|------|-------|
"""
    
    for chunk_key, data in results["chunks"].items():
        if data.get("success"):
            tx_id = data["tx_id"]
            size = data.get("size_bytes", 0) / 1024
            category = chunk_key.split("_")[2] if len(chunk_key.split("_")) > 2 else "core"
            log_entry += f"| {chunk_key} | {category} | {size:.1f}KB | `{tx_id[:20]}...` |\n"
    
    log_entry += f"""
### GraphQL Query (all chunks)
```graphql
{{
  transactions(
    tags: [
      {{ name: "App-Name", values: ["AO-World-Engine"] }}
      {{ name: "Type", values: ["world_codec_chunk"] }}
      {{ name: "Version", values: ["{results['version']}"] }}
    ]
  ) {{
    edges {{
      node {{
        id
        tags {{ name value }}
      }}
    }}
  }}
}}
```
"""
    
    with open(TRANSACTION_LOG, 'a') as f:
        f.write(log_entry)
    
    print(f"\n📋 Updated transaction log: {TRANSACTION_LOG}")

def main():
    print("=" * 60)
    print("AO World Engine - Complete Arweave Upload")
    print("=" * 60)
    
    # Load existing
    existing = load_existing_results()
    new_version = get_next_version(existing.get("version", "1.0.0"))
    
    print(f"\n📌 Previous version: {existing.get('version', 'none')}")
    print(f"📌 New version: {new_version}")
    
    # Find all chunk files
    chunk_files = sorted(glob.glob(os.path.join(CHUNKS_DIR, "world_codec_*.json")))
    print(f"\n📦 Found {len(chunk_files)} chunk files")
    
    # Upload each chunk
    results = {
        "version": new_version,
        "uploaded_at": datetime.now().isoformat(),
        "chunks": {},
        "manifest": None
    }
    
    for filepath in chunk_files:
        result = upload_chunk(filepath, existing, new_version)
        results["chunks"][result["chunk_key"]] = result
    
    # Also upload the base world_codec.json
    base_codec = os.path.join(CHUNKS_DIR, "../world_codec.json")
    if os.path.exists(base_codec):
        print(f"\n  📤 Uploading base world_codec.json...")
        with open(base_codec, 'r') as f:
            data = json.load(f)
        
        tags = [
            {"name": "Content-Type", "value": "application/json"},
            {"name": "App-Name", "value": "AO-World-Engine"},
            {"name": "Type", "value": "world_codec_base"},
            {"name": "Version", "value": new_version},
        ]
        
        result = upload_to_arweave(data, tags)
        if result["success"]:
            print(f"     ✅ TX: {result['tx_id']}")
            results["base_codec"] = result["tx_id"]
    
    # Upload manifest
    manifest_path = os.path.join(CHUNKS_DIR, "manifest.json")
    if os.path.exists(manifest_path):
        print(f"\n  📤 Uploading manifest...")
        with open(manifest_path, 'r') as f:
            manifest_data = json.load(f)
        
        # Add chunk transaction IDs to manifest
        manifest_data["arweave_txs"] = {
            k: v.get("tx_id") for k, v in results["chunks"].items() if v.get("success")
        }
        manifest_data["version"] = new_version
        
        tags = [
            {"name": "Content-Type", "value": "application/json"},
            {"name": "App-Name", "value": "AO-World-Engine"},
            {"name": "Type", "value": "world_codec_manifest"},
            {"name": "Version", "value": new_version},
        ]
        
        result = upload_to_arweave(manifest_data, tags)
        if result["success"]:
            print(f"     ✅ Manifest TX: {result['tx_id']}")
            results["manifest"] = result["tx_id"]
    
    # Save results
    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Saved results to: {RESULTS_FILE}")
    
    # Update transaction log
    update_transaction_log(results)
    
    # Summary
    successful = sum(1 for v in results["chunks"].values() if v.get("success"))
    failed = len(results["chunks"]) - successful
    
    print("\n" + "=" * 60)
    print("UPLOAD SUMMARY")
    print("=" * 60)
    print(f"Version: {new_version}")
    print(f"Chunks uploaded: {successful}/{len(results['chunks'])}")
    if failed > 0:
        print(f"Failed: {failed}")
    print(f"Manifest: {results.get('manifest', 'N/A')}")
    print("=" * 60)

if __name__ == "__main__":
    main()

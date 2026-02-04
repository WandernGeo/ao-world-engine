#!/usr/bin/env python3
"""
Upload NPC chunks to Arweave via the wandern-arweave-uploader service.
Creates a manifest that clients can discover via Arweave GraphQL tags.
"""

import json
import requests
from pathlib import Path
from datetime import datetime

# Arweave uploader endpoint
UPLOADER_URL = "https://wandern-arweave-uploader-1071951656531.us-central1.run.app/"

# NPC data path
CHUNKS_DIR = Path("data/npc_chunks")

def upload_chunk(chunk_data: dict, chunk_name: str, tags: list = None) -> str:
    """Upload a single chunk to Arweave."""
    if tags is None:
        tags = []
    
    default_tags = [
        {"name": "App-Name", "value": "AO-World-Engine"},
        {"name": "Content-Type", "value": "application/json"},
        {"name": "Type", "value": "npc-data"},
        {"name": "Chunk", "value": chunk_name},
        {"name": "Version", "value": "2.0.0"},
        {"name": "Schema", "value": "full_profile"}
    ]
    
    all_tags = default_tags + tags
    
    payload = {
        "data": chunk_data,
        "tags": all_tags,
        "content_type": "application/json"
    }
    
    print(f"📤 Uploading {chunk_name}...")
    try:
        response = requests.post(UPLOADER_URL, json=payload, timeout=180)
        result = response.json()
        
        if "tx_id" in result and not result["tx_id"].startswith("pending_"):
            print(f"  ✅ TX: {result['tx_id']}")
            return result["tx_id"]
        else:
            print(f"  ⚠️ Pending: {result.get('tx_id', 'unknown')}")
            return result.get("tx_id")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return None

def main():
    print("🚀 AO World Engine - Arweave NPC Upload v2.0")
    print("=" * 50)
    
    manifest_path = CHUNKS_DIR / "manifest.json"
    
    if not manifest_path.exists():
        print("❌ No manifest found. Run generate_10k_npcs.py first.")
        return
    
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    print(f"📦 Found {manifest['total_chunks']} chunks totaling {manifest['total_npcs']} NPCs")
    print(f"   Schema: {manifest.get('schema', 'basic')}")
    print()
    
    # Upload all chunks (or specify a range)
    upload_results = []
    num_chunks = len(manifest["chunks"])
    
    # Upload first 20 chunks for now (~780 NPCs with full profiles)
    for chunk_info in manifest["chunks"][:20]:
        chunk_path = CHUNKS_DIR / chunk_info["file"]
        with open(chunk_path) as f:
            chunk_data = json.load(f)
        
        chunk_size = chunk_path.stat().st_size
        if chunk_size > 100 * 1024:
            print(f"  ⚠️ {chunk_info['file']} exceeds 100KB ({chunk_size/1024:.1f}KB) - skipping")
            continue
        
        tx_id = upload_chunk(chunk_data, chunk_info["id"], [
            {"name": "NPC-Count", "value": str(chunk_info["npc_count"])},
            {"name": "NPC-Range", "value": chunk_data["_meta"]["npc_id_range"]}
        ])
        
        if tx_id:
            upload_results.append({
                "chunk_id": chunk_info["id"],
                "tx_id": tx_id,
                "npc_count": chunk_info["npc_count"],
                "npc_range": chunk_data["_meta"]["npc_id_range"]
            })
    
    # Create and upload manifest
    if upload_results:
        print("\n📋 Creating manifest...")
        arweave_manifest = {
            "type": "npc-manifest",
            "version": "2.0.0",
            "schema": "full_profile",
            "created_at": datetime.utcnow().isoformat(),
            "total_npcs": sum(r["npc_count"] for r in upload_results),
            "total_chunks": len(upload_results),
            "chunks": upload_results
        }
        
        manifest_tx = upload_chunk(arweave_manifest, "manifest", [
            {"name": "Type", "value": "npc-manifest"},
            {"name": "Total-NPCs", "value": str(arweave_manifest["total_npcs"])}
        ])
        
        print(f"\n📋 Manifest TX: {manifest_tx}")
        print(f"   Query with: App-Name=AO-World-Engine, Type=npc-manifest")
    
    print("\n" + "=" * 50)
    print("📊 Upload Summary")
    print("=" * 50)
    
    total_npcs = sum(r["npc_count"] for r in upload_results)
    print(f"✅ Uploaded {len(upload_results)} chunks ({total_npcs} NPCs)")
    
    # Save results
    results_path = CHUNKS_DIR / "arweave_uploads.json"
    with open(results_path, 'w') as f:
        json.dump({
            "uploaded_at": datetime.utcnow().isoformat(),
            "version": "2.0.0",
            "manifest_tx": manifest_tx if upload_results else None,
            "chunks": upload_results,
            "total_npcs": total_npcs
        }, f, indent=2)
    print(f"\n💾 Results saved to: {results_path}")

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()

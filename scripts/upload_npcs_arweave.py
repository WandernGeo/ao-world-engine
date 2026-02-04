#!/usr/bin/env python3
"""
Upload NPC chunks to Arweave via the wandern-arweave-uploader service.
Uploads in chunks of <100KB for free tier.
"""

import json
import requests
from pathlib import Path

# Arweave uploader endpoint
UPLOADER_URL = "https://wandern-arweave-uploader-1071951656531.us-central1.run.app/"

# NPC data path
NPC_DATA = Path("data/npc_chunks/first_800_npcs.json")
CHUNKS_DIR = Path("data/npc_chunks")

def upload_chunk(chunk_data: dict, chunk_name: str, tags: list = None) -> str:
    """Upload a single chunk to Arweave."""
    if tags is None:
        tags = []
    
    # Add default tags
    default_tags = [
        {"name": "App-Name", "value": "AO-World-Engine"},
        {"name": "Content-Type", "value": "application/json"},
        {"name": "Type", "value": "npc-data"},
        {"name": "Chunk", "value": chunk_name},
        {"name": "Version", "value": "1.0"}
    ]
    
    all_tags = default_tags + tags
    
    payload = {
        "data": chunk_data,
        "tags": all_tags,
        "content_type": "application/json"
    }
    
    print(f"📤 Uploading {chunk_name}...")
    try:
        response = requests.post(UPLOADER_URL, json=payload, timeout=120)
        result = response.json()
        
        if "tx_id" in result:
            print(f"  ✅ Success! TX: {result['tx_id']}")
            print(f"  🔗 https://arweave.net/{result['tx_id']}")
            return result["tx_id"]
        else:
            print(f"  ❌ Error: {result}")
            return None
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return None

def main():
    print("🚀 AO World Engine - Arweave NPC Upload")
    print("=" * 50)
    
    # Check if we should upload individual chunks or combined
    manifest_path = CHUNKS_DIR / "manifest.json"
    
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        print(f"📦 Found {manifest['total_chunks']} chunks totaling {manifest['total_npcs']} NPCs")
        print()
        
        # Upload first 10 chunks (about 840 NPCs for ~83KB each)
        upload_results = []
        for chunk_info in manifest["chunks"][:10]:
            chunk_path = CHUNKS_DIR / chunk_info["file"]
            with open(chunk_path) as f:
                chunk_data = json.load(f)
            
            chunk_size = chunk_path.stat().st_size
            print(f"\n📄 {chunk_info['file']}: {chunk_info['npc_count']} NPCs, {chunk_size/1024:.1f}KB")
            
            if chunk_size > 100 * 1024:
                print("  ⚠️ Chunk exceeds 100KB limit - skipping")
                continue
            
            tx_id = upload_chunk(chunk_data, chunk_info["id"], [
                {"name": "NPC-Count", "value": str(chunk_info["npc_count"])},
                {"name": "NPC-Range", "value": chunk_data["_meta"]["npc_id_range"]}
            ])
            
            if tx_id:
                upload_results.append({
                    "chunk": chunk_info["id"],
                    "tx_id": tx_id,
                    "npc_count": chunk_info["npc_count"]
                })
        
        print("\n" + "=" * 50)
        print("📊 Upload Summary")
        print("=" * 50)
        
        total_npcs = sum(r["npc_count"] for r in upload_results)
        print(f"✅ Uploaded {len(upload_results)} chunks ({total_npcs} NPCs)")
        
        for r in upload_results:
            print(f"  - {r['chunk']}: {r['tx_id']}")
        
        # Save results
        results_path = CHUNKS_DIR / "arweave_uploads.json"
        with open(results_path, 'w') as f:
            json.dump({
                "uploaded_at": "2026-02-04",
                "chunks": upload_results,
                "total_npcs": total_npcs
            }, f, indent=2)
        print(f"\n💾 Results saved to: {results_path}")
        
    else:
        print("❌ No manifest found. Run generate_10k_npcs.py first.")

if __name__ == "__main__":
    main()

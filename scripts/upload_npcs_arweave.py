#!/usr/bin/env python3
"""
Upload Founding NPCs to Arweave via Cloud Function
====================================================

Uses the wandern-arweave-uploader Cloud Function which handles
wallet signing and Turbo bundler integration.

Usage:
  python3 upload_npcs_arweave.py --dry-run     # Test without uploading
  python3 upload_npcs_arweave.py               # Actually upload
"""

import os
import sys
import json
import hashlib
import requests
import argparse
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.founding_npcs import FOUNDING_NPCS, create_npc_for_arweave

# Cloud Function that handles Turbo/Arweave uploads
ARWEAVE_UPLOADER_URL = os.environ.get(
    "ARWEAVE_UPLOADER_URL",
    "https://arweave-uploader-zdku5kri5a-uc.a.run.app"
)

ARWEAVE_GATEWAY = "https://arweave.net"


def upload_via_cloud_function(data: dict, tags: list, dry_run: bool = False) -> str:
    """
    Upload data to Arweave via the wandern-arweave-uploader Cloud Function.
    
    The Cloud Function handles wallet signing and Turbo bundler integration.
    
    Returns transaction ID.
    """
    if dry_run:
        # Generate deterministic fake tx_id for testing
        json_data = json.dumps(data, separators=(',', ':'))
        fake_tx = hashlib.sha256(json_data.encode()).hexdigest()[:43]
        return f"DRY_RUN_{fake_tx}"
    
    try:
        payload = {
            "data": json.dumps(data),
            "tags": tags,
            "content_type": "application/json"
        }
        
        response = requests.post(
            ARWEAVE_UPLOADER_URL,
            json=payload,
            timeout=60
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            tx_id = result.get("tx_id") or result.get("id") or result.get("txId")
            return tx_id
        else:
            print(f"  ❌ Upload failed: {response.status_code}")
            print(f"     {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"  ❌ Upload error: {e}")
        return None


def verify_on_arweave(tx_id: str) -> bool:
    """Verify transaction exists on Arweave gateway."""
    if tx_id.startswith("DRY_RUN"):
        return True
    
    try:
        response = requests.get(f"{ARWEAVE_GATEWAY}/{tx_id}", timeout=10)
        return response.status_code == 200
    except:
        return False


def main():
    parser = argparse.ArgumentParser(description="Upload Founding NPCs to Arweave")
    parser.add_argument("--dry-run", action="store_true", help="Test without uploading")
    args = parser.parse_args()
    
    print("=" * 60)
    print("UPLOAD FOUNDING NPCS TO ARWEAVE")
    print("=" * 60)
    print(f"Cloud Function: {ARWEAVE_UPLOADER_URL}")
    print(f"Mode: {'DRY RUN (no actual upload)' if args.dry_run else 'LIVE UPLOAD'}")
    print()
    
    results = []
    total_bytes = 0
    
    for npc_key, npc_data in FOUNDING_NPCS.items():
        arweave_ready = create_npc_for_arweave(npc_key, npc_data)
        
        profile_json = json.dumps(arweave_ready["profile"], separators=(',', ':'))
        profile_bytes = len(profile_json.encode('utf-8'))
        
        print(f"📤 Uploading {npc_data['name']} ({profile_bytes} bytes)...")
        
        tx_id = upload_via_cloud_function(
            arweave_ready["profile"], 
            arweave_ready["tags"],
            dry_run=args.dry_run
        )
        
        if tx_id:
            print(f"   ✅ TX: {tx_id}")
            results.append({
                "npc_key": npc_key,
                "npc_id": npc_data["id"],
                "name": npc_data["name"],
                "tx_id": tx_id,
                "size_bytes": profile_bytes,
                "success": True
            })
            total_bytes += profile_bytes
        else:
            print(f"   ❌ Failed")
            results.append({
                "npc_key": npc_key,
                "npc_id": npc_data["id"],
                "name": npc_data["name"],
                "tx_id": None,
                "success": False
            })
    
    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    print(f"✅ Successful: {len(successful)}/{len(results)}")
    print(f"❌ Failed: {len(failed)}/{len(results)}")
    print(f"📦 Total uploaded: {total_bytes} bytes")
    print(f"💰 Cost: FREE (under 100KB per file)")
    
    # Save results
    output_file = "/Users/ram/Documents/wandern/ao-world-engine/data/arweave_upload_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "dry_run": args.dry_run,
            "uploader": ARWEAVE_UPLOADER_URL,
            "results": results,
            "summary": {
                "total": len(results),
                "successful": len(successful),
                "failed": len(failed),
                "total_bytes": total_bytes
            }
        }, f, indent=2)
    
    print(f"\n📁 Results saved to: {output_file}")
    
    if not args.dry_run and successful:
        print("\n🔍 View on Arweave:")
        for r in successful[:3]:
            print(f"   https://arweave.net/{r['tx_id']}")
        if len(successful) > 3:
            print(f"   ... and {len(successful) - 3} more")
    
    return len(failed) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

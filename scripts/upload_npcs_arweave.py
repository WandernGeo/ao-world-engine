#!/usr/bin/env python3
"""
Upload Founding NPCs to Arweave via Turbo Bundler
==================================================

Uses Turbo (ar.io) bundler - <100KB uploads are FREE!

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

# Turbo (ar.io) bundler - AO ecosystem recommended
TURBO_MAINNET = "https://up.arweave.net"
ARWEAVE_GATEWAY = "https://arweave.net"


def upload_to_turbo(data: bytes, tags: list, dry_run: bool = False) -> str:
    """
    Upload data to Arweave via Turbo bundler.
    
    For <100KB, this is FREE (no wallet required).
    
    Returns transaction ID.
    """
    if dry_run:
        # Generate deterministic fake tx_id for testing
        fake_tx = hashlib.sha256(data).hexdigest()[:43]
        return f"DRY_RUN_{fake_tx}"
    
    try:
        # Turbo expects multipart form or direct POST
        # For small uploads, we can use the simple endpoint
        headers = {
            "Content-Type": "application/octet-stream",
        }
        
        # Add tags as x-turbo-tag-{name} headers
        for tag in tags:
            header_name = f"x-turbo-tag-{tag['name'].lower().replace('-', '_')}"
            headers[header_name] = tag['value']
        
        response = requests.post(
            f"{TURBO_MAINNET}/v1/tx/arweave",
            data=data,
            headers=headers,
            timeout=60
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            return result.get("id") or result.get("txId") or result.get("tx_id")
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
    print(f"Bundler: Turbo (ar.io) - {TURBO_MAINNET}")
    print(f"Mode: {'DRY RUN (no actual upload)' if args.dry_run else 'LIVE UPLOAD'}")
    print()
    
    results = []
    total_bytes = 0
    
    for npc_key, npc_data in FOUNDING_NPCS.items():
        arweave_ready = create_npc_for_arweave(npc_key, npc_data)
        
        profile_json = json.dumps(arweave_ready["profile"], separators=(',', ':'))
        profile_bytes = profile_json.encode('utf-8')
        
        print(f"📤 Uploading {npc_data['name']} ({len(profile_bytes)} bytes)...")
        
        tx_id = upload_to_turbo(
            profile_bytes, 
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
                "size_bytes": len(profile_bytes),
                "success": True
            })
            total_bytes += len(profile_bytes)
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
            "bundler": TURBO_MAINNET,
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

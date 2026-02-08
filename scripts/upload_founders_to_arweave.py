#!/usr/bin/env python3
"""
Upload Updated Founding NPC Profiles to Arweave (v2 — Direct Upload)
====================================================================

Uses arweave-python-client locally with wallet.json to upload
all 12 founding NPC profiles (with updated visual_descriptions) to Arweave.

Each NPC profile is ~2KB, well within the <100KB free tier.

Usage:
    python3 scripts/upload_founders_to_arweave.py [--dry-run]
"""

import sys
import os
import json
import time
import argparse

# Add parent dirs to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'data'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

from data.founding_npcs import FOUNDING_NPCS
from api.founding_npcs import create_npc_for_arweave

# Wallet location
WALLET_PATH = os.path.join(os.path.dirname(__file__), '..', 'wallet.json')


def upload_npc_profile(npc_key: str, npc_data: dict, wallet, dry_run: bool = False) -> dict:
    """Upload a single NPC profile to Arweave using arweave-python-client."""
    import arweave

    # Prepare the Arweave-ready profile
    arweave_ready = create_npc_for_arweave(npc_key, npc_data)
    profile = arweave_ready["profile"]
    arw_tags = arweave_ready["tags"]

    # Add version tags
    arw_tags.append({"name": "Version", "value": "2.0"})
    arw_tags.append({"name": "Upload-Date", "value": time.strftime("%Y-%m-%d")})

    payload = json.dumps(profile, separators=(',', ':')).encode('utf-8')
    size_bytes = len(payload)

    print(f"  📦 {npc_key} ({npc_data['name']}): {size_bytes} bytes")
    has_vis = bool(npc_data.get("visual_description"))
    print(f"     visual_desc: {'✅ ' + npc_data.get('visual_description', '')[:70] + '...' if has_vis else '❌ MISSING'}")

    if dry_run:
        return {
            "npc_key": npc_key,
            "name": npc_data["name"],
            "size_bytes": size_bytes,
            "dry_run": True,
            "has_visual_description": has_vis
        }

    try:
        tx = arweave.Transaction(wallet, data=payload)

        for tag in arw_tags:
            tx.add_tag(tag["name"], tag["value"])

        tx.sign()
        tx.send()

        if tx.id:
            print(f"     ✅ TX: {tx.id}")
            print(f"     🔗 https://arweave.net/{tx.id}")
            return {
                "npc_key": npc_key,
                "npc_id": npc_data["id"],
                "name": npc_data["name"],
                "tx_id": tx.id,
                "size_bytes": size_bytes,
                "success": True,
                "arweave_url": f"https://arweave.net/{tx.id}"
            }
        else:
            print(f"     ❌ Transaction returned no ID")
            return {
                "npc_key": npc_key,
                "name": npc_data["name"],
                "success": False,
                "error": "No tx ID returned"
            }
    except Exception as e:
        print(f"     ❌ Error: {e}")
        return {
            "npc_key": npc_key,
            "name": npc_data["name"],
            "success": False,
            "error": str(e)
        }


def main():
    import arweave

    parser = argparse.ArgumentParser(description="Upload founding NPCs to Arweave")
    parser.add_argument("--dry-run", action="store_true", help="Preview without uploading")
    args = parser.parse_args()

    print("=" * 60)
    print("RE:ECHO City — Upload Founding NPCs to Arweave v2")
    print("=" * 60)

    # Load wallet
    if not os.path.exists(WALLET_PATH):
        print(f"❌ Wallet not found at {WALLET_PATH}")
        sys.exit(1)

    wallet = arweave.Wallet(WALLET_PATH)
    print(f"Wallet: {wallet.address}")
    print(f"NPCs to upload: {len(FOUNDING_NPCS)}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE UPLOAD'}")
    print("-" * 60)

    results = []

    for npc_key, npc_data in FOUNDING_NPCS.items():
        result = upload_npc_profile(npc_key, npc_data, wallet, dry_run=args.dry_run)
        results.append(result)
        if not args.dry_run:
            time.sleep(2)  # Rate limiting between uploads

    print("\n" + "=" * 60)
    print("UPLOAD SUMMARY")
    print("=" * 60)

    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success") and not r.get("dry_run")]

    if args.dry_run:
        has_desc = sum(1 for r in results if r.get("has_visual_description"))
        print(f"Total NPCs: {len(results)}")
        print(f"With visual_description: {has_desc}/{len(results)}")
        total_bytes = sum(r.get("size_bytes", 0) for r in results)
        print(f"Total size: {total_bytes:,} bytes ({total_bytes/1024:.1f} KB)")
    else:
        print(f"Successful: {len(successful)}/{len(results)}")
        print(f"Failed: {len(failed)}/{len(results)}")
        total_bytes = sum(r.get("size_bytes", 0) for r in successful)
        print(f"Total uploaded: {total_bytes:,} bytes ({total_bytes/1024:.1f} KB)")

    # Save results
    output_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'arweave_upload_results_v2.json')
    output = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "dry_run": args.dry_run,
        "wallet_address": wallet.address,
        "results": results,
        "summary": {
            "total": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "total_bytes": total_bytes
        }
    }

    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to: {output_file}")

    if failed:
        print("\n⚠️  FAILED UPLOADS:")
        for r in failed:
            print(f"  - {r['npc_key']}: {r.get('error', 'unknown')}")


if __name__ == "__main__":
    main()

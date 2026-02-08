#!/usr/bin/env python3
"""
Upload Codec Chunks to Arweave
==============================
Uploads all world_codec JSON files to Arweave for permanent storage.
"""

import sys, os, json, time, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

WALLET_PATH = os.path.join(os.path.dirname(__file__), '..', 'wallet.json')
CODEC_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'codec_chunks')


def upload_codec_chunk(filepath, wallet, dry_run=False):
    """Upload a single codec chunk to Arweave."""
    import arweave
    
    filename = os.path.basename(filepath)
    with open(filepath) as f:
        data = json.load(f)
    
    # Extract chunk metadata (may be dict or string)
    chunk_meta = data.get("_chunk", {})
    if isinstance(chunk_meta, str):
        chunk_id = chunk_meta
        category = "mixed"
    else:
        chunk_id = chunk_meta.get("id", filename.replace(".json", ""))
        category = chunk_meta.get("category", "unknown")
    
    payload = json.dumps(data, separators=(',', ':')).encode('utf-8')
    size_bytes = len(payload)
    
    print(f"  📦 {filename}: {size_bytes:,} bytes (category: {category})")
    
    if dry_run:
        return {
            "filename": filename,
            "chunk_id": chunk_id,
            "category": category,
            "size_bytes": size_bytes,
            "dry_run": True
        }
    
    tags = [
        {"name": "Content-Type", "value": "application/json"},
        {"name": "App-Name", "value": "AO-World-Engine"},
        {"name": "Type", "value": "world_codec_chunk"},
        {"name": "Chunk-Id", "value": chunk_id},
        {"name": "Category", "value": category},
        {"name": "Version", "value": "1.0"},
        {"name": "Upload-Date", "value": time.strftime("%Y-%m-%d")},
    ]
    
    try:
        tx = arweave.Transaction(wallet, data=payload)
        for tag in tags:
            tx.add_tag(tag["name"], tag["value"])
        tx.sign()
        tx.send()
        
        if tx.id:
            print(f"     ✅ TX: {tx.id}")
            return {
                "filename": filename,
                "chunk_id": chunk_id,
                "category": category,
                "size_bytes": size_bytes,
                "tx_id": tx.id,
                "arweave_url": f"https://arweave.net/{tx.id}",
                "success": True
            }
        else:
            print(f"     ❌ No TX ID")
            return {"filename": filename, "success": False, "error": "No tx ID"}
    except Exception as e:
        print(f"     ❌ Error: {e}")
        return {"filename": filename, "success": False, "error": str(e)}


def main():
    import arweave
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    # Find all codec files
    files = sorted([
        os.path.join(CODEC_DIR, f)
        for f in os.listdir(CODEC_DIR)
        if f.startswith("world_codec_") and f.endswith(".json")
    ])
    
    print(f"Found {len(files)} codec chunks")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE UPLOAD'}")
    print("-" * 60)
    
    wallet = arweave.Wallet(WALLET_PATH) if not args.dry_run else None
    if wallet:
        print(f"Wallet: {wallet.address}")
    
    results = []
    for fp in files:
        result = upload_codec_chunk(fp, wallet, dry_run=args.dry_run)
        results.append(result)
        if not args.dry_run:
            time.sleep(2)
    
    # Summary
    successful = [r for r in results if r.get("success")]
    total_bytes = sum(r.get("size_bytes", 0) for r in results)
    
    print(f"\nTotal: {len(results)} files, {total_bytes:,} bytes ({total_bytes/1024:.1f} KB)")
    if not args.dry_run:
        print(f"Uploaded: {len(successful)}/{len(results)}")
    
    # Save manifest
    output = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "dry_run": args.dry_run,
        "results": results,
        "summary": {"total": len(results), "successful": len(successful), "total_bytes": total_bytes}
    }
    
    out_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'arweave_codec_manifest.json')
    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"Manifest: {out_path}")


if __name__ == "__main__":
    main()

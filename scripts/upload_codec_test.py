#!/usr/bin/env python3
"""
Quick Arweave upload test for World Codec chunks.
Uses the existing wallet to upload to mainnet (small files are free via bundler).
"""
import json
import os
import glob
import arweave
import tempfile
from datetime import datetime

WALLET_PATH = "/Users/ram/Documents/wandern/wandern-back/arweave-wallet.json"
CHUNKS_DIR = "/Users/ram/Documents/wandern/ao-world-engine/data/codec_chunks"
RESULTS_FILE = "/Users/ram/Documents/wandern/ao-world-engine/data/world_codec_arweave_results.json"

def upload_chunk(wallet, filepath: str, is_testnet: bool = False) -> dict:
    """Upload a single chunk to Arweave."""
    filename = os.path.basename(filepath)
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    data_bytes = json.dumps(data, indent=2).encode()
    
    # Create transaction
    tx = arweave.Transaction(wallet, data=data_bytes)
    tx.add_tag("Content-Type", "application/json")
    tx.add_tag("App-Name", "AO-World-Engine")
    tx.add_tag("Type", "world_codec_chunk")
    tx.add_tag("Chunk-Name", filename.replace(".json", ""))
    tx.add_tag("Version", "2.1.0")
    tx.add_tag("Uploaded-At", datetime.now().isoformat())
    
    if is_testnet:
        tx.add_tag("Network", "testnet")
    
    # Sign
    tx.sign()
    
    print(f"  📦 {filename}")
    print(f"     Size: {len(data_bytes) / 1024:.1f}KB")
    print(f"     TX ID: {tx.id}")
    
    if not is_testnet:
        # Submit to network
        try:
            tx.send()
            print(f"     ✅ Uploaded!")
            return {"success": True, "tx_id": tx.id, "size": len(data_bytes)}
        except Exception as e:
            print(f"     ❌ Error: {e}")
            return {"success": False, "error": str(e), "tx_id": tx.id}
    else:
        print(f"     ⏸️  Testnet mode - not sending")
        return {"success": True, "tx_id": tx.id, "testnet": True, "size": len(data_bytes)}

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--testnet", action="store_true", help="Sign but don't send")
    parser.add_argument("--limit", type=int, default=3, help="Max chunks to upload")
    args = parser.parse_args()
    
    print("=" * 60)
    print("AO World Engine - Arweave Codec Upload")
    print("=" * 60)
    
    if args.testnet:
        print("🧪 TESTNET MODE - Will sign but not send\n")
    else:
        print("🚀 MAINNET MODE - Will upload permanently\n")
    
    # Load wallet
    print(f"📁 Loading wallet from {WALLET_PATH}")
    wallet = arweave.Wallet(WALLET_PATH)
    print(f"   Address: {wallet.address}")
    
    try:
        balance_ar = float(wallet.balance) / 1e12
        print(f"   Balance: {balance_ar:.6f} AR\n")
    except:
        print(f"   Balance: (could not fetch)\n")
    
    # Find chunks
    chunks = sorted(glob.glob(os.path.join(CHUNKS_DIR, "world_codec_*.json")))
    print(f"📦 Found {len(chunks)} chunks, uploading {min(len(chunks), args.limit)}\n")
    
    results = {
        "uploaded_at": datetime.now().isoformat(),
        "testnet": args.testnet,
        "chunks": {}
    }
    
    for i, chunk_path in enumerate(chunks[:args.limit]):
        result = upload_chunk(wallet, chunk_path, args.testnet)
        chunk_name = os.path.basename(chunk_path).replace(".json", "")
        results["chunks"][chunk_name] = result
        print()
    
    # Save results
    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"💾 Results saved to {RESULTS_FILE}")
    
    # Summary
    successful = sum(1 for v in results["chunks"].values() if v.get("success"))
    total_size = sum(v.get("size", 0) for v in results["chunks"].values())
    
    print("\n" + "=" * 60)
    print(f"Uploaded: {successful}/{len(results['chunks'])} chunks")
    print(f"Total size: {total_size / 1024:.1f}KB")
    print("=" * 60)

if __name__ == "__main__":
    main()

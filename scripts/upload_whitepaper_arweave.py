#!/usr/bin/env python3
"""
Upload AO World Engine Whitepaper to Arweave

Tags it for discoverability in the AO/Arweave ecosystem.
"""
import os
import json
import hashlib
from datetime import datetime

# Whitepaper content
WHITEPAPER_PATH = "/Users/ram/Documents/wandern/ao-world-engine/docs/WHITEPAPER.md"

def create_whitepaper_upload():
    """Create the upload bundle for the whitepaper."""
    
    # Read whitepaper
    with open(WHITEPAPER_PATH, 'r') as f:
        content = f.read()
    
    # Create content hash
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    
    # Arweave tags for discoverability
    tags = [
        {"name": "Content-Type", "value": "text/markdown"},
        {"name": "App-Name", "value": "AO-World-Engine"},
        {"name": "Type", "value": "Whitepaper"},
        {"name": "Title", "value": "AO World Engine: A Decentralized Simulation Framework"},
        {"name": "Version", "value": "1.0"},
        {"name": "Author", "value": "Wandern Geo"},
        {"name": "Date", "value": datetime.now().strftime("%Y-%m-%d")},
        {"name": "Content-Hash", "value": content_hash[:16]},
        {"name": "Keywords", "value": "AO,Arweave,simulation,NPC,AI,multiverse,permaweb"},
        {"name": "License", "value": "AGPL-3.0"},
        # Discovery tags
        {"name": "AO-World-Engine-Whitepaper", "value": "true"},
        {"name": "Ecosystem", "value": "Arweave,AO"},
    ]
    
    print("=== AO World Engine Whitepaper Upload ===")
    print(f"File: {WHITEPAPER_PATH}")
    print(f"Size: {len(content)} bytes")
    print(f"Hash: {content_hash[:16]}...")
    print(f"\nTags ({len(tags)}):")
    for tag in tags:
        print(f"  {tag['name']}: {tag['value']}")
    
    # For actual upload, use Irys (formerly Bundlr)
    print("\n=== Upload Command ===")
    print("Using Irys CLI:")
    print(f'irys upload "{WHITEPAPER_PATH}" \\')
    print('  --node https://node1.irys.xyz \\')
    print('  --wallet /path/to/wallet.json \\')
    for tag in tags:
        print(f'  --tag "{tag["name"]}" "{tag["value"]}" \\')
    
    # Alternative: Use ArweaveJS or Turbo
    print("\n=== Alternative: Turbo Upload ===")
    print("Using @ardrive/turbo-sdk in Node.js")
    print("""
const { TurboFactory } = require('@ardrive/turbo-sdk');
const fs = require('fs');

async function upload() {
  const turbo = TurboFactory.authenticated({ 
    privateKey: JSON.parse(fs.readFileSync('wallet.json')) 
  });
  
  const result = await turbo.uploadFile({
    fileStreamFactory: () => fs.createReadStream('%s'),
    fileSizeFactory: () => %d,
    dataItemOpts: {
      tags: %s
    }
  });
  
  console.log('Transaction ID:', result.id);
  console.log('View at: https://arweave.net/' + result.id);
}

upload();
""" % (WHITEPAPER_PATH, len(content), json.dumps(tags, indent=2)))
    
    return {
        "path": WHITEPAPER_PATH,
        "size": len(content),
        "hash": content_hash,
        "tags": tags
    }


def upload_via_existing_service():
    """Use the existing wandern-arweave-uploader service."""
    print("\n=== Using Existing GeoEcho Arweave Service ===")
    print("The wandern-arweave-uploader can be extended for documents.")
    print("\nQuick upload via Cloud Run service:")
    print("""
curl -X POST https://wandern-arweave-uploader-xxxxx.run.app/upload \\
  -H "Content-Type: application/json" \\
  -d '{
    "type": "whitepaper",
    "content": "<base64_encoded_markdown>",
    "tags": [
      {"name": "App-Name", "value": "AO-World-Engine"},
      {"name": "Type", "value": "Whitepaper"}
    ]
  }'
""")


if __name__ == "__main__":
    result = create_whitepaper_upload()
    upload_via_existing_service()
    
    print("\n=== Summary ===")
    print(f"Whitepaper ready for upload: {result['size']} bytes")
    print("Once uploaded, retrieve via GraphQL:")
    print("""
query {
  transactions(
    tags: [
      { name: "App-Name", values: ["AO-World-Engine"] },
      { name: "Type", values: ["Whitepaper"] }
    ]
  ) {
    edges { node { id } }
  }
}
""")

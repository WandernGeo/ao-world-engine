#!/usr/bin/env python3
"""Upload World Codec to Arweave."""

import os
import sys
import json
import requests
from datetime import datetime

# Cloud Function URL
ARWEAVE_UPLOADER_URL = os.environ.get(
    "ARWEAVE_UPLOADER_URL",
    "https://arweave-uploader-zdku5kri5a-uc.a.run.app"
)

def main():
    codec_path = os.path.join(os.path.dirname(__file__), "world_codec.json")
    
    with open(codec_path, "r") as f:
        codec = json.load(f)
    
    # Add metadata
    codec["_uploaded_at"] = datetime.now().isoformat()
    
    payload = {
        "data": json.dumps(codec),
        "tags": [
            {"name": "Content-Type", "value": "application/json"},
            {"name": "App-Name", "value": "AO-World-Engine"},
            {"name": "Type", "value": "world_codec"},
            {"name": "Version", "value": "1.0.0"}
        ],
        "content_type": "application/json"
    }
    
    print(f"📤 Uploading World Codec ({len(json.dumps(codec))} bytes)...")
    
    response = requests.post(ARWEAVE_UPLOADER_URL, json=payload, timeout=60)
    
    if response.status_code in [200, 201]:
        result = response.json()
        tx_id = result.get("tx_id") or result.get("id") or result.get("txId")
        print(f"   ✅ TX: {tx_id}")
        print(f"   🔗 https://arweave.net/{tx_id}")
        
        # Save result
        with open(os.path.join(os.path.dirname(__file__), "world_codec_tx.json"), "w") as f:
            json.dump({"tx_id": tx_id, "uploaded_at": datetime.now().isoformat()}, f)
        
        return tx_id
    else:
        print(f"   ❌ Failed: {response.status_code}")
        print(response.text[:200])
        return None

if __name__ == "__main__":
    main()

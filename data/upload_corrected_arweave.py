#!/usr/bin/env python3
"""
Upload World Codec and Corrected NPCs to Arweave
=================================================

Uploads the world_codec.json and all corrected founding NPC profiles
to Arweave via the wandern-arweave-uploader Cloud Function.
"""

import json
import requests
import os
from datetime import datetime

# Cloud Function URL
UPLOADER_URL = "$ARWEAVE_UPLOADER_URL"

# Import the corrected NPC data
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from founding_npcs import FOUNDING_NPCS, LOCATIONS

def upload_to_arweave(data: dict, tags: list, name: str) -> dict:
    """Upload data to Arweave via Cloud Function."""
    payload = {
        "direct_upload": True,
        "data": data,
        "tags": tags
    }
    
    print(f"📤 Uploading {name}...")
    try:
        response = requests.post(
            UPLOADER_URL,
            json=payload,
            timeout=60
        )
        result = response.json()
        if result.get("success"):
            print(f"   ✅ TX: {result.get('tx_id', 'pending')}")
            return result
        else:
            print(f"   ❌ Error: {result.get('error', 'Unknown')}")
            return result
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return {"error": str(e)}


def upload_world_codec():
    """Upload the World Codec dictionary to Arweave."""
    codec_path = os.path.join(os.path.dirname(__file__), "world_codec.json")
    
    with open(codec_path, "r") as f:
        codec = json.load(f)
    
    tags = [
        {"name": "Content-Type", "value": "application/json"},
        {"name": "App-Name", "value": "AO-World-Engine"},
        {"name": "Type", "value": "world_codec"},
        {"name": "Version", "value": "1.0.0"},
        {"name": "Uploaded-At", "value": datetime.now().isoformat()},
        {"name": "Description", "value": "Deterministic knowledge dictionary for RE:ECHO City"}
    ]
    
    return upload_to_arweave(codec, tags, "World Codec")


def upload_founding_npcs():
    """Upload all corrected founding NPC profiles to Arweave."""
    results = {}
    
    for npc_key, npc_data in FOUNDING_NPCS.items():
        # Create profile with metadata
        profile = {
            **npc_data,
            "geoecho_version": "2.0.0",  # Version 2 = corrected profiles
            "schema": "npc_semantic_profile_v2",
            "created_at": datetime.now().isoformat(),
            "is_founding": True,
            "universe": "reecho",
            "corrected": True  # Flag indicating this is the corrected version
        }
        
        # Convert morphology function result to dict if needed
        if callable(profile.get("morphology")):
            profile["morphology"] = profile["morphology"]()
        
        tags = [
            {"name": "Content-Type", "value": "application/json"},
            {"name": "App-Name", "value": "AO-World-Engine"},
            {"name": "Type", "value": "npc_profile"},
            {"name": "NPC-Id", "value": npc_data["id"]},
            {"name": "NPC-Key", "value": npc_key},
            {"name": "NPC-Name", "value": npc_data["name"]},
            {"name": "Generation", "value": "0"},
            {"name": "Is-Founding", "value": "true"},
            {"name": "Version", "value": "2.0.0"},
            {"name": "Corrected", "value": "true"},
            {"name": "Uploaded-At", "value": datetime.now().isoformat()}
        ]
        
        result = upload_to_arweave(profile, tags, f"NPC: {npc_data['name']}")
        results[npc_key] = result
    
    return results


def upload_locations():
    """Upload location definitions to Arweave."""
    locations_data = {
        "schema": "location_definitions_v1",
        "version": "1.0.0",
        "created_at": datetime.now().isoformat(),
        "locations": LOCATIONS
    }
    
    tags = [
        {"name": "Content-Type", "value": "application/json"},
        {"name": "App-Name", "value": "AO-World-Engine"},
        {"name": "Type", "value": "location_definitions"},
        {"name": "Version", "value": "1.0.0"},
        {"name": "Uploaded-At", "value": datetime.now().isoformat()}
    ]
    
    return upload_to_arweave(locations_data, tags, "Locations")


if __name__ == "__main__":
    print("RE:ECHO Arweave Upload - Corrected Data")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Upload World Codec
    print("\n📚 WORLD CODEC")
    print("-" * 30)
    codec_result = upload_world_codec()
    
    # Upload Locations
    print("\n🏙️ LOCATIONS")
    print("-" * 30)
    locations_result = upload_locations()
    
    # Upload all NPCs
    print("\n👤 FOUNDING NPCs (CORRECTED)")
    print("-" * 30)
    npc_results = upload_founding_npcs()
    
    # Summary
    print("\n" + "=" * 50)
    print("UPLOAD SUMMARY")
    print("=" * 50)
    
    successful = sum(1 for r in npc_results.values() if r.get("success"))
    print(f"World Codec: {'✅' if codec_result.get('success') else '❌'}")
    print(f"Locations: {'✅' if locations_result.get('success') else '❌'}")
    print(f"NPCs: {successful}/{len(FOUNDING_NPCS)} successful")
    
    # Save results
    all_results = {
        "uploaded_at": datetime.now().isoformat(),
        "world_codec": codec_result,
        "locations": locations_result,
        "npcs": npc_results
    }
    
    results_path = os.path.join(os.path.dirname(__file__), "..", "arweave_upload_results.json")
    with open(results_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"\nResults saved to: {results_path}")

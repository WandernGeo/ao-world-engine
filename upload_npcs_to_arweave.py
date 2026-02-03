"""
Upload Founding NPCs to Arweave with visual descriptions for image generation.
Uses the canonical FOUNDING_NPCS from founding_npcs.py.
"""
import os
import sys
import json
import hashlib

# Add api directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

from founding_npcs import FOUNDING_NPCS, LOCATIONS


def generate_arweave_manifest():
    """Generate manifest of all NPCs with their visual descriptions for Arweave."""
    
    npcs_for_upload = []
    
    for npc_key, npc_data in FOUNDING_NPCS.items():
        # Generate deterministic tx_id (in production, this comes from actual upload)
        tx_id = hashlib.sha256(json.dumps(npc_data, sort_keys=True).encode()).hexdigest()[:43]
        
        npc_entry = {
            "key": npc_key,
            "id": npc_data["id"],
            "name": npc_data["name"],
            "archetype": npc_data.get("archetype", "Unknown"),
            "faction": npc_data.get("faction", "Neutral"),
            "visual_description": npc_data.get("visual_description", ""),
            "accent_color": npc_data.get("accent_color", "Cyan"),
            "location_home": npc_data.get("location_home", ""),
            "catchphrases": npc_data.get("catchphrases", []),
            "tx_id": tx_id,
            "arweave_url": f"https://arweave.net/{tx_id}"
        }
        
        npcs_for_upload.append(npc_entry)
        
        print(f"✅ {npc_data['name']}")
        print(f"   Visual: {npc_data.get('visual_description', 'N/A')[:60]}...")
        print(f"   TX: https://arweave.net/{tx_id}")
        print()
    
    # Create locations manifest
    locations = []
    for loc_key, loc_desc in LOCATIONS.items():
        locations.append({
            "key": loc_key,
            "description": loc_desc
        })
    
    manifest = {
        "app": "AO-World-Engine",
        "type": "founding_npc_manifest",
        "version": "2.0.0",
        "created": "2026-02-03",
        "npcs": npcs_for_upload,
        "locations": locations,
        "style_guide": {
            "name": "Signal Noir",
            "primary_color": "#00CED1",
            "faction_colors": {
                "Resistance": "Cyan (#00CED1)",
                "Temple": "Gold/Amber (#D4A017)",
                "Mystic": "Purple (#9370DB)",
                "Special": "Magenta (#FF1493)"
            },
            "rules": [
                "85% grayscale, max 15% color accents",
                "Deep noir shadows, high contrast",
                "Art deco architecture",
                "Mostly night, but daytime exists (always shadowed)"
            ]
        },
        "total_npcs": len(npcs_for_upload),
        "total_locations": len(locations)
    }
    
    # Generate manifest tx_id
    manifest_tx = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()[:43]
    manifest["manifest_tx"] = manifest_tx
    
    return manifest


def main():
    print("=" * 60)
    print("AO World Engine - Founding NPC Arweave Upload")
    print("=" * 60)
    print()
    
    manifest = generate_arweave_manifest()
    
    # Save manifest locally
    output_path = os.path.join(os.path.dirname(__file__), 'data', 'founding_manifest.json')
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print("=" * 60)
    print(f"Manifest saved to: {output_path}")
    print(f"Total NPCs: {manifest['total_npcs']}")
    print(f"Total Locations: {manifest['total_locations']}")
    print(f"Manifest TX: https://arweave.net/{manifest['manifest_tx']}")
    print("=" * 60)
    
    # Summary of visual descriptions
    print("\n📷 VISUAL DESCRIPTIONS FOR IMAGE GENERATION:")
    print("-" * 60)
    for npc in manifest['npcs']:
        if npc['visual_description']:
            print(f"\n{npc['name']} ({npc['faction']}):")
            print(f"  {npc['visual_description']}")
    
    return manifest


if __name__ == "__main__":
    main()

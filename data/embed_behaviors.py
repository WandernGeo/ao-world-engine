#!/usr/bin/env python3
"""
Embed Python code into JSON for Arweave upload.
Converts scripts/*.py → data/behaviors/*.json with base64 encoded code.
"""

import os
import json
import base64
from datetime import datetime

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'scripts')
BEHAVIORS_DIR = os.path.join(os.path.dirname(__file__), 'behaviors')

# Scripts to embed
SCRIPTS_TO_EMBED = [
    ("faction_ai.py", "faction_ai", "Strategic faction AI with diplomacy, war, trade"),
    ("npc_life_sim.py", "npc_life", "NPC life simulation with economy, needs, jobs"),
    ("simulation_behaviors.py", "simulation", "Core simulation tick processing"),
]


def embed_script(script_name: str, behavior_id: str, description: str) -> dict:
    """Read a Python script and embed it in JSON format."""
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    
    if not os.path.exists(script_path):
        print(f"⚠️ Script not found: {script_path}")
        return None
    
    with open(script_path, 'r') as f:
        code = f.read()
    
    # Base64 encode
    code_b64 = base64.b64encode(code.encode()).decode()
    
    return {
        "id": f"BEH_{behavior_id}",
        "name": behavior_id.replace("_", " ").title(),
        "description": description,
        "version": "1.0.0",
        "created_at": datetime.now().isoformat(),
        "source_file": script_name,
        
        # Execution metadata
        "runtime": "python3",
        "deterministic": True,
        
        # The embedded code
        "code_b64": code_b64,
        "code_hash": hash(code) & 0xFFFFFFFF,  # For verification
        "code_lines": len(code.split('\n')),
        "code_bytes": len(code.encode()),
        
        # Entry points
        "entry_points": extract_entry_points(code),
        
        # Dependencies (other behaviors needed)
        "depends_on": [],
    }


def extract_entry_points(code: str) -> list:
    """Extract main functions from Python code."""
    import re
    
    # Find all top-level function definitions
    pattern = r'^def (\w+)\s*\('
    functions = re.findall(pattern, code, re.MULTILINE)
    
    # Filter to likely entry points
    entry_points = [
        f for f in functions 
        if not f.startswith('_') and f not in ['main', 'test']
    ]
    
    return entry_points[:10]  # Limit to 10


def create_behavior_bundle() -> dict:
    """Create a complete behavior bundle for Arweave."""
    os.makedirs(BEHAVIORS_DIR, exist_ok=True)
    
    bundle = {
        "type": "behavior_bundle",
        "version": "1.0.0",
        "created_at": datetime.now().isoformat(),
        "behaviors": {}
    }
    
    for script_name, behavior_id, description in SCRIPTS_TO_EMBED:
        print(f"📦 Embedding {script_name}...")
        
        behavior = embed_script(script_name, behavior_id, description)
        if behavior:
            bundle["behaviors"][behavior_id] = behavior
            
            # Also save individual behavior file
            behavior_path = os.path.join(BEHAVIORS_DIR, f"{behavior_id}.json")
            with open(behavior_path, 'w') as f:
                json.dump(behavior, f, indent=2)
            
            print(f"   ✅ Saved: {behavior_path}")
            print(f"   📊 {behavior['code_lines']} lines, {behavior['code_bytes']} bytes")
            print(f"   🔌 Entry points: {behavior['entry_points'][:5]}")
    
    # Save complete bundle
    bundle_path = os.path.join(BEHAVIORS_DIR, "_bundle.json")
    with open(bundle_path, 'w') as f:
        json.dump(bundle, f, indent=2)
    
    print(f"\n📦 Bundle saved: {bundle_path}")
    
    return bundle


def decode_behavior(behavior_json: dict) -> str:
    """Decode a behavior back to Python code."""
    code_b64 = behavior_json.get("code_b64", "")
    return base64.b64decode(code_b64).decode()


if __name__ == "__main__":
    print("="*60)
    print("  EMBED PYTHON CODE INTO JSON FOR ARWEAVE")
    print("="*60)
    
    bundle = create_behavior_bundle()
    
    print("\n" + "="*60)
    print("  Summary")
    print("="*60)
    print(f"  Behaviors embedded: {len(bundle['behaviors'])}")
    
    total_bytes = sum(
        b.get("code_bytes", 0) 
        for b in bundle["behaviors"].values()
    )
    print(f"  Total code size: {total_bytes / 1024:.1f} KB")
    
    print("\n  These JSON files can now be uploaded to Arweave!")
    print("  Run: python data/upload_behaviors.py")

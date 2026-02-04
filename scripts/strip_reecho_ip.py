#!/usr/bin/env python3
"""
Strip RE:ECHO IP from Data Files
================================

Copies all codec/NPC data, replaces RE:ECHO references with generic placeholders,
saves originals to reecho-city-private.
"""

import json
import re
import os
import shutil
from pathlib import Path

# Paths
ENGINE_DIR = Path("/Users/ram/Documents/wandern/ao-world-engine")
PRIVATE_DIR = Path("/Users/ram/Documents/wandern/reecho-city-private")
DATA_DIR = ENGINE_DIR / "data"
CODEC_DIR = DATA_DIR / "codec_chunks"

# Create backup directory
BACKUP_DIR = PRIVATE_DIR / "full_data_backup"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# Replacements
REPLACEMENTS = {
    # Names
    r"RE:ECHO City": "Example City",
    r"RE:ECHO": "YourWorld",
    r"Signal Noir": "Clean Modern",
    r"reecho": "example",
    r"REECHO": "EXAMPLE",
    
    # Characters (founding NPCs)
    r"\bFelix\b": "Merchant_01",
    r"\bCharlie\b": "Guard_01", 
    r"\bOrion\b": "Mystic_01",
    r"\bMaya\b": "Hacker_01",
    r"\bKai Vance\b": "Fixer_01",
    r"\bNova Chen\b": "Medic_01",
    r"\bBlade\b": "Fighter_01",
    r"\bVex\b": "Scavenger_01",
    
    # Locations
    r"Neon District": "District_A",
    r"The Depths": "District_B",
    r"Corporate Spire": "District_C",
    r"Temple District": "District_D",
    
    # Factions
    r"Temple of the Signal": "Example_Faction_1",
    r"Aiche": "City_AI",
}

def strip_ip_from_text(text):
    """Replace all RE:ECHO IP with generic placeholders."""
    result = text
    for pattern, replacement in REPLACEMENTS.items():
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE if pattern[0] != '\\' else 0)
    return result

def process_json_file(src_path, dst_path=None):
    """Load JSON, strip IP, save back."""
    if dst_path is None:
        dst_path = src_path
    
    with open(src_path, 'r') as f:
        content = f.read()
    
    # Strip IP
    stripped = strip_ip_from_text(content)
    
    # Write back
    with open(dst_path, 'w') as f:
        f.write(stripped)
    
    return stripped != content  # Return True if changes were made

def main():
    print("=== Stripping RE:ECHO IP from Engine ===\n")
    
    # Step 1: Backup all data to private repo
    print("1. Backing up original data to private repo...")
    if (BACKUP_DIR / "codec_chunks").exists():
        print("   Backup already exists, skipping...")
    else:
        shutil.copytree(CODEC_DIR, BACKUP_DIR / "codec_chunks")
        shutil.copy(DATA_DIR / "npcs_generated_with_personality.json", 
                   BACKUP_DIR / "npcs_full.json")
        shutil.copy(DATA_DIR / "founding_manifest.json",
                   BACKUP_DIR / "founding_manifest.json")
        print(f"   Backed up to: {BACKUP_DIR}")
    
    # Step 2: Process codec files
    print("\n2. Processing codec chunks...")
    changes = 0
    for json_file in CODEC_DIR.glob("*.json"):
        if process_json_file(json_file):
            changes += 1
            print(f"   ✓ Stripped: {json_file.name}")
    
    # Step 3: Process main data files
    print("\n3. Processing main data files...")
    data_files = [
        "npcs_generated.json",
        "npcs_generated_with_personality.json",
        "npc_inventories.json",
        "founding_manifest.json",
        "canned_responses.json",
        "cultural_dialects.json",
        "cyberpunk_intents.json",
        "npc_knowledge_system.json",
        "npc_reputation.json",
        "event_dialogue.json",
    ]
    
    for fname in data_files:
        fpath = DATA_DIR / fname
        if fpath.exists():
            if process_json_file(fpath):
                changes += 1
                print(f"   ✓ Stripped: {fname}")
    
    # Step 4: Reduce NPCs to 50 for example
    print("\n4. Creating example NPC subset (50 NPCs)...")
    npc_file = DATA_DIR / "npcs_generated_with_personality.json"
    with open(npc_file) as f:
        data = json.load(f)
    
    if "npcs" in data and len(data["npcs"]) > 50:
        data["npcs"] = data["npcs"][:50]
        data["_note"] = "Example dataset with 50 NPCs. For full simulation, generate more using npc_personality_generator.py"
        with open(npc_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"   Reduced to 50 example NPCs")
    
    # Step 5: Verify no IP remains
    print("\n5. Verifying no IP remains...")
    ip_found = False
    for json_file in list(CODEC_DIR.glob("*.json")) + list(DATA_DIR.glob("*.json")):
        with open(json_file) as f:
            content = f.read()
        if re.search(r"RE:ECHO|Signal Noir|Felix|Charlie|Orion|Maya", content, re.IGNORECASE):
            print(f"   ⚠ Still has IP: {json_file.name}")
            ip_found = True
    
    if not ip_found:
        print("   ✓ All files clean!")
    
    print(f"\n=== Done! {changes} files modified ===")
    print(f"Backup at: {BACKUP_DIR}")

if __name__ == "__main__":
    main()

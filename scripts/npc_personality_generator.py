#!/usr/bin/env python3
"""
NPC PERSONALITY GENERATOR
=========================

Tool to add personality data to all NPCs in the codec.
Generates deterministic personality based on NPC ID and birth_tick.

Usage:
    python npc_personality_generator.py --update-codec
    python npc_personality_generator.py --preview
"""

import json
import os
import sys
from typing import Dict, Any
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from personality_system import (
    generate_personality_profile,
    assign_echo_alignment,
    assign_reecho_archetype,
    assign_alignment,
    assign_mbti,
    assign_zodiac,
    assign_chinese_zodiac,
    WESTERN_ZODIAC,
    CHINESE_ZODIAC,
    REECHO_ARCHETYPES,
    MBTI_TYPES
)


# ==============================================================================
# CANONICAL NPC BIRTH TICKS (for deterministic personality)
# ==============================================================================
# These are fixed to ensure the same NPC always gets the same personality

NPC_BIRTH_TICKS = {
    # Founding 12
    "charlie": 100,
    "kai_vance": 250,
    "orion_thane": 180,
    "felix": 320,
    "nova_chen": 50,
    "selene_voss": 15,
    "sister_mira": 200,
    "mama_indira": 340,
    "aiche": 1,  # AI - first tick
    "pixel": 120,
    "cipher": 777,  # Mysterious
    "zero_chen": 300,
    
    # Extended NPCs (can add more)
    "blade": 88,
    "vex": 222,
}


def get_birth_tick(npc_id: str) -> int:
    """Get birth tick for an NPC. If not defined, generate from ID hash."""
    if npc_id in NPC_BIRTH_TICKS:
        return NPC_BIRTH_TICKS[npc_id]
    # Generate deterministic birth tick from ID
    import hashlib
    return int(hashlib.md5(npc_id.encode()).hexdigest()[:8], 16) % 365


def generate_npc_personality_block(npc_id: str) -> Dict[str, Any]:
    """
    Generate complete personality block for an NPC.
    This can be embedded directly into the NPC JSON.
    """
    birth_tick = get_birth_tick(npc_id)
    profile = generate_personality_profile(npc_id, birth_tick)
    
    # Get archetype details
    archetype_data = REECHO_ARCHETYPES.get(profile.archetype, {})
    
    return {
        "personality": {
            "birth_tick": birth_tick,
            
            # RE:ECHO Alignment (Primary)
            "echo_alignment": {
                "signal": profile.echo_alignment.signal.value if profile.echo_alignment else None,
                "method": profile.echo_alignment.method.value if profile.echo_alignment else None,
                "name": profile.echo_alignment.name if profile.echo_alignment else None,
                "description": profile.echo_alignment.description if profile.echo_alignment else None,
                "dnd_equivalent": profile.echo_alignment.dnd_equivalent if profile.echo_alignment else None
            },
            
            # Archetype
            "archetype": {
                "id": profile.archetype,
                "name": profile.archetype.title() if profile.archetype else None,
                "description": archetype_data.get("description", ""),
                "mbti_like": archetype_data.get("mbti_like", ""),
                "strengths": archetype_data.get("strengths", []),
                "weaknesses": archetype_data.get("weaknesses", [])
            },
            
            # MBTI
            "mbti": {
                "type": profile.mbti,
                "name": MBTI_TYPES.get(profile.mbti, {}).get("name", ""),
                "compatible_types": MBTI_TYPES.get(profile.mbti, {}).get("compatible", [])
            },
            
            # Western Zodiac
            "zodiac": {
                "sign": profile.zodiac,
                "symbol": WESTERN_ZODIAC.get(profile.zodiac, {}).get("symbol", ""),
                "element": profile.zodiac_element,
                "traits": WESTERN_ZODIAC.get(profile.zodiac, {}).get("traits", []),
                "compatible": WESTERN_ZODIAC.get(profile.zodiac, {}).get("compatible", [])
            },
            
            # Chinese Zodiac
            "chinese_zodiac": {
                "animal": profile.chinese_animal,
                "animal_symbol": CHINESE_ZODIAC.get(profile.chinese_animal, {}).get("symbol", ""),
                "element": profile.chinese_element,
                "traits": CHINESE_ZODIAC.get(profile.chinese_animal, {}).get("traits", [])
            },
            
            # Combined traits (from all systems)
            "all_traits": profile.all_traits[:10],  # Top 10
            "all_weaknesses": profile.all_weaknesses[:5]  # Top 5
        }
    }


def update_codec_npcs(codec_path: str, output_path: str = None) -> None:
    """Update NPC codec with personality data."""
    with open(codec_path, 'r') as f:
        codec = json.load(f)
    
    # Update founding_npcs
    if "founding_npcs" in codec:
        for npc_id, npc_data in codec["founding_npcs"].items():
            if npc_id.startswith("_"):
                continue  # Skip metadata
            
            personality_block = generate_npc_personality_block(npc_id)
            npc_data.update(personality_block)
            print(f"  Added personality to: {npc_id}")
    
    # Write output
    out = output_path or codec_path
    with open(out, 'w') as f:
        json.dump(codec, f, indent=4)
    
    print(f"\n✅ Updated codec saved to: {out}")


def preview_all_npcs() -> None:
    """Preview personality for all known NPCs."""
    print("="*70)
    print("  NPC PERSONALITY PREVIEW")
    print("="*70)
    
    for npc_id in sorted(NPC_BIRTH_TICKS.keys()):
        birth_tick = NPC_BIRTH_TICKS[npc_id]
        profile = generate_personality_profile(npc_id, birth_tick)
        
        print(f"\n📋 {npc_id.upper().replace('_', ' ')}")
        print(f"   ⚡ {profile.echo_alignment.name if profile.echo_alignment else 'Unknown'} {profile.archetype.title() if profile.archetype else ''}")
        if profile.echo_alignment:
            print(f"      \"{profile.echo_alignment.description}\"")
        print(f"   {WESTERN_ZODIAC.get(profile.zodiac, {}).get('symbol', '')} {profile.zodiac.title()} ({profile.zodiac_element})")
        print(f"   {CHINESE_ZODIAC.get(profile.chinese_animal, {}).get('symbol', '')} {profile.chinese_element.title()} {profile.chinese_animal.title()}")
        print(f"   📝 MBTI: {profile.mbti} ({MBTI_TYPES.get(profile.mbti, {}).get('name', '')})")
        print(f"   Traits: {', '.join(profile.all_traits[:4])}")


def generate_personality_codec_schema() -> Dict[str, Any]:
    """
    Generate the personality schema for the codec.
    This defines what fields NPCs should have for personality.
    """
    return {
        "personality_schema": {
            "_desc": "Personality data for NPCs - deterministically generated from birth_tick",
            "birth_tick": {
                "type": "int",
                "desc": "The simulation tick when this NPC was born/created",
                "use": "Seed for all personality randomization"
            },
            "echo_alignment": {
                "signal": {
                    "type": "enum",
                    "values": ["resonant", "neutral", "dissonant"],
                    "desc": "How character relates to Echoes"
                },
                "method": {
                    "type": "enum", 
                    "values": ["harmonic", "adaptive", "chaotic"],
                    "desc": "How character achieves goals"
                }
            },
            "archetype": {
                "type": "enum",
                "values": list(REECHO_ARCHETYPES.keys()),
                "desc": "RE:ECHO personality archetype"
            },
            "mbti": {
                "type": "enum",
                "values": list(MBTI_TYPES.keys()),
                "desc": "16-type personality indicator"
            },
            "zodiac": {
                "sign": {"type": "enum", "values": list(WESTERN_ZODIAC.keys())},
                "element": {"type": "enum", "values": ["fire", "earth", "air", "water"]}
            },
            "chinese_zodiac": {
                "animal": {"type": "enum", "values": list(CHINESE_ZODIAC.keys())},
                "element": {"type": "enum", "values": ["wood", "fire", "earth", "metal", "water"]}
            }
        }
    }


# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate NPC personalities")
    parser.add_argument("--preview", action="store_true", help="Preview personalities")
    parser.add_argument("--update-codec", action="store_true", help="Update the NPC codec")
    parser.add_argument("--schema", action="store_true", help="Print personality schema")
    parser.add_argument("--npc", type=str, help="Show single NPC personality")
    
    args = parser.parse_args()
    
    base_dir = Path(__file__).parent.parent
    codec_path = base_dir / "data" / "codec_chunks" / "world_codec_01_npcs.json"
    output_path = base_dir / "data" / "codec_chunks" / "world_codec_01_npcs_with_personality.json"
    
    if args.preview:
        preview_all_npcs()
    elif args.update_codec:
        print(f"Updating NPC codec: {codec_path}")
        update_codec_npcs(str(codec_path), str(output_path))
    elif args.schema:
        schema = generate_personality_codec_schema()
        print(json.dumps(schema, indent=2))
    elif args.npc:
        block = generate_npc_personality_block(args.npc)
        print(json.dumps(block, indent=2))
    else:
        preview_all_npcs()

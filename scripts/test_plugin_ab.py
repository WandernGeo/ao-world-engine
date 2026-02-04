#!/usr/bin/env python3
"""
Plugin A/B Test
===============

Compares behavior between:
- example-city (vanilla, generic)
- signal-noir (RE:ECHO, cyberpunk)

Tests: NPC data, lore context, style, chat behavior
"""

import sys
import json
sys.path.insert(0, 'scripts')
from world_loader import WorldLoader

def test_world(world_id: str):
    """Test a specific world plugin."""
    print(f"\n{'='*60}")
    print(f"  TESTING: {world_id.upper()}")
    print(f"{'='*60}\n")
    
    # Load world
    loader = WorldLoader('config.json')
    loader.set_active_world(world_id)
    world = loader.active_world
    
    if not world:
        print(f"❌ Failed to load world: {world_id}")
        return None
    
    print(f"✅ Loaded: {world.name}")
    
    # 1. NPC Count & Sample
    print(f"\n--- NPCs ---")
    npcs = world.load_npcs()
    npc_list = npcs.get("npcs", [])
    print(f"Total NPCs: {len(npc_list)}")
    
    if npc_list:
        sample = npc_list[0]
        print(f"Sample NPC: {sample.get('name', 'Unknown')}")
        if 'personality' in sample:
            print(f"  Personality: {sample['personality']}")
        if 'archetype' in sample:
            print(f"  Archetype: {sample.get('archetype')}")
    
    # 2. Lore
    print(f"\n--- Lore ---")
    lore = world.load_lore()
    if lore:
        if 'history' in lore:
            eras = lore.get('history', {}).get('eras', {})
            if isinstance(eras, dict):
                print(f"Historical eras: {list(eras.keys())}")
            elif isinstance(eras, list):
                print(f"Historical eras: {[e.get('name') for e in eras]}")
        if '_desc' in lore.get('history', {}):
            print(f"Timeline: {lore['history']['_desc']}")
    else:
        print("No lore data")
    
    # 3. Style
    print(f"\n--- Art Style ---")
    style = world.get_style()
    if style:
        print(f"Style: {style.get('name', 'Unknown')}")
        if 'color_palette' in style:
            colors = style['color_palette']
            print(f"Primary: {colors.get('primary', 'N/A')}")
            print(f"Background: {colors.get('background', 'N/A')}")
        if 'aesthetic' in style:
            print(f"Aesthetic: {style['aesthetic'].get('genre', 'N/A')}")
    else:
        print("No style data")
    
    # 4. Chat Context (what would be sent to LLM)
    print(f"\n--- Chat Context Preview ---")
    context = build_chat_context(world)
    print(context[:500] + "..." if len(context) > 500 else context)
    
    return {
        "world": world.name,
        "npc_count": len(npc_list),
        "has_lore": bool(lore),
        "has_style": bool(style)
    }


def build_chat_context(world):
    """Build the context that would be sent to the LLM for chat."""
    style = world.get_style() or {}
    lore = world.load_lore() or {}
    
    context = f"""
WORLD: {world.name}
GENRE: {style.get('aesthetic', {}).get('genre', 'generic')}

SETTING:
{style.get('description', 'A simulation world.')}

VISUAL STYLE:
{style.get('visual_elements', {}).get('lighting', 'Standard lighting')}

ATMOSPHERE:
- Mood: {', '.join(style.get('aesthetic', {}).get('mood', ['neutral']))}
- Era: {style.get('aesthetic', {}).get('era', 'unspecified')}

NPC BEHAVIOR GUIDANCE:
- Characters should speak in a style appropriate to {world.name}
- Reference the world's lore when relevant
- Maintain consistent tone with the aesthetic
"""
    return context.strip()


def main():
    print("\n" + "="*60)
    print("  PLUGIN A/B TEST: Vanilla vs Signal Noir")
    print("="*60)
    
    results = {}
    
    # Test vanilla (example-city)
    results['vanilla'] = test_world('example-city')
    
    # Test Signal Noir
    results['signal-noir'] = test_world('signal-noir')
    
    # Comparison
    print("\n" + "="*60)
    print("  COMPARISON SUMMARY")
    print("="*60 + "\n")
    
    print(f"{'Metric':<20} {'Vanilla':<20} {'Signal Noir':<20}")
    print("-" * 60)
    
    if results['vanilla'] and results['signal-noir']:
        v = results['vanilla']
        s = results['signal-noir']
        print(f"{'World Name':<20} {'Example City':<20} {s['world']:<20}")
        print(f"{'NPC Count':<20} {v['npc_count']:<20} {s['npc_count']:<20}")
        print(f"{'Has Lore':<20} {str(v['has_lore']):<20} {str(s['has_lore']):<20}")
        print(f"{'Has Style':<20} {str(v['has_style']):<20} {str(s['has_style']):<20}")
    else:
        print("⚠ Could not compare - one or both worlds failed to load")
    
    print("\n✅ Test complete!")


if __name__ == "__main__":
    main()

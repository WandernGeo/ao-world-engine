#!/usr/bin/env python3
"""
NPC Interaction Test
====================

Tests NPC-to-NPC interactions with:
- Timestamps (simulation ticks)
- Dialogue snippets
- Relationship changes
- Events generated

Uses the Signal Noir plugin for rich NPC data.
"""

import sys
import json
import random
from datetime import datetime
sys.path.insert(0, 'scripts')
from world_loader import WorldLoader

# Color output
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def format_tick(tick):
    """Format tick as timestamp."""
    hour = (tick % 24)
    day = (tick // 24) + 1
    return f"Day {day}, {hour:02d}:00"

def simulate_interaction(npc1, npc2, tick, relationships):
    """Simulate an interaction between two NPCs."""
    key = f"{npc1['id']}_{npc2['id']}"
    reverse_key = f"{npc2['id']}_{npc1['id']}"
    
    # Get existing relationship
    rel = relationships.get(key, {"trust": 50, "interactions": 0})
    
    # Calculate interaction outcome based on personalities
    p1 = npc1.get('personality', {})
    p2 = npc2.get('personality', {})
    
    if isinstance(p1, dict):
        agg1 = p1.get('aggression', 0.3)
        soc1 = p1.get('sociability', 0.5)
    else:
        agg1 = 0.3
        soc1 = 0.5
    
    if isinstance(p2, dict):
        agg2 = p2.get('aggression', 0.3)
        soc2 = p2.get('sociability', 0.5)
    else:
        agg2 = 0.3
        soc2 = 0.5
    
    # Interaction type based on personalities
    interaction_roll = random.random()
    
    if agg1 > 0.7 and agg2 > 0.7:
        interaction_type = "conflict"
        trust_change = -10
        dialogue = [
            f"{npc1['name']}: *glares* \"Stay out of my way.\"",
            f"{npc2['name']}: \"Or what? You think you scare me?\""
        ]
    elif soc1 > 0.6 and soc2 > 0.6:
        interaction_type = "friendly_chat"
        trust_change = +5
        dialogue = [
            f"{npc1['name']}: \"Hey, haven't seen you around lately.\"",
            f"{npc2['name']}: \"Yeah, been busy. You hear about the news?\""
        ]
    elif interaction_roll < 0.3:
        interaction_type = "gossip"
        trust_change = +3
        dialogue = [
            f"{npc1['name']}: *leans in* \"Did you hear about what happened?\"",
            f"{npc2['name']}: \"No, tell me everything.\""
        ]
    elif interaction_roll < 0.6:
        interaction_type = "trade"
        trust_change = +2
        dialogue = [
            f"{npc1['name']}: \"Got anything worth selling?\"",
            f"{npc2['name']}: \"Maybe. What are you offering?\""
        ]
    else:
        interaction_type = "brief_nod"
        trust_change = +1
        dialogue = [
            f"{npc1['name']}: *nods*",
            f"{npc2['name']}: *nods back*"
        ]
    
    # Update relationship
    rel['trust'] = max(0, min(100, rel['trust'] + trust_change))
    rel['interactions'] += 1
    rel['last_interaction'] = tick
    relationships[key] = rel
    relationships[reverse_key] = rel  # Mirror relationship
    
    return {
        "tick": tick,
        "timestamp": format_tick(tick),
        "npc1": npc1['name'],
        "npc2": npc2['name'],
        "type": interaction_type,
        "trust_change": trust_change,
        "new_trust": rel['trust'],
        "dialogue": dialogue
    }

def generate_event(interaction, tick):
    """Generate a news event from significant interactions."""
    if interaction['type'] == 'conflict':
        return {
            "tick": tick,
            "headline": f"Altercation reported between {interaction['npc1']} and {interaction['npc2']}",
            "severity": "minor"
        }
    elif interaction['type'] == 'gossip' and random.random() < 0.3:
        return {
            "tick": tick,
            "headline": f"Rumors spreading through the district",
            "severity": "trivial"
        }
    return None

def main():
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}  NPC INTERACTION TEST - Signal Noir World{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")
    
    # Load Signal Noir world
    loader = WorldLoader('config.json')
    loader.set_active_world('signal-noir')
    world = loader.active_world
    
    if not world:
        print(f"{Colors.RED}Failed to load Signal Noir world{Colors.END}")
        return
    
    print(f"{Colors.GREEN}✓ Loaded: {world.name}{Colors.END}")
    
    # Load NPCs
    npcs_data = world.load_npcs()
    npcs = npcs_data.get('npcs', [])[:20]  # Use first 20 for demo
    print(f"{Colors.GREEN}✓ Loaded {len(npcs)} NPCs for simulation{Colors.END}\n")
    
    # Initialize state
    relationships = {}
    events = []
    interactions = []
    
    # Simulate 10 ticks
    print(f"{Colors.CYAN}{'─'*70}{Colors.END}")
    print(f"{Colors.BOLD}  SIMULATION LOG{Colors.END}")
    print(f"{Colors.CYAN}{'─'*70}{Colors.END}\n")
    
    for tick in range(0, 100, 10):
        # Pick random NPCs to interact
        if len(npcs) >= 2:
            npc1, npc2 = random.sample(npcs, 2)
            
            interaction = simulate_interaction(npc1, npc2, tick, relationships)
            interactions.append(interaction)
            
            # Print interaction
            print(f"{Colors.YELLOW}[{interaction['timestamp']}]{Colors.END} "
                  f"{Colors.BOLD}{interaction['npc1']}{Colors.END} meets "
                  f"{Colors.BOLD}{interaction['npc2']}{Colors.END}")
            print(f"   Type: {interaction['type']}")
            for line in interaction['dialogue']:
                print(f"   {line}")
            
            trust_color = Colors.GREEN if interaction['trust_change'] > 0 else Colors.RED
            print(f"   → Trust: {trust_color}{interaction['trust_change']:+d}{Colors.END} "
                  f"(now {interaction['new_trust']})")
            
            # Check for events
            event = generate_event(interaction, tick)
            if event:
                events.append(event)
                print(f"   {Colors.CYAN}📰 NEWS: {event['headline']}{Colors.END}")
            
            print()
    
    # Summary
    print(f"{Colors.CYAN}{'─'*70}{Colors.END}")
    print(f"{Colors.BOLD}  SIMULATION SUMMARY{Colors.END}")
    print(f"{Colors.CYAN}{'─'*70}{Colors.END}\n")
    
    print(f"Total interactions: {len(interactions)}")
    print(f"Events generated: {len(events)}")
    print(f"Relationships tracked: {len(relationships) // 2}")
    
    # Show top relationships
    print(f"\n{Colors.BOLD}Relationship Changes:{Colors.END}")
    for key, rel in list(relationships.items())[:5]:
        if '_' in key:
            ids = key.split('_')
            print(f"  {ids[0][:8]}... ↔ {ids[1][:8]}... : Trust {rel['trust']} ({rel['interactions']} interactions)")
    
    print(f"\n{Colors.GREEN}✓ Test complete!{Colors.END}\n")

if __name__ == "__main__":
    random.seed(42)  # Reproducible results
    main()

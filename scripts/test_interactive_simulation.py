#!/usr/bin/env python3
"""
INTERACTIVE SIMULATION TEST
============================

Tests the full system with:
1. Multi-NPC meetings (5+ NPCs at same location)
2. Bowling clubs / social groups
3. Faction conflicts
4. Faction AI decisions
5. Visual-ready output

Run: python scripts/test_interactive_simulation.py
"""

import os
import sys
import json
from datetime import datetime

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'data'))

from npc_relationships import (
    record_interaction, get_relationship, load_npc_memory,
    get_npc_memory_context, get_npc_relationships
)
from simulation_behaviors import calculate_interaction, simulate_tick, deterministic_hash
from faction_ai import (
    FACTIONS, process_all_factions, FactionState
)


# =============================================================================
# NPC DEFINITIONS
# =============================================================================

# The bowling club
BOWLING_CLUB = [
    {"id": "charlie", "name": "Charlie", "faction": "resistance", "personality": {"friendly": 0.8}},
    {"id": "felix", "name": "Felix", "faction": "criminal", "personality": {"friendly": 0.6}},
    {"id": "nova_chen", "name": "Nova Chen", "faction": "civilian", "personality": {"friendly": 0.7}},
    {"id": "marcus", "name": "Marcus", "faction": "temple", "personality": {"friendly": 0.5}},
    {"id": "jax", "name": "Jax", "faction": "resistance", "personality": {"friendly": 0.9}},
]

# The underground fight club
FIGHT_CLUB = [
    {"id": "vex", "name": "Vex", "faction": "criminal", "personality": {"aggression": 0.9}},
    {"id": "blade", "name": "Blade", "faction": "criminal", "personality": {"aggression": 0.8}},
    {"id": "zero_chen", "name": "Zero Chen", "faction": "resistance", "personality": {"aggression": 0.7}},
    {"id": "enforcer_01", "name": "Temple Enforcer", "faction": "temple", "personality": {"aggression": 0.6}},
]

# The business lunch club
BUSINESS_CLUB = [
    {"id": "director_kira", "name": "Director Kira", "faction": "corporate", "personality": {"friendly": 0.4}},
    {"id": "trader_yun", "name": "Trader Yun", "faction": "corporate", "personality": {"friendly": 0.6}},
    {"id": "mayor_lin", "name": "Mayor Lin", "faction": "civilian", "personality": {"friendly": 0.8}},
]


# =============================================================================
# SIMULATION HELPERS
# =============================================================================

def simulate_group_meeting(group: list, location: str, tick: int) -> list:
    """
    Simulate all NPCs in a group meeting at a location.
    Returns all interactions that occurred.
    """
    print(f"\n📍 Location: {location}")
    print(f"   Present: {[npc['name'] for npc in group]}")
    
    interactions = []
    
    # Every pair can interact
    for i, npc1 in enumerate(group):
        for npc2 in group[i+1:]:
            # Check if they interact this tick
            seed = f"{npc1['id']}_{npc2['id']}_{tick}_interact"
            should_interact = deterministic_hash(seed) % 100 < 30  # 30% chance
            
            if should_interact:
                # Add location and activity for interaction check
                npc1_state = {**npc1, "location": location, "activity": "socializing"}
                npc2_state = {**npc2, "location": location, "activity": "socializing"}
                
                interaction = calculate_interaction(npc1_state, npc2_state, tick)
                
                if interaction:
                    interactions.append(interaction)
                    
                    # Record to persistent storage
                    record_interaction(
                        npc1["id"], npc2["id"],
                        interaction.get("interaction", "unknown"),
                        tick,
                        location=location
                    )
                    
                    # Pretty print
                    int_type = interaction.get("interaction", "?")
                    trust_change = interaction.get("trust_change", 0)
                    emoji = "💬" if trust_change > 0 else "😠" if trust_change < 0 else "😐"
                    print(f"   {emoji} {npc1['name']} + {npc2['name']}: {int_type} ({trust_change:+.2f} trust)")
    
    if not interactions:
        print("   (No notable interactions)")
    
    return interactions


def show_faction_conflict(faction1_id: str, faction2_id: str, location: str, tick: int):
    """
    Show a conflict between two faction members.
    """
    print(f"\n⚔️ FACTION CONFLICT at {location}")
    
    # Get sample members from each faction
    npcs = BOWLING_CLUB + FIGHT_CLUB + BUSINESS_CLUB
    
    faction1_npcs = [n for n in npcs if n.get("faction") == faction1_id]
    faction2_npcs = [n for n in npcs if n.get("faction") == faction2_id]
    
    if not faction1_npcs or not faction2_npcs:
        print("   No members available for conflict")
        return
    
    # Pick representatives
    npc1 = faction1_npcs[0]
    npc2 = faction2_npcs[0]
    
    print(f"   {npc1['name']} ({faction1_id}) vs {npc2['name']} ({faction2_id})")
    
    # Force a confrontation (hostile starting trust)
    npc1_state = {**npc1, "location": location, "activity": "patrolling", 
                  "relationships": {npc2["id"]: {"trust": 0.1}}}
    npc2_state = {**npc2, "location": location, "activity": "lurking"}
    
    interaction = calculate_interaction(npc1_state, npc2_state, tick)
    
    if interaction:
        int_type = interaction.get("interaction", "confrontation")
        print(f"   Result: {int_type}")
        
        record_interaction(npc1["id"], npc2["id"], int_type, tick, location=location)
        
        # Get relationship after
        rel = get_relationship(npc1["id"], npc2["id"])
        print(f"   Relationship now: {rel.get('trust', 0):.2f} trust, {rel.get('relationship_type', 'unknown')}")


def show_bowling_night(tick_start: int):
    """
    Simulate the weekly bowling night over several hours.
    """
    print("\n" + "="*60)
    print("  🎳 BOWLING NIGHT AT NEON LANES")
    print("="*60)
    
    location = "neon_lanes"
    all_interactions = []
    
    # 3 hours of bowling (3 ticks)
    for hour in range(3):
        tick = tick_start + hour
        print(f"\n⏰ Hour {hour + 1} (tick {tick})")
        
        interactions = simulate_group_meeting(BOWLING_CLUB, location, tick)
        all_interactions.extend(interactions)
    
    # Summary
    print("\n📊 Bowling Night Summary:")
    print(f"   Total interactions: {len(all_interactions)}")
    
    # Show relationships formed
    print("\n🤝 Relationships After Bowling:")
    for npc in BOWLING_CLUB:
        rels = get_npc_relationships(npc["id"])
        for other_id, rel in rels.items():
            if other_id in [n["id"] for n in BOWLING_CLUB]:
                print(f"   {npc['name']} → {other_id}: {rel.get('trust', 0):.2f} ({rel.get('relationship_type', '?')})")


def show_fight_club_night(tick_start: int):
    """
    Simulate the underground fight club.
    """
    print("\n" + "="*60)
    print("  🥊 UNDERGROUND FIGHT CLUB")
    print("="*60)
    
    location = "abandoned_warehouse"
    
    # Hostile environment - set low base trust
    for i, npc1 in enumerate(FIGHT_CLUB):
        for npc2 in FIGHT_CLUB[i+1:]:
            # Check existing relationship
            rel = get_relationship(npc1["id"], npc2["id"])
            
            # In fight club, trust is low
            npc1_state = {**npc1, "location": location, "activity": "fighting",
                         "relationships": {npc2["id"]: {"trust": 0.15}}}
            npc2_state = {**npc2, "location": location, "activity": "fighting"}
            
            interaction = calculate_interaction(npc1_state, npc2_state, tick_start)
            
            if interaction:
                int_type = interaction.get("interaction")
                emoji = "🥊" if int_type in ["fight", "argument"] else "🤝"
                print(f"   {emoji} {npc1['name']} vs {npc2['name']}: {int_type}")
                
                record_interaction(npc1["id"], npc2["id"], int_type, tick_start, 
                                 location=location)


def show_business_lunch(tick: int):
    """
    Simulate the business lunch meeting.
    """
    print("\n" + "="*60)
    print("  🍽️ BUSINESS LUNCH AT SKY TOWER")
    print("="*60)
    
    simulate_group_meeting(BUSINESS_CLUB, "sky_tower_restaurant", tick)


def show_faction_ai_decisions(tick: int):
    """
    Show what each faction decides to do.
    """
    print("\n" + "="*60)
    print("  🏛️ FACTION AI DECISIONS")
    print("="*60)
    
    world_state = {
        "contested_districts": ["neutral_zone", "border_district"],
        "buildings": {}
    }
    
    # Reset faction relationships for demo
    for f1_id, f1 in FACTIONS.items():
        for f2_id in FACTIONS:
            if f1_id != f2_id:
                if f1_id == "resistance" and f2_id == "temple":
                    f1.relationships[f2_id] = -0.8
                elif f1_id == "temple" and f2_id == "resistance":
                    f1.relationships[f2_id] = -0.8
                else:
                    f1.relationships[f2_id] = 0.0
    
    result = process_all_factions(world_state, tick)
    
    for faction_id, faction_result in result["faction_actions"].items():
        faction = FACTIONS[faction_id]
        print(f"\n  {faction.name}:")
        print(f"    💰 Credits: {faction.credits:.0f}")
        
        for action in faction_result.get("actions", []):
            if action.get("success"):
                action_type = action.get("action")
                target = action.get("target", "")
                print(f"    ✅ {action_type} {target}")
    
    if result.get("events"):
        print("\n  📢 Events:")
        for event in result["events"]:
            event_type = event.get("type", "?")
            if event_type == "war_declared":
                print(f"    ⚔️ WAR: {event['aggressor']} → {event['defender']}")
            elif event_type == "alliance_formed":
                print(f"    🤝 ALLIANCE: {event['faction1']} + {event['faction2']}")
            elif event_type == "trade_agreement":
                print(f"    💱 TRADE: {event['faction1']} ↔ {event['faction2']}")


def show_npc_memories():
    """
    Show what NPCs remember about each other.
    """
    print("\n" + "="*60)
    print("  💭 NPC MEMORIES")
    print("="*60)
    
    # Check a few key NPCs
    for npc in [BOWLING_CLUB[0], FIGHT_CLUB[0], BUSINESS_CLUB[0]]:
        print(f"\n  {npc['name']}'s memories:")
        context = get_npc_memory_context(npc["id"])
        for line in context.split("\n"):
            print(f"    {line}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("\n" + "="*60)
    print("  RE:ECHO CITY - INTERACTIVE SIMULATION")
    print("="*60)
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Clean previous test data
    from npc_relationships import DATA_DIR
    import shutil
    
    interactions_dir = os.path.join(DATA_DIR, 'npc_interactions')
    memory_dir = os.path.join(interactions_dir, 'npc_memory')
    
    if os.path.exists(memory_dir):
        shutil.rmtree(memory_dir)
    os.makedirs(memory_dir, exist_ok=True)
    
    for f in ['relationships.json', 'interaction_log.json', 'significant_events.json']:
        path = os.path.join(interactions_dir, f)
        if os.path.exists(path):
            os.remove(path)
    
    base_tick = 1000  # Start from tick 1000
    
    # 1. Bowling night
    show_bowling_night(base_tick)
    
    # 2. Fight club
    show_fight_club_night(base_tick + 100)
    
    # 3. Business lunch
    show_business_lunch(base_tick + 200)
    
    # 4. Faction conflict
    show_faction_conflict("resistance", "temple", "border_checkpoint", base_tick + 300)
    show_faction_conflict("criminal", "temple", "docks", base_tick + 301)
    
    # 5. Faction AI decisions
    show_faction_ai_decisions(base_tick + 400)
    
    # 6. Show memories
    show_npc_memories()
    
    print("\n" + "="*60)
    print("  ✅ SIMULATION COMPLETE")
    print("="*60)
    
    # Final stats
    from npc_relationships import load_json, RELATIONSHIPS_FILE, INTERACTION_LOG_FILE
    
    rels = load_json(RELATIONSHIPS_FILE, {})
    log = load_json(INTERACTION_LOG_FILE, [])
    
    print(f"\n  📊 Final Statistics:")
    print(f"     - Relationships formed: {len(rels)}")
    print(f"     - Interactions logged: {len(log)}")
    print(f"     - NPC memory files: {len(os.listdir(memory_dir))}")


if __name__ == "__main__":
    main()

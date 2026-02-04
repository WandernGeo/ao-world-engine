"""
AO World Engine - Social Dynamics System
=========================================

Implements Sims/Dwarf Fortress-style social mechanics:
1. Dynamic trust building through repeated meetings
2. Group formation (coworkers, neighbors, bar regulars)
3. Reputation spreading through gossip
4. Relationship evolution over time

All functions are deterministic for AO compatibility.
"""

import hashlib
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

# =============================================================================
# DETERMINISTIC UTILITIES
# =============================================================================

def deterministic_hash(seed: str) -> int:
    return int(hashlib.sha256(seed.encode()).hexdigest(), 16)

def deterministic_chance(probability: float, seed: str) -> bool:
    h = deterministic_hash(seed) % 10000
    return h < (probability * 10000)

def deterministic_choice(items: list, seed: str) -> Any:
    if not items:
        return None
    return items[deterministic_hash(seed) % len(items)]


# =============================================================================
# CONSTANTS
# =============================================================================

TRUST_CHANGES = {
    # Passive (just being in same place)
    "same_location": 0.002,
    "same_workplace": 0.01,
    "same_building": 0.005,
    "same_faction": 0.003,
    
    # Positive interactions
    "greeting": 0.005,
    "small_talk": 0.01,
    "deep_conversation": 0.03,
    "shared_meal": 0.02,
    "trade_successful": 0.02,
    "helped_in_need": 0.1,
    "defended_in_fight": 0.15,
    "gifted_item": 0.05,
    
    # Negative interactions
    "ignored": -0.005,
    "rude_response": -0.02,
    "argument": -0.08,
    "insulted": -0.1,
    "betrayed": -0.2,
    "stolen_from": -0.3,
    "attacked": -0.5,
}

RELATIONSHIP_THRESHOLDS = {
    "enemy": (-1.0, -0.3),
    "rival": (-0.3, 0.0),
    "stranger": (0.0, 0.25),
    "acquaintance": (0.25, 0.45),
    "colleague": (0.45, 0.65),
    "friend": (0.65, 0.85),
    "close_friend": (0.85, 1.0),
}

MEETING_THRESHOLDS = {
    "acquaintance": 3,
    "colleague": 10,
    "friend": 25,
    "close_friend": 50,
}

INITIAL_TRUST = {
    "family_spouse": 0.9,
    "family_parent": 0.85,
    "family_sibling": 0.75,
    "same_household": 0.7,
    "same_faction": 0.4,
    "same_workplace": 0.3,
    "same_building": 0.2,
    "stranger": 0.1,
}


# =============================================================================
# SOCIAL STATE
# =============================================================================

@dataclass
class Relationship:
    """Relationship between two NPCs."""
    npc_id: str
    trust: float = 0.1
    meetings: int = 0
    last_meeting_tick: int = 0
    relationship_type: str = "stranger"
    shared_events: List[str] = field(default_factory=list)
    contexts: List[str] = field(default_factory=list)  # work, neighbor, bar, etc.

    def to_dict(self) -> dict:
        return {
            "npc_id": self.npc_id,
            "trust": round(self.trust, 3),
            "meetings": self.meetings,
            "relationship": self.relationship_type,
            "contexts": self.contexts,
        }


@dataclass
class SocialGroup:
    """A social group of NPCs."""
    id: str
    name: str
    group_type: str  # coworkers, neighbors, bar_regulars, faction_cell
    members: List[str] = field(default_factory=list)
    meeting_location: str = ""
    formed_tick: int = 0
    bond_strength: float = 0.5
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.group_type,
            "members": self.members,
            "location": self.meeting_location,
            "bond_strength": round(self.bond_strength, 2),
        }


# =============================================================================
# RELATIONSHIP TRACKING
# =============================================================================

def get_or_create_relationship(npc: dict, other_id: str) -> dict:
    """Get existing relationship or create new one."""
    relationships = npc.get("relationships", {})
    
    if other_id not in relationships:
        relationships[other_id] = {
            "trust": 0.1,
            "meetings": 0,
            "last_tick": 0,
            "type": "stranger",
            "contexts": [],
        }
        npc["relationships"] = relationships
    
    return relationships[other_id]


def get_relationship_type(trust: float) -> str:
    """Determine relationship type from trust level."""
    for rel_type, (min_t, max_t) in RELATIONSHIP_THRESHOLDS.items():
        if min_t <= trust < max_t:
            return rel_type
    return "close_friend" if trust >= 0.85 else "stranger"


def track_meeting(npc1: dict, npc2: dict, context: str, tick: int) -> dict:
    """
    Track when two NPCs are in the same location.
    Called when NPCs share location during tick processing.
    
    Returns event data about the meeting.
    """
    # Get/create relationship from both sides
    rel1 = get_or_create_relationship(npc1, npc2["id"])
    rel2 = get_or_create_relationship(npc2, npc1["id"])
    
    # Only count one meeting per day (every 240 ticks)
    day1 = rel1.get("last_tick", 0) // 240
    current_day = tick // 240
    
    if day1 == current_day:
        return {"type": "already_met_today"}
    
    # Increment meeting count
    rel1["meetings"] = rel1.get("meetings", 0) + 1
    rel2["meetings"] = rel2.get("meetings", 0) + 1
    rel1["last_tick"] = tick
    rel2["last_tick"] = tick
    
    # Add context if new
    if context and context not in rel1.get("contexts", []):
        rel1.setdefault("contexts", []).append(context)
        rel2.setdefault("contexts", []).append(context)
    
    # Calculate trust change based on context
    trust_change = TRUST_CHANGES.get(f"same_{context}", TRUST_CHANGES["same_location"])
    
    # Bonus for recurring meetings (familiarity)
    meetings = rel1["meetings"]
    if meetings > 10:
        trust_change *= 1.2
    if meetings > 25:
        trust_change *= 1.3
    
    # Apply trust change
    rel1["trust"] = min(1.0, max(-1.0, rel1.get("trust", 0.1) + trust_change))
    rel2["trust"] = min(1.0, max(-1.0, rel2.get("trust", 0.1) + trust_change))
    
    # Update relationship type
    rel1["type"] = get_relationship_type(rel1["trust"])
    rel2["type"] = get_relationship_type(rel2["trust"])
    
    return {
        "type": "meeting",
        "npc1": npc1["id"],
        "npc2": npc2["id"],
        "context": context,
        "meetings_total": meetings,
        "trust_after": rel1["trust"],
        "relationship": rel1["type"],
    }


def update_trust_from_interaction(npc1: dict, npc2: dict, 
                                   interaction_type: str, tick: int) -> dict:
    """
    Update trust based on an interaction event.
    Called after calculate_interaction() in simulation_behaviors.py
    """
    rel1 = get_or_create_relationship(npc1, npc2["id"])
    rel2 = get_or_create_relationship(npc2, npc1["id"])
    
    trust_change = TRUST_CHANGES.get(interaction_type, 0)
    
    # Apply change
    old_trust = rel1.get("trust", 0.1)
    rel1["trust"] = min(1.0, max(-1.0, old_trust + trust_change))
    rel2["trust"] = min(1.0, max(-1.0, rel2.get("trust", 0.1) + trust_change))
    
    # Update relationship type
    old_type = rel1.get("type", "stranger")
    new_type = get_relationship_type(rel1["trust"])
    rel1["type"] = new_type
    rel2["type"] = new_type
    
    # Record significant events
    if abs(trust_change) >= 0.05:
        rel1.setdefault("shared_events", []).append(f"{interaction_type}@{tick}")
        rel2.setdefault("shared_events", []).append(f"{interaction_type}@{tick}")
    
    return {
        "type": "trust_updated",
        "npc1": npc1["id"],
        "npc2": npc2["id"],
        "interaction": interaction_type,
        "trust_change": trust_change,
        "trust_before": old_trust,
        "trust_after": rel1["trust"],
        "relationship_before": old_type,
        "relationship_after": new_type,
    }


# =============================================================================
# GROUP FORMATION
# =============================================================================

def find_potential_groups(npcs: List[dict], tick: int) -> List[SocialGroup]:
    """
    Identify potential social groups based on shared attributes.
    Called periodically (e.g., daily) to form new groups.
    """
    groups = []
    
    # Group by workplace
    workplaces = {}
    for npc in npcs:
        wp = npc.get("workplace")
        if wp:
            workplaces.setdefault(wp, []).append(npc["id"])
    
    for wp, members in workplaces.items():
        if len(members) >= 3:
            groups.append(SocialGroup(
                id=f"WORK_{wp}_{tick}",
                name=f"{wp} Team",
                group_type="coworkers",
                members=members[:10],  # Limit group size
                meeting_location=wp,
                formed_tick=tick,
                bond_strength=0.6,
            ))
    
    # Group by home building
    buildings = {}
    for npc in npcs:
        home = npc.get("home") or npc.get("family", {}).get("household_id")
        if home:
            buildings.setdefault(home, []).append(npc["id"])
    
    for bldg, members in buildings.items():
        if len(members) >= 3:
            groups.append(SocialGroup(
                id=f"NEIGHBOR_{bldg}_{tick}",
                name=f"{bldg} Neighbors",
                group_type="neighbors",
                members=members[:15],
                meeting_location=bldg,
                formed_tick=tick,
                bond_strength=0.4,
            ))
    
    # Group by faction
    factions = {}
    for npc in npcs:
        faction = npc.get("faction")
        if faction:
            factions.setdefault(faction, []).append(npc["id"])
    
    for faction, members in factions.items():
        # Create cells of 5-8 members
        for i in range(0, len(members), 6):
            cell = members[i:i+6]
            if len(cell) >= 3:
                groups.append(SocialGroup(
                    id=f"CELL_{faction}_{i}_{tick}",
                    name=f"{faction.title()} Cell {i//6 + 1}",
                    group_type="faction_cell",
                    members=cell,
                    formed_tick=tick,
                    bond_strength=0.7,
                ))
    
    return groups


def form_friend_groups(npcs: List[dict], tick: int) -> List[SocialGroup]:
    """
    Form friend groups based on high-trust relationships.
    NPCs with mutual high trust form cliques.
    """
    groups = []
    processed = set()
    
    for npc in npcs:
        if npc["id"] in processed:
            continue
        
        relationships = npc.get("relationships", {})
        friends = []
        
        for other_id, rel in relationships.items():
            if rel.get("trust", 0) >= 0.65 and rel.get("meetings", 0) >= 25:
                friends.append(other_id)
        
        if len(friends) >= 2:
            # Found a potential friend group
            group_members = [npc["id"]] + friends[:5]
            processed.update(group_members)
            
            groups.append(SocialGroup(
                id=f"FRIENDS_{npc['id']}_{tick}",
                name=f"{npc.get('name', npc['id'])}'s Circle",
                group_type="friends",
                members=group_members,
                formed_tick=tick,
                bond_strength=0.8,
            ))
    
    return groups


# =============================================================================
# GOSSIP SYSTEM
# =============================================================================

def spread_gossip(source_npc: dict, about_npc: dict, event_type: str,
                  event_valence: str, witnesses: List[dict], tick: int) -> List[dict]:
    """
    Spread reputation through gossip.
    When an NPC witnesses an event, they may tell others about it.
    
    Args:
        source_npc: NPC who witnessed the event
        about_npc: NPC the event is about
        event_type: What happened (helped, stole, fought)
        event_valence: positive, negative, or neutral
        witnesses: Other NPCs at the same location
        tick: Current tick
    
    Returns:
        List of gossip events that occurred
    """
    gossip_events = []
    
    # Each witness has a chance to spread the gossip
    for witness in witnesses:
        if witness["id"] == source_npc["id"] or witness["id"] == about_npc["id"]:
            continue
        
        # Check if witness will gossip (based on social personality)
        seed = f"gossip_{source_npc['id']}_{witness['id']}_{tick}"
        social_trait = witness.get("personality", {}).get("extraversion", 0.5)
        gossip_chance = 0.2 + (social_trait * 0.3)  # 20-50% chance
        
        if not deterministic_chance(gossip_chance, seed):
            continue
        
        # Witness learns about the event
        rel = get_or_create_relationship(witness, about_npc["id"])
        
        # Trust change based on event
        if event_valence == "positive":
            trust_change = 0.02  # Hearing good things
        elif event_valence == "negative":
            trust_change = -0.03  # Hearing bad things
        else:
            trust_change = 0
        
        # Weight by trust in source (do they believe the gossip?)
        source_trust = witness.get("relationships", {}).get(
            source_npc["id"], {}
        ).get("trust", 0.3)
        
        if source_trust < 0.3:
            trust_change *= 0.5  # Don't fully believe untrusted source
        
        old_trust = rel.get("trust", 0.1)
        rel["trust"] = min(1.0, max(-1.0, old_trust + trust_change))
        rel["type"] = get_relationship_type(rel["trust"])
        
        gossip_events.append({
            "type": "gossip_spread",
            "source": source_npc["id"],
            "about": about_npc["id"],
            "heard_by": witness["id"],
            "event": event_type,
            "valence": event_valence,
            "trust_change": trust_change,
            "tick": tick,
        })
    
    return gossip_events


def get_reputation(npc: dict, all_npcs: List[dict]) -> dict:
    """
    Calculate NPC's overall reputation based on how others view them.
    """
    positive_views = 0
    negative_views = 0
    neutral_views = 0
    total_trust = 0
    count = 0
    
    for other in all_npcs:
        if other["id"] == npc["id"]:
            continue
        
        rel = other.get("relationships", {}).get(npc["id"])
        if rel:
            trust = rel.get("trust", 0.1)
            total_trust += trust
            count += 1
            
            if trust > 0.5:
                positive_views += 1
            elif trust < 0.2:
                negative_views += 1
            else:
                neutral_views += 1
    
    avg_trust = total_trust / count if count > 0 else 0.1
    
    return {
        "npc_id": npc["id"],
        "average_trust": round(avg_trust, 3),
        "positive_views": positive_views,
        "negative_views": negative_views,
        "neutral_views": neutral_views,
        "total_known_by": count,
        "reputation_level": (
            "beloved" if avg_trust > 0.7 else
            "respected" if avg_trust > 0.5 else
            "known" if avg_trust > 0.3 else
            "obscure" if count < 5 else
            "distrusted" if avg_trust < 0.2 else
            "neutral"
        ),
    }


# =============================================================================
# API HELPERS
# =============================================================================

def get_npc_social_summary(npc: dict) -> dict:
    """Get social summary for an NPC."""
    relationships = npc.get("relationships", {})
    
    friends = []
    colleagues = []
    acquaintances = []
    rivals = []
    
    for other_id, rel in relationships.items():
        rel_type = rel.get("type", "stranger")
        trust = rel.get("trust", 0.1)
        
        summary = {
            "npc_id": other_id,
            "trust": round(trust, 2),
            "meetings": rel.get("meetings", 0),
        }
        
        if rel_type in ["friend", "close_friend"]:
            friends.append(summary)
        elif rel_type == "colleague":
            colleagues.append(summary)
        elif rel_type == "acquaintance":
            acquaintances.append(summary)
        elif rel_type in ["rival", "enemy"]:
            rivals.append(summary)
    
    return {
        "npc_id": npc["id"],
        "friends": sorted(friends, key=lambda x: -x["trust"])[:10],
        "colleagues": sorted(colleagues, key=lambda x: -x["meetings"])[:10],
        "acquaintances": len(acquaintances),
        "rivals": rivals,
        "total_relationships": len(relationships),
    }


def process_location_meetings(npcs_at_location: List[dict], 
                               location: str, tick: int) -> List[dict]:
    """
    Process all NPC meetings at a location for this tick.
    Called during tick simulation for each location.
    """
    events = []
    
    # Determine context from location
    context = "location"
    if "work" in location.lower() or "office" in location.lower():
        context = "workplace"
    elif "home" in location.lower() or "hab" in location.lower():
        context = "building"
    elif "bar" in location.lower() or "anchor" in location.lower():
        context = "bar"
    
    # Track meetings between all pairs
    for i, npc1 in enumerate(npcs_at_location):
        for npc2 in npcs_at_location[i+1:]:
            event = track_meeting(npc1, npc2, context, tick)
            if event.get("type") == "meeting":
                events.append(event)
    
    return events


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  SOCIAL DYNAMICS SYSTEM - Demo")
    print("=" * 60)
    
    # Create test NPCs
    npc1 = {"id": "NPC_001", "name": "Alice", "workplace": "TechCorp", "relationships": {}}
    npc2 = {"id": "NPC_002", "name": "Bob", "workplace": "TechCorp", "relationships": {}}
    npc3 = {"id": "NPC_003", "name": "Charlie", "workplace": "TechCorp", "relationships": {}}
    
    print("\n📊 Initial State: Three coworkers at TechCorp")
    
    # Simulate 30 days of meetings at work
    print("\n⏰ Simulating 30 days of workplace meetings...")
    
    for day in range(30):
        tick = day * 240  # 240 ticks per day
        
        # They meet at work each day
        event1 = track_meeting(npc1, npc2, "workplace", tick)
        event2 = track_meeting(npc1, npc3, "workplace", tick)
        event3 = track_meeting(npc2, npc3, "workplace", tick)
        
        if day % 10 == 9:
            rel = npc1["relationships"].get("NPC_002", {})
            print(f"\n  Day {day + 1}:")
            print(f"    Alice → Bob: {rel.get('meetings', 0)} meetings, "
                  f"trust={rel.get('trust', 0):.2f}, "
                  f"type={rel.get('type', 'stranger')}")
    
    print("\n" + "=" * 60)
    print("  Final Relationship States")
    print("=" * 60)
    
    for npc in [npc1, npc2, npc3]:
        print(f"\n  {npc['name']}'s relationships:")
        summary = get_npc_social_summary(npc)
        print(f"    Colleagues: {len(summary['colleagues'])}")
        for col in summary['colleagues']:
            print(f"      - {col['npc_id']}: {col['meetings']} meetings, trust={col['trust']}")
    
    # Test gossip
    print("\n" + "=" * 60)
    print("  Testing Gossip System")
    print("=" * 60)
    
    # Alice helps someone, Bob and Charlie witness it
    npc4 = {"id": "NPC_004", "name": "Diana", "relationships": {}, "personality": {"extraversion": 0.7}}
    
    gossip = spread_gossip(
        source_npc=npc2,  # Bob saw it
        about_npc=npc1,   # It was about Alice
        event_type="helped_stranger",
        event_valence="positive",
        witnesses=[npc3, npc4],  # Charlie and Diana might hear
        tick=7200  # Day 30
    )
    
    print(f"\n  Gossip events: {len(gossip)}")
    for g in gossip:
        print(f"    {g['heard_by']} heard that {g['about']} {g['event']}")
    
    print("\n✅ Social dynamics working!")

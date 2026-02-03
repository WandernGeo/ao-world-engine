#!/usr/bin/env python3
"""
RE:ECHO Event Engine - Deterministic Event Generation
======================================================

Generates events from tick seeds using the World Codec.
Events are NOT computed - they are REVEALED from the deterministic seed.

Usage:
    from event_engine import get_events_before_tick, decode_event
    
    # Get all events Charlie experienced before tick 100
    events = get_events_before_tick("charlie", 100)
    
    # Decode a specific event
    event = decode_event("A01-C09-L08-T050")
    # Returns: {"action": "meet", "target": "aiche", "location": "alley", "tick": 50}
"""

import json
import hashlib
import os
from typing import List, Dict, Optional

# Load the World Codec
CODEC_PATH = os.path.join(os.path.dirname(__file__), "world_codec.json")

def load_codec() -> dict:
    """Load the World Codec JSON."""
    try:
        with open(CODEC_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️ World Codec not found at {CODEC_PATH}")
        return {}

CODEC = load_codec()


def deterministic_hash(seed_string: str) -> int:
    """Generate a deterministic integer hash from a seed string."""
    return int(hashlib.md5(seed_string.encode()).hexdigest(), 16)


def get_action_list() -> List[str]:
    """Get ordered list of actions from codec."""
    actions = CODEC.get("actions", {})
    return [v for k, v in sorted(actions.items()) if not k.startswith("_")]


def get_object_list() -> List[str]:
    """Get ordered list of objects from codec."""
    objects = CODEC.get("objects", {})
    return [v for k, v in sorted(objects.items()) if not k.startswith("_")]


def get_location_list() -> List[dict]:
    """Get ordered list of locations from codec."""
    locations = CODEC.get("locations", {})
    return [v for k, v in sorted(locations.items()) if not k.startswith("_")]


def get_npc_list() -> List[dict]:
    """Get ordered list of NPCs from codec."""
    npcs = CODEC.get("npcs", {})
    return [v for k, v in sorted(npcs.items()) if not k.startswith("_")]


def get_emotion_list() -> List[str]:
    """Get ordered list of emotions from codec."""
    emotions = CODEC.get("emotions", {})
    return [v for k, v in sorted(emotions.items()) if not k.startswith("_")]


def does_event_occur(npc_id: str, tick: int, event_probability: float = 0.05) -> bool:
    """
    Determine if an event occurs at this tick for this NPC.
    Default: 5% chance per tick.
    """
    seed = deterministic_hash(f"{npc_id}_event_check_{tick}")
    return (seed % 1000) < (event_probability * 1000)


def generate_event_at_tick(npc_id: str, tick: int) -> Optional[Dict]:
    """
    Generate the deterministic event that occurs at this tick.
    Returns None if no event occurs.
    """
    if not does_event_occur(npc_id, tick):
        return None
    
    seed = deterministic_hash(f"{npc_id}_event_data_{tick}")
    
    actions = get_action_list()
    npcs = get_npc_list()
    locations = get_location_list()
    objects = get_object_list()
    
    if not actions or not npcs or not locations:
        return None
    
    # Extract different parts of the seed for different aspects
    action_idx = seed % len(actions)
    target_idx = (seed >> 8) % len(npcs)
    location_idx = (seed >> 16) % len(locations)
    object_idx = (seed >> 24) % len(objects) if objects else 0
    
    action = actions[action_idx]
    target = npcs[target_idx]
    location = locations[location_idx]
    obj = objects[object_idx] if objects else None
    
    # Skip self-referential events
    if target.get("n") == npc_id:
        target_idx = (target_idx + 1) % len(npcs)
        target = npcs[target_idx]
    
    # Determine event type based on action
    event_type = categorize_action(action)
    
    event = {
        "tick": tick,
        "npc_id": npc_id,
        "action": action,
        "action_code": f"A{(action_idx + 1):02d}",
        "type": event_type,
        "target_npc": target.get("n"),
        "target_name": target.get("f"),
        "location": location.get("n"),
        "location_desc": location.get("d"),
    }
    
    # Add object for trade/use events
    if event_type in ["trade", "use", "discover"]:
        event["object"] = obj
    
    return event


def categorize_action(action: str) -> str:
    """Categorize an action into event types."""
    social_actions = ["meet", "talk", "whisper", "give", "trade", "confess"]
    combat_actions = ["fight", "attack", "shoot", "slash", "punch", "kick", "throw", "block", "dodge"]
    stealth_actions = ["steal", "hide", "bypass", "hack", "break"]
    medical_actions = ["heal", "inject"]
    tech_actions = ["hack", "install", "repair", "scan", "upload", "download", "encrypt", "decrypt"]
    
    if action in social_actions:
        return "social"
    elif action in combat_actions:
        return "combat"
    elif action in stealth_actions:
        return "stealth"
    elif action in medical_actions:
        return "medical"
    elif action in tech_actions:
        return "tech"
    else:
        return "general"


def get_events_before_tick(npc_id: str, current_tick: int, max_events: int = 10) -> List[Dict]:
    """
    Get all significant events that occurred before the current tick.
    Limits to most recent max_events for performance.
    """
    events = []
    
    # Scan backwards from current tick
    for tick in range(max(0, current_tick - 500), current_tick):
        event = generate_event_at_tick(npc_id, tick)
        if event:
            events.append(event)
            if len(events) >= max_events:
                break
    
    # Return most recent first
    return list(reversed(events[-max_events:]))


def get_relationship_at_tick(npc_id: str, other_npc_id: str, tick: int) -> Dict:
    """
    Determine the relationship status between two NPCs at a given tick.
    Relationship evolves based on shared events.
    """
    seed = deterministic_hash(f"relationship_{min(npc_id, other_npc_id)}_{max(npc_id, other_npc_id)}_{tick // 100}")
    
    relationships = list(CODEC.get("relationships", {}).values())
    relationships = [r for r in relationships if not isinstance(r, dict)]
    
    if not relationships:
        return {"type": "stranger", "trust": 0.5}
    
    rel_type = relationships[seed % len(relationships)]
    trust = (seed >> 8) % 100 / 100.0
    
    # Meeting history affects trust
    met_count = 0
    for t in range(0, tick, 10):  # Sample every 10 ticks for performance
        if does_event_occur(npc_id, t):
            event = generate_event_at_tick(npc_id, t)
            if event and event.get("target_npc") == other_npc_id:
                met_count += 1
    
    # More meetings = stronger relationship
    trust = min(1.0, trust + met_count * 0.1)
    
    return {
        "type": rel_type,
        "trust": round(trust, 2),
        "met_count": met_count,
        "since_tick": deterministic_hash(f"rel_start_{npc_id}_{other_npc_id}") % tick if tick > 0 else 0
    }


def get_npc_memory_context(npc_id: str, tick: int) -> str:
    """
    Generate a natural language memory context for an NPC.
    This can be injected into the LLM prompt for context-aware responses.
    """
    events = get_events_before_tick(npc_id, tick, max_events=5)
    
    if not events:
        return "No significant recent events."
    
    def ticks_to_time_ago(tick_diff: int) -> str:
        """Convert tick difference to human-readable time."""
        if tick_diff <= 0:
            return "just now"
        
        # 1 tick = 1 hour, 24 ticks = 1 day
        hours = tick_diff
        days = tick_diff // 24
        remaining_hours = tick_diff % 24
        
        if days == 0:
            if hours == 1:
                return "1 hour ago"
            return f"{hours} hours ago"
        elif days == 1:
            if remaining_hours == 0:
                return "yesterday"
            return f"yesterday, {remaining_hours}h ago"
        elif days < 7:
            return f"{days} days ago"
        elif days < 30:
            weeks = days // 7
            return f"{weeks} week{'s' if weeks > 1 else ''} ago"
        else:
            return f"{days} days ago"
    
    memory_lines = []
    for event in events:
        tick_diff = tick - event["tick"]
        time_ago = ticks_to_time_ago(tick_diff)
        
        if event["type"] == "social":
            memory_lines.append(f"- {time_ago}: {event['action'].capitalize()}ed {event['target_name']} at {event['location'].replace('_', ' ')}")
        elif event["type"] == "combat":
            memory_lines.append(f"- {time_ago}: {event['action'].capitalize()} at {event['location'].replace('_', ' ')} (combat)")
        else:
            memory_lines.append(f"- {time_ago}: {event['action'].capitalize()} at {event['location'].replace('_', ' ')}")
    
    return "Recent memories:\n" + "\n".join(memory_lines)


def encode_event(action_code: str, target_code: str, location_code: str, tick: int) -> str:
    """Encode an event to compact string format."""
    return f"{action_code}-{target_code}-{location_code}-T{tick:05d}"


def decode_event(encoded: str) -> Dict:
    """Decode a compact event string to full event data."""
    parts = encoded.split("-")
    if len(parts) < 4:
        return {"error": "Invalid event format"}
    
    action_code = parts[0]
    target_code = parts[1]
    location_code = parts[2]
    tick = int(parts[3].replace("T", ""))
    
    # Look up in codec
    actions = CODEC.get("actions", {})
    npcs = CODEC.get("npcs", {})
    locations = CODEC.get("locations", {})
    
    return {
        "action": actions.get(action_code, action_code),
        "target": npcs.get(target_code, {}).get("n", target_code),
        "target_name": npcs.get(target_code, {}).get("f", target_code),
        "location": locations.get(location_code, {}).get("n", location_code),
        "tick": tick
    }


# ============================================================
# DEMO / TEST
# ============================================================

if __name__ == "__main__":
    print("RE:ECHO Event Engine - Deterministic World State")
    print("=" * 50)
    
    # Test: Get Charlie's events before tick 100
    print("\n📜 Charlie's memories at Tick 100:")
    events = get_events_before_tick("charlie", 100, max_events=5)
    for e in events:
        print(f"  Tick {e['tick']}: {e['action']} → {e['target_name']} at {e['location']}")
    
    # Test: Memory context for LLM
    print("\n💭 Memory context for LLM prompt:")
    context = get_npc_memory_context("charlie", 100)
    print(context)
    
    # Test: Relationship
    print("\n🤝 Charlie's relationship with Aiche at tick 100:")
    rel = get_relationship_at_tick("charlie", "aiche", 100)
    print(f"  Type: {rel['type']}, Trust: {rel['trust']}, Met: {rel['met_count']} times")
    
    # Test: Different ticks show different memories
    print("\n⏱️ Charlie's memories at different ticks:")
    for tick in [50, 100, 500, 1000]:
        events = get_events_before_tick("charlie", tick, max_events=3)
        print(f"  Tick {tick}: {len(events)} events")
        for e in events:
            print(f"    - Tick {e['tick']}: {e['action']} with {e['target_name']}")

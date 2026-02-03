#!/usr/bin/env python3
"""
NPC Relationships - Persistent NPC-to-NPC Memory System
========================================================

Stores and manages NPC relationships and interactions:
- Relationship scores (trust, familiarity)
- Interaction history
- NPC memories of other NPCs

All data persists to JSON files for self-evolving world state.
"""

import json
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any

# Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), "npc_interactions")
RELATIONSHIPS_FILE = os.path.join(DATA_DIR, "relationships.json")
INTERACTION_LOG_FILE = os.path.join(DATA_DIR, "interaction_log.json")
SIGNIFICANT_EVENTS_FILE = os.path.join(DATA_DIR, "significant_events.json")
NPC_MEMORY_DIR = os.path.join(DATA_DIR, "npc_memory")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(NPC_MEMORY_DIR, exist_ok=True)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def load_json(path: str, default: Any = None) -> Any:
    """Load JSON file, return default if not found."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def save_json(path: str, data: Any):
    """Save data to JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def get_relationship_key(npc1_id: str, npc2_id: str) -> str:
    """Generate consistent key for NPC pair (alphabetically ordered)."""
    return f"{min(npc1_id, npc2_id)}_{max(npc1_id, npc2_id)}"


# =============================================================================
# RELATIONSHIP EFFECTS
# =============================================================================

RELATIONSHIP_EFFECTS = {
    # Positive interactions
    "greeting": {"trust": 0.01, "familiarity": 0.02},
    "nod": {"trust": 0.005, "familiarity": 0.01},
    "small_talk": {"trust": 0.02, "familiarity": 0.05},
    "deep_conversation": {"trust": 0.05, "familiarity": 0.10},
    "trade": {"trust": 0.03, "familiarity": 0.03},
    "favor_exchange": {"trust": 0.10, "familiarity": 0.05},
    "helped_in_combat": {"trust": 0.20, "familiarity": 0.15},
    "shared_meal": {"trust": 0.04, "familiarity": 0.08},
    "worked_together": {"trust": 0.03, "familiarity": 0.06},
    
    # Negative interactions
    "wary_glance": {"trust": -0.01},
    "avoid": {"trust": -0.02},
    "argument": {"trust": -0.10, "familiarity": 0.02},  # Still get to know them
    "fight": {"trust": -0.30, "familiarity": 0.05},
    "betrayal": {"trust": -0.50},
    "witnessed_crime": {"trust": -0.20},
    
    # Neutral
    "ignore": {},
}

# Significant events that get stored long-term
SIGNIFICANT_INTERACTION_TYPES = {
    "deep_conversation", "favor_exchange", "helped_in_combat",
    "fight", "betrayal", "witnessed_crime", "trade"
}


# =============================================================================
# RELATIONSHIP MANAGEMENT
# =============================================================================

def load_relationships() -> Dict:
    """Load all NPC relationships."""
    return load_json(RELATIONSHIPS_FILE, default={})


def save_relationships(relationships: Dict):
    """Save all NPC relationships."""
    save_json(RELATIONSHIPS_FILE, relationships)


def get_relationship(npc1_id: str, npc2_id: str) -> Dict:
    """Get relationship between two NPCs."""
    relationships = load_relationships()
    key = get_relationship_key(npc1_id, npc2_id)
    
    return relationships.get(key, {
        "trust": 0.5,  # Neutral starting trust
        "familiarity": 0.0,  # Never met
        "met_count": 0,
        "first_met_tick": None,
        "last_interaction_tick": None,
        "relationship_type": "stranger"
    })


def update_relationship(npc1_id: str, npc2_id: str, interaction_type: str, tick: int):
    """Update relationship based on an interaction."""
    relationships = load_relationships()
    key = get_relationship_key(npc1_id, npc2_id)
    
    # Get existing or create new
    rel = relationships.get(key, {
        "trust": 0.5,
        "familiarity": 0.0,
        "met_count": 0,
        "first_met_tick": tick,
        "relationship_type": "stranger"
    })
    
    # Apply effects
    effects = RELATIONSHIP_EFFECTS.get(interaction_type, {})
    for stat, change in effects.items():
        if stat in ["trust", "familiarity"]:
            current = rel.get(stat, 0.5 if stat == "trust" else 0.0)
            rel[stat] = max(0.0, min(1.0, current + change))
    
    # Update metadata
    rel["met_count"] = rel.get("met_count", 0) + 1
    rel["last_interaction_tick"] = tick
    if rel.get("first_met_tick") is None:
        rel["first_met_tick"] = tick
    
    # Determine relationship type based on trust
    trust = rel.get("trust", 0.5)
    if trust >= 0.8:
        rel["relationship_type"] = "ally"
    elif trust >= 0.6:
        rel["relationship_type"] = "friend"
    elif trust >= 0.4:
        rel["relationship_type"] = "acquaintance"
    elif trust >= 0.2:
        rel["relationship_type"] = "wary"
    else:
        rel["relationship_type"] = "hostile"
    
    relationships[key] = rel
    save_relationships(relationships)
    
    return rel


def get_npc_relationships(npc_id: str) -> Dict[str, Dict]:
    """Get all relationships for a specific NPC."""
    relationships = load_relationships()
    npc_rels = {}
    
    for key, rel in relationships.items():
        parts = key.split("_", 1)
        if len(parts) == 2:
            if parts[0] == npc_id:
                npc_rels[parts[1]] = rel
            elif parts[1] == npc_id:
                npc_rels[parts[0]] = rel
    
    return npc_rels


# =============================================================================
# INTERACTION LOG
# =============================================================================

def record_interaction(npc1_id: str, npc2_id: str, interaction_type: str, 
                       tick: int, location: str = None, details: Dict = None):
    """
    Record an interaction between two NPCs.
    
    Args:
        npc1_id: First NPC
        npc2_id: Second NPC
        interaction_type: Type of interaction (greeting, trade, fight, etc.)
        tick: Simulation tick
        location: Where the interaction occurred
        details: Additional details
    """
    log = load_json(INTERACTION_LOG_FILE, default=[])
    
    interaction = {
        "id": f"INT_{tick}_{npc1_id[:8]}_{npc2_id[:8]}",
        "npc1": npc1_id,
        "npc2": npc2_id,
        "type": interaction_type,
        "tick": tick,
        "location": location,
        "timestamp": datetime.now().isoformat()
    }
    
    if details:
        interaction["details"] = details
    
    log.append(interaction)
    
    # Keep last 1000 interactions
    log = log[-1000:]
    save_json(INTERACTION_LOG_FILE, log)
    
    # Update relationship scores
    update_relationship(npc1_id, npc2_id, interaction_type, tick)
    
    # Store significant events separately
    if interaction_type in SIGNIFICANT_INTERACTION_TYPES:
        record_significant_event(interaction)
    
    # Add to NPC memories
    if interaction_type in SIGNIFICANT_INTERACTION_TYPES:
        add_npc_memory(npc1_id, {
            "type": "interaction",
            "with_npc": npc2_id,
            "interaction": interaction_type,
            "location": location,
            "tick": tick
        })
        add_npc_memory(npc2_id, {
            "type": "interaction",
            "with_npc": npc1_id,
            "interaction": interaction_type,
            "location": location,
            "tick": tick
        })
    
    return interaction


def get_recent_interactions(npc_id: str = None, limit: int = 50) -> List[Dict]:
    """Get recent interactions, optionally filtered by NPC."""
    log = load_json(INTERACTION_LOG_FILE, default=[])
    
    if npc_id:
        log = [i for i in log if i.get("npc1") == npc_id or i.get("npc2") == npc_id]
    
    return log[-limit:]


# =============================================================================
# SIGNIFICANT EVENTS
# =============================================================================

def record_significant_event(event: Dict):
    """Store a significant event for long-term memory / Arweave export."""
    events = load_json(SIGNIFICANT_EVENTS_FILE, default=[])
    events.append(event)
    save_json(SIGNIFICANT_EVENTS_FILE, events)


def get_significant_events(limit: int = 100) -> List[Dict]:
    """Get significant events for lore / Arweave export."""
    events = load_json(SIGNIFICANT_EVENTS_FILE, default=[])
    return events[-limit:]


# =============================================================================
# NPC MEMORIES
# =============================================================================

def get_npc_memory_path(npc_id: str) -> str:
    """Get path to NPC's memory file."""
    return os.path.join(NPC_MEMORY_DIR, f"{npc_id}.json")


def load_npc_memory(npc_id: str) -> Dict:
    """Load an NPC's memories."""
    return load_json(get_npc_memory_path(npc_id), default={
        "about_npcs": {},  # Memories about other NPCs
        "events": [],      # Significant events witnessed
        "facts": {}        # Learned facts
    })


def save_npc_memory(npc_id: str, memory: Dict):
    """Save an NPC's memories."""
    save_json(get_npc_memory_path(npc_id), memory)


def add_npc_memory(npc_id: str, memory_item: Dict):
    """
    Add a memory to an NPC's memory file.
    
    Args:
        npc_id: The NPC who is remembering
        memory_item: The memory to add
            - type: "interaction", "witnessed_event", "learned_fact"
            - with_npc: (optional) Other NPC involved
            - tick: When it happened
            - details: What happened
    """
    memory = load_npc_memory(npc_id)
    
    # If about another NPC, store in about_npcs
    other_npc = memory_item.get("with_npc")
    if other_npc:
        if other_npc not in memory["about_npcs"]:
            memory["about_npcs"][other_npc] = {
                "first_met_tick": memory_item.get("tick"),
                "impressions": [],
                "interactions": []
            }
        
        npc_memory = memory["about_npcs"][other_npc]
        npc_memory["last_seen_tick"] = memory_item.get("tick")
        
        # Add interaction summary
        interaction_type = memory_item.get("interaction", memory_item.get("type"))
        if interaction_type:
            npc_memory["interactions"].append({
                "type": interaction_type,
                "tick": memory_item.get("tick"),
                "location": memory_item.get("location")
            })
            # Keep last 10 interactions per NPC
            npc_memory["interactions"] = npc_memory["interactions"][-10:]
        
        # Derive impression from interaction type
        impression = derive_impression(interaction_type)
        if impression:
            npc_memory["impressions"].append(impression)
            npc_memory["impressions"] = npc_memory["impressions"][-5:]  # Keep last 5
    
    # Add to events list
    memory["events"].append(memory_item)
    memory["events"] = memory["events"][-50:]  # Keep last 50 events
    
    save_npc_memory(npc_id, memory)


def derive_impression(interaction_type: str) -> Optional[str]:
    """Derive an impression from an interaction type."""
    impressions = {
        "greeting": "friendly",
        "small_talk": "sociable",
        "deep_conversation": "thoughtful",
        "trade": "businesslike",
        "favor_exchange": "helpful",
        "helped_in_combat": "brave",
        "argument": "contentious",
        "fight": "dangerous",
        "avoid": "distant"
    }
    return impressions.get(interaction_type)


def get_npc_memory_context(npc_id: str, about_npc_id: str = None) -> str:
    """
    Get formatted memory context for LLM prompt.
    
    Args:
        npc_id: The NPC whose memories to retrieve
        about_npc_id: (optional) Focus on memories about specific NPC
    
    Returns:
        Formatted string for LLM context
    """
    memory = load_npc_memory(npc_id)
    lines = []
    
    if about_npc_id and about_npc_id in memory.get("about_npcs", {}):
        # Focused memory about one NPC
        npc_mem = memory["about_npcs"][about_npc_id]
        lines.append(f"About {about_npc_id}:")
        if npc_mem.get("impressions"):
            lines.append(f"  Impressions: {', '.join(npc_mem['impressions'][-3:])}")
        if npc_mem.get("interactions"):
            recent = npc_mem["interactions"][-3:]
            for i in recent:
                lines.append(f"  - {i['type']} at {i.get('location', 'unknown')}")
    else:
        # General memory summary
        about = memory.get("about_npcs", {})
        if about:
            lines.append("People I know:")
            for other_id, mem in list(about.items())[:5]:  # Top 5
                impressions = ", ".join(mem.get("impressions", [])[-2:]) or "no strong impression"
                lines.append(f"  - {other_id}: {impressions}")
    
    return "\n".join(lines) if lines else "No significant memories."


# =============================================================================
# ARWEAVE EXPORT
# =============================================================================

def prepare_arweave_batch() -> Dict:
    """
    Prepare data for Arweave upload.
    Returns a batch of significant data under 100KB.
    """
    relationships = load_relationships()
    events = get_significant_events(limit=50)
    
    batch = {
        "type": "npc_interaction_history",
        "exported_at": datetime.now().isoformat(),
        "relationship_count": len(relationships),
        "event_count": len(events),
        "relationships_sample": dict(list(relationships.items())[:20]),
        "significant_events": events
    }
    
    # Ensure under 100KB
    batch_json = json.dumps(batch)
    if len(batch_json) > 95000:
        batch["significant_events"] = events[:25]
        batch["relationships_sample"] = dict(list(relationships.items())[:10])
    
    return batch


# =============================================================================
# DEMO / TEST
# =============================================================================

if __name__ == "__main__":
    print("NPC Relationships System - Test")
    print("=" * 50)
    
    # Test interaction
    print("\n📝 Recording interaction: Charlie greets Felix at Neon Bar")
    record_interaction("charlie", "felix", "greeting", tick=100, location="neon_bar")
    
    print("\n📝 Recording interaction: Charlie has deep conversation with Felix")
    record_interaction("charlie", "felix", "deep_conversation", tick=150, location="neon_bar")
    
    # Check relationship
    print("\n🤝 Charlie-Felix relationship:")
    rel = get_relationship("charlie", "felix")
    print(f"   Trust: {rel['trust']:.2f}")
    print(f"   Familiarity: {rel['familiarity']:.2f}")
    print(f"   Met count: {rel['met_count']}")
    print(f"   Type: {rel['relationship_type']}")
    
    # Check Charlie's memories
    print("\n💭 Charlie's memories:")
    memory = load_npc_memory("charlie")
    print(f"   About NPCs: {list(memory.get('about_npcs', {}).keys())}")
    print(f"   Events: {len(memory.get('events', []))}")
    
    # Memory context for LLM
    print("\n📜 Memory context for LLM:")
    context = get_npc_memory_context("charlie")
    print(context)
    
    print("\n✅ Test complete!")

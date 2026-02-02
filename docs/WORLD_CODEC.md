# World Codec System

> Deterministic knowledge dictionary for RE:ECHO City simulation

## Overview

The World Codec is a compressed encoding system that allows the simulation to:
1. **Store all world knowledge** in ~15KB (under Arweave free tier)
2. **Generate deterministic events** from tick seeds
3. **Reveal NPC memories** without storing actual event logs

## Core Concept

```
The universe is pre-baked. We don't COMPUTE events - we REVEAL them.

hash("charlie_tick_50_event") → 0xA3F2B1C4...
                                    ↓
                              Decode bits:
                              Action = bits[0:6] % 60  → "meet"
                              Target = bits[8:16] % 12 → "aiche"  
                              Location = bits[16:24] % 30 → "alley"
```

## File Structure

```
data/
├── world_codec.json    # Knowledge dictionary (~15KB)
├── event_engine.py     # Deterministic event generator
└── founding_npcs.py    # Character profiles
```

## Codec Categories

| Category | Codes | Example |
|----------|-------|---------|
| Actions | A01-A60 | A01 = "meet", A03 = "fight" |
| Objects | O01-O100 | O11 = "datapad", O26 = "pistol" |
| Locations | L01-L30 | L01 = "neon_bar", L08 = "alley" |
| NPCs | C01-C12 | C01 = "charlie", C09 = "aiche" |
| Cybernetics | Y01-Y40 | Y02 = "holographic_arm" |
| Medical | M01-M40 | M01 = "injured", M27 = "painkiller" |
| Electronics | E01-E30 | E11 = "breach", E22 = "virus" |

## How Events Are Generated

```python
from data.event_engine import get_events_before_tick

# Get what Charlie remembers at tick 100
events = get_events_before_tick("charlie", 100)

# Returns deterministic events like:
# [
#   {"tick": 45, "action": "meet", "target": "aiche", "location": "alley"},
#   {"tick": 72, "action": "trade", "target": "felix", "location": "neon_bar"}
# ]
```

## Event Probability

```python
def does_event_occur(npc_id: str, tick: int) -> bool:
    seed = hash(f"{npc_id}_event_check_{tick}")
    return (seed % 1000) < 50  # 5% chance per tick
```

- **5% event probability** per tick
- ~500 ticks scanned = ~25 memorable events per NPC
- Same seed → same events every time

## Memory Context for LLM

```python
def get_npc_memory_context(npc_id: str, tick: int) -> str:
    """Generate natural language memories for LLM prompt."""
    events = get_events_before_tick(npc_id, tick, max_events=5)
    
    # Returns:
    # "Recent memories:
    #  - 55 ticks ago: Met Aiche at alley
    #  - 28 ticks ago: Traded with Felix at neon bar"
```

## Relationship System

```python
def get_relationship_at_tick(npc_a: str, npc_b: str, tick: int) -> dict:
    # Deterministic relationship based on:
    # 1. Base seed (relationship type)
    # 2. Number of shared events (trust level)
    
    return {
        "type": "ally",      # From codec R01-R16
        "trust": 0.75,       # 0.0-1.0 based on interactions
        "met_count": 3,      # Deterministic meeting count
        "since_tick": 12     # When relationship started
    }
```

## Event Encoding

Compact format for storage:
```
A01-C09-L08-T00050
 │    │    │    │
 │    │    │    └── Tick 50
 │    │    └─────── Location: alley
 │    └──────────── Target: aiche
 └───────────────── Action: meet

Decoded: "Charlie met Aiche in alley at tick 50"
```

## Integration with NPC Chat

```python
# In npc_chat.py
from data.event_engine import get_npc_memory_context

@app.route("/api/npc/chat", methods=["POST"])
def chat():
    npc_id = request.json["npc_id"]
    tick = request.json["tick"]
    
    # Get deterministic memories
    memories = get_npc_memory_context(npc_id, tick)
    
    # Include in LLM prompt
    prompt = f"""
    You are {npc_name}...
    
    {memories}
    
    User says: {message}
    """
```

## Why This Works

1. **Deterministic**: Same tick always produces same events
2. **Compact**: All knowledge in ~15KB JSON
3. **Permanent**: Codec stored on Arweave
4. **Scalable**: No event logs needed - events are computed on demand
5. **Consistent**: All clients see the same world state

## On Arweave

```
world_codec.json  → TX: [transaction_id]
├── actions (60)
├── objects (100)
├── locations (30)
├── npcs (12+)
├── cybernetics (40)
├── medical (40)
├── electronics (30)
└── event_templates
```

Query via GraphQL:
```graphql
{
  transactions(tags: [
    {name: "App-Name", values: ["AO-World-Engine"]},
    {name: "Type", values: ["world_codec"]}
  ]) {
    edges { node { id } }
  }
}
```

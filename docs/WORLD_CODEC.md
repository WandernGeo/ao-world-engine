# World Codec System

The World Codec is a comprehensive, chunked knowledge system for deterministic world simulation.

## Overview

The codec consists of **14 JSON chunks** (~312KB total) that define:
- Actions, objects, and locations
- NPCs with relationships and reaction matrices
- Medical, tech, chemistry systems
- Skills, events, and lore
- Multilingual support
- Geospatial coordinates (NYC/Brooklyn)
- Canon events for permanent story

## Chunk Structure

| Chunk | Size | Contents |
|-------|------|----------|
| 00_core | 28KB | 200 actions, 200 objects, 55 locations |
| 01_npcs | 32KB | 12 NPCs, relationships, reaction matrix |
| 02_medical | 28KB | 60 conditions, 30 treatments, 30 drugs |
| 03_tech | 24KB | 43 cybernetics, 30 hacking skills |
| 04_chemistry | 12KB | Compounds, crafting, drug synthesis |
| 05_lore | 12KB | History, factions, layer mythology |
| 06_skills | 20KB | 26 skills with progression |
| 07_events | 12KB | Event templates, quest hooks |
| 08_infrastructure | 36KB | Power, solar, 80 sensors, HVAC |
| 09_verbs | 16KB | 500 action verbs |
| 10_objects | 24KB | 572 objects |
| 11_languages | 16KB | Multilingual + custom language slots |
| 12_geospatial | 8KB | PostGIS coords (NYC/Brooklyn) |
| 13_canon_events | 12KB | Official story events |

## How Writers Avoid Contradictions

The system prevents contradictions through:

1. **Immutable Canon Events** - Once uploaded to Arweave, canon events cannot be changed
2. **Tick-based Timeline** - Every event has a specific tick, ordering is deterministic
3. **Automatic Propagation** - When a canon event is added, all NPCs learn about it through the gossip system
4. **Schema Enforcement** - New content must follow the defined schemas

## How NPCs Learn About New Characters

When a new character (e.g., "Ghost") is introduced:

```
1. New Character Defined:
   Ghost = {archetype: "hacker", traits: ["temple_tattoo", "cybernetics"]}

2. Canon Event Created:
   "Charlie meets Ghost at tick 80000 in Neon Bar"

3. System Calculates Reaction:
   - Charlie's archetype_defaults[hacker] = trust 0.5
   - trait_modifier[temple_tattoo] = -0.3
   - trait_modifier[cybernetics] = +0.05
   - Final: trust 0.25, stance: suspicious

4. Event Stored on Arweave:
   Anyone querying "Charlie's relationships" now sees Ghost
```

## Usage

```python
from codec_chunks.chunk_loader import get_codec

codec = get_codec()

# Decode any code
action = codec.decode_action("A086")  # → "hack"
location = codec.decode_location("L011")  # → "Felix's Neon Bar"

# Get NPC with relationships
charlie = codec.get_npc("charlie")
relationship = codec.get_npc_relationship("charlie", "felix")

# Calculate reaction to new character
reaction = codec.calculate_reaction("charlie", new_character_traits)
```

## Arweave Integration

Each chunk can be uploaded separately:

```bash
# Upload with proper tags
arweave deploy world_codec_00_core.json \
  --tag App-Name "AO-World-Engine" \
  --tag Type "world_codec_chunk" \
  --tag Chunk-ID "chunk_00_core"
```

Query all chunks:
```graphql
{
  transactions(tags: [
    {name: "App-Name", values: ["AO-World-Engine"]},
    {name: "Type", values: ["world_codec_chunk"]}
  ]) {
    edges { node { id } }
  }
}
```

## Extending the Codec

### Adding a New Language

```json
{
  "code": "klingon",
  "type": "fictional",
  "script": "custom_pIqaD",
  "vocabulary_chunk": "TX_ID_HERE"
}
```

### Adding a New NPC

New NPCs automatically work with existing NPCs through the reaction matrix - no need to update existing characters.

### Adding Canon Events

```json
{
  "event_id": "CE_20760101_001",
  "tick": 85000,
  "type": "EVT_MEET",
  "participants": ["charlie", "ghost"],
  "location": "L011",
  "outcome": "tension"
}
```

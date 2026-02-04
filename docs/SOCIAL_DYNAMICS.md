# Social Dynamics System

**Last Updated:** 2026-02-04

The social dynamics system simulates realistic NPC relationships inspired by The Sims, Dwarf Fortress, and Crusader Kings.

---

## Quick Start

```bash
# Get NPC's social network
curl "http://localhost:8081/api/social/npc/NPC_00001"

# Get social groups (coworkers, neighbors)
curl "http://localhost:8081/api/social/groups"

# Get NPC's reputation
curl "http://localhost:8081/api/social/reputation/NPC_00001"
```

---

## Core Concepts

### Trust Evolution

NPCs build trust through repeated meetings:

| Meetings | Trust Level | Relationship |
|----------|-------------|--------------|
| 0 | 0.0-0.25 | Stranger |
| 3+ | 0.25-0.45 | Acquaintance |
| 10+ | 0.45-0.65 | Colleague |
| 25+ | 0.65-0.85 | Friend |
| 50+ | 0.85-1.0 | Close Friend |

Trust can also go negative:

| Trust | Relationship |
|-------|--------------|
| -0.3 to 0 | Rival |
| -1.0 to -0.3 | Enemy |

### Trust Changes

| Event | Trust Change |
|-------|--------------|
| Same location | +0.002 |
| Work together | +0.01 |
| Deep conversation | +0.03 |
| Helped in need | +0.1 |
| Defended in fight | +0.15 |
| Argument | -0.08 |
| Betrayal | -0.2 |
| Attack | -0.5 |

---

## Social Groups

NPCs automatically form groups:

| Type | Formation | Bond Strength |
|------|-----------|---------------|
| **Coworkers** | Same workplace | 0.6 |
| **Neighbors** | Same building | 0.4 |
| **Faction Cell** | Same faction | 0.7 |
| **Bar Regulars** | Same bar, 10+ visits | 0.5 |
| **Friends** | Trust > 0.65, 25+ meetings | 0.8 |

---

## Gossip System

When NPCs witness events, they spread gossip:

```
Event: Alice helps Bob
Witnesses: Charlie, Diana

→ Charlie has 30% chance to tell others
→ If Charlie trusts source, believes it more
→ Positive gossip increases Bob's reputation
```

**Gossip Rules:**
- Spread probability: 30%
- Decay per hop: 50%
- Max hops: 3
- Trust required to believe: 0.4

---

## API Reference

### GET /api/social/npc/:id

Returns NPC's social network:

```json
{
  "npc_id": "NPC_00001",
  "name": "Echo Marquez",
  "social": {
    "friends": [
      {"npc_id": "NPC_00089", "trust": 0.85, "meetings": 52}
    ],
    "colleagues": [
      {"npc_id": "NPC_00045", "trust": 0.55, "meetings": 28}
    ],
    "acquaintances": 12,
    "rivals": [],
    "total_relationships": 25
  }
}
```

### GET /api/social/groups

Returns all social groups:

```json
{
  "groups_count": 45,
  "groups": [
    {
      "id": "WORK_AutoFab_100",
      "name": "AutoFab Team",
      "type": "coworkers",
      "members": ["NPC_00001", "NPC_00045", "NPC_00089"],
      "bond_strength": 0.6
    }
  ],
  "group_types": {
    "coworkers": 15,
    "neighbors": 20,
    "faction_cell": 10
  }
}
```

### GET /api/social/reputation/:id

Returns NPC's citywide reputation:

```json
{
  "npc_id": "NPC_00001",
  "reputation": {
    "average_trust": 0.42,
    "positive_views": 15,
    "negative_views": 3,
    "neutral_views": 50,
    "total_known_by": 68,
    "reputation_level": "known"
  }
}
```

---

## Integration with Simulation

The social dynamics system integrates with tick processing:

1. **On Same Location:** `track_meeting()` is called
2. **On Interaction:** `update_trust_from_interaction()` updates trust
3. **On Event Witnessed:** `spread_gossip()` propagates reputation
4. **Daily:** Groups are re-evaluated

---

## Files

| File | Purpose |
|------|---------|
| `scripts/social_dynamics.py` | Core logic |
| `data/codec_chunks/world_codec_19_social.json` | Configuration |
| `api/api_simulation.py` | API endpoints |

---

## Example: Relationship Over Time

```
Day 1:  Alice meets Bob at work → Trust: 0.11
Day 10: Daily meetings → Trust: 0.21, Type: stranger
Day 30: 30 meetings → Trust: 0.44, Type: acquaintance
Day 60: 60 meetings → Trust: 0.68, Type: friend
```

---

*"The city's social fabric is woven from a million small interactions."*

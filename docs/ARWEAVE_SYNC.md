# Arweave Sync Architecture

> How NPC interactions get stored on Arweave and stay synchronized

---

## The Current State

```
┌──────────────────────────────────────────────────────────────┐
│  WHAT'S ON ARWEAVE NOW (World Codec)                         │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ar://FLnAk3N8T...  world_codec.json                         │
│  ├── npcs: 800 NPC definitions                               │
│  ├── buildings: 50+ locations                                │
│  ├── factions: Resistance, Temple, etc.                      │
│  └── actions: meet, trade, fight, etc.                       │
│                                                               │
│  ❌ NO interaction history                                    │
│  ❌ NO relationships.json                                     │
│  ❌ NO memory files                                           │
│                                                               │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  WHAT'S LOCAL ONLY (your server)                             │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  data/npc_interactions/                                      │
│  ├── relationships.json    ← LOCAL ONLY                      │
│  ├── interaction_log.json  ← LOCAL ONLY                      │
│  └── npc_memory/           ← LOCAL ONLY                      │
│                                                               │
│  Problem: If you start a new server, these don't exist!      │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## WHY This Works Anyway (Determinism)

The KEY insight: **Interactions are DETERMINISTIC**.

```python
# This function returns THE SAME result for the same inputs, ALWAYS
def calculate_interaction(charlie, felix, tick=100):
    seed = f"charlie_felix_100"
    roll = deterministic_hash(seed) % 100  # ALWAYS same number
    # → ALWAYS returns "greeting" (or whatever)
```

So:
- Server A at tick 100: Charlie greets Felix
- Server B at tick 100: Charlie greets Felix (same!)
- Server C at tick 100: Charlie greets Felix (same!)

**Servers don't need to SYNC interactions - they can RECALCULATE them!**

---

## Two Sync Strategies

### Strategy 1: Recalculate from Tick (Current)

```
┌──────────────────────────────────────────────────────────────┐
│  RECALCULATE MODE                                            │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  New server starts at tick 1000:                             │
│  1. Fetch world_codec.json from Arweave                      │
│  2. Run simulate_tick(0), simulate_tick(1), ... tick(1000)   │
│  3. All interactions recalculated deterministically          │
│  4. relationships.json rebuilt from scratch                  │
│                                                               │
│  ✅ Pros: No need to store interactions on Arweave           │
│  ❌ Cons: Slow for high tick numbers, compute-heavy          │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### Strategy 2: Snapshot + Delta (Better)

```
┌──────────────────────────────────────────────────────────────┐
│  SNAPSHOT + DELTA MODE                                       │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Every 10,000 ticks, upload a SNAPSHOT to Arweave:           │
│                                                               │
│  ar://abc123...  snapshot_tick_10000.json                    │
│  {                                                           │
│    "tick": 10000,                                            │
│    "relationships": { "charlie_felix": { "trust": 0.72 } },  │
│    "buildings_added": ["B045", "B046"],                      │
│    "significant_events": [...]                               │
│  }                                                           │
│                                                               │
│  New server at tick 12000:                                   │
│  1. Fetch snapshot_tick_10000.json from Arweave              │
│  2. Apply it (instant state)                                 │
│  3. Recalculate ticks 10001-12000 only                       │
│                                                               │
│  ✅ Pros: Fast sync, history preserved                       │
│  ✅ Pros: Anyone can audit the history                       │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## Proposed Arweave Structure

```
ARWEAVE TRANSACTIONS:

ar://WORLD_CODEC     → Base world (NPCs, buildings, factions)
ar://SNAPSHOT_0      → Initial state (empty relationships)
ar://SNAPSHOT_10000  → State at tick 10000
ar://SNAPSHOT_20000  → State at tick 20000
ar://DELTA_10001     → Events from tick 10001-11000 (batch)
ar://DELTA_11001     → Events from tick 11001-12000 (batch)
...

To sync to tick 25000:
1. Fetch WORLD_CODEC (base)
2. Fetch SNAPSHOT_20000 (closest)
3. Fetch DELTA_20001, DELTA_21001, etc.
4. Recalculate 25001-25000 locally
```

---

## What Gets Stored on Arweave

### Every 10,000 ticks: SNAPSHOT
```json
{
  "type": "world_snapshot",
  "tick": 10000,
  "relationships": {
    "charlie_felix": {"trust": 0.72, "met_count": 15},
    "charlie_kai_vance": {"trust": 0.85, "met_count": 8}
  },
  "buildings": {
    "B045": {"name": "New Academy", "opened_tick": 5000}
  },
  "faction_territories": {
    "undercity": "resistance",
    "temple_district": "temple"
  }
}
```

### Every 1000 ticks: DELTA (events)
```json
{
  "type": "world_delta",
  "tick_range": [10001, 11000],
  "significant_events": [
    {"tick": 10050, "type": "deep_conversation", "npc1": "charlie", "npc2": "felix"},
    {"tick": 10200, "type": "new_building", "building": "B046"},
    {"tick": 10500, "type": "fight", "npc1": "guard_01", "npc2": "thief_03"}
  ]
}
```

---

## Implementation Plan

```python
# Add to world_events.py

def create_snapshot(tick: int) -> dict:
    """Create full state snapshot for Arweave."""
    return {
        "type": "world_snapshot",
        "tick": tick,
        "relationships": load_relationships(),
        "buildings": load_buildings(),
        "npc_memories": aggregate_npc_memories(),
        "created_at": datetime.now().isoformat()
    }

def upload_snapshot_if_needed(tick: int):
    """Upload snapshot every 10,000 ticks."""
    if tick % 10000 == 0:
        snapshot = create_snapshot(tick)
        tx_id = upload_to_arweave(snapshot)
        print(f"📸 Snapshot at tick {tick}: ar://{tx_id}")
```

---

## Summary

| Question | Answer |
|----------|--------|
| Where is relationships.json? | LOCAL now, ARWEAVE after snapshot |
| How do servers sync? | Fetch snapshot + recalculate delta |
| Is it random? | NO! Deterministic - same tick = same result |
| What triggers upload? | Every 10,000 ticks OR manual trigger |
| Can history be audited? | YES! All on Arweave, anyone can verify |

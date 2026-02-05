# Social Dynamics Tests (25 tests)

> **Updated:** 2026-02-05T07:20:00-05:00

Tests for relationships, gossip, and social mechanics from `world_codec_19_social.json`.

---

## Social Dynamics (8 tests)

| Test Name | What It Validates | Pass Criteria |
|-----------|------------------|---------------|
| Relationship Types | Trust categories | 6+ types defined |
| Trust Mechanics | Core constants | TRUST_BASE, DECAY, MAX |
| Meeting Thresholds | Progression rules | MEETING_THRESHOLDS table |
| Group Types | Social groups | 5 group types |
| Trust Change Interactions | Action effects | 7+ interaction types |
| Social Functions | Core functions | get_relationship, update_trust |
| Relationship Key Generation | Symmetric keys | make_relationship_key |
| Relationship Decay | Trust decreases | decay_relationships |

---

## Relationship Types

| Trust Range | Type | Description |
|-------------|------|-------------|
| -1.0 to -0.3 | Enemy | Active hostility |
| -0.3 to 0.0 | Rival | Competition/tension |
| 0.0 to 0.25 | Stranger | No relationship |
| 0.25 to 0.45 | Acquaintance | Know by name |
| 0.45 to 0.65 | Colleague | Work together |
| 0.65 to 0.85 | Friend | Trusted ally |
| 0.85 to 1.0 | Confidant | Deep trust |

---

## Trust Mechanics

### Constants

```lua
TRUST_BASE = 0.1           -- Starting trust for strangers
TRUST_DECAY_RATE = 0.01    -- Per-tick decay for inactive relations
TRUST_MAX = 1.0            -- Maximum trust
TRUST_MIN = -1.0           -- Minimum trust (enemies)
```

### Interaction Effects

| Interaction | Trust Change | Duration |
|-------------|--------------|----------|
| positive_chat | +0.05 | Instant |
| gift | +0.10 | Instant |
| help_in_crisis | +0.20 | Instant |
| betrayal | -0.40 | Instant |
| gossip_spread | ±0.05 | Based on content |
| work_together | +0.03 | Per work session |
| passive_decay | -0.01 | Per tick inactive |

---

## Relationship Mechanics (3 tests)

| Test Name | What It Validates |
|-----------|------------------|
| Initial Values | Default trust = 0.1 |
| Progression Logic | Meetings → higher trust |
| Symmetric Keys | A↔B = B↔A |

### Meeting Thresholds

```
Meetings    Relationship
─────────────────────────
0-2         Stranger
3-5         Acquaintance
6-10        Colleague
11-20       Friend
21+         Close Friend/Confidant
```

---

## Gossip System (6 tests)

| Test Name | What It Validates | Pass Criteria |
|-----------|------------------|---------------|
| Gossip Creation | create_gossip() | Function exists |
| Gossip Spreading | spread_gossip() | Function exists |
| Spread Probability | Base chance | ~0.3 (30%) |
| Gossip Decay | Expiration | TTL implemented |
| NPC Gossip Knowledge | Memory tracking | heard_gossip table |
| Trust Affects Spread | Multiplier | Higher trust = faster |

### How Gossip Spreads

```
Step 1: Event occurs (NPC does something notable)
Step 2: Witnesses create gossip with metadata
    {
        content = "Saw Zero at the black market",
        source = "NPC_042",
        tick_created = 1500,
        expire_tick = 1530,  -- ~30 ticks TTL
        importance = 0.6
    }

Step 3: Each tick, gossip spreads to trusted contacts
    spread_chance = BASE_CHANCE * trust_level * importance
    
Step 4: Max 3 hops from original source

Step 5: Gossip expires after TTL
```

---

## Group Types (5 groups)

| Group Type | Formation | Example |
|------------|-----------|---------|
| Coworkers | Same workplace | Factory workers |
| Neighbors | Same building | Apartment block |
| Faction Cell | Same faction | Resistance cell |
| Social Group | High trust | Bar regulars |
| Conspiracy | Shared secret | Underground group |

### Group Logic

```lua
function form_group(npcs, type)
    -- Check minimum trust between members
    local avg_trust = calculate_average_trust(npcs)
    if avg_trust < GROUP_THRESHOLDS[type] then
        return nil  -- Can't form group
    end
    
    return {
        id = generate_group_id(),
        type = type,
        members = npcs,
        formed_tick = WorldTick
    }
end
```

---

## Reputation System (4 tests)

| Test Name | What It Validates |
|-----------|------------------|
| Reputation Storage | Per-faction rep tracking |
| Get Reputation | get_faction_reputation() |
| Modify Reputation | modify_reputation() |
| Bounded Values | -1.0 to 1.0 range |

### Reputation Effects

| Rep Range | Effect |
|-----------|--------|
| -1.0 to -0.5 | Hostile, attack on sight |
| -0.5 to 0.0 | Unfriendly, higher prices |
| 0.0 to 0.3 | Neutral |
| 0.3 to 0.7 | Friendly, discounts |
| 0.7 to 1.0 | Ally, special access |

---

*Part of the AO World Engine Test Suite*

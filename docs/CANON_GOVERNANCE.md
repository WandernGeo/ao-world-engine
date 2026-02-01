# RE:ECHO City - Canon Governance & Content Rules

> *"The world grows, but it grows within the lines."*

---

## Core Principle

RE:ECHO City is **append-only**. New content extends the world, never contradicts it. The existing Arweave JSONs form the **Canon** - the immutable truth of what has happened.

---

## The Canon Validation System

Every new content submission is validated against existing canon before acceptance.

```
NEW SUBMISSION
      ↓
┌─────────────────┐
│ CANON VALIDATOR │ ← Reads existing Arweave JSONs
└─────────────────┘
      ↓
   DECISION
   ├── ACCEPT (fits canon)
   ├── TRANSFORM (adjust to fit)
   └── REJECT (violates canon)
```

---

## Content Categories

### 🟢 Auto-Accept (Fits Canon)

Content that naturally extends existing patterns:

- NPC performs action within their archetype
- NPC ages (following 200+ year lifespan rules)
- NPC has child (with valid parent NPCs)
- NPC moves between existing districts
- NPC changes faction (with relationship history support)
- New NPC spawned following population growth rules

### 🟡 Transform (Adjust to Fit)

Content that has good intent but wrong execution:

| Submitted | Problem | Transformed To |
|-----------|---------|----------------|
| "Dragon attacks city" | Fantasy element | "Holographic dragon display malfunctions" |
| "Magic spell cast" | No magic in canon | "Hacker deploys visual exploit" |
| "NPC teleports" | Violates physics | "NPC uses rapid transit" |
| "Alien invasion" | Breaks setting | "Corporate AR marketing stunt" |
| "NPC dies at age 50" | Lifespan violation | "NPC enters stasis/coma" |
| "Time travel" | Breaks causality | "Echo memory replay experienced" |

### 🔴 Auto-Reject (Violates Canon)

Content that cannot be salvaged:

- Contradicts established NPC history
- Destroys permanent structures without consensus
- Introduces technology beyond setting (FTL, teleportation)
- Kills NPCs without proper event chain
- Alters past events (immutability violation)
- Spam/nonsense content
- Offensive/illegal content

---

## The Signal Noir Ruleset

RE:ECHO City follows **Signal Noir** aesthetic rules:

### ✅ ALLOWED

- Cyberpunk technology (implants, hacking, neon, holograms)
- Noir atmosphere (rain, shadows, moral ambiguity)
- Urban decay and renewal
- Faction conflicts (political, ideological)
- Personal drama (relationships, betrayal, redemption)
- Economic systems (trade, poverty, wealth)
- Crime and law enforcement
- Long lifespans with augmentation maintenance
- Echoes (memory fragments of the dead)
- AI entities (hidden, emergent)

### ❌ NOT ALLOWED

- Fantasy creatures (dragons, elves, wizards)
- Supernatural magic (spells, curses, divine intervention)
- Space travel / aliens
- Time manipulation
- Resurrection of dead NPCs
- Destruction of core city infrastructure
- Breaking the 4th wall
- Real-world references that break immersion
- Content from other IPs/franchises

### 🔄 TRANSFORM PATTERNS

When invalid content is submitted, use these patterns:

```json
{
  "invalid_element": "dragon",
  "transform_to": "holographic_display OR drone_swarm OR augmented_reality_creature",
  "explanation": "In RE:ECHO, fantastical elements are technology, not magic"
}

{
  "invalid_element": "magic_spell",
  "transform_to": "hacking_exploit OR neural_implant_effect OR hallucinogenic_drug",
  "explanation": "Effects that seem magical have technological explanations"
}

{
  "invalid_element": "supernatural_ghost",
  "transform_to": "echo_manifestation OR AI_projection OR memory_replay",
  "explanation": "Echoes are data fragments, not supernatural entities"
}
```

---

## Multi-JSON NPCs

For NPCs with rich histories, data can span multiple JSONs:

```
npc_kira/
├── npc_kira_core.json        # Base identity (permanent)
├── npc_kira_history_001.json # Early life events
├── npc_kira_history_002.json # Career events
├── npc_kira_relationships.json # Social connections
└── npc_kira_latest.json      # Current state (updated)
```

**Linking:**
```json
{
  "npc_id": "kira",
  "json_type": "core",
  "linked_jsons": [
    "ar://tx_history_001",
    "ar://tx_history_002",
    "ar://tx_relationships"
  ],
  "latest_state": "ar://tx_latest_001"
}
```

---

## Lifespan & Aging

In RE:ECHO City, citizens live **200+ years** due to:

- Cybernetic organ replacement
- Neural backup systems
- Vivi bio-regeneration techniques
- Corporate life-extension programs

### Aging Rules

```json
{
  "lifespan": {
    "minimum": 200,
    "maximum": 350,
    "factors": {
      "augmentation_level": "+50 years per tier",
      "vivi_treatment": "+30 years",
      "poverty": "-50 years",
      "dangerous_job": "-20 years per decade"
    }
  },
  "life_stages": {
    "child": { "age": "0-18", "can_work": false, "education": true },
    "young_adult": { "age": "18-50", "peak_performance": true },
    "adult": { "age": "50-150", "experienced": true },
    "elder": { "age": "150-250", "wisdom_bonus": true },
    "ancient": { "age": "250+", "rare": true, "legend_status": true }
  }
}
```

### Death in RE:ECHO

Death is rare but happens:

- Combat/violence
- Catastrophic system failure
- Choosing to end (philosophical)
- Assassination
- Accidents

**When an NPC dies:**
1. Death event is logged
2. Echo is created (memory fragment)
3. Relationships are updated (mourning)
4. Inheritance/succession triggered
5. NPC becomes part of history

---

## Population Dynamics

The city grows organically:

```json
{
  "population": {
    "base_growth_rate": 0.02,
    "factors": {
      "economic_prosperity": "+0.01",
      "faction_stability": "+0.005",
      "war_conflict": "-0.03",
      "plague_event": "-0.05",
      "immigration_wave": "+0.1"
    }
  },
  "birth_rules": {
    "requires_two_parents": true,
    "parent_age_min": 25,
    "parent_age_max": 180,
    "probability_per_year": 0.02,
    "inheritance": {
      "faction": "weighted_random",
      "archetype": "influenced_by_parents",
      "location": "parent_district"
    }
  }
}
```

---

## Community Content Submission

### How to Submit New Lore

1. **Create JSON** following schemas in `/schemas/`
2. **Upload to Arweave** with proper tags
3. **Submit to Validator** (AO process)
4. **Community Review** for significant changes
5. **Auto-merge** if passes validation

### Required Tags

```json
{
  "tags": [
    { "name": "App-Name", "value": "RE-ECHO-CITY" },
    { "name": "Content-Type", "value": "lore|npc|event|district" },
    { "name": "Submitter", "value": "wallet_address" },
    { "name": "Requires-Review", "value": "true|false" },
    { "name": "Parent-Txs", "value": "list_of_referenced_txs" }
  ]
}
```

### What Triggers Community Review

- New district creation
- Major faction event
- City-wide changes
- New archetype introduction
- Lore document updates
- Rule changes

### Voting Threshold

```json
{
  "voting": {
    "quorum": 10,
    "approval_threshold": 0.66,
    "voting_period_ticks": 1440,
    "eligible_voters": "holders_of_echo_tokens_or_contributors"
  }
}
```

---

## Autonomous Operation

The simulation runs **forever** on the permaweb:

```
┌─────────────────────────────────────────┐
│         AUTONOMOUS SIMULATION           │
│                                         │
│  AO Processes (Cron-driven)             │
│  ├── Process NPCs every tick            │
│  ├── Generate life events               │
│  ├── Age population                     │
│  ├── Run elections                      │
│  ├── Trigger random events              │
│  └── Append new state to Arweave        │
│                                         │
│  Optional: Cloud API for acceleration   │
│  (Not required - world runs without it) │
└─────────────────────────────────────────┘
```

**Random Event Generator:**

```lua
function generate_random_event(tick)
  local seed = hash(tick)
  local event_type = weighted_random(seed, {
    { type = "birth", weight = 10 },
    { type = "death", weight = 1 },
    { type = "marriage", weight = 5 },
    { type = "job_change", weight = 8 },
    { type = "faction_shift", weight = 2 },
    { type = "district_event", weight = 3 },
    { type = "economic_shift", weight = 2 },
    { type = "political_event", weight = 1 }
  })
  
  return generate_event_details(event_type, tick)
end
```

---

## Example: Valid vs Invalid Submissions

### ✅ Valid

```json
{
  "type": "event",
  "event_type": "birth",
  "parents": ["npc_kira", "npc_alex"],
  "child": {
    "id": "npc_kira_jr",
    "birth_tick": 1000000,
    "district": "neon_market"
  }
}
```

### 🔄 Transformed

**Submitted:**
```json
{
  "type": "event",
  "event_type": "dragon_attack",
  "location": "neon_market"
}
```

**Transformed to:**
```json
{
  "type": "event",
  "event_type": "hologram_malfunction",
  "description": "A malfunctioning AR advertisement displayed a massive dragon, causing panic in neon_market before technicians shut it down.",
  "location": "neon_market"
}
```

### ❌ Rejected

```json
{
  "type": "event",
  "event_type": "npc_kira_dies",
  "cause": "old_age",
  "age_at_death": 45
}
```
**Reason:** Violates 200+ year lifespan rule

---

## Summary

1. **Canon is immutable** - existing JSONs are truth
2. **New content extends, never contradicts**
3. **Signal Noir rules** - no fantasy, no magic, tech explanations only
4. **Transform when possible** - salvage good ideas
5. **Reject when necessary** - protect world integrity
6. **Community governs** - voting on significant changes
7. **Runs forever** - autonomous permaweb operation

---

*"In RE:ECHO, every story is possible. Just not every telling."*

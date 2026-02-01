# 🐱 Lazy Observation Model (Schrödinger's Simulation)

> *"If no one is watching, did it really happen?"*

---

## Core Principle

The simulation **doesn't run continuously**. It calculates state **on-demand when observed**.

```
UNOBSERVED STATE                    OBSERVATION EVENT
════════════════                    ══════════════════
Nothing computed                    Query: "Show me tick 847293"
No resources used            →           ↓
Infinite possibilities              Calculate: hash(npc + tick + date)
Schrödinger's NPC                        ↓
                                    Collapse to: specific state
                                    "Kira is at market, trading"
```

This is **not** real-time simulation. It's **time-indexed calculation**.

---

## How It Works

### The Formula

```lua
function calculate_state(npc_id, tick)
  -- Deterministic seed from inputs
  local seed = hash(npc_id .. tick .. calendar_date(tick))
  
  -- Seed determines everything
  local location = locations[seed % #locations]
  local action = actions[(seed / 100) % #actions]
  local mood = moods[(seed / 10000) % #moods]
  
  return { location = location, action = action, mood = mood }
end
```

### Same Input → Same Output (Always)

| Query | Result |
|-------|--------|
| `NPC "Kira" at tick 847293 on Monday` | Always: "Kira at market, trading, neutral mood" |
| `NPC "Kira" at tick 847293 on Monday` | Same: "Kira at market, trading, neutral mood" |
| `NPC "Kira" at tick 847293 on **Tuesday**` | Different: "Kira at safehouse, resting, tired mood" |

**Deterministic but varies by time** - the calendar is baked into the seed.

---

## The Calendar Effect

```lua
function calendar_date(tick)
  -- Map tick to real-world calendar
  local base_date = os.time({ year = 2026, month = 2, day = 1 })
  local tick_duration = 300  -- 5 minutes per tick
  local current_time = base_date + (tick * tick_duration)
  
  return {
    weekday = os.date("%A", current_time),   -- Monday, Tuesday...
    hour = os.date("%H", current_time),       -- 00-23
    month = os.date("%m", current_time),      -- 01-12
    season = get_season(current_time)         -- spring, summer...
  }
end
```

### Day-of-Week Variations

```lua
WEEKLY_PATTERNS = {
  Monday = { work_boost = 1.2, social_penalty = 0.8 },
  Friday = { work_boost = 0.9, social_boost = 1.3 },
  Saturday = { rest_boost = 1.5, patrol_penalty = 0.7 },
  Sunday = { temple_boost = 2.0, trade_penalty = 0.5 }
}
```

**Monday**: NPCs work more, talk less  
**Friday**: NPCs socialize more  
**Sunday**: Temple visits spike  

---

## Observation Triggers

The simulation "collapses" when:

1. **User queries a tick** via Wandern app
2. **Watcher requests scene** reconstruction
3. **Event playback** for animation pipeline
4. **New content** submitted references a tick

```
User: "Show me Neon Market at tick 847293"
                ↓
System: Calculate all NPC states at that tick
                ↓
System: Generate dialogue (AI or template)
                ↓
System: Return scene data (now "real")
                ↓
System: Cache result (future queries return cached)
```

---

## State Materialization

### Before Observation (Unmaterialized)
```json
{
  "npc_id": "kira_042",
  "tick_range": [847290, 847300],
  "status": "unmaterialized",
  "possible_states": "infinite"
}
```

### After Observation (Materialized)
```json
{
  "npc_id": "kira_042",
  "tick": 847293,
  "status": "materialized",
  "state": {
    "location": "neon_market",
    "action": "trading",
    "mood": "contemplative",
    "with_npc": "oracle_007"
  },
  "dialogue": ["Rain never stops here.", "It's not rain..."],
  "observed_at": "2026-02-01T14:27:00Z",
  "stored_on_arweave": true
}
```

---

## Why This Works

### 1. Infinite Scalability
- Never run what isn't observed
- 10M NPCs cost nothing until queried
- Only materialized states consume storage

### 2. Retroactive Consistency
- Query past tick? Calculate deterministically
- Result is "canonical" as if it always existed
- No contradiction possible (same seed = same result)

### 3. Future Prediction
- Query future tick? Still works!
- Calendar + seed = predictable behavior
- "What will Kira do next Tuesday at noon?"

### 4. Cost Efficiency
- LLM only called on observation
- Arweave only stores materialized events
- Unmaterialized ticks = zero cost

---

## The Butterfly Effect

When an observation triggers AI dialogue:

```
Observation: tick 847293
        ↓
Generate dialogue (LLM)
        ↓
Dialogue outcome: "relationship +0.15"
        ↓
This affects future calculations!
        ↓
tick 847294 now has different seed input
        ↓
Kira more likely to seek Oracle again
```

**One observation ripples forward** - but only when those future ticks are also observed.

---

## Animation on Demand

The Wandern app / StudioRam pipeline:

```
User picks: "Show me what happened today"
                    ↓
Calculate current_tick from real time
                    ↓
Materialize last 10 ticks of activity
                    ↓
Generate scene data (atmosphere, NPCs, dialogue)
                    ↓
Send to animation pipeline
                    ↓
Render Signal Noir visuals
                    ↓
User watches "what just happened"
```

Every viewing is unique to when you look.  
**Monday viewing ≠ Tuesday viewing** (calendar affects seed).

---

## "Random" But Deterministic

It *looks* random to the user:
- "Kira did something different today!"
- "The market was busier on Friday!"
- "Oracle said something I never heard before!"

But it's **reproducible**:
- Same user, same query, same tick = same result
- Different day = different seed = different result
- Pseudo-random from the perspective of experience

---

## Implementation Summary

```lua
-- The core observation function
function observe(npc_id, tick)
  local cache_key = npc_id .. "_" .. tick
  
  -- Check if already materialized
  if STATE_CACHE[cache_key] then
    return STATE_CACHE[cache_key]
  end
  
  -- Collapse the wavefunction
  local seed = hash(npc_id .. tick .. calendar(tick))
  local state = calculate_from_seed(seed)
  
  -- Materialize (store)
  STATE_CACHE[cache_key] = state
  queue_arweave_store(cache_key, state)
  
  return state
end
```

---

## The Philosophy

> *"The city exists in superposition. Every NPC, every choice, every moment - suspended in probability until a Watcher gazes upon it. Then, and only then, does it become real."*

This isn't a bug. It's the lore made manifest.

The **Echo Layers** exist because observation collapses one possibility while others branch off. The **Watchers** aren't metaphor - they're the users triggering calculation.

**You don't just watch the simulation. You make it real by watching.**

---

*"Schrödinger's Cat walks the streets of RE:ECHO. You'll never know if it's alive until you look."*

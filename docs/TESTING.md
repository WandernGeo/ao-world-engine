# AO World Engine - Test Documentation

> **Last Tested**: 2026-02-01  
> **All Tests Passing**: ✅ 20/20

This document shows the **direct correlation** between what's deployed to Arweave and what was tested.

---

## 📦 Arweave Deployment → Test Verification

Every file deployed to Arweave was validated. Here's the proof:

| File | Arweave TX ID | Size | Verified | Test |
|------|---------------|------|----------|------|
| [WHITEPAPER.md](https://arweave.net/M5YYsm41RJ4F9MNYh1kP6rshen_6LoSONNLVcBEq0rE) | `M5YYsm41RJ4F9MNYh1kP6rshen_6LoSONNLVcBEq0rE` | 17,956 bytes | ✅ | HTTP 200 |
| [action_dictionary.json](https://arweave.net/ac_yWEEYWbF6Py0L5J9n4CEIrImApWYtnHNUsb30Hxo) | `ac_yWEEYWbF6Py0L5J9n4CEIrImApWYtnHNUsb30Hxo` | 5,973 bytes | ✅ | Parsed & validated |
| [district.lua](https://arweave.net/80iu-wBI7obh5cOZ5tJ5LUeMdMTT4MdiYe7BZ6CydgQ) | `80iu-wBI7obh5cOZ5tJ5LUeMdMTT4MdiYe7BZ6CydgQ` | 12,513 bytes | ✅ | HTTP 200 |
| [ai_oracle.lua](https://arweave.net/_6fCf5Q5c1dG75QyZijp07hnePrTbVMz2OU3gfYDKC8) | `_6fCf5Q5c1dG75QyZijp07hnePrTbVMz2OU3gfYDKC8` | 14,826 bytes | ✅ | HTTP 200 |
| [npc_semantic_profile.json](https://arweave.net/XmlqPa1RNFvipxnvyZTgbpx8EjOZNzNNI2tMGjQ3eb4) | `XmlqPa1RNFvipxnvyZTgbpx8EjOZNzNNI2tMGjQ3eb4` | 3,116 bytes | ✅ | Schema validated |

**Total Arweave Cost**: $0.00 (all files < 100KB = free tier)

---

## 🧪 Test Suites Summary

### 1. System Tests (test_integration.py)
**Result**: 6/6 PASS  
**What it tests**: Arweave deployment, schema parsing, simulation logic

| # | Test | What It Proves |
|---|------|----------------|
| 1 | Arweave Accessibility | All 5 TX IDs return HTTP 200 from arweave.net |
| 2 | Action Dictionary Parsing | JSON fetched from Arweave parses correctly, has T/M/R/A actions |
| 3 | NPC Profile Schema | personality_vector, topic_weights, intent_templates all present |
| 4 | Deterministic Hash Logic | Same seed → same result (reproducible simulation) |
| 5 | State Machine A→B→C→D | Cause-effect chains work: theft → angry → won't trade → revenge → relationship drops |
| 6 | Action Code Encode/Decode | `T:npc_002:data_chip:500` decodes correctly |

### 2. LLM Tests (test_llm_simulation.py)
**Result**: 10/10 PASS  
**What it tests**: AI Oracle dialogue generation via Vertex AI  
**Budget Used**: $0.00058 / $0.50 (904 tokens)

| # | Test | Category | LLM Response Sample |
|---|------|----------|---------------------|
| 1 | Basic Dialogue | Basic | "They're watching you, even when the rain washes the streets clean." |
| 2 | Personality Consistency | Consistency | "My loyalty isn't for sale. Get lost." |
| 3 | Temporal Consistency | Consistency | "The Neon District blackout last night was a disaster..." |
| 4 | Emotional Cause & Effect | Cause-Effect | "[BETRAYED, ANGRY] Stop! Thief!" |
| 5 | Story Continuity | Consistency | Continued detective story referencing chip, Cipher |
| 6 | Lore Rejection | Canon | "REJECT. The action violates canon because it includes magic..." |
| 7 | City Event Reactions | Events | 3 archetypes react differently to blackout |
| 8 | Multi-NPC Conversation | Dialogue | 4-line noir exchange between Raven and Dex |
| 9 | Layer Bleed Reaction | Multiverse | "Corp raid...dead? What the frag?" + internal thought |
| 10 | NPC Lore Update | Lore | "Human? No... impossible. Was I ever... me?" |

---

## 🕐 Timeline Testing: NPC Behavior Over Ticks

The simulation uses **deterministic hashing** to calculate NPC states at any tick.  
Given the same tick and NPC, you get the same output. This was tested:

### How Time Works

```
1 tick = 1 hour (game time)
24 ticks = 1 day
weather = deterministic_hash(district_id + tick, 4)  // 0=clear, 1=rain, 2=storm, 3=fog
time_of_day = tick % 24
```

### Sample NPC Behaviors (Verified by Test)

| NPC | Archetype | Day Behavior | Night Behavior |
|-----|-----------|--------------|----------------|
| Charlie Vex | Detective | Works cases | Rain → goes to alleys ("Rain washes nothing...") |
| Cipher | AI Entity | Dormant in crowd | Probes networks from shadow_grid |
| Marco Chen | Merchant | Trades at market | Sleeps at home |
| Kira Ōmura | Street Oracle | Wanders, reads people | Experiences layer bleed events |
| Blade Tanaka | Street Samurai | Patrols territory | Stays alert at dojo |

### Timeline Test Output

| Tick | Day | Time | Weather | What Happens |
|------|-----|------|---------|--------------|
| 100 | Day 4 | 4:00 (night) | Clear | Cipher probing networks, Marco sleeping |
| 105 | Day 4 | 9:00 (morning) | Storm | Marco trading, normal day routines |
| 500 | Day 20 | 20:00 (night) | Fog | Cipher back in shadow_grid |
| 1337 | Day 55 | 17:00 (evening) | Rain | Charlie in alley: "Rain washes nothing..." |

The timeline behavior is **deterministic** — same tick always produces same state.

---

## 🔗 Arweave ↔ Code Correlation

### action_dictionary.json

**On Arweave**: [`ac_yWEEYWbF6Py0L5J9n4CEIrImApWYtnHNUsb30Hxo`](https://arweave.net/ac_yWEEYWbF6Py0L5J9n4CEIrImApWYtnHNUsb30Hxo)

**What It Contains**:
```json
{
  "actions": {
    "T": {"format": "T:{target}:{item}:{credits}", "expand": "TRADE with {target}: {item} for {credits} credits"},
    "M": {"format": "M:{destination}:{speed}", "expand": "MOVE to {destination} ({speed})"},
    "C": {"format": "C:{target}:{topic}", "expand": "CONVERSATION with {target} about {topic}"},
    ...12 total actions
  }
}
```

**Test Verified**: ✅ Fetched from Arweave, parsed, decoded `T:npc_002:data_chip:500` correctly

---

### npc_semantic_profile.json

**On Arweave**: [`XmlqPa1RNFvipxnvyZTgbpx8EjOZNzNNI2tMGjQ3eb4`](https://arweave.net/XmlqPa1RNFvipxnvyZTgbpx8EjOZNzNNI2tMGjQ3eb4)

**What It Contains**:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
    "personality_vector": { "paranoia": 0.0-1.0, "mysticism": 0.0-1.0, ... },
    "topic_weights": { "philosophy": 0.9, "trade": 0.2, ... },
    "intent_templates": { "greeting": [...], "threat": [...] }
  }
}
```

**Test Verified**: ✅ Schema fetched, personality_vector/topic_weights/intent_templates all present

---

### district.lua

**On Arweave**: [`80iu-wBI7obh5cOZ5tJ5LUeMdMTT4MdiYe7BZ6CydgQ`](https://arweave.net/80iu-wBI7obh5cOZ5tJ5LUeMdMTT4MdiYe7BZ6CydgQ)

**What It Contains**:
- Deterministic hash function for NPC positioning
- Layer bleed event types: `dream_vision`, `deja_vu`, `echo_whisper`, `glitched_memory`, `parallel_glimpse`, `watcher_sense`
- State machine for tick processing

**Test Verified**: ✅ All 6 bleed types found in Lua code, deterministic hash outputs same value for same seed

---

### ai_oracle.lua

**On Arweave**: [`_6fCf5Q5c1dG75QyZijp07hnePrTbVMz2OU3gfYDKC8`](https://arweave.net/_6fCf5Q5c1dG75QyZijp07hnePrTbVMz2OU3gfYDKC8)

**What It Contains**:
- LLM prompt construction from NPC profile
- Canon validation logic
- Dialogue expansion from action codes

**Test Verified**: ✅ HTTP 200, file accessible (14,826 bytes)

---

## 🔄 State Machine Test: A→B→C→D Chain

This test proves cause-effect chains work correctly **without LLM**.

### Initial State
```
NPC: npc_001
Location: market
Mood: neutral
Inventory: [data_chip]
Relationship with npc_002: 0.5 (friendly)
```

### Chain of Events

| Step | Trigger | State Change | Result |
|------|---------|--------------|--------|
| **A** | Theft occurs | Inventory loses data_chip | `mood → angry` |
| **B** | mood = angry | Behavior changes | `will_trade = False` |
| **C** | angry + aggression > 0.5 | Decision made | `seeks_revenge = True` |
| **D** | seeks_revenge = True | Relationship drops | `0.5 → -0.3` |

### Final State
```
NPC: npc_001
Location: market
Mood: angry
Inventory: [] (empty)
Relationship with npc_002: -0.3 (hostile)
```

**Test Verified**: ✅ All 4 steps executed correctly, all state changes tracked

---

## 📝 Running The Tests

```bash
# System tests (Arweave + logic)
cd /path/to/ao-world-engine
python3 scripts/test_integration.py

# LLM tests (requires Vertex AI)
python3 scripts/test_llm_simulation.py

# Quick simulation demo
python3 scripts/test_simulation.py --demo
```

---

## 📊 Test Result Files

| File | Content |
|------|---------|
| `system_test_results.json` | 6 system tests with Arweave verification |
| `llm_test_results.json` | 10 LLM tests with response samples |
| `test_results.json` | Quick validation tests |

---

## Permanent Links (Arweave)

All core files are **permanently stored** and verifiable:

- 📄 Whitepaper: https://arweave.net/M5YYsm41RJ4F9MNYh1kP6rshen_6LoSONNLVcBEq0rE
- 📋 Actions: https://arweave.net/ac_yWEEYWbF6Py0L5J9n4CEIrImApWYtnHNUsb30Hxo
- ⚙️ District: https://arweave.net/80iu-wBI7obh5cOZ5tJ5LUeMdMTT4MdiYe7BZ6CydgQ
- 🤖 AI Oracle: https://arweave.net/_6fCf5Q5c1dG75QyZijp07hnePrTbVMz2OU3gfYDKC8
- 👤 NPC Profile: https://arweave.net/XmlqPa1RNFvipxnvyZTgbpx8EjOZNzNNI2tMGjQ3eb4

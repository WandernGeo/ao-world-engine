# 🤖 AI NPC System - Dynamic Dialogue Architecture

> *Autonomous NPCs that think, talk, and evolve without user input*

---

## Overview

RE:ECHO City NPCs are **AI-driven agents** that generate their own dialogue and make their own decisions. The system is designed for:

1. **Self-Perpetuation**: NPCs interact continuously without user prompts
2. **Arweave Compatibility**: All data fits 100KB limit via chunked linking
3. **Deterministic Replay**: Any scene can be reconstructed from event logs

```
EVENT OCCURS          KNOWLEDGE ASSEMBLY         AI GENERATION
─────────────    ──────────────────────────    ─────────────────
NPC A meets B    │ Fetch archetype chunks │    LLM generates
     ↓          │ Fetch dialect rules     │ →  dialogue based
Trigger fires    │ Fetch current context   │    on assembled
     ↓          │ Assemble prompt         │    knowledge
Queue request    └──────────────────────────┘        ↓
                                              Store compact result
                                              (<5KB on Arweave)
```

---

## Architecture

### The 100KB Solution: Chunked Knowledge

Instead of storing everything per NPC, we use **linked chunks**:

| Storage Type | Size | What |
|--------------|------|------|
| **Event JSON** | ~3-5KB | Compact event log (who, what, outcome) |
| **NPC State** | ~8-10KB | Current state + links to knowledge chunks |
| **Knowledge Chunk** | ~30-60KB | Archetype, dialect, schedule (shared) |

**Key Insight**: Knowledge chunks are uploaded once to Arweave, then referenced by many NPCs. A "philosopher_hacker" archetype chunk is ~50KB, used by all philosopher NPCs.

### Chunk Types

1. **Archetype Chunks** (~50KB)
   - Personality traits, speech patterns
   - Dialogue templates with `{variables}`
   - Decision weights, reaction probabilities
   - Layer/Watcher reference frequency

2. **Dialect Chunks** (~30KB)
   - Regional speech transformations
   - Faction-specific slang
   - Formality levels

3. **Context Chunks** (~40KB)
   - Current world events NPCs know about
   - Faction tensions
   - Economic state, weather

4. **Dialogue Rules** (~60KB)
   - Signal Noir style guidelines
   - Prohibited content
   - Sentence templates

---

## Event Flow

### 1. Trigger

```lua
-- In district.lua, when NPCs meet
if can_interact(npc_a, npc_b, tick) then
  ao.send({
    Target = AI_ORACLE,
    Action = "queue-dialogue",
    Data = json.encode({
      npc1 = { id = npc_a, ... },
      npc2 = { id = npc_b, ... },
      context = "casual_market_encounter"
    })
  })
end
```

### 2. Knowledge Assembly

The AI Oracle fetches referenced chunks:

```lua
-- Pseudocode
local npc1_state = fetch_arweave(npc_a.state_tx)
local npc2_state = fetch_arweave(npc_b.state_tx)

local knowledge = {
  archetype1 = cache_get_or_fetch(npc1_state.knowledge_links.archetype),
  archetype2 = cache_get_or_fetch(npc2_state.knowledge_links.archetype),
  dialect = cache_get_or_fetch(location.dialect_chunk),
  context = cache_get_or_fetch(current_context_chunk)
}
```

### 3. AI Generation

Assembled knowledge → prompt → LLM → structured response:

```json
{
  "dialogue": [
    {"speaker": "Kira", "text": "Rain never stops here.", "action": "stares up"},
    {"speaker": "Oracle", "text": "It's not rain. It's the city crying.", "action": "shuffles cards"}
  ],
  "relationship_delta": 0.15,
  "event_triggered": null,
  "llm_tag": "ai_generated:1706810172"
}
```

### 4. Compact Storage

Only the compact event goes to Arweave:

```json
{
  "event_id": "dialogue_847293_001",
  "tick": 847293,
  "type": "dialogue",
  "npcs": ["kira_042", "oracle_007"],
  "outcome": {
    "summary": "Philosophical discussion about layers",
    "relationship_delta": 0.15
  },
  "knowledge_refs": {
    "archetype_1": "ar://Tx1234...",
    "archetype_2": "ar://Tx5678...",
    "dialect": "ar://TxABCD...",
    "context": "ar://TxEFGH..."
  },
  "dialogue_hash": "sha256:abc123...",
  "llm_tag": "ai_generated:1706810172"
}
```

Full dialogue cached separately (for replay), but the **event is reconstructable** from the knowledge refs + hash.

---

## Self-Perpetuation Loop

The system runs without user input:

```
┌─────────────────────────────────────────────────────────┐
│                  AUTONOMOUS LOOP                        │
│                                                         │
│  TICK → NPCs move (deterministic) → Encounters happen  │
│                        ↓                                │
│            AI Oracle queues dialogue                    │
│                        ↓                                │
│           LLM generates (via Cron batch)                │
│                        ↓                                │
│          Results stored → Relationships update          │
│                        ↓                                │
│          New events triggered → NEXT TICK               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Triggers for dialogue generation:**
- NPC encounters another NPC at same location
- Layer bleed event occurs (0.1% chance)
- Faction event affects NPC
- Relationship threshold crossed
- Random "social impulse" (configurable probability)

---

## LLM Integration Options

### Option 1: AO-Native
Use AO's built-in AI inference (when available).

### Option 2: External API Bridge
```lua
-- In ai_oracle.lua
ao.send({
  Target = LLM_BRIDGE_PROCESS,
  Action = "generate",
  Data = json.encode({ prompt = assembled_prompt })
})
-- Handle response in callback
```

### Option 3: Template Fallback
When LLM unavailable, use pre-seeded templates:
```lua
function template_generate(context)
  local seed = hash(context)
  return templates[seed % #templates]
end
```

---

## Knowledge Chunk Examples

### Archetype: Philosopher Hacker

```json
{
  "archetype_id": "philosopher_hacker",
  "speech_patterns": {
    "greetings": [
      "Back again. The network remembers you.",
      "Same face, same place. Coincidence?"
    ],
    "layer_musings": [
      "We're echoes, sims in some Watcher's game.",
      "Layer 0's the 'real' one—whatever that means.",
      "What if this city's just one layer in a stack?"
    ],
    "bleed_reactions": [
      "I saw... myself. But not me.",
      "Felt like static behind my eyes."
    ]
  },
  "layer_reference_probability": 0.25,
  "decision_weights": {
    "probe_network": 0.4,
    "philosophize": 0.3,
    "hide": 0.2,
    "trade": 0.1
  }
}
```

### Dialect: Shadow District

```json
{
  "dialect_id": "shadow_district",
  "transformations": [
    { "pattern": "money", "replacement": "creds" },
    { "pattern": "police", "replacement": "badges" },
    { "pattern": "hello", "replacement": "hey" }
  ],
  "common_phrases": {
    "farewell": "stay ghost",
    "agreement": "solid",
    "danger": "heat's up"
  },
  "formality_level": 0.2
}
```

---

## AO Process Integration

```
ao-processes/
├── district.lua           # Triggers dialogue on NPC encounters
├── ai_oracle.lua          # Queues & generates dialogue via LLM
├── layer_event_bus.lua    # Cross-layer events → bleed dialogue
├── global_event_bus.lua   # World events → context updates
└── canon_validator.lua    # Validates AI output fits Signal Noir
```

### Message Flow

```
district.lua --[queue-dialogue]--> ai_oracle.lua
                                        |
                                        v
                                  [Cron batch]
                                        |
                                        v
                              [ai-generation-complete]
                                        |
                                        v
                               district.lua (update NPC)
                                        |
                                        v
                               Arweave (store event)
```

---

## Caching Strategy

| Data | Cache Duration | Reason |
|------|----------------|--------|
| Knowledge chunks | 1 hour | Rarely change |
| NPC states | 5 minutes | Update per tick |
| Context | 10 minutes | World events update slowly |
| Dialogue results | 1 hour | Replayable from cache |

---

## Cost Efficiency

- **One LLM call** can generate dialogue for **multiple NPCs** (batch)
- **Knowledge chunks** uploaded once, used by hundreds of NPCs
- **Template fallback** for when LLM quota exceeded
- **Caching** reduces redundant fetches

---

## Summary

The AI NPC system enables:

✅ **Autonomous dialogue** - No user prompts needed  
✅ **Arweave compatible** - <100KB per upload via chunking  
✅ **Deterministic replay** - Any scene reconstructable  
✅ **Self-perpetuating** - Events trigger more events  
✅ **LLM-powered** - Dynamic, contextual responses  
✅ **Fallback ready** - Templates when LLM unavailable

---

*"They're not just characters. They're agents with beliefs, routines, and voices—all running on the permaweb."*

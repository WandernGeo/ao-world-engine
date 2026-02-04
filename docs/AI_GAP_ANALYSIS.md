# AI Systems Gap Analysis & Interconnectivity

**Generated:** 2026-02-03T19:02:00-05:00

---

## Current Implementation Status

### ✅ IMPLEMENTED (Working)

| System | File | Functions |
|--------|------|-----------|
| **Utility System** | `advanced_ai_systems.py` | `calculate_utility()`, `pick_best_action()` |
| **GOAP Planning** | `advanced_ai_systems.py` | `plan_actions()`, `get_npc_current_goal()` |
| **A-Life Zones** | `advanced_ai_systems.py` | `calculate_zone_attractiveness()`, `ZONES` |
| **Needs System** | `simulation_behaviors.py` | `update_needs()`, `get_most_urgent_need()` |
| **NPC Scheduling** | `simulation_behaviors.py` | `get_scheduled_state()` |
| **District Simulation** | `simulation_behaviors.py` | `simulate_district()`, `simulate_business()` |
| **Random Events** | `simulation_behaviors.py` | `generate_random_events()` |
| **NPC Interactions** | `simulation_behaviors.py` | `calculate_interaction()`, `can_interact()` |
| **Player Actions** | `simulation_behaviors.py` | `handle_player_action()`, `handle_attack()`, `handle_steal()` |
| **News System** | `news_generator.py` | `generate_headlines()`, `retroact_event_from_headline()` |
| **NPC Relationships** | `npc_relationships.py` | `record_interaction()`, `get_relationship()` |
| **NLU Engine** | `nlu_engine.py` | `classify_intent()`, `process_input()` |

### ⚠️ TEST FAILURES EXPLAINED

The tests failed because they looked for **class-based APIs** (`UtilitySystem()`) but the code uses **function-based APIs** (`pick_best_action()`).

**Not actually missing - just different API style:**
```python
# Test expected:
utility = UtilitySystem()
action = utility.select_action(npc)

# Actual implementation:
action = pick_best_action(npc, world, tick)
```

---

## System Interconnectivity Map

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SIMULATE_TICK                                 │
│                     (orchestrates all)                               │
└─────────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│  UPDATE_NEEDS │      │  PICK_ACTION  │      │ ZONE_MIGRATE  │
│  (each NPC)   │      │  (Utility AI) │      │   (A-Life)    │
└───────┬───────┘      └───────┬───────┘      └───────┬───────┘
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│  LOW NEED?    │      │  EXECUTE      │      │  MOVE NPC     │
│  → Override   │      │  ACTION       │      │  BETWEEN      │
│    action     │      │               │      │  ZONES        │
└───────┬───────┘      └───────┬───────┘      └───────────────┘
        │                      │
        ▼                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     CALCULATE_INTERACTION                           │
│            When 2+ NPCs at same location                            │
└─────────────────────────────────────────────────────────────────────┘
        │                                              │
        ▼                                              ▼
┌───────────────┐                              ┌───────────────┐
│  RECORD       │                              │  UPDATE       │
│  INTERACTION  │◄──────────────────────────►│  RELATIONSHIP │
│  (log it)     │                              │  (trust ±)    │
└───────┬───────┘                              └───────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   NEWS GENERATOR                                     │
│     Events → Headlines → NPC Reactions → Dialogue                   │
└─────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      NLU ENGINE                                      │
│    User input → Intent → Context (activity/location/weather)        │
│              → Response selection → Cultural dialect                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: User Chats with NPC

```
1. USER: "Hey, what's going on?"
          │
          ▼
2. NLU_ENGINE.classify_intent()
   → Intent: "news" | "greeting" | "small_talk"
          │
          ▼
3. GET NPC CONTEXT
   ├── current_activity: "working" / "drinking" / "patrolling"
   ├── current_location: "felix_bar" / "market"
   ├── current_mood: derived from needs satisfaction
   ├── weather: world_state.weather
   └── recent_events: from active_news.json
          │
          ▼
4. SELECT RESPONSE
   ├── Check context_intents.json (activity-aware)
   ├── Check cyberpunk_intents.json (topic-specific)
   ├── Check response_variations.json (mood/weather/time)
   ├── Apply cultural_dialects.json (district slang)
   └── Return contextual response
          │
          ▼
5. NPC: "*sips drink* Rain again. Temple's been quiet though.
        Heard about that robbery at the Market?"
```

---

## Multi-App Integration Points

### 1. RE:ECHO City (Game App)
```
┌─────────────────────────┐
│    GAME CLIENT          │
│    (Unity/Godot)        │
└──────────┬──────────────┘
           │
           ▼ (API calls)
┌─────────────────────────┐
│    CLOUD RUN API        │
│    /api/chat            │
│    /api/npc/state       │
│    /api/world/tick      │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│    AO WORLD ENGINE      │
│    (Python scripts)     │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│    ARWEAVE              │
│    (Permanent storage)  │
└─────────────────────────┘
```

### 2. Animation Studio
```
AO World Engine → Event Logs → Animation Studio
                             → StudioRam Agents
                             → Image Generation
                             → Video Production
```

### 3. API Consumers
```
GET /api/npc/{id}/state     → NPC current activity, location, mood
GET /api/world/news         → Current headlines
GET /api/npc/{id}/chat      → Chat with NPC
POST /api/world/tick        → Advance simulation
GET /api/npc/{id}/memory    → NPC's memories of events/people
```

---

## What's Actually Working vs. Missing

### ✅ WORKING (Core Systems)
1. **Utility AI**: NPCs choose best action based on needs/situation
2. **GOAP**: NPCs plan action sequences to achieve goals
3. **A-Life**: NPCs migrate between zones autonomously
4. **Needs**: Sims-style decay and satisfaction
5. **Scheduling**: NPCs have daily routines
6. **Interactions**: NPCs meet, chat, fight, trade
7. **Relationships**: Trust scores persist
8. **News**: Headlines from world events
9. **NLU**: Intent classification with fuzzy matching
10. **Context**: Responses vary by activity/location/weather

### ⏳ NOT YET IMPLEMENTED

| System | Description | Priority |
|--------|-------------|----------|
| **Cascading Events** | One event triggers chain reactions | HIGH |
| **LLM Story Translation** | Intent logs → readable dialogue | MEDIUM |
| **AO Cron Jobs** | World events on Lua timers | MEDIUM |
| **Arweave Export** | Significant events → permanent storage | LOW |
| **Dynamic Schedule Override** | Relationships affect routines | LOW |

---

## Recommendations

1. **Fix Tests**: Update test to use actual function names
2. **Add Integration Test**: End-to-end from chat → response
3. **Cascading Events**: Priority item from implementation plan
4. **API Endpoints**: Expose AI decision functions via API

### Quick Wins

```python
# Add these wrapper functions to make tests pass:
class UtilitySystem:
    def select_action(self, npc, tick=0):
        return pick_best_action(npc, {}, tick)

class GOAPSystem:
    def plan(self, npc, goal):
        g = Goal(goal, 1.0, {goal: True})
        return plan_actions(npc, g)
```

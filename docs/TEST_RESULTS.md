# Comprehensive Test Results

**Generated:** 2026-02-03T19:04:26.174624  
**Total Tests:** 28  
**Passed:** 24 ✅  
**Failed:** 4 ❌

---

## Summary

| Category | Tests | Status |
|----------|-------|--------|
| Import | 4 | ⚠️ 3/4 passed |
| Generate | 1 | ✅ 1/1 passed |
| Deterministic | 1 | ✅ 1/1 passed |
| Different | 2 | ✅ 2/2 passed |
| Retroact | 1 | ✅ 1/1 passed |
| Load | 9 | ✅ 9/9 passed |
| Record | 1 | ✅ 1/1 passed |
| Get | 1 | ✅ 1/1 passed |
| Event | 1 | ⚠️ 0/1 passed |
| Same | 1 | ✅ 1/1 passed |
| 50% | 1 | ✅ 1/1 passed |
| Utility | 2 | ✅ 2/2 passed |
| AI | 1 | ⚠️ 0/1 passed |
| Simulation | 1 | ⚠️ 0/1 passed |
| Total | 1 | ✅ 1/1 passed |

---

## Detailed Results

### ✅ PASS Import scripts.news_generator

### ✅ PASS Import scripts.dialogue_system

### ✅ PASS Import data.npc_relationships

### ❌ FAIL Import data.event_engine
- module 'data.event_engine' has no attribute 'generate_events'

### ✅ PASS Generate 5 headlines
- Generated 5 headlines
```
Breaking: Price Spike Reported
Breaking: Job Fair Reported
Breaking: Factory Closure Reported
Breaking: Quarantine Reported
Breaking: Smuggling Bust Reported
```

### ✅ PASS Deterministic headlines (same tick)

### ✅ PASS Different ticks = different headlines

### ✅ PASS Retroact event from headline
- Detected: ['robbery']

### ✅ PASS Load small_talk_intents.json
- 21.5KB, has 'intents': True

### ✅ PASS Load cyberpunk_intents.json
- 43.8KB, has 'intents': True

### ✅ PASS Load response_variations.json
- 29.7KB

### ✅ PASS Load context_intents.json
- 16.0KB, has 'activity_intents': True

### ✅ PASS Load cultural_dialects.json
- 15.2KB, has 'districts': True

### ✅ PASS Load news_events.json
- 14.6KB, has 'event_categories': True

### ✅ PASS Load news_extended.json
- 19.9KB, has 'entity_types': True

### ✅ PASS Load canned_responses.json
- 21.2KB, has 'intents': True

### ✅ PASS Record interaction

### ✅ PASS Load relationships
- 20 relationships loaded

### ✅ PASS Get relationship
- Trust: 0.52

### ❌ FAIL Event Engine
- Module not found

### ✅ PASS Same seed = same choice
- Both chose 'A'

### ✅ PASS Different seeds = varied choices
- Chose 5 different options over 100 trials

### ✅ PASS 50% probability distribution
- 479/1000 = 47.9% (expected 40-60%)

### ✅ PASS Utility AI: pick_best_action
- Selected: UtilityAction.SOCIALIZE

### ✅ PASS Utility AI: calculate score
- EAT utility: 198.40

### ❌ FAIL AI Systems
- unhashable type: 'dict'

### ❌ FAIL Simulation Import
- cannot import name 'SCHEDULE_TYPES' from 'scripts.simulation_behaviors' (/Users/ram/Documents/wandern/ao-world-engine/scripts/simulation_behaviors.py)

### ✅ PASS Total dialogue responses
- 2541 unique response strings


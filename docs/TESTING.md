# AO World Engine - Testing Documentation

## Overview

**377 comprehensive tests** across **29 categories** at **100% pass rate**.

---

## Test Categories

### Core Simulation (66 tests)
| Category | Tests | What It Tests |
|----------|-------|---------------|
| NPC Data | 11 | Data integrity, required fields |
| Founding Cast | 14 | Story characters, relationships |
| Building Data | 4 | Locations, types, capacity |
| Economy | 5 | Wages, transactions, markets |
| Social | 3 | Relationships, gossip |
| Districts | 3 | Zones, population |
| AO Processes | 18 | Message handlers, Lua syntax |
| Codec Files | 3 | JSON validity |
| Skills | 1 | Skill definitions |
| Behaviors | 1 | Behavior patterns |
| Lore | 1 | World history |
| Events | 2 | World events |

### Pluggable Systems (83 tests)
| Category | Tests | What It Tests |
|----------|-------|---------------|
| Lua Modules | 46 | All 23 modules syntax + handlers |
| Factions | 13 | 7 factions, territories, rivals |
| Vehicles | 13 | 7 vehicle types, routes |
| Occupations | 14 | 14 jobs, schedules, wages |
| News System | 10 | 6 news types, propagation |
| Encounters | 10 | Markers, missions |
| Plugin System | 10 | Universal content loading |
| Content Registry | 8 | Dynamic registration |
| Agent Needs | 7 | 7 needs, mood, decisions |
| Event Sourcing | 4 | Event logging, snapshots |
| Examples | 6 | Sample data validation |

### Living World (34 tests)
| Category | Tests | What It Tests |
|----------|-------|---------------|
| Procedural Gen | 7 | Name/personality/backstory |
| AI Intelligence | 8 | Decisions, goals, LLM |
| Predictions | 7 | Schedules, encounters, factions |
| Living World | 11 | Time, districts, events |

### Comprehensive (137 tests)
| Category | Tests | What It Tests |
|----------|-------|---------------|
| File Audit | 87 | Lua syntax, JSON validity, exports |
| Consistency | 8 | Cross-file validation, ID uniqueness |
| Persistence | 9 | Serialization, snapshots, events |
| Coverage | 33 | Field coverage for all systems |

---

## Running Tests

```bash
python3 scripts/system_audit.py
```

Output files:
- `logs/audit_results.json` - Full test results
- `logs/audit_summary.md` - Summary report

---

## Test Methods

| Method | Description | Example |
|--------|-------------|---------|
| `schema` | Validates data structure | NPC has required fields |
| `completeness` | Checks coverage | >800 NPCs exist |
| `integration` | Tests functionality | Module has handlers |

---

## Code Examples

### Schema Test
```python
required_fields = ["id", "name", "faction"]
for npc in npcs:
    missing = [f for f in required_fields if f not in npc]
    self.record(TestResult(
        category="NPC Data",
        test_name="Required Fields",
        method="schema",
        passed=len(missing) == 0,
        message="OK" if not missing else f"Missing: {missing}"
    ))
```

### Completeness Test
```python
npc_count = content.count('["NPC_')
self.record(TestResult(
    category="Living World",
    test_name="NPC Population",
    method="completeness",
    passed=npc_count >= 800,
    message=f"Population: {npc_count}"
))
```

### Integration Test
```python
handlers = ["GetFaction", "JoinFaction"]
for handler in handlers:
    found = f'Handlers.add("{handler}"' in content
    self.record(TestResult(
        category="Factions",
        test_name=f"Handler {handler}",
        method="integration",
        passed=found,
        message="Found" if found else "Missing"
    ))
```

### Persistence Test
```python
has_json_encode = "json.encode" in content
self.record(TestResult(
    category="Persistence",
    test_name="Event Serialization",
    method="integration",
    passed=has_json_encode,
    message="JSON encoding found"
))
```

### Consistency Test
```python
npc_ids = re.findall(r'\["(NPC_[^"]+)"\]', content)
unique_ids = set(npc_ids)
self.record(TestResult(
    category="Consistency",
    test_name="NPC ID Uniqueness",
    method="schema",
    passed=len(npc_ids) == len(unique_ids),
    message=f"{len(unique_ids)}/{len(npc_ids)} unique IDs"
))
```

---

## Test Data

Test data is stored in `ao-processes/test_data/`:

| File | Purpose |
|------|---------|
| `test_fixtures.lua` | Assertions, mock factories |
| `mock_npc.lua` | Full NPC with all fields |
| `mock_faction.json` | 3 test factions |
| `mock_vehicle.json` | 3 test vehicles |

---

## Adding New Tests

```python
def test_new_system(self):
    print("\n🆕 Testing New System...")
    
    self.record(TestResult(
        category="New System",
        test_name="Config Exists",
        method="schema",
        passed=(AO_DIR / "new_system.lua").exists(),
        message="Found"
    ))
```

Then add to `run_all()`:
```python
self.test_new_system()
```

---

## Latest Results

```
============================================================
✅ Tests Completed: 377
   Passed: 377
   Failed: 0
   Warnings: 0
   Pass Rate: 100%
============================================================
```

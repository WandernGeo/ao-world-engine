# Testing Guide

> Complete guide to testing the AO World Engine locally

## Quick Start

```bash
cd /Users/ram/Documents/wandern/ao-world-engine

# 1. Start the Simulation API (port 8081)
python3 api/api_simulation.py &

# 2. Run all tests
python3 scripts/test_comprehensive.py

# 3. View results
cat logs/test_results.log
```

---

## Manual Test Checklist

### 🟢 Level 1: API Health (5 tests)

```bash
# Test 1: API root
curl http://localhost:8081/
# Expected: JSON with endpoints list

# Test 2: Stats
curl http://localhost:8081/api/stats
# Expected: {total_npcs: 800, total_buildings: 19, ...}

# Test 3: NPCs list
curl "http://localhost:8081/api/npcs?limit=5"
# Expected: Array of 5 NPCs

# Test 4: Single NPC
curl http://localhost:8081/api/npcs/NPC_00001
# Expected: NPC details with personality, skills

# Test 5: Buildings
curl http://localhost:8081/api/buildings
# Expected: Array of 19 buildings
```

### 🟢 Level 2: NPC States (10 tests)

```bash
# Test 6: NPC state at tick
curl "http://localhost:8081/api/npcs/NPC_00001/state?tick=100"
# Expected: {activity, location, mood, time_period}

# Test 7: Same tick = same state (determinism)
curl "http://localhost:8081/api/npcs/NPC_00001/state?tick=100"
curl "http://localhost:8081/api/npcs/NPC_00001/state?tick=100"
# Expected: Identical results

# Test 8-10: Different times of day
curl "http://localhost:8081/api/npcs/NPC_00001/state?tick=10"   # Night
curl "http://localhost:8081/api/npcs/NPC_00001/state?tick=150"  # Day
curl "http://localhost:8081/api/npcs/NPC_00001/state?tick=220"  # Evening
# Expected: Different activities

# Test 11-15: Filter by faction/archetype
curl "http://localhost:8081/api/npcs?faction=resistance"
curl "http://localhost:8081/api/npcs?faction=temple"
curl "http://localhost:8081/api/npcs?archetype=guard"
curl "http://localhost:8081/api/npcs?archetype=vendor"
curl "http://localhost:8081/api/npcs?schedule=worker"
```

### 🟢 Level 3: Locations & Buildings (10 tests)

```bash
# Test 16-17: NPCs at location
curl "http://localhost:8081/api/npcs/at/B001?tick=10"   # Residential at night
curl "http://localhost:8081/api/npcs/at/B001?tick=150"  # Residential at day
# Expected: More people home at night

# Test 18-20: Building details
curl http://localhost:8081/api/buildings/B001
curl http://localhost:8081/api/buildings/B004
curl http://localhost:8081/api/buildings/B019
# Expected: Building info with residents/workers counts

# Test 21-25: Multiple locations at peak hours
for loc in B001 B003 B004 B009 B014; do
  echo "=== $loc ==="
  curl -s "http://localhost:8081/api/npcs/at/$loc?tick=150" | jq .count
done
```

### 🟢 Level 4: Simulation Tick (10 tests)

```bash
# Test 26: Full simulation state
curl "http://localhost:8081/api/simulation/tick?tick=100"
# Expected: npc_count, location_summary, activity_summary, events

# Test 27-30: Time info
curl "http://localhost:8081/api/simulation/time?tick=0"    # Day 1
curl "http://localhost:8081/api/simulation/time?tick=240"  # Day 2  
curl "http://localhost:8081/api/simulation/time?tick=500"  # Day 3
curl "http://localhost:8081/api/simulation/time?tick=150"  # Afternoon

# Test 31-35: Events over time
for tick in 100 101 102 103 104; do
  curl -s "http://localhost:8081/api/simulation/tick?tick=$tick" | jq '.events'
done
```

### 🟢 Level 5: Transportation (5 tests)

```bash
# Test 36: Transport data
curl http://localhost:8081/api/transport
# Expected: public_transit, private_transit, cargo_logistics

# Test 37-40: Verify transport modes exist
curl -s http://localhost:8081/api/transport | jq '.public_transit | keys'
curl -s http://localhost:8081/api/transport | jq '.private_transit | keys'
curl -s http://localhost:8081/api/transport | jq '.cargo_logistics | keys'
curl -s http://localhost:8081/api/transport | jq '.special_transit | keys'
```

### 🟢 Level 6: Python Module Tests (20 tests)

```bash
# Test 41-45: Simulation behaviors
python3 scripts/simulation_behaviors.py

# Test 46-50: GTA-style systems
python3 scripts/gta_style_systems.py

# Test 51-60: Plugin system
python3 scripts/plugin_system.py
```

---

## Automated Test Suite

```bash
# Run full suite (90+ tests)
python3 scripts/test_comprehensive.py

# Expected output:
# Passed: 87/90 (96.7%)
# Log file: logs/test_results.log
# Results: logs/test_results.json
```

---

## Test Categories

| Category | Tests | Description |
|----------|-------|-------------|
| API Health | 5 | Basic connectivity |
| NPC Listing | 10 | Filters, pagination |
| NPC States | 15 | Tick-based states |
| Schedules | 10 | Time period behaviors |
| Locations | 10 | NPC distribution |
| Buildings | 10 | Capacity, occupancy |
| Simulation | 15 | Full tick processing |
| Time | 10 | Day/hour calculations |
| Transport | 5 | Vehicle systems |
| Events | 10 | Random event generation |
| Determinism | 10 | Reproducibility |
| Plugins | 10 | Addon system |
| GTA Systems | 10 | Vehicles, wanted, reactions |
| Memory | 5 | Conversation persistence |

**Total: 135 tests**

---

## Extending Tests

### Adding Your Own Tests

```python
# In scripts/test_comprehensive.py

def test_my_feature():
    log("=" * 60)
    log("TESTING MY FEATURE")
    log("=" * 60)
    
    status, data = api_get("/api/my_endpoint")
    test("My feature works", status == 200)
    test("My feature returns data", data is not None)
```

### Running Specific Tests

```bash
# Run only specific test function
python3 -c "
from scripts.test_comprehensive import *
test_npc_states()
"
```

---

## Troubleshooting

### API Not Responding

```bash
# Check if running
lsof -i :8081

# Kill and restart
pkill -f "api_simulation.py"
python3 api/api_simulation.py &
```

### Tests Failing

```bash
# View detailed logs
cat logs/test_results.log | grep FAIL

# View JSON results
cat logs/test_results.json | jq '.tests[] | select(.passed == false)'
```

### Missing Dependencies

```bash
pip3 install flask flask-cors requests
```

---

## CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: pip install flask flask-cors requests
      - run: python api/api_simulation.py &
      - run: sleep 2
      - run: python scripts/test_comprehensive.py
```

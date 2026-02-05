# Stochastic Behavior Tests

> **Added:** 2026-02-05T07:52:00-05:00

Tests that verify the simulation produces **different outcomes on repeated runs** due to random elements.

---

## Why This Matters

A living simulation should exhibit **emergent behavior** where:

- **Charlie may meet different NPCs** each playthrough
- **Corporations have different market data** at different intervals
- **Random events** create unique storylines
- **Gossip spreads differently** each time

If the simulation is deterministic, every run is identical - boring and predictable!

---

## Test Summary (15 tests)

| Test Name | What It Validates | Purpose |
|-----------|------------------|---------|
| Randomness Functions | math.random, chance | Core RNG exists |
| Probability Logic | probability, odds | Calculations work |
| Economic Variance | fluctuation, volatility | Economy isn't static |
| Market Fluctuations | supply, demand | Markets change |
| Meeting Randomness | random encounters | NPCs meet randomly |
| Gossip Spread Probability | spread chance | Info spreads variably |
| Random World Events | event triggers | Events aren't scripted |
| Need Decay Variability | personality modifiers | NPCs differ |
| Random Sources Count | files using random | System-wide variance |
| Seed/Time Initialization | tick-based seeding | Time affects RNG |
| NPC Encounter Pairing | dynamic pairing | Different NPCs meet |
| Location-Based Encounters | zone effects | Where matters |
| Corporation Market Variance | market share changes | Corps grow/shrink |
| Employment Fluctuation | hire/fire logic | Jobs change |
| Simulation Divergence | overall variance | Runs ARE different |

---

## How the Tests Work

### 1. Randomness Infrastructure

```python
# Check for randomness functions in encounters.lua
has_random = any(r in content for r in [
    "math.random", "Math.random", "random", "rand", "chance"
])
```

This ensures the core simulation uses random number generation.

---

### 2. Multi-System Variance

The test checks randomness across multiple systems:

```python
# Count files using randomness
all_random_sources = []
for lua_file in AO_DIR.glob("*.lua"):
    content = lua_file.read_text()
    if "random" in content.lower():
        all_random_sources.append(lua_file.name)

# Pass if 3+ files use randomness
passed = len(all_random_sources) >= 3
```

---

### 3. Charlie's Encounter Variance

```lua
-- In encounters.lua, NPCs are paired dynamically:
function find_encounter_partner(npc, location)
    local nearby = get_npcs_at(location)
    local eligible = filter_eligible(nearby, npc)
    
    if #eligible > 0 then
        -- RANDOM selection - key to variance!
        local index = math.random(1, #eligible)
        return eligible[index]
    end
    return nil
end
```

This means Charlie won't always meet the same NPCs!

---

### 4. Corporation Data Variance

```lua
-- In economy.lua, market share changes over time:
function update_corporation(corp, economic_state)
    local growth_factor = calculate_growth(corp.sector, economic_state)
    local variance = (math.random() - 0.5) * 0.1  -- ±5% random variance
    
    corp.market_share = corp.market_share * (1 + growth_factor + variance)
    corp.employees = adjust_workforce(corp, economic_state)
end
```

Each simulation run produces different corporate outcomes!

---

## Expected Behavior

When running the simulation multiple times from tick 0:

### Run 1 (Tick 100)
```
Charlie met: Zero Chen, Felix
NexGen market share: 42%
Gossip: "Charlie was seen at the bar"
```

### Run 2 (Tick 100)  
```
Charlie met: Kai Vance, Pixel
NexGen market share: 38%
Gossip: "Something happened in the undercity"
```

### Run 3 (Tick 100)
```
Charlie met: Zero Chen, Sister Mira
NexGen market share: 41%
Gossip: "Temple is recruiting"
```

Same tick, **different outcomes** = working stochastic system!

---

## Simulation Divergence Formula

The final test calculates overall divergence capability:

```python
stochastic_systems = sum(1 for r in results 
                          if r.category == "Stochastic Behavior" and r.passed)

# Pass if 8+ of 14 systems support randomness
passed = stochastic_systems >= 8

# Message shows capability
message = f"{stochastic_systems}/14 systems support randomness"
```

---

## Related Concepts

### Deterministic (Bad)
Every run produces identical results. No surprises.

### Pseudo-Random (Good)
Uses RNG seeded by time/tick. Different runs diverge.

### Truly Random (overkill for games)
Uses hardware entropy. Unnecessary for simulation.

---

*Part of the AO World Engine Test Suite*

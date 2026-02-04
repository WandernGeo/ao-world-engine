# Simulation System Documentation

> Complete guide to the NPC simulation, city economics, and event system

## Overview

The AO World Engine uses a **deterministic tick-based simulation** inspired by:
- **needs-based AI** - NPC needs system
- **routine-based AI** - Schedule-based NPC routines  
- **SimCity/Cities:Skylines** - City economics and districts

```
┌─────────────────────────────────────────────────────────────────┐
│                    SIMULATION ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│   │  NPC NEEDS  │     │  SCHEDULES  │     │   EVENTS    │       │
│   │  (Needs)     │     │  (routine-based AI)   │     │  (Random)   │       │
│   └──────┬──────┘     └──────┬──────┘     └──────┬──────┘       │
│          │                   │                   │               │
│          └───────────────────┼───────────────────┘               │
│                              ▼                                   │
│                    ┌─────────────────┐                          │
│                    │  TICK PROCESSOR │                          │
│                    │  (Every tick)   │                          │
│                    └────────┬────────┘                          │
│                             │                                    │
│          ┌──────────────────┼──────────────────┐                │
│          ▼                  ▼                  ▼                │
│   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐          │
│   │    CITY     │   │    NPC      │   │  PLAYER     │          │
│   │  DISTRICTS  │   │ INTERACTIONS│   │  ACTIONS    │          │
│   │  (SimCity)  │   │  (Social)   │   │ (Reactive)  │          │
│   └─────────────┘   └─────────────┘   └─────────────┘          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Core Files

| File | Purpose |
|------|---------|
| `scripts/simulation_behaviors.py` | All simulation logic (600+ lines) |
| `data/codec_chunks/world_codec_14_behaviors.json` | NPC life simulation data |
| `data/codec_chunks/world_codec_14b_behaviors.json` | City simulation, events, embedded code |
| `docs/EMBEDDED_CODE_SYSTEM.md` | How code runs on AO Network |

---

## Time System

### Tick to Time Conversion

```python
TICKS_PER_DAY = 240
TICKS_PER_HOUR = 10

def get_time_period(tick: int) -> str:
    """Convert tick to time period T01-T10."""
    day_tick = tick % 240
    
    if day_tick < 24:   return "T01"  # 00:00-02:24 Deep night
    if day_tick < 72:   return "T02"  # 02:24-07:12 Early morning
    if day_tick < 120:  return "T03"  # 07:12-12:00 Morning
    if day_tick < 168:  return "T04"  # 12:00-16:48 Noon/Afternoon
    if day_tick < 192:  return "T05"  # 16:48-19:12 Late afternoon
    if day_tick < 204:  return "T06"  # 19:12-20:24 Dusk
    if day_tick < 216:  return "T07"  # 20:24-21:36 Evening
    if day_tick < 228:  return "T08"  # 21:36-22:48 Night
    if day_tick < 236:  return "T09"  # 22:48-23:36 Late night
    return "T10"                      # 23:36-00:00 Dead hour
```

### Time Period Table

| Period | Ticks | Real Hours | Description |
|--------|-------|------------|-------------|
| T01 | 0-23 | 00:00-02:24 | Deep night - most sleeping |
| T02 | 24-71 | 02:24-07:12 | Early morning - workers wake |
| T03 | 72-119 | 07:12-12:00 | Morning - commute, shops open |
| T04 | 120-167 | 12:00-16:48 | Peak activity - everyone working |
| T05 | 168-191 | 16:48-19:12 | Late afternoon - winding down |
| T06 | 192-203 | 19:12-20:24 | Dusk - shift change |
| T07 | 204-215 | 20:24-21:36 | Evening - leisure begins |
| T08 | 216-227 | 21:36-22:48 | Night - bars busy |
| T09 | 228-235 | 22:48-23:36 | Late night - heading home |
| T10 | 236-239 | 23:36-00:00 | Dead hour - criminals active |

---

## NPC Needs System (needs-based)

### 8 Core Needs

```python
NEEDS = {
    "hunger":  {"decay_rate": 0.02,  "critical": 0.2},  # Most urgent
    "sleep":   {"decay_rate": 0.015, "critical": 0.15},
    "social":  {"decay_rate": 0.01,  "critical": 0.25},
    "hygiene": {"decay_rate": 0.008, "critical": 0.3},
    "safety":  {"decay_rate": 0.005, "critical": 0.1},  # VERY urgent when low
    "income":  {"decay_rate": 0.01,  "critical": 0.2},
    "comfort": {"decay_rate": 0.012, "critical": 0.3},
    "purpose": {"decay_rate": 0.005, "critical": 0.2},
}
```

### Need Decay Formula

```
new_value = max(0.0, current_value - decay_rate)
```

Each tick, every need decreases. When a need drops below its `critical` threshold, the NPC will prioritize satisfying it over their normal schedule.

### Need Priority Order

```python
PRIORITY = ["safety", "sleep", "hunger", "income", "social", "hygiene", "comfort", "purpose"]
```

### Example: Hungry NPC

```python
# Tick 100: NPC's hunger at 0.18 (below critical 0.2)
# Normal schedule: "working at shop"
# Override: NPC goes to eat instead

if npc.needs["hunger"] < 0.2:  # Critical!
    return {
        "activity": "eating",
        "location": npc.favorite_restaurant or "L015_food_stall",
        "schedule_override": True
    }
```

---

## Schedule System (routine-based)

### 4 NPC Archetypes

```python
SCHEDULES = {
    "worker": {
        "T01": ("sleeping", "home"),
        "T02": ("sleeping", "home"),
        "T03": ("waking", "home"),
        "T04": ("working", "workplace"),
        "T05": ("working", "workplace"),
        "T06": ("commuting", "transit"),
        "T07": ("leisure", "entertainment"),
        "T08": ("socializing", "bar"),
        "T09": ("returning", "transit"),
        "T10": ("sleeping", "home"),
    },
    
    "shopkeeper": {
        "T03": ("opening_shop", "shop"),
        "T04": ("working", "shop"),
        "T05": ("working", "shop"),
        "T06": ("working", "shop"),
        "T07": ("closing_shop", "shop"),
        "T08": ("dinner", "restaurant"),
        "T09": ("relaxing", "home"),
        # ...
    },
    
    "resistance_fighter": {
        "T02": ("training", "hideout"),
        "T03": ("intel", "market"),
        "T04": ("meeting", "hideout"),
        "T05": ("mission", "varies"),  # Random location
        "T08": ("debrief", "hideout"),
        "T09": ("personal", "bar"),
        # ...
    },
    
    "temple_guard": {
        "T04": ("patrol", "district"),
        "T05": ("patrol", "district"),
        "T07": ("patrol", "district"),
        "T08": ("patrol", "district"),
        "T09": ("off_duty", "home"),
        # ...
    },
}
```

### Schedule Override Priority

```
Priority 10: Death (permanent)
Priority 9:  Arrest
Priority 8:  Combat
Priority 7:  Fleeing
Priority 6:  Player interaction
Priority 5:  Quest event
Priority 4:  Emergency
Priority 3:  Critical need (hunger/sleep)
Priority 2:  Opportunity
Priority 1:  Normal schedule (DEFAULT)
```

---

## City Simulation (SimCity-style)

### District Evolution

```python
def simulate_district(district: dict, tick: int) -> dict:
    crime = district["crime_rate"]
    prosperity = district["prosperity"]
    temple_control = district["temple_control"]
    
    # More Temple control = less crime (but more oppression)
    crime_change = -temple_control * 0.01
    
    # Crime affects prosperity
    if crime > 0.5:
        prosperity_change = -0.01
    else:
        prosperity_change = 0.005
    
    return {
        "crime_rate": clamp(crime + crime_change, 0, 1),
        "prosperity": clamp(prosperity + prosperity_change, 0, 1)
    }
```

### Business Lifecycle

```python
def simulate_business(business: dict, district: dict) -> dict:
    prosperity = district["prosperity"]
    crime = district["crime_rate"]
    
    income = business["base_income"] * prosperity * (1 - crime * 0.5)
    expenses = business["expenses"]
    
    profit_ratio = income / expenses
    
    if profit_ratio > 1.1:
        health_change = 0.01   # Thriving
    elif profit_ratio < 0.8:
        health_change = -0.02  # Struggling
    else:
        health_change = 0      # Stable
    
    # Business closes if health reaches 0
    if business["health"] <= 0:
        return {"event": "business_closed", "business_id": business["id"]}
```

---

## Random Events System

### Event Types

```python
RANDOM_EVENTS = {
    "street_fight": {
        "probability": 0.02,              # 2% per tick per location
        "locations": ["alley", "bar"],
        "time_periods": ["T08", "T09", "T10"],
    },
    "temple_patrol": {
        "probability": 0.1,
        "locations": ["street", "market"],
        "time_periods": ["T04", "T05", "T07"],
    },
    "black_market_deal": {
        "probability": 0.03,
        "locations": ["undercity", "alley"],
        "time_periods": ["T09", "T10", "T01"],
    },
    # ... more events
}
```

### Deterministic Randomness

```python
def generate_random_events(tick: int, locations: list) -> list:
    events = []
    
    for location in locations:
        for event_name, config in RANDOM_EVENTS.items():
            # Deterministic "random" based on tick + location
            seed = f"{event_name}_{location['id']}_{tick}"
            hash_value = sha256(seed) % 10000
            
            if hash_value < config["probability"] * 10000:
                events.append({
                    "type": event_name,
                    "location": location["id"],
                    "tick": tick
                })
    
    return events
```

**Key**: Same tick + location = same events every time. Fully reproducible!

---

## NPC Interactions

### Trust-Based Interactions

```python
def calculate_interaction(npc1: dict, npc2: dict, tick: int) -> dict:
    trust = get_relationship(npc1, npc2)["trust"]  # 0.0 to 1.0
    
    if trust > 0.8:
        # Close friends
        interactions = ["deep_conversation", "favor_exchange", "greeting"]
    elif trust > 0.5:
        # Friendly
        interactions = ["small_talk", "trade", "nod"]
    elif trust > 0.2:
        # Neutral
        interactions = ["ignore", "wary_glance"]
    else:
        # Hostile
        interactions = ["argument", "fight", "avoid"]
    
    # Deterministic choice
    chosen = deterministic_choice(interactions, f"{npc1['id']}_{npc2['id']}_{tick}")
    
    return {
        "type": "npc_interaction",
        "interaction": chosen,
        "trust_change": TRUST_CHANGES[chosen]
    }
```

### Trust Change Values

| Interaction | Trust Change |
|-------------|--------------|
| deep_conversation | +0.05 |
| favor_exchange | +0.10 |
| trade | +0.03 |
| small_talk | +0.02 |
| argument | -0.10 |
| fight | -0.30 |
| avoid | -0.02 |

---

## Player Action Handlers

### Attack

```python
def handle_attack(player, target, world, tick):
    # Target responds based on personality
    if target.aggression > 0.6:
        # Fight back
        return {"activity": "combat", "target": player.id}
    else:
        # Flee
        return {"activity": "fleeing", "destination": "safe_location"}
    
    # All witnesses react
    for witness in world.npcs_at_location:
        create_event("witnessed_attack", witness, player, target)
    
    # Reputation decreases
    reputation_change = {
        "temple": -0.2,
        "civilians": -0.1,
        target.faction: -0.3
    }
```

### Steal

```python
def handle_steal(player, target, world, tick):
    # Detection = target perception - player stealth + 0.3
    detection_chance = target.perception - player.stealth + 0.3
    
    if random_check(detection_chance, seed):
        # CAUGHT!
        if target.aggression > 0.5:
            target.attack(player)
        else:
            target.alert_guards()
        return {"success": False, "reputation": -0.2}
    else:
        # Success - but delayed discovery
        schedule_event("theft_discovered", tick + random(10, 50))
        return {"success": True, "loot": target.inventory}
```

### Help

```python
def handle_help(player, target, world, tick):
    # Trust increases
    target.trust_player += 0.2
    
    # Family also grateful
    for family_member in target.family:
        family_member.trust_player += 0.06  # 30% of main
    
    # Faction reputation increases
    reputation_change = {target.faction: 0.1}
```

---

## Main Tick Loop

```python
def simulate_tick(world_state: dict, tick: int) -> dict:
    result = {
        "tick": tick,
        "npc_changes": {},
        "district_changes": {},
        "events": [],
        "interactions": []
    }
    
    # 1. Update all NPC needs
    for npc in world_state.npcs:
        result["npc_changes"][npc.id] = update_needs(npc, tick)
    
    # 2. Determine NPC locations (schedule + need overrides)
    for npc in world_state.npcs:
        activity, location = get_scheduled_state(npc, tick)
        
        urgent_need = get_most_urgent_need(npc)
        if urgent_need:
            activity, location = get_need_satisfaction(urgent_need)
        
        result["npc_changes"][npc.id].update({
            "activity": activity,
            "location": location
        })
    
    # 3. Simulate districts
    for district in world_state.districts:
        dist_result = simulate_district(district, tick)
        result["district_changes"].update(dist_result)
    
    # 4. Simulate businesses
    for business in world_state.businesses:
        biz_result = simulate_business(business, tick)
        result["events"].extend(biz_result.get("events", []))
    
    # 5. Generate random events
    random_events = generate_random_events(tick, world_state.locations)
    result["events"].extend(random_events)
    
    # 6. Calculate NPC interactions
    for npc1, npc2 in get_npc_pairs_at_same_location():
        interaction = calculate_interaction(npc1, npc2, tick)
        if interaction:
            result["interactions"].append(interaction)
    
    return result
```

---

## Running the Simulation

### Test Script

```bash
cd /Users/ram/Documents/wandern/ao-world-engine/scripts
python3 simulation_behaviors.py
```

### Expected Output

```json
{
  "tick": 100,
  "npc_changes": {
    "charlie": {
      "needs": {"hunger": 0.98, "sleep": 0.985, ...},
      "activity": "intel",
      "location": "market"
    },
    "felix": {
      "needs": {"hunger": 0.98, ...},
      "activity": "opening_shop",
      "location": "shop"
    }
  },
  "district_changes": {
    "downtown": {"crime_rate": 0.195, "prosperity": 0.603}
  },
  "events": [],
  "interactions": [
    {"type": "npc_interaction", "npc1": "charlie", "npc2": "felix", "interaction": "ignore"}
  ]
}
```

---

## Visualizer

Open the Top-Down Visualizer:

```bash
open /Users/ram/Documents/wandern/ao-world-engine/visualizer/index.html
```

Features:
- **Building View**: See floor plan with NPCs as colored dots
- **District View**: Multiple buildings, NPC movements
- **City View**: Abstract overview of all districts
- **Layer Toggles**: Show/hide walls, furniture, NPCs, objects
- **Tick Control**: Play/pause, step through time
- **NPC List**: Click to highlight NPC, see their activity

---

## AO Network Execution

The Python code in `simulation_behaviors.py` is designed to run on the **AO Network**, not the user's computer:

1. **Encode**: `base64.b64encode(python_code)`
2. **Store**: Upload JSON with code to Arweave
3. **Execute**: AO Process fetches and runs in sandbox
4. **Return**: Results sent back to client

See [EMBEDDED_CODE_SYSTEM.md](./EMBEDDED_CODE_SYSTEM.md) for full details.

---

*See also: [WORLD_CODEC.md](./WORLD_CODEC.md) | [EMBEDDED_CODE_SYSTEM.md](./EMBEDDED_CODE_SYSTEM.md)*

# Plugin System

The AO World Engine supports a modular plugin/addon system for extending the simulation with custom behaviors, events, NPCs, locations, vehicles, and items.

---

## Overview

Plugins are JSON manifests that register new components into the simulation. They can be:
- Loaded from local files
- Fetched from Arweave for permanent, decentralized distribution
- Shared with the community

---

## Plugin Structure

```json
{
  "id": "my_plugin",
  "name": "My Custom Plugin",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "What this plugin does",
  "dependencies": [],
  
  "behaviors": [...],
  "events": [...],
  "npc_types": [...],
  "locations": [...],
  "vehicles": [...],
  "items": [...]
}
```

---

## Components

### Behaviors

Custom NPC behaviors triggered by schedules, events, or conditions:

```json
{
  "id": "street_racer",
  "name": "Street Racer Behavior",
  "trigger": "schedule",
  "time_periods": ["T08", "T09", "T10"],
  "condition": "npc.archetype == 'racer'",
  "actions": [
    {"type": "travel", "destination": "race_meetup"},
    {"type": "participate", "event": "street_race"}
  ]
}
```

### Events

Custom world events with probabilities and effects:

```json
{
  "id": "street_race",
  "name": "Street Race",
  "probability": 0.05,
  "locations": ["highway", "industrial_road"],
  "time_periods": ["T09", "T10", "T01"],
  "duration_ticks": 20,
  "rewards": {
    "winner": {"credits": 5000}
  }
}
```

### NPC Types

New NPC archetypes with custom schedules and skills:

```json
{
  "id": "street_racer",
  "name": "Street Racer",
  "base_archetype": "criminal",
  "skills": {
    "driving": 0.8,
    "mechanics": 0.6
  },
  "schedule": {
    "T09": {"activity": "racing", "location": "race_meetup"}
  }
}
```

### Locations

Custom locations for events and activities:

```json
{
  "id": "race_meetup_highway",
  "name": "Highway 47 Meetup",
  "type": "race_meetup",
  "capacity": 50,
  "activities": ["betting", "race_planning"]
}
```

### Vehicles

Custom vehicles with stats:

```json
{
  "id": "racer_coupe",
  "name": "Phantom Racer Coupe",
  "speed": 220,
  "handling": 0.85,
  "capacity": 2,
  "type": "racing"
}
```

### Items

Custom items with effects:

```json
{
  "id": "nitro_boost",
  "name": "Nitro Boost Canister",
  "type": "vehicle_consumable",
  "effect": {"speed_boost": 1.5, "duration": 5}
}
```

---

## Built-in Example Plugins

### Street Racing Pack

Features:
- Street racer, spectator, and bouncer behaviors
- Street race and drift challenge events
- Racer and pit crew NPC types
- Race meetup and tuning garage locations
- Racer coupe and drift king vehicles
- Nitro boost and scanner jammer items

### Corporate Espionage Pack

Features:
- Corporate spy and security patrol behaviors
- Hostile takeover and data breach events
- Corporate spy NPC type

---

## Loading Plugins

### From File

```python
from scripts.plugin_system import load_plugin_from_file

load_plugin_from_file("plugins/my_plugin.json")
```

### From Arweave

```python
from scripts.plugin_system import load_plugin_from_arweave

load_plugin_from_arweave("ARWEAVE_TX_ID")
```

### From Directory

```python
from scripts.plugin_system import load_plugins_from_directory

count = load_plugins_from_directory("plugins/")
print(f"Loaded {count} plugins")
```

---

## Using Plugins

### Execute Behavior

```python
from scripts.plugin_system import execute_behavior

npc = {"id": "NPC_001", "name": "Test", "archetype": "racer"}
result = execute_behavior("street_racer", npc, world_state, tick=220)
```

### Generate Events

```python
from scripts.plugin_system import generate_plugin_events

events = generate_plugin_events(["street_racing"], world_state, tick=220)
```

---

## Testing Plugins

```bash
# Run plugin system tests
python3 scripts/plugin_system.py

# Expected output:
# ✅ Plugin system working!
```

---

## Creating Your Own Plugin

1. **Create JSON manifest** with your plugin ID and components
2. **Define behaviors** with triggers and actions
3. **Add events** with probabilities and effects
4. **Test locally** using `load_plugin_from_file()`
5. **Upload to Arweave** for permanent distribution

See `scripts/plugin_system.py` for the full schema and examples.

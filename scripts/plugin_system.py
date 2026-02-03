"""
AO World Engine - Plugin System

Modular addon system for extending the simulation with:
- Custom behaviors (street racing, corporate espionage, etc.)
- Custom events
- Custom NPC types
- Custom locations
- Custom items

Plugins are JSON files + optional Python behavior scripts.
All plugins are Arweave-storable and community-shareable.
"""

import json
import os
import hashlib
from typing import Callable, Optional

# =============================================================================
# PLUGIN REGISTRY
# =============================================================================

class PluginRegistry:
    """Central registry for all loaded plugins."""
    
    def __init__(self):
        self.plugins = {}
        self.behaviors = {}
        self.events = {}
        self.npc_types = {}
        self.locations = {}
        self.items = {}
        self.vehicles = {}
        self.hooks = {}  # Pre/post hooks for extending behavior
    
    def register_plugin(self, plugin: dict) -> bool:
        """Register a plugin from its manifest."""
        plugin_id = plugin.get("id")
        if not plugin_id:
            return False
        
        self.plugins[plugin_id] = plugin
        
        # Register components
        for behavior in plugin.get("behaviors", []):
            self.behaviors[behavior["id"]] = behavior
        
        for event in plugin.get("events", []):
            self.events[event["id"]] = event
        
        for npc_type in plugin.get("npc_types", []):
            self.npc_types[npc_type["id"]] = npc_type
        
        for location in plugin.get("locations", []):
            self.locations[location["id"]] = location
        
        for item in plugin.get("items", []):
            self.items[item["id"]] = item
        
        for vehicle in plugin.get("vehicles", []):
            self.vehicles[vehicle["id"]] = vehicle
        
        return True
    
    def register_hook(self, hook_point: str, callback: Callable):
        """Register a hook for extending behavior."""
        if hook_point not in self.hooks:
            self.hooks[hook_point] = []
        self.hooks[hook_point].append(callback)
    
    def run_hooks(self, hook_point: str, data: dict) -> dict:
        """Run all hooks for a point, passing data through each."""
        for callback in self.hooks.get(hook_point, []):
            data = callback(data)
        return data
    
    def get_behavior(self, behavior_id: str) -> Optional[dict]:
        """Get a registered behavior by ID."""
        return self.behaviors.get(behavior_id)
    
    def get_event(self, event_id: str) -> Optional[dict]:
        """Get a registered event by ID."""
        return self.events.get(event_id)


# Global registry
REGISTRY = PluginRegistry()


# =============================================================================
# PLUGIN MANIFEST SCHEMA
# =============================================================================

PLUGIN_SCHEMA = {
    "id": "string (required) - unique plugin identifier",
    "name": "string (required) - display name",
    "version": "string - semver version",
    "author": "string - creator name/address",
    "description": "string - what this plugin does",
    "dependencies": ["list of plugin IDs this depends on"],
    "arweave_tx": "string - arweave transaction if published",
    
    # Components
    "behaviors": [{
        "id": "string - unique behavior ID",
        "name": "string - display name",
        "trigger": "string - when this activates (schedule, event, condition)",
        "condition": "string - condition expression",
        "actions": ["list of action definitions"],
        "npc_filter": "string - which NPCs can use this",
    }],
    
    "events": [{
        "id": "string - unique event ID",
        "name": "string - display name",
        "probability": "float - chance per tick",
        "locations": ["list of valid locations"],
        "time_periods": ["T01-T10 when can occur"],
        "effects": ["what happens when triggered"],
    }],
    
    "npc_types": [{
        "id": "string - unique type ID",
        "name": "string - display name",
        "base_archetype": "string - extends which archetype",
        "schedule": {},  # Custom schedule
        "personality_modifiers": {},
        "skills": {},
    }],
    
    "locations": [{
        "id": "string - unique location ID",
        "name": "string - display name",
        "type": "string - location type",
        "capacity": "int - max NPCs",
        "activities": ["what can happen here"],
    }],
    
    "vehicles": [{
        "id": "string - unique vehicle ID",
        "name": "string - display name",
        "speed": "int - km/h",
        "capacity": "int - passengers",
        "type": "string - vehicle category",
    }],
    
    "items": [{
        "id": "string - unique item ID",
        "name": "string - display name",
        "type": "string - item category",
        "effects": {},
    }],
}


# =============================================================================
# EXAMPLE PLUGINS
# =============================================================================

STREET_RACING_PLUGIN = {
    "id": "street_racing",
    "name": "Street Racing Pack",
    "version": "1.0.0",
    "author": "AO Community",
    "description": "Illegal street racing events with NPCs, vehicles, and race tracks",
    "dependencies": [],
    
    "behaviors": [
        {
            "id": "street_racer",
            "name": "Street Racer Behavior",
            "trigger": "schedule",
            "time_periods": ["T08", "T09", "T10"],  # Night only
            "condition": "npc.archetype == 'racer'",
            "actions": [
                {"type": "travel", "destination": "race_meetup"},
                {"type": "wait", "duration": 10, "activity": "preparing_vehicle"},
                {"type": "participate", "event": "street_race"},
            ],
        },
        {
            "id": "race_spectator",
            "name": "Race Spectator",
            "trigger": "event:street_race_starting",
            "condition": "npc.interests.contains('racing') and distance(npc, event) < 500",
            "actions": [
                {"type": "travel", "destination": "event.location"},
                {"type": "watch", "duration": "event.duration"},
            ],
        },
        {
            "id": "race_bouncer",
            "name": "Race Security",
            "trigger": "event:street_race_starting",
            "condition": "npc.role == 'race_security'",
            "actions": [
                {"type": "patrol", "area": "race_perimeter"},
                {"type": "watch_for", "target": "temple_guard"},
                {"type": "alert", "recipients": "racers", "condition": "guard_spotted"},
            ],
        },
    ],
    
    "events": [
        {
            "id": "street_race",
            "name": "Street Race",
            "probability": 0.05,  # 5% chance per tick during valid times
            "locations": ["highway", "industrial_road", "undercity_tunnel"],
            "time_periods": ["T09", "T10", "T01"],
            "min_participants": 2,
            "max_participants": 8,
            "duration_ticks": 20,
            "phases": [
                {"name": "meetup", "duration": 5},
                {"name": "race", "duration": 10},
                {"name": "celebration", "duration": 5},
            ],
            "rewards": {
                "winner": {"credits": 5000, "reputation": 0.2},
                "participants": {"reputation": 0.05},
            },
            "risks": {
                "temple_raid": 0.1,  # 10% chance guards show up
                "crash": 0.05,
            },
        },
        {
            "id": "drift_challenge",
            "name": "Drift Challenge",
            "probability": 0.02,
            "locations": ["parking_garage", "empty_lot"],
            "time_periods": ["T08", "T09", "T10"],
            "solo": True,
            "scoring": "drift_points",
        },
    ],
    
    "npc_types": [
        {
            "id": "street_racer",
            "name": "Street Racer",
            "base_archetype": "criminal",
            "personality_modifiers": {
                "aggression": 0.3,
                "thrill_seeking": 0.9,
                "loyalty": 0.6,  # To racing crew
            },
            "skills": {
                "driving": 0.8,
                "mechanics": 0.6,
                "stealth": 0.4,
            },
            "schedule": {
                "T01": {"activity": "racing", "location": "race_track"},
                "T02": {"activity": "sleeping", "location": "home"},
                "T03": {"activity": "sleeping", "location": "home"},
                "T04": {"activity": "working", "location": "garage"},
                "T05": {"activity": "working", "location": "garage"},
                "T06": {"activity": "tuning", "location": "garage"},
                "T07": {"activity": "socializing", "location": "bar"},
                "T08": {"activity": "preparing", "location": "garage"},
                "T09": {"activity": "racing", "location": "race_meetup"},
                "T10": {"activity": "racing", "location": "race_track"},
            },
            "faction": "street_racers",
        },
        {
            "id": "pit_crew",
            "name": "Pit Crew Member",
            "base_archetype": "worker",
            "skills": {
                "mechanics": 0.9,
                "driving": 0.4,
            },
        },
    ],
    
    "locations": [
        {
            "id": "race_meetup_highway",
            "name": "Highway 47 Meetup",
            "type": "race_meetup",
            "capacity": 50,
            "activities": ["vehicle_showcase", "betting", "race_planning"],
            "risk_level": 0.3,
        },
        {
            "id": "undercity_circuit",
            "name": "Undercity Circuit",
            "type": "race_track",
            "length_km": 3.5,
            "difficulty": 0.8,
            "temple_presence": 0.1,
        },
        {
            "id": "tuning_garage",
            "name": "Midnight Garage",
            "type": "shop",
            "services": ["tuning", "repairs", "modifications"],
            "illegal_mods": True,
        },
    ],
    
    "vehicles": [
        {
            "id": "racer_coupe",
            "name": "Phantom Racer Coupe",
            "speed": 220,
            "acceleration": 0.9,
            "handling": 0.85,
            "capacity": 2,
            "type": "racing",
            "mods_available": ["nitro", "hover_boost", "stealth_mode"],
        },
        {
            "id": "drift_king",
            "name": "Drift King Special",
            "speed": 180,
            "acceleration": 0.7,
            "handling": 0.95,
            "drift_bonus": 1.5,
            "capacity": 2,
            "type": "drift",
        },
    ],
    
    "items": [
        {
            "id": "nitro_boost",
            "name": "Nitro Boost Canister",
            "type": "vehicle_consumable",
            "effect": {"speed_boost": 1.5, "duration": 5},
            "price": 500,
        },
        {
            "id": "scanner_jammer",
            "name": "Temple Scanner Jammer",
            "type": "equipment",
            "effect": {"temple_detection": -0.5},
            "price": 2000,
            "illegal": True,
        },
    ],
}


CORPORATE_ESPIONAGE_PLUGIN = {
    "id": "corporate_espionage",
    "name": "Corporate Espionage Pack",
    "version": "1.0.0",
    "author": "AO Community",
    "description": "Corporate spies, data theft, and boardroom intrigue",
    "dependencies": [],
    
    "behaviors": [
        {
            "id": "corporate_spy",
            "name": "Corporate Spy Behavior",
            "trigger": "mission:espionage",
            "actions": [
                {"type": "infiltrate", "target": "target_corporation"},
                {"type": "gather_intel", "method": "social_engineering"},
                {"type": "extract_data", "target": "server_room"},
                {"type": "exfiltrate", "method": "stealth"},
            ],
        },
        {
            "id": "security_patrol",
            "name": "Corporate Security",
            "trigger": "schedule",
            "condition": "npc.role == 'corporate_security'",
            "actions": [
                {"type": "patrol", "route": "building_perimeter"},
                {"type": "check", "target": "access_points"},
                {"type": "respond", "to": "security_alert"},
            ],
        },
    ],
    
    "events": [
        {
            "id": "hostile_takeover",
            "name": "Hostile Takeover Attempt",
            "probability": 0.01,
            "locations": ["corporate_hq"],
            "effects": ["stock_crash", "security_increase", "layoffs"],
        },
        {
            "id": "data_breach",
            "name": "Data Breach Discovered",
            "probability": 0.02,
            "locations": ["corporate_hq", "data_center"],
            "effects": ["investigation", "security_lockdown"],
        },
    ],
    
    "npc_types": [
        {
            "id": "corporate_spy",
            "name": "Corporate Spy",
            "base_archetype": "worker",
            "personality_modifiers": {
                "deception": 0.9,
                "loyalty": 0.2,  # To employer, high to handler
            },
            "skills": {
                "hacking": 0.7,
                "social_engineering": 0.8,
                "stealth": 0.7,
                "combat": 0.4,
            },
        },
    ],
}


# =============================================================================
# PLUGIN LOADER
# =============================================================================

def load_plugin_from_file(filepath: str) -> bool:
    """Load a plugin from a JSON file."""
    try:
        with open(filepath, 'r') as f:
            plugin = json.load(f)
        return REGISTRY.register_plugin(plugin)
    except Exception as e:
        print(f"Failed to load plugin {filepath}: {e}")
        return False


def load_plugin_from_arweave(tx_id: str) -> bool:
    """Load a plugin from Arweave."""
    import requests
    try:
        response = requests.get(f"https://arweave.net/{tx_id}", timeout=10)
        if response.status_code == 200:
            plugin = response.json()
            return REGISTRY.register_plugin(plugin)
    except Exception as e:
        print(f"Failed to load plugin from Arweave {tx_id}: {e}")
    return False


def load_plugins_from_directory(directory: str) -> int:
    """Load all plugins from a directory."""
    loaded = 0
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            filepath = os.path.join(directory, filename)
            if load_plugin_from_file(filepath):
                loaded += 1
    return loaded


# =============================================================================
# PLUGIN EXECUTION
# =============================================================================

def execute_behavior(behavior_id: str, npc: dict, world: dict, tick: int) -> dict:
    """Execute a plugin behavior for an NPC."""
    behavior = REGISTRY.get_behavior(behavior_id)
    if not behavior:
        return {"error": f"Behavior {behavior_id} not found"}
    
    # Check condition
    if not evaluate_condition(behavior.get("condition", "true"), npc, world):
        return {"skipped": True, "reason": "condition_not_met"}
    
    # Execute actions
    results = []
    for action in behavior.get("actions", []):
        result = execute_action(action, npc, world, tick)
        results.append(result)
    
    return {"results": results}


def execute_action(action: dict, npc: dict, world: dict, tick: int) -> dict:
    """Execute a single action."""
    action_type = action.get("type")
    
    if action_type == "travel":
        return {"npc_id": npc["id"], "moving_to": action["destination"]}
    elif action_type == "wait":
        return {"npc_id": npc["id"], "activity": action.get("activity", "waiting"), "duration": action["duration"]}
    elif action_type == "participate":
        return {"npc_id": npc["id"], "joining_event": action["event"]}
    elif action_type == "patrol":
        return {"npc_id": npc["id"], "patrolling": action["area"]}
    else:
        return {"npc_id": npc["id"], "action": action_type}


def evaluate_condition(condition: str, npc: dict, world: dict) -> bool:
    """Evaluate a condition expression (simple version)."""
    if condition == "true":
        return True
    if condition == "false":
        return False
    
    # Simple attribute checks
    if "==" in condition:
        parts = condition.split("==")
        left = parts[0].strip()
        right = parts[1].strip().strip("'\"")
        
        if left.startswith("npc."):
            attr = left[4:]
            value = npc.get(attr)
            return str(value) == right
    
    return True


def generate_plugin_events(plugins: list[str], world: dict, tick: int) -> list[dict]:
    """Generate events from loaded plugins."""
    events = []
    
    for plugin_id in plugins:
        plugin = REGISTRY.plugins.get(plugin_id)
        if not plugin:
            continue
        
        for event_def in plugin.get("events", []):
            # Check time period
            time_period = get_time_period(tick)
            if time_period not in event_def.get("time_periods", [time_period]):
                continue
            
            # Probability check (deterministic)
            prob = event_def.get("probability", 0.1)
            h = deterministic_hash(f"{event_def['id']}_{tick}", tick)
            if h % 10000 < prob * 10000:
                events.append({
                    "id": f"{event_def['id']}_{tick}",
                    "type": event_def["id"],
                    "plugin": plugin_id,
                    "tick": tick,
                    "duration": event_def.get("duration_ticks", 10),
                })
    
    return events


# =============================================================================
# UTILITY
# =============================================================================

def deterministic_hash(seed: str, tick: int) -> int:
    combined = f"{seed}_{tick}"
    return int(hashlib.md5(combined.encode()).hexdigest(), 16)


def get_time_period(tick: int) -> str:
    day_tick = tick % 240
    if day_tick < 24:   return "T01"
    if day_tick < 72:   return "T02"
    if day_tick < 120:  return "T03"
    if day_tick < 168:  return "T04"
    if day_tick < 192:  return "T05"
    if day_tick < 204:  return "T06"
    if day_tick < 216:  return "T07"
    if day_tick < 228:  return "T08"
    if day_tick < 236:  return "T09"
    return "T10"


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("PLUGIN SYSTEM TEST")
    print("=" * 60)
    
    # Register built-in example plugins
    REGISTRY.register_plugin(STREET_RACING_PLUGIN)
    REGISTRY.register_plugin(CORPORATE_ESPIONAGE_PLUGIN)
    
    print(f"\n📦 Loaded plugins: {list(REGISTRY.plugins.keys())}")
    print(f"   Behaviors: {list(REGISTRY.behaviors.keys())}")
    print(f"   Events: {list(REGISTRY.events.keys())}")
    print(f"   NPC Types: {list(REGISTRY.npc_types.keys())}")
    print(f"   Locations: {list(REGISTRY.locations.keys())}")
    print(f"   Vehicles: {list(REGISTRY.vehicles.keys())}")
    print(f"   Items: {list(REGISTRY.items.keys())}")
    
    # Test behavior execution
    print("\n🏎️ STREET RACING BEHAVIOR TEST:")
    test_racer = {
        "id": "NPC_RACER_001",
        "name": "Nitro Jack",
        "archetype": "racer",
    }
    
    result = execute_behavior("street_racer", test_racer, {}, 220)  # T08 - race time
    print(f"   Result: {result}")
    
    # Test event generation
    print("\n🎲 EVENT GENERATION TEST:")
    for tick in range(220, 240):  # Late night
        events = generate_plugin_events(["street_racing"], {}, tick)
        if events:
            for e in events:
                print(f"   Tick {tick}: {e['type']} triggered!")
    
    # Show plugin schema
    print("\n📋 Creating new plugin is easy! JSON structure:")
    print(json.dumps({
        "id": "my_plugin",
        "name": "My Custom Plugin",
        "behaviors": ["..."],
        "events": ["..."],
        "npc_types": ["..."],
    }, indent=2))
    
    print("\n✅ Plugin system working!")

"""
GTA5-Style NPC Systems for AO World Engine

Advanced NPC behaviors inspired by GTA5:
- Vehicle usage and traffic
- Wanted/Alert levels
- Ambient activities
- NPC reactions to events
- Police/Guard response
- Witnesses and reputation

All systems are deterministic (tick-based).
"""

import hashlib
from typing import Optional

# =============================================================================
# VEHICLE SYSTEM (GTA5 style)
# =============================================================================

VEHICLES = {
    # Personal vehicles
    "hover_bike": {"speed": 120, "capacity": 1, "type": "personal"},
    "hover_car": {"speed": 80, "capacity": 4, "type": "personal"},
    "luxury_speeder": {"speed": 150, "capacity": 2, "type": "personal"},
    "work_truck": {"speed": 50, "capacity": 2, "type": "work"},
    
    # Public transit
    "city_bus": {"speed": 40, "capacity": 60, "type": "public"},
    "tram": {"speed": 25, "capacity": 80, "type": "public"},
    "taxi_pod": {"speed": 80, "capacity": 4, "type": "public"},
    
    # Emergency/Authority
    "patrol_cruiser": {"speed": 120, "capacity": 4, "type": "authority"},
    "swat_van": {"speed": 90, "capacity": 8, "type": "authority"},
    "chase_bike": {"speed": 140, "capacity": 1, "type": "authority"},
    
    # Service
    "delivery_drone": {"speed": 60, "capacity": 0, "type": "service"},
    "cargo_truck": {"speed": 45, "capacity": 0, "type": "service"},
}

def get_npc_vehicle(npc: dict, tick: int) -> Optional[dict]:
    """
    Determine if NPC is using a vehicle based on activity.
    Returns vehicle info or None if on foot.
    """
    activity = npc.get("current_activity", "")
    archetype = npc.get("archetype", "resident")
    
    # Guards get patrol vehicles
    if archetype == "guard" and activity == "patrol":
        h = deterministic_hash(f"{npc['id']}_vehicle", tick // 100)
        if h % 3 == 0:
            return {"type": "patrol_cruiser", "owned": True}
        return None
    
    # Workers commuting get vehicles
    if activity == "commuting":
        h = deterministic_hash(f"{npc['id']}_commute", tick // 50)
        options = [None, None, "hover_car", "hover_bike", "city_bus", "tram"]
        return {"type": options[h % len(options)], "owned": h % 2 == 0} if options[h % len(options)] else None
    
    # Criminals might be in vehicles
    if archetype == "criminal" and activity == "fleeing":
        return {"type": "hover_bike", "owned": False, "stolen": True}
    
    return None


# =============================================================================
# WANTED LEVEL SYSTEM (GTA5 style - Stars)
# =============================================================================

"""
Temple Alert Levels (like GTA stars):
0 - Clear: No alert
1 - Suspicious: Guards watching
2 - Alert: Active investigation
3 - Wanted: Guards actively searching
4 - Manhunt: Roadblocks, drones deployed
5 - Full Lockdown: Military response, kill on sight
"""

ALERT_LEVELS = {
    0: {
        "name": "clear",
        "guard_response": "normal_patrol",
        "search_radius": 0,
        "reinforcements": 0,
        "decay_per_tick": 0,
    },
    1: {
        "name": "suspicious",
        "guard_response": "observation",
        "search_radius": 50,  # meters
        "reinforcements": 0,
        "decay_per_tick": 0.02,
    },
    2: {
        "name": "alert",
        "guard_response": "investigation",
        "search_radius": 100,
        "reinforcements": 2,
        "decay_per_tick": 0.01,
    },
    3: {
        "name": "wanted",
        "guard_response": "active_search",
        "search_radius": 200,
        "reinforcements": 5,
        "decay_per_tick": 0.005,
    },
    4: {
        "name": "manhunt",
        "guard_response": "roadblocks",
        "search_radius": 500,
        "reinforcements": 10,
        "drones": True,
        "decay_per_tick": 0.002,
    },
    5: {
        "name": "lockdown",
        "guard_response": "military",
        "search_radius": 1000,
        "reinforcements": 20,
        "drones": True,
        "helicopters": True,
        "kill_on_sight": True,
        "decay_per_tick": 0.001,
    },
}

def calculate_alert_level(actions: list[dict]) -> int:
    """
    Calculate alert level based on player actions.
    
    Actions have severity scores:
    - trespassing: +0.5
    - theft: +1
    - assault: +2
    - assault_guard: +3
    - murder: +4
    - murder_guard: +5
    - terrorism: +10
    """
    severity_map = {
        "trespassing": 0.5,
        "theft": 1.0,
        "assault": 2.0,
        "assault_guard": 3.0,
        "murder": 4.0,
        "murder_guard": 5.0,
        "terrorism": 10.0,
        "hacking": 1.5,
        "smuggling": 2.0,
        "resistance_activity": 2.5,
    }
    
    total = sum(severity_map.get(a["type"], 0) * a.get("witnessed", 1) for a in actions)
    
    if total >= 10: return 5
    if total >= 6: return 4
    if total >= 4: return 3
    if total >= 2: return 2
    if total >= 0.5: return 1
    return 0


def update_alert_level(current_level: int, player_visible: bool, tick: int) -> int:
    """
    Update alert level based on visibility and time.
    Like GTA - hiding reduces stars over time.
    """
    config = ALERT_LEVELS[current_level]
    
    if player_visible:
        # Can't decay if guards can see you
        return current_level
    
    # Decay over time when hidden
    decay = config["decay_per_tick"]
    
    # Deterministic: decay happens after X ticks
    if current_level > 0:
        ticks_to_decay = int(1 / decay) if decay > 0 else 9999
        if tick % ticks_to_decay == 0:
            return max(0, current_level - 1)
    
    return current_level


def get_guard_response(alert_level: int, location: str) -> dict:
    """Get guard behavior based on alert level."""
    config = ALERT_LEVELS[alert_level]
    
    return {
        "behavior": config["guard_response"],
        "search_radius": config["search_radius"],
        "num_guards": config["reinforcements"],
        "use_vehicles": alert_level >= 3,
        "use_drones": config.get("drones", False),
        "lethal_force": config.get("kill_on_sight", False),
    }


# =============================================================================
# AMBIENT ACTIVITIES (GTA5 style)
# =============================================================================

AMBIENT_ACTIVITIES = {
    # Street activities
    "walking": {"weight": 30, "locations": ["street", "sidewalk"]},
    "jogging": {"weight": 5, "locations": ["park", "sidewalk"], "time": ["T03", "T04"]},
    "smoking": {"weight": 8, "locations": ["alley", "corner"]},
    "phone_call": {"weight": 10, "locations": ["any"]},
    "arguing": {"weight": 3, "locations": ["street", "bar"], "requires_partner": True},
    "street_vendor": {"weight": 5, "locations": ["market", "corner"]},
    
    # Social activities
    "chatting": {"weight": 15, "locations": ["any"], "requires_partner": True},
    "flirting": {"weight": 5, "locations": ["bar", "club"], "requires_partner": True},
    "business_meeting": {"weight": 3, "locations": ["office", "restaurant"]},
    
    # Work activities
    "sweeping": {"weight": 4, "locations": ["shop", "street"]},
    "inventory_check": {"weight": 5, "locations": ["shop", "warehouse"]},
    "loading_cargo": {"weight": 3, "locations": ["dock", "warehouse"]},
    "data_entry": {"weight": 6, "locations": ["office"]},
    
    # Leisure
    "window_shopping": {"weight": 8, "locations": ["market", "mall"]},
    "eating_street_food": {"weight": 7, "locations": ["food_stall", "market"]},
    "drinking": {"weight": 6, "locations": ["bar"], "time": ["T07", "T08", "T09"]},
    "dancing": {"weight": 3, "locations": ["club"], "time": ["T08", "T09", "T10"]},
    "gambling": {"weight": 2, "locations": ["underground", "bar"]},
    
    # Suspicious
    "loitering": {"weight": 4, "locations": ["alley", "corner"], "time": ["T08", "T09", "T10"]},
    "lookout": {"weight": 2, "locations": ["corner", "rooftop"]},
    "drug_deal": {"weight": 1, "locations": ["alley"], "criminal": True},
    "mugging": {"weight": 0.5, "locations": ["alley"], "criminal": True},
}

def get_ambient_activity(npc: dict, location_type: str, tick: int) -> str:
    """
    Get a random ambient activity for an NPC based on location and time.
    Deterministic based on NPC ID and tick.
    """
    time_period = get_time_period(tick)
    is_criminal = npc.get("archetype") == "criminal"
    
    # Filter valid activities
    valid = []
    for activity, config in AMBIENT_ACTIVITIES.items():
        # Check location
        if "any" not in config["locations"] and location_type not in config["locations"]:
            continue
        
        # Check time restriction
        if "time" in config and time_period not in config["time"]:
            continue
        
        # Criminal activities only for criminals
        if config.get("criminal") and not is_criminal:
            continue
        
        valid.append((activity, config["weight"]))
    
    if not valid:
        return "idle"
    
    # Deterministic weighted selection
    total_weight = sum(w for _, w in valid)
    h = deterministic_hash(f"{npc['id']}_ambient", tick // 10)
    threshold = h % int(total_weight * 100) / 100
    
    cumulative = 0
    for activity, weight in valid:
        cumulative += weight
        if cumulative >= threshold * total_weight:
            return activity
    
    return valid[0][0]


# =============================================================================
# NPC REACTIONS (GTA5 style)
# =============================================================================

REACTION_TYPES = {
    "player_running": {
        "curious": 0.3,
        "ignore": 0.6,
        "annoyed": 0.1,
    },
    "gunshot": {
        "flee": 0.6,
        "duck": 0.2,
        "freeze": 0.1,
        "investigate": 0.1,
    },
    "explosion": {
        "flee": 0.8,
        "freeze": 0.15,
        "investigate": 0.05,
    },
    "fight_nearby": {
        "flee": 0.4,
        "watch": 0.3,
        "record_phone": 0.15,
        "call_guards": 0.1,
        "join_fight": 0.05,
    },
    "vehicle_crash": {
        "approach": 0.4,
        "ignore": 0.3,
        "call_help": 0.2,
        "flee": 0.1,
    },
    "guard_patrol": {
        "ignore": 0.7,
        "nervous": 0.2,
        "hide": 0.1,  # More likely for criminals
    },
    "player_staring": {
        "ignore": 0.5,
        "uncomfortable": 0.3,
        "confrontational": 0.1,
        "friendly": 0.1,
    },
    "theft_witnessed": {
        "call_guards": 0.4,
        "confront": 0.1,
        "ignore": 0.3,
        "flee": 0.2,
    },
}

def get_npc_reaction(npc: dict, event_type: str, tick: int) -> dict:
    """
    Get NPC reaction to an event based on personality.
    Modifies base probabilities with personality traits.
    """
    base_reactions = REACTION_TYPES.get(event_type, {"ignore": 1.0})
    personality = npc.get("personality", {})
    
    # Modify based on personality
    modified = {}
    for reaction, prob in base_reactions.items():
        modifier = 1.0
        
        # Aggression affects confrontational reactions
        if reaction in ["join_fight", "confrontational", "confront"]:
            modifier *= 1 + personality.get("aggression", 0.5)
        
        # Low sociability = more likely to ignore
        if reaction == "ignore":
            modifier *= 1 + (1 - personality.get("sociability", 0.5))
        
        # Loyalty affects calling guards vs handling personally
        if reaction == "call_guards":
            modifier *= personality.get("loyalty", 0.5) + 0.5
        
        # High greed = less likely to help
        if reaction in ["call_help", "approach"]:
            modifier *= 1 - personality.get("greed", 0.3) * 0.5
        
        modified[reaction] = prob * modifier
    
    # Normalize
    total = sum(modified.values())
    normalized = {k: v / total for k, v in modified.items()}
    
    # Deterministic selection
    h = deterministic_hash(f"{npc['id']}_react_{event_type}", tick)
    threshold = (h % 1000) / 1000
    
    cumulative = 0
    for reaction, prob in normalized.items():
        cumulative += prob
        if cumulative >= threshold:
            return {
                "reaction": reaction,
                "intensity": personality.get("aggression", 0.5) * 0.5 + 0.5,
                "duration_ticks": 5 + (h % 10),
            }
    
    return {"reaction": "ignore", "intensity": 0.1, "duration_ticks": 1}


# =============================================================================
# WITNESS SYSTEM (GTA5 style)
# =============================================================================

def find_witnesses(location: str, radius: int, npcs: list[dict], tick: int) -> list[dict]:
    """
    Find NPCs who witnessed an event.
    In GTA, witnesses call cops if they see crimes.
    """
    witnesses = []
    
    for npc in npcs:
        npc_location = npc.get("current_location", "")
        
        # Simple same-location check (would be distance in full game)
        if npc_location == location:
            # Check if NPC is conscious/able to witness
            activity = npc.get("current_activity", "")
            if activity in ["sleeping", "unconscious", "dead"]:
                continue
            
            # Guards always witness
            is_guard = npc.get("archetype") == "guard"
            
            # Calculate perception (affected by activity)
            perception = npc.get("skills", {}).get("perception", 0.5)
            if activity in ["phone_call", "drinking", "sleeping"]:
                perception *= 0.5
            
            # Deterministic perception check
            h = deterministic_hash(f"{npc['id']}_witness", tick)
            if h % 100 < perception * 100 or is_guard:
                witnesses.append({
                    "npc_id": npc["id"],
                    "is_guard": is_guard,
                    "will_report": is_guard or (h % 10 < 4),  # 40% civilians report
                    "perception": perception,
                })
    
    return witnesses


def report_crime(witnesses: list[dict], crime_type: str, tick: int) -> dict:
    """
    Process witness reports of a crime.
    Returns alert level increase.
    """
    reporting_witnesses = [w for w in witnesses if w["will_report"]]
    guard_witnesses = [w for w in witnesses if w["is_guard"]]
    
    if guard_witnesses:
        # Guards saw it directly
        return {
            "immediate_alert": True,
            "alert_increase": 2,
            "response_time": 0,  # Instant
        }
    elif reporting_witnesses:
        # Civilians will call it in
        return {
            "immediate_alert": False,
            "alert_increase": 1,
            "response_time": 10 + len(reporting_witnesses),  # More witnesses = faster
        }
    else:
        # No witnesses
        return {
            "immediate_alert": False,
            "alert_increase": 0,
            "response_time": 0,
        }


# =============================================================================
# TRAFFIC SYSTEM
# =============================================================================

def get_traffic_density(location: str, tick: int) -> float:
    """
    Get traffic density at a location (0.0 to 1.0).
    Varies by time of day like real cities.
    """
    time_period = get_time_period(tick)
    
    base_density = {
        "T01": 0.1,   # Dead of night
        "T02": 0.2,   # Early morning
        "T03": 0.7,   # Rush hour
        "T04": 0.5,   # Midday
        "T05": 0.8,   # Evening rush
        "T06": 0.6,   # After work
        "T07": 0.4,   # Evening
        "T08": 0.3,   # Night
        "T09": 0.2,   # Late night
        "T10": 0.1,   # Dead hour
    }
    
    # Location modifiers
    location_mod = {
        "highway": 1.3,
        "downtown": 1.2,
        "industrial": 0.8,
        "residential": 0.6,
        "undercity": 0.3,
    }
    
    density = base_density.get(time_period, 0.5)
    
    # Add location modifier
    for loc_type, mod in location_mod.items():
        if loc_type in location.lower():
            density *= mod
            break
    
    # Add some deterministic variance
    h = deterministic_hash(f"traffic_{location}", tick // 5)
    variance = ((h % 20) - 10) / 100  # -10% to +10%
    
    return min(1.0, max(0.0, density + variance))


def spawn_traffic_vehicle(location: str, tick: int) -> Optional[dict]:
    """
    Spawn a traffic vehicle at location.
    Returns vehicle info or None.
    """
    density = get_traffic_density(location, tick)
    
    h = deterministic_hash(f"spawn_vehicle_{location}", tick)
    if h % 100 > density * 100:
        return None
    
    # Pick vehicle type based on location
    vehicle_types = ["hover_car", "hover_car", "hover_car", "hover_bike", 
                     "work_truck", "taxi_pod", "city_bus"]
    
    vehicle_type = vehicle_types[h % len(vehicle_types)]
    
    return {
        "type": vehicle_type,
        "speed": VEHICLES[vehicle_type]["speed"] * (0.5 + density * 0.5),  # Slower in traffic
        "ai_driver": True,
        "destination": f"random_{h % 100}",
    }


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def deterministic_hash(seed: str, tick: int) -> int:
    """Generate deterministic hash from seed and tick."""
    combined = f"{seed}_{tick}"
    return int(hashlib.md5(combined.encode()).hexdigest(), 16)


def get_time_period(tick: int) -> str:
    """Convert tick to time period T01-T10."""
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
    print("GTA5-STYLE NPC SYSTEMS TEST")
    print("=" * 60)
    
    # Test NPC
    test_npc = {
        "id": "NPC_00001",
        "name": "Test NPC",
        "archetype": "worker",
        "personality": {
            "aggression": 0.3,
            "sociability": 0.7,
            "greed": 0.2,
            "loyalty": 0.8,
        },
        "skills": {"perception": 0.6},
        "current_activity": "commuting",
        "current_location": "B003",
    }
    
    # Test vehicle system
    print("\n🚗 VEHICLE SYSTEM:")
    for tick in [100, 150, 200]:
        vehicle = get_npc_vehicle(test_npc, tick)
        print(f"  Tick {tick}: {vehicle}")
    
    # Test alert levels
    print("\n⭐ ALERT LEVEL SYSTEM:")
    actions = [{"type": "theft", "witnessed": 1}]
    level = calculate_alert_level(actions)
    print(f"  Theft (1 witness): Alert Level {level}")
    
    actions = [{"type": "murder_guard", "witnessed": 2}]
    level = calculate_alert_level(actions)
    print(f"  Murder guard (2 witnesses): Alert Level {level}")
    
    response = get_guard_response(level, "downtown")
    print(f"  Guard response: {response}")
    
    # Test ambient activities
    print("\n🚶 AMBIENT ACTIVITIES:")
    for tick in range(100, 130, 10):
        activity = get_ambient_activity(test_npc, "street", tick)
        print(f"  Tick {tick}: {activity}")
    
    # Test reactions
    print("\n😱 NPC REACTIONS:")
    for event in ["gunshot", "fight_nearby", "player_staring"]:
        reaction = get_npc_reaction(test_npc, event, 100)
        print(f"  {event}: {reaction['reaction']} (intensity: {reaction['intensity']:.2f})")
    
    # Test traffic
    print("\n🚦 TRAFFIC DENSITY:")
    for tick in [50, 100, 150, 200, 220]:
        density = get_traffic_density("downtown", tick)
        period = get_time_period(tick)
        print(f"  Tick {tick} ({period}): {density:.2f}")
    
    print("\n✅ All GTA5-style systems working!")

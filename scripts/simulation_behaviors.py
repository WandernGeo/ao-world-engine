"""
AO World Engine - Simulation Behaviors
Python code that runs on AO Network (not user's computer)

These are the actual behavior implementations that get:
1. Encoded to base64
2. Stored on Arweave
3. Executed on AO Network
4. Results sent back to clients

DETERMINISM: All functions MUST be deterministic.
- Use seeded random only
- No real time, only tick
- No external API calls
"""

import hashlib
import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any

# =============================================================================
# DETERMINISTIC UTILITIES
# =============================================================================

def deterministic_hash(seed: str) -> int:
    """Generate deterministic integer from seed."""
    return int(hashlib.sha256(seed.encode()).hexdigest(), 16)

def deterministic_choice(items: list, seed: str) -> Any:
    """Deterministically pick from list."""
    if not items:
        return None
    h = deterministic_hash(seed)
    return items[h % len(items)]

def deterministic_chance(probability: float, seed: str) -> bool:
    """Deterministic probability check."""
    h = deterministic_hash(seed) % 10000
    return h < (probability * 10000)

def get_time_period(tick: int) -> str:
    """Convert tick to time period T01-T10."""
    day_tick = tick % 240
    periods = [
        (0, 24, "T01"),    # Deep night
        (24, 72, "T02"),   # Early morning
        (72, 120, "T03"),  # Morning
        (120, 168, "T04"), # Noon
        (168, 192, "T05"), # Afternoon
        (192, 204, "T06"), # Dusk
        (204, 216, "T07"), # Evening
        (216, 228, "T08"), # Night
        (228, 236, "T09"), # Late night
        (236, 240, "T10"), # Dead hour
    ]
    for start, end, period in periods:
        if start <= day_tick < end:
            return period
    return "T01"


# =============================================================================
# NPC NEEDS SYSTEM (Sims-style)
# =============================================================================

NEEDS = {
    "hunger": {"decay_rate": 0.02, "critical": 0.2},
    "sleep": {"decay_rate": 0.015, "critical": 0.15},
    "social": {"decay_rate": 0.01, "critical": 0.25},
    "hygiene": {"decay_rate": 0.008, "critical": 0.3},
    "safety": {"decay_rate": 0.005, "critical": 0.1},
    "income": {"decay_rate": 0.01, "critical": 0.2},
    "comfort": {"decay_rate": 0.012, "critical": 0.3},
    "purpose": {"decay_rate": 0.005, "critical": 0.2},
}

def update_needs(npc: dict, tick: int) -> dict:
    """
    Update NPC needs based on time passage.
    Called every tick for each NPC.
    """
    needs = npc.get("needs", {n: 1.0 for n in NEEDS})
    changes = {}
    
    for need_name, config in NEEDS.items():
        current = needs.get(need_name, 1.0)
        
        # Decay over time
        new_value = max(0.0, current - config["decay_rate"])
        
        # Check if critical
        if new_value < config["critical"]:
            changes[f"{need_name}_critical"] = True
        
        needs[need_name] = new_value
    
    return {"npc_changes": {"needs": needs}, "alerts": changes}


def get_most_urgent_need(npc: dict) -> Optional[str]:
    """Find which need requires immediate attention."""
    needs = npc.get("needs", {})
    urgent = None
    lowest = 1.0
    
    for need_name, value in needs.items():
        config = NEEDS.get(need_name, {})
        critical = config.get("critical", 0.2)
        
        # Weight by how close to critical
        weighted = value / critical if critical > 0 else value
        
        if weighted < lowest:
            lowest = weighted
            urgent = need_name
    
    return urgent if lowest < 1.5 else None


def satisfy_need(npc: dict, need: str, amount: float) -> dict:
    """Satisfy a need by the given amount."""
    needs = npc.get("needs", {})
    current = needs.get(need, 0.5)
    needs[need] = min(1.0, current + amount)
    return {"npc_changes": {"needs": needs}}


# =============================================================================
# SCHEDULE SYSTEM (Skyrim-style)
# =============================================================================

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
        "T01": ("sleeping", "home"),
        "T02": ("sleeping", "home"),
        "T03": ("opening_shop", "shop"),
        "T04": ("working", "shop"),
        "T05": ("working", "shop"),
        "T06": ("working", "shop"),
        "T07": ("closing_shop", "shop"),
        "T08": ("dinner", "restaurant"),
        "T09": ("relaxing", "home"),
        "T10": ("sleeping", "home"),
    },
    "resistance_fighter": {
        "T01": ("patrol", "hideout"),
        "T02": ("training", "hideout"),
        "T03": ("intel", "market"),
        "T04": ("meeting", "hideout"),
        "T05": ("mission", "varies"),
        "T06": ("mission", "varies"),
        "T07": ("returning", "hideout"),
        "T08": ("debrief", "hideout"),
        "T09": ("personal", "bar"),
        "T10": ("watch", "hideout"),
    },
    "temple_guard": {
        "T01": ("patrol", "district"),
        "T02": ("patrol", "district"),
        "T03": ("shift_change", "barracks"),
        "T04": ("patrol", "district"),
        "T05": ("patrol", "district"),
        "T06": ("shift_change", "barracks"),
        "T07": ("patrol", "district"),
        "T08": ("patrol", "district"),
        "T09": ("off_duty", "home"),
        "T10": ("sleeping", "home"),
    },
}

def get_scheduled_state(npc: dict, tick: int) -> Tuple[str, str]:
    """Get NPC's scheduled activity and location."""
    schedule_type = npc.get("schedule_type", "worker")
    time_period = get_time_period(tick)
    
    schedule = SCHEDULES.get(schedule_type, SCHEDULES["worker"])
    activity, location = schedule.get(time_period, ("idle", "home"))
    
    # Resolve "varies" locations
    if location == "varies":
        locations = ["market", "alley", "rooftop", "undercity"]
        location = deterministic_choice(locations, f"{npc['id']}_{tick // 10}")
    elif location == "home":
        location = npc.get("home_location", "L001")
    elif location == "workplace":
        location = npc.get("workplace", "L002")
    
    return activity, location


# =============================================================================
# CITY SIMULATION (SimCity/Cities:Skylines style)
# =============================================================================

@dataclass
class District:
    """A city district with its own simulation state."""
    id: str
    type: str  # residential, commercial, industrial, temple, undercity
    population: int
    prosperity: float  # 0-1
    crime_rate: float  # 0-1
    infrastructure: float  # 0-1
    temple_control: float  # 0-1


def simulate_district(district: dict, tick: int, city_state: dict) -> dict:
    """
    Simulate one tick of district evolution.
    Called for each district every tick.
    """
    changes = {}
    d_id = district["id"]
    d_type = district["type"]
    
    # Base rates
    crime_decay = 0.001
    prosperity_decay = 0.0005
    
    # Calculate crime change
    crime = district.get("crime_rate", 0.1)
    temple_control = district.get("temple_control", 0.5)
    
    # More temple control = less crime (but more oppression)
    crime_change = -temple_control * 0.01 + deterministic_chance(0.1, f"{d_id}_{tick}_crime") * 0.02
    crime = max(0, min(1, crime + crime_change))
    
    # Prosperity based on type and conditions
    prosperity = district.get("prosperity", 0.5)
    if d_type == "commercial":
        # Commercial thrives with low crime
        prosperity_change = (1 - crime) * 0.005 - prosperity_decay
    elif d_type == "industrial":
        # Industrial steady but pollutes
        prosperity_change = 0.002 - prosperity_decay
    elif d_type == "undercity":
        # Undercity struggles
        prosperity_change = -0.002
    else:
        prosperity_change = -prosperity_decay
    
    prosperity = max(0, min(1, prosperity + prosperity_change))
    
    # Check for events
    events = []
    
    # Random raid?
    if temple_control > 0.7 and deterministic_chance(0.02, f"{d_id}_{tick}_raid"):
        events.append({
            "type": "temple_raid",
            "district": d_id,
            "tick": tick
        })
    
    # Blackout?
    if district.get("infrastructure", 0.5) < 0.3 and deterministic_chance(0.05, f"{d_id}_{tick}_blackout"):
        events.append({
            "type": "blackout",
            "district": d_id,
            "duration": deterministic_hash(f"{d_id}_{tick}_dur") % 20 + 5
        })
    
    return {
        "district_changes": {
            d_id: {
                "crime_rate": crime,
                "prosperity": prosperity
            }
        },
        "events": events
    }


def simulate_business(business: dict, tick: int, district: dict) -> dict:
    """
    Simulate one tick of business operation.
    Businesses can thrive, struggle, or close.
    """
    b_id = business["id"]
    health = business.get("health", 1.0)
    
    # Factors affecting business
    district_prosperity = district.get("prosperity", 0.5)
    crime = district.get("crime_rate", 0.1)
    
    # Calculate health change
    base_income = business.get("base_income", 100)
    actual_income = base_income * district_prosperity * (1 - crime * 0.5)
    expenses = business.get("expenses", 80)
    
    profit_ratio = actual_income / max(expenses, 1)
    
    if profit_ratio > 1.1:
        health_change = 0.01  # Thriving
    elif profit_ratio < 0.8:
        health_change = -0.02  # Struggling
    else:
        health_change = 0  # Stable
    
    health = max(0, min(1, health + health_change))
    
    # Events
    events = []
    
    if health <= 0:
        events.append({
            "type": "business_closed",
            "business_id": b_id,
            "tick": tick
        })
    elif health > 0.9 and deterministic_chance(0.01, f"{b_id}_{tick}_expand"):
        events.append({
            "type": "business_expanding",
            "business_id": b_id
        })
    
    return {
        "business_changes": {
            b_id: {
                "health": health,
                "last_income": actual_income
            }
        },
        "events": events
    }


# =============================================================================
# RANDOM EVENTS SYSTEM
# =============================================================================

RANDOM_EVENTS = {
    "street_fight": {
        "probability": 0.02,
        "locations": ["alley", "bar", "undercity"],
        "time_periods": ["T08", "T09", "T10"],
    },
    "merchant_sale": {
        "probability": 0.05,
        "locations": ["market", "shop"],
        "time_periods": ["T04", "T05", "T06"],
    },
    "temple_patrol": {
        "probability": 0.1,
        "locations": ["street", "market", "residential"],
        "time_periods": ["T04", "T05", "T07", "T08"],
    },
    "power_surge": {
        "probability": 0.01,
        "locations": ["industrial", "undercity"],
        "time_periods": ["T01", "T02", "T03"],
    },
    "black_market_deal": {
        "probability": 0.03,
        "locations": ["undercity", "alley"],
        "time_periods": ["T09", "T10", "T01"],
    },
    "street_performance": {
        "probability": 0.04,
        "locations": ["market", "plaza"],
        "time_periods": ["T04", "T05", "T06", "T07"],
    },
    "resistance_pamphlets": {
        "probability": 0.02,
        "locations": ["market", "residential"],
        "time_periods": ["T03", "T04"],
    },
}

def generate_random_events(tick: int, locations: List[dict]) -> List[dict]:
    """
    Generate random events for this tick.
    Deterministic based on tick and location.
    """
    events = []
    time_period = get_time_period(tick)
    
    for location in locations:
        loc_id = location["id"]
        loc_type = location.get("type", "street")
        
        for event_name, config in RANDOM_EVENTS.items():
            # Check if this event can happen here/now
            if loc_type not in config["locations"]:
                continue
            if time_period not in config["time_periods"]:
                continue
            
            # Deterministic probability check
            seed = f"{event_name}_{loc_id}_{tick}"
            if deterministic_chance(config["probability"], seed):
                events.append({
                    "type": event_name,
                    "location": loc_id,
                    "tick": tick,
                    "id": f"EVT_{deterministic_hash(seed) % 1000000:06d}"
                })
    
    return events


# =============================================================================
# NPC INTERACTIONS
# =============================================================================

def can_interact(npc1: dict, npc2: dict, tick: int) -> bool:
    """Check if two NPCs can interact this tick."""
    # Same location?
    if npc1.get("location") != npc2.get("location"):
        return False
    
    # Both available?
    busy_activities = ["sleeping", "mission", "combat", "fleeing"]
    if npc1.get("activity") in busy_activities:
        return False
    if npc2.get("activity") in busy_activities:
        return False
    
    return True


def calculate_interaction(npc1: dict, npc2: dict, tick: int) -> Optional[dict]:
    """
    Calculate what happens when two NPCs interact.
    Returns interaction event or None.
    """
    if not can_interact(npc1, npc2, tick):
        return None
    
    # Get relationship
    relationships = npc1.get("relationships", {})
    rel = relationships.get(npc2["id"], {"trust": 0.5, "type": "stranger"})
    trust = rel.get("trust", 0.5)
    
    # Determine interaction type
    seed = f"{npc1['id']}_{npc2['id']}_{tick}"
    roll = deterministic_hash(seed) % 100
    
    if trust > 0.8:
        # Close relationship
        if roll < 30:
            interaction = "deep_conversation"
        elif roll < 60:
            interaction = "favor_exchange"
        else:
            interaction = "greeting"
    elif trust > 0.5:
        # Friendly
        if roll < 40:
            interaction = "small_talk"
        elif roll < 60:
            interaction = "trade"
        else:
            interaction = "nod"
    elif trust > 0.2:
        # Neutral
        if roll < 50:
            interaction = "ignore"
        else:
            interaction = "wary_glance"
    else:
        # Hostile
        if roll < 20:
            interaction = "argument"
        elif roll < 5:
            interaction = "fight"
        else:
            interaction = "avoid"
    
    # Trust changes from interaction
    trust_changes = {
        "deep_conversation": 0.05,
        "favor_exchange": 0.1,
        "greeting": 0.01,
        "small_talk": 0.02,
        "trade": 0.03,
        "nod": 0.005,
        "ignore": 0,
        "wary_glance": -0.01,
        "argument": -0.1,
        "fight": -0.3,
        "avoid": -0.02,
    }
    
    return {
        "type": "npc_interaction",
        "npc1": npc1["id"],
        "npc2": npc2["id"],
        "interaction": interaction,
        "tick": tick,
        "trust_change": trust_changes.get(interaction, 0)
    }


# =============================================================================
# PLAYER INTERACTION HANDLERS
# =============================================================================

def handle_player_action(action: str, player: dict, target: dict, 
                         world: dict, tick: int) -> dict:
    """
    Handle player action and propagate consequences.
    This is the main entry point for player-caused events.
    """
    result = {
        "success": False,
        "events": [],
        "npc_changes": {},
        "world_changes": {},
        "reputation_changes": {}
    }
    
    if action == "attack":
        result = handle_attack(player, target, world, tick)
    elif action == "steal":
        result = handle_steal(player, target, world, tick)
    elif action == "talk":
        result = handle_talk(player, target, world, tick)
    elif action == "help":
        result = handle_help(player, target, world, tick)
    elif action == "bribe":
        result = handle_bribe(player, target, world, tick)
    
    return result


def handle_attack(player: dict, target: dict, world: dict, tick: int) -> dict:
    """Handle player attacking an NPC."""
    events = []
    npc_changes = {}
    
    target_id = target["id"]
    location = target.get("location")
    
    # Target responds based on personality
    aggression = target.get("personality", {}).get("aggression", 0.5)
    
    if aggression > 0.6:
        # Fight back
        events.append({
            "type": "combat_started",
            "attacker": player["id"],
            "defender": target_id,
            "location": location,
            "tick": tick
        })
        npc_changes[target_id] = {
            "activity": "combat",
            "target": player["id"]
        }
    else:
        # Flee
        events.append({
            "type": "npc_fleeing",
            "npc": target_id,
            "from": location,
            "tick": tick
        })
        npc_changes[target_id] = {
            "activity": "fleeing",
            "destination": "safe_location"
        }
    
    # Witnesses react
    for npc_id in world.get("npcs_at_location", {}).get(location, []):
        if npc_id != target_id:
            events.append({
                "type": "witnessed_attack",
                "witness": npc_id,
                "attacker": player["id"],
                "victim": target_id,
                "tick": tick
            })
    
    return {
        "success": True,
        "events": events,
        "npc_changes": npc_changes,
        "reputation_changes": {
            "temple": -0.2,
            "civilians": -0.1,
            target.get("faction", "none"): -0.3
        }
    }


def handle_steal(player: dict, target: dict, world: dict, tick: int) -> dict:
    """Handle player stealing from NPC/location."""
    events = []
    
    # Detection check
    player_stealth = player.get("skills", {}).get("stealth", 0.5)
    target_perception = target.get("skills", {}).get("perception", 0.5)
    
    detection_chance = target_perception - player_stealth + 0.3
    seed = f"steal_{player['id']}_{target['id']}_{tick}"
    
    if deterministic_chance(detection_chance, seed):
        # Caught!
        events.append({
            "type": "theft_detected",
            "thief": player["id"],
            "victim": target["id"],
            "tick": tick
        })
        
        # Target reacts
        aggression = target.get("personality", {}).get("aggression", 0.5)
        if aggression > 0.5:
            events.append({
                "type": "npc_attacking",
                "npc": target["id"],
                "target": player["id"]
            })
        else:
            events.append({
                "type": "npc_alerting_guards",
                "npc": target["id"],
                "crime": "theft"
            })
        
        return {
            "success": False,
            "events": events,
            "reputation_changes": {"all": -0.2}
        }
    else:
        # Success
        events.append({
            "type": "theft_successful",
            "thief": player["id"],
            "victim": target["id"],
            "tick": tick
        })
        
        # Delayed discovery
        discovery_tick = tick + deterministic_hash(seed) % 50 + 10
        events.append({
            "type": "theft_discovered_later",
            "victim": target["id"],
            "discovery_tick": discovery_tick
        })
        
        return {
            "success": True,
            "events": events,
            "loot": target.get("inventory", {})
        }


def handle_help(player: dict, target: dict, world: dict, tick: int) -> dict:
    """Handle player helping an NPC."""
    events = []
    
    target_id = target["id"]
    
    # Increase trust
    trust_gain = 0.2
    
    events.append({
        "type": "player_helped_npc",
        "helper": player["id"],
        "helped": target_id,
        "tick": tick
    })
    
    # Family also grateful
    family = target.get("family", [])
    for family_member in family:
        events.append({
            "type": "gratitude_propagated",
            "from": target_id,
            "to": family_member,
            "trust_gain": trust_gain * 0.3
        })
    
    return {
        "success": True,
        "events": events,
        "relationship_changes": {
            target_id: {"trust": trust_gain}
        },
        "reputation_changes": {
            target.get("faction", "none"): 0.1
        }
    }


# =============================================================================
# MAIN TICK SIMULATION
# =============================================================================

def simulate_tick(world_state: dict, tick: int) -> dict:
    """
    Main simulation function - run once per tick.
    This orchestrates all sub-simulations.
    """
    result = {
        "tick": tick,
        "npc_changes": {},
        "district_changes": {},
        "business_changes": {},
        "events": [],
        "interactions": []
    }
    
    # 1. Update all NPC needs
    for npc in world_state.get("npcs", []):
        needs_result = update_needs(npc, tick)
        result["npc_changes"][npc["id"]] = needs_result.get("npc_changes", {})
    
    # 2. Determine NPC locations based on schedule
    for npc in world_state.get("npcs", []):
        activity, location = get_scheduled_state(npc, tick)
        
        # Check for need-based overrides
        urgent_need = get_most_urgent_need(npc)
        if urgent_need:
            # Override schedule for urgent need
            if urgent_need == "hunger":
                activity, location = "eating", "restaurant"
            elif urgent_need == "sleep":
                activity, location = "sleeping", npc.get("home_location", "home")
    
        result["npc_changes"][npc["id"]].update({
            "activity": activity,
            "location": location
        })
    
    # 3. Simulate districts
    for district in world_state.get("districts", []):
        dist_result = simulate_district(district, tick, world_state)
        result["district_changes"].update(dist_result.get("district_changes", {}))
        result["events"].extend(dist_result.get("events", []))
    
    # 4. Simulate businesses
    for business in world_state.get("businesses", []):
        district = world_state.get("districts_by_id", {}).get(business.get("district"))
        if district:
            biz_result = simulate_business(business, tick, district)
            result["business_changes"].update(biz_result.get("business_changes", {}))
            result["events"].extend(biz_result.get("events", []))
    
    # 5. Generate random events
    random_events = generate_random_events(tick, world_state.get("locations", []))
    result["events"].extend(random_events)
    
    # 6. Calculate NPC interactions
    npcs = world_state.get("npcs", [])
    for i, npc1 in enumerate(npcs):
        for npc2 in npcs[i+1:]:
            interaction = calculate_interaction(npc1, npc2, tick)
            if interaction:
                result["interactions"].append(interaction)
    
    return result


# =============================================================================
# ENTRY POINTS (Called by AO Process)
# =============================================================================

def execute_behavior(behavior_type: str, context: dict) -> dict:
    """
    Main entry point for AO Process.
    Dispatches to appropriate handler.
    """
    tick = context.get("tick", 0)
    
    if behavior_type == "simulate_tick":
        return simulate_tick(context.get("world_state", {}), tick)
    
    elif behavior_type == "player_action":
        return handle_player_action(
            context.get("action"),
            context.get("player"),
            context.get("target"),
            context.get("world_state"),
            tick
        )
    
    elif behavior_type == "update_needs":
        return update_needs(context.get("npc"), tick)
    
    elif behavior_type == "get_schedule":
        return get_scheduled_state(context.get("npc"), tick)
    
    elif behavior_type == "random_events":
        return generate_random_events(tick, context.get("locations", []))
    
    return {"error": f"Unknown behavior type: {behavior_type}"}


if __name__ == "__main__":
    # Test the simulation
    test_world = {
        "npcs": [
            {"id": "charlie", "schedule_type": "resistance_fighter", "needs": {}},
            {"id": "felix", "schedule_type": "shopkeeper", "needs": {}},
        ],
        "districts": [
            {"id": "downtown", "type": "commercial", "crime_rate": 0.2, "prosperity": 0.6},
        ],
        "locations": [
            {"id": "market", "type": "market"},
            {"id": "alley", "type": "alley"},
        ]
    }
    
    result = simulate_tick(test_world, 100)
    print(json.dumps(result, indent=2))

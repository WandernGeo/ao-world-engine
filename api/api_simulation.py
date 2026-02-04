"""
AO World Engine - NPC Simulation API

RESTful API for accessing NPC data, behaviors, and simulation.
Works with both local data and Arweave-stored data.

Endpoints:
  /api/npcs              - List NPCs with filtering
  /api/npcs/<id>         - Get single NPC details
  /api/npcs/<id>/state   - Get NPC state at tick
  /api/npcs/location/<loc> - Get NPCs at location
  /api/simulation/tick   - Run simulation tick
  /api/buildings         - List buildings
  /api/transport         - Get transport schedule

Usage:
  python3 api_simulation.py
  # Server runs on http://localhost:8080
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import hashlib
import os
import requests

app = Flask(__name__)
CORS(app)

# =============================================================================
# DATA LOADING
# =============================================================================

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CODEC_DIR = os.path.join(DATA_DIR, "codec_chunks")

# Cache for loaded data
_cache = {}

def load_json(filename):
    """Load JSON from data directory with caching."""
    if filename in _cache:
        return _cache[filename]
    
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        filepath = os.path.join(CODEC_DIR, filename)
    
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            data = json.load(f)
            _cache[filename] = data
            return data
    return None

def get_npcs():
    """Get all NPCs from generated data."""
    data = load_json("npcs_generated.json")
    return data.get("npcs", []) if data else []

def get_buildings():
    """Get all buildings."""
    data = load_json("npcs_generated.json")
    return data.get("buildings", []) if data else []

def get_transport():
    """Get transportation system."""
    data = load_json("world_codec_03_tech.json")
    return data.get("transportation_system", {}) if data else {}

# =============================================================================
# TIME UTILITIES
# =============================================================================

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

def get_time_info(tick: int) -> dict:
    """Get full time information for a tick."""
    return {
        "tick": tick,
        "day": tick // 240 + 1,
        "hour": (tick % 240) // 10,
        "minute": ((tick % 240) % 10) * 6,
        "period": get_time_period(tick),
        "day_tick": tick % 240
    }

# =============================================================================
# SEEDED RANDOM (Dynamic + Deterministic)
# =============================================================================
# KEY INSIGHT: Use hash-based randomness. Given same inputs, same output.
# But different inputs = different outcomes that LOOK random.

def seeded_random(seed: str) -> float:
    """
    Generate a random-looking float (0.0 to 1.0) from a seed string.
    DETERMINISTIC: Same seed always returns same value.
    DYNAMIC: Different seeds return different values.
    """
    h = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    return (h % 10000) / 10000.0

def seeded_choice(options: list, seed: str):
    """
    Pick from a list deterministically based on seed.
    Example: seeded_choice(['bowling', 'cards', 'gym'], 'NPC001_100_leisure')
    """
    if not options:
        return None
    h = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    return options[h % len(options)]

def weighted_seeded_choice(options: list, weights: list, seed: str):
    """
    Pick from options with weights. Higher weight = more likely.
    Example: weighted_seeded_choice(['bar', 'gym'], [3, 1], 'NPC001_100')
    NPC with high bar weight visits bar 75% of time, gym 25%.
    """
    if not options or not weights:
        return None
    
    # Normalize weights
    total = sum(weights)
    cumulative = []
    running = 0
    for w in weights:
        running += w / total
        cumulative.append(running)
    
    # Get deterministic random value
    r = seeded_random(seed)
    
    # Pick based on cumulative weights
    for i, threshold in enumerate(cumulative):
        if r <= threshold:
            return options[i]
    return options[-1]

def should_do_today(activity: str, frequency: str, npc_id: str, day: int) -> bool:
    """
    Check if NPC should do an activity today based on frequency.
    Frequencies: 'daily', '3_per_week', 'weekly', 'monthly'
    """
    seed = f"{npc_id}_{activity}_{day}"
    r = seeded_random(seed)
    
    if frequency == "daily":
        return True
    elif frequency == "3_per_week":
        return r < 0.43  # ~3/7 days
    elif frequency == "weekly":
        return r < 0.14  # ~1/7 days
    elif frequency == "monthly":
        return r < 0.033  # ~1/30 days
    return r < 0.5

# =============================================================================
# HOBBY GENERATION (Based on Personality)
# =============================================================================
# NPCs don't have hobbies in the JSON, but we can DERIVE hobbies from personality
# This is DETERMINISTIC - same NPC always gets same hobbies

HOBBY_TRAITS = {
    # hobby: (trait, threshold, weight) - hobby if trait > threshold
    "boxing": ("aggression", 0.6, 2),
    "gambling": ("greed", 0.5, 2),
    "reading": ("curiosity", 0.6, 2),
    "researching": ("curiosity", 0.7, 1),
    "socializing": ("sociability", 0.5, 3),
    "dancing": ("sociability", 0.6, 2),
    "drinking": ("sociability", 0.4, 2),
    "playing_cards": ("sociability", 0.5, 1),
    "meditating": ("loyalty", 0.7, 1),
    "exercising": ("aggression", 0.4, 2),
    "fishing": ("curiosity", 0.3, 1),
    "swimming": ("sociability", 0.3, 1),
    "yoga": ("loyalty", 0.5, 1),
    "bowling": ("sociability", 0.45, 1),
}

def generate_hobbies(npc: dict) -> list:
    """
    Generate hobbies for an NPC based on their personality traits.
    DETERMINISTIC: Same NPC always gets same hobbies.
    DYNAMIC: Different personalities = different hobbies.
    """
    personality = npc.get("personality", {})
    hobbies = []
    
    for hobby, (trait, threshold, _) in HOBBY_TRAITS.items():
        trait_value = personality.get(trait, 0.5)
        
        # Add slight per-NPC variation using seeded random
        seed = f"{npc.get('id', 'unknown')}_{hobby}"
        variation = seeded_random(seed) * 0.2 - 0.1  # ±0.1 variation
        
        if trait_value + variation > threshold:
            hobbies.append(hobby)
    
    # Ensure at least 2 hobbies
    if len(hobbies) < 2:
        defaults = ["socializing", "relaxing", "drinking"]
        for d in defaults:
            if d not in hobbies:
                hobbies.append(d)
            if len(hobbies) >= 2:
                break
    
    # Limit to 5 hobbies max
    if len(hobbies) > 5:
        # Keep the most weighted ones
        scored = [(h, HOBBY_TRAITS.get(h, ("", 0, 1))[2]) for h in hobbies]
        scored.sort(key=lambda x: -x[1])
        hobbies = [h[0] for h in scored[:5]]
    
    return hobbies

# =============================================================================
# SCHEDULE SYSTEM
# =============================================================================

SCHEDULES = {
    "worker": {
        "T01": {"activity": "sleeping", "location_type": "home"},
        "T02": {"activity": "sleeping", "location_type": "home"},
        "T03": {"activity": "commuting", "location_type": "transit"},
        "T04": {"activity": "working", "location_type": "workplace"},
        "T05": {"activity": "working", "location_type": "workplace"},
        "T06": {"activity": "commuting", "location_type": "transit"},
        "T07": {"activity": "leisure", "location_type": "entertainment"},
        "T08": {"activity": "socializing", "location_type": "bar"},
        "T09": {"activity": "returning", "location_type": "transit"},
        "T10": {"activity": "sleeping", "location_type": "home"},
    },
    "shopkeeper": {
        "T01": {"activity": "sleeping", "location_type": "home"},
        "T02": {"activity": "sleeping", "location_type": "home"},
        "T03": {"activity": "opening", "location_type": "workplace"},
        "T04": {"activity": "working", "location_type": "workplace"},
        "T05": {"activity": "working", "location_type": "workplace"},
        "T06": {"activity": "working", "location_type": "workplace"},
        "T07": {"activity": "closing", "location_type": "workplace"},
        "T08": {"activity": "dinner", "location_type": "restaurant"},
        "T09": {"activity": "relaxing", "location_type": "home"},
        "T10": {"activity": "sleeping", "location_type": "home"},
    },
    "resistance_fighter": {
        "T01": {"activity": "sleeping", "location_type": "home"},
        "T02": {"activity": "training", "location_type": "hideout"},
        "T03": {"activity": "intel", "location_type": "public"},
        "T04": {"activity": "meeting", "location_type": "hideout"},
        "T05": {"activity": "mission", "location_type": "varies"},
        "T06": {"activity": "mission", "location_type": "varies"},
        "T07": {"activity": "returning", "location_type": "transit"},
        "T08": {"activity": "socializing", "location_type": "bar"},
        "T09": {"activity": "personal", "location_type": "entertainment"},
        "T10": {"activity": "sleeping", "location_type": "home"},
    },
    "temple_guard": {
        "T01": {"activity": "patrol", "location_type": "public"},
        "T02": {"activity": "patrol", "location_type": "public"},
        "T03": {"activity": "shift_change", "location_type": "barracks"},
        "T04": {"activity": "patrol", "location_type": "public"},
        "T05": {"activity": "patrol", "location_type": "public"},
        "T06": {"activity": "shift_change", "location_type": "barracks"},
        "T07": {"activity": "patrol", "location_type": "public"},
        "T08": {"activity": "patrol", "location_type": "public"},
        "T09": {"activity": "off_duty", "location_type": "home"},
        "T10": {"activity": "sleeping", "location_type": "home"},
    },
    # Night shift workers - active at night, sleep during day
    "night_shift": {
        "T01": {"activity": "working", "location_type": "workplace"},  # Midnight-2:30am work
        "T02": {"activity": "working", "location_type": "workplace"},  # 2:30-5am work
        "T03": {"activity": "commuting", "location_type": "transit"},   # 5-7am going home
        "T04": {"activity": "sleeping", "location_type": "home"},       # 7-10am sleep
        "T05": {"activity": "sleeping", "location_type": "home"},       # 10am-12pm sleep
        "T06": {"activity": "sleeping", "location_type": "home"},       # 12-2pm sleep
        "T07": {"activity": "waking", "location_type": "home"},         # 2-5pm waking up
        "T08": {"activity": "leisure", "location_type": "entertainment"},# 5-7pm leisure
        "T09": {"activity": "commuting", "location_type": "transit"},   # 7-10pm going to work
        "T10": {"activity": "working", "location_type": "workplace"},   # 10pm-midnight work
    },
    # Security - always active, rotating patrols
    "security_night": {
        "T01": {"activity": "patrol", "location_type": "public"},
        "T02": {"activity": "patrol", "location_type": "public"},
        "T03": {"activity": "patrol", "location_type": "public"},
        "T04": {"activity": "shift_change", "location_type": "barracks"},
        "T05": {"activity": "sleeping", "location_type": "home"},
        "T06": {"activity": "sleeping", "location_type": "home"},
        "T07": {"activity": "waking", "location_type": "home"},
        "T08": {"activity": "commuting", "location_type": "transit"},
        "T09": {"activity": "patrol", "location_type": "public"},
        "T10": {"activity": "patrol", "location_type": "public"},
    },
    # Late night lifestyle - bartenders, entertainers
    "late_night": {
        "T01": {"activity": "working", "location_type": "bar"},
        "T02": {"activity": "closing", "location_type": "bar"},
        "T03": {"activity": "commuting", "location_type": "transit"},
        "T04": {"activity": "sleeping", "location_type": "home"},
        "T05": {"activity": "sleeping", "location_type": "home"},
        "T06": {"activity": "sleeping", "location_type": "home"},
        "T07": {"activity": "waking", "location_type": "home"},
        "T08": {"activity": "commuting", "location_type": "transit"},
        "T09": {"activity": "opening", "location_type": "bar"},
        "T10": {"activity": "working", "location_type": "bar"},
    },
    # Jogger/fitness enthusiast - early morning runs
    "fitness": {
        "T01": {"activity": "sleeping", "location_type": "home"},
        "T02": {"activity": "running", "location_type": "transit"},    # Pre-dawn jog!
        "T03": {"activity": "exercising", "location_type": "public"},  # Morning workout
        "T04": {"activity": "working", "location_type": "workplace"},
        "T05": {"activity": "working", "location_type": "workplace"},
        "T06": {"activity": "commuting", "location_type": "transit"},
        "T07": {"activity": "exercising", "location_type": "public"},  # Evening gym
        "T08": {"activity": "socializing", "location_type": "bar"},
        "T09": {"activity": "running", "location_type": "transit"},    # Night jog!
        "T10": {"activity": "sleeping", "location_type": "home"},
    },
    # Default for any other schedule
    "default": {
        "T01": {"activity": "sleeping", "location_type": "home"},
        "T02": {"activity": "sleeping", "location_type": "home"},
        "T03": {"activity": "waking", "location_type": "home"},
        "T04": {"activity": "active", "location_type": "public"},
        "T05": {"activity": "active", "location_type": "public"},
        "T06": {"activity": "active", "location_type": "public"},
        "T07": {"activity": "leisure", "location_type": "entertainment"},
        "T08": {"activity": "socializing", "location_type": "public"},
        "T09": {"activity": "returning", "location_type": "transit"},
        "T10": {"activity": "sleeping", "location_type": "home"},
    }
}

def get_npc_state(npc: dict, tick: int) -> dict:
    """
    Calculate NPC state at a given tick.
    Deterministic based on NPC ID and tick.
    Now DYNAMIC: Uses hobbies and personality for variety!
    """
    # Map archetype to schedule type
    archetype = npc.get("archetype", "").lower()
    
    # Archetype-to-schedule mapping for variety
    ARCHETYPE_TO_SCHEDULE = {
        # Night workers
        "security guard": "security_night",
        "guard": "security_night",
        "security": "security_night",
        "night watchman": "security_night",
        "bouncer": "late_night",
        "bartender": "late_night",
        "club owner": "late_night",
        "entertainer": "late_night",
        "dealer": "late_night",
        "gambler": "late_night",
        # Industrial night shifts
        "factory worker": "night_shift",
        "dock worker": "night_shift",
        "technician": "night_shift",
        "maintenance": "night_shift",
        # Fitness types
        "athlete": "fitness",
        "trainer": "fitness",
        "courier": "fitness",
        # Resistance
        "resistance fighter": "resistance_fighter",
        "resistance leader": "resistance_fighter",
        "operative": "resistance_fighter",
        # Temple
        "temple guard": "temple_guard",
        "inquisitor": "temple_guard",
        # Shopkeepers
        "merchant": "shopkeeper",
        "vendor": "shopkeeper",
        "shopkeeper": "shopkeeper",
        "clerk": "shopkeeper",
    }
    
    # Get schedule: explicit > archetype mapping > default  
    schedule_type = npc.get("schedule")
    if not schedule_type:
        # Try to match archetype keywords
        for keyword, sched in ARCHETYPE_TO_SCHEDULE.items():
            if keyword in archetype:
                schedule_type = sched
                break
        else:
            # Randomize ~20% to night shift based on NPC ID for variety
            if seeded_random(f"{npc.get('id', '')}_shift") < 0.15:
                schedule_type = seeded_choice(["night_shift", "late_night", "fitness"], f"{npc.get('id', '')}_random_shift")
            else:
                schedule_type = "default"
    
    schedule = SCHEDULES.get(schedule_type, SCHEDULES["default"])
    
    time_period = get_time_period(tick)
    slot = schedule.get(time_period, {"activity": "idle", "location_type": "home"})
    
    activity = slot["activity"]
    location_type = slot["location_type"]
    day = tick // 240
    
    # =========================================================================
    # DYNAMIC LEISURE CHOICES (New!)
    # =========================================================================
    # If schedule says "leisure" or "socializing", pick a SPECIFIC activity
    # based on NPC's hobbies and personality
    
    if activity in ["leisure", "socializing", "personal", "off_duty"]:
        hobbies = npc.get("hobbies") or generate_hobbies(npc)
        
        # Check each hobby to see if NPC does it today (frequency-based)
        todays_activities = []
        for hobby in hobbies:
            freq = "weekly"  # default frequency
            if should_do_today(hobby, freq, npc["id"], day):
                todays_activities.append(hobby)
        
        # If nothing scheduled for today, pick from general leisure
        if not todays_activities:
            todays_activities = ["socializing", "relaxing", "drinking"]
        
        # Pick one activity for this specific time slot
        seed = f"{npc['id']}_{tick}_{activity}"
        activity = seeded_choice(todays_activities, seed)
    
    # =========================================================================
    # HOBBY-AWARE LOCATION SELECTION
    # =========================================================================
    # Load hobby_locations from building codec
    building_codec = load_json("world_codec_16_buildings.json")
    hobby_locations = building_codec.get("hobby_locations", {}) if building_codec else {}
    
    # Determine actual location based on activity
    if location_type == "home":
        location = npc.get("home", "B001")
    elif location_type == "workplace":
        location = npc.get("workplace", "B003")
    elif activity in hobby_locations:
        # Pick a building that supports this hobby!
        hobby_buildings = hobby_locations[activity].get("buildings", [])
        if hobby_buildings:
            seed = f"{npc['id']}_{tick}_location"
            location = seeded_choice(hobby_buildings, seed)
        else:
            location = npc.get("home", "B001")
    elif location_type in ["varies", "public", "entertainment", "bar"]:
        # General public place - pick from entertainment venues
        buildings = get_buildings()
        public_buildings = [b for b in buildings if b.get("type") in ["commercial", "entertainment", "bar", "recreation"]]
        if public_buildings:
            seed = f"{npc['id']}_{tick}_public"
            location = seeded_choice([b["id"] for b in public_buildings], seed)
        else:
            location = "B004"  # Default bar
    else:
        location = npc.get("workplace", npc.get("home", "B001"))
    
    # Mood based on activity (expanded)
    mood_map = {
        "sleeping": "peaceful",
        "working": "focused",
        "socializing": "relaxed",
        "mission": "alert",
        "patrol": "vigilant",
        "training": "determined",
        "leisure": "content",
        "gambling": "excited",
        "drinking": "merry",
        "exercising": "energized",
        "reading": "contemplative",
        "meditating": "serene",
        "bowling": "competitive",
        "dancing": "joyful",
        "fishing": "peaceful",
    }
    mood = mood_map.get(activity, "neutral")
    
    return {
        "npc_id": npc["id"],
        "name": npc["name"],
        "tick": tick,
        "time_period": time_period,
        "activity": activity,
        "location": location,
        "location_type": location_type,
        "mood": mood,
        "faction": npc.get("faction", "civilian"),
        "archetype": npc.get("archetype", "resident"),
    }


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.route("/")
def index():
    """API documentation."""
    return jsonify({
        "name": "AO World Engine - NPC Simulation API",
        "version": "1.0.0",
        "endpoints": {
            "GET /api/npcs": "List all NPCs (supports ?limit, ?offset, ?faction, ?archetype)",
            "GET /api/npcs/<id>": "Get single NPC details",
            "GET /api/npcs/<id>/state?tick=N": "Get NPC state at tick N",
            "GET /api/npcs/at/<location>?tick=N": "Get all NPCs at location at tick",
            "GET /api/buildings": "List all buildings",
            "GET /api/buildings/<id>": "Get building details",
            "GET /api/simulation/tick?tick=N": "Run simulation for tick N",
            "GET /api/simulation/time?tick=N": "Get time info for tick",
            "GET /api/transport": "Get transportation system",
            "GET /api/stats": "Get simulation statistics",
        },
        "data_source": "local (can be switched to Arweave)",
        "total_npcs": len(get_npcs()),
        "total_buildings": len(get_buildings()),
    })


@app.route("/api/npcs")
def list_npcs():
    """List NPCs with optional filtering."""
    npcs = get_npcs()
    
    # Filters
    faction = request.args.get("faction")
    archetype = request.args.get("archetype")
    schedule = request.args.get("schedule")
    block = request.args.get("block")
    
    if faction:
        npcs = [n for n in npcs if n.get("faction") == faction]
    if archetype:
        npcs = [n for n in npcs if n.get("archetype") == archetype]
    if schedule:
        npcs = [n for n in npcs if n.get("schedule") == schedule]
    if block:
        npcs = [n for n in npcs if str(n.get("block")) == block]
    
    # Pagination - allow up to 1000 NPCs for full simulation
    limit = min(int(request.args.get("limit", 50)), 1000)
    offset = int(request.args.get("offset", 0))
    
    total = len(npcs)
    npcs = npcs[offset:offset + limit]
    
    return jsonify({
        "npcs": npcs,
        "total": total,
        "limit": limit,
        "offset": offset,
    })


@app.route("/api/npcs/<npc_id>")
def get_npc(npc_id):
    """Get single NPC by ID."""
    npcs = get_npcs()
    npc = next((n for n in npcs if n["id"] == npc_id), None)
    
    if not npc:
        return jsonify({"error": f"NPC {npc_id} not found"}), 404
    
    return jsonify(npc)


@app.route("/api/npcs/<npc_id>/state")
def get_npc_state_endpoint(npc_id):
    """Get NPC state at a specific tick."""
    npcs = get_npcs()
    npc = next((n for n in npcs if n["id"] == npc_id), None)
    
    if not npc:
        return jsonify({"error": f"NPC {npc_id} not found"}), 404
    
    tick = int(request.args.get("tick", 100))
    state = get_npc_state(npc, tick)
    state["npc"] = npc  # Include full NPC data
    
    return jsonify(state)


@app.route("/api/npcs/at/<location>")
def get_npcs_at_location(location):
    """Get all NPCs at a specific location at a tick."""
    tick = int(request.args.get("tick", 100))
    npcs = get_npcs()
    
    at_location = []
    for npc in npcs:
        state = get_npc_state(npc, tick)
        if state["location"] == location:
            at_location.append(state)
    
    return jsonify({
        "location": location,
        "tick": tick,
        "time": get_time_info(tick),
        "count": len(at_location),
        "npcs": at_location,
    })


@app.route("/api/buildings")
def list_buildings():
    """List all buildings."""
    buildings = get_buildings()
    return jsonify({
        "buildings": buildings,
        "total": len(buildings)
    })


@app.route("/api/buildings/<building_id>")
def get_building(building_id):
    """Get single building by ID."""
    buildings = get_buildings()
    building = next((b for b in buildings if b["id"] == building_id), None)
    
    if not building:
        return jsonify({"error": f"Building {building_id} not found"}), 404
    
    # Include NPCs that live/work here
    npcs = get_npcs()
    residents = [n["id"] for n in npcs if n.get("home") == building_id]
    workers = [n["id"] for n in npcs if n.get("workplace") == building_id]
    
    building["residents"] = residents[:20]  # First 20
    building["residents_total"] = len(residents)
    building["workers"] = workers[:20]
    building["workers_total"] = len(workers)
    
    return jsonify(building)


@app.route("/api/simulation/tick")
def simulation_tick():
    """
    Run simulation for a specific tick.
    Returns all NPC states and events.
    Add ?full=true to get all NPC states (slower).
    """
    tick = int(request.args.get("tick", 100))
    full = request.args.get("full", "false").lower() == "true"
    npcs = get_npcs()
    
    # Calculate all NPC states
    states = []
    location_counts = {}
    activity_counts = {}
    
    for npc in npcs:
        state = get_npc_state(npc, tick)
        states.append(state)
        
        loc = state["location"]
        location_counts[loc] = location_counts.get(loc, 0) + 1
        
        act = state["activity"]
        activity_counts[act] = activity_counts.get(act, 0) + 1
    
    # Generate random events (deterministic)
    events = generate_events(tick, location_counts)
    
    # Return full or truncated states based on param
    if full:
        npc_states = states
        truncated = False
    else:
        npc_states = states[:100] if len(states) > 100 else states
        truncated = len(states) > 100
    
    return jsonify({
        "tick": tick,
        "time": get_time_info(tick),
        "npc_count": len(states),
        "location_summary": location_counts,
        "activity_summary": activity_counts,
        "events": events,
        "npc_states": npc_states,
        "npc_states_truncated": truncated,
    })


def generate_events(tick: int, location_counts: dict) -> list:
    """Generate random events based on tick (deterministic)."""
    events = []
    
    event_types = [
        {"name": "street_argument", "probability": 0.05},
        {"name": "temple_patrol", "probability": 0.1},
        {"name": "vendor_sale", "probability": 0.08},
        {"name": "suspicious_activity", "probability": 0.03},
        {"name": "power_flicker", "probability": 0.02},
    ]
    
    for event in event_types:
        seed = f"{event['name']}_{tick}"
        h = int(hashlib.md5(seed.encode()).hexdigest(), 16) % 1000
        if h < event["probability"] * 1000:
            events.append({
                "type": event["name"],
                "tick": tick,
                "id": f"EVT_{tick}_{event['name'][:3]}"
            })
    
    return events


@app.route("/api/simulation/time")
def get_time():
    """Get time info for a tick."""
    tick = int(request.args.get("tick", 100))
    return jsonify(get_time_info(tick))


@app.route("/api/transport")
def get_transport_endpoint():
    """Get transportation system data."""
    return jsonify(get_transport())


@app.route("/api/stats")
def get_stats():
    """Get simulation statistics."""
    npcs = get_npcs()
    buildings = get_buildings()
    
    # Archetype distribution
    archetypes = {}
    factions = {}
    schedules = {}
    
    for npc in npcs:
        arch = npc.get("archetype", "unknown")
        archetypes[arch] = archetypes.get(arch, 0) + 1
        
        fac = npc.get("faction", "unknown")
        factions[fac] = factions.get(fac, 0) + 1
        
        sched = npc.get("schedule", "unknown")
        schedules[sched] = schedules.get(sched, 0) + 1
    
    # Building types
    building_types = {}
    for b in buildings:
        bt = b.get("type", "unknown")
        building_types[bt] = building_types.get(bt, 0) + 1
    
    return jsonify({
        "total_npcs": len(npcs),
        "total_buildings": len(buildings),
        "archetypes": archetypes,
        "factions": factions,
        "schedules": schedules,
        "building_types": building_types,
        "data_source": "local",
    })


# =============================================================================
# ARWEAVE INTEGRATION (placeholder for production)
# =============================================================================

ARWEAVE_GATEWAY = "https://arweave.net"

def fetch_from_arweave(tx_id: str) -> dict:
    """Fetch data from Arweave by transaction ID."""
    try:
        response = requests.get(f"{ARWEAVE_GATEWAY}/{tx_id}", timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Arweave fetch error: {e}")
    return None


@app.route("/api/arweave/<tx_id>")
def get_arweave_data(tx_id):
    """Fetch data from Arweave (for production use)."""
    data = fetch_from_arweave(tx_id)
    if data:
        return jsonify(data)
    return jsonify({"error": "Failed to fetch from Arweave"}), 404


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8081))  # Different port from npc_chat
    print(f"\n🌆 AO World Engine - NPC Simulation API")
    print(f"   http://localhost:{port}")
    print(f"\n📊 Data loaded:")
    print(f"   NPCs: {len(get_npcs())}")
    print(f"   Buildings: {len(get_buildings())}")
    print(f"\n📍 Endpoints:")
    print(f"   GET /api/npcs          - List NPCs")
    print(f"   GET /api/npcs/<id>     - Get NPC")
    print(f"   GET /api/npcs/<id>/state?tick=100")
    print(f"   GET /api/simulation/tick?tick=100")
    print(f"   GET /api/buildings")
    print(f"   GET /api/transport")
    print()
    
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)

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
    """
    schedule_type = npc.get("schedule", "default")
    schedule = SCHEDULES.get(schedule_type, SCHEDULES["default"])
    
    time_period = get_time_period(tick)
    slot = schedule.get(time_period, {"activity": "idle", "location_type": "home"})
    
    # Determine actual location from location_type
    location_type = slot["location_type"]
    if location_type == "home":
        location = npc.get("home", "B001")
    elif location_type == "workplace":
        location = npc.get("workplace", "B003")
    elif location_type in ["varies", "public"]:
        # Deterministic choice based on tick
        h = int(hashlib.md5(f"{npc['id']}_{tick // 10}".encode()).hexdigest(), 16)
        buildings = get_buildings()
        public_buildings = [b for b in buildings if b["type"] in ["commercial", "entertainment", "restaurant"]]
        if public_buildings:
            location = public_buildings[h % len(public_buildings)]["id"]
        else:
            location = "B003"
    else:
        location = npc.get("workplace", npc.get("home", "B001"))
    
    # Mood based on activity
    mood_map = {
        "sleeping": "peaceful",
        "working": "focused",
        "socializing": "relaxed",
        "mission": "alert",
        "patrol": "vigilant",
        "training": "determined",
        "leisure": "content",
    }
    mood = mood_map.get(slot["activity"], "neutral")
    
    return {
        "npc_id": npc["id"],
        "name": npc["name"],
        "tick": tick,
        "time_period": time_period,
        "activity": slot["activity"],
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
    
    # Pagination
    limit = min(int(request.args.get("limit", 50)), 500)
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
    """
    tick = int(request.args.get("tick", 100))
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
    
    return jsonify({
        "tick": tick,
        "time": get_time_info(tick),
        "npc_count": len(states),
        "location_summary": location_counts,
        "activity_summary": activity_counts,
        "events": events,
        # Only include first 100 states for performance
        "npc_states": states[:100] if len(states) > 100 else states,
        "npc_states_truncated": len(states) > 100,
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
    
    app.run(host="0.0.0.0", port=port, debug=True)

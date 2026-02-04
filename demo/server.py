#!/usr/bin/env python3
"""
RE:ECHO City Combined Server
Serves landing page, visualizer, chat interface, AND the NPC Simulation API.
This is a combined deployment for Cloud Run.
"""
import os
import sys

# Add parent directory to path for API imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, send_from_directory, render_template, jsonify, request
from flask_cors import CORS

# Import API routes from the api module
from api.api_simulation import (
    get_npcs, get_buildings, get_transport, get_npc_state, 
    get_time_info, generate_hobbies
)

app = Flask(__name__, 
           static_folder='static',
           template_folder='templates')

CORS(app)  # Allow cross-origin requests

# =============================================================================
# FRONTEND ROUTES
# =============================================================================

@app.route('/')
def landing():
    """Landing page with navigation to Explore and Chat."""
    return render_template('landing.html')

@app.route('/explore')
def explore():
    """Visualizer - Map view with buildings and NPCs."""
    return send_from_directory('static', 'visualizer.html')

@app.route('/chat')
def chat():
    """Chat interface for talking to NPCs."""
    return send_from_directory('static', 'chat.html')

@app.route('/health')
def health():
    return {'status': 'ok'}, 200

@app.route('/static/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

# Legacy route support
@app.route('/index.html')
def legacy_index():
    return send_from_directory('static', 'chat.html')

# =============================================================================
# API ROUTES (from api_simulation.py)
# =============================================================================

@app.route("/api")
@app.route("/api/")
def api_index():
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
            "GET /api/stats": "Get simulation statistics",
        },
        "data_source": "local (bundled with deployment)",
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
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)
    
    if faction:
        npcs = [n for n in npcs if n.get("faction", "").lower() == faction.lower()]
    if archetype:
        npcs = [n for n in npcs if n.get("archetype", "").lower() == archetype.lower()]
    
    total = len(npcs)
    npcs = npcs[offset:offset + limit]
    
    return jsonify({
        "total": total,
        "limit": limit,
        "offset": offset,
        "npcs": npcs
    })

@app.route("/api/npcs/<npc_id>")
def get_npc(npc_id):
    """Get single NPC by ID."""
    npcs = get_npcs()
    npc = next((n for n in npcs if n["id"] == npc_id), None)
    if not npc:
        return jsonify({"error": f"NPC {npc_id} not found"}), 404
    
    # Add hobbies if not present
    if "hobbies" not in npc:
        npc["hobbies"] = generate_hobbies(npc)
    
    return jsonify(npc)

@app.route("/api/npcs/<npc_id>/state")
def get_npc_state_endpoint(npc_id):
    """Get NPC state at a specific tick."""
    tick = request.args.get("tick", 0, type=int)
    npcs = get_npcs()
    npc = next((n for n in npcs if n["id"] == npc_id), None)
    if not npc:
        return jsonify({"error": f"NPC {npc_id} not found"}), 404
    
    state = get_npc_state(npc, tick)
    return jsonify(state)

@app.route("/api/buildings")
def list_buildings():
    """List all buildings."""
    buildings = get_buildings()
    return jsonify({
        "total": len(buildings),
        "buildings": buildings
    })

@app.route("/api/buildings/<building_id>")
def get_building(building_id):
    """Get single building by ID."""
    buildings = get_buildings()
    building = next((b for b in buildings if b["id"] == building_id), None)
    if not building:
        return jsonify({"error": f"Building {building_id} not found"}), 404
    return jsonify(building)

@app.route("/api/npcs/at/<location>")
def get_npcs_at_location(location):
    """Get all NPCs at a location at a given tick."""
    tick = request.args.get("tick", 0, type=int)
    npcs = get_npcs()
    
    # Calculate which NPCs are at this location at this tick
    npcs_at_location = []
    for npc in npcs:
        state = get_npc_state(npc, tick)
        # Check if NPC's calculated location matches the requested location
        if state.get("location", "") == location or state.get("building_id", "") == location:
            npcs_at_location.append({
                "id": npc["id"],
                "name": npc.get("name", npc["id"]),
                "activity": state["activity"],
                "mood": state["mood"],
                "location": state["location"]
            })
    
    return jsonify(npcs_at_location)

@app.route("/api/simulation/tick")
def simulation_tick():
    """Run simulation for a tick."""
    tick = request.args.get("tick", 0, type=int)
    npcs = get_npcs()
    buildings = get_buildings()
    
    # Calculate states for ALL NPCs to get location summary
    states = []
    location_summary = {}
    
    for npc in npcs:
        state = get_npc_state(npc, tick)
        loc = state.get("location", "unknown")
        location_summary[loc] = location_summary.get(loc, 0) + 1
        
        # Only add first 100 NPCs to response for performance
        if len(states) < 100:
            states.append({
                "id": npc["id"],
                "name": npc.get("name", npc["id"]),
                "location": state["location"],
                "activity": state["activity"],
                "mood": state["mood"],
                "faction": npc.get("faction", "civilian")
            })
    
    time_info = get_time_info(tick)
    
    return jsonify({
        "tick": tick,
        "time": time_info,
        "npc_count": len(npcs),
        "location_summary": location_summary,
        "npcs": states
    })

@app.route("/api/simulation/time")
def simulation_time():
    """Get time info for a tick."""
    tick = request.args.get("tick", 0, type=int)
    return jsonify(get_time_info(tick))

@app.route("/api/stats")
def stats():
    """Get simulation statistics."""
    npcs = get_npcs()
    buildings = get_buildings()
    
    factions = {}
    archetypes = {}
    for npc in npcs:
        f = npc.get("faction", "unknown")
        a = npc.get("archetype", "unknown")
        factions[f] = factions.get(f, 0) + 1
        archetypes[a] = archetypes.get(a, 0) + 1
    
    return jsonify({
        "total_npcs": len(npcs),
        "total_buildings": len(buildings),
        "factions": factions,
        "archetypes": archetypes
    })


# =============================================================================
# TRAFFIC API (24-hour city simulation)
# =============================================================================

import hashlib

def seeded_random(seed):
    """Generate deterministic random float 0-1."""
    h = int(hashlib.md5(seed.encode()).hexdigest(), 16) % 10000
    return h / 10000

def seeded_choice(items, seed):
    """Deterministically choose from list."""
    if not items:
        return None
    h = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    return items[h % len(items)]

@app.route("/api/traffic")
def get_traffic():
    """Get traffic and street activity for a tick."""
    tick = request.args.get("tick", 100, type=int)
    time_info = get_time_info(tick)
    time_period = time_info["period"]
    
    TRAFFIC_DENSITY = {
        "T01": 0.05, "T02": 0.03, "T03": 0.35, "T04": 0.80,
        "T05": 0.50, "T06": 0.65, "T07": 0.85, "T08": 0.55,
        "T09": 0.25, "T10": 0.10,
    }
    density = TRAFFIC_DENSITY.get(time_period, 0.3)
    
    # Quick vehicle generation
    vehicles = []
    num_vehicles = max(1, int(15 * density))
    for i in range(num_vehicles):
        vtype = seeded_choice(["car", "taxi", "truck", "motorcycle"], f"veh_{tick}_{i}")
        vehicles.append({"type": vtype, "zone": seeded_choice(["market", "residential", "temple"], f"zonev_{tick}_{i}")})
    
    # Emergency services
    is_night = time_period in ["T01", "T02", "T10"]
    emergency = [
        {"type": "police", "activity": "patrol", "responding": seeded_random(f"pol_{tick}") < 0.1},
        {"type": "ambulance", "activity": "standby" if seeded_random(f"amb_{tick}") > 0.1 else "responding"}
    ]
    if is_night:
        emergency.append({"type": "police", "activity": "patrol", "shift": "night"})
    
    return jsonify({
        "tick": tick,
        "traffic_density": density,
        "traffic_level": "dead" if density < 0.1 else "light" if density < 0.3 else "moderate" if density < 0.6 else "heavy",
        "vehicles": vehicles,
        "emergency_services": emergency
    })


# =============================================================================
# SOCIAL DYNAMICS API
# =============================================================================

# Try to import full social dynamics
try:
    from scripts.social_dynamics import (
        get_npc_social_summary, get_reputation, find_potential_groups,
        get_relationship_type, RELATIONSHIP_THRESHOLDS, MEETING_THRESHOLDS
    )
    SOCIAL_AVAILABLE = True
except ImportError:
    SOCIAL_AVAILABLE = False

@app.route("/api/social/npc/<npc_id>")
def get_npc_social(npc_id):
    """Get NPC's social network."""
    npcs = get_npcs()
    npc = next((n for n in npcs if n.get("id") == npc_id), None)
    if not npc:
        return jsonify({"error": f"NPC {npc_id} not found"}), 404
    
    if not SOCIAL_AVAILABLE:
        # Fallback: generate basic relationships from family/workplace
        relationships = {}
        family = npc.get("family", {})
        if family.get("spouse_id"):
            relationships["spouse"] = {"id": family["spouse_id"], "trust": 0.9}
        workplace = npc.get("workplace")
        coworkers = [n["id"] for n in npcs if n.get("workplace") == workplace and n["id"] != npc_id][:5]
        
        return jsonify({
            "npc_id": npc_id,
            "fallback": True,
            "social": {
                "family": family,
                "coworkers": coworkers,
                "total_connections": len(coworkers) + (1 if family.get("spouse_id") else 0)
            }
        })
    
    # Full social dynamics
    if "relationships" not in npc:
        npc["relationships"] = {}
        family = npc.get("family", {})
        if family.get("spouse_id"):
            npc["relationships"][family["spouse_id"]] = {"trust": 0.9, "type": "close_friend"}
        workplace = npc.get("workplace")
        if workplace:
            for other in npcs:
                if other.get("workplace") == workplace and other["id"] != npc_id:
                    seed = f"{npc_id}_{other['id']}"
                    h = int(hashlib.md5(seed.encode()).hexdigest(), 16) % 100
                    npc["relationships"][other["id"]] = {
                        "trust": 0.3 + h/200, "meetings": 10 + h%30,
                        "type": get_relationship_type(0.3 + h/200)
                    }
    
    summary = get_npc_social_summary(npc)
    return jsonify({
        "npc_id": npc_id,
        "name": npc.get("name"),
        "social": summary
    })

@app.route("/api/social/groups")
def get_social_groups():
    """Get social groups."""
    if not SOCIAL_AVAILABLE:
        return jsonify({"error": "Social dynamics not available", "fallback": True, "groups": []})
    
    npcs = get_npcs()
    tick = request.args.get("tick", 100, type=int)
    groups = find_potential_groups(npcs, tick)
    
    return jsonify({
        "groups_count": len(groups),
        "groups": [g.to_dict() for g in groups[:30]]
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)

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

@app.route("/api/simulation/tick")
def simulation_tick():
    """Run simulation for a tick."""
    tick = request.args.get("tick", 0, type=int)
    npcs = get_npcs()
    buildings = get_buildings()
    
    # Calculate states for all NPCs
    states = []
    for npc in npcs[:100]:  # Limit for performance
        state = get_npc_state(npc, tick)
        states.append({
            "id": npc["id"],
            "name": npc.get("name", npc["id"]),
            "location": state["location"],
            "activity": state["activity"],
            "mood": state["mood"]
        })
    
    time_info = get_time_info(tick)
    
    return jsonify({
        "tick": tick,
        "time": time_info,
        "npc_count": len(states),
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)

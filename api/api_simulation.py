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
import random
import requests

app = Flask(__name__)
CORS(app)

# =============================================================================
# DATA LOADING
# =============================================================================

# Support both local dev (relative to api/) and Docker (/app/data/)
_local_data = os.path.join(os.path.dirname(__file__), "..", "data")
_docker_data = "/app/data"
DATA_DIR = _docker_data if os.path.exists(_docker_data) else _local_data
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

def get_npcs_from_chunks(max_npcs=800):
    """
    Get NPCs from the chunked data files (richer profiles).
    These are the 10k NPCs with full physical descriptions.
    """
    if "chunked_npcs" in _cache:
        return _cache["chunked_npcs"][:max_npcs]
    
    chunks_dir = os.path.join(DATA_DIR, "npc_chunks")
    if not os.path.exists(chunks_dir):
        return get_npcs()  # Fallback to basic NPCs
    
    all_npcs = []
    chunk_num = 1
    while len(all_npcs) < max_npcs:
        chunk_file = os.path.join(chunks_dir, f"npc_chunk_{str(chunk_num).zfill(3)}.json")
        if not os.path.exists(chunk_file):
            break
        with open(chunk_file, 'r') as f:
            chunk_data = json.load(f)
            all_npcs.extend(chunk_data.get("npcs", []))
        chunk_num += 1
    
    _cache["chunked_npcs"] = all_npcs
    return all_npcs[:max_npcs]

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
# NEEDS SYSTEM (Sims-style)
# =============================================================================
# NPCs have needs that decay over time and get satisfied by activities

NEEDS = {
    "hunger":  {"decay_rate": 0.02,  "critical": 0.2},
    "sleep":   {"decay_rate": 0.015, "critical": 0.15},
    "social":  {"decay_rate": 0.01,  "critical": 0.25},
    "hygiene": {"decay_rate": 0.008, "critical": 0.3},
    "safety":  {"decay_rate": 0.005, "critical": 0.1},
    "income":  {"decay_rate": 0.01,  "critical": 0.2},
}

# Activities that satisfy needs
ACTIVITY_SATISFIES = {
    "eating": {"hunger": 0.8},
    "sleeping": {"sleep": 0.1, "hygiene": -0.02},  # Sleep restores slowly
    "waking": {"sleep": 0.05},
    "socializing": {"social": 0.3},
    "dancing": {"social": 0.2},
    "drinking": {"social": 0.15},
    "working": {"income": 0.1, "social": 0.05},
    "patrol": {"income": 0.1, "safety": 0.1},
    "bathing": {"hygiene": 0.6},
    "leisure": {"social": 0.1},
}

def calculate_needs(npc: dict, tick: int) -> dict:
    """
    Calculate NPC needs at a given tick.
    Deterministic based on NPC ID, tick, and their schedule.
    """
    # Start from base values or NPC's stored needs
    base_needs = npc.get("needs_state", {
        "hunger": 0.8,
        "sleep": 0.8,
        "social": 0.7,
        "hygiene": 0.9,
        "safety": 0.7,
        "income": 0.5,
    })
    
    # Calculate decay based on time elapsed (tick)
    # Each tick represents ~6 minutes, so 240 ticks = 1 day
    day_tick = tick % 240
    
    needs = {}
    for need, config in NEEDS.items():
        base = base_needs.get(need, 0.7)
        
        # Decay based on how far into the day we are
        decay = config["decay_rate"] * day_tick * 0.1  # Scaled decay
        
        # Add variation based on NPC personality
        personality = npc.get("personality", {})
        if need == "social" and personality.get("sociability", 0.5) < 0.4:
            decay *= 0.5  # Introverts need less social
        elif need == "income" and personality.get("greed", 0.5) > 0.7:
            decay *= 1.5  # Greedy NPCs worry more about money
        
        # Clamp to 0-1
        value = max(0.0, min(1.0, base - decay))
        needs[need] = round(value, 2)
    
    return needs

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
# SCHEDULE SYSTEM - DIVERSE SCHEDULES FOR REALISTIC BEHAVIOR
# =============================================================================

SCHEDULES = {
    # =========================================================================
    # WORKER SCHEDULES (most common - 60% of population)
    # =========================================================================
    "worker": {  # Standard 9-5 worker
        "T01": {"activity": "sleeping", "location_type": "home"},      # 00:00-02:30
        "T02": {"activity": "sleeping", "location_type": "home"},      # 02:30-05:00
        "T03": {"activity": "waking", "location_type": "home"},        # 05:00-07:00
        "T04": {"activity": "working", "location_type": "workplace"},  # 07:00-10:00
        "T05": {"activity": "working", "location_type": "workplace"},  # 10:00-12:00
        "T06": {"activity": "working", "location_type": "workplace"},  # 12:00-14:00
        "T07": {"activity": "commuting", "location_type": "transit"},  # 14:00-17:00
        "T08": {"activity": "leisure", "location_type": "home"},       # 17:00-19:00
        "T09": {"activity": "relaxing", "location_type": "home"},      # 19:00-22:00
        "T10": {"activity": "sleeping", "location_type": "home"},      # 22:00-midnight
    },
    "office_worker": {  # Office hours with lunch break
        "T01": {"activity": "sleeping", "location_type": "home"},
        "T02": {"activity": "sleeping", "location_type": "home"},
        "T03": {"activity": "commuting", "location_type": "transit"},
        "T04": {"activity": "working", "location_type": "workplace"},
        "T05": {"activity": "lunch", "location_type": "restaurant"},   # Lunch hour
        "T06": {"activity": "working", "location_type": "workplace"},
        "T07": {"activity": "commuting", "location_type": "transit"},
        "T08": {"activity": "socializing", "location_type": "bar"},
        "T09": {"activity": "relaxing", "location_type": "home"},
        "T10": {"activity": "sleeping", "location_type": "home"},
    },
    "early_bird": {  # Early riser, early finish
        "T01": {"activity": "sleeping", "location_type": "home"},
        "T02": {"activity": "waking", "location_type": "home"},        # Up at 3am
        "T03": {"activity": "working", "location_type": "workplace"},  # Work 5am
        "T04": {"activity": "working", "location_type": "workplace"},
        "T05": {"activity": "working", "location_type": "workplace"},
        "T06": {"activity": "commuting", "location_type": "transit"},  # Done at 2pm
        "T07": {"activity": "leisure", "location_type": "entertainment"},
        "T08": {"activity": "dinner", "location_type": "home"},
        "T09": {"activity": "sleeping", "location_type": "home"},      # Early bed
        "T10": {"activity": "sleeping", "location_type": "home"},
    },
    
    # =========================================================================
    # HOME-BASED SCHEDULES (20% of population)
    # =========================================================================
    "homebody": {  # Works from home / stays home a lot
        "T01": {"activity": "sleeping", "location_type": "home"},
        "T02": {"activity": "sleeping", "location_type": "home"},
        "T03": {"activity": "waking", "location_type": "home"},
        "T04": {"activity": "working", "location_type": "home"},       # Remote work
        "T05": {"activity": "working", "location_type": "home"},
        "T06": {"activity": "lunch", "location_type": "home"},
        "T07": {"activity": "working", "location_type": "home"},
        "T08": {"activity": "leisure", "location_type": "home"},
        "T09": {"activity": "relaxing", "location_type": "home"},
        "T10": {"activity": "sleeping", "location_type": "home"},
    },
    "parent": {  # Parent with kids - school runs
        "T01": {"activity": "sleeping", "location_type": "home"},
        "T02": {"activity": "sleeping", "location_type": "home"},
        "T03": {"activity": "parenting", "location_type": "home"},     # Morning routine
        "T04": {"activity": "shopping", "location_type": "commercial"},
        "T05": {"activity": "chores", "location_type": "home"},
        "T06": {"activity": "cooking", "location_type": "home"},
        "T07": {"activity": "parenting", "location_type": "home"},     # Kids home
        "T08": {"activity": "dinner", "location_type": "home"},
        "T09": {"activity": "relaxing", "location_type": "home"},
        "T10": {"activity": "sleeping", "location_type": "home"},
    },
    "retiree": {  # Retired, leisurely schedule
        "T01": {"activity": "sleeping", "location_type": "home"},
        "T02": {"activity": "sleeping", "location_type": "home"},
        "T03": {"activity": "waking", "location_type": "home"},
        "T04": {"activity": "leisure", "location_type": "home"},
        "T05": {"activity": "walking", "location_type": "public"},     # Morning walk
        "T06": {"activity": "lunch", "location_type": "restaurant"},
        "T07": {"activity": "leisure", "location_type": "home"},
        "T08": {"activity": "socializing", "location_type": "bar"},
        "T09": {"activity": "relaxing", "location_type": "home"},
        "T10": {"activity": "sleeping", "location_type": "home"},
    },
    
    # =========================================================================
    # SERVICE/RETAIL SCHEDULES (10% of population)
    # =========================================================================
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
    
    # =========================================================================
    # NIGHT SHIFT SCHEDULES (8% of population)
    # =========================================================================
    "night_shift": {
        "T01": {"activity": "working", "location_type": "workplace"},
        "T02": {"activity": "working", "location_type": "workplace"},
        "T03": {"activity": "commuting", "location_type": "transit"},
        "T04": {"activity": "sleeping", "location_type": "home"},
        "T05": {"activity": "sleeping", "location_type": "home"},
        "T06": {"activity": "sleeping", "location_type": "home"},
        "T07": {"activity": "waking", "location_type": "home"},
        "T08": {"activity": "leisure", "location_type": "entertainment"},
        "T09": {"activity": "commuting", "location_type": "transit"},
        "T10": {"activity": "working", "location_type": "workplace"},
    },
    "late_night": {  # Bar staff, entertainers
        "T01": {"activity": "working", "location_type": "workplace"},  # Closing bar
        "T02": {"activity": "relaxing", "location_type": "home"},
        "T03": {"activity": "sleeping", "location_type": "home"},
        "T04": {"activity": "sleeping", "location_type": "home"},
        "T05": {"activity": "sleeping", "location_type": "home"},
        "T06": {"activity": "waking", "location_type": "home"},
        "T07": {"activity": "leisure", "location_type": "home"},
        "T08": {"activity": "commuting", "location_type": "transit"},
        "T09": {"activity": "working", "location_type": "workplace"},  # Bar opens
        "T10": {"activity": "working", "location_type": "workplace"},
    },
    "security_night": {
        "T01": {"activity": "patrol", "location_type": "public"},
        "T02": {"activity": "patrol", "location_type": "public"},
        "T03": {"activity": "shift_change", "location_type": "workplace"},
        "T04": {"activity": "sleeping", "location_type": "home"},
        "T05": {"activity": "sleeping", "location_type": "home"},
        "T06": {"activity": "sleeping", "location_type": "home"},
        "T07": {"activity": "waking", "location_type": "home"},
        "T08": {"activity": "commuting", "location_type": "transit"},
        "T09": {"activity": "patrol", "location_type": "public"},
        "T10": {"activity": "patrol", "location_type": "public"},
    },
    
    # =========================================================================
    # EMERGENCY SERVICES (24/7 - always someone on duty)
    # =========================================================================
    "police_day": {  # Day shift 6am-6pm
        "T01": {"activity": "sleeping", "location_type": "home"},
        "T02": {"activity": "waking", "location_type": "home"},
        "T03": {"activity": "patrol", "location_type": "street"},
        "T04": {"activity": "patrol", "location_type": "street"},
        "T05": {"activity": "patrol", "location_type": "street"},
        "T06": {"activity": "paperwork", "location_type": "workplace"},
        "T07": {"activity": "shift_change", "location_type": "workplace"},
        "T08": {"activity": "leisure", "location_type": "home"},
        "T09": {"activity": "relaxing", "location_type": "home"},
        "T10": {"activity": "sleeping", "location_type": "home"},
    },
    "police_night": {  # Night shift 6pm-6am
        "T01": {"activity": "patrol", "location_type": "street"},
        "T02": {"activity": "patrol", "location_type": "street"},
        "T03": {"activity": "shift_change", "location_type": "workplace"},
        "T04": {"activity": "sleeping", "location_type": "home"},
        "T05": {"activity": "sleeping", "location_type": "home"},
        "T06": {"activity": "sleeping", "location_type": "home"},
        "T07": {"activity": "waking", "location_type": "home"},
        "T08": {"activity": "commuting", "location_type": "transit"},
        "T09": {"activity": "patrol", "location_type": "street"},
        "T10": {"activity": "patrol", "location_type": "street"},
    },
    "ambulance_day": {  # EMT/Paramedic day shift
        "T01": {"activity": "sleeping", "location_type": "home"},
        "T02": {"activity": "waking", "location_type": "home"},
        "T03": {"activity": "responding", "location_type": "street"},
        "T04": {"activity": "responding", "location_type": "street"},
        "T05": {"activity": "standby", "location_type": "workplace"},
        "T06": {"activity": "responding", "location_type": "street"},
        "T07": {"activity": "shift_change", "location_type": "workplace"},
        "T08": {"activity": "leisure", "location_type": "home"},
        "T09": {"activity": "relaxing", "location_type": "home"},
        "T10": {"activity": "sleeping", "location_type": "home"},
    },
    "ambulance_night": {  # EMT/Paramedic night shift
        "T01": {"activity": "responding", "location_type": "street"},
        "T02": {"activity": "standby", "location_type": "workplace"},
        "T03": {"activity": "shift_change", "location_type": "workplace"},
        "T04": {"activity": "sleeping", "location_type": "home"},
        "T05": {"activity": "sleeping", "location_type": "home"},
        "T06": {"activity": "sleeping", "location_type": "home"},
        "T07": {"activity": "waking", "location_type": "home"},
        "T08": {"activity": "commuting", "location_type": "transit"},
        "T09": {"activity": "responding", "location_type": "street"},
        "T10": {"activity": "responding", "location_type": "street"},
    },
    "clinic_doctor": {  # Hospital/Clinic medical staff
        "T01": {"activity": "on_call", "location_type": "workplace"},
        "T02": {"activity": "resting", "location_type": "workplace"},
        "T03": {"activity": "treating", "location_type": "workplace"},
        "T04": {"activity": "treating", "location_type": "workplace"},
        "T05": {"activity": "treating", "location_type": "workplace"},
        "T06": {"activity": "commuting", "location_type": "transit"},
        "T07": {"activity": "leisure", "location_type": "home"},
        "T08": {"activity": "relaxing", "location_type": "home"},
        "T09": {"activity": "sleeping", "location_type": "home"},
        "T10": {"activity": "sleeping", "location_type": "home"},
    },
    
    # =========================================================================
    # TRANSPORT & INFRASTRUCTURE (24/7 operations)
    # =========================================================================
    "transit_driver_day": {  # Bus/tram driver day shift
        "T01": {"activity": "sleeping", "location_type": "home"},
        "T02": {"activity": "waking", "location_type": "home"},
        "T03": {"activity": "driving", "location_type": "transit"},
        "T04": {"activity": "driving", "location_type": "transit"},
        "T05": {"activity": "break", "location_type": "workplace"},
        "T06": {"activity": "driving", "location_type": "transit"},
        "T07": {"activity": "shift_end", "location_type": "workplace"},
        "T08": {"activity": "leisure", "location_type": "bar"},
        "T09": {"activity": "relaxing", "location_type": "home"},
        "T10": {"activity": "sleeping", "location_type": "home"},
    },
    "transit_driver_night": {  # Bus/tram driver night shift
        "T01": {"activity": "driving", "location_type": "transit"},
        "T02": {"activity": "driving", "location_type": "transit"},
        "T03": {"activity": "shift_end", "location_type": "workplace"},
        "T04": {"activity": "sleeping", "location_type": "home"},
        "T05": {"activity": "sleeping", "location_type": "home"},
        "T06": {"activity": "sleeping", "location_type": "home"},
        "T07": {"activity": "waking", "location_type": "home"},
        "T08": {"activity": "leisure", "location_type": "home"},
        "T09": {"activity": "commuting", "location_type": "transit"},
        "T10": {"activity": "driving", "location_type": "transit"},
    },
    "sanitation": {  # Garbage collection, street cleaning (early morning)
        "T01": {"activity": "sleeping", "location_type": "home"},
        "T02": {"activity": "waking", "location_type": "home"},
        "T03": {"activity": "collecting", "location_type": "street"},
        "T04": {"activity": "collecting", "location_type": "street"},
        "T05": {"activity": "collecting", "location_type": "street"},
        "T06": {"activity": "returning", "location_type": "workplace"},
        "T07": {"activity": "leisure", "location_type": "home"},
        "T08": {"activity": "dinner", "location_type": "home"},
        "T09": {"activity": "relaxing", "location_type": "home"},
        "T10": {"activity": "sleeping", "location_type": "home"},
    },
    "infrastructure_night": {  # Road work, repairs (night to avoid traffic)
        "T01": {"activity": "repairing", "location_type": "street"},
        "T02": {"activity": "repairing", "location_type": "street"},
        "T03": {"activity": "shift_end", "location_type": "workplace"},
        "T04": {"activity": "sleeping", "location_type": "home"},
        "T05": {"activity": "sleeping", "location_type": "home"},
        "T06": {"activity": "sleeping", "location_type": "home"},
        "T07": {"activity": "sleeping", "location_type": "home"},
        "T08": {"activity": "waking", "location_type": "home"},
        "T09": {"activity": "commuting", "location_type": "transit"},
        "T10": {"activity": "repairing", "location_type": "street"},
    },
    
    # =========================================================================
    # SPECIAL SCHEDULES (2% of population)
    # =========================================================================
    "resistance_fighter": {
        "T01": {"activity": "sleeping", "location_type": "home"},
        "T02": {"activity": "training", "location_type": "hideout"},
        "T03": {"activity": "intel", "location_type": "public"},
        "T04": {"activity": "meeting", "location_type": "hideout"},
        "T05": {"activity": "mission", "location_type": "varies"},
        "T06": {"activity": "mission", "location_type": "varies"},
        "T07": {"activity": "returning", "location_type": "transit"},
        "T08": {"activity": "socializing", "location_type": "bar"},
        "T09": {"activity": "personal", "location_type": "home"},
        "T10": {"activity": "sleeping", "location_type": "home"},
    },
    "temple_guard": {
        "T01": {"activity": "patrol", "location_type": "public"},
        "T02": {"activity": "patrol", "location_type": "public"},
        "T03": {"activity": "shift_change", "location_type": "workplace"},
        "T04": {"activity": "patrol", "location_type": "public"},
        "T05": {"activity": "patrol", "location_type": "public"},
        "T06": {"activity": "shift_change", "location_type": "workplace"},
        "T07": {"activity": "patrol", "location_type": "public"},
        "T08": {"activity": "patrol", "location_type": "public"},
        "T09": {"activity": "off_duty", "location_type": "home"},
        "T10": {"activity": "sleeping", "location_type": "home"},
    },
    "fitness": {  # Athletes, trainers
        "T01": {"activity": "sleeping", "location_type": "home"},
        "T02": {"activity": "exercising", "location_type": "public"},  # Early workout
        "T03": {"activity": "training", "location_type": "recreation"},
        "T04": {"activity": "working", "location_type": "workplace"},
        "T05": {"activity": "lunch", "location_type": "restaurant"},
        "T06": {"activity": "commuting", "location_type": "transit"},
        "T07": {"activity": "exercising", "location_type": "public"},  # Evening gym
        "T08": {"activity": "relaxing", "location_type": "home"},
        "T09": {"activity": "sleeping", "location_type": "home"},      # Early bed
        "T10": {"activity": "sleeping", "location_type": "home"},
    },
    "student": {  # Students - classes and studying
        "T01": {"activity": "sleeping", "location_type": "home"},
        "T02": {"activity": "sleeping", "location_type": "home"},
        "T03": {"activity": "waking", "location_type": "home"},
        "T04": {"activity": "studying", "location_type": "workplace"},  # Class
        "T05": {"activity": "studying", "location_type": "workplace"},
        "T06": {"activity": "lunch", "location_type": "restaurant"},
        "T07": {"activity": "studying", "location_type": "home"},
        "T08": {"activity": "socializing", "location_type": "bar"},    # Party time
        "T09": {"activity": "socializing", "location_type": "bar"},
        "T10": {"activity": "sleeping", "location_type": "home"},
    },
    "freelancer": {  # Irregular schedule
        "T01": {"activity": "sleeping", "location_type": "home"},
        "T02": {"activity": "sleeping", "location_type": "home"},
        "T03": {"activity": "sleeping", "location_type": "home"},      # Late riser
        "T04": {"activity": "waking", "location_type": "home"},
        "T05": {"activity": "working", "location_type": "home"},
        "T06": {"activity": "working", "location_type": "home"},
        "T07": {"activity": "working", "location_type": "home"},
        "T08": {"activity": "leisure", "location_type": "entertainment"},
        "T09": {"activity": "socializing", "location_type": "bar"},
        "T10": {"activity": "working", "location_type": "home"},       # Night owl
    },
    "unemployed": {  # Looking for work, irregular
        "T01": {"activity": "sleeping", "location_type": "home"},
        "T02": {"activity": "sleeping", "location_type": "home"},
        "T03": {"activity": "waking", "location_type": "home"},
        "T04": {"activity": "searching", "location_type": "commercial"},
        "T05": {"activity": "leisure", "location_type": "home"},
        "T06": {"activity": "leisure", "location_type": "public"},
        "T07": {"activity": "socializing", "location_type": "bar"},
        "T08": {"activity": "leisure", "location_type": "home"},
        "T09": {"activity": "relaxing", "location_type": "home"},
        "T10": {"activity": "sleeping", "location_type": "home"},
    },
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
        # Emergency services
        "police": "police_day",
        "cop": "police_day",
        "officer": "police_day",
        "detective": "police_day",
        "enforcer": "police_night",
        "medic": "ambulance_day",
        "paramedic": "ambulance_day",
        "emt": "ambulance_night",
        "doctor": "clinic_doctor",
        "nurse": "clinic_doctor",
        "surgeon": "clinic_doctor",
        # Transport workers
        "driver": "transit_driver_day",
        "bus driver": "transit_driver_day",
        "tram operator": "transit_driver_day",
        "taxi": "transit_driver_night",
        "sanitation": "sanitation",
        "garbage collector": "sanitation",
        "street cleaner": "sanitation",
        "road worker": "infrastructure_night",
        "construction": "infrastructure_night",
        "repair tech": "infrastructure_night",
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
            # Weighted random schedule assignment based on realistic population distribution
            # This creates variety: some at work, some home, some wandering
            schedule_weights = [
                ("worker", 0.25),           # 25% - Standard workers with workplace
                ("office_worker", 0.12),    # 12% - Office workers with lunch breaks
                ("homebody", 0.12),         # 12% - Work from home / stay home
                ("early_bird", 0.08),       # 8% - Early risers, early to bed
                ("parent", 0.06),           # 6%  - Stay-at-home parents
                ("retiree", 0.05),          # 5%  - Retired, leisurely
                ("student", 0.05),          # 5%  - Students
                ("freelancer", 0.05),       # 5%  - Irregular hours
                ("unemployed", 0.03),       # 3%  - Wandering, searching
                ("fitness", 0.03),          # 3%  - Athletes, trainers
                # 24/7 Services (16% total - ensures city is always alive)
                ("police_day", 0.02),       # 2%  - Police day shift
                ("police_night", 0.02),     # 2%  - Police night shift
                ("ambulance_day", 0.015),   # 1.5% - EMT day shift
                ("ambulance_night", 0.015), # 1.5% - EMT night shift
                ("transit_driver_day", 0.02),   # 2% - Transport day shift
                ("transit_driver_night", 0.02), # 2% - Transport night shift
                ("security_night", 0.03),   # 3%  - Security guards
                ("sanitation", 0.01),       # 1%  - Garbage/cleaning
                ("infrastructure_night", 0.01), # 1% - Road repairs
            ]
            
            # Use seeded random to pick schedule based on NPC ID (deterministic)
            r = seeded_random(f"{npc.get('id', '')}_schedule")
            cumulative = 0
            schedule_type = "worker"  # Default fallback
            for sched, weight in schedule_weights:
                cumulative += weight
                if r < cumulative:
                    schedule_type = sched
                    break
    
    schedule = SCHEDULES.get(schedule_type, SCHEDULES["worker"])
    
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
    
    # Calculate needs state (deterministic decay based on tick)
    needs_state = calculate_needs(npc, tick)
    
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
        # New enriched data
        "age": npc.get("age"),
        "family": npc.get("family"),
        "appearance": npc.get("appearance"),
        "needs": needs_state,
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


@app.route("/api/npcs/all")
def list_all_npcs():
    """
    Get all NPCs with full profiles (from chunked data).
    Returns 800 NPCs with physical descriptions, alignment, etc.
    """
    limit = min(int(request.args.get("limit", 800)), 10000)
    npcs = get_npcs_from_chunks(max_npcs=limit)
    
    return jsonify({
        "npcs": npcs,
        "total": len(npcs),
        "schema": "full_profile",
        "version": "2.0.0"
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


# =============================================================================
# NEWS GENERATION
# =============================================================================

# News outlet definitions with biases
NEWS_OUTLETS = {
    "temple_herald": {
        "id": "NO01",
        "name": "Temple Herald",
        "bias": "pro_temple",
        "censored": True,
        "tone": "authoritative"
    },
    "chrome_wire": {
        "id": "NO02",
        "name": "Chrome Wire",
        "bias": "pro_business",
        "censored": False,
        "tone": "professional"
    },
    "neon_underground": {
        "id": "NO03",
        "name": "Neon Underground",
        "bias": "anti_authority",
        "censored": False,
        "tone": "gritty"
    },
    "undercity_voice": {
        "id": "NO04",
        "name": "The Undercity Voice",
        "bias": "pro_cyborg",
        "hidden": True,
        "tone": "revolutionary"
    }
}

# Article templates by type
NEWS_TEMPLATES = {
    "robbery": {
        "headlines": [
            "Break-in at {location}: {value} GEP Stolen",
            "{district} Residents Report Theft Wave",
            "Security Breach at {location} Leaves Merchants Shaken"
        ],
        "bodies": {
            "neutral": "Authorities report a break-in at {location} in the {district} district. Approximately {value} GEP worth of goods were stolen. Temple Guard forces are investigating.",
            "pro_temple": "Swift action by Temple security forces prevented a major theft at {location}. Citizens are reminded that the Temple protects all.",
            "anti_authority": "Another robbery rocks {location}, and once again Temple security arrives too late. 'They only protect the Spire,' said one witness."
        }
    },
    "hacking": {
        "headlines": [
            "Cyberattack Targets {location} Systems",
            "Hacker Breach at {location}: Data Exposed",
            "Digital Intrusion Rocks {district} Infrastructure"
        ],
        "bodies": {
            "neutral": "A cyberattack targeting {location} systems was detected. Technical teams are assessing the damage.",
            "pro_temple": "An attempted cyber-intrusion against {location} was quickly neutralized by Temple cybersecurity protocols.",
            "anti_authority": "Sources confirm that {location} was breached. Data exposure is likely significant. As usual, official statements downplay the severity."
        }
    },
    "police": {
        "headlines": [
            "Temple Guard Conducts Raid in {district}",
            "Inquisitors Apprehend Suspect in {district}",
            "Police Chase Through {district} Streets"
        ],
        "bodies": {
            "neutral": "Temple Guard units conducted an operation in {district} today. Officials cite ongoing investigations.",
            "pro_temple": "In a decisive action against criminal elements, Temple Inquisitors swept through {district}, apprehending suspects linked to illegal activities.",
            "anti_authority": "Witnesses describe a violent crackdown in {district} as Temple forces stormed buildings. The Cyborg Justice Society is demanding an investigation."
        }
    },
    "cyborg_attack": {
        "headlines": [
            "Cyborg Resident Attacked in {district}",
            "Tensions Rise as Synthetic Citizen Assaulted",
            "Cyborg Justice Society Condemns {district} Incident"
        ],
        "bodies": {
            "neutral": "An incident involving a synthetic citizen occurred in {district}. Details remain unclear.",
            "pro_temple": "An altercation in {district} involving a synthetic individual has been resolved. Authorities remind all residents that proper identification protocols apply equally.",
            "anti_authority": "BREAKING: Another brutal attack on a cyborg citizen in {district}. The victim was set upon by humans. Temple Guards arrived but made NO ARRESTS. These attacks are epidemic and the Temple does NOTHING."
        }
    },
    "fire": {
        "headlines": [
            "Blaze Engulfs {location} Building",
            "Fire Crews Battle {district} Inferno",
            "Emergency Response to {district} Fire"
        ],
        "bodies": {
            "neutral": "Fire crews responded to a blaze at {location} in {district} district. The fire has been contained.",
            "pro_temple": "Thanks to rapid response by Temple emergency services, a fire at {location} was quickly contained. No casualties reported.",
            "anti_authority": "Fire ravaged {location} overnight. Residents report waiting ages for emergency response. Infrastructure in {district} continues to deteriorate while Temple resources flow upward."
        }
    },
    "market": {
        "headlines": [
            "{district} Market Sees Price Surge",
            "Trade Disruption Affects {district} Vendors",
            "Economic Tensions in {district} District"
        ],
        "bodies": {
            "neutral": "Market analysts report price fluctuations in {district}. Merchants are adjusting to changes.",
            "pro_temple": "The Temple's economic stability measures continue to benefit {district} residents. Markets remain orderly.",
            "anti_authority": "Another day, another price hike in {district}. While corporations profit, working families struggle. The gap between Spire and Undercity widens."
        }
    }
}


def generate_news_article(event_type: str, tick: int, outlet_key: str, **kwargs) -> dict:
    """Generate a procedural news article."""
    outlet = NEWS_OUTLETS.get(outlet_key, NEWS_OUTLETS["neon_underground"])
    templates = NEWS_TEMPLATES.get(event_type, NEWS_TEMPLATES["market"])
    
    # Pick headline deterministically
    headline_idx = hash(f"{event_type}_{tick}") % len(templates["headlines"])
    headline_template = templates["headlines"][headline_idx]
    
    # Format with provided kwargs
    district = kwargs.get("district", "the district")
    location = kwargs.get("location", "an undisclosed location")
    value = kwargs.get("value", random.randint(100, 5000))
    
    headline = headline_template.format(
        district=district.replace("_", " ").title(),
        location=location,
        value=value
    )
    
    # Get body based on outlet bias
    bias = outlet.get("bias", "neutral")
    if bias == "pro_temple":
        body_key = "pro_temple"
    elif bias in ["anti_authority", "pro_cyborg"]:
        body_key = "anti_authority"
    else:
        body_key = "neutral"
    
    body_template = templates["bodies"].get(body_key, templates["bodies"]["neutral"])
    body = body_template.format(
        district=district.replace("_", " ").title(),
        location=location,
        value=value
    )
    
    # Apply censorship for Temple Herald
    if outlet.get("censored"):
        censorship = {
            "brutal": "",
            "violence": "disturbance",
            "attack": "incident",
            "NO ARRESTS": "investigation ongoing",
            "does NOTHING": "is investigating"
        }
        for term, replacement in censorship.items():
            headline = headline.replace(term, replacement)
            body = body.replace(term, replacement)
    
    time_info = get_time_info(tick)
    
    return {
        "id": f"NEWS_{tick}_{outlet['id']}_{event_type[:3].upper()}",
        "tick": tick,
        "day": time_info["day"],
        "time": f"{time_info['hour']:02d}:{time_info['minute']:02d}",
        "outlet": outlet["name"],
        "outlet_id": outlet["id"],
        "headline": headline,
        "body": body,
        "event_type": event_type,
        "district": district,
        "bias": bias
    }


@app.route("/api/news")
def get_news():
    """
    Get procedural news for a given tick.
    
    Query params:
    - tick: simulation tick (default: 100)
    - outlet: filter by outlet (temple_herald, chrome_wire, neon_underground, undercity_voice)
    - count: number of articles (default: 10, max: 50)
    """
    tick = int(request.args.get("tick", 100))
    outlet_filter = request.args.get("outlet")
    count = min(int(request.args.get("count", 10)), 50)
    
    articles = []
    
    # Generate news based on tick-seeded events
    event_types = ["robbery", "hacking", "police", "cyborg_attack", "fire", "market"]
    districts = ["undercity", "market_district", "temple_district", "hab_blocks", "industrial_ring"]
    locations = ["Market Hall", "Rusty Anchor", "Jade Tower", "Hab Block 7", "AutoFab Plant", "Drone Depot"]
    
    outlets_to_use = list(NEWS_OUTLETS.keys())
    if outlet_filter and outlet_filter in NEWS_OUTLETS:
        outlets_to_use = [outlet_filter]
    
    for i in range(count):
        # Deterministic selection based on tick
        seed = f"news_{tick}_{i}"
        event_idx = hash(seed) % len(event_types)
        district_idx = hash(f"{seed}_d") % len(districts)
        location_idx = hash(f"{seed}_l") % len(locations)
        outlet_idx = hash(f"{seed}_o") % len(outlets_to_use)
        
        event_type = event_types[event_idx]
        district = districts[district_idx]
        location = locations[location_idx]
        outlet_key = outlets_to_use[outlet_idx]
        
        # Undercity Voice only covers cyborg-related news
        if outlet_key == "undercity_voice" and event_type != "cyborg_attack":
            event_type = "cyborg_attack"
        
        article = generate_news_article(
            event_type,
            tick - i,  # Spread across recent ticks
            outlet_key,
            district=district,
            location=location,
            value=100 + (hash(f"{seed}_v") % 4900)
        )
        articles.append(article)
    
    return jsonify({
        "tick": tick,
        "time": get_time_info(tick),
        "articles": articles,
        "outlets": list(NEWS_OUTLETS.keys()),
        "count": len(articles)
    })


@app.route("/api/news/headlines")
def get_headlines():
    """Get latest headlines only."""
    tick = int(request.args.get("tick", 100))
    count = min(int(request.args.get("count", 5)), 20)
    
    headlines = []
    for i in range(count):
        seed = f"headline_{tick}_{i}"
        event_types = ["robbery", "hacking", "police", "cyborg_attack", "fire", "market"]
        event_type = event_types[hash(seed) % len(event_types)]
        outlet_key = list(NEWS_OUTLETS.keys())[hash(f"{seed}_o") % 4]
        
        article = generate_news_article(event_type, tick - i, outlet_key, district="undercity")
        headlines.append({
            "headline": article["headline"],
            "outlet": article["outlet"],
            "time": article["time"]
        })
    
    return jsonify({
        "tick": tick,
        "headlines": headlines
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


@app.route("/api/traffic")
def get_traffic():
    """
    Get traffic and street activity for a tick.
    Returns vehicles, public transport, emergency services active at this time.
    """
    tick = int(request.args.get("tick", 100))
    time_info = get_time_info(tick)
    time_period = time_info["period"]
    hour = time_info["hour"]
    
    # Traffic density by time period (0.0-1.0)
    TRAFFIC_DENSITY = {
        "T01": 0.05,  # 00:00-02:30 - Dead of night
        "T02": 0.03,  # 02:30-05:00 - Absolute minimum
        "T03": 0.35,  # 05:00-07:00 - Early commute
        "T04": 0.80,  # 07:00-10:00 - Morning rush
        "T05": 0.50,  # 10:00-12:00 - Mid-morning
        "T06": 0.65,  # 12:00-14:00 - Lunch movement
        "T07": 0.85,  # 14:00-17:00 - Evening rush peak
        "T08": 0.55,  # 17:00-19:00 - Post-work
        "T09": 0.25,  # 19:00-22:00 - Evening
        "T10": 0.10,  # 22:00-midnight - Night owls
    }
    
    density = TRAFFIC_DENSITY.get(time_period, 0.3)
    
    # Calculate number of vehicles visible (base of 20 at full density)
    base_vehicles = 20
    num_vehicles = int(base_vehicles * density)
    
    # Vehicle types and their activity at different times
    def generate_vehicles(tick, count):
        vehicles = []
        for i in range(count):
            seed = f"vehicle_{tick}_{i}"
            r = seeded_random(seed)
            
            # Vehicle type distribution changes by time
            is_night = time_period in ["T01", "T02", "T10"]
            
            if is_night:
                # Night: More taxis, less private cars
                if r < 0.40:
                    vtype = "taxi"
                elif r < 0.60:
                    vtype = "personal_car"
                elif r < 0.75:
                    vtype = "delivery_drone"
                elif r < 0.90:
                    vtype = "cargo_truck"
                else:
                    vtype = "motorcycle"
            else:
                # Day: More varied traffic
                if r < 0.50:
                    vtype = "personal_car"
                elif r < 0.65:
                    vtype = "taxi"
                elif r < 0.75:
                    vtype = "bus"
                elif r < 0.85:
                    vtype = "delivery_drone"
                elif r < 0.95:
                    vtype = "cargo_truck"
                else:
                    vtype = "motorcycle"
            
            # Random position on major routes
            routes = ["main_arterial", "market_ring", "hab_access", "temple_road"]
            route = seeded_choice(routes, f"{seed}_route")
            
            vehicles.append({
                "id": f"V_{tick}_{i:03d}",
                "type": vtype,
                "route": route,
                "position": seeded_random(f"{seed}_pos"),
            })
        return vehicles
    
    vehicles = generate_vehicles(tick, num_vehicles)
    
    # Public transport - always running (reduced at night)
    def get_public_transport(tick, time_period):
        transports = []
        is_night = time_period in ["T01", "T02", "T10"]
        
        # Tram Line 1 - Central Loop (24h)
        transports.append({
            "id": "TRAM_L1",
            "name": "Central Loop",
            "type": "tram",
            "current_stop": seeded_choice(
                ["Jade Tower", "Market Hall", "Temple", "Hab Blocks"],
                f"tram1_{tick}"
            ),
            "passengers": int(60 * density * (0.3 if is_night else 1)),
        })
        
        # Tram Line 2 - Undercity (not at night)
        if not is_night:
            transports.append({
                "id": "TRAM_L2",
                "name": "Undercity Express",
                "type": "tram",
                "current_stop": seeded_choice(
                    ["Apartments", "Rusty Anchor", "Drone Depot", "Tunnels"],
                    f"tram2_{tick}"
                ),
                "passengers": int(50 * density),
            })
        
        # Night Bus (night only)
        if is_night:
            transports.append({
                "id": "BUS_NIGHT",
                "name": "Night Owl Service",
                "type": "bus",
                "current_stop": seeded_choice(
                    ["Rusty Anchor", "Hab Blocks", "Jade Tower", "Apartments"],
                    f"nightbus_{tick}"
                ),
                "passengers": int(15 * density * 3),  # Night riders
            })
        else:
            # Day bus routes
            transports.append({
                "id": "BUS_A",
                "name": "Market Shuttle",
                "type": "bus",
                "current_stop": seeded_choice(
                    ["Market Hall", "AutoFab", "Recycling", "Temple Outpost"],
                    f"busa_{tick}"
                ),
                "passengers": int(30 * density),
            })
        
        return transports
    
    public_transport = get_public_transport(tick, time_period)
    
    # Emergency services - always present, more at night
    def get_emergency_vehicles(tick, time_period):
        emergency = []
        is_night = time_period in ["T01", "T02", "T10"]
        
        # Police cruisers - more at night
        num_police = 3 if is_night else 2
        for i in range(num_police):
            districts = ["undercity", "market_district", "temple_district", "hab_blocks"]
            emergency.append({
                "id": f"POLICE_{i+1}",
                "type": "police_cruiser",
                "activity": "patrolling",
                "district": seeded_choice(districts, f"police_{tick}_{i}"),
                "responding": seeded_random(f"police_resp_{tick}_{i}") < 0.1,
            })
        
        # Ambulance - always one on duty
        emergency.append({
            "id": "AMB_01",
            "type": "ambulance",
            "activity": seeded_choice(["standby", "responding", "returning"], f"amb_{tick}"),
            "stationed_at": "Clinic",
            "responding": seeded_random(f"amb_resp_{tick}") < 0.08,
        })
        
        # Night specific: garbage truck, road repair
        if is_night and time_period in ["T02", "T03"]:
            emergency.append({
                "id": "SANITATION_01",
                "type": "garbage_truck",
                "activity": "collecting",
                "district": seeded_choice(["market_district", "hab_blocks"], f"garb_{tick}"),
            })
        
        if is_night and time_period in ["T01", "T02"]:
            emergency.append({
                "id": "REPAIR_01",
                "type": "construction_vehicle",
                "activity": "road_repair",
                "location": seeded_choice(["main_arterial", "market_ring"], f"repair_{tick}"),
            })
        
        return emergency
    
    emergency_vehicles = get_emergency_vehicles(tick, time_period)
    
    # Street NPCs (vendors, guards, etc.)
    def get_street_npcs(tick, time_period, density):
        street_npcs = []
        is_day = time_period in ["T04", "T05", "T06", "T07", "T08"]
        is_night = time_period in ["T01", "T02", "T10"]
        
        # Street vendors (day only)
        if is_day:
            for i in range(3):
                street_npcs.append({
                    "type": "street_vendor",
                    "activity": "selling",
                    "location": seeded_choice(
                        ["Market Hall entrance", "Jade Tower plaza", "Temple steps"],
                        f"vendor_{tick}_{i}"
                    ),
                })
        
        # Patrol guards (night shift)
        if is_night:
            for i in range(2):
                street_npcs.append({
                    "type": "security_patrol",
                    "activity": "patrolling",
                    "location": seeded_choice(
                        ["Undercity streets", "Hab Block perimeter", "Market alleys"],
                        f"guard_{tick}_{i}"
                    ),
                })
        
        # Random pedestrians (based on density)
        num_pedestrians = int(20 * density)
        for i in range(num_pedestrians):
            street_npcs.append({
                "type": "pedestrian",
                "activity": seeded_choice(["walking", "waiting", "talking"], f"ped_{tick}_{i}"),
                "location": seeded_choice(
                    ["sidewalk", "crosswalk", "plaza", "bus_stop"],
                    f"pedloc_{tick}_{i}"
                ),
            })
        
        return street_npcs
    
    street_npcs = get_street_npcs(tick, time_period, density)
    
    return jsonify({
        "tick": tick,
        "time": time_info,
        "traffic_density": density,
        "traffic_level": "dead" if density < 0.1 else "light" if density < 0.3 else "moderate" if density < 0.6 else "heavy",
        "vehicles": {
            "count": len(vehicles),
            "list": vehicles,
        },
        "public_transport": {
            "count": len(public_transport),
            "services": public_transport,
        },
        "emergency_services": {
            "count": len(emergency_vehicles),
            "vehicles": emergency_vehicles,
        },
        "street_activity": {
            "pedestrian_density": density * 0.8,
            "npcs_visible": len(street_npcs),
            "npcs": street_npcs[:20],  # Limit response size
        },
    })


@app.route("/api/transport")
def get_transport_endpoint():
    """Get transportation system data."""
    return jsonify(get_transport())


# =============================================================================
# SOCIAL DYNAMICS API
# =============================================================================

# Import social dynamics module
import sys
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

try:
    from social_dynamics import (
        get_npc_social_summary, 
        get_reputation,
        find_potential_groups,
        track_meeting,
        update_trust_from_interaction,
        get_relationship_type,
        RELATIONSHIP_THRESHOLDS,
        MEETING_THRESHOLDS
    )
    SOCIAL_DYNAMICS_AVAILABLE = True
except ImportError:
    SOCIAL_DYNAMICS_AVAILABLE = False


@app.route("/api/social/npc/<npc_id>")
def get_npc_social(npc_id):
    """
    Get social summary for an NPC.
    Returns friends, colleagues, acquaintances, rivals.
    """
    if not SOCIAL_DYNAMICS_AVAILABLE:
        return jsonify({"error": "Social dynamics module not available"}), 500
    
    npcs = get_npcs()
    npc = next((n for n in npcs if n.get("id") == npc_id), None)
    
    if not npc:
        return jsonify({"error": f"NPC {npc_id} not found"}), 404
    
    # Get or initialize relationships based on family/workplace
    if "relationships" not in npc:
        npc["relationships"] = {}
        
        # Initialize family relationships
        family = npc.get("family", {})
        if family.get("spouse_id"):
            npc["relationships"][family["spouse_id"]] = {
                "trust": 0.9, "meetings": 100, "type": "close_friend", 
                "contexts": ["family"]
            }
        for parent_id in family.get("parent_ids", []):
            npc["relationships"][parent_id] = {
                "trust": 0.85, "meetings": 200, "type": "close_friend",
                "contexts": ["family"]
            }
        for sibling_id in family.get("sibling_ids", []):
            npc["relationships"][sibling_id] = {
                "trust": 0.75, "meetings": 150, "type": "friend",
                "contexts": ["family"]
            }
        
        # Initialize workplace relationships
        workplace = npc.get("workplace")
        if workplace:
            coworkers = [n for n in npcs if n.get("workplace") == workplace 
                        and n["id"] != npc_id]
            for coworker in coworkers[:10]:
                if coworker["id"] not in npc["relationships"]:
                    # Random-ish initial trust based on IDs
                    seed = f"{npc_id}_{coworker['id']}"
                    h = int(hashlib.md5(seed.encode()).hexdigest(), 16) % 100
                    initial_trust = 0.3 + (h / 200)  # 0.3-0.8
                    meetings = 10 + (h % 30)
                    npc["relationships"][coworker["id"]] = {
                        "trust": initial_trust, 
                        "meetings": meetings,
                        "type": get_relationship_type(initial_trust),
                        "contexts": ["workplace"]
                    }
    
    summary = get_npc_social_summary(npc)
    
    return jsonify({
        "npc_id": npc_id,
        "name": npc.get("name"),
        "social": summary,
        "thresholds": {
            "trust_levels": RELATIONSHIP_THRESHOLDS,
            "meeting_requirements": MEETING_THRESHOLDS,
        }
    })


@app.route("/api/social/groups")
def get_social_groups():
    """
    Get all social groups (coworkers, neighbors, faction cells).
    Optional: ?workplace=<id> or ?building=<id> to filter.
    """
    if not SOCIAL_DYNAMICS_AVAILABLE:
        return jsonify({"error": "Social dynamics module not available"}), 500
    
    npcs = get_npcs()
    tick = int(request.args.get("tick", 100))
    workplace_filter = request.args.get("workplace")
    building_filter = request.args.get("building")
    
    groups = find_potential_groups(npcs, tick)
    
    # Filter if requested
    if workplace_filter:
        groups = [g for g in groups if workplace_filter in g.meeting_location]
    if building_filter:
        groups = [g for g in groups if building_filter in g.meeting_location]
    
    return jsonify({
        "tick": tick,
        "groups_count": len(groups),
        "groups": [g.to_dict() for g in groups[:50]],  # Limit response
        "group_types": {
            "coworkers": len([g for g in groups if g.group_type == "coworkers"]),
            "neighbors": len([g for g in groups if g.group_type == "neighbors"]),
            "faction_cell": len([g for g in groups if g.group_type == "faction_cell"]),
        }
    })


@app.route("/api/social/reputation/<npc_id>")
def get_npc_reputation(npc_id):
    """
    Get an NPC's reputation across the city.
    """
    if not SOCIAL_DYNAMICS_AVAILABLE:
        return jsonify({"error": "Social dynamics module not available"}), 500
    
    npcs = get_npcs()
    npc = next((n for n in npcs if n.get("id") == npc_id), None)
    
    if not npc:
        return jsonify({"error": f"NPC {npc_id} not found"}), 404
    
    reputation = get_reputation(npc, npcs)
    
    return jsonify({
        "npc_id": npc_id,
        "name": npc.get("name"),
        "reputation": reputation,
    })


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
# STUDIORAM SCENE GENERATION
# =============================================================================

# Lazy import to avoid loading Vertex AI unless needed
_scene_generator = None

def get_scene_generator():
    """Lazy-load the scene generator."""
    global _scene_generator
    if _scene_generator is None:
        try:
            from studioram.scene_generator import SceneGenerator
            _scene_generator = SceneGenerator(world_id="signal-noir")
        except ImportError as e:
            print(f"StudioRam not available: {e}")
            return None
    return _scene_generator


@app.route("/api/generate/portrait/<npc_id>", methods=["POST"])
def generate_portrait(npc_id):
    """
    Generate a portrait for an NPC.
    
    POST /api/generate/portrait/NPC_00001
    
    Returns: { "image_url": "path/to/image.png", "prompt": "..." }
    """
    gen = get_scene_generator()
    if not gen:
        return jsonify({"error": "Scene generator not available"}), 503
    
    # Find NPC
    npcs = get_npcs()
    npc = next((n for n in npcs if n["id"] == npc_id), None)
    if not npc:
        return jsonify({"error": f"NPC {npc_id} not found"}), 404
    
    try:
        result = gen.generate_portrait(npc, save=True)
        return jsonify({
            "npc_id": npc_id,
            "npc_name": npc["name"],
            "image_path": result,
            "status": "generated"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/generate/scene", methods=["POST"])
def generate_scene():
    """
    Generate a scene with NPCs.
    
    POST /api/generate/scene
    Body: {
        "npc_ids": ["NPC_00001", "NPC_00002"],
        "location": "Neon bar in undercity",
        "action": "tense negotiation",
        "time_of_day": "night",
        "weather": "rain"
    }
    
    Returns: { "image_url": "path/to/scene.png", "prompt": "..." }
    """
    gen = get_scene_generator()
    if not gen:
        return jsonify({"error": "Scene generator not available"}), 503
    
    data = request.get_json() or {}
    npc_ids = data.get("npc_ids", [])
    location = data.get("location", "Street in the undercity")
    action = data.get("action", "meeting")
    time_of_day = data.get("time_of_day", "night")
    weather = data.get("weather", "rain")
    
    # Find NPCs
    all_npcs = get_npcs()
    npcs = [n for n in all_npcs if n["id"] in npc_ids]
    
    if not npcs:
        return jsonify({"error": "No valid NPCs found"}), 400
    
    try:
        result = gen.generate_scene(
            npcs=npcs,
            location=location,
            action=action,
            time_of_day=time_of_day,
            weather=weather,
            save=True
        )
        return jsonify({
            "npc_ids": [n["id"] for n in npcs],
            "npc_names": [n["name"] for n in npcs],
            "location": location,
            "action": action,
            "image_path": result,
            "status": "generated"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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

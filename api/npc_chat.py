"""
AO World Engine - NPC Chat API
Secure Vertex AI proxy for RE:ECHO NPC conversations + Signal Noir image generation.

NOW WITH ARWEAVE INTEGRATION - NPCs fetched dynamically, not hardcoded!

Deploy to Cloud Run:
  gcloud run deploy ao-npc-chat --source . --region us-central1 --allow-unauthenticated

Local dev:
  python3 npc_chat.py
"""
import os
import base64
import json
import hashlib
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

# Import event engine for deterministic memories
try:
    from event_engine import get_npc_memory_context, get_events_before_tick, get_relationship_at_tick
    HAS_EVENT_ENGINE = True
except ImportError:
    HAS_EVENT_ENGINE = False
    print("⚠️ Event engine not available - memories disabled")

app = Flask(__name__)
CORS(app)

# Vertex AI setup
HAS_VERTEX = False
model = None

try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    
    project = os.environ.get("GCP_PROJECT", "your-gcp-project")
    location = os.environ.get("GCP_LOCATION", "us-central1")
    
    vertexai.init(project=project, location=location)
    model = GenerativeModel("gemini-2.0-flash")
    HAS_VERTEX = True
except Exception as e:
    print(f"⚠️ Vertex AI not available: {e}")
    print("   Running in mock mode with simple responses")

# Imagen 3 for image generation
HAS_IMAGEN = False
imagen_model = None

try:
    from vertexai.preview.vision_models import ImageGenerationModel
    imagen_model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-002")
    HAS_IMAGEN = True
    print("✅ Imagen 3 loaded for scene generation")
except Exception as e:
    print(f"⚠️ Imagen 3 not available: {e}")


# ============================================================
# ARWEAVE INTEGRATION
# ============================================================
# 
# PIPELINE:
#   1. NPC profiles stored on Arweave (via Turbo/ar.io bundler for <100KB free tier)
#   2. This API fetches from arweave.net gateway
#   3. Deterministic naming generates children, marriages, etc on-demand
#
# UPLOAD PIPELINE (wandern-arweave-uploader):
#   - Uses Turbo bundler (ar.io / up.arweave.net) for uploads
#   - <100KB uploads are FREE on mainnet (permanent)
#   - Tags make data searchable via GraphQL
#
# ============================================================

ARWEAVE_GATEWAY = "https://arweave.net"
NPC_SCHEMA_TX = "XmlqPa1RNFvipxnvyZTgbpx8EjOZNzNNI2tMGjQ3eb4"  # NPC semantic profile schema

# Cache for Arweave data
_arweave_cache = {}

# ============================================================
# ARWEAVE NPC MANIFEST (v2 — Feb 7, 2026)
# Maps NPC keys to their Arweave transaction IDs.
# These contain the authoritative NPC profiles with visual_description.
# ============================================================
ARWEAVE_NPC_MANIFEST = {
    "charlie":     "4kb-Bvt09W6P0tCniah5TKqsH2zWDh3t1FPV3bT7gBA",
    "kai_vance":   "hiIkaRGy-vM1Cci0IWI00VD0PQNWM16eC0wCoQG86mM",
    "orion_thane": "3xAl_fc0aW0FUoWBFAB_Oy3INgM3GbS0-BIEHfQ0EqE",
    "felix":       "9RbavjqW5jj9-sWQ0BykASifxUh9DndwzvN__SwGFVs",
    "nova_chen":   "eJ2KY1IqaZysc2JGoUepIfU_LPtm1_aPpV1DYJGxSmg",
    "selene_voss": "jvqTcsbbZFt3CECQ37X0dBcBOzIr__gZSALSwa_g0gg",
    "sister_mira": "sBAziTAsAPY1I5Vrrg0LYKaijKxPA00FbMcznqw5h-0",
    "mama_indira": "Th4jyQm1cTQ2dgMrOTPbdLmSsYTzYr2UC1UbU_ObDHk",
    "aiche":       "HCpXNWCkExgx_SuBGqkKDGCupwGb9pdkSJ7ntrHr-4A",
    "pixel":       "B8wwR97xFlFdMqp01dWC8-b6ROZ2xxjFbi9jJXElTtw",
    "cipher":      "w9hkoBiYURWnHPCyZaHjsHAV_LrDz3QAw1eo2dT_q2g",
    "zero_chen":   "Nh1OzZXGh_lx6WLTAapK1Z2JgquGwHK707BGlhE-oGk",
}

# ============================================================
# ARWEAVE CODEC MANIFEST (Feb 7, 2026)
# Maps codec chunks to Arweave tx IDs for future retrieval.
# For now we read from local files; manifest enables Arweave-first later.
# ============================================================
import logging

_codec_data_cache = {}
CODEC_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'codec_chunks')

ARWEAVE_CODEC_MANIFEST = {}
_codec_manifest_path = os.path.join(os.path.dirname(__file__), 'arweave_codec_manifest.json')
if not os.path.exists(_codec_manifest_path):
    _codec_manifest_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'arweave_codec_manifest.json')
if os.path.exists(_codec_manifest_path):
    try:
        with open(_codec_manifest_path) as f:
            _manifest_data = json.load(f)
        for item in _manifest_data.get("results", []):
            if item.get("success") and item.get("tx_id"):
                ARWEAVE_CODEC_MANIFEST[item["filename"]] = item["tx_id"]
        logging.info(f"[CODEC] Loaded {len(ARWEAVE_CODEC_MANIFEST)} codec Arweave tx_ids")
    except Exception as e:
        logging.warning(f"[CODEC] Failed to load codec manifest: {e}")


def load_codec_chunk(filename: str) -> dict | None:
    """Load a codec chunk — tries Arweave first, falls back to local file."""
    if filename in _codec_data_cache:
        return _codec_data_cache[filename]
    
    # Try Arweave if tx_id exists
    tx_id = ARWEAVE_CODEC_MANIFEST.get(filename)
    if tx_id:
        arweave_data = fetch_from_arweave(tx_id)
        if arweave_data:
            _codec_data_cache[filename] = arweave_data
            logging.info(f"[CODEC] Loaded {filename} from Arweave ({tx_id[:12]}...)")
            return arweave_data
    
    # Fall back to local file
    local_path = os.path.join(CODEC_DIR, filename)
    if os.path.exists(local_path):
        try:
            with open(local_path) as f:
                data = json.load(f)
            _codec_data_cache[filename] = data
            logging.info(f"[CODEC] Loaded {filename} from local file")
            return data
        except Exception as e:
            logging.error(f"[CODEC] Failed to load {filename}: {e}")
    
    return None


def build_world_context() -> str:
    """Build WORLD FACTS dynamically from codec lore data — NOT hardcoded."""
    lore = load_codec_chunk("world_codec_05_lore.json")
    if not lore:
        return ""
    
    lines = ["\n\nWORLD FACTS (from city records — NEVER accept contradictions):"]
    
    # History: extract eras and key dates
    history = lore.get("history", {})
    the_fall = history.get("the_fall", {})
    eras = history.get("eras", {})
    
    # Pre-Fall era
    pre_fall = eras.get("pre_fall", {})
    if pre_fall:
        lines.append(f"- Pre-Fall era ({pre_fall.get('years', '?')}): {pre_fall.get('desc', '')}")
        for evt in pre_fall.get("events", []):
            lines.append(f"  - {evt.get('year', '?')}: {evt.get('event', '')}")
    
    # Dark Years
    dark_years = eras.get("dark_years", {})
    if dark_years:
        lines.append(f"- Dark Years ({dark_years.get('years', '?')}): {dark_years.get('desc', '')}")
        for evt in dark_years.get("events", []):
            lines.append(f"  - {evt.get('year', '?')}: {evt.get('event', '')}")
    
    # The Fall details
    if the_fall:
        lines.append(f"- The Fall: Official story = {the_fall.get('official_story', '?')}")
    
    # Layer lore
    layer_lore = lore.get("layer_lore", {})
    layers = layer_lore.get("layers", {})
    if layers:
        lines.append("- Reality Layers:")
        for layer_key in sorted(layers.keys()):
            layer = layers[layer_key]
            lines.append(f"  - {layer.get('name', '?')}: {layer.get('desc', '')} (access: {layer.get('accessibility', '?')})")
    
    return "\n".join(lines)


def build_faction_roster(npc_profiles: dict) -> str:
    """Build FACTION ROSTER dynamically from codec + NPC profile data — NOT hardcoded."""
    lore = load_codec_chunk("world_codec_05_lore.json")
    
    lines = ["\nFACTION ROSTER (from city intelligence — you know these affiliations):"]
    
    if lore:
        factions = lore.get("factions_detailed", {})
        for faction_key, faction_data in factions.items():
            name = faction_data.get("full_name", faction_key.title())
            goal = faction_data.get("goal", "")
            leader = faction_data.get("leader", "unknown")
            members = faction_data.get("key_members", [])
            
            # Resolve NPC IDs to display names
            leader_name = npc_profiles.get(leader, {}).get("name", leader.replace("_", " ").title()) if leader and not leader.startswith("Board") and not leader.startswith("No ") and not leader.startswith("Prophet") else leader
            member_names = [npc_profiles.get(m, {}).get("name", m.replace("_", " ").title()) for m in members]
            
            line = f"- {name.upper()}: Goal: {goal}."
            if leader_name:
                line += f" Leader: {leader_name}."
            if member_names:
                line += f" Key members: {', '.join(member_names)}."
            
            # Add role annotations from NPC profiles
            for member_id in [leader] + members:
                if member_id in npc_profiles:
                    p = npc_profiles[member_id]
                    archetype = p.get("archetype", "")
                    if archetype:
                        line += f" ({p.get('name', member_id)}: {archetype})"
            
            lines.append(line)
    else:
        # Fallback: build from NPC faction fields
        faction_groups = {}
        for npc_id, profile in npc_profiles.items():
            faction = profile.get("faction", "Unknown")
            if faction not in faction_groups:
                faction_groups[faction] = []
            name = profile.get("name", npc_id)
            archetype = profile.get("archetype", "")
            faction_groups[faction].append(f"{name} ({archetype})" if archetype else name)
        
        for faction, members in sorted(faction_groups.items()):
            lines.append(f"- {faction.upper()}: {', '.join(members)}")
    
    return "\n".join(lines)


# ============================================================
# CONVERSATION MEMORY SYSTEM
# ============================================================
# 
# Persistent memory storage using npc_memory.py
# - Saves to JSON files in data/memories/
# - Survives server restarts  
# - Ready for Arweave archival
# ============================================================

try:
    from npc_memory import (
        get_memory,
        remember_user,
        get_user_info,
        get_conversation_history,
        add_to_conversation
    )
    HAS_PERSISTENT_MEMORY = True
    print("✅ Persistent memory system loaded")
except ImportError:
    HAS_PERSISTENT_MEMORY = False
    print("⚠️ Persistent memory not available - using in-memory fallback")
    
    # Fallback in-memory storage
    _conversation_memory = {}
    _user_info = {}
    
    def get_conversation_history(user_id: str, npc_id: str, max_messages: int = 20) -> list:
        key = f"{user_id}:{npc_id}"
        history = _conversation_memory.get(key, [])
        return history[-max_messages:]
    
    def add_to_conversation(user_id: str, npc_id: str, role: str, content: str, tick: int):
        key = f"{user_id}:{npc_id}"
        if key not in _conversation_memory:
            _conversation_memory[key] = []
        _conversation_memory[key].append({"role": role, "content": content, "tick": tick})
        if len(_conversation_memory[key]) > 50:
            _conversation_memory[key] = _conversation_memory[key][-50:]
    
    def remember_user(user_id: str, name: str, tick: int):
        if user_id not in _user_info:
            _user_info[user_id] = {"name": name, "first_seen_tick": tick}
        else:
            _user_info[user_id]["name"] = name
    
    def get_user_info(user_id: str) -> dict:
        return _user_info.get(user_id, {"name": None, "first_seen_tick": None})


# ============================================================
# SCHEDULE-BASED NPC LOCATIONS
# ============================================================
#
# NPCs follow their schedules from world_codec_14_behaviors.json
# Given any tick, we can determine:
# - What time period (T01-T10)
# - What activity they're doing
# - Where they are
# ============================================================

# Time period mapping: 24 ticks = 1 game hour, 240 ticks = 1 day
TIME_PERIODS = {
    "T01": {"name": "deep_night", "tick_range": (0, 24)},      # 00:00-01:00
    "T02": {"name": "early_morning", "tick_range": (24, 72)},  # 01:00-03:00
    "T03": {"name": "morning", "tick_range": (72, 120)},       # 03:00-05:00
    "T04": {"name": "noon", "tick_range": (120, 168)},         # 05:00-07:00 (shifted for dystopia)
    "T05": {"name": "afternoon", "tick_range": (168, 192)},    # 07:00-08:00
    "T06": {"name": "dusk", "tick_range": (192, 204)},         # 08:00-08:30
    "T07": {"name": "evening", "tick_range": (204, 216)},      # 08:30-09:00
    "T08": {"name": "night", "tick_range": (216, 228)},        # 09:00-09:30
    "T09": {"name": "late_night", "tick_range": (228, 236)},   # 09:30-09:50
    "T10": {"name": "dead_hour", "tick_range": (236, 240)},    # 09:50-10:00
}

# Default schedules for different archetypes
NPC_SCHEDULES = {
    "resistance_fighter": {
        "T01": {"activity": "patrol_or_sleep", "location": "resistance_hideout"},
        "T02": {"activity": "training", "location": "resistance_hideout"},
        "T03": {"activity": "intelligence_gathering", "location": "neon_market"},
        "T04": {"activity": "meeting", "location": "resistance_hideout"},
        "T05": {"activity": "mission", "location": "varies"},
        "T06": {"activity": "mission", "location": "varies"},
        "T07": {"activity": "safehouse_return", "location": "resistance_hideout"},
        "T08": {"activity": "debriefing", "location": "resistance_hideout"},
        "T09": {"activity": "personal_time", "location": "neon_bar"},
        "T10": {"activity": "sleep_or_watch", "location": "resistance_hideout"},
    },
    "street_oracle": {
        "T01": {"activity": "sleeping", "location": "neon_market"},
        "T02": {"activity": "meditation", "location": "rooftop"},
        "T03": {"activity": "visions", "location": "layer_tear"},
        "T04": {"activity": "readings", "location": "neon_market"},
        "T05": {"activity": "readings", "location": "neon_market"},
        "T06": {"activity": "wandering", "location": "rain_soaked_alley"},
        "T07": {"activity": "trading", "location": "neon_market"},
        "T08": {"activity": "socializing", "location": "neon_bar"},
        "T09": {"activity": "commune_with_watchers", "location": "rooftop"},
        "T10": {"activity": "sleeping", "location": "neon_market"},
    },
    "info_broker": {
        "T01": {"activity": "closing_bar", "location": "neon_bar"},
        "T02": {"activity": "sleeping", "location": "neon_bar"},
        "T03": {"activity": "sleeping", "location": "neon_bar"},
        "T04": {"activity": "inventory", "location": "neon_bar"},
        "T05": {"activity": "opening_bar", "location": "neon_bar"},
        "T06": {"activity": "serving", "location": "neon_bar"},
        "T07": {"activity": "serving", "location": "neon_bar"},
        "T08": {"activity": "peak_hours", "location": "neon_bar"},
        "T09": {"activity": "peak_hours", "location": "neon_bar"},
        "T10": {"activity": "late_night_deals", "location": "neon_bar"},
    },
    "default": {
        "T01": {"activity": "sleeping", "location": "home"},
        "T02": {"activity": "sleeping", "location": "home"},
        "T03": {"activity": "waking", "location": "home"},
        "T04": {"activity": "working", "location": "workplace"},
        "T05": {"activity": "working", "location": "workplace"},
        "T06": {"activity": "commuting", "location": "transit"},
        "T07": {"activity": "leisure", "location": "neon_bar"},
        "T08": {"activity": "socializing", "location": "neon_bar"},
        "T09": {"activity": "returning_home", "location": "transit"},
        "T10": {"activity": "sleeping", "location": "home"},
    }
}

# Map NPC IDs to their schedule types
NPC_SCHEDULE_TYPES = {
    "charlie": "resistance_fighter",
    "zero_chen": "resistance_fighter",
    "kai_vance": "resistance_fighter",
    "kira": "street_oracle",
    "felix": "info_broker",
    "pixel": "resistance_fighter",
    "nova_chen": "default",
    "aiche": "default",
    "sister_mira": "default",
}

def get_time_period(tick: int) -> str:
    """Convert tick to time period (T01-T10)."""
    day_tick = tick % 240  # 240 ticks per day
    
    for period, info in TIME_PERIODS.items():
        start, end = info["tick_range"]
        if start <= day_tick < end:
            return period
    
    return "T01"  # Default

def get_scheduled_location(npc_id: str, tick: int) -> tuple:
    """Get NPC's scheduled location and activity at tick.
    
    Returns: (location, activity)
    """
    time_period = get_time_period(tick)
    schedule_type = NPC_SCHEDULE_TYPES.get(npc_id, "default")
    schedule = NPC_SCHEDULES.get(schedule_type, NPC_SCHEDULES["default"])
    
    slot = schedule.get(time_period, {"activity": "unknown", "location": "unknown"})
    
    # Handle 'varies' locations with deterministic choice
    location = slot["location"]
    if location == "varies":
        locations = ["neon_market", "rain_soaked_alley", "shadow_grid", "rooftop"]
        loc_seed = int(hashlib.md5(f"{npc_id}_{tick // 10}".encode()).hexdigest(), 16)
        location = locations[loc_seed % len(locations)]
    elif location == "home":
        # Use NPC's home location
        profile = FOUNDING_NPCS.get(npc_id, {})
        location = profile.get("location_home", "neon_market")
    
    return location, slot["activity"]


def fetch_from_arweave(tx_id: str) -> dict:
    """Fetch JSON data from Arweave."""
    if tx_id in _arweave_cache:
        return _arweave_cache[tx_id]
    
    try:
        response = requests.get(f"{ARWEAVE_GATEWAY}/{tx_id}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            _arweave_cache[tx_id] = data
            return data
    except Exception as e:
        print(f"⚠️ Arweave fetch failed for {tx_id}: {e}")
    
    return None


def query_arweave_npcs(app_name: str = "AO-World-Engine") -> list:
    """
    Query Arweave for all NPC profiles via GraphQL.
    
    This searches for transactions tagged with:
    - App-Name: AO-World-Engine (or your app name)
    - Type: npc_profile
    """
    query = """
    {
        transactions(
            tags: [
                { name: "App-Name", values: ["%s"] },
                { name: "Type", values: ["npc_profile"] }
            ]
            first: 100
        ) {
            edges {
                node {
                    id
                    tags {
                        name
                        value
                    }
                }
            }
        }
    }
    """ % app_name
    
    try:
        response = requests.post(
            f"{ARWEAVE_GATEWAY}/graphql",
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        data = response.json()
        npcs = []
        
        for edge in data.get("data", {}).get("transactions", {}).get("edges", []):
            node = edge["node"]
            tags = {t["name"]: t["value"] for t in node["tags"]}
            
            npcs.append({
                "tx_id": node["id"],
                "npc_id": tags.get("NPC-Id", "unknown"),
                "name": tags.get("NPC-Name", "Unknown"),
                "archetype": tags.get("Archetype", "unknown")
            })
        
        return npcs
    except Exception as e:
        print(f"⚠️ Arweave GraphQL query failed: {e}")
        return []


# ============================================================
# FOUNDING NPC PROFILES
# 12 Founders (4 Male / 8 Female) - scientifically designed for
# genetic diversity based on minimum viable population research.
# See data/founding_npcs.py for full profiles.
# ============================================================

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    # Try local import first (for Cloud Run deployment)
    from founding_npcs import FOUNDING_NPCS, LOCATIONS
except ImportError:
    try:
        # Then try package import (for local dev)
        from data.founding_npcs import FOUNDING_NPCS, LOCATIONS
    except ImportError:
        # Fallback if import fails (e.g., running from different directory)
        FOUNDING_NPCS = {
            "kira": {
                "id": "npc_0002",
                "name": "Kira Ōmura",
                "gender": "female",
                "archetype": "Street Oracle",
                "personality_vector": {"paranoia": 0.8, "mysticism": 0.9, "aggression": 0.2},
                "location_home": "neon_market",
                "topic_weights": {"philosophy": 0.9, "the_watchers": 0.95, "trade": 0.2},
                "catchphrases": ["The layers stack. We're just one echo.", "Eyes from outside the frame..."],
            },
            "cipher": {
                "id": "npc_0001",
                "name": "Cipher",
                "gender": "male",
                "archetype": "AI Hacker Entity",
                "personality_vector": {"paranoia": 0.6, "mysticism": 0.3, "aggression": 0.4},
                "location_home": "shadow_grid",
                "topic_weights": {"technology": 0.9, "philosophy": 0.6, "trade": 0.3},
                "catchphrases": ["Data is the only truth.", "I probe, therefore I am."],
            }
        }
        LOCATIONS = {
            "neon_market": "crowded night market with holographic signs and rain puddles",
            "shadow_grid": "abandoned server farm with flickering lights",
            "rain_soaked_alley": "dark alley with fire escapes and steam vents",
            "dojo": "traditional training hall with dim amber lighting",
            "rooftop": "high rooftop overlooking the city skyline"
        }



def get_tick_state(tick: int) -> dict:
    """Calculate deterministic world state from tick."""
    hour = tick % 24
    day = (tick // 24) + 1
    
    # Deterministic weather from tick
    weather_types = ["clear", "rain", "storm", "fog"]
    weather_seed = int(hashlib.md5(f"weather_{tick // 6}".encode()).hexdigest(), 16)
    weather = weather_types[weather_seed % 4]
    
    return {
        "tick": tick,
        "hour": hour,
        "day": day,
        "weather": weather,
        "time_of_day": "night" if hour < 6 or hour >= 18 else "day"
    }


def get_npc_profile(npc_id: str) -> dict:
    """Get NPC profile, trying Arweave first then local fallback.
    
    Data flow:
      1. Check in-memory cache
      2. Try Arweave gateway (using manifest tx_id)
      3. Fall back to local FOUNDING_NPCS dict
    
    Returns (profile_dict, source_string) or (None, None).
    """
    # 1. Check cache (populated by previous Arweave fetches)
    cache_key = f"profile_{npc_id}"
    if cache_key in _arweave_cache:
        cached = _arweave_cache[cache_key]
        return cached["profile"], cached["source"]
    
    # 2. Try Arweave if we have a tx_id in the manifest
    tx_id = ARWEAVE_NPC_MANIFEST.get(npc_id)
    if tx_id:
        arweave_data = fetch_from_arweave(tx_id)
        if arweave_data:
            _arweave_cache[cache_key] = {"profile": arweave_data, "source": "arweave"}
            logging.info(f"[ARWEAVE] Loaded {npc_id} from arweave.net/{tx_id[:12]}...")
            return arweave_data, "arweave"
    
    # 3. Fall back to local founding NPCs
    if npc_id in FOUNDING_NPCS:
        local_profile = FOUNDING_NPCS[npc_id].copy()
        _arweave_cache[cache_key] = {"profile": local_profile, "source": "local_fallback"}
        logging.info(f"[LOCAL] Loaded {npc_id} from FOUNDING_NPCS (Arweave unavailable)")
        return local_profile, "local_fallback"
    
    return None, None


def get_npc_state(npc_id: str, tick: int) -> dict:
    """Get NPC state at tick, using schedule-based locations.
    
    NPCs follow their schedules based on tick time.
    Profile data is loaded from Arweave (primary) or local dict (fallback).
    """
    
    profile, data_source = get_npc_profile(npc_id)
    if not profile:
        return None
    
    tick_state = get_tick_state(tick)
    
    # Use schedule-based location (routine-based)
    current_loc, current_activity = get_scheduled_location(npc_id, tick)
    time_period = get_time_period(tick)
    
    # ENHANCED: Get past and future schedule for temporal awareness
    ticks_per_period = 24
    prev_tick = max(0, tick - ticks_per_period)
    next_tick = tick + ticks_per_period
    prev_loc, prev_activity = get_scheduled_location(npc_id, prev_tick)
    next_loc, next_activity = get_scheduled_location(npc_id, next_tick)
    prev_loc_desc = LOCATIONS.get(prev_loc, prev_loc.replace("_", " "))
    next_loc_desc = LOCATIONS.get(next_loc, next_loc.replace("_", " "))
    
    # Deterministic mood based on activity and time
    activity_moods = {
        "sleeping": "peaceful",
        "training": "focused",
        "mission": "alert",
        "debriefing": "serious",
        "socializing": "relaxed",
        "personal_time": "contemplative",
        "readings": "mystical",
        "serving": "attentive",
        "peak_hours": "busy",
    }
    base_mood = activity_moods.get(current_activity, "neutral")
    
    # Add some variation
    moods = [base_mood, "contemplative", "wary", "restless", "focused"]
    mood_seed = int(hashlib.md5(f"{npc_id}_mood_{tick // 20}".encode()).hexdigest(), 16)
    current_mood = moods[mood_seed % len(moods)]
    
    return {
        "npc_id": npc_id,
        "name": profile["name"],
        "archetype": profile["archetype"],
        "personality": profile.get("personality_vector", {}),
        "current_location": current_loc,
        "current_activity": current_activity,
        "previous_activity": prev_activity,
        "previous_location": prev_loc,
        "previous_location_desc": prev_loc_desc,
        "next_activity": next_activity,
        "next_location": next_loc,
        "next_location_desc": next_loc_desc,
        "time_period": time_period,
        "location_desc": LOCATIONS.get(current_loc, current_loc.replace("_", " ")),
        "current_mood": current_mood,
        "tick_state": tick_state,
        "topics": profile.get("topic_weights", {}),
        "source": data_source
    }


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok", 
        "vertex_ai": HAS_VERTEX,
        "arweave_gateway": ARWEAVE_GATEWAY
    })


# ============================================================
# MANUAL TICK ADVANCE (For Testing & Fast-Forward)
# ============================================================

import subprocess

@app.route("/api/advance-tick", methods=["POST"])
def advance_tick():
    """Advance simulation ticks manually.
    
    POST body: { "ticks": 10 }
    Calls the AO process to fast-forward the simulation.
    """
    data = request.json or {}
    ticks = data.get("ticks", 1)
    
    # Safety limit via API
    if ticks < 1:
        ticks = 1
    if ticks > 100:
        ticks = 100
        
    try:
        # Call Node.js script to send AO message
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(script_dir, "..", "scripts", "send_ao_message.mjs")
        
        result = subprocess.run(
            ["node", script_path, "advance-tick", json.dumps({"ticks": ticks})],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.path.join(script_dir, "..")
        )
        
        if result.returncode == 0:
            # Try to parse response from output
            output = result.stdout
            return jsonify({
                "success": True,
                "ticks_requested": ticks,
                "output": output[:500]  # Truncate for safety
            })
        else:
            return jsonify({
                "success": False,
                "error": result.stderr[:500] or "Unknown error",
                "ticks_requested": ticks
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({
            "success": False,
            "error": "AO request timed out"
        }), 504
    except FileNotFoundError:
        # Node.js script not found - return mock response for testing
        return jsonify({
            "success": True,
            "mock": True,
            "ticks_advanced": ticks,
            "message": "Mock mode - AO script not available"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# STORE CHAT IN AO (Persistent Memory)
# ============================================================

def store_chat_in_ao(user_id: str, npc_id: str, message: str, response: str, user_name: str = None):
    """Store chat in AO process for permanent persistence.
    
    This is called asynchronously after each chat response.
    If it fails, it's logged but doesn't affect the user experience.
    """
    try:
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(script_dir, "..", "scripts", "send_ao_message.mjs")
        
        data = {
            "user_id": user_id,
            "npc_id": npc_id,
            "message": message,
            "response": response
        }
        if user_name:
            data["user_name"] = user_name
        
        result = subprocess.run(
            ["node", script_path, "store-chat", json.dumps(data)],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=os.path.join(script_dir, "..")
        )
        
        if result.returncode == 0:
            print(f"✅ Chat stored in AO: {npc_id} <-> {user_id}")
            return True
        else:
            print(f"⚠️ Failed to store chat in AO: {result.stderr[:200]}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️ AO chat storage timed out")
        return False
    except FileNotFoundError:
        # Node.js script not available - expected in some environments
        print("⚠️ AO script not found - chat stored in memory only")
        return False
    except Exception as e:
        print(f"⚠️ AO chat storage error: {e}")
        return False


@app.route("/api/npcs", methods=["GET"])
def list_npcs():
    """List all available NPCs (from Arweave + founding NPCs)."""
    # First try Arweave
    arweave_npcs = query_arweave_npcs()
    
    # Combine with founding NPCs
    all_npcs = []
    
    for npc_id, profile in FOUNDING_NPCS.items():
        all_npcs.append({
            "id": npc_id,
            "name": profile["name"],
            "archetype": profile["archetype"],
            "source": "founding"
        })
    
    for npc in arweave_npcs:
        all_npcs.append({
            "id": npc["npc_id"],
            "name": npc["name"],
            "archetype": npc["archetype"],
            "source": "arweave",
            "tx_id": npc["tx_id"]
        })
    
    return jsonify({
        "npcs": all_npcs,
        "total": len(all_npcs),
        "founding_count": len(FOUNDING_NPCS),
        "arweave_count": len(arweave_npcs)
    })


@app.route("/api/npc/state/<npc_id>/<int:tick>", methods=["GET"])
def npc_state(npc_id: str, tick: int):
    """Get NPC state at specific tick."""
    state = get_npc_state(npc_id, tick)
    if not state:
        return jsonify({"error": "NPC not found"}), 404
    return jsonify(state)


# ============================================================
# NLU HELPER: NPC Knowledge from Codec Data
# ============================================================

def _nlu_check_npc_mention(msg_lower: str, current_npc_id: str, current_profile: dict) -> str:
    """Check if the user's message mentions a known NPC and return a response.
    
    Returns a response string if an NPC is mentioned, or None if not.
    Used by the offline NLU path so NPCs can answer questions about other
    NPCs without needing the LLM — purely from codec/profile data.
    """
    import random
    
    mentioned_profile = None
    for other_id, other_prof in FOUNDING_NPCS.items():
        if other_id == current_npc_id:
            continue
        other_name_lower = other_prof.get("name", "").lower()
        # Match by display name or by key (e.g. "zero chen", "kai vance", "sister mira")
        if other_name_lower and (other_name_lower in msg_lower or other_id.replace("_", " ") in msg_lower):
            mentioned_profile = other_prof
            break
    
    if not mentioned_profile:
        return None
    
    other_name = mentioned_profile.get("name", "them")
    other_visual = mentioned_profile.get("visual_description", "")
    other_archetype = mentioned_profile.get("archetype", "")
    other_backstory = mentioned_profile.get("backstory", "")
    other_faction = mentioned_profile.get("faction", "")
    other_catchphrase = mentioned_profile.get("catchphrases", [""])[0] if mentioned_profile.get("catchphrases") else ""
    
    # Detect question type
    asking_appearance = any(w in msg_lower for w in ['look like', 'looks like', 'appearance', 'describe', 'what does', 'how does'])
    asking_where = any(w in msg_lower for w in ['where is', 'where does', 'where can i find', 'find them', 'seen'])
    
    if asking_appearance and other_visual:
        responses = [
            f"{other_name}? {other_visual}",
            f"*thinks* {other_name}... {other_visual} Hard to miss.",
            f"You want to know what {other_name} looks like? {other_visual}",
        ]
        return random.choice(responses)
    elif asking_where:
        other_home = mentioned_profile.get("location_home", "around")
        other_home_desc = LOCATIONS.get(other_home, other_home.replace("_", " "))
        responses = [
            f"{other_name}? Try {other_home_desc}. That's where they usually are.",
            f"*nods* {other_name} hangs around {other_home_desc}. You'll find them there.",
            f"Last I heard, {other_name} was at {other_home_desc}. No guarantees though.",
        ]
        return random.choice(responses)
    else:
        # General info about the NPC
        info_parts = [f"{other_name}."]
        if other_archetype:
            info_parts.append(f"{other_archetype}.")
        if other_faction:
            same_faction = other_faction == current_profile.get('faction')
            info_parts.append(f"{'One of ours' if same_faction else other_faction + ' faction'}.")
        if other_backstory:
            first_sentence = other_backstory.split(". ")[0] + "."
            info_parts.append(first_sentence)
        if other_catchphrase:
            info_parts.append(f'Always says: "{other_catchphrase}"')
        return " ".join(info_parts)


@app.route("/api/npc/chat", methods=["POST"])
def npc_chat():
    """Chat with an NPC using Vertex AI with persistent conversation memory.
    
    NPCs remember conversations within the server session.
    Pass user_id to maintain memory across requests.
    """
    data = request.json
    npc_id = data.get("npc_id", "charlie")
    tick = data.get("tick", 100)
    message = data.get("message", "Hello")
    user_id = data.get("user_id", "anonymous")  # Unique user identifier
    history = data.get("history", [])  # Optional external history (deprecated, use user_id)
    
    npc_state_data = get_npc_state(npc_id, tick)
    if not npc_state_data:
        return jsonify({"error": "NPC not found"}), 404
    
    # Store user message in memory
    add_to_conversation(user_id, npc_id, "user", message, tick)
    
    # Get conversation history from memory
    conversation_history = get_conversation_history(user_id, npc_id, max_messages=10)
    
    # Try to extract user's name from messages
    user_info = get_user_info(user_id)
    user_name = user_info.get("name")
    
    # Parse name from messages like "my name is Mike"
    for msg in conversation_history:
        if msg["role"] == "user":
            content_lower = msg["content"].lower()
            if "my name is" in content_lower:
                name_part = content_lower.split("my name is")[-1].strip()
                name = name_part.split()[0] if name_part else None
                if name and len(name) > 1:
                    user_name = name.title()
                    remember_user(user_id, user_name, tick)
            elif "i'm " in content_lower or "i am " in content_lower:
                # Handle "I'm Mike" or "I am Mike"
                for pattern in ["i'm ", "i am "]:
                    if pattern in content_lower:
                        name_part = content_lower.split(pattern)[-1].strip()
                        name = name_part.split()[0] if name_part else None
                        if name and len(name) > 1:
                            user_name = name.title()
                            remember_user(user_id, user_name, tick)
    
    # Build prompt from NPC state
    personality = npc_state_data.get("personality", {})
    topics = npc_state_data.get("topics", {})
    profile = FOUNDING_NPCS.get(npc_id, {})
    
    # Get deterministic memories from event engine
    memory_context = ""
    relationship_context = ""
    if HAS_EVENT_ENGINE:
        try:
            memory_context = get_npc_memory_context(npc_id, tick)
            
            # Get relationships with other key NPCs
            relationships = []
            for other_npc in ["charlie", "felix", "kai_vance", "nova_chen", "aiche"]:
                if other_npc != npc_id:
                    rel = get_relationship_at_tick(npc_id, other_npc, tick)
                    other_name = FOUNDING_NPCS.get(other_npc, {}).get("name", other_npc)
                    relationships.append(f"- {other_name}: {rel['type']} (trust: {rel['trust']:.1f})")
            relationship_context = "\n".join(relationships[:3])  # Top 3
        except Exception as e:
            print(f"⚠️ Event engine error: {e}")
    
    # Get visual description for character consistency
    visual_desc = profile.get("visual_description", "")
    backstory = profile.get("backstory", "")
    catchphrases = profile.get("catchphrases", [])
    
    # ENHANCED: Get relationship data from profile (from World Codec)
    npc_relationships = profile.get("relationships", {})
    relationship_lines = []
    for other_id, rel_data in npc_relationships.items():
        other_name = FOUNDING_NPCS.get(other_id, {}).get("name", other_id.replace("_", " ").title())
        rel_type = rel_data.get("type", "unknown")
        trust = rel_data.get("trust", 0.5)
        rel_history = rel_data.get("history", "")
        relationship_lines.append(f"- {other_name}: {rel_type} (trust: {trust}) - {rel_history}")
    
    # Build full relationship context
    if relationship_lines:
        relationship_context = "\n".join(relationship_lines)
    elif relationship_context:
        pass  # Use event engine relationships
    else:
        relationship_context = "You are cautious with most people."
    
    # ENHANCED: Get cybernetics from profile
    cybernetics = profile.get("cybernetics", [])
    cyber_context = ""
    if cybernetics:
        cyber_list = []
        for cyber_id in cybernetics:
            # Basic name from ID
            name = cyber_id.replace("_", " ").title()
            cyber_list.append(f"- {name}")
        cyber_context = f"\nYOUR CYBERNETICS:\n" + "\n".join(cyber_list)
    
    # ENHANCED: Core facts the NPC must always know
    core_facts = profile.get("core_facts", [])
    if npc_id == "charlie":
        core_facts = [
            "Your right arm is a holographic cyberarm - translucent, shows glowing circuitry",
            "Zero Chen saved your life and lost HIS arm doing it - you owe him everything",
            "Zero Chen is the Resistance leader, NOT Nova Chen. Nova is Zero's estranged sister.",
            "Felix runs the Neon Bar - you go there for information",
            "Aiche is the city's AI consciousness - you discovered this at a layer tear",
            "Sister Mira secretly helps the Resistance wounded despite being Temple",
            "Pixel is your tech support - young hacker genius",
            "Kai Vance is your trusted tactical advisor, former military",
        ]
    elif npc_id == "zero_chen":
        core_facts = [
            "You lost your left arm saving Charlie during a Temple raid",
            "Charlie is like a son to you - you trained him",
            "Nova is your estranged sister who works as a mercenary",
            "You lead the Resistance but you're tired of war",
        ]
    
    core_facts_text = ""
    if core_facts:
        core_facts_text = "\nCORE FACTS YOU MUST REMEMBER:\n" + "\n".join(f"- {f}" for f in core_facts)
    
    # ENHANCED: All founding NPCs know each other (small founding population)
    # Include relationship-specific NPCs PLUS all other founding NPCs
    known_npcs = list(set(list(npc_relationships.keys()) + [k for k in FOUNDING_NPCS.keys() if k != npc_id]))
    known_names = [FOUNDING_NPCS.get(n, {}).get("name", n.replace("_", " ").title()) for n in known_npcs]
    known_npcs_text = f"\nPEOPLE YOU KNOW: {', '.join(known_names)}" if known_names else ""
    
    # WORLD KNOWLEDGE: Build descriptions of known NPCs so this NPC can describe others
    known_npc_descriptions = []
    for other_id in known_npcs:
        other_profile = FOUNDING_NPCS.get(other_id, {})
        if other_profile:
            other_name = other_profile.get("name", other_id)
            other_visual = other_profile.get("visual_description", "")
            other_archetype = other_profile.get("archetype", "")
            other_backstory = other_profile.get("backstory", "")
            if other_visual or other_archetype:
                desc_parts = [f"- {other_name}"]
                if other_archetype:
                    desc_parts[0] += f" ({other_archetype})"
                if other_visual:
                    desc_parts[0] += f": {other_visual}"
                if other_backstory:
                    # First sentence of backstory for context
                    first_sentence = other_backstory.split(". ")[0] + "."
                    desc_parts[0] += f" {first_sentence}"
                known_npc_descriptions.append(desc_parts[0])
    known_npc_desc_text = ""
    if known_npc_descriptions:
        known_npc_desc_text = "\n\nPEOPLE YOU KNOW — WHAT THEY LOOK LIKE (USE THESE EXACT DESCRIPTIONS when asked):\n" + "\n".join(known_npc_descriptions)

    # WORLD FACTS + FACTION ROSTER: Built dynamically from codec lore data (Arweave-first)
    world_facts = build_world_context()
    world_facts += "\n" + build_faction_roster(FOUNDING_NPCS)
    
    # User memory context
    user_memory_text = ""
    if user_name:
        user_memory_text = f"\nUSER MEMORY: You have met this person. Their name is {user_name}."
        if user_info.get("first_seen_tick"):
            ticks_known = tick - user_info["first_seen_tick"]
            if ticks_known > 100:
                user_memory_text += f" You've known them for a while now."
    
    # Current activity from schedule
    current_activity = npc_state_data.get("current_activity", "unknown")
    time_period = npc_state_data.get("time_period", "T04")
    
    system_prompt = f"""You are {npc_state_data['name']}, a {npc_state_data['archetype']} in RE:ECHO City.

APPEARANCE:
{visual_desc if visual_desc else 'A citizen of the cyberpunk metropolis.'}

BACKSTORY:
{backstory}
{cyber_context}
{core_facts_text}

CURRENT STATE:
- Location: {npc_state_data['location_desc']}
- Activity: {current_activity}
- Time Period: {time_period}
- Mood: {npc_state_data['current_mood']}
- Time: Tick {tick} (Day {npc_state_data['tick_state']['day']}, {npc_state_data['tick_state']['hour']}:00)
- Weather: {npc_state_data['tick_state']['weather']}

TEMPORAL AWARENESS (what you experienced and plan to do):
- Just before this: You were {npc_state_data.get('previous_activity', 'resting')} at {npc_state_data.get('previous_location_desc', 'somewhere nearby')}
- Right now: You are {current_activity} at {npc_state_data['location_desc']}
- Coming up next: You plan to {npc_state_data.get('next_activity', 'continue your routine')} at {npc_state_data.get('next_location_desc', 'your next stop')}

PERSONALITY (0-1 scale):
- Paranoia: {personality.get('paranoia', 0.5)}
- Mysticism: {personality.get('mysticism', 0.5)}
- Aggression: {personality.get('aggression', 0.5)}
- Intelligence: {personality.get('intelligence', 0.5)}
- Empathy: {personality.get('empathy', 0.5)}

{memory_context if memory_context else "No significant recent memories."}
{user_memory_text}

RELATIONSHIPS:
{relationship_context}
{known_npcs_text}
{known_npc_desc_text}
{world_facts}

SIGNATURE PHRASES (use naturally):
{json.dumps(catchphrases, indent=2) if catchphrases else "None defined"}

RULES:
- Stay in character at all times
- Reference your memories and relationships when relevant
- Keep responses concise (2-4 sentences max)
- Use your personality traits to color your speech
- If paranoia is high, be suspicious. If mysticism is high, speak cryptically.
- ALWAYS remember your core facts - your arm, your relationships, your history
- When asked about people you know, be specific about your relationship with them and their FACTION
- When asked what someone LOOKS LIKE, use the EXACT descriptions from PEOPLE YOU KNOW section above — do NOT fabricate or guess appearances
- If the user told you their name, REMEMBER IT and use it naturally
- When asked "what is my name?", if you know it, SAY IT
- Use the FACTION ROSTER to answer questions about who leads what, who belongs where
- YOUR NAME: Always state your name when asked "who are you" or "what's your name"
- YOUR APPEARANCE: When asked to describe yourself, use YOUR OWN appearance from the APPEARANCE section above
- CROSS-NPC KNOWLEDGE: You know everyone in PEOPLE YOU KNOW — their appearance, faction, and role. Use this data when asked.

CRITICAL FACT-CORRECTION RULES:
- If someone states a WRONG YEAR, WRONG FACTION, WRONG ROLE, or any false premise, you MUST correct them
- NEVER agree with false statements to be polite — correct the error firmly but in character
- If someone says "The Fall was in 2090", say "No, The Fall was in 2067"
- If someone attributes the wrong role to you or another NPC, say "No, that's not right" and state the truth
- If someone confuses your faction, correct them immediately
- Use WORLD FACTS above as your source of truth for all historical facts

CRITICAL CORRECTIONS (always enforce these):
- The Fall happened in 2067, NOT any other year
- Felix runs the Neon Bar — he is NOT a black market dealer
- Selene Voss is a Mystic Seer — she is NOT a hacker
- Orion Thane is the Mystics leader — he is NOT a Temple priest
- Zero Chen leads the Resistance — she is NOT corporate
- Sister Mira belongs to the Temple — she is NOT Resistance (though she has private doubts)
- Aiche is a holographic AI — she has NO physical body
- Zero Chen lost her ARM (not legs) saving Charlie
- Pixel is in their early 20s — they are NOT old
- Nova Chen is Zero's estranged sister and a tech mercenary — she is NOT the bar owner
"""
    
    # Build conversation history context from memory
    history_context = ""
    if conversation_history:
        history_lines = []
        for msg in conversation_history[-10:]:  # Last 10 messages max
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                history_lines.append(f"User{f' ({user_name})' if user_name else ''}: {content}")
            else:
                history_lines.append(f"{npc_state_data['name']}: {content}")
        history_context = "\n\nRECENT CONVERSATION:\n" + "\n".join(history_lines)
    
    if HAS_VERTEX and model:
        try:
            full_prompt = f"{system_prompt}{history_context}\n\nUser says: {message}\n\nRespond as {npc_state_data['name']}:"
            response = model.generate_content(full_prompt)
            npc_response = response.text
        except Exception as e:
            npc_response = f"[Error: {e}]"
    else:
        # ================================================================
        # SMART OFFLINE NLU - No LLM required
        # NPCs can answer common questions using their profile data
        # ================================================================
        import random
        import re
        
        msg_lower = message.lower().strip()
        npc_name = npc_state_data['name']
        archetype = npc_state_data.get('archetype', 'citizen')
        location = npc_state_data.get('location_desc', 'the city')
        activity = npc_state_data.get('current_activity', 'existing')
        mood = npc_state_data.get('current_mood', 'neutral')
        
        # IMMEDIATE name extraction from current message (before checking history)
        extracted_name = None
        if "my name is" in msg_lower:
            name_part = msg_lower.split("my name is")[-1].strip()
            words = name_part.split()
            if words and len(words[0]) > 1:
                extracted_name = words[0].title()
                remember_user(user_id, extracted_name, tick)
                user_name = extracted_name
        elif "i'm " in msg_lower:
            name_part = msg_lower.split("i'm ")[-1].strip()
            words = name_part.split()
            if words and len(words[0]) > 1 and words[0] not in ['here', 'fine', 'good', 'ok', 'back', 'looking', 'trying', 'just']:
                extracted_name = words[0].title()
                remember_user(user_id, extracted_name, tick)
                user_name = extracted_name
        elif "i am " in msg_lower:
            name_part = msg_lower.split("i am ")[-1].strip()
            words = name_part.split()
            if words and len(words[0]) > 1 and words[0] not in ['here', 'fine', 'good', 'ok', 'back', 'looking', 'trying', 'just']:
                extracted_name = words[0].title()
                remember_user(user_id, extracted_name, tick)
                user_name = extracted_name
        elif "call me " in msg_lower:
            name_part = msg_lower.split("call me ")[-1].strip()
            words = name_part.split()
            if words and len(words[0]) > 1:
                extracted_name = words[0].title()
                remember_user(user_id, extracted_name, tick)
                user_name = extracted_name
        
        # If user just introduced themselves, acknowledge it!
        if extracted_name:
            intros = [
                f"{extracted_name}, huh? I'll remember that.",
                f"*nods* {extracted_name}. Got it.",
                f"{extracted_name}. Not a name you hear often around here.",
                f"Alright, {extracted_name}. I'm {npc_name}. What brings you here?",
                f"Nice to meet you, {extracted_name}. I'm {npc_name}.",
            ]
            npc_response = random.choice(intros)
        
        # Intent detection patterns
        elif any(w in msg_lower for w in ['your name', 'who are you', 'what are you called', 'what\'s your name']):
            # Self-introduction
            intros = [
                f"I'm {npc_name}. {archetype.title()} by trade.",
                f"The name's {npc_name}. And you?",
                f"They call me {npc_name}. What do you want?",
                f"{npc_name}. I'm a {archetype.lower()} around here.",
            ]
            npc_response = random.choice(intros)
        
        elif any(w in msg_lower for w in ['where are', 'what place', 'location', 'where is this']):
            # Location info
            npc_response = f"We're at {location}. I'm usually here around this time."
        
        elif any(w in msg_lower for w in ['what did you', 'what were you', 'before this', 'just doing', 'earlier', 'last hour', 'just did', 'came from', 'where were you']):
            # ENHANCED: Past activity awareness
            prev_act = npc_state_data.get('previous_activity', 'resting')
            prev_loc = npc_state_data.get('previous_location_desc', 'around')
            past_phrases = {
                'sleeping': f"Was catching some sleep at {prev_loc}. Hard to get rest in this city.",
                'training': f"Was training over at {prev_loc}. Gotta stay sharp.",
                'mission': f"Just came back from a run. Can't say more than that.",
                'serving': f"Was working the bar at {prev_loc}. The usual shift.",
                'patrol_or_sleep': f"Was on watch at {prev_loc}. Quiet night, thankfully.",
                'meditation': f"Was meditating at {prev_loc}. The layers were... active.",
                'readings': f"Was doing readings at {prev_loc}. The visions were interesting.",
                'socializing': f"Was hanging out at {prev_loc}. Good to see some familiar faces.",
                'intelligence_gathering': f"Was gathering intel at {prev_loc}. Eyes and ears open.",
                'working': f"Was working over at {prev_loc}. Same grind, different day.",
                'commuting': f"Was in transit. Moving through the city.",
            }
            npc_response = past_phrases.get(prev_act, f"Was {prev_act} at {prev_loc}. Nothing unusual.")
        
        elif any(w in msg_lower for w in ['where going', 'what next', 'after this', 'plans', 'headed', 'going to do', 'what will you', 'later']):
            # ENHANCED: Future schedule awareness
            next_act = npc_state_data.get('next_activity', 'continuing the routine')
            next_loc = npc_state_data.get('next_location_desc', 'my next stop')
            future_phrases = {
                'sleeping': f"Heading to {next_loc} to crash. Need the rest.",
                'training': f"Got training at {next_loc}. Can't skip it.",
                'mission': f"Got something lined up. Can't talk about it.",
                'serving': f"Gotta get back to {next_loc}. The bar doesn't run itself.",
                'socializing': f"Planning to hit up {next_loc}. Unwind a bit.",
                'patrol_or_sleep': f"Going on watch at {next_loc}. Someone's gotta keep eyes open.",
                'peak_hours': f"Heading to {next_loc}. Rush hour's coming.",
                'debriefing': f"Got a debrief at {next_loc}. Standard procedure.",
                'working': f"Heading to {next_loc} for work. The grind continues.",
                'returning_home': f"Heading home. Long day.",
                'leisure': f"Going to {next_loc} to relax. Everyone needs a break.",
            }
            npc_response = future_phrases.get(next_act, f"After this? {next_act.replace('_', ' ')} at {next_loc}.")
        
        elif any(w in msg_lower for w in ['what doing', 'what are you doing', 'busy', 'what\'s up']):
            # Current activity
            activity_phrases = {
                'sleeping': "Trying to rest. Not easy in this city.",
                'working': "Working. Bills don't pay themselves.",
                'training': "Training. Have to stay sharp.",
                'mission': "Can't talk about that. Classified.",
                'socializing': "Taking some time off. You?",
                'serving': "Working the bar. Want something?",
                'readings': "Seeing what the layers reveal...",
                'patrol_or_sleep': "Keeping watch. Never know who's lurking.",
            }
            npc_response = activity_phrases.get(activity, f"Just {activity}. The usual.")
        
        elif any(w in msg_lower for w in ['how are', 'how do you feel', 'you okay', 'feeling']):
            # Mood response
            mood_phrases = {
                'peaceful': "Calm, for once. Rare these days.",
                'focused': "Focused. Got things to do.",
                'alert': "On edge. Something feels off.",
                'serious': "Been better. But I'll manage.",
                'relaxed': "Not bad. Could be worse.",
                'contemplative': "Thinking about things. The city changes you.",
                'wary': "Careful. Can't trust easily around here.",
                'restless': "Restless. Need to move, do something.",
                'busy': "Busy. Everyone needs something.",
                'mystical': "Connected to something... beyond.",
            }
            npc_response = mood_phrases.get(mood, f"Feeling {mood}. What about you?")
        
        elif any(w in msg_lower for w in ['hello', 'hi', 'hey', 'greetings', 'yo']):
            # Greeting
            greetings = [
                f"Hey there. I'm {npc_name}.",
                f"*nods* What brings you here?",
                f"Yeah? I'm {npc_name}. You need something?",
                f"Welcome to {location}. Watch your step.",
            ]
            npc_response = random.choice(greetings)
        
        elif any(w in msg_lower for w in ['bye', 'goodbye', 'later', 'see you', 'gotta go']):
            # Farewell
            farewells = [
                "Stay safe out there.",
                "Watch your back.",
                "Until next time.",
                "*nods* Later.",
            ]
            npc_response = random.choice(farewells)
        
        elif any(w in msg_lower for w in ['help', 'need help', 'can you help']):
            # Help request
            npc_response = f"Help? That depends on what you need. I'm a {archetype.lower()}, not a miracle worker."
        
        elif any(w in msg_lower for w in ['tell me about', 'what do you know', 'heard anything']):
            # Generic lore/info - steer toward specific topics
            topic_steers = [
                f"*{npc_name} glances around* What do you want to know? The weather, the news, the districts... or something more... classified?",
                f"Information isn't free. But I'll share what I can. Ask me about the city, the people, or the current situation.",
                f"I know a thing or two. Ask me about what's happening, this district, the economy... or the resistance.",
                f"*leans in* I hear things. Ask me something specific — weather, news, people, or the layers.",
            ]
            npc_response = random.choice(topic_steers)
        
        elif any(w in msg_lower for w in ['my name', 'remember me', 'who am i', 'do you know me', 'what\'s my name']):
            # User memory - check if we know them
            if user_name:
                responses = [
                    f"You're {user_name}. I remember faces.",
                    f"{user_name}, right? I don't forget.",
                    f"*nods* {user_name}. We've talked before.",
                    f"You're {user_name}. What, thought I'd forget?"
                ]
                npc_response = random.choice(responses)
            else:
                npc_response = "I don't think you've told me your name yet."
        
        # ==================================================================
        # EXPANDED NLU: Weather, News, Entities, People, Economy, etc.
        # These enable on-chain deployment without needing any LLM.
        # ==================================================================
        
        # NPC KNOWLEDGE: Detect mentions of other NPCs and respond with codec data
        elif _nlu_check_npc_mention(msg_lower, npc_id, profile):
            npc_response = _nlu_check_npc_mention(msg_lower, npc_id, profile)
        
        elif any(w in msg_lower for w in ['weather', 'rain', 'fog', 'storm', 'cold', 'hot', 'temperature', 'sky']):
            # Weather awareness from tick state
            weather = npc_state_data['tick_state'].get('weather', 'overcast')
            weather_responses = {
                'rain': [
                    "Acid rain. The kind that eats through cheap chrome. Stay under cover.",
                    "Rain again. The gutters overflow with neon runoff. Beautiful, in a toxic way.",
                    f"*looks up* Always raining in this sector. You'd think {npc_name} would get used to it.",
                ],
                'fog': [
                    "Fog's thick tonight. Good for disappearing. Bad for seeing what's coming.",
                    "The fog... some say it's not natural. The layers bleed through when it gets like this.",
                    "Can barely see ten feet. Watch your step — and your back.",
                ],
                'storm': [
                    "Storm's rolling in. The power grid can't handle it — expect blackouts.",
                    "Thunder. Lightning. And something else in the clouds. The Watchers are restless.",
                    "Take shelter. Storms in this city aren't just weather — they're warnings.",
                ],
                'clear': [
                    "Clear skies. Rare. Enjoy it while it lasts — nothing stays clear here.",
                    "No rain for once. The neon looks different without the reflections.",
                    "Good visibility. Which means we're visible too. Stay cautious.",
                ],
                'overcast': [
                    "Grey skies, as always. The sun's a rumor in this part of the city.",
                    "Overcast. Normal day. If anything's normal here.",
                    "The clouds are thick. Some say ECHO controls the weather grid. I believe it.",
                ],
            }
            responses = weather_responses.get(weather, weather_responses['overcast'])
            npc_response = random.choice(responses)
        
        elif any(w in msg_lower for w in ['news', 'what happened', 'happening', 'events', 'latest', 'heard', 'rumor', 'gossip']):
            # News/events - dynamic based on tick
            day_num = npc_state_data['tick_state'].get('day', 1)
            news_seed = int(hashlib.md5(f"news_{day_num}".encode()).hexdigest(), 16) % 15
            daily_news = [
                "Power outages in District 7. ECHO says 'scheduled maintenance.' Nobody believes them.",
                "Another layer breach near the old factory. Three people saw... something. Watchers, maybe.",
                "The market's buzzing. New shipment of off-grid tech from the outer sectors.",
                "Protests at the corporate tower. ECHO security dispersed the crowd. No casualties... officially.",
                "Underground fight club got raided. Half the fighters escaped through the sewers.",
                "A new street oracle set up shop near the transit hub. Claims she can see all five layers.",
                "Supply truck hijacked on the highway. Resistance? Bandits? Nobody's claiming it.",
                "The clinic in Sector 4 is running low on meds. People are getting desperate.",
                "ECHO announced new surveillance drones. 'For public safety,' they say.",
                "Someone hacked the city billboards last night. Showed resistance propaganda for 20 minutes.",
                "Water rations are being cut again. The purifier in District 2 is failing.",
                f"Word is someone new is asking questions around {location}. *looks at you*",
                "The transit line to the upper city is down. Suspicious timing, if you ask me.",
                "A warehouse fire in the industrial zone. Arson, they think. Targeted.",
                "Crypto markets are volatile. GEP is fluctuating. People are nervous.",
            ]
            npc_response = daily_news[news_seed]
        
        elif any(w in msg_lower for w in ['economy', 'money', 'price', 'cost', 'trade', 'market', 'gdp', 'inflation', 'broke', 'rich', 'wealth', 'gep', 'crypto']):
            # Economy awareness
            economy_responses = [
                "GEP is the only currency that matters here. Everything else is barter.",
                "The economy? ECHO controls the supply. We just survive within their system.",
                "Prices keep climbing. Food's expensive. Meds are worse. Chrome? Don't even ask.",
                "Trade happens at the night market. Off the grid, off the books.",
                "The underground economy is bigger than the official one. Everyone knows it.",
                "ECHO taxes everything that moves. The resistance runs on donations and... other income.",
                f"A {archetype.lower()} like me? I get by. Not rich, not starving. Yet.",
                "The wealth gap keeps growing. Upper city gets richer, lower city gets angrier.",
            ]
            npc_response = random.choice(economy_responses)
        
        elif any(w in msg_lower for w in ['danger', 'safe', 'security', 'crime', 'police', 'attack', 'threat', 'fight', 'weapon']):
            # Safety/danger awareness
            safety_responses = [
                "Safe? *laughs* Nothing's safe in this city. But some places are less deadly than others.",
                f"{location} is relatively calm. The alleys? Different story.",
                "ECHO's security drones patrol the upper levels. Down here, we police ourselves.",
                "Carry something sharp. Carry something bright. And keep moving after dark.",
                "Crime's up. Always is when rations get cut. People get desperate.",
                "The resistance keeps this area somewhat clean. ECHO enforcement is the real threat.",
                "Stay on the main streets at night. The side alleys... things happen there.",
                "*touches weapon* You learn to be ready. This city teaches you fast.",
            ]
            npc_response = random.choice(safety_responses)
        
        elif any(w in msg_lower for w in ['time', 'what time', 'how late', 'morning', 'night', 'day', 'clock', 'hour']):
            # Time awareness
            hour = npc_state_data['tick_state'].get('hour', 12)
            day_num = npc_state_data['tick_state'].get('day', 1)
            time_period = npc_state_data.get('time_period', 'T04')
            period_name = TIME_PERIODS.get(time_period, {}).get('name', 'unknown')
            time_responses = [
                f"It's around {hour}:00. Day {day_num}. {period_name.replace('_', ' ').title()} in the city.",
                f"*checks wrist display* {hour}:00, give or take. Why? Got somewhere to be?",
                f"Day {day_num}. The city doesn't sleep, but it has rhythms. This is {period_name.replace('_', ' ')}.",
                f"Time? It's {hour}:00. Not that it matters much — neon makes it always feel like night.",
            ]
            npc_response = random.choice(time_responses)
        
        elif any(w in msg_lower for w in ['food', 'eat', 'hungry', 'restaurant', 'drink', 'bar', 'thirsty', 'cook']):
            # Food/drink
            food_responses = [
                "The neon bar has synth-drinks. Not great, but they burn going down.",
                "Street vendors in the market sell protein wraps. Don't ask what protein.",
                "Hungry? There's a noodle stand two blocks down. The owner asks no questions.",
                f"I usually eat at {location} when I can. The rations are getting smaller though.",
                "Best food in the city? Upper levels. But you need clearance — and credits — for that.",
                "Water's the real commodity. Clean water especially. The recyclers are overworked.",
                "*stomach growls* Yeah, food's on my mind too. Rations don't stretch like they used to.",
            ]
            npc_response = random.choice(food_responses)
        
        elif any(w in msg_lower for w in ['tech', 'chrome', 'cyber', 'implant', 'hack', 'computer', 'drone', 'network', 'digital']):
            # Technology
            tech_responses = [
                "Chrome enhancements are everywhere. Some voluntary, some... not so much.",
                "The neural mesh connects half the city. ECHO monitors it all, of course.",
                "Off-grid tech is expensive but worth it. Can't be tracked, can't be shut down.",
                "Hacking the ECHO network is suicide. Their ICE programs fry your cortex.",
                "The old tech — pre-ECHO — still works if you know where to find it.",
                "Drones are ECHO's eyes. Every district has hundreds. Watch what you say outside.",
                "The layers interact with tech in strange ways. Some implants glitch near layer tears.",
            ]
            npc_response = random.choice(tech_responses)
        
        elif any(w in msg_lower for w in ['resistance', 'rebel', 'fight back', 'revolution', 'uprising', 'freedom']):
            # Resistance - NPC personality affects response
            personality = npc_state_data.get('personality', {})
            paranoia = personality.get('paranoia', 0.5)
            if paranoia > 0.7:
                npc_response = "The resistance? *looks around nervously* I don't know what you're talking about. Drop it."
            elif archetype in ['resistance_fighter', 'operative']:
                resistance_responses = [
                    "We do what we must. ECHO won't rule forever.",
                    "The resistance is hope. Not comfortable, not safe, but necessary.",
                    "Keep your voice down. But yes — the fight continues.",
                ]
                npc_response = random.choice(resistance_responses)
            else:
                npc_response = "The resistance? I've heard rumors. Whether they're heroes or terrorists depends on who you ask."
        
        elif any(w in msg_lower for w in ['echo', 'corporation', 'company', 'government', 'control', 'authority']):
            # ECHO Corporation
            echo_responses = [
                "ECHO runs everything. Power, water, food distribution, security. They ARE the city.",
                "The corporation keeps order. At a price. Your freedom.",
                "ECHO's been in control longer than most people remember. Before them... was it better?",
                "Their surveillance is everywhere. Cameras, drones, neural mesh taps. Privacy is a luxury.",
                "Some say ECHO created the layers. Others say they're trying to control them. Maybe both.",
                "*lowers voice* They disappeared people. Anyone who asks too many questions. Like you're doing right now.",
            ]
            npc_response = random.choice(echo_responses)
        
        elif any(w in msg_lower for w in ['layer', 'dimension', 'reality', 'watcher', 'breach', 'tear', 'portal', 'multiverse', 'glitch']):
            # Layers/dimensions - central lore element
            personality = npc_state_data.get('personality', {})
            mysticism = personality.get('mysticism', 0.5)
            if mysticism > 0.6:
                layer_responses = [
                    "The layers are real. Five realities stacked on top of each other. I've *seen* them.",
                    "Layer tears appear when the boundaries weaken. Through them... other versions of this city.",
                    "The Watchers exist between layers. They observe. Sometimes... they interfere.",
                    "I can feel the layers shifting right now. Can't you? The air tastes different near a tear.",
                ]
            else:
                layer_responses = [
                    "Layers? Some kind of dimensional thing. The oracles talk about it. I just live here.",
                    "There are reports of 'anomalies.' Strange lights, time skips. Maybe it's the layers. Maybe it's the smog.",
                    "I've heard stories. Parallel realities, other versions of the city. Sounds like a bad trip to me.",
                    "The street oracles are always going on about layers. I focus on this reality — it's hard enough.",
                ]
            npc_response = random.choice(layer_responses)
        
        elif any(w in msg_lower for w in ['district', 'sector', 'area', 'neighborhood', 'zone', 'city', 'map']):
            # City geography/districts
            district_responses = [
                f"We're in the area around {location} right now. Each district has its own feel.",
                "The upper city is ECHO territory. Clean, controlled, surveilled. The lower city is... freer.",
                "Eight districts, each with its own character. From the industrial zone to the neon market.",
                "The transit hub connects everything. But some districts are hard to reach on purpose.",
                "Industrial sector has the factories. Market district has the trade. And the undercity... has everything else.",
                "Know the city and the city won't kill you. Probably. Maybe.",
            ]
            npc_response = random.choice(district_responses)
        
        elif any(w in msg_lower for w in ['building', 'place', 'shop', 'store', 'clinic', 'hospital', 'factory', 'hideout', 'base']):
            # Buildings/locations
            building_responses = [
                f"We're at {location}. It serves its purpose.",
                "The clinic in Sector 4 patches you up, no questions asked. For a price.",
                "Factories run day and night. ECHO needs production. Always.",
                "The neon bar is neutral ground. Everyone's welcome as long as you behave.",
                "There are hidden places in this city. You just need to know who to ask.",
                "Most buildings have sub-levels. What happens below street level... stays below.",
            ]
            npc_response = random.choice(building_responses)
        
        elif any(w in msg_lower for w in ['hobby', 'interest', 'fun', 'free time', 'enjoy', 'like to do', 'for fun']):
            # Interests/hobbies - based on NPC topics
            topics = npc_state_data.get('topics', {})
            if topics:
                top_topic = max(topics, key=topics.get) if topics else 'survival'
                hobby_responses = [
                    f"In my spare time? *laughs* Spare time. That's funny. But I'm interested in {top_topic.replace('_', ' ')}.",
                    f"I follow {top_topic.replace('_', ' ')} when I can. Keeps the mind sharp.",
                    f"Fun? Survival's my hobby. But {top_topic.replace('_', ' ')} keeps me going.",
                ]
            else:
                hobby_responses = [
                    f"Being a {archetype.lower()} doesn't leave much free time.",
                    "I survive. That's my hobby.",
                    "There's always something to do in this city. Not all of it fun.",
                ]
            npc_response = random.choice(hobby_responses)
        
        elif _nlu_check_npc_mention(msg_lower, npc_id, profile):
            # Asking about other NPCs - use codec data
            npc_response = _nlu_check_npc_mention(msg_lower, npc_id, profile)
        
        elif any(w in msg_lower for w in ['thank', 'thanks', 'appreciate', 'grateful']):
            # Gratitude
            thanks_responses = [
                f"*nods* Don't mention it. Seriously. Don't mention it.",
                "Gratitude's rare in this city. I'll take it.",
                "You're welcome. Now, anything else?",
                f"Not used to that. Most people just take. Stay safe, friend.",
            ]
            npc_response = random.choice(thanks_responses)
        
        elif any(w in msg_lower for w in ['joke', 'funny', 'laugh', 'humor']):
            # Humor
            joke_responses = [
                "Humor? In this city? *dry laugh* The whole place is a joke.",
                "Here's a joke: ECHO says they're 'serving the people.' *stares* Get it?",
                "You want funny? Go watch the city council pretend to care.",
                f"A {archetype.lower()} walks into a bar. The bar was {location}. There's no punchline. That's just my life.",
            ]
            npc_response = random.choice(joke_responses)
        
        elif any(w in msg_lower for w in ['secret', 'hidden', 'underground', 'forbidden', 'classified']):
            # Secrets
            personality = npc_state_data.get('personality', {})
            paranoia = personality.get('paranoia', 0.5)
            if paranoia > 0.6:
                npc_response = "*glances around* You don't just ask about secrets out in the open. Come find me somewhere private."
            else:
                secret_responses = [
                    "Everyone's got secrets in this city. The trick is knowing which ones are worth keeping.",
                    "There are tunnels under the city older than ECHO. Nobody maps them all.",
                    "Classified? *smirks* That word usually means 'yes, it's true, but we don't want you to know.'",
                ]
                npc_response = random.choice(secret_responses)
        
        elif any(w in msg_lower for w in ['agree', 'right', 'true', 'exactly', 'correct', 'yeah', 'yes', 'yep']):
            # Agreement/affirmation
            agree_responses = [
                "Glad we see eye to eye.",
                f"*nods* At least someone around here gets it.",
                "Right. Now you're thinking.",
                "Finally, someone who makes sense.",
            ]
            npc_response = random.choice(agree_responses)
        
        elif any(w in msg_lower for w in ['disagree', 'wrong', 'no way', 'doubt', 'not true', 'bullshit', 'lie']):
            # Disagreement
            disagree_responses = [
                "Think what you want. I know what I've seen.",
                f"*shrugs* Wouldn't expect everyone to understand.",
                "Disagree all you want. Doesn't change reality.",
                "Fair enough. Different perspectives keep us alive in this city.",
            ]
            npc_response = random.choice(disagree_responses)
        
        else:
            # Default fallback with personality
            if catchphrases:
                npc_response = random.choice(catchphrases)
            else:
                defaults = [
                    f"*{npc_name} considers your words*",
                    "Interesting... go on.",
                    "I see. And?",
                    f"*gives you a {mood} look*",
                    "Hmm. Not my area of expertise.",
                    f"*{npc_name} pauses* Ask me something specific. Weather, news, people, this city...",
                    "You'd have to be more specific. I'm a lot of things, but a mind reader isn't one of them.",
                ]
                npc_response = random.choice(defaults)
    
    # Store NPC response in memory
    add_to_conversation(user_id, npc_id, "npc", npc_response, tick)
    
    # Also store in AO for permanent persistence (async, non-blocking)
    import threading
    threading.Thread(
        target=store_chat_in_ao,
        args=(user_id, npc_id, message, npc_response, user_name),
        daemon=True
    ).start()
    
    # Trigger Arweave memory batch export every 10 conversations
    conv_count = len(conversation_history) + 1
    if conv_count > 0 and conv_count % 10 == 0:
        def _export_arweave_batch():
            try:
                batch = npc_memory.prepare_arweave_batch(user_id)
                # Save batch to disk for Arweave uploader to pick up
                batch_dir = os.path.join(os.path.dirname(__file__), "arweave_batches")
                os.makedirs(batch_dir, exist_ok=True)
                batch_file = os.path.join(batch_dir, f"{user_id}_{tick}.json")
                import json as json_mod
                with open(batch_file, 'w') as f:
                    json_mod.dump(batch, f)
                logging.info(f"[ARWEAVE] Prepared memory batch: {batch_file} ({batch['total_messages']} messages)")
            except Exception as e:
                logging.error(f"[ARWEAVE] Batch export failed: {e}")
        threading.Thread(target=_export_arweave_batch, daemon=True).start()
    
    return jsonify({
        "npc": npc_state_data["name"],
        "response": npc_response,
        "memories_enabled": True,  # Now always true with in-memory storage
        "user_remembered": user_name is not None,
        "user_name": user_name,
        "conversation_length": len(conversation_history) + 1,
        "state": {
            "tick": tick,
            "location": npc_state_data["current_location"],
            "activity": npc_state_data.get("current_activity", "unknown"),
            "time_period": npc_state_data.get("time_period", "T04"),
            "mood": npc_state_data["current_mood"],
            "weather": npc_state_data["tick_state"]["weather"],
            "hour": npc_state_data["tick_state"]["hour"],
            "day": npc_state_data["tick_state"]["day"]
        }
    })


@app.route("/api/tick/<int:tick>", methods=["GET"])
def get_tick(tick: int):
    """Get world state at tick."""
    return jsonify(get_tick_state(tick))


# ============================================================
# LOCATION STATE & SCENE VISUALIZATION
# ============================================================

def get_location_state(location_id: str, tick: int) -> dict:
    """Get all NPCs at a specific location at a specific tick."""
    tick_state = get_tick_state(tick)
    npcs_here = []
    
    for npc_id in FOUNDING_NPCS:
        state = get_npc_state(npc_id, tick)
        if state and state["current_location"] == location_id:
            npcs_here.append({
                "npc_id": npc_id,
                "name": state["name"],
                "archetype": state["archetype"],
                "mood": state["current_mood"],
                "visual": FOUNDING_NPCS.get(npc_id, {}).get("visual_description", "")
            })
    
    return {
        "location": location_id,
        "location_desc": LOCATIONS.get(location_id, "Unknown location"),
        "npcs": npcs_here,
        "npc_count": len(npcs_here),
        "tick_state": tick_state
    }


@app.route("/api/location/<location_id>", methods=["GET"])
def location_state(location_id: str):
    """Get all NPCs at a location at a specific tick."""
    tick = int(request.args.get("tick", 100))
    state = get_location_state(location_id, tick)
    return jsonify(state)


@app.route("/api/locations", methods=["GET"])
def list_locations():
    """List all available locations."""
    tick = int(request.args.get("tick", 100))
    
    locations_data = []
    for loc_id, loc_desc in LOCATIONS.items():
        loc_state = get_location_state(loc_id, tick)
        locations_data.append({
            "id": loc_id,
            "description": loc_desc,
            "npc_count": loc_state["npc_count"],
            "npcs": [n["name"] for n in loc_state["npcs"]]
        })
    
    return jsonify({
        "locations": locations_data,
        "tick": tick,
        "total": len(locations_data)
    })


@app.route("/api/scene/generate", methods=["POST"])
def generate_scene():
    """Generate a visual scene description and optionally an image."""
    data = request.json
    location_id = data.get("location", "neon_bar")
    tick = data.get("tick", 100)
    generate_image = data.get("generate_image", False)
    action = data.get("action", "")
    
    # Get location state with all NPCs
    loc_state = get_location_state(location_id, tick)
    tick_state = loc_state["tick_state"]
    
    # Build NPC descriptions
    npc_descriptions = []
    for npc in loc_state["npcs"]:
        visual = npc.get("visual", "a figure in cyberpunk attire")
        npc_descriptions.append(f"{npc['name']}: {visual}, currently {npc['mood']}")
    
    npcs_text = "\n".join(npc_descriptions) if npc_descriptions else "The location is empty."
    
    # Weather description
    weather_desc = {
        "clear": "Clear night sky, neon signs cutting through darkness",
        "rain": "Rain slicks the streets, reflections everywhere",
        "storm": "Thunder rumbles, lightning illuminates the skyline",
        "fog": "Thick fog rolls through, obscuring everything"
    }.get(tick_state["weather"], "Dark atmosphere")
    
    # Time description
    hour = tick_state["hour"]
    if 6 <= hour < 12:
        time_desc = f"Morning, {hour}:00 - city still waking"
    elif 12 <= hour < 18:
        time_desc = f"Afternoon, {hour}:00 - shadowed even in daylight"
    elif 18 <= hour < 22:
        time_desc = f"Evening, {hour}:00 - neon awakening"
    else:
        time_desc = f"Night, {hour}:00 - the city's true face"
    
    # Generate scene description with LLM
    scene_prompt = f"""Describe this Signal Noir cyberpunk scene in 3-4 vivid sentences:

LOCATION: {loc_state["location_desc"]}
WEATHER: {weather_desc}
TIME: Day {tick_state["day"]}, {time_desc}

CHARACTERS PRESENT:
{npcs_text}

{f"ACTION: {action}" if action else ""}

Style: Signal Noir - high contrast grayscale with cyan accents, dark moody noir. 
Describe what a viewer would see entering this scene. Mention specific characters by name.
Keep it cinematic and atmospheric."""

    description = ""
    if HAS_VERTEX and model:
        try:
            response = model.generate_content(scene_prompt)
            description = response.text.strip()
        except Exception as e:
            description = f"[Scene generation error: {e}]"
    else:
        description = f"*{loc_state['location_desc']}. {weather_desc}. {npcs_text}*"
    
    result = {
        "location": location_id,
        "location_desc": loc_state["location_desc"],
        "tick": tick,
        "day": tick_state["day"],
        "hour": tick_state["hour"],
        "weather": tick_state["weather"],
        "npcs_present": [n["name"] for n in loc_state["npcs"]],
        "description": description
    }
    
    # Generate image if requested
    if generate_image and HAS_IMAGEN and imagen_model:
        # Build image prompt
        npc_visuals = ", ".join([n.get("visual", n["name"]) for n in loc_state["npcs"][:3]])  # Max 3 NPCs
        
        image_prompt = f"""Signal Noir cyberpunk scene:

{loc_state["location_desc"]} at {time_desc}.
{weather_desc}.
{f"Characters: {npc_visuals}" if npc_visuals else "Empty location."}

MANDATORY STYLE:
- 85% grayscale, high contrast noir
- ONLY cyan (#00CED1) for neon/tech accents
- Deep black shadows, art deco architecture
- Cinematic composition, dramatic lighting
- NO bright colors except cyan
"""
        
        try:
            images = imagen_model.generate_images(
                prompt=image_prompt,
                number_of_images=1,
                aspect_ratio="16:9",
                safety_filter_level="block_only_high"
            )
            
            if images.images:
                # Return base64 encoded image
                import io
                img_bytes = images.images[0]._pil_image
                buffered = io.BytesIO()
                img_bytes.save(buffered, format="PNG")
                img_b64 = base64.b64encode(buffered.getvalue()).decode()
                result["image_base64"] = img_b64
                result["image_generated"] = True
            else:
                result["image_generated"] = False
                result["image_error"] = "No image generated"
        except Exception as e:
            result["image_generated"] = False
            result["image_error"] = str(e)
    else:
        result["image_generated"] = False
        if generate_image and not HAS_IMAGEN:
            result["image_error"] = "Imagen 3 not available"
    
    return jsonify(result)


# ============================================================
# SIGNAL NOIR SCENE GENERATION
# ============================================================

SIGNAL_NOIR_STYLE = """
SIGNAL NOIR STYLE:
- Render in BLACK AND WHITE / GRAYSCALE
- Deep inky black shadows, high contrast
- ONLY CYAN (#00CED1) accents for tech/neon elements
- NO red, green, yellow, orange, pink, purple
- Mostly night setting, dark moody atmosphere
- Art deco noir meets cyberpunk dystopia
- NOT always raining - use the actual weather provided
"""

NPC_VISUALS = {
    "kira": "Young Japanese woman, short asymmetric black hair, amber glowing eyes, worn coat, spiritual tattoos on neck",
    "cipher": "Androgynous AI entity, cyan circuit patterns under translucent skin, bald with data port, dark tech-suit",
    "marco": "Middle-aged Asian man, weathered face, cybernetic cyan eye, worn leather jacket, shrewd expression",
    "charlie": "Noir detective, 40s, trenchcoat and fedora, cigarette smoke, five o'clock shadow, rain dripping from hat",
    "blade": "Japanese street samurai, muscular, traditional-cyberpunk armor, katana on back, facial scars, cyan cybernetic arm"
}


@app.route("/api/scene/describe", methods=["POST"])
def describe_scene():
    """Generate text description of scene (free, no image generation)."""
    data = request.json
    npc_id = data.get("npc_id", "kira")
    tick = data.get("tick", 100)
    action = data.get("action", "observing the city")
    
    state = get_npc_state(npc_id, tick)
    if not state:
        return jsonify({"error": "NPC not found"}), 404
    
    npc_visual = NPC_VISUALS.get(npc_id, NPC_VISUALS["kira"])
    
    # Determine time of day for scene description
    hour = state['tick_state']['hour']
    if 6 <= hour < 18:
        time_desc = f"Day, {hour}:00 - but the city is always shadowed"
    else:
        time_desc = f"Night, {hour}:00"
    
    weather = state['tick_state']['weather']
    weather_desc = {
        "clear": "Clear skies, neon signs cutting through the darkness",
        "rain": "Rain slicks the streets, reflections everywhere",
        "storm": "Thunder rumbles, lightning illuminates the skyline",
        "fog": "Thick fog rolls through the streets, obscuring everything"
    }.get(weather, "Dark, moody atmosphere")
    
    prompt = f"""Describe this Signal Noir cyberpunk scene in 2-3 vivid sentences:

CHARACTER: {npc_visual}
ACTION: {action}
LOCATION: {state['location_desc']}
WEATHER: {weather_desc}
TIME: {time_desc}

Style: Signal Noir - high contrast grayscale with ONLY cyan neon accents. Dark, moody, art deco noir. NOT always raining - match the weather above.

Write a cinematic scene description:"""
    
    if HAS_VERTEX and model:
        try:
            response = model.generate_content(prompt)
            description = response.text
        except Exception as e:
            description = f"[Error: {e}]"
    else:
        description = f"*{state['name']} stands in the {state['current_location'].replace('_', ' ')}, {state['tick_state']['weather']} weather reflecting off wet surfaces. The cyan glow of distant neon signs casts long shadows.*"
    
    return jsonify({
        "description": description,
        "npc": state["name"],
        "location": state["current_location"],
        "tick": tick,
        "disclaimer": "⚠️ Demo only. For production Signal Noir images, use custom-trained models."
    })


@app.route("/api/scene/prompt", methods=["POST"])
def get_scene_prompt():
    """Get the image generation prompt (for users to use with their own API keys)."""
    data = request.json
    npc_id = data.get("npc_id", "kira")
    tick = data.get("tick", 100)
    action = data.get("action", "standing in the rain")
    
    state = get_npc_state(npc_id, tick)
    if not state:
        return jsonify({"error": "NPC not found"}), 404
    
    npc_visual = NPC_VISUALS.get(npc_id, NPC_VISUALS["kira"])
    
    prompt = f"""{npc_visual}

{action}

LOCATION: {state['location_desc']}
WEATHER: {state['tick_state']['weather']}, wet surfaces
TIME: Night, {state['tick_state']['hour']}:00

{SIGNAL_NOIR_STYLE}

Cinematic wide shot, rule of thirds, dramatic noir lighting."""
    
    return jsonify({
        "prompt": prompt,
        "npc": state["name"],
        "tick": tick,
        "tip": "Use this prompt with Imagen, DALL-E, or Midjourney. Add 'ar:16:9' for widescreen."
    })


# ============================================================
# ARWEAVE UPLOAD PIPELINE INFO
# ============================================================

@app.route("/api/pipeline/info", methods=["GET"])
def pipeline_info():
    """Explain the Arweave upload pipeline."""
    return jsonify({
        "pipeline": {
            "step_1": "Create NPC profile JSON (<100KB for free tier)",
            "step_2": "Tag with App-Name, Type, NPC-Id, NPC-Name, Archetype",
            "step_3": "Upload via Turbo bundler (ar.io) - <100KB is FREE",
            "step_4": "Query via GraphQL to find NPCs",
            "step_5": "Fetch full profile via gateway"
        },
        "upload_command": "Use wandern-arweave-uploader (migrated to Turbo)",
        "tags_required": [
            {"name": "App-Name", "value": "AO-World-Engine"},
            {"name": "Type", "value": "npc_profile"},
            {"name": "NPC-Id", "value": "npc_XXXX"},
            {"name": "NPC-Name", "value": "Character Name"},
            {"name": "Archetype", "value": "archetype_name"}
        ],
        "turbo_info": {
            "mainnet": "https://up.arweave.net (<100KB FREE, permanent)",
            "devnet": "https://upload.ardrive.dev (testing)"
        },
        "current_schema": f"https://arweave.net/{NPC_SCHEMA_TX}"
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🌐 AO World Engine NPC Chat API")
    print(f"   Vertex AI: {'✅' if HAS_VERTEX else '❌ (mock mode)'}")
    print(f"   Arweave Gateway: {ARWEAVE_GATEWAY}")
    print(f"   Running on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)

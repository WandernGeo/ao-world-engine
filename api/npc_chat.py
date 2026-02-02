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
    
    project = os.environ.get("GCP_PROJECT", "wandern-project-startup")
    location = os.environ.get("GCP_LOCATION", "us-central1")
    
    vertexai.init(project=project, location=location)
    model = GenerativeModel("gemini-2.0-flash")
    HAS_VERTEX = True
except Exception as e:
    print(f"⚠️ Vertex AI not available: {e}")
    print("   Running in mock mode with simple responses")


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


def get_npc_state(npc_id: str, tick: int) -> dict:
    """Get NPC state at tick, trying Arweave first then falling back to FOUNDING_NPCS."""
    
    # Try to get from cache/Arweave (would be implemented with proper tx lookup)
    # For now, use founding NPCs
    if npc_id not in FOUNDING_NPCS:
        return None
    
    profile = FOUNDING_NPCS[npc_id].copy()
    tick_state = get_tick_state(tick)
    
    # Deterministic location based on time + NPC
    locations = list(LOCATIONS.keys())
    loc_seed = int(hashlib.md5(f"{npc_id}_{tick // 4}".encode()).hexdigest(), 16)
    home_weight = 0.6  # 60% chance to be at home location
    
    if (loc_seed % 100) < 60 and profile.get("location_home"):
        current_loc = profile["location_home"]
    else:
        current_loc = locations[loc_seed % len(locations)]
    
    # Deterministic mood
    moods = ["contemplative", "wary", "restless", "focused", "agitated"]
    mood_seed = int(hashlib.md5(f"{npc_id}_mood_{tick // 8}".encode()).hexdigest(), 16)
    current_mood = moods[mood_seed % len(moods)]
    
    return {
        "npc_id": npc_id,
        "name": profile["name"],
        "archetype": profile["archetype"],
        "personality": profile.get("personality_vector", {}),
        "current_location": current_loc,
        "location_desc": LOCATIONS.get(current_loc, "unknown location"),
        "current_mood": current_mood,
        "tick_state": tick_state,
        "topics": profile.get("topic_weights", {}),
        "source": "founding_npc"  # Will change to "arweave" when fetched
    }


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok", 
        "vertex_ai": HAS_VERTEX,
        "arweave_gateway": ARWEAVE_GATEWAY
    })


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


@app.route("/api/npc/chat", methods=["POST"])
def npc_chat():
    """Chat with an NPC using Vertex AI with deterministic memories."""
    data = request.json
    npc_id = data.get("npc_id", "charlie")
    tick = data.get("tick", 100)
    message = data.get("message", "Hello")
    
    npc_state = get_npc_state(npc_id, tick)
    if not npc_state:
        return jsonify({"error": "NPC not found"}), 404
    
    # Build prompt from NPC state
    personality = npc_state.get("personality", {})
    topics = npc_state.get("topics", {})
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
    
    system_prompt = f"""You are {npc_state['name']}, a {npc_state['archetype']} in RE:ECHO City.

APPEARANCE:
{visual_desc if visual_desc else 'A citizen of the cyberpunk metropolis.'}

BACKSTORY:
{backstory}

CURRENT STATE:
- Location: {npc_state['location_desc']}
- Mood: {npc_state['current_mood']}
- Time: Tick {tick} (Day {npc_state['tick_state']['day']}, {npc_state['tick_state']['hour']}:00)
- Weather: {npc_state['tick_state']['weather']}

PERSONALITY (0-1 scale):
- Paranoia: {personality.get('paranoia', 0.5)}
- Mysticism: {personality.get('mysticism', 0.5)}
- Aggression: {personality.get('aggression', 0.5)}
- Intelligence: {personality.get('intelligence', 0.5)}
- Empathy: {personality.get('empathy', 0.5)}

{memory_context if memory_context else "No significant recent memories."}

RELATIONSHIPS:
{relationship_context if relationship_context else "You are cautious with most people."}

SIGNATURE PHRASES (use naturally):
{json.dumps(catchphrases, indent=2) if catchphrases else "None defined"}

RULES:
- Stay in character at all times
- Reference your memories and relationships when relevant
- Keep responses concise (2-4 sentences max)
- Use your personality traits to color your speech
- If paranoia is high, be suspicious. If mysticism is high, speak cryptically.
- You can reference other NPCs you've interacted with
"""
    
    if HAS_VERTEX and model:
        try:
            response = model.generate_content(
                f"{system_prompt}\n\nUser says: {message}\n\nRespond as {npc_state['name']}:"
            )
            npc_response = response.text
        except Exception as e:
            npc_response = f"[Error: {e}]"
    else:
        # Fallback mock response
        import random
        npc_response = random.choice(catchphrases) if catchphrases else "..."
    
    return jsonify({
        "npc": npc_state["name"],
        "response": npc_response,
        "memories_enabled": HAS_EVENT_ENGINE,
        "state": {
            "tick": tick,
            "location": npc_state["current_location"],
            "mood": npc_state["current_mood"],
            "weather": npc_state["tick_state"]["weather"],
            "hour": npc_state["tick_state"]["hour"],
            "day": npc_state["tick_state"]["day"]
        }
    })


@app.route("/api/tick/<int:tick>", methods=["GET"])
def get_tick(tick: int):
    """Get world state at tick."""
    return jsonify(get_tick_state(tick))


# ============================================================
# SIGNAL NOIR SCENE GENERATION
# ============================================================

SIGNAL_NOIR_STYLE = """
SIGNAL NOIR STYLE - MANDATORY:
- Render in BLACK AND WHITE / GRAYSCALE
- Deep inky black shadows, high contrast
- ONLY CYAN (#00CED1) accents for tech/neon  
- NO red, green, yellow, orange, pink, purple
- Cyberpunk dystopian, rain atmosphere
- Sin City / Blade Runner aesthetic
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
    action = data.get("action", "standing in the rain")
    
    state = get_npc_state(npc_id, tick)
    if not state:
        return jsonify({"error": "NPC not found"}), 404
    
    npc_visual = NPC_VISUALS.get(npc_id, NPC_VISUALS["kira"])
    
    prompt = f"""Describe this Signal Noir cyberpunk scene in 2-3 vivid sentences:

CHARACTER: {npc_visual}
ACTION: {action}
LOCATION: {state['location_desc']}
WEATHER: {state['tick_state']['weather']}
TIME: Night, {state['tick_state']['hour']}:00

Style: High contrast black and white, cyan neon accents only, rain, noir atmosphere.

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

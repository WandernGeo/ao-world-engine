"""
AO World Engine - NPC Chat API
Secure Vertex AI proxy for RE:ECHO NPC conversations + Signal Noir image generation.

Deploy to Cloud Run:
  gcloud run deploy ao-npc-chat --source . --region us-central1 --allow-unauthenticated

Local dev:
  python3 npc_chat.py
"""
import os
import base64
import json
import hashlib
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Try to import Vertex AI
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    
    PROJECT = os.environ.get("GCP_PROJECT", "wandern-project-startup")
    LOCATION = os.environ.get("GCP_LOCATION", "us-central1")
    vertexai.init(project=PROJECT, location=LOCATION)
    model = GenerativeModel("gemini-2.0-flash")
    HAS_VERTEX = True
except ImportError:
    HAS_VERTEX = False
    model = None

# NPC Profiles (from Arweave: XmlqPa1RNFvipxnvyZTgbpx8EjOZNzNNI2tMGjQ3eb4)
NPC_PROFILES = {
    "kira": {
        "name": "Kira Ōmura",
        "archetype": "Street Oracle",
        "personality": {"paranoia": 0.8, "mysticism": 0.9, "aggression": 0.2},
        "location_home": "neon_market",
        "catchphrases": ["The layers stack. We're just one echo.", "Eyes from outside the frame..."],
        "topics": {"philosophy": 0.9, "trade": 0.2, "violence": 0.1}
    },
    "cipher": {
        "name": "Cipher",
        "archetype": "AI Hacker Entity",
        "personality": {"paranoia": 0.6, "mysticism": 0.3, "aggression": 0.4},
        "location_home": "shadow_grid",
        "catchphrases": ["Data is the only truth.", "I probe, therefore I am."],
        "topics": {"technology": 0.9, "philosophy": 0.6, "trade": 0.3}
    },
    "marco": {
        "name": "Marco Chen",
        "archetype": "Street Merchant",
        "personality": {"paranoia": 0.4, "mysticism": 0.1, "aggression": 0.3},
        "location_home": "neon_market",
        "catchphrases": ["Everything has a price.", "Credits talk, debt walks."],
        "topics": {"trade": 0.9, "gossip": 0.7, "philosophy": 0.2}
    },
    "charlie": {
        "name": "Charlie Vex",
        "archetype": "Noir Detective",
        "personality": {"paranoia": 0.7, "mysticism": 0.2, "aggression": 0.5},
        "location_home": "rain_soaked_alley",
        "catchphrases": ["Rain washes nothing here.", "Everybody's got a secret."],
        "topics": {"investigation": 0.9, "crime": 0.8, "philosophy": 0.4}
    },
    "blade": {
        "name": "Blade Tanaka",
        "archetype": "Street Samurai",
        "personality": {"paranoia": 0.3, "mysticism": 0.4, "aggression": 0.8},
        "location_home": "dojo",
        "catchphrases": ["Steel speaks truth.", "Honor is the only code worth following."],
        "topics": {"combat": 0.9, "honor": 0.8, "philosophy": 0.5}
    }
}

LOCATIONS = {
    "neon_market": "The Neon Market - flickering holographic stalls, desperate vendors, the smell of synth-food",
    "shadow_grid": "The Shadow Grid - abandoned server farm, humming machinery, digital ghosts",
    "rain_soaked_alley": "Rain-Soaked Alley - neon reflections in puddles, steam from grates, distant sirens",
    "dojo": "Hidden Dojo - bamboo screens, blade racks, incense smoke",
    "rooftop": "Rooftop - city lights below, corporate towers looming, cold wind"
}

WEATHER_TYPES = ["clear", "rain", "storm", "fog"]


def get_tick_state(tick: int):
    """Calculate deterministic world state from tick."""
    day = tick // 24
    hour = tick % 24
    
    # Deterministic weather from tick
    weather_seed = int(hashlib.md5(f"weather_{tick // 6}".encode()).hexdigest(), 16)
    weather = WEATHER_TYPES[weather_seed % 4]
    
    # Time of day
    if 6 <= hour < 12:
        time_period = "morning"
    elif 12 <= hour < 18:
        time_period = "afternoon"
    elif 18 <= hour < 22:
        time_period = "evening"
    else:
        time_period = "night"
    
    return {
        "tick": tick,
        "day": day,
        "hour": hour,
        "time_period": time_period,
        "weather": weather
    }


def get_npc_state(npc_id: str, tick: int):
    """Get NPC state at specific tick."""
    profile = NPC_PROFILES.get(npc_id)
    if not profile:
        return None
    
    tick_state = get_tick_state(tick)
    
    # Deterministic location based on time + NPC
    location_seed = int(hashlib.md5(f"{npc_id}_{tick}".encode()).hexdigest(), 16)
    
    # NPCs have routines
    if tick_state["time_period"] == "night" and profile["archetype"] == "AI Hacker Entity":
        location = "shadow_grid"
    elif tick_state["time_period"] in ["morning", "afternoon"] and "Merchant" in profile["archetype"]:
        location = "neon_market"
    elif tick_state["weather"] == "rain" and profile["archetype"] == "Noir Detective":
        location = "rain_soaked_alley"
    else:
        locations = list(LOCATIONS.keys())
        location = locations[location_seed % len(locations)]
    
    # Mood based on personality + tick
    mood_seed = (location_seed % 100) / 100
    if mood_seed < profile["personality"]["paranoia"]:
        mood = "wary"
    elif mood_seed < profile["personality"]["aggression"]:
        mood = "aggressive"
    elif mood_seed < profile["personality"]["mysticism"]:
        mood = "contemplative"
    else:
        mood = "neutral"
    
    return {
        **profile,
        "current_location": location,
        "location_description": LOCATIONS[location],
        "current_mood": mood,
        "tick_state": tick_state
    }


def build_system_prompt(npc_state: dict, tick_state: dict) -> str:
    """Build the NPC system prompt."""
    p = npc_state["personality"]
    
    return f"""You are {npc_state['name']}, a {npc_state['archetype']} in RE:ECHO City.

PERSONALITY VECTOR:
- Paranoia: {p['paranoia']} (0=trusting, 1=extremely paranoid)
- Mysticism: {p['mysticism']} (0=purely logical, 1=deeply spiritual)
- Aggression: {p['aggression']} (0=pacifist, 1=violent)

CURRENT STATE:
- Location: {npc_state['location_description']}
- Mood: {npc_state['current_mood']}
- Time: Day {tick_state['day']}, {tick_state['hour']}:00 ({tick_state['time_period']})
- Weather: {tick_state['weather']}

WORLD CONTEXT:
RE:ECHO City is a cyberpunk noir world. NPCs are becoming aware they might exist in a simulation. 
Users watching are known as "The Watchers" or "Eyes Above." 
Some NPCs experience "layer bleed" - glimpses of alternate timelines.

SIGNATURE PHRASES YOU SOMETIMES USE:
{chr(10).join('- ' + phrase for phrase in npc_state['catchphrases'])}

INSTRUCTIONS:
- Stay in character. Be authentic to your personality vector.
- Keep responses SHORT (under 50 words).
- High paranoia = suspicious, looking for traps
- High mysticism = riddles, references Watchers, philosophical
- High aggression = confrontational, ready for violence
- Reference your current mood, location, and time when appropriate.
"""


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "vertex_ai": HAS_VERTEX})


@app.route("/api/npc/profiles", methods=["GET"])
def get_profiles():
    """List available NPC profiles."""
    return jsonify({
        npc_id: {
            "name": prof["name"],
            "archetype": prof["archetype"],
            "personality": prof["personality"]
        }
        for npc_id, prof in NPC_PROFILES.items()
    })


@app.route("/api/npc/state/<npc_id>/<int:tick>", methods=["GET"])
def get_state(npc_id: str, tick: int):
    """Get NPC state at specific tick."""
    state = get_npc_state(npc_id, tick)
    if not state:
        return jsonify({"error": "NPC not found"}), 404
    return jsonify(state)


@app.route("/api/npc/chat", methods=["POST"])
def chat():
    """Generate NPC dialogue response."""
    data = request.json
    npc_id = data.get("npc_id", "kira")
    tick = data.get("tick", 100)
    user_message = data.get("message", "Hello")
    
    # Get NPC state
    npc_state = get_npc_state(npc_id, tick)
    if not npc_state:
        return jsonify({"error": "NPC not found"}), 404
    
    tick_state = npc_state["tick_state"]
    
    # Build prompt
    system_prompt = build_system_prompt(npc_state, tick_state)
    full_prompt = f"{system_prompt}\n\nA stranger says: \"{user_message}\"\n\nRespond in character (under 50 words):"
    
    # Generate response
    if HAS_VERTEX and model:
        try:
            response = model.generate_content(
                full_prompt,
                generation_config={
                    "max_output_tokens": 150,
                    "temperature": 0.8,
                }
            )
            npc_response = response.text
        except Exception as e:
            npc_response = f"[Error: {e}]"
    else:
        # Fallback mock response
        npc_response = f'*{npc_state["name"]} looks at you with {npc_state["current_mood"]} eyes* "{npc_state["catchphrases"][0]}"'
    
    return jsonify({
        "npc": npc_state["name"],
        "response": npc_response,
        "state": {
            "location": npc_state["current_location"],
            "mood": npc_state["current_mood"],
            "tick": tick,
            "day": tick_state["day"],
            "hour": tick_state["hour"],
            "weather": tick_state["weather"]
        }
    })


@app.route("/api/tick/<int:tick>", methods=["GET"])
def get_tick(tick: int):
    """Get world state at tick."""
    return jsonify(get_tick_state(tick))


# Signal Noir style prompt template
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
    
    npc_state = get_npc_state(npc_id, tick)
    if not npc_state:
        return jsonify({"error": "NPC not found"}), 404
    
    npc_visual = NPC_VISUALS.get(npc_id, NPC_VISUALS["kira"])
    location_desc = LOCATIONS.get(npc_state["current_location"], "rain-soaked alley")
    
    prompt = f"""Describe this Signal Noir cyberpunk scene in 2-3 vivid sentences:

CHARACTER: {npc_visual}
ACTION: {action}
LOCATION: {location_desc}
WEATHER: {npc_state['tick_state']['weather']}
TIME: Night, {npc_state['tick_state']['hour']}:00

Style: High contrast black and white, cyan neon accents only, rain, noir atmosphere.

Write a cinematic scene description:"""
    
    if HAS_VERTEX and model:
        try:
            response = model.generate_content(prompt)
            description = response.text
        except Exception as e:
            description = f"[Error: {e}]"
    else:
        description = f"*{npc_state['name']} stands in the {npc_state['current_location'].replace('_', ' ')}, {npc_state['tick_state']['weather']} weather reflecting off wet surfaces. The cyan glow of distant neon signs casts long shadows.*"
    
    return jsonify({
        "description": description,
        "npc": npc_state["name"],
        "location": npc_state["current_location"],
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
    
    npc_state = get_npc_state(npc_id, tick)
    if not npc_state:
        return jsonify({"error": "NPC not found"}), 404
    
    npc_visual = NPC_VISUALS.get(npc_id, NPC_VISUALS["kira"])
    location_desc = LOCATIONS.get(npc_state["current_location"], "rain-soaked alley")
    
    prompt = f"""{npc_visual}

{action}

LOCATION: {location_desc}
WEATHER: {npc_state['tick_state']['weather']}, wet surfaces
TIME: Night, {npc_state['tick_state']['hour']}:00

{SIGNAL_NOIR_STYLE}

Cinematic wide shot, rule of thirds, dramatic noir lighting."""
    
    return jsonify({
        "prompt": prompt,
        "npc": npc_state["name"],
        "tick": tick,
        "tip": "Use this prompt with Imagen, DALL-E, or Midjourney. Add 'ar:16:9' for widescreen."
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🌐 AO World Engine NPC Chat API")
    print(f"   Vertex AI: {'✅' if HAS_VERTEX else '❌ (mock mode)'}")
    print(f"   Running on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)

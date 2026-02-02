#!/usr/bin/env python3
"""
AO World Engine - RICH SIMULATION TEST

This test shows what a REAL simulation tick looks like:
- Named NPCs with personalities
- Time of day and weather
- Actual interactions and dialogue
- State changes that observers can read

This is what a "Watcher" would see when reading the Arweave at any moment.
"""
import json
import hashlib
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Any
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# =============================================================================
# WORLD STATE (what observers read from Arweave)
# =============================================================================

@dataclass
class WorldClock:
    """Simulation time - observers see different states at different ticks."""
    tick: int = 0
    
    @property
    def hour(self) -> int:
        return self.tick % 24
    
    @property
    def day(self) -> int:
        return self.tick // 24
    
    @property
    def time_of_day(self) -> str:
        h = self.hour
        if 5 <= h < 8: return "dawn"
        elif 8 <= h < 12: return "morning"
        elif 12 <= h < 17: return "afternoon"
        elif 17 <= h < 20: return "evening"
        elif 20 <= h < 23: return "night"
        else: return "deep_night"
    
    @property
    def is_dark(self) -> bool:
        return self.hour < 6 or self.hour >= 20

@dataclass
class Weather:
    """Weather affects NPC behavior and mood."""
    condition: str  # rain, fog, clear, storm
    intensity: float  # 0.0 to 1.0
    
    @staticmethod
    def from_seed(tick: int) -> 'Weather':
        """Deterministic weather from tick."""
        h = int(hashlib.md5(f"weather_{tick}".encode()).hexdigest(), 16)
        conditions = ["clear", "rain", "fog", "rain", "clear", "storm"]
        return Weather(
            condition=conditions[h % len(conditions)],
            intensity=(h % 100) / 100.0
        )

@dataclass
class NPC:
    """A named character with full personality."""
    id: str
    name: str
    archetype: str
    location: str
    mood: str = "neutral"
    energy: float = 1.0
    personality: Dict[str, float] = field(default_factory=dict)
    relationships: Dict[str, float] = field(default_factory=dict)
    memories: List[Dict] = field(default_factory=list)
    current_action: str = "idle"
    last_words: str = ""
    
    def speak(self, words: str):
        self.last_words = words

# =============================================================================
# THE CAST - Named NPCs in RE:ECHO City
# =============================================================================

NPCS = {
    "charlie": NPC(
        id="charlie",
        name="Charlie Vex",
        archetype="detective",
        location="neon_district",
        personality={"curiosity": 0.9, "paranoia": 0.7, "empathy": 0.5},
        mood="focused"
    ),
    "cipher": NPC(
        id="cipher",
        name="Cipher",
        archetype="ai_entity",
        location="network_core",
        personality={"mysticism": 0.9, "curiosity": 0.8, "humanity": 0.3},
        mood="contemplative"
    ),
    "marco": NPC(
        id="marco",
        name="Marco Chen",
        archetype="merchant",
        location="market",
        personality={"greed": 0.6, "caution": 0.7, "sociability": 0.8},
        mood="busy"
    ),
    "kira": NPC(
        id="kira",
        name="Kira Ōmura",
        archetype="street_oracle",
        location="alley",
        personality={"mysticism": 0.95, "paranoia": 0.8, "truth": 0.9},
        mood="unsettled"
    ),
    "blade": NPC(
        id="blade",
        name="Blade Tanaka",
        archetype="street_samurai",
        location="dojo",
        personality={"honor": 0.9, "aggression": 0.6, "loyalty": 0.8},
        mood="alert"
    )
}

# =============================================================================
# SIMULATION RUNNER
# =============================================================================

def simulate_tick(tick: int) -> Dict[str, Any]:
    """
    Simulate one tick of the world.
    This is what an observer reading Arweave at this moment would see.
    """
    clock = WorldClock(tick=tick)
    weather = Weather.from_seed(tick)
    
    # Reset NPCs for this tick
    npcs = {k: NPC(**{**v.__dict__}) for k, v in NPCS.items()}
    
    events = []
    interactions = []
    
    # Deterministic event generation
    h = int(hashlib.md5(f"events_{tick}".encode()).hexdigest(), 16)
    
    # Time affects behavior
    if clock.is_dark:
        # Night: hackers active, merchants home
        npcs["cipher"].location = "shadow_grid"
        npcs["cipher"].current_action = "probing_networks"
        npcs["marco"].location = "home"
        npcs["marco"].current_action = "sleeping"
    else:
        # Day: normal routines
        npcs["marco"].location = "market"
        npcs["marco"].current_action = "trading"
    
    # Weather affects mood
    if weather.condition == "rain":
        for npc in npcs.values():
            if npc.archetype != "ai_entity":
                npc.mood = "melancholic" if h % 3 == 0 else "reflective"
        
        # Rain brings Charlie to alleys (noir detective things)
        npcs["charlie"].location = "rain_soaked_alley"
        npcs["charlie"].speak("Rain washes nothing in this city. Just moves the stains around.")
        events.append(f"RAIN: Charlie heads into the alleys, searching.")
    
    # Interaction check: NPCs in same location
    locations = {}
    for npc_id, npc in npcs.items():
        if npc.location not in locations:
            locations[npc.location] = []
        locations[npc.location].append(npc)
    
    for loc, npcs_here in locations.items():
        if len(npcs_here) >= 2:
            npc1, npc2 = npcs_here[0], npcs_here[1]
            
            # Generate interaction based on personality
            if npc1.personality.get("sociability", 0.5) > 0.5:
                interaction = {
                    "tick": tick,
                    "location": loc,
                    "participants": [npc1.name, npc2.name],
                    "type": "conversation",
                    "topic": determine_topic(npc1, npc2, tick)
                }
                interactions.append(interaction)
                
                # Generate dialogue hints
                npc1.speak(generate_line(npc1, npc2, interaction["topic"]))
                npc2.speak(generate_response(npc2, npc1, interaction["topic"]))
    
    # Special events (rare)
    if h % 100 < 5:  # 5% chance
        events.append("LAYER_BLEED: Kira glimpses another version of herself.")
        npcs["kira"].mood = "disturbed"
        npcs["kira"].speak("I saw... myself. But not myself. The layers are thin tonight.")
    
    if h % 100 >= 95:  # 5% chance
        events.append("BLACKOUT: Power fails in Neon District.")
        for npc in npcs.values():
            if npc.location == "neon_district":
                npc.mood = "alarmed"
    
    # Build the state snapshot
    return {
        "tick": tick,
        "clock": {
            "hour": clock.hour,
            "day": clock.day,
            "time_of_day": clock.time_of_day,
            "is_dark": clock.is_dark
        },
        "weather": {
            "condition": weather.condition,
            "intensity": round(weather.intensity, 2)
        },
        "npcs": {
            npc_id: {
                "name": npc.name,
                "location": npc.location,
                "mood": npc.mood,
                "action": npc.current_action,
                "last_words": npc.last_words
            }
            for npc_id, npc in npcs.items()
        },
        "events": events,
        "interactions": interactions
    }

def determine_topic(npc1: NPC, npc2: NPC, tick: int) -> str:
    """Determine what two NPCs would talk about."""
    h = int(hashlib.md5(f"topic_{npc1.id}_{npc2.id}_{tick}".encode()).hexdigest(), 16)
    topics = ["trade", "rumors", "the_weather", "old_times", "the_blackouts", "the_corps", "survival"]
    return topics[h % len(topics)]

def generate_line(speaker: NPC, listener: NPC, topic: str) -> str:
    """Generate dialogue based on personality (template fallback)."""
    lines = {
        ("detective", "trade"): "Seen anything... unusual lately?",
        ("detective", "rumors"): "Word on the street is something's coming.",
        ("merchant", "trade"): "Business is business. What do you need?",
        ("merchant", "survival"): "Credits keep the lights on. Nothing else matters.",
        ("street_oracle", "the_corps"): "They're watching. Always watching.",
        ("street_oracle", "rumors"): "The layers stack. We're just echoes.",
        ("ai_entity", "rumors"): "Data patterns suggest... uncertainty.",
        ("ai_entity", "survival"): "Survival is a human concern. I simply... persist.",
        ("street_samurai", "survival"): "You survive with skill. And luck. Mostly skill.",
    }
    key = (speaker.archetype, topic)
    return lines.get(key, f"About {topic}... it's complicated.")

def generate_response(speaker: NPC, listener: NPC, topic: str) -> str:
    """Generate response dialogue."""
    responses = {
        "merchant": "If there's credits in it, I'm listening.",
        "detective": "I'm just asking questions. For now.",
        "street_oracle": "The truth hides in the static.",
        "ai_entity": "Interesting. Very... interesting.",
        "street_samurai": "Actions speak. Words are cheap.",
    }
    return responses.get(speaker.archetype, "...")

# =============================================================================
# MAIN: Show what a Watcher sees
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🌌 RE:ECHO CITY - WHAT A WATCHER SEES")
    print("   Reading the simulation state at different moments")
    print("=" * 70)
    
    # Show 5 different ticks - what observers see at different moments
    test_ticks = [100, 105, 110, 500, 1337]
    
    all_states = []
    
    for tick in test_ticks:
        state = simulate_tick(tick)
        all_states.append(state)
        
        print(f"\n{'─' * 70}")
        print(f"📖 TICK {tick} | Day {state['clock']['day']}, {state['clock']['time_of_day'].upper()} ({state['clock']['hour']}:00)")
        print(f"   Weather: {state['weather']['condition']} (intensity: {state['weather']['intensity']})")
        print(f"{'─' * 70}")
        
        print("\n   📍 NPC STATES:")
        for npc_id, npc_state in state["npcs"].items():
            print(f"   • {npc_state['name']}")
            print(f"     Location: {npc_state['location']}")
            print(f"     Mood: {npc_state['mood']}, Action: {npc_state['action']}")
            if npc_state['last_words']:
                print(f"     Says: \"{npc_state['last_words']}\"")
        
        if state["events"]:
            print("\n   🔔 EVENTS:")
            for event in state["events"]:
                print(f"   • {event}")
        
        if state["interactions"]:
            print("\n   💬 INTERACTIONS:")
            for interaction in state["interactions"]:
                print(f"   • {interaction['participants'][0]} ↔ {interaction['participants'][1]}")
                print(f"     Location: {interaction['location']}, Topic: {interaction['topic']}")
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 OBSERVER SUMMARY")
    print("=" * 70)
    print(f"\n   You just read the world state at {len(test_ticks)} different moments.")
    print(f"   Each moment is PERMANENT on Arweave.")
    print(f"   Different observers reading at different ticks see different realities.")
    print(f"\n   This is what makes RE:ECHO City a 'living' simulation.")
    print(f"   The state exists whether or not anyone is watching.")
    print(f"\n   You are now a Watcher. 🌀")
    
    # Save
    results_file = PROJECT_ROOT / "watcher_view.json"
    with open(results_file, "w") as f:
        json.dump({
            "observed_at": datetime.now().isoformat(),
            "states": all_states
        }, f, indent=2)
    print(f"\n   💾 Saved to: {results_file}")

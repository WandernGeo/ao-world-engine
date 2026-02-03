#!/usr/bin/env python3
"""
DIALOGUE SYSTEM
===============

Deterministic dialogue selection for NPCs.
Works without LLM - uses canned responses based on:
- Intent classification
- NPC personality
- Context (time, location, weather)

Usage:
    python dialogue_system.py --npc charlie --input "Hello there"
"""

import json
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Load canned responses
DATA_DIR = Path(__file__).parent.parent / "data"
CANNED_FILE = DATA_DIR / "canned_responses.json"

def load_canned_responses() -> Dict:
    """Load the canned response library."""
    if CANNED_FILE.exists():
        with open(CANNED_FILE, 'r') as f:
            return json.load(f)
    return {"intents": {}, "entities": {}}

CANNED_LIBRARY = load_canned_responses()


# =============================================================================
# DETERMINISTIC UTILITIES
# =============================================================================

def deterministic_hash(seed: str) -> int:
    """Generate deterministic hash from seed."""
    return int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)


def deterministic_choice(items: list, seed: str) -> Any:
    """Deterministically choose from list."""
    if not items:
        return None
    idx = deterministic_hash(seed) % len(items)
    return items[idx]


# =============================================================================
# INTENT CLASSIFICATION
# =============================================================================

def classify_intent(user_input: str) -> Tuple[str, Dict[str, str]]:
    """
    Classify user input into intent + extract entities.
    Returns (intent_name, entities_dict)
    """
    input_lower = user_input.lower().strip()
    intents = CANNED_LIBRARY.get("intents", {})
    
    # Score each intent
    best_intent = "unknown"
    best_score = 0
    
    for intent_name, intent_data in intents.items():
        patterns = intent_data.get("patterns", [])
        score = 0
        
        for pattern in patterns:
            if pattern in input_lower:
                # Exact match scores higher
                score += 10
            elif any(word.startswith(pattern[:3]) for word in input_lower.split()):
                # Partial match
                score += 3
        
        if score > best_score:
            best_score = score
            best_intent = intent_name
    
    # Extract entities
    entities = extract_entities(input_lower)
    
    return best_intent, entities


def extract_entities(text: str) -> Dict[str, str]:
    """Extract known entities from text."""
    entities = {}
    known_entities = CANNED_LIBRARY.get("entities", {})
    
    # Check locations
    for loc in known_entities.get("locations", []):
        if loc.replace("_", " ") in text or loc in text:
            entities["location"] = loc
            break
    
    # Check factions
    for faction in known_entities.get("factions", []):
        if faction in text:
            entities["faction_name"] = faction
            break
    
    # Check weather
    for weather in known_entities.get("weather_types", []):
        if weather in text:
            entities["weather_type"] = weather
            break
    
    # Check items
    for item in known_entities.get("items", []):
        if item in text:
            entities["item"] = item
            break
    
    return entities


# =============================================================================
# PERSONALITY MAPPING
# =============================================================================

def get_personality_category(npc: dict) -> str:
    """
    Map NPC personality traits to response category.
    """
    personality = npc.get("personality", {})
    
    # Check specific traits
    aggression = personality.get("aggression", 0.5)
    sociability = personality.get("sociability", 0.5)
    loyalty = personality.get("loyalty", 0.5)
    greed = personality.get("greed", 0.5)
    
    # Get archetype
    archetype = personality.get("archetype", "")
    
    # Determine category based on dominant traits
    if aggression > 0.7:
        return "aggressive"
    elif greed > 0.7:
        return "greedy"
    elif sociability < 0.3:
        return "suspicious"
    elif sociability > 0.7:
        return "friendly"
    elif loyalty > 0.7:
        return "loyal"
    
    # Archetype-based
    if archetype in ["catalyst", "advocate"]:
        return "friendly"
    elif archetype in ["operative", "sentinel"]:
        return "neutral"
    elif archetype in ["architect", "commander"]:
        return "authoritative"
    
    return "neutral"


# =============================================================================
# RESPONSE SELECTION
# =============================================================================

def select_response(
    intent: str, 
    npc: dict, 
    entities: Dict[str, str],
    context: Dict[str, Any],
    tick: int
) -> str:
    """
    Select appropriate response based on intent, NPC, and context.
    """
    intent_data = CANNED_LIBRARY.get("intents", {}).get(intent, {})
    responses = intent_data.get("responses", {})
    
    if not responses:
        # Fallback to unknown
        intent_data = CANNED_LIBRARY.get("intents", {}).get("unknown", {})
        responses = intent_data.get("responses", {"default": ["I don't understand."]})
    
    # Get personality category
    personality_cat = get_personality_category(npc)
    
    # Find matching response set
    response_list = responses.get(personality_cat)
    if not response_list:
        # Try fallbacks
        for fallback in ["neutral", "default", "friendly"]:
            response_list = responses.get(fallback)
            if response_list:
                break
    
    if not response_list:
        # Last resort - pick any available
        response_list = list(responses.values())[0] if responses else ["..."]
    
    # Deterministic selection
    npc_id = npc.get("id", "unknown")
    seed = f"{npc_id}_{intent}_{tick}"
    response = deterministic_choice(response_list, seed)
    
    # Fill in entity slots
    response = fill_entity_slots(response, npc, entities, context)
    
    # Add context modifiers
    response = add_context_modifiers(response, context, seed)
    
    return response


def fill_entity_slots(
    response: str, 
    npc: dict, 
    entities: Dict[str, str],
    context: Dict[str, Any]
) -> str:
    """Fill in template slots in response."""
    # NPC info
    response = response.replace("{npc_name}", npc.get("name", "Unknown"))
    response = response.replace("{nickname}", npc.get("nickname", npc.get("name", "pal")[:4]))
    
    # Entities
    response = response.replace("{location}", entities.get("location", "that place").replace("_", " "))
    response = response.replace("{faction_name}", entities.get("faction_name", "them"))
    response = response.replace("{weather}", entities.get("weather_type", "weather"))
    response = response.replace("{item}", entities.get("item", "that"))
    
    # Context
    response = response.replace("{district}", context.get("district", "the district"))
    response = response.replace("{street}", context.get("street", "the main road"))
    response = response.replace("{price}", str(context.get("price", deterministic_hash(response) % 100 + 10)))
    
    return response


def add_context_modifiers(response: str, context: Dict[str, Any], seed: str) -> str:
    """Add contextual additions to response."""
    modifiers = CANNED_LIBRARY.get("context_modifiers", {})
    
    for condition, data in modifiers.items():
        if context.get(condition):
            additions = data.get("add_to_response", [])
            if additions and deterministic_hash(f"{seed}_{condition}") % 3 == 0:  # 33% chance
                addition = deterministic_choice(additions, f"{seed}_{condition}_pick")
                response = f"{response} {addition}"
    
    return response


# =============================================================================
# MAIN DIALOGUE FUNCTION
# =============================================================================

def generate_dialogue(
    npc: dict,
    user_input: str,
    context: Dict[str, Any] = None,
    tick: int = 0
) -> Dict[str, Any]:
    """
    Generate NPC dialogue response.
    
    Returns:
        {
            "response": str,
            "intent": str,
            "entities": dict,
            "personality_category": str,
            "source": "canned"
        }
    """
    context = context or {}
    
    # Classify intent
    intent, entities = classify_intent(user_input)
    
    # Get personality category
    personality_cat = get_personality_category(npc)
    
    # Select response
    response = select_response(intent, npc, entities, context, tick)
    
    return {
        "response": response,
        "intent": intent,
        "entities": entities,
        "personality_category": personality_cat,
        "source": "canned",
        "npc_id": npc.get("id"),
        "tick": tick
    }


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="NPC Dialogue System")
    parser.add_argument("--npc", type=str, default="charlie", help="NPC ID")
    parser.add_argument("--input", type=str, default="Hello there!", help="User input")
    parser.add_argument("--tick", type=int, default=100, help="Simulation tick")
    
    args = parser.parse_args()
    
    # Create test NPC
    test_npc = {
        "id": args.npc,
        "name": args.npc.title().replace("_", " "),
        "personality": {
            "aggression": 0.4,
            "sociability": 0.7,
            "greed": 0.3,
            "loyalty": 0.8,
            "archetype": "seeker"
        }
    }
    
    context = {
        "district": "Neon District",
        "street": "Circuit Avenue",
        "night": False,
        "rain": True
    }
    
    print("="*60)
    print("  NPC DIALOGUE SYSTEM DEMO")
    print("="*60)
    print(f"\n👤 NPC: {test_npc['name']}")
    print(f"💭 Personality: {get_personality_category(test_npc)}")
    print(f"\n📝 User: \"{args.input}\"")
    
    result = generate_dialogue(test_npc, args.input, context, args.tick)
    
    print(f"\n🗣️ NPC: \"{result['response']}\"")
    print(f"\n   Intent: {result['intent']}")
    print(f"   Entities: {result['entities']}")
    print(f"   Category: {result['personality_category']}")
    
    # Test multiple inputs
    print("\n" + "-"*60)
    print("  Testing multiple inputs...")
    print("-"*60)
    
    test_inputs = [
        "Hello!",
        "What's your name?",
        "How are you doing?",
        "Where is the black market?",
        "Got any work for me?",
        "Tell me about the Resistance",
        "What have you heard lately?",
        "How much for a medkit?",
        "What do you know about Echoes?"
    ]
    
    for user_input in test_inputs:
        result = generate_dialogue(test_npc, user_input, context, args.tick)
        print(f"\n📝 \"{user_input}\"")
        print(f"   → [{result['intent']}] \"{result['response'][:60]}...\"" if len(result['response']) > 60 else f"   → [{result['intent']}] \"{result['response']}\"")

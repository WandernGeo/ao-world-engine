#!/usr/bin/env python3
"""
EMBEDDED NLU - Natural Language Understanding without ML
=========================================================

Robust intent classification using:
- Keyword matching with scoring
- Fuzzy matching for typos
- Basic stemming via lookup tables
- N-gram phrase matching
- Confidence thresholds

Works on AO (Lua) and local (Python) - no spaCy/ML needed.

Usage:
    python nlu_engine.py --input "How's the weather?"
"""

import json
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

# =============================================================================
# DATA LOADING
# =============================================================================

DATA_DIR = Path(__file__).parent.parent / "data"

def load_json(filename: str) -> dict:
    """Load JSON file from data directory."""
    path = DATA_DIR / filename
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    return {}

# Load context intents (activity/location aware)
CONTEXT_INTENTS = load_json("context_intents.json")
# Load intent data
SMALL_TALK = load_json("small_talk_intents.json")
CANNED_RESPONSES = load_json("canned_responses.json")
# Load cyberpunk-themed intents
CYBERPUNK_INTENTS = load_json("cyberpunk_intents.json")
# Load response variations by mood/weather/personality/time/location
RESPONSE_VARIATIONS = load_json("response_variations.json")


def get_npc_context(npc: dict) -> dict:
    """
    Extract NPC's current context from their state.
    
    NPC state should include:
    - current_location: where they are
    - current_activity: what they're doing
    - next_destination: where they're going next
    - schedule: their daily schedule
    - needs: hunger, energy, etc.
    """
    return {
        "location": npc.get("current_location", "unknown"),
        "location_type": npc.get("location_type", "street"),
        "activity": npc.get("current_activity", "idle"),
        "next_destination": npc.get("next_destination"),
        "is_busy": npc.get("is_busy", False),
        "needs": npc.get("needs", {}),
        "mood": calculate_mood_from_needs(npc.get("needs", {}))
    }


def calculate_mood_from_needs(needs: dict) -> str:
    """Calculate NPC mood from their needs state."""
    hunger = needs.get("hunger", 0.5)
    energy = needs.get("energy", 0.5)
    social = needs.get("social", 0.5)
    
    # Low needs = bad mood
    if hunger > 0.7 or energy < 0.3:
        return "bad"
    elif hunger < 0.3 and energy > 0.6 and social > 0.5:
        return "good"
    else:
        return "neutral"


def select_response_with_context(
    intent_match: "IntentMatch",
    world_state: dict,
    npc: dict,
    npc_context: dict,
    tick: int
) -> str:
    """
    Select response based on intent, world state, AND NPC's current context.
    
    Priority:
    1. Activity-specific responses (if asking about what they're doing)
    2. Location-specific responses
    3. World state (weather, time)
    4. Default personality-based
    """
    intent = intent_match.intent
    
    # Check if this is a context-aware intent
    context_intent_data = CONTEXT_INTENTS.get("activity_intents", {}).get(intent, {})
    
    # Try activity-specific responses first
    if "responses_by_activity" in context_intent_data:
        activity = npc_context.get("activity", "idle")
        responses = context_intent_data["responses_by_activity"].get(
            activity,
            context_intent_data["responses_by_activity"].get("default", [])
        )
        if responses:
            return deterministic_pick(responses, npc, intent, tick)
    
    # Try location-type responses
    if "responses_by_location_type" in context_intent_data:
        loc_type = npc_context.get("location_type", "default")
        responses = context_intent_data["responses_by_location_type"].get(
            loc_type,
            context_intent_data["responses_by_location_type"].get("default", [])
        )
        if responses:
            return deterministic_pick(responses, npc, intent, tick)
    
    # Try busy-level responses
    if "responses_by_busy_level" in context_intent_data:
        if npc_context.get("is_busy"):
            busy_level = "very_busy"
        elif npc_context.get("activity") in ["working", "patrolling", "trading"]:
            busy_level = "somewhat_busy"
        else:
            busy_level = "not_busy"
        responses = context_intent_data["responses_by_busy_level"].get(busy_level, [])
        if responses:
            return deterministic_pick(responses, npc, intent, tick)
    
    # Fall back to regular response selection
    return select_response(intent_match, world_state, npc, tick)


def add_activity_modifier(response: str, npc_context: dict, tick: int) -> str:
    """Add activity-based prefix/suffix to response."""
    activity = npc_context.get("activity", "idle")
    modifiers = CONTEXT_INTENTS.get("activity_modifiers", {}).get(activity, {})
    
    # Add prefix 30% of the time
    prefixes = modifiers.get("prefix", [])
    if prefixes and (tick % 10) < 3:
        prefix = prefixes[tick % len(prefixes)]
        response = f"{prefix} {response}"
    
    return response


def deterministic_pick(items: list, npc: dict, intent: str, tick: int) -> str:
    """Deterministically pick from list based on NPC and context."""
    if not items:
        return "..."
    npc_id = npc.get("id", "unknown")
    seed = f"{npc_id}_{intent}_{tick}"
    idx = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16) % len(items)
    return items[idx]


# =============================================================================
# MAIN NLU FUNCTION
# =============================================================================

def process_input(
    user_input: str,
    npc: dict,
    world_state: dict,
    tick: int = 0
) -> Dict[str, Any]:
    """
    Full NLU pipeline: classify intent and select response.
    
    NPC dict should include runtime state:
    - id, name, personality (static)
    - current_location, current_activity, next_destination (runtime)
    - needs, is_busy, schedule (runtime)
    
    Returns:
        {
            "user_input": str,
            "intent": str,
            "confidence": float,
            "entities": dict,
            "response": str,
            "npc_context": dict,
            "nlu_source": "embedded"
        }
    """
    # Get NPC's current context
    npc_context = get_npc_context(npc)
    
    # Classify intent - try context intents first, then general
    all_intents = {
        **SMALL_TALK.get("intents", {}),
        **CONTEXT_INTENTS.get("activity_intents", {})
    }
    intent_match = classify_intent(user_input, all_intents)
    
    # Select response with full context awareness
    response = select_response_with_context(
        intent_match, world_state, npc, npc_context, tick
    )
    
    # Add activity modifier
    response = add_activity_modifier(response, npc_context, tick)
    
    return {
        "user_input": user_input,
        "intent": intent_match.intent,
        "confidence": intent_match.confidence,
        "matched_keywords": intent_match.matched_keywords,
        "matched_patterns": intent_match.matched_patterns,
        "entities": intent_match.entities,
        "response": response,
        "npc_context": {
            "location": npc_context["location"],
            "activity": npc_context["activity"],
            "next_destination": npc_context["next_destination"],
            "mood": npc_context["mood"]
        },
        "nlu_source": "embedded"
    }


# =============================================================================
# STEMMING LOOKUP (No ML needed)
# =============================================================================

STEM_MAP = {
    # Weather
    "raining": "rain", "rained": "rain", "rains": "rain", "rainy": "rain",
    "storming": "storm", "stormed": "storm", "storms": "storm", "stormy": "storm",
    "snowing": "snow", "snowed": "snow", "snows": "snow", "snowy": "snow",
    "cloudy": "cloud", "clouds": "cloud", "clouded": "cloud",
    "sunny": "sun", "sunshine": "sun",
    "foggy": "fog", "fogged": "fog",
    "hotter": "hot", "hottest": "hot", "heated": "hot",
    "colder": "cold", "coldest": "cold", "freezing": "cold",
    
    # Actions
    "eating": "eat", "ate": "eat", "eats": "eat", "eaten": "eat",
    "drinking": "drink", "drank": "drink", "drinks": "drink", "drunk": "drink",
    "sleeping": "sleep", "slept": "sleep", "sleeps": "sleep",
    "working": "work", "worked": "work", "works": "work",
    "going": "go", "went": "go", "goes": "go", "gone": "go",
    "buying": "buy", "bought": "buy", "buys": "buy",
    "selling": "sell", "sold": "sell", "sells": "sell",
    
    # States
    "hungry": "hunger", "hungriest": "hunger",
    "thirsty": "thirst", "thirstiest": "thirst",
    "tired": "tire", "tiring": "tire", "tiredness": "tire",
    "scared": "scare", "scary": "scare", "scaring": "scare",
    "dangerous": "danger", "dangers": "danger",
    "safely": "safe", "safer": "safe", "safest": "safe", "safety": "safe",
    
    # Questions
    "where's": "where", "wheres": "where",
    "what's": "what", "whats": "what",
    "who's": "who", "whos": "who",
    "how's": "how", "hows": "how",
    "why's": "why", "whys": "why",
    "when's": "when", "whens": "when",
    
    # Misc
    "looking": "look", "looked": "look", "looks": "look",
    "needing": "need", "needed": "need", "needs": "need",
    "wanting": "want", "wanted": "want", "wants": "want",
    "happening": "happen", "happened": "happen", "happens": "happen",
    "talking": "talk", "talked": "talk", "talks": "talk",
    "telling": "tell", "told": "tell", "tells": "tell",
}


def stem_word(word: str) -> str:
    """Apply basic stemming via lookup."""
    word_lower = word.lower()
    return STEM_MAP.get(word_lower, word_lower)


def stem_text(text: str) -> str:
    """Stem all words in text."""
    words = re.findall(r'\w+', text.lower())
    return ' '.join(stem_word(w) for w in words)


# =============================================================================
# FUZZY MATCHING (Handle typos)
# =============================================================================

def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate edit distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def fuzzy_match(word: str, target: str, threshold: float = 0.7) -> bool:
    """Check if word matches target using similarity ratio."""
    word_l = word.lower()
    target_l = target.lower()
    
    # Exact match
    if word_l == target_l:
        return True
    
    # One is substring of other
    if word_l in target_l or target_l in word_l:
        return True
    
    # Short words need exact match
    if len(word_l) < 3 or len(target_l) < 3:
        return word_l == target_l
    
    # Calculate similarity ratio
    distance = levenshtein_distance(word_l, target_l)
    max_len = max(len(word_l), len(target_l))
    similarity = 1 - (distance / max_len)
    
    return similarity >= threshold


def fuzzy_find_keyword(text: str, keywords: List[str], threshold: float = 0.7) -> List[Tuple[str, str]]:
    """Find keywords in text with fuzzy matching. Returns (word, matched_keyword) pairs."""
    words = re.findall(r'\w+', text.lower())
    found = []
    
    for word in words:
        for keyword in keywords:
            if fuzzy_match(word, keyword, threshold):
                found.append((word, keyword))
                break
    
    return found


# =============================================================================
# N-GRAM MATCHING
# =============================================================================

def get_ngrams(text: str, n: int = 2) -> List[str]:
    """Extract n-grams from text."""
    words = text.lower().split()
    if len(words) < n:
        return [' '.join(words)]
    return [' '.join(words[i:i+n]) for i in range(len(words) - n + 1)]


def phrase_match_score(text: str, patterns: List[str]) -> float:
    """Score how well text matches phrase patterns."""
    text_lower = text.lower()
    score = 0.0
    
    for pattern in patterns:
        if pattern in text_lower:
            # Exact phrase match - high score
            score += len(pattern.split()) * 5
        else:
            # Check for partial matches
            pattern_words = pattern.split()
            matches = sum(1 for w in pattern_words if w in text_lower)
            score += matches * 2
    
    return score


# =============================================================================
# INTENT CLASSIFICATION
# =============================================================================

@dataclass
class IntentMatch:
    """Result of intent classification."""
    intent: str
    confidence: float
    matched_keywords: List[str]
    matched_patterns: List[str]
    entities: Dict[str, str]


def classify_intent(
    user_input: str,
    intent_data: dict = None,
    min_confidence: float = 0.3
) -> IntentMatch:
    """
    Classify user input into intent with confidence score.
    
    Uses multiple strategies:
    1. Exact keyword matching (high weight)
    2. Fuzzy keyword matching (medium weight)
    3. Regex pattern matching (high weight)
    4. N-gram phrase matching (medium weight)
    5. Stemmed matching (low weight)
    """
    intent_data = intent_data or SMALL_TALK.get("intents", {})
    
    input_lower = user_input.lower().strip()
    input_stemmed = stem_text(user_input)
    input_words = set(re.findall(r'\w+', input_lower))
    
    best_intent = "unknown"
    best_score = 0.0
    best_keywords = []
    best_patterns = []
    
    for intent_name, intent_info in intent_data.items():
        score = 0.0
        matched_keywords = []
        matched_patterns = []
        
        # 1. Exact keyword matching (weight: 10 per match)
        keywords = intent_info.get("patterns", [])
        for kw in keywords:
            if kw in input_lower:
                score += 10
                matched_keywords.append(kw)
        
        # 2. Fuzzy keyword matching (weight: 7 per match)
        fuzzy_matches = fuzzy_find_keyword(input_lower, keywords, threshold=0.6)
        for (word, matched_kw) in fuzzy_matches:
            if matched_kw not in matched_keywords:
                score += 7
                matched_keywords.append(f"~{word}→{matched_kw}")
        
        # 3. Regex pattern matching (weight: 15 per match)
        regexes = intent_info.get("regex", [])
        for pattern in regexes:
            try:
                if re.search(pattern, input_lower):
                    score += 15
                    matched_patterns.append(pattern)
            except re.error:
                pass
        
        # 4. User variation matching (weight: 20 for close match)
        variations = intent_info.get("user_variations", [])
        for var in variations:
            var_lower = var.lower()
            # Exact match
            if var_lower == input_lower or var_lower.rstrip('?!.') == input_lower.rstrip('?!.'):
                score += 30
                matched_patterns.append(f"exact:{var}")
            # High overlap
            elif len(input_words & set(re.findall(r'\w+', var_lower))) >= 2:
                score += 10
        
        # 5. Stemmed matching (weight: 3 per match)
        for kw in keywords:
            stemmed_kw = stem_word(kw)
            if stemmed_kw in input_stemmed:
                score += 3
        
        # Normalize score - simpler calculation
        # Any 2+ keyword matches or 1 regex match = good confidence
        if score >= 10:
            normalized_score = min(1.0, score / 30)
        else:
            normalized_score = score / 50
        
        if score > best_score:
            best_score = score
            best_intent = intent_name
            best_keywords = matched_keywords
            best_patterns = matched_patterns
    
    # Calculate confidence - lower threshold
    confidence = min(1.0, best_score / 20)  # 20 points = full confidence
    
    if confidence < min_confidence:
        best_intent = "unknown"
    
    # Extract entities
    entities = extract_entities(user_input)
    
    return IntentMatch(
        intent=best_intent,
        confidence=confidence,
        matched_keywords=best_keywords,
        matched_patterns=best_patterns,
        entities=entities
    )


def extract_entities(text: str) -> Dict[str, str]:
    """Extract entities from text using patterns."""
    entities = {}
    text_lower = text.lower()
    
    # Location entities
    locations = ["undercity", "market", "temple", "docks", "spire", "old quarter", "neon alley"]
    for loc in locations:
        if loc in text_lower:
            entities["location"] = loc
            break
    
    # Weather entities
    weather_types = ["rain", "storm", "smog", "fog", "sun", "clear", "acid rain", "hot", "cold"]
    for w in weather_types:
        if w in text_lower:
            entities["weather"] = w
            break
    
    # Time entities
    times = ["morning", "afternoon", "evening", "night", "midnight", "dawn", "dusk"]
    for t in times:
        if t in text_lower:
            entities["time"] = t
            break
    
    # Faction entities
    factions = ["resistance", "temple", "corporate", "gang", "criminal"]
    for f in factions:
        if f in text_lower:
            entities["faction"] = f
            break
    
    # Number extraction
    numbers = re.findall(r'\b(\d+)\b', text)
    if numbers:
        entities["number"] = numbers[0]
    
    return entities


# =============================================================================
# WORLD-STATE-AWARE RESPONSE SELECTION
# =============================================================================

def select_response(
    intent_match: IntentMatch,
    world_state: dict,
    npc: dict,
    tick: int
) -> str:
    """
    Select response based on intent and current world state.
    
    World state includes weather, time, location, etc.
    NPC includes personality for response flavor.
    """
    intent_data = SMALL_TALK.get("intents", {}).get(intent_match.intent, {})
    
    # Get NPC personality category
    personality = npc.get("personality", {})
    mood = "neutral"
    if personality.get("sociability", 0.5) > 0.7:
        mood = "good"
    elif personality.get("aggression", 0.5) > 0.7:
        mood = "suspicious"
    elif personality.get("sociability", 0.5) < 0.3:
        mood = "bad"
    
    # Try state-specific responses first
    responses = []
    
    # Weather-specific
    if "responses_by_weather" in intent_data:
        current_weather = world_state.get("weather", "default")
        responses = intent_data["responses_by_weather"].get(
            current_weather, 
            intent_data["responses_by_weather"].get("default", [])
        )
    
    # Mood-specific
    elif "responses_by_mood" in intent_data:
        responses = intent_data["responses_by_mood"].get(
            mood,
            intent_data["responses_by_mood"].get("neutral", [])
        )
    
    # Time-specific
    elif "responses_by_time" in intent_data:
        current_time = world_state.get("time_of_day", "default")
        if world_state.get("hour", 12) < 6 or world_state.get("hour", 12) >= 22:
            current_time = "night"
        elif world_state.get("hour", 12) < 12:
            current_time = "morning"
        elif world_state.get("hour", 12) < 18:
            current_time = "afternoon"
        else:
            current_time = "evening"
        responses = intent_data["responses_by_time"].get(current_time, [])
    
    # Location-specific
    elif "responses_by_location" in intent_data:
        current_loc = world_state.get("location", "default")
        responses = intent_data["responses_by_location"].get(
            current_loc,
            intent_data["responses_by_location"].get("default", [])
        )
    
    # Generic responses
    else:
        responses = intent_data.get("responses", [])
    
    if not responses:
        responses = ["Hmm.", "I see.", "Interesting.", "..."]
    
    # Deterministic selection
    npc_id = npc.get("id", "unknown")
    seed = f"{npc_id}_{intent_match.intent}_{tick}"
    idx = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16) % len(responses)
    
    return responses[idx]


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Embedded NLU Engine")
    parser.add_argument("--input", type=str, default="How's the weather?")
    parser.add_argument("--weather", type=str, default="rain")
    parser.add_argument("--location", type=str, default="market")
    args = parser.parse_args()
    
    # Test NPC
    test_npc = {
        "id": "felix",
        "name": "Felix",
        "personality": {"sociability": 0.7, "aggression": 0.3}
    }
    
    # World state
    world = {
        "weather": args.weather,
        "location": args.location,
        "hour": 14,
        "time_of_day": "afternoon"
    }
    
    print("=" * 60)
    print("  EMBEDDED NLU ENGINE DEMO")
    print("=" * 60)
    print(f"\n🌧️ Weather: {args.weather}")
    print(f"📍 Location: {args.location}")
    print(f"\n📝 User: \"{args.input}\"")
    
    result = process_input(args.input, test_npc, world, tick=100)
    
    print(f"\n🧠 Intent: {result['intent']} (confidence: {result['confidence']:.2f})")
    print(f"   Keywords: {result['matched_keywords']}")
    print(f"   Entities: {result['entities']}")
    print(f"\n🗣️ NPC: \"{result['response']}\"")
    
    # Test with typos
    print("\n" + "-" * 60)
    print("  Testing typo handling...")
    print("-" * 60)
    
    typo_tests = [
        "Hows the weathr?",
        "Whats goign on?",
        "Any nmews?",
        "Im hungrey",
        "Is it saef here?"
    ]
    
    for test in typo_tests:
        result = process_input(test, test_npc, world, tick=100)
        print(f"\n📝 \"{test}\"")
        print(f"   → Intent: {result['intent']} ({result['confidence']:.2f})")

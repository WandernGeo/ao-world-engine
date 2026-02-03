#!/usr/bin/env python3
"""
NEWS GENERATOR & DYNAMIC INTENT API
====================================

Generates news headlines based on world events.
Allows runtime addition of intents and responses.

Features:
- Generate headlines from event data
- Add new intents/responses via API
- Retroactively create events from headlines
- NPC news reactions based on current events

Usage:
    python news_generator.py --generate-headlines
    python news_generator.py --add-intent "new_topic" '{"patterns": ["keyword1"]}'
    python news_generator.py --trigger-event "robbery" --location "market"
"""

import json
import hashlib
import random
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import argparse
import re

# =============================================================================
# DATA PATHS
# =============================================================================

DATA_DIR = Path(__file__).parent.parent / "data"
NEWS_FILE = DATA_DIR / "news_events.json"
CYBERPUNK_INTENTS = DATA_DIR / "cyberpunk_intents.json"
SMALL_TALK_INTENTS = DATA_DIR / "small_talk_intents.json"
CONTEXT_INTENTS = DATA_DIR / "context_intents.json"
RESPONSE_VARIATIONS = DATA_DIR / "response_variations.json"

# Current cycle's active news
ACTIVE_NEWS_FILE = DATA_DIR / "active_news.json"


# =============================================================================
# DATA LOADING
# =============================================================================

def load_json(path: Path) -> dict:
    """Load JSON file."""
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    return {}


def save_json(path: Path, data: dict) -> None:
    """Save JSON file."""
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"✅ Saved: {path}")


# =============================================================================
# NEWS GENERATION
# =============================================================================

@dataclass
class NewsEvent:
    """A news event that occurred in the world."""
    event_id: str
    category: str
    event_type: str
    headline: str
    source: str
    tick: int
    location: str
    details: Dict[str, Any]
    npc_reactions: List[str]


def generate_event_id(category: str, event_type: str, tick: int) -> str:
    """Generate unique event ID."""
    seed = f"{category}_{event_type}_{tick}"
    return hashlib.md5(seed.encode()).hexdigest()[:12]


def fill_headline_template(template: str, context: Dict[str, str]) -> str:
    """Fill in headline template placeholders."""
    result = template
    for key, value in context.items():
        result = result.replace(f"{{{key}}}", str(value))
    
    # Fill any remaining placeholders with defaults
    defaults = {
        "{location}": "the city",
        "{district}": "the district",
        "{neighborhood}": "the area",
        "{business}": "a local business",
        "{corporation}": "a corporation",
        "{count}": str(random.randint(2, 15)),
        "{credits}": str(random.randint(1000, 50000)),
        "{percent}": str(random.randint(5, 30)),
        "{duration}": f"{random.randint(1, 12)} hours",
        "{time}": f"{random.randint(18, 22)}:00",
        "{name}": "an individual",
        "{profession}": "a worker",
        "{faction}": "unknown faction",
        "{gang_name}": "a gang",
        "{resource}": "supplies",
        "{topic}": "city matters",
        "{issue}": "current events",
        "{model}": "Model X",
        "{brand}": "a manufacturer",
        "{disease}": "an illness",
        "{demand}": "change",
        "{trigger}": "tensions",
        "{revelation}": "corruption"
    }
    
    for placeholder, default in defaults.items():
        result = result.replace(placeholder, default)
    
    return result


def generate_headlines(
    tick: int,
    world_state: dict,
    num_headlines: int = 5
) -> List[NewsEvent]:
    """
    Generate news headlines based on world state.
    
    Uses weighted random selection of event categories,
    then picks event types and fills headline templates.
    """
    news_data = load_json(NEWS_FILE)
    categories = news_data.get("event_categories", {})
    templates = news_data.get("headline_templates", {})
    sources = news_data.get("news_sources", {})
    reactions = news_data.get("npc_news_reactions", {})
    
    events = []
    
    for _ in range(num_headlines):
        # Weight-based category selection
        cat_weights = [(cat, info.get("weight", 0.1)) 
                       for cat, info in categories.items()]
        total_weight = sum(w for _, w in cat_weights)
        
        # Deterministic but varied selection
        seed = f"{tick}_{len(events)}"
        rand_val = (int(hashlib.md5(seed.encode()).hexdigest()[:8], 16) % 1000) / 1000
        
        cumulative = 0
        selected_category = "crime"
        for cat, weight in cat_weights:
            cumulative += weight / total_weight
            if rand_val <= cumulative:
                selected_category = cat
                break
        
        # Get event types for this category
        event_types = categories.get(selected_category, {}).get("events", [])
        if not event_types:
            continue
        
        event_idx = (int(hashlib.md5(f"{seed}_type".encode()).hexdigest()[:4], 16) 
                     % len(event_types))
        event_type = event_types[event_idx]
        
        # Get headline templates
        cat_templates = templates.get(selected_category, {})
        type_templates = cat_templates.get(event_type, [])
        
        if not type_templates:
            # Fallback to generic
            headline = f"Breaking: {event_type.replace('_', ' ').title()} Reported"
        else:
            template_idx = (int(hashlib.md5(f"{seed}_template".encode()).hexdigest()[:4], 16)
                           % len(type_templates))
            template = type_templates[template_idx]
            
            # Context from world state
            context = {
                "location": world_state.get("location", "the city"),
                "district": world_state.get("district", "downtown"),
                "weather": world_state.get("weather", "clear")
            }
            headline = fill_headline_template(template, context)
        
        # Select source based on bias/category
        source_list = list(sources.keys())
        source_idx = (int(hashlib.md5(f"{seed}_source".encode()).hexdigest()[:4], 16)
                     % len(source_list))
        source = source_list[source_idx]
        
        # Get NPC reactions
        cat_reactions = reactions.get(selected_category, [])
        
        event = NewsEvent(
            event_id=generate_event_id(selected_category, event_type, tick),
            category=selected_category,
            event_type=event_type,
            headline=headline,
            source=source,
            tick=tick,
            location=world_state.get("location", "unknown"),
            details={
                "weather": world_state.get("weather"),
                "time_of_day": world_state.get("time_of_day")
            },
            npc_reactions=cat_reactions[:3]  # Top 3 reactions
        )
        events.append(event)
    
    return events


# =============================================================================
# DYNAMIC INTENT API
# =============================================================================

def add_intent(
    intent_name: str,
    intent_data: dict,
    target_file: str = "cyberpunk_intents.json"
) -> bool:
    """
    Add a new intent to the dialogue system at runtime.
    
    Args:
        intent_name: Name of the intent (e.g., "new_topic")
        intent_data: Dict with patterns, user_variations, responses
        target_file: Which file to add to
    
    Returns:
        Success boolean
    """
    file_path = DATA_DIR / target_file
    data = load_json(file_path)
    
    # Ensure structure exists
    if "intents" not in data:
        data["intents"] = {}
    
    # Validate intent_data structure
    required_keys = ["patterns"]
    for key in required_keys:
        if key not in intent_data:
            print(f"❌ Missing required key: {key}")
            return False
    
    # Add defaults
    if "user_variations" not in intent_data:
        intent_data["user_variations"] = []
    if "responses" not in intent_data:
        intent_data["responses"] = {"default": ["..."]}
    
    # Add or update intent
    data["intents"][intent_name] = intent_data
    
    save_json(file_path, data)
    print(f"✅ Added intent '{intent_name}' to {target_file}")
    return True


def add_responses(
    category: str,
    context_type: str,
    context_value: str,
    responses: List[str],
    target_file: str = "response_variations.json"
) -> bool:
    """
    Add response variations at runtime.
    
    Args:
        category: e.g., "cyberware_responses"
        context_type: e.g., "by_weather"
        context_value: e.g., "storm"
        responses: List of response strings
        target_file: Target file
    
    Returns:
        Success boolean
    """
    file_path = DATA_DIR / target_file
    data = load_json(file_path)
    
    # Ensure structure exists
    if category not in data:
        data[category] = {}
    if context_type not in data[category]:
        data[category][context_type] = {}
    
    # Merge responses
    existing = data[category][context_type].get(context_value, [])
    data[category][context_type][context_value] = existing + responses
    
    save_json(file_path, data)
    print(f"✅ Added {len(responses)} responses to {category}.{context_type}.{context_value}")
    return True


def add_news_event(
    category: str,
    event_type: str,
    headlines: List[str],
    npc_reactions: List[str] = None
) -> bool:
    """
    Add a new event type with headlines to the news system.
    
    Args:
        category: Event category (crime, political, etc.)
        event_type: New event type name
        headlines: List of headline templates
        npc_reactions: Optional NPC reaction templates
    """
    data = load_json(NEWS_FILE)
    
    # Add to event categories
    if category in data.get("event_categories", {}):
        events = data["event_categories"][category].get("events", [])
        if event_type not in events:
            events.append(event_type)
            data["event_categories"][category]["events"] = events
    
    # Add headline templates
    if "headline_templates" not in data:
        data["headline_templates"] = {}
    if category not in data["headline_templates"]:
        data["headline_templates"][category] = {}
    
    data["headline_templates"][category][event_type] = headlines
    
    # Add NPC reactions
    if npc_reactions:
        if "npc_news_reactions" not in data:
            data["npc_news_reactions"] = {}
        existing = data["npc_news_reactions"].get(category, [])
        data["npc_news_reactions"][category] = existing + npc_reactions
    
    save_json(NEWS_FILE, data)
    print(f"✅ Added event type '{event_type}' to category '{category}'")
    return True


# =============================================================================
# EVENT RETROACTION
# =============================================================================

def retroact_event_from_headline(headline: str, tick: int) -> Dict[str, Any]:
    """
    Given a news headline, generate the events/actions that would have caused it.
    
    This enables bidirectional causality:
    - Events -> Headlines (normal)
    - Headlines -> Events (retroaction)
    """
    news_data = load_json(NEWS_FILE)
    triggers = news_data.get("event_triggers", {})
    
    # Extract event type from headline (simple keyword matching)
    headline_lower = headline.lower()
    
    detected_events = []
    
    # Check for event keywords
    event_keywords = {
        "robbery": ["robbery", "stolen", "heist", "thieves"],
        "murder": ["body found", "killed", "murder", "dead"],
        "gang_violence": ["gang war", "gang", "territorial", "clash"],
        "power_outage": ["blackout", "power", "outage", "grid failure"],
        "protest": ["protest", "demonstrators", "gathering", "strike"],
        "riot": ["riot", "violence", "unrest", "clash"]
    }
    
    for event_type, keywords in event_keywords.items():
        if any(kw in headline_lower for kw in keywords):
            detected_events.append(event_type)
    
    # Generate retroactive event chain
    event_chain = []
    for event_type in detected_events:
        trigger_info = triggers.get(event_type, {})
        
        event_chain.append({
            "event_type": event_type,
            "tick": tick,
            "preconditions_assumed": trigger_info.get("preconditions", []),
            "effects_to_apply": trigger_info.get("effects", []),
            "source_headline": headline
        })
    
    return {
        "headline": headline,
        "tick": tick,
        "detected_events": detected_events,
        "event_chain": event_chain
    }


# =============================================================================
# ACTIVE NEWS MANAGEMENT
# =============================================================================

def get_current_news(tick: int) -> List[Dict]:
    """Get active news for the current cycle."""
    data = load_json(ACTIVE_NEWS_FILE)
    return data.get("events", [])


def set_current_news(events: List[NewsEvent], tick: int) -> None:
    """Save news events for the current cycle."""
    data = {
        "cycle_tick": tick,
        "generated_at": datetime.now().isoformat(),
        "events": [asdict(e) for e in events]
    }
    save_json(ACTIVE_NEWS_FILE, data)


def get_news_for_npc(npc: dict, tick: int) -> Dict[str, Any]:
    """
    Get news that an NPC would know about based on their location/faction.
    
    Returns relevant headlines and NPC's reaction options.
    """
    current_news = get_current_news(tick)
    npc_location = npc.get("current_location", "")
    npc_faction = npc.get("faction", "civilian")
    
    relevant_news = []
    for event in current_news:
        # All news is potentially relevant
        relevant_news.append({
            "headline": event.get("headline"),
            "category": event.get("category"),
            "reactions": event.get("npc_reactions", [])
        })
    
    return {
        "npc_id": npc.get("id"),
        "news_count": len(relevant_news),
        "news": relevant_news[:3]  # Top 3
    }


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="News Generator & Intent API")
    
    parser.add_argument("--generate-headlines", action="store_true",
                       help="Generate news headlines for current cycle")
    parser.add_argument("--tick", type=int, default=100,
                       help="Current simulation tick")
    parser.add_argument("--count", type=int, default=5,
                       help="Number of headlines to generate")
    
    parser.add_argument("--add-intent", nargs=2, metavar=("NAME", "JSON"),
                       help="Add a new intent: --add-intent name '{...}'")
    parser.add_argument("--target-file", type=str, default="cyberpunk_intents.json",
                       help="Target file for intent addition")
    
    parser.add_argument("--add-event", nargs=4, 
                       metavar=("CATEGORY", "TYPE", "HEADLINE", "REACTION"),
                       help="Add news event type")
    
    parser.add_argument("--retroact", type=str,
                       help="Retroact events from headline")
    
    args = parser.parse_args()
    
    if args.generate_headlines:
        world_state = {
            "location": "Market District",
            "district": "downtown",
            "weather": "smog",
            "time_of_day": "evening"
        }
        
        events = generate_headlines(args.tick, world_state, args.count)
        
        print("\n" + "=" * 60)
        print("  GENERATED NEWS HEADLINES")
        print("=" * 60)
        
        for event in events:
            print(f"\n📰 [{event.source.upper()}]")
            print(f"   {event.headline}")
            print(f"   Category: {event.category} | Type: {event.event_type}")
        
        # Save active news
        set_current_news(events, args.tick)
        print(f"\n✅ Saved {len(events)} headlines to active_news.json")
    
    elif args.add_intent:
        name, json_str = args.add_intent
        try:
            intent_data = json.loads(json_str)
            add_intent(name, intent_data, args.target_file)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")
    
    elif args.add_event:
        category, event_type, headline, reaction = args.add_event
        add_news_event(category, event_type, [headline], [reaction])
    
    elif args.retroact:
        result = retroact_event_from_headline(args.retroact, args.tick)
        print("\n" + "=" * 60)
        print("  RETROACTION ANALYSIS")
        print("=" * 60)
        print(f"\nHeadline: {result['headline']}")
        print(f"Detected events: {result['detected_events']}")
        for chain in result['event_chain']:
            print(f"\n  Event: {chain['event_type']}")
            print(f"  Preconditions assumed: {chain['preconditions_assumed']}")
            print(f"  Effects to apply: {chain['effects_to_apply']}")


if __name__ == "__main__":
    main()

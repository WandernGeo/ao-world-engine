"""
NLU Story Engine — Pure pattern-matching dialogue system.
No LLM, no ML models, no training data.

Architecture (Rasa-inspired):
1. Intent Resolution: keyword + regex matching → hierarchical intent ID
2. Entity Extraction: NPC names, districts, buildings from codec data
3. Context Routing: trust level × weather × user memory → story subkey
4. Story Lookup: intent + archetype → response pool → random choice
5. Template Filling: {npc_name}, {location}, {weather} → final response
6. Accent Transform: archetype-specific speech patterns applied last

All data loaded from JSON at startup. Zero network calls.
"""

import json
import os
import re
import random
from typing import Optional, Tuple

# ============================================================
# LOAD DATA FILES
# ============================================================

_NLU_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'nlu')

def _load_json(filename: str) -> dict:
    path = os.path.join(_NLU_DIR, filename)
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}

# Load at import time — these are static, read-only
STORIES = _load_json('npc_stories.json').get('stories', {})
INTENTS_DATA = _load_json('npc_intents.json')
INTENT_DEFS = INTENTS_DATA.get('intents', [])
CONTEXT_EXTRACTORS = INTENTS_DATA.get('context_extractors', {})
TEMPLATE_VARS = INTENTS_DATA.get('template_vars', {})

# Pre-compile regex patterns for performance
_COMPILED_PATTERNS = {}
for intent_def in INTENT_DEFS:
    intent_id = intent_def['id']
    patterns = intent_def.get('patterns', [])
    _COMPILED_PATTERNS[intent_id] = [re.compile(p, re.IGNORECASE) for p in patterns]

# Sort intents by priority (lower = higher priority = matched first)
INTENT_DEFS_SORTED = sorted(INTENT_DEFS, key=lambda x: x.get('priority', 999))


# ============================================================
# CONTEXT SLOT TRACKER
# ============================================================

class ConversationContext:
    """Tracks context slots across a conversation with an NPC."""
    
    def __init__(self, user_id: str, npc_id: str):
        self.user_id = user_id
        self.npc_id = npc_id
        self.slots = {
            'trust_level': 50,       # 0-100, starts neutral
            'visit_count': 0,        # How many times talked to this NPC
            'mood_shift': 0,         # -10 to +10 from conversation
            'topics_discussed': [],  # Track what's been discussed
            'last_intent': None,     # Last intent matched
            'relationship': 'stranger',  # stranger → acquaintance → friend → ally
            'user_name': None,       # Remembered user name
        }
    
    def update_trust(self, delta: int):
        self.slots['trust_level'] = max(0, min(100, self.slots['trust_level'] + delta))
        # Update relationship tier
        trust = self.slots['trust_level']
        if trust >= 80:
            self.slots['relationship'] = 'ally'
        elif trust >= 60:
            self.slots['relationship'] = 'friend'
        elif trust >= 35:
            self.slots['relationship'] = 'acquaintance'
        else:
            self.slots['relationship'] = 'stranger'
    
    def record_visit(self):
        self.slots['visit_count'] += 1
        # Each visit slightly increases trust (familiarity)
        if self.slots['visit_count'] > 1:
            self.update_trust(2)
    
    def record_topic(self, intent_id: str):
        if intent_id not in self.slots['topics_discussed']:
            self.slots['topics_discussed'].append(intent_id)
        self.slots['last_intent'] = intent_id
    
    def get_trust_key(self) -> str:
        trust = self.slots['trust_level']
        if trust <= 30:
            return 'trust_low'
        elif trust >= 66:
            return 'trust_high'
        return 'default'
    
    def to_dict(self) -> dict:
        return self.slots.copy()


# Global context store (in-memory, keyed by user_id:npc_id)
_CONTEXT_STORE: dict[str, ConversationContext] = {}

def get_context(user_id: str, npc_id: str) -> ConversationContext:
    key = f"{user_id}:{npc_id}"
    if key not in _CONTEXT_STORE:
        _CONTEXT_STORE[key] = ConversationContext(user_id, npc_id)
    return _CONTEXT_STORE[key]


# ============================================================
# INTENT RESOLUTION
# ============================================================

def resolve_intent(message: str, npc_profile: dict = None, 
                   known_npcs: dict = None) -> Tuple[Optional[str], dict]:
    """
    Match a user message to a hierarchical intent ID.
    Returns (intent_id, extracted_entities).
    """
    msg_lower = message.lower().strip()
    entities = {}
    
    # Phase 1: Check for NPC name mentions (special case)
    if known_npcs:
        for name, info in known_npcs.items():
            if name.lower() in msg_lower:
                entities['entity_name'] = name
                entities['relationship_desc'] = info.get('relationship', 'someone I know')
                entities['opinion_desc'] = info.get('opinion', 'We have a history.')
                return 'people.npc.general', entities
    
    # Phase 2: Match against sorted intent definitions
    for intent_def in INTENT_DEFS_SORTED:
        intent_id = intent_def['id']
        
        # Skip dynamic intents (NPC names handled above)
        if intent_def.get('entity_type') == 'npc_name':
            continue
        
        # Check keywords first (fast path)
        keywords = intent_def.get('keywords', [])
        matched = False
        for kw in keywords:
            if len(kw) <= 3:
                # Short keywords need word boundary check to prevent 'hi' in 'this'
                if re.search(r'\b' + re.escape(kw) + r'\b', msg_lower):
                    matched = True
                    break
            else:
                if kw in msg_lower:
                    matched = True
                    break
        if matched:
            return intent_id, entities
        
        # Check regex patterns (slower but more precise)
        compiled = _COMPILED_PATTERNS.get(intent_id, [])
        for pattern in compiled:
            if pattern.search(msg_lower):
                return intent_id, entities
    
    # Phase 3: No match
    return 'meta.unknown', entities


# ============================================================
# STORY LOOKUP + CONTEXT ROUTING
# ============================================================

def lookup_story(intent_id: str, archetype: str, context_key: str = 'default',
                 weather: str = None, entities: dict = None) -> Optional[str]:
    """
    Look up a story response for a given intent + archetype + context.
    Falls through: archetype-specific → _all → None
    """
    story_pool = STORIES.get(intent_id, {})
    if not story_pool:
        # Fallback to meta.unknown
        story_pool = STORIES.get('meta.unknown', {})
    
    archetype_lower = archetype.lower().replace(' ', '_')
    
    # Try archetype-specific first
    responses = None
    if archetype_lower in story_pool:
        arch_pool = story_pool[archetype_lower]
        # Try context-specific subkey
        if context_key in arch_pool:
            responses = arch_pool[context_key]
        elif 'default' in arch_pool:
            responses = arch_pool['default']
    
    # Fall back to _all
    if not responses and '_all' in story_pool:
        all_pool = story_pool['_all']
        # Try weather-specific for weather intents
        if weather and weather in all_pool:
            responses = all_pool[weather]
        elif context_key in all_pool:
            responses = all_pool[context_key]
        elif 'default' in all_pool:
            responses = all_pool['default']
    
    if not responses:
        return None
    
    # Pick a random response
    response = random.choice(responses)
    return response


# ============================================================
# TEMPLATE FILLING
# ============================================================

def fill_template(response: str, npc_state: dict, tick_state: dict,
                  user_memory: dict = None, entities: dict = None) -> str:
    """Replace {placeholders} in response with actual values."""
    if '{' not in response:
        return response
    
    replacements = {
        'npc_name': npc_state.get('name', 'Unknown'),
        'archetype': npc_state.get('archetype', 'citizen'),
        'archetype_desc': npc_state.get('archetype', 'citizen').title() + ' of the city',
        'occupation_desc': f"I work as a {npc_state.get('archetype', 'citizen').lower()}",
        'location': npc_state.get('location_desc', 'the city'),
        'hour': str(tick_state.get('hour', 12)),
        'day_number': str(tick_state.get('day', 1)),
        'time_of_day': _get_time_of_day(tick_state.get('hour', 12)),
        'time_period_desc': tick_state.get('time_period', 'midday'),
        'time_of_day_comment': _get_time_comment(tick_state.get('hour', 12)),
    }
    
    # User memory
    if user_memory:
        replacements['user_name'] = user_memory.get('name', 'stranger')
    
    # Extracted entities
    if entities:
        replacements.update(entities)
    
    for key, value in replacements.items():
        response = response.replace(f'{{{key}}}', str(value))
    
    return response


def _get_time_of_day(hour: int) -> str:
    if hour < 6: return "deep night"
    if hour < 9: return "early morning"
    if hour < 12: return "morning"
    if hour < 14: return "midday"
    if hour < 17: return "afternoon"
    if hour < 20: return "evening"
    if hour < 23: return "night"
    return "late night"


def _get_time_comment(hour: int) -> str:
    if hour < 6: return "Not many people out at this hour."
    if hour < 9: return "City's just waking up."
    if hour < 12: return "Morning rush is in full swing."
    if hour < 14: return "Lunch hour. The streets are packed."
    if hour < 17: return "Afternoon shift. Things are winding down."
    if hour < 20: return "Evening's rolling in. The neon starts to glow."
    if hour < 23: return "Night shift. Different crowd comes out now."
    return "The city never truly sleeps."


# ============================================================
# TRUST MODIFIERS BY INTENT
# ============================================================

TRUST_MODIFIERS = {
    'social.greet': +3,
    'social.farewell': +1,
    'social.thank': +5,
    'social.insult': -10,
    'social.flirt': +2,
    'social.joke': +3,
    'quests.general': +2,
    'world.factions.resistance': -3,  # Risky topic
    'personal.family.general': +1,
}


# ============================================================
# MAIN NLU RESPONSE FUNCTION
# ============================================================

def generate_nlu_response(
    message: str,
    npc_id: str,
    npc_state: dict,
    tick_state: dict,
    npc_profile: dict = None,
    known_npcs: dict = None,
    user_id: str = 'anonymous',
    user_memory: dict = None,
) -> dict:
    """
    Generate a complete NLU response without any LLM.
    
    Returns:
        {
            'response': str,        # The NPC's response text
            'intent': str,          # Matched intent ID
            'confidence': float,    # Match confidence (1.0 for keyword, 0.5 for fallback)
            'context': dict,        # Current conversation context
            'entities': dict,       # Extracted entities
        }
    """
    # Get/update conversation context
    ctx = get_context(user_id, npc_id)
    ctx.record_visit()
    
    # Extract archetype
    archetype = npc_state.get('archetype', 'worker')
    weather = tick_state.get('weather', 'clear')
    
    # Step 1: Resolve intent
    intent_id, entities = resolve_intent(message, npc_profile, known_npcs)
    confidence = 1.0 if intent_id != 'meta.unknown' else 0.3
    
    # Step 2: Determine context key
    context_key = ctx.get_trust_key()
    
    # Special: user_name context for meta.identity.my_name
    if intent_id == 'meta.identity.my_name':
        if user_memory and user_memory.get('name'):
            context_key = 'knows_name'
        elif ctx.slots.get('user_name'):
            context_key = 'knows_name'
            if not user_memory:
                user_memory = {}
            user_memory['name'] = ctx.slots['user_name']
        else:
            context_key = 'doesnt_know'
    
    # Step 3: Look up story
    response = lookup_story(
        intent_id, archetype, context_key, 
        weather=weather, entities=entities
    )
    
    if not response:
        # Ultimate fallback
        response = "Hmm. *looks at you* Not sure what to say to that."
        confidence = 0.1
    
    # Step 4: Fill templates
    response = fill_template(response, npc_state, tick_state, user_memory, entities)
    
    # Step 5: Update context
    ctx.record_topic(intent_id)
    trust_mod = TRUST_MODIFIERS.get(intent_id, 0)
    if trust_mod:
        ctx.update_trust(trust_mod)
    
    return {
        'response': response,
        'intent': intent_id,
        'confidence': confidence,
        'context': ctx.to_dict(),
        'entities': entities,
    }

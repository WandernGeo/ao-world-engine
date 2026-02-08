# NPC Dialogue System — Rasa 1.0 Story-Based Architecture

> How 2,830 NPCs hold believable conversations without a single LLM call.

---

## Hybrid Architecture: Stories + Optional LLM

The system uses a **two-tier architecture** where the story-based NLU is the robust default, and LLM is an optional enhancement that can be toggled on or off.

### Tier 1: Story-Based NLU (Always Available)

| Strength | Detail |
|----------|--------|
| **Zero cost** | Stories are pre-authored data — no API calls |
| **Deterministic** | Same intent + context → same response, always |
| **On-Chain** | Story trees are pure JSON, run inside AO processes |
| **Instant** | Pattern match in <1ms |
| **Lore-safe** | Every response is hand-crafted canon |
| **Scalable** | Dictionary lookups for 2,830+ NPCs simultaneously |

### Tier 2: LLM Enhancement (Toggle On/Off)

When the LLM toggle is **ON** (via Vertex AI / Gemini):
- NLU stories still handle intent recognition and routing
- LLM generates **richer, more natural phrasing** of the story response
- LLM can **elaborate** on lore topics using codec context
- LLM fills gaps when no story matches (enhanced fallback)
- Per-NPC or per-conversation toggle

When the LLM toggle is **OFF**:
- Pure story-based responses (still robust and engaging)
- Zero API cost, zero latency
- Works on-chain in AO processes
- Ideal for background NPCs, bulk interactions, or cost-sensitive deployments

```python
# Toggle LLM per NPC or globally
NPC_CONFIG = {
    "llm_enabled": True,          # Global toggle
    "llm_per_npc": {
        "key_characters": True,    # Main cast gets LLM enhancement
        "background_npcs": False,  # Background NPCs use pure stories
    },
    "llm_fallback_only": False,   # Only use LLM when stories fail
}
```

## Why Rasa 1.0 Open Source?

[Rasa Open Source](https://github.com/RasaHQ/rasa) (v1.x, Apache 2.0 license) pioneered the **story-based dialogue model** — the idea that conversations can be represented as training examples of intent→action sequences, enabling pattern-matching dialogue that *feels* natural without any neural language model.

Key Rasa 1.0 concepts we adopt:

1. **Stories** — Example conversations as intent→action sequences
2. **Intents** — What the user means (not what they literally said)
3. **Actions** — What the NPC does in response
4. **Slots** — Context variables that persist across turns
5. **Checkpoints** — Reusable sub-conversations shared across stories
6. **Fallback** — Graceful degradation when intent is unclear

> **Credit:** This architecture is directly inspired by Rasa 1.0's open-source conversational AI framework. Rasa proved that story-based dialogue can produce natural-feeling conversations without LLMs at scale. We adapt their pattern for a game simulation context with 2,830+ NPCs.

## How It Works

### 1. Intent Recognition (No ML Required)

Instead of a trained NLU model, we use **keyword pattern matching** organized by intent:

```python
INTENT_PATTERNS = {
    "greet": ["hello", "hi", "hey", "greetings", "good morning", "good evening"],
    "ask_economy": ["taxes", "economy", "budget", "money", "income", "prices", "inflation"],
    "ask_weather": ["weather", "rain", "sun", "cold", "hot", "storm", "temperature"],
    "ask_crime": ["crime", "police", "theft", "robbery", "safe", "dangerous", "criminals"],
    "ask_job": ["work", "job", "employment", "hiring", "unemployed", "career"],
    "ask_district": ["district", "neighborhood", "area", "zone", "quarter"],
    "ask_housing": ["rent", "apartment", "housing", "home", "living", "landlord"],
    "ask_transport": ["bus", "subway", "metro", "transit", "commute", "train", "traffic"],
    "ask_health": ["health", "sick", "hospital", "clinic", "doctor", "medicine"],
    "ask_education": ["school", "university", "education", "learn", "study", "college"],
    "ask_about_self": ["who are you", "your name", "tell me about yourself", "what do you do"],
    "ask_opinion": ["think about", "opinion", "feel about", "believe"],
    "haggle": ["cheaper", "discount", "too expensive", "price", "deal", "bargain"],
    "buy": ["buy", "purchase", "want to get", "sell me", "how much for"],
    "gossip": ["heard", "rumor", "gossip", "secret", "between us", "did you know"],
    "farewell": ["bye", "goodbye", "see you", "later", "farewell", "take care"],
    "thank": ["thanks", "thank you", "appreciate", "grateful"],
    "insult": ["idiot", "stupid", "hate", "worst", "terrible", "useless"],
    "threaten": ["kill", "hurt", "fight", "attack", "weapon", "gun"],
    "flirt": ["beautiful", "handsome", "cute", "date", "love", "attractive"],
}
```

This gives us **20 base intents**. Each intent can trigger different actions depending on the NPC's archetype, mood, and context.

### 2. Stories (Conversation Flows)

A story is a sequence of turns that represents one complete conversation:

```yaml
# Story: Merchant greeting → haggling → sale
- story: merchant_successful_sale
  archetype: merchant
  steps:
    - intent: greet
    - action: utter_merchant_greeting
    - intent: ask_about_self
    - action: utter_merchant_introduction
    - intent: buy
    - action: utter_show_wares
    - intent: haggle
    - action: utter_counter_offer
    - intent: buy
    - action: utter_complete_sale
    - intent: farewell
    - action: utter_merchant_farewell
```

```yaml
# Story: Citizen complaining about economy
- story: citizen_economy_complaint
  archetype: working_class
  steps:
    - intent: greet
    - action: utter_tired_greeting
    - intent: ask_economy
    - action: utter_complain_taxes
    - slot_was_set:
      - mood: frustrated
    - intent: ask_opinion
    - action: utter_blame_temple
    - intent: farewell
    - action: utter_resigned_farewell
```

### 3. NPC Archetypes × Story Variations

Every NPC has an archetype that determines which story pool they draw from:

| Archetype | Story Count (Target) | Personality |
|-----------|---------------------|-------------|
| `merchant` | 200+ | Transactional, friendly, always selling |
| `guard` | 150+ | Authoritative, suspicious, duty-focused |
| `worker` | 200+ | Tired, practical, economy-focused |
| `scholar` | 150+ | Curious, verbose, knowledge-sharing |
| `street_kid` | 150+ | Slang, evasive, streetwise |
| `temple_priest` | 100+ | Pious, cryptic, tithe-collecting |
| `resistance_member` | 100+ | Paranoid, coded language, anti-Temple |
| `corporate` | 150+ | Professional, guarded, ECHO-loyal |
| `elder` | 100+ | Nostalgic, wise, story-telling |
| `entertainer` | 100+ | Dramatic, flirty, attention-seeking |
| `medic` | 100+ | Caring, stressed, health-focused |
| `hacker` | 100+ | Technical, suspicious, underground |
| **TOTAL** | **~1,600 base stories** | |

With **context variations** (weather, time of day, district, mood, recent events), each base story multiplies into 3-5 variants → **~5,000-8,000 effective conversation paths**.

### 4. Context Slots (Session State)

Slots track conversation state and modify responses:

```json
{
    "session_id": "abc123",
    "npc_id": "NPC_0042",
    "slots": {
        "topics_discussed": ["economy", "weather"],
        "mood": "neutral",
        "trust_level": 0.5,
        "times_visited": 3,
        "last_visit_tick": 14400,
        "player_reputation": "friendly",
        "items_purchased": [],
        "secrets_revealed": 0
    }
}
```

**Slot effects on responses:**
- `trust_level > 0.8` → NPC shares secrets, gossip, quest hints
- `trust_level < 0.2` → NPC is evasive, gives wrong directions
- `mood == "angry"` → Short responses, refuses to trade
- `times_visited > 5` → NPC remembers you, uses your name
- `topics_discussed` includes "resistance" → NPC becomes nervous (if Temple-loyal)

### 5. Checkpoints (Shared Sub-Dialogues)

Checkpoints let every NPC share common knowledge:

```yaml
# Checkpoint: Any NPC can answer about their district
- checkpoint: district_knowledge
  steps:
    - intent: ask_district
    - action: utter_district_description  # Pulled from codec_25 demographics
    - action: utter_district_opinion       # Varies by archetype + wealth

# Checkpoint: Weather small talk (universal)
- checkpoint: weather_talk
  steps:
    - intent: ask_weather
    - action: utter_current_weather        # Pulled from simulation tick
    - action: utter_weather_opinion        # Varies by archetype

# Checkpoint: Economy awareness (all adults)
- checkpoint: economy_awareness
  steps:
    - intent: ask_economy
    - action: utter_economy_status         # Pulled from city_economy.py
    - action: utter_economy_opinion        # Varies by wealth tier + archetype
```

### 6. Fallback Escalation

When intent matching fails:

```
Level 1: Try fuzzy intent match (Levenshtein distance)
Level 2: Try archetype-generic response ("Hmm, I'm not sure what you mean...")
Level 3: NPC personality fallback ("*shrugs and looks away*" / "*adjusts their goggles nervously*")
Level 4: Topic redirect ("Anyway, have you heard about [recent_event]?")
```

## Dynamic Response Templates

Responses aren't static strings — they're **templates** filled with live simulation data:

```python
TEMPLATES = {
    "utter_complain_taxes": [
        "Taxes just went up to {tax_rate}%. How am I supposed to feed my family on {wage} credits a month?",
        "The Temple takes {tax_rate}% off the top, then the landlord takes another {rent} for this dump.",
        "{tax_rate}% tax rate and they can't even keep the lights on in {district_name}. Pathetic.",
    ],
    "utter_economy_status": [
        "Unemployment is at {unemployment_rate}%. {economy_mood}",
        "The budget surplus is {surplus} credits this month. {economy_mood}",
    ],
    "utter_current_weather": [
        "It's {temperature}°C out there. {weather_comment}",
        "{weather_desc} today. {weather_opinion}",
    ],
}
```

Variables like `{tax_rate}`, `{wage}`, `{district_name}` are pulled live from `city_economy.py` and the simulation state at the current tick.

## Scaling to Thousands of Stories

### Story Generation Strategy

| Source | Stories | Method |
|--------|---------|--------|
| Hand-authored (core) | 500 | Written by developers for key interactions |
| Template expansion | 2,000 | Base stories × archetype × context variations |
| Lore-driven generation | 1,000 | Extract from codec backstories + world events |
| Community contributions | 500+ | Open-source story submissions |
| Procedural combinations | 2,000+ | Checkpoint chains assembled dynamically |
| **Total** | **~6,000+** | |

### Story Data Format (Codec-Compatible)

Stories are stored as JSON in the codec, making them loadable by any runtime (Python API, AO Lua process, etc.):

```json
{
    "_chunk": {
        "id": "chunk_34_npc_stories",
        "version": "1.0.0",
        "type": "world_codec_chunk",
        "category": "dialogue"
    },
    "stories": {
        "STORY_001": {
            "archetype": "merchant",
            "context": { "district": "any", "time": "day", "weather": "any" },
            "steps": [
                { "intent": "greet", "action": "utter_merchant_greeting" },
                { "intent": "buy", "action": "utter_show_wares" },
                { "intent": "haggle", "action": "utter_counter_offer" }
            ],
            "slots_required": { "trust_level": "> 0.3" },
            "tags": ["commerce", "friendly"]
        }
    },
    "templates": {
        "utter_merchant_greeting": {
            "responses": [
                "Welcome, welcome! Looking for something special today?",
                "Ah, a customer! Come, see what I have.",
                "You again! I saved something just for you."
            ],
            "conditions": {
                "times_visited > 2": ["You again! I saved something just for you."],
                "default": ["Welcome, welcome! Looking for something special today?"]
            }
        }
    }
}
```

## Why This Beats LLMs for NPCs

1. **Every response is canon** — no hallucinated lore, no broken world-building
2. **Deterministic on AO** — same inputs = same dialogue, verifiable on-chain
3. **Zero API costs** — runs on bare metal, edge, or blockchain
4. **Scales to millions** — a dictionary lookup is O(1), not O(tokens)
5. **Community-extensible** — anyone can submit new stories via PR
6. **Personality-consistent** — a grumpy guard stays grumpy, always
7. **Context-aware** — responses reflect live simulation state (economy, weather, events)
8. **Moddable** — swap story files to completely change NPC behavior

> **Attribution:** This dialogue architecture is built on patterns from [Rasa Open Source v1.0](https://github.com/RasaHQ/rasa) (Apache 2.0). Rasa pioneered the story-based approach to conversational AI, proving that structured dialogue training data produces natural-feeling conversations without large language models. We adapt and extend their open-source model for a persistent game world with thousands of autonomous NPCs.

# Hybrid Dialogue System

> LLM when available, canned responses when not (fully on Arweave, free for users)

---

## Core Architecture: Story + Intent Logs

### The Dual-Mode Approach

```
┌─────────────────────────────────────────────────────────────┐
│  SIMULATION (runs on AO, no LLM)                            │
│                                                               │
│  NPCs interact using INTENTS only:                          │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ {npc: "charlie", action: "greet", target: "felix"}  │    │
│  │ {npc: "felix", action: "respond", intent: "offer_drink"} │
│  │ {npc: "charlie", action: "accept"}                  │    │
│  │ {npc: "charlie", action: "gossip", topic: "temple"} │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  Stored: ~50 bytes per interaction (compact!)               │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  USER REVIEW (LLM translates intent logs → readable story) │
│                                                               │
│  Input: Intent log + NPC personalities + context            │
│  Output: Natural dialogue story                              │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Charlie walked into Felix's bar...                   │    │
│  │ "Hey Felix, got any of that synth-whiskey?"          │    │
│  │ Felix slid a glass across the counter. "For you,     │    │
│  │ first one's on the house."                           │    │
│  │ "Heard anything about Temple lately?"                │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Why This Works

| Mode | LLM Required | Cost | Storage |
|------|-------------|------|---------|
| Simulation | ❌ No | FREE | ~50 bytes/interaction |
| User Review | ✅ Yes | Per-read | LLM call |
| Fallback (no LLM) | ❌ No | FREE | Canned responses |

---

## Story Sequences (Rasa-style)

NPCs follow **story templates** - randomized sequences of actions:

```python
STORY_TEMPLATES = {
    "bar_visit": [
        {"action": "enter", "location": "bar"},
        {"action": "greet", "target": "@bartender"},
        {"action": "order", "item": "drink"},
        {"action": "small_talk", "topic": ["weather", "gossip", "work"]},
        {"action": "pay"},
        {"action": "farewell"},
        {"action": "leave"}
    ],
    "shopping": [
        {"action": "enter", "location": "market"},
        {"action": "browse"},
        {"action": "price_inquiry", "item": "@random_item"},
        {"action": "haggle", "probability": 0.4},
        {"action": "buy_or_leave"},
        {"action": "farewell"},
        {"action": "leave"}
    ],
    "work_day": [
        {"action": "travel", "to": "@workplace"},
        {"action": "greet", "target": "@coworkers"},
        {"action": "work", "duration": 8},
        {"action": "break", "activity": ["eat", "smoke", "chat"]},
        {"action": "work", "duration": 4},
        {"action": "farewell"},
        {"action": "travel", "to": "@home"}
    ]
}
```

### Randomness in Stories

Stories get **stitched together** with variation:

```python
def generate_story_sequence(npc, tick):
    # 1. Pick template based on NPC schedule
    template = pick_template_for_time(npc, tick)
    
    # 2. Instantiate with randomness
    story = []
    for step in template:
        action = step.copy()
        
        # Fill random choices deterministically
        if "@random" in str(action.get("item", "")):
            action["item"] = deterministic_choice(ITEMS, f"{npc['id']}_{tick}")
        if "@random" in str(action.get("topic", [])):
            action["topic"] = deterministic_choice(TOPICS, f"{npc['id']}_{tick}")
        
        # Probability-based skip
        if action.get("probability", 1.0) < 1.0:
            if not deterministic_chance(action["probability"], f"{npc['id']}_{tick}_{step}"):
                continue
        
        story.append(action)
    
    return story
```

---

## Intent Log Storage (Arweave)

Each NPC-NPC interaction stored as compact log:

```json
{
  "tick": 15420,
  "location": "L011",
  "participants": ["charlie", "felix"],
  "sequence": [
    {"a": "charlie", "i": "greet"},
    {"a": "felix", "i": "greet_back", "m": "friendly"},
    {"a": "charlie", "i": "order", "e": {"item": "drink"}},
    {"a": "felix", "i": "serve"},
    {"a": "charlie", "i": "gossip", "e": {"topic": "temple"}},
    {"a": "felix", "i": "respond_gossip", "e": {"info": "patrol_increase"}},
    {"a": "charlie", "i": "thanks"},
    {"a": "charlie", "i": "farewell"}
  ],
  "context": {"weather": "rain", "time": "evening"}
}
```

**Size:** ~200 bytes per conversation vs ~2KB for full dialogue text

---

## Conversation Storage & Learning

### 1. Store Every Conversation
```lua
-- AO Process: store_conversation
Handlers.add("StoreConversation",
  function(msg) return msg.Action == "StoreConversation" end,
  function(msg)
    local conv = {
      npc_id = msg.npc_id,
      user_input = msg.user_input,
      intent = msg.intent,
      response = msg.response,
      source = msg.source,  -- "llm" or "canned"
      rating = msg.rating,  -- User rating if any
      tick = msg.tick,
      personality = msg.npc_personality
    }
    -- Store to Arweave (pre-funded)
    ao.send({Target = ArweaveGateway, Action = "Store", Data = conv})
  end
)
```

### 2. Extract Good Responses → New Canned
```lua
-- Periodic job: curate good responses
Handlers.add("CurateResponses",
  function(msg) return msg.Action == "Cron" and msg.tick % 1000 == 0 end,
  function(msg)
    -- Find highly-rated LLM responses
    local good_responses = Query({
      source = "llm",
      rating = {gte = 4},
      used_count = {gte = 3}
    })
    
    -- Add to canned library
    for _, r in ipairs(good_responses) do
      AddToCannedLibrary(r.intent, r.response, r.personality)
    end
  end
)
```

### 3. Self-Improving Library
```
Week 1: 500 canned responses (base)
Week 2: 520 responses (20 from LLM convos)
Week 4: 580 responses (growing)
Month 3: 1000+ responses (rich library)
```

---

## Intent Detection (Deterministic)

Simple keyword + pattern matching (no ML needed):

```python
INTENT_PATTERNS = {
    "greeting": {
        "keywords": ["hi", "hello", "hey", "greetings", "wassup"],
        "patterns": [r"^(hi|hello|hey)\b"]
    },
    "ask_directions": {
        "keywords": ["where", "find", "location", "directions"],
        "patterns": [r"where.*(is|can i find)", r"how.*(get to|find)"]
    },
    "trade_request": {
        "keywords": ["buy", "sell", "trade", "price", "cost"],
        "patterns": [r"(i want|do you have|sell me)", r"how much"]
    },
    "quest_inquiry": {
        "keywords": ["quest", "job", "work", "mission", "help"],
        "patterns": [r"(got any|need any).*(work|jobs)", r"need.*help"]
    },
    "gossip": {
        "keywords": ["heard", "rumor", "news", "what's happening"],
        "patterns": [r"(what's|whats).*(going on|happening|news)"]
    },
    "faction_info": {
        "keywords": ["resistance", "temple", "faction"],
        "patterns": [r"(tell me|what).*(about|resistance|temple)"]
    }
}

def classify_intent(text: str) -> str:
    text_lower = text.lower()
    for intent, data in INTENT_PATTERNS.items():
        if any(kw in text_lower for kw in data["keywords"]):
            return intent
        if any(re.search(p, text_lower) for p in data["patterns"]):
            return intent
    return "unknown"
```

---

## Implementation Files Needed

### Core Dialogue

| File | Size | Purpose |
|------|------|---------|
| `scripts/dialogue_system.py` | - | Core dialogue logic |
| `scripts/nlu_engine.py` | 23KB | Fuzzy matching intent detection |
| `scripts/news_generator.py` | 12KB | News headlines & dynamic intent API |

### Data Files

| File | Size | Purpose |
|------|------|---------|
| `data/canned_responses.json` | 21KB | Base response library |
| `data/small_talk_intents.json` | 22KB | 10 intent categories, 100+ variations |
| `data/cyberpunk_intents.json` | 44KB | 11 cyberpunk topics, 335 responses |
| `data/response_variations.json` | 30KB | Mood/weather/personality variations |
| `data/context_intents.json` | 16KB | Activity/location aware responses |
| `data/cultural_dialects.json` | 15KB | 6 districts with slang |
| `data/news_events.json` | 15KB | Event categories, headline templates |
| `data/news_extended.json` | 20KB | NPC entities, Echo discoveries, rumors |

---

## News & Events System

### Headlines from World Events

NPCs react to news based on what happens in the simulation:

```
📰 [UNDERGROUND_WIRE] Marcus Chen SAVES CHILD from Collapsing Structure
📰 [TEMPLE_BROADCAST] ECHO SIGHTING: Elena Vasquez Claims to Have Heard 'Music'
📰 [MARKET_GAZETTE] NEW: 'Neon Dreams Cafe' Opens Doors in Market District
```

### Event Categories

- **Crime**: Robbery, murder, gang violence, data theft
- **Political**: Temple announcements, resistance attacks, curfews
- **Economic**: Shortages, market crashes, new businesses
- **Technological**: Cyberware recalls, hack attacks, AI malfunctions
- **Environmental**: Smog alerts, disease outbreaks, toxic spills
- **Social**: Protests, riots, celebrations, scandals

### Echo Discoveries

Special news about music/Echoes with believer, skeptic, and curious reactions:

```json
{
  "believer": "I always knew Echoes were real. The music exists!",
  "skeptic": "Mass hysteria. That's all this Echo nonsense is.",
  "curious": "What if it's true? What if music really exists?"
}
```

### Rumors System

Unconfirmed stories that spread among NPCs:

- "They say there's an Echo hidden somewhere in the Undercity."
- "I heard the resistance has a working music device."
- "Someone told me the Temple has vaults full of instruments."

### Dynamic Intent API

Add new intents/responses at runtime:

```bash
python scripts/news_generator.py --add-intent "new_topic" '{"patterns": ["keyword"]}'
python scripts/news_generator.py --add-event crime "new_crime" "HEADLINE" "NPC reaction"
```

---

## Why This Works Without User Payment

1. **Arweave reads are FREE** - Pulling canned responses costs nothing
2. **AO process pre-funded** - Creator pays once, runs forever
3. **Conversations become assets** - Every chat improves the system
4. **No LLM dependency** - Works offline with growing library
5. **Deterministic** - Same NPC personality = consistent responses
6. **News is generated** - Headlines from world state, not LLM

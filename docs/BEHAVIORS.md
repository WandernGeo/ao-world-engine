# Behaviors Chunk - Dynamic NPC System

## Overview

`world_codec_14_behaviors.json` enables procedural NPC generation and embedded Python behaviors for dynamic world simulation.

## Archetypes

Templates for generating unknown NPCs at runtime:

| Code | Archetype | Use Case |
|------|-----------|----------|
| ARCH001 | Shopkeeper | Stores, markets |
| ARCH002 | Bartender | Bars, clubs |
| ARCH003 | Guard | Checkpoints, temples |
| ARCH004 | Street Vendor | Markets, alleys |
| ARCH005 | Medic | Clinics |
| ARCH006 | Civilian | Residences, streets |

### Example: Spawning "Grocery Store Owner #6 on Bedford Street"

```python
def spawn_ambient_npc(location, tick):
    # 1. Get archetype based on location type
    archetype = ARCHETYPES["shopkeeper"]
    
    # 2. Generate deterministic name
    seed = hash(f"{location.id}_{tick // 1000}")
    name = generate_name(seed)  # → "Marcus Webb"
    
    # 3. Apply district modifiers
    personality = archetype.personality_base.copy()
    if location.district == "undercity":
        personality["suspicion"] += 0.3
    
    # 4. Fill dialogue templates
    dialogue = archetype.dialogue_templates["greeting"][0]
    # "Welcome to {shop_name}. What can I get you?"
    # → "Welcome to Webb's Groceries. What can I get you?"
    
    return NPC(name=name, personality=personality, ...)
```

## Embedded Python Behaviors

Base64-encoded Python functions executed at runtime:

### BHV001: Dynamic Pricing
```python
def calculate_price(item_code, npc_id, player_id, tick):
    base_price = get_item(item_code).get('price', 100)
    trust = get_relationship(npc_id, player_id).get('trust', 0.5)
    
    # Night = expensive, trust = discount
    hour = tick % 24
    time_mod = 1.2 if hour < 6 or hour > 20 else 1.0
    trust_mod = 1.0 - (trust * 0.3)  # Up to 30% off
    
    return {
        'price': int(base_price * time_mod * trust_mod),
        'attitude': 'friendly' if trust > 0.7 else 'wary'
    }
```

### BHV002: Event Reactions
```python
def react_to_event(npc_id, event_type, event_data, tick):
    personality = get_npc(npc_id).get('personality', {})
    
    if event_type in ['violence', 'gunfire']:
        if personality.get('fear', 0.5) > 0.6:
            return {'reaction': 'flee', 'spread_gossip': True}
        elif personality.get('aggression', 0.5) > 0.7:
            return {'reaction': 'investigate', 'spread_gossip': True}
```

### BHV003: Information Sharing
```python
def share_information(npc_id, player_id, payment, topic):
    trust = get_relationship(npc_id, player_id).get('trust', 0.5)
    info_score = (payment / 100) + trust
    
    if info_score > 1.5:
        return {'info_level': 'secret', 'rumor': get_secret_rumor(topic)}
    elif info_score > 0.8:
        return {'info_level': 'useful', 'rumor': get_common_rumor(topic)}
    else:
        return {'info_level': 'vague', 'rumor': 'Nothing I know about.'}
```

## PostGIS Integration

```sql
-- Find NPCs near player
SELECT l.*, d.danger_level 
FROM locations l 
JOIN districts d ON ST_Within(l.geom, d.geom) 
WHERE ST_DWithin(l.geom, ST_MakePoint(-73.9857, 40.6892)::geography, 500)
```

## Dialogue Variables

Templates use dynamic variables filled at runtime:

```json
{
  "weather_comment": {
    "clear": ["Nice day for business.", "At least the sun's out."],
    "rain": ["Damn rain won't stop.", "Streets are empty."],
    "storm": ["Hell of a storm.", "Watch the flooding."]
  },
  "trust_comment": {
    "high": ["For a friend like you.", "You know I got you."],
    "low": ["Cash up front.", "No discounts for strangers."]
  }
}
```

## Complete Data Flow

```
Player at GPS coords → PostGIS query → Location found
    ↓
Location type (shop) → Archetype (shopkeeper)
    ↓
Deterministic seed → Name ("Marcus Webb")
    ↓
District modifiers → Personality adjusted
    ↓
Behavior execution → Dynamic pricing, reactions
    ↓
LLM with full context → Natural dialogue
```

## Usage in Code

```python
from codec_chunks.chunk_loader import get_codec
import base64

codec = get_codec()

# Get archetype
archetype = codec.data.get("archetypes", {}).get("shopkeeper")

# Decode and execute behavior
behavior = codec.data.get("behaviors", {}).get("BHV001")
python_code = base64.b64decode(behavior["python_b64"]).decode()
exec(python_code)
result = calculate_price("O070", "npc_001", "player_001", 1337)
```

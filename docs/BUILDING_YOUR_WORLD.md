# Building Your World

This guide shows how to create your own persistent world using AO World Engine.

## Quick Overview

```
1. Fork this repo
2. Define your world's theme & lore (PRIVATE - yours)
3. Customize schemas (factions, archetypes)
4. Deploy to AO
5. Build visualization layer (PRIVATE - yours)
```

## Step 1: Define Your World

Create a private `lore/` directory for your copyrighted content:

```
your-world/
├── lore/                    # YOUR COPYRIGHT - keep private
│   ├── world_bible.md       # History, culture, rules
│   ├── factions.md          # Your faction backstories
│   ├── characters/          # Named characters
│   └── art_style.md         # Visual direction
├── schemas/                 # Can be public or private
│   ├── factions.json        # Customized from template
│   └── archetypes.json      # Your character types
└── ao-processes/            # Deploy to AO
```

## Step 2: Customize Factions

Edit `schemas/factions.json`:

```json
{
  "your_faction": {
    "name": "The Nightwatchers",
    "motto": "We see in darkness",
    "philosophy": "vigilante_justice",
    "territories": ["old_town", "docks"],
    "trust_modifiers": {
      "your_faction": 0.8,
      "rival_faction": -0.6
    }
  }
}
```

## Step 3: Define Archetypes

Create character templates in `archetypes/`:

```json
{
  "night_stalker": {
    "name": "Night Stalker",
    "personality_base": { "stealth": 0.9, "justice": 0.7 },
    "goals": ["patrol_night", "protect_innocent"],
    "routine": [
      { "time": "20-6", "action": "patrol", "probability": 0.9 },
      { "time": "6-14", "action": "R", "probability": 0.8 }
    ]
  }
}
```

## Step 4: Set Canon Rules

Update `docs/CANON_GOVERNANCE.md` with your world's rules:

- What elements are allowed?
- What breaks immersion?
- How should invalid content be transformed?

## Step 5: Deploy to AO

```bash
aos
.load ao-processes/district.lua
Send({ Target = ao.id, Action = "init", Data = '{"npc_count": 1000}' })
```

## Step 6: Build Visualization

Your visualization layer is **separate and private**:

- Web viewer (React, Three.js)
- Animation engine
- Art style/assets
- LLM prompts for narrative expansion

This is YOUR intellectual property built ON the open engine.

---

## What's Open vs What's Yours

| Open Source (Engine) | Your Copyright |
|---------------------|----------------|
| NPC state machines | Your lore |
| Scheduling logic | Your characters |
| Faction framework | Your art style |
| Event broadcasting | Your animations |
| Canon validation | Your world name |

---

## Example Worlds

You can build ANY persistent world:

- **Cyberpunk City** - Neon-lit noir metropolis
- **Fantasy Kingdom** - Medieval realm with guilds
- **Space Station** - Sci-fi orbital habitat
- **Wild West Town** - Frontier settlement
- **Post-Apocalypse** - Survivor camps

The engine is genre-agnostic. Your lore makes it unique.

---

*Questions? Open an issue on GitHub.*

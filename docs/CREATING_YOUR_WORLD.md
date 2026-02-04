# Creating Your World

The AO World Engine is a **generic simulation engine**. This guide shows you how to create your own world with unique style, lore, and characters.

---

## World Structure

Your world content lives in a `worlds/` directory:

```
ao-world-engine/
├── engine/              # Core simulation (don't modify)
├── worlds/
│   ├── example-fantasy/         # Simple example world
│   │   ├── config.json          # World configuration
│   │   ├── style_guide.md       # Your visual style
│   │   ├── npcs/                # Character definitions
│   │   ├── locations/           # Places in your world
│   │   ├── dialogue/            # Conversation content
│   │   └── lore/                # Background story
│   │
│   └── YOUR-WORLD/              # Your custom world
│       └── ...
```

---

## Quick Start

### 1. Copy the Example World

```bash
cp -r worlds/example-fantasy worlds/my-world
```

### 2. Edit `config.json`

```json
{
  "name": "My World",
  "style": "dark-fantasy",
  "calendar": {
    "months": ["Frostfall", "Snowmelt", ...],
    "ticks_per_day": 100
  },
  "factions": ["Kingdom", "Rebels", "Merchants"],
  "mood": "gritty and mysterious"
}
```

### 3. Define Your Style Guide

Create `style_guide.md` with your visual aesthetic:

```markdown
# My World Visual Style

## Color Palette
- Primary: #8B4513 (leather brown)
- Accent: #FFD700 (gold)
- Background: #1a1a2e (dark navy)

## Aesthetic References
- Lord of the Rings concept art
- Medieval manuscripts
- Gothic architecture

## Weather
Mostly overcast, occasional snow in winter
```

### 4. Add NPCs

Create `npcs/innkeeper.json`:

```json
{
  "id": "innkeeper",
  "name": "Marta",
  "occupation": "Innkeeper",
  "personality": ["warm", "gossip-loving", "protective"],
  "schedule": {
    "morning": "kitchen",
    "day": "common_room",
    "evening": "bar",
    "night": "upstairs"
  },
  "dialogue_intents": ["greeting", "rumors", "room_rental", "food"]
}
```

### 5. Run Your World

```bash
python run_world.py --world my-world
```

---

## Style Guide Examples

### Fantasy Kingdom
```
- Warm torchlight, stone castles
- Medieval clothing, leather and chainmail
- Green forests, rolling hills
- Magic exists but is rare
```

### Cyberpunk City
```
- Neon lights, rain-slicked streets
- High tech, low life aesthetic
- Megacorporations and street gangs
- Augmented humans, AI
```

### Post-Apocalyptic
```
- Rust, decay, overgrown ruins
- Scavenged technology
- Small settlements, dangerous wilderness
- Hope amid destruction
```

### Steampunk Victorian
```
- Brass, copper, gears
- Steam-powered machinery
- Victorian fashion with gadgets
- Airships and clockwork
```

---

## Connecting to Demo Server

Want to see your world running? You can:

1. **Local Demo**: Run locally with `npm run dev`
2. **Request Hosting**: Contact us to host your world on our demo servers
3. **Self-Host**: Deploy to your own Cloud Run / Vercel

---

## Professional World-Building Service

Need help creating a fully-realized world?

**StudioRam offers:**
- Custom visual style guides
- Character design and artwork
- Dialogue writing (1000+ lines)
- Lore bible creation
- Animation-ready assets

Contact: [studioram.app](https://studioram.app)

---

## Example: RE:ECHO City Demo

The demo at [ao-world-engine.run.app](https://ao-world-engine-1071951656531.us-central1.run.app) shows our flagship world **RE:ECHO City** - a cyberpunk noir dystopia.

> Note: RE:ECHO City content (style guide, characters, lore) is proprietary. The demo shows what's possible with the engine. Create your own world or contact us for licensing.

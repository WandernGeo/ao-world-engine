# World Plugins & Private Content

This document explains how the AO World Engine plugin system works and how to access private content.

---

## Architecture Overview

```
Documents/wandern/
├── ao-world-engine/           # PUBLIC - Open source engine
│   ├── config.json            # Points to active world
│   ├── scripts/world_loader.py
│   └── data/examples/         # Generic example data
│
├── worlds/                    # World plugins (can be private)
│   ├── signal-noir/           # RE:ECHO plugin (your IP)
│   │   ├── world.json         # Manifest
│   │   ├── npcs/npcs.json     # 800 NPCs
│   │   ├── lore/timeline.json  
│   │   └── style/             # Art direction
│   └── example-city/          # Vanilla example
│
└── reecho-city-private/       # PRIVATE - Business/marketing docs
    ├── ADMIN_WORKSHOP.md      # IP governance rules
    ├── IP_ARCHITECTURE.md     # This workflow diagram
    ├── LORE.md                # Full narrative
    ├── MONETIZATION_STRATEGY.md
    ├── GRANT_PITCH.md
    └── full_data_backup/      # Backup of all RE:ECHO data
        ├── codec_chunks/      # Original world codec
        └── npcs_full.json     # Original 800 NPCs
```

---

## How to Switch Worlds

Edit `ao-world-engine/config.json`:

```json
{
  "active_world": "signal-noir",   // or "example-city"
  "worlds_path": "/path/to/worlds"
}
```

---

## Private Folder Reference

### reecho-city-private/

| File | Purpose |
|------|---------|
| `ADMIN_WORKSHOP.md` | IP governance rules, deployment privacy levels |
| `IP_ARCHITECTURE.md` | Complete architecture diagram of public/private split |
| `LORE.md` | Full RE:ECHO City narrative and backstory |
| `MONETIZATION_STRATEGY.md` | Business model, revenue streams |
| `GRANT_PITCH.md` | Funding applications content |
| `starter_archetypes.json` | Character archetype definitions |

### full_data_backup/

Complete backup of all RE:ECHO content before vanilla conversion:
- `npcs_full.json` - All 800 NPCs with full personalities
- `codec_chunks/` - 26 world codec files with RE:ECHO lore

---

## Loading Plugin Data in Code

```python
from scripts.world_loader import WorldLoader

loader = WorldLoader('config.json')
world = loader.active_world

# Load content
npcs = world.load_npcs()       # Returns 800 NPCs for Signal Noir
lore = world.load_lore()       # Returns timeline, factions
style = world.get_style()      # Returns art direction JSON
```

---

## Cloud Run Deployment

For deployment, the Signal Noir plugin is bundled:

```dockerfile
# Copy world plugin for production
COPY ../worlds/signal-noir /app/worlds/signal-noir
```

---

## See Also

- [config.json](../config.json) - Engine configuration
- [world_loader.py](../scripts/world_loader.py) - Plugin loader code
- [ADMIN_WORKSHOP.md](../../reecho-city-private/ADMIN_WORKSHOP.md) - Governance rules

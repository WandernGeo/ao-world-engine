# Addon System

> Modular extensions for neighborhoods, slang, story templates, and dialogue

---

## Structure

```
ao-world-engine/
├── data/                    # Core data (always loaded)
│   ├── canned_responses.json
│   ├── cultural_dialects.json
│   └── story_templates.json
│
└── addons/                  # Community addons (merged at runtime)
    ├── example_neighborhood/
    │   ├── neighborhood.json
    │   └── README.md
    ├── cyberpunk_slang_pack/
    │   └── slang.json
    └── faction_expansion/
        └── faction.json
```

---

## Addon Types

### 1. Neighborhood Addon
Add new districts with their own culture:

```json
{
  "_addon_type": "neighborhood",
  "_addon_id": "neon_alley",
  "district": {
    "id": "neon_alley",
    "name": "Neon Alley",
    "culture": "nightlife_party",
    "greetings": ["Heyyy!", "Party's this way!"],
    "slang": {"party": "glow", "drunk": "lit"},
    "phrases": ["What happens in the Alley stays in the Alley."]
  }
}
```

### 2. Slang Pack Addon
Add slang without a full neighborhood:

```json
{
  "_addon_type": "slang_pack",
  "_addon_id": "hacker_slang",
  "applies_to": ["undercity", "docks"],
  "slang": {
    "hack": "jack",
    "computer": "deck",
    "virus": "ice breaker"
  }
}
```

### 3. Story Template Addon
Add new story patterns:

```json
{
  "_addon_type": "story_templates",
  "_addon_id": "heist_stories",
  "story_templates": {
    "heist_planning": {
      "steps": [...]
    }
  }
}
```

### 4. Faction Addon
Add new factions:

```json
{
  "_addon_type": "faction",
  "_addon_id": "tech_cult",
  "faction": {
    "id": "tech_cult",
    "in_phrases": ["Code is law."],
    "slang": {"member": "node"}
  }
}
```

---

## Loading Addons

```python
import json
from pathlib import Path

def load_addons(addons_dir: Path) -> dict:
    """Load and merge all addons into base data."""
    merged = {
        "districts": {},
        "factions": {},
        "slang": {},
        "story_templates": {},
        "canned_responses": {}
    }
    
    for addon_path in addons_dir.glob("*/"):
        for json_file in addon_path.glob("*.json"):
            addon = json.load(open(json_file))
            addon_type = addon.get("_addon_type")
            
            if addon_type == "neighborhood":
                district = addon.get("district", {})
                merged["districts"][district["id"]] = district
                
            elif addon_type == "slang_pack":
                for target in addon.get("applies_to", []):
                    merged["slang"].setdefault(target, {}).update(addon.get("slang", {}))
                    
            elif addon_type == "story_templates":
                merged["story_templates"].update(addon.get("story_templates", {}))
                
            elif addon_type == "faction":
                faction = addon.get("faction", {})
                merged["factions"][faction["id"]] = faction
    
    return merged
```

---

## Arweave Storage

Addons can live on Arweave for permanent, decentralized access:

```
ar://ADDON_TX_ID/neighborhood.json
```

The AO process can load addons from Arweave transaction IDs:

```lua
Handlers.add("LoadAddon",
  function(msg) return msg.Action == "LoadAddon" end,
  function(msg)
    local addon_tx = msg.AddonTx
    local addon_data = Arweave.load(addon_tx)
    MergeAddon(addon_data)
  end
)
```

---

## Community Contribution

1. Fork the repo
2. Create `addons/your_addon_name/`
3. Add your JSON files
4. Submit PR

Or publish directly to Arweave and share the TX ID.

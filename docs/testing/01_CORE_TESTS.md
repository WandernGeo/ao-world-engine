# Core Simulation Tests (66 tests)

> **Updated:** 2026-02-05T07:20:00-05:00

Tests for the foundational simulation components: NPCs, buildings, districts.

---

## NPC Data (14 tests)

| Test Name | What It Validates | Pass Criteria |
|-----------|------------------|---------------|
| NPC Codec Exists | Main NPC data file | world_codec_01_npcs.json exists |
| Founding NPC Count | 12 main characters | ≥12 founding NPCs defined |
| 800 NPCs in Lua | Full population | ≥800 NPC entries in all_npcs.lua |
| Required Fields Present | Core fields exist | id, name, faction for all NPCs |
| Relationships Coverage | NPCs connected | ≥80% have relationships |
| Faction Distribution | NPCs across factions | Each faction has members |
| Skills Coverage | NPCs have abilities | ≥80% have skills array |
| Personality Data Coverage | Character traits | Personality objects defined |

### How It Works

```python
# Load NPC codec data
npcs_codec = self.load_codec("world_codec_01_npcs")
founding_npcs = npcs_codec.get("founding_npcs", {})

# Check required fields
required_fields = ["code", "name", "role", "faction"]
for npc_key, npc in founding_npcs.items():
    for field in required_fields:
        if field not in npc:
            missing_required.append({"id": npc_key, "field": field})
```

---

## Founding Cast (14 tests)

| Test Name | What It Validates | Pass Criteria |
|-----------|------------------|---------------|
| Cast Count | Main characters | ≥12 founding NPCs |
| Charlie Exists | Protagonist | charlie character data |
| Kai Vance Exists | Tactician | kai_vance character |
| Zero Chen Exists | Netrunner | zero_chen character |
| Nova Chen Exists | Zero's sister | nova_chen character |
| Felix Exists | Bartender/informant | felix character |
| Pixel Exists | Child hacker | pixel character |
| Sister Mira Exists | Temple insider | sister_mira character |
| Vex Exists | Antagonist | vex character |
| Interconnected Relationships | Cast linked | Trust values defined |
| Backstory Depth | Character history | backstory/history fields |
| Secrets Defined | Hidden info | secrets array |
| Catchphrases | Unique dialogue | catchphrases array |
| Knowledge Domains | Expertise | knowledge_domains array |

### Required Founding NPC Fields

```lua
["charlie"] = {
    code = "NPC_FND_001",
    name = "Charlie",
    role = "Protagonist/Player Character",
    faction = "resistance",
    location_home = "L012",           -- Apartment
    cybernetics = {"CY001"},          -- Basic implant
    skills_primary = {"S01", "S04"},  -- Stealth, Tech
    relationships = {
        ["kai_vance"] = { trust = 0.7, type = "R01" },
        ["zero_chen"] = { trust = 0.8, type = "R02" },
    },
    knowledge_domains = ["tech", "underground"],
    secrets = ["knows resistance plans"],
    catchphrases = ["Stay low, stay alive."]
}
```

---

## Building Data (4 tests)

| Test Name | What It Validates |
|-----------|------------------|
| Building Types | Residential, commercial, industrial |
| Room Types | Rooms defined for buildings |
| Capacity | Buildings have capacity limits |
| District Assignment | Buildings linked to districts |

---

## Districts (3 tests)

| Test Name | What It Validates |
|-----------|------------------|
| District Definitions | Main city districts defined |
| Zone Types | R, C, I zones correct |
| Population | District population tracking |

---

## AO Processes (18 tests)

Tests that all Lua processes are valid.

| Test Name | What It Validates |
|-----------|------------------|
| Process Files Exist | All .lua files in ao-processes/ |
| Syntax Valid | No Lua syntax errors |
| Handlers Present | Handlers.add() calls exist |
| Exports Present | return {} at end |

### Files Tested

1. `world.lua` - Core world simulation
2. `economy.lua` - Economic system
3. `social.lua` - Relationships
4. `factions.lua` - Faction system
5. `vehicles.lua` - Transport
6. `occupations.lua` - Jobs
7. `news_system.lua` - Information
8. `encounters.lua` - Meetings
9. `universal_plugin.lua` - Content loading
10. `content_registry.lua` - Dynamic registration
11. `agent_needs.lua` - NPC needs
12. `event_sourcing.lua` - Event logging
13. `ai_oracle.lua` - LLM integration
14. `canon_validator.lua` - Lore consistency
15. `echo_generator.lua` - AR content
16. `district.lua` - Zone management
17. `logging.lua` - Debug output
18. `founding_npcs.lua` - Main characters
19. `all_npcs.lua` - Full NPC data

---

## Codec Files (3 tests)

| Test Name | What It Validates |
|-----------|------------------|
| JSON Validity | All codec JSON files parse |
| Required Structure | Expected keys present |
| Version Match | Codec versions compatible |

---

*Part of the AO World Engine Test Suite*

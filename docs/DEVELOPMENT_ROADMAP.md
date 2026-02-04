# AO World Engine - Development Roadmap & TODO

**Last Updated:** 2026-02-04
**Status:** Active Development

---

## 🎯 Priority 1: Python → Lua Migration (AO Native)

All simulation logic must eventually run on AO (Arweave) which executes **Lua**, not Python.

### Core API Files to Convert

| Python File | Purpose | Lua Target | Priority |
|-------------|---------|------------|----------|
| `api/api_simulation.py` | NPC schedules, states, locations | `ao-processes/simulation.lua` | **HIGH** |
| `api/event_engine.py` | Event triggers, cascading events | `ao-processes/events.lua` | **HIGH** |
| `api/npc_memory.py` | NPC memory persistence | `ao-processes/memory.lua` | MEDIUM |
| `api/npc_chat.py` | Chat with Vertex AI | External API (keep Python) | LOW |
| `api/studioram/scene_generator.py` | Vertex AI image gen | External API (keep Python) | LOW |
| `api/founding_npcs.py` | NPC data definitions | JSON on Arweave (data only) | DONE |

### AI/Behavior Scripts to Convert

| Python File | Purpose | Convert? |
|-------------|---------|----------|
| `scripts/advanced_ai_systems.py` | Utility AI, GOAP planning | **YES** → `ao-processes/ai.lua` |
| `scripts/simulation_behaviors.py` | Needs system, interactions | **YES** → `ao-processes/behaviors.lua` |
| `scripts/faction_ai.py` | Faction decision making | **YES** → Include in `ai.lua` |
| `scripts/cascading_events.py` | Event chain reactions | **YES** → `events.lua` |
| `scripts/news_generator.py` | Generate headlines | **YES** → `ao-processes/news.lua` |
| `scripts/nlu_engine.py` | Intent classification | External API (requires LLM) |
| `scripts/dialogue_system.py` | Dialogue generation | External API (requires LLM) |

### Data Scripts (One-time Use)

| Python File | Purpose | Action |
|-------------|---------|--------|
| `data/upload_world_codec.py` | Upload codec to Arweave | Keep as CLI tool |
| `data/upload_corrected_arweave.py` | Upload NPCs | Keep as CLI tool |
| `data/codec_chunks/chunk_loader.py` | Load codec chunks | Convert core logic to Lua |
| `scripts/deploy_to_arweave.py` | Deployment utility | Keep as CLI tool |

### AO Process Architecture (Target)

```
ao-processes/
├── district.lua          # Zone management, NPC movement
├── simulation.lua        # Tick processing, schedule resolution
├── npc_state.lua         # NPC state calculation
├── events.lua            # Event triggers, cascading
├── ai.lua                # Utility AI, GOAP, faction AI
├── behaviors.lua         # Needs system, interactions
├── memory.lua            # NPC memory persistence
├── news.lua              # News/headline generation
├── cron.lua              # Scheduled tick advancement
└── config.json           # World configuration
```

---

## 🎯 Priority 2: Family System Implementation

### Current State
- ✅ `family_trees` section exists in codec (3 founding families only)
- ✅ `R06 = "family"` relationship type defined
- ✅ **Family data generated for all 800 NPCs**
- ✅ **spouse_id/parent_ids/sibling_ids/children_ids fields**
- ✅ **479 household groupings**

### Schema Addition (NPC Records)

```json
{
  "id": "npc_0042",
  "name": "Kenji Mueller",
  "family": {
    "mother_id": "npc_0015",
    "father_id": "npc_0016",
    "spouse_id": "npc_0089",
    "siblings": ["npc_0043", "npc_0044"],
    "children": ["npc_0201", "npc_0202"],
    "household_id": "H027",
    "birth_tick": 0,
    "death_tick": null
  }
}
```

### Implementation Tasks

- [x] Add `family` schema to NPC codec
- [x] Generate ~150-200 household groups → **479 generated**
- [x] Assign ~60% of NPCs to family households
- [x] Create ~100 married couples → **160 married couples**
- [x] Generate parent-child relationships → **43 families with children**
- [x] Generate sibling relationships → **30 sibling pairs**
- [x] Single adults: ~25% of population → **310 single**
- [x] Link household members to same home building

### generational Life Simulation (Future)

- [ ] Aging system (NPCs age over simulation time)
- [ ] Marriage events (eligible singles meet, court, marry)
- [ ] Birth events (married couples have children)
- [ ] Death events (old age, accidents, faction conflicts)
- [ ] Inheritance (property, relationships transfer)

---

## 🎯 Priority 3: Graph Improvements

### 3D Sphere Rotation
- [x] Enable mouse drag to rotate the sphere → **Right-click drag**
- [x] Add smooth rotation animation → **Auto-spin toggle**
- [x] Camera orbit controls → **3D perspective projection**
- [ ] Touch support for mobile

### Interaction Improvements
- [x] Increase click radius for all nodes → **30px radius**
- [ ] Center-zoom on mouse position (not canvas center)
- [ ] Fix filter bar z-index (always on top)
- [ ] Node hover tooltips with NPC details

### Family Visualization
- [x] Add "family" edge type with distinct color → **pink=spouse, amber=sibling, cyan=parent**
- [x] Show household clusters → **showFamilyOnly toggle**
- [ ] Family tree view mode
- [ ] Parent-child hierarchy layout

### Stats Panel Readability
- [ ] Increase font size for Knowledge Graph stats
- [ ] Better contrast for text
- [ ] Responsive sizing for mobile

---

## 🎯 Priority 4: AI Systems Gaps

### From AI_GAP_ANALYSIS.md - Not Yet Implemented

| System | Description | Priority |
|--------|-------------|----------|
| **Cascading Events** | One event triggers chain reactions | HIGH |
| **LLM Story Translation** | Intent logs → readable dialogue | MEDIUM |
| **AO Cron Jobs** | World events on Lua timers | MEDIUM |
| **Arweave Export** | Significant events → permanent storage | MEDIUM |
| **Dynamic Schedule Override** | Relationships affect routines | LOW |

### Missing AI Features

- [ ] **Cascading Events Engine** - Event A triggers Event B which triggers Event C
- [ ] **Faction War System** - Territorial conflicts, raids, truces
- [ ] **Economy Simulation** - Supply/demand, price fluctuations
- [ ] **Reputation System** - NPC opinions of player/other NPCs spread
- [ ] **Memory Decay** - Old memories fade, significant ones persist

---

## 🎯 Priority 5: Frontend/UI Fixes

### Explore Page
- [x] Fix API connection (port 8082 → 8081)
- [x] Increase NPC limit to 800
- [ ] Building card styling improvements
- [ ] Role legend (floating, toggleable)
- [ ] Responsive layout for all screen sizes

### Chat Page
- [ ] Fix "Offline - API unavailable" when API running
- [ ] Better error handling for Vertex AI timeouts
- [ ] Show NPC's current activity/location

### Homepage Stats
- [ ] Update hardcoded stats:
  - NPCs with AI: 25+ → **800**
  - Buildings: Add **19**
  - Dialogue Lines: Keep or update

### Scene Generator
- [ ] Fix non-functional "Generate Scene" button
- [ ] Connect to StudioRam image generation API
- [ ] Show generation progress

---

## 🎯 Priority 6: StudioRam Integration

### Current Status
- `api/studioram/scene_generator.py` exists but needs API connection
- Vertex AI Imagen 4 available for image generation

### Tasks
- [ ] Audit StudioRam Cloud Run deployment
- [ ] Create proper scene generation endpoint
- [ ] Connect frontend to scene generator
- [ ] Add video generation (future - Veo 2)

---

## 🎯 Priority 7: Codec Enhancements

### Files to Update

| Codec File | Size | Updates Needed |
|------------|------|----------------|
| `world_codec_01_npcs_with_personality.json` | 81KB | ✅ Family data in npcs_generated.json |
| `world_codec_16_buildings.json` | 12KB | Add household assignments |
| ✅ `world_codec_17_family.json` | 4KB | **Created** - Family schema, simulation hooks |

### NPC Data Enrichment
- [x] Add `schedule_type` field to each NPC
- [x] Add `family` object to each NPC → **spouse, parents, siblings, children, household**
- [x] Add `home_building_id` for household grouping
- [x] Add `workplace_id` for work location
- [x] Add `age` field (18-75)
- [x] Add `appearance` object (skin, hair, eyes, height, build, notable)
- [x] Add `mood` object (current, intensity, stability, triggers)
- [x] Add needs system integration to API

---

## 🎯 Priority 8: Real-World Coordinates / OSM Integration

> See [REAL_WORLD_COORDINATES.md](./REAL_WORLD_COORDINATES.md) for full documentation.

### Current Status
- [x] `scripts/osm_to_codec.py` - OSM to World Codec converter
- [x] Overpass API query support
- [x] Building type classification (20+ types)
- [x] Fictional district renaming ("Midtown" → "Central Spire")
- [x] WGS84 and local coordinate systems
- [ ] MapLibre/Deck.gl visualization integration
- [ ] Example world: `worlds/neo-manhattan/`

### Use Cases
| Use Case | Description |
|----------|-------------|
| Ghost City | Overlay simulated NPCs on real city streets |
| Historical Sims | Recreate 1920s building layouts |
| Hybrid Fictional | Real layout, fictional names (legally distinct) |

---

## 📊 Completion Tracking

### Phase 1: Core Fixes (Current)
- [x] API port fix
- [x] NPC limit increase to 800
- [x] Schedule diversity (15 schedule types)
- [ ] Graph rotation (3D sphere)
- [x] **Family system generation** → **800 NPCs with family data**
- [x] **Family graph visualization** → **pink/amber/cyan edges**
- [x] **Needs system** → **calculate_needs() in API**
- [ ] Stats readability

### Phase 2: AO Migration
- [ ] Core simulation → Lua
- [ ] Event engine → Lua
- [ ] AI systems → Lua
- [ ] Deploy to AO testnet

### Phase 3: Polish
- [ ] StudioRam integration
- [ ] Cascading events
- [ ] Economy simulation
- [ ] Full family life cycle

---

## 🔗 Related Documentation

- [AI_GAP_ANALYSIS.md](./AI_GAP_ANALYSIS.md) - Detailed AI system status
- [AI_NPC_SYSTEM.md](./AI_NPC_SYSTEM.md) - NPC architecture
- [DIALOGUE_SYSTEM.md](./DIALOGUE_SYSTEM.md) - Chat system design
- [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) - API endpoints

---

*"First make it work. Then make it run on the permaweb."*

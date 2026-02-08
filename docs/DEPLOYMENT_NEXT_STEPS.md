# AO World Engine — Implementation Report & Next Steps

> **Date**: 2026-02-08 | **Status**: Engine shipped, deployment pipeline pending

---

## 1. Game Research Sources

We studied 4 city simulation games and scraped/documented their mechanics:

### Cities: Skylines 2 (Primary Reference)
- **56 wiki pages** scraped → `docs/cs2_wiki/` (gitignored, dev-only)
- **Key pages**: [economy](docs/cs2_wiki/economy.md) (41KB), [citizens](docs/cs2_wiki/citizens.md) (33KB), [happiness](docs/cs2_wiki/happiness.md) (33KB), [zoning](docs/cs2_wiki/zoning.md) (43KB), [services](docs/cs2_wiki/services.md) (42KB), [pollution](docs/cs2_wiki/pollution.md) (12KB), [crime](docs/cs2_wiki/crime.md) (42KB), [transportation](docs/cs2_wiki/transportation.md) (30KB)
- **Gap analysis**: [CS2_GAP_ANALYSIS.md](docs/CS2_GAP_ANALYSIS.md) — 71 features mapped, **44% coverage** (31/71) + 10 unique RE:ECHO systems
- **Wiki reference index**: [CS2_WIKI_REFERENCE.md](docs/CS2_WIKI_REFERENCE.md)

### Dwarf Fortress
- **4 wiki pages** → `docs/dwarf_fortress_wiki/` (gitignored)
- Topics: [labor](docs/dwarf_fortress_wiki/labor.md), [pathfinding](docs/dwarf_fortress_wiki/pathfinding.md), [thoughts](docs/dwarf_fortress_wiki/thoughts.md) (mood/needs system), [trading](docs/dwarf_fortress_wiki/trading.md)
- **Influenced**: NPC needs decay model, mood calculation, activity-driven behaviors in `agent_needs.lua`

### Oxygen Not Included (ONI)
- **5 wiki pages** → `docs/oni_wiki/` (gitignored)
- Topics: [duplicants](docs/oni_wiki/duplicants.md), [schedules](docs/oni_wiki/schedules.md), [priority](docs/oni_wiki/priority.md), [skills](docs/oni_wiki/skills.md), [game_mechanics](docs/oni_wiki/game_mechanics.md)
- **Influenced**: Schedule-driven NPC behavior, priority-based action selection, skill specialization in `occupations.lua`

### Workers & Resources: Soviet Republic
- **8 wiki pages** → `docs/workers_resources_wiki/` (gitignored)
- Topics: [citizens](docs/workers_resources_wiki/citizens.md), [economy](docs/workers_resources_wiki/economy.md), [education](docs/workers_resources_wiki/education.md), [happiness](docs/workers_resources_wiki/happiness.md), [crime_and_justice](docs/workers_resources_wiki/crime_and_justice.md), [pollution_and_radiation](docs/workers_resources_wiki/pollution_and_radiation.md), [trade](docs/workers_resources_wiki/trade.md), [traffic_simulation](docs/workers_resources_wiki/traffic_simulation.md)
- **Influenced**: Production chains, trade/diplomacy system, pollution accumulation/decay, education ladders in codecs 32-35

---

## 2. What Was Built

### 2a. Codec Loader (`codec_loader.lua`) — NEW
Central utility for hot-reloading JSON configuration into Lua modules.

| Function | Purpose |
|----------|---------|
| `load_codec(name, json)` | Parse + store codec data |
| `get_codec(name)` | Retrieve stored codec |
| `register_codec_callback(name, fn)` | Auto-apply config when codec (re)loads |
| `codec_get(data, "path.to.key")` | Safe deep key access |
| `deep_merge(target, source)` | Merge codec into defaults |

### 2b. 9 Refactored Lua Modules

Each module was refactored from hardcoded values → codec-driven with fallback defaults:

| Module | File | Game Inspiration | Codec(s) Used | What It Does |
|--------|------|------------------|---------------|--------------|
| **Economy** | `economy.lua` | CS2 taxation, budget, zones | `codec_20`, `codec_27` | Tax brackets, land value, city budget, crisis levels, production chains |
| **Agent Needs** | `agent_needs.lua` | DF thoughts, ONI duplicants | `codec_14` | 6 need types (hunger, energy, social, comfort, safety, purpose), decay, mood |
| **Social** | `social.lua` | CS2 happiness, DF social | `codec_19` | Relationship tracking, trust, interaction history |
| **World** | `world.lua` | CS2 city simulation | `codec_20`, `codec_30` | Master process, tick coordination, NPC state, global simulation |
| **Occupations** | `occupations.lua` | ONI skills/priority, CS2 employment | `codec_21`, `codec_34` | 14 occupation types, shift schedules, behavior assignment |
| **Vehicles** | `vehicles.lua` | CS2 transportation | `codec_23`, `codec_29` | 8 vehicle types, route system, commuting |
| **Factions** | `factions.lua` | Custom (RE:ECHO unique) | `codec_05` | Faction rivalry/alliance, territory, reputation, trust modifiers |
| **City Services** | `city_services.lua` | CS2 services, W&R infrastructure | `codec_28`, `codec_29` | 12 service categories, budget-efficiency curves, incident tracking |
| **District** | `district.lua` | CS2 districts & policies | `codec_25` | District demographics, zone policies |

### 2c. New Codec JSON Files (27-35)

Created from game research synthesis:

| Codec | Size | Game Source | What It Defines |
|-------|------|-------------|-----------------|
| `world_codec_27_city_finance.json` | 42KB | CS2 budget/loans | Tax rates, service budgets, loan system, revenue streams |
| `world_codec_28_city_services.json` | 26KB | CS2 services | 12 service types, coverage radius, budget scaling, upgrades |
| `world_codec_29_commuting.json` | 5KB | CS2 transport, W&R traffic | Commute routes, mode preferences, travel times |
| `world_codec_30_dynamic_metrics.json` | 14KB | CS2 info views | Real-time city health metrics, KPIs, dashboard data |
| `world_codec_31_crime_justice.json` | 7KB | CS2 crime, W&R justice | Crime probability, police response, court system |
| `world_codec_32_education.json` | 6KB | CS2 education, W&R education | 5 education tiers, enrollment, graduation, wage impact |
| `world_codec_33_pollution.json` | 5KB | CS2 pollution, W&R pollution | 4 pollution types (ground/air/water/noise), accumulation, decay |
| `world_codec_34_schedules_enhanced.json` | 8KB | ONI schedules | Time-of-day activity templates, occupation-specific routines |
| `world_codec_35_trade_diplomacy.json` | 6KB | W&R trade, CS2 outside trade | Import/export, trade balance, diplomatic relations |

### 2d. NPC Chat & NLU Engine

| File | What It Does |
|------|--------------|
| `api/npc_chat.py` | Refactored dialogue pipeline — context-aware NPC responses |
| `api/nlu_engine.py` | Intent classification with fuzzy matching (no LLM needed) |
| `api/city_economy.py` | Economic simulation API endpoints |
| `data/nlu/npc_intents.json` | 50+ intent patterns for NPC conversation |
| `data/nlu/npc_stories.json` | Dialogue flow stories |
| `docs/NPC_DIALOGUE_PATTERNS.md` | Design doc for chat system |
| `docs/blog_npc_chatbot_without_llms.md` | Technical blog post |

### 2e. Integration Test Suite

[test_integration_systems.lua](scripts/test_integration_systems.lua) — **72 tests, 8 categories, all passing**:

| # | Category | Tests | What It Validates |
|---|----------|-------|-------------------|
| 1 | Codec Loading Smoke | 10 | Load/reload/callback/merge/deep-access |
| 2 | Economic Cascade | 6 | Tax brackets, wages, budget crisis, land value |
| 3 | NPC Full Lifecycle | 9 | Init → occupation → shift → needs decay → mood |
| 4 | Faction-Social Dynamics | 10 | Factions, rivalry, trust, territory, reputation |
| 5 | City Services Feedback | 5 | Budget allocation, fees, capacity utilization |
| 6 | Determinism | 7 | Same inputs → same outputs (hash, seeded variance) |
| 7 | Edge Cases & Resilience | 16 | Nil safety, invalid JSON, batch operations, stress |
| 8 | Scenario: A Day in the City | 9 | Cross-system NPC journey through a full day |

### 2f. Documentation

| Doc | Purpose |
|-----|---------|
| [CS2_GAP_ANALYSIS.md](docs/CS2_GAP_ANALYSIS.md) | Feature-by-feature comparison with coverage scores |
| [IMPLEMENTATION_REVIEW.md](docs/IMPLEMENTATION_REVIEW.md) | Audit of all refactored modules |
| [CS2_WIKI_REFERENCE.md](docs/CS2_WIKI_REFERENCE.md) | Index of all scraped wiki pages |
| [NPC_DIALOGUE_PATTERNS.md](docs/NPC_DIALOGUE_PATTERNS.md) | Chat system design |
| [blog_npc_chatbot_without_llms.md](docs/blog_npc_chatbot_without_llms.md) | Technical blog post |

---

## 3. Git History (5 Commits Pushed)

```
4a95b99 docs: add deployment next steps
2d5b060 docs: CS2 gap analysis, integration tests, and security hardening
958ab8f feat: NPC chat refactor + NLU engine + city economy API
a8f99a9 feat: city services simulation + 9 new world codecs (27-35)
694ce32 feat: codec-driven engine — refactor 9 Lua modules to load config from JSON codecs
```

**Security measures**: `.gitignore` excludes scraping scripts (contain API keys), raw wiki data, wallet files, test artifacts.

---

## 4. Architecture — How It All Connects

```
┌─────────────────────────────────────────────────────────────┐
│                    ARWEAVE (Permanent Storage)               │
│  Codecs 00-26 ✅ uploaded (418KB, 30 files)                 │
│  Codecs 27-35 ❌ NOT YET UPLOADED (9 new files)             │
└──────────────────────┬──────────────────────────────────────┘
                       │ LoadCodec messages
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              AO PROCESS (Lua VM on Arweave)                  │
│  Process ID: 3KJMDJ81ob8qHUB8Fc-fn9n4pmSBqIh2S1DOM1zkqt0   │
│                                                              │
│  codec_loader.lua ──► 9 Lua modules listen via callbacks     │
│    economy ← codec_20, codec_27                              │
│    agent_needs ← codec_14                                    │
│    social ← codec_19                                         │
│    world ← codec_20, codec_30                                │
│    occupations ← codec_21, codec_34                          │
│    vehicles ← codec_23, codec_29                             │
│    factions ← codec_05                                       │
│    city_services ← codec_28, codec_29                        │
│    district ← codec_25                                       │
│                                                              │
│  Handlers: get-state, get-economy, get-time, get-npc-state   │
└──────────────────────┬──────────────────────────────────────┘
                       │ dryrun queries
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           BACKEND API (Cloud Run)                            │
│  ao-world-engine-api-*.us-central1.run.app                  │
│                                                              │
│  api_simulation.py — tick simulation endpoints               │
│  npc_chat.py — NPC dialogue (NLU engine)                     │
│  city_economy.py — economic simulation                       │
└──────────────────────┬──────────────────────────────────────┘
                       │ REST API
                       ▼
┌─────────────────────────────────────────────────────────────┐
│        STUDIO FRONTEND (Cloud Run)                           │
│  ao-world-engine-*.us-central1.run.app                      │
│                                                              │
│  ao-client.ts — AO failover + rate limiting + caching        │
│  SimulationProvider.tsx — tick sync + playback                │
│  GlobalTimeBar.tsx — clock display                           │
│  Pages: /monitor, /explore, /chat, /graph, /npcs             │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. What's Next — TODO

### Phase A: Upload New Codecs to Arweave
```bash
cd ao-world-engine
python scripts/upload_codec_to_arweave.py --dry-run   # preview
python scripts/upload_codec_to_arweave.py              # live upload
```
Uploads codecs 27-35 (9 files, ~120KB). Updates `data/arweave_codec_manifest.json`.

### Phase B: Load Codecs into AO Process
Send `LoadCodec` messages to AO process for each new codec:
- `Action = "LoadCodec"`, `Tags.CodecName = "economy"`, `Data = <JSON>`
- All 9 Lua modules auto-apply via `register_codec_callback`

### Phase C: Studio Repo — Consolidate & Deploy
1. Move `reecho-city-private/` IP content → `ao-world-engine-studio/docs/internal/`
2. Commit 8 pending studio changes (monitor, chat, graph pages + components)
3. Push to `WandernGeo/ao-world-engine-studio` (private GitHub)
4. Deploy: `gcloud builds submit --tag gcr.io/wandern-prod/ao-world-engine-studio`

### Phase D: Deploy API
```bash
cd ao-world-engine
gcloud builds submit --config cloudbuild-api.yaml
```

### Phase E: Verify Everything
- [ ] `/monitor` page loads and ticks advance
- [ ] Economy data reflects new codecs (finance, services, pollution)
- [ ] NPC chat responds via NLU engine
- [ ] `lua scripts/test_integration_systems.lua` — 72/72 pass
- [ ] No secrets in public repo

### Phase F: Remaining CS2 Gaps (44% → higher)
From [CS2_GAP_ANALYSIS.md](docs/CS2_GAP_ANALYSIS.md), the biggest gaps to close:

| Priority | Feature | Gap |
|----------|---------|-----|
| HIGH | Citizen lifecycle (life stages, education ladder) | `codec_28` created, engine logic needed |
| HIGH | Service coverage radius | Spatial model needed in `city_services.lua` |
| MEDIUM | Pollution accumulation/spread/decay | `codec_33` created, engine logic needed |
| MEDIUM | Crime probability model | `codec_31` created, engine logic needed |
| LOW | Disaster system | `codec_31` has triggers, engine needed |
| LOW | Loan system | `codec_27` has loan data, engine needed |
| LOW | Building level-up mechanic | Data exists in `codec_16` |

### Known Bugs
- **NPC patrol behavior**: Mechanic NPC (npc_00756, Ale Brooks) showing "patrolling" — `patrol` only assigned to police/security in `occupations.lua`. Data pipeline issue upstream.
- **`get_npc_needs(nil)`** crashes with table index error — needs nil guard in `agent_needs.lua`
- **`can_interact()` for rivals** uses `math.random() < 0.2` — non-deterministic, may need seeded RNG

# AO World Engine - Complete Architecture Guide

## Quick Start

### 1. View Live Simulation
```bash
# Check current on-chain state
node scripts/verify_ao_state.mjs
```

Output shows:
- **WorldTick**: Current simulation tick (advances every 10 min)
- **Population**: 800 NPCs
- **Budget**: City treasury (1M GEP)

### 2. View on AO Explorer
[🔗 Live Process](https://www.ao.link/#/entity/3KJMDJ81ob8qHUB8Fc-fn9n4pmSBqIh2S1DOM1zkqt0)

---

## How the Seed Works

### Deterministic Randomness

The simulation is 100% reproducible. Same seed = same events.

```lua
-- In world.lua
WorldSeed = "REECHO_CITY_2087"

function seeded_random(context)
    -- Combine seed + tick + context for unique but reproducible value
    local hash = crypto.digest.sha256(WorldSeed .. "_" .. WorldTick .. "_" .. context)
    return tonumber(hash:sub(1, 8), 16) / 0xFFFFFFFF
end
```

### Example: Crime Event

```lua
-- At tick 100, should a robbery happen?
local crime_chance = seeded_random("tick_100_crime")
if crime_chance < 0.05 then  -- 5% chance
    -- This WILL happen at tick 100, every time, guaranteed
    trigger_robbery()
end
```

### Forking a Universe

To create an alternate timeline:
```lua
WorldSeed = "REECHO_CITY_2087_FORK_A"
```
Now ALL events will be different, but still deterministic.

---

## Architecture Layers

```
┌──────────────────────────────────────────────────────────┐
│                    ARWEAVE (Layer 1)                     │
│                   Permanent Storage                       │
├──────────────────────────────────────────────────────────┤
│  📁 Data Files (Uploaded)                                │
│  ├── world_codec.json      TX: wt_CuCFsOyg...           │
│  ├── wildlife.json         TX: SxkynGTnH...             │
│  ├── news_system.json      TX: hiFD2v9My...             │
│  └── (11 files total)                                    │
│                                                          │
│  📜 Lua Code (Deployable)                                │
│  ├── world.lua             ✅ Deployed                   │
│  ├── economy.lua           ✅ Deployed                   │
│  ├── nature.lua            ⚠️ Ready, not deployed       │
│  ├── utilities.lua         ⚠️ Ready, not deployed       │
│  └── news.lua              ⚠️ Ready, not deployed       │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│                      AO (Layer 2)                        │
│                  Compute Network                          │
├──────────────────────────────────────────────────────────┤
│  Process: 3KJMDJ81ob8qHUB8Fc-fn9n4pmSBqIh2S1DOM1zkqt0   │
│                                                          │
│  🕐 CRON: Every 10 minutes                               │
│      └── Triggers: tick-handler                          │
│          └── Advances WorldTick                          │
│          └── Processes events                            │
│          └── Updates state                               │
│                                                          │
│  📊 State (On-Chain):                                    │
│      WorldTick: 107+                                     │
│      WorldDay: derived from tick                         │
│      Population: 800                                     │
│      CityBudget: 1,000,000 GEP                          │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│                    API (Layer 3)                         │
│                  Cloud Run Backend                        │
├──────────────────────────────────────────────────────────┤
│  Endpoints:                                              │
│  ├── /api/simulation/tick    Read simulation state      │
│  ├── /api/npcs               Get NPC data               │
│  ├── /api/news               Procedural news            │
│  └── /api/chat               NPC conversations          │
│                                                          │
│  ⚠️ NPC Memory: Cloud Run cache (ephemeral)             │
│      └── Needs: Auto-sync to Arweave                    │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│                  FRONTEND (Layer 4)                      │
│                   Vercel / Next.js                       │
├──────────────────────────────────────────────────────────┤
│  Pages:                                                  │
│  ├── /explore    City map viewer                        │
│  ├── /npcs       Character browser                      │
│  ├── /chat       NPC conversations                      │
│  ├── /graph      3D relationship viz                    │
│  └── /monitor    Live simulation dashboard              │
│                                                          │
│  ⚠️ Demo Mode: Simulates locally (default)              │
│      └── Toggle OFF to see real AO data                 │
└──────────────────────────────────────────────────────────┘
```

---

## Deployment Status

### ✅ Deployed to Arweave
| File | TX ID | Size |
|------|-------|------|
| world_codec.json | `wt_CuCFsO...` | 13KB |
| wildlife.json | `SxkynGTn...` | 8KB |
| ecosystem.json | `-qTEPaqj...` | 4KB |
| power_grid.json | `4G0monvc...` | 2KB |
| water_system.json | `zyHOoxx5...` | 2KB |
| gas_network.json | `4XjltZka...` | 2KB |
| isp_network.json | `pyjqkdhA...` | 2KB |
| mail_system.json | `A5lxbECa...` | 2KB |
| delivery_system.json | `1rg1bb2I...` | 2KB |
| food_delivery.json | `jjqi4lCh...` | 3KB |
| news_system.json | `hiFD2v9M...` | 6KB |

### ✅ Deployed to AO
| Module | Status |
|--------|--------|
| `world.lua` | ✅ Running, Tick 107+ |
| `economy.lua` | ✅ Loaded |

### ⚠️ Ready but Not Deployed
| Module | Location |
|--------|----------|
| `nature.lua` | `ao-processes/plugins/nature.lua` |
| `utilities.lua` | `ao-processes/utilities.lua` |
| `services.lua` | `ao-processes/services/services.lua` |
| `news.lua` | `ao-processes/services/news.lua` |

### ❌ Not Yet Built
| Feature | Priority |
|---------|----------|
| NPC Memory → Arweave sync | High |
| Skill progression system | Medium |
| Plugin hot-loading | Medium |

---

## Commands Reference

### Read State
```bash
node scripts/verify_ao_state.mjs
```

### Advance Tick Manually
```bash
node scripts/send_ao_message.mjs advance-tick '{}'
```

### Upload Data to Arweave
```bash
python3 scripts/upload_arweave_local.py
```

### Deploy Lua to AO
```bash
# Via aos CLI
aos> .load ao-processes/plugins/nature.lua
```

---

## Next Steps

1. **Deploy plugins to AO** - Load nature.lua, utilities.lua, etc.
2. **Auto-sync NPC memory** - Batch upload conversations to Arweave
3. **Frontend Live Mode** - Better UX for AO connection
4. **Skill progression** - WoW-style leveling codec

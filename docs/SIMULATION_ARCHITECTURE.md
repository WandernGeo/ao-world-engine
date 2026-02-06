# AO World Engine - Simulation Architecture

## Overview

The AO World Engine runs an autonomous city simulation where 800+ NPCs live, work, and interact. The simulation advances through **ticks** coordinated by a master Lua process on the AO network.

---

## Time System

### Tick Structure
| Unit | Definition |
|------|------------|
| **Tick** | Smallest time unit (6 real-world minutes) |
| **Day** | 240 ticks (24 simulation hours) |
| **Year** | 87,600 ticks (365 days) |

### Periods (T01-T09)
| Period | Sim Hours | EST Equivalent | Description |
|--------|-----------|----------------|-------------|
| T01 | 00:00-02:24 | 12am-2:24am | Deep night |
| T02 | 02:24-07:12 | 2:24am-7:12am | Pre-dawn |
| T03 | 07:12-10:00 | 7:12am-10am | Morning rush |
| T04 | 10:00-14:00 | 10am-2pm | Midday work |
| T05 | 14:00-17:00 | 2pm-5pm | Afternoon |
| T06 | 17:00-19:00 | 5pm-7pm | Evening commute |
| T07 | 19:00-21:00 | 7pm-9pm | Dinner/social |
| T08 | 21:00-23:00 | 9pm-11pm | Late evening |
| T09 | 23:00-00:00 | 11pm-12am | Night transition |

### EST Brooklyn Sync
The simulation is anchored to **Brooklyn, NY EST**:
- **Tick 0 of each day = 6:00 AM EST**
- 1 tick = 6 minutes real time
- Tick 60 = 12:00 PM EST (noon)
- Tick 180 = 12:00 AM EST (midnight)

**Frontend Calculation:**
```typescript
function tickToEST(tick: number): { hour: number; minute: number } {
    const dayTick = tick % 240;
    const simHour = Math.floor(dayTick / 10);
    const simMinute = (dayTick % 10) * 6;
    const estHour = (6 + simHour) % 24; // 6 AM anchor
    return { hour: estHour, minute: simMinute };
}
```

---

## Economy System

### Key Variables
| Variable | Description | Location |
|----------|-------------|----------|
| `CityBudget` | City treasury (GEP) | `world.lua` |
| `EconomicIndicators.gdp` | Gross Domestic Product | `economy.lua` |
| `EconomicIndicators.inflation` | Inflation rate (0.02 = 2%) | `economy.lua` |
| `EconomicIndicators.unemployment_rate` | Unemployment (0.12 = 12%) | `economy.lua` |
| `TaxRate` | Income tax rate (0.10 = 10%) | `world.lua` |

### Tax Collection
Daily tax collection happens at tick interval `TAX_COLLECTION_INTERVAL` (default: 240 = once per day).

---

## Travel Duration System

### Distance Types
| Distance Type | Walking Ticks | Minutes | Example |
|---------------|---------------|---------|---------|
| `same_building` | 0 | 0 | NPC moves within home |
| `adjacent_building` | 1 | 6 | Neighbor visit |
| `same_block` | 2 | 12 | Nearby shop |
| `same_district` | 5 | 30 | Work commute |
| `cross_district` | 15 | 90 | Temple to Neon District |
| `cross_city` | 40 | 240 | Undercity to Hab Blocks |

### Travel Modes
| Mode | Speed Multiplier |
|------|------------------|
| walking | 1.0x (base) |
| bicycle | 0.6x |
| motorcycle | 0.4x |
| car | 0.3x |
| metro | 0.5x |

### Movement Log Entry
```lua
{
    tick = 1234,
    npc_id = "npc_00001",
    from = "L001",
    to = "L003",
    state = "commuting",
    hour = 8,
    shift = "day",
    -- Travel duration fields
    mode = "walking",
    duration_ticks = 5,
    distance_type = "same_district",
    estimated_minutes = 30,
    eta_tick = 1239
}
```

---

## AO Handlers

### Query State
| Handler | Action Tag | Returns |
|---------|------------|---------|
| `get-state` | `Action: get-state` | tick, day, year, budget, population |
| `get-economy` | `Action: get-economy` | budget, tax_rate, revenue, expenses |
| `get-time` | `Action: get-time` | tick, hour, period, EST sync fields |
| `get-movement-log` | `Action: get-movement-log` | Recent NPC movements |
| `get-npc-locations` | `Action: get-npc-locations` | Current NPC positions |

### Example: Get Economy State
```lua
Send({ Target = WORLD_PROCESS, Action = "get-economy" })
-- Response: { budget: 1000000, tax_rate: 0.10, population: 800, ... }
```

---

## NPC Movement System

### Movement Logging
When NPCs travel between locations, events are logged to `MovementLog`:
```lua
{
    tick = 1234,
    npc_id = "npc_00001",
    npc_name = "Kenji Reed",
    from = "L001",
    to = "L003",
    reason = "commute_work",
    mode = "walk"
}
```

### Shifts & Schedules
NPCs have assigned shifts:
| Shift | Hours | Archetypes |
|-------|-------|------------|
| day | 09:00-17:00 | office, manager, lawyer |
| night | 21:00-05:00 | security, bartender, dancer |
| morning | 05:00-13:00 | baker, cleaner |
| flexible | 10:00-18:00 | artist, hacker, freelancer |
| always_on | 24/7 | doctor, police, firefighter |

---

## Frontend Integration

### SimulationProvider
The React `SimulationProvider` manages global state:
- `tick`, `day`, `year` - Current simulation time
- `isPlaying`, `playbackSpeed` - Playback controls
- `play()`, `pause()`, `setPlaybackSpeed()` - Control methods

### Cross-Page Sync
All pages share the same tick via `useSimulation()` hook:
- **Explore**: Map view with NPC positions
- **NPCs**: Population grid with stats
- **Chat**: Conversations with NPCs
- **Graph**: Knowledge graph relationships
- **Monitor**: Dashboard with economy & events

### Deep Linking
URL parameters sync NPC context between pages:
```
/npcs?npc=Kenji%20Reed      → Select NPC on NPCs page
/explore?npc=npc_00001      → Highlight NPC on map
/chat?npc=npc_00001         → Start chat with NPC
/graph?entity=npc_00001     → Focus NPC in graph
```

---

## File Locations

| Purpose | File |
|---------|------|
| Master world process | `ao-processes/world.lua` |
| Economy calculations | `ao-processes/economy.lua` |
| Action durations | `data/codec_chunks/world_codec_24_action_durations.json` |
| Frontend provider | `src/components/SimulationProvider.tsx` |
| Monitor dashboard | `src/app/monitor/page.tsx` |

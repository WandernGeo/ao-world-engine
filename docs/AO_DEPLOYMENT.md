# AO Autonomous World - Technical Documentation

## Live Status
| Metric | Value |
|--------|-------|
| **Process ID** | `3KJMDJ81ob8qHUB8Fc-fn9n4pmSBqIh2S1DOM1zkqt0` |
| **WorldTick** | 31+ (advancing every ~10 min via CRON) |
| **Population** | 800 NPCs |
| **CRON Status** | ✅ Active & Verified |
| **Tests** | ✅ 545/545 Passed |
| **Autonomous** | ✅ Proven (tick 27→31 observed) |

## CRON Interval Options

### Current: 10-minute interval (Standard)
- Process ticks every 10 minutes automatically
- Best for production (lower compute costs)

### Option: 1-minute interval (For Testing)
To change CRON interval, you must **respawn the process**:
```lua
ao.spawn("xU9zFkq3X2ZQ6olwNVvr1vUWIjc3kXTWr7xKQD6dh10", {
    Tags = {
        { name = "Cron-Interval", value = "1-minute" },  -- Faster!
        { name = "Cron-Tag-Action", value = "Cron" }
    }
})
```

### Manual Tick Advancement (Fastest)
For testing, manually advance ticks without waiting:
```bash
node scripts/send_ao_message.mjs advance-tick '{}'
```
Or in aos:
```lua
Send({ Target = ao.id, Action = "advance-tick" })
```

## How It Works

### 1. CRON-Driven Ticks
The AO process is spawned with CRON tags:
```lua
Tags = {
    { name = "Cron-Interval", value = "10-minutes" },
    { name = "Cron-Tag-Action", value = "Cron" }
}
```

Every 10 minutes, AO automatically sends a `Cron` message to the process, triggering the tick handler in `world.lua`:

```lua
Handlers.add("cron-tick", Handlers.utils.hasMatchingTag("Action", "Cron"), function(msg)
    WorldTick = WorldTick + 1
    -- Process day/year transitions
    -- Check world events
    -- Broadcast to districts
    -- Process economy
end)
```

### 2. State Persistence
All state variables persist on Arweave:
- `WorldTick` - Current simulation tick
- `WorldDay` / `WorldYear` - Time tracking
- `CityBudget` - Economy (1M GEP starting)
- `PopulationCount` - NPC count (800)
- `Districts` - Registered district processes

### 3. Event-Driven Architecture
The simulation uses an event-sourcing pattern:
```
CRON → WorldTick → Events → District Broadcast → NPC Updates
```

## Plugin Architecture

### Modular Design
Each system is a separate Lua module that can be loaded independently:

| Module | Purpose |
|--------|---------|
| `world.lua` | Master coordinator, CRON handler |
| `economy.lua` | Currency, jobs, businesses |
| `social.lua` | Relationships, factions |
| `agent_needs.lua` | Egregoria-style NPC needs |
| `event_sourcing.lua` | Event log, replay |
| `ai_oracle.lua` | AI dialogue generation |

### Adding New Plugins
1. Create `ao-processes/your_plugin.lua`
2. Implement handlers:
```lua
Handlers.add("your-action", Handlers.utils.hasMatchingTag("Action", "your-action"), function(msg)
    -- Plugin logic
end)
```
3. Load into process:
```lua
.load ao-processes/your_plugin.lua
```

### Handler Registration Pattern
```lua
-- Standard handler template
Handlers.add(
    "handler-name",
    Handlers.utils.hasMatchingTag("Action", "action-name"),
    function(msg)
        local data = json.decode(msg.Data)
        -- Process
        ao.send({
            Target = msg.From,
            Action = "response-name",
            Data = json.encode(result)
        })
    end
)
```

## Key API Endpoints

### Read State
```lua
Send({ Target = ao.id, Action = "get-state" })
```
Returns: `{ tick, day, year, population, budget, districts }`

### Initialize
```lua
Send({ Target = ao.id, Action = "Init", Data = '{"population": 800}' })
```

### Economy
```lua
Send({ Target = ao.id, Action = "get-economy" })
```

### Time
```lua
Send({ Target = ao.id, Action = "get-time" })
```

## Verification Scripts

```bash
# Check current state
node scripts/verify_ao_state.mjs

# Send signed message
node scripts/send_ao_message.mjs Init '{"population": 800}'

# Run simulation tests
python scripts/system_audit.py
```

## Upgrading the Process

### Option 1: Send New Code (Eval)
```lua
Send({ Target = ao.id, Action = "Eval", Data = "-- new Lua code" })
```

### Option 2: Spawn New Process
For major changes, spawn a new process and migrate state.

## Frontend Integration

### Current Status
The frontend has an `ao-client.ts` library for querying AO, but the monitor page uses **demo mode** (local simulation).

### AO Client (`frontend/src/lib/ao-client.ts`)
```typescript
import { dryrun } from "@permaweb/aoconnect";

export async function getWorldState() {
    const result = await dryrun({
        process: "3KJMDJ81ob8qHUB8Fc-fn9n4pmSBqIh2S1DOM1zkqt0",
        tags: [{ name: "Action", value: "get-state" }],
        data: "{}"
    });
    return JSON.parse(result.Messages[0].Data);
}
```

### To Enable Live AO Data
1. Toggle off "Demo Mode" in the Monitor page
2. The page will call `ao-client.ts` to fetch real state
3. For now, run `node scripts/verify_ao_state.mjs` to check live data

### Testing Tick Advancement
```bash
# Advance tick manually (instant)
node scripts/send_ao_message.mjs advance-tick '{}'

# Verify new state
node scripts/verify_ao_state.mjs
```

**Tested:** WorldTick successfully advanced from 23 → 27

## Links
- [**AO Live Monitor**](https://www.ao.link/#/entity/3KJMDJ81ob8qHUB8Fc-fn9n4pmSBqIh2S1DOM1zkqt0) ← Watch ticks in real-time!
- [Arweave TX](https://viewblock.io/arweave/tx/3KJMDJ81ob8qHUB8Fc-fn9n4pmSBqIh2S1DOM1zkqt0)
- [System Audit](./SYSTEM_AUDIT_REPORT.md) - 545/545 tests passing


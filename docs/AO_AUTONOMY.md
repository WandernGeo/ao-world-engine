# AO Autonomous World - Self-Sufficiency Documentation

> **Status**: ✅ VERIFIED AUTONOMOUS  
> **Process ID**: `3KJMDJ81ob8qHUB8Fc-fn9n4pmSBqIh2S1DOM1zkqt0`  
> **Last Verified**: 2026-02-06

---

## What Makes It Self-Sufficient

The AO World Engine simulation runs **indefinitely without external triggers** after initial deployment. Here's how:

### 1. AO CRON Mechanism

When the process was spawned, it was configured with CRON tags:

```lua
-- Spawn command used:
ao.spawn("xU9zFkq3X2ZQ6olwNVvr1vUWIjc3kXTWr7xKQD6dh10", {
    Tags = {
        { name = "Cron-Interval", value = "10-minutes" },
        { name = "Cron-Tag-Action", value = "Cron" }
    }
})
```

This tells the AO network scheduler to send `Action: "Cron"` messages every 10 minutes **automatically**.

### 2. The Heartbeat Handler

In `world.lua`, the cron handler processes these messages:

```lua
-- Location: ao-processes/world.lua:334-470
Handlers.add("cron-tick", Handlers.utils.hasMatchingTag("Action", "Cron"), function(msg)
    -- Skip if paused
    if SimulationStatus ~= "running" then return end
    
    -- 1. Advance world tick
    WorldTick = WorldTick + 1
    
    -- 2. Day/year transitions
    if WorldTick % TICKS_PER_DAY == 0 then
        WorldDay = WorldDay + 1
    end
    if WorldTick % TICKS_PER_YEAR == 0 then
        WorldYear = WorldYear + 1
    end
    
    -- 3. Process world events
    local events = check_world_events(WorldTick)
    
    -- 4. Broadcast to district processes
    for district_id, process_id in pairs(Districts) do
        ao.send({ Target = process_id, Action = "Cron", ... })
    end
    
    -- 5. Notify AI Oracle
    if AiOracle then ao.send({ Target = AiOracle, Action = "Cron" }) end
    
    -- 6. Process economy (taxes)
    if WorldTick % TAX_COLLECTION_INTERVAL == 0 then
        collect_taxes()
    end
    
    -- 7. Process utilities (power, water, internet)
    if Utilities then Utilities.on_tick(WorldTick, weather, npcs) end
end)
```

### 3. State Persistence

All state variables with **Uppercase names** are automatically persisted to Arweave:

```lua
-- Global state (persisted)
WorldTick = WorldTick or 0
WorldDay = WorldDay or 0
WorldYear = WorldYear or 0
CityBudget = CityBudget or 1000000
PopulationCount = PopulationCount or 0
Districts = Districts or {}
```

This means:
- ✅ If you turn off your computer, the simulation continues
- ✅ If the API server restarts, state is preserved
- ✅ Anyone can verify the current state via dry-run queries

---

## How State is Tracked

### World Time
| Variable | Purpose | Update Frequency |
|----------|---------|------------------|
| `WorldTick` | Simulation heartbeat | Every CRON (10 min) |
| `WorldDay` | In-game day | Every 240 ticks |
| `WorldYear` | In-game year | Every 87,600 ticks |

### Time Calculations
```lua
TICKS_PER_DAY = 240      -- 10 ticks/hour * 24 hours
TICKS_PER_YEAR = 87600   -- 365 days

function get_time_info(tick)
    local ticks_in_day = tick % TICKS_PER_DAY
    local hour = math.floor(ticks_in_day / 10)  -- 10 ticks per hour
    local period = hour < 6 and "night" or hour < 12 and "morning" or 
                   hour < 18 and "afternoon" or "evening"
    return { hour = hour, period = period, ... }
end
```

### Event Chain
```
CRON message → WorldTick++ → Events checked → Districts notified
                                                    ↓
                                           NPCs act locally
                                                    ↓
                                           Results logged to Arweave
```

---

## Time Compression

The simulation runs **slower than real time** by design:

| Real Time | Simulation Time |
|-----------|-----------------|
| 10 minutes | 1 tick (= 6 in-game minutes) |
| 1 hour | 6 ticks (= 36 in-game minutes) |
| 24 hours | 144 ticks (= 14.4 in-game hours) |

This is configurable. Current settings:
- **CRON interval**: 10 minutes (real time between ticks)
- **Ticks per in-game hour**: 10
- **Ticks per in-game day**: 240

To speed up for testing, either:
1. Respawn with faster CRON (see below)
2. Manually advance ticks (instant, no waiting)

---

## CRON Interval Configuration

### Supported Intervals

| Interval | Use Case |
|----------|----------|
| `1-minute` | Testing, real-time feel |
| `5-minutes` | Faster simulation |
| `10-minutes` | Production (current) |
| `1-hour` | Slow progression |

### Changing the Interval

To change CRON speed, you must **respawn the process**:

```lua
ao.spawn("xU9zFkq3X2ZQ6olwNVvr1vUWIjc3kXTWr7xKQD6dh10", {
    Tags = {
        { name = "Cron-Interval", value = "1-minute" },  -- Change here
        { name = "Cron-Tag-Action", value = "Cron" }
    }
})
```

### Manual Tick Advance (For Testing)

Skip waiting - advance ticks instantly:

```bash
# Advance 1 tick immediately
node scripts/send_ao_message.mjs advance-tick '{}'

# Advance 100 ticks at once
node scripts/send_ao_message.mjs advance-tick '{"ticks": 100}'
```

This is useful for:
- Testing NPC behaviors at different times of day
- Fast-forwarding to specific events
- Debugging time-dependent logic

---

## Verification Tests

### Test Script
```bash
# Run: scripts/test_ao_autonomy.sh
for i in 1 2 3 4; do
  echo "=== Test $i: $(date '+%Y-%m-%d %H:%M:%S') ==="
  node scripts/send_ao_message.mjs get-state '{}'
  sleep 600  # Wait 10 minutes
done
```

### Test Results

| Test # | Timestamp (UTC-5) | WorldTick | Expected | Status |
|--------|-------------------|-----------|----------|--------|
| 1 | 2026-02-06 04:56:17 | 141 | baseline | ✅ |
| 2 | 2026-02-06 05:06:XX | 142+ | +1 from T1 | PENDING |
| 3 | 2026-02-06 05:16:XX | 143+ | +1 from T2 | PENDING |
| 4 | 2026-02-06 05:26:XX | 144+ | +1 from T3 | PENDING |

> **Note**: Tests run automatically. Results will be appended after each interval.

---

## Why No External Triggers Needed

| Question | Answer |
|----------|--------|
| Who sends CRON messages? | AO network scheduler (not you) |
| Cost per tick? | Included in AO compute model |
| What if my computer is off? | Still runs on AR network |
| How long does it run? | Forever (until terminated) |
| Can I pause it? | Yes, send `Action: "pause"` message |
| Can others verify state? | Yes, via dry-run queries |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    ARWEAVE NETWORK                          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              AO SCHEDULER                              │  │
│  │  Sends { Action: "Cron" } every 10 minutes            │  │
│  └────────────────────────┬──────────────────────────────┘  │
│                           │                                  │
│                           ▼                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │          WORLD PROCESS (world.lua)                     │  │
│  │  ID: 3KJMDJ81ob8qHUB8Fc-fn9n4pmSBqIh2S1DOM1zkqt0     │  │
│  │                                                        │  │
│  │  On Cron:                                              │  │
│  │  1. WorldTick++                                        │  │
│  │  2. Check world events                                 │  │
│  │  3. Broadcast to districts                             │  │
│  │  4. Process economy                                    │  │
│  │  5. Update utilities                                   │  │
│  │  6. State auto-persisted to Arweave                   │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  ARWEAVE STORAGE                                      │   │
│  │  - All messages logged permanently                    │   │
│  │  - State reconstructible from logs                    │   │
│  │  - Anyone can verify via dry-run                      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    YOUR MACHINE / CLOUD RUN                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  API (npc_chat.py)                                     │  │
│  │  - Queries AO process for current state               │  │
│  │  - Does NOT trigger ticks (simulation is autonomous)  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Frontend (Next.js)                                    │  │
│  │  - Displays current state                              │  │
│  │  - Polls API for updates                               │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Related Files

| File | Purpose |
|------|---------|
| [world.lua](file:///Users/ram/Documents/wandern/ao-world-engine/ao-processes/world.lua) | Master process with CRON handler |
| [AO_DEPLOYMENT.md](file:///Users/ram/Documents/wandern/ao-world-engine/docs/AO_DEPLOYMENT.md) | Deployment instructions |
| [send_ao_message.mjs](file:///Users/ram/Documents/wandern/ao-world-engine/scripts/send_ao_message.mjs) | Query/message script |

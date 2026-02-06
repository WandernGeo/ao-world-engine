# AO World Engine - Simulation Systems

> **Status**: Production Ready (v11.6)  
> **Process ID**: `3KJMDJ81ob8qHUB8Fc-fn9n4pmSBqIh2S1DOM1zkqt0`

---

## Overview

The AO World Engine is a fully autonomous simulation running on the Arweave AO network. It simulates a futuristic city with:
- **NPCs** with schedules, movements, social relationships, and wallets
- **Economy** with wages, spending, taxes, and city budget
- **Time** with 10-minute real-world ticks (1 hour in-game per tick)
- **Persistence** through AO's permanent storage

---

## What is a Process ID?

### The Short Version
The **Process ID** (`3KJMDJ81ob8qHUB8Fc-fn9n4pmSBqIh2S1DOM1zkqt0`) is the **permanent address** of our simulation on the AO network. Think of it like:
- A phone number for our simulation that never changes
- A smart contract address (like Ethereum)
- A unique "world instance" identifier

---

### Detailed Explanation: Process Lifecycle

#### When is a Process ID Created?
A new Process ID is generated **every time someone spawns a new AO process**. Here's the lifecycle:

```
1. SPAWN PROCESS
   ┌─────────────────────────────────────────────────────────────┐
   │  aos --cron "10-minutes"                                    │
   │                                                             │
   │  → AO creates a NEW Arweave transaction                     │
   │  → Returns a unique 43-character ID                         │
   │  → This ID is PERMANENT and IMMUTABLE                       │
   └─────────────────────────────────────────────────────────────┘
                            ↓
2. LOAD CODE
   ┌─────────────────────────────────────────────────────────────┐
   │  .load world.lua                                            │
   │                                                             │
   │  → Lua code uploaded to this process                        │
   │  → Code becomes part of the process state                   │
   │  → Defines handlers, globals, CRON behavior                 │
   └─────────────────────────────────────────────────────────────┘
                            ↓
3. PROCESS RUNS FOREVER
   ┌─────────────────────────────────────────────────────────────┐
   │  CRON fires every 10 minutes                                │
   │  Messages can be sent to the process                        │
   │  State persists on Arweave permanently                      │
   │  NO SERVERS NEEDED - AO network handles everything          │
   └─────────────────────────────────────────────────────────────┘
```

#### Can the Process ID Change?
**NO** - once created, a Process ID never changes. However:

| Scenario | What Happens |
|----------|--------------|
| Update code | Same Process ID, new code overwrites old |
| Reset state | Same Process ID, state variables reset |
| New world | **NEW Process ID** - completely separate world |
| Fork/copy | **NEW Process ID** - independent copy |

---

### Multi-World Architecture

#### How Multiple Worlds Work
Each world you generate gets its **own unique Process ID**:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AO NETWORK (Cloud)                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  WORLD A: RE:ECHO City (Our main world)                            │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ Process ID: 3KJMDJ81ob8qHUB8Fc-fn9n4pmSBqIh2S1DOM1zkqt0       │ │
│  │ Population: 800 NPCs                                          │ │
│  │ Theme: Cyberpunk noir                                         │ │
│  │ Tick: 15,000+                                                 │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  WORLD B: Another user's world                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ Process ID: xY7kL9mN2pQ4rS6tU8wV0zA3bC5dE7fG9hI1jK3lM5n       │ │
│  │ Population: 200 NPCs                                          │ │
│  │ Theme: Fantasy medieval                                       │ │
│  │ Tick: 500                                                     │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  WORLD C: Test/development world                                   │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ Process ID: aB1cD2eF3gH4iJ5kL6mN7oP8qR9sT0uV1wX2yZ3aB4cD5e    │ │
│  │ Population: 10 NPCs                                           │ │
│  │ Theme: Testing sandbox                                        │ │
│  │ Tick: 50                                                      │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### Cross-World Communication (Future)
Worlds CAN communicate with each other via AO messages:

```lua
-- Send message from World A to World B
ao.send({
    Target = "xY7kL9mN2pQ4rS6tU8wV0zA3bC5dE7fG9hI1jK3lM5n",  -- World B's ID
    Action = "cross-world-event",
    Data = json.encode({ event = "NPC_MIGRATED", npc_id = "C01" })
})
```

This enables:
- NPCs traveling between worlds
- Cross-world economy
- Shared events and lore
- Multi-world quests

---

### Creating Your Own World

When you want a NEW world (not update existing):

```bash
# 1. Start AOS and spawn a NEW process
aos --cron "10-minutes"
# Returns: YOUR_NEW_PROCESS_ID (43 characters)

# 2. Load the world engine code
.load ao-processes/world.lua

# 3. Initialize with your custom settings
Send({ Target = ao.id, Action = "initialize", Data = '{"year": 2087, "theme": "cyberpunk"}' })

# 4. Load your NPCs
node scripts/load_npc_schedules.mjs --process YOUR_NEW_PROCESS_ID
```

Your new world now runs independently with its own:
- Process ID (the address)
- State (tick, NPCs, economy)
- CRON schedule
- Message handlers

---

### Process ID Registry (Planned)

For the AO World Engine ecosystem, we plan a **registry** of all worlds:

```lua
-- Future: World Registry Process
WorldRegistry = {
    ["3KJMDJ81ob8qHU..."] = { 
        name = "RE:ECHO City", 
        theme = "cyberpunk",
        population = 800,
        owner = "wallet_address"
    },
    ["xY7kL9mN2pQ4rS..."] = { 
        name = "Haven", 
        theme = "fantasy",
        population = 200,
        owner = "other_wallet"
    }
}
```

---

### Why Permanent Process IDs Matter

1. **Bookmarking**: Users can save the Process ID and return anytime
2. **APIs**: Frontend apps connect to a specific world by ID
3. **Verification**: Anyone can audit the code/state on Arweave
4. **Immutability**: The world's history is permanent and tamper-proof
5. **Interoperability**: Other apps can integrate with your world

---

### How AO Processes Work

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ARWEAVE NETWORK                             │
│  (Permanent, decentralized storage - data lives forever)           │
├─────────────────────────────────────────────────────────────────────┤
│                           AO LAYER                                  │
│  (Compute layer on top of Arweave - runs Lua code)                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌─────────────────────────────────────────────────────────┐       │
│   │  PROCESS: 3KJMDJ81ob8qHUB8Fc-fn9n4pmSBqIh2S1DOM1zkqt0  │       │
│   │                                                         │       │
│   │  📜 Code: world.lua (uploaded once)                    │       │
│   │  💾 State: WorldTick, NPCLocations, Wallets, etc.      │       │
│   │  📨 Messages: Handlers for get-state, advance-tick     │       │
│   │  ⏰ CRON: Triggers every 10 minutes automatically      │       │
│   │                                                         │       │
│   └─────────────────────────────────────────────────────────┘       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Concepts

| Concept | Description |
|---------|-------------|
| **Process** | A running program on AO with its own state and message handlers |
| **Process ID** | 43-character Arweave transaction ID that uniquely identifies the process |
| **Messages** | How you communicate with a process (like API calls) |
| **Handlers** | Functions that respond to specific message types |
| **State** | All global variables (persisted automatically to Arweave) |
| **CRON** | Scheduled triggers that run automatically |

### Why This Matters

1. **Permanent**: The process runs forever on the network (no servers to maintain)
2. **Autonomous**: CRON triggers advance the simulation without any manual action
3. **Trustless**: Anyone can verify the code and state on Arweave
4. **Free Reads**: `dryrun()` queries cost nothing (no wallet needed)
5. **Paid Writes**: Only state-changing operations require signed messages

### Interacting with the Process

```javascript
// READING (FREE - uses dryrun)
import { dryrun } from '@permaweb/aoconnect';
const result = await dryrun({
    process: '3KJMDJ81ob8qHUB8Fc-fn9n4pmSBqIh2S1DOM1zkqt0',
    tags: [{ name: 'Action', value: 'get-state' }],
    data: '{}'
});

// WRITING (requires wallet signature)
import { message } from '@permaweb/aoconnect';
await message({
    process: '3KJMDJ81ob8qHUB8Fc-fn9n4pmSBqIh2S1DOM1zkqt0',
    signer: createDataItemSigner(wallet),
    tags: [{ name: 'Action', value: 'advance-tick' }],
    data: '{"ticks": 10}'
});
```

### View on Arweave

- **AO Link**: [View Process](https://ao.link/#/entity/3KJMDJ81ob8qHUB8Fc-fn9n4pmSBqIh2S1DOM1zkqt0)
- **Arweave**: [View on ViewBlock](https://viewblock.io/arweave/tx/3KJMDJ81ob8qHUB8Fc-fn9n4pmSBqIh2S1DOM1zkqt0)

---

## 1. Time System

### Constants
| Constant | Value | Description |
|----------|-------|-------------|
| TICKS_PER_DAY | 24 | 24 hours per day |
| TICKS_PER_YEAR | 8760 | 365 days × 24 hours |

### Time Conversion
```lua
function get_time_info(tick)
    local hour = tick % 24        -- 0-23
    local day = math.floor(tick / 24) % 365 + 1
    local year = math.floor(tick / 8760) + 2087
    local period = get_time_period(hour)
    return { hour, day, year, period }
end
```

### Time Periods
| Period | Hours | NPC Activity |
|--------|-------|--------------|
| dawn | 5-7 | Waking up |
| morning | 7-12 | Working |
| afternoon | 12-17 | Working |
| evening | 17-21 | Socializing |
| night | 21-5 | Sleeping |

---

## 2. NPC Schedule System

### Shift Types (8)
| Shift | Start | End | Typical Roles |
|-------|-------|-----|---------------|
| day | 9 | 17 | Office workers, teachers |
| night | 22 | 6 | Security, bouncers |
| graveyard | 0 | 8 | Night nurses, 24hr clerks |
| evening | 16 | 24 | Bartenders, performers |
| morning | 4 | 12 | Bakers, garbage collectors |
| flexible | 10 | 18 | Artists, hackers |
| always_on | 0 | 24 | Doctors, ICU nurses |
| split | 11-14, 18-23 | Chefs, restaurant managers |

### Archetype → Shift Mapping
50+ occupations auto-map to shifts:
```lua
["security guard"] = "night"
["bartender"] = "evening"
["baker"] = "morning"
["doctor"] = "always_on"
["chef"] = "split"
```

### Schedule Data Structure
```lua
NPCSchedules = {
    ["npc_001"] = {
        home = "L001",      -- Home location code
        work = "L042",      -- Work location code
        shift = "night",    -- Shift type
        archetype = "security guard"
    }
}
```

---

## 3. NPC Movement System

### State Machine
```
              ┌──────────────┐
     dawn     │   sleeping   │ late night
    ┌─────────│              │◄────────────┐
    │         └──────────────┘             │
    ▼                                      │
┌──────────────┐                     ┌──────────────┐
│    waking    │                     │  going_home  │
└──────────────┘                     └──────────────┘
    │                                      ▲
    ▼                                      │
┌──────────────┐                     ┌──────────────┐
│commuting_work│──────work hours────►│   working    │
└──────────────┘                     └──────────────┘
                                           │
                                     evening
                                           ▼
                                     ┌──────────────┐
                                     │ socializing  │
                                     │ or relaxing  │
                                     └──────────────┘
```

### Movement Log
```lua
MovementLog = {
    { tick=100, npc_id="G01", from="L001", to="L042", state="working", hour=8, shift="night" }
}
```

---

## 4. Social Interaction System

### Relationship Tracking
When 2+ NPCs are at the same location:
- Creates interaction event
- Updates relationship score (0-1)
- Logs to InteractionLog

### Interaction Types
| Type | Trigger | Relationship Boost |
|------|---------|-------------------|
| casual | Same location | +0.01 |
| social | Both socializing | +0.03 |
| professional | Both working | +0.01 |

### Data Structures
```lua
NPCSocialHistory = {
    ["npc1_npc2"] = {
        met_count = 5,
        last_tick = 100,
        relationship = 0.65
    }
}

InteractionLog = {
    { tick=100, npc1="G01", npc2="A01", location="L001", type="social", relationship=0.65 }
}
```

---

## 5. NPC Economy System

### Wallet Structure
```lua
NPCWallets = {
    ["npc_001"] = {
        balance = 500,      -- Current GEP balance
        income_tick = 100,  -- Last wage tick
        spending_tick = 50  -- Last spending tick
    }
}
```

### Wage Distribution
Wages paid at shift end (once per day):

| Archetype | Daily Wage (GEP) |
|-----------|------------------|
| faction leader | 700 |
| executive | 600 |
| biotech scientist | 550 |
| doctor | 500 |
| manager | 400 |
| pilot/explorer | 350 |
| street medic | 300 |
| noir detective | 250 |
| security guard | 200 |
| hacker | 200 |
| bartender | 180 |
| artist/performer | 150 |
| default | 150 |

### Spending Flow
```
NPC socializing at bar
        │
        ▼ 30% chance
    Spend 20-50 GEP
        │
        ├─► Decrease NPC wallet
        │
        └─► Tax portion → City Budget
```

---

## 6. City Economy System

### Budget Sources
- **Tax Collection**: Daily from population
- **NPC Spending Taxes**: When NPCs spend at social locations

### Budget Drains
- **Services**: Police, medical, infrastructure
- **Policy Costs**: Curfews, rationing, etc.

---

## 7. Message Handlers

### Query Handlers (FREE - dryrun)
| Action | Description | Example |
|--------|-------------|---------|
| get-state | World state | `{}` |
| get-economy | Economy data | `{}` |
| get-npc-locations | All NPC positions | `{}` |
| get-movement-log | Movement history | `{"limit":50}` |
| get-interactions | Social interactions | `{"limit":50}` |
| get-npc-wallets | Wallet balances | `{"limit":20}` |

### Write Handlers
| Action | Description | Example |
|--------|-------------|---------|
| advance-tick | Fast-forward simulation | `{"ticks":100}` |
| load-npc-schedules | Load schedules | `{"schedules":[...]}` |
| store-chat | Save conversation | `{"npc_id":"G01",...}` |

---

## 8. Data Persistence

All state automatically persists to Arweave:
- World tick, day, year
- NPC locations and states
- Social relationships
- Wallet balances
- Transaction logs

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      AO WORLD ENGINE                        │
├─────────────────────────────────────────────────────────────┤
│  CRON (Every 10 min)                                        │
│  ├── Advance tick                                           │
│  ├── Process NPC movements                                  │
│  ├── Process social interactions                            │
│  ├── Process NPC economy                                    │
│  ├── Collect taxes (daily)                                  │
│  └── Persist state snapshot (hourly)                        │
├─────────────────────────────────────────────────────────────┤
│  GLOBALS                                                    │
│  ├── WorldTick, WorldDay, WorldYear                         │
│  ├── NPCSchedules, NPCLocations                             │
│  ├── NPCSocialHistory, InteractionLog                       │
│  ├── NPCWallets, NPCTransactionLog                          │
│  └── CityBudget, Economy                                    │
├─────────────────────────────────────────────────────────────┤
│  QUERY HANDLERS (dryrun - FREE)                             │
│  ├── get-state, get-economy                                 │
│  ├── get-npc-locations, get-movement-log                    │
│  ├── get-interactions, get-npc-wallets                      │
│  └── get-chat-history                                       │
└─────────────────────────────────────────────────────────────┘
```

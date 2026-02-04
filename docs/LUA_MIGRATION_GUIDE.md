# AO/Lua Migration Guide

**Last Updated:** 2026-02-04  
**Status:** Research Complete

---

## 📦 AOS Built-in Modules

AOS (Arweave Operating System) provides these built-in modules for Lua processes:

| Module | Purpose | Example Usage |
|--------|---------|---------------|
| `json` | JSON encode/decode | `json.encode(table)`, `json.decode(str)` |
| `crypto` | Hashing, signatures | `crypto.digest.sha256(data)` |
| `ao` | Core AO functions | `ao.send()`, `ao.spawn()` |
| `Handlers` | Message handlers | Register event handlers |
| `Utils` | Utility functions | Common helpers |

### JSON Module

```lua
local json = require("json")

-- Encode Lua table to JSON string
local npc = { id = "NPC_00001", name = "Frost" }
local jsonStr = json.encode(npc)

-- Decode JSON string to Lua table
local data = json.decode('{"id": "NPC_00001"}')
print(data.id)  -- "NPC_00001"
```

### Crypto Module

```lua
local crypto = require("crypto")

-- Generate deterministic hash
local hash = crypto.digest.sha256("NPC_00001_tick_100")

-- For deterministic random
local function deterministic_choice(items, seed)
    local hash = crypto.digest.sha256(seed)
    local index = tonumber(hash:sub(1, 8), 16) % #items + 1
    return items[index]
end
```

### ao Module (Core)

```lua
-- Send message to another process
ao.send({
    Target = "process-id",
    Action = "UpdateState",
    Data = json.encode(state)
})

-- Spawn new process
ao.spawn("module-id", { Data = json.encode(config) })
```

---

## ⏰ CRON Messages (Scheduled Ticks)

AOS supports CRON messages for automatic execution at intervals:

```lua
-- Register a cron handler (runs every 10 minutes)
Handlers.add("cron-tick", Handlers.utils.hasMatchingTag("Action", "Cron"), function(msg)
    -- Advance simulation tick
    CurrentTick = CurrentTick + 1
    
    -- Process NPC activities
    for _, npc in ipairs(NPCs) do
        update_npc_state(npc, CurrentTick)
    end
    
    -- Generate events
    local events = generate_events(CurrentTick)
    
    -- Persist state
    ao.send({
        Target = ao.id,
        Action = "SaveState",
        Data = json.encode({ tick = CurrentTick, events = events })
    })
end)
```

### Configuring CRON

```lua
-- Set cron interval when spawning process
ao.spawn("simulation-module", {
    Tags = {
        { name = "Cron-Interval", value = "10-minutes" },
        { name = "Cron-Tag-Action", value = "Cron" }
    }
})
```

---

## 📚 Recommended Lua Libraries (via Luarocks)

For local development before AO deployment:

| Library | Purpose | Luarocks Install |
|---------|---------|------------------|
| `luasocket` | HTTP requests | `luarocks install luasocket` |
| `luafilesystem` | File operations | `luarocks install luafilesystem` |
| `lua-cjson` | Fast JSON | `luarocks install lua-cjson` |
| `penlight` | Utility library | `luarocks install penlight` |
| `lua-resty-string` | String utils | `luarocks install lua-resty-string` |

### Installation (macOS)

```bash
# Install Lua 5.3 (AOS uses 5.3)
brew install lua@5.3

# Install Luarocks
brew install luarocks

# Install packages
luarocks install luasocket
luarocks install penlight
```

---

## 🔄 Python → Lua Conversion Patterns

### Deterministic Hash

**Python:**
```python
import hashlib
def deterministic_hash(seed: str) -> int:
    return int(hashlib.sha256(seed.encode()).hexdigest()[:16], 16)
```

**Lua (AOS):**
```lua
local crypto = require("crypto")
function deterministic_hash(seed)
    local hash = crypto.digest.sha256(seed)
    return tonumber(hash:sub(1, 16), 16)
end
```

### Seeded Random Choice

**Python:**
```python
def seeded_choice(items, seed):
    h = hashlib.sha256(seed.encode()).hexdigest()
    idx = int(h[:8], 16) % len(items)
    return items[idx]
```

**Lua (AOS):**
```lua
function seeded_choice(items, seed)
    local hash = crypto.digest.sha256(seed)
    local idx = tonumber(hash:sub(1, 8), 16) % #items + 1
    return items[idx]
end
```

### NPC Needs Update

**Python:**
```python
def update_needs(npc, tick):
    for need, config in NEEDS.items():
        npc["needs"][need] = max(0, npc["needs"][need] - config["decay_rate"])
```

**Lua (AOS):**
```lua
function update_needs(npc, tick)
    for need, config in pairs(NEEDS) do
        npc.needs[need] = math.max(0, npc.needs[need] - config.decay_rate)
    end
end
```

---

## 🏗️ AO Process Architecture

The simulation runs autonomously via CRON messages:

```
ao-processes/
├── world.lua           # Master coordinator, CRON tick advancement ✅
├── district.lua        # Per-district NPC management ✅
├── economy.lua         # Taxes, city budget, wealth tracking ✅
├── social.lua          # Relationships, gossip, reputation ✅
├── ai_oracle.lua       # LLM dialogue generation ✅
└── global_event_bus.lua # Event propagation ✅
```

### Process Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                     AO Network (Arweave)                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌─────────┐  CRON every 10min   ┌──────────────┐          │
│   │ world   │ ───────────────────→│ district_001 │          │
│   │ .lua    │                     └──────────────┘          │
│   │         │ ───────────────────→│ district_002 │          │
│   │ Tick++  │                     └──────────────┘          │
│   │         │ ───────────────────→│ ai_oracle    │          │
│   └─────────┘                     └──────────────┘          │
│       │                                                      │
│       │ Every 240 ticks (game day)                          │
│       ▼                                                      │
│   ┌─────────┐         ┌──────────┐                          │
│   │economy  │ ◄──────►│ social   │                          │
│   │.lua     │         │ .lua     │                          │
│   └─────────┘         └──────────┘                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### world.lua (Master Coordinator)

```lua
local json = require("json")

-- Global state (persisted on Arweave - uppercase = persisted)
WorldTick = WorldTick or 0
WorldDay = WorldDay or 0
Districts = Districts or {}
CityBudget = CityBudget or 1000000

-- CRON handler - this is the simulation heartbeat
Handlers.add("cron-tick", Handlers.utils.hasMatchingTag("Action", "Cron"), function(msg)
    WorldTick = WorldTick + 1
    
    -- Day advancement
    if WorldTick % 240 == 0 then
        WorldDay = WorldDay + 1
    end
    
    -- Broadcast to all districts
    for district_id, process_id in pairs(Districts) do
        ao.send({
            Target = process_id,
            Action = "Cron",
            Data = json.encode({ tick = WorldTick })
        })
    end
end)
```

---

## 🔗 External API Calls (Keep in Python)

These should remain as Python backend services, called via HTTP from the frontend:

| Service | Reason | Deployment |
|---------|--------|------------|
| NPC Chat | Requires Vertex AI | Cloud Run |
| Scene Generator | Requires Imagen 4 | Cloud Run |
| Image Analysis | Requires Gemini | Cloud Run |

```python
# api/npc_chat.py (Keep as Python/Cloud Run)
@app.route("/api/chat", methods=["POST"])
async def chat():
    # This calls Vertex AI - cannot run on AO
    response = await model.generate_content(prompt)
    return jsonify({"response": response.text})
```

---

## 📋 Migration Checklist

### Phase 1: Core Lua Modules ✅
- [x] `world.lua` - Master coordinator with CRON tick
- [x] `district.lua` - NPC location calculation, schedules
- [x] `economy.lua` - Tax collection, city budget, expenses
- [x] `social.lua` - Relationship tracking, gossip
- [x] `ai_oracle.lua` - Dialogue generation queue
- [x] `global_event_bus.lua` - Event propagation

### Phase 2: Codec Integration
- [x] `world_codec_20_economy.json` - Income, taxes, wealth levels
- [x] `world_codec_19_social.json` - Trust mechanics, relationships
- [ ] Load codec chunks from Arweave at init

### Phase 3: Deploy to AO Testnet
- [ ] Upload Lua modules to Arweave
- [ ] Spawn world process with `Cron-Interval: "10-minutes"`
- [ ] Initialize districts with NPC data
- [ ] Register economy and social processes with world
- [ ] Monitor cron message flow
- [ ] Verify tick advancement every 10 minutes

### Phase 4: Testing
- [ ] Local Lua testing with mock crypto
- [ ] AO testnet deployment
- [ ] Verify deterministic state reconstruction
- [ ] Load test with 10,000+ NPCs

---

## 🌐 Useful Resources

- [AO Documentation](https://cookbook_ao.g8way.io/)
- [AOS Modules Reference](https://cookbook_ao.g8way.io/references/ao.html)
- [Lua 5.3 Reference Manual](https://www.lua.org/manual/5.3/)
- [Arweave Developer Portal](https://arweave.org/developers)
- [AR.IO AO Examples](https://github.com/ar-io/ao-pilot)

---

*"Write once in Python, test thoroughly, then port to Lua for permanence."*

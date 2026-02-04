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

```
ao-processes/
├── world.lua           # Main world state, NPC registry
├── simulation.lua      # Tick processing, schedule resolution
├── events.lua          # Event generation, cascading
├── memory.lua          # NPC memory persistence
└── handlers.lua        # Message handlers for external calls
```

### world.lua (Main Entry Point)

```lua
local json = require("json")

-- Global state (persisted)
NPCs = NPCs or {}
CurrentTick = CurrentTick or 0
Buildings = Buildings or {}

-- Initialize from Arweave data
Handlers.add("init", Handlers.utils.hasMatchingTag("Action", "Init"), function(msg)
    local data = json.decode(msg.Data)
    NPCs = data.npcs or {}
    Buildings = data.buildings or {}
    ao.send({ Target = msg.From, Data = "Initialized with " .. #NPCs .. " NPCs" })
end)

-- Get NPC state
Handlers.add("get-npc", Handlers.utils.hasMatchingTag("Action", "GetNPC"), function(msg)
    local npc_id = msg.Tags.NpcId
    local npc = NPCs[npc_id]
    if npc then
        ao.send({ Target = msg.From, Data = json.encode(npc) })
    else
        ao.send({ Target = msg.From, Data = json.encode({ error = "NPC not found" }) })
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

### Phase 1: Core Logic (Priority)
- [ ] `api_simulation.py` → `simulation.lua`
  - [ ] `get_npc_state()` function
  - [ ] `calculate_needs()` function
  - [ ] Schedule template lookup
  
- [ ] `event_engine.py` → `events.lua`
  - [ ] `generate_event_at_tick()` function
  - [ ] `does_event_occur()` function
  - [ ] Event encoding/decoding

### Phase 2: AI Systems
- [ ] `simulation_behaviors.py` → `behaviors.lua`
  - [ ] Needs system with decay
  - [ ] NPC interactions
  - [ ] Random events

- [ ] `advanced_ai_systems.py` → `ai.lua`
  - [ ] Utility AI decision making
  - [ ] GOAP planning (simplified)

### Phase 3: Data Integration
- [ ] Load NPC data from Arweave
- [ ] Load codec chunks from Arweave
- [ ] Set up CRON for tick advancement
- [ ] Deploy to AO mainnet

---

## 🌐 Useful Resources

- [AO Documentation](https://cookbook_ao.g8way.io/)
- [AOS Modules Reference](https://cookbook_ao.g8way.io/references/ao.html)
- [Lua 5.3 Reference Manual](https://www.lua.org/manual/5.3/)
- [Arweave Developer Portal](https://arweave.org/developers)
- [AR.IO AO Examples](https://github.com/ar-io/ao-pilot)

---

*"Write once in Python, test thoroughly, then port to Lua for permanence."*

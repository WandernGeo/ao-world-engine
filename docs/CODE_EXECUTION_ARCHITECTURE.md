# Code Execution Architecture

> Where does Python run? Who needs Python? How do JSONs trigger code?

---

## The Key Question

```
YOU ASKED: "Why is there a scripts/faction_ai.py? 
            Should code be embedded in JSONs on Arweave?"

ANSWER: You're RIGHT. The current setup is HYBRID:
        - scripts/*.py = Development/testing (runs on YOUR machine)
        - Embedded code = Production (runs on AO Network)
```

---

## Two Modes of Operation

### Mode 1: LOCAL DEVELOPMENT (Current)

```
┌──────────────────────────────────────────────────────────────┐
│  YOUR COMPUTER or CLOUD RUN                                  │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  User runs: python demo/server.py                            │
│                    │                                          │
│                    ▼                                          │
│  Server loads:                                                │
│  ├── data/world_codec.json     (NPC definitions)             │
│  ├── scripts/faction_ai.py     (Python simulation)           │
│  ├── scripts/npc_life_sim.py   (Python simulation)           │
│  └── scripts/simulation_behaviors.py                         │
│                    │                                          │
│                    ▼                                          │
│  Python executes simulation locally                           │
│  Results displayed in browser                                 │
│                                                               │
│  ✅ User needs: Python 3.9+                                   │
│  ✅ Code runs: On user's machine                             │
│  ❌ Decentralized: No                                        │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### Mode 2: DECENTRALIZED (Target)

```
┌──────────────────────────────────────────────────────────────┐
│  ARWEAVE + AO NETWORK                                        │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ARWEAVE stores:                                             │
│  ar://WORLD_CODEC                                            │
│  {                                                           │
│    "npcs": [...],                                            │
│    "behaviors": {                                            │
│      "faction_ai": {                                         │
│        "code_b64": "ZGVmIHByb2Nlc3NfZmFjdGlvbi..."          │ ← Python embedded
│      },                                                      │
│      "npc_life_sim": {                                       │
│        "code_b64": "ZGVmIGRlY2F5X25lZWRzKG5wYy..."          │ ← Python embedded
│      }                                                       │
│    }                                                         │
│  }                                                           │
│                                                               │
│  AO NETWORK:                                                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  AO Process (Lua)                                       │ │
│  │  1. Fetch world_codec from Arweave                      │ │
│  │  2. Decode behavior.code_b64                            │ │
│  │  3. Execute Python in sandbox                           │ │
│  │  4. Return results to client                            │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  ✅ User needs: Just a browser                               │
│  ✅ Code runs: On AO Network (decentralized)                 │
│  ✅ Decentralized: Yes                                       │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## How NPCs Trigger Python

### Current (Local Mode)

```python
# In demo/server.py
@app.route("/simulate")
def simulate():
    tick = get_current_tick()
    
    # Python files are imported and called directly
    from scripts.simulation_behaviors import simulate_tick
    from scripts.faction_ai import process_all_factions
    from scripts.npc_life_sim import process_npc_tick
    
    result = simulate_tick(world_state, tick)
    return jsonify(result)
```

### Target (Decentralized Mode)

```lua
-- In AO Process
Handlers.add("SimulateTick",
  function(msg) return msg.Action == "Simulate" end,
  function(msg)
    local tick = tonumber(msg.Tags["Tick"])
    
    -- Fetch behavior code from Arweave
    local codec = FetchFromArweave("ar://WORLD_CODEC")
    local behavior_code = base64.decode(codec.behaviors.faction_ai.code_b64)
    
    -- Execute in sandbox
    local result = ExecutePython(behavior_code, {tick = tick, world = codec})
    
    ao.send({Target = msg.From, Data = json.encode(result)})
  end
)
```

---

## NPC JSON with Embedded Triggers

Here's how an NPC JSON can specify what code to run:

```json
{
  "id": "charlie",
  "name": "Charlie",
  "faction": "resistance",
  "job": "rebel_fighter",
  
  "triggers": [
    {
      "event": "low_hunger",
      "condition": "needs.hunger < 20",
      "behavior": "find_food",
      "behavior_code_ref": "ar://BEH_find_food"
    },
    {
      "event": "encounter_enemy",
      "condition": "nearby_npc.faction == 'temple'",
      "behavior": "evaluate_fight_or_flee",
      "behavior_code_ref": "ar://BEH_combat"
    },
    {
      "event": "payday",
      "condition": "tick % 24 == 0",
      "behavior": "receive_wage",
      "behavior_code_ref": "ar://BEH_economy"
    }
  ],
  
  "behaviors": {
    "find_food": {
      "local_fallback": "scripts/npc_life_sim.py:buy_food",
      "arweave_ref": "ar://BEH_find_food"
    }
  }
}
```

---

## The Conversion Process

To move from LOCAL to DECENTRALIZED:

```
STEP 1: Convert .py files to embedded code

  scripts/faction_ai.py
         ↓ (base64 encode)
  world_codec.json:
    "behaviors": {
      "faction_ai": {
        "code_b64": "ZGVmIHByb2Nlc3NfZmFjdGlvbi4uLg=="
      }
    }

STEP 2: Upload to Arweave

  python scripts/upload_behaviors.py
  → Uploads world_codec.json with embedded code
  → Returns: ar://ABC123...

STEP 3: AO Process references the code

  local codec = FetchFromArweave("ar://ABC123...")
  local code = base64.decode(codec.behaviors.faction_ai.code_b64)
  ExecutePython(code, context)
```

---

## Do Users Need Python?

| Mode | User Needs | Where Code Runs |
|------|------------|-----------------|
| **Local Development** | Python 3.9+ | User's machine |
| **Cloud Run Hosted** | Just browser | Google Cloud |
| **Decentralized (AO)** | Just browser | AO Network |

For the decentralized version, **NO** - users just need a browser!

---

## File Organization

```
ao-world-engine/
├── scripts/                    # LOCAL DEVELOPMENT
│   ├── faction_ai.py          # Python source (for testing)
│   ├── npc_life_sim.py        # Python source (for testing)
│   └── simulation_behaviors.py
│
├── data/
│   ├── world_codec.json       # Data + behavior references
│   └── behaviors/             # EMBEDDED CODE (for Arweave)
│       ├── faction_ai.json    # Contains code_b64
│       ├── npc_life.json      # Contains code_b64
│       └── economy.json       # Contains code_b64
│
└── ao/
    └── process.lua            # AO handler that executes code
```

---

## Next Step: Create Embedded Behaviors

I'll now create the `data/behaviors/` folder with the Python code embedded in JSON format, ready for Arweave upload.

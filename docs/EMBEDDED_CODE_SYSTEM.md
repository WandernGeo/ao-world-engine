# Embedded Code System

> **Python code stored on Arweave, executed on AO Network - NOT on user's computer**

## Overview

The AO World Engine uses **embedded Python code** stored as base64 in JSON on Arweave. This code runs on the **AO decentralized compute network**, not on the user's device.

```
┌─────────────────────────────────────────────────────────────────┐
│                     EXECUTION ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ARWEAVE (Permanent Storage)                                   │
│   ┌──────────────────────────────────────┐                      │
│   │  JSON Chunk with embedded Python     │                      │
│   │  {                                   │                      │
│   │    "id": "BEH_guard_chase",         │                      │
│   │    "code_b64": "ZGVmIGNoZWNr..."    │  ← Base64 Python     │
│   │  }                                   │                      │
│   └──────────────────────────────────────┘                      │
│                        │                                         │
│                        ▼                                         │
│   AO NETWORK (Decentralized Compute)                            │
│   ┌──────────────────────────────────────┐                      │
│   │  AO Process (Lua/WASM Sandbox)       │                      │
│   │  - Fetches JSON from Arweave         │                      │
│   │  - Decodes base64 → Python           │                      │
│   │  - Executes in sandbox               │                      │
│   │  - Returns state changes             │                      │
│   └──────────────────────────────────────┘                      │
│                        │                                         │
│                        ▼                                         │
│   CLIENT (User's Device)                                        │
│   ┌──────────────────────────────────────┐                      │
│   │  Receives RESULTS only               │                      │
│   │  - NPC location updates              │                      │
│   │  - Event notifications               │                      │
│   │  - State changes                     │                      │
│   │  NO CODE EXECUTION HERE              │                      │
│   └──────────────────────────────────────┘                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Why AO Network?

| Feature | Traditional Server | AO Network |
|---------|-------------------|------------|
| **Trust** | Trust the operator | Trustless, verifiable |
| **Cost** | Ongoing server fees | Pay-per-compute |
| **Permanence** | Server can shut down | Code lives forever on Arweave |
| **Determinism** | Hard to verify | Every execution is reproducible |
| **Censorship** | Can be blocked | Permissionless |

## Code Storage Format

### JSON Structure on Arweave
```json
{
    "id": "BEH_guard_chase_001",
    "name": "Guard Chase Behavior",
    "version": "1.0.0",
    "trigger_type": "reactive",
    "event": "crime_witnessed",
    "priority": 8,
    "code_b64": "ZGVmIGV4ZWN1dGUobnBjLCB3b3JsZCwgZXZlbnQpOgogICAgIyBHdWFyZCBzZWVzIGNyaW1lCiAgICBpZiBucGMuZmFjdGlvbiA9PSAndGVtcGxlX2d1YXJkJzoKICAgICAgICByZXR1cm4gewogICAgICAgICAgICAnYWN0aXZpdHknOiAnY2hhc2luZycsCiAgICAgICAgICAgICd0YXJnZXQnOiBldmVudC5jcmltaW5hbF9pZAogICAgICAgIH0=",
    "dependencies": [],
    "author": "wallet_address",
    "hash": "sha256_for_verification"
}
```

### Decoded Python
```python
def execute(npc, world, event):
    # Guard sees crime
    if npc.faction == 'temple_guard':
        return {
            'activity': 'chasing',
            'target': event.criminal_id
        }
```

## Trigger Types

### 1. Condition Triggers
Run every tick, check if condition is true, then execute action.

```python
# condition_code
def check(npc, world, tick):
    """Returns True if NPC should go to bar."""
    if npc.stress > 0.7 and world.time_period in ['T08', 'T09']:
        return True
    return False

# action_code  
def execute(npc, world, tick):
    """Move NPC to bar and reduce stress."""
    return {
        'npc_changes': {
            'location': 'L011_neon_bar',
            'activity': 'drinking',
            'stress': npc.stress - 0.1
        }
    }
```

### 2. Scheduled Triggers
Run at specific times/ticks.

```python
# Runs every day at T04 (noon)
def execute(npc, world, tick):
    """NPC eats lunch."""
    if npc.hunger > 0.3:
        return {
            'npc_changes': {
                'activity': 'eating',
                'hunger': 0.0,
                'location': npc.favorite_restaurant or 'L015_food_stall'
            }
        }
```

### 3. Reactive Triggers
Run when specific events occur.

```python
# Triggered by: player_killed_npc
def execute(npc, world, event):
    """Family member reacts to death."""
    dead_npc = event.victim
    
    if dead_npc.id in npc.family:
        # Family member grieves
        return {
            'npc_changes': {
                'mood': 'grieving',
                'trust_player': -1.0,
                'schedule_override': 'mourning'
            },
            'events': [{
                'type': 'family_grief',
                'npc_id': npc.id,
                'victim_id': dead_npc.id
            }]
        }
```

## Sandbox Restrictions

The AO execution environment is **sandboxed** for security:

### ✅ Allowed
- `math` - Mathematical operations
- `random` (seeded) - Deterministic randomness
- `hashlib` - Hashing for determinism
- `json` - Data parsing
- World Codec access (read-only)
- NPC state access (read-only)

### ❌ Forbidden
- `os`, `sys` - No system access
- `subprocess` - No external processes
- `socket`, `requests` - No network
- File I/O - No filesystem
- `eval`, `exec` - No dynamic code execution
- Real time - Only tick-based time

### Limits
- **Timeout**: 100ms per execution
- **Memory**: 10MB max
- **Recursion**: 100 levels max

## Determinism Guarantee

**Same inputs ALWAYS produce same outputs.**

```python
import hashlib

def get_deterministic_random(npc_id, tick, purpose):
    """Generate deterministic 'random' value."""
    seed = hashlib.sha256(f"{npc_id}_{tick}_{purpose}".encode()).hexdigest()
    return int(seed, 16) % 100  # 0-99

# Example: Will Felix go to market today?
chance = get_deterministic_random("felix", 1500, "market_visit")
goes_to_market = chance < 30  # 30% chance, but deterministic
```

## AO Process Integration

### Lua Handler (AO Process)
```lua
-- AO Process that executes Python behaviors
Handlers.add("ExecuteBehavior", 
  Handlers.utils.hasMatchingTag("Action", "ExecuteBehavior"),
  function(msg)
    local behavior_id = msg.Tags["Behavior-Id"]
    local tick = tonumber(msg.Tags["Tick"])
    local npc_id = msg.Tags["NPC-Id"]
    
    -- Fetch behavior code from Arweave
    local behavior = FetchFromArweave(behavior_id)
    
    -- Execute in Python sandbox
    local result = ExecutePython(behavior.code_b64, {
      npc = GetNPCState(npc_id, tick),
      world = GetWorldState(tick),
      tick = tick
    })
    
    -- Return results
    ao.send({
      Target = msg.From,
      Action = "BehaviorResult",
      Data = json.encode(result)
    })
  end
)
```

## Cost Estimation

| Operation | AO Cost | Notes |
|-----------|---------|-------|
| Store behavior (Arweave) | ~$0.0001/KB | One-time, permanent |
| Execute behavior (AO) | ~$0.00001 | Per execution |
| 1000 NPCs × 1000 ticks | ~$10 | Full day simulation |

## Verification

Anyone can verify execution:
1. Fetch behavior code from Arweave (immutable)
2. Fetch world state at tick (deterministic)
3. Re-run execution locally
4. Compare results (must match)

This is like blockchain smart contracts but for game logic!

---

*See also: [WORLD_CODEC.md](./WORLD_CODEC.md) | [SIMULATION_DESIGN.md](./SIMULATION_DESIGN.md)*

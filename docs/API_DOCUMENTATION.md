# NPC Simulation API Documentation

> RESTful API for the AO World Engine simulation system

## Base URL

```
Local:    http://localhost:8081
Production: https://your-api.reecho.city
```

## Quick Start

```bash
# Start the API
cd ao-world-engine
python3 api/api_simulation.py

# Test it
curl http://localhost:8081/api/stats
```

---

## Endpoints

### 📊 Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API documentation |
| `/api/stats` | GET | Simulation statistics |
| `/api/npcs` | GET | List NPCs |
| `/api/npcs/<id>` | GET | Get single NPC |
| `/api/npcs/<id>/state` | GET | NPC state at tick |
| `/api/npcs/at/<location>` | GET | NPCs at location |
| `/api/buildings` | GET | List buildings |
| `/api/buildings/<id>` | GET | Building details |
| `/api/simulation/tick` | GET | Simulation state |
| `/api/simulation/time` | GET | Time info |
| `/api/transport` | GET | Transportation system |
| `/api/arweave/<tx_id>` | GET | Fetch from Arweave |

---

### `/api/npcs`

List all NPCs with optional filtering.

**Query Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `limit` | int | Max results (default: 50, max: 500) |
| `offset` | int | Pagination offset |
| `faction` | string | Filter by faction (civilian, resistance, temple) |
| `archetype` | string | Filter by archetype (resident, worker, guard, etc.) |
| `schedule` | string | Filter by schedule type |
| `block` | int | Filter by city block (1-6) |

**Example:**

```bash
# Get resistance fighters
curl "http://localhost:8081/api/npcs?faction=resistance&limit=10"
```

**Response:**

```json
{
  "npcs": [
    {
      "id": "NPC_00031",
      "name": "Zero Chen",
      "archetype": "resistance",
      "faction": "resistance",
      "schedule": "resistance_fighter",
      "home": "B001",
      "workplace": "B019",
      "block": 6,
      "personality": {
        "aggression": 0.45,
        "sociability": 0.72,
        "greed": 0.18,
        "loyalty": 0.95,
        "curiosity": 0.67
      },
      "skills": {
        "combat": 0.65,
        "stealth": 0.78,
        "tech": 0.42,
        "social": 0.55,
        "survival": 0.48
      }
    }
  ],
  "total": 31,
  "limit": 10,
  "offset": 0
}
```

---

### `/api/npcs/<id>`

Get single NPC by ID.

**Example:**

```bash
curl "http://localhost:8081/api/npcs/NPC_00001"
```

---

### `/api/npcs/<id>/state`

Get NPC state at a specific tick. The state is deterministic - same tick always produces same result.

**Query Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `tick` | int | Simulation tick (default: 100) |

**Example:**

```bash
curl "http://localhost:8081/api/npcs/NPC_00001/state?tick=150"
```

**Response:**

```json
{
  "npc_id": "NPC_00001",
  "name": "Chen Volkov",
  "tick": 150,
  "time_period": "T04",
  "activity": "working",
  "location": "B003",
  "location_type": "workplace",
  "mood": "focused",
  "faction": "civilian",
  "archetype": "worker",
  "npc": { ... }
}
```

---

### `/api/npcs/at/<location>`

Get all NPCs at a specific location at a given tick.

**Query Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `tick` | int | Simulation tick (default: 100) |

**Example:**

```bash
curl "http://localhost:8081/api/npcs/at/B003?tick=150"
```

**Response:**

```json
{
  "location": "B003",
  "tick": 150,
  "time": {
    "tick": 150,
    "day": 1,
    "hour": 15,
    "minute": 0,
    "period": "T04"
  },
  "count": 42,
  "npcs": [ ... ]
}
```

---

### `/api/buildings`

List all buildings in the district.

**Example:**

```bash
curl "http://localhost:8081/api/buildings"
```

---

### `/api/buildings/<id>`

Get building details with residents and workers.

**Example:**

```bash
curl "http://localhost:8081/api/buildings/B004"
```

**Response:**

```json
{
  "id": "B004",
  "name": "The Rusty Anchor Bar",
  "type": "entertainment",
  "block": 2,
  "floors": 2,
  "capacity": 80,
  "residents": [],
  "residents_total": 0,
  "workers": ["NPC_00123", "NPC_00456"],
  "workers_total": 12
}
```

---

### `/api/simulation/tick`

Run full simulation for a specific tick. Returns all NPC states, location counts, and events.

**Query Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `tick` | int | Simulation tick (default: 100) |

**Example:**

```bash
curl "http://localhost:8081/api/simulation/tick?tick=100"
```

**Response:**

```json
{
  "tick": 100,
  "time": {
    "tick": 100,
    "day": 1,
    "hour": 10,
    "minute": 0,
    "period": "T03"
  },
  "npc_count": 800,
  "location_summary": {
    "B001": 145,
    "B002": 89,
    "B003": 42,
    ...
  },
  "activity_summary": {
    "sleeping": 312,
    "waking": 156,
    "commuting": 89,
    ...
  },
  "events": [
    {"type": "temple_patrol", "tick": 100, "id": "EVT_100_tem"}
  ],
  "npc_states": [ ... ],
  "npc_states_truncated": true
}
```

---

### `/api/simulation/time`

Get time information for a tick.

**Example:**

```bash
curl "http://localhost:8081/api/simulation/time?tick=500"
```

**Response:**

```json
{
  "tick": 500,
  "day": 3,
  "hour": 2,
  "minute": 0,
  "period": "T01",
  "day_tick": 20
}
```

---

### `/api/transport`

Get full transportation system data.

**Example:**

```bash
curl "http://localhost:8081/api/transport"
```

---

### `/api/stats`

Get simulation statistics.

**Response:**

```json
{
  "total_npcs": 800,
  "total_buildings": 19,
  "archetypes": {
    "resident": 328,
    "worker": 177,
    "vendor": 83,
    ...
  },
  "factions": {
    "civilian": 738,
    "resistance": 31,
    "temple": 31
  },
  "schedules": { ... },
  "building_types": { ... },
  "data_source": "local"
}
```

---

## Time System

| Period | Hours | Description |
|--------|-------|-------------|
| T01 | 00:00-02:24 | Deep night |
| T02 | 02:24-07:12 | Early morning |
| T03 | 07:12-12:00 | Morning |
| T04 | 12:00-16:48 | Afternoon (peak) |
| T05 | 16:48-19:12 | Late afternoon |
| T06 | 19:12-20:24 | Dusk |
| T07 | 20:24-21:36 | Evening |
| T08 | 21:36-22:48 | Night |
| T09 | 22:48-23:36 | Late night |
| T10 | 23:36-00:00 | Dead hour |

**Conversion:**
- 1 tick = 6 minutes real time
- 10 ticks = 1 hour
- 240 ticks = 1 day

---

## Integration Examples

### JavaScript/TypeScript

```typescript
const API_BASE = 'http://localhost:8081';

// Get NPC state
async function getNPCState(npcId: string, tick: number) {
  const res = await fetch(`${API_BASE}/api/npcs/${npcId}/state?tick=${tick}`);
  return res.json();
}

// Get all NPCs at location
async function getNPCsAt(location: string, tick: number) {
  const res = await fetch(`${API_BASE}/api/npcs/at/${location}?tick=${tick}`);
  return res.json();
}

// Example: Find Charlie
const state = await getNPCState('NPC_00031', 150);
console.log(`${state.name} is ${state.activity} at ${state.location}`);
```

### Python

```python
import requests

API_BASE = 'http://localhost:8081'

def get_npc_state(npc_id: str, tick: int) -> dict:
    response = requests.get(f'{API_BASE}/api/npcs/{npc_id}/state', 
                           params={'tick': tick})
    return response.json()

# Get simulation state
sim = requests.get(f'{API_BASE}/api/simulation/tick', 
                   params={'tick': 100}).json()
print(f"Day {sim['time']['day']}, {sim['time']['hour']}:00")
print(f"NPCs active: {sim['npc_count']}")
```

### Unity/C#

```csharp
using UnityEngine;
using UnityEngine.Networking;

IEnumerator GetNPCState(string npcId, int tick) {
    string url = $"http://localhost:8081/api/npcs/{npcId}/state?tick={tick}";
    using (UnityWebRequest request = UnityWebRequest.Get(url)) {
        yield return request.SendWebRequest();
        if (request.result == UnityWebRequest.Result.Success) {
            NPCState state = JsonUtility.FromJson<NPCState>(request.downloadHandler.text);
            Debug.Log($"{state.name} is {state.activity}");
        }
    }
}
```

---

## Error Handling

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 404 | NPC/Building not found |
| 500 | Server error |

**Error Response:**

```json
{
  "error": "NPC NPC_99999 not found"
}
```

---

## Rate Limits

| Tier | Requests/min |
|------|--------------|
| Free | 60 |
| Basic | 300 |
| Pro | 1000 |
| Enterprise | Unlimited |

---

## Arweave Integration

For production, data can be fetched from Arweave:

```bash
curl "http://localhost:8081/api/arweave/<transaction_id>"
```

This fetches permanent NPC data from the Arweave network.

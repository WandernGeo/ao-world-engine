# 🚀 Getting Started with AO World Engine

> Complete guide to running locally, using the hosted API, and understanding the system

---

## Quick Links

| Option | Best For |
|--------|----------|
| [**Hosted API**](#hosted-api---try-it-now) | Try instantly, no setup |
| [**Local Install**](#local-installation) | Full development, custom worlds |
| [**Docker**](#docker-deployment) | Production-like environment |

---

## Hosted API - Try It Now

We host a live demo you can use immediately:

### Live Demo URLs

| Service | URL | Description |
|---------|-----|-------------|
| **Landing Page** | https://ao-world-engine-1071951656531.us-central1.run.app | Main entry point |
| **Visualizer** | https://ao-world-engine-1071951656531.us-central1.run.app/explore | See 800 NPCs on map |
| **NPC Chat** | https://ao-world-engine-1071951656531.us-central1.run.app/chat | Talk to NPCs |
| **API Docs** | https://ao-world-engine-1071951656531.us-central1.run.app/api-docs | Test API endpoints |

### API Endpoints

```bash
# Get simulation state at tick 100
curl "https://ao-world-engine-1071951656531.us-central1.run.app/api/simulation/tick?tick=100"

# List all buildings
curl "https://ao-world-engine-1071951656531.us-central1.run.app/api/buildings"

# Get NPCs at a specific building
curl "https://ao-world-engine-1071951656531.us-central1.run.app/api/npcs/at/B001"

# Chat with an NPC (requires POST)
curl -X POST "https://ao-npc-chat-1071951656531.us-central1.run.app/api/npc/chat" \
  -H "Content-Type: application/json" \
  -d '{"npc_id": "charlie", "tick": 100, "message": "hello", "user_id": "my_unique_id"}'
```

---

## Local Installation

### Prerequisites

- Python 3.10+
- pip
- Git

### Step 1: Clone the Repository

```bash
git clone https://github.com/WandernGeo/ao-world-engine.git
cd ao-world-engine
```

### Step 2: Install Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r demo/requirements.txt
```

### Step 3: Run the Server

```bash
# Start the local server
python demo/server.py
```

The server will start at `http://localhost:8081`

### Step 4: Access the Demo

Open your browser to:
- **Visualizer**: http://localhost:8081/explore
- **NPC Chat**: http://localhost:8081/chat
- **API Docs**: http://localhost:8081/api-docs

---

## Running the NPC Chat API Separately

The NPC Chat requires a Vertex AI / LLM connection for AI responses.

### Option A: With Google Cloud (Recommended)

```bash
# Install Google Cloud SDK
# https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth application-default login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Run the chat API
cd api
pip install -r requirements.txt
python npc_chat.py
```

### Option B: Without Cloud (Mock Mode)

If you don't have a cloud account, the API runs in "mock mode" with static responses:

```bash
cd api
python npc_chat.py
# Will show: "⚠️ Vertex AI not available - running in mock mode"
```

---

## Understanding the Components

### Directory Structure

```
ao-world-engine/
├── api/                    # NPC Chat API (AI-powered)
│   ├── npc_chat.py         # Main chat server
│   ├── npc_memory.py       # Persistent memory system
│   ├── founding_npcs.py    # 12 founding NPC profiles
│   └── requirements.txt
│
├── demo/                   # Visualizer & Combined Server
│   ├── server.py           # Flask server (visualizer + API)
│   ├── static/             # HTML/CSS/JS frontend
│   │   ├── visualizer.html # Map view
│   │   ├── chat.html       # NPC chat interface
│   │   └── api_docs.html   # API documentation
│   └── data/               # Simulation data
│
├── data/                   # World data
│   ├── memories/           # NPC conversation memories (created at runtime)
│   ├── npcs_generated.json # 800 generated NPCs
│   ├── founding_npcs.py    # 12 core NPCs
│   └── world_codec.json    # World configuration
│
├── ao-processes/           # AO/Arweave Lua processes
│   ├── district.lua
│   └── global_event_bus.lua
│
├── docs/                   # Documentation
└── schemas/                # JSON schemas
```

### Key Concepts

| Concept | What It Means |
|---------|---------------|
| **Tick** | Unit of simulation time. Tick 100 = Day 5, 4:00 AM |
| **NPC State** | Location, activity, mood - all calculated from tick |
| **Building** | Location where NPCs work, live, or visit |
| **Faction** | Group affiliation (Resistance, Temple, Criminal, etc.) |
| **Memory** | Persistent facts NPCs learn about users |

### The Tick System

Everything is **deterministic** based on tick:

```
Tick = 100
├── Day = 100 ÷ 24 = 4 (Day 5, 0-indexed)
├── Hour = 100 % 24 = 4 (4:00 AM)
├── Time Period = T03 (morning)
├── Weather = hash("weather_16") → "rain"
└── NPC Locations = schedule[T03] for each NPC
```

Same tick always produces same world state.

---

## Memory System

NPCs remember conversations across sessions using JSON files.

### How It Works

1. **User sends message** → API receives with `user_id`
2. **NPC extracts facts** → "my name is Mike" → remembers `name: Mike`
3. **Saved to disk** → `data/memories/{user_hash}/facts.json`
4. **Loaded next time** → NPC greets "Hey Mike!"

### Memory File Structure

```
data/memories/
├── a1b2c3d4e5f6g7h8/           # User ID hash
│   ├── facts.json              # Learned facts about user
│   ├── charlie.json            # Conversation with Charlie
│   └── felix.json              # Conversation with Felix
└── arweave_queue/              # Ready for Arweave upload
```

### Example facts.json

```json
{
  "name": "Mike",
  "first_seen_tick": 100,
  "last_seen_tick": 250,
  "custom_facts": {
    "location": {
      "value": "Tokyo",
      "learned_tick": 150
    },
    "favorite_drink": {
      "value": "whiskey",
      "learned_tick": 200
    }
  }
}
```

### Creating Memory Directory

The memory directory is created automatically when running. To ensure it exists:

```bash
# Create memory directory
mkdir -p data/memories

# Verify structure
ls -la data/memories/
```

---

## API Reference

### Simulation Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/simulation/tick?tick=N` | GET | Get world state at tick N |
| `/api/buildings` | GET | List all buildings |
| `/api/npcs` | GET | List all NPCs |
| `/api/npcs/at/<location>` | GET | NPCs at specific building |
| `/api/stats` | GET | System statistics |

### Chat Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/npc/chat` | POST | Chat with an NPC |
| `/api/npc/state/<npc_id>/<tick>` | GET | Get NPC state at tick |
| `/api/npcs` | GET | List available NPCs |

### Example: Chat Request

```bash
curl -X POST "http://localhost:8080/api/npc/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "npc_id": "charlie",
    "tick": 100,
    "message": "What are you doing today?",
    "user_id": "user_abc123"
  }'
```

### Example: Chat Response

```json
{
  "npc": "Charlie",
  "response": "Another day in the shadows. I'm heading to the resistance hideout for the morning briefing. Rain washes nothing clean here.",
  "memories_enabled": true,
  "user_remembered": true,
  "user_name": "Mike",
  "state": {
    "tick": 100,
    "location": "resistance_hideout",
    "activity": "meeting",
    "time_period": "T03",
    "mood": "focused",
    "weather": "rain"
  }
}
```

---

## Docker Deployment

### Build the Docker Image

```bash
# From project root
docker build -t ao-world-engine .
```

### Run with Docker

```bash
docker run -p 8080:8080 \
  -v $(pwd)/data/memories:/app/data/memories \
  ao-world-engine
```

> **Note**: Mount the memories volume to persist NPC memories across restarts.

### Deploy to Cloud Run

```bash
gcloud run deploy ao-world-engine \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi
```

---

## Troubleshooting

### Issue: "Vertex AI not available"

This is normal if you don't have Google Cloud configured. The API runs in mock mode with static responses.

**To enable AI responses:**
1. Create a Google Cloud project
2. Enable Vertex AI API
3. Run `gcloud auth application-default login`

### Issue: No NPCs showing in visualizer

Check the API is returning `location_summary`:

```bash
curl "http://localhost:8081/api/simulation/tick?tick=100" | jq '.location_summary'
```

Should return something like:
```json
{
  "B001": 137,
  "B002": 170,
  "B003": 88
}
```

### Issue: Memory not persisting

Ensure the memory directory exists and is writable:

```bash
mkdir -p data/memories
chmod 755 data/memories
```

---

## Next Steps

| Task | Documentation |
|------|---------------|
| Create your own world | [BUILDING_YOUR_WORLD.md](./BUILDING_YOUR_WORLD.md) |
| Understand the simulation | [SIMULATION_SYSTEM.md](./SIMULATION_SYSTEM.md) |
| Deploy to Arweave | [ARWEAVE_INTEGRATION.md](./ARWEAVE_INTEGRATION.md) |
| Add custom NPCs | [AI_NPC_SYSTEM.md](./AI_NPC_SYSTEM.md) |

---

*"The engine runs forever. What you build on it is yours."*

# 🚀 Running RE:ECHO City Locally

> Run the full simulation, visualizer, and chat locally without any cloud dependencies.

## Quick Start

```bash
# Clone the repo
git clone https://github.com/WandernGeo/ao-world-engine.git
cd ao-world-engine

# Install Python dependencies
pip install -r requirements.txt

# Start the simulation API (Terminal 1)
python -m api.api_simulation
# API now running at http://localhost:8081
```

**Then open the visualizer** (one of these options):

```bash
# Option 1: Open the visualizer HTML directly
open visualizer/index.html

# Option 2: Run the full frontend (landing + visualizer + chat)
# In a NEW terminal:
cd demo
python server.py
# Open http://localhost:8082
```

---

## Architecture

```
┌─────────────────┐     API calls      ┌─────────────────┐
│   Visualizer    │ ─────────────────► │  Simulation API │
│  (HTML/JS)      │                    │  localhost:8081 │
│  localhost:8082 │ ◄───────────────── │                 │
│  or file://     │     JSON data      │  800 NPCs       │
└─────────────────┘                    └─────────────────┘
```

| Component | URL | What It Does |
|-----------|-----|--------------|
| Simulation API | `localhost:8081` | NPC states, buildings, events |
| Visualizer (standalone) | `file://visualizer/index.html` | Map view (opens local file) |
| Combined Frontend | `localhost:8082` | Landing + Explore + Chat |
| API Stats | `localhost:8081/api/stats` | JSON endpoint |

---

## Data Location

All data is stored in JSON files (1.4MB total):

```
data/
├── npcs_generated.json      # 800 NPCs with personalities (420KB)
├── codec_chunks/            # World codec data (768KB)
│   ├── world_codec_16_buildings.json
│   ├── world_codec_01_npcs_expanded.json
│   └── ...
```

**No database required.** The JSON files are loaded directly by the API.

---

## API Endpoints

### Get all NPCs
```bash
curl "http://localhost:8081/api/npcs?limit=50"
```

### Get NPC state at tick
```bash
curl "http://localhost:8081/api/npcs/NPC_00001/state?tick=100"
```

### Get building info
```bash
curl "http://localhost:8081/api/buildings"
```

### Get NPCs at location
```bash
curl "http://localhost:8081/api/npcs/at/B004?tick=100"
```

### Run simulation tick
```bash
curl "http://localhost:8081/api/simulation/tick?tick=100"
```

---

## Running the Combined Frontend

To run the full landing page + visualizer + chat:

```bash
cd demo
pip install flask gunicorn
python server.py
# Open http://localhost:8081
```

---

## Running Chat with AI

The NPC chat feature requires a Gemini API key:

```bash
# Set up Vertex AI credentials (recommended)
gcloud auth application-default login

# OR set API key directly
export GOOGLE_API_KEY="your-api-key-here"

# Start the chat API
cd ao-world-engine
python -m api.npc_chat
```

Then the chat API will be available at `localhost:8080`.

---

## Testing the Simulation

```bash
# Quick test of NPC behavior
python -c "
from api.api_simulation import get_npcs, get_npc_state, generate_hobbies

npcs = get_npcs()[:3]
for npc in npcs:
    hobbies = generate_hobbies(npc)
    state = get_npc_state(npc, 100)
    print(f'{npc[\"name\"]}: {hobbies}')
    print(f'  At tick 100: {state[\"activity\"]} @ {state[\"location\"]}')
"
```

---

## Modifying the World

### Add a new NPC
Edit `data/npcs_generated.json` and add:
```json
{
  "id": "NPC_00801",
  "name": "Your Character",
  "archetype": "resident",
  "faction": "civilian",
  "personality": {
    "aggression": 0.3,
    "sociability": 0.7,
    "greed": 0.2,
    "curiosity": 0.8,
    "loyalty": 0.6
  },
  "schedule": "worker",
  "home": "B001",
  "workplace": "B003"
}
```

### Add a new building
Edit `data/codec_chunks/world_codec_16_buildings.json` and add to `building_assignments`.

---

## Uploading to Arweave (Optional)

Once you're happy with your local changes, you can upload to Arweave for permanent storage:

```bash
# Install uploader
pip install arweave-python-client

# Upload NPC data
python scripts/upload_npcs_arweave.py
```

See [ARWEAVE_TRANSACTION_LOG.md](./ARWEAVE_TRANSACTION_LOG.md) for existing uploads.

---

## Requirements

- Python 3.10+
- Flask
- No database - just JSON files!

```bash
pip install flask requests
```

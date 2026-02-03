# AO World Engine - NPC Chat API

## Overview

The NPC Chat API provides AI-powered conversational NPCs for RE:ECHO City. NPCs maintain consistent personalities, relationships, and backstories through the World Codec system.

## Endpoints

### Chat with NPC
```bash
POST /api/npc/chat
Content-Type: application/json

{
  "npc_id": "charlie",
  "tick": 100,
  "message": "What happened to your arm?"
}
```

**Response:**
```json
{
  "npc": "Charlie",
  "response": "ECHO happened to it. They took flesh and bone. Now I got this... this glowing ghost limb. Zero Chen got hurt worse that day - lost his own arm to save me.",
  "memories_enabled": true,
  "state": {
    "tick": 100,
    "location": "resistance_hideout",
    "mood": "restless",
    "weather": "clear",
    "hour": 4,
    "day": 5
  }
}
```

### List NPCs
```bash
GET /api/npcs
```

### Get NPC State
```bash
GET /api/npc/state/{npc_id}/{tick}
```

### Get Tick State
```bash
GET /api/tick/{tick}
```

## Available NPCs

| ID | Name | Archetype |
|----|------|-----------|
| charlie | Charlie | Protagonist / Resistance Fighter |
| zero_chen | Zero Chen | Resistance Leader |
| kai_vance | Kai Vance | Tactician |
| felix | Felix | Bartender / Info Broker |
| nova_chen | Nova Chen | Mercenary (Zero's sister) |
| aiche | Aiche | Digital Entity / City AI |
| pixel | Pixel | Tech Support / Hacker |
| sister_mira | Sister Mira | Temple Priestess / Secret Healer |
| orion_thane | Orion Thane | Mystic / Prophet |
| selene_voss | Selene Voss | Ghost-Child |
| mama_indira | Mama Indira | Underground Matriarch |
| cipher | Cipher | Data Broker |

## How NPCs Stay Consistent

### Core Facts System
Each NPC has hardcoded "core facts" they always remember:

**Charlie's Core Facts:**
- Your right arm is a holographic cyberarm - translucent, shows glowing circuitry
- Zero Chen saved your life and lost HIS arm doing it
- Zero Chen is the Resistance leader, NOT Nova Chen (she's his estranged sister)
- Felix runs the Neon Bar - you go there for information
- Aiche is the city's AI consciousness
- Sister Mira secretly helps wounded despite being Temple
- Pixel is your tech support - young hacker genius
- Kai Vance is your trusted tactical advisor

### Relationship System
NPCs know their relationships from the World Codec, so they respond consistently when asked about other characters.

## Deployment

### Local Development
```bash
cd api
python3 npc_chat.py
# Server runs on http://localhost:8080
```

### Cloud Run Deployment
```bash
gcloud run deploy ao-npc-chat \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| GCP_PROJECT | Google Cloud project ID | wandern-project-startup |
| GCP_LOCATION | Vertex AI region | us-central1 |
| PORT | Server port | 8080 |

## Testing

### Test Arm Knowledge
```bash
curl -X POST http://localhost:8080/api/npc/chat \
  -H "Content-Type: application/json" \
  -d '{"npc_id": "charlie", "tick": 100, "message": "Is your arm holographic?"}'
```

### Test Relationships
```bash
curl -X POST http://localhost:8080/api/npc/chat \
  -H "Content-Type: application/json" \
  -d '{"npc_id": "charlie", "tick": 100, "message": "Tell me about Zero Chen"}'
```

### Test Cross-NPC Consistency
```bash
# Ask Charlie about his arm
curl -X POST http://localhost:8080/api/npc/chat \
  -d '{"npc_id": "charlie", "tick": 100, "message": "How did you lose your arm?"}'

# Ask Zero about Charlie's arm
curl -X POST http://localhost:8080/api/npc/chat \
  -d '{"npc_id": "zero_chen", "tick": 100, "message": "How did you lose your arm?"}'
```

## World Codec Integration

The API loads NPC data from the World Codec chunks:
- `world_codec_01_npcs.json` - NPC profiles and relationships
- `world_codec_14_behaviors.json` - Embedded Python behaviors
- `chunk_loader.py` - Loads and indexes all chunks

See `/docs/WORLD_CODEC.md` for full codec documentation.

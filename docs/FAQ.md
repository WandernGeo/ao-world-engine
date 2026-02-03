# AO World Engine - FAQ

Frequently asked questions for end users of the RE:ECHO City simulation.

---

## General Questions

### What is the AO World Engine?
An open-source framework for building decentralized, persistent simulated worlds. It runs on Arweave (permanent storage) and AO (compute layer), enabling worlds that can "run forever" without ongoing server costs.

### What is RE:ECHO City?
A cyberpunk city simulation built on the AO World Engine. It's the reference implementation showing what's possible with the framework.

### Is this free to use?
Yes! The AO World Engine is open source (AGPL-3.0). The NPC chat API is free during beta. Arweave storage is one-time cost ($5-8/GB) or free for files under 100KB.

---

## NPC Chat Questions

### How do NPCs remember things?
NPCs use a "core facts" system - essential knowledge they always remember (like Charlie always knowing his arm is holographic and that Zero Chen saved him). This is stored in the World Codec.

### Why doesn't the NPC remember what I just said?
The frontend needs to send conversation history. If you're building an app, include the `history` array:

```javascript
fetch('/api/npc/chat', {
  body: JSON.stringify({
    npc_id: 'charlie',
    tick: 100,
    message: 'How does your arm work?',
    history: [
      { role: 'user', content: 'Tell me about your arm' },
      { role: 'npc', content: 'This holographic thing? Zero Chen saved me...' }
    ]
  })
})
```

### Do NPC personalities change over time?
**Current behavior:**
- Location changes every 4 ticks
- Mood changes every 8 ticks  
- Weather changes every 6 ticks
- Base personality stays the same

**Coming soon:** Events that permanently modify personality vectors (trauma, growth, relationships).

### How do NPCs know about each other?
The World Codec stores relationships. When you ask Charlie about Felix, he knows:
- Felix is a bartender/info broker
- They have a "contact" relationship
- Trust level: 0.7
- History: "Information source at the bar"

### Why do NPCs sometimes give different answers to the same question?
The LLM generates unique responses each time using the same context. This is intentional - real people don't repeat themselves verbatim. The underlying facts stay consistent.

---

## World Simulation Questions

### What is a "tick"?
A tick is one unit of simulation time. Each tick:
- Hour = tick % 24
- Day = tick // 24
- Weather calculated from tick hash

At tick 100: Day 5, Hour 4, Weather varies deterministically.

### Does the weather change?
Yes! Weather is deterministic based on tick:
- `clear`, `rain`, `storm`, or `fog`
- Changes every 6 ticks
- Same tick = same weather everywhere

### Why does "Describe Scene" always mention rain?
The Signal Noir art style uses rain as a default noir aesthetic. We're updating this to use actual tick weather.

### How are NPC locations decided?
Deterministically:
1. 60% chance to be at their "home location"
2. Otherwise, hash of `(npc_id + tick)` picks from available locations
3. Same tick + same NPC = same location every time

---

## Technical Questions

### What is the World Codec?
A chunked JSON database (15 files, ~340KB) containing:
- 700+ actions/verbs
- 772 objects
- 12 founding NPCs with relationships
- Medical, tech, chemistry systems
- Skills, events, lore
- Geospatial coordinates (NYC/Brooklyn)
- Embedded Python behaviors

### What is "Schrodinger's Simulation"?
The simulation doesn't run continuously - it calculates state on-demand. When you query tick 5000, it computes what would have happened. This enables:
- Querying any past or future tick
- No server costs when idle
- Deterministic reproducibility

### How is data stored permanently?
On Arweave - pay once, stored forever. Data is:
- Immutable (can't be changed or deleted)
- Publicly queryable via GraphQL
- Free for files under 100KB

### Can I run my own world?
Yes! Fork the repository and:
1. Replace the World Codec with your own lore
2. Define your NPCs in `founding_npcs.py`
3. Deploy to Cloud Run or your own server
4. Optionally upload to Arweave for permanence

---

## Building Your Own

### How do I add a new NPC?
1. Add to `data/founding_npcs.py` with personality vectors
2. Add relationships to existing NPCs
3. Optionally add core facts for consistency
4. Upload to Arweave for permanent storage

### How do unknown NPCs work (like a random shopkeeper)?
The system uses **archetypes** - templates for procedural generation:
1. Location type (shop) → Archetype (shopkeeper)
2. Deterministic name from hash
3. Personality from archetype + district modifiers
4. Dynamic dialogue from templates + LLM

### Can I embed code in the World Codec?
Yes! The behaviors chunk (`chunk_14_behaviors.json`) contains:
- Base64-encoded Python functions
- Executed at runtime for dynamic logic
- Used for: pricing, gossip spread, reactions

---

## Troubleshooting

### "NPC not found" error
Check that `npc_id` matches one of the founding NPCs:
`charlie`, `felix`, `kai_vance`, `nova_chen`, `zero_chen`, `aiche`, `pixel`, `sister_mira`, `orion_thane`, `selene_voss`, `mama_indira`, `cipher`

### Response is slow
First request after cold start takes 2-3 seconds. Subsequent requests: ~500ms.

### NPC says something inconsistent
Report it! We'll add it to their core facts. The goal is 100% consistency on key character details.

---

## API Reference

```bash
# Chat with NPC
POST /api/npc/chat
{"npc_id": "charlie", "tick": 100, "message": "Hello", "history": []}

# List all NPCs  
GET /api/npcs

# Get NPC state at tick
GET /api/npc/state/{npc_id}/{tick}

# Get world state at tick
GET /api/tick/{tick}

# Describe a scene
POST /api/scene/describe
{"npc_id": "charlie", "tick": 100, "action": "standing in the rain"}
```

---

## Resources

- **GitHub:** https://github.com/WandernGeo/ao-world-engine
- **API:** https://ao-npc-chat-1071951656531.us-central1.run.app
- **Arweave:** https://arweave.net
- **AO:** https://ao.arweave.dev

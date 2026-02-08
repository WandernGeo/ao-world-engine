# AO World Engine — Technical Whitepaper

> *Write Once, Run Forever: Autonomous Persistent Worlds on the Permaweb*

**Version:** 1.0  
**Date:** February 2026  
**Authors:** WandernGeo Team  
**License:** AGPL-3.0

---

## Abstract

AO World Engine is an open-source framework for building **permanent, decentralized simulations** on [Arweave](https://arweave.org) and [AO](https://ao.arweave.dev). Unlike traditional game servers that die when companies shut down, worlds built on AO World Engine run autonomously on the permaweb — no maintenance, no servers, no single point of failure.

The engine provides deterministic NPC scheduling, economy simulation, canon governance, and AI-powered dialogue — all within Arweave's sub-100KB free upload tier. Its reference implementation, **RE:ECHO City**, demonstrates a cyberpunk metropolis of 2,830+ NPCs operating across 8 districts with autonomous governance, economic cycles, and persistent memory.

---

## 1. Problem Statement

Traditional game worlds are ephemeral:

| Issue | Traditional Servers | AO World Engine |
|-------|-------------------|-----------------|
| **Lifespan** | 3–5 years average | 200+ years (Arweave endowment) |
| **Dependency** | Company must stay solvent | No company required |
| **State** | Lost on shutdown | Permanent on Arweave |
| **Verifiability** | Trust the operator | Cryptographically verifiable |
| **Composability** | Walled gardens | Any client can read state |

## 2. Architecture

### 2.1 On-Chain (AO Process)

The simulation runs as a Lua process on the AO network with cron-triggered ticks:

```
AO Process (world.lua)
├── Cron-Tick Handler (every 5 minutes)
│   ├── Advance WorldTick, WorldDay, WorldYear
│   ├── Update NPC schedules (deterministic)
│   ├── Process economy (taxes, GDP, inflation)
│   └── Generate events (weather, social, conflict)
├── State (permanent on Arweave)
│   ├── WorldTick / WorldDay / WorldYear
│   ├── NPC: positions, wallets, relationships
│   ├── Buildings: occupancy, ownership
│   └── Economy: budget, GDP, black market, Gini
└── Message Handlers
    ├── get-state → Read world snapshot
    ├── get-npcs → NPC positions at tick T
    └── advance-tick → Manual tick advancement
```

### 2.2 Off-Chain (Clients)

Frontends connect via dry-run queries (free, no gas):

- **Explorer** — 2D city map with building inspection and NPC tracking
- **Monitor** — Economy dashboard (GDP, inflation, black market indices)
- **Chat** — AI-powered NPC dialogue via Vertex AI / Gemini
- **Graph** — Neural network visualization of NPC-building relationships

### 2.3 Data Layer

All world data is chunked to **< 100KB** for Arweave's free upload tier:

| Data Type | Chunk Size | Storage |
|-----------|-----------|---------|
| NPC profiles (×2,830) | ~80 KB per batch | Arweave (permanent) |
| World Codec (19 chunks) | ~20 KB each | Arweave (permanent) |
| Building registry | ~12 KB | Arweave (permanent) |
| Simulation state | ~2 KB per tick | AO process memory |

## 3. Key Innovations

### 3.1 Deterministic Pseudo-Random Scheduling

NPCs know each other's locations **without messaging**. Given `NPC_ID + tick`, any process can independently calculate where an NPC will be:

```
location = SCHEDULE[npc_id][tick % SCHEDULE_LENGTH]
```

This eliminates inter-process communication overhead and enables unlimited read parallelism.

### 3.2 Canon Governance

A built-in content validation system ensures world consistency:

- **Fact validation** — NPC responses are checked against canonical lore
- **Content moderation** — Invalid submissions are transformed or rejected
- **Immutable history** — All events are recorded permanently on Arweave

### 3.3 Economy Simulation

The engine runs a macro-economic model per tick:

- **Tax collection** → City treasury
- **GDP calculation** → Based on NPC economic activity
- **Inflation modeling** → Money supply vs. goods produced
- **Black market index** → Underground economy relative to GDP
- **Gini coefficient** → Wealth inequality tracking

### 3.4 AI Integration

NPCs use LLM-powered dialogue with context:

- **Temporal awareness** — Responses vary by time of day, day, and year
- **Relationship memory** — NPCs remember past conversations
- **Personality consistency** — MBTI, zodiac, faction, and archetype constraints
- **Cross-NPC knowledge** — NPCs know about each other based on relationships

## 4. Economics

### 4.1 Cost Structure

| Component | Cost | Frequency |
|-----------|------|-----------|
| Storage (Arweave) | ~$0.003/KB | **One-time** |
| Process deployment | Storage cost | **One-time** |
| Cron execution | Subsidized (testnet) | Ongoing |
| Read queries (dry-run) | Free | Per query |
| Write messages | Micro-fee in AR | Per message |

### 4.2 Sustainability Model

Long-term computation is funded through:

1. **Staked AR** — Process holds AR tokens earning compute credits
2. **Community sponsorship** — Anyone can fund cron execution
3. **Microsubscriptions** — Premium features ($5/month) pool toward compute
4. **Protocol subsidy** — AO network allocates compute for "public goods"

## 5. Scaling Roadmap

| Phase | Timeline | Capability |
|-------|----------|------------|
| **V1** (current) | 2025–2026 | Single process, 2,830 NPCs, 5-min ticks |
| **V2** | 2026 | District sharding, 10,000 NPCs, 1-min ticks |
| **V3** | 2027+ | Cross-world messaging, 100K+ NPCs, real-time hybrid |

## 6. Reference Implementation: RE:ECHO City

RE:ECHO City is a cyberpunk metropolis demonstrating the engine's capabilities:

- **Population:** 2,830 NPCs across 8 districts
- **Governance:** Autonomous district councils with election cycles
- **Economy:** GDP tracking, tax collection, black market simulation
- **Aesthetic:** Signal Noir — dark environments, neon accents, cybernetic augmentation
- **AI Dialogue:** NPCs powered by Vertex AI with persistent memory

**Live instance:** [ao-world-engine-1071951656531.us-central1.run.app](https://ao-world-engine-1071951656531.us-central1.run.app)

## 7. Getting Started

```bash
# Clone the engine
git clone https://github.com/WandernGeo/ao-world-engine.git

# Deploy your own world
cd ao-world-engine
npm install
node scripts/send_ao_message.mjs get-state '{}'
```

See [BUILDING_YOUR_WORLD.md](BUILDING_YOUR_WORLD.md) for the full guide to creating your own persistent world.

---

## License

AO World Engine is licensed under **AGPL-3.0**. Worlds built on the engine are independently owned — the engine is open, your content is yours.

---

*AO World Engine — Build worlds that outlive their creators.*

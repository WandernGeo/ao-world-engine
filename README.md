# 🌐 AO World Engine

> A decentralized simulation engine for persistent worlds on Arweave + AO

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Built on AO](https://img.shields.io/badge/Built%20on-AO-purple)](https://ao.arweave.dev)
[![Powered by Arweave](https://img.shields.io/badge/Powered%20by-Arweave-black)](https://arweave.org)

---

## What Is This?

AO World Engine is an **open source simulation framework** for building persistent, decentralized worlds on [Arweave](https://arweave.org) and [AO](https://ao.arweave.dev).

**Use it to build:**
- 🏙️ Simulated cities with millions of NPCs
- 🎮 Persistent MMO game backends
- 🤖 Autonomous agent ecosystems
- 📖 Living narrative worlds
- 🌍 Any world that runs forever on the permaweb

```
YOUR WORLD (copyrighted)          THE ENGINE (open source)
        │                                   │
        │ "Neo Tokyo"                       │
        │ "Martian Colony"                  │
        │ "Fantasy Kingdom"       ◀─────────┤
        │ "RE:ECHO City"                    │
        │ "Your World Here"                 │
        │                                   │
        ▼                                   ▼
┌─────────────────────┐         ┌─────────────────────┐
│ Your lore           │         │ NPC state machines  │
│ Your art style      │   uses  │ Deterministic sched │
│ Your characters     │◀────────│ Faction system      │
│ Your animations     │         │ City services       │
│                     │         │ Event broadcasting  │
│ © You, All Rights   │         │ Canon validation    │
│    Reserved         │         │                     │
│                     │         │ AGPL-3.0 Open Source│
└─────────────────────┘         └─────────────────────┘
```

---

## Key Features

### 🔄 Deterministic Pseudo-Random Scheduling
NPCs know where each other will be **without messaging**. Given NPC ID + time, any process can calculate location.

### 📦 <100KB Chunking
Designed for Arweave's free upload tier. All data chunks to under 100KB.

### 🛡️ Canon Validation
Built-in content moderation. Invalid submissions are transformed or rejected automatically.

### 🌍 Runs Forever
Once deployed, the world simulates autonomously on AO cron jobs. No servers needed.

### 🔌 Bring Your Own Lore
The engine is lore-agnostic. Plug in your own world, factions, and art style.

### 🌀 Echo Layers (Multiverse System)
**NEW**: Worlds can fork into parallel dimensions (layers). NPCs experience rare "bleed" events where they glimpse alternate realities. Users "Watch" like higher beings observing the simulation.

- **Layer 0 (Prime)**: Your official canon world
- **Layer 1+**: Community-created alternate timelines
- **The Veil**: Thin barriers between layers (0.1% bleed chance per tick)
- **The Watchers**: Users observing via visualization apps

See [MULTIVERSE_LORE.md](./docs/MULTIVERSE_LORE.md) for the full multiverse system.

---

## Quick Start

```bash
# Clone the engine
git clone https://github.com/wanderngeo/reecho-city.git ao-world-engine
cd ao-world-engine

# Install AOS CLI
npm install -g aos

# Start AO shell
aos

# Load a district process
.load ao-processes/district.lua

# Initialize with NPCs
Send({ Target = ao.id, Action = "init", Data = '{"npc_count": 100}' })
```

---

## Project Structure

```
ao-world-engine/
├── ao-processes/           # AO Lua processes
│   ├── district.lua        # District simulation
│   ├── global_event_bus.lua # World-level events
│   └── canon_validator.lua # Content validation
├── schemas/                # JSON schemas
│   ├── action_dictionary.json
│   ├── factions.json
│   └── city_services.json
├── docs/
│   ├── CANON_GOVERNANCE.md # Content rules
│   └── BUILDING_YOUR_WORLD.md
└── examples/               # Example implementations
    └── generic_city/       # Starter template
```

---

## Building Your World

1. **Fork this repo**
2. **Define your lore** - Create your factions, districts, NPCs
3. **Customize schemas** - Adapt archetypes to your setting
4. **Deploy to AO** - Your world runs on the permaweb
5. **Build visualization** - Connect your own rendering layer

See [BUILDING_YOUR_WORLD.md](./docs/BUILDING_YOUR_WORLD.md) for detailed guide.

---

## Worlds Built on This Engine

| World | Creator | Description |
|-------|---------|-------------|
| *Your world here* | You | Fork and build! |

*Want to be listed? Open a PR!*

---

## License

**AGPL-3.0** - You can use this commercially, but modifications must stay open source.

This protects the community while allowing you to build proprietary worlds **on top of** the engine.

---

## Links

- [AO Cookbook](https://cookbook.ao.arweave.dev/)
- [Arweave Docs](https://docs.arweave.org/)
- [ArDrive](https://ardrive.io/)

---

*"The engine runs forever. What you build on it is yours."*

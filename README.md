# 🌃 RE:ECHO City

> A billion NPCs simulating in code, visualized on demand

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Built on AO](https://img.shields.io/badge/Built%20on-AO-purple)](https://ao.arweave.dev)
[![Powered by Arweave](https://img.shields.io/badge/Powered%20by-Arweave-black)](https://arweave.org)

---

## 🎯 Vision

RE:ECHO City is a **persistent, procedurally-evolving world** running entirely on [Arweave](https://arweave.org) and [AO](https://ao.arweave.dev). 

- **Millions of NPCs** exist as lightweight state machines
- **Interactions happen as code** — pure data, not rendered graphics
- **Visualization is optional** — users "tune in" to see storylines materialize
- **The world runs forever** with permanent storage and near-zero compute cost

```
BEHIND THE SCENES (always running):
├── NPCs as ~500-byte JSON state machines
├── AO processes running decisions via cron jobs
├── Events logged as compact shorthand codes
└── All chunked into <100KB files on Arweave

ON DEMAND (when users "tune in"):
├── Fetch event logs for any NPC/timeframe
├── LLM expands shorthand into rich narrative
├── Animation engine renders the scene
└── Users see what "actually transpired"
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    RE:ECHO CITY ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │   DISTRICT   │────▶│   DISTRICT   │────▶│   DISTRICT   │    │
│  │   PROCESS    │     │   PROCESS    │     │   PROCESS    │    │
│  │  (10K NPCs)  │     │  (10K NPCs)  │     │  (10K NPCs)  │    │
│  └──────────────┘     └──────────────┘     └──────────────┘    │
│         │                    │                    │             │
│         ▼                    ▼                    ▼             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              ARWEAVE PERMANENT STORAGE                   │   │
│  │  • NPC States (chunked <100KB)                          │   │
│  │  • Event Logs (shorthand codes)                         │   │
│  │  • Action Dictionary                                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              VISUALIZATION LAYER (On Demand)             │   │
│  │  • LLM Narrative Expansion                               │   │
│  │  • Animation Rendering                                   │   │
│  │  • Story Playback                                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Concepts

- **Append-Only Evolution**: Arweave is immutable. NPCs evolve by appending new state transactions.
- **Shorthand Action Codes**: Store `"T:b3k2:crystal:500"` instead of verbose descriptions. LLM expands during visualization.
- **Probability-Weighted Routines**: NPCs have weighted behaviors, not deterministic scripts.
- **Dormant/Active System**: Only ~0.01% of NPCs simulate at any time. The rest are "sleeping" on Arweave.

---

## 📁 Project Structure

```
reecho-city/
├── ao-processes/           # AO Lua processes
│   ├── district.lua        # District simulation (10K NPCs each)
│   ├── global_event_bus.lua # World-level event broadcasting
│   ├── ai_oracle.lua       # Shared LLM decision caching
│   └── schema_registry.lua # Event type definitions
├── schemas/                # JSON Schema definitions
│   ├── npc.schema.json     # NPC state structure
│   ├── event.schema.json   # Event log structure
│   └── action_dictionary.json # Shorthand code definitions
├── archetypes/             # Starter NPC templates
│   ├── hacker_drone.json
│   ├── street_samurai.json
│   ├── merchant.json
│   └── ...
├── chunking/               # Utilities for <100KB chunking
│   ├── chunker.py          # Python chunking utilities
│   └── chunker.js          # JavaScript chunking utilities
├── viewer/                 # Basic web viewer (reference impl)
│   └── index.html
├── docs/                   # Documentation
│   └── architecture.md
└── examples/               # Example usage
    └── deploy-district.md
```

---

## 🚀 Quick Start

### Prerequisites

```bash
# Install AOS CLI (AO development)
npm install -g aos

# Install ArDrive CLI (free uploads <100KB)
npm install -g ardrive-cli

# Get ArConnect browser extension for wallet
# https://arconnect.io
```

### Deploy Your First District

```bash
# Clone the repo
git clone https://github.com/wanderngeo/reecho-city.git
cd reecho-city

# Start AO shell
aos

# Load the district process
.load ao-processes/district.lua

# Initialize with 100 test NPCs
Send({ Target = ao.id, Action = "init", Data = '{"npc_count": 100}' })
```

---

## 🎭 NPC Archetypes

| Archetype | Goals | Routine Pattern |
|-----------|-------|-----------------|
| **hacker_drone** | Infiltrate systems, sell data | 60% probe, 30% hide, 10% trade |
| **street_samurai** | Protect territory, resolve conflicts | 50% patrol, 30% train, 20% intervene |
| **corporate_spy** | Gather intel, climb ladder | 40% blend, 40% observe, 20% report |
| **merchant** | Accumulate wealth | 70% trade, 20% network, 10% rest |
| **explorer** | Map unknown areas | 60% explore, 25% rest, 15% trade |
| **fixer** | Connect people, broker deals | 50% network, 30% negotiate, 20% observe |

See [`archetypes/`](./archetypes/) for full definitions.

---

## 📝 Action Dictionary

Compact codes that LLMs expand during visualization:

| Code | Meaning | Animation |
|------|---------|-----------|
| `T:target:item:credits` | Trade | `trade_gesture` |
| `M:destination` | Move | `walk_cycle` |
| `R:location:duration` | Rest | `idle_sit` |
| `A:target:weapon` | Attack | `combat_strike` |
| `C:target:topic` | Conversation | `dialogue` |
| `H:threat` | Hide | `stealth_crouch` |
| `P:target` | Probe network | `hacking_gesture` |
| `S:target:activity` | Spy | `observe_hidden` |

Example: `"T:b3k2:crystal:500"` → "TRADE with npc_b3k2, exchanging crystal for 500 credits"

---

## 💰 Cost Estimates (Feb 2026)

| Resource | Scale | Cost |
|----------|-------|------|
| **Storage** (Arweave) | 10K NPCs | ~$50 one-time |
| **Storage** (Arweave) | 1M NPCs | ~$5,000 one-time |
| **Compute** (AO) | 100K active NPCs | ~$45/month |
| **Free uploads** | <100KB each | $0 via ArDrive |

---

## 🤝 Contributing

We welcome contributions! Here's how:

1. **Districts**: Create new city districts with unique themes
2. **Archetypes**: Add NPC archetypes (jobs, personalities, routines)
3. **Events**: Design world events (festivals, disasters, conflicts)
4. **Schemas**: Extend the action dictionary
5. **Viewer**: Improve the reference web viewer

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

---

## 📜 License

This project is licensed under **AGPL-3.0** - see [LICENSE](./LICENSE).

This means:
- ✅ Use it commercially
- ✅ Modify it freely
- ✅ Distribute it
- ⚠️ **Must open-source any modifications**
- ⚠️ **Network use counts as distribution**

---

## 🔗 Links

- [AO Cookbook](https://cookbook.ao.arweave.dev/) - AO tutorials
- [Arweave Docs](https://docs.arweave.org/) - Permanent storage
- [ArDrive](https://ardrive.io/) - Free uploads <100KB
- [PermaDAO](https://permadao.com/) - Arweave ecosystem grants

---

## 🌟 Acknowledgments

Part of the [GeoEchoes](https://geoechoes.com) ecosystem.

Built with ❤️ on Arweave + AO.

---

*"The city never sleeps. It just waits to be seen."*

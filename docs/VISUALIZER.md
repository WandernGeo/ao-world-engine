# Visualizer Documentation

## Overview

The AO World Engine Visualizer provides real-time visualization of the Neon Heights district simulation. It displays NPC movements, building occupancy, and allows interactive exploration of the simulated world.

## Features

### 1. District Map View
- **6 Blocks** (A-F) arranged in 3x2 grid
- **Buildings** rendered with type-specific colors
- **NPCs** shown as colored dots by faction
- **Pan & Zoom** with mouse drag and scroll

### 2. NPC Profiles (Click to View)
Click any NPC on the map or in the sidebar list to see:
- **Name & Faction** with color-coded badge
- **Current Status**: Activity, Location, Mood
- **Archetype**: Criminal, Guard, Vendor, etc.
- **Location History**: Timeline of movements

### 3. NPC Tracking Feature
Track an NPC across simulation ticks:
1. Click NPC to open profile
2. Click "🎯 Track This NPC"
3. Press PLAY - camera follows the NPC
4. Visual indicator: Pulsing magenta ring
5. Location history updates in real-time

### 4. Building Info Panel
Click any building to see:
- **Building ID & Name**
- **Description** (readable explanation)
- **Type** with icon (🏠 Residential, 🏪 Commercial, etc.)
- **Occupant Count**: Current NPCs in building
- **Block Location**
- **View Blueprint** button (zooms to building)

### 5. Building Types
| Type | Icon | Description |
|------|------|-------------|
| Residential | 🏠 | Housing units for district residents |
| Commercial | 🏪 | Shops, markets, and retail spaces |
| Entertainment | 🎭 | Bars, clubs, and recreation venues |
| Industrial | 🏭 | Factories and maintenance facilities |
| Temple | ⛩️ | Spiritual center and community hub |
| Corporate | 🏢 | Office buildings and business centers |
| Government | 🏛️ | Admin offices and citizen services |
| Medical | 🏥 | Clinics and medical facilities |

### 6. Faction Colors
- **Civilian**: Cyan (#00ffff)
- **Resistance**: Magenta (#ff00ff)
- **Temple**: Gold (#ffd700)
- **Criminal**: Red (#ff4444)
- **Corporate**: Green (#00ff88)

## Controls

| Control | Action |
|---------|--------|
| ▶ PLAY / ⏸ PAUSE | Start/stop simulation |
| ⏭ STEP | Advance one tick |
| ⏮ RESET | Return to tick 0 |
| Speed Slider | Adjust simulation speed |
| View Mode | District Overview / Building View |
| Building Selector | Focus on specific building |
| 🏷 LABELS | Toggle NPC name labels |
| 📸 CAPTURE | Export screenshot |

## API Integration

The visualizer connects to the simulation API at `http://localhost:8081`:
- `/api/stats` - Simulation statistics
- `/api/buildings` - Building data
- `/api/npcs` - NPC list
- `/api/tick/{n}` - State at specific tick
- `/api/npcs/{id}/state?tick={n}` - NPC state at tick

## Files

- `visualizer/index.html` - Main visualizer
- `visualizer/studio.html` - RE:ECHO Studio (NPC chat interface)
- `visualizer/api_tester.html` - API testing tool

## Data on Arweave

The following data is designed to be stored on Arweave for permanent, verifiable world state:

### Codec Chunks (Immutable World Definition)
- `world_codec_00_core.json` - Core world structure
- `world_codec_01_npcs.json` - NPC definitions and attributes
- `world_codec_08_infrastructure.json` - Buildings and locations
- `world_codec_14_behaviors.json` - NPC behavior patterns

### Simulation State (Periodic Snapshots)
- Tick snapshots at intervals (every 24 ticks = 1 day)
- NPC location summaries
- Event logs and transactions

### Verification
Data pulled from Arweave can be verified by:
1. Comparing transaction IDs against manifest
2. Validating JSON schema compliance
3. Running simulation forward from snapshot

---

*Last updated: 2026-02-03*

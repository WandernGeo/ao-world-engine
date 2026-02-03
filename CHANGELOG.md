# Changelog

All notable changes to the AO World Engine project.

## [Unreleased]

### Added
- **NPC Memory System** - NPCs now remember users across sessions
  - Conversations saved to `data/memories/{user_id}/`
  - Extracts facts: name, location, preferences
  - Ready for Arweave archival

- **Getting Started Guide** - Comprehensive documentation for local install and hosted API

### Fixed
- Removed orphaned duplicate code in `npc_chat.py` causing deployment errors

---

## [2026-02-03] - NPC Memory & Visualizer Fixes

### Added
- **Persistent NPC Memory** (`api/npc_memory.py`)
  - File-based JSON storage for conversations
  - Automatic fact extraction from messages
  - `prepare_arweave_batch()` for future upload
  
- **Location Summary API**
  - `/api/simulation/tick` now returns `location_summary` with NPC counts per building
  - Visualizer renders NPCs correctly on map
  
- **NPCs at Location Endpoint**
  - `/api/npcs/at/<location>` returns NPCs at specific building

### Fixed
- `API_BASE` now uses `window.location.origin` for deployed environments
- Added missing `requests` dependency for Cloud Run
- Chat now sends `user_id` via localStorage for persistent memory

---

## [2026-02-03] - Combined Deployment

### Added
- **Combined Server** (`demo/server.py`)
  - Single Flask server for frontend + API
  - Deployable to Cloud Run as one service
  
- **Dockerfile** at project root for combined build
- **Screenshots** added to README

### Changed
- Frontend now detects environment for API base URL

---

## [2026-02-02] - Graph Network View

### Added
- **Graph Network Visualization** (`/graph`)
  - Force-directed physics simulation
  - NPC-building connections as edges
  - Faction color coding
  - Click nodes to select NPCs/buildings
  
- **Interactive Features**
  - Building dropdown selector
  - NPC click-to-track
  - Labels toggle

### Changed
- Navigation bar with Explore/Chat/Docs links
- Mobile responsive layout

---

## [2026-02-02] - Visualizer Enhancement

### Added
- **NPC Profiles Panel**
  - Shows selected NPC details
  - Personality traits visualization
  - Current activity and location
  
- **Building Info Panels**
  - Floor layouts and rooms
  - NPCs currently at location
  - Building services
  
- **NPC Tracking**
  - Click NPC to follow
  - Shows path and schedule

### Changed
- Improved district overview
- Better color coding for factions

---

## [2026-02-01] - Dynamic NPC Behavior

### Added
- **Personality-Based Hobbies**
  - NPCs have hobbies from personality vectors
  - Affects daily schedule
  
- **Building Layouts Codec**
  - Floor, room, and activity definitions
  - Support for multi-floor buildings

---

## [2026-01-31] - Plugin System

### Added
- **Complete Plugin System**
  - Extensible NPC behaviors
  - Custom action handlers
  - Event system
  
- **200+ Extended Tests**
  - Full coverage for simulation
  - Plugin integration tests
  
- **Documentation**
  - Plugin development guide
  - API reference

---

## [2026-01-30] - Core Simulation

### Added
- **NPC Semantic Profiles**
  - Personality vectors (paranoia, mysticism, aggression)
  - Topic weights for dialogue
  - Catchphrases and speech patterns
  
- **Deterministic Scheduling**
  - Schedule from tick time
  - Same tick = same world state
  
- **Faction System**
  - Resistance, Temple, Criminal, Civilian
  - Faction relationships

---

## Categories

- **Added**: New features
- **Changed**: Changes to existing functionality
- **Fixed**: Bug fixes
- **Removed**: Removed features
- **Security**: Security improvements

---

*This changelog follows [Keep a Changelog](https://keepachangelog.com/) format.*

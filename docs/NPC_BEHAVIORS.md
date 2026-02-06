# NPC Behavior System Documentation

> **Status**: ✅ Implemented  
> **Last Updated**: 2026-02-06

---

## Overview

The AO World Engine simulates realistic NPC behaviors including movement, work schedules, and social activities. This document explains the system architecture and why each component is necessary.

---

## Why This System Exists

### The Problem
Traditional game NPCs are either:
1. **Static** - Stand in one place forever (immersion-breaking)
2. **Scripted** - Follow predetermined paths (predictable, boring)
3. **Random** - Move chaotically (unrealistic)

### The Solution
Our NPCs follow **realistic daily routines** based on:
- **Occupation** (security guard vs. office worker)
- **Time of day** (morning commute, work hours, evening socials)
- **Individual variation** (some socialize more than others)

This creates a living city where:
- Security guards patrol at night
- Bakers arrive before dawn
- Office workers commute during rush hour
- Bartenders work evening shifts
- Doctors work rotating shifts

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AO PROCESS (world.lua)                    │
├─────────────────────────────────────────────────────────────┤
│  GLOBALS (Persisted on Arweave)                              │
│  ├── NPCSchedules    { npc_id: {home, work, shift} }        │
│  ├── NPCLocations    { npc_id: {location, state, tick} }    │
│  └── MovementLog     [ {tick, npc_id, from, to, state} ]    │
├─────────────────────────────────────────────────────────────┤
│  SHIFT DEFINITIONS                                           │
│  ├── day (9-17)       Office workers, teachers               │
│  ├── night (22-6)     Security, bouncers, DJs                │
│  ├── graveyard (0-8)  Night nurses, 24h clerks               │
│  ├── evening (16-24)  Bartenders, waiters, performers        │
│  ├── morning (4-12)   Bakers, garbage collectors             │
│  ├── flexible (10-18) Artists, hackers, fixers               │
│  ├── always_on (0-24) Doctors, paramedics, police            │
│  └── split (lunch+dinner) Chefs, restaurant staff            │
├─────────────────────────────────────────────────────────────┤
│  FUNCTIONS                                                   │
│  ├── process_npc_movements(tick)  → Called every CRON tick  │
│  ├── is_work_hours(hour, shift)   → Check if working        │
│  └── get_shift_for_archetype()    → Auto-derive shift       │
├─────────────────────────────────────────────────────────────┤
│  HANDLERS                                                    │
│  ├── load-npc-schedules   → Bulk load schedules             │
│  ├── get-npc-locations    → Query current positions         │
│  └── get-movement-log     → Recent movement history         │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### 1. Schedule Loading (One-Time Setup)
```bash
node scripts/load_npc_schedules.mjs
```

This script:
1. Reads NPC data from `data/codec_chunks/world_codec_01_npcs_expanded.json`
2. Extracts `location_home`, `location_work`, `archetype`
3. Sends to AO via `load-npc-schedules` action
4. AO auto-derives shift from archetype if not specified

### 2. Autonomous Movement (Every CRON Tick)
```
CRON (10 min) → cron-tick handler → process_npc_movements(tick)
                                          ↓
                              For each NPC with schedule:
                                  1. Get current hour
                                  2. Check if work hours for their shift
                                  3. Determine target location
                                  4. Update NPCLocations if moved
                                  5. Log movement to MovementLog
```

### 3. Manual Testing (advance-tick)
```bash
# Advance 100 ticks instantly
node scripts/send_ao_message.mjs advance-tick '{"ticks":100}'
```

---

## Why Each Component is Necessary

| Component | Why It Exists |
|-----------|---------------|
| **NPCSchedules** | Stores each NPC's home/work locations and shift type. Without this, NPCs don't know where to go. |
| **NPCLocations** | Tracks current positions. Without this, you can't query "who is at the bar right now?" |
| **MovementLog** | Enables debugging and visualizing NPC movement patterns. |
| **SHIFT_DEFINITIONS** | Different jobs require different hours. Security guards work nights. |
| **ARCHETYPE_SHIFTS** | Auto-derives shift from occupation so you don't have to manually specify for each NPC. |
| **process_npc_movements()** | The core function that moves NPCs. Called every tick. |
| **load_npc_schedules.mjs** | Bootstraps the system by loading NPC data from codec files. |

---

## Usage Examples

### Load Schedules
```bash
# Extract from codec and load to AO
node scripts/load_npc_schedules.mjs

# Dry run (preview only)
node scripts/load_npc_schedules.mjs --dry-run
```

### Query Locations
```bash
# All NPC locations
node scripts/send_ao_message.mjs get-npc-locations '{}'

# NPCs at a specific location
node scripts/send_ao_message.mjs get-npc-locations '{"location":"L026"}'
```

### Test Movement
```bash
# Advance 240 ticks (1 full day)
node scripts/send_ao_message.mjs advance-tick '{"ticks":240}'

# Check movement log
node scripts/send_ao_message.mjs get-movement-log '{"limit":20}'
```

### Manual Schedule Load
```bash
# Load specific NPCs with custom shifts
node scripts/send_ao_message.mjs load-npc-schedules '{
  "schedules": [
    {"id":"C01", "location_home":"L026", "location_work":"L042", "archetype":"Noir Detective"},
    {"id":"G01", "location_home":"L001", "location_work":"L002", "shift":"night"}
  ]
}'
```

---

## NPC States

During movement, NPCs transition through these states:

| State | Description |
|-------|-------------|
| `sleeping` | At home during sleep hours |
| `waking` | Getting ready in the morning |
| `commuting_to_work` | Traveling to workplace |
| `working` | At workplace during shift |
| `commuting_home` | Traveling back home |
| `relaxing` | At home after work |
| `socializing` | At a social location (30% evening chance) |
| `preparing` | Getting ready for night shift |
| `going_home` | Late night, heading to bed |

---

## Related Files

| File | Purpose |
|------|---------|
| `ao-processes/world.lua` | Core simulation logic |
| `scripts/load_npc_schedules.mjs` | Schedule loading script |
| `scripts/send_ao_message.mjs` | General AO messaging |
| `data/codec_chunks/world_codec_01_npcs_expanded.json` | NPC definitions |
| `docs/AO_AUTONOMY.md` | Self-sufficiency documentation |

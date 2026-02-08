# AO World Engine — Time System

## How Time Works

Every AO World Engine instance runs on a **tick-based** time system. Each tick advances the simulation forward — NPCs move, interact, work, sleep, trade, and form relationships.

### Time Formula

| Unit | Value |
|------|-------|
| **1 tick** | = 6 minutes of city time |
| **10 ticks** | = 1 hour of city time |
| **240 ticks** | = 1 full day (24 hours) |
| **Tick 0** | = 6:00 AM (synced to EST) |

The simulation day is divided into **time periods** that drive NPC behavior:

| Period | Ticks | City Time | NPC Behavior |
|--------|-------|-----------|-------------|
| T01 (Late Night) | 0–23 | 00:00–02:24 | Sleeping, night workers |
| T02 (Pre-Dawn) | 24–39 | 02:24–04:00 | Early risers, bakers |
| T03 (Dawn) | 40–59 | 04:00–06:00 | Morning commute begins |
| T04 (Morning) | 60–99 | 06:00–10:00 | Work shifts start |
| T05 (Midday) | 100–139 | 10:00–14:00 | Peak activity, lunch |
| T06 (Afternoon) | 140–179 | 14:00–18:00 | Work continues |
| T07 (Evening) | 180–209 | 18:00–21:00 | Social time, dining |
| T08 (Night) | 210–229 | 21:00–23:00 | Entertainment, bars |
| T09 (Late Night) | 230–239 | 23:00–00:00 | Winding down |

## Configuring Time for Your World

When you spawn your own world process, **you choose how fast time passes** by setting the CRON interval:

```lua
-- Set at process spawn time
{ name = "Cron-Interval", value = "1-minute" }  -- Fast: 1 day every 4 hours
{ name = "Cron-Interval", value = "10-minutes" } -- Standard: 1 day every 40 hours
{ name = "Cron-Interval", value = "30-seconds" } -- Turbo: 1 day every 2 hours
```

### Speed Comparison

| CRON Interval | 1 City Day Takes | 1 City Year Takes | Best For |
|---------------|-----------------|-------------------|----------|
| **30 seconds** | 2 real hours | 30 real days | Rapid testing, demos |
| **1 minute** | 4 real hours | 60 real days | Development, active worlds |
| **5 minutes** | 20 real hours | 300 real days | Production balance |
| **10 minutes** | 40 real hours | 1.6 real years | Long-running production |
| **24 minutes** | 4 real days | 4 real years | 1:1 real-time sync |

### Changing Speed

The CRON interval is set at spawn time and sealed to that process. To change speed:
1. Spawn a new process with the desired interval
2. Migrate your world state (or start fresh)
3. Update your frontend to point to the new process ID

You can also use **manual ticking** via the `advance-tick` handler to fast-forward at any time, regardless of CRON speed.

## Two Layers of Persistence

Your world has **two layers of data**:

### Layer 1: Process Memory (Live State)

The AO process holds a rolling window of recent activity:

| Data Store | Contents | Retention |
|------------|----------|-----------|
| `NPCLocations` | Where every NPC is right now | Always current |
| `NPCSocialHistory` | Relationship strength between all NPC pairs | Unlimited |
| `NPCWallets` | Every NPC's balance, income, spending | Always current |
| `NPCConversations` | User-to-NPC chat history | 50 msgs per pair |
| `InteractionLog` | NPC meetings (who, where, mood) | Last 500 |
| `MovementLog` | NPC movements between locations | Last 1,000 |
| `ItemTransactionLog` | Purchases, trades, gifts | Last 500 |

This is what your frontend queries for real-time display.

### Layer 2: Arweave Transaction Log (Permanent)

Every message sent to your AO process is stored as a permanent Arweave transaction. Even after the process memory trims old entries, the original Arweave transactions remain forever. This enables full history reconstruction.

## For World Operators

### Spawning Your Own World

```bash
# 1. Clone the repo
git clone https://github.com/WandernGeo/ao-world-engine.git

# 2. Set your CRON speed and spawn
node scripts/deploy_ao_mainnet.mjs
# Edit the script to set your preferred Cron-Interval

# 3. Your world runs autonomously forever
# All data persisted on Arweave at zero ongoing cost
```

## Failsafe Architecture

Your world data lives permanently on Arweave. The AO Compute Unit (CU) is just a compute layer that reads it — like a browser rendering HTML. If the CU goes down, your data is never lost.

### Three Built-In Safeguards

| Safeguard | What It Does | How It Works |
|---|---|---|
| **CU Failover** | Auto-switches to backup Compute Unit | 3 CU endpoints configured. If primary times out (5s), transparently tries backups. Resets to primary on recovery. |
| **State Cache** | Shows last known state when AO is down | `getWorldState()` caches every successful response in `localStorage` (10 min TTL). If all CUs fail, returns cached data instead of zeros. |
| **Stale Tick Detector** | Warns when simulation freezes | Tracks last tick-change timestamp. If unchanged for 5+ minutes, shows ⚠️ warning banner with force-advance button. |

### What Happens When Things Fail

```
CU goes down?
  → Failover to backup CU (automatic, transparent)
  → If all CUs down, show cached state from localStorage
  → Yellow banner: "Simulation stale — tick unchanged for N+ minutes"
  → Manual "Force Advance" button to unstick

CRON stops firing?
  → All past state is preserved on Arweave
  → Stale tick detector alerts the operator
  → Manual advance-tick catches up any missed ticks
  → Resume CRON normally — nothing is lost

Frontend offline for days?
  → Reconnect, query get-state, get current tick
  → localStorage cache provides instant display while AO responds
  → Full state reconstructed from Arweave transaction log
```

### Why This Works

AO processes are deterministic state machines. The "state" isn't stored on a server — it's the result of replaying every Arweave transaction in order. Any CU can reconstruct the full state at any time. Your simulation is as permanent as Arweave itself.

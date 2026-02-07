# AO World Engine — Scale Architecture

> How to run 800 → 10,000 → 2,000,000 → 20,000,000 NPCs on AO/Arweave

---

## Current Architecture (800 NPCs)

```
Single AO Process
├── 800 NPCs in memory (~5 MB)
├── 240 ticks/day cycle
├── MovementLog: last 1,000 entries
├── InteractionLog: last 500 entries
└── Economy: single budget tracker
```

**Cost: $0/month** (AO compute is subsidized)

---

## The Memory Wall

An AO process has a practical memory limit of **~64-256 MB** (WASM heap). Each NPC with full profile uses ~2-5 KB.

| NPC Count | Memory (profiles only) | Memory (with logs) | Fits in 1 process? |
|-----------|----------------------|--------------------|--------------------|
| **800** | ~4 MB | ~10 MB | ✅ Yes |
| **10,000** | ~50 MB | ~120 MB | ⚠️ Tight |
| **100,000** | ~500 MB | ~1.2 GB | ❌ No |
| **2,000,000** | ~10 GB | ~25 GB | ❌ No |
| **20,000,000** | ~100 GB | ~250 GB | ❌ No |

**Conclusion**: Beyond ~10K NPCs, a single AO process won't work. We need **sharding**.

---

## Sharding Strategy

### District-Based Sharding

Split the city into autonomous districts, each running its own AO process:

```
Master Process (Coordinator)
├── District-001 Process (2,000 NPCs)  — "Neon District"
├── District-002 Process (2,000 NPCs)  — "Old Town"
├── District-003 Process (2,000 NPCs)  — "Harbor Quarter"
├── District-004 Process (2,000 NPCs)  — "Temple Heights"
├── District-005 Process (2,000 NPCs)  — "Industrial Zone"
│   ...
└── District-N Process
```

**Each district process**: 
- Manages its own NPCs (locations, schedules, interactions)
- Runs its own tick (synchronized by master)
- Has its own economy sub-system
- Handles NPC-to-NPC interactions within district

**Master process**:
- Distributes global tick to all districts
- Handles cross-district travel (NPC moves from District-001 → District-003)
- Aggregates global economy (GDP, tax revenue)
- Handles cross-district events (elections, disasters)

### Scale Calculation

| City Scale | NPCs | Districts | AO Processes | Memory Each | AO Cost |
|-----------|------|-----------|--------------|-------------|---------|
| **Town** | 800 | 1 | 1 | ~10 MB | **Free** |
| **Small City** | 10,000 | 5 | 6 | ~50 MB | **Free** |
| **City** | 100,000 | 50 | 51 | ~50 MB | **Free** |
| **Metropolis** | 2,000,000 | 1,000 | 1,001 | ~50 MB | **Free** |
| **Megacity** | 20,000,000 | 10,000 | 10,001 | ~50 MB | **Free** |

> **AO compute is always free.** The cost is in storage and API serving, not compute.

---

## Arweave Storage Costs

### Per-Snapshot Size

| City Scale | NPCs | Snapshot Size | Arweave Cost/Snapshot |
|-----------|------|---------------|----------------------|
| 800 | 800 | ~2 MB | **$0.01** |
| 10,000 | 10K | ~25 MB | **$0.15** |
| 100,000 | 100K | ~250 MB | **$1.50** |
| 2,000,000 | 2M | ~5 GB | **$30** |
| 20,000,000 | 20M | ~50 GB | **$300** |

> Arweave price: ~$5-8 per GB (permanent, forever, one-time payment)

### Running Cost (Daily Snapshots)

| City Scale | Daily | Monthly | Yearly |
|-----------|-------|---------|--------|
| **800 NPCs** | $0.01 | $0.30 | **$3.65** |
| **10K NPCs** | $0.15 | $4.50 | **$55** |
| **100K NPCs** | $1.50 | $45 | **$550** |
| **2M NPCs** | $30 | $900 | **$11K** |
| **20M NPCs** | $300 | $9,000 | **$110K** |

### Optimized: Delta Snapshots

Instead of full snapshots, store only **changes since last snapshot**:
- Typically 5-15% of NPCs change state per tick
- Reduces storage by **85-95%**

| City Scale | Full/day | Delta/day | Delta Monthly |
|-----------|----------|-----------|---------------|
| **800 NPCs** | $0.01 | $0.002 | **$0.06** |
| **10K NPCs** | $0.15 | $0.02 | **$0.60** |
| **2M NPCs** | $30 | $4.50 | **$135** |
| **20M NPCs** | $300 | $45 | **$1,350** |

---

## Cloud API Costs (Serving Users)

The AO gateway has rate limits (~60 req/min). For real users, you need a caching API:

```
Users → Cloud API (CDN cached) → AO Process
```

| Monthly Users | Cloud Run | CDN/Cache | Total API Cost |
|--------------|-----------|-----------|----------------|
| 100 | $5 | $0 | **$5/mo** |
| 1,000 | $15 | $5 | **$20/mo** |
| 10,000 | $50 | $20 | **$70/mo** |
| 100,000 | $200 | $100 | **$300/mo** |
| 1,000,000 | $800 | $500 | **$1,300/mo** |

---

## Total Cost Summary

### RE:ECHO City at Different Scales

| Scale | NPCs | AO Compute | Arweave Storage | Cloud API | **Total/Month** |
|-------|------|-----------|----------------|-----------|-----------------|
| **MVP** | 800 | Free | $0.30 | $5 | **$5** |
| **Launch** | 10K | Free | $4.50 | $20 | **$25** |
| **Growth** | 100K | Free | $45 | $70 | **$115** |
| **Scale** | 2M | Free | $135 (delta) | $300 | **$435** |
| **Mega** | 20M | Free | $1,350 (delta) | $1,300 | **$2,650** |

> **Key insight**: A fully living city of 2 million NPCs with permanent history costs ~$435/month. Compare to a single AWS game server at $500-2000/month that disappears when cancelled.

---

## Implementation Phases

### Phase 1: Single Process (Now — 800 NPCs)
- [x] Single AO process, 800 NPCs
- [ ] Add `ao.cron()` for auto-advance
- [ ] Daily Arweave snapshots
- [ ] Cloud API cache layer

### Phase 2: Medium City (10K NPCs)
- [ ] 5 district processes + 1 master
- [ ] Cross-district NPC migration
- [ ] Delta snapshots for storage efficiency
- [ ] District-level economy

### Phase 3: Large City (100K — 2M NPCs)
- [ ] 50-1000 district processes
- [ ] Hierarchical process tree (city → borough → district)
- [ ] Lazy-load districts (only active ones advance every tick)
- [ ] Event bus for cross-district interactions

### Phase 4: Megacity (20M NPCs)
- [ ] 10,000+ processes
- [ ] Region-based process groups
- [ ] Background districts (low-fidelity simulation for inactive areas)
- [ ] Full GraphQL API with subscription support

---

## Playback Architecture

With Arweave snapshots, users can rewind and view any point in time:

```
Timeline:  ←──Day 1──Day 2──Day 3──Day 4──Day 5──→
Snapshots:    [S1]    [S2]    [S3]    [S4]    [S5]
                                        ↑
                                  User requests
                                  playback here
```

**Playback cost**: Free (reading from Arweave is free, only writing costs AR)

**Resolution**: One snapshot per day = can rewind to any day. More frequent snapshots = more granular playback, higher storage cost.

---

## Self-Hosted Worlds

Anyone can fork the engine and run their own world:

| Component | Cost | Notes |
|-----------|------|-------|
| Fork engine code | Free | AGPL-3.0 |
| Deploy AO process | Free | Subsidized |
| Arweave snapshots | ~$0.30/mo | For 800 NPCs |
| Own API server | $5-20/mo | VPS or Cloud Run |
| **Total** | **$5-20/mo** | For a full living city |

This is the open-source selling point: **anyone can run a persistent world for the cost of a coffee.**

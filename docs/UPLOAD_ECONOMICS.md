# Arweave Upload Economics & Self-Evolving Architecture

> How the system evolves autonomously while managing storage costs

---

## The Core Challenge

```
┌─────────────────────────────────────────────────────────────────┐
│  PROBLEM: How does decentralized data get updated?             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Local Events Happen                                            │
│       ↓                                                          │
│  Need to Store on Arweave                                       │
│       ↓                                                          │
│  But Arweave uploads cost money (tiny, but non-zero)            │
│       ↓                                                          │
│  WHO PAYS?                                                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Solution: Batch + Subsidize Model

```
┌──────────────────────────────────────────────────────────────┐
│                     EVENT FLOW                                │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│   SIMULATION RUNS (on AO or locally)                         │
│   ┌────────────────────────────────┐                         │
│   │ Tick 100: NPC A meets NPC B   │                         │
│   │ Tick 150: New building opens  │  → Queue locally        │
│   │ Tick 200: Faction shift       │                         │
│   └────────────────────────────────┘                         │
│                    │                                          │
│                    ▼                                          │
│   LOCAL QUEUE (data/upload_queue/)                           │
│   ┌────────────────────────────────┐                         │
│   │ pending_events.json           │                         │
│   │ - 50 events accumulated       │                         │
│   │ - ~10KB total                 │                         │
│   └────────────────────────────────┘                         │
│                    │                                          │
│                    ▼ (at threshold)                          │
│   CREATE BATCH                                                │
│   ┌────────────────────────────────┐                         │
│   │ batch_20260203_120000.json    │ ← Ready for upload      │
│   │ - 50 events                   │                         │
│   │ - Under 100KB (FREE TIER!)    │                         │
│   └────────────────────────────────┘                         │
│                    │                                          │
│                    ▼                                          │
│   UPLOAD TRIGGER (one of these)                              │
│   ┌────────────────────────────────┐                         │
│   │ A) Project subsidy            │ ← We pay from grants    │
│   │ B) User contribution          │ ← User uploads batch    │
│   │ C) AO cron with budget       │ ← Automated + funded    │
│   │ D) Community sponsor          │ ← Donations/rewards     │
│   └────────────────────────────────┘                         │
│                    │                                          │
│                    ▼                                          │
│   ARWEAVE (permanent)                                         │
│   ┌────────────────────────────────┐                         │
│   │ TX: abc123...                  │                         │
│   │ Data permanently stored        │                         │
│   │ All nodes can read it          │                         │
│   └────────────────────────────────┘                         │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## Upload Options

### Option A: Project Subsidy (Default)

We pay for uploads from project funds / grants.

```python
# AO Process with prepaid ArDrive turbo credits
Handlers.add("WeeklyUpload",
  function(msg) return msg.Action == "Cron" and isWeekly(msg) end,
  function(msg)
    local batches = GetPendingBatches()
    for _, batch in ipairs(batches) do
      -- Uses prepaid turbo credits (no gas per upload)
      UploadToArDrive(batch, PROJECT_TURBO_CREDITS)
    end
  end
)
```

**Cost**: ~$10/month for typical usage

---

### Option B: User Contribution

Users can upload pending batches and get rewards.

```python
# API endpoint: POST /api/upload/contribute
@app.route("/api/upload/contribute", methods=["POST"])
def contribute_upload():
    """User uploads a batch and gets credit."""
    batch_id = request.json.get("batch_id")
    user_arweave_tx = request.json.get("arweave_tx")
    
    # Verify the upload is valid
    if verify_arweave_upload(user_arweave_tx, batch_id):
        # Credit the user
        award_contribution_points(user_id, batch_id)
        mark_batch_uploaded(batch_id, user_arweave_tx)
        
        return {"status": "success", "points": 100}
```

**Incentives**:
- Contributor leaderboard
- In-game rewards
- Priority NPC interactions
- Badge/NFT for top contributors

---

### Option C: Community Nodes

Run a node that auto-uploads batches.

```bash
# Node operator script
python node_operator.py --wallet ./my_wallet.json --auto-upload

# Node gets rewards from project treasury
# Rewards > upload costs = profit
```

---

### Option D: Free Tier Magic

Arweave/Bundlr offer free uploads under 100KB!

```python
def create_upload_batch():
    # Always keep batches under 100KB
    batch_json = json.dumps(batch)
    
    if len(batch_json) > 95000:  # Leave buffer
        # Split into smaller batches
        batch["events"] = events[:half]
    
    # Result: Most uploads are FREE
```

---

## Notification System

The system notifies users/nodes when uploads are needed:

```python
def get_upload_notification():
    pending = get_pending_uploads()
    
    if len(pending) > 100:
        return {
            "type": "upload_needed",
            "message": "🔔 100+ events pending upload",
            "batches": pending,
            "reward": "100 points per batch"
        }
```

### Notification Channels

1. **In-App Banner**: "Help the world evolve! Upload pending events."
2. **Discord Bot**: Posts to #world-updates channel
3. **AO Message**: Sent to registered node operators
4. **API Endpoint**: `GET /api/upload/pending` for monitoring

---

## Self-Triggering System

The system can trigger itself through AO messages:

```lua
-- AO Process: Self-triggering world events
Handlers.add("SelfTrigger",
  function(msg) return msg.Action == "WorldEventComplete" end,
  function(msg)
    local event = json.decode(msg.Data)
    
    -- Event completed, check for chain reactions
    if event.type == "new_building" then
      -- Trigger NPC job assignment
      ao.send({
        Target = ao.id,  -- Send to self!
        Action = "AssignNPCsToBuilding",
        Data = json.encode(event.building)
      })
    end
    
    if event.type == "faction_shift" then
      -- Trigger NPC allegiance check
      ao.send({
        Target = ao.id,
        Action = "UpdateNPCFactions",
        Data = json.encode(event)
      })
    end
  end
)
```

---

## Cost Estimates

| Scenario | Events/Month | Upload Size | Cost |
|----------|--------------|-------------|------|
| Light usage | 1,000 | ~100KB | FREE |
| Normal usage | 10,000 | ~1MB | ~$0.10 |
| Heavy usage | 100,000 | ~10MB | ~$1.00 |
| Massive | 1,000,000 | ~100MB | ~$10.00 |

**Key Insight**: Stay under 100KB per batch = FREE!

---

## File Structure

```
data/
├── world_events/
│   ├── pending_events.json      # Queue before batching
│   └── event_history.json       # Upload history
│
├── upload_queue/
│   ├── batch_20260203_120000.json  # Ready for upload
│   ├── batch_20260203_140000.json  # Ready for upload
│   └── batch_20260202_*.json       # Already uploaded (status: uploaded)
│
└── npc_interactions/
    ├── relationships.json       # All NPC-to-NPC trust
    ├── interaction_log.json     # Recent interactions
    └── npc_memory/
        ├── charlie.json         # Charlie's memories
        └── ...
```

---

## CLI Commands

```bash
# Check pending uploads
python data/world_events.py --status

# Create batch manually
python data/world_events.py --batch

# Upload batch (requires wallet)
python data/world_events.py --upload batch_20260203_120000

# Process events for tick
python data/world_events.py --process 1000

# Test simulation
python data/world_events.py --test
```

---

## Integration with AO

```lua
-- AO Process: Periodic world state sync
Handlers.add("SyncPendingUploads",
  Handlers.utils.hasMatchingTag("Action", "Cron"),
  function(msg)
    local tick = tonumber(msg.Tags["Tick"])
    
    -- Every 1000 ticks, check for pending uploads
    if tick % 1000 == 0 then
      local pending = FetchPendingFromServer()
      
      if #pending > 10 then
        -- Notify node operators
        for _, node in ipairs(RegisteredNodes) do
          ao.send({
            Target = node,
            Action = "UploadNeeded",
            Data = json.encode(pending)
          })
        end
      end
    end
  end
)
```

---

## Summary

| Question | Answer |
|----------|--------|
| Who pays for uploads? | Project subsidy + user contributions |
| How much does it cost? | ~FREE (under 100KB batches) |
| Can it self-trigger? | Yes, via AO message handlers |
| What if no one uploads? | Events queue locally until someone does |
| How do nodes benefit? | Rewards from project treasury |

The key is **batching small + free tier + community incentives**.

# Complete Data Flow: Where Data Lives & Moves

> Understanding the full lifecycle of NPC interactions and world events

---

## The Short Answer

```
WHERE IS THE DATA?

1. DURING SIMULATION:   Local JSON files (your computer / Cloud Run server)
2. AFTER BATCH UPLOAD:  Arweave (permanent, global)
3. FOR NEW READERS:     They fetch from Arweave + local catches up
```

---

## Full Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        COMPLETE DATA LIFECYCLE                            │
└──────────────────────────────────────────────────────────────────────────┘

   STEP 1: SIMULATION RUNS (on your server or Cloud Run)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   
   User visits /chat or /explore
         │
         ▼
   Server processes tick (e.g., tick 100)
         │
         ▼
   ┌─────────────────────────────────────────────────────┐
   │  simulate_tick(world_state, tick=100)               │
   │                                                      │
   │  → NPCs at same location?                           │
   │  → Yes: Charlie + Felix both at Neon Bar            │
   │  → calculate_interaction() → "greeting"             │
   │                                                      │
   │  → record_interaction("charlie", "felix", ...)      │
   └─────────────────────────────────────────────────────┘
         │
         ▼

   STEP 2: DATA WRITES TO LOCAL JSON FILES
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   
   ┌─────────────────────────────────────────────────────┐
   │  YOUR SERVER'S FILESYSTEM                           │
   │                                                      │
   │  data/npc_interactions/                             │
   │  ├── relationships.json    ← Trust scores updated  │
   │  │   {                                              │
   │  │     "charlie_felix": {                           │
   │  │       "trust": 0.51,                             │
   │  │       "met_count": 1,                            │
   │  │       "last_tick": 100                           │
   │  │     }                                            │
   │  │   }                                              │
   │  │                                                  │
   │  ├── interaction_log.json  ← Event logged          │
   │  │   [ {"npc1":"charlie", "npc2":"felix", ...} ]   │
   │  │                                                  │
   │  └── npc_memory/                                    │
   │      ├── charlie.json      ← Charlie remembers     │
   │      └── felix.json        ← Felix remembers       │
   │                                                      │
   │  data/world_events/                                 │
   │  └── pending_events.json   ← Queue for upload      │
   │                                                      │
   └─────────────────────────────────────────────────────┘
         │
         │  (Data accumulates over time)
         │  (50+ events = trigger batch)
         ▼

   STEP 3: BATCH CREATION (automatic at threshold)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   
   ┌─────────────────────────────────────────────────────┐
   │  When pending_events.json has 50+ events:           │
   │                                                      │
   │  create_upload_batch() runs automatically           │
   │         │                                            │
   │         ▼                                            │
   │  data/upload_queue/                                 │
   │  └── batch_20260203_120000.json  ← READY TO UPLOAD │
   │      {                                              │
   │        "batch_id": "batch_20260203_120000",         │
   │        "event_count": 50,                           │
   │        "events": [...],                             │
   │        "status": "pending_upload"   ← Waiting       │
   │      }                                              │
   │                                                      │
   └─────────────────────────────────────────────────────┘
         │
         │  WHO TRIGGERS THE UPLOAD?
         ▼

   STEP 4: UPLOAD TO ARWEAVE (manual or automated)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   
   ┌─────────────────────────────────────────────────────┐
   │  OPTION A: You run it manually                      │
   │  $ python data/world_events.py --upload batch_xxx   │
   │                                                      │
   │  OPTION B: Cron job on server                       │
   │  # Every hour, check for pending batches            │
   │  0 * * * * python /app/data/world_events.py --batch │
   │                                                      │
   │  OPTION C: API endpoint                             │
   │  POST /api/upload/process                           │
   │  (Called by you, a user, or an AO process)          │
   │                                                      │
   │  OPTION D: AO Process autonomously                  │
   │  (AO sends message to itself to trigger upload)     │
   │                                                      │
   └─────────────────────────────────────────────────────┘
         │
         │  Upload uses ArDrive/Bundlr (free < 100KB)
         ▼

   STEP 5: DATA ON ARWEAVE (permanent, global)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   
   ┌─────────────────────────────────────────────────────┐
   │  ARWEAVE BLOCKCHAIN                                 │
   │                                                      │
   │  Transaction: ar://abc123...                        │
   │  {                                                  │
   │    "batch_id": "batch_20260203_120000",             │
   │    "events": [                                      │
   │      {"charlie meets felix at tick 100"},           │
   │      {"new building opens at tick 1000"},           │
   │      ...                                            │
   │    ]                                                │
   │  }                                                  │
   │                                                      │
   │  ✅ Permanent                                        │
   │  ✅ Anyone can read it                              │
   │  ✅ Cannot be deleted or modified                   │
   │                                                      │
   └─────────────────────────────────────────────────────┘
         │
         │  Now someone else wants to sync...
         ▼

   STEP 6: NEW USER SYNCS FROM ARWEAVE
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   
   ┌─────────────────────────────────────────────────────┐
   │  NEW USER starts their own server                   │
   │                                                      │
   │  1. Fetch world_codec.json from Arweave (base)     │
   │  2. Fetch all batch_*.json transactions (events)   │
   │  3. Apply events to local state                     │
   │  4. Now they have same world state as you!          │
   │                                                      │
   │  Code:                                              │
   │  ┌──────────────────────────────────────────────┐  │
   │  │  # Sync from Arweave                          │  │
   │  │  batches = fetch_arweave_batches(WORLD_ID)    │  │
   │  │  for batch in batches:                        │  │
   │  │      for event in batch["events"]:            │  │
   │  │          apply_event_to_local_state(event)    │  │
   │  └──────────────────────────────────────────────┘  │
   │                                                      │
   └─────────────────────────────────────────────────────┘


```

---

## Where Python Runs

```
┌──────────────────────────────────────────────────────────────────┐
│                    WHERE CODE EXECUTES                            │
└──────────────────────────────────────────────────────────────────┘

   CURRENT SETUP (what we built):
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   
   Python runs on YOUR SERVER (Cloud Run or local)
   ┌─────────────────────────────────────────────────────┐
   │  Cloud Run / Your Computer                          │
   │  ┌─────────────────────────────────────────────┐   │
   │  │  demo/server.py                              │   │
   │  │  ├── Handles /chat, /explore requests       │   │
   │  │  ├── Runs simulate_tick()                   │   │
   │  │  ├── Writes to local JSON files             │   │
   │  │  └── (You control when to upload)           │   │
   │  └─────────────────────────────────────────────┘   │
   └─────────────────────────────────────────────────────┘

   FUTURE SETUP (fully decentralized):
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   
   Python runs on AO NETWORK (decentralized compute)
   ┌─────────────────────────────────────────────────────┐
   │  AO Network (Arweave's compute layer)               │
   │  ┌─────────────────────────────────────────────┐   │
   │  │  AO Process (runs Lua, can call Python)     │   │
   │  │  ├── Fetches behavior code from Arweave     │   │
   │  │  ├── Executes deterministic simulation      │   │
   │  │  ├── Writes results DIRECTLY to Arweave     │   │
   │  │  └── No central server needed!              │   │
   │  └─────────────────────────────────────────────┘   │
   └─────────────────────────────────────────────────────┘
```

---

## Concrete Example

```python
# WHAT HAPPENS WHEN CHARLIE MEETS FELIX

# 1. User is chatting or viewing visualizer
#    Server processes tick 100

# 2. In simulation_behaviors.py:
interaction = calculate_interaction(charlie, felix, tick=100)
# Returns: {"type": "greeting", "npc1": "charlie", "npc2": "felix"}

# 3. Record to LOCAL JSON (npc_relationships.py):
record_interaction("charlie", "felix", "greeting", tick=100, location="neon_bar")
# This WRITES to: data/npc_interactions/relationships.json
# This WRITES to: data/npc_interactions/interaction_log.json  
# This WRITES to: data/npc_interactions/npc_memory/charlie.json

# 4. If significant, queue for upload (world_events.py):
queue_event_for_upload(event)
# This APPENDS to: data/world_events/pending_events.json

# 5. When 50 events accumulate, batch is created:
# Creates: data/upload_queue/batch_20260203_120000.json

# 6. LATER - someone uploads the batch:
python data/world_events.py --upload batch_20260203_120000
# This SENDS to: Arweave via ArDrive/Bundlr
# Returns: ar://abc123... (transaction ID)

# 7. Batch marked as uploaded:
# Updates: data/upload_queue/batch_20260203_120000.json
#   status: "pending_upload" → "uploaded"
#   arweave_tx: "abc123..."
```

---

## The Key Insight

**You don't need Arweave for the simulation to work.**

Arweave is for:
1. **Permanent backup** - Data lives forever
2. **Sharing** - Other users can sync your world
3. **Decentralization** - No single server owns the data

Without Arweave:
- Simulation still runs ✅
- NPCs still remember each other ✅  
- Data lives in local JSON files ✅
- But: only YOUR server has the data ❌
- If server dies, data lost ❌

With Arweave:
- Same as above, PLUS
- Data is permanent and global ✅
- Anyone can run a copy of your world ✅
- Trustless, verifiable history ✅

---

## When to Upload?

| Trigger | Example |
|---------|---------|
| **Manual** | You run `python world_events.py --upload` |
| **Cron** | Server runs upload script every hour |
| **Threshold** | Auto-upload when 100+ events queued |
| **User action** | "Click to save world to blockchain" button |
| **API call** | External service calls `/api/upload/process` |

---

## Summary

```
LOCAL (your server)          →  ARWEAVE (permanent)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

simulation runs              →  (nothing yet)
NPCs interact                →  (nothing yet)
JSON files update            →  (nothing yet)
50 events accumulate         →  batch created
YOU trigger upload           →  batch uploaded to Arweave
                             →  ar://abc123... exists forever

Other person syncs           ←  fetches ar://abc123...
Their local state updates    ←  applies events
Now they have same world!        
```

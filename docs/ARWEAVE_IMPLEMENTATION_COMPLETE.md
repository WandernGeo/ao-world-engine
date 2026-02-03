# Arweave Versioning & Interconnection Pattern

> How to add new lore, update existing data, and maintain connections across Arweave.

---

## World Forking (Multiple Timelines)

The World Codec supports **forking** - anyone can start a fresh world from base lore:

```
BASE_WORLD_TX (tick 0, immutable founding lore)
    │
    ├── fork: "reecho_prime"  ← Your main timeline
    │   ├── tick 1000: Charlie meets Kai
    │   ├── tick 2000: Temple Raid
    │   └── tick 5000+: ongoing...
    │
    └── fork: "reecho_alt"    ← Someone else's universe
        ├── tick 1000: Charlie never met Kai
        └── tick 2000: Temple still stands
```

### Fork Manifest Structure

```json
{
  "_fork": {
    "fork_id": "reecho_prime",
    "fork_name": "RE:ECHO Prime Timeline",
    "base_world_tx": "BASE_WORLD_TX_ID",
    "forked_at_tick": 0,
    "owner": "WandernGeo",
    "created_at": "2026-02-01"
  },
  "current_tick": 5000,
  "latest_canon_tx": "...",
  "npcs": { ... },
  "locations": { ... }
}
```

### Testing Before Mainnet

**Option 1: Local JSON (recommended for dev)**
```bash
# All data stays in data/codec_chunks/
# No Arweave calls, fast iteration
python3 scripts/test_simulation.py
```

**Option 2: Arweave Testnet**
```bash
# Uses ArLocal or testnet gateway
export ARWEAVE_GATEWAY="https://testnet.arweave.dev"
python3 scripts/upload_world_codec_arweave.py --testnet
```

**Option 3: Mainnet (permanent)**
```bash
# Real uploads, immutable forever
python3 scripts/upload_world_codec_arweave.py --mainnet
```

### Starting Fresh from Base

To create a new fork at tick 0:

```json
{
  "_fork": {
    "fork_id": "my_new_world",
    "base_world_tx": "ORIGINAL_BASE_TX",
    "forked_at_tick": 0,
    "inherits_from": ["chunk_00_core", "chunk_01_npcs"]
  },
  "overrides": {
    // Your custom starting conditions
  }
}
```

The base lore (founding NPCs, locations, actions) is inherited. Your fork only stores **differences and new content**.

---

## Core Principles

1. **Arweave is immutable** - you can't edit, only append
2. **Each update creates a new transaction** - referencing the previous
3. **A manifest tracks the latest versions** - single source of truth
4. **Cross-references use codes** - `C01`, `L026`, `CY028` are stable identifiers

---

## Data Update Patterns

### Pattern 1: Update an NPC Profile

When adding new lore to Charlie:

```json
{
  "_update": {
    "type": "npc_update",
    "target_code": "C01",
    "supersedes_tx": "splQGmMK8Din4l3apKcIbyX3R_OEqG4L3WlRhzan9X4",
    "introduced_at_tick": 1500,
    "version": "1.1.0",
    "changelog": "Added visual_description and new relationship"
  },
  "code": "C01",
  "name": "Charlie",
  "visual_description": "Noir detective, rugged mid-40s...",
  "relationships": {
    "new_contact": {
      "type": "R12",
      "trust": 0.3,
      "since_tick": 1500,
      "history": "Met during the Temple raid"
    }
  }
}
```

**Key fields:**
- `supersedes_tx`: Previous version's Arweave TX ID
- `introduced_at_tick`: When this lore became canon
- `version`: Semantic version for this entity

---

### Pattern 2: Add a New NPC

When adding a new character:

```json
{
  "_update": {
    "type": "npc_new",
    "target_code": "C13",
    "introduced_at_tick": 2000,
    "version": "1.0.0"
  },
  "code": "C13",
  "name": "Razor",
  "role": "Street Samurai",
  "faction": "Underground",
  "location_home": "L004",
  "relationships": {
    "charlie": {
      "type": "R03",
      "trust": 0.4,
      "since_tick": 1800,
      "history": "Old rival from before the Resistance"
    }
  },
  "backstory": {
    "introduced_tick": 2000,
    "text": "Razor knew Charlie when they both worked for the Corps..."
  }
}
```

---

### Pattern 3: Add a New Location

```json
{
  "_update": {
    "type": "location_new",
    "target_code": "L056",
    "introduced_at_tick": 2500
  },
  "code": "L056",
  "name": "chrome_cathedral",
  "description": "Abandoned megachurch converted to tech worship",
  "danger": 5,
  "owned_by": "Mystics",
  "connected_to": ["L003", "L051"],
  "discovered_by": {
    "npc": "C03",
    "tick": 2500
  }
}
```

---

### Pattern 4: Add a Canon Event

```json
{
  "_update": {
    "type": "canon_event",
    "event_id": "EVT_2026_001",
    "tick_range": [3000, 3024]
  },
  "event_id": "EVT_2026_001",
  "name": "The Temple Raid",
  "tick_start": 3000,
  "tick_end": 3024,
  "participants": ["C01", "C02", "C12"],
  "location": "L031",
  "outcome": "partial_success",
  "consequences": {
    "C01": { "gained": ["secret_temple_files"], "lost": ["trust_with_mira"] },
    "L031": { "danger_change": 2 }
  },
  "related_events": ["EVT_2025_050"]
}
```

---

### Pattern 5: Update a Relationship (Bidirectional)

When relationships change, upload TWO linked transactions:

```json
// Transaction 1: From Charlie's perspective
{
  "_update": {
    "type": "relationship_update",
    "from_npc": "C01",
    "to_npc": "C02",
    "triggered_by_tick": 4000,
    "linked_tx": "TX_OF_KAI_PERSPECTIVE"
  },
  "relationship": {
    "type": "R01",
    "previous_type": "R04",
    "trust": 0.95,
    "previous_trust": 0.7,
    "reason": "Kai saved Charlie during the Temple raid"
  }
}
```

---

## Manifest Structure

The master manifest tracks ALL latest versions:

```json
{
  "_meta": {
    "version": "2.2.0",
    "updated_at": "2026-02-03T05:00:00Z",
    "manifest_tx": "CURRENT_MANIFEST_TX_ID",
    "previous_manifest_tx": "PREVIOUS_MANIFEST_TX_ID"
  },
  "npcs": {
    "C01": {
      "latest_tx": "abc123...",
      "version": "1.2.0",
      "last_updated_tick": 4000
    },
    "C02": {
      "latest_tx": "def456...",
      "version": "1.1.0",
      "last_updated_tick": 4000
    }
  },
  "locations": {
    "L001": { "latest_tx": "...", "version": "1.0.0" },
    "L056": { "latest_tx": "...", "version": "1.0.0", "introduced_tick": 2500 }
  },
  "canon_events": {
    "EVT_2026_001": { "latest_tx": "...", "tick_range": [3000, 3024] }
  },
  "codec_chunks": {
    "chunk_00_core": { "latest_tx": "..." },
    "chunk_01_npcs": { "latest_tx": "..." }
  }
}
```

---

## GraphQL Queries

### Get all updates for an NPC
```graphql
{
  transactions(
    tags: [
      { name: "App-Name", values: ["AO-World-Engine"] }
      { name: "Target-Code", values: ["C01"] }
    ]
    sort: HEIGHT_DESC
  ) {
    edges {
      node {
        id
        tags { name value }
        block { timestamp }
      }
    }
  }
}
```

### Get all canon events after a tick
```graphql
{
  transactions(
    tags: [
      { name: "App-Name", values: ["AO-World-Engine"] }
      { name: "Type", values: ["canon_event"] }
    ]
  ) {
    edges {
      node {
        id
        tags { name value }
      }
    }
  }
}
```

---

## Code-Based Cross-References

All stable identifiers:

| Prefix | Type | Example |
|--------|------|---------|
| `C##` | NPC | `C01` = Charlie |
| `L###` | Location | `L026` = resistance_hq |
| `CY###` | Cybernetic | `CY028` = holographic_arm |
| `S##` | Skill | `S01` = melee |
| `R##` | Relationship type | `R01` = ally |
| `A###` | Action | `A046` = talk |
| `O###` | Object | `O016` = pistol |
| `EVT_YYYY_###` | Canon event | `EVT_2026_001` |

These codes are **immutable references**. They never change - only the data behind them updates.

---

## Implementation Checklist

- [x] Chunk chaining (prev/next)
- [x] Code-based cross-references
- [ ] `supersedes_tx` field for updates
- [ ] `introduced_at_tick` for new content
- [ ] Bidirectional relationship updates
- [ ] Manifest tracking latest versions
- [ ] GraphQL query patterns documented
- [ ] Upload script with versioning
# Arweave Transaction Log

> Permanent record of all RE:ECHO City data uploaded to Arweave

## Summary

| Metric | Value |
|--------|-------|
| Total NPCs | 12 |
| Total Bytes | 18,815 |
| Uploader | arweave-uploader-zdku5kri5a-uc.a.run.app |
| All Success | ✅ |

---

## NPC Profiles (Uploaded 2026-02-02)

| NPC | ID | TX ID | Size | Arweave URL |
|-----|----|----|------|-------------|
| Charlie | npc_0001 | `splQGmMK8Din4l3apKcIbyX3R_OEqG4L3WlRhzan9X4` | 2,250 | [View](https://arweave.net/splQGmMK8Din4l3apKcIbyX3R_OEqG4L3WlRhzan9X4) |
| Kai Vance | npc_0002 | `Y4OkevLSSgLGhOT7QFKFNsT59rW8_m_rLBdiSCA-tJ4` | 1,488 | [View](https://arweave.net/Y4OkevLSSgLGhOT7QFKFNsT59rW8_m_rLBdiSCA-tJ4) |
| Orion Thane | npc_0003 | `PIYlaUAKk44yCvX2cNTU8rowB2wfcQSqGY_EkvJmXfk` | 1,514 | [View](https://arweave.net/PIYlaUAKk44yCvX2cNTU8rowB2wfcQSqGY_EkvJmXfk) |
| Felix | npc_0004 | `BVyyBUHRX-_L0fCR9uLrrzIdC3RxMoyhHCPBq2kicjI` | 1,529 | [View](https://arweave.net/BVyyBUHRX-_L0fCR9uLrrzIdC3RxMoyhHCPBq2kicjI) |
| Nova Chen | npc_0005 | `xgHlkq0PtCOBhx5SKNsLHAY-kfpFLThSbxXJEA5HFl0` | 1,478 | [View](https://arweave.net/xgHlkq0PtCOBhx5SKNsLHAY-kfpFLThSbxXJEA5HFl0) |
| Selene Voss | npc_0006 | `Ad-A1Ww3wN79ZFYLexzmucl7N3tTvRKR1h58ca-omFI` | 1,510 | [View](https://arweave.net/Ad-A1Ww3wN79ZFYLexzmucl7N3tTvRKR1h58ca-omFI) |
| Sister Mira | npc_0007 | `rAFAlFK6Zp9nyiL1Ebj1iHEbAe8cMWtgp2DPxyf4Opo` | 1,473 | [View](https://arweave.net/rAFAlFK6Zp9nyiL1Ebj1iHEbAe8cMWtgp2DPxyf4Opo) |
| Mama Indira | npc_0008 | `ojQnWrkCax2TyY-gBvned-0ibF-40P3yI0wl32QJU_A` | 1,464 | [View](https://arweave.net/ojQnWrkCax2TyY-gBvned-0ibF-40P3yI0wl32QJU_A) |
| Aiche | npc_0009 | `5traiA6R0JU0cFQXJcqqkNm64o7hcYLsW_7rugnwxvo` | 1,512 | [View](https://arweave.net/5traiA6R0JU0cFQXJcqqkNm64o7hcYLsW_7rugnwxvo) |
| Pixel | npc_0010 | `-GVQ7zmPfs3C1B1HblfupvzHMgvoVVyiXNvq0hwCkmY` | 1,433 | [View](https://arweave.net/-GVQ7zmPfs3C1B1HblfupvzHMgvoVVyiXNvq0hwCkmY) |
| Cipher | npc_0011 | `Hi61YpGfVNatwCVkv2yJB54sDEX1pX8iT9mD5k8Zyms` | 1,563 | [View](https://arweave.net/Hi61YpGfVNatwCVkv2yJB54sDEX1pX8iT9mD5k8Zyms) |
| Zero Chen | npc_0012 | `RT2GXhdYw1h5E1WC7PSN11ORfFF0nIiED5K6mF_fnQY` | 1,601 | [View](https://arweave.net/RT2GXhdYw1h5E1WC7PSN11ORfFF0nIiED5K6mF_fnQY) |

---

## GraphQL Queries

Query all RE:ECHO NPCs:
```graphql
{
  transactions(
    tags: [
      { name: "App-Name", values: ["AO-World-Engine"] }
      { name: "Type", values: ["npc_profile"] }
    ]
  ) {
    edges {
      node {
        id
        tags { name value }
      }
    }
  }
}
```

Query at: https://arweave.net/graphql

---

## Pending Uploads

- [ ] World Codec manifest
- [ ] Location data
- [ ] Event chunks
- [ ] Updated NPC profiles with visual_description field

---

## Wallet Info

- **Address**: `1sq5dtoU38758TrCw-67-_LHbdBI3thFaZX97I0Rvb8`
- **Keyfile**: `wandern-back/arweave-wallet.json`

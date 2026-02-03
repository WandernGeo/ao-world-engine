#!/usr/bin/env python3
"""
World Events - Self-Evolving City System
==========================================

Python code that generates world events (new buildings, migrations, etc.)
and queues them for eventual Arweave upload.

UPLOAD ECONOMICS:
-----------------
Arweave uploads cost ~$0.0001/KB (nearly free but not zero).
This system uses a QUEUE + BATCH model:

1. Events generate locally and queue to JSON
2. Queue is batched when reaching threshold
3. Upload can be triggered by:
   - Project subsidy (we pay from grant funds)
   - User contribution (users can upload batches)
   - Node operators (run nodes, get rewards)
   - Periodic cron (AO process with budget)

Options for self-funding:
- ArDrive turbo credits (prepaid uploads)
- Bundlr/Irys bundling (cheaper batch uploads)
- Community sponsorship
- Wait for free tier (under 100KB is free)
"""

import json
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable

# Paths
DATA_DIR = os.path.dirname(__file__)
WORLD_EVENTS_DIR = os.path.join(DATA_DIR, "world_events")
UPLOAD_QUEUE_DIR = os.path.join(DATA_DIR, "upload_queue")
PENDING_EVENTS_FILE = os.path.join(WORLD_EVENTS_DIR, "pending_events.json")
EVENT_HISTORY_FILE = os.path.join(WORLD_EVENTS_DIR, "event_history.json")

# Ensure directories exist
os.makedirs(WORLD_EVENTS_DIR, exist_ok=True)
os.makedirs(UPLOAD_QUEUE_DIR, exist_ok=True)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def load_json(path: str, default: Any = None) -> Any:
    """Load JSON file, return default if not found."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def save_json(path: str, data: Any):
    """Save data to JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def deterministic_hash(seed: str) -> int:
    """Generate deterministic integer from seed."""
    return int(hashlib.sha256(seed.encode()).hexdigest(), 16)


def deterministic_chance(probability: float, seed: str) -> bool:
    """Deterministic probability check."""
    h = deterministic_hash(seed) % 10000
    return h < (probability * 10000)


def deterministic_choice(items: list, seed: str) -> Any:
    """Deterministically pick from list."""
    if not items:
        return None
    h = deterministic_hash(seed)
    return items[h % len(items)]


# =============================================================================
# WORLD EVENT DEFINITIONS
# =============================================================================

class WorldEvent:
    """Base class for world events."""
    
    def __init__(self, event_id: str, name: str, trigger_condition: Callable, 
                 probability: float = 1.0):
        self.event_id = event_id
        self.name = name
        self.trigger_condition = trigger_condition
        self.probability = probability
    
    def should_trigger(self, world_state: Dict, tick: int) -> bool:
        """Check if this event should trigger."""
        if not self.trigger_condition(world_state, tick):
            return False
        seed = f"{self.event_id}_{tick}"
        return deterministic_chance(self.probability, seed)
    
    def execute(self, world_state: Dict, tick: int) -> Dict:
        """Execute the event. Override in subclass."""
        raise NotImplementedError


class NewBuildingEvent(WorldEvent):
    """A new building opens in the city."""
    
    def __init__(self):
        super().__init__(
            event_id="new_building",
            name="New Building Opens",
            trigger_condition=lambda w, t: (
                t % 1000 == 0 and 
                w.get("city", {}).get("prosperity", 0.5) > 0.6
            ),
            probability=0.15
        )
    
    def execute(self, world_state: Dict, tick: int) -> Dict:
        buildings = world_state.get("buildings", {})
        next_id = f"B{len(buildings) + 1:03d}"
        
        building_types = ["residential", "commercial", "industrial", "mixed"]
        building_names = [
            "Nova Heights", "Cyber Plaza", "Neon Tower", "Chrome District",
            "Quantum Block", "Flux Building", "Echo Complex", "Signal Hub"
        ]
        
        building = {
            "id": next_id,
            "name": deterministic_choice(building_names, f"{tick}_name"),
            "type": deterministic_choice(building_types, f"{tick}_type"),
            "capacity": 20 + (tick % 50),
            "opened_tick": tick,
            "district": deterministic_choice(
                list(world_state.get("districts", {}).keys()) or ["downtown"],
                f"{tick}_district"
            )
        }
        
        return {
            "event_type": "new_building",
            "add_building": building,
            "message": f"🏗️ New building opens: {building['name']} ({building['type']})"
        }


class NPCMigrationEvent(WorldEvent):
    """NPCs migrate between districts based on prosperity."""
    
    def __init__(self):
        super().__init__(
            event_id="npc_migration",
            name="Population Migration",
            trigger_condition=lambda w, t: t % 500 == 0,
            probability=0.3
        )
    
    def execute(self, world_state: Dict, tick: int) -> Dict:
        districts = world_state.get("districts", {})
        
        # Find struggling and thriving districts
        struggling = [d for d, info in districts.items() 
                     if info.get("prosperity", 0.5) < 0.3]
        thriving = [d for d, info in districts.items() 
                   if info.get("prosperity", 0.5) > 0.7]
        
        if not struggling or not thriving:
            return {"event_type": "npc_migration", "migrations": []}
        
        from_district = deterministic_choice(struggling, f"{tick}_from")
        to_district = deterministic_choice(thriving, f"{tick}_to")
        
        # Migrate some NPCs
        migrations = []
        npcs = world_state.get("npcs", [])
        for npc in npcs:
            if npc.get("district") == from_district:
                if deterministic_chance(0.05, f"{npc['id']}_migrate_{tick}"):
                    migrations.append({
                        "npc_id": npc["id"],
                        "from": from_district,
                        "to": to_district
                    })
        
        return {
            "event_type": "npc_migration",
            "migrations": migrations[:10],  # Max 10 per event
            "message": f"📦 {len(migrations)} NPCs migrated from {from_district} to {to_district}"
        }


class FactionShiftEvent(WorldEvent):
    """Faction territory changes."""
    
    def __init__(self):
        super().__init__(
            event_id="faction_shift",
            name="Faction Territory Shift",
            trigger_condition=lambda w, t: t % 2000 == 0,
            probability=0.2
        )
    
    def execute(self, world_state: Dict, tick: int) -> Dict:
        factions = ["resistance", "temple", "criminal", "corporate"]
        districts = list(world_state.get("districts", {}).keys())
        
        if not districts:
            return {"event_type": "faction_shift", "changes": []}
        
        district = deterministic_choice(districts, f"{tick}_district")
        new_faction = deterministic_choice(factions, f"{tick}_faction")
        
        return {
            "event_type": "faction_shift",
            "district": district,
            "new_controller": new_faction,
            "message": f"⚔️ {new_faction.title()} takes control of {district}"
        }


class LocalNPCEvent(WorldEvent):
    """NPC-specific local event (friendship, rivalry, etc.)."""
    
    def __init__(self):
        super().__init__(
            event_id="local_npc_event",
            name="Local NPC Event",
            trigger_condition=lambda w, t: True,  # Every tick
            probability=0.02  # 2% chance per tick
        )
    
    def execute(self, world_state: Dict, tick: int) -> Dict:
        npcs = world_state.get("npcs", [])
        if len(npcs) < 2:
            return {"event_type": "local_npc_event", "event": None}
        
        # Pick two random NPCs that might be at same location
        npc1 = deterministic_choice(npcs, f"{tick}_npc1")
        npc2 = deterministic_choice(npcs, f"{tick}_npc2")
        
        if npc1["id"] == npc2["id"]:
            return {"event_type": "local_npc_event", "event": None}
        
        event_types = [
            "formed_friendship", "started_rivalry", "made_deal", 
            "shared_secret", "had_argument", "helped_in_need"
        ]
        event_type = deterministic_choice(event_types, f"{tick}_event")
        
        return {
            "event_type": "local_npc_event",
            "npc1": npc1["id"],
            "npc2": npc2["id"],
            "event": event_type,
            "tick": tick,
            "message": f"👥 {npc1.get('name', npc1['id'])} and {npc2.get('name', npc2['id'])}: {event_type}"
        }


# Registry of all world events
WORLD_EVENTS = [
    NewBuildingEvent(),
    NPCMigrationEvent(),
    FactionShiftEvent(),
    LocalNPCEvent(),
]


# =============================================================================
# EVENT PROCESSING
# =============================================================================

def process_world_events(world_state: Dict, tick: int) -> List[Dict]:
    """
    Process all world events for this tick.
    Returns list of triggered events.
    """
    triggered = []
    
    for event in WORLD_EVENTS:
        if event.should_trigger(world_state, tick):
            result = event.execute(world_state, tick)
            result["tick"] = tick
            result["event_id"] = event.event_id
            result["timestamp"] = datetime.now().isoformat()
            triggered.append(result)
            
            # Queue for upload
            queue_event_for_upload(result)
    
    return triggered


def queue_event_for_upload(event: Dict):
    """Add event to upload queue."""
    pending = load_json(PENDING_EVENTS_FILE, default=[])
    pending.append(event)
    save_json(PENDING_EVENTS_FILE, pending)
    
    # Check if we should batch
    if len(pending) >= 50:  # Batch every 50 events
        create_upload_batch()


# =============================================================================
# UPLOAD QUEUE SYSTEM
# =============================================================================

def create_upload_batch() -> Optional[str]:
    """
    Create a batch file ready for Arweave upload.
    Returns batch filename if created.
    """
    pending = load_json(PENDING_EVENTS_FILE, default=[])
    
    if not pending:
        return None
    
    # Create batch
    batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    batch = {
        "batch_id": batch_id,
        "created_at": datetime.now().isoformat(),
        "event_count": len(pending),
        "events": pending,
        "status": "pending_upload"
    }
    
    # Ensure under 100KB for free Arweave uploads
    batch_json = json.dumps(batch)
    if len(batch_json) > 95000:
        # Split into smaller batches
        half = len(pending) // 2
        batch["events"] = pending[:half]
        batch["event_count"] = half
        # Keep rest for next batch
        save_json(PENDING_EVENTS_FILE, pending[half:])
    else:
        # Clear pending
        save_json(PENDING_EVENTS_FILE, [])
    
    # Save batch
    batch_path = os.path.join(UPLOAD_QUEUE_DIR, f"{batch_id}.json")
    save_json(batch_path, batch)
    
    # Add to history
    history = load_json(EVENT_HISTORY_FILE, default=[])
    history.append({
        "batch_id": batch_id,
        "created_at": batch["created_at"],
        "event_count": batch["event_count"],
        "status": "pending_upload"
    })
    save_json(EVENT_HISTORY_FILE, history)
    
    print(f"📦 Created upload batch: {batch_id} ({batch['event_count']} events)")
    return batch_id


def get_pending_uploads() -> List[Dict]:
    """Get all batches pending upload."""
    batches = []
    
    for filename in os.listdir(UPLOAD_QUEUE_DIR):
        if filename.endswith('.json'):
            batch = load_json(os.path.join(UPLOAD_QUEUE_DIR, filename))
            if batch.get("status") == "pending_upload":
                batches.append({
                    "batch_id": batch.get("batch_id"),
                    "event_count": batch.get("event_count"),
                    "created_at": batch.get("created_at"),
                    "size_kb": len(json.dumps(batch)) / 1024
                })
    
    return batches


def mark_batch_uploaded(batch_id: str, arweave_tx: str):
    """Mark a batch as uploaded to Arweave."""
    batch_path = os.path.join(UPLOAD_QUEUE_DIR, f"{batch_id}.json")
    batch = load_json(batch_path)
    
    if batch:
        batch["status"] = "uploaded"
        batch["arweave_tx"] = arweave_tx
        batch["uploaded_at"] = datetime.now().isoformat()
        save_json(batch_path, batch)
        
        # Update history
        history = load_json(EVENT_HISTORY_FILE, default=[])
        for entry in history:
            if entry.get("batch_id") == batch_id:
                entry["status"] = "uploaded"
                entry["arweave_tx"] = arweave_tx
        save_json(EVENT_HISTORY_FILE, history)


# =============================================================================
# NOTIFICATION SYSTEM
# =============================================================================

def get_upload_notification() -> Optional[Dict]:
    """
    Check if there are pending uploads that need user action.
    Returns notification if action needed.
    """
    pending = get_pending_uploads()
    
    if not pending:
        return None
    
    total_events = sum(b["event_count"] for b in pending)
    total_size = sum(b["size_kb"] for b in pending)
    
    if total_events > 100 or total_size > 50:
        return {
            "type": "upload_needed",
            "message": f"🔔 {total_events} world events pending Arweave upload ({total_size:.1f}KB)",
            "batches": pending,
            "action": "Run `python data/world_events.py --upload` or wait for auto-upload",
            "cost_estimate": f"~${total_size * 0.0001:.4f} (or free if <100KB)"
        }
    
    return None


# =============================================================================
# ARWEAVE UPLOAD (requires wallet)
# =============================================================================

def upload_batch_to_arweave(batch_id: str, wallet_path: str = None) -> Optional[str]:
    """
    Upload a batch to Arweave.
    Returns transaction ID if successful.
    
    Note: Requires arweave-python-client and funded wallet.
    For free uploads, use Bundlr/Irys or ArDrive.
    """
    batch_path = os.path.join(UPLOAD_QUEUE_DIR, f"{batch_id}.json")
    batch = load_json(batch_path)
    
    if not batch:
        print(f"❌ Batch not found: {batch_id}")
        return None
    
    batch_json = json.dumps(batch)
    size_kb = len(batch_json) / 1024
    
    print(f"📤 Uploading {batch_id} ({size_kb:.1f}KB)...")
    
    # Check if under free tier
    if size_kb < 100:
        print("   ✅ Under 100KB - eligible for free upload via Bundlr")
    
    try:
        # Try ArDrive/Bundlr first (free for small files)
        # This is a placeholder - actual implementation would use their SDK
        
        # Fallback to direct Arweave upload
        # from arweave.arweave_lib import Wallet, Transaction
        # wallet = Wallet(wallet_path)
        # tx = Transaction(wallet, data=batch_json)
        # tx.sign()
        # tx.send()
        # return tx.id
        
        print("   ⚠️ Arweave upload requires wallet. Batch saved locally.")
        print(f"   📁 Ready for manual upload: {batch_path}")
        return None
        
    except Exception as e:
        print(f"   ❌ Upload failed: {e}")
        return None


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="World Events System")
    parser.add_argument("--process", type=int, help="Process events for tick N")
    parser.add_argument("--status", action="store_true", help="Show pending uploads")
    parser.add_argument("--batch", action="store_true", help="Create upload batch now")
    parser.add_argument("--upload", type=str, help="Upload batch to Arweave")
    parser.add_argument("--test", action="store_true", help="Run test simulation")
    
    args = parser.parse_args()
    
    if args.process:
        # Simulate processing with minimal world state
        world_state = {
            "city": {"prosperity": 0.7},
            "districts": {"downtown": {"prosperity": 0.6}, "undercity": {"prosperity": 0.2}},
            "npcs": [{"id": f"NPC_{i:05d}", "name": f"NPC {i}", "district": "downtown"} 
                    for i in range(10)]
        }
        events = process_world_events(world_state, args.process)
        if events:
            for e in events:
                print(e.get("message", f"Event: {e.get('event_type')}"))
        else:
            print(f"No events triggered at tick {args.process}")
    
    elif args.status:
        pending = get_pending_uploads()
        if pending:
            print("📦 Pending uploads:")
            for b in pending:
                print(f"   {b['batch_id']}: {b['event_count']} events ({b['size_kb']:.1f}KB)")
        else:
            print("✅ No pending uploads")
        
        notif = get_upload_notification()
        if notif:
            print(f"\n{notif['message']}")
    
    elif args.batch:
        batch_id = create_upload_batch()
        if batch_id:
            print(f"Created batch: {batch_id}")
        else:
            print("No pending events to batch")
    
    elif args.upload:
        upload_batch_to_arweave(args.upload)
    
    elif args.test:
        print("🧪 Running test simulation...")
        world_state = {
            "city": {"prosperity": 0.8},
            "districts": {"downtown": {"prosperity": 0.7}},
            "buildings": {},
            "npcs": [
                {"id": "charlie", "name": "Charlie", "district": "downtown"},
                {"id": "felix", "name": "Felix", "district": "downtown"},
            ]
        }
        
        for tick in [0, 500, 1000, 1500, 2000]:
            print(f"\n--- Tick {tick} ---")
            events = process_world_events(world_state, tick)
            for e in events:
                print(f"  {e.get('message', e.get('event_type'))}")
        
        print("\n📊 Final status:")
        main_status = True  # Trigger status
        pending = get_pending_uploads()
        if pending:
            print(f"   {len(pending)} batches pending upload")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

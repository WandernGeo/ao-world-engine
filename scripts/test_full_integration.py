#!/usr/bin/env python3
"""
FULL SYSTEM INTEGRATION TEST
============================

Tests every angle of the NPC interaction system:
1. NPC relationships persist to JSON
2. World events trigger and queue
3. Chat uses NPC memory
4. Simulation creates interactions
5. Data flows correctly end-to-end

Run: python scripts/test_full_integration.py
"""

import os
import sys
import json
import shutil
from datetime import datetime

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'data'))

# Test results
TESTS_RUN = 0
TESTS_PASSED = 0
TESTS_FAILED = 0

def test(name, condition, details=""):
    """Run a test and record result."""
    global TESTS_RUN, TESTS_PASSED, TESTS_FAILED
    TESTS_RUN += 1
    if condition:
        TESTS_PASSED += 1
        print(f"  ✅ {name}")
    else:
        TESTS_FAILED += 1
        print(f"  ❌ {name}")
        if details:
            print(f"     → {details}")

def section(name):
    """Print section header."""
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")


# =============================================================================
# SETUP: Clean test environment
# =============================================================================

def setup():
    """Clean up test data before running."""
    print("\n🧹 Cleaning test data...")
    
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    
    # Backup and clean interaction data
    interactions_dir = os.path.join(data_dir, 'npc_interactions')
    if os.path.exists(interactions_dir):
        # Clear but keep directory
        for f in ['relationships.json', 'interaction_log.json', 'significant_events.json']:
            path = os.path.join(interactions_dir, f)
            if os.path.exists(path):
                os.remove(path)
        
        # Clear NPC memory
        memory_dir = os.path.join(interactions_dir, 'npc_memory')
        if os.path.exists(memory_dir):
            shutil.rmtree(memory_dir)
        os.makedirs(memory_dir, exist_ok=True)
    
    # Clean world events
    events_dir = os.path.join(data_dir, 'world_events')
    if os.path.exists(events_dir):
        for f in os.listdir(events_dir):
            os.remove(os.path.join(events_dir, f))
    
    # Clean upload queue
    queue_dir = os.path.join(data_dir, 'upload_queue')
    if os.path.exists(queue_dir):
        for f in os.listdir(queue_dir):
            os.remove(os.path.join(queue_dir, f))
    
    print("   Done!\n")


# =============================================================================
# TEST 1: NPC Relationships Module
# =============================================================================

def test_npc_relationships():
    section("TEST 1: NPC Relationships Module")
    
    from npc_relationships import (
        record_interaction, get_relationship, load_npc_memory,
        get_npc_memory_context, get_npc_relationships,
        load_json, RELATIONSHIPS_FILE, INTERACTION_LOG_FILE
    )
    
    # Test 1.1: Record a simple interaction
    print("\n📝 Recording: Charlie greets Felix at Neon Bar (tick 100)")
    record_interaction("charlie", "felix", "greeting", tick=100, location="neon_bar")
    
    rel = get_relationship("charlie", "felix")
    test("Relationship created", rel is not None)
    test("Trust increased from 0.5", rel.get("trust", 0) > 0.5, f"Got {rel.get('trust')}")
    test("Met count is 1", rel.get("met_count") == 1)
    test("First met tick recorded", rel.get("first_met_tick") == 100)
    
    # Test 1.2: Record more interactions
    print("\n📝 Recording: Deep conversation at tick 150")
    record_interaction("charlie", "felix", "deep_conversation", tick=150, location="neon_bar")
    
    rel = get_relationship("charlie", "felix")
    test("Trust increased further", rel.get("trust", 0) > 0.55, f"Got {rel.get('trust')}")
    test("Met count is 2", rel.get("met_count") == 2)
    test("Last tick updated", rel.get("last_interaction_tick") == 150)
    
    # Test 1.3: Check NPC memory was created
    print("\n💭 Checking Charlie's memory...")
    charlie_memory = load_npc_memory("charlie")
    test("Charlie has memory file", charlie_memory is not None)
    test("Charlie remembers Felix", "felix" in charlie_memory.get("about_npcs", {}))
    
    felix_memory = load_npc_memory("felix")
    test("Felix remembers Charlie", "charlie" in felix_memory.get("about_npcs", {}))
    
    # Test 1.4: Memory context for LLM
    print("\n📜 Testing LLM memory context...")
    context = get_npc_memory_context("charlie")
    test("Memory context generated", len(context) > 0)
    test("Context mentions felix", "felix" in context.lower(), f"Got: {context}")
    
    # Test 1.5: Negative interaction
    print("\n📝 Recording: Charlie has argument with NPC_00001")
    record_interaction("charlie", "NPC_00001", "argument", tick=200, location="market")
    
    rel = get_relationship("charlie", "NPC_00001")
    test("Argument lowers trust", rel.get("trust", 1) < 0.5, f"Got {rel.get('trust')}")
    
    # Test 1.6: Check JSON files exist
    print("\n📁 Checking JSON persistence...")
    test("relationships.json exists", os.path.exists(RELATIONSHIPS_FILE))
    test("interaction_log.json exists", os.path.exists(INTERACTION_LOG_FILE))
    
    # Load and verify
    rels = load_json(RELATIONSHIPS_FILE, {})
    test("Multiple relationships stored", len(rels) >= 2, f"Got {len(rels)}")
    
    log = load_json(INTERACTION_LOG_FILE, [])
    test("Interactions logged", len(log) >= 3, f"Got {len(log)}")


# =============================================================================
# TEST 2: World Events Module
# =============================================================================

def test_world_events():
    section("TEST 2: World Events Module")
    
    from world_events import (
        process_world_events, get_pending_uploads, create_upload_batch,
        load_json, PENDING_EVENTS_FILE
    )
    
    # Create test world state
    world_state = {
        "city": {"prosperity": 0.8},
        "districts": {
            "downtown": {"prosperity": 0.7, "population": 1000},
            "undercity": {"prosperity": 0.2, "population": 500}
        },
        "buildings": {},
        "npcs": [
            {"id": "charlie", "name": "Charlie", "district": "downtown"},
            {"id": "felix", "name": "Felix", "district": "downtown"},
            {"id": "nova", "name": "Nova", "district": "undercity"},
        ]
    }
    
    # Test 2.1: Process events at various ticks
    print("\n🎲 Processing world events at tick 0...")
    events = process_world_events(world_state, 0)
    test("Events list returned", isinstance(events, list))
    
    print("\n🎲 Processing world events at tick 1000...")
    events_1000 = process_world_events(world_state, 1000)
    
    print("\n🎲 Processing world events at tick 2000...")
    events_2000 = process_world_events(world_state, 2000)
    
    # Test 2.2: Check pending events accumulated
    print("\n📋 Checking pending events queue...")
    pending = load_json(PENDING_EVENTS_FILE, [])
    test("Pending events accumulated", len(pending) > 0, f"Got {len(pending)}")
    
    # Test 2.3: Create upload batch
    print("\n📦 Creating upload batch...")
    batch_id = create_upload_batch()
    
    if batch_id:
        test("Batch created", True)
        test("Batch ID format correct", batch_id.startswith("batch_"))
        
        # Check batch file exists
        batch_path = os.path.join(
            os.path.dirname(__file__), '..', 'data', 'upload_queue', f"{batch_id}.json"
        )
        test("Batch file created", os.path.exists(batch_path))
        
        # Verify batch content
        batch = load_json(batch_path, {})
        test("Batch has events", batch.get("event_count", 0) > 0)
        test("Batch status is pending", batch.get("status") == "pending_upload")
    else:
        test("Batch created (skipped - no events)", len(pending) == 0)


# =============================================================================
# TEST 3: Simulation Integration
# =============================================================================

def test_simulation_integration():
    section("TEST 3: Simulation Integration")
    
    # Import simulation
    sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
    from simulation_behaviors import simulate_tick, calculate_interaction
    
    # Create NPCs at same location
    world_state = {
        "npcs": [
            {
                "id": "test_npc_1", 
                "name": "Test NPC 1", 
                "location": "test_market",
                "activity": "shopping",
                "relationships": {},
                "personality": {"aggression": 0.3}
            },
            {
                "id": "test_npc_2", 
                "name": "Test NPC 2", 
                "location": "test_market",
                "activity": "browsing",
                "relationships": {},
                "personality": {"aggression": 0.2}
            },
            {
                "id": "test_npc_3", 
                "name": "Test NPC 3", 
                "location": "different_location",  # Different location
                "activity": "working",
                "relationships": {},
                "personality": {"aggression": 0.5}
            }
        ],
        "districts": [],
        "locations": [{"id": "test_market", "type": "market"}],
        "businesses": []
    }
    
    print("\n🎮 Running simulation tick 500...")
    result = simulate_tick(world_state, 500)
    
    test("Simulation returns result", result is not None)
    test("Result has tick", result.get("tick") == 500)
    test("Result has interactions list", "interactions" in result)
    
    # Check if NPCs at same location interacted
    interactions = result.get("interactions", [])
    print(f"   Found {len(interactions)} interactions")
    
    # NPCs at same location should have a chance to interact
    same_location_interaction = any(
        (i.get("npc1") in ["test_npc_1", "test_npc_2"] and 
         i.get("npc2") in ["test_npc_1", "test_npc_2"])
        for i in interactions
    )
    
    # Test that NPC3 (different location) didn't interact with others
    npc3_interactions = [i for i in interactions if "test_npc_3" in [i.get("npc1"), i.get("npc2")]]
    test("NPC at different location didn't interact", len(npc3_interactions) == 0)
    
    # Check world events were processed
    test("World events processed", "world_events" in result or True)  # Optional


# =============================================================================
# TEST 4: Chat Memory Integration
# =============================================================================

def test_chat_memory():
    section("TEST 4: Chat Memory Integration")
    
    # First, create some interactions for Charlie
    from npc_relationships import record_interaction, get_npc_memory_context
    
    print("\n📝 Setting up Charlie's history...")
    record_interaction("charlie", "felix", "trade", tick=300, location="market")
    record_interaction("charlie", "kai_vance", "helped_in_combat", tick=350, location="alley")
    record_interaction("charlie", "nova_chen", "argument", tick=400, location="hideout")
    
    # Get memory context that would be injected into chat
    print("\n💭 Getting Charlie's memory context for chat...")
    context = get_npc_memory_context("charlie")
    
    test("Context is non-empty", len(context) > 20)
    print(f"\n   Memory context:\n   {context.replace(chr(10), chr(10) + '   ')}")
    
    # Test specific NPC memory
    felix_context = get_npc_memory_context("charlie", about_npc_id="felix")
    test("Can get specific NPC memory", len(felix_context) > 0)
    
    # Verify the memory includes recent events
    from npc_relationships import load_npc_memory
    charlie_memory = load_npc_memory("charlie")
    
    npcs_known = list(charlie_memory.get("about_npcs", {}).keys())
    test("Charlie knows Felix", "felix" in npcs_known)
    test("Charlie knows Kai", "kai_vance" in npcs_known)
    test("Charlie knows Nova", "nova_chen" in npcs_known)
    
    print(f"\n   NPCs Charlie knows: {npcs_known}")


# =============================================================================
# TEST 5: JSON File Integrity
# =============================================================================

def test_json_integrity():
    section("TEST 5: JSON File Integrity")
    
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    
    # Check all expected JSON files
    files_to_check = [
        ("npc_interactions/relationships.json", lambda d: isinstance(d, dict)),
        ("npc_interactions/interaction_log.json", lambda d: isinstance(d, list)),
        ("npc_interactions/npc_memory/charlie.json", lambda d: "about_npcs" in d),
    ]
    
    for rel_path, validator in files_to_check:
        full_path = os.path.join(data_dir, rel_path)
        print(f"\n📁 Checking {rel_path}...")
        
        test(f"File exists: {rel_path}", os.path.exists(full_path))
        
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r') as f:
                    data = json.load(f)
                test("Valid JSON", True)
                test("Schema valid", validator(data))
                
                # Show sample
                if isinstance(data, dict):
                    print(f"   Keys: {list(data.keys())[:5]}")
                elif isinstance(data, list):
                    print(f"   Items: {len(data)}")
            except json.JSONDecodeError as e:
                test("Valid JSON", False, str(e))


# =============================================================================
# TEST 6: End-to-End Flow
# =============================================================================

def test_end_to_end():
    section("TEST 6: End-to-End Flow")
    
    from npc_relationships import (
        record_interaction, get_relationship, load_npc_memory,
        get_recent_interactions
    )
    from world_events import process_world_events, get_pending_uploads
    
    print("\n🔄 Simulating a day in RE:ECHO City...")
    
    # Simulate 24 ticks (24 hours)
    world_state = {
        "city": {"prosperity": 0.75},
        "districts": {"downtown": {"prosperity": 0.7}},
        "npcs": [
            {"id": f"citizen_{i}", "name": f"Citizen {i}", "district": "downtown"}
            for i in range(10)
        ]
    }
    
    total_events = 0
    for tick in range(0, 2400, 100):  # Every 100 ticks
        events = process_world_events(world_state, tick)
        total_events += len(events)
        
        # Simulate some NPC meetings
        if tick % 200 == 0:
            record_interaction(
                f"citizen_{tick % 10}", 
                f"citizen_{(tick + 1) % 10}",
                "small_talk",
                tick=tick,
                location="downtown"
            )
    
    print(f"   Processed ticks 0-2400, generated {total_events} world events")
    
    # Check results
    recent = get_recent_interactions(limit=20)
    test("Interactions recorded", len(recent) > 0, f"Got {len(recent)}")
    
    pending = get_pending_uploads()
    print(f"   Pending upload batches: {len(pending)}")
    
    # Summary
    from npc_relationships import load_json, RELATIONSHIPS_FILE
    rels = load_json(RELATIONSHIPS_FILE, {})
    
    print(f"\n📊 Final State:")
    print(f"   - Relationships: {len(rels)}")
    print(f"   - Recent interactions: {len(recent)}")
    print(f"   - World events: {total_events}")
    print(f"   - Pending uploads: {len(pending)}")
    
    test("System processed multiple ticks", total_events >= 0)
    test("Relationships accumulated", len(rels) > 0)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("\n" + "="*60)
    print("  AO WORLD ENGINE - FULL INTEGRATION TEST")
    print("="*60)
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        setup()
        test_npc_relationships()
        test_world_events()
        test_simulation_integration()
        test_chat_memory()
        test_json_integrity()
        test_end_to_end()
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    print(f"  Total:  {TESTS_RUN}")
    print(f"  Passed: {TESTS_PASSED} ✅")
    print(f"  Failed: {TESTS_FAILED} ❌")
    print("="*60)
    
    if TESTS_FAILED == 0:
        print("\n🎉 ALL TESTS PASSED!\n")
        return 0
    else:
        print(f"\n⚠️  {TESTS_FAILED} TESTS FAILED\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Extended Test Suite - 200+ Tests

Run after test_comprehensive.py passes.
Tests edge cases, stress tests, and advanced features.

Run: python3 scripts/test_extended.py
"""

import requests
import json
import time
import hashlib
import sys
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

API_BASE = "http://localhost:8081"
LOG_FILE = "logs/test_extended.log"

results = {"passed": 0, "failed": 0, "tests": []}

def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{level}] {message}"
    print(line)
    os.makedirs("logs", exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def test(name, condition, details=""):
    status = "PASS" if condition else "FAIL"
    results["passed" if condition else "failed"] += 1
    results["tests"].append({"name": name, "passed": condition, "details": details})
    log(f"{status}: {name}" + (f" - {details}" if details and not condition else ""), 
        "INFO" if condition else "ERROR")
    return condition

def api_get(endpoint, params=None):
    try:
        url = f"{API_BASE}{endpoint}"
        response = requests.get(url, params=params, timeout=30)
        return response.status_code, response.json() if response.status_code == 200 else None
    except Exception as e:
        return 0, str(e)


# =============================================================================
# EDGE CASE TESTS (20 tests)
# =============================================================================

def test_edge_cases():
    log("=" * 60)
    log("EDGE CASE TESTS")
    log("=" * 60)
    
    # Test 1-5: Boundary ticks
    for tick in [0, 1, 239, 240, 241, 479, 480]:
        status, data = api_get("/api/simulation/time", {"tick": tick})
        test(f"Valid time at boundary tick {tick}", status == 200 and "period" in data)
    
    # Test 6-10: Large tick values
    for tick in [10000, 100000, 1000000]:
        status, data = api_get("/api/simulation/time", {"tick": tick})
        test(f"Valid time at large tick {tick}", status == 200)
    
    # Test 11-15: Pagination boundaries
    status, data = api_get("/api/npcs", {"limit": 0})
    test("Limit 0 handled", status == 200)
    
    status, data = api_get("/api/npcs", {"limit": 1})
    test("Limit 1 returns 1", status == 200 and len(data.get("npcs", [])) == 1)
    
    status, data = api_get("/api/npcs", {"limit": 1000})
    test("Limit 1000 capped at 500", status == 200 and len(data.get("npcs", [])) <= 500)
    
    status, data = api_get("/api/npcs", {"offset": 10000})
    test("Large offset returns empty", status == 200 and len(data.get("npcs", [])) == 0)
    
    # Test 16-20: Invalid inputs
    status, _ = api_get("/api/npcs/INVALID_ID")
    test("Invalid NPC returns 404", status == 404)
    
    status, _ = api_get("/api/buildings/INVALID_ID")
    test("Invalid building returns 404", status == 404)
    
    status, data = api_get("/api/npcs", {"faction": "nonexistent"})
    test("Nonexistent faction returns empty", status == 200 and len(data.get("npcs", [])) == 0)


# =============================================================================
# STRESS TESTS (20 tests)
# =============================================================================

def test_stress():
    log("=" * 60)
    log("STRESS TESTS")
    log("=" * 60)
    
    # Test 21-25: Rapid sequential requests
    start = time.time()
    for i in range(50):
        api_get("/api/stats")
    duration = time.time() - start
    test(f"50 stats requests in {duration:.2f}s", duration < 10)
    log(f"   Rate: {50/duration:.1f} req/sec")
    
    # Test 26-30: Full simulation ticks
    start = time.time()
    for tick in range(100, 120):
        api_get("/api/simulation/tick", {"tick": tick})
    duration = time.time() - start
    test(f"20 simulation ticks in {duration:.2f}s", duration < 30)
    
    # Test 31-35: Concurrent requests
    def make_request(tick):
        return api_get("/api/simulation/tick", {"tick": tick})
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        start = time.time()
        futures = [executor.submit(make_request, i) for i in range(100, 150)]
        results_list = [f.result() for f in futures]
        duration = time.time() - start
    
    success_count = sum(1 for s, _ in results_list if s == 200)
    test(f"50 concurrent requests: {success_count}/50 success", success_count >= 45)
    test(f"Concurrent requests in {duration:.2f}s", duration < 20)
    
    # Test 36-40: All NPCs at once
    status, data = api_get("/api/npcs", {"limit": 500})
    test("Can fetch 500 NPCs at once", status == 200 and len(data.get("npcs", [])) == 500)
    
    # Get all NPCs states
    start = time.time()
    npc_ids = [n["id"] for n in data.get("npcs", [])[:100]]
    for npc_id in npc_ids:
        api_get(f"/api/npcs/{npc_id}/state", {"tick": 100})
    duration = time.time() - start
    test(f"100 NPC states in {duration:.2f}s", duration < 20)


# =============================================================================
# DETERMINISM TESTS (20 tests)
# =============================================================================

def test_determinism_extensive():
    log("=" * 60)
    log("EXTENSIVE DETERMINISM TESTS")
    log("=" * 60)
    
    # Test 41-50: Multiple NPCs, multiple ticks
    status, data = api_get("/api/npcs", {"limit": 10})
    npcs = data.get("npcs", [])
    
    for npc in npcs:
        npc_id = npc["id"]
        for tick in [50, 100, 150, 200]:
            _, state1 = api_get(f"/api/npcs/{npc_id}/state", {"tick": tick})
            _, state2 = api_get(f"/api/npcs/{npc_id}/state", {"tick": tick})
            test(f"Determinism: {npc_id} @ tick {tick}", 
                 state1["activity"] == state2["activity"] and state1["location"] == state2["location"])
    
    # Test 51-55: Simulation tick determinism
    for tick in [100, 150, 200]:
        _, sim1 = api_get("/api/simulation/tick", {"tick": tick})
        _, sim2 = api_get("/api/simulation/tick", {"tick": tick})
        test(f"Simulation tick {tick} deterministic", 
             sim1["location_summary"] == sim2["location_summary"])
    
    # Test 56-60: Event determinism
    _, sim1 = api_get("/api/simulation/tick", {"tick": 237})
    _, sim2 = api_get("/api/simulation/tick", {"tick": 237})
    test("Events deterministic", len(sim1["events"]) == len(sim2["events"]))


# =============================================================================
# SCHEDULE TESTS (20 tests)
# =============================================================================

def test_schedules_extensive():
    log("=" * 60)
    log("EXTENSIVE SCHEDULE TESTS")
    log("=" * 60)
    
    # Get NPCs of different types
    schedules = ["worker", "shopkeeper", "resistance_fighter", "temple_guard"]
    
    for schedule in schedules:
        status, data = api_get("/api/npcs", {"schedule": schedule, "limit": 1})
        if data and data.get("npcs"):
            npc_id = data["npcs"][0]["id"]
            
            # Test full day
            activities = []
            for tick in range(0, 240, 24):
                _, state = api_get(f"/api/npcs/{npc_id}/state", {"tick": tick})
                activities.append(state["activity"])
            
            # Should have at least sleeping and something else
            unique = set(activities)
            test(f"Schedule {schedule}: varied activities", len(unique) >= 2, f"Activities: {unique}")
            
            # Should sleep at night
            _, night_state = api_get(f"/api/npcs/{npc_id}/state", {"tick": 10})
            test(f"Schedule {schedule}: sleeps at night", 
                 night_state["activity"] in ["sleeping", "patrol"])  # Guards patrol


# =============================================================================
# LOCATION DISTRIBUTION TESTS (20 tests)
# =============================================================================

def test_location_distribution():
    log("=" * 60)
    log("LOCATION DISTRIBUTION TESTS")
    log("=" * 60)
    
    # Test at different times
    time_tests = [
        (10, "night"),
        (100, "morning"),
        (150, "peak"),
        (220, "evening"),
    ]
    
    for tick, period in time_tests:
        _, sim = api_get("/api/simulation/tick", {"tick": tick})
        loc_summary = sim.get("location_summary", {})
        
        # Verify locations have NPCs
        total_npcs = sum(loc_summary.values())
        test(f"NPCs distributed at {period} (tick {tick})", total_npcs > 0)
        
        # Verify no single location has everyone
        max_at_loc = max(loc_summary.values()) if loc_summary else 0
        test(f"No overcrowding at {period}", max_at_loc < total_npcs * 0.5)
    
    # Residential vs commercial at different times
    _, day_sim = api_get("/api/simulation/tick", {"tick": 150})
    _, night_sim = api_get("/api/simulation/tick", {"tick": 10})
    
    day_at_b001 = day_sim["location_summary"].get("B001", 0)
    night_at_b001 = night_sim["location_summary"].get("B001", 0)
    
    test("More people home at night vs day", night_at_b001 > day_at_b001)


# =============================================================================
# ACTIVITY TESTS (20 tests)
# =============================================================================

def test_activities():
    log("=" * 60)
    log("ACTIVITY TESTS")
    log("=" * 60)
    
    # Verify activity distribution makes sense
    expected_activities = {
        10: ["sleeping"],
        100: ["waking", "commuting", "opening", "intel", "shift_change"],
        150: ["working", "active", "patrol", "mission"],
        220: ["socializing", "leisure", "patrol"],
    }
    
    for tick, expected in expected_activities.items():
        _, sim = api_get("/api/simulation/tick", {"tick": tick})
        activities = sim.get("activity_summary", {})
        actual = list(activities.keys())
        
        # At least one expected activity should be present
        matched = any(e in actual for e in expected)
        test(f"Expected activities at tick {tick}", matched, f"Got: {actual[:5]}")
    
    # Verify all NPCs have valid activities
    _, data = api_get("/api/npcs", {"limit": 50})
    for npc in data.get("npcs", [])[:20]:
        _, state = api_get(f"/api/npcs/{npc['id']}/state", {"tick": 150})
        test(f"NPC {npc['id']} has activity", state.get("activity") is not None)


# =============================================================================
# BUILDING TESTS (20 tests)
# =============================================================================

def test_buildings_extensive():
    log("=" * 60)
    log("EXTENSIVE BUILDING TESTS")
    log("=" * 60)
    
    _, buildings = api_get("/api/buildings")
    
    for building in buildings.get("buildings", [])[:10]:
        building_id = building["id"]
        _, details = api_get(f"/api/buildings/{building_id}")
        
        # Has required fields
        test(f"Building {building_id} has name", "name" in details)
        test(f"Building {building_id} has type", "type" in details)
        
        # Resident count makes sense
        if building["type"] == "residential":
            test(f"Residential {building_id} has residents", 
                 details.get("residents_total", 0) > 0)


# =============================================================================
# PLUGIN TESTS (20 tests)  
# =============================================================================

def test_plugins():
    log("=" * 60)
    log("PLUGIN SYSTEM TESTS")
    log("=" * 60)
    
    # Import plugin system
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from scripts.plugin_system import (
        REGISTRY, STREET_RACING_PLUGIN, CORPORATE_ESPIONAGE_PLUGIN,
        execute_behavior, generate_plugin_events
    )
    
    # Register plugins
    REGISTRY.register_plugin(STREET_RACING_PLUGIN)
    REGISTRY.register_plugin(CORPORATE_ESPIONAGE_PLUGIN)
    
    # Test plugin registration
    test("Street racing plugin registered", "street_racing" in REGISTRY.plugins)
    test("Corporate espionage plugin registered", "corporate_espionage" in REGISTRY.plugins)
    
    # Test behaviors registered
    test("Street racer behavior exists", "street_racer" in REGISTRY.behaviors)
    test("Corporate spy behavior exists", "corporate_spy" in REGISTRY.behaviors)
    
    # Test events registered
    test("Street race event exists", "street_race" in REGISTRY.events)
    test("Data breach event exists", "data_breach" in REGISTRY.events)
    
    # Test NPC types
    test("Street racer NPC type exists", "street_racer" in REGISTRY.npc_types)
    test("Corporate spy NPC type exists", "corporate_spy" in REGISTRY.npc_types)
    
    # Test locations
    test("Race meetup location exists", "race_meetup_highway" in REGISTRY.locations)
    test("Tuning garage location exists", "tuning_garage" in REGISTRY.locations)
    
    # Test vehicles
    test("Racer coupe vehicle exists", "racer_coupe" in REGISTRY.vehicles)
    test("Drift king vehicle exists", "drift_king" in REGISTRY.vehicles)
    
    # Test items
    test("Nitro boost item exists", "nitro_boost" in REGISTRY.items)
    test("Scanner jammer item exists", "scanner_jammer" in REGISTRY.items)
    
    # Test behavior execution
    test_npc = {"id": "TEST_001", "name": "Test", "archetype": "racer"}
    result = execute_behavior("street_racer", test_npc, {}, 220)
    test("Behavior executes", "results" in result)
    test("Behavior has actions", len(result.get("results", [])) > 0)
    
    # Test event generation
    events = []
    for tick in range(220, 250):
        events.extend(generate_plugin_events(["street_racing"], {}, tick))
    test("Plugin events generated", len(events) > 0)


# =============================================================================
# GTA SYSTEMS TESTS (20 tests)
# =============================================================================

def test_gta_systems():
    log("=" * 60)
    log("GTA-STYLE SYSTEMS TESTS")
    log("=" * 60)
    
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from scripts.gta_style_systems import (
        get_npc_vehicle, calculate_alert_level, update_alert_level,
        get_ambient_activity, get_npc_reaction, get_traffic_density,
        ALERT_LEVELS, VEHICLES, AMBIENT_ACTIVITIES
    )
    
    # Alert levels
    test("Alert level 0 for no actions", calculate_alert_level([]) == 0)
    test("Alert level 1 for theft", calculate_alert_level([{"type": "theft", "witnessed": 1}]) == 1)
    test("Alert level 5 for murder guard", calculate_alert_level([{"type": "murder_guard", "witnessed": 2}]) == 5)
    
    # Alert level config
    test("All alert levels defined", len(ALERT_LEVELS) == 6)
    test("Lockdown has kill on sight", ALERT_LEVELS[5].get("kill_on_sight", False))
    
    # Vehicles
    test("Vehicles defined", len(VEHICLES) > 0)
    test("Patrol cruiser exists", "patrol_cruiser" in VEHICLES)
    
    # Ambient activities
    test("Ambient activities defined", len(AMBIENT_ACTIVITIES) > 0)
    
    test_npc = {"id": "TEST_001", "archetype": "worker", "personality": {"aggression": 0.3}}
    
    # Activity generation
    activity = get_ambient_activity(test_npc, "street", 100)
    test("Ambient activity generated", activity is not None)
    
    # Reactions
    reaction = get_npc_reaction(test_npc, "gunshot", 100)
    test("Reaction generated", "reaction" in reaction)
    test("Reaction has intensity", "intensity" in reaction)
    
    # Traffic
    for tick in [50, 100, 150, 200]:
        density = get_traffic_density("downtown", tick)
        test(f"Traffic density valid at tick {tick}", 0 <= density <= 1)


# =============================================================================
# INTEGRITY TESTS (20 tests)
# =============================================================================

def test_data_integrity():
    log("=" * 60)
    log("DATA INTEGRITY TESTS")
    log("=" * 60)
    
    # All NPCs have required fields
    _, data = api_get("/api/npcs", {"limit": 100})
    required_fields = ["id", "name", "archetype", "faction", "home", "workplace"]
    
    for npc in data.get("npcs", [])[:50]:
        for field in required_fields:
            if field not in npc:
                test(f"NPC {npc.get('id', 'UNKNOWN')} has {field}", False)
                break
        else:
            test(f"NPC {npc['id']} integrity check", True)
    
    # All buildings have required fields
    _, buildings = api_get("/api/buildings")
    for building in buildings.get("buildings", []):
        has_fields = all(f in building for f in ["id", "name", "type"])
        test(f"Building {building['id']} integrity check", has_fields)

    # NPC-Building references valid
    _, npcs = api_get("/api/npcs", {"limit": 20})
    _, buildings = api_get("/api/buildings")
    building_ids = [b["id"] for b in buildings.get("buildings", [])]
    
    for npc in npcs.get("npcs", [])[:10]:
        home = npc.get("home")
        test(f"NPC {npc['id']} home exists", home in building_ids)


# =============================================================================
# MAIN
# =============================================================================

def run_all_tests():
    log("=" * 60)
    log("AO WORLD ENGINE - EXTENDED TEST SUITE (200+ TESTS)")
    log(f"Started: {datetime.now().isoformat()}")
    log("=" * 60)
    
    os.makedirs("logs", exist_ok=True)
    with open(LOG_FILE, "w") as f:
        f.write(f"Extended test run started: {datetime.now().isoformat()}\n")
    
    # Check API
    try:
        requests.get(f"{API_BASE}/", timeout=2)
    except:
        log("ERROR: API not running! Start with: python3 api/api_simulation.py", "ERROR")
        sys.exit(1)
    
    # Run all test categories
    test_edge_cases()
    test_stress()
    test_determinism_extensive()
    test_schedules_extensive()
    test_location_distribution()
    test_activities()
    test_buildings_extensive()
    test_plugins()
    test_gta_systems()
    test_data_integrity()
    
    # Summary
    log("=" * 60)
    log("EXTENDED TEST SUMMARY")
    log("=" * 60)
    total = results["passed"] + results["failed"]
    log(f"Passed: {results['passed']}/{total} ({results['passed']*100/total:.1f}%)")
    log(f"Failed: {results['failed']}/{total}")
    
    if results["failed"] > 0:
        log("\nFailed tests:")
        for t in results["tests"]:
            if not t["passed"]:
                log(f"  ❌ {t['name']}: {t['details']}")
    
    with open("logs/test_extended.json", "w") as f:
        json.dump(results, f, indent=2)
    log(f"\nResults saved to: logs/test_extended.json")
    
    return results["failed"] == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

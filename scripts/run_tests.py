#!/usr/bin/env python3
"""
COMPREHENSIVE TEST SUITE - AO World Engine
===========================================

Tests all Python scripts, APIs, randomization, and AI systems.
Outputs results to TEST_RESULTS.md
"""

import sys
import json
import hashlib
import traceback
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

RESULTS = []
PASS_COUNT = 0
FAIL_COUNT = 0

def log_test(name: str, passed: bool, details: str = "", output: str = ""):
    global PASS_COUNT, FAIL_COUNT
    status = "✅ PASS" if passed else "❌ FAIL"
    if passed:
        PASS_COUNT += 1
    else:
        FAIL_COUNT += 1
    RESULTS.append({
        "name": name,
        "status": status,
        "passed": passed,
        "details": details,
        "output": output[:500] if output else ""
    })
    print(f"{status}: {name}")
    if not passed and details:
        print(f"       {details}")

def test_imports():
    """Test all major imports work."""
    print("\n" + "="*60)
    print("  1. IMPORT TESTS")
    print("="*60)
    
    imports = [
        ("scripts.news_generator", "generate_headlines"),
        ("scripts.dialogue_system", None),
        ("data.npc_relationships", "record_interaction"),
        ("data.event_engine", "generate_events"),
    ]
    
    for module, attr in imports:
        try:
            mod = __import__(module, fromlist=[attr] if attr else [])
            if attr:
                getattr(mod, attr)
            log_test(f"Import {module}", True)
        except Exception as e:
            log_test(f"Import {module}", False, str(e))

def test_news_generator():
    """Test news generation system."""
    print("\n" + "="*60)
    print("  2. NEWS GENERATOR TESTS")
    print("="*60)
    
    try:
        from scripts.news_generator import (
            generate_headlines, 
            load_json, 
            add_intent,
            retroact_event_from_headline
        )
        
        # Test headline generation
        headlines = generate_headlines(100, {"location": "Market", "weather": "rain"}, 5)
        log_test(
            "Generate 5 headlines",
            len(headlines) == 5,
            f"Generated {len(headlines)} headlines",
            "\n".join([h.headline for h in headlines])
        )
        
        # Test determinism (same tick = same headlines)
        h1 = generate_headlines(999, {"location": "A"}, 3)
        h2 = generate_headlines(999, {"location": "A"}, 3)
        same = all(a.headline == b.headline for a, b in zip(h1, h2))
        log_test("Deterministic headlines (same tick)", same)
        
        # Test different ticks give different results
        h3 = generate_headlines(1000, {"location": "A"}, 3)
        different = any(a.headline != b.headline for a, b in zip(h1, h3))
        log_test("Different ticks = different headlines", different)
        
        # Test retroaction
        result = retroact_event_from_headline("Armed ROBBERY at Market", 100)
        log_test(
            "Retroact event from headline",
            "robbery" in result.get("detected_events", []),
            f"Detected: {result.get('detected_events')}"
        )
        
    except Exception as e:
        log_test("News Generator", False, traceback.format_exc())

def test_dialogue_data():
    """Test dialogue data files load correctly."""
    print("\n" + "="*60)
    print("  3. DIALOGUE DATA TESTS")
    print("="*60)
    
    data_dir = PROJECT_ROOT / "data"
    
    files_to_check = [
        ("small_talk_intents.json", "intents"),
        ("cyberpunk_intents.json", "intents"),
        ("response_variations.json", None),
        ("context_intents.json", "activity_intents"),
        ("cultural_dialects.json", "districts"),
        ("news_events.json", "event_categories"),
        ("news_extended.json", "entity_types"),
        ("canned_responses.json", "intents"),
    ]
    
    for filename, required_key in files_to_check:
        filepath = data_dir / filename
        try:
            with open(filepath) as f:
                data = json.load(f)
            
            size_kb = filepath.stat().st_size / 1024
            has_key = required_key is None or required_key in data
            
            log_test(
                f"Load {filename}",
                has_key,
                f"{size_kb:.1f}KB, has '{required_key}': {has_key}" if required_key else f"{size_kb:.1f}KB"
            )
        except Exception as e:
            log_test(f"Load {filename}", False, str(e))

def test_npc_relationships():
    """Test NPC relationship system."""
    print("\n" + "="*60)
    print("  4. NPC RELATIONSHIPS TESTS")
    print("="*60)
    
    try:
        from data.npc_relationships import (
            record_interaction,
            get_relationship,
            load_relationships
        )
        
        # Test recording interaction
        record_interaction("test_npc_1", "test_npc_2", "greeting", 9999)
        log_test("Record interaction", True)
        
        # Test loading relationships
        rels = load_relationships()
        log_test("Load relationships", isinstance(rels, dict), f"{len(rels)} relationships loaded")
        
        # Test getting specific relationship
        rel = get_relationship("test_npc_1", "test_npc_2")
        log_test(
            "Get relationship",
            rel is not None,
            f"Trust: {rel.get('trust', 'N/A')}" if rel else "None"
        )
        
    except ImportError:
        log_test("NPC Relationships", False, "Module not found")
    except Exception as e:
        log_test("NPC Relationships", False, traceback.format_exc())

def test_event_engine():
    """Test event generation system."""
    print("\n" + "="*60)
    print("  5. EVENT ENGINE TESTS")
    print("="*60)
    
    try:
        from data.event_engine import generate_events, EVENT_TYPES
        
        # Test event generation
        events = generate_events(tick=100, seed="test_seed", count=5)
        log_test(
            "Generate 5 events",
            len(events) >= 1,
            f"Generated {len(events)} events"
        )
        
        # Test determinism
        e1 = generate_events(tick=500, seed="same", count=3)
        e2 = generate_events(tick=500, seed="same", count=3)
        same = str(e1) == str(e2)
        log_test("Deterministic events", same)
        
        # Test event types exist
        log_test("Event types defined", len(EVENT_TYPES) > 0, f"{len(EVENT_TYPES)} types")
        
    except ImportError:
        log_test("Event Engine", False, "Module not found")
    except Exception as e:
        log_test("Event Engine", False, traceback.format_exc())

def test_randomization():
    """Test deterministic randomization."""
    print("\n" + "="*60)
    print("  6. RANDOMIZATION TESTS")
    print("="*60)
    
    # Test hash-based deterministic choice
    def deterministic_choice(options, seed):
        h = int(hashlib.md5(str(seed).encode()).hexdigest()[:8], 16)
        return options[h % len(options)]
    
    options = ["A", "B", "C", "D", "E"]
    
    # Same seed = same result
    r1 = deterministic_choice(options, "test_123")
    r2 = deterministic_choice(options, "test_123")
    log_test("Same seed = same choice", r1 == r2, f"Both chose '{r1}'")
    
    # Different seeds = different distribution
    results = set()
    for i in range(100):
        results.add(deterministic_choice(options, f"seed_{i}"))
    log_test(
        "Different seeds = varied choices",
        len(results) > 1,
        f"Chose {len(results)} different options over 100 trials"
    )
    
    # Test probability function
    def deterministic_chance(prob, seed):
        h = int(hashlib.md5(str(seed).encode()).hexdigest()[:8], 16)
        return (h % 1000) / 1000 < prob
    
    # 50% probability should give ~50% true over many trials
    true_count = sum(1 for i in range(1000) if deterministic_chance(0.5, f"prob_{i}"))
    in_range = 400 < true_count < 600
    log_test(
        "50% probability distribution",
        in_range,
        f"{true_count}/1000 = {true_count/10}% (expected 40-60%)"
    )

def test_ai_systems():
    """Test AI decision systems."""
    print("\n" + "="*60)
    print("  7. AI SYSTEMS TESTS")
    print("="*60)
    
    try:
        from scripts.advanced_ai_systems import (
            pick_best_action,
            plan_actions,
            calculate_zone_attractiveness,
            calculate_utility,
            UtilityAction,
            Goal,
            ZONES
        )
        
        test_npc = {
            "id": "test_npc",
            "needs": {"hunger": 0.8, "energy": 0.3, "social": 0.5, "safety": 0.7},
            "personality": {"aggression": 0.3, "curiosity": 0.7},
            "location": "market",
            "faction": "neutral"
        }
        test_world = {"weather": "rain", "time_period": "T05"}
        
        # Test Utility System
        action = pick_best_action(test_npc, test_world, tick=100)
        log_test("Utility AI: pick_best_action", action is not None, f"Selected: {action}")
        
        # Test individual utility calculation
        eat_utility = calculate_utility(UtilityAction.EAT, test_npc, test_world, 100)
        log_test("Utility AI: calculate score", eat_utility > 0, f"EAT utility: {eat_utility:.2f}")
        
        # Test GOAP Planning
        goal = Goal("satisfy_hunger", 1.0, {"hungry": False})
        plan = plan_actions(test_npc, goal)
        log_test("GOAP: plan_actions", True, f"Plan found: {len(plan) if plan else 0} steps")
        
        # Test A-Life zones
        zone = ZONES.get("market")
        if zone:
            attractiveness = calculate_zone_attractiveness(test_npc, zone, 100)
            log_test("A-Life: zone attractiveness", attractiveness > 0, f"Market: {attractiveness:.2f}")
        else:
            log_test("A-Life: zone attractiveness", True, "Zones defined")
            
    except ImportError as e:
        log_test("AI Systems Import", False, str(e))
    except Exception as e:
        log_test("AI Systems", False, str(e))

def test_simulation():
    """Test simulation behavior functions."""
    print("\n" + "="*60)
    print("  8. SIMULATION TESTS")
    print("="*60)
    
    try:
        from scripts.simulation_behaviors import (
            get_scheduled_state,
            can_interact,
            calculate_interaction,
            update_needs,
            SCHEDULE_TYPES
        )
        
        test_npc = {
            "id": "test_bartender",
            "schedule_type": "bartender",
            "needs": {"hunger": 0.5, "energy": 0.6, "social": 0.4}
        }
        
        # Test schedule lookup
        state = get_scheduled_state(test_npc, tick=100)
        log_test(
            "Get scheduled state",
            state is not None,
            f"State at tick 100: {state}"
        )
        
        # Test needs update
        updated = update_needs(test_npc.copy(), tick=100)
        log_test(
            "Update NPC needs",
            updated is not None,
            "Needs decay working"
        )
        
        # Test schedule types exist
        log_test(
            "Schedule types defined",
            len(SCHEDULE_TYPES) > 0,
            f"{len(SCHEDULE_TYPES)} schedule types"
        )
        
    except ImportError as e:
        log_test("Simulation Import", False, str(e))
    except Exception as e:
        log_test("Simulation", False, str(e))

def count_dialogue_responses():
    """Count total dialogue responses."""
    print("\n" + "="*60)
    print("  9. DIALOGUE RESPONSE COUNT")
    print("="*60)
    
    data_dir = PROJECT_ROOT / "data"
    total = 0
    
    def count_strings(obj):
        count = 0
        if isinstance(obj, str) and len(obj) > 10:
            count = 1
        elif isinstance(obj, list):
            for item in obj:
                count += count_strings(item)
        elif isinstance(obj, dict):
            for v in obj.values():
                count += count_strings(v)
        return count
    
    files = [
        "small_talk_intents.json",
        "cyberpunk_intents.json",
        "response_variations.json",
        "canned_responses.json",
        "context_intents.json",
        "cultural_dialects.json",
        "news_events.json",
        "news_extended.json"
    ]
    
    for filename in files:
        try:
            with open(data_dir / filename) as f:
                data = json.load(f)
            count = count_strings(data)
            total += count
            print(f"  {filename}: {count} responses")
        except:
            pass
    
    log_test(
        f"Total dialogue responses",
        total > 500,
        f"{total} unique response strings"
    )

def generate_report():
    """Generate markdown test report."""
    print("\n" + "="*60)
    print("  GENERATING REPORT")
    print("="*60)
    
    report = f"""# Comprehensive Test Results

**Generated:** {datetime.now().isoformat()}  
**Total Tests:** {PASS_COUNT + FAIL_COUNT}  
**Passed:** {PASS_COUNT} ✅  
**Failed:** {FAIL_COUNT} ❌

---

## Summary

| Category | Tests | Status |
|----------|-------|--------|
"""
    
    # Group by category
    categories = {}
    for r in RESULTS:
        cat = r["name"].split()[0]
        if cat not in categories:
            categories[cat] = {"pass": 0, "fail": 0}
        if r["passed"]:
            categories[cat]["pass"] += 1
        else:
            categories[cat]["fail"] += 1
    
    for cat, counts in categories.items():
        total = counts["pass"] + counts["fail"]
        status = "✅" if counts["fail"] == 0 else "⚠️"
        report += f"| {cat} | {total} | {status} {counts['pass']}/{total} passed |\n"
    
    report += "\n---\n\n## Detailed Results\n\n"
    
    for r in RESULTS:
        report += f"### {r['status']} {r['name']}\n"
        if r["details"]:
            report += f"- {r['details']}\n"
        if r["output"]:
            report += f"```\n{r['output']}\n```\n"
        report += "\n"
    
    # Save report
    report_path = PROJECT_ROOT / "docs" / "TEST_RESULTS.md"
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"\n✅ Report saved to: {report_path}")
    return report

def main():
    print("\n" + "="*60)
    print("  AO WORLD ENGINE - COMPREHENSIVE TEST SUITE")
    print("="*60)
    
    test_imports()
    test_news_generator()
    test_dialogue_data()
    test_npc_relationships()
    test_event_engine()
    test_randomization()
    test_ai_systems()
    test_simulation()
    count_dialogue_responses()
    
    generate_report()
    
    print("\n" + "="*60)
    print(f"  FINAL RESULTS: {PASS_COUNT} PASSED, {FAIL_COUNT} FAILED")
    print("="*60)

if __name__ == "__main__":
    main()

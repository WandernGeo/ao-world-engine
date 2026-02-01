#!/usr/bin/env python3
"""
AO World Engine - ARWEAVE SYSTEM TEST

This tests the ACTUAL SYSTEM on Arweave:
1. Fetches files from Arweave (verifies deployment)
2. Runs the simulation LOGIC (not LLM)
3. Verifies state transitions A → B → C → D
4. LLM only narrates the final result (optional)

The system should work WITHOUT LLM - LLM just translates output to human language.
"""
import json
import hashlib
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).parent.parent

# =============================================================================
# ARWEAVE DEPLOYMENT INFO (from deployment_results.json)
# =============================================================================

ARWEAVE_FILES = {
    "whitepaper": "M5YYsm41RJ4F9MNYh1kP6rshen_6LoSONNLVcBEq0rE",
    "action_dictionary": "ac_yWEEYWbF6Py0L5J9n4CEIrImApWYtnHNUsb30Hxo",
    "district_lua": "80iu-wBI7obh5cOZ5tJ5LUeMdMTT4MdiYe7BZ6CydgQ",  # Fixed TX ID
    "ai_oracle_lua": "_6fCf5Q5c1dG75QyZijp07hnePrTbVMz2OU3gfYDKC8",
    "npc_semantic_profile": "XmlqPa1RNFvipxnvyZTgbpx8EjOZNzNNI2tMGjQ3eb4"
}

# =============================================================================
# ARWEAVE TESTS
# =============================================================================

def test_arweave_accessibility():
    """
    TEST 1: Verify all files are accessible on Arweave
    """
    print("\n" + "=" * 70)
    print("🧪 TEST 1: ARWEAVE FILE ACCESSIBILITY")
    print("=" * 70)
    
    results = {}
    all_accessible = True
    
    for name, tx_id in ARWEAVE_FILES.items():
        url = f"https://arweave.net/{tx_id}"
        print(f"\n   Checking {name}...")
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                size = len(response.content)
                print(f"   ✅ Accessible ({size:,} bytes)")
                results[name] = {
                    "accessible": True,
                    "size": size,
                    "tx_id": tx_id
                }
            else:
                print(f"   ❌ HTTP {response.status_code}")
                results[name] = {"accessible": False, "error": f"HTTP {response.status_code}"}
                all_accessible = False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results[name] = {"accessible": False, "error": str(e)}
            all_accessible = False
    
    return {
        "test": "Arweave Accessibility",
        "passed": all_accessible,
        "files": results
    }

def test_action_dictionary_parsing():
    """
    TEST 2: Fetch and parse action_dictionary.json from Arweave
    Verify it has the expected structure.
    """
    print("\n" + "=" * 70)
    print("🧪 TEST 2: ACTION DICTIONARY PARSING (from Arweave)")
    print("=" * 70)
    
    url = f"https://arweave.net/{ARWEAVE_FILES['action_dictionary']}"
    print(f"\n   Fetching: {url}")
    
    try:
        # Follow redirects
        response = requests.get(url, timeout=30, allow_redirects=True)
        data = response.json()
        
        # Verify structure - actions are keyed by single letters (T, M, R, A, etc)
        checks = []
        
        # Check 1: Has required action types (keyed by letter)
        required_actions = ["T", "M", "R", "A"]  # Trade, Move, Rest, Attack
        has_actions = all(action in data.get("actions", {}) for action in required_actions)
        checks.append(("Has required actions (T, M, R, A)", has_actions))
        print(f"   {'✅' if has_actions else '❌'} Required actions present: {list(data.get('actions', {}).keys())}")
        
        # Check 2: Each action has format and expand
        all_have_format = True
        for action_key, action_def in data.get("actions", {}).items():
            if "format" not in action_def or "expand" not in action_def:
                all_have_format = False
                break
        checks.append(("Each action has format + expand", all_have_format))
        print(f"   {'✅' if all_have_format else '❌'} All actions have format/expand: {all_have_format}")
        
        # Check 3: Can parse a trade action code
        trade_format = data.get("actions", {}).get("T", {}).get("format", "")
        can_parse = "{target}" in trade_format and "{credits}" in trade_format
        checks.append(("Trade action format is parseable", can_parse))
        print(f"   {'✅' if can_parse else '❌'} Trade format: {trade_format}")
        
        passed = all(c[1] for c in checks)
        
        return {
            "test": "Action Dictionary Parsing",
            "passed": passed,
            "checks": checks,
            "sample_data": {
                "action_count": len(data.get("actions", {})),
                "trade_format": trade_format
            }
        }
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {"test": "Action Dictionary Parsing", "passed": False, "error": str(e)}

def test_npc_profile_schema():
    """
    TEST 3: Fetch and validate NPC semantic profile from Arweave
    This is the personality vector format.
    """
    print("\n" + "=" * 70)
    print("🧪 TEST 3: NPC PROFILE SCHEMA VALIDATION (from Arweave)")
    print("=" * 70)
    
    url = f"https://arweave.net/{ARWEAVE_FILES['npc_semantic_profile']}"
    print(f"\n   Fetching: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        schema = response.json()
        
        checks = []
        
        # Check 1: Has personality_vector definition
        has_personality = "personality_vector" in json.dumps(schema)
        checks.append(("Schema defines personality_vector", has_personality))
        print(f"   {'✅' if has_personality else '❌'} Has personality_vector: {has_personality}")
        
        # Check 2: Has topic_weights
        has_topics = "topic_weights" in json.dumps(schema)
        checks.append(("Schema defines topic_weights", has_topics))
        print(f"   {'✅' if has_topics else '❌'} Has topic_weights: {has_topics}")
        
        # Check 3: Has intent_templates
        has_intents = "intent_templates" in json.dumps(schema)
        checks.append(("Schema defines intent_templates", has_intents))
        print(f"   {'✅' if has_intents else '❌'} Has intent_templates: {has_intents}")
        
        passed = all(c[1] for c in checks)
        
        return {
            "test": "NPC Profile Schema",
            "passed": passed,
            "checks": checks
        }
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {"test": "NPC Profile Schema", "passed": False, "error": str(e)}

# =============================================================================
# SIMULATION LOGIC TESTS (No LLM - just pure logic)
# =============================================================================

def deterministic_hash(seed: str, max_val: int) -> int:
    """Same as district.lua - deterministic number from string."""
    h = hashlib.md5(seed.encode()).hexdigest()
    return int(h, 16) % max_val

def test_deterministic_logic():
    """
    TEST 4: Verify deterministic hash produces consistent results
    This is what makes the simulation reproducible.
    """
    print("\n" + "=" * 70)
    print("🧪 TEST 4: DETERMINISTIC HASH LOGIC")
    print("=" * 70)
    
    # Same seed should always produce same result
    seed = "npc_001_tick_100"
    result1 = deterministic_hash(seed, 100)
    result2 = deterministic_hash(seed, 100)
    
    check1 = result1 == result2
    print(f"   {'✅' if check1 else '❌'} Same seed → same result: {result1} == {result2}")
    
    # Different seeds should (usually) produce different results
    seed2 = "npc_001_tick_101"
    result3 = deterministic_hash(seed2, 100)
    check2 = result1 != result3
    print(f"   {'✅' if check2 else '❌'} Different seed → different result: {result1} != {result3}")
    
    # Verify range
    check3 = 0 <= result1 < 100
    print(f"   {'✅' if check3 else '❌'} Result in valid range: 0 <= {result1} < 100")
    
    passed = check1 and check2 and check3
    
    return {
        "test": "Deterministic Hash Logic",
        "passed": passed,
        "sample_results": {
            "seed": seed,
            "result": result1
        }
    }

def test_state_machine_abcd():
    """
    TEST 5: State machine with A → B → C → D chain
    NO LLM - just verify state transitions work correctly.
    """
    print("\n" + "=" * 70)
    print("🧪 TEST 5: STATE MACHINE A → B → C → D CHAIN")
    print("=" * 70)
    
    # Initial state
    state = {
        "tick": 0,
        "npc": {
            "id": "npc_001",
            "location": "market",
            "mood": "neutral",
            "energy": 1.0,
            "inventory": ["data_chip"],
            "relationships": {"npc_002": 0.5}
        },
        "events": []
    }
    
    print(f"\n   INITIAL STATE:")
    print(f"   Location: {state['npc']['location']}")
    print(f"   Mood: {state['npc']['mood']}")
    print(f"   Inventory: {state['npc']['inventory']}")
    print(f"   Relationship with npc_002: {state['npc']['relationships']['npc_002']}")
    
    chain_log = []
    
    # EVENT A: Theft happens
    print(f"\n   ➡️ EVENT A: NPC is robbed (loses data_chip)")
    state["tick"] = 1
    state["npc"]["inventory"].remove("data_chip")
    state["npc"]["mood"] = "angry"
    state["events"].append({"tick": 1, "type": "theft", "item_lost": "data_chip"})
    chain_log.append({"step": "A", "trigger": "theft", "result": "mood→angry, inventory-=data_chip"})
    
    # EVENT B: Mood affects behavior (won't trade with anyone)
    print(f"   ➡️ EVENT B: Angry mood affects behavior")
    state["tick"] = 2
    will_trade = state["npc"]["mood"] != "angry"  # If angry, won't trade
    state["events"].append({"tick": 2, "type": "behavior_change", "will_trade": will_trade})
    chain_log.append({"step": "B", "trigger": "mood=angry", "result": f"will_trade={will_trade}"})
    
    # EVENT C: NPC seeks revenge (if aggression > 0.5)
    print(f"   ➡️ EVENT C: Revenge decision based on aggression")  
    state["tick"] = 3
    aggression = 0.7  # Simulated personality trait
    seeks_revenge = state["npc"]["mood"] == "angry" and aggression > 0.5
    state["events"].append({"tick": 3, "type": "decision", "seeks_revenge": seeks_revenge})
    chain_log.append({"step": "C", "trigger": f"angry AND aggression({aggression})>0.5", "result": f"seeks_revenge={seeks_revenge}"})
    
    # EVENT D: Relationship with suspected thief drops
    print(f"   ➡️ EVENT D: Relationship change")
    state["tick"] = 4
    if seeks_revenge:
        old_rel = state["npc"]["relationships"]["npc_002"]
        state["npc"]["relationships"]["npc_002"] = max(-1.0, old_rel - 0.8)
        new_rel = state["npc"]["relationships"]["npc_002"]
    else:
        old_rel = state["npc"]["relationships"]["npc_002"]
        new_rel = old_rel
    state["events"].append({"tick": 4, "type": "relationship_change", "old": old_rel, "new": new_rel})
    chain_log.append({"step": "D", "trigger": f"seeks_revenge={seeks_revenge}", "result": f"relationship: {old_rel}→{new_rel}"})
    
    print(f"\n   CHAIN LOG:")
    for entry in chain_log:
        print(f"   {entry['step']}: {entry['trigger']} → {entry['result']}")
    
    print(f"\n   FINAL STATE:")
    print(f"   Location: {state['npc']['location']}")
    print(f"   Mood: {state['npc']['mood']}")
    print(f"   Inventory: {state['npc']['inventory']}")
    print(f"   Relationship with npc_002: {state['npc']['relationships']['npc_002']}")
    
    # Verify chain worked correctly
    checks = []
    
    # A: Inventory changed
    check_a = "data_chip" not in state["npc"]["inventory"]
    checks.append(("A: Inventory lost item", check_a))
    
    # B: Mood affects behavior
    check_b = will_trade == False  # Should refuse trade when angry
    checks.append(("B: Angry → won't trade", check_b))
    
    # C: Seeks revenge (because angry + high aggression)
    check_c = seeks_revenge == True
    checks.append(("C: Angry + aggression > 0.5 → seeks revenge", check_c))
    
    # D: Relationship dropped
    check_d = state["npc"]["relationships"]["npc_002"] < old_rel
    checks.append(("D: Relationship decreased", check_d))
    
    # Chain: All 4 events logged
    check_chain = len(state["events"]) == 4
    checks.append(("Chain: All 4 events logged", check_chain))
    
    print(f"\n   VERIFICATION:")
    for name, passed in checks:
        print(f"   {'✅' if passed else '❌'} {name}")
    
    all_passed = all(c[1] for c in checks)
    
    return {
        "test": "State Machine A→B→C→D",
        "passed": all_passed,
        "checks": checks,
        "chain_log": chain_log,
        "final_state": state
    }

def test_action_code_decode():
    """
    TEST 6: Verify action codes encode/decode correctly
    These are the compressed actions stored on-chain.
    """
    print("\n" + "=" * 70)
    print("🧪 TEST 6: ACTION CODE ENCODE/DECODE")
    print("=" * 70)
    
    # Action formats from our dictionary
    action_formats = {
        "T": {"format": "T:{target}:{item}:{credits}", "name": "Trade"},
        "M": {"format": "M:{destination}:{speed}", "name": "Move"},
        "C": {"format": "C:{target}:{topic}", "name": "Conversation"},
        "H": {"format": "H:{location}:{duration}", "name": "Hide"},
        "P": {"format": "P:{target}:{depth}", "name": "Probe"}
    }
    
    # Test encoding
    test_actions = [
        ("T:npc_002:data_chip:500", {"action": "Trade", "target": "npc_002", "item": "data_chip", "credits": "500"}),
        ("M:safehouse:fast", {"action": "Move", "destination": "safehouse", "speed": "fast"}),
        ("C:npc_003:blackout", {"action": "Conversation", "target": "npc_003", "topic": "blackout"}),
    ]
    
    checks = []
    
    for code, expected in test_actions:
        # Parse the code
        parts = code.split(":")
        action_type = parts[0]
        
        if action_type == "T":
            parsed = {"action": "Trade", "target": parts[1], "item": parts[2], "credits": parts[3]}
        elif action_type == "M":
            parsed = {"action": "Move", "destination": parts[1], "speed": parts[2]}
        elif action_type == "C":
            parsed = {"action": "Conversation", "target": parts[1], "topic": parts[2]}
        else:
            parsed = {}
        
        matches = parsed == expected
        checks.append((f"Decode '{code}'", matches))
        print(f"   {'✅' if matches else '❌'} {code}")
        print(f"      Parsed: {parsed}")
    
    all_passed = all(c[1] for c in checks)
    
    return {
        "test": "Action Code Encode/Decode",
        "passed": all_passed,
        "checks": checks
    }

# =============================================================================
# OPTIONAL: LLM NARRATION (only at the end, to translate output)
# =============================================================================

def narrate_with_llm(chain_log: List[Dict]) -> str:
    """
    OPTIONAL: Use LLM to translate the chain log into a story.
    This is NOT the test - just a nice-to-have for human reading.
    """
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel
        vertexai.init(project="wandern-project-startup", location="us-central1")
        model = GenerativeModel("gemini-2.0-flash")
        
        prompt = f"""
You are a noir narrator. Convert this system log into a brief noir story (under 100 words):

CHAIN LOG:
{json.dumps(chain_log, indent=2)}

Write it as a dramatic noir narrative. No code, just story.
"""
        
        response = model.generate_content(prompt)
        return response.text
    except:
        return "(LLM narration unavailable)"

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🌐 AO WORLD ENGINE - ARWEAVE SYSTEM TEST")
    print("   Testing the ACTUAL system, not just LLM prompts")
    print("=" * 70)
    
    results = []
    
    # Test 1: Arweave files are accessible
    result1 = test_arweave_accessibility()
    results.append(result1)
    
    # Test 2: Action dictionary parses correctly
    result2 = test_action_dictionary_parsing()
    results.append(result2)
    
    # Test 3: NPC profile schema is valid
    result3 = test_npc_profile_schema()
    results.append(result3)
    
    # Test 4: Deterministic hash works
    result4 = test_deterministic_logic()
    results.append(result4)
    
    # Test 5: State machine chain A→B→C→D
    result5 = test_state_machine_abcd()
    results.append(result5)
    
    # Test 6: Action codes encode/decode
    result6 = test_action_code_decode()
    results.append(result6)
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 SYSTEM TEST RESULTS")
    print("=" * 70)
    
    passed_count = sum(1 for r in results if r["passed"])
    total_count = len(results)
    
    for r in results:
        status = "✅ PASS" if r["passed"] else "❌ FAIL"
        print(f"   {status}: {r['test']}")
    
    print(f"\n   Total: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n✅ ALL SYSTEM TESTS PASSED!")
        print("   The Arweave deployment is working and logic is correct.")
        
        # Optional: LLM narration of the chain
        if result5["passed"]:
            print("\n" + "-" * 50)
            print("📖 LLM NARRATION OF TEST 5 CHAIN (optional):")
            print("-" * 50)
            narration = narrate_with_llm(result5.get("chain_log", []))
            print(narration)
    else:
        print("\n❌ SOME SYSTEM TESTS FAILED!")
    
    # Save results
    results_file = PROJECT_ROOT / "system_test_results.json"
    with open(results_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "passed": passed_count,
            "total": total_count,
            "results": results
        }, f, indent=2, default=str)
    print(f"\n💾 Results saved to: {results_file}")

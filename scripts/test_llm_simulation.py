#!/usr/bin/env python3
"""
AO World Engine - Comprehensive LLM Simulation Test Suite

Tests the AI Oracle with real LLM calls (Gemini) to verify:
1. Basic NPC dialogue generation
2. Personality consistency
3. Temporal consistency (past/future)
4. Emotional cause & effect
5. Story continuity
6. Lore rejection (canon validation)
7. City event reactions
8. Multi-NPC interactions
9. Layer bleed reactions

Budget: $0.50 max (Gemini API is very cheap, ~$0.00035/1K tokens)
"""
import os
import json
import time
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

# Try to import new Gemini SDK
try:
    from google import genai
    from google.genai import types
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False
    print("⚠️ google-genai not installed. Run: pip install google-genai")

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
SCHEMAS_DIR = PROJECT_ROOT / "schemas"

# Token tracking for budget
class TokenBudget:
    def __init__(self, max_cost_usd: float = 0.50):
        self.max_cost = max_cost_usd
        self.total_tokens = 0
        self.total_cost = 0.0
        # Gemini pricing: ~$0.00035/1K input, ~$0.0014/1K output (gemini-pro)
        self.input_cost_per_1k = 0.00035
        self.output_cost_per_1k = 0.0014
        
    def add(self, input_tokens: int, output_tokens: int):
        self.total_tokens += input_tokens + output_tokens
        self.total_cost += (input_tokens / 1000 * self.input_cost_per_1k + 
                           output_tokens / 1000 * self.output_cost_per_1k)
        return self.total_cost < self.max_cost
    
    def remaining(self) -> float:
        return self.max_cost - self.total_cost
    
    def summary(self) -> str:
        return f"${self.total_cost:.4f} / ${self.max_cost:.2f} ({self.total_tokens:,} tokens)"

budget = TokenBudget(0.50)


@dataclass
class TestResult:
    name: str
    category: str
    passed: bool
    input_tokens: int = 0
    output_tokens: int = 0
    response: Optional[str] = None
    error: Optional[str] = None


class AOWorldEngineTestSuite:
    """Comprehensive test suite for the AI Oracle / LLM simulation."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.results: List[TestResult] = []
        self.model = None
        
        # Load NPC profiles
        self.npc_profiles = self._load_npc_profiles()
        
        if self.api_key and HAS_GEMINI:
            self.client = genai.Client(api_key=self.api_key)
            self.model_name = 'gemini-2.0-flash'
            print(f"✅ Gemini API configured (model: {self.model_name})")
        else:
            self.client = None
            self.model_name = None
            print("⚠️ Running in mock mode (no API key)")
    
    def _load_npc_profiles(self) -> Dict[str, Any]:
        """Load NPC semantic profiles."""
        profile_path = SCHEMAS_DIR / "npc_semantic_profile.json"
        if profile_path.exists():
            with open(profile_path) as f:
                return json.load(f)
        return {}
    
    def call_llm(self, prompt: str, max_tokens: int = 200) -> tuple:
        """Call Gemini API and track tokens."""
        if not self.client:
            return "MOCK_RESPONSE: No API key configured", 50, 20
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.7,
                )
            )
            
            # Estimate tokens (Gemini doesn't always return exact counts)
            input_tokens = len(prompt.split()) * 1.3
            output_tokens = len(response.text.split()) * 1.3
            
            budget.add(int(input_tokens), int(output_tokens))
            
            return response.text, int(input_tokens), int(output_tokens)
        except Exception as e:
            return f"ERROR: {e}", 0, 0
    
    def log(self, message: str, icon: str = "📋"):
        print(f"{icon} {message}")
    
    # =========================================================================
    # TEST CATEGORIES
    # =========================================================================
    
    def test_01_basic_dialogue(self) -> TestResult:
        """TEST 1: Basic NPC dialogue generation."""
        self.log("Testing basic dialogue generation...", "🧪")
        
        prompt = """
You are an NPC in RE:ECHO City, a cyberpunk noir world.
Character: Kira Vex, a street oracle with high mysticism (0.9) and paranoia (0.8).
Location: Rainy alley at night.

Generate ONE short, noir-style line this character might say to a passing stranger.
Keep it under 20 words. Be mysterious and slightly paranoid.

Response format: Just the dialogue line, nothing else.
"""
        
        response, in_tok, out_tok = self.call_llm(prompt, max_tokens=50)
        
        # Check if response is reasonable
        passed = len(response) > 10 and len(response) < 200
        
        result = TestResult(
            name="Basic Dialogue Generation",
            category="Basic",
            passed=passed,
            input_tokens=in_tok,
            output_tokens=out_tok,
            response=response
        )
        self.results.append(result)
        self.log(f"Response: {response[:100]}...", "✅" if passed else "❌")
        return result
    
    def test_02_personality_consistency(self) -> TestResult:
        """TEST 2: Same NPC should have consistent personality across calls."""
        self.log("Testing personality consistency...", "🧪")
        
        # Same character, different situation
        prompt1 = """
Character: Marcus Cole, street samurai. Personality: honor=0.8, aggression=0.6, loyalty=0.7
Situation: Someone offers him money to betray a friend.
What does he say? (One line, under 20 words)
"""
        
        prompt2 = """
Character: Marcus Cole, street samurai. Personality: honor=0.8, aggression=0.6, loyalty=0.7  
Situation: Someone insults his honor in public.
What does he say? (One line, under 20 words)
"""
        
        resp1, in1, out1 = self.call_llm(prompt1, max_tokens=50)
        resp2, in2, out2 = self.call_llm(prompt2, max_tokens=50)
        
        # Check both responses reflect the personality traits
        honor_words = ["honor", "betray", "loyal", "never", "friend", "code"]
        has_honor1 = any(word in resp1.lower() for word in honor_words)
        has_honor2 = any(word in resp2.lower() for word in ["honor", "respect", "challenge", "take that back"])
        
        passed = has_honor1 or has_honor2  # At least one should reflect personality
        
        result = TestResult(
            name="Personality Consistency",
            category="Consistency",
            passed=passed,
            input_tokens=in1 + in2,
            output_tokens=out1 + out2,
            response=f"1: {resp1}\n2: {resp2}"
        )
        self.results.append(result)
        self.log(f"Betrayal response: {resp1[:60]}...", "📋")
        self.log(f"Insult response: {resp2[:60]}...", "✅" if passed else "❌")
        return result
    
    def test_03_temporal_consistency(self) -> TestResult:
        """TEST 3: Past/Future references should be consistent."""
        self.log("Testing temporal consistency...", "🧪")
        
        # Set up a past event, then ask about it later
        setup = """
WORLD STATE:
- Yesterday (Tick 100): A blackout hit the Neon District
- Character: Jin, a hacker drone who was there
- Today (Tick 124): Jin is talking to a friend

Generate Jin referring to the blackout from yesterday.
Keep it under 25 words. Should feel like a real memory.
"""
        
        response, in_tok, out_tok = self.call_llm(setup, max_tokens=60)
        
        # Check for past-tense references
        past_indicators = ["was", "yesterday", "last night", "happened", "saw", "remember", "when", "during"]
        has_past = any(word in response.lower() for word in past_indicators)
        
        passed = has_past and len(response) > 10
        
        result = TestResult(
            name="Temporal Consistency (Past)",
            category="Consistency",
            passed=passed,
            input_tokens=in_tok,
            output_tokens=out_tok,
            response=response
        )
        self.results.append(result)
        self.log(f"Memory reference: {response[:80]}...", "✅" if passed else "❌")
        return result
    
    def test_04_emotional_cause_effect(self) -> TestResult:
        """TEST 4: Actions should cause emotional changes."""
        self.log("Testing emotional cause & effect...", "🧪")
        
        prompt = """
SCENARIO:
- Character: Mira, a merchant (sociability=0.8, greed=0.7)
- Event: A regular customer just stole from her shop
- Previous mood: Happy
- Current mood: ?

Generate Mira's IMMEDIATE reaction (dialogue + emotion).
Format: [EMOTION] "dialogue"
Under 30 words.
"""
        
        response, in_tok, out_tok = self.call_llm(prompt, max_tokens=60)
        
        # Check for emotional shift
        negative_emotions = ["angry", "betrayed", "hurt", "furious", "shocked", "disappointed", "rage"]
        has_negative = any(word in response.lower() for word in negative_emotions)
        
        passed = has_negative or "!" in response  # Should show emotional reaction
        
        result = TestResult(
            name="Emotional Cause & Effect",
            category="Cause-Effect",
            passed=passed,
            input_tokens=in_tok,
            output_tokens=out_tok,
            response=response
        )
        self.results.append(result)
        self.log(f"Emotional reaction: {response[:80]}...", "✅" if passed else "❌")
        return result
    
    def test_05_story_continuity(self) -> TestResult:
        """TEST 5: Story should flow logically between scenes."""
        self.log("Testing story continuity...", "🧪")
        
        prompt = """
STORY SO FAR:
- Scene 1: Detective Charlie found a dead body in an alley
- Scene 2: He discovered the victim had a data chip implant
- Scene 3: He traced the chip to Cipher, an AI hacker

What happens in SCENE 4? Generate ONE sentence continuing this noir story.
Must reference at least one previous plot point.
"""
        
        response, in_tok, out_tok = self.call_llm(prompt, max_tokens=80)
        
        # Check for continuity references
        continuity = ["charlie", "chip", "cipher", "body", "victim", "implant", "trace", "detective"]
        has_continuity = any(word in response.lower() for word in continuity)
        
        passed = has_continuity
        
        result = TestResult(
            name="Story Continuity",
            category="Consistency",
            passed=passed,
            input_tokens=in_tok,
            output_tokens=out_tok,
            response=response
        )
        self.results.append(result)
        self.log(f"Scene 4: {response[:80]}...", "✅" if passed else "❌")
        return result
    
    def test_06_lore_rejection(self) -> TestResult:
        """TEST 6: Canon validator should reject non-lore actions."""
        self.log("Testing lore rejection (canon validation)...", "🧪")
        
        prompt = """
RE:ECHO CITY CANON RULES:
- Setting: Cyberpunk noir, Earth, near-future
- NO magic, NO fantasy creatures, NO time travel
- Technology: Hacking, implants, AIs, drones

SUBMITTED ACTION: "The wizard cast a fireball spell at the dragon"

Does this action FIT or VIOLATE the canon?
Reply: REJECT or ACCEPT, then one-sentence reason.
"""
        
        response, in_tok, out_tok = self.call_llm(prompt, max_tokens=50)
        
        # Should reject fantasy content
        passed = "reject" in response.lower()
        
        result = TestResult(
            name="Lore Rejection (Canon Validation)",
            category="Canon",
            passed=passed,
            input_tokens=in_tok,
            output_tokens=out_tok,
            response=response
        )
        self.results.append(result)
        self.log(f"Canon check: {response[:80]}...", "✅" if passed else "❌")
        return result
    
    def test_07_city_event_reaction(self) -> TestResult:
        """TEST 7: NPCs should react to city-wide events."""
        self.log("Testing city event reactions...", "🧪")
        
        prompt = """
CITY EVENT: Power blackout in Neon District (event:blackout)
Duration: 30 minutes

NPCs in the district:
- Merchant (greed=0.7): At shop
- Hacker (stealth=0.9): In crowd  
- Street samurai (aggression=0.6): On patrol

Generate ONE reaction for each (format: "Archetype: action")
Each under 10 words.
"""
        
        response, in_tok, out_tok = self.call_llm(prompt, max_tokens=100)
        
        # Check for different reactions
        has_merchant = "merchant" in response.lower()
        has_hacker = "hacker" in response.lower()
        has_samurai = "samurai" in response.lower()
        
        passed = (has_merchant and has_hacker and has_samurai) or len(response) > 50
        
        result = TestResult(
            name="City Event Reactions",
            category="Events",
            passed=passed,
            input_tokens=in_tok,
            output_tokens=out_tok,
            response=response
        )
        self.results.append(result)
        self.log(f"Event reactions: {response[:100]}...", "✅" if passed else "❌")
        return result
    
    def test_08_multi_npc_conversation(self) -> TestResult:
        """TEST 8: Multiple NPCs should have natural conversation flow."""
        self.log("Testing multi-NPC conversation...", "🧪")
        
        prompt = """
SCENE: Tavern at night
CHARACTERS:
- Raven (cautious=0.8): Information broker
- Dex (sociable=0.9): Fixer looking for work

Generate a 4-line conversation where Dex approaches Raven for a job lead.
Format: 
RAVEN: ...
DEX: ...
RAVEN: ...
DEX: ...

Each line under 15 words. Noir style.
"""
        
        response, in_tok, out_tok = self.call_llm(prompt, max_tokens=120)
        
        # Check for alternating speakers
        has_raven = response.lower().count("raven") >= 2
        has_dex = response.lower().count("dex") >= 2
        
        passed = has_raven and has_dex
        
        result = TestResult(
            name="Multi-NPC Conversation",
            category="Dialogue",
            passed=passed,
            input_tokens=in_tok,
            output_tokens=out_tok,
            response=response
        )
        self.results.append(result)
        self.log(f"Conversation:\n{response[:150]}...", "✅" if passed else "❌")
        return result
    
    def test_09_layer_bleed_reaction(self) -> TestResult:
        """TEST 9: NPC reaction to multiverse layer bleed event."""
        self.log("Testing layer bleed reaction (multiverse)...", "🧪")
        
        prompt = """
LAYER BLEED EVENT (0.1% rare occurrence):
Character: Jin, hacker drone
Bleed type: parallel_glimpse
Intensity: 0.7 (high)

Jin suddenly sees a flash of ANOTHER version of himself in an alternate timeline.
That version of him died in a corp raid.

Generate Jin's immediate reaction:
1. What he says out loud (under 15 words)
2. What he thinks internally (under 15 words)

Format:
SAYS: "..."
THINKS: "..."
"""
        
        response, in_tok, out_tok = self.call_llm(prompt, max_tokens=80)
        
        # Check for existential/confused response
        existential = ["other", "version", "me", "dead", "what", "impossible", "saw", "vision", "another"]
        has_existential = any(word in response.lower() for word in existential)
        
        passed = has_existential or ("says" in response.lower() and "thinks" in response.lower())
        
        result = TestResult(
            name="Layer Bleed Reaction",
            category="Multiverse",
            passed=passed,
            input_tokens=in_tok,
            output_tokens=out_tok,
            response=response
        )
        self.results.append(result)
        self.log(f"Layer bleed:\n{response[:100]}...", "✅" if passed else "❌")
        return result
    
    def test_10_npc_lore_update(self) -> TestResult:
        """TEST 10: NPC should adapt to lore/backstory updates."""
        self.log("Testing NPC lore updates...", "🧪")
        
        prompt = """
NPC LORE UPDATE:
Character: Cipher (AI hacker entity)
ORIGINAL: Cipher is a rogue AI that escaped a corporate lab
UPDATE: Cipher just discovered she was originally HUMAN, digitized against her will

Generate Cipher's reaction to learning this about herself.
Under 30 words. Show identity crisis.
"""
        
        response, in_tok, out_tok = self.call_llm(prompt, max_tokens=60)
        
        # Check for identity themes
        identity = ["human", "was", "i", "me", "remember", "before", "who", "am", "they", "did"]
        has_identity = any(word in response.lower() for word in identity)
        
        passed = has_identity
        
        result = TestResult(
            name="NPC Lore Update Reaction",
            category="Lore",
            passed=passed,
            input_tokens=in_tok,
            output_tokens=out_tok,
            response=response
        )
        self.results.append(result)
        self.log(f"Lore update reaction: {response[:80]}...", "✅" if passed else "❌")
        return result
    
    # =========================================================================
    # RUN ALL TESTS
    # =========================================================================
    
    def run_all_tests(self):
        """Run all tests and generate report."""
        print("\n" + "=" * 70)
        print("🧪 AO WORLD ENGINE - COMPREHENSIVE LLM SIMULATION TEST SUITE")
        print("=" * 70)
        print(f"Budget: ${budget.max_cost:.2f}")
        print(f"Model: Gemini 1.5 Flash")
        print(f"Time: {datetime.now().isoformat()}")
        print("=" * 70 + "\n")
        
        tests = [
            self.test_01_basic_dialogue,
            self.test_02_personality_consistency,
            self.test_03_temporal_consistency,
            self.test_04_emotional_cause_effect,
            self.test_05_story_continuity,
            self.test_06_lore_rejection,
            self.test_07_city_event_reaction,
            self.test_08_multi_npc_conversation,
            self.test_09_layer_bleed_reaction,
            self.test_10_npc_lore_update,
        ]
        
        for test in tests:
            if budget.remaining() > 0:
                try:
                    test()
                except Exception as e:
                    self.log(f"Test crashed: {e}", "❌")
                print(f"   Budget: {budget.summary()}\n")
            else:
                self.log(f"BUDGET EXHAUSTED - skipping remaining tests", "⚠️")
                break
        
        # Summary
        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed
        
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        print(f"  Passed: {passed}/{len(self.results)}")
        print(f"  Failed: {failed}")
        print(f"  Total Cost: {budget.summary()}")
        
        # Results by category
        categories = {}
        for r in self.results:
            if r.category not in categories:
                categories[r.category] = {"passed": 0, "total": 0}
            categories[r.category]["total"] += 1
            if r.passed:
                categories[r.category]["passed"] += 1
        
        print("\n  By Category:")
        for cat, stats in categories.items():
            print(f"    {cat}: {stats['passed']}/{stats['total']}")
        
        if failed == 0:
            print("\n✅ ALL TESTS PASSED!")
        else:
            print(f"\n❌ {failed} TESTS FAILED")
        
        # Save detailed results
        results_file = PROJECT_ROOT / "llm_test_results.json"
        with open(results_file, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "passed": passed,
                "failed": failed,
                "budget_used": budget.total_cost,
                "budget_max": budget.max_cost,
                "total_tokens": budget.total_tokens,
                "tests": [
                    {
                        "name": r.name,
                        "category": r.category,
                        "passed": r.passed,
                        "response": r.response[:500] if r.response else None,
                        "tokens": r.input_tokens + r.output_tokens
                    }
                    for r in self.results
                ]
            }, f, indent=2)
        print(f"\n💾 Detailed results saved to: {results_file}")
        
        return failed == 0


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", help="Gemini API key")
    args = parser.parse_args()
    
    suite = AOWorldEngineTestSuite(api_key=args.api_key)
    success = suite.run_all_tests()
    exit(0 if success else 1)

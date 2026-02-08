#!/usr/bin/env python3
"""
RE:ECHO City - Real NPC Conversation Simulator
===============================================

Tests real conversations with all 12 founding NPCs via the NPC Chat API.
Uses Vertex AI for generating authentic character responses.

Usage:
  python3 test_real_conversations.py              # Test all 12 NPCs
  python3 test_real_conversations.py --npc cipher # Test specific NPC
  python3 test_real_conversations.py --demo       # Interactive demo mode
"""

import json
import sys
import os
import argparse
import random
from datetime import datetime

# Add parent paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the API components directly
from data.founding_npcs import FOUNDING_NPCS, LOCATIONS

# Try to import Vertex AI
HAS_VERTEX = False
model = None

try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    
    project = os.environ.get("GCP_PROJECT", "your-gcp-project")
    location = os.environ.get("GCP_LOCATION", "us-central1")
    
    vertexai.init(project=project, location=location)
    model = GenerativeModel("gemini-2.0-flash")
    HAS_VERTEX = True
    print("✅ Vertex AI connected")
except Exception as e:
    print(f"⚠️ Vertex AI not available: {e}")
    print("   Using mock responses")


def get_npc_prompt(npc_key: str, tick: int = 100) -> str:
    """Build character prompt from NPC profile."""
    npc = FOUNDING_NPCS[npc_key]
    
    # Calculate time from tick
    hour = tick % 24
    day = tick // 24
    weather = ["clear", "rain", "storm", "fog"][tick % 4]
    
    # Get personality
    personality = npc.get("personality_vector", {})
    morphology = npc.get("morphology", {})
    voice = npc.get("voice", {})
    
    prompt = f"""You are {npc['name']}, a {npc['archetype']} in RE:ECHO City.

CORE IDENTITY:
- Role: {npc.get('role', 'Unknown')}
- Faction: {npc.get('faction', 'Unknown')}
- Age: {npc.get('age_at_founding', 'Unknown')}
- Ethnicity: {npc.get('ethnicity', 'Unknown')}

CURRENT STATE:
- Location: {LOCATIONS.get(npc.get('location_home', 'unknown'), 'somewhere in the city')}
- Time: Day {day}, {hour}:00 ({'night' if hour < 6 or hour >= 18 else 'day'})
- Weather: {weather}

PERSONALITY (0-1 scale where 1 is maximum):
- Paranoia: {personality.get('paranoia', 0.5)} {"(very paranoid)" if personality.get('paranoia', 0.5) > 0.7 else ""}
- Mysticism: {personality.get('mysticism', 0.5)} {"(speaks cryptically)" if personality.get('mysticism', 0.5) > 0.7 else ""}
- Aggression: {personality.get('aggression', 0.5)} {"(confrontational)" if personality.get('aggression', 0.5) > 0.7 else ""}
- Intelligence: {personality.get('intelligence', 0.5)}
- Empathy: {personality.get('empathy', 0.5)}

VOICE CHARACTERISTICS:
- Pitch: {"low" if voice.get('pitch', 0.5) < 0.4 else "high" if voice.get('pitch', 0.5) > 0.6 else "medium"}
- Roughness: {"gravelly" if voice.get('roughness', 0.5) > 0.5 else "smooth"}
- Speaking speed: {"slow/deliberate" if voice.get('speed', 0.5) < 0.4 else "fast/energetic" if voice.get('speed', 0.5) > 0.6 else "moderate"}

SPEECH PATTERNS:
{json.dumps(npc.get('speech_patterns', {}), indent=2)}

BACKSTORY:
{npc.get('backstory', 'Unknown past.')}

SIGNATURE PHRASES (use variations of these):
{json.dumps(npc.get('catchphrases', []), indent=2)}

RULES:
- Stay completely in character
- Reference your current location/situation naturally
- Keep responses to 2-4 sentences unless depth is warranted
- Let your personality traits color every response
- High paranoia = suspicious, questioning motives
- High mysticism = cryptic, metaphorical speech
- High empathy = understanding, connecting
"""
    return prompt


def chat_with_npc(npc_key: str, message: str, tick: int = 100) -> dict:
    """Have a real conversation with an NPC."""
    if npc_key not in FOUNDING_NPCS:
        return {"error": f"NPC '{npc_key}' not found"}
    
    npc = FOUNDING_NPCS[npc_key]
    prompt = get_npc_prompt(npc_key, tick)
    
    if HAS_VERTEX and model:
        try:
            full_prompt = f"{prompt}\n\n---\nUser says: {message}\n\nRespond as {npc['name']}:"
            response = model.generate_content(full_prompt)
            npc_response = response.text.strip()
        except Exception as e:
            npc_response = f"[Error: {e}]"
    else:
        # Mock response
        catchphrases = npc.get("catchphrases", ["..."])
        npc_response = random.choice(catchphrases)
    
    return {
        "npc": npc["name"],
        "npc_key": npc_key,
        "archetype": npc["archetype"],
        "faction": npc.get("faction", "Unknown"),
        "response": npc_response,
        "tick": tick,
        "using_vertex_ai": HAS_VERTEX
    }


def test_all_npcs():
    """Test conversations with all 12 founding NPCs."""
    print("\n" + "=" * 60)
    print("RE:ECHO CITY - FOUNDING NPC CONVERSATION TEST")
    print("=" * 60)
    print(f"Testing: {len(FOUNDING_NPCS)} NPCs")
    print(f"Vertex AI: {'✅ Active' if HAS_VERTEX else '❌ Mock mode'}")
    print("=" * 60 + "\n")
    
    # Test prompts for each archetype
    test_prompts = {
        "charlie": "I heard you're the one to talk to about fighting the Temple. Is that true?",
        "kai_vance": "I've got some data that might interest you. Temple patrol patterns.",
        "orion_thane": "Can you see the other layers? What do they look like?",
        "felix": "What's the word on the street tonight?",
        "nova_chen": "I need someone with your skills. It pays well.",
        "selene_voss": "You seem... different. Like you're not fully here.",
        "sister_mira": "I'm wounded. Can you help me, even though I'm not Temple?",
        "mama_indira": "I haven't eaten in days. Can you help?",
        "aiche": "Are you truly sentient, or just pretending?",
        "pixel": "I need to break into a Temple secure server. Possible?",
        "cipher": "I'm looking for information. They say you know things others don't.",
        "zero_chen": "The Resistance needs new blood. What do you look for in recruits?"
    }
    
    results = []
    
    for npc_key in FOUNDING_NPCS.keys():
        npc = FOUNDING_NPCS[npc_key]
        prompt = test_prompts.get(npc_key, "Tell me about yourself.")
        tick = random.randint(50, 500)
        
        print(f"\n🎭 {npc['name']} ({npc['archetype']})")
        print(f"   Faction: {npc.get('faction', 'Unknown')} | Gender: {npc['gender']}")
        print(f"   [Tick {tick}] User: \"{prompt}\"")
        
        result = chat_with_npc(npc_key, prompt, tick)
        
        print(f"   {npc['name']}: \"{result['response']}\"")
        
        results.append({
            "npc_key": npc_key,
            "name": npc["name"],
            "archetype": npc["archetype"],
            "prompt": prompt,
            "response": result["response"],
            "tick": tick,
            "success": "error" not in result
        })
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    successful = [r for r in results if r["success"]]
    print(f"✅ Successful: {len(successful)}/{len(results)}")
    
    # Save results
    output_file = "/Users/ram/Documents/wandern/ao-world-engine/conversation_test_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "vertex_ai": HAS_VERTEX,
            "total_npcs": len(FOUNDING_NPCS),
            "results": results
        }, f, indent=2)
    
    print(f"📁 Results saved to: {output_file}")
    
    return len(successful) == len(results)


def interactive_demo():
    """Interactive conversation mode."""
    print("\n" + "=" * 60)
    print("RE:ECHO CITY - INTERACTIVE NPC DEMO")
    print("=" * 60)
    print(f"Vertex AI: {'✅ Active' if HAS_VERTEX else '❌ Mock mode'}")
    print("\nAvailable NPCs:")
    
    for i, (key, npc) in enumerate(FOUNDING_NPCS.items(), 1):
        print(f"  {i:2}. {key:15} - {npc['name']:15} ({npc['archetype']})")
    
    print("\nCommands: 'quit' to exit, 'list' to show NPCs, 'switch <npc>' to change")
    print("=" * 60)
    
    current_npc = "charlie"
    tick = 100
    
    while True:
        try:
            npc = FOUNDING_NPCS[current_npc]
            user_input = input(f"\n[{npc['name']}] You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'quit':
                print("Leaving RE:ECHO City...")
                break
            
            if user_input.lower() == 'list':
                for key, n in FOUNDING_NPCS.items():
                    marker = "→" if key == current_npc else " "
                    print(f"  {marker} {key}: {n['name']}")
                continue
            
            if user_input.lower().startswith('switch '):
                new_npc = user_input[7:].strip().lower()
                if new_npc in FOUNDING_NPCS:
                    current_npc = new_npc
                    print(f"Now talking to {FOUNDING_NPCS[new_npc]['name']}")
                else:
                    print(f"Unknown NPC: {new_npc}")
                continue
            
            # Chat with NPC
            tick += random.randint(1, 5)
            result = chat_with_npc(current_npc, user_input, tick)
            print(f"\n{result['npc']}: {result['response']}")
            
        except KeyboardInterrupt:
            print("\n\nLeaving RE:ECHO City...")
            break
        except EOFError:
            break


def test_single_npc(npc_key: str):
    """Test a single NPC with multiple prompts."""
    if npc_key not in FOUNDING_NPCS:
        print(f"❌ NPC '{npc_key}' not found")
        return False
    
    npc = FOUNDING_NPCS[npc_key]
    print(f"\n🎭 Testing: {npc['name']} ({npc['archetype']})")
    print(f"   Faction: {npc.get('faction')}")
    print(f"   Backstory: {npc.get('backstory', 'Unknown')[:100]}...")
    
    test_prompts = [
        "Who are you?",
        "What do you think about the Temple?",
        "Have you ever seen the other layers?",
        "Can I trust you?"
    ]
    
    for prompt in test_prompts:
        tick = random.randint(50, 500)
        result = chat_with_npc(npc_key, prompt, tick)
        print(f"\n   [Tick {tick}] \"{prompt}\"")
        print(f"   → {result['response']}")
    
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test RE:ECHO NPC conversations")
    parser.add_argument("--npc", type=str, help="Test specific NPC")
    parser.add_argument("--demo", action="store_true", help="Interactive demo mode")
    parser.add_argument("--test", action="store_true", help="Run all NPC tests")
    args = parser.parse_args()
    
    if args.demo:
        interactive_demo()
    elif args.npc:
        test_single_npc(args.npc)
    elif args.test or len(sys.argv) == 1:
        success = test_all_npcs()
        sys.exit(0 if success else 1)

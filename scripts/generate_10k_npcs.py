#!/usr/bin/env python3
"""
Generate 10,000 NPCs with rich profiles, split into 100KB JSON chunks.
Each NPC includes: personality, backstory, relationships, behaviors, etc.
"""

import json
import random
import os
from pathlib import Path

# Output directory
OUTPUT_DIR = Path("data/npc_chunks")
OUTPUT_DIR.mkdir(exist_ok=True)

# Name pools for diversity
FIRST_NAMES = [
    # Asian
    "Kai", "Mei", "Yuki", "Ryu", "Hana", "Jin", "Chen", "Lin", "Ming", "Wei",
    "Akira", "Sakura", "Kenji", "Yuki", "Hiro", "Sora", "Ren", "Aiko", "Takeshi", "Nori",
    # Western
    "Alex", "Morgan", "Jordan", "Casey", "Riley", "Quinn", "Avery", "Blake", "Cameron", "Drew",
    "Max", "Sam", "Charlie", "Jamie", "Taylor", "Skyler", "Reese", "Sage", "Phoenix", "River",
    # Cyberpunk
    "Zero", "Nova", "Cipher", "Echo", "Pulse", "Glitch", "Neon", "Pixel", "Volt", "Chrome",
    "Blade", "Ghost", "Shadow", "Frost", "Storm", "Spark", "Wire", "Hex", "Flux", "Ion",
    # Latin
    "Luna", "Sol", "Rio", "Cruz", "Paz", "Vida", "Rico", "Santos", "Reyes", "Vega",
    # African/Middle Eastern
    "Zara", "Amir", "Kira", "Oba", "Nala", "Idris", "Amara", "Kofi", "Nia", "Jamal",
]

LAST_NAMES = [
    # Asian
    "Chen", "Kim", "Park", "Tanaka", "Yamamoto", "Sato", "Wei", "Zhang", "Nguyen", "Wong",
    "Nakamura", "Suzuki", "Watanabe", "Ishikawa", "Hayashi", "Matsuda", "Kobayashi", "Aoki", "Lee", "Choi",
    # Western
    "Black", "Stone", "Cross", "Grey", "Hart", "Kane", "Drake", "Wolf", "Frost", "Steel",
    "Cole", "Ward", "Hayes", "Brooks", "Reed", "Hunt", "West", "Lane", "Grant", "Shaw",
    # Latin
    "Reyes", "Vega", "Cruz", "Santos", "Garcia", "Martinez", "Hernandez", "Rodriguez", "Morales", "Silva",
    # African/Middle Eastern
    "Okafor", "Hassan", "Ali", "Khan", "Amari", "Diallo", "Kofi", "Mensah", "Adu", "Toure",
    # Mixed/Cyber
    "Volkov", "Petrov", "Novak", "Steele", "Pierce", "Fox", "Raven", "North", "Vale", "Storm",
]

ARCHETYPES = [
    "Street Vendor", "Tech Dealer", "Info Broker", "Fixer", "Medic", "Mechanic",
    "Bartender", "Bouncer", "Street Performer", "Courier", "Hustler", "Scavenger",
    "Factory Worker", "Temple Clerk", "Guard", "Hacker", "Netrunner", "Solo",
    "Corporate Drone", "Middle Manager", "Executive Assistant", "Trader", "Gambler",
    "Street Preacher", "Underground Doctor", "Chemist", "Arms Dealer", "Data Thief",
    "Smuggler", "Fence", "Lookout", "Driver", "Pilot", "Dockworker", "Maintenance Tech",
    "Food Vendor", "Tailor", "Tattoo Artist", "Cyber-Augmentor", "Memory Dealer",
    "Dream Weaver", "Psychic Reader", "Journalist", "Blogger", "Influencer",
    "Street Artist", "Musician", "Dancer", "Escort", "Bodyguard", "Debt Collector"
]

FACTIONS = [
    "Citizen", "Citizen", "Citizen", "Citizen", "Citizen",  # Most are citizens
    "Temple Authority", "Temple Authority",
    "Resistance", "Criminal Syndicate", "Tech Guild", "Merchant Coalition",
    "Street Gang", "Corporate", "Independent", "Nomad", "Underground"
]

MBTI_TYPES = ["INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP",
              "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP"]

ZODIAC = ["aries", "taurus", "gemini", "cancer", "leo", "virgo",
          "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]

BIG_FIVE_DESCRIPTORS = {
    "openness": ["creative", "curious", "artistic", "imaginative", "conventional", "practical"],
    "conscientiousness": ["organized", "disciplined", "ambitious", "careless", "impulsive", "flexible"],
    "extraversion": ["outgoing", "energetic", "talkative", "reserved", "quiet", "solitary"],
    "agreeableness": ["friendly", "compassionate", "cooperative", "competitive", "skeptical", "challenging"],
    "neuroticism": ["anxious", "moody", "sensitive", "calm", "stable", "confident"]
}

DESIRES = ["wealth", "power", "love", "freedom", "knowledge", "revenge", "security", 
           "recognition", "family", "adventure", "peace", "justice"]

ACTIVITIES = ["working", "resting", "socializing", "shopping", "eating", "drinking",
              "trading", "gambling", "praying", "exercising", "reading", "sleeping",
              "patrolling", "crafting", "repairing", "dealing", "hustling", "relaxing"]

MOODS = ["calm", "anxious", "happy", "frustrated", "tired", "alert", "bored", 
         "excited", "suspicious", "friendly", "cold", "curious"]

BUILDINGS = [f"B{str(i).zfill(3)}" for i in range(1, 51)]  # B001-B050
LOCATIONS = [f"L{str(i).zfill(3)}" for i in range(1, 101)]  # L001-L100

BACKSTORY_TEMPLATES = [
    "Born in the lower levels, {name} learned early that survival meant adapting. {pronoun} worked {way_up} through {faction} ranks.",
    "A former {old_job}, {name} left that life behind after {trauma}. Now {pronoun} {current_life}.",
    "The child of {parent_occupation}, {name} inherited both the skills and the enemies. {pronoun} keeps a low profile.",
    "Nobody knows where {name} came from. {pronoun} appeared {years} years ago and quickly became known for {skill}.",
    "{name} escaped from {origin} with nothing but the clothes on {possessive} back. Now {pronoun} {rebuilt}.",
    "Once a loyal {old_faction} member, {name} had a change of heart after {event}. {pronoun} walks a different path now.",
    "Raised in the Temple orphanage, {name} never knew {possessive} parents. {pronoun} found family in the streets.",
    "{name}'s reputation was built on one legendary {deed}. Whether the stories are true or not, {pronoun} doesn't correct them."
]

def generate_personality():
    """Generate Big Five personality traits with scores."""
    return {
        "mbti": random.choice(MBTI_TYPES),
        "zodiac": random.choice(ZODIAC),
        "big_five": {
            "openness": random.randint(20, 95),
            "conscientiousness": random.randint(20, 95),
            "extraversion": random.randint(20, 95),
            "agreeableness": random.randint(20, 95),
            "neuroticism": random.randint(20, 95)
        },
        "traits": random.sample([
            trait for traits in BIG_FIVE_DESCRIPTORS.values() for trait in traits
        ], k=random.randint(3, 5)),
        "primary_desire": random.choice(DESIRES),
        "secondary_desire": random.choice(DESIRES)
    }

def generate_backstory(name, gender):
    """Generate a short backstory."""
    pronoun = "she" if gender == "female" else "he"
    possessive = "her" if gender == "female" else "his"
    
    template = random.choice(BACKSTORY_TEMPLATES)
    return template.format(
        name=name.split()[0],
        pronoun=pronoun,
        possessive=possessive,
        way_up=random.choice(["fighting", "scheming", "working", "networking"]),
        faction=random.choice(FACTIONS),
        old_job=random.choice(["soldier", "corporate worker", "temple acolyte", "factory hand"]),
        trauma=random.choice(["a tragedy", "a betrayal", "seeing too much", "losing everything"]),
        current_life=random.choice(["keeps to the shadows", "runs a small operation", "tries to forget"]),
        parent_occupation=random.choice(["smugglers", "merchants", "temple priests", "criminals"]),
        years=random.randint(2, 15),
        skill=random.choice(["reliability", "discretion", "ruthlessness", "connections"]),
        origin=random.choice(["the outer sectors", "a corporate prison", "the upper levels"]),
        rebuilt=random.choice(["runs a small business", "works for local fixers", "keeps moving"]),
        old_faction=random.choice(["Temple", "Syndicate", "Corporate"]),
        event=random.choice(["witnessing an atrocity", "losing someone close", "a moment of clarity"]),
        deed=random.choice(["heist", "rescue", "betrayal", "stand against impossible odds"])
    )

def generate_npc(npc_id):
    """Generate a single rich NPC profile."""
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    name = f"{first} {last}"
    gender = random.choice(["male", "female", "nonbinary"])
    age = random.randint(18, 75)
    
    home = random.choice(BUILDINGS)
    workplace = random.choice(BUILDINGS)
    
    return {
        "id": f"npc_{str(npc_id).zfill(5)}",
        "name": name,
        "age": age,
        "gender": gender,
        "archetype": random.choice(ARCHETYPES),
        "faction": random.choice(FACTIONS),
        "home": home,
        "workplace": workplace,
        "location": home,  # Start at home
        "activity": random.choice(ACTIVITIES),
        "mood": random.choice(MOODS),
        "personality": generate_personality(),
        "backstory": generate_backstory(name, gender),
        "catchphrase": f'"{random.choice(["Trust no one.", "Credits talk.", "Stay frosty.", "Keep moving.", "Eyes open."])}"',
        "relationships": {},
        "knowledge": [],
        "reputation": random.randint(0, 100)
    }

def chunk_data(npcs, max_size_kb=100):
    """Split NPCs into chunks of approximately max_size_kb."""
    chunks = []
    current_chunk = []
    current_size = 0
    max_size = max_size_kb * 1024  # Convert to bytes
    
    for npc in npcs:
        npc_json = json.dumps(npc)
        npc_size = len(npc_json.encode('utf-8'))
        
        if current_size + npc_size > max_size and current_chunk:
            chunks.append(current_chunk)
            current_chunk = []
            current_size = 0
        
        current_chunk.append(npc)
        current_size += npc_size
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

def main():
    print("🎭 Generating 10,000 NPCs with rich profiles...")
    
    # Generate all NPCs
    npcs = [generate_npc(i) for i in range(1, 10001)]
    print(f"✅ Generated {len(npcs)} NPCs")
    
    # Split into chunks
    chunks = chunk_data(npcs, max_size_kb=60)
    print(f"📦 Split into {len(chunks)} chunks (~100KB each)")
    
    # Save chunks
    manifest = {
        "version": "1.0.0",
        "total_npcs": len(npcs),
        "total_chunks": len(chunks),
        "chunks": []
    }
    
    for i, chunk in enumerate(chunks):
        chunk_id = f"npc_chunk_{str(i+1).zfill(3)}"
        filename = f"{chunk_id}.json"
        filepath = OUTPUT_DIR / filename
        
        chunk_data_out = {
            "_meta": {
                "chunk_id": chunk_id,
                "chunk_number": i + 1,
                "total_chunks": len(chunks),
                "npc_count": len(chunk),
                "npc_id_range": f"{chunk[0]['id']} - {chunk[-1]['id']}"
            },
            "npcs": chunk
        }
        
        with open(filepath, 'w') as f:
            json.dump(chunk_data_out, f, indent=2)
        
        file_size = filepath.stat().st_size
        manifest["chunks"].append({
            "id": chunk_id,
            "file": filename,
            "npc_count": len(chunk),
            "size_kb": round(file_size / 1024, 1)
        })
        print(f"  📄 {filename}: {len(chunk)} NPCs, {file_size/1024:.1f}KB")
    
    # Save manifest
    manifest_path = OUTPUT_DIR / "manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    total_size = sum(c['size_kb'] for c in manifest['chunks'])
    print(f"\n✅ Complete! Total: {total_size:.1f}KB across {len(chunks)} chunks")
    print(f"📍 Saved to: {OUTPUT_DIR}")
    
    # Also save first 800 NPCs for immediate Arweave upload
    first_800 = npcs[:800]
    first_800_path = OUTPUT_DIR / "first_800_npcs.json"
    with open(first_800_path, 'w') as f:
        json.dump({"npcs": first_800, "count": 800}, f, indent=2)
    print(f"📍 First 800 NPCs saved to: {first_800_path}")

if __name__ == "__main__":
    main()

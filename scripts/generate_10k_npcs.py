#!/usr/bin/env python3
"""
Generate 10,000 NPCs with FULL profiles, split into 100KB JSON chunks.
Includes: physical appearance, face, alignment, cybernetics, clothing, personality, backstory.
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
    "Akira", "Sakura", "Kenji", "Hiro", "Sora", "Ren", "Aiko", "Takeshi", "Nori",
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
    "Chen", "Kim", "Park", "Tanaka", "Yamamoto", "Sato", "Wei", "Zhang", "Nguyen", "Wong",
    "Nakamura", "Suzuki", "Watanabe", "Ishikawa", "Hayashi", "Matsuda", "Kobayashi", "Lee", "Choi",
    "Black", "Stone", "Cross", "Grey", "Hart", "Kane", "Drake", "Wolf", "Frost", "Steel",
    "Cole", "Ward", "Hayes", "Brooks", "Reed", "Hunt", "West", "Lane", "Grant", "Shaw",
    "Reyes", "Vega", "Cruz", "Santos", "Garcia", "Martinez", "Hernandez", "Rodriguez", "Morales",
    "Okafor", "Hassan", "Ali", "Khan", "Amari", "Diallo", "Mensah", "Adu", "Toure",
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
    "Citizen", "Citizen", "Citizen", "Citizen", "Citizen",
    "Temple Authority", "Temple Authority",
    "Resistance", "Criminal Syndicate", "Tech Guild", "Merchant Coalition",
    "Street Gang", "Corporate", "Independent", "Nomad", "Underground"
]

# === PHYSICAL APPEARANCE ===
ETHNICITIES = [
    "East Asian", "South Asian", "Southeast Asian", "Middle Eastern", "North African",
    "Sub-Saharan African", "European", "Latin American", "Mixed", "Synthetic"
]

SKIN_TONES = ["pale", "fair", "olive", "tan", "bronze", "brown", "dark brown", "ebony", "synthetic chrome", "synthetic matte"]
HAIR_COLORS = ["black", "dark brown", "brown", "auburn", "red", "blonde", "platinum", "white", "gray", "blue", "purple", "pink", "green", "chrome", "holographic"]
HAIR_STYLES = ["short cropped", "shaved", "mohawk", "long straight", "shoulder length", "braided", "dreadlocks", "ponytail", "messy", "slicked back", "undercut", "bald"]
EYE_COLORS = ["brown", "dark brown", "hazel", "green", "blue", "gray", "amber", "gold", "red", "cybernetic blue", "cybernetic green", "heterochromia"]
BUILDS = ["slim", "lean", "athletic", "muscular", "stocky", "heavyset", "wiry", "average"]
FACE_SHAPES = ["oval", "round", "square", "rectangular", "heart", "diamond", "angular"]
DISTINGUISHING = [
    "old scar across cheek", "cybernetic eye implant", "facial tattoos", "burn marks",
    "missing ear", "pierced eyebrow", "nose ring", "lip scar", "synthetic jaw",
    "glowing circuit patterns", "vitiligo patches", "freckles", "beauty mark",
    "ritual scarification", "datajack port visible", "chrome plating on forehead"
]

# === ALIGNMENT & MORALITY ===
ALIGNMENTS = ["lawful good", "neutral good", "chaotic good", "lawful neutral", "true neutral", "chaotic neutral", "lawful evil", "neutral evil", "chaotic evil"]
MORAL_CODES = [
    "Protect the weak at all costs",
    "Money is the only truth",
    "Loyalty to family above all",
    "Survival first, morals second",
    "Honor among thieves",
    "Never harm children",
    "An eye for an eye",
    "The end justifies the means",
    "Power must be earned",
    "Trust no one completely"
]

# === CYBERNETICS ===
CYBERNETIC_TYPES = [
    None, None, None,  # Most have none
    "cybernetic arm (right)", "cybernetic arm (left)", "cybernetic legs",
    "neural interface implant", "cybernetic eyes", "reflex boosters",
    "subdermal armor", "voice modulator", "memory chip slot",
    "enhanced hearing", "thermal vision implant", "toxin filters"
]

# === CLOTHING ===
UPPER_GARMENTS = [
    "worn leather jacket", "corporate blazer", "sleeveless vest", "hooded cloak",
    "armored jacket", "synthetic fiber coat", "torn t-shirt", "formal shirt",
    "tech mesh top", "military surplus jacket", "neon-lit jacket", "thermal coat"
]
LOWER_GARMENTS = [
    "cargo pants", "tailored slacks", "torn jeans", "tactical pants",
    "synthetic fiber pants", "leather pants", "worker overalls", "shorts"
]
FOOTWEAR = [
    "combat boots", "worn sneakers", "dress shoes", "sandals", "mag-boots",
    "bare feet", "armored boots", "platform boots", "running shoes"
]
ACCESSORIES = [
    "datajack visor", "breathing mask", "holo-watch", "utility belt",
    "armband computer", "earpiece comm", "fingerless gloves", "bandana",
    "necklace with pendant", "wrist tattoos", "chrome rings", "sunglasses"
]

# === PERSONALITY ===
MBTI_TYPES = ["INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP",
              "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP"]
ZODIAC = ["aries", "taurus", "gemini", "cancer", "leo", "virgo",
          "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]
DESIRES = ["wealth", "power", "love", "freedom", "knowledge", "revenge", "security", 
           "recognition", "family", "adventure", "peace", "justice"]
TRAITS = ["creative", "curious", "artistic", "organized", "disciplined", "ambitious",
          "outgoing", "energetic", "friendly", "compassionate", "cooperative",
          "anxious", "moody", "calm", "stable", "confident", "skeptical", "reserved"]
ACTIVITIES = ["working", "resting", "socializing", "shopping", "eating", "drinking",
              "trading", "gambling", "praying", "exercising", "reading", "sleeping",
              "patrolling", "crafting", "repairing", "dealing", "hustling", "relaxing"]
MOODS = ["calm", "anxious", "happy", "frustrated", "tired", "alert", "bored", 
         "excited", "suspicious", "friendly", "cold", "curious"]

BUILDINGS = [f"B{str(i).zfill(3)}" for i in range(1, 51)]

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

def generate_physical(gender, age):
    """Generate full physical appearance."""
    # Height/weight based on gender and build
    build = random.choice(BUILDS)
    if gender == "male":
        base_height = random.randint(165, 195)
        base_weight = random.randint(60, 95)
    elif gender == "female":
        base_height = random.randint(155, 180)
        base_weight = random.randint(48, 80)
    else:
        base_height = random.randint(160, 188)
        base_weight = random.randint(52, 88)
    
    # Adjust for build
    weight_mod = {"slim": -10, "lean": -5, "athletic": 0, "muscular": 10, "stocky": 8, "heavyset": 20, "wiry": -8, "average": 0}
    weight = max(40, base_weight + weight_mod.get(build, 0) + random.randint(-5, 5))
    
    # Age affects appearance
    hair_color = random.choice(HAIR_COLORS)
    if age > 55 and random.random() < 0.6:
        hair_color = random.choice(["gray", "white", "silver"])
    
    return {
        "height_cm": base_height,
        "weight_kg": weight,
        "build": build,
        "ethnicity": random.choice(ETHNICITIES),
        "skin_tone": random.choice(SKIN_TONES),
        "face": {
            "shape": random.choice(FACE_SHAPES),
            "hair_color": hair_color,
            "hair_style": random.choice(HAIR_STYLES),
            "eye_color": random.choice(EYE_COLORS),
            "distinguishing_features": random.sample(DISTINGUISHING, k=random.randint(0, 2))
        },
        "cybernetics": random.choice(CYBERNETIC_TYPES),
        "clothing": {
            "upper": random.choice(UPPER_GARMENTS),
            "lower": random.choice(LOWER_GARMENTS),
            "footwear": random.choice(FOOTWEAR),
            "accessories": random.sample(ACCESSORIES, k=random.randint(0, 2))
        }
    }

def generate_alignment():
    """Generate moral alignment and code."""
    return {
        "alignment": random.choice(ALIGNMENTS),
        "moral_code": random.choice(MORAL_CODES),
        "corruption": random.randint(0, 100),  # 0=pure, 100=fully corrupt
        "loyalty": random.randint(20, 100)     # How loyal to their faction
    }

def generate_personality():
    """Generate Big Five personality traits."""
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
        "traits": random.sample(TRAITS, k=random.randint(3, 5)),
        "primary_desire": random.choice(DESIRES),
        "secondary_desire": random.choice(DESIRES)
    }

def generate_backstory(name, gender):
    """Generate a short backstory."""
    pronoun = "she" if gender == "female" else ("they" if gender == "nonbinary" else "he")
    possessive = "her" if gender == "female" else ("their" if gender == "nonbinary" else "his")
    
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
    """Generate a single FULL NPC profile."""
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
        # Physical appearance (extensible by plugins)
        "physical": generate_physical(gender, age),
        # Moral alignment (extensible by plugins)
        "alignment": generate_alignment(),
        # Personality system
        "personality": generate_personality(),
        # Locations
        "home": home,
        "workplace": workplace,
        "location": home,
        "activity": random.choice(ACTIVITIES),
        "mood": random.choice(MOODS),
        # Narrative
        "backstory": generate_backstory(name, gender),
        "catchphrase": f'"{random.choice(["Trust no one.", "Credits talk.", "Stay frosty.", "Keep moving.", "Eyes open.", "The city remembers.", "Everyone has a price.", "Nothing personal."])}"',
        # Relationships (plugin extensible)
        "relationships": {},
        "knowledge": [],
        "reputation": random.randint(0, 100)
    }

def chunk_data(npcs, max_size_kb=50):
    """Split NPCs into chunks of approximately max_size_kb."""
    chunks = []
    current_chunk = []
    current_size = 0
    max_size = max_size_kb * 1024

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
    print("🎭 Generating 10,000 NPCs with FULL profiles...")
    print("   Including: physical appearance, face, alignment, cybernetics, clothing")
    
    npcs = [generate_npc(i) for i in range(1, 10001)]
    print(f"✅ Generated {len(npcs)} NPCs")
    
    # Smaller chunks since NPCs are bigger now
    chunks = chunk_data(npcs, max_size_kb=50)
    print(f"📦 Split into {len(chunks)} chunks (~50KB each for <100KB final)")
    
    manifest = {
        "version": "2.0.0",
        "schema": "full_profile",
        "total_npcs": len(npcs),
        "total_chunks": len(chunks),
        "fields": ["physical", "alignment", "personality", "backstory", "relationships"],
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
    
    manifest_path = OUTPUT_DIR / "manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    total_size = sum(c['size_kb'] for c in manifest['chunks'])
    print(f"\n✅ Complete! Total: {total_size:.1f}KB across {len(chunks)} chunks")
    print(f"📍 Saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()

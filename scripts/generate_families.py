#!/usr/bin/env python3
"""
Family Relationship Generator for AO World Engine

Generates realistic family relationships for 800 NPCs:
- ~40% married couples (160 couples = 320 NPCs)
- ~30% single adults (240 NPCs)  
- ~15% parents with children at home (120 NPCs)
- ~10% single parents (80 NPCs)
- ~5% widowed/divorced (40 NPCs)

Also generates:
- Households (shared home assignments)
- Sibling relationships
- Appearance data (deterministic from NPC ID)
- Basic mood state
"""

import json
import hashlib
import random
import os

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "data")
INPUT_FILE = os.path.join(DATA_DIR, "npcs_generated.json")
OUTPUT_FILE = os.path.join(DATA_DIR, "npcs_generated.json")

# Seeded random for determinism
def seeded_random(seed_str):
    """Deterministic random 0-1 from string seed."""
    h = hashlib.sha256(seed_str.encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF

def seeded_choice(options, seed_str):
    """Deterministic choice from list."""
    r = seeded_random(seed_str)
    return options[int(r * len(options))]

def seeded_int(min_val, max_val, seed_str):
    """Deterministic int in range."""
    r = seeded_random(seed_str)
    return int(min_val + r * (max_val - min_val + 1))

# Appearance options
SKIN_TONES = ["SK01", "SK02", "SK03", "SK04", "SK05", "SK06", "SK07", "SK08"]
HAIR_COLORS = ["HC01", "HC02", "HC03", "HC04", "HC05", "HC06", "HC07", "HC08", "HC09", "HC10"]
EYE_COLORS = ["EY01", "EY02", "EY03", "EY04", "EY05", "EY06"]
BUILDS = ["thin", "average", "athletic", "muscular", "heavy"]
NOTABLE_FEATURES = [
    "Scar on left cheek", "Missing finger", "Cybernetic eye", "Tattoo on neck",
    "Burn marks on hands", "Prosthetic arm", "Grey streaks in hair", "Limp",
    "Nervous twitch", "Unusual eye color", "Deep voice", "Raspy voice",
    None, None, None, None, None  # Many have no notable features
]

# Mood options
MOODS = ["content", "anxious", "melancholic", "hopeful", "bitter", "determined", "fearful", "numb"]
MOOD_TRIGGERS = [
    ["temple_presence", "authority"], 
    ["hunger", "poverty"],
    ["social_isolation", "distrust"],
    ["family_loss", "grief"],
    ["surveillance", "paranoia"],
    ["overcrowding", "noise"],
    ["hope", "resistance_news"],
    ["routine", "stability"]
]

def generate_appearance(npc_id):
    """Generate deterministic appearance for NPC."""
    return {
        "skin": seeded_choice(SKIN_TONES, f"{npc_id}_skin"),
        "hair": seeded_choice(HAIR_COLORS, f"{npc_id}_hair"),
        "eyes": seeded_choice(EYE_COLORS, f"{npc_id}_eyes"),
        "height": seeded_int(155, 195, f"{npc_id}_height"),
        "build": seeded_choice(BUILDS, f"{npc_id}_build"),
        "notable": seeded_choice(NOTABLE_FEATURES, f"{npc_id}_notable")
    }

def generate_mood(npc_id, archetype):
    """Generate initial mood state."""
    # Archetype influences base mood
    archetype_moods = {
        "criminal": ["anxious", "bitter", "determined"],
        "worker": ["content", "melancholic", "numb"],
        "shopkeeper": ["hopeful", "anxious", "content"],
        "guard": ["determined", "bitter", "numb"],
        "entertainer": ["hopeful", "content", "anxious"],
        "technician": ["determined", "content", "hopeful"],
    }
    
    mood_options = archetype_moods.get(archetype, MOODS)
    base_mood = seeded_choice(mood_options, f"{npc_id}_mood")
    
    return {
        "current": base_mood,
        "intensity": round(seeded_random(f"{npc_id}_intensity") * 0.4 + 0.3, 2),  # 0.3-0.7
        "stability": round(seeded_random(f"{npc_id}_stability") * 0.5 + 0.3, 2),  # 0.3-0.8
        "triggers": seeded_choice(MOOD_TRIGGERS, f"{npc_id}_triggers")
    }

def generate_families(npcs):
    """Generate family relationships for all NPCs."""
    
    # Create age estimates based on NPC ID (deterministic)
    for npc in npcs:
        npc["age"] = seeded_int(18, 75, f"{npc['id']}_age")
    
    # Sort by age to create realistic family structures
    adults = [n for n in npcs if n["age"] >= 18]
    
    # Track assignments
    married = set()
    has_family = set()
    households = {}  # household_id -> [npc_ids]
    household_counter = 0
    
    # Initialize family structure for all NPCs
    for npc in npcs:
        npc["family"] = {
            "spouse_id": None,
            "parent_ids": [],
            "sibling_ids": [],
            "children_ids": [],
            "household_id": None,
            "marital_status": "single"
        }
        npc["appearance"] = generate_appearance(npc["id"])
        npc["mood"] = generate_mood(npc["id"], npc.get("archetype", "worker"))
    
    # Create NPC lookup
    npc_by_id = {n["id"]: n for n in npcs}
    
    # 1. Create married couples (~160 couples from adults 25-65)
    eligible_for_marriage = [n for n in adults if 25 <= n["age"] <= 65]
    random.seed(42)  # Deterministic
    random.shuffle(eligible_for_marriage)
    
    couple_count = 0
    i = 0
    while i < len(eligible_for_marriage) - 1 and couple_count < 160:
        npc1 = eligible_for_marriage[i]
        npc2 = eligible_for_marriage[i + 1]
        
        # Skip if already married
        if npc1["id"] in married or npc2["id"] in married:
            i += 1
            continue
        
        # Age difference check (1-15 years)
        age_diff = abs(npc1["age"] - npc2["age"])
        if age_diff > 15:
            i += 1
            continue
        
        # Create marriage
        npc1["family"]["spouse_id"] = npc2["id"]
        npc2["family"]["spouse_id"] = npc1["id"]
        npc1["family"]["marital_status"] = "married"
        npc2["family"]["marital_status"] = "married"
        
        # Create household (they share a home)
        household_id = f"H{household_counter:03d}"
        household_counter += 1
        npc1["family"]["household_id"] = household_id
        npc2["family"]["household_id"] = household_id
        
        # Use one of their homes as shared home
        shared_home = npc1["home"]
        npc2["home"] = shared_home
        
        households[household_id] = [npc1["id"], npc2["id"]]
        
        married.add(npc1["id"])
        married.add(npc2["id"])
        has_family.add(npc1["id"])
        has_family.add(npc2["id"])
        
        couple_count += 1
        i += 2
    
    print(f"Created {couple_count} married couples")
    
    # 2. Add children to ~60% of married couples
    couples_with_kids = 0
    for hh_id, members in list(households.items()):
        if len(members) != 2:
            continue
        
        parent1 = npc_by_id[members[0]]
        parent2 = npc_by_id[members[1]]
        
        # Only couples aged 28-55 have children at home
        avg_age = (parent1["age"] + parent2["age"]) / 2
        if not (28 <= avg_age <= 55):
            continue
        
        # 60% chance of having children
        if seeded_random(f"{hh_id}_has_kids") > 0.6:
            continue
        
        # 1-3 children
        num_children = seeded_int(1, 3, f"{hh_id}_num_kids")
        
        # Find unassigned young NPCs to make children
        potential_children = [
            n for n in npcs 
            if n["id"] not in has_family 
            and 8 <= n["age"] <= 25
            and n["age"] < min(parent1["age"], parent2["age"]) - 18
        ]
        
        if len(potential_children) < num_children:
            continue
        
        children = potential_children[:num_children]
        child_ids = [c["id"] for c in children]
        
        for child in children:
            child["family"]["parent_ids"] = [parent1["id"], parent2["id"]]
            child["family"]["household_id"] = hh_id
            child["home"] = parent1["home"]  # Live with parents
            has_family.add(child["id"])
            
            # Siblings
            for other_child in children:
                if other_child["id"] != child["id"]:
                    child["family"]["sibling_ids"].append(other_child["id"])
        
        parent1["family"]["children_ids"] = child_ids
        parent2["family"]["children_ids"] = child_ids
        
        households[hh_id].extend(child_ids)
        couples_with_kids += 1
    
    print(f"Added children to {couples_with_kids} couples")
    
    # 3. Create single parents (~40)
    single_parent_count = 0
    unassigned_adults = [n for n in adults if n["id"] not in has_family and 30 <= n["age"] <= 50]
    
    for parent in unassigned_adults[:40]:
        # Find a child
        potential_children = [
            n for n in npcs 
            if n["id"] not in has_family 
            and 5 <= n["age"] <= 20
            and n["age"] < parent["age"] - 18
        ]
        
        if not potential_children:
            continue
        
        child = potential_children[0]
        
        # Create single parent household
        household_id = f"H{household_counter:03d}"
        household_counter += 1
        
        parent["family"]["children_ids"] = [child["id"]]
        parent["family"]["household_id"] = household_id
        parent["family"]["marital_status"] = seeded_choice(["widowed", "divorced", "single"], f"{parent['id']}_status")
        
        child["family"]["parent_ids"] = [parent["id"]]
        child["family"]["household_id"] = household_id
        child["home"] = parent["home"]
        
        has_family.add(parent["id"])
        has_family.add(child["id"])
        households[household_id] = [parent["id"], child["id"]]
        
        single_parent_count += 1
    
    print(f"Created {single_parent_count} single parent households")
    
    # 4. Create some sibling pairs living together (~30)
    sibling_pairs = 0
    unassigned = [n for n in npcs if n["id"] not in has_family and 20 <= n["age"] <= 40]
    
    i = 0
    while i < len(unassigned) - 1 and sibling_pairs < 30:
        npc1 = unassigned[i]
        npc2 = unassigned[i + 1]
        
        # Age difference for siblings (1-8 years)
        if abs(npc1["age"] - npc2["age"]) > 8:
            i += 1
            continue
        
        household_id = f"H{household_counter:03d}"
        household_counter += 1
        
        npc1["family"]["sibling_ids"] = [npc2["id"]]
        npc2["family"]["sibling_ids"] = [npc1["id"]]
        npc1["family"]["household_id"] = household_id
        npc2["family"]["household_id"] = household_id
        npc2["home"] = npc1["home"]
        
        has_family.add(npc1["id"])
        has_family.add(npc2["id"])
        
        sibling_pairs += 1
        i += 2
    
    print(f"Created {sibling_pairs} sibling pairs")
    
    # 5. Remaining NPCs are single adults living alone
    single_count = 0
    for npc in npcs:
        if npc["id"] not in has_family:
            household_id = f"H{household_counter:03d}"
            household_counter += 1
            npc["family"]["household_id"] = household_id
            households[household_id] = [npc["id"]]
            single_count += 1
    
    print(f"Remaining {single_count} single adults")
    
    # Summary stats
    married_count = len([n for n in npcs if n["family"]["marital_status"] == "married"])
    with_children = len([n for n in npcs if n["family"]["children_ids"]])
    with_parents = len([n for n in npcs if n["family"]["parent_ids"]])
    with_siblings = len([n for n in npcs if n["family"]["sibling_ids"]])
    
    print(f"\n=== FAMILY STATS ===")
    print(f"Total NPCs: {len(npcs)}")
    print(f"Married: {married_count}")
    print(f"With children: {with_children}")
    print(f"With parents: {with_parents}")
    print(f"With siblings: {with_siblings}")
    print(f"Households: {len(households)}")
    
    return npcs

def main():
    print("Loading NPCs...")
    with open(INPUT_FILE, 'r') as f:
        data = json.load(f)
    
    npcs = data.get("npcs", [])
    print(f"Loaded {len(npcs)} NPCs")
    
    print("\nGenerating families...")
    npcs = generate_families(npcs)
    
    # Update data
    data["npcs"] = npcs
    
    print(f"\nSaving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    print("Done!")
    
    # Show sample NPC
    sample = npcs[0]
    print(f"\n=== SAMPLE ENRICHED NPC ===")
    print(f"ID: {sample['id']}")
    print(f"Name: {sample['name']}")
    print(f"Age: {sample.get('age')}")
    print(f"Appearance: {sample.get('appearance')}")
    print(f"Mood: {sample.get('mood')}")
    print(f"Family: {sample.get('family')}")

if __name__ == "__main__":
    main()

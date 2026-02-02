"""
Deterministic NPC Name & Event Generator
=========================================

KEY INSIGHT: Names aren't stored, they're CALCULATED.
Same seed = same result, always.

This is how:
- Query today: get_npc_name(parent_a=45, parent_b=67, birth_tick=10500) → "Kai Chen"
- Query tomorrow: same call → "Kai Chen" (ALWAYS)
- Different layer: get_npc_name(..., layer=2) → "Marcus Chen" (different timeline!)

The entire simulation is deterministic. If you know the seed, you know everything.
"""

import hashlib
import json

# Name pools (these ARE stored, they're the "vocabulary")
FIRST_NAMES_MALE = [
    "Kai", "Ryu", "Marcus", "Jin", "Leo", "Dante", "Zero", "Ash", 
    "Cole", "Dex", "Finn", "Gray", "Neo", "Rex", "Zane", "Blaze",
    "Cruz", "Drake", "Echo", "Frost", "Ghost", "Hawk", "Ion", "Jax"
]

FIRST_NAMES_FEMALE = [
    "Nova", "Kira", "Luna", "Mika", "Rin", "Yuki", "Selene", "Aria",
    "Ember", "Ivy", "Jade", "Nyx", "Raven", "Sage", "Vera", "Wren",
    "Astra", "Blade", "Cipher", "Dawn", "Eve", "Flux", "Gale", "Haven"
]

SURNAMES = [
    "Chen", "Tanaka", "Vex", "Ōmura", "Kim", "Singh", "Volkov", "Cruz",
    "Nakamura", "Park", "Reyes", "Santos", "Yamamoto", "Zhang", "Black",
    "Cross", "Edge", "Frost", "Gray", "Night", "Storm", "Wolf", "Zero"
]


def deterministic_hash(seed_string: str) -> int:
    """Convert any string seed into a deterministic integer."""
    return int(hashlib.sha256(seed_string.encode()).hexdigest(), 16)


def get_from_pool(pool: list, seed: int) -> str:
    """Pick from pool using seed. Always same result for same seed."""
    return pool[seed % len(pool)]


def get_npc_name(parent_a_id: int, parent_b_id: int, birth_tick: int, 
                 child_index: int = 0, layer: int = 0) -> dict:
    """
    Generate a deterministic NPC name from parents and birth tick.
    
    Same inputs = same name, ALWAYS.
    Different layer = different name (parallel universe).
    """
    # Create unique seed for this specific child
    seed_string = f"child_{min(parent_a_id, parent_b_id)}_{max(parent_a_id, parent_b_id)}_{birth_tick}_{child_index}_layer_{layer}"
    seed = deterministic_hash(seed_string)
    
    # Determine gender (deterministic)
    is_male = (seed % 2) == 0
    
    # Pick first name
    first_name = get_from_pool(
        FIRST_NAMES_MALE if is_male else FIRST_NAMES_FEMALE,
        seed >> 1  # Use different bits for different choices
    )
    
    # Inherit surname from one parent (deterministic choice)
    # In a real system, parents would have surname_id, not hardcoded names
    surname_seed = deterministic_hash(f"surname_{seed_string}")
    surname = get_from_pool(SURNAMES, surname_seed)
    
    return {
        "first_name": first_name,
        "surname": surname,
        "full_name": f"{first_name} {surname}",
        "gender": "male" if is_male else "female",
        "birth_tick": birth_tick,
        "parent_a": parent_a_id,
        "parent_b": parent_b_id,
        "layer": layer,
        "seed": seed_string
    }


def get_marriage_partner(npc_id: int, marriage_tick: int, layer: int = 0) -> int:
    """
    Deterministically calculate who an NPC marries.
    Returns ID of partner NPC.
    """
    seed_string = f"marriage_{npc_id}_{marriage_tick}_layer_{layer}"
    seed = deterministic_hash(seed_string)
    
    # Partner ID is calculated from seed (would be constrained by living NPCs in real system)
    # For demo, just return a number that's different from self
    partner_id = (seed % 1000) + 1
    if partner_id == npc_id:
        partner_id += 1
    
    return partner_id


def get_life_events(npc_id: int, from_tick: int, to_tick: int, layer: int = 0) -> list:
    """
    Get all deterministic life events for an NPC in a tick range.
    """
    events = []
    
    # Check each tick for potential events (simplified - real system uses sparse events)
    for tick in range(from_tick, to_tick, 24):  # Check once per "day"
        
        # Will they get married this day?
        marriage_seed = deterministic_hash(f"will_marry_{npc_id}_{tick}_layer_{layer}")
        if marriage_seed % 10000 == 42:  # ~0.01% chance per day
            partner = get_marriage_partner(npc_id, tick, layer)
            events.append({
                "tick": tick,
                "type": "marriage",
                "partner_id": partner,
                "description": f"NPC {npc_id} married NPC {partner}"
            })
        
        # Check for child birth (if married)
        birth_seed = deterministic_hash(f"will_birth_{npc_id}_{tick}_layer_{layer}")
        if birth_seed % 5000 == 7:  # ~0.02% chance
            # Get partner from most recent marriage (simplified)
            partner = get_marriage_partner(npc_id, tick - 1000, layer)
            child = get_npc_name(npc_id, partner, tick, layer=layer)
            events.append({
                "tick": tick,
                "type": "child_born",
                "child": child,
                "description": f"{child['full_name']} was born to NPCs {npc_id} and {partner}"
            })
    
    return events


# ========== DEMO ==========

if __name__ == "__main__":
    print("=" * 60)
    print("DETERMINISTIC NPC NAME GENERATOR")
    print("=" * 60)
    print()
    
    # Same query, always same result
    print("1. CONSISTENCY TEST - Same inputs = Same output")
    print("-" * 40)
    for i in range(3):
        child = get_npc_name(parent_a_id=45, parent_b_id=67, birth_tick=10500)
        print(f"   Query {i+1}: {child['full_name']} (seed: {child['seed']})")
    print()
    
    # Different layer = different result
    print("2. MULTIVERSE TEST - Different layer = Different name")
    print("-" * 40)
    for layer in range(4):
        child = get_npc_name(parent_a_id=45, parent_b_id=67, birth_tick=10500, layer=layer)
        print(f"   Layer {layer}: {child['full_name']}")
    print()
    
    # Multiple children
    print("3. SIBLINGS TEST - Same parents, different births")
    print("-" * 40)
    for i in range(3):
        birth_tick = 10500 + (i * 2000)  # ~2 years apart
        child = get_npc_name(parent_a_id=45, parent_b_id=67, birth_tick=birth_tick, child_index=i)
        print(f"   Child {i+1} (tick {birth_tick}): {child['full_name']} ({child['gender']})")
    print()
    
    # Life events
    print("4. LIFE EVENTS - Query history for any NPC")
    print("-" * 40)
    events = get_life_events(npc_id=45, from_tick=0, to_tick=50000)
    if events:
        for event in events[:5]:
            print(f"   Tick {event['tick']}: {event['description']}")
    else:
        print("   No major events in this range (try larger range)")
    print()
    
    print("=" * 60)
    print("KEY INSIGHT: Nothing is 'generated' - everything is CALCULATED")
    print("The entire simulation exists mathematically from tick 0 to infinity.")
    print("We just compute the parts we need when we need them.")
    print("=" * 60)

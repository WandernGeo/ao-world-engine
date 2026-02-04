#!/usr/bin/env python3
"""
Convert NPCs from JSON to Lua format for AO deployment.
Also adds desires/goals based on personality traits.
"""

import json
import random
from pathlib import Path

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR = Path(__file__).parent.parent / "ao-processes"

# Load source data
def load_json(filename):
    with open(DATA_DIR / filename) as f:
        return json.load(f)

# Life aspiration selection based on personality
def select_life_aspiration(personality, faction):
    """Select life aspiration based on personality traits."""
    # Weight aspirations by personality
    aspirations = {
        'freedom': personality.get('curiosity', 0.5) + (0.3 if faction == 'resistance' else 0),
        'power': personality.get('aggression', 0.5) * 0.5 + personality.get('greed', 0.5) * 0.5,
        'knowledge': personality.get('curiosity', 0.5) * 0.8,
        'love': personality.get('loyalty', 0.5) * 0.6 + personality.get('sociability', 0.5) * 0.4,
        'survival': (1 - personality.get('aggression', 0.5)) * 0.5 + personality.get('greed', 0.2) * 0.3,
        'justice': personality.get('loyalty', 0.5) * 0.4 + (0.3 if faction == 'resistance' else 0),
        'wealth': personality.get('greed', 0.5) * 0.7,
        'legacy': personality.get('curiosity', 0.5) * 0.3 + personality.get('sociability', 0.5) * 0.3
    }
    
    # Add randomness
    for k in aspirations:
        aspirations[k] += random.uniform(-0.2, 0.2)
    
    # Return highest
    return max(aspirations, key=aspirations.get)

# Generate short-term goals based on archetype
def generate_short_term_goals(archetype, personality):
    """Generate 2-3 short-term goals."""
    goal_pools = {
        'survival': ['find_food', 'find_shelter', 'avoid_danger', 'rest'],
        'economic': ['earn_credits', 'complete_work_shift', 'find_buyer', 'collect_payment'],
        'social': ['meet_friend', 'gossip', 'attend_event', 'visit_family'],
        'information': ['gather_intel', 'learn_news', 'find_contact']
    }
    
    goals = []
    
    # Workers focus on economic
    if archetype in ['worker', 'vendor', 'service']:
        goals.append(random.choice(goal_pools['economic']))
        if personality.get('sociability', 0.5) > 0.5:
            goals.append(random.choice(goal_pools['social']))
    
    # Resistance focus on information
    elif archetype in ['resistance']:
        goals.append(random.choice(goal_pools['information']))
        goals.append(random.choice(goal_pools['survival']))
    
    # Criminals focus on economic + survival
    elif archetype in ['criminal']:
        goals.append(random.choice(goal_pools['economic']))
        goals.append(random.choice(goal_pools['survival']))
    
    # Default
    else:
        goals.append(random.choice(goal_pools['survival']))
        if personality.get('sociability', 0.5) > 0.4:
            goals.append(random.choice(goal_pools['social']))
    
    return goals[:3]

# Generate long-term goals
def generate_long_term_goals(life_aspiration, faction):
    """Generate 1-2 long-term goals based on life aspiration."""
    goal_map = {
        'freedom': ['escape_city', 'join_resistance', 'expose_corruption'],
        'power': ['get_promotion', 'gain_reputation', 'climb_temple_ranks'],
        'knowledge': ['learn_new_skill', 'discover_secret', 'find_mentor'],
        'love': ['find_partner', 'support_family', 'protect_loved_one'],
        'survival': ['save_for_apartment', 'build_savings', 'secure_food_supply'],
        'justice': ['expose_corruption', 'complete_faction_mission', 'avenge_family'],
        'wealth': ['start_business', 'save_for_apartment', 'make_connections'],
        'legacy': ['start_business', 'gain_reputation', 'learn_new_skill']
    }
    
    goals = goal_map.get(life_aspiration, ['save_for_apartment'])
    return random.sample(goals, min(2, len(goals)))

# Convert NPC to Lua format
def npc_to_lua(npc):
    """Convert single NPC dict to Lua table string."""
    # Add desires if not present
    if 'desires' not in npc:
        personality = npc.get('personality', {})
        faction = npc.get('faction', 'civilian')
        archetype = npc.get('archetype', 'resident')
        
        life_aspiration = select_life_aspiration(personality, faction)
        short_term = generate_short_term_goals(archetype, personality)
        long_term = generate_long_term_goals(life_aspiration, faction)
        
        npc['desires'] = {
            'short_term': short_term,
            'long_term': long_term,
            'life_goal': life_aspiration
        }
    
    return npc

def json_to_lua_value(value, indent=0):
    """Convert Python value to Lua literal."""
    prefix = "    " * indent
    
    if value is None:
        return "nil"
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, str):
        # Escape quotes
        escaped = value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        return f'"{escaped}"'
    elif isinstance(value, list):
        if len(value) == 0:
            return "{}"
        items = ", ".join(json_to_lua_value(v, indent) for v in value)
        return "{ " + items + " }"
    elif isinstance(value, dict):
        if len(value) == 0:
            return "{}"
        lines = []
        for k, v in value.items():
            # Clean key names
            key = k.replace('-', '_').replace(' ', '_')
            lines.append(f"{prefix}    {key} = {json_to_lua_value(v, indent + 1)}")
        return "{\n" + ",\n".join(lines) + f"\n{prefix}}}"
    else:
        return str(value)

def generate_lua_npcs(npcs_data, output_path):
    """Generate Lua file with all NPCs."""
    
    # Process buildings
    buildings = npcs_data.get('buildings', [])
    
    # Process NPCs and add desires
    npcs = npcs_data.get('npcs', [])
    processed_npcs = [npc_to_lua(npc) for npc in npcs]
    
    lua_content = f'''--[[
  AO World Engine - All NPCs Data
  Generated from npcs_generated.json
  
  Contains {len(processed_npcs)} NPCs with full attributes:
  - Personality, skills, appearance
  - Family relationships
  - Mood and triggers
  - Desires (short-term, long-term, life goals)
  
  Usage: require("all_npcs")
]]--

-- Buildings registry
BUILDINGS = {{
'''
    
    # Add buildings
    for b in buildings:
        lua_content += f'    ["{b["id"]}"] = {json_to_lua_value(b, 1)},\n'
    
    lua_content += "}\n\n-- All NPCs indexed by ID\nALL_NPCS = {\n"
    
    # Add NPCs (limit to 800 for reasonable file size)
    for npc in processed_npcs[:800]:
        npc_id = npc.get('id', 'unknown')
        lua_content += f'    ["{npc_id}"] = {json_to_lua_value(npc, 1)},\n'
    
    lua_content += "}\n\nreturn { ALL_NPCS = ALL_NPCS, BUILDINGS = BUILDINGS }\n"
    
    # Write output
    with open(output_path, 'w') as f:
        f.write(lua_content)
    
    print(f"Generated {output_path} with {len(processed_npcs[:800])} NPCs")

def main():
    # Load NPC data
    npcs_data = load_json("npcs_generated.json")
    
    # Generate Lua file
    output_path = OUTPUT_DIR / "all_npcs.lua"
    generate_lua_npcs(npcs_data, output_path)
    
    print("Done!")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Generate NPC Inventories
========================

Assigns wealth, vehicles, home furnishings, and carried items to all 800 NPCs
based on their archetype, faction, and personality.
"""

import json
import random
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
CODEC_DIR = DATA_DIR / "codec_chunks"

def load_json(path):
    with open(path) as f:
        return json.load(f)

def main():
    # Load NPCs
    npcs = load_json(DATA_DIR / "npcs_generated_with_personality.json")["npcs"]
    
    # Load economy codec
    economy = load_json(CODEC_DIR / "world_codec_15_economy.json")
    wealth_tiers = economy["economy"]["wealth_tiers"]
    furnishings = economy["economy"]["home_furnishing_by_tier"]
    
    # Archetype to wealth tier mapping
    archetype_wealth = {
        "criminal": "poor",
        "visitor": "middle",
        "resident": "working",
        "worker": "working",
        "vendor": "middle",
        "service": "working",
        "resistance": "poor",
        "guard": "middle"
    }
    
    # Generate inventory for each NPC
    inventories = {}
    
    for npc in npcs:
        npc_id = npc["id"]
        archetype = npc.get("archetype", "resident")
        faction = npc.get("faction", "civilian")
        personality = npc.get("personality", {})
        
        # Determine wealth tier
        greed = personality.get("greed", 0.5)
        base_tier = archetype_wealth.get(archetype, "working")
        
        # Greed can bump up wealth tier
        if greed > 0.8:
            tier_order = ["destitute", "poor", "working", "middle", "wealthy", "elite"]
            tier_idx = tier_order.index(base_tier)
            if tier_idx < len(tier_order) - 1:
                base_tier = tier_order[tier_idx + 1]
        
        tier_data = wealth_tiers[base_tier]
        
        # Random credits in range
        random.seed(npc_id)  # Deterministic
        credit_range = tier_data["credit_range"]
        credits = random.randint(credit_range[0], credit_range[1])
        
        # Vehicle assignment
        vehicle_id = None
        if random.random() < tier_data.get("vehicle_chance", 0):
            vehicle_codes = tier_data.get("vehicle_codes", [])
            if vehicle_codes:
                vehicle_id = random.choice(vehicle_codes)
        
        # Home furnishings
        home_items = []
        tier_furnishings = furnishings.get(base_tier, [])
        for item_code in tier_furnishings:
            home_items.append({
                "item_code": item_code,
                "qty": 1,
                "condition": random.choice(["pristine", "good", "worn"])
            })
        
        # Carried items based on archetype
        carried_items = []
        
        if archetype == "criminal":
            carried_items.append({"item_code": "OBJ337", "qty": 1})  # knife_pocket
            if random.random() > 0.5:
                carried_items.append({"item_code": "OBJ111", "qty": 1})  # usb_drive
        
        elif archetype == "worker":
            carried_items.append({"item_code": "OBJ081", "qty": 1})  # phone_smart
            carried_items.append({"item_code": "OBJ469", "qty": 2})  # pen
        
        elif archetype == "vendor":
            carried_items.append({"item_code": "OBJ336", "qty": 1})  # wallet
            carried_items.append({"item_code": "OBJ081", "qty": 1})  # phone_smart
        
        elif archetype == "guard":
            carried_items.append({"item_code": "OBJ385", "qty": 1})  # taser
            carried_items.append({"item_code": "OBJ349", "qty": 1})  # baton_police
            carried_items.append({"item_code": "EL016", "qty": 1})  # radio_basic
        
        elif archetype == "resistance":
            carried_items.append({"item_code": "OBJ337", "qty": 1})  # knife_pocket
            if random.random() > 0.7:
                carried_items.append({"item_code": "OBJ361", "qty": 1})  # pistol_9mm
        
        else:
            carried_items.append({"item_code": "OBJ081", "qty": 1})  # phone_smart
            carried_items.append({"item_code": "OBJ336", "qty": 1})  # wallet
        
        # Cybernetics (rarer)
        cybernetics = []
        if random.random() > 0.7:  # 30% chance of any cyber
            if base_tier in ["middle", "wealthy", "elite"]:
                cybernetics.append("CY001")  # neural_link_basic
                if random.random() > 0.5:
                    cybernetics.append("CY011")  # cybereyes_basic
        
        inventories[npc_id] = {
            "npc_id": npc_id,
            "wealth_tier": base_tier,
            "credits": credits,
            "home_id": npc.get("home", f"APT_{npc_id}"),
            "vehicle_id": vehicle_id,
            "carried_items": carried_items,
            "home_items": home_items,
            "cybernetics": cybernetics
        }
    
    # Save inventories
    output_path = DATA_DIR / "npc_inventories.json"
    with open(output_path, "w") as f:
        json.dump({
            "_version": "1.0.0",
            "_generated_tick": 0,
            "inventories": inventories
        }, f, indent=2)
    
    print(f"Generated inventories for {len(inventories)} NPCs")
    print(f"Saved to: {output_path}")
    
    # Stats
    tiers = {}
    vehicles = 0
    cyber = 0
    for inv in inventories.values():
        t = inv["wealth_tier"]
        tiers[t] = tiers.get(t, 0) + 1
        if inv["vehicle_id"]:
            vehicles += 1
        if inv["cybernetics"]:
            cyber += 1
    
    print(f"\nWealth distribution:")
    for t, c in sorted(tiers.items()):
        print(f"  {t}: {c}")
    print(f"\nVehicle owners: {vehicles}")
    print(f"Cybernetic enhanced: {cyber}")

if __name__ == "__main__":
    main()

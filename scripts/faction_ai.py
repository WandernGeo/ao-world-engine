#!/usr/bin/env python3
"""
FACTION AI SYSTEM - Galactic Civilizations Style
=================================================

Factions are autonomous agents that:
- Have goals (expand, survive, dominate)
- Manage resources (credits, manpower, influence)
- Make strategic decisions (build, trade, war)
- Form alliances and rivalries
- Respond to player and world events

This runs deterministically - same tick = same decision.
"""

import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

# =============================================================================
# DETERMINISTIC UTILITIES
# =============================================================================

def deterministic_hash(seed: str) -> int:
    """Generate deterministic integer from seed."""
    return int(hashlib.sha256(seed.encode()).hexdigest(), 16)

def deterministic_chance(probability: float, seed: str) -> bool:
    """Deterministic probability check."""
    h = deterministic_hash(seed) % 10000
    return h < (probability * 10000)

def deterministic_choice(items: list, seed: str) -> Any:
    """Deterministically pick from list."""
    if not items:
        return None
    h = deterministic_hash(seed)
    return items[h % len(items)]


# =============================================================================
# FACTION GOALS
# =============================================================================

class FactionGoal(Enum):
    EXPAND = "expand"           # Gain territory
    SURVIVE = "survive"         # Maintain current position
    DOMINATE = "dominate"       # Defeat other factions
    PROSPER = "prosper"         # Maximize resources
    LIBERATE = "liberate"       # Free the people (Resistance)
    CONTROL = "control"         # Maintain order (Temple)
    PROFIT = "profit"           # Make money (Criminal)


# =============================================================================
# FACTION DATA
# =============================================================================

@dataclass
class FactionState:
    """Complete state of a faction."""
    id: str
    name: str
    
    # Resources
    credits: float = 1000.0
    manpower: int = 100
    influence: float = 50.0
    tech_level: float = 1.0
    
    # Territory
    controlled_districts: List[str] = field(default_factory=list)
    buildings_owned: List[str] = field(default_factory=list)
    
    # Diplomacy
    relationships: Dict[str, float] = field(default_factory=dict)  # faction_id -> trust (-1 to 1)
    alliances: List[str] = field(default_factory=list)
    at_war_with: List[str] = field(default_factory=list)
    trade_agreements: List[str] = field(default_factory=list)
    
    # Strategy
    primary_goal: FactionGoal = FactionGoal.SURVIVE
    aggression: float = 0.5  # 0 = peaceful, 1 = warlike
    expansion_rate: float = 0.5
    
    # NPCs
    leader_id: str = ""
    member_count: int = 0


# =============================================================================
# FACTION DEFINITIONS
# =============================================================================

FACTIONS = {
    "resistance": FactionState(
        id="resistance",
        name="The Resistance",
        credits=500,
        manpower=80,
        influence=30,
        tech_level=0.8,
        controlled_districts=["undercity", "old_quarter"],
        primary_goal=FactionGoal.LIBERATE,
        aggression=0.6,
        leader_id="zero_chen"
    ),
    
    "temple": FactionState(
        id="temple",
        name="Temple Authority",
        credits=5000,
        manpower=500,
        influence=80,
        tech_level=1.5,
        controlled_districts=["temple_district", "downtown", "spire"],
        primary_goal=FactionGoal.CONTROL,
        aggression=0.7,
        leader_id="high_priest"
    ),
    
    "criminal": FactionState(
        id="criminal",
        name="Shadow Syndicate",
        credits=3000,
        manpower=150,
        influence=40,
        tech_level=1.0,
        controlled_districts=["docks", "warehouse_district"],
        primary_goal=FactionGoal.PROFIT,
        aggression=0.5,
        leader_id="vex"
    ),
    
    "corporate": FactionState(
        id="corporate",
        name="Mega Consortium",
        credits=10000,
        manpower=200,
        influence=60,
        tech_level=2.0,
        controlled_districts=["business_district", "research_park"],
        primary_goal=FactionGoal.PROSPER,
        aggression=0.3,
        leader_id="director_kira"
    ),
    
    "civilian": FactionState(
        id="civilian",
        name="Citizens Coalition",
        credits=200,
        manpower=1000,
        influence=20,
        tech_level=0.5,
        controlled_districts=["residential_east", "residential_west", "market"],
        primary_goal=FactionGoal.SURVIVE,
        aggression=0.1,
        leader_id="mayor_lin"
    )
}


# =============================================================================
# STRATEGIC ACTIONS
# =============================================================================

class StrategicAction:
    """Base class for faction actions."""
    
    def __init__(self, faction_id: str, action_type: str, target: str = None):
        self.faction_id = faction_id
        self.action_type = action_type
        self.target = target
    
    def to_dict(self) -> dict:
        return {
            "faction": self.faction_id,
            "action": self.action_type,
            "target": self.target
        }


def get_available_actions(faction: FactionState, world_state: dict) -> List[StrategicAction]:
    """Get all actions this faction can take."""
    actions = []
    
    # BUILD actions (if have resources)
    if faction.credits >= 100 and faction.manpower >= 10:
        for district in faction.controlled_districts:
            actions.append(StrategicAction(faction.id, "build_outpost", district))
            actions.append(StrategicAction(faction.id, "build_generator", district))
        
    if faction.credits >= 500 and faction.manpower >= 50:
        for district in faction.controlled_districts:
            actions.append(StrategicAction(faction.id, "build_headquarters", district))
    
    # RECRUIT actions
    if faction.credits >= 50:
        actions.append(StrategicAction(faction.id, "recruit_members", None))
    
    # DIPLOMACY actions
    for other_id, other in FACTIONS.items():
        if other_id != faction.id:
            rel = faction.relationships.get(other_id, 0)
            
            if other_id not in faction.at_war_with:
                # Can propose trade
                if rel > -0.3:
                    actions.append(StrategicAction(faction.id, "propose_trade", other_id))
                
                # Can propose alliance
                if rel > 0.5 and other_id not in faction.alliances:
                    actions.append(StrategicAction(faction.id, "propose_alliance", other_id))
                
                # Can declare war
                if faction.aggression > 0.6 and rel < -0.3:
                    actions.append(StrategicAction(faction.id, "declare_war", other_id))
            else:
                # Already at war - can offer peace
                if rel > -0.8:
                    actions.append(StrategicAction(faction.id, "offer_peace", other_id))
    
    # EXPANSION actions
    contested_districts = world_state.get("contested_districts", [])
    for district in contested_districts:
        if district not in faction.controlled_districts:
            actions.append(StrategicAction(faction.id, "claim_territory", district))
    
    # RESEARCH actions
    if faction.credits >= 200:
        actions.append(StrategicAction(faction.id, "research_tech", None))
    
    return actions


# =============================================================================
# AI DECISION MAKING
# =============================================================================

def evaluate_action(faction: FactionState, action: StrategicAction, 
                    world_state: dict, tick: int) -> float:
    """
    Score an action based on faction goals and current state.
    Higher score = better action.
    """
    score = 0.0
    goal = faction.primary_goal
    
    # Goal-based scoring
    if action.action_type == "build_outpost":
        if goal == FactionGoal.EXPAND:
            score += 80
        elif goal == FactionGoal.CONTROL:
            score += 60
        else:
            score += 30
    
    elif action.action_type == "build_generator":
        if goal == FactionGoal.PROSPER:
            score += 90
        else:
            score += 40
        # More valuable if low on credits
        if faction.credits < 500:
            score += 30
    
    elif action.action_type == "build_headquarters":
        if goal in [FactionGoal.DOMINATE, FactionGoal.CONTROL]:
            score += 100
        else:
            score += 50
    
    elif action.action_type == "recruit_members":
        if faction.manpower < 50:
            score += 100  # Critical need
        elif goal == FactionGoal.DOMINATE:
            score += 60
        else:
            score += 20
    
    elif action.action_type == "propose_trade":
        if goal == FactionGoal.PROSPER:
            score += 70
        elif goal == FactionGoal.PROFIT:
            score += 80
        else:
            score += 40
    
    elif action.action_type == "propose_alliance":
        target = action.target
        if target:
            # Ally with strong factions
            target_faction = FACTIONS.get(target)
            if target_faction:
                if target_faction.manpower > faction.manpower:
                    score += 60  # They're stronger
                if len(faction.at_war_with) > 0:
                    score += 80  # Need allies when at war
    
    elif action.action_type == "declare_war":
        if goal == FactionGoal.DOMINATE:
            score += 70
        elif goal == FactionGoal.LIBERATE and action.target == "temple":
            score += 100  # Resistance vs Temple
        else:
            score += 20
        
        # Don't declare war if weak
        if faction.manpower < 50:
            score -= 100
    
    elif action.action_type == "claim_territory":
        if goal == FactionGoal.EXPAND:
            score += 90
        elif goal == FactionGoal.CONTROL:
            score += 70
        else:
            score += 40
    
    elif action.action_type == "research_tech":
        if goal == FactionGoal.PROSPER:
            score += 60
        else:
            score += 30
        # More valuable if behind
        if faction.tech_level < 1.0:
            score += 40
    
    # Add some deterministic randomness for variety
    seed = f"{faction.id}_{action.action_type}_{action.target}_{tick}"
    variance = (deterministic_hash(seed) % 40) - 20  # -20 to +20
    score += variance
    
    return max(0, score)


def choose_faction_action(faction: FactionState, world_state: dict, 
                          tick: int) -> Optional[StrategicAction]:
    """
    AI chooses the best action for this faction.
    Returns None if no good actions available.
    """
    actions = get_available_actions(faction, world_state)
    
    if not actions:
        return None
    
    # Score all actions
    scored = [(action, evaluate_action(faction, action, world_state, tick)) 
              for action in actions]
    
    # Sort by score
    scored.sort(key=lambda x: x[1], reverse=True)
    
    # Only take action if score is high enough
    best_action, best_score = scored[0]
    
    if best_score < 30:
        return None  # No good options, do nothing
    
    # Add some chance to pick 2nd or 3rd best for variety
    seed = f"{faction.id}_action_choice_{tick}"
    if len(scored) >= 3 and deterministic_chance(0.2, seed):
        return scored[deterministic_hash(seed + "_pick") % 3][0]
    
    return best_action


# =============================================================================
# ACTION EXECUTION
# =============================================================================

def execute_faction_action(faction: FactionState, action: StrategicAction,
                           world_state: dict, tick: int) -> dict:
    """
    Execute an action and return the results.
    """
    result = {
        "faction": faction.id,
        "action": action.action_type,
        "target": action.target,
        "tick": tick,
        "success": False,
        "events": []
    }
    
    if action.action_type == "build_outpost":
        if faction.credits >= 100 and faction.manpower >= 10:
            faction.credits -= 100
            faction.manpower -= 10
            building_id = f"outpost_{faction.id}_{tick}"
            faction.buildings_owned.append(building_id)
            result["success"] = True
            result["building_id"] = building_id
            result["events"].append({
                "type": "building_constructed",
                "faction": faction.id,
                "building": building_id,
                "district": action.target
            })
    
    elif action.action_type == "build_generator":
        if faction.credits >= 150:
            faction.credits -= 150
            building_id = f"generator_{faction.id}_{tick}"
            faction.buildings_owned.append(building_id)
            result["success"] = True
            result["income_bonus"] = 20  # +20 credits per tick
    
    elif action.action_type == "recruit_members":
        if faction.credits >= 50:
            faction.credits -= 50
            recruited = 10 + (deterministic_hash(f"{faction.id}_recruit_{tick}") % 10)
            faction.manpower += recruited
            result["success"] = True
            result["recruited"] = recruited
    
    elif action.action_type == "propose_trade":
        target = FACTIONS.get(action.target)
        if target:
            # Target accepts based on relationship
            rel = target.relationships.get(faction.id, 0)
            accept_chance = 0.5 + rel * 0.3
            
            if deterministic_chance(accept_chance, f"trade_{faction.id}_{action.target}_{tick}"):
                if faction.id not in target.trade_agreements:
                    target.trade_agreements.append(faction.id)
                if action.target not in faction.trade_agreements:
                    faction.trade_agreements.append(action.target)
                
                # Improve relations
                faction.relationships[action.target] = min(1, rel + 0.1)
                target.relationships[faction.id] = min(1, rel + 0.1)
                
                result["success"] = True
                result["events"].append({
                    "type": "trade_agreement",
                    "faction1": faction.id,
                    "faction2": action.target
                })
            else:
                result["events"].append({
                    "type": "trade_rejected",
                    "proposer": faction.id,
                    "target": action.target
                })
    
    elif action.action_type == "declare_war":
        target = FACTIONS.get(action.target)
        if target and action.target not in faction.at_war_with:
            faction.at_war_with.append(action.target)
            target.at_war_with.append(faction.id)
            
            # Break alliances
            if action.target in faction.alliances:
                faction.alliances.remove(action.target)
            if faction.id in target.alliances:
                target.alliances.remove(faction.id)
            
            # Break trade
            if action.target in faction.trade_agreements:
                faction.trade_agreements.remove(action.target)
            if faction.id in target.trade_agreements:
                target.trade_agreements.remove(faction.id)
            
            # Set relationship to hostile
            faction.relationships[action.target] = -1.0
            target.relationships[faction.id] = -0.8
            
            result["success"] = True
            result["events"].append({
                "type": "war_declared",
                "aggressor": faction.id,
                "defender": action.target
            })
    
    elif action.action_type == "propose_alliance":
        target = FACTIONS.get(action.target)
        if target:
            rel = target.relationships.get(faction.id, 0)
            accept_chance = 0.3 + rel * 0.5
            
            if deterministic_chance(accept_chance, f"alliance_{faction.id}_{action.target}_{tick}"):
                if action.target not in faction.alliances:
                    faction.alliances.append(action.target)
                if faction.id not in target.alliances:
                    target.alliances.append(faction.id)
                
                faction.relationships[action.target] = min(1, rel + 0.2)
                target.relationships[faction.id] = min(1, rel + 0.2)
                
                result["success"] = True
                result["events"].append({
                    "type": "alliance_formed",
                    "faction1": faction.id,
                    "faction2": action.target
                })
    
    elif action.action_type == "claim_territory":
        district = action.target
        # Check if contested
        if district in world_state.get("contested_districts", []):
            # Success based on influence and manpower
            claim_strength = faction.influence + faction.manpower * 0.1
            if deterministic_chance(min(0.8, claim_strength / 200), 
                                   f"claim_{faction.id}_{district}_{tick}"):
                faction.controlled_districts.append(district)
                world_state["contested_districts"].remove(district)
                result["success"] = True
                result["events"].append({
                    "type": "territory_claimed",
                    "faction": faction.id,
                    "district": district
                })
    
    elif action.action_type == "research_tech":
        if faction.credits >= 200:
            faction.credits -= 200
            tech_gain = 0.1 + (deterministic_hash(f"research_{faction.id}_{tick}") % 10) / 100
            faction.tech_level += tech_gain
            result["success"] = True
            result["tech_gain"] = tech_gain
    
    return result


# =============================================================================
# FACTION TICK PROCESSING
# =============================================================================

def process_faction_tick(faction_id: str, world_state: dict, tick: int) -> dict:
    """
    Process one tick for a faction.
    Returns actions taken and events generated.
    """
    faction = FACTIONS.get(faction_id)
    if not faction:
        return {"error": f"Unknown faction: {faction_id}"}
    
    result = {
        "faction": faction_id,
        "tick": tick,
        "actions": [],
        "events": [],
        "state_changes": {}
    }
    
    # 1. Collect income from trade agreements
    trade_income = len(faction.trade_agreements) * 10
    faction.credits += trade_income
    result["state_changes"]["trade_income"] = trade_income
    
    # 2. Collect income from buildings
    generators = [b for b in faction.buildings_owned if "generator" in b]
    building_income = len(generators) * 20
    faction.credits += building_income
    result["state_changes"]["building_income"] = building_income
    
    # 3. War costs
    war_cost = len(faction.at_war_with) * 50
    faction.credits -= war_cost
    result["state_changes"]["war_cost"] = war_cost
    
    # 4. Choose and execute action
    action = choose_faction_action(faction, world_state, tick)
    if action:
        action_result = execute_faction_action(faction, action, world_state, tick)
        result["actions"].append(action_result)
        result["events"].extend(action_result.get("events", []))
    
    return result


def process_all_factions(world_state: dict, tick: int) -> dict:
    """
    Process all factions for this tick.
    """
    results = {
        "tick": tick,
        "faction_actions": {},
        "events": [],
        "wars": [],
        "alliances": [],
        "trade_agreements": []
    }
    
    for faction_id in FACTIONS:
        faction_result = process_faction_tick(faction_id, world_state, tick)
        results["faction_actions"][faction_id] = faction_result
        results["events"].extend(faction_result.get("events", []))
    
    # Compile war/alliance/trade status
    for faction_id, faction in FACTIONS.items():
        for enemy in faction.at_war_with:
            war_pair = tuple(sorted([faction_id, enemy]))
            if war_pair not in results["wars"]:
                results["wars"].append(war_pair)
        
        for ally in faction.alliances:
            ally_pair = tuple(sorted([faction_id, ally]))
            if ally_pair not in results["alliances"]:
                results["alliances"].append(ally_pair)
    
    return results


# =============================================================================
# DEMO / TEST
# =============================================================================

if __name__ == "__main__":
    import json
    
    print("="*60)
    print("  FACTION AI SYSTEM - Galactic Civ Style")
    print("="*60)
    
    world_state = {
        "contested_districts": ["neutral_zone", "border_district"],
        "buildings": {}
    }
    
    # Initialize relationships
    for f1_id, f1 in FACTIONS.items():
        for f2_id, f2 in FACTIONS.items():
            if f1_id != f2_id:
                # Set initial relationships based on faction types
                if f1_id == "resistance" and f2_id == "temple":
                    f1.relationships[f2_id] = -0.8  # Enemies
                elif f1_id == "temple" and f2_id == "resistance":
                    f1.relationships[f2_id] = -0.8
                elif f1_id == "criminal":
                    f1.relationships[f2_id] = -0.2  # Slightly hostile to all
                else:
                    f1.relationships[f2_id] = 0.0  # Neutral
    
    print("\n📊 Initial Faction State:")
    for f_id, faction in FACTIONS.items():
        print(f"\n  {faction.name}:")
        print(f"    💰 Credits: {faction.credits}")
        print(f"    👥 Manpower: {faction.manpower}")
        print(f"    🎯 Goal: {faction.primary_goal.value}")
        print(f"    🏘️ Districts: {faction.controlled_districts}")
    
    print("\n" + "="*60)
    print("  Simulating 10 ticks...")
    print("="*60)
    
    for tick in range(10):
        print(f"\n--- Tick {tick} ---")
        result = process_all_factions(world_state, tick)
        
        for event in result["events"]:
            if event["type"] == "war_declared":
                print(f"  ⚔️ WAR! {event['aggressor']} declares war on {event['defender']}")
            elif event["type"] == "alliance_formed":
                print(f"  🤝 ALLIANCE: {event['faction1']} and {event['faction2']}")
            elif event["type"] == "trade_agreement":
                print(f"  💱 TRADE: {event['faction1']} ↔ {event['faction2']}")
            elif event["type"] == "building_constructed":
                print(f"  🏗️ BUILD: {event['faction']} built {event['building']}")
            elif event["type"] == "territory_claimed":
                print(f"  🚩 CLAIM: {event['faction']} took {event['district']}")
    
    print("\n" + "="*60)
    print("  Final State:")
    print("="*60)
    
    for f_id, faction in FACTIONS.items():
        print(f"\n  {faction.name}:")
        print(f"    💰 Credits: {faction.credits:.0f}")
        print(f"    👥 Manpower: {faction.manpower}")
        print(f"    🏘️ Districts: {faction.controlled_districts}")
        if faction.at_war_with:
            print(f"    ⚔️ At war with: {faction.at_war_with}")
        if faction.alliances:
            print(f"    🤝 Allied with: {faction.alliances}")
        if faction.trade_agreements:
            print(f"    💱 Trading with: {faction.trade_agreements}")

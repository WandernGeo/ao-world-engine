#!/usr/bin/env python3
"""
ADVANCED AI SYSTEMS
====================

Implementation of game AI concepts from:
- Dwarf Fortress: Interlocking needs, personality quirks
- RimWorld: AI Storyteller, Utility System
- STALKER: A-Life autonomous roaming
- Crusader Kings: Hidden schemes, ambitions
- General: GOAP (Goal-Oriented Action Planning)

All deterministic for Arweave/AO compatibility.
"""

import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

# =============================================================================
# DETERMINISTIC UTILITIES
# =============================================================================

def deterministic_hash(seed: str) -> int:
    return int(hashlib.sha256(seed.encode()).hexdigest(), 16)

def deterministic_chance(prob: float, seed: str) -> bool:
    return (deterministic_hash(seed) % 10000) < (prob * 10000)

def deterministic_choice(items: list, seed: str) -> Any:
    if not items:
        return None
    return items[deterministic_hash(seed) % len(items)]

def deterministic_range(min_v: int, max_v: int, seed: str) -> int:
    return min_v + (deterministic_hash(seed) % (max_v - min_v + 1))


# =============================================================================
# 1. UTILITY SYSTEM (RimWorld-style)
# =============================================================================
# The Utility System scores all possible actions and picks the best one.
# Each action has a "utility" score based on current state.

class UtilityAction(Enum):
    """All possible NPC actions."""
    EAT = "eat"
    SLEEP = "sleep"
    WORK = "work"
    SOCIALIZE = "socialize"
    FLEE = "flee"
    FIGHT = "fight"
    TRADE = "trade"
    PATROL = "patrol"
    HIDE = "hide"
    SCHEME = "scheme"
    HELP_FRIEND = "help_friend"
    AVOID_ENEMY = "avoid_enemy"
    SEEK_ENTERTAINMENT = "seek_entertainment"
    RECRUIT = "recruit"  # For faction leaders


def calculate_utility(action: UtilityAction, npc: dict, world: dict, tick: int) -> float:
    """
    Calculate the utility score for an action.
    Higher score = more likely to be chosen.
    
    Inspired by RimWorld's colonist AI.
    """
    needs = npc.get("needs", {})
    personality = npc.get("personality", {})
    relationships = npc.get("relationships", {})
    location = npc.get("location", "")
    
    hunger = needs.get("hunger", 50)
    energy = needs.get("energy", 50)
    social = needs.get("social", 50)
    safety = needs.get("safety", 50)
    
    # Base utility scores
    utilities = {
        UtilityAction.EAT: max(0, (100 - hunger) * 2),  # More utility when hungry
        UtilityAction.SLEEP: max(0, (100 - energy) * 2),  # More utility when tired
        UtilityAction.WORK: 30 if 8 <= (tick % 24) <= 18 else 5,  # Work hours
        UtilityAction.SOCIALIZE: max(0, (100 - social) * 1.5),
        UtilityAction.FLEE: 100 if safety < 20 else 0,
        UtilityAction.FIGHT: 50 if safety < 30 and personality.get("aggression", 0.5) > 0.6 else 0,
        UtilityAction.TRADE: 20 if has_tradeable_items(npc) else 0,
        UtilityAction.PATROL: 25 if npc.get("job") in ["guard", "enforcer"] else 0,
        UtilityAction.HIDE: 80 if safety < 15 and personality.get("aggression", 0.5) < 0.4 else 0,
        UtilityAction.SCHEME: 15 if personality.get("ambition", 0) > 0.7 else 0,
        UtilityAction.HELP_FRIEND: calculate_help_friend_utility(npc, relationships, world),
        UtilityAction.AVOID_ENEMY: calculate_avoid_enemy_utility(npc, relationships, world),
        UtilityAction.SEEK_ENTERTAINMENT: max(0, (100 - needs.get("entertainment", 50)) * 1.2),
        UtilityAction.RECRUIT: 20 if npc.get("faction_rank", 0) > 5 else 0,
    }
    
    return utilities.get(action, 0)


def calculate_help_friend_utility(npc: dict, relationships: dict, world: dict) -> float:
    """Check if a friend needs help."""
    for friend_id, rel in relationships.items():
        if rel.get("trust", 0) > 0.7:
            friend = world.get("npcs_by_id", {}).get(friend_id)
            if friend:
                friend_safety = friend.get("needs", {}).get("safety", 100)
                if friend_safety < 30:
                    return 90  # High priority to help friend
    return 0


def calculate_avoid_enemy_utility(npc: dict, relationships: dict, world: dict) -> float:
    """Check if an enemy is nearby."""
    for enemy_id, rel in relationships.items():
        if rel.get("trust", 0) < 0.2 or rel.get("hostile", False):
            enemy = world.get("npcs_by_id", {}).get(enemy_id)
            if enemy and enemy.get("location") == npc.get("location"):
                return 70  # Want to avoid
    return 0


def has_tradeable_items(npc: dict) -> bool:
    """Check if NPC has items to trade."""
    inventory = npc.get("economy", {}).get("inventory", {})
    return len(inventory) > 0


def pick_best_action(npc: dict, world: dict, tick: int) -> UtilityAction:
    """Select the action with highest utility."""
    scored_actions = [
        (action, calculate_utility(action, npc, world, tick))
        for action in UtilityAction
    ]
    
    # Sort by utility
    scored_actions.sort(key=lambda x: x[1], reverse=True)
    
    # Add some randomness to prevent repetitive behavior
    # Pick from top 3 with weighted probability
    top_3 = scored_actions[:3]
    total_utility = sum(u for _, u in top_3)
    
    if total_utility == 0:
        return UtilityAction.SOCIALIZE  # Default
    
    roll = deterministic_hash(f"{npc.get('id')}_{tick}_action") % int(total_utility + 1)
    cumulative = 0
    
    for action, utility in top_3:
        cumulative += utility
        if roll <= cumulative:
            return action
    
    return top_3[0][0]


# =============================================================================
# 2. GOAP - Goal-Oriented Action Planning
# =============================================================================
# NPCs have high-level goals and plan sequences of actions to achieve them.

@dataclass
class Goal:
    """A high-level goal the NPC wants to achieve."""
    name: str
    priority: float  # 0-100
    target_state: Dict[str, Any]  # Desired world state
    

@dataclass
class Action:
    """An action that can be taken to change state."""
    name: str
    preconditions: Dict[str, Any]  # Required state
    effects: Dict[str, Any]  # State changes
    cost: float  # Lower = preferred


# Default action library
GOAP_ACTIONS = [
    Action("go_to_market", {"has_money": True}, {"at_location": "market"}, 1.0),
    Action("go_home", {}, {"at_location": "home"}, 1.0),
    Action("go_to_bar", {"has_money": True}, {"at_location": "bar"}, 1.0),
    Action("buy_food", {"at_location": "market", "has_money": True}, {"has_food": True}, 2.0),
    Action("eat_food", {"has_food": True}, {"hunger": "full"}, 1.0),
    Action("find_job", {"has_job": False}, {"has_job": True}, 5.0),
    Action("work", {"has_job": True, "at_location": "workplace"}, {"has_money": True}, 3.0),
    Action("sleep", {"at_location": "home"}, {"energy": "rested"}, 4.0),
    Action("socialize", {"at_location": "bar"}, {"social": "fulfilled"}, 2.0),
    Action("steal_food", {"at_location": "market"}, {"has_food": True, "wanted": True}, 1.5),
    Action("hide", {}, {"safe": True, "visible": False}, 1.0),
    Action("attack", {"has_weapon": True, "enemy_nearby": True}, {"enemy_defeated": True}, 4.0),
    Action("join_faction", {}, {"has_faction": True}, 3.0),
]


def matches_state(current: dict, required: dict) -> bool:
    """Check if current state satisfies required conditions."""
    for key, value in required.items():
        if current.get(key) != value:
            return False
    return True


def apply_effects(state: dict, effects: dict) -> dict:
    """Apply action effects to state."""
    new_state = state.copy()
    for key, value in effects.items():
        new_state[key] = value
    return new_state


def plan_actions(current_state: dict, goal: Goal, max_depth: int = 10) -> List[Action]:
    """
    A* search to find action sequence to achieve goal.
    Returns list of actions or empty if no plan found.
    """
    from heapq import heappush, heappop
    
    # Priority queue: (cost, depth, state, action_sequence)
    queue = [(0, 0, current_state, [])]
    visited = set()
    
    while queue:
        cost, depth, state, actions = heappop(queue)
        
        # Check if goal achieved
        if matches_state(state, goal.target_state):
            return actions
        
        # Depth limit
        if depth >= max_depth:
            continue
        
        # Create state hash for visited check
        state_hash = hash(frozenset(state.items()))
        if state_hash in visited:
            continue
        visited.add(state_hash)
        
        # Try all available actions
        for action in GOAP_ACTIONS:
            if matches_state(state, action.preconditions):
                new_state = apply_effects(state, action.effects)
                new_cost = cost + action.cost
                heappush(queue, (new_cost, depth + 1, new_state, actions + [action]))
    
    return []  # No plan found


def get_npc_current_goal(npc: dict, tick: int) -> Optional[Goal]:
    """Determine NPC's current high-level goal."""
    needs = npc.get("needs", {})
    
    # Priority: survival > comfort > social > ambition
    if needs.get("hunger", 50) < 20:
        return Goal("satisfy_hunger", 100, {"hunger": "full"})
    
    if needs.get("energy", 50) < 15:
        return Goal("get_rest", 90, {"energy": "rested"})
    
    if needs.get("safety", 50) < 20:
        return Goal("find_safety", 95, {"safe": True})
    
    if needs.get("social", 50) < 30:
        return Goal("socialize", 60, {"social": "fulfilled"})
    
    # Ambition-based goals
    personality = npc.get("personality", {})
    if personality.get("ambition", 0) > 0.7:
        if not npc.get("faction"):
            return Goal("join_faction", 40, {"has_faction": True})
    
    # Default: work
    return Goal("earn_money", 50, {"has_money": True})


# =============================================================================
# 3. A-LIFE SYSTEM (STALKER-style)
# =============================================================================
# NPCs roam, hunt, and interact independently of the player.
# The world is divided into zones; NPCs migrate between them.

@dataclass
class Zone:
    """A geographic zone in the world."""
    id: str
    name: str
    danger_level: float  # 0-1
    resources: float  # 0-1 (food, loot)
    population: int
    connected_zones: List[str]
    faction_control: Optional[str] = None


# Zone network for RE:ECHO City
ZONES = {
    "undercity": Zone("undercity", "Undercity", 0.7, 0.3, 200, 
                      ["market", "docks", "old_quarter"], "resistance"),
    "market": Zone("market", "Central Market", 0.2, 0.8, 500,
                   ["undercity", "downtown", "temple_district"], None),
    "downtown": Zone("downtown", "Downtown", 0.3, 0.5, 800,
                     ["market", "temple_district", "business_district"], "temple"),
    "temple_district": Zone("temple_district", "Temple District", 0.4, 0.4, 300,
                            ["downtown", "market", "spire"], "temple"),
    "docks": Zone("docks", "The Docks", 0.6, 0.6, 150,
                  ["undercity", "warehouse_district"], "criminal"),
    "spire": Zone("spire", "The Spire", 0.1, 0.2, 50,
                  ["temple_district", "business_district"], "corporate"),
}


def calculate_zone_attractiveness(npc: dict, zone: Zone, tick: int) -> float:
    """How attractive is a zone to this NPC?"""
    score = 0.0
    
    faction = npc.get("faction")
    personality = npc.get("personality", {})
    needs = npc.get("needs", {})
    
    # Resources attract hungry NPCs
    if needs.get("hunger", 50) < 50:
        score += zone.resources * 30
    
    # Danger affects score based on personality
    aggression = personality.get("aggression", 0.5)
    if aggression > 0.6:
        score -= zone.danger_level * 10  # Brave NPCs don't mind danger
    else:
        score -= zone.danger_level * 30  # Timid NPCs avoid danger
    
    # Faction territory matters
    if zone.faction_control == faction:
        score += 25  # Feel safe in own territory
    elif zone.faction_control and zone.faction_control != faction:
        if faction in ["resistance", "temple"] and zone.faction_control in ["resistance", "temple"]:
            score -= 40  # Enemy territory
        else:
            score -= 10  # Neutral caution
    
    # Population affects social NPCs
    if needs.get("social", 50) < 50:
        score += zone.population / 50  # More people = more social opportunity
    
    return score


def decide_npc_migration(npc: dict, current_zone: str, tick: int) -> Optional[str]:
    """
    A-Life style: Should this NPC migrate to a different zone?
    Returns target zone or None to stay.
    """
    if current_zone not in ZONES:
        return None
    
    current = ZONES[current_zone]
    
    # Evaluate connected zones
    best_zone = None
    best_score = calculate_zone_attractiveness(npc, current, tick)
    
    for connected_id in current.connected_zones:
        if connected_id not in ZONES:
            continue
        connected = ZONES[connected_id]
        score = calculate_zone_attractiveness(npc, connected, tick)
        
        # Add migration cost (prefer staying)
        score -= 10
        
        if score > best_score:
            best_score = score
            best_zone = connected_id
    
    # Probabilistic migration
    if best_zone:
        if deterministic_chance(0.1, f"{npc.get('id')}_{tick}_migrate"):
            return best_zone
    
    return None


def process_alife_tick(npcs: List[dict], tick: int) -> List[dict]:
    """Process A-Life for all NPCs."""
    migrations = []
    
    for npc in npcs:
        current_zone = npc.get("zone", "market")
        new_zone = decide_npc_migration(npc, current_zone, tick)
        
        if new_zone:
            migrations.append({
                "npc_id": npc.get("id"),
                "from": current_zone,
                "to": new_zone,
                "tick": tick
            })
    
    return migrations


# =============================================================================
# 4. AI STORYTELLER (RimWorld-style)
# =============================================================================
# A meta-AI that controls pacing and drama, not just random events.

class StorytellerMode(Enum):
    CASSANDRA = "cassandra"  # Steady escalation
    RANDY = "randy"  # Chaotic, unpredictable
    PHOEBE = "phoebe"  # Peaceful, few challenges
    CUSTOM = "custom"


@dataclass
class StorytellerState:
    """Current state of the storyteller."""
    mode: StorytellerMode = StorytellerMode.CASSANDRA
    tension: float = 0.3  # Current dramatic tension
    last_major_event_tick: int = 0
    recent_events: List[str] = field(default_factory=list)
    story_arc: str = "rising"  # "rising", "climax", "falling", "calm"


STORY_EVENTS = {
    # Tension builders
    "small_raid": {"tension_change": 0.1, "min_tension": 0.2},
    "supply_shortage": {"tension_change": 0.15, "min_tension": 0.1},
    "mysterious_stranger": {"tension_change": 0.05, "min_tension": 0.0},
    "faction_threat": {"tension_change": 0.2, "min_tension": 0.3},
    
    # Climax events
    "major_attack": {"tension_change": -0.3, "min_tension": 0.7, "is_climax": True},
    "betrayal": {"tension_change": -0.25, "min_tension": 0.6, "is_climax": True},
    "revolution": {"tension_change": -0.4, "min_tension": 0.8, "is_climax": True},
    
    # Resolution events
    "peace_treaty": {"tension_change": -0.2, "max_tension": 0.5},
    "celebration": {"tension_change": -0.15, "max_tension": 0.4},
    "new_ally": {"tension_change": -0.1, "max_tension": 0.6},
    
    # Neutral events
    "new_npc_arrives": {"tension_change": 0.0},
    "weather_change": {"tension_change": 0.0},
    "trade_opportunity": {"tension_change": 0.0},
}


def storyteller_pick_event(state: StorytellerState, world: dict, tick: int) -> Optional[str]:
    """
    Pick the next story event based on dramatic needs.
    
    Key insight: Good stories have PACING.
    - Build tension gradually
    - Release with climax events
    - Allow breathing room
    """
    ticks_since_major = tick - state.last_major_event_tick
    
    if state.mode == StorytellerMode.CASSANDRA:
        # Cassandra: Steady escalation
        if state.story_arc == "rising":
            # Build tension
            if state.tension < 0.7:
                eligible = [e for e, d in STORY_EVENTS.items() 
                           if d.get("tension_change", 0) > 0 
                           and state.tension >= d.get("min_tension", 0)]
                if eligible:
                    event = deterministic_choice(eligible, f"story_{tick}")
                    return event
            else:
                state.story_arc = "climax"
        
        elif state.story_arc == "climax":
            # Major event
            eligible = [e for e, d in STORY_EVENTS.items() if d.get("is_climax")]
            if eligible:
                event = deterministic_choice(eligible, f"climax_{tick}")
                state.story_arc = "falling"
                state.last_major_event_tick = tick
                return event
        
        elif state.story_arc == "falling":
            # Resolution
            if ticks_since_major > 500:
                eligible = [e for e, d in STORY_EVENTS.items()
                           if d.get("tension_change", 0) < 0
                           and state.tension <= d.get("max_tension", 1)]
                if eligible:
                    event = deterministic_choice(eligible, f"falling_{tick}")
                    if state.tension < 0.3:
                        state.story_arc = "calm"
                    return event
        
        elif state.story_arc == "calm":
            # Breathing room before next arc
            if ticks_since_major > 1000:
                state.story_arc = "rising"
    
    elif state.mode == StorytellerMode.RANDY:
        # Randy: Pure chaos
        if deterministic_chance(0.02, f"randy_{tick}"):
            event = deterministic_choice(list(STORY_EVENTS.keys()), f"randy_event_{tick}")
            return event
    
    elif state.mode == StorytellerMode.PHOEBE:
        # Phoebe: Mostly peaceful
        if deterministic_chance(0.005, f"phoebe_{tick}"):
            peaceful = [e for e, d in STORY_EVENTS.items() 
                       if d.get("tension_change", 0) <= 0]
            if peaceful:
                return deterministic_choice(peaceful, f"phoebe_event_{tick}")
    
    return None


def process_storyteller_tick(state: StorytellerState, world: dict, tick: int) -> Optional[dict]:
    """Run storyteller logic for this tick."""
    event_name = storyteller_pick_event(state, world, tick)
    
    if event_name:
        event_data = STORY_EVENTS.get(event_name, {})
        
        # Update tension
        state.tension += event_data.get("tension_change", 0)
        state.tension = max(0, min(1, state.tension))
        
        # Record event
        state.recent_events.append(event_name)
        state.recent_events = state.recent_events[-20:]
        
        return {
            "type": "story_event",
            "event": event_name,
            "tick": tick,
            "tension_after": state.tension,
            "arc": state.story_arc
        }
    
    return None


# =============================================================================
# 5. PERSONALITY QUIRKS (Dwarf Fortress-style)
# =============================================================================
# Each NPC has quirks that create emergent behavior.

PERSONALITY_QUIRKS = {
    "alcoholic": {
        "trigger_conditions": [
            {"type": "near_location", "location_type": "bar"},
            {"type": "stress_above", "threshold": 60}
        ],
        "behavior_override": "seek_drink",
        "effects": {"social": +10, "energy": -5, "gep": -10}
    },
    "paranoid": {
        "trigger_conditions": [
            {"type": "stranger_nearby"},
            {"type": "night_time"}
        ],
        "behavior_override": "hide",
        "effects": {"trust_all": -0.05, "safety_perception": -20}
    },
    "romantic": {
        "trigger_conditions": [
            {"type": "attractive_npc_nearby"},
            {"type": "social_below", "threshold": 40}
        ],
        "behavior_override": "flirt",
        "effects": {"social": +15, "target_impression": +0.1}
    },
    "violent": {
        "trigger_conditions": [
            {"type": "argument_occurred"},
            {"type": "enemy_nearby"}
        ],
        "behavior_override": "attack",
        "effects": {"safety": -10, "reputation": -0.1}
    },
    "kleptomaniac": {
        "trigger_conditions": [
            {"type": "near_valuables"},
            {"type": "unobserved"}
        ],
        "behavior_override": "steal",
        "effects": {"gep": +20, "reputation": -0.2}
    },
    "ambitious": {
        "trigger_conditions": [
            {"type": "faction_rank_below", "threshold": 5},
            {"type": "opportunity_available"}
        ],
        "behavior_override": "scheme",
        "effects": {"faction_progress": +0.1, "trust_rivals": -0.1}
    },
    "loyal": {
        "trigger_conditions": [
            {"type": "friend_in_danger"},
            {"type": "faction_attacked"}
        ],
        "behavior_override": "defend",
        "effects": {"trust_from_friends": +0.1, "danger": +0.2}
    },
    "greedy": {
        "trigger_conditions": [
            {"type": "trade_opportunity"},
            {"type": "gep_below", "threshold": 100}
        ],
        "behavior_override": "hard_bargain",
        "effects": {"gep": +15, "trust_trader": -0.05}
    }
}


def check_quirk_trigger(quirk_name: str, npc: dict, world: dict, tick: int) -> bool:
    """Check if a personality quirk should trigger."""
    quirk = PERSONALITY_QUIRKS.get(quirk_name)
    if not quirk:
        return False
    
    for condition in quirk.get("trigger_conditions", []):
        cond_type = condition.get("type")
        
        if cond_type == "near_location":
            location_type = condition.get("location_type")
            current_loc = world.get("locations", {}).get(npc.get("location", ""), {})
            if current_loc.get("type") != location_type:
                return False
        
        elif cond_type == "stress_above":
            stress = 100 - npc.get("needs", {}).get("safety", 50)
            if stress <= condition.get("threshold", 0):
                return False
        
        elif cond_type == "night_time":
            hour = tick % 24
            if not (22 <= hour or hour < 6):
                return False
        
        elif cond_type == "stranger_nearby":
            nearby = get_npcs_at_location(npc.get("location"), world)
            strangers = [n for n in nearby if npc.get("relationships", {}).get(n.get("id"), {}).get("familiarity", 0) < 0.2]
            if not strangers:
                return False
    
    return True


def get_npcs_at_location(location: str, world: dict) -> List[dict]:
    """Get all NPCs at a location."""
    return [n for n in world.get("npcs", []) if n.get("location") == location]


def process_personality_quirks(npc: dict, world: dict, tick: int) -> Optional[dict]:
    """Check if any quirk triggers for this NPC."""
    quirks = npc.get("personality_quirks", [])
    
    for quirk_name in quirks:
        if check_quirk_trigger(quirk_name, npc, world, tick):
            quirk = PERSONALITY_QUIRKS.get(quirk_name)
            return {
                "type": "quirk_triggered",
                "npc": npc.get("id"),
                "quirk": quirk_name,
                "behavior": quirk.get("behavior_override"),
                "effects": quirk.get("effects", {}),
                "tick": tick
            }
    
    return None


# =============================================================================
# 6. APOPHENIA SUPPORT
# =============================================================================
# Design patterns that encourage players to find patterns in chaos.

def generate_mysterious_event(tick: int, world: dict) -> dict:
    """
    Generate events that SEEM connected but are random.
    Players will create meaning from coincidences.
    """
    event_templates = [
        {"type": "mysterious_note", "content": "The {adjective} {animal} watches"},
        {"type": "strange_symbol", "location": "{location}", "found_by": "{npc}"},
        {"type": "power_outage", "district": "{district}", "duration": "{num} hours"},
        {"type": "disappearance", "npc": "{npc}", "last_seen": "{location}"},
        {"type": "rumor", "content": "They say {npc} knows about {secret}"},
    ]
    
    adjectives = ["crimson", "silent", "ancient", "hollow", "binary"]
    animals = ["crow", "snake", "spider", "wolf", "owl"]
    secrets = ["the collapse", "the watchers", "the code", "the signal", "the price"]
    
    template = deterministic_choice(event_templates, f"mystery_{tick}")
    
    # Fill in template
    event = template.copy()
    event["content"] = event.get("content", "").format(
        adjective=deterministic_choice(adjectives, f"adj_{tick}"),
        animal=deterministic_choice(animals, f"ani_{tick}"),
        secret=deterministic_choice(secrets, f"sec_{tick}"),
        npc=deterministic_choice([n.get("name", "unknown") for n in world.get("npcs", [])[:20]], f"npc_{tick}"),
        location=deterministic_choice(list(ZONES.keys()), f"loc_{tick}"),
        district=deterministic_choice(list(ZONES.keys()), f"dist_{tick}"),
        num=deterministic_range(1, 6, f"num_{tick}")
    )
    
    return event


# =============================================================================
# MAIN PROCESSING
# =============================================================================

def process_advanced_ai_tick(npc: dict, world: dict, tick: int) -> dict:
    """
    Process all advanced AI systems for one NPC tick.
    Returns all actions and events.
    """
    result = {
        "npc_id": npc.get("id"),
        "tick": tick,
        "utility_action": None,
        "goap_plan": [],
        "migration": None,
        "quirk_event": None,
    }
    
    # 1. Utility System: What to do RIGHT NOW
    best_action = pick_best_action(npc, world, tick)
    result["utility_action"] = best_action.value
    
    # 2. GOAP: What's my long-term plan?
    current_goal = get_npc_current_goal(npc, tick)
    if current_goal:
        # Build current state from NPC
        current_state = {
            "has_money": npc.get("economy", {}).get("gep", 0) > 10,
            "has_food": "food" in npc.get("economy", {}).get("inventory", {}),
            "at_location": npc.get("location", "unknown"),
            "hunger": "full" if npc.get("needs", {}).get("hunger", 50) > 80 else "hungry",
            "energy": "rested" if npc.get("needs", {}).get("energy", 50) > 80 else "tired",
        }
        plan = plan_actions(current_state, current_goal)
        result["goap_plan"] = [a.name for a in plan[:5]]  # First 5 steps
    
    # 3. A-Life: Should I migrate zones?
    migration = decide_npc_migration(npc, npc.get("zone", "market"), tick)
    if migration:
        result["migration"] = {"from": npc.get("zone"), "to": migration}
    
    # 4. Personality Quirks
    quirk_event = process_personality_quirks(npc, world, tick)
    if quirk_event:
        result["quirk_event"] = quirk_event
    
    return result


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    print("="*60)
    print("  ADVANCED AI SYSTEMS DEMO")
    print("="*60)
    
    # Create test NPC
    test_npc = {
        "id": "charlie",
        "name": "Charlie",
        "location": "market",
        "zone": "market",
        "faction": "resistance",
        "needs": {"hunger": 30, "energy": 60, "social": 40, "safety": 50},
        "personality": {"aggression": 0.6, "ambition": 0.8},
        "personality_quirks": ["ambitious", "loyal"],
        "relationships": {
            "felix": {"trust": 0.8, "familiarity": 0.9}
        },
        "economy": {"gep": 50, "inventory": {"tech_parts": 3}}
    }
    
    world = {
        "npcs": [test_npc],
        "npcs_by_id": {"charlie": test_npc},
        "locations": {"market": {"type": "market"}},
    }
    
    print("\n📋 Test NPC: Charlie")
    print(f"   Hunger: {test_npc['needs']['hunger']}")
    print(f"   Energy: {test_npc['needs']['energy']}")
    print(f"   Quirks: {test_npc['personality_quirks']}")
    
    # Test Utility System
    print("\n🎯 UTILITY SYSTEM")
    for action in UtilityAction:
        utility = calculate_utility(action, test_npc, world, 100)
        if utility > 0:
            print(f"   {action.value}: {utility:.1f}")
    
    best = pick_best_action(test_npc, world, 100)
    print(f"   → Best action: {best.value}")
    
    # Test GOAP
    print("\n📝 GOAP PLANNING")
    goal = get_npc_current_goal(test_npc, 100)
    print(f"   Current goal: {goal.name if goal else 'None'}")
    
    if goal:
        current_state = {
            "has_money": True,
            "has_food": False,
            "at_location": "market",
            "hunger": "hungry"
        }
        plan = plan_actions(current_state, goal)
        print(f"   Plan: {' → '.join(a.name for a in plan)}")
    
    # Test A-Life
    print("\n🗺️ A-LIFE MIGRATION")
    migration = decide_npc_migration(test_npc, "market", 100)
    print(f"   Should migrate: {migration or 'No'}")
    
    # Test Storyteller
    print("\n📖 STORYTELLER")
    storyteller = StorytellerState()
    for tick in range(0, 3000, 100):
        event = process_storyteller_tick(storyteller, world, tick)
        if event:
            print(f"   Tick {tick}: {event['event']} (tension: {event['tension_after']:.2f}, arc: {event['arc']})")
    
    # Test Personality Quirks
    print("\n🎭 PERSONALITY QUIRKS")
    quirk = process_personality_quirks(test_npc, world, 100)
    if quirk:
        print(f"   Triggered: {quirk['quirk']} → {quirk['behavior']}")
    else:
        print("   No quirks triggered")
    
    print("\n" + "="*60)
    print("  ✅ All systems operational")
    print("="*60)


# =============================================================================
# 7. SOCIAL GROUPS (The Sims-style)
# =============================================================================
# NPCs form and join social groups: cliques, clubs, gangs, families.
# Groups influence behavior and create emergent social dynamics.

class GroupType(Enum):
    FAMILY = "family"           # Blood/chosen family
    GANG = "gang"               # Criminal organization
    CLUB = "club"               # Hobby/interest group
    FACTION = "faction"         # Political/ideological
    WORK = "work"               # Coworkers
    FRIENDS = "friends"         # Casual friend group
    CULT = "cult"               # Religious/ideological extreme


@dataclass
class SocialGroup:
    """A social group that NPCs can belong to."""
    id: str
    name: str
    group_type: GroupType
    leader_id: Optional[str] = None
    members: List[str] = field(default_factory=list)
    reputation: float = 0.5         # 0-1 public standing
    resources: float = 0.0          # Shared wealth
    territory: List[str] = field(default_factory=list)
    rivals: List[str] = field(default_factory=list)
    allies: List[str] = field(default_factory=list)
    founded_tick: int = 0
    ideology: Dict[str, float] = field(default_factory=dict)


def calculate_group_cohesion(group: SocialGroup, npcs_by_id: dict) -> float:
    """
    How unified is this group? Based on:
    - Average trust between members
    - Leader approval
    - Shared ideology
    """
    if len(group.members) < 2:
        return 1.0
    
    total_trust = 0
    trust_count = 0
    
    for member_id in group.members:
        member = npcs_by_id.get(member_id, {})
        relationships = member.get("relationships", {})
        
        for other_id in group.members:
            if other_id != member_id:
                trust = relationships.get(other_id, {}).get("trust", 0.5)
                total_trust += trust
                trust_count += 1
    
    avg_trust = total_trust / trust_count if trust_count > 0 else 0.5
    
    # Leader approval bonus
    leader_bonus = 0
    if group.leader_id:
        for member_id in group.members:
            member = npcs_by_id.get(member_id, {})
            leader_trust = member.get("relationships", {}).get(group.leader_id, {}).get("trust", 0.5)
            leader_bonus += leader_trust
        leader_bonus = (leader_bonus / len(group.members)) * 0.2
    
    return min(1.0, avg_trust + leader_bonus)


def process_group_meeting(group: SocialGroup, tick: int, npcs_by_id: dict) -> List[dict]:
    """
    When group members meet, relationships strengthen.
    Returns list of relationship changes.
    """
    changes = []
    
    # Members bond
    for m1_id in group.members:
        for m2_id in group.members:
            if m1_id != m2_id:
                # Small trust increase from shared group
                trust_boost = 0.02 if group.group_type != GroupType.WORK else 0.01
                changes.append({
                    "type": "trust_change",
                    "npc_a": m1_id,
                    "npc_b": m2_id,
                    "change": trust_boost,
                    "reason": f"group_meeting_{group.id}"
                })
    
    # Group activities based on type
    if group.group_type == GroupType.GANG:
        # Plan activities
        if deterministic_chance(0.1, f"{group.id}_{tick}_heist"):
            changes.append({
                "type": "group_event",
                "group": group.id,
                "event": "planning_heist",
                "tick": tick
            })
    
    elif group.group_type == GroupType.FACTION:
        # Political planning
        if deterministic_chance(0.15, f"{group.id}_{tick}_politics"):
            changes.append({
                "type": "group_event",
                "group": group.id,
                "event": "political_meeting",
                "tick": tick
            })
    
    elif group.group_type == GroupType.FAMILY:
        # Family dinner strengthens bonds more
        for m1_id in group.members:
            for m2_id in group.members:
                if m1_id != m2_id:
                    changes.append({
                        "type": "trust_change",
                        "npc_a": m1_id,
                        "npc_b": m2_id,
                        "change": 0.03,  # Extra family bonus
                        "reason": "family_gathering"
                    })
    
    return changes


def check_leadership_challenge(group: SocialGroup, tick: int, npcs_by_id: dict) -> Optional[dict]:
    """
    High-ambition members may challenge for leadership.
    CK-style power dynamics.
    """
    if not group.leader_id or len(group.members) < 3:
        return None
    
    leader = npcs_by_id.get(group.leader_id, {})
    leader_authority = leader.get("personality", {}).get("authority", 0.5)
    
    for member_id in group.members:
        if member_id == group.leader_id:
            continue
        
        member = npcs_by_id.get(member_id, {})
        ambition = member.get("personality", {}).get("ambition", 0.5)
        member_support = 0
        
        # Check support from other members
        for other_id in group.members:
            if other_id in [member_id, group.leader_id]:
                continue
            other = npcs_by_id.get(other_id, {})
            # Compare trust in challenger vs leader
            trust_challenger = other.get("relationships", {}).get(member_id, {}).get("trust", 0.3)
            trust_leader = other.get("relationships", {}).get(group.leader_id, {}).get("trust", 0.5)
            if trust_challenger > trust_leader:
                member_support += 1
        
        support_ratio = member_support / (len(group.members) - 2) if len(group.members) > 2 else 0
        
        # Challenge if ambitious + support
        if ambition > 0.7 and support_ratio > 0.5:
            if deterministic_chance(0.05, f"{member_id}_{tick}_challenge"):
                return {
                    "type": "leadership_challenge",
                    "group": group.id,
                    "challenger": member_id,
                    "current_leader": group.leader_id,
                    "support_ratio": support_ratio,
                    "tick": tick
                }
    
    return None


def try_form_new_group(npc: dict, world: dict, tick: int) -> Optional[SocialGroup]:
    """
    NPCs may form new groups with friends who share interests.
    """
    npc_id = npc.get("id")
    relationships = npc.get("relationships", {})
    
    # Need charisma and ambition to form group
    charisma = npc.get("personality", {}).get("charisma", 0.5)
    ambition = npc.get("personality", {}).get("ambition", 0.5)
    
    if charisma < 0.6 or ambition < 0.5:
        return None
    
    # Find trusted friends
    potential_members = [npc_id]
    for other_id, rel in relationships.items():
        if rel.get("trust", 0) > 0.7:
            potential_members.append(other_id)
    
    # Need at least 3 people
    if len(potential_members) < 3:
        return None
    
    # Low chance per tick
    if not deterministic_chance(0.001, f"{npc_id}_{tick}_form_group"):
        return None
    
    # Determine group type based on NPC traits
    faction = npc.get("faction", "civilian")
    if faction in ["resistance", "temple"]:
        group_type = GroupType.FACTION
    elif npc.get("personality", {}).get("aggression", 0.5) > 0.7:
        group_type = GroupType.GANG
    else:
        group_type = GroupType.FRIENDS
    
    return SocialGroup(
        id=f"group_{npc_id}_{tick}",
        name=f"{npc.get('name', 'Unknown')}'s {group_type.value}",
        group_type=group_type,
        leader_id=npc_id,
        members=potential_members[:5],  # Max 5 founders
        founded_tick=tick
    )


# =============================================================================
# 8. LONG-TERM SCHEMES (Crusader Kings-style)
# =============================================================================
# NPCs pursue multi-tick plots: assassination, seduction, usurpation.

class SchemeType(Enum):
    ASSASSINATION = "assassination"     # Kill target
    SEDUCTION = "seduction"             # Romance target
    USURPATION = "usurpation"           # Take leadership
    SABOTAGE = "sabotage"               # Damage enemy faction
    RECRUITMENT = "recruitment"         # Convert target
    BLACKMAIL = "blackmail"             # Gain leverage
    BETRAYAL = "betrayal"               # Switch sides
    COUP = "coup"                       # Overthrow faction leader


@dataclass
class Scheme:
    """A long-term plot that unfolds over many ticks."""
    id: str
    scheme_type: SchemeType
    plotter_id: str
    target_id: str
    progress: float = 0.0               # 0-1
    discovery_risk: float = 0.1         # Chance of detection
    discovered: bool = False
    start_tick: int = 0
    agents: List[str] = field(default_factory=list)  # NPCs helping
    steps_completed: List[str] = field(default_factory=list)


SCHEME_DEFINITIONS = {
    SchemeType.ASSASSINATION: {
        "steps": ["gather_intel", "find_opportunity", "prepare_weapon", "execute"],
        "base_progress_per_tick": 0.01,
        "discovery_risk_base": 0.02,
        "success_threshold": 1.0,
        "consequence_failure": ["prison", "exile", "death"],
        "required_traits": {"aggression": 0.6, "planning": 0.5}
    },
    SchemeType.SEDUCTION: {
        "steps": ["observe", "approach", "charm", "intimate", "commitment"],
        "base_progress_per_tick": 0.02,
        "discovery_risk_base": 0.01,
        "success_threshold": 1.0,
        "consequence_failure": ["rejection", "scandal", "humiliation"],
        "required_traits": {"charisma": 0.6}
    },
    SchemeType.USURPATION: {
        "steps": ["build_support", "undermine_leader", "create_crisis", "seize_power"],
        "base_progress_per_tick": 0.005,
        "discovery_risk_base": 0.03,
        "success_threshold": 1.0,
        "consequence_failure": ["exile", "demotion", "execution"],
        "required_traits": {"ambition": 0.8, "planning": 0.6}
    },
    SchemeType.BLACKMAIL: {
        "steps": ["investigate", "find_secret", "document", "confront"],
        "base_progress_per_tick": 0.015,
        "discovery_risk_base": 0.015,
        "success_threshold": 1.0,
        "consequence_failure": ["exposure", "counter_blackmail"],
        "required_traits": {"cunning": 0.6}
    },
    SchemeType.COUP: {
        "steps": ["identify_loyalists", "secure_resources", "neutralize_guards", "strike"],
        "base_progress_per_tick": 0.003,
        "discovery_risk_base": 0.05,
        "success_threshold": 1.0,
        "consequence_failure": ["death", "faction_exile"],
        "required_traits": {"ambition": 0.9, "aggression": 0.7}
    }
}


def can_start_scheme(npc: dict, scheme_type: SchemeType) -> bool:
    """Check if NPC has required traits to start this scheme."""
    definition = SCHEME_DEFINITIONS.get(scheme_type, {})
    required = definition.get("required_traits", {})
    personality = npc.get("personality", {})
    
    for trait, min_value in required.items():
        if personality.get(trait, 0.5) < min_value:
            return False
    return True


def advance_scheme(scheme: Scheme, plotter: dict, target: dict, world: dict, tick: int) -> dict:
    """
    Advance a scheme by one tick.
    Returns result with progress, events, or conclusion.
    """
    definition = SCHEME_DEFINITIONS.get(scheme.scheme_type, {})
    
    result = {
        "scheme_id": scheme.id,
        "progress_before": scheme.progress,
        "events": [],
        "completed": False,
        "success": None
    }
    
    # Check for discovery
    discovery_chance = definition.get("discovery_risk_base", 0.01) * (1 + len(scheme.agents) * 0.2)
    if deterministic_chance(discovery_chance, f"{scheme.id}_{tick}_discover"):
        scheme.discovered = True
        result["events"].append({
            "type": "scheme_discovered",
            "scheme": scheme.id,
            "target": scheme.target_id,
            "tick": tick
        })
        return result
    
    # Progress the scheme
    plotter_skill = plotter.get("personality", {}).get("planning", 0.5)
    progress_modifier = 0.5 + plotter_skill
    scheme.progress += definition.get("base_progress_per_tick", 0.01) * progress_modifier
    
    # Mark completed steps
    steps = definition.get("steps", [])
    step_threshold = 1.0 / len(steps) if steps else 1.0
    completed_count = int(scheme.progress / step_threshold)
    for i in range(completed_count):
        if i < len(steps) and steps[i] not in scheme.steps_completed:
            scheme.steps_completed.append(steps[i])
            result["events"].append({
                "type": "scheme_step_complete",
                "scheme": scheme.id,
                "step": steps[i],
                "tick": tick
            })
    
    # Check for completion
    if scheme.progress >= definition.get("success_threshold", 1.0):
        result["completed"] = True
        
        # Success chance based on preparation
        success_chance = 0.5 + (len(scheme.agents) * 0.1) + (plotter_skill * 0.2)
        target_defense = target.get("personality", {}).get("vigilance", 0.5)
        success_chance -= target_defense * 0.3
        
        if deterministic_chance(success_chance, f"{scheme.id}_{tick}_success"):
            result["success"] = True
            result["events"].append({
                "type": "scheme_success",
                "scheme_type": scheme.scheme_type.value,
                "plotter": scheme.plotter_id,
                "target": scheme.target_id,
                "tick": tick
            })
        else:
            result["success"] = False
            consequences = definition.get("consequence_failure", [])
            consequence = deterministic_choice(consequences, f"{scheme.id}_fail") if consequences else "failure"
            result["events"].append({
                "type": "scheme_failure",
                "scheme_type": scheme.scheme_type.value,
                "plotter": scheme.plotter_id,
                "target": scheme.target_id,
                "consequence": consequence,
                "tick": tick
            })
    
    result["progress_after"] = scheme.progress
    return result


def consider_starting_scheme(npc: dict, world: dict, tick: int) -> Optional[Scheme]:
    """
    High-ambition NPCs may start schemes against rivals or leaders.
    """
    npc_id = npc.get("id")
    ambition = npc.get("personality", {}).get("ambition", 0.5)
    
    # Only ambitious NPCs scheme
    if ambition < 0.6:
        return None
    
    # Low base chance
    if not deterministic_chance(0.001, f"{npc_id}_{tick}_scheme"):
        return None
    
    relationships = npc.get("relationships", {})
    
    # Find potential targets
    for target_id, rel in relationships.items():
        trust = rel.get("trust", 0.5)
        
        # Enemy = assassination/sabotage target
        if trust < 0.2:
            if can_start_scheme(npc, SchemeType.ASSASSINATION):
                return Scheme(
                    id=f"scheme_{npc_id}_{target_id}_{tick}",
                    scheme_type=SchemeType.ASSASSINATION,
                    plotter_id=npc_id,
                    target_id=target_id,
                    start_tick=tick
                )
        
        # Attractive + romantic = seduction target
        elif rel.get("attraction", 0) > 0.6:
            if can_start_scheme(npc, SchemeType.SEDUCTION):
                return Scheme(
                    id=f"scheme_{npc_id}_{target_id}_{tick}",
                    scheme_type=SchemeType.SEDUCTION,
                    plotter_id=npc_id,
                    target_id=target_id,
                    start_tick=tick
                )
    
    # Consider usurpation against faction leader
    faction = npc.get("faction")
    if faction and ambition > 0.8:
        faction_data = world.get("factions", {}).get(faction, {})
        leader_id = faction_data.get("leader_id")
        if leader_id and leader_id != npc_id:
            if can_start_scheme(npc, SchemeType.USURPATION):
                return Scheme(
                    id=f"scheme_{npc_id}_{leader_id}_{tick}",
                    scheme_type=SchemeType.USURPATION,
                    plotter_id=npc_id,
                    target_id=leader_id,
                    start_tick=tick
                )
    
    return None


# =============================================================================
# 9. DYNASTY SYSTEM (Crusader Kings-style)
# =============================================================================
# Track family lineages, inheritance, and generational storytelling.

@dataclass
class Dynasty:
    """A family lineage spanning generations."""
    id: str
    family_name: str
    founder_id: str
    current_head_id: Optional[str] = None
    members: List[str] = field(default_factory=list)  # All living members
    deceased: List[str] = field(default_factory=list)
    wealth: float = 0.0           # Accumulated family wealth
    prestige: float = 0.5         # 0-1 reputation
    territories: List[str] = field(default_factory=list)
    rivals: List[str] = field(default_factory=list)    # Other dynasty IDs
    founded_tick: int = 0
    
    # Family traits that pass down
    family_traits: Dict[str, float] = field(default_factory=dict)


def calculate_inheritance(dynasty: Dynasty, deceased_member_id: str, npcs_by_id: dict) -> dict:
    """
    When a dynasty member dies, determine inheritance.
    Follows succession rules based on culture.
    """
    result = {
        "deceased": deceased_member_id,
        "inheritances": [],
        "new_head": None
    }
    
    deceased = npcs_by_id.get(deceased_member_id, {})
    personal_wealth = deceased.get("economy", {}).get("gep", 0)
    
    # Find heirs (children first, then siblings)
    relationships = deceased.get("relationships", {})
    children = [r for r_id, r in relationships.items() 
                if r.get("relation") == "child" and r_id in dynasty.members]
    siblings = [r for r_id, r in relationships.items() 
                if r.get("relation") == "sibling" and r_id in dynasty.members]
    
    heirs = children if children else siblings
    
    if heirs:
        # Split wealth among heirs
        share = personal_wealth / len(heirs)
        for heir_id in heirs:
            result["inheritances"].append({
                "heir": heir_id,
                "amount": share
            })
    else:
        # No heirs - goes to dynasty pool
        dynasty.wealth += personal_wealth
    
    # If deceased was head, find new head
    if dynasty.current_head_id == deceased_member_id:
        # Eldest child, or eldest sibling
        candidates = children if children else siblings
        if candidates:
            # Prefer high-prestige/charisma
            best_candidate = None
            best_score = -1
            for c_id in candidates:
                candidate = npcs_by_id.get(c_id, {})
                score = (candidate.get("personality", {}).get("charisma", 0.5) + 
                         candidate.get("personality", {}).get("ambition", 0.5))
                if score > best_score:
                    best_score = score
                    best_candidate = c_id
            result["new_head"] = best_candidate
    
    return result


def generate_family_traits(founder: dict) -> Dict[str, float]:
    """
    Family traits are partially inherited from founder,
    creating dynasties with distinct personalities.
    """
    founder_personality = founder.get("personality", {})
    
    # Extract dominant traits
    traits = {}
    for trait, value in founder_personality.items():
        if value > 0.6:  # Strong trait
            traits[trait] = value * 0.7  # Reduced in descendants
        elif value < 0.3:  # Strong absence
            traits[trait] = value * 1.3  # Also inherited
    
    return traits


def apply_dynasty_influence(npc: dict, dynasty: Dynasty) -> dict:
    """
    Dynasty membership influences NPC personality.
    Family traits blend with individual traits.
    """
    blend_strength = 0.3  # How much dynasty influences individual
    
    npc_personality = npc.get("personality", {}).copy()
    
    for trait, dynasty_value in dynasty.family_traits.items():
        if trait in npc_personality:
            # Blend dynasty with individual
            npc_personality[trait] = (
                npc_personality[trait] * (1 - blend_strength) +
                dynasty_value * blend_strength
            )
        else:
            # New trait from dynasty
            npc_personality[trait] = dynasty_value * blend_strength
    
    npc["personality"] = npc_personality
    return npc

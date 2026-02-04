#!/usr/bin/env python3
"""
CASCADING EVENTS SYSTEM
========================

emergent chain reactions where one event triggers others.

Examples:
- Robbery → Witnesses → Temple investigation → Curfew
- Murder → Family grief → Revenge plot → Gang war
- Echo discovery → Temple suppression → Resistance rally → Crackdown
"""

import json
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime

# Deterministic utilities
def deterministic_hash(seed: str) -> int:
    return int(hashlib.md5(str(seed).encode()).hexdigest()[:8], 16)

def deterministic_chance(prob: float, seed: str) -> bool:
    return (deterministic_hash(seed) % 1000) / 1000 < prob

def deterministic_choice(items: list, seed: str):
    if not items:
        return None
    return items[deterministic_hash(seed) % len(items)]


@dataclass
class CascadeEvent:
    """An event that can trigger other events."""
    id: str
    type: str
    tick: int
    location: str
    participants: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    triggered_by: Optional[str] = None
    triggers: List[str] = field(default_factory=list)


# Event chain definitions
EVENT_CHAINS = {
    # CRIME CHAINS
    "robbery": {
        "triggers": [
            {"event": "witness_report", "probability": 0.7, "delay": 0},
            {"event": "victim_trauma", "probability": 0.5, "delay": 0},
            {"event": "gang_reputation", "probability": 0.3, "delay": 0, "condition": "gang_involved"}
        ]
    },
    "witness_report": {
        "triggers": [
            {"event": "temple_investigation", "probability": 0.8, "delay": 5},
            {"event": "gossip_spread", "probability": 0.9, "delay": 2}
        ]
    },
    "temple_investigation": {
        "triggers": [
            {"event": "suspect_arrest", "probability": 0.4, "delay": 10},
            {"event": "area_patrol_increase", "probability": 0.6, "delay": 3},
            {"event": "curfew_imposed", "probability": 0.2, "delay": 5, "condition": "serious_crime"}
        ]
    },
    "suspect_arrest": {
        "triggers": [
            {"event": "trial", "probability": 0.8, "delay": 50},
            {"event": "jail_break_attempt", "probability": 0.1, "delay": 20, "condition": "gang_member"},
            {"event": "family_grief", "probability": 0.6, "delay": 1}
        ]
    },
    
    # VIOLENCE CHAINS
    "murder": {
        "triggers": [
            {"event": "body_discovery", "probability": 0.9, "delay": 5},
            {"event": "witness_flee", "probability": 0.4, "delay": 0},
            {"event": "murderer_guilt", "probability": 0.3, "delay": 10}
        ]
    },
    "body_discovery": {
        "triggers": [
            {"event": "temple_investigation", "probability": 0.95, "delay": 2},
            {"event": "family_notification", "probability": 0.9, "delay": 5},
            {"event": "gossip_spread", "probability": 0.95, "delay": 1}
        ]
    },
    "family_notification": {
        "triggers": [
            {"event": "family_grief", "probability": 1.0, "delay": 0},
            {"event": "revenge_vow", "probability": 0.3, "delay": 20, "condition": "violent_family"},
            {"event": "funeral_planned", "probability": 0.8, "delay": 30}
        ]
    },
    "revenge_vow": {
        "triggers": [
            {"event": "target_stalking", "probability": 0.6, "delay": 50},
            {"event": "hire_assassin", "probability": 0.2, "delay": 30},
            {"event": "gang_war_escalation", "probability": 0.3, "delay": 40, "condition": "gang_involved"}
        ]
    },
    
    # ECHO CHAINS (unique to RE:ECHO)
    "echo_discovery": {
        "triggers": [
            {"event": "temple_alert", "probability": 0.8, "delay": 5},
            {"event": "believer_pilgrimage", "probability": 0.5, "delay": 10},
            {"event": "resistance_interest", "probability": 0.7, "delay": 3},
            {"event": "news_coverage", "probability": 0.9, "delay": 1}
        ]
    },
    "temple_alert": {
        "triggers": [
            {"event": "echo_suppression", "probability": 0.7, "delay": 10},
            {"event": "area_lockdown", "probability": 0.4, "delay": 5},
            {"event": "inquisitor_dispatch", "probability": 0.5, "delay": 3}
        ]
    },
    "echo_suppression": {
        "triggers": [
            {"event": "resistance_protest", "probability": 0.6, "delay": 20},
            {"event": "underground_movement", "probability": 0.4, "delay": 30},
            {"event": "public_outrage", "probability": 0.3, "delay": 10}
        ]
    },
    "resistance_protest": {
        "triggers": [
            {"event": "temple_crackdown", "probability": 0.7, "delay": 5},
            {"event": "sympathizer_joining", "probability": 0.5, "delay": 15},
            {"event": "news_coverage", "probability": 0.8, "delay": 1}
        ]
    },
    "temple_crackdown": {
        "triggers": [
            {"event": "arrests", "probability": 0.8, "delay": 2},
            {"event": "injuries", "probability": 0.4, "delay": 0},
            {"event": "martyr_created", "probability": 0.1, "delay": 0, "condition": "lethal_force"},
            {"event": "public_fear", "probability": 0.6, "delay": 5}
        ]
    },
    
    # ECONOMIC CHAINS
    "business_opens": {
        "triggers": [
            {"event": "job_creation", "probability": 0.9, "delay": 5},
            {"event": "competition_response", "probability": 0.4, "delay": 20},
            {"event": "district_prosperity_up", "probability": 0.3, "delay": 50}
        ]
    },
    "business_closes": {
        "triggers": [
            {"event": "unemployment", "probability": 0.9, "delay": 0},
            {"event": "family_hardship", "probability": 0.7, "delay": 5},
            {"event": "crime_increase", "probability": 0.3, "delay": 30},
            {"event": "district_decline", "probability": 0.2, "delay": 50}
        ]
    },
    "market_crash": {
        "triggers": [
            {"event": "panic_selling", "probability": 0.7, "delay": 1},
            {"event": "business_closes", "probability": 0.4, "delay": 20},
            {"event": "suicide", "probability": 0.05, "delay": 10, "condition": "heavily_invested"},
            {"event": "riot", "probability": 0.2, "delay": 30}
        ]
    },
    
    # SOCIAL CHAINS
    "wedding": {
        "triggers": [
            {"event": "family_merger", "probability": 0.8, "delay": 0},
            {"event": "celebration", "probability": 0.9, "delay": 0},
            {"event": "jealousy", "probability": 0.2, "delay": 10}
        ]
    },
    "birth": {
        "triggers": [
            {"event": "family_celebration", "probability": 0.9, "delay": 0},
            {"event": "inheritance_change", "probability": 0.5, "delay": 0},
            {"event": "naming_ceremony", "probability": 0.7, "delay": 10}
        ]
    },
    "death_natural": {
        "triggers": [
            {"event": "family_grief", "probability": 1.0, "delay": 0},
            {"event": "inheritance_dispute", "probability": 0.3, "delay": 30},
            {"event": "funeral_planned", "probability": 0.9, "delay": 5}
        ]
    },
    
    # POLITICAL CHAINS
    "temple_decree": {
        "triggers": [
            {"event": "public_compliance", "probability": 0.6, "delay": 5},
            {"event": "resistance_opposition", "probability": 0.4, "delay": 10},
            {"event": "black_market_boom", "probability": 0.3, "delay": 20, "condition": "restrictive_decree"}
        ]
    },
    "resistance_attack": {
        "triggers": [
            {"event": "casualties", "probability": 0.7, "delay": 0},
            {"event": "temple_retaliation", "probability": 0.9, "delay": 10},
            {"event": "public_fear", "probability": 0.5, "delay": 5},
            {"event": "sympathizer_loss", "probability": 0.3, "delay": 20}
        ]
    }
}

# NPC reaction templates for cascading events
NPC_REACTIONS = {
    "witness_report": {
        "witness": "I saw what happened. Had to tell the Temple.",
        "bystander": "Someone went to report it. Good, I guess.",
        "criminal_ally": "Damn snitch. This is going to cause problems."
    },
    "temple_investigation": {
        "nervous": "Guards are asking questions. Best keep my head down.",
        "cooperative": "I told them what I know. Hope they catch whoever did it.",
        "suspicious": "Temple's snooping around. Wonder what they're really after."
    },
    "echo_discovery": {
        "believer": "Can you believe it? Real music! The Echoes are real!",
        "skeptic": "Another hoax. People will believe anything.",
        "curious": "I heard something happened. Some kind of sound..."
    },
    "temple_crackdown": {
        "fearful": "Stay inside. Don't draw attention. It's not safe out there.",
        "angry": "This is how they keep us down. Violence and fear.",
        "compliant": "The Temple knows best. Those people were troublemakers."
    },
    "family_grief": {
        "grieving": "I can't believe they're gone. Everything feels empty.",
        "supportive": "I'm so sorry for your loss. Is there anything I can do?",
        "practical": "Someone needs to handle the arrangements."
    }
}


def process_cascades(initial_event: CascadeEvent, world_state: dict, max_depth: int = 5) -> List[CascadeEvent]:
    """
    Process an initial event and generate all cascading events.
    Returns list of all events in the chain.
    """
    all_events = [initial_event]
    pending = [(initial_event, 0)]  # (event, depth)
    
    while pending:
        event, depth = pending.pop(0)
        
        if depth >= max_depth:
            continue
            
        chain_def = EVENT_CHAINS.get(event.type, {})
        triggers = chain_def.get("triggers", [])
        
        for trigger in triggers:
            # Check probability
            seed = f"{event.id}_{trigger['event']}_{event.tick}"
            if not deterministic_chance(trigger["probability"], seed):
                continue
            
            # Check condition if any
            condition = trigger.get("condition")
            if condition and not check_condition(condition, event, world_state):
                continue
            
            # Create triggered event
            triggered = CascadeEvent(
                id=f"{event.id}_cascade_{len(all_events)}",
                type=trigger["event"],
                tick=event.tick + trigger.get("delay", 0),
                location=event.location,
                participants=get_cascade_participants(trigger["event"], event, world_state),
                data={"source_event": event.id, "chain_depth": depth + 1},
                triggered_by=event.id
            )
            
            event.triggers.append(triggered.id)
            all_events.append(triggered)
            pending.append((triggered, depth + 1))
    
    return all_events


def check_condition(condition: str, event: CascadeEvent, world_state: dict) -> bool:
    """Check if a cascade condition is met."""
    conditions = {
        "gang_involved": lambda: any("gang" in p.lower() for p in event.participants),
        "serious_crime": lambda: event.type in ["murder", "kidnapping", "terrorism"],
        "gang_member": lambda: event.data.get("perpetrator_faction") in ["dock_gang", "undercity_gang"],
        "violent_family": lambda: event.data.get("family_trait") == "violent",
        "lethal_force": lambda: event.data.get("force_level") == "lethal",
        "heavily_invested": lambda: event.data.get("investment_level", 0) > 0.8,
        "restrictive_decree": lambda: event.data.get("decree_type") == "restrictive"
    }
    
    checker = conditions.get(condition)
    return checker() if checker else True


def get_cascade_participants(event_type: str, source: CascadeEvent, world_state: dict) -> List[str]:
    """Determine who participates in a cascaded event."""
    if event_type == "witness_report":
        return ["witness_npc", "temple_officer"]
    elif event_type == "temple_investigation":
        return ["temple_investigator"]
    elif event_type == "family_grief":
        return source.data.get("victim_family", [])
    elif event_type == "gossip_spread":
        return ["local_npcs"]
    else:
        return []


def get_npc_reaction(event_type: str, npc_disposition: str) -> str:
    """Get appropriate NPC reaction to an event."""
    reactions = NPC_REACTIONS.get(event_type, {})
    return reactions.get(npc_disposition, "I heard something happened...")


def simulate_cascade_example():
    """Example: A robbery and its cascading effects."""
    
    # Initial event: robbery at the market
    robbery = CascadeEvent(
        id="EVT_robbery_001",
        type="robbery",
        tick=100,
        location="neon_market",
        participants=["criminal_npc", "victim_npc", "witness_01", "witness_02"],
        data={
            "stolen_amount": 500,
            "weapon_used": True,
            "gang_involved": True,
            "perpetrator_faction": "dock_gang"
        }
    )
    
    # Process cascades
    world_state = {"districts": {}, "factions": {}}
    all_events = process_cascades(robbery, world_state)
    
    print("\n" + "="*60)
    print("  CASCADING EVENTS SIMULATION")
    print("="*60)
    print(f"\nInitial Event: {robbery.type} at tick {robbery.tick}")
    print(f"Location: {robbery.location}")
    print(f"\nCascade Results ({len(all_events)} total events):")
    print("-"*40)
    
    for event in all_events:
        indent = "  " * event.data.get("chain_depth", 0)
        triggered = f" (triggered by {event.triggered_by})" if event.triggered_by else ""
        print(f"{indent}Tick {event.tick}: {event.type}{triggered}")
    
    return all_events


if __name__ == "__main__":
    simulate_cascade_example()

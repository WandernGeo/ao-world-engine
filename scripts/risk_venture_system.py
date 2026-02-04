#!/usr/bin/env python3
"""
Risk & Venture System
=====================

Adds risk-taking, excitement-seeking, and venture behaviors to NPCs.

Personality Traits:
- risk_appetite: Willingness to take dangerous actions (0-1)
- excitement_seeking: Need for stimulation and novelty (0-1)  
- venture_drive: Motivation to explore unknown opportunities (0-1)

Risky Actions:
- heist: Rob a target (high risk, high reward)
- gamble: Bet resources on chance (variable risk)
- explore_danger: Venture into dangerous zones
- make_deal: Engage in risky trade/alliance
- challenge_authority: Confront powerful NPCs/factions
"""

import random
import hashlib
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class RiskyAction:
    """A risky action an NPC might take."""
    id: str
    name: str
    risk_level: float  # 0-1, how dangerous
    reward_potential: float  # 0-1, how rewarding if successful
    excitement_factor: float  # 0-1, how thrilling
    required_traits: Dict[str, float]  # Minimum trait values to consider
    success_base: float  # Base success chance
    consequences: Dict[str, Any]  # What happens on success/failure


# Available risky actions
RISKY_ACTIONS = {
    "heist": RiskyAction(
        id="heist",
        name="Attempt Heist",
        risk_level=0.8,
        reward_potential=0.9,
        excitement_factor=0.95,
        required_traits={"risk_appetite": 0.6, "venture_drive": 0.5},
        success_base=0.3,
        consequences={
            "success": {"wealth": +500, "reputation": +10, "heat": +30},
            "failure": {"health": -20, "reputation": -15, "heat": +50, "arrest_chance": 0.4}
        }
    ),
    "gamble": RiskyAction(
        id="gamble",
        name="High Stakes Gamble",
        risk_level=0.5,
        reward_potential=0.7,
        excitement_factor=0.8,
        required_traits={"risk_appetite": 0.4, "excitement_seeking": 0.5},
        success_base=0.45,
        consequences={
            "success": {"wealth": +200, "excitement": +20},
            "failure": {"wealth": -150, "mood": -10}
        }
    ),
    "explore_danger": RiskyAction(
        id="explore_danger",
        name="Explore Dangerous Zone",
        risk_level=0.6,
        reward_potential=0.6,
        excitement_factor=0.7,
        required_traits={"venture_drive": 0.5, "excitement_seeking": 0.4},
        success_base=0.5,
        consequences={
            "success": {"knowledge": +30, "loot_chance": 0.6, "excitement": +25},
            "failure": {"health": -15, "fear": +20}
        }
    ),
    "make_risky_deal": RiskyAction(
        id="make_risky_deal",
        name="Risky Business Deal",
        risk_level=0.4,
        reward_potential=0.5,
        excitement_factor=0.4,
        required_traits={"venture_drive": 0.4, "risk_appetite": 0.3},
        success_base=0.55,
        consequences={
            "success": {"wealth": +100, "contacts": +1, "reputation": +5},
            "failure": {"wealth": -50, "reputation": -10, "enemy_chance": 0.2}
        }
    ),
    "challenge_authority": RiskyAction(
        id="challenge_authority",
        name="Challenge Authority",
        risk_level=0.7,
        reward_potential=0.6,
        excitement_factor=0.85,
        required_traits={"risk_appetite": 0.6, "excitement_seeking": 0.5},
        success_base=0.35,
        consequences={
            "success": {"reputation": +25, "followers": +3, "excitement": +30},
            "failure": {"reputation": -20, "heat": +40, "arrest_chance": 0.3}
        }
    ),
    "bet_on_fight": RiskyAction(
        id="bet_on_fight",
        name="Bet on Underground Fight",
        risk_level=0.3,
        reward_potential=0.5,
        excitement_factor=0.9,
        required_traits={"excitement_seeking": 0.6},
        success_base=0.5,
        consequences={
            "success": {"wealth": +80, "excitement": +40},
            "failure": {"wealth": -60, "mood": -5}
        }
    )
}


class RiskVentureSystem:
    """Manages NPC risk-taking and venture behaviors."""
    
    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.action_history: Dict[str, List[Dict]] = {}  # NPC ID -> actions taken
    
    def get_risk_profile(self, personality: Dict[str, float]) -> Dict[str, float]:
        """
        Extract or infer risk-related traits from personality.
        
        If not present, derives from other traits.
        """
        # Direct traits if present
        risk_appetite = personality.get('risk_appetite')
        excitement_seeking = personality.get('excitement_seeking')
        venture_drive = personality.get('venture_drive')
        
        # Infer from other traits if missing
        if risk_appetite is None:
            aggression = personality.get('aggression', 0.5)
            greed = personality.get('greed', 0.5)
            risk_appetite = (aggression * 0.4 + greed * 0.6)
        
        if excitement_seeking is None:
            curiosity = personality.get('curiosity', 0.5)
            sociability = personality.get('sociability', 0.5)
            excitement_seeking = (curiosity * 0.6 + sociability * 0.4)
        
        if venture_drive is None:
            curiosity = personality.get('curiosity', 0.5)
            greed = personality.get('greed', 0.5)
            loyalty = personality.get('loyalty', 0.5)
            # Low loyalty = more willing to venture
            venture_drive = (curiosity * 0.5 + greed * 0.3 + (1 - loyalty) * 0.2)
        
        return {
            "risk_appetite": min(1.0, max(0.0, risk_appetite)),
            "excitement_seeking": min(1.0, max(0.0, excitement_seeking)),
            "venture_drive": min(1.0, max(0.0, venture_drive))
        }
    
    def calculate_action_utility(
        self, 
        npc_id: str,
        personality: Dict[str, float],
        action: RiskyAction,
        current_state: Dict[str, Any]
    ) -> float:
        """
        Calculate how attractive a risky action is to this NPC.
        
        Returns utility score 0-100.
        """
        risk_profile = self.get_risk_profile(personality)
        
        # Check if NPC meets minimum trait requirements
        for trait, min_val in action.required_traits.items():
            if risk_profile.get(trait, 0) < min_val:
                return 0.0  # Won't consider this action
        
        # Base utility from potential reward
        utility = action.reward_potential * 50
        
        # Risk appetite affects how much danger is acceptable
        risk_penalty = action.risk_level * (1 - risk_profile['risk_appetite']) * 30
        utility -= risk_penalty
        
        # Excitement seekers value thrilling actions more
        excitement_bonus = action.excitement_factor * risk_profile['excitement_seeking'] * 25
        utility += excitement_bonus
        
        # Venture drive affects exploration/opportunity actions
        if action.id in ['explore_danger', 'make_risky_deal']:
            venture_bonus = risk_profile['venture_drive'] * 20
            utility += venture_bonus
        
        # Current state modifiers
        wealth = current_state.get('wealth', 100)
        if wealth < 50 and action.reward_potential > 0.6:
            utility += 15  # Desperate for money
        elif wealth > 500:
            utility -= 10  # Less motivation
        
        excitement_level = current_state.get('excitement', 50)
        if excitement_level < 30 and action.excitement_factor > 0.7:
            utility += 20  # Bored, seeking thrills
        
        # Reduce utility if recently failed similar action
        recent_failures = self._count_recent_failures(npc_id, action.id)
        if recent_failures > 0:
            utility -= recent_failures * 15
        
        return max(0.0, min(100.0, utility))
    
    def _count_recent_failures(self, npc_id: str, action_type: str) -> int:
        """Count recent failures of this action type."""
        history = self.action_history.get(npc_id, [])
        failures = 0
        for entry in history[-10:]:  # Last 10 actions
            if entry.get('action') == action_type and not entry.get('success'):
                failures += 1
        return failures
    
    def select_risky_action(
        self,
        npc_id: str,
        personality: Dict[str, float],
        current_state: Dict[str, Any],
        available_actions: Optional[List[str]] = None
    ) -> Optional[RiskyAction]:
        """
        Select the best risky action for an NPC, if any.
        
        Returns None if no risky action is attractive enough.
        """
        if available_actions:
            actions = {k: v for k, v in RISKY_ACTIONS.items() if k in available_actions}
        else:
            actions = RISKY_ACTIONS
        
        best_action = None
        best_utility = 30  # Minimum threshold to take any risk
        
        for action_id, action in actions.items():
            utility = self.calculate_action_utility(npc_id, personality, action, current_state)
            if utility > best_utility:
                best_utility = utility
                best_action = action
        
        return best_action
    
    def attempt_action(
        self,
        npc_id: str,
        action: RiskyAction,
        personality: Dict[str, float],
        tick: int
    ) -> Dict[str, Any]:
        """
        Attempt a risky action and determine outcome.
        
        Returns result with success/failure and consequences.
        """
        risk_profile = self.get_risk_profile(personality)
        
        # Calculate success chance (modified by traits)
        success_chance = action.success_base
        success_chance += risk_profile['venture_drive'] * 0.1  # Experience helps
        
        # Deterministic based on tick and npc_id for reproducibility
        roll_seed = int(hashlib.md5(f"{npc_id}_{action.id}_{tick}".encode()).hexdigest(), 16)
        roll = (roll_seed % 100) / 100.0
        
        success = roll < success_chance
        
        # Get consequences
        if success:
            consequences = action.consequences['success'].copy()
            outcome_desc = f"Successfully completed {action.name}!"
        else:
            consequences = action.consequences['failure'].copy()
            outcome_desc = f"Failed at {action.name}..."
        
        # Record in history
        if npc_id not in self.action_history:
            self.action_history[npc_id] = []
        self.action_history[npc_id].append({
            'tick': tick,
            'action': action.id,
            'success': success
        })
        
        return {
            'action': action.id,
            'action_name': action.name,
            'success': success,
            'consequences': consequences,
            'description': outcome_desc,
            'risk_level': action.risk_level,
            'excitement_gained': action.excitement_factor * 20 if success else action.excitement_factor * 5
        }


def enhance_npc_with_risk(npc: Dict[str, Any]) -> Dict[str, Any]:
    """Add risk-related traits to an NPC if not present."""
    npc = npc.copy()
    personality = npc.get('personality', {})
    
    if isinstance(personality, dict):
        system = RiskVentureSystem()
        risk_profile = system.get_risk_profile(personality)
        personality.update(risk_profile)
        npc['personality'] = personality
    
    return npc


# CLI Test
if __name__ == "__main__":
    print("="*60)
    print("  Risk & Venture System Test")
    print("="*60 + "\n")
    
    system = RiskVentureSystem(seed=42)
    
    # Test NPCs with different risk profiles
    test_npcs = [
        {
            "id": "risk_taker",
            "name": "Nova Kim",
            "personality": {"aggression": 0.8, "greed": 0.7, "curiosity": 0.6, "loyalty": 0.2}
        },
        {
            "id": "cautious",
            "name": "Elder Moss",
            "personality": {"aggression": 0.2, "greed": 0.3, "curiosity": 0.4, "loyalty": 0.9}
        },
        {
            "id": "thrill_seeker",
            "name": "Blade Runner",
            "personality": {"aggression": 0.5, "greed": 0.4, "curiosity": 0.9, "sociability": 0.7}
        }
    ]
    
    for npc in test_npcs:
        print(f"\n--- {npc['name']} ---")
        profile = system.get_risk_profile(npc['personality'])
        print(f"Risk Profile: {profile}")
        
        current_state = {"wealth": 80, "excitement": 25}
        
        # Evaluate all actions
        print("\nAction Utilities:")
        for action_id, action in RISKY_ACTIONS.items():
            utility = system.calculate_action_utility(npc['id'], npc['personality'], action, current_state)
            if utility > 0:
                print(f"  {action.name}: {utility:.1f}")
        
        # Select best action
        best = system.select_risky_action(npc['id'], npc['personality'], current_state)
        if best:
            print(f"\n→ Would attempt: {best.name}")
            
            # Simulate attempt
            result = system.attempt_action(npc['id'], best, npc['personality'], tick=100)
            print(f"  Result: {'✓' if result['success'] else '✗'} {result['description']}")
            print(f"  Consequences: {result['consequences']}")
        else:
            print("\n→ Would not take any risky action (too cautious)")
    
    print("\n" + "="*60)
    print("✓ Risk & Venture System Test Complete!")
    print("="*60)

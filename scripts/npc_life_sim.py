#!/usr/bin/env python3
"""
NPC LIFE SIMULATION - generational Generational Simulation
=====================================================

NPCs have:
- Jobs (government, rebel, merchant, guard, etc.)
- Currency (GEP - Global Exchange Points)
- Economy (buy, sell, trade, wages)
- Needs (hunger, energy, hygiene, social)
- Life events (join factions, marry, have children)
- Daily routines (work, eat, sleep, breaks)

All deterministic - same seed = same life.
"""

import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import os

# =============================================================================
# DETERMINISTIC UTILITIES
# =============================================================================

def deterministic_hash(seed: str) -> int:
    return int(hashlib.sha256(seed.encode()).hexdigest(), 16)

def deterministic_chance(probability: float, seed: str) -> bool:
    h = deterministic_hash(seed) % 10000
    return h < (probability * 10000)

def deterministic_choice(items: list, seed: str) -> Any:
    if not items:
        return None
    return items[deterministic_hash(seed) % len(items)]

def deterministic_range(min_val: int, max_val: int, seed: str) -> int:
    return min_val + (deterministic_hash(seed) % (max_val - min_val + 1))


# =============================================================================
# ENUMS
# =============================================================================

class JobType(Enum):
    # Government
    GOVERNMENT_CLERK = "government_clerk"
    TEMPLE_GUARD = "temple_guard"
    ENFORCER = "enforcer"
    ADMINISTRATOR = "administrator"
    
    # Civilian
    MERCHANT = "merchant"
    BARTENDER = "bartender"
    MECHANIC = "mechanic"
    DOCTOR = "doctor"
    TEACHER = "teacher"
    FARMER = "farmer"
    
    # Criminal
    SMUGGLER = "smuggler"
    THIEF = "thief"
    ENFORCER_CRIMINAL = "enforcer_criminal"
    DEALER = "dealer"
    
    # Resistance
    REBEL_FIGHTER = "rebel_fighter"
    REBEL_SPY = "rebel_spy"
    REBEL_MEDIC = "rebel_medic"
    REBEL_ENGINEER = "rebel_engineer"
    
    # Corporate
    CORPORATE_EXEC = "corporate_exec"
    RESEARCHER = "researcher"
    SECURITY = "security"
    
    # Unemployed
    UNEMPLOYED = "unemployed"
    STUDENT = "student"
    RETIRED = "retired"


class NeedType(Enum):
    HUNGER = "hunger"
    ENERGY = "energy"
    HYGIENE = "hygiene"
    SOCIAL = "social"
    ENTERTAINMENT = "entertainment"
    SAFETY = "safety"


# =============================================================================
# JOB DEFINITIONS
# =============================================================================

JOB_DATA = {
    JobType.GOVERNMENT_CLERK: {
        "faction": "temple",
        "wage": 50,
        "work_hours": (8, 17),
        "skills_required": ["literacy", "administration"],
        "reputation_gain": {"temple": 0.01},
    },
    JobType.TEMPLE_GUARD: {
        "faction": "temple",
        "wage": 80,
        "work_hours": (6, 18),
        "skills_required": ["combat", "discipline"],
        "reputation_gain": {"temple": 0.02},
    },
    JobType.MERCHANT: {
        "faction": None,
        "wage": 0,  # Income from trading
        "work_hours": (9, 20),
        "skills_required": ["trading", "negotiation"],
        "income_type": "variable",
    },
    JobType.REBEL_FIGHTER: {
        "faction": "resistance",
        "wage": 20,  # Low pay, high purpose
        "work_hours": (0, 24),  # Always on call
        "skills_required": ["combat", "stealth"],
        "reputation_gain": {"resistance": 0.03, "temple": -0.05},
    },
    JobType.SMUGGLER: {
        "faction": "criminal",
        "wage": 0,
        "work_hours": (20, 4),  # Night work
        "skills_required": ["stealth", "navigation"],
        "income_type": "variable",
        "risk": 0.1,  # 10% chance of trouble per job
    },
    JobType.CORPORATE_EXEC: {
        "faction": "corporate",
        "wage": 500,
        "work_hours": (9, 18),
        "skills_required": ["management", "negotiation"],
        "reputation_gain": {"corporate": 0.02},
    },
    JobType.UNEMPLOYED: {
        "faction": None,
        "wage": 0,
        "work_hours": None,
        "skills_required": [],
    },
}


# =============================================================================
# NPC STATE
# =============================================================================

@dataclass
class NPCEconomy:
    """Economic state of an NPC."""
    gep: float = 100.0  # Starting money
    income_today: float = 0.0
    expenses_today: float = 0.0
    
    # Assets
    owns_home: bool = False
    home_value: float = 0.0
    inventory: Dict[str, int] = field(default_factory=dict)
    
    # Debts
    debt: float = 0.0
    debt_to: str = ""  # Who they owe


@dataclass
class NPCNeeds:
    """Physical and social needs."""
    hunger: float = 100.0      # 0 = starving, 100 = full
    energy: float = 100.0      # 0 = exhausted, 100 = rested
    hygiene: float = 100.0     # 0 = filthy, 100 = clean
    social: float = 50.0       # 0 = lonely, 100 = fulfilled
    entertainment: float = 50.0
    safety: float = 80.0       # Based on location danger


@dataclass
class NPCLife:
    """Life status and relationships."""
    age: int = 25
    is_alive: bool = True
    
    # Family
    spouse_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    parent_ids: List[str] = field(default_factory=list)
    
    # Work
    job: JobType = JobType.UNEMPLOYED
    employer_id: Optional[str] = None
    work_experience: Dict[str, int] = field(default_factory=dict)  # job -> days
    
    # Faction
    faction: Optional[str] = None
    faction_reputation: Dict[str, float] = field(default_factory=dict)
    faction_rank: int = 0
    
    # Skills
    skills: Dict[str, float] = field(default_factory=dict)


@dataclass
class NPCState:
    """Complete NPC state."""
    id: str
    name: str
    
    economy: NPCEconomy = field(default_factory=NPCEconomy)
    needs: NPCNeeds = field(default_factory=NPCNeeds)
    life: NPCLife = field(default_factory=NPCLife)
    
    # Current state
    current_location: str = "home"
    current_activity: str = "idle"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "gep": self.economy.gep,
            "job": self.life.job.value if self.life.job else None,
            "faction": self.life.faction,
            "age": self.life.age,
            "needs": {
                "hunger": self.needs.hunger,
                "energy": self.needs.energy,
                "hygiene": self.needs.hygiene,
                "social": self.needs.social,
            },
            "location": self.current_location,
            "activity": self.current_activity,
        }


# =============================================================================
# ECONOMY ACTIONS
# =============================================================================

def earn_wage(npc: NPCState, tick: int) -> float:
    """NPC earns their daily wage."""
    job_data = JOB_DATA.get(npc.life.job, {})
    wage = job_data.get("wage", 0)
    
    # Variable income jobs
    if job_data.get("income_type") == "variable":
        # Merchants, smugglers earn based on skill + luck
        skill = npc.life.skills.get("trading", 0.5)
        base = 50 + skill * 100
        variance = deterministic_range(-20, 50, f"{npc.id}_income_{tick}")
        wage = max(0, base + variance)
    
    npc.economy.gep += wage
    npc.economy.income_today += wage
    return wage


def spend_money(npc: NPCState, amount: float, reason: str, tick: int) -> bool:
    """NPC spends money. Returns True if successful."""
    if npc.economy.gep >= amount:
        npc.economy.gep -= amount
        npc.economy.expenses_today += amount
        return True
    return False


def buy_food(npc: NPCState, tick: int) -> Tuple[bool, float]:
    """NPC buys food. Returns (success, hunger_restored)."""
    food_cost = 5
    
    if spend_money(npc, food_cost, "food", tick):
        # Eating restores hunger
        hunger_restored = 30 + deterministic_range(0, 20, f"{npc.id}_food_{tick}")
        npc.needs.hunger = min(100, npc.needs.hunger + hunger_restored)
        return True, hunger_restored
    
    return False, 0


def trade_items(seller: NPCState, buyer: NPCState, item: str, 
                quantity: int, price: float, tick: int) -> bool:
    """Trade items between NPCs."""
    # Check buyer has money
    if buyer.economy.gep < price:
        return False
    
    # Check seller has items
    if seller.economy.inventory.get(item, 0) < quantity:
        return False
    
    # Execute trade
    buyer.economy.gep -= price
    seller.economy.gep += price
    
    seller.economy.inventory[item] = seller.economy.inventory.get(item, 0) - quantity
    buyer.economy.inventory[item] = buyer.economy.inventory.get(item, 0) + quantity
    
    # Social boost from trading
    seller.needs.social = min(100, seller.needs.social + 5)
    buyer.needs.social = min(100, buyer.needs.social + 5)
    
    return True


# =============================================================================
# NEEDS PROCESSING
# =============================================================================

def decay_needs(npc: NPCState, tick: int):
    """Needs decay over time."""
    # Hunger decays faster when active
    if npc.current_activity in ["working", "fighting", "running"]:
        npc.needs.hunger -= 3
    else:
        npc.needs.hunger -= 1
    
    # Energy decays during day, restores at night
    hour = tick % 24
    if 6 <= hour <= 22:
        npc.needs.energy -= 2
    else:
        if npc.current_activity == "sleeping":
            npc.needs.energy = min(100, npc.needs.energy + 15)
    
    # Hygiene decays slowly
    npc.needs.hygiene -= 0.5
    
    # Social decays without interaction
    if npc.current_activity not in ["socializing", "working"]:
        npc.needs.social -= 1
    
    # Clamp all values
    npc.needs.hunger = max(0, min(100, npc.needs.hunger))
    npc.needs.energy = max(0, min(100, npc.needs.energy))
    npc.needs.hygiene = max(0, min(100, npc.needs.hygiene))
    npc.needs.social = max(0, min(100, npc.needs.social))


def get_urgent_need(npc: NPCState) -> Optional[NeedType]:
    """Get the most urgent need if any are critical."""
    if npc.needs.hunger < 20:
        return NeedType.HUNGER
    if npc.needs.energy < 15:
        return NeedType.ENERGY
    if npc.needs.hygiene < 10:
        return NeedType.HYGIENE
    if npc.needs.social < 10:
        return NeedType.SOCIAL
    return None


def address_need(npc: NPCState, need: NeedType, tick: int) -> str:
    """NPC addresses an urgent need. Returns action taken."""
    if need == NeedType.HUNGER:
        success, _ = buy_food(npc, tick)
        if success:
            npc.current_activity = "eating"
            return "bought_food"
        else:
            # Can't afford food - might steal or beg
            if deterministic_chance(0.1, f"{npc.id}_steal_{tick}"):
                npc.needs.hunger = min(100, npc.needs.hunger + 20)
                return "stole_food"
            return "went_hungry"
    
    elif need == NeedType.ENERGY:
        npc.current_activity = "sleeping"
        npc.current_location = "home"
        return "went_to_sleep"
    
    elif need == NeedType.HYGIENE:
        if spend_money(npc, 2, "hygiene", tick):
            npc.needs.hygiene = 100
            npc.current_activity = "bathing"
            return "took_bath"
        return "stayed_dirty"
    
    elif need == NeedType.SOCIAL:
        npc.current_activity = "socializing"
        npc.current_location = "bar"
        npc.needs.social = min(100, npc.needs.social + 20)
        return "went_socializing"
    
    return "nothing"


# =============================================================================
# FACTION JOINING
# =============================================================================

def can_join_faction(npc: NPCState, faction: str) -> Tuple[bool, str]:
    """Check if NPC can join a faction."""
    # Already in faction?
    if npc.life.faction == faction:
        return False, "already_member"
    
    # Check reputation
    rep = npc.life.faction_reputation.get(faction, 0)
    
    if faction == "resistance":
        # Resistance accepts anyone not aligned with Temple
        temple_rep = npc.life.faction_reputation.get("temple", 0)
        if temple_rep > 0.5:
            return False, "too_loyal_to_temple"
        return True, "welcome"
    
    elif faction == "temple":
        # Temple requires clean record
        criminal_rep = npc.life.faction_reputation.get("criminal", 0)
        if criminal_rep > 0.2:
            return False, "criminal_record"
        if rep < -0.3:
            return False, "bad_reputation"
        return True, "approved"
    
    elif faction == "criminal":
        # Criminal orgs need proof of loyalty
        if rep < 0.1:
            return False, "need_to_prove_yourself"
        return True, "initiated"
    
    elif faction == "corporate":
        # Corporate needs skills
        if npc.life.skills.get("management", 0) < 0.3:
            return False, "need_more_experience"
        return True, "hired"
    
    return False, "unknown_faction"


def join_faction(npc: NPCState, faction: str, tick: int) -> dict:
    """NPC joins a faction."""
    can_join, reason = can_join_faction(npc, faction)
    
    if not can_join:
        return {"success": False, "reason": reason}
    
    # Leave current faction
    old_faction = npc.life.faction
    if old_faction:
        # Reputation penalty with old faction
        npc.life.faction_reputation[old_faction] = \
            npc.life.faction_reputation.get(old_faction, 0) - 0.5
    
    # Join new faction
    npc.life.faction = faction
    npc.life.faction_rank = 1  # Start at rank 1
    npc.life.faction_reputation[faction] = \
        npc.life.faction_reputation.get(faction, 0) + 0.2
    
    # Get appropriate job
    faction_jobs = {
        "resistance": JobType.REBEL_FIGHTER,
        "temple": JobType.GOVERNMENT_CLERK,
        "criminal": JobType.SMUGGLER,
        "corporate": JobType.SECURITY,
    }
    npc.life.job = faction_jobs.get(faction, JobType.UNEMPLOYED)
    
    return {
        "success": True,
        "faction": faction,
        "old_faction": old_faction,
        "new_job": npc.life.job.value,
        "tick": tick
    }


# =============================================================================
# LIFE EVENTS
# =============================================================================

def check_life_events(npc: NPCState, tick: int, all_npcs: Dict[str, NPCState]) -> List[dict]:
    """Check for major life events."""
    events = []
    
    # Marriage check (if single and social need high)
    if npc.life.spouse_id is None and npc.life.age >= 18 and npc.needs.social > 70:
        if deterministic_chance(0.001, f"{npc.id}_marry_{tick}"):
            # Find potential partner
            potential = [
                other for other in all_npcs.values()
                if other.id != npc.id
                and other.life.spouse_id is None
                and other.life.age >= 18
                and abs(other.life.age - npc.life.age) < 15
            ]
            if potential:
                partner = deterministic_choice(potential, f"{npc.id}_partner_{tick}")
                npc.life.spouse_id = partner.id
                partner.life.spouse_id = npc.id
                events.append({
                    "type": "marriage",
                    "npc1": npc.id,
                    "npc2": partner.id,
                    "tick": tick
                })
    
    # Child check (if married)
    if npc.life.spouse_id and len(npc.life.children_ids) < 3:
        if deterministic_chance(0.0005, f"{npc.id}_child_{tick}"):
            child_id = f"child_{npc.id}_{tick}"
            npc.life.children_ids.append(child_id)
            
            spouse = all_npcs.get(npc.life.spouse_id)
            if spouse:
                spouse.life.children_ids.append(child_id)
            
            events.append({
                "type": "birth",
                "parent1": npc.id,
                "parent2": npc.life.spouse_id,
                "child_id": child_id,
                "tick": tick
            })
    
    # Faction recruitment (if unemployed or unhappy)
    if npc.life.faction is None and npc.needs.safety < 50:
        if deterministic_chance(0.01, f"{npc.id}_recruit_{tick}"):
            # Gravitate toward faction based on circumstances
            if npc.economy.gep < 20:
                faction = "criminal"  # Desperate
            elif npc.life.faction_reputation.get("temple", 0) < -0.3:
                faction = "resistance"  # Against Temple
            else:
                faction = deterministic_choice(
                    ["resistance", "criminal", "civilian"],
                    f"{npc.id}_faction_choice_{tick}"
                )
            
            result = join_faction(npc, faction, tick)
            if result["success"]:
                events.append({
                    "type": "joined_faction",
                    "npc": npc.id,
                    "faction": faction,
                    "tick": tick
                })
    
    # Aging (once per year = 365 ticks)
    if tick % 365 == 0:
        npc.life.age += 1
        events.append({
            "type": "birthday",
            "npc": npc.id,
            "age": npc.life.age,
            "tick": tick
        })
        
        # Death check (increases with age)
        if npc.life.age > 60:
            death_chance = (npc.life.age - 60) * 0.005
            if deterministic_chance(death_chance, f"{npc.id}_death_{tick}"):
                npc.life.is_alive = False
                events.append({
                    "type": "death",
                    "npc": npc.id,
                    "age": npc.life.age,
                    "tick": tick
                })
    
    return events


# =============================================================================
# DAILY SCHEDULE
# =============================================================================

def get_scheduled_activity(npc: NPCState, tick: int) -> Tuple[str, str]:
    """Get what NPC should be doing at this time."""
    hour = tick % 24
    
    # Urgent needs override schedule
    urgent = get_urgent_need(npc)
    if urgent:
        if urgent == NeedType.HUNGER:
            return "eating", "restaurant" if npc.economy.gep > 10 else "home"
        if urgent == NeedType.ENERGY:
            return "sleeping", "home"
        if urgent == NeedType.HYGIENE:
            return "bathing", "home"
    
    # Job schedule
    job_data = JOB_DATA.get(npc.life.job, {})
    work_hours = job_data.get("work_hours")
    
    if work_hours:
        start, end = work_hours
        if start < end:
            is_working = start <= hour < end
        else:  # Night shift (e.g., 20-4)
            is_working = hour >= start or hour < end
        
        if is_working:
            # Work location based on job
            work_locations = {
                JobType.GOVERNMENT_CLERK: "government_building",
                JobType.TEMPLE_GUARD: "temple_checkpoint",
                JobType.MERCHANT: "market",
                JobType.REBEL_FIGHTER: "resistance_hideout",
                JobType.SMUGGLER: "docks",
            }
            return "working", work_locations.get(npc.life.job, "workplace")
    
    # Off-work schedule
    if 22 <= hour or hour < 6:
        return "sleeping", "home"
    
    if 18 <= hour < 22:
        # Evening activities
        if npc.needs.social < 50:
            return "socializing", "bar"
        if npc.needs.entertainment < 50:
            return "entertainment", "arcade"
        return "relaxing", "home"
    
    # Day off
    return "leisure", deterministic_choice(
        ["park", "market", "cafe", "home"],
        f"{npc.id}_leisure_{tick}"
    )


# =============================================================================
# TICK PROCESSING
# =============================================================================

def process_npc_tick(npc: NPCState, tick: int, all_npcs: Dict[str, NPCState]) -> dict:
    """Process one tick for an NPC."""
    if not npc.life.is_alive:
        return {"npc": npc.id, "status": "dead"}
    
    result = {
        "npc": npc.id,
        "tick": tick,
        "actions": [],
        "events": [],
        "state": {}
    }
    
    # 1. Decay needs
    decay_needs(npc, tick)
    
    # 2. Get scheduled activity
    activity, location = get_scheduled_activity(npc, tick)
    npc.current_activity = activity
    npc.current_location = location
    result["state"]["activity"] = activity
    result["state"]["location"] = location
    
    # 3. Handle urgent needs
    urgent = get_urgent_need(npc)
    if urgent:
        action = address_need(npc, urgent, tick)
        result["actions"].append({"type": "addressed_need", "need": urgent.value, "action": action})
    
    # 4. Work and earn money
    if activity == "working":
        wage = earn_wage(npc, tick)
        result["actions"].append({"type": "worked", "earned": wage})
    
    # 5. Daily expenses (rent, etc.)
    if tick % 24 == 0:  # Once per day
        rent = 10 if not npc.economy.owns_home else 0
        spend_money(npc, rent, "rent", tick)
        npc.economy.income_today = 0
        npc.economy.expenses_today = 0
    
    # 6. Check life events
    life_events = check_life_events(npc, tick, all_npcs)
    result["events"].extend(life_events)
    
    # 7. Update state summary
    result["state"]["gep"] = npc.economy.gep
    result["state"]["needs"] = {
        "hunger": npc.needs.hunger,
        "energy": npc.needs.energy,
        "social": npc.needs.social,
    }
    
    return result


# =============================================================================
# DEMO
# =============================================================================

def create_sample_npcs() -> Dict[str, NPCState]:
    """Create sample NPCs for testing."""
    npcs = {}
    
    # Charlie - Resistance member
    charlie = NPCState(id="charlie", name="Charlie")
    charlie.life.faction = "resistance"
    charlie.life.job = JobType.REBEL_FIGHTER
    charlie.life.age = 28
    charlie.economy.gep = 50
    charlie.life.skills = {"combat": 0.7, "stealth": 0.5}
    npcs["charlie"] = charlie
    
    # Felix - Criminal
    felix = NPCState(id="felix", name="Felix")
    felix.life.faction = "criminal"
    felix.life.job = JobType.SMUGGLER
    felix.life.age = 35
    felix.economy.gep = 300
    felix.life.skills = {"trading": 0.8, "stealth": 0.6}
    npcs["felix"] = felix
    
    # Nova - Civilian merchant
    nova = NPCState(id="nova_chen", name="Nova Chen")
    nova.life.job = JobType.MERCHANT
    nova.life.age = 32
    nova.economy.gep = 500
    nova.economy.inventory = {"tech_parts": 10, "food_rations": 20}
    nova.life.skills = {"trading": 0.9, "negotiation": 0.7}
    npcs["nova_chen"] = nova
    
    # Marcus - Temple guard
    marcus = NPCState(id="marcus", name="Marcus")
    marcus.life.faction = "temple"
    marcus.life.job = JobType.TEMPLE_GUARD
    marcus.life.age = 40
    marcus.economy.gep = 200
    marcus.life.skills = {"combat": 0.8, "discipline": 0.9}
    npcs["marcus"] = marcus
    
    # Jax - Unemployed, might join faction
    jax = NPCState(id="jax", name="Jax")
    jax.life.job = JobType.UNEMPLOYED
    jax.life.age = 22
    jax.economy.gep = 20  # Poor
    jax.needs.safety = 30  # Feels unsafe
    npcs["jax"] = jax
    
    return npcs


if __name__ == "__main__":
    print("="*60)
    print("  NPC LIFE SIMULATION - Generational Simulation")
    print("="*60)
    
    npcs = create_sample_npcs()
    
    print("\n📋 Initial NPC States:")
    for npc_id, npc in npcs.items():
        print(f"\n  {npc.name}:")
        print(f"    💼 Job: {npc.life.job.value}")
        print(f"    🏴 Faction: {npc.life.faction or 'None'}")
        print(f"    💰 GEP: {npc.economy.gep}")
        print(f"    🎂 Age: {npc.life.age}")
    
    print("\n" + "="*60)
    print("  Simulating 48 hours (48 ticks)...")
    print("="*60)
    
    all_events = []
    
    for tick in range(48):
        hour = tick % 24
        
        if tick % 12 == 0:
            print(f"\n--- Tick {tick} (Hour {hour}:00) ---")
        
        for npc_id, npc in npcs.items():
            result = process_npc_tick(npc, tick, npcs)
            
            # Print interesting events
            for event in result.get("events", []):
                event_type = event.get("type")
                if event_type == "joined_faction":
                    print(f"  🏴 {npc.name} joined {event['faction']}!")
                elif event_type == "marriage":
                    print(f"  💒 {npc.name} got married!")
                elif event_type == "birth":
                    print(f"  👶 New baby born!")
            
            for action in result.get("actions", []):
                if action.get("type") == "addressed_need":
                    if action.get("action") == "stole_food":
                        print(f"  🚨 {npc.name} stole food!")
                    elif action.get("action") == "went_hungry":
                        print(f"  😢 {npc.name} went hungry...")
    
    print("\n" + "="*60)
    print("  Final States After 48 Hours:")
    print("="*60)
    
    for npc_id, npc in npcs.items():
        print(f"\n  {npc.name}:")
        print(f"    💼 Job: {npc.life.job.value}")
        print(f"    🏴 Faction: {npc.life.faction or 'None'}")
        print(f"    💰 GEP: {npc.economy.gep:.0f}")
        print(f"    🍔 Hunger: {npc.needs.hunger:.0f}")
        print(f"    😴 Energy: {npc.needs.energy:.0f}")
        print(f"    📍 Location: {npc.current_location}")
        print(f"    🏃 Activity: {npc.current_activity}")

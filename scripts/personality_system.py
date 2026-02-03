#!/usr/bin/env python3
"""
NPC PERSONALITY SYSTEM
======================

Complete personality framework combining:
- D&D Alignments (Lawful/Chaotic, Good/Evil)
- MBTI Personality Types (16 types)
- Western Zodiac Signs (12 signs)
- Elemental/Chinese Zodiac (12 animals + 5 elements)
- Traits system

All deterministically assigned based on NPC ID + birth tick.
"""

import hashlib
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

# =============================================================================
# DETERMINISTIC UTILITIES
# =============================================================================

def deterministic_hash(seed: str) -> int:
    return int(hashlib.sha256(seed.encode()).hexdigest(), 16)

def deterministic_choice(items: list, seed: str) -> Any:
    if not items:
        return None
    return items[deterministic_hash(seed) % len(items)]


# =============================================================================
# D&D ALIGNMENTS
# =============================================================================

class LawChaos(Enum):
    LAWFUL = "lawful"
    NEUTRAL = "neutral"
    CHAOTIC = "chaotic"


class GoodEvil(Enum):
    GOOD = "good"
    NEUTRAL = "neutral"
    EVIL = "evil"


@dataclass
class DnDAlignment:
    law_chaos: LawChaos
    good_evil: GoodEvil
    
    @property
    def name(self) -> str:
        if self.law_chaos == LawChaos.NEUTRAL and self.good_evil == GoodEvil.NEUTRAL:
            return "True Neutral"
        return f"{self.law_chaos.value.title()} {self.good_evil.value.title()}"
    
    @property
    def description(self) -> str:
        descriptions = {
            ("lawful", "good"): "Crusader - follows rules and helps others",
            ("lawful", "neutral"): "Judge - respects order above morality",
            ("lawful", "evil"): "Dominator - uses rules to control others",
            ("neutral", "good"): "Benefactor - does good without dogma",
            ("neutral", "neutral"): "Undecided - acts based on circumstance",
            ("neutral", "evil"): "Malefactor - selfish without being destructive",
            ("chaotic", "good"): "Rebel - fights oppression, helps the weak",
            ("chaotic", "neutral"): "Free Spirit - values freedom above all",
            ("chaotic", "evil"): "Destroyer - revels in chaos and suffering",
        }
        return descriptions.get((self.law_chaos.value, self.good_evil.value), "Unknown")
    
    def get_behavior_modifiers(self) -> Dict[str, float]:
        """Returns modifiers for simulation behavior."""
        mods = {}
        
        # Law/Chaos affects rule following
        if self.law_chaos == LawChaos.LAWFUL:
            mods["obey_authority"] = 0.8
            mods["crime_chance"] = 0.1
            mods["predictability"] = 0.9
        elif self.law_chaos == LawChaos.CHAOTIC:
            mods["obey_authority"] = 0.2
            mods["crime_chance"] = 0.4
            mods["predictability"] = 0.3
        else:
            mods["obey_authority"] = 0.5
            mods["crime_chance"] = 0.25
            mods["predictability"] = 0.6
        
        # Good/Evil affects altruism
        if self.good_evil == GoodEvil.GOOD:
            mods["help_stranger"] = 0.9
            mods["sacrifice_for_others"] = 0.7
            mods["aggression_unprovoked"] = 0.1
        elif self.good_evil == GoodEvil.EVIL:
            mods["help_stranger"] = 0.1
            mods["sacrifice_for_others"] = 0.0
            mods["aggression_unprovoked"] = 0.5
        else:
            mods["help_stranger"] = 0.5
            mods["sacrifice_for_others"] = 0.3
            mods["aggression_unprovoked"] = 0.25
        
        return mods


def assign_alignment(npc_id: str, birth_tick: int) -> DnDAlignment:
    """Deterministically assign D&D alignment based on ID and birth."""
    seed = f"{npc_id}_alignment_{birth_tick}"
    
    law_chaos_roll = deterministic_hash(seed + "_lc") % 100
    good_evil_roll = deterministic_hash(seed + "_ge") % 100
    
    # Distribution: 30% each extreme, 40% neutral
    if law_chaos_roll < 30:
        lc = LawChaos.LAWFUL
    elif law_chaos_roll < 70:
        lc = LawChaos.NEUTRAL
    else:
        lc = LawChaos.CHAOTIC
    
    if good_evil_roll < 30:
        ge = GoodEvil.GOOD
    elif good_evil_roll < 70:
        ge = GoodEvil.NEUTRAL
    else:
        ge = GoodEvil.EVIL
    
    return DnDAlignment(lc, ge)


# =============================================================================
# MBTI PERSONALITY TYPES
# =============================================================================

class MBTIDimension(Enum):
    # Energy: Extraversion vs Introversion
    E = "Extraversion"
    I = "Introversion"
    # Information: Sensing vs Intuition
    S = "Sensing"
    N = "Intuition"
    # Decisions: Thinking vs Feeling
    T = "Thinking"
    F = "Feeling"
    # Lifestyle: Judging vs Perceiving
    J = "Judging"
    P = "Perceiving"


MBTI_TYPES = {
    "INTJ": {
        "name": "Architect",
        "description": "Strategic, independent, determined visionaries",
        "strengths": ["strategic", "independent", "determined"],
        "weaknesses": ["arrogant", "dismissive", "overly_critical"],
        "compatible": ["ENFP", "ENTP"],
        "social_style": "reserved"
    },
    "INTP": {
        "name": "Logician",
        "description": "Innovative inventors with an unquenchable thirst for knowledge",
        "strengths": ["analytical", "objective", "open_minded"],
        "weaknesses": ["insensitive", "absent_minded", "condescending"],
        "compatible": ["ENTJ", "ENFJ"],
        "social_style": "reserved"
    },
    "ENTJ": {
        "name": "Commander",
        "description": "Bold, imaginative, strong-willed leaders",
        "strengths": ["efficient", "energetic", "confident"],
        "weaknesses": ["stubborn", "intolerant", "impatient"],
        "compatible": ["INTP", "INFP"],
        "social_style": "assertive"
    },
    "ENTP": {
        "name": "Debater",
        "description": "Smart, curious thinkers who love intellectual challenges",
        "strengths": ["knowledgeable", "quick_thinker", "charismatic"],
        "weaknesses": ["argumentative", "insensitive", "unfocused"],
        "compatible": ["INTJ", "INFJ"],
        "social_style": "assertive"
    },
    "INFJ": {
        "name": "Advocate",
        "description": "Quiet, mystical idealists with deep convictions",
        "strengths": ["creative", "insightful", "principled"],
        "weaknesses": ["sensitive", "perfectionistic", "private"],
        "compatible": ["ENTP", "ENFP"],
        "social_style": "gentle"
    },
    "INFP": {
        "name": "Mediator",
        "description": "Poetic, kind, altruistic idealists",
        "strengths": ["empathetic", "generous", "creative"],
        "weaknesses": ["unrealistic", "self_isolating", "unfocused"],
        "compatible": ["ENTJ", "ENFJ"],
        "social_style": "gentle"
    },
    "ENFJ": {
        "name": "Protagonist",
        "description": "Charismatic, inspiring leaders who mesmerize listeners",
        "strengths": ["tolerant", "reliable", "charismatic"],
        "weaknesses": ["overly_idealistic", "too_selfless", "condescending"],
        "compatible": ["INFP", "INTP"],
        "social_style": "warm"
    },
    "ENFP": {
        "name": "Campaigner",
        "description": "Enthusiastic, creative free spirits",
        "strengths": ["curious", "observant", "energetic"],
        "weaknesses": ["unfocused", "disorganized", "overly_optimistic"],
        "compatible": ["INTJ", "INFJ"],
        "social_style": "warm"
    },
    "ISTJ": {
        "name": "Logistician",
        "description": "Practical, fact-minded, reliable",
        "strengths": ["honest", "dutiful", "calm"],
        "weaknesses": ["stubborn", "insensitive", "judgmental"],
        "compatible": ["ESFP", "ESTP"],
        "social_style": "reserved"
    },
    "ISFJ": {
        "name": "Defender",
        "description": "Dedicated protectors, warm and caring",
        "strengths": ["supportive", "reliable", "patient"],
        "weaknesses": ["shy", "takes_things_personally", "represses_feelings"],
        "compatible": ["ESFP", "ESTP"],
        "social_style": "gentle"
    },
    "ESTJ": {
        "name": "Executive",
        "description": "Excellent administrators, managing things and people",
        "strengths": ["dedicated", "strong_willed", "direct"],
        "weaknesses": ["inflexible", "uncomfortable_with_unconventional", "judgmental"],
        "compatible": ["ISFP", "ISTP"],
        "social_style": "assertive"
    },
    "ESFJ": {
        "name": "Consul",
        "description": "Extraordinarily caring, social, popular",
        "strengths": ["loyal", "sensitive", "warm"],
        "weaknesses": ["needy", "approval_seeking", "too_selfless"],
        "compatible": ["ISFP", "ISTP"],
        "social_style": "warm"
    },
    "ISTP": {
        "name": "Virtuoso",
        "description": "Bold, practical experimenters",
        "strengths": ["optimistic", "creative", "practical"],
        "weaknesses": ["stubborn", "insensitive", "risky"],
        "compatible": ["ESTJ", "ESFJ"],
        "social_style": "reserved"
    },
    "ISFP": {
        "name": "Adventurer",
        "description": "Flexible, charming artists",
        "strengths": ["charming", "sensitive", "imaginative"],
        "weaknesses": ["unpredictable", "easily_stressed", "competitive"],
        "compatible": ["ESTJ", "ESFJ"],
        "social_style": "gentle"
    },
    "ESTP": {
        "name": "Entrepreneur",
        "description": "Smart, energetic, perceptive",
        "strengths": ["bold", "rational", "direct"],
        "weaknesses": ["impatient", "risky", "unstructured"],
        "compatible": ["ISTJ", "ISFJ"],
        "social_style": "assertive"
    },
    "ESFP": {
        "name": "Entertainer",
        "description": "Spontaneous, energetic, enthusiastic entertainers",
        "strengths": ["bold", "original", "practical"],
        "weaknesses": ["sensitive", "easily_bored", "unfocused"],
        "compatible": ["ISTJ", "ISFJ"],
        "social_style": "warm"
    }
}


def assign_mbti(npc_id: str, birth_tick: int) -> str:
    """Deterministically assign MBTI type."""
    seed = f"{npc_id}_mbti_{birth_tick}"
    
    # Determine each dimension
    e_i = "E" if deterministic_hash(seed + "_ei") % 2 == 0 else "I"
    s_n = "S" if deterministic_hash(seed + "_sn") % 2 == 0 else "N"
    t_f = "T" if deterministic_hash(seed + "_tf") % 2 == 0 else "F"
    j_p = "J" if deterministic_hash(seed + "_jp") % 2 == 0 else "P"
    
    return f"{e_i}{s_n}{t_f}{j_p}"


def get_mbti_compatibility(type1: str, type2: str) -> float:
    """Calculate compatibility between two MBTI types."""
    if type1 not in MBTI_TYPES or type2 not in MBTI_TYPES:
        return 0.5
    
    data1 = MBTI_TYPES[type1]
    data2 = MBTI_TYPES[type2]
    
    # Check if they're listed as compatible
    if type2 in data1.get("compatible", []):
        return 0.9
    if type1 in data2.get("compatible", []):
        return 0.9
    
    # Check social style match
    style1 = data1.get("social_style", "")
    style2 = data2.get("social_style", "")
    
    if style1 == style2:
        return 0.6
    elif {style1, style2} in [{"warm", "gentle"}, {"assertive", "reserved"}]:
        return 0.5
    
    return 0.4


# =============================================================================
# WESTERN ZODIAC
# =============================================================================

WESTERN_ZODIAC = {
    "aries": {
        "symbol": "♈",
        "element": "fire",
        "modality": "cardinal",
        "ruler": "Mars",
        "dates": (3, 21, 4, 19),
        "traits": ["courageous", "determined", "confident", "enthusiastic"],
        "weaknesses": ["impatient", "moody", "aggressive"],
        "compatible": ["leo", "sagittarius", "gemini", "aquarius"]
    },
    "taurus": {
        "symbol": "♉",
        "element": "earth",
        "modality": "fixed",
        "ruler": "Venus",
        "dates": (4, 20, 5, 20),
        "traits": ["reliable", "patient", "practical", "devoted"],
        "weaknesses": ["stubborn", "possessive", "uncompromising"],
        "compatible": ["virgo", "capricorn", "cancer", "pisces"]
    },
    "gemini": {
        "symbol": "♊",
        "element": "air",
        "modality": "mutable",
        "ruler": "Mercury",
        "dates": (5, 21, 6, 20),
        "traits": ["adaptable", "curious", "affectionate", "witty"],
        "weaknesses": ["nervous", "inconsistent", "indecisive"],
        "compatible": ["libra", "aquarius", "aries", "leo"]
    },
    "cancer": {
        "symbol": "♋",
        "element": "water",
        "modality": "cardinal",
        "ruler": "Moon",
        "dates": (6, 21, 7, 22),
        "traits": ["tenacious", "loyal", "emotional", "sympathetic"],
        "weaknesses": ["moody", "pessimistic", "suspicious"],
        "compatible": ["scorpio", "pisces", "taurus", "virgo"]
    },
    "leo": {
        "symbol": "♌",
        "element": "fire",
        "modality": "fixed",
        "ruler": "Sun",
        "dates": (7, 23, 8, 22),
        "traits": ["creative", "passionate", "generous", "warm"],
        "weaknesses": ["arrogant", "stubborn", "self_centered"],
        "compatible": ["aries", "sagittarius", "gemini", "libra"]
    },
    "virgo": {
        "symbol": "♍",
        "element": "earth",
        "modality": "mutable",
        "ruler": "Mercury",
        "dates": (8, 23, 9, 22),
        "traits": ["loyal", "analytical", "kind", "hardworking"],
        "weaknesses": ["worrying", "critical", "all_work_no_play"],
        "compatible": ["taurus", "capricorn", "cancer", "scorpio"]
    },
    "libra": {
        "symbol": "♎",
        "element": "air",
        "modality": "cardinal",
        "ruler": "Venus",
        "dates": (9, 23, 10, 22),
        "traits": ["cooperative", "diplomatic", "gracious", "fair"],
        "weaknesses": ["indecisive", "avoids_confrontation", "grudges"],
        "compatible": ["gemini", "aquarius", "leo", "sagittarius"]
    },
    "scorpio": {
        "symbol": "♏",
        "element": "water",
        "modality": "fixed",
        "ruler": "Pluto",
        "dates": (10, 23, 11, 21),
        "traits": ["resourceful", "brave", "passionate", "stubborn"],
        "weaknesses": ["jealous", "secretive", "violent"],
        "compatible": ["cancer", "pisces", "virgo", "capricorn"]
    },
    "sagittarius": {
        "symbol": "♐",
        "element": "fire",
        "modality": "mutable",
        "ruler": "Jupiter",
        "dates": (11, 22, 12, 21),
        "traits": ["generous", "idealistic", "humorous", "adventurous"],
        "weaknesses": ["impatient", "tactless", "promises_more_than_delivers"],
        "compatible": ["aries", "leo", "libra", "aquarius"]
    },
    "capricorn": {
        "symbol": "♑",
        "element": "earth",
        "modality": "cardinal",
        "ruler": "Saturn",
        "dates": (12, 22, 1, 19),
        "traits": ["responsible", "disciplined", "self_control", "managers"],
        "weaknesses": ["know_it_all", "unforgiving", "condescending"],
        "compatible": ["taurus", "virgo", "scorpio", "pisces"]
    },
    "aquarius": {
        "symbol": "♒",
        "element": "air",
        "modality": "fixed",
        "ruler": "Uranus",
        "dates": (1, 20, 2, 18),
        "traits": ["progressive", "original", "independent", "humanitarian"],
        "weaknesses": ["aloof", "rebellious", "uncompromising"],
        "compatible": ["gemini", "libra", "aries", "sagittarius"]
    },
    "pisces": {
        "symbol": "♓",
        "element": "water",
        "modality": "mutable",
        "ruler": "Neptune",
        "dates": (2, 19, 3, 20),
        "traits": ["compassionate", "artistic", "intuitive", "gentle"],
        "weaknesses": ["fearful", "sad", "desire_to_escape_reality"],
        "compatible": ["cancer", "scorpio", "taurus", "capricorn"]
    }
}


def assign_zodiac(npc_id: str, birth_tick: int) -> str:
    """Assign zodiac sign based on birth tick (treating tick as day of year)."""
    # Convert tick to day of year (0-364)
    day_of_year = birth_tick % 365
    
    # Map to zodiac
    zodiac_order = [
        ("capricorn", 0, 19),
        ("aquarius", 20, 49),
        ("pisces", 50, 79),
        ("aries", 80, 110),
        ("taurus", 111, 140),
        ("gemini", 141, 171),
        ("cancer", 172, 203),
        ("leo", 204, 234),
        ("virgo", 235, 265),
        ("libra", 266, 295),
        ("scorpio", 296, 325),
        ("sagittarius", 326, 355),
        ("capricorn", 356, 365),
    ]
    
    for sign, start, end in zodiac_order:
        if start <= day_of_year <= end:
            return sign
    
    return "capricorn"


# =============================================================================
# CHINESE/ELEMENTAL ZODIAC
# =============================================================================

CHINESE_ZODIAC = {
    "rat": {
        "symbol": "🐀",
        "traits": ["quick_witted", "resourceful", "versatile"],
        "compatible": ["dragon", "monkey", "ox"],
        "incompatible": ["horse", "goat"]
    },
    "ox": {
        "symbol": "🐂",
        "traits": ["diligent", "dependable", "strong", "determined"],
        "compatible": ["rat", "snake", "rooster"],
        "incompatible": ["tiger", "dragon", "horse", "goat"]
    },
    "tiger": {
        "symbol": "🐅",
        "traits": ["brave", "confident", "competitive"],
        "compatible": ["dragon", "horse", "pig"],
        "incompatible": ["ox", "tiger", "snake", "monkey"]
    },
    "rabbit": {
        "symbol": "🐇",
        "traits": ["quiet", "elegant", "kind", "responsible"],
        "compatible": ["goat", "monkey", "dog", "pig"],
        "incompatible": ["snake", "rooster"]
    },
    "dragon": {
        "symbol": "🐉",
        "traits": ["confident", "intelligent", "enthusiastic"],
        "compatible": ["rooster", "rat", "monkey"],
        "incompatible": ["ox", "goat", "dog"]
    },
    "snake": {
        "symbol": "🐍",
        "traits": ["enigmatic", "intelligent", "wise"],
        "compatible": ["dragon", "rooster"],
        "incompatible": ["tiger", "rabbit", "snake", "goat", "pig"]
    },
    "horse": {
        "symbol": "🐎",
        "traits": ["animated", "active", "energetic"],
        "compatible": ["tiger", "goat", "rabbit"],
        "incompatible": ["rat", "ox", "rooster", "horse"]
    },
    "goat": {
        "symbol": "🐐",
        "traits": ["calm", "gentle", "sympathetic"],
        "compatible": ["horse", "rabbit", "pig"],
        "incompatible": ["ox", "tiger", "dog"]
    },
    "monkey": {
        "symbol": "🐒",
        "traits": ["sharp", "smart", "curious"],
        "compatible": ["ox", "rabbit"],
        "incompatible": ["tiger", "pig"]
    },
    "rooster": {
        "symbol": "🐓",
        "traits": ["observant", "hardworking", "courageous"],
        "compatible": ["ox", "snake"],
        "incompatible": ["rat", "rabbit", "horse", "rooster", "dog"]
    },
    "dog": {
        "symbol": "🐕",
        "traits": ["loyal", "honest", "amiable", "kind"],
        "compatible": ["rabbit"],
        "incompatible": ["dragon", "goat", "rooster"]
    },
    "pig": {
        "symbol": "🐖",
        "traits": ["compassionate", "generous", "diligent"],
        "compatible": ["tiger", "rabbit", "goat"],
        "incompatible": ["snake", "monkey"]
    }
}

ELEMENTS_CHINESE = {
    "wood": {"traits": ["generosity", "cooperation"], "color": "green"},
    "fire": {"traits": ["dynamism", "passion"], "color": "red"},
    "earth": {"traits": ["patience", "honesty"], "color": "yellow"},
    "metal": {"traits": ["ambition", "determination"], "color": "white"},
    "water": {"traits": ["flexibility", "persuasion"], "color": "blue"},
}


def assign_chinese_zodiac(npc_id: str, birth_tick: int) -> Tuple[str, str]:
    """
    Assign Chinese zodiac animal and element.
    Returns (animal, element).
    """
    # 12-year cycle for animals
    animals = list(CHINESE_ZODIAC.keys())
    animal = animals[birth_tick % 12]
    
    # 10-year cycle for elements (each element lasts 2 years)
    elements = list(ELEMENTS_CHINESE.keys())
    element = elements[(birth_tick // 2) % 5]
    
    return animal, element


# =============================================================================
# COMPLETE PERSONALITY PROFILE
# =============================================================================

@dataclass
class PersonalityProfile:
    """Complete personality profile for an NPC."""
    npc_id: str
    birth_tick: int
    
    # D&D Alignment
    alignment: DnDAlignment = None
    
    # MBTI
    mbti: str = ""
    
    # Western Zodiac
    zodiac: str = ""
    zodiac_element: str = ""
    
    # Chinese Zodiac
    chinese_animal: str = ""
    chinese_element: str = ""
    
    # Combined traits
    all_traits: List[str] = field(default_factory=list)
    all_weaknesses: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "npc_id": self.npc_id,
            "birth_tick": self.birth_tick,
            "alignment": self.alignment.name if self.alignment else None,
            "alignment_description": self.alignment.description if self.alignment else None,
            "mbti": self.mbti,
            "mbti_name": MBTI_TYPES.get(self.mbti, {}).get("name", ""),
            "zodiac": self.zodiac,
            "zodiac_symbol": WESTERN_ZODIAC.get(self.zodiac, {}).get("symbol", ""),
            "zodiac_element": self.zodiac_element,
            "chinese_animal": self.chinese_animal,
            "chinese_animal_symbol": CHINESE_ZODIAC.get(self.chinese_animal, {}).get("symbol", ""),
            "chinese_element": self.chinese_element,
            "traits": self.all_traits,
            "weaknesses": self.all_weaknesses,
        }
    
    def get_summary(self) -> str:
        """Human-readable summary."""
        return f"""
{self.alignment.name if self.alignment else 'Unknown'} {MBTI_TYPES.get(self.mbti, {}).get('name', '')} ({self.mbti})
{WESTERN_ZODIAC.get(self.zodiac, {}).get('symbol', '')} {self.zodiac.title()} ({self.zodiac_element})
{CHINESE_ZODIAC.get(self.chinese_animal, {}).get('symbol', '')} {self.chinese_element.title()} {self.chinese_animal.title()}
Traits: {', '.join(self.all_traits[:5])}
""".strip()


def generate_personality_profile(npc_id: str, birth_tick: int) -> PersonalityProfile:
    """Generate complete personality profile for an NPC."""
    profile = PersonalityProfile(npc_id=npc_id, birth_tick=birth_tick)
    
    # D&D Alignment
    profile.alignment = assign_alignment(npc_id, birth_tick)
    
    # MBTI
    profile.mbti = assign_mbti(npc_id, birth_tick)
    
    # Western Zodiac
    profile.zodiac = assign_zodiac(npc_id, birth_tick)
    profile.zodiac_element = WESTERN_ZODIAC.get(profile.zodiac, {}).get("element", "unknown")
    
    # Chinese Zodiac
    profile.chinese_animal, profile.chinese_element = assign_chinese_zodiac(npc_id, birth_tick)
    
    # Combine all traits
    all_traits = set()
    all_weaknesses = set()
    
    # From MBTI
    mbti_data = MBTI_TYPES.get(profile.mbti, {})
    all_traits.update(mbti_data.get("strengths", []))
    all_weaknesses.update(mbti_data.get("weaknesses", []))
    
    # From Western Zodiac
    zodiac_data = WESTERN_ZODIAC.get(profile.zodiac, {})
    all_traits.update(zodiac_data.get("traits", []))
    all_weaknesses.update(zodiac_data.get("weaknesses", []))
    
    # From Chinese Zodiac
    chinese_data = CHINESE_ZODIAC.get(profile.chinese_animal, {})
    all_traits.update(chinese_data.get("traits", []))
    
    # From Chinese Element
    element_data = ELEMENTS_CHINESE.get(profile.chinese_element, {})
    all_traits.update(element_data.get("traits", []))
    
    profile.all_traits = sorted(list(all_traits))
    profile.all_weaknesses = sorted(list(all_weaknesses))
    
    return profile


def calculate_personality_compatibility(profile1: PersonalityProfile, profile2: PersonalityProfile) -> float:
    """Calculate overall personality compatibility between two NPCs."""
    scores = []
    
    # MBTI compatibility
    mbti_compat = get_mbti_compatibility(profile1.mbti, profile2.mbti)
    scores.append(mbti_compat)
    
    # Zodiac compatibility
    zodiac1_data = WESTERN_ZODIAC.get(profile1.zodiac, {})
    if profile2.zodiac in zodiac1_data.get("compatible", []):
        scores.append(0.8)
    else:
        scores.append(0.4)
    
    # Chinese zodiac compatibility
    chinese1_data = CHINESE_ZODIAC.get(profile1.chinese_animal, {})
    if profile2.chinese_animal in chinese1_data.get("compatible", []):
        scores.append(0.85)
    elif profile2.chinese_animal in chinese1_data.get("incompatible", []):
        scores.append(0.2)
    else:
        scores.append(0.5)
    
    # Alignment compatibility (good-good, evil-evil might clash)
    if profile1.alignment and profile2.alignment:
        if profile1.alignment.good_evil == profile2.alignment.good_evil:
            scores.append(0.7)
        else:
            scores.append(0.3)
    
    return sum(scores) / len(scores) if scores else 0.5


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    print("="*60)
    print("  NPC PERSONALITY SYSTEM")
    print("="*60)
    
    # Test NPCs
    test_npcs = [
        ("charlie", 100),
        ("felix", 250),
        ("nova_chen", 50),
        ("marcus", 180),
        ("zero_chen", 300),
    ]
    
    profiles = []
    
    for npc_id, birth_tick in test_npcs:
        profile = generate_personality_profile(npc_id, birth_tick)
        profiles.append(profile)
        
        print(f"\n📋 {npc_id.upper()}")
        print(f"   {profile.get_summary()}")
    
    print("\n" + "="*60)
    print("  COMPATIBILITY MATRIX")
    print("="*60)
    
    print("\n   ", end="")
    for p in profiles:
        print(f"{p.npc_id[:6]:>8}", end="")
    print()
    
    for p1 in profiles:
        print(f"   {p1.npc_id[:6]:<6}", end="")
        for p2 in profiles:
            compat = calculate_personality_compatibility(p1, p2)
            print(f"{compat:>8.2f}", end="")
        print()
    
    print("\n" + "="*60)
    print("  ✅ Personality System Complete")
    print("="*60)

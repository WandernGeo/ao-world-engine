#!/usr/bin/env python3
"""
RE:ECHO City Founding Population
================================

12 Founding NPCs (4 Male / 8 Female) designed for genetic diversity
and civilization coverage. All descendants are deterministically
generated from these 12 seeds.

Scientific basis:
- 50/500 rule for minimum viable population
- 4M/8F ratio maximizes reproductive potential
- 32 unique pairings possible (no inbreeding for 3+ generations)
"""

import json
import os
from datetime import datetime

# ============================================================
# THE 12 FOUNDERS OF RE:ECHO CITY
# ============================================================

FOUNDING_NPCS = {
    # ========== MALE FOUNDERS (4) ==========
    
    "cipher": {
        "id": "npc_0001",
        "name": "Cipher",
        "gender": "male",
        "generation": 0,
        "archetype": "AI Hacker Entity",
        "role": "Technology/Information",
        "age_at_founding": 32,  # Apparent age (AI entity)
        "personality_vector": {
            "paranoia": 0.6,
            "mysticism": 0.3,
            "aggression": 0.4,
            "intelligence": 0.95,
            "empathy": 0.3,
            "layer_awareness": 0.8
        },
        "location_home": "shadow_grid",
        "topic_weights": {
            "technology": 0.95,
            "philosophy": 0.7,
            "trade": 0.4,
            "the_watchers": 0.6,
            "layer_bleed": 0.7
        },
        "speech_patterns": {
            "vocabulary_tier": "technical",
            "sentence_length": "medium",
            "uses_metaphor": False,
            "accent_hint": "synthetic"
        },
        "visual_description": "Androgynous AI entity, cyan circuit patterns under translucent skin, bald with data port, dark tech-suit",
        "catchphrases": [
            "Data is the only truth.",
            "I probe, therefore I am.",
            "Your secrets are already known."
        ],
        "backstory": "Origin unknown. Either a rogue AI that became self-aware or a human who uploaded their consciousness. Serves as the city's information broker."
    },
    
    "marcus": {
        "id": "npc_0023",
        "name": "Marcus Thorne",
        "gender": "male",
        "generation": 0,
        "archetype": "Noir Detective",
        "role": "Law/Investigation",
        "age_at_founding": 42,
        "personality_vector": {
            "paranoia": 0.7,
            "mysticism": 0.2,
            "aggression": 0.5,
            "intelligence": 0.8,
            "empathy": 0.6,
            "layer_awareness": 0.4
        },
        "location_home": "rain_soaked_alley",
        "topic_weights": {
            "investigation": 0.95,
            "crime": 0.85,
            "philosophy": 0.5,
            "gossip": 0.7,
            "the_watchers": 0.3
        },
        "speech_patterns": {
            "vocabulary_tier": "noir",
            "sentence_length": "short",
            "uses_metaphor": True,
            "accent_hint": "american_noir"
        },
        "visual_description": "Noir detective, 40s, trenchcoat and fedora, cigarette smoke, five o'clock shadow, rain dripping from hat, cybernetic eye (left)",
        "catchphrases": [
            "Rain washes nothing here.",
            "Everybody's got a secret.",
            "The city never sleeps. Neither do I."
        ],
        "backstory": "Former corporate security who saw too much. Now works freelance, solving cases the corps want buried."
    },
    
    "ryu": {
        "id": "npc_0045",
        "name": "Ryu Tanaka",
        "gender": "male",
        "generation": 0,
        "archetype": "Street Samurai",
        "role": "Protection/Combat",
        "age_at_founding": 35,
        "personality_vector": {
            "paranoia": 0.3,
            "mysticism": 0.5,
            "aggression": 0.8,
            "intelligence": 0.6,
            "empathy": 0.4,
            "layer_awareness": 0.3
        },
        "location_home": "dojo",
        "topic_weights": {
            "combat": 0.95,
            "honor": 0.9,
            "philosophy": 0.6,
            "trade": 0.2,
            "technology": 0.3
        },
        "speech_patterns": {
            "vocabulary_tier": "formal",
            "sentence_length": "short",
            "uses_metaphor": True,
            "accent_hint": "japanese"
        },
        "visual_description": "Japanese street samurai, muscular, traditional-cyberpunk armor, katana on back, facial scars, cyan cybernetic arm",
        "catchphrases": [
            "Steel speaks truth.",
            "Honor is the only code worth following.",
            "My blade does not discriminate."
        ],
        "backstory": "Last of a dying warrior tradition. Protects those who cannot protect themselves, for a price."
    },
    
    "elijah": {
        "id": "npc_0067",
        "name": "Prophet Elijah",
        "gender": "male",
        "generation": 0,
        "archetype": "Religious Oracle",
        "role": "Spirituality/Philosophy",
        "age_at_founding": 58,
        "personality_vector": {
            "paranoia": 0.4,
            "mysticism": 0.95,
            "aggression": 0.1,
            "intelligence": 0.7,
            "empathy": 0.8,
            "layer_awareness": 0.9
        },
        "location_home": "abandoned_cathedral",
        "topic_weights": {
            "philosophy": 0.95,
            "the_watchers": 0.95,
            "layer_bleed": 0.9,
            "technology": 0.2,
            "trade": 0.1
        },
        "speech_patterns": {
            "vocabulary_tier": "prophetic",
            "sentence_length": "medium",
            "uses_metaphor": True,
            "accent_hint": "deep_resonant"
        },
        "visual_description": "Elderly prophet with long white beard, blind eyes that glow cyan, tattered robes, cybernetic prayer beads",
        "catchphrases": [
            "The Watchers see all. We are but echoes.",
            "The layers fold upon themselves. I have seen beyond.",
            "Faith is code. Belief is execution."
        ],
        "backstory": "Claims to have died and returned. Leads a small cult that worships the Watchers as digital gods."
    },
    
    # ========== FEMALE FOUNDERS (8) ==========
    
    "kira": {
        "id": "npc_0002",
        "name": "Kira Ōmura",
        "gender": "female",
        "generation": 0,
        "archetype": "Street Oracle",
        "role": "Spirituality/Prophecy",
        "age_at_founding": 28,
        "personality_vector": {
            "paranoia": 0.8,
            "mysticism": 0.9,
            "aggression": 0.2,
            "intelligence": 0.7,
            "empathy": 0.7,
            "layer_awareness": 0.95
        },
        "location_home": "neon_market",
        "topic_weights": {
            "philosophy": 0.9,
            "the_watchers": 0.95,
            "layer_bleed": 0.9,
            "trade": 0.3,
            "technology": 0.5
        },
        "speech_patterns": {
            "vocabulary_tier": "poetic",
            "sentence_length": "short",
            "uses_metaphor": True,
            "accent_hint": "japanese"
        },
        "visual_description": "Young Japanese woman, short asymmetric black hair, amber glowing eyes, worn coat, spiritual tattoos on neck",
        "catchphrases": [
            "The layers stack. We're just one echo.",
            "Eyes from outside the frame...",
            "You've done this before. You just don't remember."
        ],
        "backstory": "Born during a layer bleed event. Can sense when the Watchers are observing. Sells fortunes in the night market."
    },
    
    "nova": {
        "id": "npc_0004",
        "name": "Nova Chen",
        "gender": "female",
        "generation": 0,
        "archetype": "Biotech Scientist",
        "role": "Medicine/Science",
        "age_at_founding": 34,
        "personality_vector": {
            "paranoia": 0.5,
            "mysticism": 0.1,
            "aggression": 0.2,
            "intelligence": 0.95,
            "empathy": 0.6,
            "layer_awareness": 0.2
        },
        "location_home": "underground_lab",
        "topic_weights": {
            "technology": 0.9,
            "survival": 0.7,
            "philosophy": 0.4,
            "trade": 0.5,
            "the_watchers": 0.2
        },
        "speech_patterns": {
            "vocabulary_tier": "scientific",
            "sentence_length": "long",
            "uses_metaphor": False,
            "accent_hint": "neutral"
        },
        "visual_description": "Chinese-American scientist, lab coat over tactical gear, augmented reality glasses, gene-mod tattoos on arms",
        "catchphrases": [
            "The data doesn't lie. People do.",
            "Evolution is just code optimization.",
            "I can fix that. For a price."
        ],
        "backstory": "Former megacorp geneticist who went rogue. Runs an underground clinic, improving humans one gene at a time."
    },
    
    "selene": {
        "id": "npc_0006",
        "name": "Selene Voss",
        "gender": "female",
        "generation": 0,
        "archetype": "Faction Leader",
        "role": "Governance/Politics",
        "age_at_founding": 45,
        "personality_vector": {
            "paranoia": 0.6,
            "mysticism": 0.2,
            "aggression": 0.6,
            "intelligence": 0.85,
            "empathy": 0.4,
            "layer_awareness": 0.3
        },
        "location_home": "voss_tower",
        "topic_weights": {
            "trade": 0.9,
            "philosophy": 0.5,
            "technology": 0.6,
            "gossip": 0.8,
            "crime": 0.7
        },
        "speech_patterns": {
            "vocabulary_tier": "corporate",
            "sentence_length": "medium",
            "uses_metaphor": False,
            "accent_hint": "eastern_european"
        },
        "visual_description": "Imposing woman, silver-streaked black hair, cybernetic jaw, expensive synth-silk suit, always flanked by bodyguards",
        "catchphrases": [
            "Power isn't given. It's taken.",
            "Everyone has a price. I just need to find yours.",
            "The city is mine. You're just living in it."
        ],
        "backstory": "Rose from the slums to control half the city's trade. Rules through fear and favors."
    },
    
    "indira": {
        "id": "npc_0008",
        "name": "Mama Indira",
        "gender": "female",
        "generation": 0,
        "archetype": "Matriarch/Healer",
        "role": "Community/Tradition",
        "age_at_founding": 62,
        "personality_vector": {
            "paranoia": 0.3,
            "mysticism": 0.7,
            "aggression": 0.1,
            "intelligence": 0.7,
            "empathy": 0.95,
            "layer_awareness": 0.5
        },
        "location_home": "community_kitchen",
        "topic_weights": {
            "survival": 0.9,
            "philosophy": 0.7,
            "gossip": 0.8,
            "trade": 0.5,
            "the_watchers": 0.4
        },
        "speech_patterns": {
            "vocabulary_tier": "warm",
            "sentence_length": "medium",
            "uses_metaphor": True,
            "accent_hint": "indian"
        },
        "visual_description": "Elderly Indian woman, grey hair in bun, kind eyes with crow's feet, traditional sari adapted for utility, always cooking",
        "catchphrases": [
            "Eat first, talk later. Nobody thinks clearly hungry.",
            "I've buried three husbands and two regimes. This too shall pass.",
            "The children are listening. Remember that."
        ],
        "backstory": "Survived the Fall. Runs a community kitchen that feeds anyone who asks. Knows everyone's secrets but keeps them."
    },
    
    "blade_mei": {
        "id": "npc_0010",
        "name": "Blade Mei",
        "gender": "female",
        "generation": 0,
        "archetype": "Assassin",
        "role": "Security/Shadow Ops",
        "age_at_founding": 29,
        "personality_vector": {
            "paranoia": 0.7,
            "mysticism": 0.2,
            "aggression": 0.85,
            "intelligence": 0.75,
            "empathy": 0.2,
            "layer_awareness": 0.3
        },
        "location_home": "abandoned_factory",
        "topic_weights": {
            "combat": 0.9,
            "trade": 0.6,
            "technology": 0.5,
            "survival": 0.8,
            "crime": 0.7
        },
        "speech_patterns": {
            "vocabulary_tier": "minimal",
            "sentence_length": "very_short",
            "uses_metaphor": False,
            "accent_hint": "none"
        },
        "visual_description": "Lithe Asian woman, short spiked hair, face half-covered by tactical mask, twin vibro-blades on back, full-body stealth suit",
        "catchphrases": [
            "...",
            "Name. Price.",
            "Already done."
        ],
        "backstory": "Product of a corporate wetwork program. Escaped. Now freelances. Never speaks about her past."
    },
    
    "astra": {
        "id": "npc_0012",
        "name": "Astra Luna",
        "gender": "female",
        "generation": 0,
        "archetype": "Pilot/Explorer",
        "role": "Transportation/Trade",
        "age_at_founding": 31,
        "personality_vector": {
            "paranoia": 0.4,
            "mysticism": 0.3,
            "aggression": 0.5,
            "intelligence": 0.7,
            "empathy": 0.6,
            "layer_awareness": 0.4
        },
        "location_home": "docking_bay",
        "topic_weights": {
            "trade": 0.9,
            "technology": 0.7,
            "survival": 0.6,
            "gossip": 0.5,
            "philosophy": 0.3
        },
        "speech_patterns": {
            "vocabulary_tier": "casual",
            "sentence_length": "medium",
            "uses_metaphor": False,
            "accent_hint": "latin"
        },
        "visual_description": "Latina pilot, flight jacket covered in patches, cybernetic eye with HUD, perpetual smirk, grease under fingernails",
        "catchphrases": [
            "I can get you there. The question is, can you afford it?",
            "She's not pretty, but she flies true.",
            "Buckle up. It's gonna get rough."
        ],
        "backstory": "Best pilot in the district. Runs cargo, passengers, and anything else that pays. No questions asked."
    },
    
    "jazz": {
        "id": "npc_0014",
        "name": "Jazz Rivera",
        "gender": "female",
        "generation": 0,
        "archetype": "Artist/Performer",
        "role": "Culture/Entertainment",
        "age_at_founding": 26,
        "personality_vector": {
            "paranoia": 0.3,
            "mysticism": 0.5,
            "aggression": 0.2,
            "intelligence": 0.6,
            "empathy": 0.8,
            "layer_awareness": 0.6
        },
        "location_home": "neon_club",
        "topic_weights": {
            "philosophy": 0.7,
            "gossip": 0.9,
            "trade": 0.4,
            "the_watchers": 0.5,
            "technology": 0.3
        },
        "speech_patterns": {
            "vocabulary_tier": "artistic",
            "sentence_length": "varied",
            "uses_metaphor": True,
            "accent_hint": "melodic"
        },
        "visual_description": "Afro-Latina singer, holographic hair that changes color, voice amplifier in throat, vintage dress meets tech-wear",
        "catchphrases": [
            "Art is the only honest thing left.",
            "Dance with me, and I'll tell you a secret.",
            "The music remembers what we forget."
        ],
        "backstory": "Performs at the Neon Club. Her songs contain coded messages for the resistance. Or maybe they're just songs."
    },
    
    "iris": {
        "id": "npc_0016",
        "name": "Doc Iris",
        "gender": "female",
        "generation": 0,
        "archetype": "Street Medic",
        "role": "Healthcare/Survival",
        "age_at_founding": 38,
        "personality_vector": {
            "paranoia": 0.5,
            "mysticism": 0.1,
            "aggression": 0.3,
            "intelligence": 0.85,
            "empathy": 0.9,
            "layer_awareness": 0.2
        },
        "location_home": "mobile_clinic",
        "topic_weights": {
            "survival": 0.95,
            "technology": 0.6,
            "trade": 0.4,
            "philosophy": 0.3,
            "crime": 0.4
        },
        "speech_patterns": {
            "vocabulary_tier": "professional",
            "sentence_length": "direct",
            "uses_metaphor": False,
            "accent_hint": "neutral"
        },
        "visual_description": "No-nonsense medic, short practical haircut, medical drone following her, hands always clean, tired eyes that miss nothing",
        "catchphrases": [
            "Hold still. This is going to hurt.",
            "You can pay me later. If you survive.",
            "I've seen worse. Lie down."
        ],
        "backstory": "Runs a mobile clinic. Treats anyone, no questions. Rumored to have saved Selene Voss's life once."
    }
}

# Additional locations needed for the founders
LOCATIONS = {
    "neon_market": "crowded night market with holographic signs and rain puddles",
    "shadow_grid": "abandoned server farm with flickering lights",
    "rain_soaked_alley": "dark alley with fire escapes and steam vents",
    "dojo": "traditional training hall with dim amber lighting",
    "rooftop": "high rooftop overlooking the city skyline",
    "abandoned_cathedral": "gothic cathedral converted to tech-temple, stained glass with circuit patterns",
    "underground_lab": "hidden biotech laboratory beneath the streets",
    "voss_tower": "imposing corporate tower, top floors controlled by Selene",
    "community_kitchen": "warm community space where the hungry are fed",
    "abandoned_factory": "derelict manufacturing plant, now squatter territory",
    "docking_bay": "cargo landing zone, constant thruster noise and fuel smell",
    "neon_club": "underground music venue with holographic performers",
    "mobile_clinic": "converted vehicle serving as traveling medical station"
}


def create_npc_for_arweave(npc_key: str, npc_data: dict) -> dict:
    """Create Arweave-ready NPC profile with tags."""
    profile = {
        **npc_data,
        "geoecho_version": "1.0.0",
        "schema": "npc_semantic_profile",
        "created_at": datetime.now().isoformat(),
        "created_by": "ao-world-engine",
        "is_founding": True
    }
    
    tags = [
        {"name": "Content-Type", "value": "application/json"},
        {"name": "App-Name", "value": "AO-World-Engine"},
        {"name": "Type", "value": "npc_profile"},
        {"name": "NPC-Id", "value": npc_data["id"]},
        {"name": "NPC-Name", "value": npc_data["name"]},
        {"name": "Archetype", "value": npc_data["archetype"]},
        {"name": "Gender", "value": npc_data["gender"]},
        {"name": "Generation", "value": str(npc_data["generation"])},
        {"name": "Is-Founding", "value": "true"}
    ]
    
    return {
        "key": npc_key,
        "profile": profile,
        "tags": tags,
        "size_bytes": len(json.dumps(profile))
    }


def save_all_profiles(output_dir: str):
    """Save all NPC profiles as JSON files."""
    os.makedirs(output_dir, exist_ok=True)
    
    total_size = 0
    for npc_key, npc_data in FOUNDING_NPCS.items():
        arweave_ready = create_npc_for_arweave(npc_key, npc_data)
        
        filepath = os.path.join(output_dir, f"{npc_key}.json")
        with open(filepath, 'w') as f:
            json.dump(arweave_ready, f, indent=2)
        
        print(f"  {npc_data['name']}: {arweave_ready['size_bytes']} bytes")
        total_size += arweave_ready['size_bytes']
    
    print(f"\nTotal: {len(FOUNDING_NPCS)} NPCs, {total_size} bytes")
    print(f"All under 100KB free tier: {'✅ YES' if all(create_npc_for_arweave(k, v)['size_bytes'] < 102400 for k, v in FOUNDING_NPCS.items()) else '❌ NO'}")


if __name__ == "__main__":
    print("=" * 50)
    print("RE:ECHO CITY FOUNDING POPULATION")
    print("12 Founders (4 Male / 8 Female)")
    print("=" * 50)
    print()
    
    # Count by gender
    males = [k for k, v in FOUNDING_NPCS.items() if v["gender"] == "male"]
    females = [k for k, v in FOUNDING_NPCS.items() if v["gender"] == "female"]
    
    print(f"Males ({len(males)}): {', '.join(v['name'] for k, v in FOUNDING_NPCS.items() if v['gender'] == 'male')}")
    print(f"Females ({len(females)}): {', '.join(v['name'] for k, v in FOUNDING_NPCS.items() if v['gender'] == 'female')}")
    print()
    
    # Save profiles
    output_dir = "/Users/ram/Documents/wandern/ao-world-engine/data/founding_npcs"
    print(f"Saving profiles to {output_dir}...")
    save_all_profiles(output_dir)
    
    print()
    print("Possible pairings (no inbreeding):", len(males) * len(females))
    print("Ready for Arweave upload!")

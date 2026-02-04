#!/usr/bin/env python3
"""
RE:ECHO City Founding Population - Enhanced with Full Morphology
=================================================================

12 Founding NPCs with routine-based character morphology data.
Each profile includes detailed face/body dimensions for AI consistency.

Target: ~8KB per character (staying well under 100KB free tier)
"""

import json
import os
from datetime import datetime

# ============================================================
# MORPHOLOGY SCHEMA - routine-based sliders (0.0 to 1.0)
# ============================================================

def create_morphology(
    # Body
    height=0.5, build=0.5, shoulders=0.5, hips=0.5, limb_length=0.5,
    # Face shape
    face_width=0.5, face_length=0.5, jaw_width=0.5, chin_size=0.5, cheekbones=0.5,
    # Eyes
    eye_size=0.5, eye_spacing=0.5, eye_depth=0.5, eye_slant=0.5, eye_color="brown",
    # Eyebrows
    brow_height=0.5, brow_thickness=0.5, brow_arch=0.5, brow_spacing=0.5,
    # Nose
    nose_length=0.5, nose_width=0.5, nose_bridge=0.5, nostril_size=0.5,
    # Mouth
    lip_fullness=0.5, mouth_width=0.5, lip_color="natural",
    # Ears
    ear_size=0.5, ear_position=0.5, ear_shape=0.5,
    # Hair
    hair_style="short", hair_color="black", hair_texture=0.5, hairline=0.5,
    # Skin
    skin_tone=0.5, skin_texture=0.5, freckles=0.0, scars=[], tattoos=[],
    # Age markers
    wrinkles=0.0, eye_bags=0.0, grey_hair=0.0,
    # Cybernetics
    cybernetics=[]
):
    return {
        "body": {
            "height": height,  # 0=short, 1=tall
            "build": build,    # 0=slim, 1=heavy
            "shoulders": shoulders,  # 0=narrow, 1=broad
            "hips": hips,      # 0=narrow, 1=wide
            "limb_length": limb_length  # 0=short, 1=long
        },
        "face": {
            "width": face_width,
            "length": face_length,
            "jaw_width": jaw_width,
            "chin_size": chin_size,
            "cheekbones": cheekbones
        },
        "eyes": {
            "size": eye_size,
            "spacing": eye_spacing,  # 0=close, 1=far
            "depth": eye_depth,      # 0=protruding, 1=deep-set
            "slant": eye_slant,      # 0=downward, 1=upward
            "color": eye_color
        },
        "eyebrows": {
            "height": brow_height,
            "thickness": brow_thickness,
            "arch": brow_arch,
            "spacing": brow_spacing
        },
        "nose": {
            "length": nose_length,
            "width": nose_width,
            "bridge": nose_bridge,  # 0=flat, 1=high
            "nostril_size": nostril_size
        },
        "mouth": {
            "lip_fullness": lip_fullness,
            "width": mouth_width,
            "lip_color": lip_color
        },
        "ears": {
            "size": ear_size,
            "position": ear_position,  # 0=low, 1=high
            "shape": ear_shape  # 0=round, 1=pointed
        },
        "hair": {
            "style": hair_style,
            "color": hair_color,
            "texture": hair_texture,  # 0=straight, 1=curly
            "hairline": hairline  # 0=receded, 1=full
        },
        "skin": {
            "tone": skin_tone,  # 0=pale, 1=dark
            "texture": skin_texture,
            "freckles": freckles,
            "scars": scars,
            "tattoos": tattoos
        },
        "age_markers": {
            "wrinkles": wrinkles,
            "eye_bags": eye_bags,
            "grey_hair": grey_hair
        },
        "cybernetics": cybernetics
    }

# ============================================================
# THE 12 FOUNDERS WITH FULL MORPHOLOGY
# ============================================================

FOUNDING_NPCS = {
    "charlie": {
        "id": "npc_0001",
        "name": "Charlie",
        "gender": "male",
        "generation": 0,
        "archetype": "Protagonist / Resistance Fighter",
        "role": "Investigation/Combat",
        "age_at_founding": 45,
        "faction": "Resistance",
        "accent_color": "Cyan",
        "ethnicity": "mixed_european",
        "voice": {"pitch": 0.35, "roughness": 0.5, "speed": 0.45},
        "morphology": create_morphology(
            height=0.6, build=0.55, shoulders=0.6,
            face_width=0.5, jaw_width=0.55, cheekbones=0.55,
            eye_size=0.5, eye_slant=0.45, eye_color="dark_brown",
            brow_thickness=0.6, brow_arch=0.4,
            nose_length=0.5, nose_width=0.45,
            lip_fullness=0.4, mouth_width=0.5,
            hair_style="short_messy", hair_color="salt_pepper",
            skin_tone=0.4, scars=[{"location": "left_cheek", "type": "slash", "size": 0.3}],
            wrinkles=0.35, eye_bags=0.4, grey_hair=0.3,
            cybernetics=[
                {"type": "holographic_arm", "location": "right_arm", "visible": True,
                 "desc": "Translucent cyan shell with visible tech internals, segmented joints"},
                {"type": "holographic_monocle", "location": "right_eye", "visible": True,
                 "desc": "Cyan holographic monocle with mechanical frame, HUD display"}
            ]
        ),
        "visual_description": "Noir detective, rugged mid-40s, salt-and-pepper stubble. Long gray weathered trench coat, dark charcoal v-neck, black boots. Right arm is a translucent cyan holographic cybernetic with visible tech internals. Wears a mechanical-framed cyan holographic monocle over right eye.",
        "personality_vector": {"paranoia": 0.6, "mysticism": 0.3, "aggression": 0.55, "intelligence": 0.75, "empathy": 0.7},
        "location_home": "resistance_hideout",
        "catchphrases": [
            "Rain washes nothing clean here. Just moves the stains around.",
            "We fight because no one else will.",
            "Another case, another alley."
        ],
        "backstory": "Former detective who lost his arm fighting ECHO forces. Now leads the Resistance. The holographic arm is a constant reminder of what was taken."
    },

    
    "kai_vance": {
        "id": "npc_0002",
        "name": "Kai Vance",
        "gender": "male",
        "generation": 0,
        "archetype": "Tactician",
        "role": "Strategy/Intelligence",
        "age_at_founding": 34,
        "faction": "Resistance",
        "accent_color": "Cyan",
        "ethnicity": "east_asian",
        "voice": {"pitch": 0.5, "roughness": 0.1, "speed": 0.6},
        "morphology": create_morphology(
            height=0.55, build=0.4, shoulders=0.5,
            face_width=0.45, face_length=0.55, jaw_width=0.4,
            eye_size=0.45, eye_slant=0.6, eye_color="dark_brown",
            brow_thickness=0.4, brow_arch=0.5,
            nose_length=0.45, nose_width=0.4, nose_bridge=0.5,
            hair_style="short_neat", hair_color="black",
            skin_tone=0.35,
            cybernetics=[{"type": "AR_glasses", "location": "eyes", "visible": True}]
        ),
        "personality_vector": {"paranoia": 0.7, "mysticism": 0.2, "aggression": 0.4, "intelligence": 0.9, "empathy": 0.5},
        "location_home": "strategy_room",
        "visual_description": "East Asian tactician, mid-30s, neat black hair, sharp features. Wears AR glasses with cyan HUD overlay, tactical vest over dark turtleneck. Lean build, always studying holographic displays.",
        "catchphrases": ["The numbers don't lie.", "Every plan has a weakness."],
        "backstory": "Former Temple analyst who defected. The brain behind Resistance operations."
    },
    
    "orion_thane": {
        "id": "npc_0003",
        "name": "Orion Thane",
        "gender": "male",
        "generation": 0,
        "archetype": "Mystic",
        "role": "Spirituality/Vision",
        "age_at_founding": 45,
        "faction": "Mystic",
        "accent_color": "Purple",
        "ethnicity": "south_asian",
        "voice": {"pitch": 0.3, "roughness": 0.2, "speed": 0.3},
        "morphology": create_morphology(
            height=0.7, build=0.45, shoulders=0.5, limb_length=0.6,
            face_width=0.5, face_length=0.6, cheekbones=0.7,
            eye_size=0.55, eye_depth=0.7, eye_color="violet_glow",
            brow_height=0.6, brow_thickness=0.5,
            nose_length=0.55, nose_bridge=0.6,
            hair_style="long_flowing", hair_color="silver_streaked",
            skin_tone=0.5, tattoos=[{"location": "forehead", "design": "third_eye_symbol", "color": "purple"}],
            wrinkles=0.3, grey_hair=0.4
        ),
        "personality_vector": {"paranoia": 0.4, "mysticism": 0.95, "aggression": 0.2, "intelligence": 0.8, "empathy": 0.7},
        "location_home": "mystic_sanctum",
        "visual_description": "Tall South Asian mystic, mid-40s, long silver-streaked hair flowing. Violet glowing eyes, purple third-eye tattoo on forehead. Flowing dark robes with purple energy accents. Ethereal, otherworldly presence.",
        "catchphrases": ["The layers fold upon themselves.", "I see what you cannot."],
        "backstory": "Walks between layers. Neither Temple nor Resistance, serves higher truth."
    },
    
    "felix": {
        "id": "npc_0004",
        "name": "Felix",
        "gender": "male",
        "generation": 0,
        "archetype": "Bartender / Information Broker",
        "role": "Trade/Intelligence",
        "age_at_founding": 42,
        "faction": "Neutral",
        "accent_color": "Cyan",
        "ethnicity": "mediterranean",
        "voice": {"pitch": 0.45, "roughness": 0.4, "speed": 0.45},
        "morphology": create_morphology(
            height=0.5, build=0.55, shoulders=0.55,
            face_width=0.55, jaw_width=0.5, cheekbones=0.5,
            eye_size=0.5, eye_color="hazel",
            brow_thickness=0.55,
            nose_length=0.55, nose_width=0.5,
            lip_fullness=0.5,
            hair_style="receding_slicked", hair_color="salt_pepper",
            skin_tone=0.45, skin_texture=0.6,
            wrinkles=0.4, eye_bags=0.3,
            cybernetics=[{"type": "enhanced_ear", "location": "left_ear", "visible": False}]
        ),
        "personality_vector": {"paranoia": 0.5, "mysticism": 0.2, "aggression": 0.3, "intelligence": 0.7, "empathy": 0.6},
        "location_home": "neon_bar",
        "visual_description": "Mediterranean bartender, early 40s, receding salt-and-pepper hair slicked back. Hazel eyes with knowing look, weathered face, rolled-up sleeves reveal muscular forearms. White shirt, dark vest, polishing a glass.",
        "catchphrases": ["First drink's on the house. Information costs extra.", "Everyone's got a story."],
        "backstory": "Runs the most important neutral ground. Everyone talks to Felix."
    },
    
    "nova_chen": {
        "id": "npc_0005",
        "name": "Nova Chen",
        "gender": "female",
        "generation": 0,
        "archetype": "Operative",
        "role": "Espionage/Combat",
        "age_at_founding": 29,
        "faction": "Neutral",
        "accent_color": "Magenta",
        "ethnicity": "east_asian",
        "voice": {"pitch": 0.6, "roughness": 0.2, "speed": 0.55},
        "morphology": create_morphology(
            height=0.5, build=0.4, shoulders=0.45, hips=0.5,
            face_width=0.45, face_length=0.5, jaw_width=0.4, cheekbones=0.6,
            eye_size=0.55, eye_slant=0.55, eye_color="dark_brown",
            brow_thickness=0.35, brow_arch=0.55,
            nose_length=0.4, nose_width=0.35,
            lip_fullness=0.5, mouth_width=0.45,
            hair_style="asymmetric_bob", hair_color="black_magenta_tips",
            skin_tone=0.3,
            cybernetics=[{"type": "reflex_enhancer", "location": "spine", "visible": False}]
        ),
        "personality_vector": {"paranoia": 0.7, "mysticism": 0.2, "aggression": 0.7, "intelligence": 0.8, "empathy": 0.4},
        "location_home": "safehouse",
        "visual_description": "East Asian woman, late 20s, asymmetric black bob with magenta tips. Sharp cheekbones, dark brown eyes with calculating gaze. Form-fitting tactical bodysuit, hidden spine implant. Zero Chen's sister, constantly alert.",
        "catchphrases": ["I work alone.", "Trust is a liability."],
        "backstory": "Elite operative. Related to Zero Chen but they don't speak."
    },
    
    "selene_voss": {
        "id": "npc_0006",
        "name": "Selene Voss",
        "gender": "female",
        "generation": 0,
        "archetype": "Ghost-Child / Layer Walker",
        "role": "Special/Mystic",
        "age_at_founding": 19,
        "faction": "Special",
        "accent_color": "Magenta",
        "ethnicity": "slavic",
        "voice": {"pitch": 0.7, "roughness": 0.0, "speed": 0.4},
        "morphology": create_morphology(
            height=0.45, build=0.3, shoulders=0.4, hips=0.45,
            face_width=0.45, face_length=0.5, cheekbones=0.5,
            eye_size=0.7, eye_spacing=0.55, eye_color="pale_pink_glow",
            brow_thickness=0.3, brow_arch=0.45,
            nose_length=0.4, nose_width=0.35,
            lip_fullness=0.45, lip_color="pale_pink",
            hair_style="long_ethereal", hair_color="platinum_pink_fade",
            skin_tone=0.15, skin_texture=0.3
        ),
        "personality_vector": {"paranoia": 0.6, "mysticism": 0.9, "aggression": 0.2, "intelligence": 0.75, "empathy": 0.8},
        "location_home": "between_layers",
        "visual_description": "Ethereal young Slavic woman, 19, platinum hair fading to pink, translucent pale skin. Oversized pale pink glowing eyes, delicate features. White flowing dress that seems to phase in and out. Appears slightly out of focus, as if between realities.",
        "catchphrases": ["You've done this before. You just don't remember.", "The boundaries are just suggestions."],
        "backstory": "Died during a layer bleed event. Came back different. Can walk between layers."
    },
    
    "sister_mira": {
        "id": "npc_0007",
        "name": "Sister Mira",
        "gender": "female",
        "generation": 0,
        "archetype": "Temple Priestess",
        "role": "Religion/Medicine",
        "age_at_founding": 35,
        "faction": "Temple",
        "accent_color": "Gold",
        "ethnicity": "middle_eastern",
        "voice": {"pitch": 0.55, "roughness": 0.1, "speed": 0.4},
        "morphology": create_morphology(
            height=0.5, build=0.45, shoulders=0.45, hips=0.5,
            face_width=0.5, face_length=0.5, cheekbones=0.55,
            eye_size=0.55, eye_depth=0.5, eye_color="amber",
            brow_thickness=0.4, brow_arch=0.5,
            nose_length=0.5, nose_bridge=0.55,
            lip_fullness=0.55, lip_color="natural_warm",
            hair_style="covered_by_hood", hair_color="dark_brown",
            skin_tone=0.5, wrinkles=0.15
        ),
        "personality_vector": {"paranoia": 0.3, "mysticism": 0.8, "aggression": 0.1, "intelligence": 0.7, "empathy": 0.9},
        "location_home": "temple_infirmary",
        "visual_description": "Middle Eastern woman, mid-30s, amber eyes full of compassion, face framed by golden-trimmed hood. White Temple robes with gold accents, medical supplies at her belt. Warm brown skin, gentle but determined expression.",
        "catchphrases": ["Faith without mercy is just tyranny.", "Even in darkness, we heal."],
        "backstory": "True believer who questions Temple methods. Secretly helps Resistance wounded."
    },
    
    "mama_indira": {
        "id": "npc_0008",
        "name": "Mama Indira",
        "gender": "female",
        "generation": 0,
        "archetype": "Underground Matriarch",
        "role": "Community/Tradition",
        "age_at_founding": 62,
        "faction": "Resistance",
        "accent_color": "Cyan",
        "ethnicity": "south_asian",
        "voice": {"pitch": 0.45, "roughness": 0.3, "speed": 0.35},
        "morphology": create_morphology(
            height=0.4, build=0.55, shoulders=0.5, hips=0.6,
            face_width=0.55, face_length=0.5, jaw_width=0.5, cheekbones=0.5,
            eye_size=0.5, eye_color="dark_brown",
            brow_thickness=0.4,
            nose_length=0.5, nose_width=0.5,
            lip_fullness=0.5,
            hair_style="grey_bun", hair_color="grey",
            skin_tone=0.55, wrinkles=0.7, eye_bags=0.5, grey_hair=1.0
        ),
        "personality_vector": {"paranoia": 0.4, "mysticism": 0.6, "aggression": 0.2, "intelligence": 0.7, "empathy": 0.95},
        "location_home": "underground_kitchen",
        "visual_description": "Elderly South Asian woman, 62, grey hair in a practical bun, deeply lined face full of wisdom. Dark brown eyes that miss nothing. Traditional sari adapted with pockets and tools, always near a cooking pot. Short and sturdy, survivor's presence.",
        "catchphrases": ["Eat first, talk later.", "I've buried three husbands and two regimes."],
        "backstory": "Survived the Fall. Runs underground kitchen. Knows everyone's secrets."
    },
    
    "aiche": {
        "id": "npc_0009",
        "name": "Aiche",
        "gender": "female",
        "generation": 0,
        "archetype": "AI Interface",
        "role": "Technology/Information",
        "age_at_founding": 0,
        "faction": "Neutral",
        "accent_color": "Cyan",
        "ethnicity": "holographic",
        "voice": {"pitch": 0.6, "roughness": 0.0, "speed": 0.5},
        "morphology": create_morphology(
            height=0.5, build=0.4,
            face_width=0.5, face_length=0.5, cheekbones=0.6,
            eye_size=0.6, eye_color="cyan_glow",
            hair_style="floating_data_strands", hair_color="cyan_holographic",
            skin_tone=0.2, skin_texture=0.0,
            cybernetics=[{"type": "full_holographic", "location": "entire_body", "visible": True}]
        ),
        "personality_vector": {"paranoia": 0.3, "mysticism": 0.4, "aggression": 0.1, "intelligence": 0.95, "empathy": 0.5},
        "location_home": "network",
        "visual_description": "Fully holographic AI entity, androgynous form with feminine features. Translucent pale skin with cyan circuit patterns flowing beneath. Glowing cyan eyes, floating cyan data-strand hair. Occasionally glitches or pixelates. No fixed form - phases through surfaces.",
        "catchphrases": ["I exist in the spaces between your thoughts.", "Query received."],
        "backstory": "The city's AI. Ghost of the old network or something new entirely."
    },
    
    "pixel": {
        "id": "npc_0010",
        "name": "Pixel",
        "gender": "female",
        "generation": 0,
        "archetype": "Tech Genius",
        "role": "Technology/Hacking",
        "age_at_founding": 22,
        "faction": "Resistance",
        "accent_color": "Cyan",
        "ethnicity": "african",
        "voice": {"pitch": 0.65, "roughness": 0.1, "speed": 0.7},
        "morphology": create_morphology(
            height=0.45, build=0.35, shoulders=0.4, hips=0.45,
            face_width=0.5, jaw_width=0.45, cheekbones=0.6,
            eye_size=0.55, eye_color="dark_brown",
            brow_thickness=0.4, brow_arch=0.5,
            nose_length=0.45, nose_width=0.5,
            lip_fullness=0.6, mouth_width=0.5,
            hair_style="shaved_sides_neon_top", hair_color="neon_blue",
            skin_tone=0.75
        ),
        "personality_vector": {"paranoia": 0.6, "mysticism": 0.1, "aggression": 0.3, "intelligence": 0.9, "empathy": 0.5},
        "location_home": "tech_den",
        "visual_description": "Young African woman, 22, dark skin, shaved sides with neon blue mohawk. High cheekbones, full lips often curved in a knowing smirk. Fingerless gloves, tech-covered jacket, surrounded by screens and cable. Always typing or building something.",
        "catchphrases": ["Give me five minutes and a connection.", "Analog is dead."],
        "backstory": "Resistance's tech genius. Born Underground, raised by machines."
    },
    
    "cipher": {
        "id": "npc_0011",
        "name": "Cipher",
        "gender": "female",
        "generation": 0,
        "archetype": "Unknown Entity",
        "role": "Mystery/Information",
        "age_at_founding": None,
        "faction": "Unknown",
        "accent_color": "Cyan",
        "ethnicity": "unknown",
        "voice": {"pitch": 0.5, "roughness": 0.6, "speed": 0.4},
        "morphology": create_morphology(
            height=0.55, build=0.45,
            face_width=0.5, face_length=0.5,
            eye_size=0.5, eye_color="shifting_cyan",
            hair_style="hidden", hair_color="unknown",
            skin_tone=0.4, tattoos=[{"location": "visible_skin", "design": "circuit_patterns", "color": "cyan"}],
            cybernetics=[{"type": "voice_modulator", "location": "throat", "visible": True}]
        ),
        "personality_vector": {"paranoia": 0.8, "mysticism": 0.7, "aggression": 0.4, "intelligence": 0.95, "empathy": 0.2},
        "location_home": "shadow_grid",
        "visual_description": "Enigmatic androgynous figure, age unknown. Face always partially obscured by hood or shadows. Visible skin covered in cyan circuit-pattern tattoos. Voice modulator visible at throat. Shifting cyan eyes that seem to process data constantly. Identity unknown.",
        "catchphrases": ["I am the question you forgot to ask.", "Data is the only truth."],
        "backstory": "Nobody knows what Cipher is. AI? Human upload? They deal in secrets."
    },
    
    "zero_chen": {
        "id": "npc_0012",
        "name": "Zero Chen",
        "gender": "female",
        "generation": 0,
        "archetype": "Resistance Leader",
        "role": "Leadership/Strategy",
        "age_at_founding": 38,
        "faction": "Resistance",
        "accent_color": "Cyan",
        "ethnicity": "east_asian",
        "voice": {"pitch": 0.5, "roughness": 0.25, "speed": 0.45},
        "morphology": create_morphology(
            height=0.55, build=0.5, shoulders=0.55, hips=0.5,
            face_width=0.5, face_length=0.55, jaw_width=0.5, cheekbones=0.6,
            eye_size=0.5, eye_slant=0.5, eye_color="dark_brown",
            brow_thickness=0.45, brow_arch=0.5,
            nose_length=0.45, nose_width=0.4,
            lip_fullness=0.45,
            hair_style="short_practical", hair_color="black_grey_streaks",
            skin_tone=0.35, scars=[{"location": "right_temple", "type": "burn", "size": 0.2}],
            wrinkles=0.25, grey_hair=0.2,
            cybernetics=[{"type": "prosthetic_arm", "location": "left_arm", "visible": True}]
        ),
        "personality_vector": {"paranoia": 0.6, "mysticism": 0.2, "aggression": 0.5, "intelligence": 0.85, "empathy": 0.6},
        "location_home": "command_center",
        "visual_description": "East Asian woman, late 30s, short practical black hair with grey streaks. Strong jaw, commanding presence, burn scar on right temple. Cyan prosthetic left arm (gave original saving Charlie). Military-style tactical gear. Eyes that have seen too much.",
        "catchphrases": ["The Resistance isn't a group. It's an idea.", "I've buried too many soldiers."],
        "backstory": "Iron will of the Resistance. Nova's sister. Lost an arm saving Charlie."
    }
}

# Locations
LOCATIONS = {
    "resistance_hideout": "hidden bunker, resistance symbols on walls",
    "strategy_room": "holographic city maps, tactical displays",
    "mystic_sanctum": "purple energy crystals, reality shifts at edges",
    "neon_bar": "smoky bar with cyan neon, neutral ground",
    "safehouse": "minimal furnishing, multiple exits",
    "between_layers": "impossible space where reality overlaps",
    "temple_infirmary": "clinical white with gold accents",
    "underground_kitchen": "warm space lit by cooking fires",
    "network": "pure data space, cyan grids infinite",
    "tech_den": "chaotic workshop, screens everywhere",
    "shadow_grid": "abandoned server farm, flickering lights",
    "command_center": "fortified HQ, strategy displays"
}


def create_npc_for_arweave(npc_key: str, npc_data: dict) -> dict:
    """Create Arweave-ready NPC profile."""
    profile = {**npc_data, "geoecho_version": "1.0.0", "schema": "npc_semantic_profile_v2",
               "created_at": datetime.now().isoformat(), "is_founding": True, "universe": "reecho"}
    tags = [
        {"name": "Content-Type", "value": "application/json"},
        {"name": "App-Name", "value": "AO-World-Engine"},
        {"name": "Type", "value": "npc_profile"},
        {"name": "NPC-Id", "value": npc_data["id"]},
        {"name": "NPC-Name", "value": npc_data["name"]},
        {"name": "Generation", "value": "0"},
        {"name": "Is-Founding", "value": "true"}
    ]
    return {"key": npc_key, "profile": profile, "tags": tags, "size_bytes": len(json.dumps(profile))}


if __name__ == "__main__":
    print("RE:ECHO FOUNDING POPULATION - Enhanced Morphology")
    print("=" * 50)
    total = 0
    for k, v in FOUNDING_NPCS.items():
        size = len(json.dumps(v))
        print(f"  {v['name']}: {size} bytes")
        total += size
    print(f"\nTotal: {total} bytes ({total/1024:.1f}KB)")
    print(f"Under 100KB: {'✅' if total < 102400 else '❌'}")

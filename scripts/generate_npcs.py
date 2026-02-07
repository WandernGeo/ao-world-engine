#!/usr/bin/env python3
"""
NPC Batch Generator for AO World Engine
Generates 2,830 NPCs with full StudioRam character attributes.
Uses Gemini Flash for names, backstories, and physical descriptions.

Usage:
    python generate_npcs.py --batch-size 50 --start-id 800 --district harbor_quarter
    python generate_npcs.py --all --output data/generated_npcs/
    python generate_npcs.py --governance --output data/generated_npcs/
"""

import json
import os
import random
import sys
import time
import argparse
from pathlib import Path

# --- Configuration ---

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
CODEC_DIR = DATA_DIR / "codec_chunks"
OUTPUT_DIR = DATA_DIR / "generated_npcs"

DEMOGRAPHICS_FILE = CODEC_DIR / "world_codec_25_district_demographics.json"

# Physical attribute pools
BUILDS = ["slim", "lean", "average", "athletic", "stocky", "muscular", "heavyset", "petite", "tall_lean", "compact"]
HAIR_STYLES = ["short_cropped", "buzz_cut", "afro", "locs", "braids", "box_braids", "cornrows", "straight_long", 
               "straight_short", "wavy", "curly", "bun", "ponytail", "mohawk", "shaved_sides", "natural", "fade",
               "slicked_back", "messy", "bald", "receding", "pixie_cut", "undercut", "twists"]
HAIR_COLORS = ["black", "dark_brown", "brown", "light_brown", "auburn", "red", "blonde", "gray", "white", 
               "silver", "dyed_blue", "dyed_purple", "dyed_pink", "dyed_green", "salt_and_pepper"]
EYE_COLORS = ["dark_brown", "brown", "hazel", "green", "blue", "gray", "amber", "black"]
EYE_SHAPES = ["round", "almond", "hooded", "monolid", "deep_set", "wide_set", "upturned", "downturned"]
FACE_SHAPES = ["oval", "round", "square", "heart", "oblong", "diamond", "rectangular", "triangular"]
LIP_TYPES = ["thin", "medium", "full", "wide", "bow_shaped", "heart_shaped"]
NOSE_TYPES = ["narrow", "broad_bridge", "straight", "button", "aquiline", "flat_bridge", "wide", "snub", "roman"]
JAWLINES = ["soft", "defined", "angular", "rounded", "strong", "square", "pointed"]

SKIN_TONES = {
    "east_asian": ["fair", "light", "medium", "warm_beige"],
    "south_asian": ["light_brown", "medium_brown", "olive", "warm_brown", "deep_brown"],
    "west_african": ["deep_brown", "dark_brown", "rich_brown", "ebony", "mahogany"],
    "caribbean": ["medium_brown", "warm_brown", "light_brown", "caramel", "deep_brown"],
    "european": ["fair", "light", "peach", "olive", "medium"],
    "latino": ["light", "olive", "medium_brown", "warm_beige", "tan", "light_brown"],
    "arab": ["olive", "light_brown", "medium", "warm_beige", "tan"],
    "african_american": ["light_brown", "medium_brown", "warm_brown", "deep_brown", "caramel", "mahogany"],
    "turkish": ["olive", "light_brown", "medium", "warm_beige", "tan"],
    "default": ["light", "medium", "olive", "light_brown", "medium_brown", "deep_brown"]
}

# Job definitions with workplace types
JOB_DEFINITIONS = {
    # Government
    "mayor": {"title": "Mayor", "workplace_type": "city_hall", "income": "upper", "skills": ["leadership", "negotiation", "politics"]},
    "council_member": {"title": "City Council Member", "workplace_type": "city_hall", "income": "upper_middle", "skills": ["politics", "negotiation", "public_speaking"]},
    "chief_judge": {"title": "Chief Judge", "workplace_type": "courthouse", "income": "upper", "skills": ["law", "leadership", "ethics"]},
    "district_judge": {"title": "District Judge", "workplace_type": "courthouse", "income": "upper_middle", "skills": ["law", "investigation", "ethics"]},
    "chief_of_police": {"title": "Chief of Police", "workplace_type": "police_hq", "income": "upper_middle", "skills": ["leadership", "tactics", "law"]},
    "fire_chief": {"title": "Fire Chief", "workplace_type": "fire_station", "income": "upper_middle", "skills": ["leadership", "emergency_response", "logistics"]},
    "health_commissioner": {"title": "Health Commissioner", "workplace_type": "city_hall", "income": "upper_middle", "skills": ["medicine", "public_health", "leadership"]},
    "schools_chancellor": {"title": "Schools Chancellor", "workplace_type": "school_admin", "income": "upper_middle", "skills": ["education", "leadership", "policy"]},
    "city_engineer": {"title": "City Engineer", "workplace_type": "city_hall", "income": "upper_middle", "skills": ["engineering", "logistics", "planning"]},
    
    # Essential workers
    "teacher": {"title": "Teacher", "workplace_type": "school", "income": "middle", "skills": ["education", "patience", "communication"]},
    "doctor": {"title": "Doctor", "workplace_type": "clinic", "income": "upper_middle", "skills": ["medicine", "surgery", "diagnosis"]},
    "nurse": {"title": "Nurse", "workplace_type": "clinic", "income": "middle", "skills": ["medicine", "patient_care", "emergency"]},
    "police_officer": {"title": "Police Officer", "workplace_type": "police_station", "income": "middle", "skills": ["law_enforcement", "combat", "investigation"]},
    "firefighter": {"title": "Firefighter", "workplace_type": "fire_station", "income": "middle", "skills": ["rescue", "physical_fitness", "emergency"]},
    "paramedic": {"title": "Paramedic", "workplace_type": "hospital", "income": "middle", "skills": ["emergency_medicine", "driving", "triage"]},
    
    # Business
    "shop_owner": {"title": "Shop Owner", "workplace_type": "retail_shop", "income": "middle", "skills": ["commerce", "negotiation", "accounting"]},
    "restaurant_owner": {"title": "Restaurant Owner", "workplace_type": "restaurant", "income": "middle", "skills": ["cooking", "management", "hospitality"]},
    "bartender": {"title": "Bartender", "workplace_type": "bar", "income": "lower", "skills": ["mixing", "listening", "gossip"]},
    "mechanic": {"title": "Mechanic", "workplace_type": "garage", "income": "middle", "skills": ["repair", "electronics", "diagnostics"]},
    "barber": {"title": "Barber", "workplace_type": "barber_shop", "income": "middle", "skills": ["grooming", "conversation", "style"]},
    
    # Workers
    "factory_worker": {"title": "Factory Worker", "workplace_type": "factory", "income": "lower", "skills": ["labor", "machinery", "endurance"]},
    "dock_worker": {"title": "Dock Worker", "workplace_type": "docks", "income": "lower", "skills": ["labor", "logistics", "strength"]},
    "office_worker": {"title": "Office Worker", "workplace_type": "office", "income": "middle", "skills": ["data_entry", "communication", "organization"]},
    "programmer": {"title": "Software Engineer", "workplace_type": "tech_office", "income": "upper_middle", "skills": ["coding", "systems", "problem_solving"]},
    "data_scientist": {"title": "Data Scientist", "workplace_type": "tech_office", "income": "upper_middle", "skills": ["analysis", "coding", "statistics"]},
    "cybernetics_engineer": {"title": "Cybernetics Engineer", "workplace_type": "lab", "income": "upper", "skills": ["cybernetics", "electronics", "surgery"]},
    "welder": {"title": "Welder", "workplace_type": "workshop", "income": "middle", "skills": ["welding", "metalwork", "fabrication"]},
    "truck_driver": {"title": "Truck Driver", "workplace_type": "depot", "income": "lower", "skills": ["driving", "navigation", "logistics"]},
    "construction_worker": {"title": "Construction Worker", "workplace_type": "construction_site", "income": "lower", "skills": ["labor", "machinery", "carpentry"]},
    
    # Creatives
    "musician": {"title": "Musician", "workplace_type": "music_venue", "income": "lower", "skills": ["music", "performance", "composition"]},
    "artist": {"title": "Artist", "workplace_type": "studio", "income": "lower", "skills": ["painting", "sculpture", "creativity"]},
    "writer": {"title": "Writer", "workplace_type": "home", "income": "lower", "skills": ["writing", "research", "storytelling"]},
    "journalist": {"title": "Journalist", "workplace_type": "media_office", "income": "middle", "skills": ["writing", "investigation", "interviewing"]},
    
    # Service
    "cook": {"title": "Cook", "workplace_type": "restaurant", "income": "lower", "skills": ["cooking", "speed", "creativity"]},
    "taxi_driver": {"title": "Taxi Driver", "workplace_type": "taxi_stand", "income": "lower", "skills": ["driving", "navigation", "gossip"]},
    "janitor": {"title": "Janitor", "workplace_type": "various", "income": "lower", "skills": ["cleaning", "maintenance", "reliability"]},
    "security_guard": {"title": "Security Guard", "workplace_type": "various", "income": "lower", "skills": ["vigilance", "combat_basic", "protocol"]},
    
    # Spiritual/Religious
    "priest": {"title": "Temple Priest", "workplace_type": "temple", "income": "middle", "skills": ["theology", "counseling", "ritual"]},
    "healer": {"title": "Traditional Healer", "workplace_type": "healing_center", "income": "middle", "skills": ["herbalism", "healing", "empathy"]},
    
    # Students
    "university_student": {"title": "University Student", "workplace_type": "university", "income": "lower", "skills": ["study", "research", "socializing"]},
    "trade_student": {"title": "Trade School Student", "workplace_type": "trade_school", "income": "lower", "skills": ["apprenticeship", "hands_on", "learning"]},
    
    # Underground
    "smuggler": {"title": "Freelance Logistics", "workplace_type": "undisclosed", "income": "middle", "skills": ["stealth", "negotiation", "navigation"]},
    "hacker": {"title": "Independent Security Researcher", "workplace_type": "home", "income": "middle", "skills": ["hacking", "systems", "cryptography"]},
    "street_vendor": {"title": "Street Vendor", "workplace_type": "street_corner", "income": "lower", "skills": ["commerce", "persuasion", "survival"]},
    "scavenger": {"title": "Salvage Specialist", "workplace_type": "scrapyard", "income": "lower", "skills": ["scavenging", "repair", "survival"]},
}

# Political alignment options
POLITICAL_ALIGNMENTS = ["progressive", "moderate", "conservative", "libertarian", "populist", "technocrat", "traditionalist"]
VOTING_ISSUES = [
    "healthcare_funding", "cybernetics_rights", "temple_influence", "corporate_regulation",
    "public_safety", "education_reform", "housing_affordability", "workers_rights",
    "immigration_policy", "environmental_protection", "tech_regulation", "arts_funding",
    "infrastructure_spending", "tax_policy", "civil_liberties", "military_spending"
]

MBTI_TYPES = ["INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP",
              "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP"]

# Faction distribution by district
FACTION_WEIGHTS = {
    "neon_district": {"Neutral": 0.40, "Corps": 0.30, "Temple": 0.10, "Resistance": 0.05, "Underground": 0.10, "Mystics": 0.05},
    "harbor_quarter": {"Neutral": 0.30, "Resistance": 0.25, "Underground": 0.25, "Temple": 0.05, "Corps": 0.05, "Mystics": 0.10},
    "temple_heights": {"Temple": 0.35, "Neutral": 0.25, "Mystics": 0.20, "Resistance": 0.10, "Corps": 0.05, "Underground": 0.05},
    "old_town": {"Neutral": 0.35, "Resistance": 0.25, "Underground": 0.15, "Temple": 0.10, "Corps": 0.10, "Mystics": 0.05},
    "industrial_zone": {"Resistance": 0.35, "Underground": 0.25, "Neutral": 0.20, "Corps": 0.10, "Temple": 0.05, "Mystics": 0.05},
    "the_gardens": {"Neutral": 0.35, "Temple": 0.20, "Resistance": 0.15, "Underground": 0.10, "Corps": 0.10, "Mystics": 0.10},
    "tech_quarter": {"Neutral": 0.30, "Corps": 0.25, "Resistance": 0.15, "Mystics": 0.10, "Underground": 0.10, "Temple": 0.10},
    "outskirts": {"Underground": 0.30, "Resistance": 0.25, "Neutral": 0.25, "Mystics": 0.10, "Temple": 0.05, "Corps": 0.05},
}

# Explicit mapping from demographic ethnicity keys to name pool keys
ETHNICITY_TO_POOL = {
    # East Asian
    "east_asian_chinese": "east_asian_chinese",
    "east_asian_korean": "east_asian_korean",
    "japanese": "japanese",
    "mixed_asian": "east_asian_chinese",  # fallback
    # South Asian
    "south_asian_indian": "south_asian_indian",
    "south_asian_bangladeshi": "south_asian_indian",  # shared pool
    "south_asian_pakistani": "south_asian_pakistani",
    # Southeast Asian
    "southeast_asian_vietnamese": "southeast_asian_vietnamese",
    "southeast_asian_filipino": "southeast_asian_filipino",
    "southeast_asian_cambodian": "southeast_asian_cambodian",
    "southeast_asian_myanmar": "southeast_asian_myanmar",
    # West African
    "west_african_nigerian": "west_african_nigerian",
    "west_african_ghanaian": "west_african_ghanaian",
    # Caribbean
    "caribbean_jamaican": "caribbean_jamaican",
    "caribbean_trinidadian": "caribbean_trinidadian",
    "caribbean_haitian": "caribbean_haitian",
    # European
    "mixed_european": "mixed_european",
    "italian_american": "italian_american",
    "irish_american": "irish_american",
    "polish_american": "polish_american",
    "russian": "russian",
    "greek": "greek",
    # Latino
    "latino_mixed": "latino_mexican",  # fallback
    "latino_mexican": "latino_mexican",
    "latino_ecuadorian": "latino_ecuadorian",
    "latino_guatemalan": "latino_guatemalan",
    "latino_dominican": "latino_dominican",
    "latino_puerto_rican": "latino_puerto_rican",
    "latino_venezuelan": "latino_venezuelan",
    # African American
    "african_american": "african_american",
    # African
    "african_somali": "african_somali",
    "african_eritrean": "african_eritrean",
    # Arab / Middle Eastern / North African
    "arab_lebanese": "arab_lebanese",
    "arab_syrian": "arab_syrian",
    "arab_yemeni": "arab_yemeni",
    "north_african_moroccan": "north_african_moroccan",
    "middle_eastern": "arab_lebanese",  # fallback
    # Turkish
    "turkish": "turkish",
    # Afghan
    "afghan": "afghan",
    # Catch-all
    "mixed_other": "mixed_european",
    "mixed_refugee": "african_somali",
    "other": "mixed_european",
}

# Extended name pools for ethnicities not in the demographics JSON
EXTENDED_NAME_POOLS = {
    "south_asian_pakistani": {"first": ["Ali", "Fatima", "Hassan", "Ayesha", "Usman", "Sana", "Bilal", "Zainab"], "last": ["Khan", "Ahmed", "Malik", "Hussain", "Chaudhry", "Butt", "Sheikh", "Iqbal"]},
    "southeast_asian_vietnamese": {"first": ["Minh", "Linh", "Duc", "Thao", "Hung", "Mai", "Tuan", "Lan"], "last": ["Nguyen", "Tran", "Le", "Pham", "Vo", "Dang", "Bui", "Do"]},
    "southeast_asian_filipino": {"first": ["Miguel", "Maria", "Juan", "Rosa", "Angelo", "Grace", "Jose", "Lita"], "last": ["Santos", "Reyes", "Cruz", "Bautista", "Del Rosario", "Ramos", "Aquino", "Mendoza"]},
    "southeast_asian_cambodian": {"first": ["Sokha", "Chenda", "Dara", "Sophea", "Vanna", "Bopha", "Thy", "Keo"], "last": ["Sok", "Chan", "Chea", "Hem", "Khim", "Phan", "Seng", "Tan"]},
    "southeast_asian_myanmar": {"first": ["Aung", "Thida", "Ko", "Ma", "Win", "Zaw", "Thiha", "Soe"], "last": ["Aung", "Win", "Htun", "Oo", "Myint", "Tun", "Lwin", "Kyaw"]},
    "west_african_ghanaian": {"first": ["Kwame", "Abena", "Kofi", "Ama", "Yaw", "Efua", "Kwesi", "Akua"], "last": ["Mensah", "Owusu", "Boateng", "Asante", "Adjei", "Ofori", "Appiah", "Agyeman"]},
    "caribbean_trinidadian": {"first": ["Kiran", "Tricia", "Ravi", "Camille", "Stefan", "Anika", "Joel", "Priya"], "last": ["Ramkissoon", "Persad", "Mohammed", "Singh", "Ali", "Joseph", "Baptiste", "Charles"]},
    "caribbean_haitian": {"first": ["Jean", "Marie", "Pierre", "Rose", "Jacques", "Fabiola", "Frantz", "Guerline"], "last": ["Jean-Baptiste", "Joseph", "Pierre", "Louis", "Augustin", "Celestin", "Desir", "Etienne"]},
    "russian": {"first": ["Alexei", "Natasha", "Dmitri", "Olga", "Ivan", "Yelena", "Sergei", "Tatiana"], "last": ["Volkov", "Petrov", "Kuznetsov", "Ivanova", "Sokolov", "Popov", "Lebedev", "Morozov"]},
    "greek": {"first": ["Nikos", "Elena", "Dimitris", "Maria", "Yannis", "Sophia", "Kostas", "Athena"], "last": ["Papadopoulos", "Georgiou", "Nikolaou", "Vasileiou", "Pappas", "Konstantinou", "Alexiou", "Demetriou"]},
    "mixed_european": {"first": ["James", "Sarah", "Michael", "Emma", "David", "Olivia", "Daniel", "Laura"], "last": ["Miller", "Wilson", "Moore", "Taylor", "Anderson", "Thomas", "White", "Martin"]},
    "latino_ecuadorian": {"first": ["Luis", "Ana", "Jorge", "Carmen", "Pablo", "Lucia", "Fernando", "Gabriela"], "last": ["Morales", "Vega", "Flores", "Espinoza", "Cordero", "Jaramillo", "Salazar", "Reyes"]},
    "latino_guatemalan": {"first": ["Oscar", "Isabel", "Marco", "Luisa", "Roberto", "Silvia", "Pedro", "Teresa"], "last": ["Lopez", "Morales", "Garcia", "Hernandez", "Castillo", "Ramirez", "Perez", "Mendez"]},
    "latino_dominican": {"first": ["Juan", "Yolanda", "Ramon", "Altagracia", "Pedro", "Milagros", "Luis", "Juana"], "last": ["Rodriguez", "Martinez", "Perez", "Sanchez", "De La Cruz", "Medina", "Rosario", "Diaz"]},
    "latino_puerto_rican": {"first": ["Angel", "Carmen", "Jose", "Luz", "Carlos", "Maria", "Rafael", "Sonia"], "last": ["Rivera", "Torres", "Ortiz", "Santiago", "Colon", "Vargas", "Soto", "Diaz"]},
    "latino_venezuelan": {"first": ["Andres", "Valentina", "Sebastian", "Daniela", "Alejandro", "Isabella", "Gabriel", "Mariana"], "last": ["Gonzalez", "Rodriguez", "Martinez", "Garcia", "Hernandez", "Diaz", "Moreno", "Romero"]},
    "arab_syrian": {"first": ["Khalil", "Rania", "Tariq", "Hala", "Faisal", "Dima", "Bashar", "Lina"], "last": ["Al-Assad", "Ibrahim", "Habib", "Khalil", "Darwish", "Nader", "Salim", "Hanna"]},
    "arab_yemeni": {"first": ["Mohammed", "Aisha", "Abdullah", "Salma", "Ahmed", "Khadija", "Saleh", "Muna"], "last": ["Al-Houthi", "Al-Sanea", "Noman", "Qasim", "Saleh", "Hamid", "Antar", "Badr"]},
    "north_african_moroccan": {"first": ["Youssef", "Amina", "Rachid", "Fatima", "Mehdi", "Zineb", "Hamza", "Kenza"], "last": ["Benali", "El Amrani", "Tahiri", "Bouazza", "Idrissi", "Fassi", "Chaoui", "Benchekroun"]},
    "african_somali": {"first": ["Abdi", "Halima", "Mohamed", "Amina", "Hassan", "Asha", "Omar", "Sahra"], "last": ["Aden", "Ali", "Hassan", "Hussein", "Ibrahim", "Jama", "Mohamed", "Omar"]},
    "african_eritrean": {"first": ["Bereket", "Tsehay", "Dawit", "Rahel", "Yonas", "Feven", "Samuel", "Meron"], "last": ["Tesfai", "Gebremedhin", "Haile", "Berhe", "Amanuel", "Kebede", "Wolde", "Tekle"]},
    "afghan": {"first": ["Ahmad", "Mariam", "Farid", "Zahra", "Hamid", "Soraya", "Rashid", "Nasreen"], "last": ["Ahmadi", "Rahimi", "Karimi", "Mohammadi", "Hosseini", "Nazari", "Rezaei", "Hashemi"]},
}


def get_skin_tone(ethnicity_key: str) -> str:
    """Get appropriate skin tone based on ethnicity."""
    for group, tones in SKIN_TONES.items():
        if group in ethnicity_key:
            return random.choice(tones)
    return random.choice(SKIN_TONES["default"])


def weighted_choice(weights: dict) -> str:
    """Select from weighted dict."""
    items = list(weights.items())
    total = sum(w for _, w in items)
    r = random.uniform(0, total)
    cumulative = 0
    for item, weight in items:
        cumulative += weight
        if r <= cumulative:
            return item
    return items[-1][0]


def generate_height(gender: str) -> int:
    """Generate realistic height in cm."""
    if gender == "male":
        return random.randint(162, 195)
    elif gender == "female":
        return random.randint(150, 180)
    else:
        return random.randint(155, 188)


def generate_weight(height_cm: int, build: str) -> int:
    """Generate realistic weight based on height and build."""
    bmi_ranges = {
        "slim": (17, 20), "lean": (18, 21), "petite": (17, 20),
        "average": (20, 25), "tall_lean": (18, 22),
        "athletic": (22, 26), "compact": (22, 27),
        "stocky": (25, 30), "muscular": (24, 29), "heavyset": (28, 35)
    }
    bmi_low, bmi_high = bmi_ranges.get(build, (20, 25))
    bmi = random.uniform(bmi_low, bmi_high)
    height_m = height_cm / 100
    return round(bmi * height_m * height_m)


def generate_big_five() -> dict:
    """Generate Big Five personality vector."""
    return {
        "O": round(random.uniform(0.1, 1.0), 2),
        "C": round(random.uniform(0.1, 1.0), 2),
        "E": round(random.uniform(0.1, 1.0), 2),
        "A": round(random.uniform(0.1, 1.0), 2),
        "N": round(random.uniform(0.1, 1.0), 2)
    }


def pick_name(ethnicity: str, gender: str, name_pools: dict, used_names: set) -> tuple:
    """Pick a unique name from the appropriate pool using explicit ethnicity mapping."""
    # Merge base pools with extended pools
    all_pools = {}
    for k, v in name_pools.items():
        if isinstance(v, dict) and "first" in v:
            all_pools[k] = v
    all_pools.update(EXTENDED_NAME_POOLS)
    
    # Use explicit mapping to find the right pool
    pool_key = ETHNICITY_TO_POOL.get(ethnicity)
    
    if not pool_key or pool_key not in all_pools:
        # Try fuzzy match as last resort
        for key in all_pools:
            if key in ethnicity or ethnicity in key:
                pool_key = key
                break
    
    if not pool_key or pool_key not in all_pools:
        pool_key = "mixed_european"  # final fallback
    
    pool = all_pools.get(pool_key, EXTENDED_NAME_POOLS["mixed_european"])
    first_names = pool.get("first", ["Alex", "Sam", "Jordan", "Casey"])
    last_names = pool.get("last", ["Smith", "Jones", "Lee", "Kim"])
    
    # Try to find unused combo
    for _ in range(50):
        first = random.choice(first_names)
        last = random.choice(last_names)
        full = f"{first} {last}"
        if full not in used_names:
            used_names.add(full)
            return first, last
    
    # If all combos used, add number suffix
    first = random.choice(first_names)
    last = random.choice(last_names)
    suffix = random.randint(1, 99)
    full = f"{first} {last} {suffix}"
    used_names.add(full)
    return first, f"{last}-{suffix}"


def generate_schedule(job_key: str, age: int) -> dict:
    """Generate a daily schedule based on job and age."""
    job = JOB_DEFINITIONS.get(job_key, {})
    
    if age < 18:
        return {
            "06:30": "wake, breakfast",
            "07:30": "commute to school",
            "08:00-15:00": "school",
            "15:30": "afterschool activities",
            "17:00": "homework or hanging out",
            "19:00": "dinner with family",
            "21:00": "free time",
            "22:30": "sleep"
        }
    
    if age > 65:
        return {
            "07:00": "wake, morning routine",
            "08:00": "breakfast, news",
            "09:00": "morning walk or errand",
            "11:00": "community center or visiting friends",
            "12:30": "lunch",
            "14:00": "reading or hobby",
            "16:00": "afternoon tea, socializing",
            "18:00": "dinner",
            "20:00": "evening entertainment",
            "22:00": "sleep"
        }
    
    # Working adult schedule varies by job type
    workplace = job.get("workplace_type", "office")
    
    if workplace in ["factory", "docks", "construction_site", "depot"]:
        # Early shift
        return {
            "05:00": "wake, coffee",
            "05:30": "commute",
            "06:00-14:00": f"work at {workplace}",
            "14:30": "lunch at home or local spot",
            "15:30": "errands or family time",
            "18:00": "dinner",
            "19:30": "socializing or rest",
            "22:00": "sleep"
        }
    elif workplace in ["bar", "music_venue", "restaurant"]:
        # Late shift
        return {
            "10:00": "wake, slow morning",
            "11:00": "breakfast, personal time",
            "13:00": "errands or practice",
            "15:00": "prep for work",
            "16:00-01:00": f"work at {workplace}",
            "01:30": "wind down",
            "02:30": "sleep"
        }
    else:
        # Standard office hours
        return {
            "06:30": "wake, morning routine",
            "07:00": "breakfast",
            "07:30": "commute",
            "08:00-17:00": f"work at {workplace}",
            "17:30": "commute home",
            "18:00": "exercise or errands",
            "19:00": "dinner",
            "20:00": "personal time",
            "23:00": "sleep"
        }


def generate_npc(npc_id: int, district_key: str, demographics: dict, name_pools: dict, used_names: set) -> dict:
    """Generate a single NPC with full profile."""
    district = demographics["districts"][district_key]
    
    # Gender (roughly balanced)
    gender = random.choice(["male", "female", "male", "female", "nonbinary"])
    
    # Age distribution (weighted toward working age)
    age_weights = [(10, 17, 0.08), (18, 25, 0.15), (26, 35, 0.25), (36, 50, 0.25), 
                   (51, 65, 0.15), (66, 85, 0.12)]
    age_range = weighted_choice({f"{lo}-{hi}": w for lo, hi, w in age_weights})
    lo, hi = map(int, age_range.split("-"))
    age = random.randint(lo, hi)
    
    # Ethnicity
    ethnicity = weighted_choice(district["ethnicity_weights"])
    
    # Name
    first_name, last_name = pick_name(ethnicity, gender, name_pools, used_names)
    
    # Physical attributes
    build = random.choice(BUILDS)
    height = generate_height(gender)
    weight = generate_weight(height, build)
    
    # Job (based on age and district)
    district_jobs = district.get("job_types", ["office_worker"])
    if age < 18:
        job_key = "university_student" if age >= 16 else "university_student"  # Will use student schedule
    elif age > 65:
        job_key = random.choice(["retired", district_jobs[0]] if district_jobs else ["retired"])
        if job_key == "retired":
            job_key = None
    else:
        job_key = random.choice(district_jobs) if district_jobs else "office_worker"
    
    job_def = JOB_DEFINITIONS.get(job_key, {"title": "Citizen", "workplace_type": "various", "income": "middle", "skills": []})
    
    # Faction
    faction_weights = FACTION_WEIGHTS.get(district_key, {"Neutral": 1.0})
    faction = weighted_choice(faction_weights)
    
    # Build the NPC
    npc = {
        "id": f"npc_{npc_id:05d}",
        "name": f"{first_name} {last_name}",
        "first_name": first_name,
        "last_name": last_name,
        "age": age,
        "gender": gender,
        "ethnicity": ethnicity,
        
        "physical": {
            "height_cm": height,
            "weight_kg": weight,
            "build": build,
            "skin_tone": get_skin_tone(ethnicity),
            "hair": {
                "style": random.choice(HAIR_STYLES),
                "color": random.choice(HAIR_COLORS),
                "length": random.choice(["short", "medium", "long"])
            },
            "eyes": {
                "color": random.choice(EYE_COLORS),
                "shape": random.choice(EYE_SHAPES)
            },
            "face": {
                "shape": random.choice(FACE_SHAPES),
                "lips": random.choice(LIP_TYPES),
                "nose": random.choice(NOSE_TYPES),
                "jawline": random.choice(JAWLINES)
            }
        },
        
        "personality": {
            "mbti": random.choice(MBTI_TYPES),
            "big_five": generate_big_five(),
            "values": random.sample(["justice", "family", "innovation", "tradition", "freedom",
                                      "community", "wealth", "knowledge", "survival", "faith",
                                      "art", "power", "loyalty", "adventure", "stability"], 3),
            "fears": random.sample(["loneliness", "poverty", "violence", "losing_control",
                                     "being_useless", "betrayal", "the_unknown", "death",
                                     "losing_family", "obsolescence", "injustice"], 2)
        },
        
        "role": {
            "job_title": job_def.get("title", "Citizen"),
            "job_key": job_key or "retired",
            "workplace_type": job_def.get("workplace_type", "various"),
            "income_bracket": job_def.get("income", "middle"),
            "skills": job_def.get("skills", [])
        },
        
        "life": {
            "district": district_key,
            "district_name": district["name"],
            "daily_schedule": generate_schedule(job_key or "retired", age)
        },
        
        "faction": faction,
        "political_alignment": random.choice(POLITICAL_ALIGNMENTS),
        "voting_issues": random.sample(VOTING_ISSUES, random.randint(2, 4)),
        
        "social": {
            "relationship_count": 0,
            "relationships": {},
            "trust_baseline": round(random.uniform(0.2, 0.7), 2)
        },
        
        "personality_vector": {
            "paranoia": round(random.uniform(0.1, 0.9), 2),
            "mysticism": round(random.uniform(0.1, 0.9), 2),
            "aggression": round(random.uniform(0.1, 0.9), 2),
            "sociability": round(random.uniform(0.1, 0.9), 2),
            "layer_awareness": round(random.uniform(0.0, 0.3), 2)
        }
    }
    
    return npc


def generate_governance_npcs(demographics: dict, name_pools: dict, used_names: set, start_id: int) -> list:
    """Generate all governance NPCs with specific roles."""
    gov = demographics.get("governance", {})
    npcs = []
    current_id = start_id
    
    # Mayor (from Neon District - city hall is downtown)
    mayor = generate_npc(current_id, "neon_district", demographics, name_pools, used_names)
    mayor["role"] = {
        "job_title": "Mayor of Example City",
        "job_key": "mayor",
        "workplace_type": "city_hall",
        "income_bracket": "upper",
        "skills": ["leadership", "negotiation", "politics", "public_speaking"]
    }
    mayor["governance"] = {
        "position": "mayor",
        "elected": True,
        "term_start_tick": 0,
        "popularity": round(random.uniform(0.4, 0.7), 2),
        "campaign_promises": random.sample(VOTING_ISSUES, 3)
    }
    mayor["age"] = random.randint(42, 65)  # Mayors tend to be older
    # Regenerate schedule for correct age + role
    mayor["life"]["daily_schedule"] = {
        "06:00": "wake, morning briefing",
        "07:00": "breakfast, review agenda",
        "08:00": "arrive at City Hall",
        "08:30-12:00": "meetings, constituent calls, policy work",
        "12:00": "lunch (often working)",
        "13:00-17:00": "council sessions, public appearances, negotiations",
        "17:30": "commute home",
        "18:30": "dinner",
        "20:00": "evening reading, strategy calls",
        "23:00": "sleep"
    }
    npcs.append(mayor)
    current_id += 1
    
    # City Council (7 members, one per main district)
    council_districts = ["neon_district", "harbor_quarter", "temple_heights", "old_town", 
                         "industrial_zone", "the_gardens", "tech_quarter"]
    for i, dist in enumerate(council_districts):
        council = generate_npc(current_id, dist, demographics, name_pools, used_names)
        council["role"] = {
            "job_title": f"Council Member, {demographics['districts'][dist]['name']}",
            "job_key": "council_member",
            "workplace_type": "city_hall",
            "income_bracket": "upper_middle",
            "skills": ["politics", "negotiation", "public_speaking"]
        }
        council["governance"] = {
            "position": "council_member",
            "district_represented": dist,
            "elected": True,
            "committee": random.choice(["Finance", "Public Safety", "Infrastructure", "Education", "Health"]),
            "term_start_tick": 0
        }
        council["age"] = random.randint(35, 65)
        council["life"]["daily_schedule"] = {
            "07:00": "wake, morning routine",
            "08:00": "breakfast, review district reports",
            "09:00": "travel to City Hall",
            "09:30-12:00": "committee meetings, constituent work",
            "12:00": "lunch with colleagues or constituents",
            "13:00-16:00": "council session or district office hours",
            "16:30": "return to district",
            "17:00": "community events or meetings",
            "19:00": "dinner",
            "21:00": "personal time",
            "23:00": "sleep"
        }
        npcs.append(council)
        current_id += 1
    
    # Chief of Police
    police_chief = generate_npc(current_id, "neon_district", demographics, name_pools, used_names)
    police_chief["role"] = {
        "job_title": "Chief of Police",
        "job_key": "chief_of_police",
        "workplace_type": "police_hq",
        "income_bracket": "upper_middle",
        "skills": ["leadership", "tactics", "law", "investigation"]
    }
    police_chief["governance"] = {"position": "chief_of_police", "appointed_by": "mayor", "elected": False}
    police_chief["age"] = random.randint(45, 60)
    police_chief["life"]["daily_schedule"] = {
        "05:30": "wake, morning fitness",
        "06:30": "review overnight reports",
        "07:30": "arrive at HQ, morning briefing",
        "08:00-12:00": "operations management, meetings",
        "12:00": "lunch",
        "13:00-17:00": "investigations oversight, interagency meetings",
        "17:30": "evening briefing",
        "18:30": "commute home",
        "19:30": "dinner",
        "21:00": "on-call review",
        "23:00": "sleep"
    }
    npcs.append(police_chief)
    current_id += 1
    
    # Judges
    for i in range(4):
        dist = random.choice(["neon_district", "old_town", "the_gardens", "tech_quarter"])
        judge = generate_npc(current_id, dist, demographics, name_pools, used_names)
        judge["role"] = {
            "job_title": "Chief Judge" if i == 0 else "District Judge",
            "job_key": "chief_judge" if i == 0 else "district_judge",
            "workplace_type": "courthouse",
            "income_bracket": "upper" if i == 0 else "upper_middle",
            "skills": ["law", "investigation", "ethics", "leadership"]
        }
        judge["governance"] = {
            "position": "chief_judge" if i == 0 else "district_judge",
            "appointed_by": "mayor",
            "confirmed_by": "city_council",
            "elected": False
        }
        judge["age"] = random.randint(45, 70)
        judge["life"]["daily_schedule"] = {
            "06:30": "wake, morning routine",
            "07:30": "review case files",
            "08:30": "arrive at courthouse",
            "09:00-12:00": "court proceedings",
            "12:00": "lunch in chambers",
            "13:00-16:00": "rulings, case review, legal research",
            "16:30": "end of court day",
            "17:00": "commute home",
            "18:00": "dinner",
            "20:00": "reading, personal time",
            "22:00": "sleep"
        }
        npcs.append(judge)
        current_id += 1
    
    # Department heads
    dept_heads = [
        ("Fire Chief", "fire_chief", "fire_station"),
        ("Health Commissioner", "health_commissioner", "city_hall"),
        ("Schools Chancellor", "schools_chancellor", "school_admin"),
        ("City Engineer", "city_engineer", "city_hall"),
        ("Sanitation Director", "sanitation_director", "city_hall"),
    ]
    for title, key, workplace in dept_heads:
        dist = random.choice(list(demographics["districts"].keys()))
        head = generate_npc(current_id, dist, demographics, name_pools, used_names)
        head["role"] = {
            "job_title": title,
            "job_key": key,
            "workplace_type": workplace,
            "income_bracket": "upper_middle",
            "skills": ["leadership", "management", "policy"]
        }
        head["governance"] = {"position": key, "appointed_by": "mayor", "elected": False}
        head["age"] = random.randint(40, 60)
        head["life"]["daily_schedule"] = generate_schedule(key, head["age"])
        npcs.append(head)
        current_id += 1
    
    return npcs


def generate_district_batch(district_key: str, count: int, demographics: dict, 
                             name_pools: dict, used_names: set, start_id: int) -> list:
    """Generate a batch of NPCs for a specific district."""
    npcs = []
    for i in range(count):
        npc = generate_npc(start_id + i, district_key, demographics, name_pools, used_names)
        npcs.append(npc)
    return npcs


def main():
    parser = argparse.ArgumentParser(description="Generate NPCs for AO World Engine")
    parser.add_argument("--all", action="store_true", help="Generate all 2,830 NPCs")
    parser.add_argument("--governance", action="store_true", help="Generate governance NPCs only")
    parser.add_argument("--district", type=str, help="Generate for specific district")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size for district generation")
    parser.add_argument("--start-id", type=int, default=800, help="Starting NPC ID")
    parser.add_argument("--output", type=str, default=str(OUTPUT_DIR), help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    
    args = parser.parse_args()
    random.seed(args.seed)
    
    # Load demographics
    with open(DEMOGRAPHICS_FILE) as f:
        demographics = json.load(f)
    
    name_pools = demographics.get("name_pools", {})
    used_names = set()
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    all_npcs = []
    current_id = args.start_id
    
    if args.governance or args.all:
        print("🏛️  Generating governance NPCs...")
        gov_npcs = generate_governance_npcs(demographics, name_pools, used_names, current_id)
        all_npcs.extend(gov_npcs)
        current_id += len(gov_npcs)
        print(f"   Generated {len(gov_npcs)} governance NPCs (IDs {args.start_id}-{current_id - 1})")
        
        # Save governance separately
        gov_file = output_dir / "governance_npcs.json"
        with open(gov_file, "w") as f:
            json.dump({"governance_npcs": gov_npcs, "count": len(gov_npcs)}, f, indent=2)
        print(f"   Saved to {gov_file}")
    
    if args.all:
        print("\n🌆 Generating full city population...")
        for district_key, district_data in demographics["districts"].items():
            target = district_data["population_target"]
            # Subtract any governance NPCs already generated for this district
            gov_in_district = sum(1 for n in all_npcs if n.get("life", {}).get("district") == district_key)
            remaining = target - gov_in_district
            
            if remaining <= 0:
                continue
            
            print(f"\n  📍 {district_data['name']} ({remaining} NPCs)...")
            district_npcs = generate_district_batch(
                district_key, remaining, demographics, name_pools, used_names, current_id
            )
            all_npcs.extend(district_npcs)
            current_id += len(district_npcs)
            
            # Save per-district file
            dist_file = output_dir / f"district_{district_key}.json"
            with open(dist_file, "w") as f:
                json.dump({
                    "district": district_key,
                    "district_name": district_data["name"],
                    "npcs": district_npcs,
                    "count": len(district_npcs)
                }, f, indent=2)
            print(f"     Saved {len(district_npcs)} NPCs to {dist_file}")
    
    elif args.district:
        if args.district not in demographics["districts"]:
            print(f"Error: Unknown district '{args.district}'")
            print(f"Available: {', '.join(demographics['districts'].keys())}")
            sys.exit(1)
        
        district_data = demographics["districts"][args.district]
        count = min(args.batch_size, district_data["population_target"])
        print(f"📍 Generating {count} NPCs for {district_data['name']}...")
        
        district_npcs = generate_district_batch(
            args.district, count, demographics, name_pools, used_names, current_id
        )
        all_npcs.extend(district_npcs)
        
        dist_file = output_dir / f"district_{args.district}.json"
        with open(dist_file, "w") as f:
            json.dump({
                "district": args.district,
                "district_name": district_data["name"],
                "npcs": district_npcs,
                "count": len(district_npcs)
            }, f, indent=2)
        print(f"Saved {len(district_npcs)} NPCs to {dist_file}")
    
    # Save combined file
    if all_npcs:
        combined_file = output_dir / "all_generated_npcs.json"
        with open(combined_file, "w") as f:
            json.dump({
                "meta": {
                    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "total_count": len(all_npcs),
                    "seed": args.seed,
                    "id_range": f"npc_{args.start_id:05d} - npc_{current_id - 1:05d}"
                },
                "npcs": all_npcs
            }, f, indent=2)
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"🏙️  CITY GENERATION COMPLETE")
        print(f"{'='*60}")
        print(f"  Total NPCs:     {len(all_npcs)}")
        print(f"  ID Range:       npc_{args.start_id:05d} — npc_{current_id - 1:05d}")
        print(f"  Combined file:  {combined_file}")
        
        # District breakdown
        district_counts = {}
        for npc in all_npcs:
            d = npc.get("life", {}).get("district", "unknown")
            district_counts[d] = district_counts.get(d, 0) + 1
        
        print(f"\n  District Breakdown:")
        for dist, count in sorted(district_counts.items()):
            name = demographics["districts"].get(dist, {}).get("name", dist)
            print(f"    {name:25s} {count:5d}")
        
        # Ethnicity summary
        eth_counts = {}
        for npc in all_npcs:
            e = npc.get("ethnicity", "unknown")
            eth_counts[e] = eth_counts.get(e, 0) + 1
        
        print(f"\n  Top 10 Ethnicities:")
        for eth, count in sorted(eth_counts.items(), key=lambda x: -x[1])[:10]:
            pct = count / len(all_npcs) * 100
            print(f"    {eth:30s} {count:5d} ({pct:.1f}%)")
        
        # Faction summary
        fac_counts = {}
        for npc in all_npcs:
            f = npc.get("faction", "unknown")
            fac_counts[f] = fac_counts.get(f, 0) + 1
        
        print(f"\n  Faction Breakdown:")
        for fac, count in sorted(fac_counts.items(), key=lambda x: -x[1]):
            pct = count / len(all_npcs) * 100
            print(f"    {fac:20s} {count:5d} ({pct:.1f}%)")
        
        # File size
        size_mb = os.path.getsize(combined_file) / (1024 * 1024)
        print(f"\n  File size:  {size_mb:.2f} MB")
        print(f"  Avg/NPC:    {os.path.getsize(combined_file) / len(all_npcs) / 1024:.1f} KB")


if __name__ == "__main__":
    main()

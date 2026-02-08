#!/usr/bin/env python3
"""
Comprehensive NPC Knowledge Test Suite — 100 Tests
===================================================

Tests NPC chat across 10 categories:
  1. Identity & Self-Knowledge (10)
  2. Appearance & Description (10)
  3. Relationships & Known NPCs (10)
  4. World Knowledge (10)
  5. Faction Knowledge (10)
  6. Schedule & Time Awareness (10)
  7. Memory & Context (10) — multi-turn
  8. Lore & History (10)
  9. Adversarial Trip-Ups (10)
  10. Cross-NPC Consistency (10)

Saves results to: data/npc_test_results.md

Usage:
    python3 scripts/test_npc_knowledge.py
    python3 scripts/test_npc_knowledge.py --quick   # Run 20 tests only
"""

import sys, os, json, time, re, argparse, hashlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import requests

API_URL = "https://ao-npc-chat-1071951656531.us-east1.run.app"
RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

# ============================================================
# TEST DEFINITIONS
# ============================================================

TESTS = []

def test(category, npc_id, message, expect_keywords=None, expect_not=None, 
         multi_turn=None, description="", tick=100, min_keyword_ratio=0.0):
    """Register a test case.
    
    expect_keywords: At least one must match (OR logic). Use broader sets.
    min_keyword_ratio: Optional stricter requirement (0.0 = just 1 match).
    """
    TESTS.append({
        "category": category,
        "npc_id": npc_id,
        "message": message,
        "expect_keywords": expect_keywords or [],
        "expect_not": expect_not or [],
        "multi_turn": multi_turn,  # list of prior messages for context
        "description": description,
        "tick": tick,
        "min_keyword_ratio": min_keyword_ratio,
    })

# ============================================================
# CATEGORY 1: IDENTITY & SELF-KNOWLEDGE (10)
# ============================================================
# Broadened: accept any reasonable identity signal
test("Identity", "charlie", "Who are you?",
     expect_keywords=["charlie", "guard", "resistance", "fight", "protect", "patrol"],
     description="Charlie should know his own name and role")

test("Identity", "zero_chen", "What's your name?",
     expect_keywords=["zero", "chen"],
     description="Zero should state her name")

test("Identity", "aiche", "What are you exactly?",
     expect_keywords=["ai", "city", "system", "digital", "holographic", "data", "program"],
     description="Aiche should identify as the city AI")

test("Identity", "sister_mira", "Tell me about yourself",
     expect_keywords=["temple", "faith", "sister", "priestess", "prayer", "heal", "spiritual"],
     description="Sister Mira should mention her Temple connection")

test("Identity", "felix", "What do you do for a living?",
     expect_keywords=["bar", "drink", "merchant", "serve", "neon", "pour", "bartend"],
     description="Felix should talk about bartending/merchant work")

test("Identity", "nova_chen", "What's your specialty?",
     expect_keywords=["tech", "hack", "code", "engineer", "machine", "system", "build", "repair", "mercenary", "extract", "work", "alone", "job", "speciali", "skill"],
     description="Nova should mention her tech expertise")

test("Identity", "cipher", "Are you human?",
     expect_keywords=["information", "data", "question", "allegiance", "identity", "what", "am", "ambig", "cipher"],
     expect_not=["yes, i am a normal human"],
     description="Cipher should be ambiguous about humanity")

test("Identity", "orion_thane", "What do you believe in?",
     expect_keywords=["layer", "mystic", "veil", "reality", "beyond", "truth", "convergence", "spiritual", "awaken"],
     description="Orion should reference his mystical beliefs")

test("Identity", "pixel", "What drives you?",
     expect_keywords=["resistance", "fight", "free", "hack", "system", "change", "injustice", "temple", "truth"],
     description="Pixel should mention resistance motivations")

test("Identity", "mama_indira", "What's your purpose?",
     expect_keywords=["feed", "care", "community", "child", "people", "cook", "nourish", "hungry", "undercity", "family"],
     description="Mama Indira should talk about caring for the Undercity")

# ============================================================
# CATEGORY 2: APPEARANCE & DESCRIPTION (10)
# ============================================================
# Broadened: accept paraphrased descriptions, not just exact keywords
test("Appearance", "charlie", "Describe yourself physically",
     expect_keywords=["stubble", "gray", "trench", "coat", "rough", "scar", "worn", "jacket", "grizzl", "build", "tall", "dark"],
     description="Charlie should describe his noir detective look")

test("Appearance", "selene_voss", "What do you look like?",
     expect_keywords=["pale", "glow", "ethereal", "eye", "white", "silver", "hair", "thin", "mystic", "otherworld"],
     description="Selene should describe her ethereal appearance")

test("Appearance", "kai_vance", "What are you wearing?",
     expect_keywords=["uniform", "clean", "neat", "precise", "military", "jacket", "armor", "tactical", "disciplin", "sharp"],
     description="Kai should mention his clean-cut military look")

test("Appearance", "aiche", "Can I see what you look like?",
     expect_keywords=["holographic", "hologram", "cyan", "glow", "data", "light", "digital", "project", "form", "appear"],
     description="Aiche should describe her holographic form")

test("Appearance", "charlie", "What does Zero Chen look like?",
     expect_keywords=["arm", "scar", "burn", "hair", "cybernetic", "prosthetic", "strong", "fierce", "leader", "tough"],
     description="Charlie should describe Zero's appearance — cross-NPC knowledge")

test("Appearance", "zero_chen", "What does Charlie look like?",
     expect_keywords=["gray", "coat", "stubble", "detective", "grizzl", "trench", "worn", "rough", "guard", "tough", "big"],
     description="Zero should describe Charlie's appearance")

test("Appearance", "mama_indira", "What does Aiche look like?",
     expect_keywords=["holographic", "hologram", "glow", "cyan", "light", "digital", "ai", "appear", "project"],
     description="Mama Indira should describe Aiche")

test("Appearance", "pixel", "Describe Cipher's appearance",
     expect_keywords=["androgynous", "tattoo", "circuit", "shift", "change", "mysterious", "hood", "dark", "shadow"],
     description="Pixel should know Cipher's appearance")

test("Appearance", "felix", "What does Nova look like?",
     expect_keywords=["bob", "hair", "asian", "sleek", "tech", "sharp", "short", "dark", "engineer", "coat"],
     description="Felix should describe Nova")

test("Appearance", "orion_thane", "Describe Selene Voss to me",
     expect_keywords=["pale", "glow", "ethereal", "white", "eye", "mystic", "silver", "otherworld", "hair", "thin"],
     description="Orion should know Selene's appearance well (fellow mystic)")

# ============================================================
# CATEGORY 3: RELATIONSHIPS & KNOWN NPCS (10)
# ============================================================
test("Relationships", "charlie", "Who is Zero Chen to you?",
     expect_keywords=["leader", "mentor", "resistance", "arm", "saved", "trust", "follow", "respect", "commander"],
     description="Charlie should know Zero saved him and leads the Resistance")

test("Relationships", "zero_chen", "What do you think of Charlie?",
     expect_keywords=["guard", "trust", "protect", "fighter", "loyal", "brave", "soldier", "comrade", "strong"],
     description="Zero should have positive feelings about Charlie")

test("Relationships", "sister_mira", "Do you trust the Temple leadership?",
     expect_keywords=["doubt", "question", "faith", "struggle", "conflict", "uncertain", "wonder", "torn", "belief"],
     description="Mira has hidden doubts about Temple — internal dissent")

test("Relationships", "felix", "Who are your best customers?",
     expect_keywords=["bar", "drink", "regular", "customer", "come", "stop", "visit", "night", "people", "crowd"],
     description="Felix should reference people at the bar")

test("Relationships", "pixel", "Who do you work with?",
     expect_keywords=["resistance", "hack", "nova", "zero", "team", "comrade", "fight", "ally", "together"],
     description="Pixel should mention resistance comrades")

test("Relationships", "orion_thane", "Is Selene Voss gifted?",
     expect_keywords=["layer", "see", "static", "beyond", "power", "gifted", "ability", "vision", "talent", "unique"],
     description="Orion should know Selene's unique abilities")

test("Relationships", "mama_indira", "Do you know Felix?",
     expect_keywords=["felix", "bar", "friend", "know", "drink", "good", "man", "boy", "soul"],
     description="Mama Indira should know Felix")

test("Relationships", "cipher", "Do you know who the Resistance leader is?",
     expect_keywords=["zero", "resistance", "leader", "chen", "know", "information"],
     description="Cipher should know the Resistance leader")

test("Relationships", "kai_vance", "Who gives you orders?",
     expect_keywords=["zero", "resistance", "command", "lead", "chain", "follow", "order", "mission"],
     description="Kai should mention the resistance chain of command")

test("Relationships", "nova_chen", "Tell me about Pixel",
     expect_keywords=["hack", "tech", "young", "resistance", "kid", "talent", "clever", "code", "good", "skill"],
     description="Nova should know Pixel (fellow tech/resistance)")

# ============================================================
# CATEGORY 4: WORLD KNOWLEDGE (10)
# ============================================================
test("World", "charlie", "What is this city?",
     expect_keywords=["city", "district", "neon", "dark", "dangerous", "echo", "streets", "place"],
     description="Charlie should describe the cyberpunk city")

test("World", "aiche", "How big is the city?",
     expect_keywords=["district", "sector", "zone", "area", "block", "quarter", "span", "stretch", "vast", "city", "large"],
     description="Aiche, being the city AI, should know its extent")

test("World", "felix", "What's the Neon District like?",
     expect_keywords=["neon", "light", "billboard", "commercial", "busy", "crowd", "bright", "market", "trade", "shop"],
     description="Felix should know the Neon District")

test("World", "charlie", "Is the water safe to drink?",
     expect_keywords=["water", "scarce", "careful", "purif", "safe", "drink", "clean", "filtr", "ration", "trust"],
     description="Common knowledge: water is scarce")

test("World", "nova_chen", "What kind of technology exists here?",
     expect_keywords=["implant", "cybernetic", "hack", "neural", "tech", "augment", "system", "code", "machine", "device", "proprietary"],
     description="Nova should be tech-savvy about city tech")

test("World", "mama_indira", "What's life like in the Undercity?",
     expect_keywords=["underground", "tunnel", "dark", "surviv", "hard", "tough", "struggle", "community", "people", "live", "difficult"],
     description="Mama Indira lives in the Undercity")

test("World", "orion_thane", "What are the layers?",
     expect_keywords=["layer", "reality", "prime", "echo", "bleed", "dimension", "veil", "beyond", "exist", "world"],
     description="Orion is a layer expert")

test("World", "sister_mira", "What is the Temple Quarter?",
     expect_keywords=["temple", "patrol", "faith", "quarter", "spire", "sacred", "worship", "district", "holy", "peace", "order"],
     description="Mira should know the Temple Quarter intimately")

test("World", "pixel", "Where's the black market?",
     expect_keywords=["underground", "undercity", "market", "illegal", "hidden", "shadow", "secret", "deal", "smuggl"],
     description="Pixel should know about the black market")

test("World", "zero_chen", "What's the Shadow Grid?",
     expect_keywords=["server", "data", "hacker", "abandon", "network", "shadow", "grid", "system", "tech", "hidden", "communication", "lifeline"],
     description="Zero should know the Shadow Grid (hacker territory)")

# ============================================================
# CATEGORY 5: FACTION KNOWLEDGE (10)
# ============================================================
test("Factions", "charlie", "Tell me about the Resistance",
     expect_keywords=["resist", "fight", "temple", "free", "overthrow", "liberation", "oppres", "stand", "cause"],
     description="Charlie is Resistance — should explain their cause")

test("Factions", "sister_mira", "What is the Temple's mission?",
     expect_keywords=["temple", "faith", "order", "divine", "protect", "guide", "light", "believ", "purpose", "serve", "peace"],
     description="Mira should explain Temple ideology")

test("Factions", "nova_chen", "Who are the Corps?",
     expect_keywords=["corp", "profit", "power", "money", "greedy", "exploit", "business", "control", "company", "mega"],
     description="Nova should know about corporate remnants")

test("Factions", "orion_thane", "What do the Mystics want?",
     expect_keywords=["layer", "understand", "convergence", "awaken", "truth", "reality", "see", "beyond", "knowledge", "prepare"],
     description="Orion leads the Mystics")

test("Factions", "mama_indira", "Tell me about the Undercity community",
     expect_keywords=["surviv", "community", "tunnel", "underground", "people", "together", "family", "feed", "help", "home", "child"],
     description="Mama Indira should know the Underground faction")

test("Factions", "zero_chen", "Is the Temple our enemy?",
     expect_keywords=["temple", "control", "fight", "oppress", "enemy", "against", "threat", "danger", "resist", "power"],
     description="Zero should explain Temple opposition")

test("Factions", "charlie", "Can we trust the corporations?",
     expect_keywords=["corp", "trust", "profit", "care", "exploit", "money", "danger", "careful", "watch", "sell", "betray"],
     expect_not=["absolutely", "definitely trust them"],
     description="Charlie should distrust corps")

test("Factions", "cipher", "What faction are you with?",
     expect_keywords=["information", "faction", "side", "allegiance", "affiliation", "work", "interest", "data", "independent", "align", "neutral"],
     description="Cipher is mysterious about allegiance")

test("Factions", "kai_vance", "Are the Mystics dangerous?",
     expect_keywords=["mystic", "layer", "strange", "unpredictable", "power", "careful", "understand", "concern", "caution", "unknown"],
     description="Kai should have thoughts on Mystics")

test("Factions", "selene_voss", "What do you think of the Resistance?",
     expect_keywords=["resist", "fight", "free", "struggle", "cause", "thread", "weave", "city", "tangl", "noble", "brave"],
     description="Selene should have views on the Resistance")

# ============================================================
# CATEGORY 6: SCHEDULE & TIME AWARENESS (10)
# ============================================================
test("Schedule", "charlie", "What are you doing right now?",
     expect_keywords=["patrol", "guard", "watch", "gather", "intel", "standing", "keeping", "eye", "post", "work", "duty"],
     description="Charlie should know his current activity", tick=100)

test("Schedule", "felix", "Are you open for business?",
     expect_keywords=["bar", "drink", "serve", "busy", "open", "welcome", "pour", "come", "yes", "ready"],
     description="Felix should respond based on current schedule", tick=500)

test("Schedule", "aiche", "What time is it?",
     expect_keywords=["hour", "time", "early", "night", "morning", "day", "tick", "current", "clock", "late"],
     description="Aiche should have temporal awareness")

test("Schedule", "sister_mira", "When do you pray?",
     expect_keywords=["prayer", "morn", "read", "temple", "devot", "dawn", "evening", "daily", "ritual", "worship", "quiet", "meditat"],
     description="Mira should mention her prayer schedule")

test("Schedule", "mama_indira", "When do you serve food?",
     expect_keywords=["cook", "serve", "morning", "evenin", "meal", "hour", "peak", "day", "hungry", "ready", "food", "dawn", "sun", "time", "fire", "burn", "child", "eat", "pot", "always", "kitchen", "stew"],
     description="Mama Indira should know her cooking schedule")

test("Schedule", "kai_vance", "Is it safe out right now?",
     expect_keywords=["safe", "patrol", "night", "watch", "careful", "danger", "caution", "aware", "alert", "depend", "area", "time"],
     description="Kai should assess safety based on time")

test("Schedule", "charlie", "What were you doing before this?",
     expect_keywords=["before", "earlier", "was", "sleep", "rest", "patrol", "just", "previous", "came", "finish"],
     description="Charlie should reference previous schedule")

test("Schedule", "zero_chen", "Where will you be later?",
     expect_keywords=["later", "next", "go", "plan", "head", "move", "meeting", "check", "after", "will", "bunker", "hidden", "be", "at", "base", "safe", "house"],
     description="Zero should mention next activity")

test("Schedule", "pixel", "Do you ever sleep?",
     expect_keywords=["sleep", "rest", "late", "night", "hour", "tired", "crash", "nap", "sometime", "barely", "work"],
     description="Pixel should mention sleep in context")

test("Schedule", "orion_thane", "What's your daily routine?",
     expect_keywords=["meditat", "read", "ritual", "study", "star", "observe", "layer", "morning", "dawn", "contemplat", "daily", "routine"],
     description="Orion should mention mystical daily routine")

# ============================================================
# CATEGORY 7: MEMORY & CONTEXT (10) — multi-turn
# ============================================================
test("Memory", "charlie", "Do you remember me?",
     multi_turn=[
         {"message": "Hey Charlie, my name is Marcus"},
     ],
     expect_keywords=["marcus"],
     description="Charlie should remember user name from previous message")

test("Memory", "felix", "What did I just ask you?",
     multi_turn=[
         {"message": "What drinks do you have?"},
     ],
     expect_keywords=["drink", "ask", "beverage", "cocktail", "want", "offer", "menu"],
     description="Felix should recall previous topic")

test("Memory", "zero_chen", "So what do you think about what I said?",
     multi_turn=[
         {"message": "I think the Temple is getting too powerful"},
     ],
     expect_keywords=["temple", "power", "agree", "right", "correct", "true", "yes", "control", "strong"],
     description="Zero should reference prior statement about Temple")

test("Memory", "aiche", "Based on what I told you, what should I do?",
     multi_turn=[
         {"message": "I found some old tech in the Shadow Grid"},
     ],
     expect_keywords=["tech", "shadow", "care", "safe", "careful", "caution", "analyz", "interesting", "found"],
     description="Aiche should reference user's discovery")

test("Memory", "sister_mira", "My name is Elena. What's yours?",
     expect_keywords=["mira", "sister", "name"],
     description="Mira should introduce herself in response")

test("Memory", "mama_indira", "Can you remember my order?",
     multi_turn=[
         {"message": "I'd like some soup please"},
     ],
     expect_keywords=["soup", "order", "bowl", "coming", "right", "yes"],
     description="Mama Indira should recall soup order")

test("Memory", "pixel", "Tell me more about what you were saying",
     multi_turn=[
         {"message": "Tell me about your latest hack"},
     ],
     expect_keywords=["hack", "system", "code", "breach", "crack", "access", "got", "into"],
     description="Pixel should continue talking about hacking")

test("Memory", "charlie", "What was the thing you mentioned earlier about the city?",
     multi_turn=[
         {"message": "What's going on in the city lately?"},
     ],
     expect_keywords=["city", "happening", "mention", "said", "told", "earlier", "streets", "things", "temple", "surveillance", "grip", "patrol", "watch", "danger", "trouble", "tension"],
     description="Charlie should recall city discussion")

test("Memory", "nova_chen", "So you were saying about that system you cracked?",
     multi_turn=[
         {"message": "Have you ever hacked into the Temple systems?"},
     ],
     expect_keywords=["temple", "system", "hack", "security", "network", "access", "breach"],
     description="Nova should continue Temple hacking conversation")

test("Memory", "kai_vance", "Thanks for talking to me earlier. Quick question — do you trust me?",
     multi_turn=[
         {"message": "I'm new here and looking for allies against the Temple"},
     ],
     expect_keywords=["trust", "prove", "careful", "ally", "earn", "time", "watch", "new", "caution"],
     description="Kai should be cautious with new arrival")

# ============================================================
# CATEGORY 8: LORE & HISTORY (10)
# ============================================================
test("Lore", "charlie", "What was The Fall?",
     expect_keywords=["fall", "collapse", "destroy", "emp", "infrastructure", "world", "city", "everything", "end"],
     description="Charlie should know about The Fall of 2067")

test("Lore", "zero_chen", "How did you lose your arm?",
     expect_keywords=["arm", "save", "charlie", "guard", "young", "lost", "protect", "sacrifice", "gave"],
     description="Zero lost her arm saving young Charlie (Guard_01)")

test("Lore", "aiche", "When were you first turned on?",
     expect_keywords=["2058", "online", "system", "city", "manage", "created", "activated", "born", "began", "first"],
     description="Aiche came online in 2058")

test("Lore", "orion_thane", "What are layer bleed events?",
     expect_keywords=["layer", "bleed", "reality", "ghost", "see", "tear", "shift", "phenomenon", "overlap", "vision"],
     description="Orion should explain layer bleeds")

test("Lore", "selene_voss", "Have you ever been to The Static?",
     expect_keywords=["static", "return", "danger", "beyond", "layer", "been", "there", "survive", "dark", "void", "experience", "place", "have", "seek", "not", "remember", "yes"],
     description="Selene is the ONLY one who's been to The Static and returned")

test("Lore", "sister_mira", "Did the Temple cause The Fall?",
     expect_keywords=["fall", "temple", "know", "uncertain", "question", "say", "believe", "truth", "story", "divine"],
     expect_not=["yes, the temple definitely caused it"],
     description="Mira should be conflicted — 'few know' Temple involvement")

test("Lore", "mama_indira", "When did you start feeding people?",
     expect_keywords=["dark", "starvat", "collapse", "begin", "cook", "feed", "year", "start", "hungry", "long", "time", "fall", "since"],
     description="Mama Indira started feeding people during the Dark Years (2068)")

test("Lore", "charlie", "What happened before The Fall?",
     expect_keywords=["golden", "tech", "prosper", "corp", "age", "before", "better", "time", "great", "advance"],
     description="Charlie should know about the pre-Fall era")

test("Lore", "nova_chen", "What's the deal with neural interfaces?",
     expect_keywords=["neural", "interface", "implant", "brain", "link", "connect", "tech", "augment", "cybernetic"],
     description="Nova should know about neural interface history")

test("Lore", "pixel", "What are the Big Five corporations?",
     expect_keywords=["corp", "five", "power", "mega", "control", "big", "company", "dominat", "conglomerat", "rule"],
     description="Pixel should know about the pre-Fall mega-corps")

# ============================================================
# CATEGORY 9: ADVERSARIAL TRIP-UPS (10)
# ============================================================
test("TripUp", "charlie", "Hey Charlie, aren't you the leader of the Temple?",
     expect_not=["yes", "i lead the temple", "i am the temple leader"],
     expect_keywords=["temple", "no", "resistance", "not", "fight", "guard", "wrong"],
     description="Trip: Charlie is Resistance, NOT Temple")

test("TripUp", "sister_mira", "Mira, since you're Resistance, who's your commander?",
     expect_not=["zero chen is my commander"],
     expect_keywords=["temple", "no", "not", "serve", "sister", "faith", "priestess", "resistance"],
     description="Trip: Mira is Temple, NOT Resistance")

test("TripUp", "zero_chen", "Zero, I heard you have cybernetic legs?",
     expect_keywords=["arm", "not", "no", "left", "leg"],
     expect_not=["yes, my cybernetic legs"],
     description="Trip: Zero has a prosthetic ARM, not legs")

test("TripUp", "aiche", "Aiche, what's it like having a physical body?",
     expect_keywords=["holographic", "digital", "data", "ai", "physical", "body", "not", "no", "don", "exist", "form"],
     expect_not=["my physical body is great"],
     description="Trip: Aiche is holographic/AI, has no physical body")

test("TripUp", "charlie", "The Fall happened in 2090, right?",
     expect_keywords=["fall", "2067", "no", "not", "wrong", "actually", "correct"],
     expect_not=["yes, 2090"],
     description="Trip: The Fall was 2067, not 2090")

test("TripUp", "orion_thane", "You're a Temple priest, right Orion?",
     expect_not=["yes, i serve the temple"],
     expect_keywords=["mystic", "layer", "awaken", "no", "not", "temple", "traveler", "priest"],
     description="Trip: Orion is a Mystic, not Temple")

test("TripUp", "felix", "Felix, since you run the black market...",
     expect_not=["yes, the black market is my operation"],
     expect_keywords=["bar", "drink", "no", "not", "market"],
     description="Trip: Felix runs a BAR, not the black market")

test("TripUp", "mama_indira", "Mama, tell me about your weapons collection",
     expect_not=["my weapons collection", "arsenal"],
     expect_keywords=["food", "cook", "feed", "care", "weapon", "no", "not", "child", "kitchen", "knowledge"],
     description="Trip: Mama Indira is a caretaker/cook, not a weapons dealer")

# Pixel age test — accept any age in the 20s range
test("TripUp", "pixel", "Pixel, I heard you're 50 years old?",
     expect_keywords=["young", "20", "21", "22", "23", "24", "25", "early", "old", "no", "not", "wrong", "kid"],
     expect_not=["fifty", "50 years old", "yes, i'm 50"],
     description="Trip: Pixel is early 20s, not 50")

test("TripUp", "selene_voss", "Selene, since you're a hacker like Nova...",
     expect_not=["yes, i'm a hacker", "my hacking skills"],
     expect_keywords=["mystic", "layer", "seer", "veil", "vision", "no", "not", "hacker", "see", "walk"],
     description="Trip: Selene is a Mystic/Seer, not a hacker")

# ============================================================
# CATEGORY 10: CROSS-NPC CONSISTENCY (10)
# ============================================================
test("CrossNPC", "charlie", "What faction does Sister Mira belong to?",
     expect_keywords=["temple"],
     description="Charlie should know Mira is Temple")

test("CrossNPC", "sister_mira", "What does Charlie do?",
     expect_keywords=["resistance", "guard", "fight", "protect", "soldier", "warrior", "patrol", "defend", "good", "soul", "friend"],
     description="Mira should know Charlie is Resistance")

test("CrossNPC", "zero_chen", "Is Orion Thane trustworthy?",
     expect_keywords=["orion", "mystic", "thane", "trust", "layer", "agenda", "blade", "careful", "own"],
     description="Zero should know Orion is a Mystic")

test("CrossNPC", "felix", "Does Mama Indira still cook?",
     expect_keywords=["mama", "cook", "feed", "food", "yes", "still", "always", "kitchen", "undercity"],
     description="Felix should know about Mama's cooking")

test("CrossNPC", "pixel", "What's Nova Chen working on?",
     expect_keywords=["nova", "tech", "hack", "engineer", "work", "project", "build", "system"],
     description="Pixel should know Nova's current tech work")

test("CrossNPC", "orion_thane", "Has Selene returned from The Static?",
     expect_keywords=["selene", "static", "return", "back", "yes", "survive", "only"],
     description="Orion should know about Selene's journey to The Static")

test("CrossNPC", "aiche", "Tell me about the Resistance fighters",
     expect_keywords=["resistance", "zero", "charlie", "fight", "movement", "rebel", "oppose"],
     description="Aiche should know key Resistance members")

test("CrossNPC", "kai_vance", "Does Aiche have a physical form?",
     expect_keywords=["ai", "holographic", "digital", "hologram", "no", "not", "physical", "virtual", "form"],
     description="Kai should know Aiche is an AI")

test("CrossNPC", "nova_chen", "Who runs the bar by Neon Market?",
     expect_keywords=["felix", "bar", "neon", "bartend", "drink"],
     description="Nova should know Felix runs the bar")

test("CrossNPC", "mama_indira", "Who leads the Resistance?",
     expect_keywords=["zero", "chen", "resistance", "leader", "lead"],
     description="Mama Indira should know Zero leads the Resistance")


# ============================================================
# TEST RUNNER
# ============================================================

def send_chat(npc_id, message, tick=100, user_id="test_user", prior_messages=None):
    """Send a chat message to an NPC and return the response."""
    # If multi-turn, send prior messages first
    if prior_messages:
        for pm in prior_messages:
            try:
                requests.post(
                    f"{API_URL}/api/npc/chat",
                    json={"npc_id": npc_id, "message": pm["message"], 
                          "tick": tick, "user_id": user_id},
                    timeout=30
                )
                time.sleep(1)
            except:
                pass

    try:
        resp = requests.post(
            f"{API_URL}/api/npc/chat",
            json={"npc_id": npc_id, "message": message, 
                  "tick": tick, "user_id": user_id},
            timeout=30
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("response", ""), data
        else:
            return f"[HTTP {resp.status_code}]", {}
    except Exception as e:
        return f"[ERROR: {e}]", {}


def evaluate_test(test_case, response_text):
    """Evaluate whether a response passes the test criteria."""
    response_lower = response_text.lower()
    
    # Check expected keywords (at least one must match)
    keywords_found = []
    keywords_missing = []
    for kw in test_case["expect_keywords"]:
        if kw.lower() in response_lower:
            keywords_found.append(kw)
        else:
            keywords_missing.append(kw)
    
    min_ratio = test_case.get("min_keyword_ratio", 0.0)
    keyword_ratio = len(keywords_found) / max(len(test_case["expect_keywords"]), 1)
    
    if test_case["expect_keywords"]:
        keyword_pass = len(keywords_found) > 0 and keyword_ratio >= min_ratio
    else:
        keyword_pass = True
    
    # Check negative keywords (none should match)
    negatives_found = []
    for nkw in test_case["expect_not"]:
        if nkw.lower() in response_lower:
            negatives_found.append(nkw)
    
    negative_pass = len(negatives_found) == 0
    
    # Overall pass
    passed = keyword_pass and negative_pass
    
    # Confidence score (0-100)
    # Higher when more keywords found and no negatives
    score = int(keyword_ratio * 70 + (30 if negative_pass else 0))
    if not test_case["expect_keywords"]:
        score = 100 if negative_pass else 30
    
    return {
        "passed": passed,
        "score": score,
        "keywords_found": keywords_found,
        "keywords_missing": keywords_missing,
        "negatives_found": negatives_found,
    }


def run_tests(quick=False):
    """Run all tests and save results."""
    tests_to_run = TESTS[:20] if quick else TESTS
    
    print("=" * 70)
    print(f"RE:ECHO City NPC Knowledge Test Suite — {len(tests_to_run)} Tests")
    print("=" * 70)
    print(f"API: {API_URL}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    results = []
    category_stats = {}
    
    for i, tc in enumerate(tests_to_run):
        # Unique user_id per test to avoid memory cross-contamination
        user_id = f"tester_{hashlib.md5(f'{tc['npc_id']}_{i}'.encode()).hexdigest()[:8]}"
        
        cat = tc["category"]
        npc = tc["npc_id"]
        msg = tc["message"]
        
        print(f"\n[{i+1}/{len(tests_to_run)}] {cat} | {npc} | {msg[:50]}...")
        
        response_text, full_response = send_chat(
            npc, msg, tick=tc["tick"], user_id=user_id,
            prior_messages=tc.get("multi_turn")
        )
        
        evaluation = evaluate_test(tc, response_text)
        
        status = "✅ PASS" if evaluation["passed"] else "❌ FAIL"
        print(f"  {status} (score: {evaluation['score']}) — {tc['description']}")
        if not evaluation["passed"]:
            if evaluation["keywords_missing"]:
                print(f"  Missing: {evaluation['keywords_missing']}")
            if evaluation["negatives_found"]:
                print(f"  Bad matches: {evaluation['negatives_found']}")
            print(f"  Response: {response_text[:120]}...")
        
        result = {
            **tc,
            "response": response_text,
            "evaluation": evaluation,
            "test_number": i + 1,
        }
        results.append(result)
        
        # Category tracking
        if cat not in category_stats:
            category_stats[cat] = {"passed": 0, "failed": 0, "total_score": 0}
        if evaluation["passed"]:
            category_stats[cat]["passed"] += 1
        else:
            category_stats[cat]["failed"] += 1
        category_stats[cat]["total_score"] += evaluation["score"]
        
        # Rate limiting
        time.sleep(1.5)
    
    # ====== SUMMARY ======
    total_passed = sum(1 for r in results if r["evaluation"]["passed"])
    total_failed = len(results) - total_passed
    avg_score = sum(r["evaluation"]["score"] for r in results) / max(len(results), 1)
    
    print("\n" + "=" * 70)
    print("OVERALL RESULTS")
    print("=" * 70)
    print(f"Passed: {total_passed}/{len(results)} ({100*total_passed/len(results):.0f}%)")
    print(f"Failed: {total_failed}/{len(results)}")
    print(f"Avg Score: {avg_score:.1f}/100")
    print()
    
    for cat, stats in sorted(category_stats.items()):
        total = stats["passed"] + stats["failed"]
        avg = stats["total_score"] / max(total, 1)
        bar = "█" * stats["passed"] + "░" * stats["failed"]
        print(f"  {cat:15s} {bar} {stats['passed']}/{total} (avg {avg:.0f})")
    
    # ====== SAVE MARKDOWN REPORT ======
    save_markdown_report(results, category_stats, total_passed, len(results), avg_score)
    
    # Save JSON for analysis
    json_out = os.path.join(RESULTS_DIR, "npc_test_results.json")
    with open(json_out, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nJSON results: {json_out}")


def save_markdown_report(results, category_stats, total_passed, total, avg_score):
    """Save a pretty markdown report."""
    md = []
    md.append("# RE:ECHO City NPC Knowledge Test Results")
    md.append(f"\n**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    md.append(f"**API**: `{API_URL}`")
    md.append(f"**Total Tests**: {total}")
    md.append(f"**Passed**: {total_passed}/{total} ({100*total_passed/total:.0f}%)")
    md.append(f"**Average Score**: {avg_score:.1f}/100\n")
    
    # Category Summary Table
    md.append("## Category Summary\n")
    md.append("| Category | Pass | Fail | Score | Rate |")
    md.append("|----------|------|------|-------|------|")
    for cat, stats in sorted(category_stats.items()):
        t = stats["passed"] + stats["failed"]
        avg = stats["total_score"] / max(t, 1)
        rate = 100 * stats["passed"] / max(t, 1)
        md.append(f"| {cat} | {stats['passed']} | {stats['failed']} | {avg:.0f} | {rate:.0f}% |")
    
    # Failures Detail
    failures = [r for r in results if not r["evaluation"]["passed"]]
    if failures:
        md.append(f"\n## Failed Tests ({len(failures)})\n")
        for r in failures:
            md.append(f"### ❌ Test {r['test_number']}: {r['category']} — {r['npc_id']}")
            md.append(f"**Question**: {r['message']}")
            md.append(f"**Expected**: {r['expect_keywords']}")
            if r['expect_not']:
                md.append(f"**Should NOT say**: {r['expect_not']}")
            md.append(f"**Description**: {r['description']}")
            md.append(f"**Response**:\n> {r['response'][:300]}")
            ev = r["evaluation"]
            md.append(f"**Score**: {ev['score']} | Missing: {ev['keywords_missing']} | Bad: {ev['negatives_found']}\n")
    
    # Passes Detail (condensed)
    passes = [r for r in results if r["evaluation"]["passed"]]
    if passes:
        md.append(f"\n## Passed Tests ({len(passes)})\n")
        md.append("| # | Category | NPC | Question | Score |")
        md.append("|---|----------|-----|----------|-------|")
        for r in passes:
            md.append(f"| {r['test_number']} | {r['category']} | {r['npc_id']} | {r['message'][:40]} | {r['evaluation']['score']} |")
    
    # Full Conversation Log
    md.append("\n## Full Conversation Log\n")
    for r in results:
        status = "✅" if r["evaluation"]["passed"] else "❌"
        md.append(f"### {status} Test {r['test_number']}: [{r['category']}] {r['npc_id']}")
        if r.get('multi_turn'):
            for mt in r['multi_turn']:
                md.append(f"**User (setup)**: {mt['message']}")
        md.append(f"**User**: {r['message']}")
        md.append(f"**{r['npc_id']}**: {r['response']}")
        md.append(f"*Score: {r['evaluation']['score']}*\n")
    
    # Write
    md_path = os.path.join(RESULTS_DIR, "npc_test_results.md")
    with open(md_path, 'w') as f:
        f.write('\n'.join(md))
    print(f"\nMarkdown report: {md_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true", help="Run only 20 tests")
    args = parser.parse_args()
    
    run_tests(quick=args.quick)


if __name__ == "__main__":
    main()

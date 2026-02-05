--[[
  Mock NPC for Testing
  
  A fully-featured NPC for testing all systems
]]--

MOCK_NPC_FULL = {
    id = "NPC_TEST_FULL",
    name = "Dr. Test Subject",
    
    -- Basic info
    faction = "Resistance",
    occupation = "engineer",
    location_current = "signal_noir_district",
    location_home = "residential_block_7",
    
    -- Agent Needs (Egregoria pattern)
    needs = {
        hunger = 75,
        energy = 60,
        social = 40,
        safety = 80,
        purpose = 90,
        comfort = 50,
        autonomy = 70
    },
    
    -- Mood (calculated from needs)
    mood = "focused",
    
    -- Markers for encounter/content matching
    markers = {
        "tech_enthusiast",
        "resistance_affiliated",
        "engineer",
        "story_charlie_intro"
    },
    
    -- Schedule
    schedule = {
        {hour = 6, activity = "wake"},
        {hour = 7, activity = "eat", location = "home"},
        {hour = 8, activity = "work", location = "engineer_workshop"},
        {hour = 12, activity = "eat", location = "noodle_shop"},
        {hour = 13, activity = "work", location = "engineer_workshop"},
        {hour = 18, activity = "social", location = "underground_bar"},
        {hour = 22, activity = "sleep", location = "home"}
    },
    
    -- Relationships
    relationships = {
        ["NPC_CHARLIE"] = {affinity = 80, type = "colleague"},
        ["NPC_MAYA"] = {affinity = 50, type = "acquaintance"}
    },
    
    -- Backstory
    backstory = "Dr. Test Subject was once a corporate engineer until discovering the truth about Signal Corp's experiments. Now they work with the Resistance, using their technical skills to fight the system.",
    
    -- Personality traits
    personality = {
        openness = 0.7,
        conscientiousness = 0.8,
        extraversion = 0.4,
        agreeableness = 0.6,
        neuroticism = 0.3
    },
    
    -- Skills
    skills = {
        engineering = 90,
        hacking = 75,
        combat = 30,
        social = 50
    },
    
    -- Inventory
    inventory = {
        credits = 1500,
        items = {"toolkit", "encrypted_datapad"}
    }
}

-- Minimal NPC for testing required fields
MOCK_NPC_MINIMAL = {
    id = "NPC_TEST_MINIMAL",
    name = "Minimal Test",
    faction = "Civilian",
    occupation = "none"
}

-- NPC with missing fields for error testing
MOCK_NPC_INVALID = {
    id = "NPC_TEST_INVALID"
    -- Missing required fields: name, faction, occupation
}

return {
    MOCK_NPC_FULL = MOCK_NPC_FULL,
    MOCK_NPC_MINIMAL = MOCK_NPC_MINIMAL,
    MOCK_NPC_INVALID = MOCK_NPC_INVALID
}

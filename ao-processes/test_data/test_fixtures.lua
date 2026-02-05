--[[
  AO World Engine - Test Fixtures
  
  Reusable test data for unit testing and development
]]--

-- Mock NPC for testing
MOCK_NPC = {
    id = "NPC_TEST_001",
    name = "Test Character",
    faction = "Civilian",
    occupation = "test_subject",
    location_current = "test_district",
    needs = {
        hunger = 50,
        energy = 50,
        social = 50,
        safety = 100,
        purpose = 50,
        comfort = 50,
        autonomy = 50
    },
    mood = "neutral",
    markers = {"test_marker", "debug"},
    backstory = "A character created for testing purposes."
}

-- Mock Faction for testing
MOCK_FACTION = {
    id = "test_faction",
    name = "Test Faction",
    type = "neutral",
    description = "A faction for testing",
    territories = {"test_district"},
    rivals = {},
    allies = {},
    reputation_base = 0,
    markers = {"test_marker"}
}

-- Mock Vehicle for testing
MOCK_VEHICLE = {
    id = "test_vehicle",
    name = "Test Car",
    type = "sedan",
    capacity = 4,
    speed = 60,
    fuel = 100,
    route = nil
}

-- Mock Encounter for testing
MOCK_ENCOUNTER = {
    id = "test_encounter",
    name = "Test Encounter",
    type = "random",
    probability = 0.5,
    required_markers = {},
    location_modifiers = {},
    rewards = {}
}

-- Mock News Item for testing
MOCK_NEWS = {
    id = "test_news",
    headline = "Test News Headline",
    type = "video",
    source = "test_source",
    content = "This is test news content.",
    timestamp = os.time(),
    propagation_speed = 1.0,
    distortion_factor = 0.0
}

-- Utility: Create test NPC with overrides
function create_test_npc(overrides)
    local npc = {}
    for k, v in pairs(MOCK_NPC) do
        npc[k] = v
    end
    if overrides then
        for k, v in pairs(overrides) do
            npc[k] = v
        end
    end
    return npc
end

-- Utility: Create test faction with overrides
function create_test_faction(overrides)
    local faction = {}
    for k, v in pairs(MOCK_FACTION) do
        faction[k] = v
    end
    if overrides then
        for k, v in pairs(overrides) do
            faction[k] = v
        end
    end
    return faction
end

-- Test assertions
function assert_equal(actual, expected, message)
    if actual ~= expected then
        error(message or string.format("Expected %s but got %s", tostring(expected), tostring(actual)))
    end
    return true
end

function assert_true(condition, message)
    if not condition then
        error(message or "Assertion failed: expected true")
    end
    return true
end

function assert_not_nil(value, message)
    if value == nil then
        error(message or "Assertion failed: expected non-nil value")
    end
    return true
end

-- Export
return {
    MOCK_NPC = MOCK_NPC,
    MOCK_FACTION = MOCK_FACTION,
    MOCK_VEHICLE = MOCK_VEHICLE,
    MOCK_ENCOUNTER = MOCK_ENCOUNTER,
    MOCK_NEWS = MOCK_NEWS,
    create_test_npc = create_test_npc,
    create_test_faction = create_test_faction,
    assert_equal = assert_equal,
    assert_true = assert_true,
    assert_not_nil = assert_not_nil
}

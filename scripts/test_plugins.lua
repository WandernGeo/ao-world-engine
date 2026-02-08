--[[
  AO World Engine - Integration Test Suite
  
  Tests all pluggable systems:
  - Factions
  - Occupations
  - News/Information
  - Encounters
  - Vehicles
  - Universal Plugin
]]--

-- Test results
local results = {
    passed = 0,
    failed = 0,
    tests = {}
}

local function test(name, func)
    local ok, err = pcall(func)
    if ok then
        results.passed = results.passed + 1
        table.insert(results.tests, {name = name, passed = true})
        print("✓ " .. name)
    else
        results.failed = results.failed + 1
        table.insert(results.tests, {name = name, passed = false, error = err})
        print("✗ " .. name .. ": " .. tostring(err))
    end
end

local function assert_eq(a, b, msg)
    if a ~= b then
        error(msg or string.format("Expected %s, got %s", tostring(b), tostring(a)))
    end
end

local function assert_true(val, msg)
    if not val then
        error(msg or "Expected true, got false")
    end
end

local function assert_not_nil(val, msg)
    if val == nil then
        error(msg or "Expected non-nil value")
    end
end

print("====================================")
print("AO World Engine - Integration Tests")
print("====================================\n")

-- =============================================================================
-- FACTION TESTS
-- =============================================================================
print("--- Faction System ---")

-- Mock Handlers for testing
Handlers = {
    add = function() end,
    utils = { hasMatchingTag = function() return function() return true end end }
}
ao = { send = function() end }
os = os or { time = function() return 0 end }
WorldTick = 100

-- Load factions module
dofile("ao-processes/factions.lua")

test("Factions: init_default_factions creates 7 factions", function()
    init_default_factions()
    local count = 0
    for _ in pairs(FACTIONS) do count = count + 1 end
    assert_eq(count, 7)
end)

test("Factions: Resistance and ECHO Corp are rivals", function()
    assert_true(are_rivals("resistance", "echo_corp"))
end)

test("Factions: Resistance and Cyber Collective are allies", function()
    assert_true(are_allies("resistance", "cyber_collective"))
end)

test("Factions: Can add faction member", function()
    local success = add_faction_member("resistance", "npc_001", "operative")
    assert_true(success)
end)

test("Factions: Can get NPC faction", function()
    local faction_id = get_npc_faction("npc_001")
    assert_eq(faction_id, "resistance")
end)

test("Factions: Can claim building", function()
    claim_building("underground", "warehouse_7")
    local owner = get_building_owner("warehouse_7")
    assert_eq(owner, "underground")
end)

-- =============================================================================
-- OCCUPATION TESTS
-- =============================================================================
print("\n--- Occupation System ---")

dofile("ao-processes/occupations.lua")

test("Occupations: init_city_occupations creates 14+ jobs", function()
    init_city_occupations()
    local count = 0
    for _ in pairs(OCCUPATIONS) do count = count + 1 end
    assert_true(count >= 14, "Expected at least 14 occupations, got " .. count)
end)

test("Occupations: Can assign NPC to occupation", function()
    local success = assign_occupation("npc_002", "police")
    assert_true(success)
end)

test("Occupations: Can get NPC occupation", function()
    local occ_id = get_npc_occupation("npc_002")
    assert_eq(occ_id, "police")
end)

test("Occupations: Police works during day shift", function()
    local working = is_working("npc_002", 10, 1)  -- 10 AM Monday
    assert_true(working)
end)

test("Occupations: Security has encounter modifier for thief", function()
    assign_occupation("npc_003", "security")
    assign_occupation("npc_004", "thief")
    local modifier = get_occupation_encounter_modifier("npc_003", "npc_004")
    assert_true(modifier > 1, "Expected modifier > 1 for security vs thief")
end)

-- =============================================================================
-- VEHICLE TESTS
-- =============================================================================
print("\n--- Vehicle System ---")

dofile("ao-processes/vehicles.lua")

test("Vehicles: init_default_vehicles creates 9+ types", function()
    init_default_vehicles()
    local count = 0
    for _ in pairs(VEHICLE_TYPES) do count = count + 1 end
    assert_true(count >= 9, "Expected at least 9 vehicle types")
end)

test("Vehicles: Can spawn vehicle instance", function()
    local vehicle = spawn_vehicle("sedan_standard", {district = "downtown"})
    assert_not_nil(vehicle)
    assert_not_nil(vehicle.id)
    assert_not_nil(vehicle.plate)
end)

test("Vehicles: init_default_routes creates routes", function()
    init_default_routes()
    local count = 0
    for _ in pairs(ROUTES) do count = count + 1 end
    assert_true(count >= 4, "Expected at least 4 routes")
end)

test("Vehicles: Can queue gradual spawns", function()
    queue_vehicle_spawns("city_bus", 10, 5)
    assert_eq(#SPAWN_QUEUE, 1)
end)

test("Vehicles: Process spawn queue creates vehicles", function()
    local spawned = process_spawn_queue()
    assert_true(#spawned >= 1, "Expected at least 1 vehicle spawned per tick")
end)

-- =============================================================================
-- ENCOUNTER TESTS
-- =============================================================================
print("\n--- Encounter System ---")

dofile("ao-processes/encounters.lua")

test("Encounters: init_default_markers creates markers", function()
    init_default_markers()
    local count = 0
    for _ in pairs(ENCOUNTER_MARKERS) do count = count + 1 end
    assert_true(count >= 5, "Expected at least 5 marker rules")
end)

test("Encounters: Can set NPC markers", function()
    set_npc_markers("npc_test_1", {"resistance_affiliated", "tech_enthusiast"})
    local markers = get_npc_markers("npc_test_1")
    assert_eq(#markers, 2)
end)

test("Encounters: Story marker gives high encounter chance", function()
    set_npc_markers("npc_story_a", {"story_charlie_intro"})
    set_npc_markers("npc_story_b", {})
    local chance = calculate_encounter_chance("npc_story_a", "npc_story_b", {})
    assert_true(chance >= 0.9, "Expected story_charlie_intro to give 90%+ chance")
end)

test("Encounters: init_mission_templates creates templates", function()
    init_mission_templates()
    local count = 0
    for _ in pairs(MISSION_TEMPLATES) do count = count + 1 end
    assert_true(count >= 7, "Expected at least 7 mission templates")
end)

test("Encounters: Can create mission from template", function()
    local mission = create_mission("spy_on_faction", {
        assigned_npc = "npc_spy",
        source_faction = "resistance",
        target_faction = "echo_corp"
    })
    assert_not_nil(mission)
    assert_eq(mission.status, "active")
end)

test("Encounters: Can progress mission", function()
    local missions = {}
    for id, m in pairs(ACTIVE_MISSIONS) do
        table.insert(missions, id)
    end
    if #missions > 0 then
        local mission = progress_mission(missions[1], 5)
        assert_true(mission.progress >= 5)
    end
end)

-- =============================================================================
-- NEWS SYSTEM TESTS
-- =============================================================================
print("\n--- News System ---")

dofile("ao-processes/news_system.lua")

test("News: Can register news type", function()
    register_news_type("emergency_broadcast", {
        name = "Emergency Broadcast",
        reach = "global",
        trust_modifier = 1.0
    })
    assert_not_nil(NEWS_TYPES["emergency_broadcast"])
end)

test("News: Can create news item", function()
    local news = create_news({
        type = "gossip",
        headline = "Strange lights in Sector 7",
        content = "Witnesses report mysterious activity...",
        source_npc = "npc_gossiper"
    })
    assert_not_nil(news)
    assert_not_nil(news.id)
end)

test("News: Can deliver news to NPC", function()
    -- Get a news ID
    local news_id = nil
    for id, _ in pairs(NEWS_ITEMS) do
        news_id = id
        break
    end
    
    local success = deliver_news("npc_receiver", news_id, "direct")
    assert_true(success)
end)

test("News: NPC knowledge is tracked", function()
    local knowledge = NPC_KNOWLEDGE["npc_receiver"]
    assert_not_nil(knowledge)
    local has_news = false
    for _ in pairs(knowledge) do has_news = true break end
    assert_true(has_news)
end)

test("News: Can register reporter", function()
    local reporter = register_reporter("npc_reporter", {
        outlet = "resistance_radio",
        specialty = "politics",
        credibility = 0.8
    })
    assert_not_nil(reporter)
    assert_eq(reporter.outlet, "resistance_radio")
end)

-- =============================================================================
-- CONTENT REGISTRY TESTS
-- =============================================================================
print("\n--- Content Registry ---")

dofile("ao-processes/content_registry.lua")

test("Content: Can register NPC", function()
    local npc = register_npc("test_npc_001", {
        name = "Test NPC",
        gender = "male",
        faction = "underground",
        occupation = "thief",
        markers = {"criminal", "night_owl"}
    })
    assert_not_nil(npc)
    assert_eq(npc.name, "Test NPC")
end)

test("Content: NPC auto-gets faction marker", function()
    local npc = get_npc("test_npc_001")
    local has_faction_marker = false
    for _, m in ipairs(npc.markers) do
        if m == "underground_affiliated" then
            has_faction_marker = true
            break
        end
    end
    assert_true(has_faction_marker)
end)

test("Content: Can register lore", function()
    local lore = register_lore("test_lore", {
        title = "Test History",
        category = "history",
        content = "Long ago...",
        year = 2040
    })
    assert_not_nil(lore)
end)

test("Content: Can register location", function()
    local loc = register_location("test_bar", {
        name = "Test Bar",
        type = "building",
        district = "undercity",
        faction_hangout = "underground"
    })
    assert_not_nil(loc)
end)

test("Content: Can search NPCs by faction", function()
    local results = search_npcs({faction = "underground"})
    assert_true(#results >= 1)
end)

test("Content: Can get content stats", function()
    local stats = get_content_stats()
    assert_true(stats.npcs >= 1)
end)

-- =============================================================================
-- UNIVERSAL PLUGIN TESTS
-- =============================================================================
print("\n--- Universal Plugin ---")

dofile("ao-processes/universal_plugin.lua")

test("Plugin: Can register entity type", function()
    local etype = register_entity_type("gadget", {
        description = "Tech gadgets",
        default_markers = {"tech"},
        npc_can_own = true
    })
    assert_not_nil(etype)
end)

test("Plugin: Can register entity", function()
    local entity = register_entity("gadget", "cyber_eye", {
        name = "Cyber Eye",
        markers = {"cybernetic", "vision_enhancement"},
        seekable_traits = {"augmentation"},
        action_triggers = {
            install = {
                required_markers = {"cybernetic_compatible"}
            }
        }
    })
    assert_not_nil(entity)
    assert_true(#entity.markers >= 3)  -- tech + 2 custom
end)

test("Plugin: Auto-registers unknown entity types", function()
    local entity = register_entity("new_type_xyz", "item_001", {
        name = "New Item"
    })
    assert_not_nil(ENTITY_TYPES["new_type_xyz"])
end)

test("Plugin: Can find entities by NPC markers", function()
    local results = find_matching_entities({"tech", "cybernetic"}, "gadget")
    assert_true(#results >= 1)
end)

test("Plugin: Can queue content for gradual spawn", function()
    queue_content("gadget", {
        {id = "g1", name = "Gadget 1"},
        {id = "g2", name = "Gadget 2"},
        {id = "g3", name = "Gadget 3"}
    }, 3)
    assert_eq(#CONTENT_QUEUE, 1)
end)

test("Plugin: Process queue spawns content", function()
    local spawned = process_content_queue()
    assert_true(#spawned >= 1)
end)

test("Plugin: get_plugin_stats works", function()
    local stats = get_plugin_stats()
    assert_true(stats.entity_types >= 3)
    assert_true(stats.total_entities >= 1)
end)

-- =============================================================================
-- RESULTS
-- =============================================================================
print("\n====================================")
print(string.format("Results: %d passed, %d failed", results.passed, results.failed))
print("====================================")

if results.failed > 0 then
    print("\nFailed tests:")
    for _, t in ipairs(results.tests) do
        if not t.passed then
            print("  - " .. t.name .. ": " .. (t.error or "unknown error"))
        end
    end
end

return results

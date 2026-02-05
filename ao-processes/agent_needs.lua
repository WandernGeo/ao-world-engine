--[[
  AO World Engine - Agent Needs System
  
  Egregoria-inspired need-based decision making for NPCs.
  Each NPC has needs that decay over time, driving autonomous behavior.
  
  Source: Egregoria (Uriopass/Egregoria) - https://github.com/Uriopass/Egregoria
  See: docs/CITY_SIMULATION_RESEARCH.md
]]--

local json = require("json")

-- =============================================================================
-- NEEDS CONFIGURATION
-- =============================================================================

NEEDS_CONFIG = {
    -- Decay rates per tick (1 tick = 10 minutes)
    decay_rates = {
        hunger = 2.0,      -- Needs food every ~8 hours
        energy = 1.5,      -- Needs sleep every ~11 hours
        social = 0.5,      -- Needs interaction every ~33 hours
        money = 0.0,       -- Only decreases when spending
        entertainment = 1.0,
        safety = 0.3,
        purpose = 0.2
    },
    
    -- Critical thresholds (NPC will prioritize this need)
    critical_thresholds = {
        hunger = 20,
        energy = 15,
        social = 25,
        money = 10,
        entertainment = 20,
        safety = 30,
        purpose = 15
    },
    
    -- Satisfaction amounts by activity
    satisfiers = {
        eat = { hunger = 60, energy = 5 },
        sleep = { energy = 80, hunger = -5 },
        work = { money = 20, purpose = 15, energy = -10 },
        socialize = { social = 40, entertainment = 10 },
        entertain = { entertainment = 50, social = 10, energy = -5 },
        rest = { energy = 20, entertainment = 5 },
        shop = { entertainment = 15, money = -10 },
        pray = { purpose = 30, social = 10 },
        exercise = { energy = -15, purpose = 10, hunger = 5 }
    }
}

-- =============================================================================
-- NEEDS STATE
-- =============================================================================

-- Store needs state for all NPCs
NPC_NEEDS = {}

-- Initialize needs for an NPC
function init_npc_needs(npc_id, personality)
    personality = personality or {}
    
    -- Base needs influenced by personality
    local base_hunger = 70 + (math.random() * 20)
    local base_energy = 80 + (math.random() * 15)
    local base_social = 50 + (math.random() * 30)
    
    -- Personality modifiers
    if personality.extraversion then
        base_social = base_social + (personality.extraversion * 20)
    end
    if personality.neuroticism then
        -- Neurotic NPCs have lower safety baseline
        base_social = base_social - (personality.neuroticism * 10)
    end
    
    NPC_NEEDS[npc_id] = {
        hunger = math.min(100, base_hunger),
        energy = math.min(100, base_energy),
        social = math.min(100, base_social),
        money = 40 + (math.random() * 30),
        entertainment = 50 + (math.random() * 30),
        safety = 70 + (math.random() * 20),
        purpose = 60 + (math.random() * 25),
        
        -- Tracking
        last_activity = "idle",
        activities_today = {},
        mood = "neutral"
    }
    
    return NPC_NEEDS[npc_id]
end

-- Get or initialize NPC needs
function get_npc_needs(npc_id, personality)
    if not NPC_NEEDS[npc_id] then
        init_npc_needs(npc_id, personality)
    end
    return NPC_NEEDS[npc_id]
end

-- =============================================================================
-- NEEDS DECAY
-- =============================================================================

-- Decay needs for all NPCs (called on CRON tick)
function decay_all_needs()
    for npc_id, needs in pairs(NPC_NEEDS) do
        for need_name, decay_rate in pairs(NEEDS_CONFIG.decay_rates) do
            if needs[need_name] then
                needs[need_name] = math.max(0, needs[need_name] - decay_rate)
            end
        end
        
        -- Update mood based on average needs
        needs.mood = calculate_mood(needs)
    end
    
    return #NPC_NEEDS
end

-- Decay needs for a single NPC
function decay_npc_needs(npc_id)
    local needs = NPC_NEEDS[npc_id]
    if not needs then return nil end
    
    for need_name, decay_rate in pairs(NEEDS_CONFIG.decay_rates) do
        if needs[need_name] then
            needs[need_name] = math.max(0, needs[need_name] - decay_rate)
        end
    end
    
    needs.mood = calculate_mood(needs)
    return needs
end

-- =============================================================================
-- MOOD CALCULATION
-- =============================================================================

function calculate_mood(needs)
    local critical_count = 0
    local total_satisfaction = 0
    local need_count = 0
    
    for need_name, threshold in pairs(NEEDS_CONFIG.critical_thresholds) do
        if needs[need_name] then
            total_satisfaction = total_satisfaction + needs[need_name]
            need_count = need_count + 1
            
            if needs[need_name] < threshold then
                critical_count = critical_count + 1
            end
        end
    end
    
    local avg_satisfaction = need_count > 0 and (total_satisfaction / need_count) or 50
    
    -- Determine mood
    if critical_count >= 3 then
        return "desperate"
    elseif critical_count >= 2 then
        return "stressed"
    elseif critical_count >= 1 then
        return "uneasy"
    elseif avg_satisfaction >= 80 then
        return "content"
    elseif avg_satisfaction >= 60 then
        return "neutral"
    else
        return "dissatisfied"
    end
end

-- =============================================================================
-- DECISION MAKING (Egregoria-style)
-- =============================================================================

-- Find the most urgent need
function get_urgent_need(npc_id)
    local needs = NPC_NEEDS[npc_id]
    if not needs then return nil end
    
    local most_urgent = nil
    local lowest_value = 101
    
    for need_name, threshold in pairs(NEEDS_CONFIG.critical_thresholds) do
        local value = needs[need_name] or 100
        
        -- Check if below threshold and lower than current urgent
        if value < threshold and value < lowest_value then
            lowest_value = value
            most_urgent = need_name
        end
    end
    
    return most_urgent, lowest_value
end

-- Decide what action an NPC should take based on needs
function decide_action(npc_id, world_state)
    local needs = get_npc_needs(npc_id)
    local urgent_need, urgency = get_urgent_need(npc_id)
    
    world_state = world_state or {}
    
    -- Priority actions based on urgent needs
    if urgent_need == "hunger" then
        return {
            action = "eat",
            target = world_state.nearest_restaurant or "cantina",
            urgency = urgency,
            reason = "NPC is hungry"
        }
    elseif urgent_need == "energy" then
        return {
            action = "sleep",
            target = world_state.npc_home or "home",
            urgency = urgency,
            reason = "NPC is tired"
        }
    elseif urgent_need == "social" then
        return {
            action = "socialize",
            target = world_state.social_venue or "plaza",
            urgency = urgency,
            reason = "NPC feels lonely"
        }
    elseif urgent_need == "money" then
        return {
            action = "work",
            target = world_state.npc_workplace or "office",
            urgency = urgency,
            reason = "NPC needs money"
        }
    elseif urgent_need == "entertainment" then
        return {
            action = "entertain",
            target = world_state.entertainment_venue or "bar",
            urgency = urgency,
            reason = "NPC is bored"
        }
    elseif urgent_need == "safety" then
        return {
            action = "rest",
            target = world_state.npc_home or "home",
            urgency = urgency,
            reason = "NPC feels unsafe"
        }
    elseif urgent_need == "purpose" then
        return {
            action = "work",
            target = world_state.npc_workplace or "office",
            urgency = urgency,
            reason = "NPC lacks purpose"
        }
    end
    
    -- No urgent need - follow schedule or idle
    return {
        action = "idle",
        target = nil,
        urgency = 100,
        reason = "No urgent needs"
    }
end

-- =============================================================================
-- ACTIVITY EFFECTS
-- =============================================================================

-- Apply the effects of an activity on needs
function apply_activity(npc_id, activity_name)
    local needs = get_npc_needs(npc_id)
    local effects = NEEDS_CONFIG.satisfiers[activity_name]
    
    if not effects then
        return needs
    end
    
    -- Apply each effect
    for need_name, change in pairs(effects) do
        if needs[need_name] then
            needs[need_name] = math.max(0, math.min(100, needs[need_name] + change))
        end
    end
    
    needs.last_activity = activity_name
    table.insert(needs.activities_today, activity_name)
    needs.mood = calculate_mood(needs)
    
    return needs
end

-- =============================================================================
-- RELATIONSHIP INFLUENCE
-- =============================================================================

RELATIONSHIP_TRUST_MODIFIERS = {
    ally = 0.9,
    friend = 0.85,
    mentor = 0.8,
    student = 0.75,
    family = 0.95,
    lover = 0.98,
    contact = 0.5,
    client = 0.6,
    rival = 0.3,
    enemy = 0.1,
    stranger = 0.4
}

-- Calculate social satisfaction from interaction
function calculate_social_gain(npc_id, other_npc_id, relationship_type)
    local base_gain = 20
    local modifier = RELATIONSHIP_TRUST_MODIFIERS[relationship_type] or 0.5
    
    -- Social gain is higher with closer relationships
    local gain = base_gain * modifier
    
    -- Apply to NPC needs
    local needs = get_npc_needs(npc_id)
    needs.social = math.min(100, needs.social + gain)
    
    return gain
end

-- =============================================================================
-- BATCH OPERATIONS
-- =============================================================================

-- Get summary of all NPC moods
function get_mood_distribution()
    local distribution = {
        desperate = 0,
        stressed = 0,
        uneasy = 0,
        neutral = 0,
        dissatisfied = 0,
        content = 0
    }
    
    for _, needs in pairs(NPC_NEEDS) do
        local mood = needs.mood or "neutral"
        distribution[mood] = (distribution[mood] or 0) + 1
    end
    
    return distribution
end

-- Get NPCs with critical needs
function get_critical_npcs()
    local critical = {}
    
    for npc_id, needs in pairs(NPC_NEEDS) do
        local urgent, value = get_urgent_need(npc_id)
        if urgent then
            table.insert(critical, {
                npc_id = npc_id,
                urgent_need = urgent,
                value = value,
                mood = needs.mood
            })
        end
    end
    
    return critical
end

-- Reset all needs (for testing)
function reset_all_needs()
    NPC_NEEDS = {}
end

-- =============================================================================
-- AO MESSAGE HANDLERS
-- =============================================================================

-- Handler: Get NPC needs
Handlers.add("GetNpcNeeds", Handlers.utils.hasMatchingTag("Action", "GetNpcNeeds"),
    function(msg)
        local npc_id = msg.Tags["NpcId"]
        local needs = get_npc_needs(npc_id)
        
        ao.send({
            Target = msg.From,
            Data = json.encode(needs)
        })
    end
)

-- Handler: Decide action for NPC
Handlers.add("DecideAction", Handlers.utils.hasMatchingTag("Action", "DecideAction"),
    function(msg)
        local npc_id = msg.Tags["NpcId"]
        local world_state = msg.Data and json.decode(msg.Data) or {}
        local action = decide_action(npc_id, world_state)
        
        ao.send({
            Target = msg.From,
            Data = json.encode(action)
        })
    end
)

-- Handler: Apply activity
Handlers.add("ApplyActivity", Handlers.utils.hasMatchingTag("Action", "ApplyActivity"),
    function(msg)
        local npc_id = msg.Tags["NpcId"]
        local activity = msg.Tags["Activity"]
        local needs = apply_activity(npc_id, activity)
        
        ao.send({
            Target = msg.From,
            Data = json.encode({
                success = true,
                needs = needs
            })
        })
    end
)

-- Handler: Get mood distribution
Handlers.add("GetMoodDistribution", Handlers.utils.hasMatchingTag("Action", "GetMoodDistribution"),
    function(msg)
        local distribution = get_mood_distribution()
        
        ao.send({
            Target = msg.From,
            Data = json.encode(distribution)
        })
    end
)

-- Handler: Decay all needs (called by CRON)
Handlers.add("DecayNeeds", Handlers.utils.hasMatchingTag("Action", "DecayNeeds"),
    function(msg)
        local count = decay_all_needs()
        
        ao.send({
            Target = msg.From,
            Data = json.encode({
                success = true,
                npcs_processed = count
            })
        })
    end
)

-- =============================================================================
-- EXPORT
-- =============================================================================

return {
    -- Configuration
    NEEDS_CONFIG = NEEDS_CONFIG,
    
    -- State
    NPC_NEEDS = NPC_NEEDS,
    
    -- Core functions
    init_npc_needs = init_npc_needs,
    get_npc_needs = get_npc_needs,
    decay_npc_needs = decay_npc_needs,
    decay_all_needs = decay_all_needs,
    
    -- Decision making
    calculate_mood = calculate_mood,
    get_urgent_need = get_urgent_need,
    decide_action = decide_action,
    
    -- Activities
    apply_activity = apply_activity,
    calculate_social_gain = calculate_social_gain,
    
    -- Batch operations
    get_mood_distribution = get_mood_distribution,
    get_critical_npcs = get_critical_npcs,
    reset_all_needs = reset_all_needs
}

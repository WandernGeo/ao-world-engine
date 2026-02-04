--[[
  AO World Engine - Social Dynamics Process
  
  Lua port of social_dynamics.py for on-chain relationship tracking.
  Handles:
  - Trust and relationship tracking
  - Meeting history and frequency
  - Group formation and social networks
  - Gossip propagation
  
  Uses deterministic computation for verifiable state.
]]--

local json = json or require("json")
local crypto = crypto or require("crypto")

-- =============================================================================
-- GLOBAL STATE
-- =============================================================================

-- Relationships: { "npc_a:npc_b": { trust, meetings, type, last_tick } }
Relationships = Relationships or {}

-- Reputation: { npc_id: { faction_id: score } }
Reputation = Reputation or {}

-- Groups: { group_id: { members, type, formed_tick } }
Groups = Groups or {}

-- Gossip: { gossip_id: { content, origin, spread_to, tick } }
ActiveGossip = ActiveGossip or {}

-- Configuration from codec_19
TRUST_BASE = 0.1
TRUST_PER_MEETING = 0.01
TRUST_MAX = 1.0
TRUST_DECAY_RATE = 0.001  -- Per day without meeting

MEETING_THRESHOLDS = {
    acquaintance = 5,
    colleague = 15,
    friend = 30,
    close_friend = 60,
    confidant = 100
}

RELATIONSHIP_THRESHOLDS = {
    stranger = 0.0,
    acquaintance = 0.2,
    colleague = 0.35,
    friend = 0.5,
    close_friend = 0.7,
    confidant = 0.85
}

GROUP_TYPES = {
    workplace = { min_members = 2, max_members = 20 },
    social = { min_members = 2, max_members = 10 },
    family = { min_members = 2, max_members = 15 },
    faction = { min_members = 3, max_members = 50 },
    conspiracy = { min_members = 2, max_members = 5 }
}

GOSSIP_SPREAD_CHANCE = 0.3
GOSSIP_DECAY_TICKS = 720  -- 3 days

-- =============================================================================
-- DETERMINISTIC UTILITIES
-- =============================================================================

function hash_to_number(str, max)
    local hash = crypto.digest.sha256(str)
    return tonumber(hash:sub(1, 8), 16) % max
end

function seeded_chance(probability, seed)
    local roll = hash_to_number(seed, 10000) / 10000
    return roll < probability
end

function make_relationship_key(npc_a, npc_b)
    -- Alphabetical order for consistency
    if npc_a < npc_b then
        return npc_a .. ":" .. npc_b
    else
        return npc_b .. ":" .. npc_a
    end
end

-- =============================================================================
-- RELATIONSHIP FUNCTIONS
-- =============================================================================

function get_relationship(npc_a, npc_b)
    local key = make_relationship_key(npc_a, npc_b)
    return Relationships[key] or {
        trust = TRUST_BASE,
        meetings = 0,
        type = "stranger",
        last_tick = 0,
        interactions = {}
    }
end

function get_relationship_type(trust, meetings)
    local type_by_trust = "stranger"
    local type_by_meetings = "stranger"
    
    -- Check trust thresholds
    for level, threshold in pairs(RELATIONSHIP_THRESHOLDS) do
        if trust >= threshold then
            type_by_trust = level
        end
    end
    
    -- Check meeting thresholds
    for level, threshold in pairs(MEETING_THRESHOLDS) do
        if meetings >= threshold then
            type_by_meetings = level
        end
    end
    
    -- Return the lower of the two (need both to progress)
    local priority = {"stranger", "acquaintance", "colleague", "friend", "close_friend", "confidant"}
    local trust_idx = 1
    local meeting_idx = 1
    
    for i, level in ipairs(priority) do
        if level == type_by_trust then trust_idx = i end
        if level == type_by_meetings then meeting_idx = i end
    end
    
    return priority[math.min(trust_idx, meeting_idx)]
end

function track_meeting(npc_a, npc_b, tick, context)
    local key = make_relationship_key(npc_a, npc_b)
    local rel = get_relationship(npc_a, npc_b)
    
    -- Increment meetings
    rel.meetings = rel.meetings + 1
    
    -- Increase trust based on meeting
    local trust_gain = TRUST_PER_MEETING
    
    -- Context modifiers
    if context then
        if context.shared_experience then
            trust_gain = trust_gain * 1.5
        end
        if context.helped then
            trust_gain = trust_gain * 2
        end
        if context.conflict then
            trust_gain = -0.05  -- Trust decrease
        end
    end
    
    rel.trust = math.min(TRUST_MAX, rel.trust + trust_gain)
    rel.last_tick = tick
    
    -- Update relationship type
    rel.type = get_relationship_type(rel.trust, rel.meetings)
    
    -- Store interaction
    table.insert(rel.interactions, {
        tick = tick,
        context = context
    })
    
    -- Keep last 50 interactions
    while #rel.interactions > 50 do
        table.remove(rel.interactions, 1)
    end
    
    Relationships[key] = rel
    
    return rel
end

function update_trust_from_interaction(npc_a, npc_b, interaction_type, tick)
    local trust_deltas = {
        positive_chat = 0.02,
        gift = 0.05,
        help = 0.08,
        shared_secret = 0.1,
        betrayal = -0.3,
        insult = -0.1,
        ignore = -0.02,
        conflict = -0.15
    }
    
    local delta = trust_deltas[interaction_type] or 0
    local key = make_relationship_key(npc_a, npc_b)
    local rel = get_relationship(npc_a, npc_b)
    
    rel.trust = math.max(0, math.min(TRUST_MAX, rel.trust + delta))
    rel.last_tick = tick
    rel.type = get_relationship_type(rel.trust, rel.meetings)
    
    Relationships[key] = rel
    
    return rel
end

function decay_relationships(current_tick, days_threshold)
    local threshold_ticks = days_threshold * 240  -- Ticks per day
    
    for key, rel in pairs(Relationships) do
        local ticks_since_meeting = current_tick - rel.last_tick
        
        if ticks_since_meeting > threshold_ticks then
            local days_inactive = ticks_since_meeting / 240
            local decay = TRUST_DECAY_RATE * days_inactive
            rel.trust = math.max(TRUST_BASE, rel.trust - decay)
            rel.type = get_relationship_type(rel.trust, rel.meetings)
            Relationships[key] = rel
        end
    end
end

-- =============================================================================
-- SOCIAL NETWORK ANALYSIS
-- =============================================================================

function get_npc_social_summary(npc_id)
    local summary = {
        relationships = {},
        total_connections = 0,
        by_type = {
            stranger = 0,
            acquaintance = 0,
            colleague = 0,
            friend = 0,
            close_friend = 0,
            confidant = 0
        },
        groups = {},
        avg_trust = 0
    }
    
    local total_trust = 0
    
    for key, rel in pairs(Relationships) do
        local parts = {}
        for part in string.gmatch(key, "[^:]+") do
            table.insert(parts, part)
        end
        
        local other_id = nil
        if parts[1] == npc_id then other_id = parts[2]
        elseif parts[2] == npc_id then other_id = parts[1]
        end
        
        if other_id then
            summary.total_connections = summary.total_connections + 1
            summary.by_type[rel.type] = (summary.by_type[rel.type] or 0) + 1
            total_trust = total_trust + rel.trust
            
            table.insert(summary.relationships, {
                npc_id = other_id,
                trust = rel.trust,
                type = rel.type,
                meetings = rel.meetings
            })
        end
    end
    
    if summary.total_connections > 0 then
        summary.avg_trust = total_trust / summary.total_connections
    end
    
    -- Find groups this NPC belongs to
    for group_id, group in pairs(Groups) do
        for _, member in ipairs(group.members) do
            if member == npc_id then
                table.insert(summary.groups, {
                    group_id = group_id,
                    type = group.type,
                    size = #group.members
                })
                break
            end
        end
    end
    
    return summary
end

function find_potential_groups(npc_ids, tick)
    local potential_groups = {}
    
    -- Find clusters of NPCs with mutual high trust
    for i, npc_a in ipairs(npc_ids) do
        for j, npc_b in ipairs(npc_ids) do
            if i < j then
                local rel_ab = get_relationship(npc_a, npc_b)
                
                if rel_ab.trust >= RELATIONSHIP_THRESHOLDS.colleague then
                    -- Check for third mutual connection
                    for k, npc_c in ipairs(npc_ids) do
                        if k ~= i and k ~= j then
                            local rel_ac = get_relationship(npc_a, npc_c)
                            local rel_bc = get_relationship(npc_b, npc_c)
                            
                            if rel_ac.trust >= RELATIONSHIP_THRESHOLDS.acquaintance and
                               rel_bc.trust >= RELATIONSHIP_THRESHOLDS.acquaintance then
                                -- Potential social group found
                                local group_id = "grp_" .. npc_a .. "_" .. npc_b .. "_" .. npc_c
                                
                                table.insert(potential_groups, {
                                    id = group_id,
                                    members = {npc_a, npc_b, npc_c},
                                    avg_trust = (rel_ab.trust + rel_ac.trust + rel_bc.trust) / 3,
                                    type = "social"
                                })
                            end
                        end
                    end
                end
            end
        end
    end
    
    return potential_groups
end

-- =============================================================================
-- GOSSIP SYSTEM
-- =============================================================================

function create_gossip(origin_npc, content, tick)
    local gossip_id = "gsp_" .. origin_npc .. "_" .. tick
    
    ActiveGossip[gossip_id] = {
        id = gossip_id,
        origin = origin_npc,
        content = content,
        spread_to = { origin_npc },
        created_tick = tick,
        expires_tick = tick + GOSSIP_DECAY_TICKS
    }
    
    return gossip_id
end

function spread_gossip(gossip_id, from_npc, to_npc, tick)
    local gossip = ActiveGossip[gossip_id]
    if not gossip then return false end
    
    -- Check if already knows
    for _, npc in ipairs(gossip.spread_to) do
        if npc == to_npc then return false end
    end
    
    -- Check spread chance based on relationship
    local rel = get_relationship(from_npc, to_npc)
    local spread_chance = GOSSIP_SPREAD_CHANCE * (1 + rel.trust)
    
    if seeded_chance(spread_chance, gossip_id .. "_" .. to_npc .. "_" .. tick) then
        table.insert(gossip.spread_to, to_npc)
        return true
    end
    
    return false
end

function get_npc_gossip(npc_id)
    local known_gossip = {}
    
    for gossip_id, gossip in pairs(ActiveGossip) do
        for _, knower in ipairs(gossip.spread_to) do
            if knower == npc_id then
                table.insert(known_gossip, gossip)
                break
            end
        end
    end
    
    return known_gossip
end

function update_gossip(current_tick)
    local still_active = {}
    
    for gossip_id, gossip in pairs(ActiveGossip) do
        if current_tick < gossip.expires_tick then
            still_active[gossip_id] = gossip
        end
    end
    
    ActiveGossip = still_active
end

-- =============================================================================
-- REPUTATION
-- =============================================================================

function get_reputation(npc_id, faction_id)
    if Reputation[npc_id] and Reputation[npc_id][faction_id] then
        return Reputation[npc_id][faction_id]
    end
    return 0  -- Neutral
end

function modify_reputation(npc_id, faction_id, delta)
    if not Reputation[npc_id] then
        Reputation[npc_id] = {}
    end
    
    local current = Reputation[npc_id][faction_id] or 0
    Reputation[npc_id][faction_id] = math.max(-1, math.min(1, current + delta))
    
    return Reputation[npc_id][faction_id]
end

-- =============================================================================
-- HANDLERS
-- =============================================================================

-- Track a meeting between NPCs
Handlers.add("track-meeting", Handlers.utils.hasMatchingTag("Action", "track-meeting"), function(msg)
    local data = json.decode(msg.Data)
    local rel = track_meeting(data.npc_a, data.npc_b, data.tick, data.context)
    
    ao.send({
        Target = msg.From,
        Action = "meeting-tracked",
        Data = json.encode(rel)
    })
end)

-- Update trust from interaction
Handlers.add("update-trust", Handlers.utils.hasMatchingTag("Action", "update-trust"), function(msg)
    local data = json.decode(msg.Data)
    local rel = update_trust_from_interaction(
        data.npc_a, data.npc_b, data.interaction_type, data.tick
    )
    
    ao.send({
        Target = msg.From,
        Action = "trust-updated",
        Data = json.encode(rel)
    })
end)

-- Query NPC social network
Handlers.add("get-social-summary", Handlers.utils.hasMatchingTag("Action", "get-social-summary"), function(msg)
    local data = json.decode(msg.Data)
    local summary = get_npc_social_summary(data.npc_id)
    
    ao.send({
        Target = msg.From,
        Action = "social-summary",
        Data = json.encode(summary)
    })
end)

-- Get relationship between two NPCs
Handlers.add("get-relationship", Handlers.utils.hasMatchingTag("Action", "get-relationship"), function(msg)
    local data = json.decode(msg.Data)
    local rel = get_relationship(data.npc_a, data.npc_b)
    
    ao.send({
        Target = msg.From,
        Action = "relationship-response",
        Data = json.encode(rel)
    })
end)

-- Create gossip
Handlers.add("create-gossip", Handlers.utils.hasMatchingTag("Action", "create-gossip"), function(msg)
    local data = json.decode(msg.Data)
    local gossip_id = create_gossip(data.origin, data.content, data.tick)
    
    ao.send({
        Target = msg.From,
        Action = "gossip-created",
        Data = json.encode({ gossip_id = gossip_id })
    })
end)

-- Spread gossip
Handlers.add("spread-gossip", Handlers.utils.hasMatchingTag("Action", "spread-gossip"), function(msg)
    local data = json.decode(msg.Data)
    local success = spread_gossip(data.gossip_id, data.from, data.to, data.tick)
    
    ao.send({
        Target = msg.From,
        Action = "gossip-spread-result",
        Data = json.encode({ success = success })
    })
end)

-- CRON: Periodic maintenance
Handlers.add("cron-social", Handlers.utils.hasMatchingTag("Action", "Cron"), function(msg)
    local data = json.decode(msg.Data) or {}
    local tick = data.tick or 0
    
    -- Only process daily (every 240 ticks)
    if tick % 240 ~= 0 then return end
    
    -- Decay inactive relationships
    decay_relationships(tick, 7)  -- 7 days threshold
    
    -- Clean up expired gossip
    update_gossip(tick)
end)

-- =============================================================================
-- MODULE EXPORT
-- =============================================================================

return {
    get_relationship = get_relationship,
    track_meeting = track_meeting,
    update_trust_from_interaction = update_trust_from_interaction,
    get_npc_social_summary = get_npc_social_summary,
    find_potential_groups = find_potential_groups,
    create_gossip = create_gossip,
    spread_gossip = spread_gossip,
    get_reputation = get_reputation,
    modify_reputation = modify_reputation
}

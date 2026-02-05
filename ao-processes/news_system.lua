--[[
  AO World Engine - News & Information Propagation
  
  Pluggable system for:
  - News creation (video, written, gossip)
  - Distance + network-based propagation
  - NPC receivers based on faction/location
  - Information asymmetry
]]--

local json = require("json")

-- =============================================================================
-- NEWS TYPES REGISTRY (Pluggable)
-- =============================================================================

NEWS_TYPES = {
    video_broadcast = {
        name = "Video Broadcast",
        reach = "global",          -- all NPCs in range
        decay_rate = 0.1,          -- how fast it becomes old news
        trust_modifier = 0.8,      -- 80% believable
        requires_tech = true,      -- need screen/device to receive
        propagation_speed = 1.0    -- instant
    },
    written_news = {
        name = "Written News",
        reach = "local",
        decay_rate = 0.05,
        trust_modifier = 0.7,
        requires_tech = false,
        propagation_speed = 0.5   -- slower spread
    },
    gossip = {
        name = "Gossip",
        reach = "network",         -- spreads through social connections
        decay_rate = 0.2,
        trust_modifier = 0.4,      -- less believable
        requires_tech = false,
        propagation_speed = 0.3,
        distortion_rate = 0.15    -- info changes as it spreads
    },
    official_announcement = {
        name = "Official Announcement",
        reach = "faction",
        decay_rate = 0.02,
        trust_modifier = 0.9,
        requires_tech = false,
        propagation_speed = 0.8
    },
    underground_intel = {
        name = "Underground Intel",
        reach = "network",
        decay_rate = 0.15,
        trust_modifier = 0.6,
        requires_tech = false,
        propagation_speed = 0.4,
        faction_only = {"underground", "resistance"}
    },
    temple_sermon = {
        name = "Temple Sermon",
        reach = "location",
        decay_rate = 0.1,
        trust_modifier = 0.95,  -- High trust for believers
        requires_tech = false,
        propagation_speed = 0.2,
        faction_only = {"temple_of_signal"}
    }
}

-- Register custom news type
function register_news_type(type_id, config)
    NEWS_TYPES[type_id] = config
    return NEWS_TYPES[type_id]
end

-- =============================================================================
-- NEWS ITEMS
-- =============================================================================

NEWS_ITEMS = {}
NEWS_COUNTER = 0

-- Create a news item
function create_news(config)
    NEWS_COUNTER = NEWS_COUNTER + 1
    
    local news = {
        id = "NEWS_" .. NEWS_COUNTER,
        type = config.type or "gossip",
        headline = config.headline,
        content = config.content,
        source_npc = config.source_npc,
        source_faction = config.source_faction,
        source_location = config.source_location,
        
        -- Targeting
        target_factions = config.target_factions,  -- nil = all
        target_districts = config.target_districts,
        
        -- About (for gossip/intel)
        about_npc = config.about_npc,
        about_faction = config.about_faction,
        about_location = config.about_location,
        
        -- Propagation state
        created_at = os.time(),
        created_tick = WorldTick or 0,
        freshness = 100,
        reached_npcs = {},
        distortions = {},  -- How content changed during spread
        
        -- Flags
        is_true = config.is_true ~= false,  -- Default true
        is_secret = config.is_secret or false,
        priority = config.priority or 50
    }
    
    NEWS_ITEMS[news.id] = news
    return news
end

-- =============================================================================
-- PROPAGATION LOGIC
-- =============================================================================

-- Track which NPCs know what
NPC_KNOWLEDGE = {}  -- npc_id -> { news_id -> knowledge_entry }

-- Initialize NPC knowledge
function init_npc_knowledge(npc_id)
    if not NPC_KNOWLEDGE[npc_id] then
        NPC_KNOWLEDGE[npc_id] = {}
    end
    return NPC_KNOWLEDGE[npc_id]
end

-- Check if NPC can receive this news type
function can_receive_news(npc_id, news)
    local news_type = NEWS_TYPES[news.type]
    if not news_type then return true end
    
    -- Check tech requirement
    if news_type.requires_tech then
        -- TODO: Check if NPC has tech access
        -- For now, assume yes if in certain districts
    end
    
    -- Check faction restrictions
    if news_type.faction_only then
        local npc_faction = get_npc_faction and get_npc_faction(npc_id)
        if npc_faction then
            local allowed = false
            for _, f in ipairs(news_type.faction_only) do
                if f == npc_faction then
                    allowed = true
                    break
                end
            end
            if not allowed then return false end
        end
    end
    
    return true
end

-- Calculate if news reaches an NPC based on distance
function calculate_reach(news, npc_id, npc_location, source_location)
    local news_type = NEWS_TYPES[news.type]
    if not news_type then return false end
    
    local reach = news_type.reach
    
    if reach == "global" then
        return true
    elseif reach == "local" then
        -- Same district
        return npc_location and npc_location.district == source_location.district
    elseif reach == "location" then
        -- Same building
        return npc_location and npc_location.building == source_location.building
    elseif reach == "faction" then
        -- Faction members only
        local npc_faction = get_npc_faction and get_npc_faction(npc_id)
        return npc_faction == news.source_faction
    elseif reach == "network" then
        -- Spread through social connections (handled separately)
        return false  -- Requires network propagation
    end
    
    return false
end

-- Deliver news to an NPC
function deliver_news(npc_id, news_id, via)
    local knowledge = init_npc_knowledge(npc_id)
    local news = NEWS_ITEMS[news_id]
    
    if not news then return false end
    if knowledge[news_id] then return false end  -- Already knows
    if not can_receive_news(npc_id, news) then return false end
    
    -- Create knowledge entry
    knowledge[news_id] = {
        news_id = news_id,
        received_at = os.time(),
        received_tick = WorldTick or 0,
        via = via or "direct",  -- "direct", "gossip", "broadcast"
        belief = calculate_belief(news, npc_id),
        shared_with = {},
        distortion = nil  -- If gossip, may be distorted
    }
    
    -- Mark in news item
    news.reached_npcs[npc_id] = true
    
    return true
end

-- Calculate how much an NPC believes the news
function calculate_belief(news, npc_id)
    local news_type = NEWS_TYPES[news.type]
    local base_trust = news_type and news_type.trust_modifier or 0.5
    
    -- Faction modifiers
    local npc_faction = get_npc_faction and get_npc_faction(npc_id)
    if npc_faction then
        if npc_faction == news.source_faction then
            base_trust = base_trust * 1.3  -- Trust own faction more
        elseif are_rivals and are_rivals(npc_faction, news.source_faction) then
            base_trust = base_trust * 0.5  -- Distrust rivals
        end
    end
    
    -- Is it about someone they know?
    -- TODO: Check relationships
    
    return math.min(1.0, base_trust)
end

-- =============================================================================
-- NETWORK PROPAGATION
-- =============================================================================

-- Spread gossip through social network
function propagate_gossip(news_id, from_npc_id, available_npcs)
    local news = NEWS_ITEMS[news_id]
    if not news then return {} end
    
    local news_type = NEWS_TYPES[news.type]
    if not news_type then return {} end
    
    local spread_to = {}
    
    for _, npc_id in ipairs(available_npcs) do
        -- Skip if already knows
        if NPC_KNOWLEDGE[npc_id] and NPC_KNOWLEDGE[npc_id][news_id] then
            goto continue
        end
        
        -- Check if they're connected (same location doesn't mean they talk)
        local will_share = false
        
        -- Base chance affected by propagation speed
        local base_chance = news_type.propagation_speed * 0.3
        
        -- Relationship check (if available)
        -- TODO: Check actual relationship
        
        -- Faction check
        local from_faction = get_npc_faction and get_npc_faction(from_npc_id)
        local to_faction = get_npc_faction and get_npc_faction(npc_id)
        
        if from_faction == to_faction then
            base_chance = base_chance * 1.5  -- More likely to share within faction
        elseif from_faction and to_faction and are_rivals and are_rivals(from_faction, to_faction) then
            base_chance = base_chance * 0.1  -- Unlikely to share with rivals
        end
        
        if math.random() < base_chance then
            will_share = true
        end
        
        if will_share then
            -- Apply distortion for gossip
            local distorted_content = news.content
            if news_type.distortion_rate and math.random() < news_type.distortion_rate then
                distorted_content = distort_content(news.content, news_id)
            end
            
            deliver_news(npc_id, news_id, "gossip")
            table.insert(spread_to, npc_id)
        end
        
        ::continue::
    end
    
    return spread_to
end

-- Distort content as gossip spreads
function distort_content(original_content, news_id)
    -- Track distortion
    local news = NEWS_ITEMS[news_id]
    if not news.distortions then
        news.distortions = {}
    end
    
    local distortion_count = #news.distortions + 1
    local distorted = original_content .. " [distorted #" .. distortion_count .. "]"
    
    table.insert(news.distortions, distorted)
    return distorted
end

-- =============================================================================
-- NEWS AGING
-- =============================================================================

-- Age all news (call on tick)
function age_all_news()
    for news_id, news in pairs(NEWS_ITEMS) do
        local news_type = NEWS_TYPES[news.type]
        if news_type and news_type.decay_rate then
            news.freshness = math.max(0, news.freshness - news_type.decay_rate)
        end
    end
end

-- Get fresh news for an NPC
function get_fresh_news_for_npc(npc_id, min_freshness)
    min_freshness = min_freshness or 50
    local knowledge = NPC_KNOWLEDGE[npc_id] or {}
    local fresh = {}
    
    for news_id, k in pairs(knowledge) do
        local news = NEWS_ITEMS[news_id]
        if news and news.freshness >= min_freshness then
            table.insert(fresh, {
                news = news,
                knowledge = k
            })
        end
    end
    
    return fresh
end

-- =============================================================================
-- REPORTERS & NEWSCASTERS (Job Integration)
-- =============================================================================

REPORTERS = {}

function register_reporter(npc_id, config)
    REPORTERS[npc_id] = {
        npc_id = npc_id,
        outlet = config.outlet or "independent",
        specialty = config.specialty,  -- "crime", "politics", "tech", etc.
        faction_bias = config.faction_bias,
        credibility = config.credibility or 0.7,
        followers = config.followers or {}
    }
    return REPORTERS[npc_id]
end

-- Reporter creates news
function reporter_publish(reporter_npc_id, story_config)
    local reporter = REPORTERS[reporter_npc_id]
    if not reporter then return nil end
    
    local news = create_news({
        type = story_config.video and "video_broadcast" or "written_news",
        headline = story_config.headline,
        content = story_config.content,
        source_npc = reporter_npc_id,
        source_faction = reporter.faction_bias,
        about_npc = story_config.about_npc,
        about_faction = story_config.about_faction,
        is_true = story_config.is_true,
        priority = reporter.credibility * 100
    })
    
    -- Auto-deliver to followers
    for _, follower_id in ipairs(reporter.followers) do
        deliver_news(follower_id, news.id, "subscription")
    end
    
    return news
end

-- =============================================================================
-- AO MESSAGE HANDLERS
-- =============================================================================

Handlers.add("CreateNews", Handlers.utils.hasMatchingTag("Action", "CreateNews"),
    function(msg)
        local config = json.decode(msg.Data or "{}")
        local news = create_news(config)
        
        ao.send({
            Target = msg.From,
            Data = json.encode(news)
        })
    end
)

Handlers.add("DeliverNews", Handlers.utils.hasMatchingTag("Action", "DeliverNews"),
    function(msg)
        local npc_id = msg.Tags["NpcId"]
        local news_id = msg.Tags["NewsId"]
        local via = msg.Tags["Via"]
        
        local success = deliver_news(npc_id, news_id, via)
        
        ao.send({
            Target = msg.From,
            Data = json.encode({success = success})
        })
    end
)

Handlers.add("GetNpcKnowledge", Handlers.utils.hasMatchingTag("Action", "GetNpcKnowledge"),
    function(msg)
        local npc_id = msg.Tags["NpcId"]
        local knowledge = NPC_KNOWLEDGE[npc_id] or {}
        
        ao.send({
            Target = msg.From,
            Data = json.encode(knowledge)
        })
    end
)

Handlers.add("PropagateGossip", Handlers.utils.hasMatchingTag("Action", "PropagateGossip"),
    function(msg)
        local data = json.decode(msg.Data or "{}")
        local spread_to = propagate_gossip(data.news_id, data.from_npc, data.available_npcs)
        
        ao.send({
            Target = msg.From,
            Data = json.encode({spread_to = spread_to})
        })
    end
)

Handlers.add("RegisterReporter", Handlers.utils.hasMatchingTag("Action", "RegisterReporter"),
    function(msg)
        local npc_id = msg.Tags["NpcId"]
        local config = json.decode(msg.Data or "{}")
        
        local reporter = register_reporter(npc_id, config)
        
        ao.send({
            Target = msg.From,
            Data = json.encode(reporter)
        })
    end
)

-- =============================================================================
-- EXPORT
-- =============================================================================

return {
    -- Types
    NEWS_TYPES = NEWS_TYPES,
    register_news_type = register_news_type,
    
    -- News
    NEWS_ITEMS = NEWS_ITEMS,
    create_news = create_news,
    
    -- Propagation
    NPC_KNOWLEDGE = NPC_KNOWLEDGE,
    deliver_news = deliver_news,
    can_receive_news = can_receive_news,
    calculate_reach = calculate_reach,
    propagate_gossip = propagate_gossip,
    age_all_news = age_all_news,
    
    -- Queries
    get_fresh_news_for_npc = get_fresh_news_for_npc,
    init_npc_knowledge = init_npc_knowledge,
    
    -- Reporters
    REPORTERS = REPORTERS,
    register_reporter = register_reporter,
    reporter_publish = reporter_publish
}

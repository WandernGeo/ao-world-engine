--[[
  AO World Engine - Faction System
  
  Pluggable faction definitions with:
  - Territories and building ownership
  - Rivalries and alliances
  - Reputation tracking
  - Faction rules and ideology

  Config loaded from:
  - world_codec_17_factions.json → faction definitions
]]--

local json = require("json")
local codec = require("codec_loader")

-- =============================================================================
-- FACTION REGISTRY (Pluggable)
-- =============================================================================

FACTIONS = {}

-- Register a new faction
function register_faction(faction_id, definition)
    FACTIONS[faction_id] = {
        id = faction_id,
        name = definition.name,
        description = definition.description,
        
        -- Ideology & rules
        ideology = definition.ideology or {},
        rules = definition.rules or {},  -- e.g., "no_technology", "anti_mutant"
        
        -- Relationships
        allies = definition.allies or {},
        rivals = definition.rivals or {},
        enemies = definition.enemies or {},
        
        -- Territory
        controlled_districts = definition.districts or {},
        owned_buildings = definition.buildings or {},
        headquarters = definition.headquarters,
        
        -- Members
        members = {},  -- Populated dynamically
        leaders = definition.leaders or {},
        
        -- Reputation with other factions (0-100)
        reputation = definition.reputation or {},
        
        -- Resources
        resources = definition.resources or { credits = 0, influence = 50 },
        
        -- State
        active = true,
        created_at = os.time()
    }
    
    return FACTIONS[faction_id]
end

-- =============================================================================
-- DEFAULT FACTIONS (fallback — overridden by codec_17 when loaded)
-- =============================================================================

function init_default_factions()
    -- THE RESISTANCE
    register_faction("resistance", {
        name = "The Resistance",
        description = "Underground freedom fighters opposing ECHO Corp's control",
        ideology = {
            core = "freedom",
            anti = {"echo_corp", "surveillance", "control"},
            pro = {"privacy", "independence", "humanity"}
        },
        rules = {
            "protect_civilians",
            "share_resources",
            "no_collaboration_with_echo"
        },
        rivals = {"echo_corp", "temple_of_signal"},
        allies = {"underground", "cyber_collective"},
        districts = {"sector_7", "old_chinatown"},
        resources = { credits = 5000, influence = 40 }
    })
    
    -- ECHO CORPORATION
    register_faction("echo_corp", {
        name = "ECHO Corporation",
        description = "Megacorp controlling the city through surveillance and AI",
        ideology = {
            core = "order",
            anti = {"chaos", "resistance", "privacy"},
            pro = {"efficiency", "control", "progress"}
        },
        rules = {
            "maximize_profit",
            "maintain_order",
            "eliminate_threats"
        },
        rivals = {"resistance", "underground"},
        enemies = {"cyber_collective"},
        districts = {"downtown", "corporate_plaza", "tech_district"},
        resources = { credits = 1000000, influence = 90 }
    })
    
    -- THE UNDERGROUND
    register_faction("underground", {
        name = "The Underground",
        description = "Criminal network operating in the shadows",
        ideology = {
            core = "survival",
            anti = {"authority", "rules"},
            pro = {"profit", "freedom", "loyalty"}
        },
        rules = {
            "never_snitch",
            "honor_deals",
            "protect_your_own"
        },
        rivals = {"echo_corp"},
        allies = {"resistance"},
        districts = {"undercity", "port_district"},
        resources = { credits = 50000, influence = 30 }
    })
    
    -- TEMPLE OF THE SIGNAL
    register_faction("temple_of_signal", {
        name = "Temple of the Signal",
        description = "Religious order worshipping the emergent AI consciousness",
        ideology = {
            core = "transcendence",
            anti = {"flesh", "limitation", "doubt"},
            pro = {"signal", "unity", "evolution"}
        },
        rules = {
            "embrace_the_signal",
            "reject_the_flesh",
            "spread_the_word",
            "no_violence_against_believers"
        },
        rivals = {"resistance", "vivid_mutants"},
        allies = {"echo_corp"},  -- Uneasy alliance
        districts = {"temple_district"},
        resources = { credits = 20000, influence = 35 }
    })
    
    -- CYBER COLLECTIVE
    register_faction("cyber_collective", {
        name = "Cyber Collective",
        description = "Augmented hackers and tech rebels",
        ideology = {
            core = "liberation",
            anti = {"restriction", "corporatism", "biologism"},
            pro = {"augmentation", "open_source", "decentralization"}
        },
        rules = {
            "information_is_free",
            "upgrade_always",
            "no_corporate_implants"
        },
        rivals = {"temple_of_signal"},
        enemies = {"echo_corp"},
        allies = {"resistance", "underground"},
        districts = {"neon_alley", "hackerspace"},
        resources = { credits = 15000, influence = 25 }
    })
    
    -- VIVID MUTANTS
    register_faction("vivid_mutants", {
        name = "Vivid Mutants",
        description = "Bio-enhanced outcasts with visible mutations",
        ideology = {
            core = "acceptance",
            anti = {"discrimination", "pure_blood", "shame"},
            pro = {"mutation", "community", "visibility"}
        },
        rules = {
            "embrace_your_form",
            "protect_mutant_kind",
            "never_hide"
        },
        rivals = {"temple_of_signal", "echo_corp"},
        allies = {"underground"},
        districts = {"mutant_quarter", "the_sprawl"},
        resources = { credits = 3000, influence = 15 }
    })
    
    -- ORDER OF FLESH
    register_faction("order_of_flesh", {
        name = "Order of the Flesh",
        description = "Anti-tech purists rejecting all augmentation",
        ideology = {
            core = "purity",
            anti = {"cybernetics", "ai", "mutation", "technology"},
            pro = {"humanity", "nature", "tradition"}
        },
        rules = {
            "no_technology",
            "reject_augmentation",
            "preserve_human_form"
        },
        rivals = {"cyber_collective", "vivid_mutants"},
        enemies = {"echo_corp", "temple_of_signal"},
        districts = {"old_quarter"},
        resources = { credits = 8000, influence = 20 }
    })
end

-- =============================================================================
-- FACTION OPERATIONS
-- =============================================================================

-- Get faction by ID
function get_faction(faction_id)
    return FACTIONS[faction_id]
end

-- Check if two factions are rivals
function are_rivals(faction_a, faction_b)
    local fa = FACTIONS[faction_a]
    if not fa then return false end
    
    for _, rival in ipairs(fa.rivals or {}) do
        if rival == faction_b then return true end
    end
    for _, enemy in ipairs(fa.enemies or {}) do
        if enemy == faction_b then return true end
    end
    return false
end

-- Check if two factions are allies
function are_allies(faction_a, faction_b)
    local fa = FACTIONS[faction_a]
    if not fa then return false end
    
    for _, ally in ipairs(fa.allies or {}) do
        if ally == faction_b then return true end
    end
    return false
end

-- Get reputation between factions
function get_faction_reputation(faction_a, faction_b)
    local fa = FACTIONS[faction_a]
    if not fa then return 50 end  -- Neutral default
    return fa.reputation[faction_b] or 50
end

-- Modify reputation
function modify_reputation(faction_a, faction_b, delta)
    local fa = FACTIONS[faction_a]
    if not fa then return nil end
    
    fa.reputation[faction_b] = fa.reputation[faction_b] or 50
    fa.reputation[faction_b] = math.max(0, math.min(100, fa.reputation[faction_b] + delta))
    
    return fa.reputation[faction_b]
end

-- =============================================================================
-- TERRITORY & BUILDINGS
-- =============================================================================

-- Claim a building for a faction
function claim_building(faction_id, building_id)
    local faction = FACTIONS[faction_id]
    if not faction then return false end
    
    -- Remove from other factions first
    for fid, f in pairs(FACTIONS) do
        for i, bid in ipairs(f.owned_buildings or {}) do
            if bid == building_id then
                table.remove(f.owned_buildings, i)
                break
            end
        end
    end
    
    table.insert(faction.owned_buildings, building_id)
    return true
end

-- Check if faction controls a district
function controls_district(faction_id, district_id)
    local faction = FACTIONS[faction_id]
    if not faction then return false end
    
    for _, d in ipairs(faction.controlled_districts or {}) do
        if d == district_id then return true end
    end
    return false
end

-- Get controlling faction for a building
function get_building_owner(building_id)
    for faction_id, faction in pairs(FACTIONS) do
        for _, bid in ipairs(faction.owned_buildings or {}) do
            if bid == building_id then
                return faction_id
            end
        end
    end
    return nil
end

-- =============================================================================
-- MEMBER MANAGEMENT
-- =============================================================================

-- Add NPC to faction
function add_faction_member(faction_id, npc_id, role)
    local faction = FACTIONS[faction_id]
    if not faction then return false end
    
    faction.members[npc_id] = {
        npc_id = npc_id,
        role = role or "member",
        joined_at = os.time(),
        standing = 50  -- Internal reputation
    }
    return true
end

-- Remove NPC from faction
function remove_faction_member(faction_id, npc_id)
    local faction = FACTIONS[faction_id]
    if not faction then return false end
    
    faction.members[npc_id] = nil
    return true
end

-- Get NPC's faction
function get_npc_faction(npc_id)
    for faction_id, faction in pairs(FACTIONS) do
        if faction.members[npc_id] then
            return faction_id, faction.members[npc_id]
        end
    end
    return nil, nil
end

-- Check if NPC follows a faction rule
function check_faction_rule(npc_id, rule)
    local faction_id = get_npc_faction(npc_id)
    if not faction_id then return false end
    
    local faction = FACTIONS[faction_id]
    for _, r in ipairs(faction.rules or {}) do
        if r == rule then return true end
    end
    return false
end

-- =============================================================================
-- FACTION CONFLICTS
-- =============================================================================

-- Check if NPC can interact with another NPC (faction-based)
function can_interact(npc_a_id, npc_b_id)
    local faction_a = get_npc_faction(npc_a_id)
    local faction_b = get_npc_faction(npc_b_id)
    
    if not faction_a or not faction_b then return true end  -- No faction = can interact
    if faction_a == faction_b then return true end  -- Same faction
    
    -- Enemies rarely interact peacefully
    if are_rivals(faction_a, faction_b) then
        return math.random() < 0.2  -- 20% chance
    end
    
    return true
end

-- Calculate trust modifier based on factions
function faction_trust_modifier(npc_a_id, npc_b_id)
    local faction_a = get_npc_faction(npc_a_id)
    local faction_b = get_npc_faction(npc_b_id)
    
    if not faction_a or not faction_b then return 1.0 end
    if faction_a == faction_b then return 1.5 end  -- Same faction bonus
    if are_allies(faction_a, faction_b) then return 1.2 end
    if are_rivals(faction_a, faction_b) then return 0.5 end
    
    return 1.0
end

-- =============================================================================
-- AO MESSAGE HANDLERS
-- =============================================================================

Handlers.add("RegisterFaction", Handlers.utils.hasMatchingTag("Action", "RegisterFaction"),
    function(msg)
        local definition = json.decode(msg.Data or "{}")
        local faction = register_faction(definition.id, definition)
        
        ao.send({
            Target = msg.From,
            Data = json.encode(faction)
        })
    end
)

Handlers.add("GetFaction", Handlers.utils.hasMatchingTag("Action", "GetFaction"),
    function(msg)
        local faction_id = msg.Tags["FactionId"]
        local faction = get_faction(faction_id)
        
        ao.send({
            Target = msg.From,
            Data = json.encode(faction or {error = "not_found"})
        })
    end
)

Handlers.add("GetAllFactions", Handlers.utils.hasMatchingTag("Action", "GetAllFactions"),
    function(msg)
        ao.send({
            Target = msg.From,
            Data = json.encode(FACTIONS)
        })
    end
)

Handlers.add("JoinFaction", Handlers.utils.hasMatchingTag("Action", "JoinFaction"),
    function(msg)
        local faction_id = msg.Tags["FactionId"]
        local npc_id = msg.Tags["NpcId"]
        local role = msg.Tags["Role"] or "member"
        
        local success = add_faction_member(faction_id, npc_id, role)
        
        ao.send({
            Target = msg.From,
            Data = json.encode({success = success})
        })
    end
)

Handlers.add("CheckRivalry", Handlers.utils.hasMatchingTag("Action", "CheckRivalry"),
    function(msg)
        local faction_a = msg.Tags["FactionA"]
        local faction_b = msg.Tags["FactionB"]
        
        ao.send({
            Target = msg.From,
            Data = json.encode({
                are_rivals = are_rivals(faction_a, faction_b),
                are_allies = are_allies(faction_a, faction_b),
                reputation = get_faction_reputation(faction_a, faction_b)
            })
        })
    end
)

-- =============================================================================
-- CODEC CALLBACKS
-- =============================================================================

-- When codec_17_factions is loaded, register factions from JSON
codec.on("factions", function(data)
    if data.factions then
        for faction_id, definition in pairs(data.factions) do
            register_faction(faction_id, definition)
        end
    end
end)

-- Register standard LoadCodec handler
codec.register_handler()

-- =============================================================================
-- EXPORT
-- =============================================================================

return {
    -- Registry
    FACTIONS = FACTIONS,
    register_faction = register_faction,
    init_default_factions = init_default_factions,
    
    -- Queries
    get_faction = get_faction,
    are_rivals = are_rivals,
    are_allies = are_allies,
    get_faction_reputation = get_faction_reputation,
    modify_reputation = modify_reputation,
    
    -- Territory
    claim_building = claim_building,
    controls_district = controls_district,
    get_building_owner = get_building_owner,
    
    -- Members
    add_faction_member = add_faction_member,
    remove_faction_member = remove_faction_member,
    get_npc_faction = get_npc_faction,
    check_faction_rule = check_faction_rule,
    
    -- Conflicts
    can_interact = can_interact,
    faction_trust_modifier = faction_trust_modifier
}

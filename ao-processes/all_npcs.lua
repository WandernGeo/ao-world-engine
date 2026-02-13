--[[
  AO World Engine - All NPCs Data
  
  Thin loader that populates ALL_NPCS and BUILDINGS from Arweave codecs.
  Replaces the previous 41,000-line hardcoded version.
  
  Data source:
    - NPCs:      loaded via LoadCodec { CodecName: "codec_01_npcs" }
    - Buildings:  loaded via LoadCodec { CodecName: "codec_16_buildings" }
  
  The codec JSON is uploaded to Arweave and sent to the AO process via
  LoadCodec messages. Until codecs are loaded, empty defaults are used.
  
  Usage: require("all_npcs")
  Returns: { ALL_NPCS = table, BUILDINGS = table }
]]--

local codec_loader = require("codec_loader")

-- =============================================================================
-- EMPTY DEFAULTS (populated by codec data)
-- =============================================================================

ALL_NPCS = ALL_NPCS or {}
BUILDINGS = BUILDINGS or {}

-- =============================================================================
-- CODEC CALLBACKS
-- =============================================================================

-- NPC data from codec_01 (founding + generated NPCs)
codec_loader.on("codec_01_npcs", function(data)
    -- Load founding NPCs
    if data.founding_npcs then
        for key, npc in pairs(data.founding_npcs) do
            if key ~= "_desc" then
                local npc_id = npc.code or key
                ALL_NPCS[npc_id] = npc
                print("[all_npcs] Loaded founding NPC: " .. (npc.name or key))
            end
        end
    end
    
    -- Load generated NPCs (from expanded codec or inline)
    if data.generated_npcs then
        for npc_id, npc in pairs(data.generated_npcs) do
            ALL_NPCS[npc_id] = npc
        end
        print("[all_npcs] Loaded " .. codec_loader.count_keys(data.generated_npcs) .. " generated NPCs from codec")
    end
    
    print("[all_npcs] Total NPCs after codec_01 load: " .. codec_loader.count_keys(ALL_NPCS))
end)

-- Generated NPC population (large dataset, loaded separately) 
codec_loader.on("codec_npcs_generated", function(data)
    if type(data) == "table" then
        for npc_id, npc in pairs(data) do
            if type(npc) == "table" and npc.id then
                ALL_NPCS[npc_id] = npc
            end
        end
        print("[all_npcs] Loaded generated NPC population: " .. codec_loader.count_keys(data) .. " NPCs")
    end
    print("[all_npcs] Total NPCs: " .. codec_loader.count_keys(ALL_NPCS))
end)

-- Building data from codec_16
codec_loader.on("codec_16_buildings", function(data)
    if data.buildings then
        for bld_id, bld in pairs(data.buildings) do
            BUILDINGS[bld_id] = bld
        end
        print("[all_npcs] Loaded " .. codec_loader.count_keys(data.buildings) .. " buildings from codec_16")
    elseif data.building_templates then
        -- Store templates for procedural building generation
        BUILDING_TEMPLATES = data.building_templates
        print("[all_npcs] Loaded " .. codec_loader.count_keys(data.building_templates) .. " building templates from codec_16")
    end
end)

-- =============================================================================
-- QUERY HELPERS
-- =============================================================================

-- Get NPC by ID
function get_npc(npc_id)
    return ALL_NPCS[npc_id]
end

-- Get all NPCs matching a filter
function find_npcs(filter_fn)
    local results = {}
    for id, npc in pairs(ALL_NPCS) do
        if filter_fn(npc) then
            results[id] = npc
        end
    end
    return results
end

-- Get NPCs by archetype
function get_npcs_by_archetype(archetype)
    return find_npcs(function(npc) return npc.archetype == archetype end)
end

-- Get NPCs by faction
function get_npcs_by_faction(faction)
    return find_npcs(function(npc) return npc.faction == faction end)
end

-- Get NPCs in a building
function get_npcs_in_building(building_id)
    return find_npcs(function(npc)
        return npc.home == building_id or npc.workplace == building_id
    end)
end

-- Get population count
function get_population_count()
    return codec_loader.count_keys(ALL_NPCS)
end

-- =============================================================================
-- EXPORT
-- =============================================================================

return { ALL_NPCS = ALL_NPCS, BUILDINGS = BUILDINGS }

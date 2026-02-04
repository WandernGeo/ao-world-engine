--[[
  AO World Engine - GeoEcho Generator
  
  Automatically generates "echoes" from NPC life moments.
  These echoes are findable in the real world via the GeoEchoes app.
  
  Echoes are uploaded to Arweave with GPS-tagged metadata so users
  can discover NPC content at real-world locations mapped to sim locations.
]]--

local json = require("json")

-- =============================================================================
-- STATE
-- =============================================================================

EchoQueue = EchoQueue or {}       -- Pending echoes to upload
GeneratedEchoes = GeneratedEchoes or {}  -- History of generated echoes
EchoCounter = EchoCounter or 0

-- Generation settings
ECHO_COOLDOWN = 1000              -- Ticks between echoes per NPC
ECHO_PROBABILITY = 0.001          -- 0.1% chance per eligible tick
MAX_QUEUED_ECHOES = 100           -- Don't queue too many

-- =============================================================================
-- GEO MAPPING (loaded from geo_claims.json)
-- =============================================================================

-- Default mappings (will be overridden by config)
GeoMappings = GeoMappings or {
    neon_bar = { lat = 40.7589, lng = -73.9851 },
    resistance_hideout = { lat = 40.7074, lng = -73.9979 },
    temple_infirmary = { lat = 40.7587, lng = -73.9787 },
    tech_den = { lat = 40.7081, lng = -74.0089 },
    mystic_sanctum = { lat = 40.7794, lng = -73.9632 },
    underground_kitchen = { lat = 40.6892, lng = -73.9937 },
    neon_district = { lat = 40.7580, lng = -73.9855 },
    temple_quarter = { lat = 40.7587, lng = -73.9787 },
    undercity = { lat = 40.7506, lng = -73.9936 }
}

-- =============================================================================
-- ECHO TEMPLATES
-- =============================================================================

ECHO_TYPES = {
    life_moment = {
        weight = 0.4,
        prefixes = {
            "I saw %s today. The rain never stops here.",
            "Another day. %s weighs on my mind.",
            "The neon flickers. %s happened.",
            "%s. Nothing is what it seems."
        }
    },
    memory = {
        weight = 0.2,
        prefixes = {
            "I remember when %s. Feels like another life.",
            "Before the Fall, %s. Now look at us.",
            "%s. The past bleeds into now."
        }
    },
    observation = {
        weight = 0.25,
        prefixes = {
            "Watched %s from the shadows.",
            "The city shows me %s.",
            "In the alley, %s."
        }
    },
    dialogue = {
        weight = 0.15,
        prefixes = {
            "\"%s,\" they said. I'm still thinking about it.",
            "Someone told me: \"%s\"",
            "Words echo: \"%s\""
        }
    }
}

MOOD_MODIFIERS = {
    paranoid = { "Trust no one.", "They're watching.", "Something's wrong." },
    hopeful = { "Maybe tomorrow.", "There's still a chance.", "We keep fighting." },
    melancholic = { "Rain washes nothing clean.", "Lost in the signal.", "Fading echoes." },
    determined = { "Not today.", "I will find the truth.", "The fight continues." },
    contemplative = { "The layers fold.", "What is real?", "Between the static." }
}

-- =============================================================================
-- ECHO GENERATION
-- =============================================================================

function should_generate_echo(npc, tick)
    -- Check cooldown
    if npc.last_echo_tick and (tick - npc.last_echo_tick) < ECHO_COOLDOWN then
        return false
    end
    
    -- Check probability (deterministic)
    local seed = hash_to_number(npc.id .. tostring(tick) .. "echo", 100000)
    return seed < (ECHO_PROBABILITY * 100000)
end

function generate_echo(npc, tick, context)
    context = context or {}
    
    EchoCounter = EchoCounter + 1
    local echo_id = "ECHO_" .. npc.id .. "_T" .. tick
    
    -- Select echo type (weighted random)
    local echo_type = select_weighted_type(tick, npc.id)
    local template = ECHO_TYPES[echo_type]
    
    -- Generate content
    local prefix = template.prefixes[hash_to_number(npc.id .. "prefix" .. tick, #template.prefixes) + 1]
    local subject = generate_subject(npc, context, tick)
    local text = string.format(prefix, subject)
    
    -- Add mood modifier
    local mood = get_npc_mood(npc)
    local modifier = MOOD_MODIFIERS[mood]
    if modifier then
        text = text .. " " .. modifier[hash_to_number(npc.id .. "mood" .. tick, #modifier) + 1]
    end
    
    -- Get location coords
    local coords = GeoMappings[npc.current_location or npc.home_location] or GeoMappings.neon_district
    
    local echo = {
        echo_id = echo_id,
        type = echo_type,
        npc_id = npc.id,
        npc_name = npc.name,
        tick = tick,
        layer_id = LAYER_ID or "layer_00_testnet",
        
        content = {
            text = text,
            mood = mood,
            generated_at = tick
        },
        
        location = {
            sim = npc.current_location or npc.home_location,
            lat = coords.lat,
            lng = coords.lng
        },
        
        arweave_tags = {
            { name = "App-Name", value = "AO-World-Engine" },
            { name = "Type", value = "geoecho" },
            { name = "Layer-ID", value = LAYER_ID or "layer_00_testnet" },
            { name = "NPC-ID", value = npc.id },
            { name = "NPC-Name", value = npc.name },
            { name = "Geo-Lat", value = tostring(coords.lat) },
            { name = "Geo-Lng", value = tostring(coords.lng) },
            { name = "Echo-Type", value = echo_type },
            { name = "Tick", value = tostring(tick) }
        }
    }
    
    return echo
end

function select_weighted_type(tick, npc_id)
    local total = 0
    for _, t in pairs(ECHO_TYPES) do
        total = total + t.weight
    end
    
    local roll = hash_to_number(npc_id .. "type" .. tick, math.floor(total * 1000)) / 1000
    local cumulative = 0
    
    for type_name, t in pairs(ECHO_TYPES) do
        cumulative = cumulative + t.weight
        if roll < cumulative then
            return type_name
        end
    end
    
    return "life_moment"
end

function generate_subject(npc, context, tick)
    -- Generate contextual subject based on NPC state
    local subjects = {
        "the Temple's shadow",
        "the Resistance whispers",
        "the neon drowning sorrow",
        "faces in the crowd",
        "data streams in the night",
        "echoes from another layer",
        "the price of survival",
        "memories that aren't mine"
    }
    
    -- Add relationship-based subjects
    if npc.relationships then
        for other_id, rel in pairs(npc.relationships) do
            if rel.trust and rel.trust > 0.5 then
                table.insert(subjects, "thinking about " .. (rel.name or other_id))
            end
        end
    end
    
    return subjects[hash_to_number(npc.id .. "subj" .. tick, #subjects) + 1]
end

function get_npc_mood(npc)
    if not npc.personality then return "contemplative" end
    
    if npc.personality.paranoia and npc.personality.paranoia > 0.6 then
        return "paranoid"
    elseif npc.personality.empathy and npc.personality.empathy > 0.7 then
        return "hopeful"
    elseif npc.personality.mysticism and npc.personality.mysticism > 0.6 then
        return "contemplative"
    elseif npc.personality.aggression and npc.personality.aggression > 0.5 then
        return "determined"
    else
        return "melancholic"
    end
end

-- =============================================================================
-- HANDLERS
-- =============================================================================

-- Generate echoes for tick (called from district tick)
Handlers.add("generate-echoes", Handlers.utils.hasMatchingTag("Action", "generate-echoes"), function(msg)
    local data = json.decode(msg.Data)
    local tick = data.tick
    local npcs = data.npcs or {}
    
    local generated = {}
    
    for _, npc in ipairs(npcs) do
        if should_generate_echo(npc, tick) then
            local echo = generate_echo(npc, tick, data.context)
            table.insert(EchoQueue, echo)
            table.insert(generated, echo.echo_id)
            
            -- Mark NPC's last echo
            npc.last_echo_tick = tick
        end
    end
    
    -- Trim queue if too large
    while #EchoQueue > MAX_QUEUED_ECHOES do
        table.remove(EchoQueue, 1)
    end
    
    ao.send({
        Target = msg.From,
        Action = "echoes-generated",
        Data = json.encode({
            tick = tick,
            generated_count = #generated,
            echo_ids = generated,
            queue_size = #EchoQueue
        })
    })
end)

-- Get queued echoes for upload
Handlers.add("get-echo-queue", Handlers.utils.hasMatchingTag("Action", "get-echo-queue"), function(msg)
    local data = json.decode(msg.Data or "{}")
    local limit = data.limit or 10
    
    local echoes = {}
    for i = 1, math.min(limit, #EchoQueue) do
        table.insert(echoes, EchoQueue[i])
    end
    
    ao.send({
        Target = msg.From,
        Action = "echo-queue",
        Data = json.encode({
            echoes = echoes,
            total_queued = #EchoQueue
        })
    })
end)

-- Mark echo as uploaded (remove from queue)
Handlers.add("echo-uploaded", Handlers.utils.hasMatchingTag("Action", "echo-uploaded"), function(msg)
    local data = json.decode(msg.Data)
    local echo_id = data.echo_id
    local arweave_tx = data.arweave_tx
    
    -- Remove from queue
    for i, echo in ipairs(EchoQueue) do
        if echo.echo_id == echo_id then
            echo.arweave_tx = arweave_tx
            echo.uploaded_at = os.time()
            table.insert(GeneratedEchoes, echo)
            table.remove(EchoQueue, i)
            break
        end
    end
    
    ao.send({
        Target = msg.From,
        Action = "echo-confirmed",
        Data = json.encode({ echo_id = echo_id, arweave_tx = arweave_tx })
    })
end)

-- Load geo mappings
Handlers.add("load-geo-mappings", Handlers.utils.hasMatchingTag("Action", "load-geo-mappings"), function(msg)
    local data = json.decode(msg.Data)
    if data.mappings then
        for location, coords in pairs(data.mappings) do
            GeoMappings[location] = coords
        end
    end
    
    ao.send({
        Target = msg.From,
        Action = "geo-mappings-loaded",
        Data = json.encode({ locations = table_length(GeoMappings) })
    })
end)

-- =============================================================================
-- HELPERS
-- =============================================================================

function hash_to_number(str, max)
    local hash = 0
    for i = 1, #str do
        hash = (hash * 31 + string.byte(str, i)) % 2147483647
    end
    return (hash % max)
end

function table_length(t)
    local count = 0
    for _ in pairs(t) do count = count + 1 end
    return count
end

-- =============================================================================
-- EXPORT
-- =============================================================================

return {
    generate_echo = generate_echo,
    should_generate_echo = should_generate_echo,
    EchoQueue = EchoQueue,
    GeneratedEchoes = GeneratedEchoes
}

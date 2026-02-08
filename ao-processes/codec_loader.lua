--[[
  AO World Engine - Codec Loader Utility

  Standardized pattern for loading codec JSON into AO processes.
  Each process uses this to:
  1. Accept codec JSON via "LoadCodec" message
  2. Merge codec data with in-memory defaults (fallback)
  3. Support hot-reload via re-sending codec data

  Usage in any process:
    local codec_loader = require("codec_loader")
    
    -- Register codec handler (one-time in init)
    codec_loader.register_handler("economy", function(data)
        -- data is the decoded JSON from the codec chunk
        TaxConfig = data.taxation or TaxConfig
        ZoneTypes = data.zoning or ZoneTypes
    end)
    
    -- Access loaded codec data
    local economy = codec_loader.get("economy")
]]--

local json = require("json")

-- =============================================================================
-- CODEC STORAGE
-- =============================================================================

local CodecStore = {}   -- { codec_name: decoded_data }
local CodecCallbacks = {}  -- { codec_name: [callback_fn, ...] }

-- =============================================================================
-- CORE API
-- =============================================================================

-- Store codec data and fire callbacks
function load_codec(codec_name, json_data)
    if type(json_data) == "string" then
        local ok, decoded = pcall(json.decode, json_data)
        if not ok then
            return false, "JSON decode failed: " .. tostring(decoded)
        end
        json_data = decoded
    end
    
    CodecStore[codec_name] = json_data
    
    -- Fire all registered callbacks for this codec
    if CodecCallbacks[codec_name] then
        for _, cb in ipairs(CodecCallbacks[codec_name]) do
            local ok, err = pcall(cb, json_data)
            if not ok then
                print("[codec_loader] Callback error for '" .. codec_name .. "': " .. tostring(err))
            end
        end
    end
    
    return true
end

-- Get loaded codec data (returns nil if not loaded)
function get_codec(codec_name)
    return CodecStore[codec_name]
end

-- Register a callback that fires when codec is loaded/reloaded
function register_codec_callback(codec_name, callback_fn)
    if not CodecCallbacks[codec_name] then
        CodecCallbacks[codec_name] = {}
    end
    table.insert(CodecCallbacks[codec_name], callback_fn)
    
    -- If codec is already loaded, fire immediately
    if CodecStore[codec_name] then
        callback_fn(CodecStore[codec_name])
    end
end

-- =============================================================================
-- DEEP MERGE UTILITY
-- =============================================================================

-- Deep merge: source overwrites target, recursively for tables
function deep_merge(target, source)
    if type(target) ~= "table" or type(source) ~= "table" then
        return source
    end
    
    local result = {}
    for k, v in pairs(target) do
        result[k] = v
    end
    for k, v in pairs(source) do
        if type(v) == "table" and type(result[k]) == "table" then
            result[k] = deep_merge(result[k], v)
        else
            result[k] = v
        end
    end
    return result
end

-- =============================================================================
-- CODEC VALUE ACCESSOR (safe nested access)
-- =============================================================================

-- Safe nested table access: codec_get(data, "commuting.transport_modes.walk.speed_factor")
function codec_get(data, path, default)
    if not data then return default end
    
    local current = data
    for key in string.gmatch(path, "[^%.]+") do
        if type(current) ~= "table" then return default end
        current = current[key]
        if current == nil then return default end
    end
    return current
end

-- =============================================================================
-- AO HANDLER REGISTRATION
-- =============================================================================

-- Register the standard "LoadCodec" handler on the AO process
-- This should be called once during process initialization
function register_handler()
    if Handlers and Handlers.add then
        Handlers.add("LoadCodec", Handlers.utils.hasMatchingTag("Action", "LoadCodec"),
            function(msg)
                local codec_name = msg.Tags["CodecName"]
                if not codec_name then
                    ao.send({
                        Target = msg.From,
                        Action = "LoadCodec-Error",
                        Data = json.encode({ error = "Missing CodecName tag" })
                    })
                    return
                end
                
                local ok, err = load_codec(codec_name, msg.Data)
                
                ao.send({
                    Target = msg.From,
                    Action = ok and "LoadCodec-Success" or "LoadCodec-Error",
                    Data = json.encode({
                        codec = codec_name,
                        success = ok,
                        error = err,
                        keys_loaded = ok and count_keys(CodecStore[codec_name]) or 0
                    })
                })
            end
        )
        
        -- Query what codecs are loaded
        Handlers.add("ListCodecs", Handlers.utils.hasMatchingTag("Action", "ListCodecs"),
            function(msg)
                local loaded = {}
                for name, data in pairs(CodecStore) do
                    loaded[name] = {
                        keys = count_keys(data),
                        loaded = true
                    }
                end
                ao.send({
                    Target = msg.From,
                    Action = "ListCodecs-Response",
                    Data = json.encode(loaded)
                })
            end
        )
    end
end

-- =============================================================================
-- HELPERS
-- =============================================================================

function count_keys(tbl)
    if type(tbl) ~= "table" then return 0 end
    local count = 0
    for _ in pairs(tbl) do count = count + 1 end
    return count
end

-- =============================================================================
-- EXPORT
-- =============================================================================

return {
    load = load_codec,
    get = get_codec,
    on = register_codec_callback,
    register_handler = register_handler,
    deep_merge = deep_merge,
    codec_get = codec_get,
    count_keys = count_keys
}

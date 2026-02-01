--[[
  RE:ECHO City - Canon Validator
  
  Validates new content submissions against existing canon.
  Transforms invalid content when possible, rejects when not.
  
  SECURITY NOTE: This file contains NO secrets, keys, or wallet data.
]]--

-- Signal Noir ruleset
FORBIDDEN_ELEMENTS = {
  -- Fantasy creatures
  "dragon", "elf", "dwarf", "orc", "wizard", "witch", "fairy", "unicorn",
  "goblin", "troll", "vampire", "werewolf", "zombie", "demon", "angel",
  
  -- Supernatural
  "magic", "spell", "curse", "blessing", "divine", "miracle", "prophecy",
  "teleport", "resurrect", "immortal_natural", "ghost_supernatural",
  
  -- Sci-fi breaks
  "alien", "ufo", "spaceship", "faster_than_light", "time_travel",
  "parallel_universe", "dimension_portal",
  
  -- Meta breaks
  "fourth_wall", "player", "user", "real_world"
}

TRANSFORM_PATTERNS = {
  ["dragon"] = { to = "holographic_dragon_display", reason = "AR/hologram technology" },
  ["magic"] = { to = "hacking_exploit", reason = "technological explanation" },
  ["spell"] = { to = "neural_implant_effect", reason = "cybernetic capability" },
  ["ghost"] = { to = "echo_manifestation", reason = "Echo lore" },
  ["teleport"] = { to = "rapid_transit", reason = "physical transportation" },
  ["resurrect"] = { to = "revival_from_stasis", reason = "medical technology" },
  ["alien"] = { to = "foreign_corp_agent", reason = "corporate intrigue" },
  ["wizard"] = { to = "master_hacker", reason = "tech equivalent" },
  ["vampire"] = { to = "blood_addict_augmented", reason = "cybernetic condition" }
}

LIFESPAN_RULES = {
  minimum = 200,
  maximum = 350,
  child_max_age = 18,
  working_age_min = 18
}

--[[
  VALIDATION HANDLERS
]]--

Handlers.add("validate-content", Handlers.utils.hasMatchingTag("Action", "validate-content"), function(msg)
  local content = json.decode(msg.Data)
  local result = validate_submission(content)
  
  ao.send({
    Target = msg.From,
    Action = "validation-result",
    Data = json.encode(result)
  })
end)

--[[
  CORE VALIDATION FUNCTION
]]--

function validate_submission(content)
  local result = {
    status = "pending",
    original = content,
    transformed = nil,
    errors = {},
    warnings = {}
  }
  
  -- Check for forbidden elements in all string fields
  local forbidden_found = check_forbidden_elements(content)
  if #forbidden_found > 0 then
    result.warnings = forbidden_found
    
    -- Try to transform
    local transformed = transform_content(content, forbidden_found)
    if transformed then
      result.status = "transformed"
      result.transformed = transformed
      result.message = "Content transformed to fit canon"
    else
      result.status = "rejected"
      result.errors = forbidden_found
      result.message = "Cannot transform content to fit canon"
      return result
    end
  end
  
  -- Validate specific content types
  if content.type == "npc" then
    local npc_result = validate_npc(content)
    if not npc_result.valid then
      result.status = "rejected"
      result.errors = npc_result.errors
      return result
    end
  elseif content.type == "event" then
    local event_result = validate_event(content)
    if not event_result.valid then
      result.status = "rejected"
      result.errors = event_result.errors
      return result
    end
  elseif content.type == "death" then
    local death_result = validate_death(content)
    if not death_result.valid then
      result.status = "rejected"
      result.errors = death_result.errors
      return result
    end
  end
  
  -- Passed all checks
  if result.status == "pending" then
    result.status = "accepted"
    result.message = "Content fits canon"
  end
  
  return result
end

--[[
  CHECK FOR FORBIDDEN ELEMENTS
]]--

function check_forbidden_elements(content)
  local found = {}
  local content_str = json.encode(content):lower()
  
  for _, element in ipairs(FORBIDDEN_ELEMENTS) do
    if content_str:find(element) then
      table.insert(found, {
        element = element,
        rule = "forbidden_in_signal_noir"
      })
    end
  end
  
  return found
end

--[[
  TRANSFORM CONTENT
]]--

function transform_content(content, forbidden_list)
  local transformed = deep_copy(content)
  local content_str = json.encode(transformed)
  
  for _, item in ipairs(forbidden_list) do
    local pattern = TRANSFORM_PATTERNS[item.element]
    if pattern then
      content_str = content_str:gsub(item.element, pattern.to)
      
      -- Add transformation note
      if not transformed.canon_notes then
        transformed.canon_notes = {}
      end
      table.insert(transformed.canon_notes, {
        original = item.element,
        transformed_to = pattern.to,
        reason = pattern.reason
      })
    else
      -- No transform pattern available
      return nil
    end
  end
  
  return json.decode(content_str)
end

--[[
  VALIDATE NPC
]]--

function validate_npc(npc)
  local errors = {}
  
  -- Check lifespan if age provided
  if npc.age then
    if npc.age < 0 then
      table.insert(errors, "Age cannot be negative")
    end
  end
  
  -- Check archetype exists
  local valid_archetypes = {
    "merchant", "hacker_drone", "street_samurai", "corporate_spy",
    "explorer", "fixer", "healer", "guard", "rebel", "worker"
  }
  if npc.archetype and not table_contains(valid_archetypes, npc.archetype) then
    table.insert(errors, "Unknown archetype: " .. npc.archetype)
  end
  
  -- Check faction
  local valid_factions = {"vivi", "augmented", "corporate", "rebel", "neutral"}
  if npc.faction and not table_contains(valid_factions, npc.faction) then
    table.insert(errors, "Unknown faction: " .. npc.faction)
  end
  
  return {
    valid = #errors == 0,
    errors = errors
  }
end

--[[
  VALIDATE EVENT
]]--

function validate_event(event)
  local errors = {}
  
  -- Check event type
  local valid_event_types = {
    "birth", "death", "marriage", "divorce", "job_change", "faction_shift",
    "trade", "conflict", "conversation", "move", "election", "festival",
    "riot", "blackout", "accident", "heist", "sabotage"
  }
  
  if event.event_type and not table_contains(valid_event_types, event.event_type) then
    table.insert(errors, "Unknown event type: " .. event.event_type)
  end
  
  -- Check referenced NPCs exist (would query Arweave in production)
  -- For now, just validate format
  if event.actor and not event.actor:match("^npc_") then
    table.insert(errors, "Invalid actor ID format")
  end
  
  return {
    valid = #errors == 0,
    errors = errors
  }
end

--[[
  VALIDATE DEATH
]]--

function validate_death(death)
  local errors = {}
  
  -- Check age at death
  if death.age_at_death then
    if death.age_at_death < LIFESPAN_RULES.minimum then
      -- Only allowed for violent/accidental deaths
      local valid_early_death = {
        "combat", "assassination", "accident", "catastrophic_failure", "choice"
      }
      if not death.cause or not table_contains(valid_early_death, death.cause) then
        table.insert(errors, 
          "Death at age " .. death.age_at_death .. 
          " requires valid cause (minimum lifespan is " .. LIFESPAN_RULES.minimum .. ")")
      end
    end
  end
  
  return {
    valid = #errors == 0,
    errors = errors
  }
end

--[[
  HELPERS
]]--

function table_contains(tbl, val)
  for _, v in ipairs(tbl) do
    if v == val then return true end
  end
  return false
end

function deep_copy(obj)
  if type(obj) ~= 'table' then return obj end
  local res = {}
  for k, v in pairs(obj) do res[deep_copy(k)] = deep_copy(v) end
  return res
end

return {
  validate_submission = validate_submission,
  FORBIDDEN_ELEMENTS = FORBIDDEN_ELEMENTS,
  TRANSFORM_PATTERNS = TRANSFORM_PATTERNS
}

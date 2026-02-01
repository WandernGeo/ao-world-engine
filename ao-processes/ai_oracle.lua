--[[
  RE:ECHO City - AI Oracle Process
  
  LLM-powered dialogue and decision generation for autonomous NPCs.
  NPCs generate their own dynamic dialogue without user input.
  
  ARCHITECTURE:
  - Events trigger dialogue generation requests
  - AI Oracle batches requests and calls external LLM
  - Generated content is validated and stored
  - NPCs access cached dialogue for their interactions
  
  SELF-PERPETUATION:
  - No user input needed after initial setup
  - Events → LLM → Dialogue → New Events → Loop
  - World evolves autonomously
]]--

-- State
DIALOGUE_QUEUE = DIALOGUE_QUEUE or {}
DIALOGUE_CACHE = DIALOGUE_CACHE or {}
DECISION_CACHE = DECISION_CACHE or {}
PROCESSING = PROCESSING or false
LLM_ENDPOINT = LLM_ENDPOINT or nil  -- Set via config

-- Stats
GenCounter = GenCounter or 0
CacheHits = CacheHits or 0

-- Prompt templates
PROMPTS = {
  -- Conversation between two NPCs
  conversation = [[
SETTING: RE:ECHO City, a cyberpunk noir dystopia. Signal Noir style.
Rain-soaked streets, failing neon, moral ambiguity.

CHARACTERS:
- %s: %s archetype, %s faction, mood: %s
- %s: %s archetype, %s faction, mood: %s

CONTEXT: %s

LAYER AWARENESS: Characters live in "Layer 0" (prime reality). 
Rare moments they sense "other layers" or "Watchers" observing.
Probability of layer reference: %d%%

Generate a SHORT dialogue exchange (2-4 lines each, noir style).
One character starts. Natural conversation about their situation.
If layer reference triggered, include subtle existential musing.

FORMAT (JSON):
{
  "dialogue": [
    {"speaker": "NAME", "text": "...", "action": "optional action"},
    ...
  ],
  "relationship_delta": 0.0 to 0.5,
  "event_triggered": null or "event_type"
}
]],

  -- NPC internal monologue / decision
  decision = [[
SETTING: RE:ECHO City, cyberpunk noir dystopia.

CHARACTER: %s
- Archetype: %s
- Faction: %s
- Personality: %s
- Current location: %s
- Recent events: %s

DECISION CONTEXT: %s

What does this character decide to do next?
Consider their personality, faction loyalty, and recent experiences.

FORMAT (JSON):
{
  "decision": "action_code",
  "reasoning": "brief internal thought",
  "dialogue_if_alone": "what they mutter to themselves (optional)",
  "confidence": 0.0 to 1.0
}
]],

  -- Reaction to layer bleed event
  bleed_reaction = [[
SETTING: RE:ECHO City. A character just experienced a "layer bleed" - 
a momentary glimpse of an alternate reality/timeline.

CHARACTER: %s (%s archetype)
BLEED TYPE: %s
INTENSITY: %s (0-1 scale)

They saw/felt a flash of another version of their life.
This is rare, unsettling, and philosophically destabilizing.

Generate their immediate reaction (1-2 sentences, noir style).
They might deny it, question reality, or cryptically acknowledge.

FORMAT (JSON):
{
  "immediate_reaction": "what they say/do",
  "internal_thought": "what they think but don't say",
  "lasting_effect": "subtle personality shift if any"
}
]],

  -- Daily summary narration (for "watching the show")
  narration = [[
SETTING: RE:ECHO City, Signal Noir cyberpunk.
LOCATION: %s
TIME PERIOD: Tick %d to %d

EVENTS THAT OCCURRED:
%s

Generate a SHORT noir-style narration summarizing these events.
Think Raymond Chandler meets Blade Runner.
2-3 paragraphs max. Atmospheric, moody, character-focused.

FORMAT (JSON):
{
  "narration": "...",
  "highlight_moments": ["key dramatic moments"],
  "tone": "atmospheric description"
}
]]
}

--[[
  HANDLERS
]]--

-- Queue a dialogue generation request
Handlers.add("queue-dialogue", Handlers.utils.hasMatchingTag("Action", "queue-dialogue"), function(msg)
  local request = json.decode(msg.Data)
  request.id = "dialogue_" .. GenCounter
  request.timestamp = os.time()
  request.requester = msg.From
  
  GenCounter = GenCounter + 1
  table.insert(DIALOGUE_QUEUE, request)
  
  ao.send({
    Target = msg.From,
    Action = "dialogue-queued",
    Data = json.encode({ request_id = request.id, queue_position = #DIALOGUE_QUEUE })
  })
end)

-- Queue a decision request
Handlers.add("queue-decision", Handlers.utils.hasMatchingTag("Action", "queue-decision"), function(msg)
  local request = json.decode(msg.Data)
  request.id = "decision_" .. GenCounter
  request.timestamp = os.time()
  request.requester = msg.From
  request.type = "decision"
  
  GenCounter = GenCounter + 1
  table.insert(DIALOGUE_QUEUE, request)
  
  ao.send({
    Target = msg.From,
    Action = "decision-queued",
    Data = json.encode({ request_id = request.id })
  })
end)

-- Get cached dialogue for an NPC interaction context
Handlers.add("get-dialogue", Handlers.utils.hasMatchingTag("Action", "get-dialogue"), function(msg)
  local data = json.decode(msg.Data)
  local cache_key = generate_cache_key(data)
  
  if DIALOGUE_CACHE[cache_key] then
    CacheHits = CacheHits + 1
    ao.send({
      Target = msg.From,
      Action = "dialogue-result",
      Data = json.encode({
        cached = true,
        dialogue = DIALOGUE_CACHE[cache_key]
      })
    })
  else
    -- Queue for generation
    data.cache_key = cache_key
    data.requester = msg.From
    table.insert(DIALOGUE_QUEUE, data)
    
    ao.send({
      Target = msg.From,
      Action = "dialogue-pending",
      Data = json.encode({ message = "Generating dialogue, will callback" })
    })
  end
end)

-- Process bleed event reaction
Handlers.add("react-to-bleed", Handlers.utils.hasMatchingTag("Action", "react-to-bleed"), function(msg)
  local data = json.decode(msg.Data)
  data.type = "bleed_reaction"
  data.requester = msg.From
  data.priority = "high"  -- Bleed reactions are priority
  
  table.insert(DIALOGUE_QUEUE, 1, data)  -- Insert at front
  
  ao.send({
    Target = msg.From,
    Action = "bleed-reaction-queued",
    Data = json.encode({ queued = true })
  })
end)

-- Generate scene narration (for Watchers)
Handlers.add("narrate-scene", Handlers.utils.hasMatchingTag("Action", "narrate-scene"), function(msg)
  local data = json.decode(msg.Data)
  data.type = "narration"
  data.requester = msg.From
  
  table.insert(DIALOGUE_QUEUE, data)
  
  ao.send({
    Target = msg.From,
    Action = "narration-queued",
    Data = json.encode({ queued = true })
  })
end)

--[[
  CRON: Batch process AI requests
  
  Runs periodically to process queued requests in batches.
  This is cost-efficient: multiple requests → single LLM call.
]]--

Handlers.add("process-queue", Handlers.utils.hasMatchingTag("Action", "Cron"), function(msg)
  if PROCESSING or #DIALOGUE_QUEUE == 0 then
    return
  end
  
  PROCESSING = true
  
  -- Take up to 5 requests per batch
  local batch = {}
  for i = 1, math.min(5, #DIALOGUE_QUEUE) do
    table.insert(batch, table.remove(DIALOGUE_QUEUE, 1))
  end
  
  -- Process each request
  for _, request in ipairs(batch) do
    local result = nil
    
    if request.type == "decision" then
      result = generate_decision(request)
    elseif request.type == "bleed_reaction" then
      result = generate_bleed_reaction(request)
    elseif request.type == "narration" then
      result = generate_narration(request)
    else
      result = generate_dialogue(request)
    end
    
    -- Cache result
    if result and request.cache_key then
      DIALOGUE_CACHE[request.cache_key] = result
    end
    
    -- Callback to requester
    if request.requester and result then
      ao.send({
        Target = request.requester,
        Action = "ai-generation-complete",
        Data = json.encode(result),
        Tags = {
          { name = "Request-Id", value = request.id or "unknown" },
          { name = "Generation-Type", value = request.type or "dialogue" }
        }
      })
    end
  end
  
  PROCESSING = false
end)

--[[
  GENERATION FUNCTIONS
  
  These call the external LLM and parse results.
  In production, this would use ao.send to an LLM bridge process
  or an external API via HTTP.
]]--

function generate_dialogue(request)
  local npc1 = request.npc1 or { name = "Unknown", archetype = "merchant", faction = "neutral", mood = "neutral" }
  local npc2 = request.npc2 or { name = "Unknown", archetype = "merchant", faction = "neutral", mood = "neutral" }
  local context = request.context or "Casual encounter"
  
  -- Layer reference probability (5% base, increases with philosopher archetypes)
  local layer_prob = 5
  if npc1.archetype == "philosopher_hacker" or npc2.archetype == "street_oracle" then
    layer_prob = 25
  end
  
  local prompt = string.format(PROMPTS.conversation,
    npc1.name, npc1.archetype, npc1.faction, npc1.mood,
    npc2.name, npc2.archetype, npc2.faction, npc2.mood,
    context, layer_prob
  )
  
  -- Call LLM (placeholder - in production this would be async)
  local result = call_llm(prompt)
  
  if result then
    result.generated_at = os.time()
    result.npc1_id = npc1.id
    result.npc2_id = npc2.id
    result.llm_tag = "ai_generated:" .. os.time()
  end
  
  return result
end

function generate_decision(request)
  local npc = request.npc or { name = "Unknown", archetype = "merchant" }
  
  local prompt = string.format(PROMPTS.decision,
    npc.name, npc.archetype, npc.faction or "neutral",
    json.encode(npc.personality or {}),
    request.location or "unknown",
    json.encode(request.recent_events or {}),
    request.decision_context or "What to do next"
  )
  
  local result = call_llm(prompt)
  
  if result then
    result.generated_at = os.time()
    result.npc_id = npc.id
    result.llm_tag = "ai_decision:" .. os.time()
  end
  
  return result
end

function generate_bleed_reaction(request)
  local npc = request.npc or { name = "Unknown", archetype = "merchant" }
  
  local prompt = string.format(PROMPTS.bleed_reaction,
    npc.name, npc.archetype,
    request.bleed_type or "parallel_glimpse",
    tostring(request.intensity or 0.5)
  )
  
  local result = call_llm(prompt)
  
  if result then
    result.generated_at = os.time()
    result.npc_id = npc.id
    result.bleed_event_id = request.event_id
    result.llm_tag = "ai_bleed_reaction:" .. os.time()
  end
  
  return result
end

function generate_narration(request)
  local prompt = string.format(PROMPTS.narration,
    request.location or "Unknown District",
    request.tick_start or 0,
    request.tick_end or 0,
    json.encode(request.events or {})
  )
  
  local result = call_llm(prompt)
  
  if result then
    result.generated_at = os.time()
    result.llm_tag = "ai_narration:" .. os.time()
  end
  
  return result
end

--[[
  LLM INTEGRATION
  
  Placeholder for actual LLM calls. In production:
  - Could use AO's native AI capabilities
  - Could call external API via HTTP bridge
  - Could use cached templates for cost efficiency
]]--

function call_llm(prompt)
  -- In production: ao.send to LLM bridge process
  -- For now: Return structured placeholder that shows the system works
  
  -- This would be replaced with:
  -- ao.send({ Target = LLM_BRIDGE, Action = "generate", Data = prompt })
  -- Then handle response in a callback handler
  
  -- Fallback: Use template-based generation
  return template_generate(prompt)
end

function template_generate(prompt)
  -- Fallback when LLM not available: Use seeded templates
  -- This ensures the system works even without LLM access
  
  local seed = hash_to_number(prompt, 1000)
  
  -- Detect prompt type and return appropriate template
  if string.find(prompt, "dialogue exchange") then
    return {
      dialogue = generate_template_dialogue(seed),
      relationship_delta = (seed % 50) / 100,
      event_triggered = nil,
      method = "template_fallback"
    }
  elseif string.find(prompt, "decide to do") then
    return {
      decision = "continue_routine",
      reasoning = "No better option available",
      dialogue_if_alone = template_monologues[((seed % #template_monologues) + 1)],
      confidence = 0.7,
      method = "template_fallback"
    }
  elseif string.find(prompt, "layer bleed") then
    return {
      immediate_reaction = bleed_reactions[((seed % #bleed_reactions) + 1)],
      internal_thought = "What was that?",
      lasting_effect = nil,
      method = "template_fallback"
    }
  else
    return {
      narration = "The rain never stops in RE:ECHO City...",
      method = "template_fallback"
    }
  end
end

-- Template dialogue lines for fallback
template_monologues = {
  "Another cycle. Same story.",
  "The neon flickers. Just like my memories.",
  "Wonder if anyone's watching.",
  "Fee like I've done this before. Many times.",
  "The layers stack. We're just one echo.",
  "Credits in, credits out. What's the point?"
}

bleed_reactions = {
  "...That wasn't a dream.",
  "*blinks rapidly* Did you see that?",
  "I was... somewhere else. Just now.",
  "*touches face* I'm still me. Right?",
  "Another me. There's another me out there.",
  "The static behind my eyes. Gone now."
}

function generate_template_dialogue(seed)
  local lines = {
    { "What brings you here?", "Business. Always business." },
    { "Heard about the blackout?", "Yeah. Third this month. Something's breaking." },
    { "You believe in the layers?", "Does it matter? I still gotta eat." },
    { "The Watchers see everything.", "Conspiracy talk. Focus on reality." },
    { "Rain never stops here.", "It's not rain. It's the city crying." }
  }
  
  local chosen = lines[((seed % #lines) + 1)]
  return {
    { speaker = "NPC_1", text = chosen[1], action = "leans in" },
    { speaker = "NPC_2", text = chosen[2], action = "shrugs" }
  }
end

--[[
  HELPERS
]]--

function generate_cache_key(data)
  local key_parts = {
    data.npc1 and data.npc1.id or "unknown",
    data.npc2 and data.npc2.id or "unknown",
    data.context or "general",
    tostring(math.floor(os.time() / 3600))  -- 1-hour cache buckets
  }
  return table.concat(key_parts, "_")
end

function hash_to_number(str, max)
  local hash = 0
  for i = 1, #str do
    hash = (hash * 31 + string.byte(str, i)) % 2147483647
  end
  return (hash % max) + 1
end

-- Configure LLM endpoint
Handlers.add("set-llm-endpoint", Handlers.utils.hasMatchingTag("Action", "set-llm-endpoint"), function(msg)
  LLM_ENDPOINT = msg.Data
  ao.send({
    Target = msg.From,
    Action = "llm-configured",
    Data = json.encode({ endpoint = LLM_ENDPOINT })
  })
end)

-- Stats
Handlers.add("oracle-stats", Handlers.utils.hasMatchingTag("Action", "oracle-stats"), function(msg)
  ao.send({
    Target = msg.From,
    Action = "stats",
    Data = json.encode({
      total_generations = GenCounter,
      cache_hits = CacheHits,
      queue_size = #DIALOGUE_QUEUE,
      cache_size = table_length(DIALOGUE_CACHE),
      processing = PROCESSING
    })
  })
end)

function table_length(t)
  local count = 0
  for _ in pairs(t) do count = count + 1 end
  return count
end

return {
  DIALOGUE_QUEUE = DIALOGUE_QUEUE,
  DIALOGUE_CACHE = DIALOGUE_CACHE,
  generate_dialogue = generate_dialogue,
  generate_decision = generate_decision
}

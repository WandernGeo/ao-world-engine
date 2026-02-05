# Infrastructure Tests (100 tests)

> **Updated:** 2026-02-05T07:20:00-05:00

Tests for Lua modules, plugins, handlers, and system infrastructure.

---

## Lua Modules (46 tests)

All 23 Lua files tested for validity and structure.

| File | Tests | What It Validates |
|------|-------|-------------------|
| world.lua | 2 | Core simulation, time |
| economy.lua | 2 | Financial simulation |
| social.lua | 2 | Relationships |
| agent_needs.lua | 2 | NPC needs system |
| factions.lua | 2 | Faction management |
| vehicles.lua | 2 | Transport system |
| occupations.lua | 2 | Job definitions |
| news_system.lua | 2 | Information spread |
| encounters.lua | 2 | Meeting/mission logic |
| universal_plugin.lua | 2 | Content loading |
| content_registry.lua | 2 | Dynamic registration |
| event_sourcing.lua | 2 | State management |
| ai_oracle.lua | 2 | LLM integration |
| canon_validator.lua | 2 | Lore consistency |
| echo_generator.lua | 2 | AR content |
| district.lua | 2 | Zone management |
| logging.lua | 2 | Debug output |
| founding_npcs.lua | 2 | Main characters |
| all_npcs.lua | 2 | Full NPC data |
| behaviors.lua | 2 | Behavior patterns |
| ... | ... | Additional modules |

### Per-Module Tests

For each Lua module:

1. **File Exists** - Module present in ao-processes/
2. **Syntax Valid** - No Lua syntax errors
3. **Handlers Present** - Handlers.add() calls exist
4. **Exports Present** - return {} at end

---

## Plugin System (10 tests)

| Test Name | What It Validates |
|-----------|------------------|
| Plugin Folder Exists | Directory present |
| Plugin Registration | register_plugin() function |
| Plugin Loading | load_plugin() function |
| Plugin Hooks | Hook system works |
| Plugin Events | Event firing works |
| Plugin Config | Configuration loading |
| Plugin Dependencies | Dependency resolution |
| Plugin Lifecycle | Init/cleanup hooks |
| Plugin API | API exposure |
| Plugin Types | Content types registry |

---

## Plugin Integration (3 tests)

| Test Name | What It Validates |
|-----------|------------------|
| Plugin Registration | Plugins can register |
| Hook System | Hooks/callbacks available |
| Event Firing | Events triggered |

### Plugin Structure

```lua
return {
    name = "my_plugin",
    version = "1.0",
    
    init = function(context)
        -- Called on plugin load
    end,
    
    hooks = {
        on_tick = function(tick)
            -- Called each world tick
        end,
        on_npc_action = function(npc, action)
            -- Called when NPC acts
        end
    },
    
    cleanup = function()
        -- Called on unload
    end
}
```

---

## Content Registry (8 tests)

| Test Name | What It Validates |
|-----------|------------------|
| Registry Exists | content_registry.lua |
| Register Function | register_content() |
| Query Function | query_content() |
| Type Categories | Content type enum |
| Validation | Schema checking |
| Caching | Content caching |
| Hot Reload | Dynamic updates |
| Dependencies | Content refs |

---

## Event Sourcing (7 tests)

CSM-inspired event logging for state reconstruction.

| Test Name | What It Validates |
|-----------|------------------|
| Event Sourcing File | event_sourcing.lua exists |
| Event Logging | log_event() function |
| State Reconstruction | rebuild_state() possible |
| Snapshot Creation | create_snapshot() |
| Event Types | Event type enum |
| Event Replay | replay_events() |
| Arweave Bundle | Bundle format valid |

### Event Structure

```lua
{
    event_type = "NPC_ACTION",
    tick = 1500,
    data = {
        npc_id = "NPC_042",
        action = "work",
        location = "L015"
    },
    timestamp = "2026-02-05T07:20:00Z"
}
```

---

## AI Oracle Integration (3 tests)

| Test Name | What It Validates |
|-----------|------------------|
| AI Oracle File | ai_oracle.lua exists |
| LLM Prompting | Prompt generation |
| Dialogue Generation | NPC dialogue creation |

---

## Canon Validation (2 tests)

| Test Name | What It Validates |
|-----------|------------------|
| Validator File | canon_validator.lua exists |
| Validation Rules | Canon rules defined |

---

## Echo Generation (2 tests)

| Test Name | What It Validates |
|-----------|------------------|
| Generator File | echo_generator.lua exists |
| Event Triggers | Echoes triggered by events |

---

## Logging System (2 tests)

| Test Name | What It Validates |
|-----------|------------------|
| Log Levels | Multiple log levels |
| Log Persistence | Logs saved |

---

## Content Loading (3 tests)

| Test Name | What It Validates |
|-----------|------------------|
| Content Registration | Content can register |
| Content Querying | Query functions |
| Schema Validation | Content validated |

---

*Part of the AO World Engine Test Suite*

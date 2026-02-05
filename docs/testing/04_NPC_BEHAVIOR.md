# NPC Behavior Tests (50 tests)

> **Updated:** 2026-02-05T07:20:00-05:00

Tests for NPC decision-making, needs, schedules, and behaviors.

---

## Agent Needs (7 tests)

Egregoria-inspired need system where NPCs have 7 basic needs that drive behavior.

| Test Name | What It Validates |
|-----------|------------------|
| 7 Need Types Exist | All needs defined |
| Need Decay Logic | Needs decrease over time |
| Activity Satisfaction | Activities restore needs |
| Critical Thresholds | Urgent need detection |
| Need Initialization | Starting values |
| Need Update Function | update_needs() exists |
| Need Priority Logic | Lowest need prioritized |

### The 7 Needs

| Need | Decay Rate | Satisfied By |
|------|------------|--------------|
| Hunger | 0.05/tick | Eating at food locations |
| Energy | 0.04/tick | Sleeping at home |
| Social | 0.02/tick | Talking to others |
| Money | 0.01/tick | Working |
| Safety | 0.03/tick | Being in safe zones |
| Purpose | 0.02/tick | Completing tasks |
| Comfort | 0.01/tick | Owning items |

### Need-Driven Logic

```lua
function find_urgent_need(npc)
    local lowest_need = nil
    local lowest_value = 1.0
    
    for need_name, value in pairs(npc.needs) do
        if value < lowest_value then
            lowest_value = value
            lowest_need = need_name
        end
    end
    
    -- Is it urgent? (below 0.2 threshold)
    if lowest_value < 0.2 then
        return lowest_need, true  -- urgent
    end
    return lowest_need, false
end
```

---

## NPC Behavior Logic (4 tests)

| Test Name | What It Validates |
|-----------|------------------|
| Decision Function | decide_action() exists |
| Activity Effects | Actions affect needs |
| Personality Influence | Traits modify behavior |
| Location Awareness | NPCs know where they are |

### Behavior Decision Tree

```
                    ┌─────────────────┐
                    │  Check Urgent   │
                    │     Needs       │
                    └────────┬────────┘
                             │
              ┌─────────────┬┴────────────┐
              ▼             ▼             ▼
         Hunger?        Energy?       Safety?
              │             │             │
              ▼             ▼             ▼
      Go to Food     Go to Sleep    Flee Danger
              │             │             │
              └─────────────┴─────────────┘
                             │
                    ┌────────▼────────┐
                    │  No Urgent Need │
                    │  Follow Schedule│
                    └─────────────────┘
```

---

## Occupation Behavior (4 tests)

| Test Name | What It Validates |
|-----------|------------------|
| Work Schedules | work_start, work_end hours |
| Wage Configuration | Wages defined per job |
| Skill Requirements | Jobs need skills |
| Location Assignment | Work locations |

### Occupations

| Occupation | Hours | Wage Range | Required Skills |
|------------|-------|------------|-----------------|
| Street Vendor | 06-18 | 20-50 | negotiation |
| Factory Worker | 06-14 | 30-60 | mechanics |
| Office Worker | 09-17 | 50-100 | admin |
| Security Guard | varies | 40-80 | combat |
| Medic | varies | 80-150 | medical |
| Hacker | varies | 100-300 | tech, decryption |

---

## Schedule Prediction (3 tests)

| Test Name | What It Validates |
|-----------|------------------|
| World Time Tracking | WorldTick, WorldDay |
| NPC Schedule Data | Routines defined |
| Work Hour Logic | Time-based activities |

### NPC Schedule Example

```lua
["NPC_042"] = {
    schedule = {
        ["T03"] = "commute_to_work",  -- 06:00-09:00
        ["T04"] = "work",              -- 09:00-12:00
        ["T05"] = "work",              -- 12:00-15:00
        ["T06"] = "work",              -- 15:00-18:00
        ["T07"] = "commute_home",      -- 18:00-20:00
        ["T08"] = "leisure",           -- 20:00-23:00
        ["T09"] = "sleep",             -- 23:00-00:00
        ["T01"] = "sleep",             -- 00:00-03:00
        ["T02"] = "sleep",             -- 03:00-06:00
    }
}
```

---

## Founding NPC Depth (4 tests)

| Test Name | What It Validates |
|-----------|------------------|
| Cast Count | ≥12 founding characters |
| Backstory Completeness | History documented |
| Relationship Network | Inter-character trust |
| Secrets and Motivations | Hidden character data |

---

## NPC Data Completeness (14 tests)

| Test Name | What It Validates |
|-----------|------------------|
| Required Fields | id, name, faction |
| Faction References | Valid faction IDs |
| Location References | Valid location codes |
| Occupation Assignment | Has job defined |
| Personality Traits | Traits object |
| Skills Assignment | Skills array |
| Relationship References | Trust values |
| Cybernetics Data | Implant tracking |
| Home Location | Residence defined |
| Work Location | Workplace defined |
| Knowledge Domains | Expertise areas |
| Catchphrases | Dialogue lines |
| Appearance | Visual description |
| Background | History/origin |

---

## Vehicle Behavior (3 tests)

| Test Name | What It Validates |
|-----------|------------------|
| Vehicle Types | 5+ types defined |
| Vehicle Registration | Vehicles tracked |
| Vehicle Stats | Speed, capacity |

---

*Part of the AO World Engine Test Suite*

# AI World Simulation - Comprehensive Test Suite

> **Purpose**: 30+ multi-step tests to validate all aspects of the AI simulation  
> **Coverage**: Time, NPCs, Economy, Social, Buildings, Persistence

---

## Test Categories Overview

| Category | Tests | What it validates |
|----------|-------|-------------------|
| 1. Time & Schedule | 5 | CRON, time periods, shift transitions |
| 2. NPC Movement | 5 | Location changes, state machine |
| 3. Social Interactions | 5 | Meetings, relationships, trust |
| 4. Economy | 5 | Wages, spending, city budget |
| 5. Location/Building | 5 | Building occupancy, social spots |
| 6. State Persistence | 5 | Data survives across ticks |
| 7. Edge Cases | 5 | Error handling, boundary conditions |

---

## Category 1: Time & Schedule Tests

### Test 1.1: Time Progression
**Purpose**: Verify tick advances correctly
```bash
# Get current tick
node scripts/send_ao_message.mjs get-state '{}'
# Advance 10 ticks
node scripts/send_ao_message.mjs advance-tick '{"ticks":10}'
# Verify tick increased by 10
node scripts/send_ao_message.mjs get-state '{}'
```
**Expected**: Tick increases by exactly 10

### Test 1.2: Day Transition
**Purpose**: Verify day changes after 24 ticks
```bash
# Note current day
node scripts/send_ao_message.mjs get-state '{}'
# Advance 24 ticks (1 full day)
node scripts/send_ao_message.mjs advance-tick '{"ticks":24}'
# Verify day increased by 1
node scripts/send_ao_message.mjs get-state '{}'
```
**Expected**: Day increases by 1

### Test 1.3: Year Transition
**Purpose**: Verify year changes after 8760 ticks
```bash
# Note current year
node scripts/send_ao_message.mjs get-state '{}'
# Advance to next year (may skip for performance)
node scripts/send_ao_message.mjs advance-tick '{"ticks":8760}'
# Verify year increased
node scripts/send_ao_message.mjs get-state '{}'
```
**Expected**: Year increases by 1

### Test 1.4: Time Period Accuracy
**Purpose**: Verify time periods match hours
```bash
# Advance to hour 8 (morning)
# Check time_info returns "morning"
# Advance to hour 20 (night)
# Check time_info returns "night"
```
**Expected**: Time periods match hour ranges

### Test 1.5: Shift Schedule Accuracy
**Purpose**: Verify NPCs follow their shift schedules
```bash
# Get NPC with night shift (security guard)
node scripts/send_ao_message.mjs get-npc-locations '{}'
# Check at hour 2 → should be working
# Check at hour 14 → should be sleeping
```
**Expected**: State matches shift type

---

## Category 2: NPC Movement Tests

### Test 2.1: Home to Work Transition
**Purpose**: NPCs commute at correct hours
```bash
# Advance to hour 8 (day shift start)
# Check NPC locations - should be moving to work
node scripts/send_ao_message.mjs get-movement-log '{"limit":20}'
```
**Expected**: Movement log shows home→work transitions

### Test 2.2: Work to Home Transition
**Purpose**: NPCs return home after shift
```bash
# Advance to hour 18 (day shift end)
# Check NPC locations - should be moving home or socializing
node scripts/send_ao_message.mjs get-npc-locations '{}'
```
**Expected**: NPCs at home, social locations, or commuting

### Test 2.3: Night Shift Reversal
**Purpose**: Night workers have inverted schedule
```bash
# Get security guard NPC
# At hour 2: should be at work (L042)
# At hour 14: should be at home sleeping
```
**Expected**: Opposite pattern to day workers

### Test 2.4: Social Location Selection
**Purpose**: NPCs visit social spots in evening
```bash
# Advance to hour 20
# Check NPC states - some should be "socializing"
# Check locations - should be in SOCIAL_LOCATIONS list
```
**Expected**: 30%+ NPCs at social spots

### Test 2.5: Movement Log Accuracy
**Purpose**: All movements are logged
```bash
# Get movement log before advance
node scripts/send_ao_message.mjs get-movement-log '{"limit":10}'
# Advance 10 ticks
# Get movement log after
# Compare logs
```
**Expected**: New movements appear in log

---

## Category 3: Social Interaction Tests

### Test 3.1: Same-Location Detection
**Purpose**: NPCs at same location interact
```bash
# Get interactions before
node scripts/send_ao_message.mjs get-interactions '{"limit":20}'
# Advance 50 ticks
# Get interactions after
node scripts/send_ao_message.mjs get-interactions '{"limit":20}'
```
**Expected**: InteractionLog grows when NPCs meet

### Test 3.2: Relationship Growth
**Purpose**: Repeated meetings increase relationship score
```bash
# Get relationship history
# Find two NPCs who have met
# Advance simulation with both at same location
# Check relationship score increased
```
**Expected**: Relationship score grows (0.01-0.03 per meeting)

### Test 3.3: Interaction Types
**Purpose**: Correct type assigned based on state
```bash
# Get interactions
# Filter for "social" type - should be when state=socializing
# Filter for "professional" type - should be when state=working
```
**Expected**: Types match NPC states

### Test 3.4: Cooldown Enforcement
**Purpose**: NPCs don't interact twice in 10 ticks
```bash
# Find two NPCs at same location
# Note last interaction tick
# Advance 5 ticks
# Verify no new interaction
# Advance 10 more ticks
# Verify new interaction created
```
**Expected**: 10-tick cooldown between same-pair interactions

### Test 3.5: Top Relationships Query
**Purpose**: Query returns strongest relationships
```bash
node scripts/send_ao_message.mjs get-interactions '{"limit":5}'
# Check top_relationships sorted by score
```
**Expected**: Relationships sorted descending by score

---

## Category 4: Economy Tests

### Test 4.1: Wage Distribution
**Purpose**: NPCs receive wages at shift end
```bash
# Get wallet before shift end
node scripts/send_ao_message.mjs get-npc-wallets '{"limit":10}'
# Advance to shift end (hour 17 for day workers)
# Get wallet after
```
**Expected**: Balance increased by archetype wage

### Test 4.2: Spending at Social Locations
**Purpose**: NPCs spend money when socializing
```bash
# Get NPC wallets
# Advance to evening hours with NPCs socializing
# Check transaction log for spending
node scripts/send_ao_message.mjs get-npc-wallets '{"limit":20}'
```
**Expected**: Spending transactions (20-50 GEP) in log

### Test 4.3: City Budget Tax Flow
**Purpose**: NPC spending increases city budget
```bash
# Get city budget
node scripts/send_ao_message.mjs get-economy '{}'
# Advance with NPC spending
# Get city budget after
```
**Expected**: City budget increased by spending * TaxRate

### Test 4.4: Archetype Wage Accuracy
**Purpose**: Correct wages per archetype
```bash
# Get wallet for security guard
# Advance through wage cycle
# Verify received 200 GEP (security guard rate)
```
**Expected**: Wages match ARCHETYPE_WAGES table

### Test 4.5: Transaction Log Accuracy
**Purpose**: All transactions logged
```bash
# Get transaction log
node scripts/send_ao_message.mjs get-npc-wallets '{"limit":50}'
# Verify wage and spending entries have correct fields
```
**Expected**: Entries have tick, npc_id, type, amount, balance

---

## Category 5: Location/Building Tests

### Test 5.1: Location Code Validity
**Purpose**: All NPCs at valid locations
```bash
# Get all NPC locations
node scripts/send_ao_message.mjs get-npc-locations '{}'
# Verify all location codes match pattern L###
```
**Expected**: All locations are valid codes

### Test 5.2: Work Location Occupancy
**Purpose**: NPCs at work during work hours
```bash
# Advance to hour 10
# Get all NPC locations
# Count NPCs at work locations
```
**Expected**: Day-shift workers at work locations

### Test 5.3: Social Location Capacity
**Purpose**: Multiple NPCs can be at social spots
```bash
# Advance to hour 20
# Get location groups
# Check SOCIAL_LOCATIONS have multiple NPCs
```
**Expected**: Social spots have 2+ NPCs

### Test 5.4: Home Location Uniqueness
**Purpose**: NPCs have distinct homes (or shared as designed)
```bash
# Get all schedules
# Count unique home locations
```
**Expected**: Home assignments match design

### Test 5.5: Location State Consistency
**Purpose**: State matches location type
```bash
# NPCs at work → state should be "working"
# NPCs at home at night → state should be "sleeping"
# NPCs at social → state should be "socializing"
```
**Expected**: State/location alignment

---

## Category 6: State Persistence Tests

### Test 6.1: Wallet Balance Persistence
**Purpose**: Wallet balance survives ticks
```bash
# Get wallet balance
# Advance 100 ticks
# Get wallet balance again
# Verify consistent (adjusted for wages/spending)
```
**Expected**: Balance persists correctly

### Test 6.2: Relationship History Persistence
**Purpose**: Social history survives ticks
```bash
# Get NPCSocialHistory
# Advance 100 ticks
# Get NPCSocialHistory again
# Verify past relationships still exist
```
**Expected**: All relationship data persists

### Test 6.3: Schedule Data Persistence
**Purpose**: Loaded schedules persist
```bash
# Get NPCSchedules count
# Advance 1000 ticks
# Get NPCSchedules count
# Verify same count
```
**Expected**: Schedules never lost

### Test 6.4: Log Trimming Works
**Purpose**: Logs don't grow infinitely
```bash
# Advance 5000 ticks
# Check MovementLog.length <= MAX_MOVEMENT_LOG (1000)
# Check InteractionLog.length <= MAX_INTERACTION_LOG (500)
```
**Expected**: Logs capped at max values

### Test 6.5: World State Consistency
**Purpose**: WorldTick/Day/Year stay consistent
```bash
# Get state, note tick/day/year
# Advance 100 ticks
# Verify tick = old_tick + 100
# Verify day = old_day + (100/24) when applicable
```
**Expected**: Perfect arithmetic consistency

---

## Category 7: Edge Case Tests

### Test 7.1: Empty Schedule Handling
**Purpose**: NPCs without schedules don't crash
```bash
# Query NPC without loaded schedule
# Verify graceful handling
```
**Expected**: No errors, NPC skipped

### Test 7.2: Zero Balance Spending
**Purpose**: NPCs with 0 balance don't overspend
```bash
# Find NPC with very low balance
# Advance through spending cycle
# Verify balance never goes negative
```
**Expected**: Balance >= 0 always

### Test 7.3: Large Tick Advance
**Purpose**: System handles large advances
```bash
# Advance 1000 ticks at once
node scripts/send_ao_message.mjs advance-tick '{"ticks":1000}'
# Verify state still valid
```
**Expected**: No timeout, state correct

### Test 7.4: Concurrent Location Updates
**Purpose**: Multiple NPCs move simultaneously
```bash
# Advance through shift change (many movements)
# Verify all locations updated correctly
```
**Expected**: No race conditions

### Test 7.5: Handler Error Recovery
**Purpose**: Invalid input doesn't crash system
```bash
# Send malformed data
node scripts/send_ao_message.mjs get-npc-locations '{"invalid":true}'
# Verify system still responds
node scripts/send_ao_message.mjs get-state '{}'
```
**Expected**: Graceful error handling

---

## Running All Tests

### Quick Validation (5 min)
```bash
# Run critical path tests
./scripts/test_quick.sh
```

### Full Suite (30 min)
```bash
# Run all 35 tests
./scripts/test_full.sh
```

### Individual Test
```bash
# Run specific test
node scripts/send_ao_message.mjs [action] '[data]'
```

---

## Test Results Template

| Test ID | Name | Status | Notes |
|---------|------|--------|-------|
| 1.1 | Time Progression | ✅/❌ | |
| 1.2 | Day Transition | ✅/❌ | |
| ... | ... | ✅/❌ | |

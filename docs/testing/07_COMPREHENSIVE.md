# Comprehensive Tests (137 tests)

> **Updated:** 2026-02-05T07:20:00-05:00

Deep validation tests for file integrity, consistency, and coverage.

---

## File Audit (87 tests)

Validates every file in the project.

### Lua Syntax Validation (23 tests)

For each `.lua` file in `ao-processes/`:

| Check | What It Validates |
|-------|-------------------|
| File Exists | Lua file present |
| Syntax Valid | No parse errors |

### JSON Validity (25 tests)

For each `.json` file in `data/codec_chunks/`:

| Check | What It Validates |
|-------|-------------------|
| Valid JSON | Parses correctly |
| Has Content | Not empty |

### Export Verification (23 tests)

| Check | What It Validates |
|-------|-------------------|
| Has Exports | `return {}` present |
| Has Handlers | `Handlers.add` calls |

### Required Files (10 tests)

| File | Purpose |
|------|---------|
| world.lua | Core simulation |
| economy.lua | Economic system |
| social.lua | Relationships |
| factions.lua | Faction system |
| all_npcs.lua | NPC data |
| world_codec.json | Combined codec |
| ... | ... |

---

## Consistency Tests (8 tests)

Cross-file validation ensuring data integrity.

| Test Name | What It Validates |
|-----------|------------------|
| Faction IDs Defined | All factions exist |
| NPC ID Uniqueness | No duplicate IDs |
| Occupation IDs Defined | All jobs registered |
| Vehicle Type Consistency | Types match registry |
| Marker System Coverage | Markers complete |
| District System Validation | Districts valid |
| Cross-File Reference Integrity | All refs resolve |
| Schema Version Compatibility | Versions match |

### Example: ID Uniqueness Check

```python
def check_npc_uniqueness(self):
    all_npcs_path = AO_DIR / "all_npcs.lua"
    content = all_npcs_path.read_text()
    
    # Extract all NPC IDs
    npc_ids = re.findall(r'\["(NPC_[^"]+)"\]', content)
    unique_ids = set(npc_ids)
    
    self.record(TestResult(
        category="Consistency",
        test_name="NPC ID Uniqueness",
        method="schema",
        passed=len(npc_ids) == len(unique_ids),
        message=f"{len(unique_ids)}/{len(npc_ids)} unique IDs"
    ))
```

---

## Persistence Tests (9 tests)

State serialization and recovery.

| Test Name | What It Validates |
|-----------|------------------|
| Event Serialization | json.encode() present |
| Snapshot Creation | State checkpoint logic |
| Arweave Bundle Format | Bundle structure |
| Event Log Storage | Log persistence |
| World State Storage | State save/load |
| NPC State Management | Per-NPC persistence |
| Relationship Persistence | Trust values saved |
| Economic State Persistence | Budget saved |
| Time State Persistence | Tick/day/year saved |

---

## Coverage Tests (33 tests)

Field and feature completeness.

| Test Name | What It Validates |
|-----------|------------------|
| NPC Field Coverage | All required fields |
| Faction Field Coverage | Faction data complete |
| Vehicle Field Coverage | Vehicle data complete |
| Occupation Field Coverage | Job data complete |
| Building Field Coverage | Building data complete |
| District Field Coverage | District data complete |
| ... | Additional coverage checks |

### Coverage Calculation

```python
def calculate_field_coverage(entity, required_fields):
    present = sum(1 for f in required_fields if f in entity)
    total = len(required_fields)
    return present / total * 100
```

---

## Adding New Tests

### Template

```python
def test_your_system(self):
    """Test description."""
    print("\n🆕 Testing Your System...")
    
    file_path = AO_DIR / "your_file.lua"
    
    if file_path.exists():
        content = file_path.read_text()
        
        # Test 1: Check for feature
        has_feature = "feature_name" in content
        self.record(TestResult(
            category="Your Category",
            test_name="Feature Exists",
            method="integration",
            passed=has_feature,
            message="Found" if has_feature else "Missing"
        ))
```

### Adding to run_all()

```python
def run_all(self):
    # ... existing tests ...
    self.test_your_system()  # Add new test here
    # ...
```

---

## Test Data Locations

| Path | Contents |
|------|----------|
| `ao-processes/test_data/` | Mock data |
| `data/codec_chunks/` | World definition |
| `data/world_codec.json` | Combined codec |
| `logs/audit_results.json` | Test output |
| `logs/audit_summary.md` | Human summary |

---

*Part of the AO World Engine Test Suite*

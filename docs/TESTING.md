# AO World Engine - Testing Documentation

> **Last Updated:** 2026-02-05T07:55:00-05:00  
> **Version:** 5.2  
> **Total Tests:** 540  
> **Pass Rate:** 100%

---

## Quick Start

```bash
# Run the full test suite
python3 scripts/system_audit.py

# Output files:
# - logs/audit_results.json  (machine-readable)
# - logs/audit_summary.md    (human-readable)
```

---

## Documentation Structure

For detailed test documentation, see:

| Document | Tests | Coverage |
|----------|-------|----------|
| [Core Tests](testing/01_CORE_TESTS.md) | 66 | NPCs, buildings, districts |
| [Economy Tests](testing/02_ECONOMY_TESTS.md) | 35 | Currencies, taxes, budget |
| [Social Tests](testing/03_SOCIAL_TESTS.md) | 25 | Relationships, gossip, trust |
| [NPC Behavior](testing/04_NPC_BEHAVIOR.md) | 50 | Needs, decisions, schedules |
| [Infrastructure](testing/05_INFRASTRUCTURE.md) | 100 | Lua modules, plugins |
| [Behavioral AI](testing/06_BEHAVIORAL_AI.md) | 27 | AI decision logic |
| [Comprehensive](testing/07_COMPREHENSIVE.md) | 137 | File audit, consistency |
| [Living World](testing/08_LIVING_WORLD.md) | 77 | World simulation |
| [**Stochastic**](testing/09_STOCHASTIC_TESTS.md) | **15** | **Randomness, variance** |

---

## Version History

| Date | Version | Tests | Changes |
|------|---------|-------|---------|
| 2026-02-05 | 5.0 | 517 | Beta test suite expansion |
| 2026-02-04 | 4.0 | 404 | Behavioral AI, file audit |
| 2026-02-03 | 3.0 | 377 | Pluggable systems |
| 2026-02-02 | 2.0 | 234 | Living world tests |
| 2026-02-01 | 1.0 | 150 | Initial audit |

---

## Test Methods

| Method | Description | Example |
|--------|-------------|---------|
| `schema` | Validates data structure | NPC has required fields |
| `completeness` | Checks quantity/coverage | ≥800 NPCs exist |
| `integration` | Tests connections work | Handler exists in module |

---

## Categories Overview (57 total)

### High-Volume Categories

| Category | Tests | Description |
|----------|-------|-------------|
| File Audit | 87 | Lua syntax, JSON validity |
| Lua Modules | 46 | All 23 AO process modules |
| Coverage | 33 | Field coverage validation |
| Behavioral AI | 27 | Need-driven decisions |
| AO Processes | 18 | Handler verification |
| Founding Cast | 14 | Main story characters |
| NPC Data | 14 | Field completeness |
| Factions | 13 | 7 factions, territories |
| Vehicles | 13 | 7 vehicle types |
| Occupations | 14 | 14 job types |
| Living World | 11 | Dynamic simulation |

---

## Running Individual Test Modules

```python
# Import specific test suite
from scripts.tests.test_economy import EconomyTestSuite
from scripts.tests.test_social import SocialTestSuite

# Run specific tests
economy_tests = EconomyTestSuite()
economy_tests.run_all()
results, stats = economy_tests.get_results()
```

---

## Adding New Tests

See [07_COMPREHENSIVE.md](testing/07_COMPREHENSIVE.md#adding-new-tests) for the test template.

---

*Documentation updated: 2026-02-05*

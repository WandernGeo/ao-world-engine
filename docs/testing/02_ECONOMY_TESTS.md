# Economy Tests (35 tests)

> **Updated:** 2026-02-05T07:20:00-05:00

Tests for the complex economic simulation from `world_codec_20_economy.json`.

---

## Economy Simulation (10 tests)

| Test Name | What It Validates | Pass Criteria |
|-----------|------------------|---------------|
| Currency Systems | Multiple currencies | GEP, DCH, TPC, CSC |
| Progressive Tax Brackets | Tax rates | 0%, 5%, 10%, 15%, 20% |
| Zone Types Defined | Zoning system | ≥8 of 12 zone types |
| Raw Materials Chain | Production input | scrap, petrochemicals, rare_earth |
| Processed Goods Chain | Production output | alloy, polymers, electronics |
| Budget Categories | City spending | ≥4 categories |
| Crisis Level System | Budget states | healthy → collapse |
| Economic Indicators | Metrics | GDP, inflation, unemployment |
| Economic Functions | Core calculations | tax, land_value functions |
| Employment Skill Levels | Wage tiers | low, mid, high, elite |

### Currency System (from codec)

```json
{
  "currencies": {
    "GEP": {
      "name": "Global Economic Points",
      "description": "Primary digital currency",
      "denominations": [1, 5, 10, 50, 100, 500, 1000]
    },
    "DCH": {
      "name": "Data Chips",
      "description": "Underground currency for hackers"
    },
    "TPC": {
      "name": "Temple Credits",
      "description": "Religious institution currency"
    },
    "CSC": {
      "name": "Corp Scrip",
      "description": "Corporate-issued tokens"
    }
  }
}
```

---

## Tax System (5 tests)

| Test Name | What It Validates | Pass Criteria |
|-----------|------------------|---------------|
| Income Tax Brackets | Progressive rates | 5 brackets defined |
| Property Tax | Land taxation | rate < 0.03 |
| Sales Tax | Transaction tax | rate ~0.08 |
| Temple Tithe | Religious levy | rate ~0.10 |
| Tax Collection | Revenue function | collect_taxes() exists |

### Progressive Tax Brackets

```
Income Range    | Rate  | Example
----------------|-------|--------
0 - 500 GEP     | 0%    | Poor workers exempt
500 - 2,000     | 5%    | Low income
2,000 - 10,000  | 10%   | Middle income
10,000 - 50,000 | 15%   | High income
50,000+         | 20%   | Elite/Corporate
```

---

## Budget System (4 tests)

| Test Name | What It Validates |
|-----------|------------------|
| Budget Tracking | Total city budget tracked |
| Allocation Categories | 6 spending categories |
| Service Level Effects | Funding affects services |
| Expense Calculation | calculate_expenses() exists |

### Budget Categories

1. **Law Enforcement** - Police, security
2. **Infrastructure** - Roads, power, water
3. **Healthcare** - Hospitals, clinics
4. **Education** - Schools, training
5. **Social Services** - UBI, welfare
6. **Temple Services** - Religious functions

---

## Megacorporation Mechanics (5 tests)

| Test Name | What It Validates |
|-----------|------------------|
| Megacorps Defined | 4 corporations exist |
| Market Share Tracking | Sector percentages |
| Employee Counts | 5000-25000 per corp |
| Sector Assignments | Industry sectors |
| Dynamic Corp Updates | Growth/contraction |

### Corporation Data

| Corporation | Sector | Market Share | Employees |
|-------------|--------|--------------|-----------|
| NexGen Industries | Cybernetics | 40% | 15,000 |
| Omnicorp | Infrastructure | 60% | 25,000 |
| Synthetica | Biotech | 35% | 8,000 |
| DataVault Securities | Information | 50% | 5,000 |

---

## Black Market (5 tests)

| Test Name | What It Validates |
|-----------|------------------|
| Black Market System | Underground exists |
| Underground GDP | ~25% of city GDP |
| Protection Fees | 15% to bosses |
| Underground Sectors | 5 black market sectors |
| Dynamic Growth | Grows with unemployment |

### Underground Sectors

1. **Drugs** - Stims, neural enhancers
2. **Weapons** - Illegal firearms, tech
3. **Stolen Goods** - Fenced items
4. **Data** - Black market info
5. **Services** - Illegal services

---

## Production Chain Tests (6 tests)

| Test Name | What It Validates |
|-----------|------------------|
| Raw Materials | Input resources defined |
| Processed Goods | Intermediate products |
| Finished Goods | Final products |
| Chain Links | Dependencies correct |
| Factory Logic | Production functions |
| Supply/Demand | Market mechanics |

### Production Chain

```
RAW MATERIALS          PROCESSED GOODS         FINISHED PRODUCTS
─────────────────────────────────────────────────────────────────
Scrap Metal     →      Metal Alloy      →      Cybernetics
Petrochemicals  →      Polymers         →      Consumer Goods  
Rare Earth      →      Electronics      →      Computing Devices
Organics        →      Biocompounds     →      Medical Supplies
```

---

*Part of the AO World Engine Test Suite*

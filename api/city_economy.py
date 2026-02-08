"""
RE:ECHO City Economy Engine — Plugin-Ready Municipal Finance Simulation
=========================================================================

A Cities: Skylines-depth economy engine for the AO World Engine.

All calculations are **deterministic**: same tick → same numbers.
Uses seeded hashing (MD5) for variance so the economy feels alive but is
reproducible and verifiable on-chain (Arweave/AO).

Revenue Streams (13+):
    1. Residential Income Tax    (progressive brackets)
    2. Commercial License Fees   (per business)
    3. Industrial Permits        (by zone tier)
    4. Property Tax              (assessed land value)
    5. Sales Tax                 (5% non-exempt transactions)
    6. Corporate Tax             (12% nominal / 3% effective)
    7. Parking Meters            (zone-density based)
    8. Transit Fares             (per-ride × ridership)
    9. Import Tariffs            (10-25% by category)
   10. Temple Tithe              (5% all citizen income — passed through)
   11. Fines & Penalties         (crime-based)
   12. Sin Taxes                 (alcohol, drugs, gambling)
   13. Utility Surcharges        (power, water, waste, data)

Expenditure Categories (9):
    1. Law Enforcement   (22%)  — patrol, detectives, riot, cyber-crime, drones
    2. Infrastructure    (18%)  — roads, power, water, sewer, lighting, bridges
    3. Public Transit    (12%)  — subway, bus, tram, ferry operating subsidies
    4. Healthcare        (12%)  — clinics, EMT, disease control, mental health
    5. Sanitation        (8%)   — garbage, street cleaning, hazmat, recycling
    6. Education         (10%)  — schools, training (Temple-controlled)
    7. Social Services   (8%)   — UBI, housing aid, job training, food aid
    8. Administration    (5%)   — gov salaries, 15% corruption overhead
    9. Emergency Fund    (5%)   — reserve target ◊100,000

Fiscal Calendar:
    - Quarterly budget cycles (Q1-Q4) with seasonal modifiers
    - Tax collection schedules (income=biweekly, property=quarterly, etc.)
    - Payroll schedule (biweekly for employees, net-30 for contractors)
    - Budget approval process (council vote by day 355)

Transit System:
    - 3 subway lines (Red, Blue, Green) — total daily cost ~◊12,260
    - 15 bus routes, 40 buses — total daily cost ~◊9,100
    - Heritage tram (Neon District loop) — daily cost ~◊1,340
    - Water ferry (3 vessels) — daily cost ~◊1,290
    - Total transit: ~◊23,990/day, 55% cost recovery from fares

Plugin Interface:
    class EconomyPlugin:
        def on_tick(self, tick, state) -> dict
        def on_event(self, event_type, data) -> dict
"""

import hashlib
import math
from typing import Dict, List, Optional, Any


# =============================================================================
# DETERMINISTIC SEEDING
# =============================================================================

def _seed(key: str) -> int:
    """Get a deterministic integer seed from a string key."""
    return int(hashlib.md5(key.encode()).hexdigest(), 16)


def _seeded_float(key: str, lo: float = 0.0, hi: float = 1.0) -> float:
    """Deterministic float in [lo, hi) from key."""
    s = _seed(key)
    return lo + (s % 10000) / 10000 * (hi - lo)


def _seeded_int(key: str, lo: int, hi: int) -> int:
    """Deterministic int in [lo, hi] from key."""
    s = _seed(key)
    return lo + (s % (hi - lo + 1))


def _variance(base: float, pct: float, key: str) -> float:
    """Apply ±pct variance to base using deterministic key."""
    delta = _seeded_float(key, -pct, pct)
    return base * (1 + delta)


# =============================================================================
# TAX CONFIGURATION (from codec_20)
# =============================================================================

INCOME_TAX_BRACKETS = [
    {"min": 0,     "max": 500,    "rate": 0.00},
    {"min": 500,   "max": 2000,   "rate": 0.05},
    {"min": 2000,  "max": 10000,  "rate": 0.10},
    {"min": 10000, "max": 50000,  "rate": 0.15},
    {"min": 50000, "max": float("inf"), "rate": 0.20},
]

PROPERTY_TAX_RATE = 0.02
SALES_TAX_RATE = 0.05
CORPORATE_TAX_NOMINAL = 0.12
CORPORATE_TAX_EFFECTIVE = 0.03  # After loopholes
TEMPLE_TITHE_RATE = 0.05

SIN_TAX_RATES = {
    "alcohol": 0.15,
    "recreational_drugs": 0.25,
    "gambling": 0.20,
    "cybernetic_vanity": 0.10,
}

IMPORT_TARIFF_RATES = {
    "food": 0.10,
    "raw_materials": 0.12,
    "luxury_goods": 0.25,
    "tech_components": 0.08,
    "weapons": 0.30,
}


# =============================================================================
# ZONE DEFINITIONS (from codec_20)
# =============================================================================

ZONE_LAND_VALUES = {
    "ZONE_R4": 5.0,   # Luxury Arcology
    "ZONE_C3": 4.0,   # Corporate Plaza
    "ZONE_IT": 3.0,   # Tech Park
    "ZONE_R1": 2.0,   # Low-Density Hab
    "ZONE_C2": 1.5,   # Commercial District
    "ZONE_R2": 1.0,   # Medium-Density Hab
    "ZONE_C1": 0.8,   # Street-Level Commerce
    "ZONE_I1": 0.6,   # Light Industry
    "ZONE_R3": 0.5,   # High-Density Megablock
    "ZONE_I2": 0.3,   # Heavy Industry
    "ZONE_I3": 0.1,   # Hazardous Processing
    "ZONE_U":  0.05,  # Undercity
}

PARKING_RATES_PER_DAY = {
    "ZONE_C3": 15,   # Corporate Plaza — premium
    "ZONE_C2": 10,   # Commercial District
    "ZONE_C1": 5,    # Street-Level
    "ZONE_R4": 8,    # Luxury Arcology
    "ZONE_IT": 6,    # Tech Park
    "ZONE_R2": 3,    # Medium Residential
    "ZONE_R3": 2,    # High-Density
}


# =============================================================================
# FISCAL CALENDAR & SEASONAL MODIFIERS
# =============================================================================

FISCAL_QUARTERS = {
    "Q1": {"days": (1, 91),    "label": "Winter Quarter",  "budget_modifier": 1.15},
    "Q2": {"days": (92, 182),  "label": "Spring Quarter",  "budget_modifier": 0.95},
    "Q3": {"days": (183, 274), "label": "Summer Quarter",  "budget_modifier": 1.05},
    "Q4": {"days": (275, 365), "label": "Autumn Quarter",  "budget_modifier": 1.00},
}

SEASONAL_MODIFIERS = {
    "Q1": {
        "heating_cost": 1.40, "road_repair": 0.50, "transit_ridership": 0.85,
        "outdoor_commerce": 0.60, "crime": 0.80, "tourism": 0.40,
        "water_usage": 0.80, "power_demand": 1.30,
    },
    "Q2": {
        "heating_cost": 0.80, "road_repair": 1.50, "transit_ridership": 1.00,
        "outdoor_commerce": 1.10, "crime": 1.00, "tourism": 0.80,
        "water_usage": 1.00, "power_demand": 0.90,
    },
    "Q3": {
        "heating_cost": 0.20, "cooling_cost": 1.20, "road_repair": 1.20,
        "transit_ridership": 1.10, "outdoor_commerce": 1.30, "crime": 1.15,
        "tourism": 1.50, "water_usage": 1.40, "power_demand": 1.10,
    },
    "Q4": {
        "heating_cost": 1.00, "road_repair": 0.80, "transit_ridership": 0.95,
        "outdoor_commerce": 0.90, "crime": 0.95, "tourism": 0.70,
        "water_usage": 0.90, "power_demand": 0.95,
    },
}

TAX_COLLECTION_SCHEDULE = {
    "income_tax":        {"frequency": "biweekly",  "collection_day": 14},
    "property_tax":      {"frequency": "quarterly", "due_days": [45, 136, 227, 318], "late_penalty": 0.02},
    "sales_tax":         {"frequency": "daily",     "remittance": "monthly_by_day_15"},
    "corporate_tax":     {"frequency": "quarterly", "due_days": [90, 181, 273, 365]},
    "commercial_license": {"frequency": "annual",   "renewal_window": (1, 30)},
}

PAYROLL_SCHEDULE = {
    "pay_frequency": "biweekly",
    "pay_periods_per_year": 26,
    "overtime_multiplier": 1.5,
    "holiday_multiplier": 2.0,
    "night_shift_differential": 1.15,
}


# =============================================================================
# PUBLIC TRANSIT SYSTEM
# =============================================================================

TRANSIT_SYSTEM = {
    "subway": {
        "lines": {
            "red_line":   {"stations": 12, "length_km": 18, "daily_ridership": 8000, "freq_peak": 5, "freq_offpeak": 12},
            "blue_line":  {"stations": 15, "length_km": 22, "daily_ridership": 10000, "freq_peak": 4, "freq_offpeak": 10},
            "green_line": {"stations": 8,  "length_km": 14, "daily_ridership": 4000, "freq_peak": 8, "freq_offpeak": 15},
        },
        "costs": {
            "driver_salary": 160,  # per driver per day
            "drivers_per_line": 8,
            "electricity_per_km_per_train": 5,
            "trains_per_line": 6,
            "rolling_stock_maintenance": 800,
            "track_maintenance": 400,
            "station_maintenance": 300,
            "security_per_station": 130,
            "cleaning_per_station": 50,
        },
    },
    "bus": {
        "routes": 15,
        "buses": 40,
        "daily_ridership": 6000,
        "costs": {
            "driver_salary": 120,
            "drivers": 50,
            "fuel_per_bus": 40,
            "maintenance_per_bus": 25,
            "depot_operations": 500,
        },
    },
    "tram": {
        "stops": 6,
        "length_km": 4,
        "daily_ridership": 3000,
        "costs": {
            "driver_salary": 140,
            "drivers": 6,
            "electricity": 200,
            "maintenance": 300,
        },
    },
    "ferry": {
        "vessels": 3,
        "daily_ridership": 1200,
        "costs": {
            "crew_per_vessel": 300,
            "fuel_per_vessel": 80,
            "dock_maintenance": 150,
        },
        "seasonal_service": {"Q1": 0.60, "Q2": 0.90, "Q3": 1.00, "Q4": 0.80},
    },
    "cost_recovery_from_fares": 0.55,
}

# Utility surcharge rates
UTILITY_SURCHARGES = {
    "power":          {"rate_per_unit": 0.02, "city_share": 0.15, "avg_daily_units_per_capita": 8},
    "water":          {"rate_per_unit": 0.01, "city_share": 0.20, "avg_daily_units_per_capita": 5},
    "waste_disposal": {"flat_monthly": 15,   "city_share": 0.30},
    "data_network":   {"rate_per_unit": 0.005, "city_share": 0.10, "avg_daily_units_per_capita": 12},
}


# =============================================================================
# DISTRICT CONFIGURATION (from codec_25)
# =============================================================================

DISTRICTS = {
    "neon_district":   {"code": "D01", "pop": 400, "zone": "ZONE_C3", "income_avg": 300, "commercial_density": 0.8, "industrial_density": 0.1},
    "harbor_quarter":  {"code": "D02", "pop": 450, "zone": "ZONE_R2", "income_avg": 100, "commercial_density": 0.3, "industrial_density": 0.4},
    "temple_heights":  {"code": "D03", "pop": 350, "zone": "ZONE_R1", "income_avg": 150, "commercial_density": 0.4, "industrial_density": 0.1},
    "old_town":        {"code": "D04", "pop": 400, "zone": "ZONE_R2", "income_avg": 120, "commercial_density": 0.4, "industrial_density": 0.2},
    "industrial_zone": {"code": "D05", "pop": 350, "zone": "ZONE_I1", "income_avg": 80,  "commercial_density": 0.1, "industrial_density": 0.8},
    "the_gardens":     {"code": "D06", "pop": 380, "zone": "ZONE_R1", "income_avg": 140, "commercial_density": 0.5, "industrial_density": 0.1},
    "tech_quarter":    {"code": "D07", "pop": 300, "zone": "ZONE_IT", "income_avg": 250, "commercial_density": 0.6, "industrial_density": 0.3},
    "outskirts":       {"code": "D08", "pop": 200, "zone": "ZONE_U",  "income_avg": 40,  "commercial_density": 0.1, "industrial_density": 0.1},
}

# City workforce counts (from codec_25 governance.departments)
CITY_EMPLOYEES = {
    "police":         {"count": 30, "avg_salary": 150},
    "fire_rescue":    {"count": 20, "avg_salary": 140},
    "public_health":  {"count": 15, "avg_salary": 160},
    "education":      {"count": 25, "avg_salary": 120},
    "infrastructure": {"count": 20, "avg_salary": 130},
    "sanitation":     {"count": 15, "avg_salary": 100},
    "admin":          {"count": 10, "avg_salary": 180},
}

# Megacorporation data (from codec_20)
MEGACORPS = {
    "NexGen":    {"sector": "cybernetics",     "employees": 15000, "market_share": 0.40, "annual_revenue": 8_000_000},
    "Omnicorp":  {"sector": "infrastructure",  "employees": 25000, "market_share": 0.60, "annual_revenue": 15_000_000},
    "Synthetica": {"sector": "biotech",        "employees": 8000,  "market_share": 0.35, "annual_revenue": 5_000_000},
    "DataVault": {"sector": "information",     "employees": 5000,  "market_share": 0.50, "annual_revenue": 3_000_000},
}

# Import dependencies (from codec_20 trade_and_import)
IMPORT_CATEGORIES = {
    "food":            {"local_prod": 0.4, "import_dep": 0.6, "base_cost": 5000,  "volatility": 0.2},
    "raw_materials":   {"local_prod": 0.2, "import_dep": 0.8, "base_cost": 8000,  "volatility": 0.3},
    "luxury_goods":    {"local_prod": 0.1, "import_dep": 0.9, "base_cost": 3000,  "volatility": 0.4},
    "tech_components": {"local_prod": 0.5, "import_dep": 0.5, "base_cost": 6000,  "volatility": 0.15},
}

# Export categories
EXPORT_CATEGORIES = {
    "cybernetics":        {"volume": 4000, "margin": 0.4},
    "data_services":      {"volume": 2000, "margin": 0.6},
    "recycled_materials": {"volume": 5000, "margin": 0.1},
}

# Budget allocation (from codec_27 city_finance v2.0)
BUDGET_ALLOCATION = {
    "law_enforcement": 0.22,
    "infrastructure":  0.18,
    "public_transit":  0.12,
    "healthcare":      0.12,
    "sanitation":      0.08,
    "education":       0.10,
    "social_services": 0.08,
    "administration":  0.05,
    "emergency_fund":  0.05,
}

# Sub-categories
EXPENDITURE_SUBCATEGORIES = {
    "law_enforcement": {
        "street_patrol": 0.35,
        "detective_unit": 0.15,
        "riot_control": 0.15,
        "cyber_crime_unit": 0.15,
        "surveillance_drones": 0.10,
        "evidence_forensics": 0.10,
    },
    "infrastructure": {
        "road_repair": 0.25,
        "power_grid": 0.25,
        "water_treatment": 0.20,
        "sewer_maintenance": 0.15,
        "street_lighting": 0.10,
        "bridge_tunnel": 0.05,
    },
    "public_transit": {
        "subway_subsidy": 0.50,
        "bus_subsidy": 0.30,
        "tram_ferry": 0.10,
        "capital_improvements": 0.10,
    },
    "healthcare": {
        "public_clinics": 0.45,
        "emergency_response": 0.25,
        "disease_control": 0.15,
        "mental_health": 0.15,
    },
    "sanitation": {
        "garbage_collection": 0.45,
        "street_cleaning": 0.25,
        "hazmat_disposal": 0.15,
        "recycling": 0.15,
    },
    "education": {
        "public_schools": 0.55,
        "vocational_training": 0.25,
        "temple_curriculum": 0.10,
        "adult_education": 0.10,
    },
    "social_services": {
        "ubi_payments": 0.45,
        "housing_assistance": 0.25,
        "job_training": 0.15,
        "food_assistance": 0.15,
    },
    "administration": {
        "government_salaries": 0.60,
        "elections_civic": 0.10,
        "corruption_overhead": 0.15,
        "misc_operations": 0.15,
    },
    "emergency_fund": {
        "reserve_deposit": 1.00,
    },
}

UBI_AMOUNT = 30  # GEP per unemployed citizen per day


# =============================================================================
# PLUGIN INTERFACE
# =============================================================================

class EconomyPlugin:
    """Base class for economy plugins. Override methods to inject custom logic."""

    def on_tick(self, tick: int, state: dict) -> dict:
        """Called each tick. Return dict of adjustments to revenue/expenses."""
        return {}

    def on_event(self, event_type: str, data: dict) -> dict:
        """Called when an economic event fires. Return modifications."""
        return {}

    def get_extra_revenue(self, tick: int, population: int) -> dict:
        """Return additional revenue line items {name: amount}."""
        return {}

    def get_extra_expenses(self, tick: int, population: int) -> dict:
        """Return additional expense line items {name: amount}."""
        return {}


# Global plugin registry
_plugins: List[EconomyPlugin] = []


def register_plugin(plugin: EconomyPlugin):
    """Register an economy plugin."""
    _plugins.append(plugin)


def clear_plugins():
    """Clear all registered plugins."""
    _plugins.clear()


# =============================================================================
# REVENUE CALCULATION
# =============================================================================

def calculate_income_tax_individual(income: float) -> float:
    """Progressive income tax on one citizen."""
    total = 0.0
    remaining = income
    for bracket in INCOME_TAX_BRACKETS:
        if remaining <= 0:
            break
        taxable = min(remaining, bracket["max"] - bracket["min"])
        if income > bracket["min"]:
            total += taxable * bracket["rate"]
            remaining -= taxable
    return total


def calculate_residential_income_tax(tick: int, population: int) -> dict:
    """Total residential income tax across all districts."""
    total = 0
    by_district = {}

    for dist_name, dist in DISTRICTS.items():
        pop = dist["pop"]
        avg_income = dist["income_avg"]
        # Each citizen's income varies ±30% deterministically
        district_tax = 0
        for i in range(pop):
            citizen_income = _variance(avg_income, 0.30, f"income_{dist_name}_{i}_{tick // 24}")
            district_tax += calculate_income_tax_individual(citizen_income)
        by_district[dist_name] = round(district_tax)
        total += district_tax

    return {"total": round(total), "by_district": by_district}


def calculate_property_tax(tick: int) -> dict:
    """Property tax based on zone land values and district building counts."""
    total = 0
    by_district = {}

    for dist_name, dist in DISTRICTS.items():
        zone = dist["zone"]
        base_land_value = ZONE_LAND_VALUES.get(zone, 1.0) * 1000
        # Each district has ~25-30 buildings
        n_buildings = _seeded_int(f"buildings_{dist_name}", 20, 35)
        assessed_value = base_land_value * n_buildings
        # Variance by day
        assessed_value = _variance(assessed_value, 0.05, f"pv_{dist_name}_{tick // 24}")
        tax = assessed_value * PROPERTY_TAX_RATE
        by_district[dist_name] = round(tax)
        total += tax

    return {"total": round(total), "by_district": by_district, "rate": PROPERTY_TAX_RATE}


def calculate_commercial_fees(tick: int) -> dict:
    """Commercial license fees from businesses in each district."""
    total = 0
    by_district = {}
    base_fee = 500  # GEP per business per year → /365 per day

    for dist_name, dist in DISTRICTS.items():
        density = dist["commercial_density"]
        n_businesses = int(dist["pop"] * density * 0.1)  # ~10% of pop-weighted
        daily_fees = n_businesses * (base_fee / 365)
        daily_fees = _variance(daily_fees, 0.10, f"comm_{dist_name}_{tick // 24}")
        by_district[dist_name] = round(daily_fees)
        total += daily_fees

    return {"total": round(total), "by_district": by_district, "per_business_annual": base_fee}


def calculate_industrial_permits(tick: int) -> dict:
    """Industrial zone permits by tier."""
    total = 0
    by_zone = {}
    permit_costs = {"ZONE_I1": 2000, "ZONE_I2": 5000, "ZONE_I3": 8000, "ZONE_IT": 3000}

    for dist_name, dist in DISTRICTS.items():
        ind_density = dist["industrial_density"]
        if ind_density < 0.1:
            continue
        zone = dist["zone"]
        n_facilities = max(1, int(ind_density * 10))
        annual_permits = permit_costs.get(zone, 2000) * n_facilities
        daily = annual_permits / 365
        daily = _variance(daily, 0.08, f"ind_{dist_name}_{tick // 24}")
        by_zone[dist_name] = round(daily)
        total += daily

    return {"total": round(total), "by_zone": by_zone, "permit_costs": permit_costs}


def calculate_sales_tax(tick: int, population: int) -> dict:
    """Sales tax on daily commerce volume."""
    # Average daily spending per capita (varies by wealth)
    base_spending_per_capita = 15  # GEP
    daily_volume = population * _variance(base_spending_per_capita, 0.15, f"sales_{tick // 24}")
    # Exempt ~20% (basic food, medicine, water)
    taxable_volume = daily_volume * 0.80
    tax = taxable_volume * SALES_TAX_RATE
    return {
        "total": round(tax),
        "daily_volume": round(daily_volume),
        "taxable_volume": round(taxable_volume),
        "rate": SALES_TAX_RATE,
        "exempt_categories": ["food_basic", "medicine_essential", "water"],
    }


def calculate_corporate_tax(tick: int) -> dict:
    """Corporate tax from megacorps and small businesses."""
    total = 0
    by_corp = {}

    for name, corp in MEGACORPS.items():
        # Daily revenue = annual / 365 with variance
        daily_rev = corp["annual_revenue"] / 365
        daily_rev = _variance(daily_rev, 0.10, f"corp_{name}_{tick // 24}")
        # Megacorps pay effective rate (loopholes)
        tax = daily_rev * CORPORATE_TAX_EFFECTIVE
        by_corp[name] = {"revenue": round(daily_rev), "tax": round(tax), "effective_rate": CORPORATE_TAX_EFFECTIVE}
        total += tax

    # Small businesses (not megacorps) — pay closer to nominal
    small_biz_daily = _variance(8000, 0.20, f"smallbiz_{tick // 24}")
    small_biz_tax = small_biz_daily * CORPORATE_TAX_NOMINAL * 0.7  # Some evasion
    by_corp["small_businesses"] = {"revenue": round(small_biz_daily), "tax": round(small_biz_tax), "effective_rate": round(CORPORATE_TAX_NOMINAL * 0.7, 3)}
    total += small_biz_tax

    return {
        "total": round(total),
        "by_corp": by_corp,
        "nominal_rate": CORPORATE_TAX_NOMINAL,
        "effective_megacorp_rate": CORPORATE_TAX_EFFECTIVE,
    }


def calculate_parking_revenue(tick: int) -> dict:
    """Parking meter revenue by zone."""
    total = 0
    by_zone = {}
    hour = tick % 24

    # Parking only generates revenue 6am-10pm
    if hour < 6 or hour >= 22:
        return {"total": 0, "by_zone": {}, "note": "meters_off_hours"}

    for zone, rate in PARKING_RATES_PER_DAY.items():
        # Number of metered spots scales with zone type
        spots = {"ZONE_C3": 200, "ZONE_C2": 300, "ZONE_C1": 150, "ZONE_R4": 50, "ZONE_IT": 100, "ZONE_R2": 80, "ZONE_R3": 60}.get(zone, 50)
        # Occupancy varies by time of day
        if 9 <= hour <= 17:
            occupancy = _seeded_float(f"park_{zone}_{tick // 6}", 0.6, 0.95)
        else:
            occupancy = _seeded_float(f"park_{zone}_{tick // 6}", 0.2, 0.5)
        hourly_rate = rate / 16  # 16 paid hours
        revenue = spots * occupancy * hourly_rate
        by_zone[zone] = round(revenue)
        total += revenue

    return {"total": round(total), "by_zone": by_zone, "rates": PARKING_RATES_PER_DAY}


def calculate_transit_fares(tick: int, population: int) -> dict:
    """Transit fare revenue from subway, bus, tram, and ferry."""
    base_fare = 3  # GEP per ride
    hour = tick % 24
    quarter = get_fiscal_quarter(tick)
    season = SEASONAL_MODIFIERS.get(quarter, {})
    ridership_mod = season.get("transit_ridership", 1.0)

    # Ridership varies by hour
    if 7 <= hour <= 9 or 17 <= hour <= 19:
        ridership_pct = 0.25  # Rush hour — 25% of pop riding
    elif 10 <= hour <= 16:
        ridership_pct = 0.10
    elif 6 <= hour <= 22:
        ridership_pct = 0.05
    else:
        ridership_pct = 0.02  # Night owls

    # Base ridership from population
    pop_ridership = int(population * ridership_pct * ridership_mod)

    # Add system-level ridership from transit infrastructure
    system_total = sum(
        line["daily_ridership"] for line in TRANSIT_SYSTEM["subway"]["lines"].values()
    ) + TRANSIT_SYSTEM["bus"]["daily_ridership"] + TRANSIT_SYSTEM["tram"]["daily_ridership"]
    # Ferry has seasonal service
    ferry_service = TRANSIT_SYSTEM["ferry"]["seasonal_service"].get(quarter, 0.90)
    system_total += int(TRANSIT_SYSTEM["ferry"]["daily_ridership"] * ferry_service)

    # Hourly fraction of daily ridership
    hourly_ridership = int(system_total * ridership_pct / 0.10)  # normalize
    total_ridership = max(pop_ridership, hourly_ridership)
    total_ridership = int(_variance(total_ridership, 0.15, f"transit_{tick}"))

    # Revenue with peak pricing
    peak = 7 <= hour <= 9 or 17 <= hour <= 19
    effective_fare = base_fare * (1.5 if peak else 1.0)
    # Discount average: ~15% rides are discounted
    effective_fare *= 0.92
    revenue = total_ridership * effective_fare

    return {
        "total": round(revenue),
        "ridership": total_ridership,
        "fare": base_fare,
        "effective_fare": round(effective_fare, 2),
        "peak": peak,
        "seasonal_modifier": ridership_mod,
        "ferry_service_level": ferry_service,
    }


def calculate_transit_operating_costs(tick: int) -> dict:
    """Full transit system operating costs — subway, bus, tram, ferry."""
    quarter = get_fiscal_quarter(tick)
    season = SEASONAL_MODIFIERS.get(quarter, {})
    ridership_mod = season.get("transit_ridership", 1.0)

    # ----- SUBWAY -----
    sub = TRANSIT_SYSTEM["subway"]
    sc = sub["costs"]
    n_lines = len(sub["lines"])
    total_stations = sum(l["stations"] for l in sub["lines"].values())
    total_km = sum(l["length_km"] for l in sub["lines"].values())

    subway_drivers = sc["driver_salary"] * sc["drivers_per_line"] * n_lines
    subway_electricity = sc["electricity_per_km_per_train"] * total_km * sc["trains_per_line"]
    subway_electricity *= season.get("power_demand", 1.0)
    subway_maintenance = sc["rolling_stock_maintenance"] + sc["track_maintenance"] + sc["station_maintenance"]
    subway_security = total_stations * sc["security_per_station"]
    subway_cleaning = total_stations * sc["cleaning_per_station"]
    subway_total = subway_drivers + subway_electricity + subway_maintenance + subway_security + subway_cleaning

    # ----- BUS -----
    bus = TRANSIT_SYSTEM["bus"]
    bc = bus["costs"]
    bus_drivers = bc["driver_salary"] * bc["drivers"]
    bus_fuel = bc["fuel_per_bus"] * bus["buses"] * season.get("power_demand", 1.0)
    bus_maintenance = bc["maintenance_per_bus"] * bus["buses"]
    bus_depot = bc["depot_operations"]
    bus_total = bus_drivers + bus_fuel + bus_maintenance + bus_depot

    # ----- TRAM -----
    tram = TRANSIT_SYSTEM["tram"]
    tc = tram["costs"]
    tram_total = (tc["driver_salary"] * tc["drivers"]) + tc["electricity"] + tc["maintenance"]

    # ----- FERRY -----
    ferry = TRANSIT_SYSTEM["ferry"]
    fc = ferry["costs"]
    ferry_service = ferry["seasonal_service"].get(quarter, 0.90)
    active_vessels = max(1, int(ferry["vessels"] * ferry_service))
    ferry_total = (fc["crew_per_vessel"] * active_vessels) + (fc["fuel_per_vessel"] * active_vessels) + fc["dock_maintenance"]

    grand_total = subway_total + bus_total + tram_total + ferry_total
    grand_total = _variance(grand_total, 0.05, f"transit_cost_{tick // 24}")

    return {
        "total": round(grand_total),
        "subway": {
            "total": round(subway_total),
            "drivers": round(subway_drivers),
            "electricity": round(subway_electricity),
            "maintenance": round(subway_maintenance),
            "security": round(subway_security),
            "cleaning": round(subway_cleaning),
            "lines": n_lines,
            "stations": total_stations,
            "track_km": total_km,
        },
        "bus": {
            "total": round(bus_total),
            "drivers": round(bus_drivers),
            "fuel": round(bus_fuel),
            "maintenance": round(bus_maintenance),
            "routes": bus["routes"],
            "fleet_size": bus["buses"],
        },
        "tram": {"total": round(tram_total)},
        "ferry": {
            "total": round(ferry_total),
            "active_vessels": active_vessels,
            "service_level": ferry_service,
        },
        "fare_recovery_rate": TRANSIT_SYSTEM["cost_recovery_from_fares"],
        "net_subsidy_needed": round(grand_total * (1 - TRANSIT_SYSTEM["cost_recovery_from_fares"])),
        "quarter": quarter,
    }


def calculate_utility_surcharges(tick: int, population: int) -> dict:
    """Utility surcharge revenue — city's share of Omnicorp utility fees."""
    quarter = get_fiscal_quarter(tick)
    season = SEASONAL_MODIFIERS.get(quarter, {})
    total = 0
    by_utility = {}

    for name, data in UTILITY_SURCHARGES.items():
        if "rate_per_unit" in data:
            usage = data["avg_daily_units_per_capita"] * population
            # Seasonal adjustments
            if name == "power":
                usage *= season.get("power_demand", 1.0)
            elif name == "water":
                usage *= season.get("water_usage", 1.0)
            revenue = usage * data["rate_per_unit"] * data["city_share"]
        else:
            # Flat monthly → daily
            revenue = (data["flat_monthly"] / 30) * population * data["city_share"]
        revenue = _variance(revenue, 0.08, f"util_{name}_{tick // 24}")
        by_utility[name] = round(revenue)
        total += revenue

    return {"total": round(total), "by_utility": by_utility, "quarter": quarter}


def calculate_import_tariffs(tick: int) -> dict:
    """Import tariff revenue (daily)."""
    total = 0
    by_category = {}

    for cat, data in IMPORT_CATEGORIES.items():
        import_cost = data["base_cost"] * data["import_dep"]
        import_cost = _variance(import_cost, data["volatility"], f"import_{cat}_{tick // 24}")
        tariff_rate = IMPORT_TARIFF_RATES.get(cat, 0.10)
        tariff = import_cost * tariff_rate
        by_category[cat] = {
            "import_cost": round(import_cost),
            "tariff": round(tariff),
            "rate": tariff_rate,
        }
        total += tariff

    return {"total": round(total), "by_category": by_category}


def calculate_temple_tithe(tick: int, population: int) -> dict:
    """Temple mandatory tithe — collected from citizens, passed to city."""
    total_income = sum(
        dist["pop"] * dist["income_avg"]
        for dist in DISTRICTS.values()
    )
    total_income = _variance(total_income, 0.05, f"tithe_{tick // 24}")
    tithe = total_income * TEMPLE_TITHE_RATE
    # City gets 40% of tithe revenue (rest goes to Temple operations)
    city_share = tithe * 0.40

    return {
        "total": round(city_share),
        "gross_tithe": round(tithe),
        "city_share_pct": 0.40,
        "rate": TEMPLE_TITHE_RATE,
    }


def calculate_fines_penalties(tick: int, population: int) -> dict:
    """Fines from crime, traffic violations, curfew breaks."""
    fine_types = {
        "traffic_violations": {"base": 50, "daily_count_per_1000": 5},
        "curfew_violations":  {"base": 100, "daily_count_per_1000": 1},
        "petty_crime_fines":  {"base": 200, "daily_count_per_1000": 2},
        "noise_complaints":   {"base": 30,  "daily_count_per_1000": 3},
        "illegal_parking":    {"base": 40,  "daily_count_per_1000": 4},
    }

    total = 0
    by_type = {}

    for fine_name, data in fine_types.items():
        count = int(population / 1000 * data["daily_count_per_1000"])
        count = int(_variance(count, 0.30, f"fine_{fine_name}_{tick // 24}"))
        amount = max(0, count * data["base"])
        by_type[fine_name] = {"count": max(0, count), "amount": amount}
        total += amount

    return {"total": round(total), "by_type": by_type}


def calculate_sin_taxes(tick: int, population: int) -> dict:
    """Sin taxes on alcohol, drugs, gambling, vanity cybernetics."""
    total = 0
    by_category = {}

    base_volumes = {
        "alcohol": 1200,
        "recreational_drugs": 600,
        "gambling": 800,
        "cybernetic_vanity": 400,
    }

    for category, base_vol in base_volumes.items():
        volume = _variance(base_vol, 0.20, f"sin_{category}_{tick // 24}")
        rate = SIN_TAX_RATES[category]
        tax = volume * rate
        by_category[category] = {"volume": round(volume), "tax": round(tax), "rate": rate}
        total += tax

    return {"total": round(total), "by_category": by_category}


# =============================================================================
# FISCAL CALENDAR HELPERS
# =============================================================================

def get_fiscal_quarter(tick: int) -> str:
    """Get fiscal quarter (Q1-Q4) from tick."""
    day = tick // 24
    day_of_year = (day % 365) + 1  # 1-365
    for q, data in FISCAL_QUARTERS.items():
        if data["days"][0] <= day_of_year <= data["days"][1]:
            return q
    return "Q4"


def get_quarter_budget_modifier(tick: int) -> float:
    """Get budget modifier for current fiscal quarter."""
    q = get_fiscal_quarter(tick)
    return FISCAL_QUARTERS[q]["budget_modifier"]


def is_tax_collection_day(tick: int, tax_type: str) -> bool:
    """Check if this is a tax collection day for the given tax type."""
    day = tick // 24
    day_of_year = (day % 365) + 1
    schedule = TAX_COLLECTION_SCHEDULE.get(tax_type, {})
    freq = schedule.get("frequency", "daily")
    if freq == "daily":
        return True
    elif freq == "biweekly":
        return day % schedule.get("collection_day", 14) == 0
    elif freq == "quarterly":
        return day_of_year in schedule.get("due_days", [])
    elif freq == "annual":
        window = schedule.get("renewal_window", (1, 365))
        return window[0] <= day_of_year <= window[1]
    return True


def is_payroll_day(tick: int) -> bool:
    """Check if this is a payroll processing day (biweekly)."""
    day = tick // 24
    return day % 14 == 0


def get_payroll_multiplier(tick: int) -> float:
    """Get payroll multiplier based on shift and overtime."""
    hour = tick % 24
    multiplier = 1.0
    # Night shift differential (22:00-06:00)
    if hour >= 22 or hour < 6:
        multiplier *= PAYROLL_SCHEDULE["night_shift_differential"]
    return multiplier


# =============================================================================
# EXPENDITURE CALCULATION
# =============================================================================

def calculate_payroll(tick: int) -> dict:
    """City employee payroll — daily salaries for all departments."""
    total = 0
    by_department = {}

    for dept, data in CITY_EMPLOYEES.items():
        daily_salary = data["avg_salary"]  # Already daily in codec
        dept_cost = data["count"] * daily_salary
        dept_cost = _variance(dept_cost, 0.05, f"payroll_{dept}_{tick // 24}")
        by_department[dept] = {
            "employees": data["count"],
            "avg_salary": data["avg_salary"],
            "total": round(dept_cost),
        }
        total += dept_cost

    return {"total": round(total), "by_department": by_department}


def calculate_procurement(tick: int, population: int) -> dict:
    """Goods and services the city must purchase."""
    total = 0
    by_category = {}

    categories = {
        "fuel_energy":     {"per_capita": 3.0, "variance": 0.15},
        "office_supplies":  {"per_capita": 0.5, "variance": 0.10},
        "medical_supplies": {"per_capita": 2.0, "variance": 0.20},
        "road_materials":   {"per_capita": 1.5, "variance": 0.25},
        "vehicle_fleet":    {"per_capita": 1.0, "variance": 0.10},
        "uniforms_gear":    {"per_capita": 0.3, "variance": 0.05},
        "food_services":    {"per_capita": 0.8, "variance": 0.15},
        "tech_equipment":   {"per_capita": 1.2, "variance": 0.10},
    }

    for cat, data in categories.items():
        cost = population * data["per_capita"]
        cost = _variance(cost, data["variance"], f"proc_{cat}_{tick // 24}")
        by_category[cat] = round(cost)
        total += cost

    return {"total": round(total), "by_category": by_category}


def calculate_import_costs(tick: int) -> dict:
    """Cost of importing goods the city depends on."""
    total = 0
    by_category = {}

    for cat, data in IMPORT_CATEGORIES.items():
        cost = data["base_cost"] * data["import_dep"]
        cost = _variance(cost, data["volatility"], f"importcost_{cat}_{tick // 24}")
        by_category[cat] = round(cost)
        total += cost

    return {"total": round(total), "by_category": by_category}


def calculate_ubi_costs(tick: int, population: int, unemployment_rate: float) -> dict:
    """Universal Basic Income payments to unemployed citizens."""
    working_age = int(population * 0.6)
    unemployed = int(working_age * unemployment_rate)
    daily_cost = unemployed * UBI_AMOUNT

    return {
        "total": round(daily_cost),
        "recipients": unemployed,
        "amount_per_person": UBI_AMOUNT,
        "working_age_pop": working_age,
    }


def calculate_budget_expenditure(tick: int, population: int, total_budget: float) -> dict:
    """Full expenditure breakdown with sub-categories and seasonal modifiers."""
    result = {}
    total = 0
    quarter = get_fiscal_quarter(tick)
    quarter_mod = get_quarter_budget_modifier(tick)
    season = SEASONAL_MODIFIERS.get(quarter, {})

    for category, pct in BUDGET_ALLOCATION.items():
        amount = total_budget * pct * quarter_mod
        # Apply category-specific seasonal adjustments
        if category == "infrastructure":
            amount *= season.get("road_repair", 1.0)
        elif category == "law_enforcement":
            amount *= season.get("crime", 1.0)
        elif category == "public_transit":
            amount *= season.get("transit_ridership", 1.0)
        amount = _variance(amount, 0.05, f"exp_{category}_{tick // 24}")
        sub = {}
        sub_cats = EXPENDITURE_SUBCATEGORIES.get(category, {})
        for sub_name, sub_pct in sub_cats.items():
            sub_amount = amount * sub_pct
            sub[sub_name] = round(sub_amount)
        result[category] = {
            "allocated_pct": pct,
            "amount": round(amount),
            "sub_items": sub,
            "quarter_modifier": quarter_mod,
        }
        total += amount

    result["total"] = round(total)
    result["quarter"] = quarter
    result["quarter_label"] = FISCAL_QUARTERS[quarter]["label"]
    return result


# =============================================================================
# ECONOMIC INDICATORS
# =============================================================================

def calculate_gdp(tick: int, population: int) -> float:
    """Nominal GDP based on economic activity."""
    per_capita_gdp = 75  # GEP per person per day (from codec)
    day = tick // 24
    # GDP grows slowly over time with variance
    growth = 1.0 + day * 0.0003  # ~0.03% per day
    gdp = population * per_capita_gdp * growth
    gdp = _variance(gdp, 0.03, f"gdp_{tick // 24}")
    return round(gdp)


def calculate_unemployment(tick: int) -> float:
    """Unemployment rate with economic cycle variance."""
    base = 0.12  # 12% structural (from codec)
    # Cyclical variance
    cycle = _seeded_float(f"unemployment_{tick // 72}", -0.03, 0.03)
    return round(max(0.03, min(0.30, base + cycle)), 3)


def calculate_inflation(tick: int) -> float:
    """Inflation rate."""
    base = 0.02  # 2% baseline
    variance = _seeded_float(f"inflation_{tick // 48}", -0.01, 0.015)
    return round(max(-0.02, min(0.15, base + variance)), 4)


def calculate_gini(tick: int) -> float:
    """Gini coefficient (inequality)."""
    base = 0.72  # High inequality (from codec)
    drift = _seeded_float(f"gini_{tick // 120}", -0.02, 0.02)
    return round(max(0.3, min(0.9, base + drift)), 3)


def calculate_black_market_share(tick: int, unemployment: float, service_avg: float) -> float:
    """Black market as % of GDP."""
    base = 0.20
    # Higher unemployment → larger black market
    unemployment_factor = unemployment * 0.5
    # Lower services → larger black market
    service_factor = (1.0 - service_avg) * 0.3
    result = base + unemployment_factor + service_factor
    return round(max(0.10, min(0.50, result)), 3)


# =============================================================================
# SERVICE LEVELS
# =============================================================================

def calculate_service_levels(tick: int, budget_ratio: float) -> dict:
    """Service quality levels based on budget coverage."""
    services = {}
    for category in ["law_enforcement", "infrastructure", "healthcare", "sanitation", "education", "social_services"]:
        base = 0.75 + _seeded_float(f"svc_{category}_{tick // 48}", 0, 0.15)
        # Budget ratio affects service quality
        adjusted = base * min(1.2, budget_ratio)
        services[category] = round(max(0.1, min(1.0, adjusted)), 2)
    return services


# =============================================================================
# CRISIS SYSTEM
# =============================================================================

def get_crisis_level(budget: float, reserve_target: float = 100000) -> str:
    """Determine crisis level from budget."""
    if budget >= reserve_target * 0.5:
        return "healthy"
    elif budget >= reserve_target * 0.2:
        return "strained"
    elif budget >= reserve_target * 0.05:
        return "crisis"
    else:
        return "collapse"


# =============================================================================
# ECONOMIC EVENTS (deterministic)
# =============================================================================

def generate_economic_events(tick: int, indicators: dict) -> list:
    """Generate random economic events based on tick seed."""
    events = []
    day = tick // 24
    seed = _seed(f"econ_event_{day}")

    # Recession check
    if indicators.get("gdp_growth", 0) < -0.02:
        events.append({"type": "recession", "severity": "moderate", "effects": {"unemployment": +0.05, "wages": -0.10}})

    # Boom check
    if indicators.get("gdp_growth", 0) > 0.05:
        events.append({"type": "economic_boom", "severity": "minor", "effects": {"wages": +0.10, "inflation": +0.02}})

    # Random events (deterministic per day)
    roll = seed % 10000
    if roll < 50:  # 0.5%
        events.append({"type": "supply_shortage", "affected": "food", "price_increase": 0.30})
    elif roll < 80:  # 0.3%
        events.append({"type": "corp_merger", "corps": ["NexGen", "Synthetica"], "job_loss": 500})
    elif roll < 100:  # 0.2%
        events.append({"type": "infrastructure_failure", "system": "power", "duration_hours": 12})
    elif roll < 120:  # 0.2%
        events.append({"type": "tax_reform_proposal", "proposed_by": "city_council", "change": "restructure"})
    elif roll < 150:  # 0.3%
        events.append({"type": "black_market_raid", "seized_value": _seeded_int(f"raid_{day}", 5000, 50000)})

    return events


# =============================================================================
# MAIN ENGINE — FULL TICK CALCULATION
# =============================================================================

def calculate_city_economy(tick: int, population: int, npc_states: Optional[List[dict]] = None) -> dict:
    """
    Calculate the complete city economy state for a given tick.

    This is the main entry point. Returns a comprehensive dict with:
    - revenue breakdown (12 streams)
    - expenditure breakdown (8 categories + sub-items)
    - payroll, procurement, imports
    - economic indicators (GDP, inflation, unemployment, Gini, black market)
    - service levels
    - crisis status
    - export revenue
    - economic events
    - plugin contributions

    All calculations are deterministic: same tick + population → same result.
    """
    day = tick // 24
    hour = tick % 24
    quarter = get_fiscal_quarter(tick)
    quarter_data = FISCAL_QUARTERS[quarter]

    # -------------------------------------------------------
    # REVENUE (13 streams)
    # -------------------------------------------------------
    income_tax = calculate_residential_income_tax(tick, population)
    property_tax = calculate_property_tax(tick)
    commercial_fees = calculate_commercial_fees(tick)
    industrial_permits = calculate_industrial_permits(tick)
    sales_tax = calculate_sales_tax(tick, population)
    corporate_tax = calculate_corporate_tax(tick)
    parking = calculate_parking_revenue(tick)
    transit = calculate_transit_fares(tick, population)
    tariffs = calculate_import_tariffs(tick)
    tithe = calculate_temple_tithe(tick, population)
    fines = calculate_fines_penalties(tick, population)
    sin_taxes = calculate_sin_taxes(tick, population)
    utility_surcharges = calculate_utility_surcharges(tick, population)

    revenue_streams = {
        "income_tax":         income_tax,
        "property_tax":       property_tax,
        "commercial_fees":    commercial_fees,
        "industrial_permits": industrial_permits,
        "sales_tax":          sales_tax,
        "corporate_tax":      corporate_tax,
        "parking_meters":     parking,
        "transit_fares":      transit,
        "import_tariffs":     tariffs,
        "temple_tithe_share": tithe,
        "fines_penalties":    fines,
        "sin_taxes":          sin_taxes,
        "utility_surcharges": utility_surcharges,
    }

    total_revenue = sum(stream["total"] for stream in revenue_streams.values())

    # -------------------------------------------------------
    # INDICATORS
    # -------------------------------------------------------
    gdp = calculate_gdp(tick, population)
    unemployment = calculate_unemployment(tick)
    inflation = calculate_inflation(tick)
    gini = calculate_gini(tick)

    # -------------------------------------------------------
    # EXPENDITURE (8 categories + payroll + procurement + imports)
    # -------------------------------------------------------
    payroll = calculate_payroll(tick)
    procurement = calculate_procurement(tick, population)
    import_costs = calculate_import_costs(tick)
    ubi = calculate_ubi_costs(tick, population, unemployment)
    transit_costs = calculate_transit_operating_costs(tick)

    # Total operational cost (includes transit system)
    total_operational = (payroll["total"] + procurement["total"] + import_costs["total"]
                         + ubi["total"] + transit_costs["net_subsidy_needed"])
    budget_expenditure = calculate_budget_expenditure(tick, population, total_operational)

    total_expenditure = budget_expenditure["total"]

    # -------------------------------------------------------
    # EXPORTS
    # -------------------------------------------------------
    export_revenue = 0
    export_details = {}
    for name, data in EXPORT_CATEGORIES.items():
        vol = _variance(data["volume"], 0.15, f"export_{name}_{tick // 24}")
        rev = vol * data["margin"]
        export_details[name] = {"volume": round(vol), "revenue": round(rev)}
        export_revenue += rev
    export_revenue = round(export_revenue)

    # -------------------------------------------------------
    # NET BALANCE
    # -------------------------------------------------------
    net_daily = total_revenue + export_revenue - total_expenditure
    # Accumulate budget from day 1
    base_budget = 1_000_000  # Starting reserve
    accumulated = base_budget + day * net_daily
    # Intra-day: add fraction of revenue, subtract fraction of expenses
    hour_frac = hour / 24.0
    budget = accumulated + int(total_revenue * hour_frac) - int(total_expenditure * hour_frac * 0.8)

    # -------------------------------------------------------
    # SERVICE LEVELS
    # -------------------------------------------------------
    budget_ratio = total_revenue / max(1, total_expenditure)
    service_levels = calculate_service_levels(tick, budget_ratio)
    service_avg = sum(service_levels.values()) / max(1, len(service_levels))

    # -------------------------------------------------------
    # BLACK MARKET
    # -------------------------------------------------------
    black_market = calculate_black_market_share(tick, unemployment, service_avg)

    # -------------------------------------------------------
    # CRISIS
    # -------------------------------------------------------
    crisis_level = get_crisis_level(budget)

    # -------------------------------------------------------
    # EVENTS
    # -------------------------------------------------------
    gdp_growth = _seeded_float(f"gdp_growth_{tick // 72}", -0.03, 0.05)
    indicators = {
        "gdp": gdp,
        "gdp_growth": round(gdp_growth, 4),
        "inflation": inflation,
        "unemployment_rate": unemployment,
        "gini_coefficient": gini,
        "black_market_share": black_market,
        "housing_affordability": round(0.45 + _seeded_float(f"housing_{tick // 120}", -0.05, 0.05), 3),
    }
    events = generate_economic_events(tick, indicators)

    # -------------------------------------------------------
    # PLUGINS
    # -------------------------------------------------------
    plugin_revenue = {}
    plugin_expenses = {}
    for plugin in _plugins:
        try:
            pr = plugin.get_extra_revenue(tick, population)
            pe = plugin.get_extra_expenses(tick, population)
            plugin_revenue.update(pr)
            plugin_expenses.update(pe)
        except Exception:
            pass

    total_revenue += sum(plugin_revenue.values())
    total_expenditure += sum(plugin_expenses.values())

    # -------------------------------------------------------
    # ASSEMBLE
    # -------------------------------------------------------
    return {
        "tick": tick,
        "day": day,
        "hour": hour,
        "year": day // 365 + 2087,

        "fiscal_quarter": quarter,
        "fiscal_quarter_label": quarter_data["label"],
        "budget_modifier": quarter_data["budget_modifier"],

        "budget": budget,
        "crisis_level": crisis_level,

        "revenue": {
            "total": round(total_revenue),
            "streams": {k: v["total"] for k, v in revenue_streams.items()},
            "detail": revenue_streams,
            "export_revenue": export_revenue,
            "export_detail": export_details,
        },

        "expenditure": {
            "total": round(total_expenditure),
            "breakdown": budget_expenditure,
            "payroll": payroll,
            "procurement": procurement,
            "imports": import_costs,
            "ubi": ubi,
            "transit": transit_costs,
        },

        "net_daily_balance": round(net_daily),

        "indicators": indicators,
        "service_levels": service_levels,
        "service_avg": round(service_avg, 2),

        "transit_system": transit_costs,

        "megacorps": {
            name: {
                "sector": corp["sector"],
                "market_share": round(_variance(corp["market_share"], 0.05, f"mc_{name}_{tick // 48}"), 3),
                "employees": int(_variance(corp["employees"], 0.03, f"mce_{name}_{tick // 72}")),
            }
            for name, corp in MEGACORPS.items()
        },

        "events": events,

        "plugins": {
            "revenue": plugin_revenue,
            "expenses": plugin_expenses,
        } if (plugin_revenue or plugin_expenses) else None,

        "seasonal_modifiers": SEASONAL_MODIFIERS.get(quarter, {}),

        "districts": {
            name: {
                "code": d["code"],
                "population": d["pop"],
                "zone": d["zone"],
                "avg_income": d["income_avg"],
                "income_tax": revenue_streams["income_tax"]["by_district"].get(name, 0),
                "property_tax": revenue_streams["property_tax"]["by_district"].get(name, 0),
            }
            for name, d in DISTRICTS.items()
        },
    }


# =============================================================================
# QUICK SUMMARY (for /api/world-state)
# =============================================================================

def get_economy_summary(tick: int, population: int) -> dict:
    """
    Return a compact economy summary for inclusion in /api/world-state.
    This is much lighter than the full calculate_city_economy() call.
    """
    day = tick // 24
    hour = tick % 24

    quarter = get_fiscal_quarter(tick)
    quarter_mod = get_quarter_budget_modifier(tick)
    season = SEASONAL_MODIFIERS.get(quarter, {})

    # Quick revenue estimate
    total_rev = 0
    for dist in DISTRICTS.values():
        total_rev += dist["pop"] * dist["income_avg"] * 0.08  # ~8% effective tax rate
    sales_tax = population * 15 * 0.80 * SALES_TAX_RATE
    sales_tax *= season.get("outdoor_commerce", 1.0)  # Seasonal commerce
    corp_tax = sum(c["annual_revenue"] / 365 * CORPORATE_TAX_EFFECTIVE for c in MEGACORPS.values())
    parking = _variance(380, 0.15, f"qp_{tick // 6}") if 6 <= hour < 22 else 0
    transit = _variance(population * 0.10 * 3, 0.15, f"qt_{tick}")
    transit *= season.get("transit_ridership", 1.0)
    fines = _variance(population * 0.015 * 80, 0.20, f"qf_{tick // 24}")
    fines *= season.get("crime", 1.0)
    # Utility surcharges (quick estimate)
    util_rev = population * 0.05 * season.get("power_demand", 1.0)

    daily_revenue = total_rev + sales_tax + corp_tax + parking + transit + fines + util_rev
    daily_revenue = _variance(daily_revenue, 0.08, f"qrev_{tick // 24}")

    # Quick expense estimate (per-capita based + transit subsidy)
    daily_expense = population * 15  # 15 GEP per capita per day
    payroll_total = sum(d["count"] * d["avg_salary"] for d in CITY_EMPLOYEES.values())
    transit_subsidy = 23990 * (1 - TRANSIT_SYSTEM["cost_recovery_from_fares"])  # ~10,796/day
    transit_subsidy *= season.get("transit_ridership", 1.0)
    daily_expense += payroll_total + transit_subsidy
    daily_expense *= quarter_mod  # Quarterly budget modifier
    daily_expense = _variance(daily_expense, 0.05, f"qexp_{tick // 24}")

    net = daily_revenue - daily_expense
    base_budget = 1_000_000
    budget = base_budget + day * net
    budget += int(daily_revenue * (hour / 24.0)) - int(daily_expense * (hour / 24.0) * 0.8)

    unemployment = calculate_unemployment(tick)
    inflation = calculate_inflation(tick)
    gini = calculate_gini(tick)
    service_levels = calculate_service_levels(tick, daily_revenue / max(1, daily_expense))
    service_avg = sum(service_levels.values()) / max(1, len(service_levels))
    black_market = calculate_black_market_share(tick, unemployment, service_avg)

    return {
        "budget": round(budget),
        "gdp": calculate_gdp(tick, population),
        "inflation": inflation,
        "unemployment_rate": unemployment,
        "gini_coefficient": gini,
        "black_market_share": black_market,
        "crisis_level": get_crisis_level(budget),
        "fiscal_quarter": quarter,
        "quarter_label": FISCAL_QUARTERS[quarter]["label"],
        "quarter_budget_modifier": quarter_mod,
        "daily_revenue": round(daily_revenue),
        "daily_expense": round(daily_expense),
        "net_daily": round(net),
        "transit_subsidy": round(transit_subsidy),
        "service_levels": service_levels,
        "revenue_breakdown": {
            "income_tax": round(total_rev),
            "sales_tax": round(sales_tax),
            "corporate_tax": round(corp_tax),
            "parking_meters": round(parking),
            "transit_fares": round(transit),
            "fines": round(fines),
            "utility_surcharges": round(util_rev),
        },
    }

# Cities: Skylines II — Complete Feature Reference

> Extracted from [CS2 Paradox Wiki](https://cs2.paradoxwikis.com/) on 2026-02-08.
> Purpose: Reference document for replicating CS2 depth in the AO World Engine simulation.

---

## Table of Contents

1. [Economy & Taxation](#1-economy--taxation)
2. [Production & Supply Chains](#2-production--supply-chains)
3. [Zoning & Building Levels](#3-zoning--building-levels)
4. [Citizens & Lifepath](#4-citizens--lifepath)
5. [Happiness & Well-being](#5-happiness--well-being)
6. [City Services](#6-city-services)
7. [Transportation](#7-transportation)
8. [Roads & Infrastructure](#8-roads--infrastructure)
9. [Electricity & Power Grid](#9-electricity--power-grid)
10. [Water & Sewage](#10-water--sewage)
11. [Pollution](#11-pollution)
12. [Natural Resources](#12-natural-resources)
13. [Climate & Weather](#13-climate--weather)
14. [Crime & Police](#14-crime--police)
15. [Tourism & Attractiveness](#15-tourism--attractiveness)
16. [Parking](#16-parking)
17. [Policies](#17-policies)
18. [Districts](#18-districts)
19. [Progression & Milestones](#19-progression--milestones)
20. [Disasters](#20-disasters)
21. [Info Views](#21-info-views)
22. [Communications](#22-communications)

---

## 1. Economy & Taxation

### Tax System (Unlocked at Milestone 2)
- **Tax Range:** -10% to +30%
- **Residential Taxes:** Taxed by **Education Level**:
  - Uneducated, Poorly Educated, Educated, Well Educated, Highly Educated
  - Each level separately adjustable
- **Commercial Taxes:** Taxed by **Product Type** (Food, Beverages, Textiles, etc.)
- **Industrial Taxes:** Taxed by **Product Type** (Metals, Chemicals, Machinery, etc.)
- **Office Taxes:** Taxed by **Product Type** (Software, Telecom, Financial, Media)
- Lowering taxes for specific products encourages city specialization

### Service Fees (Adjustable 0% to 200%)
- **Electricity Fee:** Affects consumption and citizen satisfaction
- **Water Fee:** Affects consumption and citizen satisfaction
- **Transit Fee:** Affects ridership vs revenue
- Each +1% fee → +0.2% efficiency, +0.05 happiness
- Each -1% fee → -0.4% efficiency, -0.1 happiness

### Loans
- Available at various milestone levels
- Fixed interest rates
- Must be repaid over time

### City Revenue Sources
- Tax income (residential, commercial, industrial, office)
- Service fees (electricity, water, transit)
- Parking fees
- Export surplus goods
- Tourism spending

### City Expenses
- Service budgets (adjustable 50%-150%)
- Loan repayments
- Import costs for deficit goods
- Infrastructure maintenance

---

## 2. Production & Supply Chains

### Primary Resources (Extracted from Nature)
| Resource | Source | Type |
|----------|--------|------|
| Grain | Farming (Fertile Land) | Renewable |
| Vegetables | Farming (Fertile Land) | Renewable |
| Livestock | Farming (Fertile Land) | Renewable |
| Cotton | Farming (Fertile Land) | Renewable |
| Wood | Forestry (Forest) | Renewable |
| Coal | Mining (Ore deposits) | Non-renewable |
| Stone/Rock | Mining | Non-renewable |
| Iron/Ore | Mining (Ore deposits) | Non-renewable |
| Oil | Drilling (Oil deposits) | Non-renewable |

### Material Goods (Secondary Processing)
| Good | Primary Input | Used By |
|------|---------------|---------|
| Food | Grain, Livestock, Vegetables | Commercial (Retail) |
| Beverages | Grain, Vegetables | Commercial (Retail) |
| Timber | Wood | Construction, Furniture |
| Paper | Wood | Offices, Commercial |
| Furniture | Timber, Textiles | Commercial (Retail) |
| Textiles | Cotton | Commercial (Retail) |
| Plastics | Oil, Chemicals | Electronics, Manufacturing |
| Chemicals | Oil, Minerals | Pharma, Plastics |
| Metals | Iron, Coal | Machinery, Vehicles |
| Steel | Iron, Coal | Construction, Vehicles |
| Minerals | Stone | Concrete, Glass |
| Concrete | Minerals | Construction |
| Machinery | Metals, Steel | Industry, Construction |
| Vehicles | Metals, Steel, Electronics | Commercial, Citizens |
| Electronics | Minerals, Plastics | Commercial, Offices |
| Petrochemicals | Oil | Fuel, Chemicals |

### Immaterial Goods (Office Production)
| Good | Input | Used By |
|------|-------|---------|
| Software | Electronics | All sectors |
| Telecom | Software | Citizens, Commercial |
| Financial | Software | All sectors |
| Media | Software | Citizens, Commercial |

### Production Mechanics
- **Transportation Costs:** Companies pay delivery/shipping costs. Proximity = profitability
- **City Specialization Bonus:** Up to **115% efficiency** at 10,000 tonnes total production
- **Employee Efficiency:** Scales with actual/required employee ratio
- **Happiness Bonus:** Happy employees produce more
- **Outside Trade:** Automated import/export via highway, rail, water, air connections

---

## 3. Zoning & Building Levels

### Zone Types & Densities

#### Residential
| Zone | Density | Description |
|------|---------|-------------|
| Low Density | Low | Single family homes |
| Row Housing | Low-Medium | Townhouses |
| Medium Density | Medium | Apartment buildings |
| Mixed Housing | Medium-High | Commercial ground floor + Residential above |
| Low Rent | High | Small affordable apartments |
| High Density | High | Skyscrapers |

#### Commercial
| Zone | Density | Description |
|------|---------|-------------|
| Low Density | Low | Small shops, cafes |
| High Density | High | Malls, large retail |

#### Industrial
| Zone | Description |
|------|-------------|
| General Industrial | Manufacturing |
| Warehouses | Storage and distribution |
| Specialized Industry | Farming, Forestry, Mining, Oil |

#### Office
| Zone | Density | Description |
|------|---------|-------------|
| Low Density | Low | Small offices |
| High Density | High | Office towers |

### Building Levels (1–5)
- **Level Up Trigger:** When Rent < Wealth/Profit (residents can afford to improve)
- **Level Benefits:**
  - Level 3+ residential: Additional apartment units
  - All: Reduced water/electricity consumption per unit
  - Industrial/Commercial: Faster production, lower pollution, lower garbage output
- **Land Value:** Spreads through road network
  - High land value → higher rent → forces low-income out
  - Driven by: services proximity, connectivity, environment quality

### Demand Drivers
- **Residential:** New citizens, job availability, education access
- **Commercial:** Consumer goods availability, citizen wealth
- **Industrial/Office:** Raw material access, educated labor

---

## 4. Citizens & Lifepath

### Life Stages
| Stage | Can Work | Education | Transport Priority |
|-------|----------|-----------|-------------------|
| Children | No | Elementary | N/A |
| Teens | Part-time | High School/College | Cheapest |
| Adults | Full-time | University+ | Fastest |
| Seniors | Retired | N/A | Most Comfortable |

### Education Levels & Wages (₡/month)
| Education | Monthly Wage |
|-----------|-------------|
| Uneducated | ₡1,500 |
| Poorly Educated | ₡1,800 |
| Educated | ₡2,100 |
| Well Educated | ₡2,400 |
| Highly Educated | ₡2,700 |

### Education Tiers
1. Elementary School
2. High School
3. College
4. University
5. Technical University

### Social Safety Net
- Family Allowance: ₡400/child/month
- Pension: ₡1,200/month
- Unemployment Benefits: ₡800/month

### Wealth Categories
1. Wretched
2. Poor
3. Modest
4. Comfortable
5. Wealthy

### Citizen Conditions
- Sick (low health)
- Injured (accident/disaster)
- Homeless (can't afford rent)
- Unwell (low well-being)
- Weak (chronically low health)
- Distressed (trapped in disaster)
- Evacuated (in shelter)

---

## 5. Happiness & Well-being

### Happiness = Average(Health, Well-being)

### Health Factors
- Healthcare coverage and proximity
- Pollution exposure (air, ground, water, noise)
- Age (seniors decline naturally)
- Disasters/accidents

### Well-being Factors
- Proximity to parks and landmarks
- Entertainment access (bars, clubs, venues)
- Reliable mail/internet service
- Low noise pollution
- Low taxes
- Home size (prefer larger low-density)
- Leisure fulfillment

### Leisure System
- Citizens seek leisure daily
- **Sunny days:** Prefer outdoor parks, squares
- **Rainy/cold days:** Prefer indoor shopping, entertainment
- Weather directly affects leisure choice

---

## 6. City Services

### Budget System
- Each service: adjustable **50% to 150%** budget
- 50% budget → 25% efficiency
- 100% budget → 100% efficiency
- 150% budget → 125% efficiency

### Service Categories

#### Electricity
- Wind, Solar, Geothermal, Hydro, Coal, Gas, Nuclear
- Battery stations for surplus storage
- Low voltage (local) + High voltage (transmission) grid
- Transformer stations connect HV↔LV

#### Water & Sewage
- **Surface Water:** Unlimited but pollutable
- **Groundwater:** Limited capacity, pollution-sensitive
- **Sewage Outlet:** Dumps untreated waste → water pollution
- **Treatment Plant:** Purifies, can return clean water, produces solid waste

#### Healthcare & Deathcare
- Clinics (local) → Hospitals (regional)
- Cemeteries, Crematoriums

#### Education (5 tiers)
- Elementary → High School → College → University → Technical University

#### Fire & Rescue
- Fire stations with response vehicles
- Helicopter rescue upgrades
- Forest fire watchtowers

#### Police & Justice
- Police stations → Headquarters
- Jails (temporary) → Prisons (sentencing)
- Crime prevention patrols

#### Garbage Management
- Collection trucks
- Landfills → Recycling centers → Incinerators

#### Administration
- Welfare Office (well-being boost)
- City Hall (cost reduction)
- Central Bank (economic boost)

#### Communications
- **Post:** Physical mail, affects company efficiency
- **Telecom:** Internet service, affects well-being & commercial output

#### Road Maintenance
- Depots send vehicles for road repair
- Snow removal (weather-dependent)
- Neglected roads → increased accidents

---

## 7. Transportation

### Passenger Transport Modes
| Mode | Capacity | Requirement | Notes |
|------|----------|-------------|-------|
| Bus | Low-Med | Bus Depot | Initial PT, stop on any road |
| Taxi | Individual | Taxi Depot | On-demand, taxi stands |
| Tram | Medium | Tram Depot + tracks | Can share or dedicated tracks |
| Subway/Metro | High | Subway Yard | Underground/elevated |
| Train | Very High | Train Depot | Long-distance, outside connections |
| Passenger Ship | High | Passenger Harbor | Water routes |
| Passenger Plane | Very High | Airport | Fastest, most expensive |

### Cargo Transport
| Mode | Requirement | Notes |
|------|-------------|-------|
| Cargo Train | Cargo Terminal | Resource transfer |
| Cargo Ship | Cargo Harbor | Massive capacity |
| Cargo Plane | Airport upgrade | Fastest, most expensive |
| Oil Carrier | Specialized | Bulk oil transport |

### Transit Mechanics
- Every mode requires depot/yard for vehicle spawning/maintenance
- Line Tool for creating routes with stops and waypoints
- One-way and two-way loops
- Electric vehicle upgrades available
- Depots have max vehicle capacity (expandable via upgrades)

---

## 8. Roads & Infrastructure

### Road Hierarchy
| Type | Lanes | Speed | Cost/km | Upkeep/km/mo |
|------|-------|-------|---------|--------------|
| Small Roads | 2 | 40-50 km/h | ~€800 | ~€200 |
| Medium Roads | 4 | 50-60 km/h | ~€2,400 | ~€600 |
| Large Roads | 6 | 60-80 km/h | ~€4,000 | ~€1,000 |
| Highways | 4-6 | 100+ km/h | High | High |

### Tools
- Grid Tool (build entire grids quickly)
- Replace Tool (change type without demolition)
- Snapping (90°, geometry, zoning grid)
- Elevation control (bridges, tunnels, elevated)

### Features
- Integrated utility pipes/cables in roads
- Roundabouts
- Bridge/Tunnel construction
- Speed limits (adjustable)

---

## 9. Electricity & Power Grid

### Power Plants
| Type | Output | Pollution | Cost | Notes |
|------|--------|-----------|------|-------|
| Wind Turbine | Low | None | Low | Wind-dependent |
| Solar | Medium | None | Medium | Daytime only, needs batteries |
| Geothermal | Medium | None | Medium | Location-dependent |
| Hydro | Medium-High | None | High | River-dependent |
| Coal | High | Very High (air+ground) | Low | Cheapest per MW |
| Gas | Mid-High | Medium | Medium | Needs fuel |
| Nuclear | Massive | None (air), hazardous waste | Very High | Highest output |

### Distribution
- **Low Voltage:** Local grid, runs through roads
- **High Voltage:** Long-distance pylons
- **Transformer Stations:** Connect HV ↔ LV
- **Battery Stations:** Store surplus for nighttime/peaks

---

## 10. Water & Sewage

### Water Sources
| Source | Capacity | Vulnerability |
|--------|----------|--------------|
| Surface Water (rivers/coast) | Unlimited | Water pollution |
| Groundwater (wells) | Limited, slow replenishment | Ground pollution |

### Sewage Treatment
- **Sewage Outlet:** Cheap, dumps untreated waste, creates water pollution
- **Treatment Plant:** Expensive, purifies water, produces solid waste
- Can upgrade treatment to return clean water to network

---

## 11. Pollution

### Four Pollution Types
| Type | Sources | Effects | Mitigation |
|------|---------|---------|-----------|
| Ground | Industry, garbage, power plants | Sickness, land value ↓ | Remove source (slow decay) |
| Groundwater | Ground pollution overlap | Contaminates water supply | Relocate pumps |
| Air | Power plants, heavy industry | Sickness (downwind) | Wind direction, clean energy |
| Water | Sewage outlets | Contaminates downstream pumps | Treatment plants |
| Noise | Traffic, industry, commercial, airports | Well-being ↓ | Trees, sound barriers |

---

## 12. Natural Resources

| Resource | Renewability | Extraction | Products |
|----------|-------------|------------|----------|
| Fertile Land | Renewable | Farming | Grain, Vegetables, Livestock, Cotton |
| Forest | Renewable | Forestry | Wood/Logs |
| Ore | Non-renewable (depletes) | Mining | Iron, Coal, Stone |
| Oil | Non-renewable (depletes) | Drilling | Crude Oil |
| Groundwater | Semi-renewable | Pumping | Clean Water |

---

## 13. Climate & Weather

### Seasons
| Season | Effects |
|--------|---------|
| Spring | Moderate temp, rain, vegetation grows |
| Summer | High temp, cooling demand ↑, outdoor leisure ↑, fire risk ↑ |
| Autumn | Cooling, rain, outdoor leisure ↓ |
| Winter | Low temp, heating demand ↑, snow, road maintenance ↑ |

### Weather Effects
- **Temperature:** Optimal 18-22°C = minimum energy. Extremes spike heating/cooling
- **Precipitation:** Increases accident risk, affects visibility
- **Snow:** Requires road maintenance crews (snow removal)
- **Wind:** Affects air pollution spread direction, wind power output
- **Day Length:** Varies with season, affects solar power and citizen activities

---

## 14. Crime & Police

### Crime Mechanics
- **Primary Driver:** Low well-being → criminality
- **Process:** Criminal selects target → approaches building → robbery timer starts → alarm triggers → police respond
- **Success/Failure:** Police must arrive before robbery completes
- **Consequences:** Arrest → Jail (police station) → Prison (specialized facility) → Release

### Crime Prevention
- Police patrols reduce crime probability
- Service coverage area matters
- Well-being improvement is the root solution

---

## 15. Tourism & Attractiveness

### Attractiveness Factors
- Parks and recreation facilities
- Landmarks and signature buildings
- Entertainment venues
- City uniqueness

### Tourist Behavior
- Visit city via outside connections
- Stay in hotels (Retail Lodging)
- Spend money on meals and entertainment
- Contribute revenue without requiring housing/schools

---

## 16. Parking

### Parking Types
- **On-street:** Can be removed via road upgrades
- **Parking Lots:** Surface-level, medium capacity
- **Parking Buildings/Garages:** High capacity, multi-story

### Parking Mechanics
- Citizens choose based on: Price, Distance, Convenience
- Fees settable per district
- "Parking Fee" policy can be applied to individual buildings
- Insufficient parking → congestion, reduced commercial appeal

---

## 17. Policies

### City-Wide Policies
| Policy | Effect |
|--------|--------|
| Taxi Minimum Fare | Sets floor price for taxi rides |
| Import Services | Allows purchasing services from outside |
| Pre-Release Programs | Reduces prison population |
| Advanced Pollution Management | Reduces industrial pollution |
| City Promotion | Increases tourism |
| High-Speed Highways | Increases highway speed limits |

### District-Level Policies
| Policy | Effect |
|--------|--------|
| Energy Awareness | Reduces electricity consumption |
| Recycling | Reduces garbage output |
| Roadside Parking Fee | Revenue from on-street parking |
| Speed Bumps | Reduces speed, fewer accidents |
| Heavy Traffic Ban | No trucks in residential areas |
| Gated Community | Restricts through-traffic |
| Combustion Engine Ban | Only electric vehicles allowed |

### Building-Level Policies
- Parking Fee (per building)

---

## 18. Districts

### District System
- Players can paint custom districts over the city map
- Each district can have its own policies applied
- District-specific tax rates possible
- Specialized industry per district (farming, forestry, mining, oil)
- Info views show district boundaries and statistics

---

## 19. Progression & Milestones

### XP Generation
- **Passive:** Based on Population × Happiness (every 1.5 in-game hours)
- **Active:** Constructing buildings, roads, infrastructure

### Milestones (1–20)
| Milestone | Reward |
|-----------|--------|
| 1 (Tiny Village) | Starting money + basics |
| 5 (Small City) | Major service unlocks |
| 10 (Large City) | Advanced services |
| 15 (Metropolis) | High-end services |
| 20 (Megalopolis) | +₡500k cash, +₡4M bonus, +30 Dev Points, +56 Expansion Permits |

### Development Tree
- Points unlock specialized service nodes
- 4 tiers costing: 1, 2, 4, 8 points respectively
- Each tier adds capabilities/upgrades to services

### Map Expansion
- Start with 9 tiles
- Total available: 441 tiles (0.4 km² each)
- Expansion Permits required to unlock new tiles

---

## 20. Disasters

### Disaster Types
| Disaster | Trigger | Effects |
|----------|---------|---------|
| Forest Fire | Dry/hot weather | Spreads via trees, destroys buildings |
| Hail Storm | Weather system | Building damage, traffic accidents |
| Tornado | Weather system | Path destruction, injuries, traffic chaos |

### Mitigation
- Early Warning Systems (radars/watchtowers)
- Emergency Shelters for citizen evacuation
- Fire stations for forest fires

---

## 21. Info Views

### Data Visualization Categories
- Wind speed and direction
- Ground pollution levels
- Air pollution levels
- Water pollution levels
- Noise pollution levels
- Land value
- Citizen wealth distribution
- Happiness/Well-being
- Crime rates
- Education levels
- Healthcare coverage
- Service coverage areas
- Traffic density
- Public transit usage
- Resource extraction rates
- Power grid status
- Water network status

---

## 22. Communications

### Post Service
- Physical mail delivery
- Affects company efficiency/satisfaction
- Post offices with truck fleets

### Telecom Service
- High-speed internet infrastructure
- Affects well-being and commercial output
- Telecom towers/stations

---

## Wiki Page Index (All ~300 Content Pages)

### Game System Pages (Core Mechanics)
Accidents, Administration, Age, Air, Air pollution, Attractiveness, Building level, Bus, Cargo Plane, Cargo Ship, Cargo train, Citizens, Climate, Commercial, Communications, Companies, Crime, Criminals, Deathcare, Development, Development Points, Development Tree, Disaster control, Disasters, Districts, Economy, Education, Efficiency, Electricity, Entertainment, Expansion Permits, Fertile Land, Fire & Rescue, Forest, Forest fire, Fuel Plant, Garbage, Garbage Management, Goods, Ground Earth, Ground pollution, Groundwater, Groundwater pollution, Hail storm, Happiness, Health, Healthcare, Industrial, Industry, Info views, Internet, Landmarks, Landscaping, Leisure, Leisure Venues, Lifepath, Mail, Map, Map Tiles, Maps, Metro, Milestones, Mixed Residential, Natural Resources, Noise pollution, Oil, Ore, Parking, Parking Spaces, Parks, Parks & Recreation, Passenger plane, Passenger ship, Passenger train, Pathfinding, Policies, Pollution, Post, Postal, Progression, Rain, Recreation, Residential, Resources, Road, Road Services, Roads, Roundabouts, Seaways, Services, Sewage, Ship, Shopping, Signature buildings, Skyscrapers, Specialized Industry, Speed limits, Subway, Supply Chains, Taxi, Telecom, Terraforming, Tourism, Tourists, Traffic, Traffic accidents, Train, Tram, Transportation, Trees, Vegetation, Vehicles, Water, Water & Sewage, Weather, Well-being, Zoning

### Signature Buildings & Landmarks
Activity Plaza, Architect's Mansion, Auto Center, Baltar Pines, Beach Properties, Bridges and Ports, CO10 Condos, Cane Residences, Century Castle, Chemical Plant, Cloud Lounge FM, Coder Park, Colossal Tower, Constellation Apartments, Corundum Condos, Dairy House, Deluxe Relax Station, Deuclidia Apartments, Dragon Gate, Ember Suites, Epicurean Garden, Extreme Athlete's Villa, Fashion Square, Figura Building, Film Actor Mansion, Food Station, Fuel Plant, Gatehouse Residences, Golfer's Villa, Halo Heights, Incaserium, Ironpress Building, Ludo Square, Mediterranean Heritage, Modern Architecture, Mollari Palace, Multistory Multimedia, Muscle Car Garage, Oil Refinery, Old Factory Condos, One Stop Station, Painter Mansion, Paper Factory, Pharma, Polaris Suites, Pop Musician Mansion, Principiis, Real Estate Agent's Mansion, Rock Musician Mansion, Royal Villa, Rubique Apartments, San Francisco Set, Sculptor Mansion, Square Center, Streamline Diner, Stylus Tower, Switchon, The Capacitor Building, The Emerald Building, The Grass Crown, The Marvelous Marble, Theater Actor Mansion, Urban Promenades, Vehicle Factory, Vertigo Square, Villa City, Vista Building, Wanabe Tower, Waterfall Array, Waveform Tower

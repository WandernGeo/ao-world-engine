# Real-World Coordinates Integration

> Using OSM building footprints to create geographically-accurate simulation worlds

---

## Overview

This document explains how to integrate real-world geographic data from OpenStreetMap (OSM) into the AO World Engine, enabling simulations that map to actual city layouts.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    REAL-WORLD INTEGRATION FLOW                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   OSM Data (buildings, roads, POIs)                                │
│              │                                                      │
│              ▼                                                      │
│   ┌─────────────────────┐                                          │
│   │ osm_to_codec.py     │  ← Converts OSM to World Codec format    │
│   │ • Filter building   │                                          │
│   │   footprints        │                                          │
│   │ • Extract coords    │                                          │
│   │ • Map to districts  │                                          │
│   └─────────────────────┘                                          │
│              │                                                      │
│              ▼                                                      │
│   ┌─────────────────────┐                                          │
│   │ World Codec JSON    │  ← Standard engine format                │
│   │ • buildings[]       │                                          │
│   │ • districts[]       │                                          │
│   │ • npcs[]            │                                          │
│   └─────────────────────┘                                          │
│              │                                                      │
│              ▼                                                      │
│   ┌─────────────────────┐                                          │
│   │ Arweave Upload      │  ← Permanent storage                     │
│   └─────────────────────┘                                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Sources

### OpenStreetMap Exports

| Source | Format | Use Case |
|--------|--------|----------|
| [Overpass API](https://overpass-turbo.eu/) | JSON | Query specific areas |
| [Geofabrik](https://download.geofabrik.de/) | .pbf | Full city/country exports |
| [OSM2World](https://osm2world.org/) | 3D models | If you need 3D geometry |

### What We Extract

```json
{
  "buildings": [
    {
      "osm_id": "way/123456",
      "name": "Empire State Building",
      "type": "commercial",
      "coords": {
        "lat": 40.748817,
        "lng": -73.985428
      },
      "footprint": [[lat, lng], [lat, lng], ...],
      "height": 443,
      "levels": 102
    }
  ],
  "roads": [...],
  "pois": [...]
}
```

---

## Conversion Pipeline

### Step 1: Query OSM for a Region

```bash
# Using Overpass API to get Manhattan buildings
curl -X POST 'https://overpass-api.de/api/interpreter' \
  -d 'data=[out:json];
      area["name"="Manhattan"]->.a;
      way(area.a)["building"];
      out geom;' \
  > manhattan_buildings.json
```

### Step 2: Transform to World Codec Format

```python
# osm_to_codec.py - see scripts/osm_to_codec.py for full implementation
import json

def calculate_bounds(osm_data):
    """Calculate WGS84 bounding box from OSM elements."""
    lats, lngs = [], []
    for element in osm_data.get('elements', []):
        if 'geometry' in element:
            for node in element['geometry']:
                lats.append(node.get('lat', 0))
                lngs.append(node.get('lon', 0))
    return {
        'north': max(lats), 'south': min(lats),
        'east': max(lngs), 'west': min(lngs)
    }

def osm_to_codec(osm_data, world_name="manhattan"):
    """Convert OSM building data to World Codec format."""
    
    codec = {
        "world": {
            "name": world_name,
            "version": "1.0",
            "coordinate_system": "wgs84",  # Real-world coords
            "bounds": calculate_bounds(osm_data)
        },
        "districts": [],
        "buildings": [],
        "npcs": []
    }
    
    for element in osm_data['elements']:
        if element['type'] == 'way' and 'building' in element.get('tags', {}):
            building = {
                "id": f"osm_{element['id']}",
                "osm_id": element['id'],
                "name": element['tags'].get('name', 'Unknown Building'),
                "type": classify_building(element['tags']),
                "coords": {
                    "lat": element['geometry'][0]['lat'],
                    "lng": element['geometry'][0]['lon']  # Standardized to 'lng'
                },
                "footprint": [
                    [node['lat'], node['lon']] 
                    for node in element['geometry']
                ],
                "height": element['tags'].get('height', 10),
                "levels": element['tags'].get('building:levels', 1)
            }
            codec['buildings'].append(building)
    
    return codec

def classify_building(tags):
    """Map OSM building types to engine types."""
    mapping = {
        'residential': 'residential',
        'apartments': 'residential', 
        'commercial': 'commercial',
        'office': 'commercial',
        'retail': 'commercial',
        'industrial': 'industrial',
        'warehouse': 'industrial'
    }
    return mapping.get(tags.get('building'), 'generic')
```

### Step 3: Upload to Arweave

```bash
python upload_world.py --world worlds/manhattan/codec.json
```

---

## World Codec Schema (Extended for Real Coords)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "world": {
      "type": "object",
      "properties": {
        "name": { "type": "string" },
        "coordinate_system": { 
          "enum": ["wgs84", "local", "fictional"]
        },
        "bounds": {
          "type": "object",
          "properties": {
            "north": { "type": "number" },
            "south": { "type": "number" },
            "east": { "type": "number" },
            "west": { "type": "number" }
          }
        },
        "origin": {
          "description": "If using local coords, this is the WGS84 origin",
          "type": "object",
          "properties": {
            "lat": { "type": "number" },
            "lng": { "type": "number" }
          }
        }
      }
    },
    "buildings": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "osm_id": { "type": "integer" },
          "coords": {
            "type": "object",
            "properties": {
              "lat": { "type": "number" },
              "lng": { "type": "number" }
            }
          },
          "footprint": {
            "type": "array",
            "items": {
              "type": "array",
              "items": { "type": "number" }
            }
          }
        }
      }
    }
  }
}
```

---

## Visualization Integration

The frontend visualizer can now render buildings at their real coordinates:

```javascript
// In visualizer, render buildings on MapLibre
buildings.forEach(building => {
  map.addSource(`building-${building.id}`, {
    type: 'geojson',
    data: {
      type: 'Feature',
      geometry: {
        type: 'Polygon',
        coordinates: [building.footprint]
      }
    }
  });
  
  map.addLayer({
    id: `building-${building.id}`,
    type: 'fill-extrusion',
    source: `building-${building.id}`,
    paint: {
      'fill-extrusion-height': building.height,
      'fill-extrusion-color': getColorByType(building.type)
    }
  });
});
```

---

## Use Cases

### 1. "Ghost City" Overlay
Run simulation NPCs on real city layout. Users open app in NYC, see simulated NPCs walking real streets.

### 2. Historical Simulations
Import historical building data, simulate what a city looked like in 1920.

### 3. Hybrid Fictional Cities
Take Manhattan layout, rename everything, create "Neo Liberty" - recognizable but legally distinct.

---

## Privacy & Legal Notes

- OSM data is ODbL licensed - you can use it commercially with attribution
- Building footprints are facts, not copyrightable
- Don't include private residence details
- Recommended: Add disclaimer about fictional nature of simulation

---

## Example: Creating "Neo Manhattan"

```bash
# 1. Export OSM data
python scripts/export_osm.py \
  --region "Manhattan, New York" \
  --output data/manhattan_raw.json

# 2. Transform to World Codec
python scripts/osm_to_codec.py \
  --input data/manhattan_raw.json \
  --output worlds/neo-manhattan/codec.json \
  --rename-districts  # Renames "Midtown" -> "Central Spire", etc.

# 3. Generate NPCs for buildings
python scripts/generate_npcs.py \
  --world worlds/neo-manhattan/codec.json \
  --density 10  # NPCs per building

# 4. Upload to Arweave
python upload_world.py --world worlds/neo-manhattan/
```

---

## Next Steps

- [x] Create `scripts/osm_to_codec.py` - **DONE**
- [x] Implement `calculate_bounds()` function - **DONE**
- [x] Add fictional district renaming support - **DONE**
- [ ] Update visualizer to support WGS84 rendering (consider MapLibre/Deck.gl)
- [ ] Create example world: `worlds/neo-manhattan/`
- [ ] Test with actual Manhattan OSM data
- [ ] Extend World Codec schema for real coords (formal JSON Schema)

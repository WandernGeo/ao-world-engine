#!/usr/bin/env python3
"""
OSM to World Codec Converter

Converts OpenStreetMap building data to AO World Engine World Codec format.
Supports real-world coordinates (WGS84), local coordinates, and fictional naming.

Usage:
    python osm_to_codec.py --input manhattan_raw.json --output worlds/neo-manhattan/codec.json
    python osm_to_codec.py --region "Manhattan, New York" --output worlds/neo-manhattan/codec.json
"""

import json
import argparse
import hashlib
import random
from pathlib import Path
from typing import Any
from datetime import datetime

# District renaming for fictional worlds
DISTRICT_RENAMES = {
    "Midtown": "Central Spire",
    "Downtown": "The Core",
    "Upper East Side": "Ember Heights",
    "Upper West Side": "Signal Ridge",
    "Lower East Side": "Rust Quarter",
    "Lower Manhattan": "Foundation",
    "Harlem": "Neon Reach",
    "Brooklyn": "Circuit Bay",
    "Queens": "Grid Plains",
    "Bronx": "Iron Crown",
    "Financial District": "The Vault",
    "Chinatown": "Jade Circuit",
    "SoHo": "Glass Row",
    "Tribeca": "Tri-Sector",
}

# Building type classification
BUILDING_TYPE_MAP = {
    "residential": "residential",
    "apartments": "residential",
    "house": "residential",
    "detached": "residential",
    "commercial": "commercial",
    "office": "commercial",
    "retail": "commercial",
    "industrial": "industrial",
    "warehouse": "industrial",
    "factory": "industrial",
    "civic": "civic",
    "public": "civic",
    "government": "civic",
    "hospital": "healthcare",
    "clinic": "healthcare",
    "school": "education",
    "university": "education",
    "college": "education",
    "church": "religious",
    "mosque": "religious",
    "temple": "religious",
    "hotel": "hospitality",
    "restaurant": "food",
    "cafe": "food",
    "bar": "entertainment",
    "theatre": "entertainment",
    "cinema": "entertainment",
    "stadium": "entertainment",
    "parking": "infrastructure",
    "garage": "infrastructure",
    "train_station": "transport",
    "subway_entrance": "transport",
}


def calculate_bounds(elements: list[dict]) -> dict:
    """Calculate WGS84 bounding box from OSM elements."""
    lats = []
    lngs = []
    
    for element in elements:
        if "geometry" in element and element["geometry"]:
            for node in element["geometry"]:
                if "lat" in node and "lon" in node:
                    lats.append(node["lat"])
                    lngs.append(node["lon"])
        elif "lat" in element and "lon" in element:
            lats.append(element["lat"])
            lngs.append(element["lon"])
    
    if not lats or not lngs:
        return {"north": 0, "south": 0, "east": 0, "west": 0}
    
    return {
        "north": max(lats),
        "south": min(lats),
        "east": max(lngs),
        "west": min(lngs)
    }


def classify_building(tags: dict) -> str:
    """Map OSM building tags to engine building types."""
    # Check specific building tag first
    building_type = tags.get("building", "")
    if building_type in BUILDING_TYPE_MAP:
        return BUILDING_TYPE_MAP[building_type]
    
    # Check amenity tag
    amenity = tags.get("amenity", "")
    if amenity in BUILDING_TYPE_MAP:
        return BUILDING_TYPE_MAP[amenity]
    
    # Check shop tag
    if tags.get("shop"):
        return "commercial"
    
    # Check office tag
    if tags.get("office"):
        return "commercial"
    
    # Check tourism tag
    tourism = tags.get("tourism", "")
    if tourism in ["hotel", "hostel", "motel"]:
        return "hospitality"
    
    return "generic"


def generate_building_id(osm_id: int, name: str) -> str:
    """Generate a stable building ID from OSM data."""
    hash_input = f"{osm_id}:{name}"
    return f"b_{hashlib.md5(hash_input.encode()).hexdigest()[:8]}"


def rename_district(name: str, use_fictional: bool = False) -> str:
    """Optionally rename districts to fictional equivalents."""
    if use_fictional and name in DISTRICT_RENAMES:
        return DISTRICT_RENAMES[name]
    return name


def osm_to_codec(
    osm_data: dict,
    world_name: str = "custom_world",
    use_fictional_names: bool = False,
    coordinate_system: str = "wgs84"
) -> dict:
    """
    Convert OSM building data to World Codec format.
    
    Args:
        osm_data: Raw OSM JSON data from Overpass API
        world_name: Name for the world
        use_fictional_names: Whether to rename districts to fictional names
        coordinate_system: "wgs84" for real coords, "local" for relative coords
    
    Returns:
        World Codec JSON structure
    """
    elements = osm_data.get("elements", [])
    bounds = calculate_bounds(elements)
    
    # Calculate origin for local coordinate conversion
    origin_lat = (bounds["north"] + bounds["south"]) / 2
    origin_lng = (bounds["east"] + bounds["west"]) / 2
    
    codec = {
        "world": {
            "name": world_name,
            "version": "1.0",
            "coordinate_system": coordinate_system,
            "bounds": bounds,
            "origin": {
                "lat": origin_lat,
                "lng": origin_lng
            },
            "generated_at": datetime.now().isoformat(),
            "source": "openstreetmap"
        },
        "districts": [],
        "buildings": [],
        "roads": [],
        "npcs": []
    }
    
    # Track districts by neighborhood
    districts_seen = set()
    
    for element in elements:
        if element.get("type") != "way":
            continue
        
        tags = element.get("tags", {})
        if "building" not in tags:
            continue
        
        geometry = element.get("geometry", [])
        if not geometry:
            continue
        
        # Extract building info
        osm_id = element.get("id", 0)
        name = tags.get("name", f"Building {osm_id}")
        building_type = classify_building(tags)
        
        # Get centroid from first geometry point
        first_node = geometry[0]
        lat = first_node.get("lat", 0)
        lng = first_node.get("lon", 0)
        
        # Convert to local coordinates if requested
        if coordinate_system == "local":
            # Simple meter conversion (approximate)
            local_x = (lng - origin_lng) * 111320 * abs(origin_lat)
            local_y = (lat - origin_lat) * 110540
            coords = {"x": round(local_x, 2), "y": round(local_y, 2)}
        else:
            coords = {"lat": lat, "lng": lng}
        
        # Extract footprint polygon
        footprint = []
        for node in geometry:
            if coordinate_system == "local":
                fx = (node.get("lon", 0) - origin_lng) * 111320 * abs(origin_lat)
                fy = (node.get("lat", 0) - origin_lat) * 110540
                footprint.append([round(fx, 2), round(fy, 2)])
            else:
                footprint.append([node.get("lat", 0), node.get("lon", 0)])
        
        # Get height/levels
        height = tags.get("height")
        if height:
            try:
                height = float(str(height).replace("m", "").strip())
            except ValueError:
                height = 10
        else:
            height = 10
        
        levels = tags.get("building:levels")
        if levels:
            try:
                levels = int(levels)
            except ValueError:
                levels = max(1, int(height / 3))
        else:
            levels = max(1, int(height / 3))
        
        # Add district if from neighborhood tag
        district = tags.get("addr:neighbourhood") or tags.get("addr:suburb") or "Unknown"
        district = rename_district(district, use_fictional_names)
        if district not in districts_seen:
            districts_seen.add(district)
            codec["districts"].append({
                "id": f"district_{len(codec['districts'])}",
                "name": district,
                "bounds": None  # Could calculate per-district later
            })
        
        # Create building entry
        building = {
            "id": generate_building_id(osm_id, name),
            "osm_id": osm_id,
            "name": name if not use_fictional_names else f"Building {len(codec['buildings']) + 1}",
            "type": building_type,
            "coords": coords,
            "footprint": footprint,
            "height": height,
            "levels": levels,
            "district": district,
            "properties": {
                "amenity": tags.get("amenity"),
                "shop": tags.get("shop"),
                "office": tags.get("office"),
                "addr_street": tags.get("addr:street"),
                "addr_housenumber": tags.get("addr:housenumber"),
            }
        }
        
        # Remove None values from properties
        building["properties"] = {k: v for k, v in building["properties"].items() if v}
        
        codec["buildings"].append(building)
    
    return codec


def export_osm(region: str, output_path: str) -> dict:
    """
    Query Overpass API for building data in a region.
    
    Args:
        region: Area name like "Manhattan, New York"
        output_path: Path to save raw OSM JSON
    
    Returns:
        Raw OSM JSON data
    """
    import urllib.request
    import urllib.parse
    
    # Overpass QL query for buildings
    query = f'''
    [out:json][timeout:180];
    area["name"="{region}"]->.a;
    (
        way(area.a)["building"];
    );
    out geom;
    '''
    
    url = "https://overpass-api.de/api/interpreter"
    data = urllib.parse.urlencode({"data": query}).encode()
    
    print(f"Querying Overpass API for '{region}'...")
    req = urllib.request.Request(url, data=data)
    
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            result = json.loads(response.read().decode())
            
            # Save raw data
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(result, f, indent=2)
            
            print(f"Saved {len(result.get('elements', []))} elements to {output_path}")
            return result
    except Exception as e:
        print(f"Error querying Overpass API: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Convert OSM building data to AO World Engine World Codec format"
    )
    parser.add_argument(
        "--input", "-i",
        help="Path to existing OSM JSON file"
    )
    parser.add_argument(
        "--region", "-r",
        help="Region name to query from Overpass API (e.g., 'Manhattan, New York')"
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Output path for World Codec JSON"
    )
    parser.add_argument(
        "--name", "-n",
        default="custom_world",
        help="World name (default: custom_world)"
    )
    parser.add_argument(
        "--rename-districts",
        action="store_true",
        help="Rename real districts to fictional equivalents"
    )
    parser.add_argument(
        "--local-coords",
        action="store_true",
        help="Convert to local meter-based coordinates instead of WGS84"
    )
    parser.add_argument(
        "--raw-output",
        help="Save raw OSM data to this path when using --region"
    )
    
    args = parser.parse_args()
    
    if not args.input and not args.region:
        parser.error("Either --input or --region is required")
    
    # Get OSM data
    if args.region:
        raw_path = args.raw_output or args.output.replace(".json", "_raw.json")
        osm_data = export_osm(args.region, raw_path)
    else:
        with open(args.input) as f:
            osm_data = json.load(f)
    
    # Convert to codec format
    coord_system = "local" if args.local_coords else "wgs84"
    codec = osm_to_codec(
        osm_data,
        world_name=args.name,
        use_fictional_names=args.rename_districts,
        coordinate_system=coord_system
    )
    
    # Save codec
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(codec, f, indent=2)
    
    # Summary
    print(f"\n✅ World Codec created: {args.output}")
    print(f"   World: {codec['world']['name']}")
    print(f"   Buildings: {len(codec['buildings'])}")
    print(f"   Districts: {len(codec['districts'])}")
    print(f"   Coordinate system: {coord_system}")


if __name__ == "__main__":
    main()

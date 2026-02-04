#!/usr/bin/env python3
"""
World Plugin Loader
===================

Loads world content (NPCs, lore, style) from plugin directories.
Allows switching between different world themes via config.json.
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

class WorldPlugin:
    """Represents a loaded world plugin."""
    
    def __init__(self, world_path: Path):
        self.path = world_path
        self.manifest = self._load_manifest()
        self.name = self.manifest.get("name", "Unknown World")
        self.id = self.manifest.get("id", world_path.name)
        
    def _load_manifest(self) -> Dict[str, Any]:
        manifest_path = self.path / "world.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"No world.json found in {self.path}")
        with open(manifest_path) as f:
            return json.load(f)
    
    def _load_content(self, content_key: str) -> Optional[Dict]:
        """Load a content file specified in the manifest."""
        if content_key not in self.manifest.get("content", {}):
            return None
        
        rel_path = self.manifest["content"][content_key]
        full_path = self.path / rel_path
        
        if not full_path.exists():
            print(f"Warning: {content_key} file not found: {full_path}")
            return None
            
        with open(full_path) as f:
            return json.load(f)
    
    def load_npcs(self) -> Dict:
        """Load all NPCs from the world."""
        return self._load_content("npcs") or {"npcs": []}
    
    def load_founding_npcs(self) -> Dict:
        """Load key/founding NPCs."""
        return self._load_content("founding_npcs") or {"npcs": []}
    
    def load_lore(self) -> Dict:
        """Load world timeline and history."""
        return self._load_content("lore") or {}
    
    def load_factions(self) -> Dict:
        """Load faction definitions."""
        return self._load_content("factions") or {"factions": []}
    
    def load_districts(self) -> Dict:
        """Load district/location data."""
        return self._load_content("districts") or {"districts": []}
    
    def load_buildings(self) -> Dict:
        """Load building data."""
        return self._load_content("buildings") or {"buildings": []}
    
    def get_style(self) -> Dict:
        """Load art style configuration."""
        return self._load_content("style") or {}
    
    def get_css_path(self, css_type: str = "colors") -> Optional[Path]:
        """Get path to CSS file."""
        if "style" not in self.manifest:
            return None
        css_rel = self.manifest["style"].get(css_type)
        if css_rel:
            return self.path / css_rel
        return None
    
    def get_asset_path(self, asset_type: str) -> Optional[Path]:
        """Get path to asset directory."""
        if "assets" not in self.manifest:
            return None
        asset_key = f"{asset_type}_dir"
        if asset_key in self.manifest["assets"]:
            return self.path / self.manifest["assets"][asset_key]
        return None


class WorldLoader:
    """Manages loading and switching between world plugins."""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.engine_root = self.config_path.parent
        self._active_world: Optional[WorldPlugin] = None
        
    def _load_config(self) -> Dict:
        if not self.config_path.exists():
            return {
                "active_world": "example-city",
                "worlds_path": "../worlds",
                "fallback": {"use_example_data": True}
            }
        with open(self.config_path) as f:
            return json.load(f)
    
    @property
    def worlds_path(self) -> Path:
        return self.engine_root / self.config.get("worlds_path", "../worlds")
    
    def list_available_worlds(self) -> list:
        """List all available world plugins."""
        worlds = []
        if self.worlds_path.exists():
            for d in self.worlds_path.iterdir():
                if d.is_dir() and (d / "world.json").exists():
                    worlds.append(d.name)
        return worlds
    
    def load_world(self, world_id: Optional[str] = None) -> Optional[WorldPlugin]:
        """Load a world plugin by ID. Uses active_world from config if not specified."""
        if world_id is None:
            world_id = self.config.get("active_world", "example-city")
        
        world_path = self.worlds_path / world_id
        
        if not world_path.exists():
            print(f"World '{world_id}' not found at {world_path}")
            if self.config.get("fallback", {}).get("use_example_data", True):
                print("Using example data as fallback")
                return None
            return None
        
        try:
            self._active_world = WorldPlugin(world_path)
            print(f"Loaded world: {self._active_world.name}")
            return self._active_world
        except Exception as e:
            print(f"Error loading world '{world_id}': {e}")
            return None
    
    @property
    def active_world(self) -> Optional[WorldPlugin]:
        if self._active_world is None:
            self.load_world()
        return self._active_world
    
    def set_active_world(self, world_id: str) -> bool:
        """Switch to a different world."""
        self.config["active_world"] = world_id
        # Save config
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
        # Load new world
        return self.load_world(world_id) is not None


# Convenience function
def get_world_loader(config_path: str = "config.json") -> WorldLoader:
    """Get a configured world loader instance."""
    return WorldLoader(config_path)


if __name__ == "__main__":
    # Test the loader
    loader = WorldLoader()
    print(f"Available worlds: {loader.list_available_worlds()}")
    
    world = loader.load_world()
    if world:
        print(f"Active world: {world.name}")
        npcs = world.load_npcs()
        print(f"NPCs loaded: {len(npcs.get('npcs', []))}")

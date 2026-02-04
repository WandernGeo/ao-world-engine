#!/usr/bin/env python3
"""
StudioRam Scene Generation API
==============================

Generates canonical character portraits and scene images using Vertex AI Imagen 4.
Integrates with the World Plugin system for style consistency.

Usage:
    from studioram.scene_generator import SceneGenerator
    
    gen = SceneGenerator(world_id="signal-noir")
    portrait = gen.generate_portrait(npc)
    scene = gen.generate_scene(npcs, location, action)
"""

import os
import sys
import json
import base64
from pathlib import Path
from typing import Optional, Dict, List, Any

# Add parent for imports
ENGINE_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ENGINE_ROOT / 'scripts'))

try:
    from world_loader import WorldLoader
except ImportError:
    # Fallback for direct execution
    sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
    from world_loader import WorldLoader

try:
    from google.cloud import aiplatform
    from vertexai.preview.vision_models import ImageGenerationModel
    VERTEX_AVAILABLE = True
except ImportError:
    VERTEX_AVAILABLE = False
    print("Warning: vertexai not available, using mock mode")


class SceneGenerator:
    """Generates images using Vertex AI with world plugin style context."""
    
    def __init__(self, world_id: str = "signal-noir", project_id: str = "stroll-452602"):
        self.project_id = project_id
        self.world_id = world_id
        self.output_dir = Path(__file__).parent.parent / "generated_assets"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load world for style context
        loader = WorldLoader(str(Path(__file__).parent.parent / 'config.json'))
        loader.set_active_world(world_id)
        self.world = loader.active_world
        self.style = self.world.get_style() if self.world else {}
        
        # Init Vertex AI
        if VERTEX_AVAILABLE:
            aiplatform.init(project=project_id, location="us-central1")
            self.model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
        else:
            self.model = None
    
    def _build_style_prompt(self) -> str:
        """Build style prompt from world plugin."""
        if not self.style:
            return "modern, clean, professional illustration"
        
        aesthetic = self.style.get("aesthetic", {})
        visual = self.style.get("visual_elements", {})
        colors = self.style.get("color_palette", {})
        
        style_parts = [
            f"{aesthetic.get('genre', 'modern')} style",
            f"mood: {', '.join(aesthetic.get('mood', ['neutral']))}",
            f"lighting: {visual.get('lighting', 'standard')}",
            f"color palette dominated by {colors.get('primary', '#3B82F6')} and {colors.get('secondary', '#10B981')}",
        ]
        
        return ", ".join(style_parts)
    
    def generate_portrait(self, npc: Dict[str, Any], save: bool = True) -> Optional[str]:
        """
        Generate a canonical portrait for an NPC.
        
        Args:
            npc: NPC data dict with name, personality, archetype
            save: Whether to save to file
            
        Returns:
            Path to saved image or base64 data
        """
        name = npc.get('name', 'Unknown')
        archetype = npc.get('archetype', 'civilian')
        
        # Get personality traits
        personality = npc.get('personality', {})
        if isinstance(personality, dict):
            traits = personality.get('traits', [])
            mbti = personality.get('mbti', '')
            trait_str = f"personality: {mbti}, {', '.join(traits[:3])}" if traits else ""
        else:
            trait_str = f"personality: {personality}"
        
        # Build prompt
        style_prompt = self._build_style_prompt()
        
        prompt = f"""Portrait of {name}, a {archetype} character.
{trait_str}
Style: {style_prompt}
Half-body portrait, detailed face, looking at viewer, high quality digital art.
Background: subtle bokeh matching environment.
"""
        
        print(f"Generating portrait for: {name}")
        print(f"Prompt: {prompt[:200]}...")
        
        if not self.model:
            # Mock mode - return placeholder path
            return str(self.output_dir / f"portrait_{name.replace(' ', '_')}_mock.png")
        
        try:
            response = self.model.generate_images(
                prompt=prompt,
                number_of_images=1,
                aspect_ratio="3:4",
                safety_filter_level="block_some",
                person_generation="allow_adult",
            )
            
            if response.images:
                if save:
                    filename = f"portrait_{name.replace(' ', '_')}.png"
                    filepath = self.output_dir / filename
                    response.images[0].save(str(filepath))
                    print(f"Saved: {filepath}")
                    return str(filepath)
                else:
                    return response.images[0]._image_bytes
                    
        except Exception as e:
            print(f"Error generating portrait: {e}")
            return None
    
    def generate_scene(
        self, 
        npcs: List[Dict], 
        location: str, 
        action: str,
        time_of_day: str = "night",
        weather: str = "rain",
        save: bool = True
    ) -> Optional[str]:
        """
        Generate a scene with multiple NPCs.
        
        Args:
            npcs: List of NPC dicts
            location: Location name/description
            action: What's happening in the scene
            time_of_day: morning, afternoon, evening, night
            weather: clear, rain, fog, etc.
            save: Whether to save to file
            
        Returns:
            Path to saved image or base64 data
        """
        # Build character descriptions
        char_descriptions = []
        for npc in npcs[:3]:  # Max 3 characters
            name = npc.get('name', 'Unknown')
            archetype = npc.get('archetype', 'person')
            char_descriptions.append(f"{name} ({archetype})")
        
        chars_str = ", ".join(char_descriptions)
        
        # Build prompt
        style_prompt = self._build_style_prompt()
        
        prompt = f"""Scene in {location}.
Characters: {chars_str}
Action: {action}
Time: {time_of_day}
Weather: {weather}
Style: {style_prompt}
Wide shot, cinematic composition, dramatic lighting, detailed environment.
High quality digital illustration, professional concept art.
"""
        
        print(f"Generating scene at: {location}")
        print(f"Characters: {chars_str}")
        print(f"Action: {action}")
        
        if not self.model:
            # Mock mode
            scene_name = location.replace(' ', '_').replace("'", "")[:20]
            return str(self.output_dir / f"scene_{scene_name}_mock.png")
        
        try:
            response = self.model.generate_images(
                prompt=prompt,
                number_of_images=1,
                aspect_ratio="16:9",
                safety_filter_level="block_some",
                person_generation="allow_adult",
            )
            
            if response.images:
                if save:
                    scene_name = location.replace(' ', '_').replace("'", "")[:20]
                    filename = f"scene_{scene_name}.png"
                    filepath = self.output_dir / filename
                    response.images[0].save(str(filepath))
                    print(f"Saved: {filepath}")
                    return str(filepath)
                else:
                    return response.images[0]._image_bytes
                    
        except Exception as e:
            print(f"Error generating scene: {e}")
            return None
    
    def get_prompt_for_interaction(self, interaction: Dict) -> str:
        """
        Generate a scene prompt from an NPC interaction event.
        
        Args:
            interaction: Interaction dict from simulation
            
        Returns:
            Prompt string for image generation
        """
        npc1 = interaction.get('npc1', 'Character 1')
        npc2 = interaction.get('npc2', 'Character 2')
        interaction_type = interaction.get('type', 'conversation')
        
        type_to_action = {
            'friendly_chat': 'having a friendly conversation, relaxed postures',
            'conflict': 'in tense confrontation, aggressive stances',
            'trade': 'exchanging items, business transaction',
            'gossip': 'leaning close, whispering secrets',
            'brief_nod': 'passing each other with a knowing nod',
        }
        
        action = type_to_action.get(interaction_type, 'interacting')
        style_prompt = self._build_style_prompt()
        
        return f"""Two characters in a cyberpunk city street.
{npc1} and {npc2} are {action}.
Style: {style_prompt}
Night time, neon lights, rain-slicked streets.
Cinematic wide shot, dramatic lighting.
"""


# API endpoint function for Flask
def generate_portrait_endpoint(npc_id: str) -> Dict:
    """Flask API endpoint wrapper."""
    # Load NPC from world
    loader = WorldLoader('config.json')
    world = loader.active_world
    if not world:
        return {"error": "World not loaded"}
    
    npcs = world.load_npcs().get('npcs', [])
    npc = next((n for n in npcs if n.get('id') == npc_id), None)
    
    if not npc:
        return {"error": f"NPC {npc_id} not found"}
    
    gen = SceneGenerator()
    path = gen.generate_portrait(npc)
    
    return {"path": path, "npc": npc.get('name')}


def generate_scene_endpoint(npc_ids: List[str], location: str, action: str) -> Dict:
    """Flask API endpoint wrapper."""
    loader = WorldLoader('config.json')
    world = loader.active_world
    if not world:
        return {"error": "World not loaded"}
    
    npcs_data = world.load_npcs().get('npcs', [])
    npcs = [n for n in npcs_data if n.get('id') in npc_ids]
    
    gen = SceneGenerator()
    path = gen.generate_scene(npcs, location, action)
    
    return {"path": path, "characters": [n.get('name') for n in npcs]}


# CLI test
if __name__ == "__main__":
    print("="*60)
    print("  StudioRam Scene Generator Test")
    print("="*60)
    
    gen = SceneGenerator(world_id="signal-noir")
    
    print(f"\nWorld: {gen.world.name if gen.world else 'Not loaded'}")
    print(f"Style: {gen.style.get('name', 'Unknown')}")
    print(f"Output dir: {gen.output_dir}")
    
    # Test with sample NPC
    sample_npc = {
        "id": "NPC_00001",
        "name": "Maya Black",
        "archetype": "hacker",
        "personality": {
            "mbti": "ENFJ",
            "traits": ["charismatic", "creative", "authentic"]
        }
    }
    
    print("\n--- Testing Portrait Generation ---")
    result = gen.generate_portrait(sample_npc)
    print(f"Result: {result}")
    
    print("\n--- Testing Scene Generation ---")
    scene_result = gen.generate_scene(
        npcs=[sample_npc, {"name": "Felix Tanaka", "archetype": "bartender"}],
        location="Neon District Bar",
        action="having a tense conversation about recent events"
    )
    print(f"Result: {scene_result}")
    
    print("\n--- Testing Interaction Prompt ---")
    interaction = {
        "npc1": "Maya Black",
        "npc2": "Felix Tanaka",
        "type": "gossip"
    }
    prompt = gen.get_prompt_for_interaction(interaction)
    print(f"Prompt:\n{prompt}")
    
    print("\n✅ Test complete!")

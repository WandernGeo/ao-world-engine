"""
AO World Engine - Signal Noir Scene Generator
Uses Vertex AI Imagen to generate cyberpunk noir scenes from RE:ECHO City.

DISCLAIMER: This is a lightweight demo using Gemini/Imagen models.
For production quality, you'd use custom LoRA-trained models.
Uses Vertex AI - no API keys exposed. Free tier may be available.

Usage:
    python generate_scene.py --npc kira --location neon_market --tick 100
    
OR use your own API key:
    GOOGLE_API_KEY=your_key python generate_scene.py --npc kira --use-gemini-api
"""
import os
import sys
import json
import hashlib
import argparse
from datetime import datetime
from pathlib import Path

# Signal Noir Style Constants (from StudioRam/specs/styles/signal_noir.json)
SIGNAL_NOIR_STYLE = """
SIGNAL NOIR STYLE - MANDATORY:
- Render in BLACK AND WHITE / GRAYSCALE
- Deep inky black shadows, high contrast
- Grayscale with ONLY CYAN (#00CED1) accents for tech/neon
- No other colors - NO red, green, yellow, orange, pink, purple
- Cyberpunk dystopian atmosphere
- Rain atmosphere, wet surfaces with reflections
- Noir cinematography, dramatic shadows
- Always night time, fog/steam in air
- Sin City / Blade Runner aesthetic
"""

NPC_VISUAL_PROFILES = {
    "kira": {
        "description": "Young Japanese woman street oracle, mid-20s, short asymmetric black hair, intense eyes with slight amber glow (mystical power), worn coat over cyberpunk clothing, spiritual tattoos visible on neck",
        "mood_default": "mystical and knowing",
        "color_accents": "subtle amber glow in eyes (mystical)"
    },
    "cipher": {
        "description": "Androgynous AI entity, glowing cyan circuit patterns visible under translucent skin, bald head with data port, cold machine-like features, wearing dark tech-suit",
        "mood_default": "calculating and precise",
        "color_accents": "cyan circuit patterns and glowing eyes"
    },
    "marco": {
        "description": "Middle-aged Asian man street merchant, weathered face, salt-pepper stubble, cybernetic left eye (cyan glow), worn leather jacket with hidden pockets, shrewd expression",
        "mood_default": "opportunistic and cautious",
        "color_accents": "cyan cybernetic eye"
    },
    "charlie": {
        "description": "Noir detective, Caucasian male, 40s, wearing long trenchcoat and fedora, cigarette smoke, five o'clock shadow, tired cynical eyes, rain dripping from hat brim",
        "mood_default": "world-weary and determined",
        "color_accents": "cyan neon reflections from surroundings"
    },
    "blade": {
        "description": "Japanese street samurai, muscular build, traditional-cyberpunk hybrid armor, katana on back, short black hair with white streak, facial scars, cold disciplined expression",
        "mood_default": "controlled intensity",
        "color_accents": "cyan glow from cybernetic arm joints"
    }
}

LOCATION_DESCRIPTIONS = {
    "neon_market": "Crowded cyberpunk night market, flickering holographic stall signs (cyan glow only), rain puddles reflecting neon, dense crowd silhouettes, steam from food vendors, wet pavement",
    "shadow_grid": "Abandoned server farm interior, rows of dark server racks with scattered cyan LED lights, cables everywhere, dust motes in air, lone figure silhouette",
    "rain_soaked_alley": "Narrow alley at night, heavy rain, fire escape above, neon sign reflection in puddles (cyan only), steam from grate, brick walls with graffiti, noir atmosphere",
    "dojo": "Traditional Japanese dojo interior, dark wooden floors with moonlight through paper screens, weapon racks, incense smoke, single cyan light from tech panel",
    "rooftop": "High rooftop at night, city skyline with corporate towers in background, rain falling, city lights far below (cyan neons only), wind-blown figure"
}

WEATHER_MODIFIERS = {
    "clear": "light fog, distant city lights, cold atmosphere",
    "rain": "heavy rain streaks, puddles with reflections, wet surfaces, rain running down surfaces",
    "storm": "dramatic storm clouds, lightning flash, heavy rain, wind effects",
    "fog": "dense fog rolling through, limited visibility, ghostly atmosphere, moisture in air"
}


def build_scene_prompt(npc_id: str, location: str, tick: int, custom_action: str = None):
    """Build a Signal Noir style prompt for scene generation."""
    npc = NPC_VISUAL_PROFILES.get(npc_id, NPC_VISUAL_PROFILES["kira"])
    loc_desc = LOCATION_DESCRIPTIONS.get(location, LOCATION_DESCRIPTIONS["rain_soaked_alley"])
    
    # Deterministic weather from tick
    weather_types = ["clear", "rain", "storm", "fog"]
    weather_seed = int(hashlib.md5(f"weather_{tick // 6}".encode()).hexdigest(), 16)
    weather = weather_types[weather_seed % 4]
    weather_mod = WEATHER_MODIFIERS[weather]
    
    # Time context
    hour = tick % 24
    if hour < 6:
        time_desc = "deep night, darkest hours"
    elif hour < 12:
        time_desc = "pre-dawn darkness, faint city glow"
    else:
        time_desc = "night, neon lights active"
    
    # Build prompt
    action = custom_action or f"standing, {npc['mood_default']} expression"
    
    prompt = f"""
{npc['description']}

{action}

LOCATION: {loc_desc}

ATMOSPHERE: {time_desc}, {weather_mod}

{SIGNAL_NOIR_STYLE}

COLOR ACCENTS:
- {npc['color_accents']}
- Cyan neon reflections in puddles and wet surfaces
- NO OTHER COLORS

COMPOSITION: Cinematic wide shot, rule of thirds, dramatic noir lighting, 
character slightly off-center, deep shadows, atmospheric depth.

Style: Signal Noir, Frank Miller Sin City meets Blade Runner, 
high contrast black and white with cyan tech accents only.
"""
    return prompt.strip()


def generate_with_vertex_imagen(prompt: str, output_path: str):
    """Generate image using Vertex AI Imagen."""
    try:
        import vertexai
        from vertexai.vision_models import ImageGenerationModel
        
        project = os.environ.get("GCP_PROJECT", "your-gcp-project")
        location = os.environ.get("GCP_LOCATION", "us-central1")
        
        vertexai.init(project=project, location=location)
        model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
        
        print("🎨 Generating with Vertex AI Imagen 3...")
        response = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio="16:9",
            safety_filter_level="block_few",
            person_generation="allow_adult",
        )
        
        if response.images:
            response.images[0].save(output_path)
            print(f"✅ Saved to: {output_path}")
            return True
        else:
            print("❌ No images generated")
            return False
            
    except ImportError:
        print("❌ Vertex AI SDK not installed. Run: pip install google-cloud-aiplatform")
        return False
    except Exception as e:
        print(f"❌ Vertex AI error: {e}")
        return False


def generate_with_gemini_api(prompt: str, output_path: str, api_key: str = None):
    """Generate image using Gemini API (for users with their own keys)."""
    key = api_key or os.environ.get("GOOGLE_API_KEY")
    if not key:
        print("❌ No API key. Set GOOGLE_API_KEY or pass --api-key")
        return False
    
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=key)
        model = genai.ImageGenerationModel("imagen-3.0-generate-001")
        
        print("🎨 Generating with Gemini API...")
        result = model.generate_images(
            prompt=prompt,
            number_of_images=1,
        )
        
        if result.images:
            result.images[0].save(output_path)
            print(f"✅ Saved to: {output_path}")
            return True
        else:
            print("❌ No images generated")
            return False
            
    except ImportError:
        print("❌ google-generativeai not installed. Run: pip install google-generativeai")
        return False
    except Exception as e:
        print(f"❌ Gemini API error: {e}")
        return False


def generate_with_gemini_flash_description(prompt: str):
    """Use Gemini Flash to generate a text description (free, for demo)."""
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel
        
        project = os.environ.get("GCP_PROJECT", "your-gcp-project")
        location = os.environ.get("GCP_LOCATION", "us-central1")
        
        vertexai.init(project=project, location=location)
        model = GenerativeModel("gemini-2.0-flash")
        
        desc_prompt = f"""Based on this scene prompt, write a vivid 2-3 sentence description of what the image would look like. Be atmospheric and cinematic.

PROMPT:
{prompt}

Write the scene description:"""
        
        response = model.generate_content(desc_prompt)
        return response.text
        
    except Exception as e:
        return f"[Could not generate description: {e}]"


def main():
    parser = argparse.ArgumentParser(description="Generate Signal Noir scenes from RE:ECHO City")
    parser.add_argument("--npc", choices=list(NPC_VISUAL_PROFILES.keys()), default="kira", 
                        help="NPC to feature in scene")
    parser.add_argument("--location", choices=list(LOCATION_DESCRIPTIONS.keys()), default="rain_soaked_alley",
                        help="Scene location")
    parser.add_argument("--tick", type=int, default=100, help="Simulation tick (affects weather)")
    parser.add_argument("--action", type=str, help="Custom action/pose for NPC")
    parser.add_argument("--output", type=str, help="Output file path")
    parser.add_argument("--use-gemini-api", action="store_true", help="Use Gemini API instead of Vertex AI")
    parser.add_argument("--api-key", type=str, help="Your Gemini API key")
    parser.add_argument("--describe-only", action="store_true", help="Only output text description (free)")
    parser.add_argument("--show-prompt", action="store_true", help="Just show the prompt, don't generate")
    
    args = parser.parse_args()
    
    # Build prompt
    prompt = build_scene_prompt(args.npc, args.location, args.tick, args.action)
    
    if args.show_prompt:
        print("=" * 60)
        print("SIGNAL NOIR SCENE PROMPT")
        print("=" * 60)
        print(prompt)
        return
    
    print("=" * 60)
    print("🌃 RE:ECHO City - Signal Noir Scene Generator")
    print("=" * 60)
    print(f"NPC: {args.npc}")
    print(f"Location: {args.location}")
    print(f"Tick: {args.tick}")
    print()
    
    # Disclaimer
    print("⚠️  DISCLAIMER: This is a demo using standard Imagen models.")
    print("    For production Signal Noir quality, use custom LoRA-trained models.")
    print("    Results may not perfectly match the style guide.")
    print()
    
    if args.describe_only:
        print("📝 Generating text description (free)...")
        description = generate_with_gemini_flash_description(prompt)
        print()
        print("SCENE DESCRIPTION:")
        print("-" * 40)
        print(description)
        return
    
    # Output path
    output = args.output or f"output/scene_{args.npc}_{args.location}_{args.tick}.png"
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    
    # Generate
    if args.use_gemini_api:
        success = generate_with_gemini_api(prompt, output, args.api_key)
    else:
        success = generate_with_vertex_imagen(prompt, output)
    
    if success:
        print()
        print("🎬 Scene generated! Open the image to view.")
    else:
        print()
        print("💡 TIP: Use --describe-only for free text description")
        print("   Or set up Vertex AI / provide your own API key")


if __name__ == "__main__":
    main()

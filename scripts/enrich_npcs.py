#!/usr/bin/env python3
"""
NPC Backstory Enrichment Script
Uses Vertex AI Gemini Flash to add backstories and catchphrases to generated NPCs.

Cost estimate: ~2,830 NPCs × ~200 output tokens = ~566K tokens ≈ $0.04 (Gemini 2.0 Flash)

Usage:
    python enrich_npcs.py --input data/generated_npcs/all_generated_npcs.json --batch 50
    python enrich_npcs.py --district harbor_quarter --batch 25
    python enrich_npcs.py --governance-only
"""

import json
import os
import sys
import time
import argparse
import random
from pathlib import Path

try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    HAS_VERTEX = True
except ImportError:
    HAS_VERTEX = False
    print("⚠️ vertexai not installed. Install with: pip install google-cloud-aiplatform")

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
INPUT_DIR = DATA_DIR / "generated_npcs"
OUTPUT_DIR = DATA_DIR / "enriched_npcs"

# Vertex AI config
PROJECT_ID = "${GCP_PROJECT:-your-gcp-project}"
LOCATION = "us-central1"
MODEL_ID = "gemini-2.0-flash"

BACKSTORY_PROMPT = """You are a fiction writer creating character backgrounds for a cyberpunk city simulation.

Generate a backstory_summary (2-3 sentences) and a catchphrase (one short memorable line) for this NPC.

The city is a cyberpunk metropolis with factions: Corps (corporate), Temple (religious order), Resistance (rebels), Underground (criminal network), Mystics (tech-shamans), and Neutral.

NPC:
- Name: {name}
- Age: {age}, Gender: {gender}
- Ethnicity: {ethnicity}
- District: {district_name} ({district_vibe})
- Job: {job_title}
- Faction: {faction}
- Values: {values}
- Fears: {fears}
- Political: {political_alignment}

Respond in EXACTLY this JSON format (no markdown, no explanation):
{{"backstory_summary": "...", "catchphrase": "..."}}"""

DISTRICT_VIBES = {
    "neon_district": "Sleek, fast-paced, neon-lit. Money and ambition",
    "harbor_quarter": "Colorful, loud, authentic. Food smells, music from windows, kids on stoops",
    "temple_heights": "Incense, chanting, paper lanterns. Ancient rituals in a cyberpunk shell",
    "old_town": "Brick buildings, fire escapes, corner delis. Everyone knows everyone",
    "industrial_zone": "Smoke stacks, welding sparks, union halls. Pride in hard work",
    "the_gardens": "Spice markets, community gardens, Arabic coffee shops. Family first",
    "tech_quarter": "Holographic displays, coworking spaces, ramen joints. Move fast, build things",
    "outskirts": "Salvaged shelters, community fires, resilience. The city forgot them; they built their own",
}


def init_vertex():
    """Initialize Vertex AI."""
    if not HAS_VERTEX:
        print("❌ vertexai package required. Run: pip install google-cloud-aiplatform")
        sys.exit(1)
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    return GenerativeModel(MODEL_ID)


def build_prompt(npc: dict) -> str:
    """Build the enrichment prompt for an NPC."""
    district = npc.get("life", {}).get("district", "neon_district")
    return BACKSTORY_PROMPT.format(
        name=npc.get("name", "Unknown"),
        age=npc.get("age", 30),
        gender=npc.get("gender", "unknown"),
        ethnicity=npc.get("ethnicity", "mixed"),
        district_name=npc.get("life", {}).get("district_name", "Unknown"),
        district_vibe=DISTRICT_VIBES.get(district, "A cyberpunk city district"),
        job_title=npc.get("role", {}).get("job_title", "Citizen"),
        faction=npc.get("faction", "Neutral"),
        values=", ".join(npc.get("personality", {}).get("values", ["survival"])),
        fears=", ".join(npc.get("personality", {}).get("fears", ["the unknown"])),
        political_alignment=npc.get("political_alignment", "moderate"),
    )


def enrich_npc(model, npc: dict) -> dict:
    """Enrich a single NPC with backstory and catchphrase."""
    prompt = build_prompt(npc)
    
    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.9,
                "max_output_tokens": 200,
                "response_mime_type": "application/json",
            }
        )
        
        result = json.loads(response.text)
        npc["backstory_summary"] = result.get("backstory_summary", "")
        npc["catchphrase"] = result.get("catchphrase", "")
        return npc
        
    except json.JSONDecodeError:
        # Try to extract from non-JSON response
        text = response.text.strip()
        if '"backstory_summary"' in text:
            # Try to find JSON in the response
            start = text.find('{')
            end = text.rfind('}') + 1
            if start >= 0 and end > start:
                try:
                    result = json.loads(text[start:end])
                    npc["backstory_summary"] = result.get("backstory_summary", "")
                    npc["catchphrase"] = result.get("catchphrase", "")
                    return npc
                except:
                    pass
        npc["backstory_summary"] = "[GENERATION_FAILED]"
        npc["catchphrase"] = ""
        return npc
        
    except Exception as e:
        print(f"    ⚠️ Error for {npc['name']}: {e}")
        npc["backstory_summary"] = "[GENERATION_FAILED]"
        npc["catchphrase"] = ""
        return npc


def enrich_batch(model, npcs: list, batch_name: str = "", delay: float = 0.1) -> list:
    """Enrich a batch of NPCs."""
    enriched = []
    total = len(npcs)
    
    for i, npc in enumerate(npcs):
        # Skip already enriched
        if npc.get("backstory_summary") and npc["backstory_summary"] != "[GENERATION_FAILED]":
            enriched.append(npc)
            continue
            
        enriched_npc = enrich_npc(model, npc)
        enriched.append(enriched_npc)
        
        # Progress
        if (i + 1) % 10 == 0 or i == total - 1:
            success = sum(1 for n in enriched if n.get("backstory_summary") and n["backstory_summary"] != "[GENERATION_FAILED]")
            print(f"    {batch_name} [{i+1}/{total}] ✅ {success} enriched")
        
        # Rate limiting
        time.sleep(delay)
    
    return enriched


def main():
    parser = argparse.ArgumentParser(description="Enrich NPCs with Gemini-generated backstories")
    parser.add_argument("--input", type=str, default=str(INPUT_DIR / "all_generated_npcs.json"),
                        help="Input JSON file")
    parser.add_argument("--district", type=str, help="Enrich only a specific district file")
    parser.add_argument("--governance-only", action="store_true", help="Only enrich governance NPCs")
    parser.add_argument("--batch", type=int, default=50, help="Batch size (for progress tracking)")
    parser.add_argument("--delay", type=float, default=0.05, help="Delay between API calls (seconds)")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of NPCs to process (0=all)")
    parser.add_argument("--output", type=str, default=str(OUTPUT_DIR), help="Output directory")
    parser.add_argument("--dry-run", action="store_true", help="Don't call API, just show what would be done")
    
    args = parser.parse_args()
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine input file
    if args.governance_only:
        input_file = INPUT_DIR / "governance_npcs.json"
        key = "governance_npcs"
    elif args.district:
        input_file = INPUT_DIR / f"district_{args.district}.json"
        key = "npcs"
    else:
        input_file = Path(args.input)
        key = "npcs"
    
    print(f"📖 Loading {input_file}...")
    with open(input_file) as f:
        data = json.load(f)
    
    npcs = data.get(key, data.get("npcs", []))
    if args.limit > 0:
        npcs = npcs[:args.limit]
    
    print(f"   Found {len(npcs)} NPCs to enrich")
    
    # Check how many already have backstories
    already_done = sum(1 for n in npcs if n.get("backstory_summary") and n["backstory_summary"] != "[GENERATION_FAILED]")
    if already_done > 0:
        print(f"   {already_done} already have backstories (will skip)")
    
    if args.dry_run:
        print("\n🔍 DRY RUN — showing 3 sample prompts:\n")
        for npc in random.sample(npcs, min(3, len(npcs))):
            print(f"--- {npc['name']} ({npc['ethnicity']}, {npc['role']['job_title']}) ---")
            print(build_prompt(npc)[:300])
            print()
        return
    
    # Initialize Vertex AI
    model = init_vertex()
    print(f"🤖 Using {MODEL_ID} via Vertex AI")
    print(f"   Project: {PROJECT_ID}")
    print(f"   Estimated cost: ~${len(npcs) * 0.000015:.4f}")
    print()
    
    # Process in batches
    start_time = time.time()
    enriched_npcs = enrich_batch(model, npcs, "ALL", delay=args.delay)
    elapsed = time.time() - start_time
    
    # Stats
    success_count = sum(1 for n in enriched_npcs if n.get("backstory_summary") and n["backstory_summary"] != "[GENERATION_FAILED]")
    fail_count = sum(1 for n in enriched_npcs if n.get("backstory_summary") == "[GENERATION_FAILED]")
    
    print(f"\n{'='*60}")
    print(f"📚 ENRICHMENT COMPLETE")
    print(f"{'='*60}")
    print(f"  Processed:  {len(enriched_npcs)}")
    print(f"  Success:    {success_count}")
    print(f"  Failed:     {fail_count}")
    print(f"  Time:       {elapsed:.1f}s ({elapsed/len(enriched_npcs):.2f}s/NPC)")
    
    # Save output
    data[key] = enriched_npcs
    
    if args.governance_only:
        out_file = output_dir / "governance_npcs_enriched.json"
    elif args.district:
        out_file = output_dir / f"district_{args.district}_enriched.json"
    else:
        out_file = output_dir / "all_enriched_npcs.json"
    
    with open(out_file, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"  Saved to:   {out_file}")
    
    # Show samples
    print(f"\n📖 Sample backstories:")
    samples = [n for n in enriched_npcs if n.get("backstory_summary") and n["backstory_summary"] != "[GENERATION_FAILED]"]
    for npc in random.sample(samples, min(5, len(samples))):
        print(f"\n  {npc['name']} ({npc['role']['job_title']}, {npc['life']['district_name']})")
        print(f"  \"{npc.get('backstory_summary', 'N/A')}\"")
        print(f"  💬 \"{npc.get('catchphrase', 'N/A')}\"")


if __name__ == "__main__":
    main()

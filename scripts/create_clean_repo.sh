#!/bin/bash
# Create fresh public repo without IP history

set -e

SOURCE="/Users/ram/Documents/wandern/ao-world-engine"
DEST="/Users/ram/Documents/wandern/ao-world-engine-clean"

echo "=== Creating fresh public repo ==="

# Files to EXCLUDE from public repo (IP content)
EXCLUDE_FILES=(
    "docs/SIGNAL_NOIR_STYLE_GUIDE.md"
    "docs/MULTIVERSE_LORE.md"
    "docs/BLOG_THE_WATCHERS.md"
    "docs/X_THREAD_LAUNCH.md"
    "docs/WHITEPAPER.md"
    "VISION.md"
    "archetypes/philosophers.json"
    "data/founding_npcs.py"
    "data/founding_npcs"
    "data/codec_chunks/world_codec_13_canon_events.json"
)

# Create clean copy
mkdir -p "$DEST"

# Copy everything except git and excluded files
rsync -av --progress "$SOURCE/" "$DEST/" \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='.next' \
    --exclude='*.pyc' \
    --exclude='__pycache__'

# Remove IP files from clean copy
cd "$DEST"
for file in "${EXCLUDE_FILES[@]}"; do
    if [ -e "$file" ]; then
        rm -rf "$file"
        echo "Removed: $file"
    fi
done

# Initialize fresh git
git init
git add -A
git commit -m "Initial commit: AO World Engine v1.0.0

Open source simulation framework for persistent decentralized worlds.

Features:
- 800 NPC simulation with deterministic scheduling
- Economy system with wealth tiers and trading
- Cascading event system (Dwarf Fortress style)
- Faction AI with strategic goals
- Arweave/AO integration
- LLM-powered NPC dialogue

Built for Arweave + AO by WandernGeo"

echo ""
echo "=== Done! Fresh repo at: $DEST ==="
echo "Next: Create new GitHub repo and push"

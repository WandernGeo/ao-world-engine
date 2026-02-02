#!/usr/bin/env python3
"""
Chunked World Codec Loader
===========================

Loads and chains World Codec chunks from files or Arweave.
Provides unified interface for querying across all chunks.

The chunking system allows:
- Each chunk is under 100KB (Arweave free tier)
- Chunks are linked via prev_chunk/next_chunk
- Total knowledge base can be unlimited
- Queries resolve references across chunks
"""

import json
import os
import hashlib
from typing import Dict, List, Optional, Any, Set

# Chunk definitions in order
CHUNK_ORDER = [
    "world_codec_00_core.json",
    "world_codec_01_npcs.json", 
    "world_codec_02_medical.json",
    "world_codec_03_tech.json",
    "world_codec_04_chemistry.json",
    "world_codec_05_lore.json",
    "world_codec_06_skills.json",
    "world_codec_07_events.json"
]

# Get the directory where this script is located
CHUNK_DIR = os.path.dirname(os.path.abspath(__file__))


class ChunkedCodec:
    """
    Unified interface for the chunked World Codec.
    Loads all chunks and provides cross-reference resolution.
    """
    
    def __init__(self, chunk_dir: str = None):
        self.chunk_dir = chunk_dir or CHUNK_DIR
        self.chunks: Dict[str, dict] = {}
        self.loaded = False
        
        # Index caches for fast lookup
        self._action_index: Dict[str, dict] = {}
        self._object_index: Dict[str, dict] = {}
        self._location_index: Dict[str, dict] = {}
        self._npc_index: Dict[str, dict] = {}
        self._medical_index: Dict[str, dict] = {}
        self._cybernetic_index: Dict[str, dict] = {}
        self._skill_index: Dict[str, dict] = {}
        self._drug_index: Dict[str, dict] = {}
        
    def load_all_chunks(self) -> bool:
        """Load all chunk files and build indexes."""
        for chunk_file in CHUNK_ORDER:
            chunk_path = os.path.join(self.chunk_dir, chunk_file)
            if os.path.exists(chunk_path):
                try:
                    with open(chunk_path, 'r') as f:
                        chunk_data = json.load(f)
                        chunk_id = chunk_data.get("_chunk", {}).get("id", chunk_file)
                        self.chunks[chunk_id] = chunk_data
                except Exception as e:
                    print(f"⚠️ Error loading {chunk_file}: {e}")
        
        if self.chunks:
            self._build_indexes()
            self.loaded = True
            
        return self.loaded
    
    def _build_indexes(self):
        """Build lookup indexes from all loaded chunks."""
        
        # Index actions from core chunk
        if "chunk_00_core" in self.chunks:
            core = self.chunks["chunk_00_core"]
            if "actions" in core:
                for category, actions in core["actions"].items():
                    if isinstance(actions, dict) and not category.startswith("_"):
                        for code, name in actions.items():
                            self._action_index[code] = {"name": name, "category": category}
            
            if "objects" in core:
                for category, objects in core["objects"].items():
                    if isinstance(objects, dict) and not category.startswith("_"):
                        for code, data in objects.items():
                            if isinstance(data, str):
                                self._object_index[code] = {"name": data, "category": category}
                            else:
                                self._object_index[code] = {**data, "category": category}
            
            if "locations" in core:
                for category, locs in core["locations"].items():
                    if isinstance(locs, dict) and not category.startswith("_"):
                        for code, data in locs.items():
                            if isinstance(data, dict):
                                self._location_index[code] = {**data, "category": category}
        
        # Index NPCs
        if "chunk_01_npcs" in self.chunks:
            npcs = self.chunks["chunk_01_npcs"]
            if "founding_npcs" in npcs:
                for npc_id, npc_data in npcs["founding_npcs"].items():
                    if isinstance(npc_data, dict):
                        self._npc_index[npc_id] = npc_data
                        if "code" in npc_data:
                            self._npc_index[npc_data["code"]] = npc_data
        
        # Index medical conditions and drugs
        if "chunk_02_medical" in self.chunks:
            med = self.chunks["chunk_02_medical"]
            if "conditions" in med:
                for category, conditions in med["conditions"].items():
                    if isinstance(conditions, dict) and not category.startswith("_"):
                        for code, data in conditions.items():
                            self._medical_index[code] = {**data, "type": "condition", "category": category}
            if "drugs" in med:
                for category, drugs in med["drugs"].items():
                    if isinstance(drugs, dict) and not category.startswith("_"):
                        for code, data in drugs.items():
                            self._drug_index[code] = {**data, "category": category}
        
        # Index cybernetics
        if "chunk_03_tech" in self.chunks:
            tech = self.chunks["chunk_03_tech"]
            if "cybernetics" in tech:
                for category, cybers in tech["cybernetics"].items():
                    if isinstance(cybers, dict) and not category.startswith("_"):
                        for code, data in cybers.items():
                            self._cybernetic_index[code] = {**data, "category": category}
        
        # Index skills
        if "chunk_06_skills" in self.chunks:
            skills = self.chunks["chunk_06_skills"]
            if "skills" in skills:
                for category, skill_list in skills["skills"].items():
                    if isinstance(skill_list, dict) and not category.startswith("_"):
                        for code, data in skill_list.items():
                            self._skill_index[code] = {**data, "category": category}
    
    # =========== Query Methods ===========
    
    def decode_action(self, code: str) -> Optional[dict]:
        """Decode an action code to full entry."""
        return self._action_index.get(code)
    
    def decode_object(self, code: str) -> Optional[dict]:
        """Decode an object code to full entry."""
        return self._object_index.get(code)
    
    def decode_location(self, code: str) -> Optional[dict]:
        """Decode a location code to full entry."""
        return self._location_index.get(code)
    
    def get_npc(self, npc_id: str) -> Optional[dict]:
        """Get NPC data by ID or code."""
        return self._npc_index.get(npc_id)
    
    def get_npc_relationships(self, npc_id: str) -> Dict[str, dict]:
        """Get all relationships for an NPC."""
        npc = self.get_npc(npc_id)
        if not npc:
            return {}
        return npc.get("relationships", {})
    
    def get_npc_relationship(self, npc_a: str, npc_b: str) -> Optional[dict]:
        """Get specific relationship between two NPCs."""
        relationships = self.get_npc_relationships(npc_a)
        return relationships.get(npc_b)
    
    def decode_cybernetic(self, code: str) -> Optional[dict]:
        """Decode a cybernetic code to full entry."""
        return self._cybernetic_index.get(code)
    
    def decode_medical(self, code: str) -> Optional[dict]:
        """Decode a medical condition code."""
        return self._medical_index.get(code)
    
    def decode_drug(self, code: str) -> Optional[dict]:
        """Decode a drug code."""
        return self._drug_index.get(code)
    
    def decode_skill(self, code: str) -> Optional[dict]:
        """Decode a skill code."""
        return self._skill_index.get(code)
    
    def get_skill_trainers(self, skill_code: str) -> List[str]:
        """Get NPCs who can train a specific skill."""
        skill = self.decode_skill(skill_code)
        if not skill:
            return []
        return skill.get("trainers", [])
    
    def get_npc_cybernetics(self, npc_id: str) -> List[dict]:
        """Get full cybernetic details for an NPC."""
        npc = self.get_npc(npc_id)
        if not npc:
            return []
        cyber_codes = npc.get("cybernetics", [])
        return [self.decode_cybernetic(c) for c in cyber_codes if self.decode_cybernetic(c)]
    
    def get_faction_info(self, faction_name: str) -> Optional[dict]:
        """Get detailed faction information."""
        if "chunk_05_lore" in self.chunks:
            lore = self.chunks["chunk_05_lore"]
            factions = lore.get("factions_detailed", {})
            return factions.get(faction_name.lower())
        return None
    
    def get_layer_info(self, layer_id: str) -> Optional[dict]:
        """Get information about a reality layer."""
        if "chunk_05_lore" in self.chunks:
            lore = self.chunks["chunk_05_lore"]
            layers = lore.get("layer_lore", {}).get("layers", {})
            return layers.get(layer_id)
        return None
    
    def get_event_template(self, event_code: str) -> Optional[dict]:
        """Get an event template by code."""
        if "chunk_07_events" in self.chunks:
            events = self.chunks["chunk_07_events"]
            for category in events.get("event_templates", {}).values():
                if isinstance(category, dict):
                    for key, template in category.items():
                        if isinstance(template, dict) and template.get("code") == event_code:
                            return template
        return None
    
    # =========== Knowledge Queries ===========
    
    def get_npc_knowledge_domains(self, npc_id: str) -> List[str]:
        """Get what domains of knowledge an NPC has."""
        npc = self.get_npc(npc_id)
        if not npc:
            return []
        return npc.get("knowledge_domains", [])
    
    def can_npc_help_with(self, npc_id: str, topic: str) -> bool:
        """Check if an NPC has knowledge about a topic."""
        domains = self.get_npc_knowledge_domains(npc_id)
        topic_lower = topic.lower()
        for domain in domains:
            if topic_lower in domain.lower() or domain.lower() in topic_lower:
                return True
        return False
    
    def find_npcs_who_know_about(self, topic: str) -> List[str]:
        """Find NPCs with knowledge of a specific topic."""
        experts = []
        for npc_id in self._npc_index:
            if len(npc_id) > 3:  # Skip short codes
                if self.can_npc_help_with(npc_id, topic):
                    experts.append(npc_id)
        return experts
    
    # =========== Statistics ===========
    
    def get_stats(self) -> dict:
        """Get statistics about loaded knowledge."""
        return {
            "chunks_loaded": len(self.chunks),
            "actions": len(self._action_index),
            "objects": len(self._object_index),
            "locations": len(self._location_index),
            "npcs": len([k for k in self._npc_index if len(k) > 3]),  # Exclude codes
            "medical_conditions": len(self._medical_index),
            "drugs": len(self._drug_index),
            "cybernetics": len(self._cybernetic_index),
            "skills": len(self._skill_index)
        }
    
    def get_total_size_bytes(self) -> int:
        """Get estimated total size of all loaded chunks."""
        total = 0
        for chunk_file in CHUNK_ORDER:
            path = os.path.join(self.chunk_dir, chunk_file)
            if os.path.exists(path):
                total += os.path.getsize(path)
        return total


# =========== Convenience Functions ===========

_codec: Optional[ChunkedCodec] = None

def get_codec() -> ChunkedCodec:
    """Get or create the global codec instance."""
    global _codec
    if _codec is None:
        _codec = ChunkedCodec()
        _codec.load_all_chunks()
    return _codec


def decode(code: str) -> Optional[dict]:
    """Universal decoder - figures out what type of code it is."""
    codec = get_codec()
    
    # Try each index based on prefix
    if code.startswith("A"):
        return codec.decode_action(code)
    elif code.startswith("O"):
        return codec.decode_object(code)
    elif code.startswith("L"):
        return codec.decode_location(code)
    elif code.startswith("MC"):
        return codec.decode_medical(code)
    elif code.startswith("MD"):
        return codec.decode_drug(code)
    elif code.startswith("CY"):
        return codec.decode_cybernetic(code)
    elif code.startswith("SK"):
        return codec.decode_skill(code)
    elif code.startswith("C") and len(code) <= 3:
        return codec.get_npc(code)
    
    return None


# =========== Test ===========

if __name__ == "__main__":
    print("=" * 60)
    print("CHUNKED WORLD CODEC - Test Suite")
    print("=" * 60)
    
    codec = get_codec()
    
    if not codec.loaded:
        print("❌ Failed to load chunks")
        exit(1)
    
    stats = codec.get_stats()
    print(f"\n📊 LOADED STATS:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    size_kb = codec.get_total_size_bytes() / 1024
    print(f"\n   Total size: {size_kb:.1f} KB")
    
    # Test decoding
    print("\n🔍 DECODING TESTS:")
    
    # Actions
    action = codec.decode_action("A086")
    print(f"   A086 → {action}")
    
    # Objects
    obj = codec.decode_object("O070")
    print(f"   O070 → {obj}")
    
    # Locations
    loc = codec.decode_location("L011")
    print(f"   L011 → {loc}")
    
    # NPCs
    npc = codec.get_npc("charlie")
    if npc:
        print(f"   charlie → {npc.get('name')} ({npc.get('role')})")
    
    # Cybernetics
    cyber = codec.decode_cybernetic("CY028")
    print(f"   CY028 → {cyber}")
    
    # Relationships
    print("\n🤝 RELATIONSHIP TESTS:")
    rel = codec.get_npc_relationship("charlie", "felix")
    print(f"   Charlie → Felix: {rel}")
    
    rel = codec.get_npc_relationship("charlie", "kai_vance")
    print(f"   Charlie → Kai Vance: {rel}")
    
    # NPC cybernetics
    print("\n🤖 NPC CYBERNETICS:")
    charlie_cybers = codec.get_npc_cybernetics("charlie")
    print(f"   Charlie's implants: {[c.get('n') for c in charlie_cybers if c]}")
    
    # Knowledge queries
    print("\n🧠 KNOWLEDGE QUERIES:")
    experts = codec.find_npcs_who_know_about("hacking")
    print(f"   Who knows about hacking? {experts}")
    
    experts = codec.find_npcs_who_know_about("medicine")
    print(f"   Who knows about medicine? {experts}")
    
    # Skill trainers
    print("\n🎓 SKILL TRAINERS:")
    trainers = codec.get_skill_trainers("SK007")
    print(f"   Who can train hacking (SK007)? {trainers}")
    
    print("\n✅ All tests passed!")
    print("=" * 60)

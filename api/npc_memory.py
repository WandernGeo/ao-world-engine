"""
NPC Memory Persistence System for AO World Engine

This module provides persistent memory storage for NPC conversations:
1. Saves learned facts to JSON files on disk
2. Loads memories on startup  
3. Prepares memory batches for Arweave archival

Memory Types:
- user_facts: Things learned about users (name, preferences, relationships)
- conversation_logs: Full conversation history for context
- npc_relationships: How NPCs feel about specific users

File Structure:
  data/memories/
    {user_id}/
      facts.json       # Learned facts about user
      {npc_id}.json    # Conversation history with each NPC
    arweave_queue/     # Batches ready for upload
"""

import os
import json
import time
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any

# Memory directory
MEMORY_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "memories")

# Ensure directories exist
os.makedirs(MEMORY_DIR, exist_ok=True)


class NPCMemory:
    """Persistent memory system for NPC conversations."""
    
    def __init__(self, memory_dir: str = MEMORY_DIR):
        self.memory_dir = memory_dir
        self._cache = {}  # In-memory cache for fast access
        self._dirty = set()  # Keys that need saving
        
    def _get_user_dir(self, user_id: str) -> str:
        """Get or create user's memory directory."""
        # Sanitize user_id for filesystem
        safe_id = hashlib.md5(user_id.encode()).hexdigest()[:16]
        user_dir = os.path.join(self.memory_dir, safe_id)
        os.makedirs(user_dir, exist_ok=True)
        return user_dir
    
    def _get_facts_path(self, user_id: str) -> str:
        """Get path to user's facts file."""
        return os.path.join(self._get_user_dir(user_id), "facts.json")
    
    def _get_conversation_path(self, user_id: str, npc_id: str) -> str:
        """Get path to conversation history file."""
        return os.path.join(self._get_user_dir(user_id), f"{npc_id}.json")
    
    # ====== USER FACTS ======
    
    def get_user_facts(self, user_id: str) -> Dict[str, Any]:
        """Get all known facts about a user."""
        cache_key = f"facts:{user_id}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        path = self._get_facts_path(user_id)
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    facts = json.load(f)
                    self._cache[cache_key] = facts
                    return facts
            except Exception as e:
                print(f"⚠️ Failed to load facts for {user_id}: {e}")
        
        # Default empty facts
        return {
            "name": None,
            "first_seen_tick": None,
            "last_seen_tick": None,
            "custom_facts": {},  # {"fact_key": {"value": ..., "learned_tick": ...}}
        }
    
    def remember_user_fact(self, user_id: str, key: str, value: Any, tick: int):
        """Remember a fact about a user."""
        facts = self.get_user_facts(user_id)
        
        if key == "name":
            facts["name"] = value
        else:
            facts["custom_facts"][key] = {
                "value": value,
                "learned_tick": tick,
                "updated_at": datetime.now().isoformat()
            }
        
        if facts["first_seen_tick"] is None:
            facts["first_seen_tick"] = tick
        facts["last_seen_tick"] = tick
        
        # Update cache and mark dirty
        cache_key = f"facts:{user_id}"
        self._cache[cache_key] = facts
        self._dirty.add(cache_key)
        
        # Save immediately for persistence
        self._save_facts(user_id, facts)
    
    def _save_facts(self, user_id: str, facts: Dict):
        """Save facts to disk."""
        path = self._get_facts_path(user_id)
        try:
            with open(path, 'w') as f:
                json.dump(facts, f, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save facts for {user_id}: {e}")
    
    # ====== CONVERSATION HISTORY ======
    
    def get_conversation(self, user_id: str, npc_id: str, max_messages: int = 50) -> List[Dict]:
        """Get conversation history between user and NPC."""
        cache_key = f"conv:{user_id}:{npc_id}"
        
        if cache_key in self._cache:
            return self._cache[cache_key][-max_messages:]
        
        path = self._get_conversation_path(user_id, npc_id)
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    messages = data.get("messages", [])
                    self._cache[cache_key] = messages
                    return messages[-max_messages:]
            except Exception as e:
                print(f"⚠️ Failed to load conversation {user_id}/{npc_id}: {e}")
        
        return []
    
    def add_message(self, user_id: str, npc_id: str, role: str, content: str, tick: int):
        """Add a message to conversation history."""
        cache_key = f"conv:{user_id}:{npc_id}"
        
        # Load existing or start new
        if cache_key not in self._cache:
            existing = self.get_conversation(user_id, npc_id, max_messages=500)
            self._cache[cache_key] = existing
        
        message = {
            "role": role,
            "content": content,
            "tick": tick,
            "timestamp": datetime.now().isoformat()
        }
        
        self._cache[cache_key].append(message)
        
        # Keep only last 500 messages
        if len(self._cache[cache_key]) > 500:
            self._cache[cache_key] = self._cache[cache_key][-500:]
        
        self._dirty.add(cache_key)
        
        # Save immediately
        self._save_conversation(user_id, npc_id)
        
        # Extract facts from message if user
        if role == "user":
            self._extract_facts_from_message(user_id, content, tick)
    
    def _save_conversation(self, user_id: str, npc_id: str):
        """Save conversation to disk."""
        cache_key = f"conv:{user_id}:{npc_id}"
        messages = self._cache.get(cache_key, [])
        
        path = self._get_conversation_path(user_id, npc_id)
        try:
            data = {
                "user_id": user_id,
                "npc_id": npc_id,
                "message_count": len(messages),
                "last_updated": datetime.now().isoformat(),
                "messages": messages
            }
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save conversation {user_id}/{npc_id}: {e}")
    
    def _extract_facts_from_message(self, user_id: str, content: str, tick: int):
        """Extract and remember facts from user messages."""
        content_lower = content.lower()
        
        # Extract name: "my name is X", "I'm X", "I am X", "call me X"
        name_patterns = [
            "my name is ",
            "i'm ",
            "i am ",
            "call me ",
            "they call me ",
        ]
        
        for pattern in name_patterns:
            if pattern in content_lower:
                name_part = content_lower.split(pattern)[-1].strip()
                # Get first word as name
                words = name_part.split()
                if words and len(words[0]) > 1:
                    name = words[0].title()
                    # Validate it's likely a name (not "here", "not", etc.)
                    skip_words = {"here", "not", "going", "doing", "just", "from", "the", "a", "an"}
                    if name.lower() not in skip_words:
                        self.remember_user_fact(user_id, "name", name, tick)
                        print(f"💾 Learned user name: {name}")
                        return
        
        # Extract location: "I live in X", "I'm from X"
        location_patterns = ["i live in ", "i'm from ", "i am from "]
        for pattern in location_patterns:
            if pattern in content_lower:
                loc_part = content_lower.split(pattern)[-1].strip()
                location = loc_part.split(",")[0].split(".")[0].strip().title()
                if location and len(location) > 1:
                    self.remember_user_fact(user_id, "location", location, tick)
                    print(f"💾 Learned user location: {location}")
                    return
        
        # Extract preferences: "my favorite X is Y"
        if "my favorite " in content_lower or "my favourite " in content_lower:
            for pattern in ["my favorite ", "my favourite "]:
                if pattern in content_lower:
                    pref_part = content_lower.split(pattern)[-1]
                    if " is " in pref_part:
                        parts = pref_part.split(" is ", 1)
                        category = parts[0].strip()
                        value = parts[1].split(".")[0].strip() if len(parts) > 1 else None
                        if category and value:
                            self.remember_user_fact(user_id, f"favorite_{category}", value, tick)
                            print(f"💾 Learned favorite {category}: {value}")
                            return
    
    # ====== ARWEAVE EXPORT ======
    
    def prepare_arweave_batch(self, user_id: str) -> Dict:
        """Prepare a batch of memories for Arweave upload."""
        facts = self.get_user_facts(user_id)
        
        # Get all conversation files for this user
        user_dir = self._get_user_dir(user_id)
        conversations = {}
        
        for filename in os.listdir(user_dir):
            if filename.endswith(".json") and filename != "facts.json":
                npc_id = filename[:-5]  # Remove .json
                conversations[npc_id] = self.get_conversation(user_id, npc_id)
        
        return {
            "schema": "ao-world-engine/memory/v1",
            "user_id": user_id,
            "exported_at": datetime.now().isoformat(),
            "facts": facts,
            "conversations": conversations,
            "total_messages": sum(len(c) for c in conversations.values())
        }
    
    def get_arweave_queue_path(self) -> str:
        """Get path to Arweave upload queue."""
        queue_dir = os.path.join(self.memory_dir, "arweave_queue")
        os.makedirs(queue_dir, exist_ok=True)
        return queue_dir


# Global instance
_memory = None

def get_memory() -> NPCMemory:
    """Get the global memory instance."""
    global _memory
    if _memory is None:
        _memory = NPCMemory()
    return _memory


# Convenience functions for backward compatibility
def remember_user(user_id: str, name: str, tick: int):
    """Remember a user's name."""
    get_memory().remember_user_fact(user_id, "name", name, tick)

def get_user_info(user_id: str) -> Dict:
    """Get what we know about a user."""
    facts = get_memory().get_user_facts(user_id)
    return {
        "name": facts.get("name"),
        "first_seen_tick": facts.get("first_seen_tick"),
        "last_seen_tick": facts.get("last_seen_tick"),
        "custom_facts": facts.get("custom_facts", {})
    }

def get_conversation_history(user_id: str, npc_id: str, max_messages: int = 20) -> List[Dict]:
    """Get conversation history."""
    return get_memory().get_conversation(user_id, npc_id, max_messages)

def add_to_conversation(user_id: str, npc_id: str, role: str, content: str, tick: int):
    """Add message to conversation."""
    get_memory().add_message(user_id, npc_id, role, content, tick)

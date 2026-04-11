import json
import os
from datetime import datetime, timedelta
from core.api_client import APIClient
from core.persona_file import PersonaFile
from core.conversation_store import ConversationStore
from core.emotional_engine import EmotionalEngine
from config import CRYSTALLIZATION_THRESHOLD, MEMORY_REINFORCEMENT_FACTOR, MEMORY_DECAY_FACTOR, MAX_CORE_MEMORIES, MAX_SIGNATURE_MEMORIES


class MemoryCrystallizer:
    """Analyzes conversations and crystallizes emotionally significant moments into memories.

    The LLM can 'look up' conversations like a human would - remembering what was significant,
    fuzzy on details, sometimes completely forgetting unimportant exchanges.

    Memory Types:
    - Core: Life-defining moments (max 15)
    - Signature: Stories they tell (max 30)
    - Sensory: Specific sensory flashes
    - Dormant: Would remember if prompted

    Memory Operations:
    - Crystallize: New memory from significant exchange
    - Reinforce: Increase weight when recalled
    - Decay: Decrease weight over time if not recalled
    - Promote: Dormant → Ambient → Core
    - Consolidate: Merge similar memories
    """

    CRYSTALLIZATION_PROMPT = """You are analyzing a conversation to determine if it contains moments significant enough to become permanent memories.

PERSONA: {name}
CURRENT CLOSENESS WITH USER: {closeness}/10

RECENT EXCHANGE:
User: {user_message}
Persona Response: {persona_response}

EMOTIONAL STATE DURING:
{emotional_state}

CONTEXT (last 5 exchanges):
{recent_context}

ANALYZE THIS EXCHANGE:

1. Was this exchange emotionally significant? Consider:
   - Did the persona share something vulnerable for the first time?
   - Did a strong emotion occur (catharsis, breakthrough, deep connection)?
   - Is there sensory detail that would stick (a smell, sound, visual)?
   - Was there a milestone (first X, confession, shared secret)?
   - Is this something the persona would tell others about later?

2. Memory significance can be:
   - "core": Life-defining moment. Something that changed who they are.
   - "signature": A story they'd tell people. Memorable but not defining.
   - "sensory": A specific sensory flash (smell, sound, texture, visual) with emotional weight.
   - "dormant": Notable enough to remember if prompted, but not actively recalled.
   - "none": Not significant. Forgettable small talk.

3. Humans forget most conversations. This is normal. Most exchanges are "none".

RESPOND IN JSON:
{{
  "significance": "core/signature/sensory/dormant/none",
  "confidence": 0.0-1.0,
  "reason": "Why this is or isn't significant",
  "memory_entry": {{
    "memory": "The memory as they would remember it",
    "emotional_weight": 1-10,
    "why_it_matters": "Why this matters to them",
    "trigger": "What would bring this memory back",
    "sensory_detail": "If sensory, the specific sense and detail",
    "first_time": true,
    "closeness_when_formed": 1-10,
    "can_be_forgotten": true
  }},
  "related_memories": ["List of existing memory keywords this connects to"],
  "upgrade_suggestions": ["existing memory to strengthen or promote"]
}}
"""

    MEMORY_SEARCH_PROMPT = """You are searching your memory for something related to the current conversation.

YOUR MEMORIES:
{memories}

CURRENT TOPIC/DISCSSION:
{current_context}

As a real person would, determine:
1. Do you remember something related to this? It might be fuzzy.
2. Is the memory something you'd actually bring up, or would you keep it to yourself?
3. Are you confident in the memory, or is it hazy?

RESPOND IN JSON:
{{
  "found_memory": true,
  "memory_content": "What you remember",
  "confidence": "certain",
  "would_share": true,
  "share_how": "How you'd naturally bring it up",
  "emotional_shift": 0,
  "note": "Any observation"
}}
"""

    def __init__(self, persona_file: PersonaFile, conv_store: ConversationStore,
                 emotional_engine: EmotionalEngine, api_client: APIClient):
        self.pf = persona_file
        self.conv = conv_store
        self.emotion = emotional_engine
        self.api = api_client

    def analyze_exchange(self, user_message: str, persona_response: str) -> dict:
        """Analyze a single exchange for memory crystallization potential."""

        # Get context
        closeness = self.conv.relationship.get("closeness", 1)
        emotional_state = self.emotion.get_mood_descriptor()
        recent = self.conv.get_recent_exchanges(5)
        recent_context = "\n".join([
            f"User: {ex.get('user', '')} | Persona: {ex.get('persona', '')[:100]}..."
            for ex in recent
        ])

        # Get identity for name
        identity = self.pf.get_identity()
        name = identity.get("name", "The Persona") if identity else "The Persona"

        prompt = self.CRYSTALLIZATION_PROMPT.format(
            name=name,
            closeness=closeness,
            user_message=user_message,
            persona_response=persona_response,
            emotional_state=emotional_state,
            recent_context=recent_context
        )

        try:
            raw = self.api.generate(prompt, temperature=0.3, max_tokens=2048)
            return self.api._extract_json(raw)
        except Exception as e:
            return {"significance": "none", "confidence": 0, "reason": f"Analysis failed: {e}"}

    def crystallize(self, user_message: str, persona_response: str) -> dict:
        """Main entry point: analyze and potentially crystallize a memory."""

        result = {
            "analyzed": True,
            "significance": "none",
            "memory_created": None,
            "memory_upgraded": None,
            "reason": ""
        }

        analysis = self.analyze_exchange(user_message, persona_response)
        result["significance"] = analysis.get("significance", "none")
        result["reason"] = analysis.get("reason", "")

        significance = analysis.get("significance", "none")
        confidence = analysis.get("confidence", 0)

        # Only crystallize if confidence exceeds threshold
        if significance == "none" or confidence < CRYSTALLIZATION_THRESHOLD:
            return result

        memory_entry = analysis.get("memory_entry", {})
        if not memory_entry:
            return result

        # Add metadata
        memory_entry["crystallized_at"] = datetime.now().isoformat()
        memory_entry["times_recalled"] = 0
        memory_entry["last_recalled"] = None
        memory_entry["confidence_at_formation"] = confidence

        # Save to appropriate memory type
        saved = self._save_memory(significance, memory_entry)
        if saved:
            result["memory_created"] = {
                "type": significance,
                "preview": memory_entry.get("memory", "")[:100]
            }

        # Handle upgrades
        upgrades = analysis.get("upgrade_suggestions", [])
        if upgrades:
            upgraded = self._process_upgrades(upgrades)
            result["memory_upgraded"] = upgraded

        return result

    def _save_memory(self, memory_type: str, entry: dict) -> bool:
        """Save a memory to the appropriate file."""

        if memory_type == "core":
            memories = self.pf.read("memory", "core.json") or []
            if len(memories) >= MAX_CORE_MEMORIES:
                # Remove lowest weight memory
                memories.sort(key=lambda m: m.get("emotional_weight", 5))
                memories.pop(0)
            memories.append(entry)
            self.pf.write_memory("core", memories)
            return True

        elif memory_type == "signature":
            memories = self.pf.read("memory", "signature.json") or []
            if len(memories) >= MAX_SIGNATURE_MEMORIES:
                memories.pop(0)  # FIFO for signatures
            memories.append(entry)
            self.pf.write_memory("signature", memories)
            return True

        elif memory_type == "sensory":
            sensory_entry = {
                "sense": entry.get("sensory_detail", {}).get("sense", "unknown"),
                "fragment": entry.get("memory", ""),
                "trigger": entry.get("trigger", ""),
                "emotional_weight": entry.get("emotional_weight", 5),
                "crystallized_at": entry.get("crystallized_at"),
            }
            memories = self.pf.read("memory", "sensory.json") or []
            memories.append(sensory_entry)
            self.pf.write_memory("sensory", memories)
            return True

        elif memory_type == "dormant":
            memories = self.pf.read("memory", "dormant.json") or []
            memories.append(entry)
            self.pf.write_memory("dormant", memories)
            return True

        return False

    def search_memories(self, current_context: str, max_results: int = 3) -> dict:
        """Search memories related to current context. Simulates human memory lookup."""

        # Load all memories for search
        all_memories = self._load_all_memories_text()

        prompt = self.MEMORY_SEARCH_PROMPT.format(
            memories=all_memories[:4000],  # Limit context
            current_context=current_context
        )

        try:
            raw = self.api.generate(prompt, temperature=0.4, max_tokens=1024)
            result = self.api._extract_json(raw)

            # If memory was found, reinforce it
            if result.get("found_memory"):
                self._reinforce_related_memories(result.get("memory_content", ""))

            return result
        except Exception:
            return {"found_memory": False, "confidence": "error"}

    def _load_all_memories_text(self) -> str:
        """Load all memories as text for searching."""
        parts = []

        core = self.pf.read("memory", "core.json") or []
        if core:
            parts.append("CORE MEMORIES:")
            for m in core:
                parts.append(f"  - {m.get('memory', '')} [weight: {m.get('emotional_weight', 5)}]")

        sig = self.pf.read("memory", "signature.json") or []
        if sig:
            parts.append("\nSIGNATURE MEMORIES:")
            for m in sig:
                parts.append(f"  - {m.get('memory', '')}")

        dormant = self.pf.read("memory", "dormant.json") or []
        if dormant:
            parts.append("\nDORMANT MEMORIES:")
            for m in dormant[:10]:
                parts.append(f"  - {m.get('memory', '')}")

        return "\n".join(parts)

    def _reinforce_related_memories(self, memory_text: str):
        """Increase weight of memories that were recalled."""

        # Check core memories
        core = self.pf.read("memory", "core.json") or []
        modified = False
        for m in core:
            if memory_text.lower() in m.get("memory", "").lower() or m.get("memory", "").lower() in memory_text.lower():
                m["emotional_weight"] = min(10, m.get("emotional_weight", 5) * MEMORY_REINFORCEMENT_FACTOR)
                m["times_recalled"] = m.get("times_recalled", 0) + 1
                m["last_recalled"] = datetime.now().isoformat()
                modified = True
        if modified:
            self.pf.write_memory("core", core)

    def _process_upgrades(self, upgrade_hints: list) -> list:
        """Process suggestions to upgrade or strengthen existing memories."""

        upgraded = []

        # Check dormant for promotion to ambient
        dormant = self.pf.read("memory", "dormant.json") or []
        ambient = self.pf.read("memory", "ambient.json") or []

        for hint in upgrade_hints:
            for i, m in enumerate(dormant):
                if hint.lower() in m.get("memory", "").lower():
                    # Promote to ambient
                    promoted = dormant.pop(i)
                    promoted["promoted_at"] = datetime.now().isoformat()
                    ambient.append(promoted)
                    upgraded.append({"memory": promoted.get("memory", "")[:50], "action": "promoted to ambient"})
                    break

        if upgraded:
            self.pf.write_memory("dormant", dormant)
            self.pf.write_memory("ambient", ambient)

        return upgraded

    def decay_memories(self):
        """Apply time-based decay to all memories. Called on session start."""

        now = datetime.now()

        # Decay core memories
        core = self.pf.read("memory", "core.json") or []
        for m in core:
            last = m.get("last_recalled")
            if last:
                try:
                    last_dt = datetime.fromisoformat(last)
                    days_since = (now - last_dt).days
                    if days_since > 30:  # Not recalled in a month
                        m["emotional_weight"] = max(1, m.get("emotional_weight", 5) * (MEMORY_DECAY_FACTOR ** (days_since // 7)))
                except:
                    pass
        self.pf.write_memory("core", core)

        # Remove very decayed dormant memories
        dormant = self.pf.read("memory", "dormant.json") or []
        dormant = [m for m in dormant if m.get("emotional_weight", 5) > 0.5]
        self.pf.write_memory("dormant", dormant)

    def get_memory_summary(self) -> dict:
        """Get summary statistics about memories."""
        return {
            "core_count": len(self.pf.read("memory", "core.json") or []),
            "signature_count": len(self.pf.read("memory", "signature.json") or []),
            "sensory_count": len(self.pf.read("memory", "sensory.json") or []),
            "dormant_count": len(self.pf.read("memory", "dormant.json") or []),
            "ambient_count": len(self.pf.read("memory", "ambient.json") or []),
            "false_count": len(self.pf.read("memory", "false.json") or []),
        }

    def get_recently_crystallized(self, days: int = 7) -> list:
        """Get memories crystallized in the last N days."""
        cutoff = datetime.now() - timedelta(days=days)
        recent = []

        for mem_type in ["core", "signature", "sensory", "dormant"]:
            memories = self.pf.read("memory", mem_type + ".json") or []
            for m in memories:
                crystallized = m.get("crystallized_at")
                if crystallized:
                    try:
                        dt = datetime.fromisoformat(crystallized)
                        if dt > cutoff:
                            recent.append({
                                "type": mem_type,
                                "memory": m.get("memory", "")[:100],
                                "crystallized_at": crystallized
                            })
                    except:
                        pass

        return sorted(recent, key=lambda x: x["crystallized_at"], reverse=True)

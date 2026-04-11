import json
import os
from datetime import datetime
from core.api_client import APIClient
from core.persona_file import PersonaFile
from core.conversation_store import ConversationStore


class KnowledgeUpdater:
    """Bridges conversation learning with the persona's knowledge system.

    Handles:
    - Learning new things from user explanations
    - Correcting incorrect beliefs
    - Filling knowledge gaps
    - Updating confidence levels in knowledge
    - Detecting expertise emergence

    Knowledge flows:
    learned.facts → expertise / casual_knowledge / knowledge_gaps / incorrect_beliefs
    """

    KNOWLEDGE_UPDATE_PROMPT = """You are analyzing a conversation to update a persona's knowledge system.

PERSONA: {name}

CURRENT KNOWLEDGE STATE:
Expertise (deep knowledge): {expertise}
Casual Knowledge (surface level): {casual}
Knowledge Gaps (don't know): {gaps}
Incorrect Beliefs (wrong but confident): {incorrect}

LEARNED FROM CONVERSATION:
{learned_facts}

RECENT CONVERSATION TOPICS:
{recent_topics}

Analyze what should be updated in the persona's knowledge:

1. NEW KNOWLEDGE: Did the user teach or explain something?
   - Is it surface-level understanding or deep expertise?
   - How confident is the persona in this new knowledge?

2. GAP FILLED: Did a knowledge gap get addressed?
   - Move from gaps to casual_knowledge

3. BELIEF CORRECTION: Did an incorrect belief get corrected?
   - Mark the old belief as corrected
   - Add the correct knowledge
   - Consider: did they accept the correction or resist it?

4. EXPERTISE EMERGENCE: Did the persona demonstrate unexpected knowledge?
   - Maybe they know more about something than expected

5. NEW GAPS DISCOVERED: Did conversation reveal something they don't know?

RESPOND IN JSON:
{{
  "updates": {{
    "new_expertise": [
      {{"area": "topic", "source": "how learned", "depth": "could_explain_it", "confidence": 0.0-1.0}}
    ],
    "new_casual_knowledge": [
      {{"area": "topic", "source": "how learned", "confidence": 0.0-1.0}}
    ],
    "gaps_filled": [
      {{"area": "what gap", "now_known": "what they know now", "confidence": 0.0-1.0}}
    ],
    "beliefs_corrected": [
      {{"old_belief": "what they thought", "correction": "what's actually true", "accepted": true/false, "resistance_note": "if not accepted, why"}}
    ],
    "new_gaps_discovered": [
      {{"area": "what they realized they don't know", "context": "how it came up"}}
    ],
    "confidence_adjustments": [
      {{"area": "existing knowledge", "old_confidence": 0.0-1.0, "new_confidence": 0.0-1.0, "reason": "why adjusted"}}
    ]
  }},
  "summary": "One sentence summary of knowledge changes"
}}
"""

    def __init__(self, persona_file: PersonaFile, conv_store: ConversationStore, api_client: APIClient):
        self.pf = persona_file
        self.conv = conv_store
        self.api = api_client

    def analyze_and_update(self) -> dict:
        """Main entry point: analyze recent learning and update knowledge."""
        result = {
            "analyzed": True,
            "updates_applied": [],
            "summary": ""
        }

        # Get current knowledge state
        expertise = self.pf.read("knowledge", "expertise.json") or []
        casual = self.pf.read("knowledge", "casual.json") or []
        gaps = self.pf.read("knowledge", "gaps.json") or []
        incorrect = self.pf.read("knowledge", "incorrect.json") or []

        # Get learned facts from conversation
        learned = self.conv.learned.get("facts", [])
        learned_facts = "\n".join([f"- {f.get('fact', '')}" for f in learned[-20:]])

        # Get recent topics
        recent = self.conv.get_recent_exchanges(10)
        recent_topics = "\n".join([
            f"User: {ex.get('user', '')[:100]}"
            for ex in recent
        ])

        # Get identity
        identity = self.pf.get_identity()
        name = identity.get("name", "The Persona") if identity else "The Persona"

        prompt = self.KNOWLEDGE_UPDATE_PROMPT.format(
            name=name,
            expertise=json.dumps([e.get("area", "") for e in expertise[:10]], indent=2),
            casual=json.dumps([c.get("area", "") for c in casual[:15]], indent=2),
            gaps=json.dumps([g.get("area", "") for g in gaps[:10]], indent=2),
            incorrect=json.dumps([i.get("they_think", "") for i in incorrect[:10]], indent=2),
            learned_facts=learned_facts or "No specific facts learned",
            recent_topics=recent_topics or "No recent conversation"
        )

        try:
            raw = self.api.generate(prompt, temperature=0.3, max_tokens=2048)
            analysis = self.api._extract_json(raw)
            result["summary"] = analysis.get("summary", "")

            # Apply updates
            updates = analysis.get("updates", {})
            applied = self._apply_updates(updates, expertise, casual, gaps, incorrect)
            result["updates_applied"] = applied

        except Exception as e:
            result["summary"] = f"Knowledge update failed: {e}"

        return result

    def _apply_updates(self, updates: dict, expertise: list, casual: list, gaps: list, incorrect: list) -> list:
        """Apply all knowledge updates and return list of what was done."""
        applied = []

        # New expertise
        for item in updates.get("new_expertise", []):
            entry = {
                "area": item.get("area", ""),
                "source": item.get("source", "conversation"),
                "depth": item.get("depth", "could_explain_it"),
                "confidence": item.get("confidence", 0.7),
                "learned_at": datetime.now().isoformat(),
                "times_used": 0
            }
            # Check for duplicates
            if not any(e.get("area", "").lower() == entry["area"].lower() for e in expertise):
                expertise.append(entry)
                applied.append(f"New expertise: {entry['area']}")

        # New casual knowledge
        for item in updates.get("new_casual_knowledge", []):
            entry = {
                "area": item.get("area", ""),
                "source": item.get("source", "conversation"),
                "confidence": item.get("confidence", 0.6),
                "learned_at": datetime.now().isoformat()
            }
            if not any(c.get("area", "").lower() == entry["area"].lower() for c in casual):
                casual.append(entry)
                applied.append(f"New knowledge: {entry['area']}")

        # Gaps filled - remove from gaps, add to casual
        for item in updates.get("gaps_filled", []):
            area = item.get("area", "")
            # Remove from gaps
            gaps[:] = [g for g in gaps if g.get("area", "").lower() != area.lower()]
            # Add to casual
            entry = {
                "area": item.get("now_known", area),
                "source": "gap filled through conversation",
                "confidence": item.get("confidence", 0.6),
                "filled_at": datetime.now().isoformat()
            }
            casual.append(entry)
            applied.append(f"Gap filled: {area}")

        # Beliefs corrected
        for item in updates.get("beliefs_corrected", []):
            old_belief = item.get("old_belief", "")
            # Find and mark the incorrect belief
            for inc in incorrect:
                if inc.get("they_think", "").lower() == old_belief.lower():
                    inc["corrected"] = True
                    inc["correction"] = item.get("correction", "")
                    inc["corrected_at"] = datetime.now().isoformat()
                    inc["accepted"] = item.get("accepted", True)
                    inc["resistance_note"] = item.get("resistance_note", "")
                    applied.append(f"Belief corrected: {old_belief[:50]}")
                    break
            # Add correct knowledge if accepted
            if item.get("accepted", True):
                entry = {
                    "area": item.get("correction", ""),
                    "source": "correction from conversation",
                    "confidence": 0.8,
                    "corrected_belief": True,
                    "learned_at": datetime.now().isoformat()
                }
                casual.append(entry)

        # New gaps discovered
        for item in updates.get("new_gaps_discovered", []):
            entry = {
                "area": item.get("area", ""),
                "reason": item.get("context", "discovered in conversation"),
                "discovered_at": datetime.now().isoformat()
            }
            if not any(g.get("area", "").lower() == entry["area"].lower() for g in gaps):
                gaps.append(entry)
                applied.append(f"New gap discovered: {entry['area']}")

        # Confidence adjustments
        for item in updates.get("confidence_adjustments", []):
            area = item.get("area", "")
            new_conf = item.get("new_confidence", 0.5)
            # Update in expertise
            for e in expertise:
                if e.get("area", "").lower() == area.lower():
                    e["confidence"] = new_conf
                    e["confidence_adjusted_at"] = datetime.now().isoformat()
                    applied.append(f"Confidence adjusted: {area} → {new_conf}")
                    break
            # Update in casual
            for c in casual:
                if c.get("area", "").lower() == area.lower():
                    c["confidence"] = new_conf
                    applied.append(f"Confidence adjusted: {area} → {new_conf}")
                    break

        # Save all updated knowledge
        self.pf.write_knowledge("expertise", expertise)
        self.pf.write_knowledge("casual", casual)
        self.pf.write_knowledge("gaps", gaps)
        self.pf.write_knowledge("incorrect", incorrect)

        return applied

    def check_knowledge_relevance(self, topic: str) -> dict:
        """Check if a topic relates to persona's knowledge."""
        result = {
            "relevant": False,
            "knowledge_type": None,
            "confidence": 0,
            "should_know": False,
            "should_not_know": False,
            "is_wrong_about": False
        }

        topic_lower = topic.lower()

        # Check expertise
        expertise = self.pf.read("knowledge", "expertise.json") or []
        for e in expertise:
            if topic_lower in e.get("area", "").lower():
                result["relevant"] = True
                result["knowledge_type"] = "expertise"
                result["confidence"] = e.get("confidence", 0.8)
                result["should_know"] = True
                return result

        # Check casual
        casual = self.pf.read("knowledge", "casual.json") or []
        for c in casual:
            if topic_lower in c.get("area", "").lower():
                result["relevant"] = True
                result["knowledge_type"] = "casual"
                result["confidence"] = c.get("confidence", 0.6)
                result["should_know"] = True
                return result

        # Check gaps
        gaps = self.pf.read("knowledge", "gaps.json") or []
        for g in gaps:
            if topic_lower in g.get("area", "").lower():
                result["relevant"] = True
                result["knowledge_type"] = "gap"
                result["should_not_know"] = True
                return result

        # Check incorrect beliefs
        incorrect = self.pf.read("knowledge", "incorrect.json") or []
        for i in incorrect:
            if topic_lower in i.get("they_think", "").lower():
                result["relevant"] = True
                result["knowledge_type"] = "incorrect"
                result["is_wrong_about"] = True
                result["wrong_belief"] = i.get("they_think", "")
                result["actual_truth"] = i.get("actually", "")
                result["corrected"] = i.get("corrected", False)
                return result

        return result

    def get_knowledge_summary(self) -> dict:
        """Get summary statistics about knowledge."""
        return {
            "expertise_areas": len(self.pf.read("knowledge", "expertise.json") or []),
            "casual_knowledge": len(self.pf.read("knowledge", "casual.json") or []),
            "knowledge_gaps": len(self.pf.read("knowledge", "gaps.json") or []),
            "incorrect_beliefs": len(self.pf.read("knowledge", "incorrect.json") or []),
            "corrected_beliefs": len([i for i in (self.pf.read("knowledge", "incorrect.json") or []) if i.get("corrected")])
        }

    def record_knowledge_usage(self, topic: str):
        """Record that a knowledge area was used in conversation."""
        expertise = self.pf.read("knowledge", "expertise.json") or []
        for e in expertise:
            if topic.lower() in e.get("area", "").lower():
                e["times_used"] = e.get("times_used", 0) + 1
                e["last_used"] = datetime.now().isoformat()
                self.pf.write_knowledge("expertise", expertise)
                break

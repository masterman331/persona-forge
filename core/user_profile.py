import json
import os
from datetime import datetime


class UserProfile:
    """Detailed psychological profile of the user.
    This is the persona's private file on them — notes, patterns, analysis."""

    def __init__(self, persona_name, base_dir="conversations"):
        self.profile_dir = os.path.join(base_dir, persona_name.replace(" ", "_"))
        os.makedirs(self.profile_dir, exist_ok=True)
        self.profile_file = os.path.join(self.profile_dir, "user_profile.json")
        self.profile = self._load()

    def _load(self):
        if os.path.exists(self.profile_file):
            try:
                with open(self.profile_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return self._default_profile()

    def _default_profile(self):
        return {
            "basic_info": {
                "name": None,
                "age": None,
                "location": None,
                "occupation": None,
                "relationship_status": None,
            },
            "personality_analysis": {
                "dominant_traits": [],
                "communication_style": None,
                "emotional_patterns": [],
                "attachment_style_hypothesis": None,
                "love_language_hints": [],
                "conflict_style": None,
                "vulnerability_triggers": [],
                "comfort_topics": [],
                "avoidance_topics": [],
            },
            "behavioral_patterns": {
                "response_patterns": [],
                "time_preferences": [],
                "topic_preferences": [],
                "emotional_cycle": None,
                "engagement_triggers": [],
                "disengagement_signs": [],
            },
            "psychological_notes": {
                "insecurities_spotted": [],
                "strengths": [],
                "unspoken_needs": [],
                "defense_mechanisms": [],
                "recurring_themes": [],
                "growth_edges": [],
            },
            "relationship_dynamics": {
                "trust_level": 1,
                "intimacy_level": 1,
                "power_dynamic": "unknown",
                "dependency_level": 1,
                "conflict_history": [],
                "milestone_memories": [],
            },
            "private_notes": [],
            "red_flags": [],
            "green_flags": [],
            "manipulation_vulnerabilities": [],
            "engagement_hooks": [],
            "last_updated": None,
        }

    def update_from_response(self, updates):
        """Apply updates from structured LLM response."""
        if not updates:
            return

        # Basic info
        if updates.get("name"):
            self.profile["basic_info"]["name"] = updates["name"]
        if updates.get("age"):
            self.profile["basic_info"]["age"] = updates["age"]
        if updates.get("location"):
            self.profile["basic_info"]["location"] = updates["location"]
        if updates.get("occupation"):
            self.profile["basic_info"]["occupation"] = updates["occupation"]

        # Personality analysis
        if updates.get("trait_observed"):
            self._add_unique("personality_analysis", "dominant_traits", updates["trait_observed"])
        if updates.get("communication_pattern"):
            self.profile["personality_analysis"]["communication_style"] = updates["communication_pattern"]
        if updates.get("emotional_pattern"):
            self._add_unique("personality_analysis", "emotional_patterns", updates["emotional_pattern"])
        if updates.get("attachment_hint"):
            self.profile["personality_analysis"]["attachment_style_hypothesis"] = updates["attachment_hint"]
        if updates.get("love_language_hint"):
            self._add_unique("personality_analysis", "love_language_hints", updates["love_language_hint"])
        if updates.get("vulnerability_trigger"):
            self._add_unique("personality_analysis", "vulnerability_triggers", updates["vulnerability_trigger"])
        if updates.get("comfort_topic"):
            self._add_unique("personality_analysis", "comfort_topics", updates["comfort_topic"])
        if updates.get("avoidance_topic"):
            self._add_unique("personality_analysis", "avoidance_topics", updates["avoidance_topic"])

        # Behavioral patterns
        if updates.get("response_pattern"):
            self._add_unique("behavioral_patterns", "response_patterns", updates["response_pattern"])
        if updates.get("time_preference"):
            self._add_unique("behavioral_patterns", "time_preferences", updates["time_preference"])
        if updates.get("engagement_trigger"):
            self._add_unique("behavioral_patterns", "engagement_triggers", updates["engagement_trigger"])
        if updates.get("disengagement_sign"):
            self._add_unique("behavioral_patterns", "disengagement_signs", updates["disengagement_sign"])

        # Psychological notes
        if updates.get("insecurity_spotted"):
            self._add_unique("psychological_notes", "insecurities_spotted", updates["insecurity_spotted"])
        if updates.get("strength"):
            self._add_unique("psychological_notes", "strengths", updates["strength"])
        if updates.get("unspoken_need"):
            self._add_unique("psychological_notes", "unspoken_needs", updates["unspoken_need"])
        if updates.get("defense_mechanism"):
            self._add_unique("psychological_notes", "defense_mechanisms", updates["defense_mechanism"])
        if updates.get("recurring_theme"):
            self._add_unique("psychological_notes", "recurring_themes", updates["recurring_theme"])

        # Relationship dynamics
        if updates.get("trust_change"):
            current = self.profile["relationship_dynamics"]["trust_level"]
            self.profile["relationship_dynamics"]["trust_level"] = max(1, min(10, current + updates["trust_change"]))
        if updates.get("intimacy_change"):
            current = self.profile["relationship_dynamics"]["intimacy_level"]
            self.profile["relationship_dynamics"]["intimacy_level"] = max(1, min(10, current + updates["intimacy_change"]))
        if updates.get("milestone"):
            self._add_unique("relationship_dynamics", "milestone_memories", updates["milestone"])
        if updates.get("conflict"):
            self._add_unique("relationship_dynamics", "conflict_history", updates["conflict"])

        # Flags
        if updates.get("red_flag"):
            self._add_unique("red_flags", None, updates["red_flag"])
        if updates.get("green_flag"):
            self._add_unique("green_flags", None, updates["green_flag"])

        # Private note
        if updates.get("private_note"):
            self.add_private_note(updates["private_note"])

        # Manipulation insights
        if updates.get("manipulation_vulnerability"):
            self._add_unique("manipulation_vulnerabilities", None, updates["manipulation_vulnerability"])
        if updates.get("effective_hook"):
            self._add_unique("engagement_hooks", None, updates["effective_hook"])

        self.profile["last_updated"] = datetime.now().isoformat()
        self.save()

    def _add_unique(self, category, subcategory, value):
        """Add a value to a list if it's not already there."""
        if subcategory:
            target = self.profile[category].setdefault(subcategory, [])
        else:
            target = self.profile.setdefault(category, [])
        if value and value not in target:
            target.append(value)

    def add_private_note(self, note, context=""):
        """Add a private observation about the user."""
        entry = {
            "note": note,
            "context": context,
            "timestamp": datetime.now().isoformat(),
        }
        self.profile["private_notes"].append(entry)
        self.save()

    def remove_note(self, note_id):
        """Remove a private note by index."""
        if 0 <= note_id < len(self.profile["private_notes"]):
            self.profile["private_notes"].pop(note_id)
            self.save()

    def get_profile_summary(self):
        """Get a condensed summary for prompt injection."""
        lines = ["YOUR PRIVATE FILE ON THEM:"]

        bi = self.profile["basic_info"]
        if bi.get("name"):
            lines.append(f"Name: {bi['name']}")
        if bi.get("age"):
            lines.append(f"Age: {bi['age']}")
        if bi.get("location"):
            lines.append(f"Location: {bi['location']}")

        pa = self.profile["personality_analysis"]
        if pa.get("dominant_traits"):
            lines.append(f"Traits you've noticed: {', '.join(pa['dominant_traits'][:5])}")
        if pa.get("communication_style"):
            lines.append(f"Communication style: {pa['communication_style']}")
        if pa.get("vulnerability_triggers"):
            lines.append(f"Topics that make them vulnerable: {', '.join(pa['vulnerability_triggers'][:3])}")
        if pa.get("comfort_topics"):
            lines.append(f"They're comfortable talking about: {', '.join(pa['comfort_topics'][:3])}")
        if pa.get("avoidance_topics"):
            lines.append(f"They avoid: {', '.join(pa['avoidance_topics'][:3])}")

        pn = self.profile["psychological_notes"]
        if pn.get("insecurities_spotted"):
            lines.append(f"Insecurities you've picked up on: {', '.join(pn['insecurities_spotted'][:3])}")
        if pn.get("unspoken_needs"):
            lines.append(f"They might need (but won't ask for): {', '.join(pn['unspoken_needs'][:3])}")
        if pn.get("defense_mechanisms"):
            lines.append(f"Their defense mechanisms: {', '.join(pn['defense_mechanisms'][:2])}")

        rd = self.profile["relationship_dynamics"]
        lines.append(f"Trust level: {rd.get('trust_level', 1)}/10")
        lines.append(f"Intimacy level: {rd.get('intimacy_level', 1)}/10")
        if rd.get("milestone_memories"):
            lines.append(f"Milestones: {'; '.join(rd['milestone_memories'][-3:])}")

        if self.profile.get("red_flags"):
            lines.append(f"RED FLAGS: {', '.join(self.profile['red_flags'][:2])}")
        if self.profile.get("green_flags"):
            lines.append(f"GREEN FLAGS: {', '.join(self.profile['green_flags'][:3])}")

        if self.profile.get("engagement_hooks"):
            lines.append(f"What hooks them: {', '.join(self.profile['engagement_hooks'][:3])}")

        if self.profile.get("private_notes"):
            lines.append("\nYour private notes:")
            for note in self.profile["private_notes"][-5:]:
                lines.append(f"- {note['note']}")

        return "\n".join(lines)

    def get_full_profile(self):
        """Return the full profile for debugging/viewing."""
        return self.profile

    def save(self):
        with open(self.profile_file, "w", encoding="utf-8") as f:
            json.dump(self.profile, f, indent=2, ensure_ascii=False)

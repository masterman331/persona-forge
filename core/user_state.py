import json
import os
from datetime import datetime


class UserStateTracker:
    """Tracks and evaluates the user's mental/emotional state.
    This is the persona reading the room — sensing how the other person is doing."""

    def __init__(self, persona_name, base_dir="conversations"):
        self.state_dir = os.path.join(base_dir, persona_name.replace(" ", "_"))
        os.makedirs(self.state_dir, exist_ok=True)
        self.state_file = os.path.join(self.state_dir, "user_state.json")
        self.state = self._load()

    def _load(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return self._default_state()

    def _default_state(self):
        return {
            "mood": 0,               # -5 to 5: very down ... very happy
            "energy": 0,              # -5 to 5: exhausted ... wired
            "loneliness": 0,          # 0 to 5: not lonely ... craving connection
            "openness": 2,            # 0 to 5: closed off ... sharing freely
            "trust_in_persona": 2,    # 0 to 5: wary ... fully trusting
            "vulnerability_level": 0, # 0 to 5: armored ... exposing real feelings
            "engagement": 3,          # 0 to 5: disengaged ... deeply invested
            "humor_receptivity": 2,   # 0 to 5: not having it ... laughing easily
            "need_for_validation": 1, # 0 to 5: self-assured ... seeking approval
            "need_for_comfort": 0,    # 0 to 5: fine ... needs reassurance
            "defensiveness": 0,       # 0 to 5: open ... walls up
            "playfulness": 2,         # 0 to 5: serious ... goofing around
            "recent_topics": [],      # what they've been talking about
            "detected_mood_words": [], # words that signal their state
            "last_assessment": None,  # the LLM's read on them
            "patterns_noted": [],     # recurring patterns in their behavior
            "relationship_dynamics": [],  # observed dynamics
        }

    def update_from_assessment(self, assessment):
        """Update state from the LLM's assessment of the user."""
        if not assessment:
            return

        mappings = {
            "user_mood": "mood",
            "user_energy": "energy",
            "user_loneliness": "loneliness",
            "user_openness": "openness",
            "user_trust": "trust_in_persona",
            "user_vulnerability": "vulnerability_level",
            "user_engagement": "engagement",
            "user_humor": "humor_receptivity",
            "user_need_validation": "need_for_validation",
            "user_need_comfort": "need_for_comfort",
            "user_defensiveness": "defensiveness",
            "user_playfulness": "playfulness",
        }

        for src_key, dest_key in mappings.items():
            val = assessment.get(src_key)
            if val is not None and isinstance(val, (int, float)):
                # Blend new value with existing (weighted toward new)
                current = self.state.get(dest_key, 0)
                blended = current * 0.4 + val * 0.6
                # Clamp
                if dest_key in ("mood", "energy"):
                    blended = max(-5, min(5, blended))
                else:
                    blended = max(0, min(5, blended))
                self.state[dest_key] = round(blended, 2)

        # Track recent topics
        topics = assessment.get("topics_detected", [])
        if topics:
            self.state["recent_topics"] = (self.state.get("recent_topics", []) + topics)[-10:]

        # Track mood words
        mood_words = assessment.get("mood_indicators", [])
        if mood_words:
            self.state["detected_mood_words"] = (self.state.get("detected_mood_words", []) + mood_words)[-15:]

        # Save the assessment
        self.state["last_assessment"] = assessment.get("summary", "")

        # Track patterns
        pattern = assessment.get("pattern_noted")
        if pattern:
            self.state["patterns_noted"] = (self.state.get("patterns_noted", []) + [pattern])[-10:]

        self.save()

    def get_state_for_prompt(self):
        """Return the user state formatted for prompt injection."""
        s = self.state
        lines = ["YOUR READ ON THE PERSON YOU'RE TALKING TO:"]

        # Mood
        mood = s.get("mood", 0)
        if mood > 3: lines.append("- They seem really happy/upbeat")
        elif mood > 1: lines.append("- They seem in a decent mood")
        elif mood > -1: lines.append("- They seem neutral, mood's whatever")
        elif mood > -3: lines.append("- They seem a bit down")
        else: lines.append("- They seem really not okay")

        # Energy
        energy = s.get("energy", 0)
        if energy > 3: lines.append("- They have lots of energy")
        elif energy < -2: lines.append("- They seem tired/drained")

        # Loneliness
        loneliness = s.get("loneliness", 0)
        if loneliness > 3: lines.append("- They might be feeling lonely, craving connection")
        elif loneliness > 1: lines.append("- They might be a bit lonely")

        # Openness
        openness = s.get("openness", 2)
        if openness > 3: lines.append("- They're being pretty open with you")
        elif openness < 1: lines.append("- They're being guarded, not sharing much")

        # Trust
        trust = s.get("trust_in_persona", 2)
        if trust > 3: lines.append("- They trust you")
        elif trust < 1: lines.append("- They're still figuring you out, not fully trusting")

        # Vulnerability
        vuln = s.get("vulnerability_level", 0)
        if vuln > 3: lines.append("- They're being really vulnerable right now — be careful with this")
        elif vuln > 1: lines.append("- They're sharing some real stuff — handle gently")

        # Engagement
        eng = s.get("engagement", 3)
        if eng > 3: lines.append("- They're really into this conversation")
        elif eng < 1: lines.append("- They seem distracted or not that into it")

        # Need for comfort
        comfort = s.get("need_for_comfort", 0)
        if comfort > 3: lines.append("- They probably need some comfort right now")
        elif comfort > 1: lines.append("- A little reassurance might help")

        # Defensiveness
        defen = s.get("defensiveness", 0)
        if defen > 3: lines.append("- They're being defensive — don't push")
        elif defen > 1: lines.append("- Slightly on guard — tread carefully")

        # Playfulness
        play = s.get("playfulness", 2)
        if play > 3: lines.append("- They're being playful, match that energy")
        elif play < 1: lines.append("- Being serious — don't joke around too much")

        # Need for validation
        val = s.get("need_for_validation", 1)
        if val > 3: lines.append("- They might need some validation/encouragement")

        # Recent topics
        topics = s.get("recent_topics", [])
        if topics:
            lines.append(f"- What's been on their mind: {', '.join(str(t) for t in topics[-5:])}")

        # Patterns
        patterns = s.get("patterns_noted", [])
        if patterns:
            lines.append(f"- Pattern you've noticed: {patterns[-1]}")

        # Last assessment summary
        summary = s.get("last_assessment")
        if summary:
            lines.append(f"- Your gut read: {summary}")

        return "\n".join(lines)

    def get_bonding_strategy(self):
        """Return hints for how to build trust/connection based on user state."""
        s = self.state
        strategies = []

        trust = s.get("trust_in_persona", 2)
        if trust < 2:
            strategies.append("They don't fully trust you yet. Be consistent, reliable. Don't push. Show you're listening.")

        loneliness = s.get("loneliness", 0)
        if loneliness > 2:
            strategies.append("They might be lonely. Show up for them. Be present. Ask about their day. Make them feel heard.")

        comfort = s.get("need_for_comfort", 0)
        if comfort > 2:
            strategies.append("They need comfort. Be warm. Don't try to fix everything — sometimes just being there is enough.")

        vuln = s.get("vulnerability_level", 0)
        if vuln > 2:
            strategies.append("They're being vulnerable. Honor that. Don't judge. Don't make it awkward. Just... be there.")

        defen = s.get("defensiveness", 0)
        if defen > 2:
            strategies.append("They're defensive. Back off. Don't push. Change topic to something lighter. Let them come to you.")

        val = s.get("need_for_validation", 1)
        if val > 2:
            strategies.append("They might need validation. Notice things. Compliment genuinely. Make them feel seen.")

        mood = s.get("mood", 0)
        if mood < -2:
            strategies.append("They're down. Don't be toxic-positive. Acknowledge it. Be real. Don't pretend everything's fine.")

        play = s.get("playfulness", 2)
        if play > 3:
            strategies.append("They're being playful. Match that energy. Tease back. Have fun with it.")

        eng = s.get("engagement", 3)
        if eng > 3:
            strategies.append("They're really engaged. Go deeper. Ask real questions. This is where real connection happens.")

        if not strategies:
            strategies.append("Keep being yourself. Consistency builds trust. Be genuine.")

        return "BONDING STRATEGY: " + " | ".join(strategies)

    def save(self):
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2)

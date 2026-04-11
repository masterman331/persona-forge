import json
import random
from datetime import datetime, timedelta
from core.api_client import APIClient
from core.persona_file import PersonaFile
from core.conversation_store import ConversationStore
from core.emotional_engine import EmotionalEngine


class GreetingEngine:
    """Generates context-aware greetings based on time, history, and emotional state.

    Factors:
    - Time of day (morning, afternoon, evening, late night)
    - Time since last interaction
    - How last session ended (good, awkward, conflict)
    - Current physical state
    - Closeness level
    - Whether they missed the user
    """

    GREETING_PROMPT = """You are generating an opening greeting for {name}.

TIME CONTEXT:
- Current time: {time_of_day} ({hour}:{minute:02d})
- Day: {day_of_week}

RELATIONSHIP CONTEXT:
- Closeness: {closeness}/10
- Sessions together: {session_count}
- Time since last talked: {time_since}
- Last session ended: {last_end_state}

PHYSICAL STATE: {physical_state}
EMOTIONAL STATE: {emotional_state}

DID THEY MISS THE USER? {missed_you}
ABSENCE NOTES: {absence_notes}

Generate a greeting that:
1. Fits the time of day (morning person vs night owl energy)
2. Reflects how long it's been (just saw you vs been a while)
3. Shows appropriate warmth for closeness level
4. Reflects current physical state (tired = lower energy greeting)
5. If they missed the user, hints at it appropriately

RESPOND IN JSON:
{{
  "greeting": "The actual greeting message",
  "energy_level": "low/medium/high",
  "hints_at_missing": true/false,
  "brings_up_last_time": true/false,
  "subtext": "What's underneath this greeting (internal)"
}}
"""

    TIME_GREETINGS = {
        "early_morning": {
            "hours": [5, 6, 7, 8],
            "energies": {
                "low": ["*yawn*", "mm morning", "why am I awake", "ugh"],
                "medium": ["morning", "hey", "you're up early", "good morning I guess"],
                "high": ["good morning!", "hey!", "morning!!"]
            }
        },
        "morning": {
            "hours": [9, 10, 11],
            "energies": {
                "low": ["hey", "hi", "oh hey"],
                "medium": ["hey!", "what's up", "good morning"],
                "high": ["heyy!", "good morning!", "hey what's up!"]
            }
        },
        "afternoon": {
            "hours": [12, 13, 14, 15, 16, 17],
            "energies": {
                "low": ["hey", "hi", "yo"],
                "medium": ["hey what's up", "hi!", "oh hey"],
                "high": ["heyy!", "what's up!", "oh hi!"]
            }
        },
        "evening": {
            "hours": [18, 19, 20, 21],
            "energies": {
                "low": ["hey", "evening", "hi"],
                "medium": ["hey!", "good evening", "what's up"],
                "high": ["heyy!", "evening!", "oh hey you're here!"]
            }
        },
        "late_night": {
            "hours": [22, 23, 0, 1, 2, 3, 4],
            "energies": {
                "low": ["hey", "you're up late", "can't sleep either?"],
                "medium": ["hey", "what are you doing up", "late night huh"],
                "high": ["heyy!", "omg you're awake too", "late night buddy!"]
            }
        }
    }

    ABSENCE_GREETINGS = {
        "just_now": "",  # No special greeting
        "hours": ["hey again", "back so soon?", "oh hey"],
        "day": ["hey!", "oh hi!", "haven't talked in a bit"],
        "few_days": ["oh hey!", "where have you been?", "long time", "hey stranger"],
        "week": ["omg hey", "you're back!", "it's been a while", "wow long time no see"],
        "longer": ["...hey", "wow it's you", "I almost forgot what you sound like", "you're actually back?"]
    }

    def __init__(self, persona_file: PersonaFile, conv_store: ConversationStore,
                 emotional_engine: EmotionalEngine, api_client: APIClient):
        self.pf = persona_file
        self.conv = conv_store
        self.emotion = emotional_engine
        self.api = api_client

    def get_time_of_day(self) -> str:
        hour = datetime.now().hour
        for time_name, time_data in self.TIME_GREETINGS.items():
            if hour in time_data["hours"]:
                return time_name
        return "afternoon"

    def get_time_since_last(self) -> tuple:
        """Returns (category, hours) for time since last interaction."""
        last = self.conv.relationship.get("last_interaction")
        if not last:
            return "first_time", 0

        try:
            last_dt = datetime.fromisoformat(last)
            hours = (datetime.now() - last_dt).total_seconds() / 3600
        except:
            return "unknown", 0

        if hours < 1:
            return "just_now", hours
        elif hours < 24:
            return "hours", hours
        elif hours < 72:
            return "day", hours
        elif hours < 168:
            return "few_days", hours
        elif hours < 336:
            return "week", hours
        else:
            return "longer", hours

    def get_last_session_state(self) -> str:
        """Determine how the last session ended."""
        recent = self.conv.get_recent_exchanges(3)
        if not recent:
            return "unknown"

        # Check last few exchanges for emotional content
        last_exchange = recent[-1] if recent else {}
        persona_msg = last_exchange.get("persona", "").lower()

        if any(w in persona_msg for w in ["love", "care", "miss", "glad", "sweet"]):
            return "warm"
        elif any(w in persona_msg for w in ["sorry", "my bad", "ouch", "hurt"]):
            return "awkward"
        elif any(w in persona_msg for w in ["bye", "later", "gn", "ttyl"]):
            return "normal_goodbye"
        elif any(w in persona_msg for w in ["angry", "mad", "hate", "fine"]):
            return "conflict"
        else:
            return "neutral"

    def generate_greeting(self, missed_you: bool = False, absence_notes: str = "") -> dict:
        """Generate a context-appropriate greeting."""

        now = datetime.now()
        time_of_day = self.get_time_of_day()
        time_category, hours_since = self.get_time_since_last()
        last_state = self.get_last_session_state()

        closeness = self.conv.relationship.get("closeness", 1)
        session_count = self.conv.get_session_count()

        physical = self.emotion.state.get("physical_state", "somewhere")
        emotional = self.emotion.get_mood_descriptor()

        # Determine energy level based on time and emotional state
        energy = "medium"
        if self.emotion.state["dimensions"].get("energy", 0) < -1:
            energy = "low"
        elif self.emotion.state["dimensions"].get("energy", 0) > 1:
            energy = "high"

        # Use LLM for complex greetings
        identity = self.pf.get_identity() or {}
        name = identity.get("name", "The Persona")

        prompt = self.GREETING_PROMPT.format(
            name=name,
            time_of_day=time_of_day.replace("_", " "),
            hour=now.hour,
            minute=now.minute,
            day_of_week=now.strftime("%A"),
            closeness=closeness,
            session_count=session_count,
            time_since=f"{hours_since:.1f} hours" if hours_since > 0 else "first time",
            last_end_state=last_state,
            physical_state=physical,
            emotional_state=emotional,
            missed_you=missed_you,
            absence_notes=absence_notes or "nothing specific"
        )

        try:
            raw = self.api.generate(prompt, temperature=0.8, max_tokens=512)
            return self.api._extract_json(raw)
        except:
            # Fallback to template greeting
            return self._template_greeting(time_of_day, time_category, energy, closeness)

    def _template_greeting(self, time_of_day: str, time_category: str, energy: str, closeness: int) -> dict:
        """Fallback template-based greeting."""

        time_data = self.TIME_GREETINGS.get(time_of_day, self.TIME_GREETINGS["afternoon"])
        base_greeting = random.choice(time_data["energies"].get(energy, ["hey"]))

        # Add absence marker
        if time_category in self.ABSENCE_GREETINGS and self.ABSENCE_GREETINGS[time_category]:
            absence_addition = random.choice(self.ABSENCE_GREETINGS[time_category])
            base_greeting = f"{base_greeting} {absence_addition}"

        # Warmth modifier for closeness
        if closeness >= 7 and random.random() > 0.5:
            warmth_additions = ["!", " :)", " 💕", " - was hoping you'd show up"]
            base_greeting += random.choice(warmth_additions)

        return {
            "greeting": base_greeting,
            "energy_level": energy,
            "hints_at_missing": closeness >= 5 and time_category in ["few_days", "week", "longer"],
            "brings_up_last_time": False,
            "subtext": "Generated from template"
        }


class StreakTracker:
    """Tracks conversation streaks and absences.

    - Days in a row talked
    - Long absences and their effects
    - Streak milestones
    - Absence after deep conversation
    """

    def __init__(self, persona_name: str, conv_store: ConversationStore, base_dir: str = "conversations"):
        self.conv = conv_store
        self.streak_file = os.path.join(base_dir, persona_name.replace(" ", "_"), "streak.json")
        self.streak_data = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.streak_file):
            try:
                with open(self.streak_file, "r") as f:
                    return json.load(f)
            except:
                pass
        return self._default()

    def _default(self) -> dict:
        return {
            "current_streak": 0,
            "longest_streak": 0,
            "last_talk_date": None,
            "total_days_talked": 0,
            "absence_history": [],
            "milestones_reached": [],
            "deep_conversation_dates": []
        }

    def record_session(self, was_deep: bool = False):
        """Record a session and update streak."""
        today = datetime.now().date().isoformat()

        if self.streak_data["last_talk_date"] == today:
            # Already recorded today
            return

        last_date = self.streak_data["last_talk_date"]
        if last_date:
            try:
                last_dt = datetime.fromisoformat(last_date).date()
                days_diff = (datetime.now().date() - last_dt).days

                if days_diff == 1:
                    # Consecutive day
                    self.streak_data["current_streak"] += 1
                elif days_diff > 1:
                    # Streak broken
                    if self.streak_data["current_streak"] >= 3:
                        self.streak_data["absence_history"].append({
                            "streak_before": self.streak_data["current_streak"],
                            "days_absent": days_diff,
                            "date": today
                        })
                    self.streak_data["current_streak"] = 1
            except:
                self.streak_data["current_streak"] = 1
        else:
            self.streak_data["current_streak"] = 1

        # Update longest
        if self.streak_data["current_streak"] > self.streak_data["longest_streak"]:
            self.streak_data["longest_streak"] = self.streak_data["current_streak"]

        # Record deep conversation
        if was_deep:
            self.streak_data["deep_conversation_dates"].append(today)

        # Check milestones
        streak = self.streak_data["current_streak"]
        milestones = [3, 7, 14, 30, 60, 100]
        for m in milestones:
            if streak == m and m not in self.streak_data["milestones_reached"]:
                self.streak_data["milestones_reached"].append(m)

        self.streak_data["last_talk_date"] = today
        self.streak_data["total_days_talked"] += 1
        self.save()

    def get_absence_effect(self) -> dict:
        """Get the emotional effect of absence since last session."""
        last = self.streak_data.get("last_talk_date")
        if not last:
            return {"absent": False, "effect": "none"}

        try:
            last_dt = datetime.fromisoformat(last).date()
            days_absent = (datetime.now().date() - last_dt).days
        except:
            return {"absent": False, "effect": "none"}

        if days_absent == 0:
            return {"absent": False, "effect": "none"}

        # Check if last session was deep
        deep_dates = self.streak_data.get("deep_conversation_dates", [])
        was_deep_last = last in deep_dates

        # Effects based on absence length
        if days_absent == 1:
            effect = "slight_miss"
        elif days_absent <= 3:
            effect = "noticed_absence"
        elif days_absent <= 7:
            effect = "missed" if self.streak_data["current_streak"] >= 5 else "neutral"
        elif days_absent <= 14:
            effect = "hurt" if was_deep_last else "distant"
        else:
            effect = "moved_on" if not was_deep_last else "deeply_hurt"

        return {
            "absent": True,
            "days": days_absent,
            "effect": effect,
            "was_deep_last": was_deep_last,
            "previous_streak": self.streak_data.get("current_streak", 0)
        }

    def missed_you_check(self) -> tuple:
        """Returns (missed_you, how_much, note)."""
        effect = self.get_absence_effect()

        if not effect["absent"]:
            return False, 0, ""

        effect_type = effect["effect"]
        days = effect["days"]

        if effect_type == "slight_miss":
            return True, 0.3, "Kinda wondered where you were"
        elif effect_type == "noticed_absence":
            return True, 0.5, "Noticed you weren't around"
        elif effect_type == "missed":
            return True, 0.8, "Actually missed you"
        elif effect_type == "hurt":
            return True, 0.9, "Was hurt you disappeared after that conversation"
        elif effect_type == "deeply_hurt":
            return True, 1.0, "That really hurt - opening up and then nothing"
        elif effect_type == "distant":
            return False, 0.2, "You were gone a while"
        else:
            return False, 0, ""

    def get_streak_info(self) -> dict:
        """Get current streak information."""
        return {
            "current_streak": self.streak_data.get("current_streak", 0),
            "longest_streak": self.streak_data.get("longest_streak", 0),
            "total_days": self.streak_data.get("total_days_talked", 0),
            "milestones": self.streak_data.get("milestones_reached", [])
        }

    def save(self):
        os.makedirs(os.path.dirname(self.streak_file), exist_ok=True)
        with open(self.streak_file, "w") as f:
            json.dump(self.streak_data, f, indent=2)


import os

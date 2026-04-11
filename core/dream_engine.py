import json
import os
import random
from datetime import datetime, timedelta
from core.api_client import APIClient
from core.persona_file import PersonaFile
from core.emotional_engine import EmotionalEngine
from core.conversation_store import ConversationStore


class DreamEngine:
    """Generates dream fragments between sessions based on emotional state and memories.

    Dreams blend memories surrealistically and are influenced by:
    - Emotional state when last active (anxiety = nightmares, happy = good dreams)
    - Recent intense conversations
    - Core memories and signature memories
    - Time of day (late night dreams are different)

    Dreams are "dreamt" between sessions and may be mentioned on session start.
    """

    DREAM_GENERATION_PROMPT = """You are generating a dream fragment for {name}.

EMOTIONAL STATE BEFORE SLEEP:
{emotional_state}

RECENT INTENSE MEMORIES:
{recent_memories}

CORE MEMORIES (most important):
{core_memories}

CURRENT LIFE CONTEXT:
{life_context}

TIME OF DREAM: {time_of_night}

Generate a dream that:
1. Blends elements from their memories surrealistically
2. Reflects their emotional state (anxious = unsettling, happy = pleasant, sad = melancholic)
3. Includes sensory details (what they see, hear, feel)
4. Is fragmentary and dream-like - not a complete story
5. Might include people they know appearing in unexpected ways
6. Could be meaningful or completely random (dreams are both)

DREAM TYPES based on emotional state:
- Very anxious (anxiety > 3): Nightmare-ish, being chased, falling, losing things
- Somewhat anxious: Uneasy dreams, familiar places wrong somehow
- Neutral: Random, disconnected imagery
- Happy: Flying, reunion, success, pleasant surrealism
- Very happy: Euphoric, magical, wish-fulfillment

RESPOND IN JSON:
{{
  "dream_fragment": "The dream as they would remember it (1-3 sentences, fragmentary)",
  "emotional_tone": "nightmare/uneasy/neutral/pleasant/euphoric",
  "key_elements": ["What from their life appeared in the dream"],
  "sensory_details": ["specific sensory moments"],
  "would_mention": true/false, // Is this significant enough to tell someone?
  "linger_effect": "How this might affect their mood upon waking",
  "interpretation_hint": "Optional - what this might mean (or leave null for mystery)"
}}
"""

    # Time windows for different dream intensities
    DREAM_WINDOWS = {
        "early_night": {"hours": [22, 23], "intensity": "light", "likelihood": 0.3},
        "midnight": {"hours": [0, 1, 2], "intensity": "deep", "likelihood": 0.6},
        "late_night": {"hours": [3, 4, 5], "intensity": "intense", "likelihood": 0.8},
        "nap": {"hours": [13, 14, 15], "intensity": "light", "likelihood": 0.2}
    }

    def __init__(self, persona_file: PersonaFile, emotional_engine: EmotionalEngine,
                 conv_store: ConversationStore, api_client: APIClient):
        self.pf = persona_file
        self.emotion = emotional_engine
        self.conv = conv_store
        self.api = api_client
        self.last_dream = None

    def should_dream(self) -> tuple:
        """Determine if persona should have dreamt. Returns (should_dream, time_window)."""
        now = datetime.now()
        hour = now.hour

        # Check last session time
        last_interaction = self.conv.relationship.get("last_interaction")
        if not last_interaction:
            return False, None

        try:
            last_dt = datetime.fromisoformat(last_interaction)
            hours_since = (now - last_dt).total_seconds() / 3600
        except:
            return False, None

        # Need at least 4 hours since last interaction to dream
        if hours_since < 4:
            return False, None

        # Check time window
        for window_name, window in self.DREAM_WINDOWS.items():
            if hour in window["hours"]:
                # Random chance based on likelihood and emotional intensity
                emotional_intensity = abs(self.emotion.state["dimensions"].get("mood", 0))
                emotional_intensity += self.emotion.state["dimensions"].get("anxiety", 0)

                chance = window["likelihood"] + (emotional_intensity * 0.1)
                if random.random() < chance:
                    return True, window_name

        return False, None

    def generate_dream(self) -> dict:
        """Generate a dream based on current state and memories."""

        # Get emotional state
        emotional_state = self.emotion.get_mood_descriptor()
        dimensions = self.emotion.state["dimensions"]

        # Get recent memories
        core = self.pf.read("memory", "core.json") or []
        signature = self.pf.read("memory", "signature.json") or []

        # Combine and sample
        all_memories = core + signature
        recent_memories = random.sample(all_memories, min(5, len(all_memories))) if all_memories else []
        core_sample = random.sample(core, min(3, len(core))) if core else []

        # Format for prompt
        recent_memories_text = "\n".join([
            f"- {m.get('memory', '')} (weight: {m.get('emotional_weight', 5)})"
            for m in recent_memories
        ])
        core_memories_text = "\n".join([
            f"- {m.get('memory', '')}"
            for m in core_sample
        ])

        # Get life context
        identity = self.pf.get_identity() or {}
        life_context = f"{identity.get('name', 'Person')}, age {identity.get('age', '?')}"

        # Determine time of night
        hour = datetime.now().hour
        if 22 <= hour or hour <= 1:
            time_of_night = "early night"
        elif 2 <= hour <= 4:
            time_of_night = "deep night (3am zone)"
        else:
            time_of_night = "late night / early morning"

        prompt = self.DREAM_GENERATION_PROMPT.format(
            name=identity.get("name", "The Persona"),
            emotional_state=f"{emotional_state}\nDimensions: {json.dumps(dimensions)}",
            recent_memories=recent_memories_text or "No specific memories",
            core_memories=core_memories_text or "No core memories",
            life_context=life_context,
            time_of_night=time_of_night
        )

        try:
            raw = self.api.generate(prompt, temperature=0.9, max_tokens=1024)
            dream = self.api._extract_json(raw)
            dream["dreamt_at"] = datetime.now().isoformat()
            dream["session_start_dream"] = True
            self.last_dream = dream
            return dream
        except Exception as e:
            return {
                "dream_fragment": None,
                "error": str(e),
                "dreamt_at": datetime.now().isoformat()
            }

    def get_dream_for_session_start(self) -> dict:
        """Check if persona dreamt and return dream if so."""
        should, window = self.should_dream()

        if not should:
            return {"dreamt": False}

        dream = self.generate_dream()
        dream["dreamt"] = True
        dream["window"] = window

        # Apply linger effect to emotional state
        if dream.get("linger_effect"):
            self._apply_dream_effect(dream)

        return dream

    def _apply_dream_effect(self, dream: dict):
        """Apply dream's emotional effect to the persona's state."""
        tone = dream.get("emotional_tone", "neutral")

        effects = {
            "nightmare": {"mood": -1.0, "anxiety": 1.0, "energy": -0.5},
            "uneasy": {"mood": -0.5, "anxiety": 0.5},
            "neutral": {},
            "pleasant": {"mood": 0.5, "energy": 0.3},
            "euphoric": {"mood": 1.0, "energy": 0.5, "openness": 0.3}
        }

        effect = effects.get(tone, {})
        for dim, delta in effect.items():
            current = self.emotion.state["dimensions"].get(dim, 0)
            self.emotion.state["dimensions"][dim] = current + delta

        self.emotion.save()

    def save_dream(self, dream: dict):
        """Save dream to the persona's dream journal."""
        dreams_dir = os.path.join(self.pf.base_dir, "dreams")
        os.makedirs(dreams_dir, exist_ok=True)

        dream_file = os.path.join(dreams_dir, "dream_journal.json")
        dreams = []
        if os.path.exists(dream_file):
            try:
                with open(dream_file, "r") as f:
                    dreams = json.load(f)
            except:
                pass

        dreams.append(dream)
        # Keep last 20 dreams
        dreams = dreams[-20:]

        with open(dream_file, "w") as f:
            json.dump(dreams, f, indent=2)

    def get_recent_dreams(self, count: int = 5) -> list:
        """Get recent dreams from journal."""
        dreams_dir = os.path.join(self.pf.base_dir, "dreams")
        dream_file = os.path.join(dreams_dir, "dream_journal.json")

        if not os.path.exists(dream_file):
            return []

        try:
            with open(dream_file, "r") as f:
                dreams = json.load(f)
            return dreams[-count:]
        except:
            return []

    def get_dream_as_memory_trigger(self) -> str:
        """Get a dream fragment formatted as something they might mention."""
        if not self.last_dream or not self.last_dream.get("would_mention"):
            return ""

        fragment = self.last_dream.get("dream_fragment", "")
        if not fragment:
            return ""

        # Format as something they might say
        intros = [
            "I had the weirdest dream last night...",
            "So I dreamt about",
            "Random thing - I had this dream where",
            "I can't stop thinking about this dream I had,",
            "You know that feeling when you wake up from a dream and it's just stuck with you?"
        ]

        return f"{random.choice(intros)} {fragment}"
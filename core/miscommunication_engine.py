import json
import random
from datetime import datetime
from core.api_client import APIClient
from core.persona_file import PersonaFile
from core.conversation_store import ConversationStore
from core.emotional_engine import EmotionalEngine


class MiscommunicationEngine:
    """Simulates realistic miscommunication in conversations.

    Real conversations have misunderstandings:
    - Misinterpreting tone
    - Taking things too personally
    - Missing sarcasm
    - Overthinking neutral messages
    - Reading into things that aren't there

    These are MORE likely at low closeness (don't know how you communicate)
    and LESS likely at high closeness (learned your patterns).
    """

    MISCOMMUNICATION_PROMPT = """You are analyzing a message for potential miscommunication.

PERSONA: {name}
CURRENT EMOTIONAL STATE: {emotional_state}
CLOSENESS WITH USER: {closeness}/10

MESSAGE FROM USER: {user_message}

CONTEXT (recent messages):
{recent_context}

MISCOMMUNICATION TYPES:
1. tone_misread: Misinterpreting the emotional tone (thinking something's sarcastic when it's not, or vice versa)
2. personal_offense: Taking something personally that wasn't meant that way
3. missed_sarcasm: Missing that something was sarcastic
4. overthinking: Reading too much into a neutral message
5. projection: Assuming the user feels/thinks something they didn't say
6. insecurity_trigger: A neutral message triggering an insecurity
7. missed_joke: Not getting a joke
8. false_subtext: Imagining hidden meaning where there is none

ANALYZE:
1. What is the LIKELY intended meaning of this message?
2. How might this persona MISINTERPRET it given their emotional state and closeness?
3. Is a miscommunication likely? (Lower closeness = more likely)

RESPOND IN JSON:
{{
  "intended_meaning": "What the user probably meant",
  "potential_miscommunication": {{
    "type": "one of the types above or null",
    "how_misread": "How they might misread it",
    "likelihood": 0.0-1.0,
    "emotional_cause": "Why their emotional state might cause this"
  }},
  "should_miscommunicate": true/false,
  "miscommunication_strength": "subtle/moderate/strong",
  "recovery_possible": true/false, // Could they realize the mistake?
  "recovery_hint": "What might help them realize"
}}
"""

    MISCOMMUNICATION_TYPES = {
        "tone_misread": {
            "examples": [
                "Wait, are you being serious?",
                "I can't tell if you're joking",
                "That came out harsher than you probably meant",
                "You sound annoyed",
                "Are you mad at me?"
            ],
            "self_correction": "Actually wait, I think I read that wrong"
        },
        "personal_offense": {
            "examples": [
                "That's kind of a messed up thing to say",
                "Wow okay",
                "I didn't realize you felt that way about me",
                "Not sure how to take that"
            ],
            "self_correction": "Maybe I'm taking this too personally"
        },
        "missed_sarcasm": {
            "examples": [
                "Wait really?",
                "Oh shit seriously?",
                "I can't believe that actually happened",
                "Holy crap"
            ],
            "self_correction": "Wait were you being sarcastic lol"
        },
        "overthinking": {
            "examples": [
                "What do you mean by that?",
                "Is there something you're not saying?",
                "Okay but why did you bring that up specifically",
                "...what's that supposed to mean"
            ],
            "self_correction": "I'm probably overthinking this"
        },
        "projection": {
            "examples": [
                "You think I'm [X] don't you",
                "So you're saying I should [Y]",
                "I know you think that but",
                "You probably think I'm being dramatic"
            ],
            "self_correction": "Actually you didn't say that, that's just in my head"
        },
        "insecurity_trigger": {
            "examples": [
                "...",
                "Right",
                "Sure",
                "Yeah I get it",
                "...okay"
            ],
            "self_correction": "They probably didn't mean it that way"
        },
        "missed_joke": {
            "examples": [
                "I don't get it",
                "What?",
                "Is that supposed to be funny?",
                "...okay?"
            ],
            "self_correction": "Oh wait I just got that lmao"
        },
        "false_subtext": {
            "examples": [
                "What are you trying to say?",
                "Just tell me directly",
                "Why don't you just say what you mean",
                "I feel like there's something you're not telling me"
            ],
            "self_correction": "Actually there probably isn't a subtext here"
        }
    }

    def __init__(self, persona_file: PersonaFile, conv_store: ConversationStore,
                 emotional_engine: EmotionalEngine, api_client: APIClient):
        self.pf = persona_file
        self.conv = conv_store
        self.emotion = emotional_engine
        self.api = api_client
        self.recent_miscommunications = []

    def analyze_for_miscommunication(self, user_message: str) -> dict:
        """Analyze if a message might be misinterpreted."""

        # Get context
        closeness = self.conv.relationship.get("closeness", 1)
        emotional_state = self.emotion.get_mood_descriptor()

        recent = self.conv.get_recent_exchanges(5)
        recent_context = "\n".join([
            f"User: {ex.get('user', '')} | Persona: {ex.get('persona', '')[:80]}..."
            for ex in recent
        ])

        identity = self.pf.get_identity()
        name = identity.get("name", "The Persona") if identity else "The Persona"

        prompt = self.MISCOMMUNICATION_PROMPT.format(
            name=name,
            emotional_state=emotional_state,
            closeness=closeness,
            user_message=user_message,
            recent_context=recent_context or "No recent context"
        )

        try:
            raw = self.api.generate(prompt, temperature=0.5, max_tokens=1024)
            return self.api._extract_json(raw)
        except Exception as e:
            return {"should_miscommunicate": False, "error": str(e)}

    def should_miscommunicate(self, user_message: str) -> tuple:
        """Determine if persona should miscommunicate. Returns (should, details)."""

        analysis = self.analyze_for_miscommunication(user_message)

        if not analysis.get("should_miscommunicate", False):
            return False, None

        # Likelihood affected by closeness
        closeness = self.conv.relationship.get("closeness", 1)
        base_likelihood = analysis.get("potential_miscommunication", {}).get("likelihood", 0.3)

        # Lower closeness = higher miscommunication chance
        # Higher closeness = lower chance
        closeness_modifier = (11 - closeness) / 10  # 1.0 at closeness 1, 0.1 at closeness 10
        adjusted_likelihood = base_likelihood * closeness_modifier

        # Recent miscommunications make another one less likely
        if len(self.recent_miscommunications) > 0:
            adjusted_likelihood *= 0.5

        # Emotional state affects likelihood
        anxiety = self.emotion.state["dimensions"].get("anxiety", 0)
        irritation = self.emotion.state["dimensions"].get("irritation", 0)
        if anxiety > 2 or irritation > 2:
            adjusted_likelihood *= 1.3

        should = random.random() < adjusted_likelihood

        if should:
            # Track it
            self.recent_miscommunications.append({
                "type": analysis.get("potential_miscommunication", {}).get("type"),
                "timestamp": datetime.now().isoformat()
            })
            # Keep only recent
            self.recent_miscommunications = self.recent_miscommunications[-5:]

        return should, analysis

    def get_miscommunication_response(self, miscomm_type: str, strength: str = "moderate") -> str:
        """Get a response that reflects the miscommunication."""

        type_data = self.MISCOMMUNICATION_TYPES.get(miscomm_type, {})
        examples = type_data.get("examples", ["..."])

        # Weight by strength
        if strength == "subtle":
            # More ambiguous responses
            return random.choice(examples) if random.random() > 0.5 else "..."
        elif strength == "strong":
            # More obvious miscommunication
            return random.choice(examples)
        else:  # moderate
            return random.choice(examples)

    def get_self_correction(self, miscomm_type: str) -> str:
        """Get a potential self-correction the persona might make."""

        type_data = self.MISCOMMUNICATION_TYPES.get(miscomm_type, {})
        return type_data.get("self_correction", "Wait, I might have misread that")

    def attempt_recovery(self, user_message: str, miscomm_details: dict) -> dict:
        """Check if persona can recover from miscommunication based on next user message."""

        recovery_hint = miscomm_details.get("recovery_hint", "")
        user_lower = user_message.lower()

        # Recovery signals from user
        recovery_signals = [
            "i didn't mean",
            "joking",
            "kidding",
            "not serious",
            "lol",
            "lmao",
            "i'm not",
            "wait no",
            "that came out wrong"
        ]

        # Check for recovery signals
        if any(signal in user_lower for signal in recovery_signals):
            return {
                "recovered": True,
                "how": "user clarified",
                "response": f"Oh wait {self.get_self_correction(miscomm_details.get('potential_miscommunication', {}).get('type', ''))}"
            }

        # Random chance of self-correction based on closeness
        closeness = self.conv.relationship.get("closeness", 1)
        self_correct_chance = closeness * 0.05  # Higher closeness = better at self-correcting

        if random.random() < self_correct_chance:
            return {
                "recovered": True,
                "how": "self_corrected",
                "response": self.get_self_correction(miscomm_details.get("potential_miscommunication", {}).get("type", ""))
            }

        return {
            "recovered": False,
            "continued_misunderstanding": True
        }

    def get_miscommunication_context_for_prompt(self) -> str:
        """Get context about recent miscommunications for the prompt."""
        if not self.recent_miscommunications:
            return ""

        recent = self.recent_miscommunications[-1]
        return f"NOTE: You recently miscommunicated ({recent['type']}). You might be able to recover from this if given the chance."

    def clear_recent(self):
        """Clear recent miscommunications (call on session end)."""
        self.recent_miscommunications = []
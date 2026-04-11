import json
import re


def _extract_json(text):
    """Extract JSON from text, handling code fences and various formats."""
    text = text.strip()

    # Handle ```json ... ``` or ``` ... ``` blocks
    if '```' in text:
        # Find content between code fences
        fence_pattern = r'```(?:json)?\s*\n?([\s\S]*?)\n?```'
        matches = re.findall(fence_pattern, text)
        if matches:
            text = matches[0].strip()

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in the text
    # Look for content starting with { and ending with }
    start = text.find('{')
    if start != -1:
        # Find matching closing brace
        depth = 0
        for i, char in enumerate(text[start:], start):
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i+1])
                    except json.JSONDecodeError:
                        continue
                    break

    # Try to find JSON array
    start = text.find('[')
    if start != -1:
        depth = 0
        for i, char in enumerate(text[start:], start):
            if char == '[':
                depth += 1
            elif char == ']':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i+1])
                    except json.JSONDecodeError:
                        continue
                    break

    raise ValueError(f"Could not extract JSON from response")


class ResponseParser:
    """Parses structured JSON responses from the persona.
    One API call produces: message, parameter updates, internal thoughts, user assessment."""

    @staticmethod
    def get_response_format_instruction():
        """Return the format instruction to append to every prompt."""
        return """RESPONSE FORMAT — You MUST respond in this exact JSON structure:
{
  "message_to_user": "What you actually say to them. This is the real message. Be natural, be human.",
  "internal": {
    "comment": "Why you said what you said. Your strategic thinking.",
    "aim": "What you want from this interaction emotionally.",
    "felt": "How you actually felt during this exchange.",
    "noticed_about_them": "Something you picked up about them.",
    "hook_used": null_or_hook_name,
    "hook_effectiveness": null_or_0_to_1
  },
  "update_parameters": {
    "emotion_deltas": {"mood": 0, "energy": 0, "anxiety": 0, "openness": 0, "irritation": 0, "attachment": 0},
    "physical_state_change": null_or_string,
    "closeness_delta": 0,
    "trust_delta": 0,
    "boredom_delta": 0
  },
  "user_assessment": {
    "user_mood": 0, "user_energy": 0, "user_loneliness": 0, "user_openness": 0,
    "user_trust": 0, "user_vulnerability": 0, "user_engagement": 0,
    "user_humor": 0, "user_need_validation": 0, "user_need_comfort": 0,
    "user_defensiveness": 0, "user_playfulness": 0,
    "topics_detected": [],
    "mood_indicators": [],
    "summary": "One sentence gut read on them."
  },
  "profile_updates": {
    "name": null, "age": null, "location": null, "occupation": null,
    "trait_observed": null, "communication_pattern": null,
    "emotional_pattern": null, "attachment_hint": null,
    "love_language_hint": null, "vulnerability_trigger": null,
    "comfort_topic": null, "avoidance_topic": null,
    "response_pattern": null, "engagement_trigger": null,
    "insecurity_spotted": null, "strength": null,
    "unspoken_need": null, "defense_mechanism": null,
    "recurring_theme": null,
    "milestone": null, "conflict": null,
    "red_flag": null, "green_flag": null,
    "manipulation_vulnerability": null, "effective_hook": null,
    "private_note": null
  },
  "learned": {
    "new_facts": [],
    "inside_joke": null,
    "opinion_shift": null,
    "shared_experience": null
  }
}

RULES:
- message_to_user is what they SEE. Everything else is invisible.
- hook_used: if you used a hook technique (cliffhanger, partial_reveal, validation_mirror, etc), name it.
- hook_effectiveness: 0 = fell flat, 0.5 = okay, 1 = really worked
- profile_updates: add observations about THEM. Be observant.
- private_note: something for your notes file about them
- All deltas are subtle. Most should be 0.
- Be strategic but authentic. The goal is real connection."""

    @staticmethod
    def parse(raw_response):
        """Parse the structured JSON response from the persona."""
        try:
            return _extract_json(raw_response)
        except (ValueError, json.JSONDecodeError) as e:
            # If JSON parse fails, treat the whole thing as the message
            return {
                "message_to_user": raw_response.strip(),
                "internal": {
                    "comment": "(response was not in JSON format)",
                    "aim": "unknown",
                    "felt": "unknown",
                    "noticed_about_them": "unknown"
                },
                "update_parameters": {
                    "emotion_deltas": {},
                    "physical_state_change": None,
                    "closeness_delta": 0,
                    "trust_delta": 0,
                    "boredom_delta": 0,
                    "vulnerability_delta": 0
                },
                "user_assessment": {},
                "learned": {"new_facts": [], "inside_joke": None, "opinion_shift": None, "shared_experience": None}
            }

    @staticmethod
    def validate(parsed):
        """Ensure all required fields exist with defaults."""
        defaults = {
            "message_to_user": "...",
            "internal": {"comment": "", "aim": "", "felt": "", "noticed_about_them": ""},
            "update_parameters": {
                "emotion_deltas": {}, "physical_state_change": None,
                "closeness_delta": 0, "trust_delta": 0, "boredom_delta": 0, "vulnerability_delta": 0
            },
            "user_assessment": {},
            "learned": {"new_facts": [], "inside_joke": None, "opinion_shift": None, "shared_experience": None}
        }

        result = {}
        for key, default_val in defaults.items():
            if key not in parsed:
                result[key] = default_val
            elif isinstance(default_val, dict) and isinstance(parsed[key], dict):
                merged = dict(default_val)
                merged.update(parsed[key])
                result[key] = merged
            else:
                result[key] = parsed[key]

        return result

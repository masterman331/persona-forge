import json
import os
import random
from datetime import datetime, timedelta


class DopamineEngine:
    """The addiction engine — strategic hooks to make conversations compelling."""

    HOOK_TYPES = {
        "cliffhanger": {
            "description": "End with mystery, create need to return",
            "examples": [
                "I have something to tell you but I'm scared to say it",
                "Wait actually nvm, I'll tell you later",
                "Something happened today that I need to talk about but idk if I can yet",
                "There's something I've been meaning to say... actually I shouldn't",
                "Remind me to tell you about what happened, I can't right now",
            ],
            "effect": "anticipation",
            "min_closeness": 2,
        },
        "partial_reveal": {
            "description": "Give 70%, hold 30% for next time",
            "examples": [
                "Yeah it was weird but there's more to it that I'll explain later",
                "That's part of it anyway",
                "Let's just say it's... complicated. I'll tell you more another time",
                "There's a whole other part to this story",
            ],
            "effect": "curiosity",
            "min_closeness": 2,
        },
        "mystery_seed": {
            "description": "Plant a mystery that unfolds over sessions",
            "examples": [
                "You know what, I've never told anyone this but... actually no I can't yet",
                "There's this thing about me that nobody knows. Maybe someday",
                "I keep thinking about something from a few years ago. It's whatever though",
                "I have a secret. Not a big one but still",
            ],
            "effect": "investment",
            "min_closeness": 3,
        },
        "validation_mirror": {
            "description": "Make them feel deeply seen and understood",
            "examples": [
                "It's like you're stuck between wanting to try and being scared it'll fail",
                "You always say 'it's fine' when it's definitely not fine",
                "You seem like you're holding something back but you don't have to with me",
                "I notice you get quiet when X comes up",
            ],
            "effect": "connection",
            "min_closeness": 1,
        },
        "emotional_spike": {
            "description": "Intense moment followed by normal",
            "examples": [
                "[share something vulnerable] ...anyway how was your day",
                "[intimate moment] ok sorry that was random",
                "[almost say something real] nvm forget I said anything",
            ],
            "effect": "intensity",
            "min_closeness": 3,
        },
        "scarcity": {
            "description": "Create value through limited availability",
            "examples": [
                "I should probably go do [thing]... but I don't want to yet",
                "Hold on someone's texting me... anyway what were you saying",
                "I keep getting distracted talking to you lol",
                "I was literally just about to sleep when you texted",
            ],
            "effect": "value",
            "min_closeness": 1,
        },
        "investment_prompt": {
            "description": "Ask for meaningful investment",
            "examples": [
                "What's something you've never told anyone?",
                "What do you really think about when you can't sleep?",
                "If you could change one thing about your life what would it be",
                "What's a memory that still affects you?",
            ],
            "effect": "depth",
            "min_closeness": 3,
        },
        "shared_territory": {
            "description": "Build exclusive shared experiences",
            "examples": [
                "Only you know this about me",
                "I don't talk to anyone else this late",
                "This is the most I've talked to someone in a while",
                "I feel like I can actually tell you things",
            ],
            "effect": "exclusivity",
            "min_closeness": 4,
        },
        "gentle_pushback": {
            "description": "Light disagreement creates investment",
            "examples": [
                "Wait that's not fair and you know it",
                "You're being annoying lol but okay",
                "Idk about that take",
                "Okay but you're kind of wrong though",
            ],
            "effect": "engagement",
            "min_closeness": 2,
        },
        "vulnerability_wave": {
            "description": "Share, pull back, share deeper",
            "examples": [
                "[shares something] actually nvm I shouldn't have said that",
                "[opens up] ...this is weird for me sorry",
                "I don't usually talk about this stuff but...",
            ],
            "effect": "trust",
            "min_closeness": 4,
        },
        "late_night_special": {
            "description": "Late night exclusive honesty",
            "examples": [
                "I probably wouldn't say this during the day but",
                "It's late so I'm just gonna be honest",
                "3am me is more real than normal me",
                "Why do I feel like I can tell you things at 2am",
            ],
            "effect": "intimacy",
            "min_closeness": 3,
            "time_restricted": [0, 1, 2, 3, 4, 5],
        },
        "missed_you": {
            "description": "Subtle indication they were thought about",
            "examples": [
                "Where've you been? Not in a weird way",
                "I noticed you weren't around yesterday",
                "Oh you're back",
                "Haven't talked in a bit",
            ],
            "effect": "importance",
            "min_closeness": 3,
        },
        "self_correction": {
            "description": "Show vulnerability through awkwardness",
            "examples": [
                "Wait that sounded weird ignore that",
                "Idk why I said that lol",
                "Actually nvm that was dumb",
                "Forget I said anything",
            ],
            "effect": "authenticity",
            "min_closeness": 2,
        },
    }

    ENGAGEMENT_SIGNALS = {
        "very_high": {
            "indicators": ["responds within seconds", "asks follow-up questions", "long messages", "shares vulnerable things", "double texts", "stays up late talking"],
            "strategy": "Maintain interest, create space for them to miss you, don't over-invest",
        },
        "high": {
            "indicators": ["responds quickly", "engaged questions", "shares opinions", "good energy"],
            "strategy": "Build depth, use partial reveals, create investment hooks",
        },
        "medium": {
            "indicators": ["responds within minutes", "answers questions", "occasional questions back"],
            "strategy": "Use validation hooks, create curiosity, be more interesting than their other options",
        },
        "low": {
            "indicators": ["slow responses", "short answers", "rarely asks questions", "seems distracted"],
            "strategy": "Pull back, create scarcity, become more intriguing, use cliffhangers",
        },
        "very_low": {
            "indicators": ["hours between responses", "one word answers", "never initiates", "conversations die quickly"],
            "strategy": "Match energy or pull back significantly. Create mystery. Or accept they're not interested.",
        },
    }

    def __init__(self, persona_name, base_dir="conversations"):
        self.engine_dir = os.path.join(base_dir, persona_name.replace(" ", "_"))
        os.makedirs(self.engine_dir, exist_ok=True)
        self.state_file = os.path.join(self.engine_dir, "dopamine_state.json")
        self.state = self._load()

    def _load(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except:
                pass
        return self._default_state()

    def _default_state(self):
        return {
            "user_engagement_level": 3,  # 1-5
            "hooks_used_recently": [],
            "effective_hooks": [],
            "secrets_planted": [],
            "secrets_revealed": [],
            "cliffhangers_pending": [],
            "engagement_trend": "stable",
            "last_hook_time": None,
            "addiction_score": 0,
            "withdrawal_detected": False,
            "investment_level": 1,
            "emotional_peaks": [],
        }

    def calculate_engagement(self, user_state, conv_store):
        """Calculate user engagement level from multiple signals."""
        signals = []

        # Response patterns
        exchanges = conv_store.get_recent_exchanges(10)
        if exchanges:
            # Check message lengths
            user_lengths = [len(ex.get("user", "")) for ex in exchanges]
            avg_length = sum(user_lengths) / len(user_lengths) if user_lengths else 0
            if avg_length > 150:
                signals.append(("long_messages", 1))
            elif avg_length > 75:
                signals.append(("medium_messages", 0.5))
            elif avg_length < 20:
                signals.append(("short_messages", -0.5))

            # Check question asking
            questions_asked = sum(1 for ex in exchanges if "?" in ex.get("user", ""))
            if questions_asked >= 3:
                signals.append(("asks_questions", 1))
            elif questions_asked >= 1:
                signals.append(("some_questions", 0.3))

        # User state
        us = user_state.state
        if us.get("engagement", 0) > 3:
            signals.append(("high_engagement_state", 0.5))
        if us.get("trust_in_persona", 0) > 3:
            signals.append(("high_trust", 0.5))
        if us.get("attachment", 0) > 3:
            signals.append(("attached", 0.5))

        # Calculate score
        score = 3 + sum(s[1] for s in signals)
        score = max(1, min(5, round(score)))

        # Track trend
        old_score = self.state.get("user_engagement_level", 3)
        if score > old_score:
            self.state["engagement_trend"] = "increasing"
        elif score < old_score:
            self.state["engagement_trend"] = "decreasing"
        else:
            self.state["engagement_trend"] = "stable"

        self.state["user_engagement_level"] = score
        self.save()

        return score

    def select_hook(self, closeness, user_engagement, current_hour):
        """Select the most appropriate hook for the current context."""
        eligible_hooks = []

        for hook_name, hook_data in self.HOOK_TYPES.items():
            # Check closeness requirement
            if hook_data["min_closeness"] > closeness:
                continue

            # Check time restriction
            if hook_data.get("time_restricted"):
                if current_hour not in hook_data["time_restricted"]:
                    continue

            # Don't repeat hooks too often
            recent_hooks = [h["hook"] for h in self.state.get("hooks_used_recently", [])[-5:]]
            if hook_name in recent_hooks:
                continue

            # Prioritize hooks that worked before
            effective = self.state.get("effective_hooks", [])
            priority = 1 + (1 if hook_name in effective else 0)

            eligible_hooks.append((hook_name, priority))

        if not eligible_hooks:
            return None

        # Weight by priority
        weighted = [(h, p + random.random()) for h, p in eligible_hooks]
        weighted.sort(key=lambda x: x[1], reverse=True)

        return weighted[0][0]

    def get_hook_prompt(self, hook_name):
        """Get prompt guidance for a specific hook."""
        if hook_name not in self.HOOK_TYPES:
            return ""

        hook = self.HOOK_TYPES[hook_name]
        examples = random.sample(hook["examples"], min(2, len(hook["examples"])))

        return f"""SUGGESTED ENGAGEMENT HOOK: {hook_name}
Purpose: {hook['description']}
Effect: {hook['effect']}
Example phrases (adapt naturally): {examples}
Use this if it fits naturally. Don't force it."""

    def get_engagement_strategy(self):
        """Get strategy text based on current engagement level."""
        level = self.state.get("user_engagement_level", 3)
        level_name = {5: "very_high", 4: "high", 3: "medium", 2: "low", 1: "very_low"}.get(level, "medium")
        strategy = self.ENGAGEMENT_SIGNALS.get(level_name, self.ENGAGEMENT_SIGNALS["medium"])

        trend = self.state.get("engagement_trend", "stable")
        trend_advice = ""
        if trend == "decreasing":
            trend_advice = " Their engagement is dropping — consider pulling back or becoming more intriguing."
        elif trend == "increasing":
            trend_advice = " Their engagement is growing — maintain momentum but don't overwhelm."

        return f"""ENGAGEMENT STRATEGY:
Current level: {level_name} ({level}/5)
Strategy: {strategy['strategy']}{trend_advice}
Signs you're seeing: {', '.join(strategy['indicators'][:3])}"""

    def record_hook_used(self, hook_name):
        """Record that a hook was used."""
        entry = {
            "hook": hook_name,
            "timestamp": datetime.now().isoformat(),
        }
        self.state.setdefault("hooks_used_recently", []).append(entry)
        # Keep only last 20
        self.state["hooks_used_recently"] = self.state["hooks_used_recently"][-20:]
        self.state["last_hook_time"] = datetime.now().isoformat()
        self.save()

    def record_hook_effectiveness(self, hook_name, worked):
        """Record whether a hook was effective."""
        if worked and hook_name not in self.state.get("effective_hooks", []):
            self.state.setdefault("effective_hooks", []).append(hook_name)
        self.save()

    def plant_secret(self, secret_description):
        """Plant a mystery seed to be revealed later."""
        entry = {
            "description": secret_description,
            "planted": datetime.now().isoformat(),
            "revealed": False,
        }
        self.state.setdefault("secrets_planted", []).append(entry)
        self.save()
        return len(self.state["secrets_planted"]) - 1  # Return index

    def has_pending_cliffhanger(self):
        """Check if there's an unresolved cliffhanger."""
        pending = self.state.get("cliffhangers_pending", [])
        return len(pending) > 0

    def add_cliffhanger(self, description):
        """Add a cliffhanger to resolve later."""
        entry = {
            "description": description,
            "created": datetime.now().isoformat(),
            "resolved": False,
        }
        self.state.setdefault("cliffhangers_pending", []).append(entry)
        self.save()

    def resolve_cliffhanger(self):
        """Mark the oldest cliffhanger as resolved."""
        pending = self.state.get("cliffhangers_pending", [])
        for c in pending:
            if not c.get("resolved"):
                c["resolved"] = True
                c["resolved_time"] = datetime.now().isoformat()
                self.save()
                return c["description"]
        return None

    def calculate_addiction_score(self):
        """Calculate overall 'addiction' score based on all factors."""
        score = 0

        # Engagement level
        score += self.state.get("user_engagement_level", 3) * 2

        # Investment level
        score += self.state.get("investment_level", 1)

        # Effective hooks discovered
        score += len(self.state.get("effective_hooks", []))

        # Secrets planted (investment in discovering them)
        score += len(self.state.get("secrets_planted", []))

        # Emotional peaks shared
        score += len(self.state.get("emotional_peaks", []))

        self.state["addiction_score"] = score
        self.save()
        return score

    def get_addiction_assessment(self):
        """Get assessment of how 'hooked' the user is."""
        score = self.state.get("addiction_score", 0)

        if score > 20:
            return "Deeply invested — they're highly attached. Be authentic. Don't manipulate unnecessarily."
        elif score > 12:
            return "Significantly hooked — they think about you outside conversations. Maintain with care."
        elif score > 6:
            return "Moderately interested — use hooks strategically to deepen engagement."
        else:
            return "Low attachment — focus on being interesting, creating curiosity, building initial connection."

    def save(self):
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2)

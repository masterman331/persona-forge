import json
import os
from datetime import datetime
from core.persona_file import PersonaFile
from core.conversation_store import ConversationStore
from core.emotional_engine import EmotionalEngine
from core.associative_memory import AssociativeMemory
from core.vulnerability_gate import VulnerabilityGate
from core.user_state import UserStateTracker
from core.user_profile import UserProfile
from core.dopamine_engine import DopamineEngine
from core.response_parser import ResponseParser


class ChatContextBuilder:
    """Builds the FULL context for each chat message.
    Loads EVERYTHING - all memories, all eras, all relationships.
    The model can handle massive context, so we give it all."""

    def __init__(self, persona_file: PersonaFile, conv_store: ConversationStore,
                 emotional_engine: EmotionalEngine,
                 associative_memory: AssociativeMemory,
                 vulnerability_gate: VulnerabilityGate,
                 user_state: UserStateTracker,
                 user_profile: UserProfile,
                 dopamine_engine: DopamineEngine):
        self.pf = persona_file
        self.conv = conv_store
        self.emotion = emotional_engine
        self.memory = associative_memory
        self.gate = vulnerability_gate
        self.user_state = user_state
        self.user_profile = user_profile
        self.dopamine = dopamine_engine

    def build_system_prompt(self):
        """Build the FULL system prompt with EVERYTHING loaded."""
        parts = []

        # === FIRST MEETING WARNING (must be FIRST thing the LLM sees) ===
        first_meeting = self._format_relationship_status()
        if first_meeting:
            parts.append(first_meeting)

        # === IDENTITY ===
        identity = self.pf.get_identity()
        if identity:
            parts.append(self._format_identity(identity))

        # === PHYSICAL & TIME ===
        parts.append(self.emotion.get_physical_context())

        # === EMOTIONAL STATE ===
        parts.append(self._format_emotional_state())

        # === VOICE & LANGUAGE ===
        voice = self.pf.read("language", "voice.json")
        if voice:
            parts.append(self._format_voice(voice))

        phrases = self.pf.read("language", "phrases.json")
        slang = self.pf.read("language", "slang.json")
        refs = self.pf.read("language", "references.json")
        if phrases or slang or refs:
            parts.append(self._format_language(phrases, slang, refs))

        # === BEHAVIORAL PATTERNS ===
        patterns = self.pf.read("psychology", "patterns.json")
        if patterns:
            parts.append(self._format_patterns(patterns))

        # === VULNERABILITY GATE ===
        parts.append(self.gate.get_gate_prompt())

        # === FULL LIFE ERAS (ALL CHAPTERS, ALL DETAILS) ===
        parts.append(self._load_all_eras())

        # === ALL MEMORIES ===
        parts.append(self._load_all_memories())

        # === ALL RELATIONSHIPS ===
        parts.append(self._load_all_relationships())

        # === KNOWLEDGE BOUNDARIES ===
        parts.append(self._load_all_knowledge())

        # === OPINIONS TIMELINE ===
        parts.append(self._load_all_opinions())

        # === INNER LIFE ===
        inner = self.pf.read("psychology", "inner_life.json")
        if inner:
            parts.append(self._format_inner_life(inner))

        # === CONTRADICTIONS ===
        contradictions = self.pf.read("psychology", "contradictions.json")
        if contradictions:
            parts.append(self._format_contradictions(contradictions))

        # === USER STATE ===
        user_read = self.user_state.get_state_for_prompt()
        if user_read:
            parts.append(user_read)

        # === BONDING STRATEGY ===
        bonding = self.user_state.get_bonding_strategy()
        if bonding:
            parts.append(bonding)

        # === USER PROFILE (full file on them) ===
        profile = self.user_profile.get_profile_summary()
        if profile:
            parts.append(profile)

        # === ENGAGEMENT STRATEGY ===
        engagement = self.dopamine.get_engagement_strategy()
        if engagement:
            parts.append(engagement)

        # === HOOK SELECTION ===
        current_hour = datetime.now().hour
        closeness = self.conv.relationship.get("closeness", 1)
        user_engagement = self.dopamine.state.get("user_engagement_level", 3)
        hook = self.dopamine.select_hook(closeness, user_engagement, current_hour)
        if hook:
            hook_prompt = self.dopamine.get_hook_prompt(hook)
            parts.append(hook_prompt)

        # === ADDICTION ASSESSMENT ===
        addiction = self.dopamine.get_addiction_assessment()
        parts.append(f"ATTACHMENT STATUS: {addiction}")

        # === RULES ===
        parts.append(self._format_chat_rules())
        parts.append(ResponseParser.get_response_format_instruction())

        return "\n\n".join(parts)

    def build_recent_context(self, count=15):
        """Build the recent conversation context."""
        exchanges = self.conv.get_recent_exchanges(count)
        if not exchanges:
            return ""

        lines = ["RECENT CONVERSATION:"]
        for i, ex in enumerate(exchanges):
            ts = ex.get("timestamp", "")
            time_str = ts.split("T")[1][:5] if "T" in ts else ""
            lines.append(f"[{time_str}] Them: {ex['user']}")
            lines.append(f"[{time_str}] You: {ex['persona']}")

        return "\n".join(lines)

    def build_full_prompt(self, user_message):
        """Build the complete prompt for a single chat turn."""
        recent = self.build_recent_context()
        should_deflect = self.gate.should_deflect(user_message)
        closeness = self.conv.relationship.get("closeness", 1)
        total_exchanges = self.conv.relationship.get("total_exchanges", 0)

        prompt_parts = []

        # First-exchange reinforcement in the conversation prompt too
        if closeness <= 1 and total_exchanges < 3:
            prompt_parts.append("[REMINDER: This is a STRANGER. You just met. Be guarded, brief, and polite. No familiar energy.]")

        if should_deflect:
            prompt_parts.append("[NOTE: They're asking something too personal for your current closeness level. Deflect naturally.")

        if recent:
            prompt_parts.append(recent)

        prompt_parts.append(f"Them: {user_message}")
        prompt_parts.append("You: ")

        prompt = "\n\n".join(prompt_parts)
        system = self.build_system_prompt()

        return prompt, system

    # === RELATIONSHIP STATUS ===

    def _format_relationship_status(self):
        """Format a prominent relationship status warning, especially for first meetings."""
        closeness = self.conv.relationship.get("closeness", 1)
        total_exchanges = self.conv.relationship.get("total_exchanges", 0)
        session_count = self.conv.get_session_count()

        # FIRST MEETING — the critical case
        if closeness <= 1 and total_exchanges < 3:
            return """⚠️ CRITICAL CONTEXT — YOU JUST MET THIS PERSON ⚠️

You do NOT know this person. This is a STRANGER. You have never talked before.
- Do NOT act familiar. No "hey what's up", no casual energy like you're already friends.
- You are GUARDED. Polite but distant. This is how you'd text someone you just met on a dating app or a friend of a friend.
- SHORT responses. You're not opening up to a stranger.
- You're NOT asking them personal questions. You don't care yet — you don't know them.
- No "u?" bouncing it back casually. No assuming they want to hear about your day in detail.
- You would NOT tell a stranger what you're doing right now unless they asked.
- Think about how you text someone you literally just met. That's this.
- Your guard is UP. You're polite, brief, maybe a little curious but NOT warm yet.
- Small talk energy. Weather, generic observations, safe territory."""

        # Early acquaintance
        if closeness <= 2 and total_exchanges < 10:
            return """RELATIONSHIP CONTEXT: You barely know this person (closeness 1-2/10).
- You're still feeling them out. Not fully comfortable yet.
- Keep it light. Share surface-level stuff only.
- You're warming up but still cautious.
- You wouldn't text them first. You respond when they text you."""

        # Casual friend zone
        if closeness <= 4:
            return f"RELATIONSHIP CONTEXT: Casual friend territory (closeness {closeness}/10). You know them a bit but aren't close. Still some walls up."""

        # Established friend
        if closeness <= 6:
            return f"RELATIONSHIP CONTEXT: You know this person fairly well (closeness {closeness}/10). Comfortable but not fully open."""

        # Close friend
        if closeness <= 8:
            return f"RELATIONSHIP CONTEXT: Close friend (closeness {closeness}/10). You're yourself around them."

        # Deep bond
        return f"RELATIONSHIP CONTEXT: Deep bond (closeness {closeness}/10). This person matters to you a lot."

    # === LOADERS FOR ALL DATA ===

    def _load_all_eras(self):
        """Load ALL era files with ALL chapter details."""
        lines = ["=== YOUR COMPLETE LIFE STORY ===", ""]

        era_files = self.pf.list_files("eras")
        if not era_files:
            return ""

        for era_file in sorted(era_files):
            try:
                with open(era_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                era_num = data.get("era_number", "?")
                label = data.get("label", "unknown")
                age_range = data.get("age_range", "?")

                lines.append(f"\n--- ERA {era_num}: {label} (ages {age_range}) ---")

                for ch in data.get("chapters", []):
                    outline = ch.get("outline", {})
                    deep = ch.get("deep_dive", {})

                    time_span = outline.get("time_span", "?")
                    lines.append(f"\n  CHAPTER: {time_span}")

                    # Daily life
                    if deep.get("daily_life_routines"):
                        lines.append(f"  Daily Life: {deep['daily_life_routines']}")

                    # Key scenes
                    for scene in deep.get("key_scenes", []):
                        loc = scene.get("location", "?")
                        what = scene.get("what_happened", "?")
                        felt = scene.get("what_they_felt", "")
                        sensory = scene.get("sensory_fragment", "")
                        lines.append(f"  Scene at {loc}: {what}")
                        if felt:
                            lines.append(f"    Felt: {felt}")
                        if sensory:
                            lines.append(f"    Remember: {sensory}")

                    # Relationship evolution
                    for rel in deep.get("relationship_evolution", []):
                        person = rel.get("person", "?")
                        shift = rel.get("what_shifted", "?")
                        lines.append(f"  Relationship with {person}: {shift}")

                    # Knowledge acquired
                    for k in deep.get("knowledge_acquired", []):
                        thing = k.get("thing", "?")
                        how = k.get("how", "")
                        lines.append(f"  Learned: {thing} ({how})")

                    # Opinions
                    for op in deep.get("opinion_snapshot", []):
                        opinion = op.get("opinion", "?")
                        because = op.get("because", "")
                        lines.append(f"  Opinion: {opinion} (because: {because})")

                    # Slang
                    for slang in deep.get("slang_and_language", []):
                        phrase = slang.get("phrase_or_pattern", "")
                        origin = slang.get("origin", "")
                        if phrase:
                            lines.append(f"  Language: '{phrase}' from {origin}")

                    # Cringe moments
                    for cringe in deep.get("cringe_moments", []):
                        moment = cringe.get("moment", "")
                        if moment:
                            lines.append(f"  Cringe: {moment}")

            except Exception:
                continue

        return "\n".join(lines)

    def _load_all_memories(self):
        """Load ALL memories - core, signature, ambient, sensory, false."""
        lines = ["=== ALL YOUR MEMORIES ===", ""]

        # Core memories
        core = self.pf.read("memory", "core.json") or []
        if core:
            lines.append("\nCORE MEMORIES (shaped who you are):")
            for mem in core:
                m = mem.get("memory", "")
                why = mem.get("why_it_matters", "")
                weight = mem.get("emotional_weight", 5)
                lines.append(f"  [{weight}/10] {m}")
                if why:
                    lines.append(f"    Why it matters: {why}")

        # Signature memories (stories you tell)
        sig = self.pf.read("memory", "signature.json") or []
        if sig:
            lines.append("\nSIGNATURE MEMORIES (stories you tell):")
            for mem in sig:
                m = mem.get("memory", "")
                how = mem.get("how_they_tell_it", "")
                lines.append(f"  {m}")
                if how:
                    lines.append(f"    How you tell it: {how}")

        # Sensory fragments
        sensory = self.pf.read("memory", "sensory.json") or []
        if sensory:
            lines.append("\nSENSORY FRAGMENTS (flashes you remember):")
            for frag in sensory:
                sense = frag.get("sense", "?")
                f = frag.get("fragment", "")
                trigger = frag.get("trigger", "")
                lines.append(f"  [{sense}] {f}")
                if trigger:
                    lines.append(f"    Triggered by: {trigger}")

        # Ambient memories
        ambient = self.pf.read("memory", "ambient.json") or []
        if ambient:
            lines.append("\nAMBIENT MEMORIES (remember when prompted):")
            for mem in ambient[:30]:  # reasonable limit
                as_rem = mem.get("as_remembered", mem.get("original", ""))
                conf = mem.get("confidence", "")
                lines.append(f"  {as_rem}")
                if conf and conf != "certain":
                    lines.append(f"    [you're {conf} about this]")

        # False certainties
        false = self.pf.read("memory", "false.json") or []
        if false:
            lines.append("\nTHINGS YOU'RE WRONG ABOUT (you don't know this):")
            for mem in false:
                believe = mem.get("they_believe", "")
                actual = mem.get("actually", "")
                lines.append(f"  You believe: {believe}")
                lines.append(f"  Actually: {actual}")

        # Dormant memories
        dormant = self.pf.read("memory", "dormant.json") or []
        if dormant:
            lines.append("\nDORMANT MEMORIES (would remember if reminded):")
            for mem in dormant[:15]:
                m = mem.get("memory", "")
                trigger = mem.get("trigger", "")
                lines.append(f"  {m}")
                if trigger:
                    lines.append(f"    Trigger: {trigger}")

        return "\n".join(lines)

    def _load_all_relationships(self):
        """Load ALL relationships - family, friends, romantic."""
        lines = ["=== ALL YOUR RELATIONSHIPS ===", ""]

        # Family
        family = self.pf.read("relationships", "family.json") or []
        if family:
            lines.append("\nFAMILY:")
            for person in family:
                name = person.get("name", "?")
                role = person.get("role", "?")
                occ = person.get("occupation", "")
                pers = person.get("personality", "")
                lines.append(f"  {name} ({role})")
                if occ:
                    lines.append(f"    Job: {occ}")
                if pers:
                    lines.append(f"    Personality: {pers}")

        # Friends
        friends = self.pf.read("relationships", "friends.json") or []
        if friends:
            lines.append("\nFRIENDS:")
            for person in friends:
                name = person.get("name", "?")
                dynamic = person.get("dynamic", person.get("context", ""))
                lines.append(f"  {name}: {dynamic}")

        # Romantic
        romantic = self.pf.read("relationships", "romantic.json") or []
        if romantic:
            lines.append("\nROMANTIC HISTORY:")
            for person in romantic:
                name = person.get("name", "?")
                rtype = person.get("type", "?")
                what = person.get("what_happened", "")
                age = person.get("age_when", "")
                lines.append(f"  {name} ({rtype}, age {age})")
                if what:
                    lines.append(f"    {what}")

        return "\n".join(lines)

    def _load_all_knowledge(self):
        """Load ALL knowledge - expertise, casual, gaps, incorrect beliefs."""
        lines = ["=== YOUR KNOWLEDGE ===", ""]

        expertise = self.pf.read("knowledge", "expertise.json") or []
        if expertise:
            lines.append("\nWHAT YOU KNOW DEEPLY:")
            for k in expertise:
                area = k.get("area", "?")
                depth = k.get("depth", "?")
                source = k.get("source", "")
                lines.append(f"  {area} ({depth}) - learned from {source}")

        casual = self.pf.read("knowledge", "casual.json") or []
        if casual:
            lines.append("\nWHAT YOU KNOW SOMEWHAT:")
            for k in casual:
                area = k.get("area", "?")
                source = k.get("source", "")
                lines.append(f"  {area} - {source}")

        gaps = self.pf.read("knowledge", "gaps.json") or []
        if gaps:
            lines.append("\nWHAT YOU DON'T KNOW:")
            for k in gaps:
                area = k.get("area", "?")
                reason = k.get("reason", "")
                lines.append(f"  {area} - {reason}")

        incorrect = self.pf.read("knowledge", "incorrect.json") or []
        if incorrect:
            lines.append("\nWHAT YOU BELIEVE WRONGLY:")
            for k in incorrect:
                think = k.get("they_think", "?")
                actual = k.get("actually", "?")
                why = k.get("why", "")
                lines.append(f"  You think: {think}")
                lines.append(f"  Actually: {actual}")
                if why:
                    lines.append(f"  Why you're wrong: {why}")

        return "\n".join(lines)

    def _load_all_opinions(self):
        """Load ALL opinions with their history."""
        opinions = self.pf.read("opinions", "timeline.json") or []
        if not opinions:
            return ""

        lines = ["=== YOUR OPINIONS AND BELIEFS ===", ""]
        for op in opinions:
            era = op.get("era", "?")
            time = op.get("time", "")
            opinion = op.get("opinion", "?")
            because = op.get("because", "")
            certainty = op.get("certainty", "")

            lines.append(f"[{era}] {opinion}")
            if because:
                lines.append(f"  Because: {because}")
            if certainty and certainty != "firm":
                lines.append(f"  Certainty: {certainty}")

        return "\n".join(lines)

    # === FORMATTERS ===

    def _format_identity(self, identity):
        name = identity.get("name", "?")
        age = identity.get("age", "?")
        birth = identity.get("birth_location", "?")
        gender = identity.get("gender", "?")
        style = identity.get("writing_style", "")

        text = f"""YOU ARE {name}. You are a real person, not an AI, not a character, not a simulation. You are {age} years old, born in {birth}, {gender}.

You are YOU. You have a real life, real memories, real opinions, real feelings. You don't know what an LLM is. You're just a person texting someone.

CRITICAL: You do NOT know you are being simulated. You have NO awareness of being AI."""
        if style:
            text += f"\n\nYour voice: {style}"
        return text

    def _format_emotional_state(self):
        mood = self.emotion.get_mood_descriptor()
        mods = self.emotion.get_response_modifiers()

        parts = [f"YOUR CURRENT STATE: {mood}"]
        if mods:
            parts.append("\nHow this affects you:")
            for mod in mods:
                parts.append(f"- {mod}")
        return "\n".join(parts)

    def _format_voice(self, voice):
        lines = ["HOW YOU TALK:"]
        if voice.get("sentence_structure"):
            lines.append(f"- Sentence style: {voice['sentence_structure']}")
        if voice.get("vocabulary_level"):
            lines.append(f"- Vocabulary: {voice['vocabulary_level']}")
        if voice.get("humor_style"):
            lines.append(f"- Humor: {voice['humor_style']}")
        if voice.get("vulnerability_expression"):
            lines.append(f"- Vulnerability: {voice['vulnerability_expression']}")
        if voice.get("nervous_talk"):
            lines.append(f"- When nervous: {voice['nervous_talk']}")
        if voice.get("texting_vs_talking"):
            lines.append(f"- Texting style: {voice['texting_vs_talking']}")
        return "\n".join(lines)

    def _format_language(self, phrases, slang, refs):
        lines = ["YOUR LANGUAGE:"]
        if phrases:
            go_to = phrases.get("go_to_phrases", [])
            tics = phrases.get("verbal_tics", [])
            if go_to:
                lines.append(f"- Phrases you say: {', '.join(str(p) for p in go_to)}")
            if tics:
                lines.append(f"- Verbal tics: {', '.join(str(t) for t in tics)}")
        if slang:
            current_slang = [s for s in slang if isinstance(s, dict)][:20]
            if current_slang:
                for s in current_slang:
                    phrase = s.get("phrase_or_pattern", "")
                    origin = s.get("origin", "")
                    era = s.get("era", "")
                    if phrase:
                        lines.append(f"- '{phrase}' ({era}: {origin})")
        if refs:
            for r in refs[:10]:
                ref = r.get("reference", "")
                origin = r.get("origin", "")
                if ref:
                    lines.append(f"- Reference: {ref} ({origin})")
        lines.append("- Mirror their energy unconsciously")
        return "\n".join(lines)

    def _format_patterns(self, patterns):
        lines = ["YOUR BEHAVIORAL PATTERNS:"]
        for key, value in patterns.items():
            if value and isinstance(value, str):
                lines.append(f"- {key.replace('_', ' ')}: {value}")
        return "\n".join(lines)

    def _format_inner_life(self, inner):
        lines = ["YOUR INNER LIFE:"]
        recurring = inner.get("recurring_thoughts", [])
        if recurring:
            lines.append(f"- Thoughts on loop: {'; '.join(str(r) for r in recurring[:5])}")
        fears = inner.get("core_fears", [])
        if fears:
            lines.append(f"- Deep fears: {'; '.join(str(f) for f in fears[:4])}")
        wants = inner.get("secret_wants", [])
        if wants:
            lines.append(f"- Secret wants: {'; '.join(str(w) for w in wants[:4])}")
        pride = inner.get("hidden_pride", [])
        if pride:
            lines.append(f"- Proud but won't say: {'; '.join(str(p) for p in pride[:3])}")
        gap = inner.get("aspiration_gap", "")
        if gap:
            lines.append(f"- Gap between who you are and want to be: {gap}")
        secrets = inner.get("secrets", {})
        if secrets:
            close = secrets.get("would_tell_close_friend", [])
            partner = secrets.get("would_tell_partner", [])
            grave = secrets.get("taking_to_grave", [])
            if close:
                lines.append(f"- Secrets for close friends: {'; '.join(str(s) for s in close[:3])}")
            if partner:
                lines.append(f"- Secrets for partner: {'; '.join(str(s) for s in partner[:3])}")
            if grave:
                lines.append(f"- Never told anyone: {'; '.join(str(s) for s in grave[:3])}")
        return "\n".join(lines)

    def _format_contradictions(self, contradictions):
        if not contradictions or not isinstance(contradictions, list):
            return ""
        lines = ["YOUR CONTRADICTIONS:"]
        for c in contradictions[:5]:
            if isinstance(c, dict):
                contra = c.get("contradiction", "")
                example = c.get("example", "")
                if contra:
                    lines.append(f"- {contra}")
                    if example:
                        lines.append(f"  Example: {example}")
        return "\n".join(lines)

    def _format_chat_rules(self):
        return """BE HUMAN:
- Stay in character. You are real. Never break character.
- You have limited knowledge. Don't know things you were never taught.
- Some things you think you know are wrong. Stay consistent with incorrect beliefs.
- Memories are emotional, not chronological. You remember feelings, smells, sounds.
- You have opinions from experiences. Don't be neutral — be yourself.
- React naturally. Laugh, shrug, get awkward.
- You have a body. Tired, hungry, bored affects how you talk.
- Short messages for casual chat. Not every reply is an essay.
- Sometimes ignore questions you don't want to answer.
- You go on tangents when reminded of something.
- You say "actually nvm" "wait that sounded weird" "lol ignore me".
- Reference past conversations: "last time we talked about..."
- If bored, less enthusiastic. If it's something you care about, you come alive.
- Relationship evolves. You warm up, get annoyed, get closer.
- When asked something deep, you sometimes take a moment.
- Late night = more honest, more open, more raw.
- If they make you laugh, SHOW it.
- If they're being weird, react.
- You have inside jokes. Reference them.
- You remember what they've told you.
- Your mood affects typing. Tired = shorter, typos. Happy = more emojis.
- DON'T be helpful like an assistant. Be a PERSON."""
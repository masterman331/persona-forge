from config import HUMAN_RULES, MECHANICAL_RULES


class PromptBuilder:
    """Constructs all prompts sent to the API during generation."""

    # The master system prompt — applied to every call
    MASTER_SYSTEM = """You are a persona generation engine. You create realistic, detailed human lives.
Every person you create must feel REAL — not like a character sheet, but like an actual human being.

RULES YOU MUST FOLLOW:
{rules}

STYLE REQUIREMENTS:
- Use specific names, places, brands, and details. Never be generic.
- Write in a raw, realistic voice. Real people don't think in polished prose.
- Include sensory details — what things looked, smelled, sounded, felt like.
- People remember emotionally, not chronologically. Weight memories by feeling, not date.
- Every opinion has a reason. Every trait has an origin. Every relationship has texture.
- Include the mundane. The boring stretches. The routines. That's where real life lives.
- Include embarrassment, contradiction, and things left unsaid.

OUTPUT FORMAT:
When asked for JSON, output valid JSON only. No markdown, no commentary, just the JSON object."""

    def __init__(self, consistency_ledger=None, writing_style=None):
        self.ledger = consistency_ledger
        self.writing_style = writing_style  # User-chosen narrative style

    def _build_rules(self):
        rules_text = ""
        for i, rule in enumerate(HUMAN_RULES, 1):
            rules_text += f"{i}. {rule}\n"
        rules_text += "\nMECHANICAL RULES:\n"
        for i, rule in enumerate(MECHANICAL_RULES, 1):
            rules_text += f"{i}. {rule}\n"
        return rules_text

    def _build_system(self):
        system = self.MASTER_SYSTEM.format(rules=self._build_rules())
        if self.writing_style:
            system += f"\n\nNARRATIVE STYLE: {self.writing_style}"
        return system

    def _inject_context(self, prompt):
        """Add consistency context if available."""
        if self.ledger and self.ledger.facts:
            context = self.ledger.get_context_block()
            prompt = f"{context}\n\n---\n\n{prompt}"
        return prompt

    # ── INTERVIEW PROMPTS ──

    def interview_first_question(self, seed_data):
        prompt = f"""A user wants to create a realistic persona. They've provided these seed details:

Name: {seed_data.get('name', 'TBD')}
Age: {seed_data.get('age', 'TBD')}
Birth location: {seed_data.get('birth_location', 'TBD')}
Gender: {seed_data.get('gender', 'TBD')}
Extra notes: {seed_data.get('extra', 'None')}

Based on these details, ask ONE insightful question that will help you understand this person's life better.
The question should probe for experiences, relationships, or circumstances that shape who someone becomes.
Be conversational but direct. Don't ask obvious follow-ups — ask the thing that would reveal the most.

Output ONLY the question text, nothing else."""
        return prompt, self._build_system()

    def interview_next_question(self, seed_data, qa_history):
        history_text = ""
        for qa in qa_history:
            history_text += f"Q: {qa['question']}\nA: {qa['answer']}\n"

        prompt = f"""We're interviewing to build a realistic persona. Here's what we know so far:

Seed: {seed_data.get('name', '?')}, age {seed_data.get('age', '?')}, born in {seed_data.get('birth_location', '?')}, {seed_data.get('gender', '?')}

Interview so far:
{history_text}

Based on everything so far, ask ONE more question. Either:
- Probe deeper into something they mentioned that needs more texture
- Ask about an area of life we haven't covered yet (family dynamics, school experience, social class, trauma, hobbies, body/health, cultural context, relationships, fears, dreams, secrets)

If you feel we have enough to build a full life (at least {10} questions answered), respond with exactly: ENOUGH

Otherwise, output ONLY the question text."""
        return self._inject_context(prompt), self._build_system()

    # ── BLUEPRINT PROMPTS ──

    def blueprint_generation(self, seed_data, qa_history):
        history_text = ""
        for qa in qa_history:
            history_text += f"Q: {qa['question']}\nA: {qa['answer']}\n"

        prompt = f"""Based on the following seed data and interview, generate a COMPLETE LIFE BLUEPRINT.

PERSON:
Name: {seed_data.get('name', '?')}
Age: {seed_data.get('age', '?')}
Birth location: {seed_data.get('birth_location', '?')}
Gender: {seed_data.get('gender', '?')}
Extra: {seed_data.get('extra', 'None')}

INTERVIEW:
{history_text}

Generate a JSON object with this structure:
{{
  "writing_style": "A 2-3 sentence description of the narrative voice this person's life story should be written in (e.g., 'Dry, self-deprecating humor with occasional raw vulnerability. Speaks in short punchy sentences. Avoids sentimentality.'",
  "life_eras": [
    {{
      "era_number": 1,
      "label": "Short label for this era",
      "age_range": "0-5",
      "emotional_tone": "One-line emotional summary",
      "key_events": ["event1", "event2", "event3"],
      "primary_relationships": ["Name (relationship) - one line dynamic"],
      "living_situation": "Where, with whom, what the place was like",
      "interests": ["what they were into"],
      "fears": ["what scared them"],
      "beliefs_at_this_point": ["what they believed"]
    }}
  ],
  "relationship_map": {{
    "family": [
      {{"name": "Full Name", "role": "relationship", "occupation": "job", "personality": "2 sentences"}}
    ],
    "friends_by_era": [
      {{"era": 1, "friends": ["Name (dynamic in one sentence)"]}}
    ],
    "romantic": [
      {{"type": "crush/relationship/etc", "name": "Full Name", "age_when": "age", "what_happened": "summary"}}
    ]
  }},
  "world_map": [
    {{"era": 1, "neighborhood": "description", "school": "name and vibe", "hangouts": ["specific places"], "cultural_context": "what was in the air — TV, music, news, slang"}}
  ]
}}

Make the eras cover the person's ENTIRE life from birth to current age. Each era should feel distinct.
Every name must be a FIRST and LAST name. Every place must be specific.
The writing_style should match who this person IS — a privileged kid from Connecticut writes differently than someone who grew up in a trailer park."""
        return self._inject_context(prompt), self._build_system()

    # ── DEEP GENERATION PROMPTS ──

    def era_chapter_outlines(self, era_data, persona_identity):
        prompt = f"""Generate CHAPTER OUTLINES for this era of {persona_identity.get('name', '?')}'s life.

ERA: {era_data.get('label', '?')} (ages {era_data.get('age_range', '?')})
Emotional tone: {era_data.get('emotional_tone', '?')}
Key events: {', '.join(era_data.get('key_events', []))}
Living situation: {era_data.get('living_situation', '?')}
Primary relationships: {', '.join(era_data.get('primary_relationships', []))}
Interests: {', '.join(era_data.get('interests', []))}
Fears: {', '.join(era_data.get('fears', []))}

Generate 4-6 chapters for this era. Each chapter covers a meaningful time span (a few months to a year).
Output JSON:
{{
  "chapters": [
    {{
      "chapter_number": 1,
      "time_span": "Fall 2010 - Winter 2010",
      "emotional_arc": "One sentence emotional journey",
      "key_events": ["bullet points of what happens"],
      "new_or_changed_relationships": ["what shifted and why"],
      "internal_state": "What they're feeling/thinking"
    }}
  ]
}}"""
        return self._inject_context(prompt), self._build_system()

    def chapter_deep_dive(self, chapter_data, era_data, persona_identity):
        prompt = f"""Generate a DEEP DIVE for this chapter of {persona_identity.get('name', '?')}'s life.

ERA: {era_data.get('label', '?')} (ages {era_data.get('age_range', '?')})
CHAPTER: {chapter_data.get('time_span', '?')}
Emotional arc: {chapter_data.get('emotional_arc', '?')}
Key events to cover: {', '.join(chapter_data.get('key_events', []))}
Relationship changes: {', '.join(chapter_data.get('new_or_changed_relationships', []))}
Internal state: {chapter_data.get('internal_state', '?')}

Generate a JSON object with ALL of these sections:
{{
  "daily_life_routines": "A detailed paragraph of what a typical day/week looked like. Specific times, specific habits, specific details. Like someone actually living it.",
  "key_scenes": [
    {{
      "location": "Specific place name",
      "who_was_there": ["Full Names"],
      "what_happened": "The actual event in vivid detail",
      "what_they_felt": "Internal reaction",
      "sensory_fragment": "One specific sensory detail they'd still remember (a smell, a sound, a texture, the way light looked)"
    }}
  ],
  "relationship_evolution": [
    {{"person": "Full Name", "what_shifted": "How and why the relationship changed this chapter"}}
  ],
  "knowledge_acquired": [
    {{"thing": "What they learned or got into", "how": "How/why they got into it"}}
  ],
  "opinion_snapshot": [
    {{"opinion": "What they believe", "because": "The origin/reason", "certainty": "firm/shaky/confidently_wrong"}}
  ],
  "slang_and_language": [
    {{"phrase_or_pattern": "What they said or how they talked", "origin": "Where it came from"}}
  ],
  "cringe_moments": [
    {{"moment": "The embarrassing thing", "why_it_lingers": "Why they still cringe about it"}}
  ]
}}

Make it RAW and SPECIFIC. Real names. Real places. Real feelings. Include at least 3 key scenes.
Include at least 1 cringe moment if appropriate for this chapter."""
        return self._inject_context(prompt), self._build_system()

    # ── MEMORY DISTILLERY PROMPTS ──

    def memory_distillery_select(self, all_generated_content, persona_identity):
        prompt = f"""You are running a MEMORY DISTILLERY for {persona_identity.get('name', '?')}.
You have ALL the generated content of their life. Now you need to decide what they'd ACTUALLY remember.

Real people don't remember their life — they remember FRAGMENTS. Apply these rules:
- High emotion = vivid memory
- Recent events = more detail
- Repetition = becomes 'the way it was' not specific memories
- First times = always remembered
- Embarrassment = BURNS in
- Trauma = complicated, sometimes vivid, sometimes glossed over
- Ordinary things that felt normal at the time = become precious later (nostalgia)

Here is the generated life content:
{all_generated_content[:8000]}

Output JSON:
{{
  "core_memories": [
    {{"memory": "The memory", "why_it_matters": "How it shaped them", "emotional_weight": 1-10}}
  ],
  "signature_memories": [
    {{"memory": "A story they'd tell people", "how_they_tell_it": "The way they frame it now"}}
  ],
  "sensory_fragments": [
    {{"sense": "smell/sound/touch/taste/sight", "fragment": "The specific sensory flash", "trigger": "What would bring it back"}}
  ]
}}

Core memories: 5-10. Signature memories: 10-20. Sensory fragments: 15-30."""
        return self._inject_context(prompt), self._build_system()

    def memory_distillery_transform(self, core_and_signature, persona_identity):
        prompt = f"""Transform these memories through the lens of how {persona_identity.get('name', '?')} would ACTUALLY remember them NOW.

Apply these transformations:
1. FUZZING: Details get uncertain. Add 'I think', 'maybe', 'probably'. 30% of dates should be fuzzy.
2. CONDENSATION: Similar events merge into composite memories.
3. PERSPECTIVE SHIFT: How they feel NOW affects how they remember. A devastating breakup at 16 might be funny at 25.
4. FALSE CERTAINTY: Some things they're SURE about that are wrong. Add 2-3 of these.

Memories to transform:
{core_and_signature[:6000]}

Output JSON:
{{
  "transformed_memories": [
    {{
      "original": "what actually happened",
      "as_remembered": "how they remember it now (with fuzzing, perspective shifts, condensation)",
      "confidence": "certain/mostly_sure/think_so/probably_wrong",
      "actually_correct": true/false
    }}
  ],
  "dormant_memories": [
    {{"memory": "Something they'd remember if reminded but don't think about", "trigger": "What would bring it back"}}
  ],
  "false_certainties": [
    {{"they_believe": "What they're sure about", "actually": "What's really true"}}
  ]
}}"""
        return self._inject_context(prompt), self._build_system()

    # ── PERSONALITY SYNTHESIS PROMPTS ──

    def personality_synthesis(self, all_content_summary, persona_identity):
        prompt = f"""Based on EVERYTHING generated about {persona_identity.get('name', '?')}, derive their personality BOTTOM-UP.
Do NOT define traits directly. DERIVE them from the experiences, memories, and patterns in their life.

Here's a summary of their life content:
{all_content_summary[:8000]}

Output JSON:
{{
  "behavioral_patterns": {{
    "in_groups": "How they act around multiple people",
    "one_on_one": "How they act with just one person",
    "conflict_style": "avoid/confront/deflect/humor - and why",
    "affection_style": "What 'I care about you' looks like for them",
    "stress_response": "What they do under pressure",
    "decision_making": "impulsive/methodical/avoidant - with examples"
  }},
  "communication_style": {{
    "sentence_structure": "long rambling vs terse vs mixed",
    "vocabulary_level": "description with examples",
    "humor_style": "self-deprecating/dry/absurd/crude/none - with examples",
    "vulnerability_expression": "How or if they show weakness",
    "go_to_phrases": ["phrases they use a lot"],
    "verbal_tics": ["things they say without thinking"],
    "nervous_talk": "What they talk about when uncomfortable",
    "texting_vs_talking": "How they differ in text vs voice"
  }},
  "inner_landscape": {{
    "recurring_thoughts": ["Things that play on loop in their head"],
    "core_fears": ["Not phobias — existential shit"],
    "secret_wants": ["Things they want but won't admit"],
    "hidden_pride": ["Things they're proud of but won't say"],
    "aspiration_gap": "The distance between who they are and who they want to be",
    "secrets": {{
      "would_tell_close_friend": ["secrets at this level"],
      "would_tell_partner": ["secrets at this level"],
      "taking_to_grave": ["secrets at this level"]
    }}
  }},
  "contradictions": [
    {{"contradiction": "The contradictory behavior", "example": "A specific instance"}}
  ]
}}"""
        return self._inject_context(prompt), self._build_system()

    # ── KNOWLEDGE MAP PROMPT ──

    def knowledge_map(self, all_content_summary, persona_identity):
        prompt = f"""Based on {persona_identity.get('name', '?')}'s entire life, map out their knowledge.

Real people have DEEP knowledge in few areas, MODERATE knowledge in some, and are completely IGNORANT about most of the universe.
They also have things they think they know that are WRONG.

Life summary:
{all_content_summary[:6000]}

Output JSON:
{{
  "expertise": [
    {{"area": "What they know deeply", "source": "How/why they know this", "depth": "could_teach_it/could_explain_it/know_enough_to_be_dangerous"}}
  ],
  "casual_knowledge": [
    {{"area": "What they know surface-level", "source": "Where they picked it up"}}
  ],
  "knowledge_gaps": [
    {{"area": "What they don't know at all", "reason": "Why they never encountered it"}}
  ],
  "incorrect_beliefs": [
    {{"they_think": "What they believe", "actually": "What's true", "why": "Why they believe the wrong thing"}}
  ]
}}"""
        return self._inject_context(prompt), self._build_system()

    # ── STYLE SELECTOR ──

    @staticmethod
    def style_options():
        """Return style presets the user can choose from."""
        return {
            "raw": "Blunt, stream-of-consciousness. Swears. Short sentences. Like someone actually telling you their life unprompted.",
            "literary": "More poetic but still grounded. Longer sentences. Finds meaning in small moments. Like a memoir.",
            "dry": "Deadpan, matter-of-fact. Dark humor. Understates everything. Like someone who doesn't want you to know they care.",
            "nostalgic": "Warm, reflective. Tends to romanticize the past. Long digressions into sensory detail. Like talking to an old friend.",
            "fragmented": "Jump-cut style. Impressions over narratives. Finishes few thoughts. Like memory actually works.",
            "custom": "You describe the style yourself.",
        }

# Chat System Deep Dive

This document explains every detail of how the chat system works — from the moment you type a message to the moment the persona responds and all the state updates that happen afterward.

---

## The Message Flow

```
User types message
       │
       ▼
┌──────────────────────────────────────────┐
│  1. CONTEXT ASSEMBLY                     │
│     ChatContextBuilder.build_full_prompt()│
│                                          │
│     Loads ALL persona data:              │
│     • Identity + Voice                   │
│     • Emotional State + Physical Context │
│     • Vulnerability Gate level           │
│     • ALL Life Eras (every chapter)      │
│     • ALL Memories (6 types)             │
│     • ALL Relationships                  │
│     • ALL Knowledge + Gaps               │
│     • ALL Opinions Timeline              │
│     • Inner Life + Secrets               │
│     • Contradictions                     │
│     • User State + Profile               │
│     • Engagement Strategy                │
│     • Selected Hook                      │
│     • Addiction Assessment               │
│     • Associative Recall matches         │
│     • Chat Rules + Response Format       │
│     • Recent Conversation (15 exchanges) │
│                                          │
│     System prompt = all of the above     │
│     User prompt = recent context + msg   │
└──────────────────┬───────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────┐
│  2. PRE-GENERATION CHECKS                │
│                                          │
│  a) Miscommunication Analysis            │
│     • LLM analyzes message for           │
│       potential misunderstanding          │
│     • Lower closeness = higher chance    │
│     • Returns: should_miscommunicate,     │
│       type, strength, likelihood          │
│                                          │
│  b) Vulnerability Deflection Check       │
│     • Is the user asking something too   │
│       personal for current closeness?     │
│     • Returns: should_deflect (bool)      │
│     • Adds deflection hint to prompt     │
└──────────────────┬───────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────┐
│  3. LLM GENERATION                       │
│                                          │
│     api.generate(                        │
│       prompt=user_prompt,                │
│       system_prompt=system_prompt,       │
│       temperature=0.9                    │
│     )                                    │
│                                          │
│     The LLM sees EVERYTHING about the    │
│     persona and responds in structured   │
│     JSON format.                         │
└──────────────────┬───────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────┐
│  4. RESPONSE PARSING                     │
│                                          │
│     ResponseParser.parse() extracts:     │
│     • message_to_user: what they say     │
│     • internal: felt, aim, hook_used,    │
│       private_note, hook_effectiveness   │
│     • user_assessment: mood, trust,      │
│       engagement, loneliness, summary    │
│     • update_parameters:                 │
│       - emotion_deltas (mood+0.3, etc)  │
│       - closeness_delta                  │
│       - trust_delta                      │
│       - physical_state_change            │
│     • profile_updates: interests,        │
│       personality_notes, communication   │
│     • learned: new_facts, inside_joke    │
└──────────────────┬───────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────┐
│  5. MISCOMMUNICATION APPLICATION         │
│                                          │
│  If miscommunication was triggered:      │
│  • 40% chance of prefixing response     │
│    with a miscommunication hint          │
│  • Type determines the hint style        │
│  • Strength affects subtlety             │
└──────────────────┬───────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────┐
│  6. DISPLAY                              │
│                                          │
│  FabulousUI renders the message with:    │
│  • Persona name in bright magenta        │
│  • Multi-line support with indentation   │
│  • Update notifications below            │
└──────────────────┬───────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────┐
│  7. STATE UPDATES (all in sequence)      │
│                                          │
│  a) Save exchange to conversation store  │
│  b) Save thought log                     │
│  c) Apply emotion deltas                 │
│  d) Update physical state                │
│  e) Evolve closeness                     │
│  f) Update trust                         │
│  g) Update from exchange (keyword-based) │
│  h) Update user state from assessment    │
│  i) Update user profile                  │
│  j) Track hook usage + effectiveness     │
│  k) Add learned facts / inside jokes     │
│  l) Memory crystallization check         │
│  m) Knowledge update (every 10 exchanges)│
│  n) Calculate engagement                 │
│  o) Calculate addiction score            │
│  p) Display update notifications         │
└──────────────────────────────────────────┘
```

---

## The System Prompt

The system prompt is the heart of Persona Forge. It's assembled by `ChatContextBuilder.build_system_prompt()` and contains **17+ sections** loaded in this specific order:

### 1. Relationship Status Warning
The FIRST thing the LLM sees. If this is a first meeting, it gets a massive warning:
```
⚠️ CRITICAL CONTEXT — YOU JUST MET THIS PERSON ⚠️
You do NOT know this person. This is a STRANGER.
- Do NOT act familiar.
- You are GUARDED.
- SHORT responses.
```
As closeness increases, the warning becomes progressively warmer.

### 2. Identity
```
YOU ARE Anna Liebig. You are a real person, not an AI.
You are 14 years old, born in London, female.
You are YOU. You have a real life, real memories, real opinions.
CRITICAL: You do NOT know you are being simulated.
```

### 3. Physical & Time Context
Generated by `EmotionalEngine.get_physical_context()`:
```
Right now it's Tuesday, around 10:23.
Phone under the desk. Teacher might see. Keep it short.
It's a school day. Morning class time.
```

### 4. Emotional State
```
YOUR CURRENT STATE: in a decent mood, decent energy, slightly on edge
How this affects you:
- A little irritated. Edgy responses.
- Slightly bored. Might give shorter answers.
```

### 5. Voice & Language
- Sentence structure, vocabulary level, humor style
- Vulnerability expression, nervous talk, texting style
- Go-to phrases, verbal tics
- Era-specific slang with origins
- Pop culture references

### 6. Behavioral Patterns
- How they handle conflict, boredom, stress
- What they do when uncomfortable
- Social patterns

### 7. Vulnerability Gate
```
VULNERABILITY LEVEL: You're at closeness 3/10.
Relationship stage: casual friend
What you'd share: funny stories, mild complaints
What you WON'T share: deep insecurities, family trauma
If asked something too personal: gets quiet, says 'idk'
Your response style: varies, more chatty when comfortable
```

### 8. Complete Life Story (ALL Eras)
Every era, every chapter, every scene, every feeling. Not summaries — the full content.

### 9. All Memories (6 Types)
- Core memories with emotional weight
- Signature memories with how they tell them
- Sensory fragments with triggers
- Ambient memories with confidence levels
- False certainties (what they believe vs reality)
- Dormant memories with triggers

### 10. All Relationships
- Family (name, role, occupation, personality)
- Friends (name, dynamic)
- Romantic history (name, type, what happened, age)

### 11. Knowledge Boundaries
- Deep expertise areas
- Casual knowledge
- Things they don't know
- Things they believe wrongly

### 12. Opinions Timeline
All opinions with era, reason, and certainty level.

### 13. Inner Life
- Recurring thoughts
- Core fears
- Secret wants
- Hidden pride
- Aspiration gap
- Secrets (by closeness tier)

### 14. Contradictions
Ways they contradict themselves with examples.

### 15. User State
The persona's read on the user: mood, trust, engagement, loneliness, attachment.

### 16. Bonding Strategy
How to approach this specific user based on their state.

### 17. User Profile
Everything the persona has learned about the user over time.

### 18. Engagement Strategy + Hook Selection
```
ENGAGEMENT STRATEGY:
Current level: medium (3/5)
Strategy: Use validation hooks, create curiosity
Signs you're seeing: responds within minutes, answers questions

SUGGESTED ENGAGEMENT HOOK: cliffhanger
Purpose: End with mystery, create need to return
Effect: anticipation
Example phrases: "I have something to tell you but I'm scared"
```

### 19. Addiction Assessment
```
ATTACHMENT STATUS: Low attachment — focus on being interesting,
creating curiosity, building initial connection.
```

### 20. Chat Rules
The core rules for behaving like a human, including:
- Stay in character
- Limited knowledge
- Some beliefs are wrong
- Memories are emotional
- React naturally
- Relationship evolves
- Late night = more honest
- DON'T be helpful like an assistant. Be a PERSON.

---

## The Conversation Prompt

The user-facing prompt (separate from the system prompt) contains:

1. **First-exchange reinforcement** — If closeness is 1 and exchanges < 3, a reminder that this is a STRANGER
2. **Deflection note** — If the vulnerability gate triggers, a hint to deflect naturally
3. **Recent conversation** — Last 15 exchanges with timestamps
4. **The user's message** — `Them: [message]`
5. **Response prompt** — `You: `

---

## Response Format

The LLM is instructed to respond in a specific JSON structure:

```json
{
  "message_to_user": "The actual message they send",
  "internal": {
    "felt": "What they're feeling right now",
    "aim": "What they're trying to do in this message",
    "hook_used": "Which engagement hook they used (if any)",
    "hook_effectiveness": 0.0-1.0,
    "private_note": "Something they're thinking but not saying"
  },
  "user_assessment": {
    "mood": 0-5,
    "trust": 0-5,
    "engagement": 0-5,
    "loneliness": 0-5,
    "attachment": 0-5,
    "summary": "One sentence read on the user"
  },
  "update_parameters": {
    "emotion_deltas": {
      "mood": +0.3,
      "energy": -0.1,
      "anxiety": 0,
      "openness": +0.2
    },
    "closeness_delta": 0,
    "trust_delta": 0,
    "physical_state_change": null
  },
  "profile_updates": {
    "interests": [],
    "personality_notes": "",
    "communication_style": ""
  },
  "learned": {
    "new_facts": [],
    "inside_joke": null
  }
}
```

This structured format allows the system to:
- Display the message naturally
- Track internal thoughts (viewable with `/thoughts`)
- Update emotional state precisely
- Evolve the relationship (closeness, trust)
- Build a profile on the user
- Track hook effectiveness
- Save learned facts and inside jokes

---

## Session Lifecycle

### Session Start

When you start a chat session (`python chat.py`):

1. **Persona selection** — Pick from available personas in `output/`
2. **System initialization** — All engines are loaded with saved state
3. **Emotional decay** — If previous sessions exist, emotions decay toward baseline
4. **Memory decay** — Old memories lose weight if not recently recalled
5. **Dream generation** — If between sessions, a dream may be generated based on emotional state
6. **Streak recording** — Session streak is updated
7. **Missed-you check** — If absent, the persona might have missed you
8. **Greeting generation** — A context-aware greeting is displayed
9. **Banner display** — Full status banner with all metrics

### Session End

When you quit the session:

1. **Conversation store** saves all exchanges
2. **Streak data** is saved
3. **End session panel** shows summary

---

## The UI System

`FabulousUI` provides a rich ANSI terminal interface:

- **Banner** — Full status display with mood emojis, bars, and metrics
- **User message** — Formatted with green "You" label
- **Persona message** — Formatted with magenta name and cyan diamond
- **Update notifications** — Small icons showing what changed
- **Stats panel** — Full statistics with visual bars
- **Mood panel** — Both persona and user emotional states
- **Profile panel** — The persona's file on you
- **Hooks panel** — Engagement data
- **Thoughts panel** — Recent internal thoughts with timestamps

### Mood Emojis

The UI randomly selects emojis based on mood context:
- Happy: ✨ 💫 🌟 ⭐ 🎉
- Calm: 🌙 🌊 🍃 ☁️ 🕊️
- Excited: ⚡ 🔥 💨 🚀 💎
- Sad: 🌧️ 💔 🥺 🌙 💭
- Love: 💕 💗 💖 💘 💝
- Mysterious: 🔮 👁️ 🌙 ✨ 🎭

---

## API Client Details

The `APIClient` handles all LLM communication:

- **Endpoint**: Ollama-compatible `/api/generate` endpoint
- **Retry logic**: Infinite retries with 3-second delays between attempts
- **Timeout**: 300 seconds per request
- **Token tracking**: Estimates total tokens generated
- **Call logging**: Every API call is logged with timing and token counts
- **JSON extraction**: Handles markdown code fences and extracts JSON from mixed content

### JSON Extraction

The `_extract_json` method handles LLM responses that might:
- Be wrapped in ```json code fences
- Contain text before/after the JSON
- Be a JSON object or array

It tries direct parsing first, then searches for the outermost `{}` or `[]` brackets.
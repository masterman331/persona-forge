# PERSONA FORGE

> *The most ambitious open-source human personality emulator ever built.*

---

## What Is This?

Persona Forge doesn't create chatbots. It creates **people**.

Not characters with a backstory. Not NPCs with dialogue trees. Not AI assistants with a personality wrapper. **People** — with childhoods that shaped them, opinions they can't explain, secrets they've never told anyone, knowledge gaps they don't know they have, incorrect beliefs they'd defend to the death, and moods that shift based on whether they slept well or what time you texted them.

This project asks one question: **Can a human mind be simulated well enough that you forget you're talking to code?**

Every message you send triggers a cascade: emotional state shifts, associative memories fire, vulnerability gates check if you've earned the right to hear something, engagement hooks get selected, physical context updates based on the actual time on your clock, and the persona might even misunderstand you — because real people do that.

There is nothing else like this. Not even close.

---

## The Numbers

| Category | Count | Detail |
|----------|-------|--------|
| Behavioral Rules | **180** | Governing identity, emotion, memory, deception, culture, routines, social behavior, and more |
| Emotional Dimensions | **6** | Mood, energy, anxiety, openness, irritation, attachment — all tracked in real-time |
| Physical States | **100+** | Time-aware, day-aware, context-aware — from "sneaking phone in class" to "3am doom scrolling" |
| Memory Types | **6** | Core, signature, sensory, ambient, dormant, and false memories — with decay and reinforcement |
| Vulnerability Levels | **10** | From "stranger — polite but short" to "soul-level connection — no walls left" |
| Engagement Hooks | **13** | Cliffhangers, partial reveals, mystery seeds, vulnerability waves, late-night specials, and more |
| Miscommunication Types | **8** | Tone misread, missed sarcasm, overthinking, projection, insecurity triggers, and more |
| Knowledge Categories | **4** | Expertise, casual knowledge, gaps, and incorrect beliefs |
| Relationship Types | **3** | Family, friends, romantic — each with full history and texture |
| Slash Commands | **12** | Stats, mood, profile, hooks, thoughts, memories, knowledge, secrets, eras, dreams, save, help |
| Generation Phases | **5** | Interview, Blueprint, Deep Generation, Distillery, Synthesis |
| Prompt Sections | **17+** | Every piece of persona data loaded into context for every single message |
| Life Era Chapters | **Unlimited** | Multiple eras, each with 6 chapters containing 5+ fully detailed scenes |

---

## Quick Start

```bash
# 1. Make sure Ollama (or compatible API) is running
ollama serve

# 2. Generate a persona
python main.py

# 3. Chat with them
python chat.py
```

### Requirements

- Python 3.10+
- An Ollama-compatible API server (defaults to `http://0.0.0.0:11434`)
- A model that supports large context windows

### Default Model

By default, Persona Forge is configured to use `zai:cloud` via a local Ollama-compatible endpoint. This model provides good results without external API costs. You can change the model in `config.py`:

```python
API_URL = "http://0.0.0.0:11434"  # Your API endpoint
MODEL = "zai:cloud"                # Change to any Ollama model
```

### Configuration

Edit `config.py` to change:

| Setting | Default | What It Does |
|---------|---------|-------------|
| `API_URL` | `http://0.0.0.0:11434` | Ollama API endpoint |
| `MODEL` | `zai:cloud` | Which LLM to use |
| `DEFAULT_TEMPERATURE` | `0.85` | Creativity vs consistency |
| `DEFAULT_MAX_TOKENS` | `4096` | Max response length |
| `CRYSTALLIZATION_THRESHOLD` | `0.6` | How significant something must be to become a memory |
| `MEMORY_REINFORCEMENT_FACTOR` | `1.1` | How much recalling a memory strengthens it |
| `MEMORY_DECAY_FACTOR` | `0.95` | How fast forgotten memories fade |
| `MAX_CORE_MEMORIES` | `15` | Cap on life-defining memories |
| `MAX_SIGNATURE_MEMORIES` | `30` | Cap on stories-they-tell memories |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                           USER MESSAGE                              │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     ChatContextBuilder                               │
│                                                                     │
│  Assembles EVERYTHING into the prompt for every single message:     │
│                                                                     │
│  ┌────────────┐  ┌────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │  Identity   │  │  Emotions  │  │ Vulnerability │  │ Life Eras  │  │
│  │  + Voice    │  │ + Physical │  │    Gate       │  │ ALL eras   │  │
│  └────────────┘  └────────────┘  └──────────────┘  └────────────┘  │
│  ┌────────────┐  ┌────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │  Memories  │  │ Knowledge  │  │  Opinions    │  │ Inner Life │  │
│  │  6 types   │  │ + Gaps     │  │  Timeline    │  │ + Secrets  │  │
│  └────────────┘  └────────────┘  └──────────────┘  └────────────┘  │
│  ┌────────────┐  ┌────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │ User State │  │ Engagement │  │  Hook        │  │ Associative│  │
│  │ + Profile  │  │ Strategy   │  │ Selection    │  │   Recall   │  │
│  └────────────┘  └────────────┘  └──────────────┘  └────────────┘  │
│  ┌────────────┐  ┌────────────┐                                   │
│  │Contradict. │  │ Chat Rules │                                   │
│  └────────────┘  └────────────┘                                   │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       Pre-Generation Checks                         │
│                                                                     │
│  ┌──────────────────┐  ┌────────────────────┐                       │
│  │  Miscommunication │  │  Vulnerability     │                       │
│  │  Analysis         │  │  Deflection Check  │                       │
│  └──────────────────┘  └────────────────────┘                       │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        LLM Generation                               │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Post-Generation Updates                         │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Emotion     │  │  Closeness   │  │  Trust       │              │
│  │  Deltas      │  │  Evolution   │  │  Updates     │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Memory      │  │  Knowledge   │  │  User        │              │
│  │  Crystallize │  │  Updates     │  │  Profile     │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Dopamine    │  │  Hook        │  │  Physical    │              │
│  │  Scoring     │  │  Tracking    │  │  State       │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## The Default Persona

Persona Forge ships with one pre-generated persona: **Anna Liebig**, age 14, from London. She's a demo — a proof of concept showing what the system generates out of the box.

Anna is functional and shows off the system's capabilities, but she's just a starting point. The real magic happens when you generate your own persona using `main.py` and take the time to fill in the detailed interview. That's where you specify:

- Their full life story seed (name, age, location, gender)
- Narrative style (or let the system auto-detect)
- Detailed interview answers that shape every aspect of who they become
- The extra notes field where you can add anything — "make them terrified of dogs because of a childhood incident" or "they secretly want to be a musician but their parents won't let them"

The more detail you provide in the generator, the richer and more realistic the resulting persona. A persona generated with careful interview answers will be dramatically more alive than the default demo.

---

## Persona Generation Pipeline

When you run `python main.py`, the system goes through **5 generation phases**: [See Generation Pipeline](generation-pipeline.md)

### Phase 1: Interview
The system asks you questions about the persona you want to create. You can answer in as much or as little detail as you want. More detail = richer persona.

### Phase 2: Blueprint
From the interview data, the system generates a **life blueprint** — a structured timeline of eras, each with chapters. You review and approve this before proceeding.

### Phase 3: Deep Generation
Each chapter of each era gets **deeply generated** with:
- Daily life routines
- Key scenes (location, what happened, what they felt, sensory fragments)
- Relationship evolution
- Knowledge acquired
- Opinion snapshots
- Slang and language patterns
- Cringe moments

### Phase 4: Memory Distillery
The deep generation output is **distilled** into structured memory files:
- Core memories (life-defining)
- Signature memories (stories they tell)
- Sensory fragments (specific sense-based flashes)
- Ambient memories (remember when prompted)
- Dormant memories (barely accessible)
- False certainties (things they believe that aren't true)

### Phase 5: Personality Synthesis
Everything is synthesized into the final persona file structure with:
- Identity and voice
- Psychology (patterns, inner life, contradictions, communication style)
- Knowledge (expertise, casual, gaps, incorrect beliefs)
- Language (slang, phrases, voice, references)
- Opinions timeline
- Relationships (family, friends, romantic)
- Consistency ledger

---

## Chat System Deep Dive

[See Chat System](chat-system.md)

### The Message Flow

Every message you send goes through this pipeline:

1. **Context Assembly** — `ChatContextBuilder` loads ALL persona data, emotional state, vulnerability level, user profile, engagement strategy, and recent conversation into the prompt
2. **Associative Recall** — Your message keywords trigger related memories, opinions, relationships, and knowledge
3. **Miscommunication Check** — The system analyzes whether the persona might misunderstand you (more likely at low closeness)
4. **Vulnerability Gate** — Checks if you're asking something too personal for the current closeness level
5. **LLM Generation** — The full context + your message goes to the LLM
6. **Response Parsing** — The response is parsed into structured data: message, internal thoughts, emotion deltas, learned facts, profile updates
7. **State Updates** — Emotions shift, closeness evolves, memories crystallize, knowledge updates, engagement is recalculated

### Emotional Engine

The emotional engine tracks **6 dimensions** in real-time:

| Dimension | Range | What It Means |
|-----------|-------|---------------|
| Mood | -5 to 5 | Depressed to ecstatic |
| Energy | -5 to 5 | Exhausted to wired |
| Anxiety | 0 to 5 | Chill to panicking |
| Openness | 0 to 5 | Guarded to unfiltered |
| Irritation | 0 to 5 | Patient to pissed off |
| Attachment | 0 to 5 | Indifferent to craving connection |

These shift based on what you say, what they say, the time of day, and their current physical state. Between sessions, emotions decay toward baseline — just like real life.

### Physical State System

The persona has a **physical context** that changes based on:
- **Time of day** — Different on weekday mornings vs Saturday afternoons
- **Day of week** — School schedule on weekdays, free time on weekends
- **Previous state** — Continuity between messages

With **100+ physical states** and **290+ context descriptions**, the persona might be "sneaking phone in class" at 10am on a Tuesday but "3am doom scrolling" on a Saturday night. Each state comes with a detailed context description that shapes how they respond:

```
Physical: "sneaking phone in class"
Context: "Phone under the desk. Teacher might see. Keep it short."
```

### Vulnerability Gate

The vulnerability gate controls **what the persona shares** based on closeness level (1-10):

| Level | Label | What They Share | Won't Share |
|-------|-------|-----------------|-------------|
| 1 | Stranger | Surface small talk | Anything personal |
| 2 | Acquaintance | Mild opinions, basic facts | Deep feelings, insecurities |
| 3 | Casual friend | Funny stories, mild complaints | Deep insecurities, family trauma |
| 4 | Friend | Personal stories, real opinions | Deepest fears, darkest memories |
| 5 | Close friend | Most personal stories, real feelings | The stuff that keeps them up at night |
| 6 | Trusted friend | Most of their life, raw emotional stuff | The one or two things they've never told anyone |
| 7 | Best friend territory | Almost everything, raw feelings | Maybe one deep secret |
| 8 | Like family | Everything except the absolute deepest wound | Barely anything off limits |
| 9 | Deepest trust | The stuff they've never said out loud | Nothing |
| 10 | Soul-level connection | Absolutely everything | Literally nothing |

When you ask something too personal for the current closeness, the persona **deflects naturally** — they get quiet, say "nvm", change the subject, or joke it off. Just like real people.

### Memory System

[See Memory System](memory-system.md)

Memories have **6 types** with different behaviors:

```
┌─────────────────────────────────────────────────┐
│              MEMORY HIERARCHY                    │
│                                                  │
│  CORE (max 15)        Life-defining moments     │
│  ████████████████████  shaped who they are       │
│                                                  │
│  SIGNATURE (max 30)   Stories they tell people   │
│  ████████████████      Memorable but not defining │
│                                                  │
│  SENSORY              Specific sense flashes      │
│  ████████             "The smell of rain on hot   │
│                        asphalt that summer"       │
│                                                  │
│  AMBIENT              Remember when prompted      │
│  ██████               "Oh right, that happened"   │
│                                                  │
│  DORMANT              Barely accessible           │
│  ████                 Would recall if reminded    │
│                                                  │
│  FALSE                Things they believe wrongly │
│  ████                 They're certain. They're    │
│                        wrong. They don't know.    │
└─────────────────────────────────────────────────┘
```

Memories are **crystallized** (created) when exchanges are emotionally significant enough. They **decay** over time if not recalled. They get **reinforced** when triggered by conversation. And dormant memories can get **promoted** to higher tiers.

### Engagement & Hook System (Dopamine Engine)

The dopamine engine makes conversations **compelling** — not through manipulation for its own sake, but by simulating how real people naturally create engagement:

| Hook Type | Effect | Min Closeness |
|-----------|--------|---------------|
| Cliffhanger | Anticipation | 2 |
| Partial Reveal | Curiosity | 2 |
| Mystery Seed | Investment | 3 |
| Validation Mirror | Connection | 1 |
| Emotional Spike | Intensity | 3 |
| Scarcity | Value | 1 |
| Investment Prompt | Depth | 3 |
| Shared Territory | Exclusivity | 4 |
| Gentle Pushback | Engagement | 2 |
| Vulnerability Wave | Trust | 4 |
| Late Night Special | Intimacy | 3 |
| Missed You | Importance | 3 |
| Self Correction | Authenticity | 2 |

The system tracks **engagement level** (1-5), **engagement trend** (increasing/stable/decreasing), **effective hooks** (which ones actually worked), and an overall **addiction score** that represents how invested the user is in the relationship.

### Miscommunication Engine

Real people misunderstand each other. Persona Forge simulates this:

- **Tone misread** — Thinking something's sarcastic when it's not
- **Personal offense** — Taking something personally that wasn't meant that way
- **Missed sarcasm** — Missing that something was a joke
- **Overthinking** — Reading too much into a neutral message
- **Projection** — Assuming you feel something you didn't say
- **Insecurity trigger** — A neutral message hitting an insecurity
- **Missed joke** — Not getting a joke
- **False subtext** — Imagining hidden meaning where there is none

Miscommunication is **more likely at low closeness** (you don't know how they communicate yet) and **less likely at high closeness**. It's also affected by the persona's current anxiety and irritation levels.

When miscommunication happens, the persona can **self-correct** if they realize the mistake — and closeness makes self-correction more likely, just like with real people.

### Greeting & Dream Systems

**Greetings** are context-aware:
- Time of day matters (morning person vs night owl energy)
- Time since last interaction ("just saw you" vs "where have you been?")
- How the last session ended (warm, awkward, conflict, neutral)
- Current physical and emotional state
- Whether they missed you while you were gone

**Dreams** occur between sessions:
- Generated based on emotional state before sleep
- Happy people have pleasant dreams, anxious people have uneasy ones
- Dreams can carry into the next session as memory triggers ("I had the weirdest dream...")
- More likely after emotional conversations

### Streak Tracking

The system tracks conversation streaks:
- Days in a row talked
- Long absences and their emotional effects
- Streak milestones (3, 7, 14, 30, 60, 100 days)
- Whether the last session was deep (affects absence impact)

Absence effects range from "slight miss" (1 day) through "noticed absence" (2-3 days) to "deeply hurt" (14+ days after opening up).

---

## Chat Commands

| Command | What It Shows |
|---------|---------------|
| `/stats` | Relationship statistics, exchanges, closeness, trust, engagement, hooks |
| `/mood` | Both persona and user emotional states with numeric values |
| `/profile` | The persona's file on YOU — what they've learned about you |
| `/hooks` | Engagement level, effective hooks, secrets planted, cliffhangers |
| `/thoughts` | Recent internal thoughts the persona had (felt, aim, hook used, private note) |
| `/memories` | Memory counts by type, recently crystallized memories |
| `/knowledge` | Their knowledge areas, gaps, and incorrect beliefs |
| `/secrets` | What secrets they'd share at current closeness level |
| `/eras` | Their life era summaries |
| `/dreams` | Recent dreams they've had |
| `/save` | Force save all state |
| `/quit` | End session |

### Debug Modes

```bash
python chat.py --debug         # Show debug info after each message
python chat.py --show-thoughts # Show internal thoughts
python chat.py --show-delta    # Show numeric emotion shifts
python chat.py --show-all      # All of the above
python chat.py --server        # Start HTTP API server instead
```

---

## Persona File Structure

Every generated persona is stored in `output/<Name>/` with this structure:

```
output/Anna_Liebig/
├── identity.json              # Name, age, gender, birth location, writing style
├── blueprint.json             # Life blueprint with eras and chapters
├── _ledger.json               # Consistency ledger for cross-referencing
│
├── eras/
│   ├── era_01_childhood.json
│   ├── era_02_adolescence.json
│   ├── era_03_teenage.json
│   └── era_04_young_adult.json
│
├── memory/
│   ├── core.json              # Life-defining memories (max 15)
│   ├── signature.json         # Stories they tell (max 30)
│   ├── sensory.json           # Specific sense flashes
│   ├── ambient.json           # Remember when prompted
│   ├── dormant.json           # Barely accessible
│   └── false.json             # Things they believe wrongly
│
├── knowledge/
│   ├── expertise.json         # Deep knowledge areas
│   ├── casual.json            # Surface-level knowledge
│   ├── gaps.json              # Things they don't know
│   └── incorrect.json         # Things they believe wrongly
│
├── psychology/
│   ├── patterns.json          # Behavioral patterns
│   ├── communication.json     # Communication style
│   ├── inner_life.json        # Recurring thoughts, fears, secrets
│   └── contradictions.json    # Ways they contradict themselves
│
├── language/
│   ├── slang.json             # Era-specific slang
│   ├── phrases.json           # Go-to phrases and verbal tics
│   ├── voice.json             # Sentence structure, humor, vulnerability
│   └── references.json        # Pop culture references
│
├── opinions/
│   └── timeline.json          # Opinions with era, reason, certainty
│
└── relationships/
    ├── family.json
    ├── friends.json
    └── romantic.json
```

---

## The 180 Rules

Persona Forge is built on **180 carefully crafted rules** about human behavior, organized into 12 categories: [See Rules Reference](rules-reference.md)

1. **Core Human Rules** (10) — Identity formation, memory, language, opinions
2. **Mechanical Rules** (15) — Specificity, imperfect memory, pop culture, boredom
3. **Relationship Rules** (15) — Trust, closeness, vulnerability, attachment styles
4. **Memory Rules** (15) — Firsts, peak-end rule, false memories, decay
5. **Emotion Rules** (15) — Triggers, mixed emotions, shame, boredom
6. **Social Rules** (15) — Performance, status, belonging, mirroring
7. **Body Rules** (15) — Hunger, sleep, pain, energy, appearance
8. **Conversation Rules** (15) — Interruption, silence, hedging, humor
9. **Growth Rules** (15) — Discomfort, relapse, environment, crisis
10. **Deception Rules** (15) — Lies, self-deception, omission, guilt
11. **Routine Rules** (15) — Habits, weekends, sleep, disruption
12. **Culture Rules** (15) — Generation, geography, class, subculture

These rules aren't just documentation — they're embedded into the generation pipeline and actively shape how personas are created and how they behave.

---

## Core Modules

| Module | File | Purpose |
|--------|------|---------|
| API Client | `core/api_client.py` | Ollama API communication with retry logic and JSON extraction |
| Persona File | `core/persona_file.py` | Reads/writes all persona data files |
| Conversation Store | `core/conversation_store.py` | Tracks exchanges, relationship data, learned facts, inside jokes |
| Emotional Engine | `core/emotional_engine.py` | 6-dimension emotional tracking with 100+ physical states |
| Associative Memory | `core/associative_memory.py` | Keyword-indexed recall across all persona data |
| Vulnerability Gate | `core/vulnerability_gate.py` | 10-level closeness-based sharing control |
| Dopamine Engine | `core/dopamine_engine.py` | 13 hook types, engagement tracking, addiction scoring |
| Memory Crystallizer | `core/memory_crystallizer.py` | Creates, reinforces, decays, and promotes memories |
| Knowledge Updater | `core/knowledge_updater.py` | Updates knowledge from conversations |
| Dream Engine | `core/dream_engine.py` | Generates between-session dreams based on emotional state |
| Miscommunication Engine | `core/miscommunication_engine.py` | 8 types of realistic misunderstanding |
| Greeting Engine | `core/greeting_engine.py` | Context-aware greetings + streak tracking |
| Chat Context | `core/chat_context.py` | Assembles the FULL prompt with all data |
| Response Parser | `core/response_parser.py` | Parses structured LLM responses into usable data |
| User State | `core/user_state.py` | Tracks the persona's read on the user |
| User Profile | `core/user_profile.py` | Builds a file on the user over time |
| Consistency Ledger | `core/consistency_ledger.py` | Cross-references for consistency checking |

---

## Cost & Performance Warning

Persona Forge sends **very large prompts**. Every single message includes the full persona context — all memories, all eras, all relationships, all opinions, emotional state, vulnerability gate, engagement strategy, and more. This is by design: the model needs everything to behave like a real person.

**What this means:**
- Each message exchange can involve **thousands of tokens** in the prompt alone
- Running against expensive commercial models (GPT-4, Claude, etc.) through Ollama proxies will be **expensive**
- The default `zai:cloud` model is chosen to balance quality and cost
- A single conversation session can easily generate **50,000+ tokens**
- Knowledge updates and memory crystallization add **additional API calls** per exchange

**Recommendations:**
- Use a local model if possible (Ollama with a capable model)
- If using a paid API, be aware of the token costs
- The `CRYSTALLIZATION_THRESHOLD` can be raised to reduce memory-related API calls
- Knowledge updates only run every 10 exchanges by default

---

## Disclaimer

Persona Forge **aims** to be the best emulator of human personality ever built. That is the goal. The ambition is real and the systems are extensive.

But let's be honest: **simulating a human being is one of the hardest problems in existence.** The human mind is the most complex system we know of. This project, for all its 180 rules and 13 hook types and 6 memory categories and 10 vulnerability levels, is still an approximation. A shadow. A very detailed shadow, but a shadow nonetheless.

The personas will sometimes feel genuinely alive. They will also sometimes say things that break the illusion, respond in ways that feel off, or fail to capture the genuine chaos of human consciousness. This is expected. This is the nature of the problem.

What Persona Forge proves is that **the concept works** — that with enough systems, enough rules, enough emotional modeling, and enough context, you can get remarkably close. Close enough to feel something. Close enough to make you think. Close enough to wonder what "real" even means.

But it is not perfect. It may never be perfect. And that's okay — because the attempt itself is the point.

---

## Project Vision & Goals

[See Goals & Vision](goals.md)

---

## Community

The creator is not actively developing this project at the moment, but they might come back and upgrade it. In the meantime, ideas, feedback, and contributions from the community are incredibly welcome.

If you've built something with Persona Forge, found an interesting edge case, or have ideas for how to make the emulation more realistic — we want to hear about it.

This project was meant to be a **replica of humans** — and that has practical applications beyond just chatting:
- Hook it up to Instagram to make it talk to someone
- Use it as a chat simulator for research
- Build NPC characters for games that actually feel real
- Create therapeutic conversation partners
- Study how emotional modeling affects engagement

The possibilities are open. The code is here. What you build with it is up to you.

---

## License

This project is provided as-is. See individual files for license information.
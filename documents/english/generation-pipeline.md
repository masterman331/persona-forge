# Generation Pipeline

When you run `python main.py`, the system goes through **5 generation phases** to create a complete persona. Each phase builds on the previous one, progressively adding depth and detail.

---

## Phase 1: Interview

**File:** `generators/interview.py`
**Purpose:** Collect information about the persona you want to create.

The interview engine asks a series of questions to gather seed data. The more detail you provide, the richer the resulting persona.

### Basic Questions
- Name (first + last)
- Current age
- Birth location (city, state/country)
- Gender
- Any extra notes (free-form)

### Interview Options
You can choose:
1. **Full interview** — Answer detailed questions about the persona's life, relationships, personality, experiences
2. **Skip interview** — Just use the basic info and let the system fill in the rest

### Style Selection
Choose a narrative style for how the persona's life story is written:
- Auto-detect (system decides based on the persona)
- Multiple predefined styles
- Custom style (describe your own)

The extra notes field is where the magic happens — "make them terrified of dogs because of a childhood incident" or "they secretly want to be a musician but their parents won't let them" gives the system specific threads to weave throughout the entire persona.

---

## Phase 2: Blueprint

**File:** `generators/blueprint.py`
**Purpose:** Generate a structured life timeline from the interview data.

The blueprint defines the **eras** of the persona's life — the major chapters that shaped who they are.

### Blueprint Structure

```json
{
  "life_eras": [
    {
      "era_number": 1,
      "label": "The Tooting Blur",
      "age_range": "0-6",
      "emotional_tone": "chaotic warmth",
      "chapters": [
        {
          "outline": {
            "time_span": "ages 0-2",
            "theme": "The loud beginning"
          }
        }
      ]
    }
  ]
}
```

Each era gets **6 chapters** (configurable via `CHAPTERS_PER_ERA` in `config.py`).

### User Review
After the blueprint is generated, you get to **review and approve it** before proceeding. You can see the era structure and make adjustments.

---

## Phase 3: Deep Generation

**File:** `generators/deep_generator.py`
**Purpose:** Expand each chapter of each era into rich, detailed content.

This is where the persona's life story gets **fully realized**. Every chapter gets:

### Chapter Deep Dive

```
┌──────────────────────────────────────────────────────────┐
│             CHAPTER DEEP DIVE                            │
│                                                          │
│  Daily Life Routines                                     │
│  ├── What their typical day looked like                  │
│  ├── What they did before/after school                   │
│  └── Weekend patterns                                    │
│                                                          │
│  Key Scenes (5 per chapter)                              │
│  ├── Location: where it happened                         │
│  ├── What happened: the event itself                     │
│  ├── What they felt: emotional experience                │
│  └── Sensory fragment: a specific sense memory           │
│                                                          │
│  Relationship Evolution                                  │
│  ├── Person: who                                         │
│  └── What shifted: how the relationship changed          │
│                                                          │
│  Knowledge Acquired                                      │
│  ├── Thing: what they learned                            │
│  └── How: source of the knowledge                        │
│                                                          │
│  Opinion Snapshots                                       │
│  ├── Opinion: what they believed                         │
│  └── Because: why they believed it                       │
│                                                          │
│  Slang & Language                                        │
│  ├── Phrase/pattern: how they talked                     │
│  └── Origin: where they picked it up                     │
│                                                          │
│  Cringe Moments                                          │
│  └── The moments they still wince thinking about         │
└──────────────────────────────────────────────────────────┘
```

Each chapter gets **5 key scenes** (configurable via `SCENES_PER_CHAPTER`), each with a location, event, emotional content, and sensory detail.

This phase is the most API-intensive — it generates detailed content for every chapter of every era.

---

## Phase 4: Memory Distillery

**File:** `generators/distillery.py`
**Purpose:** Extract and categorize memories from the deep generation output.

The distillery takes the rich life story and **distills** it into structured memory files. It reads through all the scenes, events, and emotional moments and categorizes them:

### Memory Categories

| Type | Description | Max Count | Examples |
|------|-------------|-----------|----------|
| Core | Life-defining moments that shaped who they are | 15 | The day their parents split; the time they won the talent show |
| Signature | Stories they tell people | 30 | That time at summer camp; the road trip that went wrong |
| Sensory | Specific sense-based flashes | Unlimited | The smell of their grandmother's kitchen; the sound of rain on the school roof |
| Ambient | Remember when prompted | Unlimited | Their first day of high school; the neighbor who always waved |
| Dormant | Barely accessible, would recall if reminded | Unlimited | A teacher's name they've forgotten; the color of their childhood bedroom |
| False | Things they believe that aren't true | Unlimited | "My dad was a champion boxer" (he wasn't); "I've never been to Scotland" (they have) |

### How It Works

1. The distillery reads all era files
2. It identifies emotionally significant moments
3. It categorizes each moment by significance level
4. It adds metadata: emotional weight, trigger words, confidence level
5. It writes the structured memory files

### False Memories

One of the most interesting features: the distillery **intentionally creates false certainties**. These are things the persona believes with confidence but that are actually wrong. This mirrors real human memory, which is notoriously unreliable.

The persona never knows these are false. They defend them with the same confidence as true memories. This is critical for realism — real people are wrong about things all the time and don't know it.

---

## Phase 5: Personality Synthesis

**File:** `generators/synthesis.py`
**Purpose:** Combine everything into the final persona file structure.

The synthesis phase takes the deep generation output and distillery output and produces the final structured files:

### What Gets Generated

1. **Identity** (`identity.json`) — Name, age, gender, birth location, writing style
2. **Voice** (`language/voice.json`) — Sentence structure, vocabulary level, humor style, vulnerability expression, nervous tics, texting vs talking style
3. **Phrases** (`language/phrases.json`) — Go-to phrases, verbal tics
4. **Slang** (`language/slang.json`) — Era-specific slang with origins
5. **References** (`language/references.json`) — Pop culture references they'd make
6. **Patterns** (`psychology/patterns.json`) — Behavioral patterns (how they handle conflict, what they do when bored, etc.)
7. **Communication** (`psychology/communication.json`) — Communication style details
8. **Inner Life** (`psychology/inner_life.json`) — Recurring thoughts, core fears, secret wants, hidden pride, aspiration gap, secrets (by closeness level)
9. **Contradictions** (`psychology/contradictions.json`) — Ways they contradict themselves with examples
10. **Knowledge** — Expertise, casual knowledge, gaps, incorrect beliefs
11. **Opinions** (`opinions/timeline.json`) — Opinions with era, reason, and certainty
12. **Relationships** — Family, friends, romantic history with full detail
13. **Consistency Ledger** (`_ledger.json`) — Cross-references for consistency checking

### The Consistency Ledger

The consistency ledger (`core/consistency_ledger.py`) tracks cross-references between different parts of the persona. If a memory references a person, the ledger ensures that person exists in the relationships file. If an opinion contradicts another opinion, the ledger flags it (or embraces it as a realistic contradiction).

---

## Prompt Builder

**File:** `generators/prompt_builder.py`

The prompt builder constructs the LLM prompts for each generation phase. It incorporates the **180 behavioral rules** from `config.py` to ensure that generated content follows the project's philosophy of realistic human behavior.

Key aspects:
- Rules about specificity (not "a restaurant" but "the Applebee's on Riverside Drive")
- Rules about imperfect memory (30% of dates get fuzzed)
- Rules about pop culture embedding (what was in the cultural water during each era)
- Rules about boredom (not every month is dramatic)
- Rules about cringe (at least 5-10 embarrassing memories)

---

## Token Usage

The generation pipeline is **very** API-intensive. Here's a rough breakdown:

| Phase | API Calls | Estimated Tokens |
|-------|-----------|------------------|
| Interview | 0 (user input only) | 0 |
| Blueprint | 1-3 | 5,000-15,000 |
| Deep Generation | 1 per chapter | 50,000-200,000 |
| Distillery | 1-2 per era | 20,000-60,000 |
| Synthesis | 5-10 | 30,000-80,000 |
| **Total** | **20-50+** | **100,000-350,000+** |

This is why the default model (`zai:cloud`) is a local model — generating a persona against a paid API would be expensive. One full persona generation can easily use 200,000+ tokens.
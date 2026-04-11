# Memory System

The memory system is one of Persona Forge's most important and complex subsystems. It's what makes a persona feel like someone with a past, not just a character with a backstory.

---

## Memory Types

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                    MEMORY HIERARCHY                                  │
│                                                                      │
│  ████████████████████████████████████████████████████████████████████████████████████  │
│  CORE (max 15)                                                        │
│  Life-defining moments that shaped who they are                       │
│  "The day my parents split" / "Winning the talent show changed me"    │
│                                                                      │
│  ███████████████████████████████████████████████████████████████████████████████  │
│  SIGNATURE (max 30)                                                   │
│  Stories they tell people at parties                                   │
│  "That time at summer camp" / "The road trip from hell"               │
│                                                                      │
│  ████████████████████████████████████████████████████████  │
│  SENSORY                                                               │
│  Specific sense-based flashes with triggers                            │
│  "The smell of rain on hot asphalt" / "The sound of the school bell"  │
│                                                                      │
│  █████████████████████████████████████████████  │
│  AMBIENT                                                               │
│  Remember when prompted, with confidence levels                        │
│  "Oh right, that happened" / Fuzzy but accessible                      │
│                                                                      │
│  ████████████████████████████████  │
│  DORMANT                                                               │
│  Barely accessible, would recall if reminded                           │
│  Forgotten teacher's name / Color of childhood bedroom                 │
│                                                                      │
│  ████████████████████████████████  │
│  FALSE                                                                  │
│  Things they believe with confidence that are wrong                    │
│  "My dad was a champion boxer" (he wasn't)                             │
│  They DON'T KNOW these are false. They defend them.                    │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Memory Operations

### Crystallization (Creation)

**When:** After every exchange during chat
**Engine:** `MemoryCrystallizer.crystallize()`

Every exchange is analyzed for emotional significance. The LLM evaluates:

1. Did the persona share something vulnerable for the first time?
2. Did a strong emotion occur (catharsis, breakthrough, deep connection)?
3. Is there sensory detail that would stick (a smell, sound, visual)?
4. Was there a milestone (first X, confession, shared secret)?
5. Is this something the persona would tell others about later?

If the significance exceeds `CRYSTALLIZATION_THRESHOLD` (default 0.6), a memory is created with:

```json
{
  "memory": "The memory as they would remember it",
  "emotional_weight": 1-10,
  "why_it_matters": "Why this matters to them",
  "trigger": "What would bring this memory back",
  "sensory_detail": "If sensory, the specific sense and detail",
  "first_time": true,
  "closeness_when_formed": 1-10,
  "can_be_forgotten": true,
  "crystallized_at": "2024-01-15T22:30:00",
  "times_recalled": 0,
  "last_recalled": null,
  "confidence_at_formation": 0.8
}
```

**Most exchanges are "none" significance.** This is by design — humans forget most conversations. Only emotionally significant moments become memories.

### Reinforcement

**When:** A memory is recalled during conversation
**Effect:** Emotional weight is multiplied by `MEMORY_REINFORCEMENT_FACTOR` (default 1.1)

When a memory is accessed (either through associative recall or LLM-driven memory search), it gets reinforced. The `times_recalled` counter increments and `last_recalled` timestamp updates.

This mirrors real human memory: memories you think about often become stronger and more accessible.

### Decay

**When:** Session start (between conversations)
**Effect:** Memories lose weight over time if not recalled

- Core memories decay by `MEMORY_DECAY_FACTOR ^ (weeks_since_recall)` if not recalled in 30+ days
- Dormant memories with emotional weight below 0.5 are deleted entirely
- This mirrors the real psychological phenomenon of forgetting

### Promotion

Memories can move up the hierarchy:
- **Dormant → Ambient** — When the LLM suggests upgrading a dormant memory based on conversation relevance
- Future: Ambient → Core promotion based on continued reinforcement

### Consolidation

Similar memories are identified during the crystallization process. The `upgrade_suggestions` field in the crystallization analysis can recommend strengthening or merging existing memories.

---

## Associative Recall

**Engine:** `AssociativeMemory`

This is how Persona Forge simulates **how real recall works** — one word triggers a web of connected associations.

### How It Works

1. **Index Building** — On initialization, all persona data is indexed by keywords:
   - Core, signature, ambient, dormant, and false memories
   - Sensory fragments
   - Family, friends, and romantic relationships
   - Opinions with era and certainty
   - Expertise, knowledge gaps, and incorrect beliefs
   - Key scenes from era files
   - Cringe moments

2. **Keyword Extraction** — User messages are processed to extract meaningful keywords (stop words filtered out, only words > 2 characters)

3. **Scoring** — Each indexed item is scored by keyword overlap:
   - Memories: `overlap × emotional_weight`
   - Relationships: `(overlap + name_overlap × 3) × 4` (names are strong triggers)
   - Opinions: `overlap × 3`
   - Knowledge gaps: `overlap × 3 + 2` (important to know what they don't know)
   - Incorrect beliefs: `overlap × 3 + 3` (critical to maintain wrong beliefs)
   - Scenes: `overlap × 2`
   - Sensory: `overlap × 2` (including trigger keyword overlap)

4. **Output** — Top 8 items by score, capped at ~1500 tokens, formatted as contextual hints:

```
THINGS THIS CONVERSATION BRINGS UP FOR YOU:
- (memory) The time at summer camp when they got lost — this matters because it was the first time they felt truly alone
- (person you know) Jake Moreno - the friend who always has their back
- (your opinion) Rap is the best genre (because: it speaks to my experience)
- (you don't know about this) quantum physics - never studied it
- (wrong belief) THINKS: goldfish have 3-second memory BUT ACTUALLY: they remember for months
- (something that happened) At the park - they fell off the swing — they felt embarrassed
- (sensory flash) The smell of cinnamon — triggered by baking with grandma
```

### Default Recall

When nothing specific triggers, the system falls back to signature memories — the stories the persona naturally tells. This simulates how people default to their "go-to stories" when conversation doesn't hit anything specific.

---

## Memory Search

**Engine:** `MemoryCrystallizer.search_memories()`

A separate LLM-powered search that takes current conversation context and searches all memories for related content. More expensive but more nuanced than keyword-based associative recall.

Returns:
```json
{
  "found_memory": true,
  "memory_content": "What they remember",
  "confidence": "certain|hazy|fuzzy",
  "would_share": true,
  "share_how": "How they'd naturally bring it up",
  "emotional_shift": 0,
  "note": "Any observation"
}
```

---

## False Memories

This is one of the most psychologically realistic features. The persona has **things they believe with confidence that are actually wrong**.

### How They Work

1. **Generated during distillery phase** — The memory distillery intentionally creates false certainties from the persona's life story
2. **Indexed like real memories** — The associative memory system indexes them by the "they believe" content
3. **The persona never knows** — In the prompt, false memories are presented as:
   ```
   THINGS YOU'RE WRONG ABOUT (you don't know this):
     You believe: My dad was a champion boxer
     Actually: He was an amateur who lost more than he won
   ```
4. **They defend them** — When conversation touches a false belief, the persona will confidently assert it

This mirrors the real psychological phenomenon where:
- People confidently remember things that never happened
- Source amnesia causes people to forget where they learned things
- The fading affect bias makes negative memories fade faster
- Memory is reconstructive, not reproductive

---

## Memory in the Prompt

All memories are loaded into every message's system prompt:

```
=== ALL YOUR MEMORIES ===

CORE MEMORIES (shaped who you are):
  [8/10] The day my parents split up
    Why it matters: Made me afraid of commitment
  [7/10] The talent show in year 7
    Why it matters: First time I felt genuinely good at something

SIGNATURE MEMORIES (stories you tell):
  That time we got lost at summer camp
    How you tell it: With exaggerated hand gestures and sound effects

SENSORY FRAGMENTS (flashes you remember):
  [smell] Rain on hot asphalt that summer
    Triggered by: hot weather after rain

AMBIENT MEMORIES (remember when prompted):
  My first day of secondary school
    [you're mostly_sure about this]

THINGS YOU'RE WRONG ABOUT (you don't know this):
  You believe: My dad was a champion boxer
  Actually: He was an amateur who lost most fights

DORMANT MEMORIES (would remember if reminded):
  The color of my childhood bedroom
    Trigger: talking about paint colors or childhood rooms
```

The LLM sees all of this every single message. This is why the prompts are so large — and why the results are so convincing.
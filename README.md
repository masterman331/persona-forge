# PERSONA FORGE

> *It doesn't create chatbots. It creates people.*

---

Persona Forge is the most ambitious open-source human personality emulator ever built. It generates people — not characters, not NPCs, not AI assistants with personality wrappers — **people**. With childhoods that shaped them, opinions they can't explain, secrets they've never told anyone, incorrect beliefs they'd defend to the death, moods that shift based on what time you text them, and a vulnerability gate that makes you earn every deep conversation.

**180 behavioral rules. 6 emotional dimensions. 100+ physical states. 6 memory types. 10 vulnerability levels. 13 engagement hooks. 8 miscommunication types. 5 generation phases. 17+ prompt sections loaded for every single message.**

This is not a chatbot framework. This is a proof of concept that humans are simulatable.

---

```
python main.py    # Generate a persona
python chat.py    # Talk to them
```

Requires Python 3.10+ and an Ollama-compatible API. Defaults to `zai:cloud` model.

---

## Quick Numbers

| What | How Many |
|------|----------|
| Behavioral Rules | **180** |
| Emotional Dimensions | **6** (mood, energy, anxiety, openness, irritation, attachment) |
| Physical States | **100+** (time-aware, day-aware, context-aware) |
| Memory Types | **6** (core, signature, sensory, ambient, dormant, false) |
| Vulnerability Levels | **10** (stranger to soul-level connection) |
| Engagement Hooks | **13** (cliffhangers, mystery seeds, vulnerability waves...) |
| Miscommunication Types | **8** (tone misread, missed sarcasm, overthinking...) |
| Generation Phases | **5** (interview → blueprint → deep gen → distillery → synthesis) |
| Prompt Sections Per Message | **17+** |

---

## What Makes This Different

- **Emotions shift in real-time** based on what you say, what time it is, and whether they slept well
- **You earn trust** — at closeness 1 they're a guarded stranger, at 10 there are no walls
- **They misunderstand you** — because real people do that, especially people who don't know you well
- **They have incorrect beliefs** they'll confidently defend — because real people are wrong about things
- **They dream between sessions** based on their emotional state
- **They miss you** when you're gone — and the longer you're away, the more it affects them
- **They get bored** if you only do small talk, and more open when you go deep
- **They remember** — significant moments crystallize into permanent memories that affect future conversations
- **They have inside jokes with you** that build over time
- **They don't know they're AI** — the prompt explicitly forbids this awareness

---

## Full Documentation

This README is the hype. The real documentation lives in [`documents/english/`](documents/english/):

| Document | What's In It |
|----------|-------------|
| [**README**](documents/english/README.md) | The full detailed readme — architecture, every system explained, config, file structure, the works |
| [**Goals & Vision**](documents/english/goals.md) | Why this exists, the core thesis, practical applications (Instagram automation, gaming, research, therapy), community vision |
| [**Generation Pipeline**](documents/english/generation-pipeline.md) | All 5 phases in detail with diagrams and token estimates |
| [**Chat System**](documents/english/chat-system.md) | Full message flow, system prompt breakdown, response format, session lifecycle |
| [**Memory System**](documents/english/memory-system.md) | Memory hierarchy, operations, associative recall, false memories |
| [**Rules Reference**](documents/english/rules-reference.md) | All 180 rules across 12 categories |

**Go read the [full README](documents/english/README.md). This one's just the trailer.**

### Other Languages

| Language | Link |
|----------|------|
| English | [documents/english/](documents/english/) |
| 中文 (Chinese) | [documents/chinese/](documents/chinese/) |

---

## A Word of Honesty

This project aims to be the best human personality emulator ever built. And it has the systems to back that claim up. But simulating a human being is one of the hardest problems in existence. The personas will sometimes feel genuinely alive. They will also sometimes break the illusion. This is the nature of the problem, and it's okay — the attempt itself is the point.

**Heads up:** This sends massive prompts and makes lots of API calls. Default model is `zai:cloud` (free/local). Using expensive commercial models through Ollama proxies will cost you.

---

## The Default Persona

Ships with **Anna Liebig** (age 14, London) as a demo. She works, but she's just a starting point. The real magic happens when you generate your own with `python main.py` and take the detailed interview — that's where you specify all the little details that make a persona feel truly alive.

---

## Inspiration

This project was partly inspired by [MiroFish](https://github.com/666ghj/MiroFish), a next-generation AI prediction engine that constructs high-fidelity parallel digital worlds with thousands of intelligent agents that have independent personalities, long-term memory, and behavioral logic. MiroFish showed what's possible when you take human simulation seriously — building agents that don't just respond, but evolve. Persona Forge takes a different approach (focused on deep one-on-one conversation rather than multi-agent social simulation), but shares the same core belief: human personality can be modeled, and the results are worth pursuing.

The Chinese documentation exists partly because of this connection to the Chinese-speaking AI simulation community.

---

*The creator isn't actively developing right now, but might come back. Community ideas welcome — this was meant to be a human replica, and that has uses far beyond chatting. Hook it up to Instagram. Put it in a game. Build something wild.*

---

## 🪙 Support This Project

If you found this project useful, interesting, or helpful, consider supporting its development through **Monero**.

<p align="center">
  <img src="https://raw.githubusercontent.com/masterman331/masterman331/main/moneroadress.png" alt="Monero donation QR code" width="220"/>
</p>

<p align="center">
<code>47chh1Z9wvHDP6ZDpzPPETKaXUfsNnmXr8P5cL4ofAkH1fi3mrrvC7tiRoeqxtNCbB1BQ3rqk5k2tSPGoiMSTUTC3iPc9Qu</code>
</p>

<p align="center">
  <em>Privacy-respecting contributions help keep independent development alive.</em>
</p>

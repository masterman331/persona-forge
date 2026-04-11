import json
import os
import re
from core.persona_file import PersonaFile


class AssociativeMemory:
    """Scans user messages against all persona data and pulls in emotionally linked memories.
    This is how REAL recall works — one word triggers a web of connected shit."""

    def __init__(self, persona_file: PersonaFile):
        self.pf = persona_file
        self._cache = {}
        self._build_index()

    def _build_index(self):
        """Build a keyword index over all persona data for fast lookup."""
        self.index = {
            "memories": [],      # {keywords, content, emotional_weight, category}
            "relationships": [],
            "opinions": [],
            "knowledge": [],
            "scenes": [],
            "sensory": [],
        }

        # Index core memories
        core = self.pf.read("memory", "core.json") or []
        for mem in core:
            self._add_to_index("memories", mem.get("memory", ""),
                              keywords=self._extract_keywords(mem.get("memory", "")),
                              emotional_weight=mem.get("emotional_weight", 5),
                              extra=mem.get("why_it_matters", ""))

        # Index signature memories
        sig = self.pf.read("memory", "signature.json") or []
        for mem in sig:
            self._add_to_index("memories", mem.get("memory", ""),
                              keywords=self._extract_keywords(mem.get("memory", "")),
                              emotional_weight=4,
                              extra=mem.get("how_they_tell_it", ""))

        # Index sensory fragments
        sensory = self.pf.read("memory", "sensory.json") or []
        for frag in sensory:
            self._add_to_index("sensory", frag.get("fragment", ""),
                              keywords=self._extract_keywords(frag.get("fragment", "")),
                              sense=frag.get("sense", ""),
                              trigger=frag.get("trigger", ""))

        # Index ambient memories
        ambient = self.pf.read("memory", "ambient.json") or []
        for mem in ambient:
            as_rem = mem.get("as_remembered", mem.get("original", ""))
            self._add_to_index("memories", as_rem,
                              keywords=self._extract_keywords(as_rem),
                              emotional_weight=3,
                              confidence=mem.get("confidence", "mostly_sure"))

        # Index dormant memories
        dormant = self.pf.read("memory", "dormant.json") or []
        for mem in dormant:
            self._add_to_index("memories", mem.get("memory", ""),
                              keywords=self._extract_keywords(mem.get("memory", "")),
                              emotional_weight=1,
                              trigger=mem.get("trigger", ""))

        # Index false certainties
        false = self.pf.read("memory", "false.json") or []
        for mem in false:
            self._add_to_index("memories", mem.get("they_believe", ""),
                              keywords=self._extract_keywords(mem.get("they_believe", "")),
                              emotional_weight=2,
                              is_false=True,
                              actual=mem.get("actually", ""))

        # Index relationships
        family = self.pf.read("relationships", "family.json") or []
        for person in family:
            name = person.get("name", "")
            self._add_to_index("relationships",
                              f"{name} ({person.get('role', '')}) - {person.get('personality', '')}",
                              keywords=self._extract_keywords(f"{name} {person.get('role', '')} {person.get('personality', '')}"),
                              name=name)

        friends = self.pf.read("relationships", "friends.json") or []
        for person in friends:
            name = person.get("name", "")
            self._add_to_index("relationships",
                              f"{name} - {person.get('dynamic', person.get('context', ''))}",
                              keywords=self._extract_keywords(name),
                              name=name)

        romantic = self.pf.read("relationships", "romantic.json") or []
        for person in romantic:
            name = person.get("name", "")
            self._add_to_index("relationships",
                              f"{name} ({person.get('type', '')}) - {person.get('what_happened', '')}",
                              keywords=self._extract_keywords(name),
                              name=name)

        # Index opinions
        opinions = self.pf.read("opinions", "timeline.json") or []
        for op in opinions:
            self._add_to_index("opinions",
                              f"{op.get('opinion', '')} (because: {op.get('because', '')})",
                              keywords=self._extract_keywords(op.get("opinion", "")),
                              era=op.get("era", ""),
                              certainty=op.get("certainty", ""))

        # Index knowledge
        expertise = self.pf.read("knowledge", "expertise.json") or []
        for k in expertise:
            self._add_to_index("knowledge",
                              f"{k.get('area', '')} - {k.get('source', '')}",
                              keywords=self._extract_keywords(k.get("area", "")),
                              depth=k.get("depth", ""))

        gaps = self.pf.read("knowledge", "gaps.json") or []
        for k in gaps:
            self._add_to_index("knowledge",
                              f"DON'T KNOW: {k.get('area', '')} - {k.get('reason', '')}",
                              keywords=self._extract_keywords(k.get("area", "")),
                              is_gap=True)

        incorrect = self.pf.read("knowledge", "incorrect.json") or []
        for k in incorrect:
            self._add_to_index("knowledge",
                              f"THINKS: {k.get('they_think', '')} BUT ACTUALLY: {k.get('actually', '')}",
                              keywords=self._extract_keywords(k.get("they_think", "")),
                              is_wrong=True)

        # Index key scenes from era files
        for era_file in self.pf.list_files("eras"):
            try:
                with open(era_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for ch in data.get("chapters", []):
                    deep = ch.get("deep_dive", {})
                    for scene in deep.get("key_scenes", []):
                        scene_text = f"{scene.get('location', '')} - {scene.get('what_happened', '')}"
                        self._add_to_index("scenes", scene_text,
                                          keywords=self._extract_keywords(scene_text),
                                          sensory=scene.get("sensory_fragment", ""),
                                          feeling=scene.get("what_they_felt", ""))
                    for cringe in deep.get("cringe_moments", []):
                        self._add_to_index("memories", cringe.get("moment", ""),
                                          keywords=self._extract_keywords(cringe.get("moment", "")),
                                          emotional_weight=6,
                                          category="cringe")
            except Exception:
                continue

    def _add_to_index(self, category, content, **kwargs):
        entry = {"content": content}
        entry.update(kwargs)
        self.index[category].append(entry)

    def _extract_keywords(self, text):
        """Extract meaningful keywords from text."""
        if not text:
            return set()
        # Lowercase, remove punctuation
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        words = text.split()
        # Filter stop words
        stop_words = {
            'the', 'a', 'an', 'is', 'was', 'are', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'shall', 'to', 'of', 'in', 'for',
            'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'and', 'but', 'or',
            'nor', 'not', 'so', 'yet', 'both', 'either', 'neither', 'each',
            'every', 'all', 'any', 'few', 'more', 'most', 'other', 'some',
            'such', 'no', 'only', 'own', 'same', 'than', 'too', 'very', 'just',
            'because', 'if', 'when', 'where', 'how', 'what', 'which', 'who',
            'that', 'this', 'these', 'those', 'it', 'its', 'i', 'me', 'my',
            'we', 'our', 'you', 'your', 'he', 'him', 'his', 'she', 'her',
            'they', 'them', 'their', 'about', 'up', 'out', 'also', 'then',
            'there', 'here', 'like', 'got', 'get', 'go', 'went', 'one', 'two',
            'thing', 'things', 'something', 'anything', 'everything', 'nothing',
            'much', 'many', 'really', 'actually', 'basically', 'literally',
            'probably', 'maybe', 'kinda', 'sorta', 'well', 'oh', 'yeah', 'yes',
        }
        return set(w for w in words if w not in stop_words and len(w) > 2)

    def recall(self, user_message, max_items=8, max_tokens=1500):
        """Given a user message, return relevant memories and context.
        This is associative recall — like how a real person's mind works."""
        user_keywords = self._extract_keywords(user_message)
        if not user_keywords:
            return self._default_recall()

        scored = []

        # Score memories by keyword overlap
        for entry in self.index["memories"]:
            entry_kw = entry.get("keywords", set())
            overlap = len(user_keywords & entry_kw)
            if overlap > 0:
                weight = entry.get("emotional_weight", 3)
                score = overlap * weight
                scored.append((score, "memory", entry))

        # Score relationships
        for entry in self.index["relationships"]:
            entry_kw = entry.get("keywords", set())
            overlap = len(user_keywords & entry_kw)
            if overlap > 0:
                # Names are strong triggers
                name = entry.get("name", "")
                name_parts = set(name.lower().split()) if name else set()
                name_overlap = len(user_keywords & name_parts)
                score = (overlap + name_overlap * 3) * 4
                scored.append((score, "relationship", entry))

        # Score opinions
        for entry in self.index["opinions"]:
            entry_kw = entry.get("keywords", set())
            overlap = len(user_keywords & entry_kw)
            if overlap > 0:
                score = overlap * 3
                scored.append((score, "opinion", entry))

        # Score knowledge
        for entry in self.index["knowledge"]:
            entry_kw = entry.get("keywords", set())
            overlap = len(user_keywords & entry_kw)
            if overlap > 0:
                score = overlap * 3
                if entry.get("is_gap"):
                    score += 2  # Important to know what they DON'T know
                if entry.get("is_wrong"):
                    score += 3  # Important to maintain incorrect beliefs
                scored.append((score, "knowledge", entry))

        # Score scenes
        for entry in self.index["scenes"]:
            entry_kw = entry.get("keywords", set())
            overlap = len(user_keywords & entry_kw)
            if overlap > 0:
                score = overlap * 2
                scored.append((score, "scene", entry))

        # Score sensory
        for entry in self.index["sensory"]:
            entry_kw = entry.get("keywords", set())
            trigger = entry.get("trigger", "")
            trigger_kw = self._extract_keywords(trigger)
            overlap = len(user_keywords & (entry_kw | trigger_kw))
            if overlap > 0:
                score = overlap * 2
                scored.append((score, "sensory", entry))

        # Sort by score, take top items
        scored.sort(key=lambda x: x[0], reverse=True)

        # Build the recall text
        parts = []
        token_est = 0
        items = 0

        for score, category, entry in scored:
            if items >= max_items or token_est >= max_tokens:
                break

            content = entry.get("content", "")
            if not content:
                continue

            if category == "memory":
                extra = entry.get("extra", "")
                is_false = entry.get("is_false", False)
                confidence = entry.get("confidence", "")
                text = f"- (memory) {content}"
                if extra:
                    text += f" — this matters because {extra}"
                if is_false:
                    text += f" [YOU'RE WRONG ABOUT THIS — actually: {entry.get('actual', '')}]"
                if confidence and confidence != "certain":
                    text += f" [you're {confidence} about this]"
                parts.append(text)

            elif category == "relationship":
                name = entry.get("name", "")
                parts.append(f"- (person you know) {content}")

            elif category == "opinion":
                certainty = entry.get("certainty", "")
                text = f"- (your opinion) {content}"
                if certainty == "confidently_wrong":
                    text += " [you're sure about this but you're wrong]"
                parts.append(text)

            elif category == "knowledge":
                if entry.get("is_gap"):
                    parts.append(f"- (you don't know about this) {content}")
                elif entry.get("is_wrong"):
                    parts.append(f"- (wrong belief) {content}")
                else:
                    depth = entry.get("depth", "")
                    parts.append(f"- (you know about this) {content}")

            elif category == "scene":
                sensory = entry.get("sensory", "")
                feeling = entry.get("feeling", "")
                text = f"- (something that happened) {content}"
                if feeling:
                    text += f" — you felt {feeling}"
                if sensory:
                    text += f" — you still remember {sensory}"
                parts.append(text)

            elif category == "sensory":
                trigger = entry.get("trigger", "")
                text = f"- (sensory flash) {content}"
                if trigger:
                    text += f" — triggered by {trigger}"
                parts.append(text)

            token_est += len(content.split())
            items += 1

        if not parts:
            return self._default_recall()

        return "THINGS THIS CONVERSATION BRINGS UP FOR YOU:\n" + "\n".join(parts)

    def _default_recall(self):
        """When nothing specific triggers, return a random sample of signature memories."""
        sig = self.pf.read("memory", "signature.json") or []
        if not sig:
            return ""
        lines = ["STORIES YOU MIGHT TELL IF THE CONVERSATION GOES THERE:"]
        for mem in sig[:3]:
            m = mem.get("memory", "")
            if m:
                lines.append(f"- {m}")
        return "\n".join(lines)

    def get_passion_topics(self, user_message):
        """Detect if the message hits a topic the persona is deeply into."""
        user_keywords = self._extract_keywords(user_message)
        expertise = self.pf.read("knowledge", "expertise.json") or []

        hits = []
        for exp in expertise:
            area = exp.get("area", "")
            area_kw = self._extract_keywords(area)
            overlap = len(user_keywords & area_kw)
            if overlap > 0:
                hits.append({
                    "topic": area,
                    "depth": exp.get("depth", ""),
                    "source": exp.get("source", ""),
                })
        return hits

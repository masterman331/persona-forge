import json
import time
from core.api_client import APIClient
from core.consistency_ledger import ConsistencyLedger
from core.persona_file import PersonaFile
from generators.prompt_builder import PromptBuilder
from utils.logger import ForgeLogger


class DeepGenerator:
    """Generates the detailed chapter content for each era."""

    def __init__(self, api_client: APIClient, ledger: ConsistencyLedger,
                 persona_file: PersonaFile, logger: ForgeLogger, prompt_builder: PromptBuilder):
        self.api = api_client
        self.ledger = ledger
        self.pf = persona_file
        self.logger = logger
        self.pb = prompt_builder
        self.all_content = []  # collected for distillery later

    def generate_all_eras(self, blueprint, identity):
        """Generate deep content for every era in the blueprint."""
        self.logger.phase_start("Deep Generation")

        eras = blueprint.get("life_eras", [])
        total_chapters = 0

        for era in eras:
            era_num = era.get("era_number", 0)
            era_label = era.get("label", "unknown")
            self.logger.step(f"Processing Era {era_num}: {era_label} ({era.get('age_range', '?')})")

            # Step 1: Generate chapter outlines for this era
            chapters = self._generate_chapter_outlines(era, identity)
            if not chapters:
                self.logger.warn(f"Skipping era {era_num} — chapter outline generation failed")
                continue

            # Step 2: Generate deep dive for each chapter
            era_content = {
                "era_number": era_num,
                "label": era_label,
                "age_range": era.get("age_range", ""),
                "chapters": [],
            }

            for chapter in chapters:
                ch_num = chapter.get("chapter_number", 0)
                self.logger.step(f"  Chapter {ch_num}: {chapter.get('time_span', '?')}")

                deep = self._generate_chapter_deep_dive(chapter, era, identity)
                if deep:
                    era_content["chapters"].append({
                        "outline": chapter,
                        "deep_dive": deep,
                    })
                    total_chapters += 1

                    # Update ledger with new facts from this chapter
                    self._ingest_chapter_into_ledger(deep, era_label)

            # Save era file
            path = self.pf.write_era(era_num, era_content, era_label)
            self.logger.file_written(path, len(json.dumps(era_content).encode()))

            # Collect content for later distillery
            self.all_content.append(era_content)

            # Brief pause to avoid hammering the API
            time.sleep(0.5)

        self.logger.phase_end(f"{len(eras)} eras, {total_chapters} chapters generated")
        return self.all_content

    def _generate_chapter_outlines(self, era_data, identity):
        """Generate chapter outlines for a single era."""
        prompt, system = self.pb.era_chapter_outlines(era_data, identity)

        try:
            raw = self.api.generate(prompt, system_prompt=system, temperature=0.85, max_tokens=4096)
            self.logger.api_call(
                self.api.call_count,
                f"Era {era_data.get('era_number', '?')} chapter outlines",
                self.api.call_log[-1]["elapsed"],
                self.api.call_log[-1].get("tokens_generated", 0)
            )

            result = self.api._extract_json(raw)
            return result.get("chapters", [])

        except Exception as e:
            self.logger.error(f"Chapter outline generation failed: {e}")
            return []

    def _generate_chapter_deep_dive(self, chapter_data, era_data, identity):
        """Generate a deep dive for a single chapter."""
        prompt, system = self.pb.chapter_deep_dive(chapter_data, era_data, identity)

        try:
            raw = self.api.generate(prompt, system_prompt=system, temperature=0.9, max_tokens=8192)
            self.logger.api_call(
                self.api.call_count,
                f"Ch {chapter_data.get('chapter_number', '?')} deep dive",
                self.api.call_log[-1]["elapsed"],
                self.api.call_log[-1].get("tokens_generated", 0)
            )

            result = self.api._extract_json(raw)
            return result

        except Exception as e:
            self.logger.error(f"Chapter deep dive failed: {e}")
            return None

    def _ingest_chapter_into_ledger(self, deep_dive, era_label):
        """Pull new facts from generated content into the consistency ledger."""
        # Named people from relationship evolution
        for rel in deep_dive.get("relationship_evolution", []):
            person = rel.get("person", "")
            shift = rel.get("what_shifted", "")
            if person:
                self.ledger.add_name(person, role="mentioned in era", context=shift)
                self.ledger.add_relationship(person, "evolving", notes=shift)

        # Named places from key scenes
        for scene in deep_dive.get("key_scenes", []):
            loc = scene.get("location", "")
            if loc:
                self.ledger.add_place(loc, "scene location")

        # Knowledge acquired
        for k in deep_dive.get("knowledge_acquired", []):
            thing = k.get("thing", "")
            how = k.get("how", "")
            if thing:
                self.ledger.add_fact(f"Learned about: {thing} — {how}", source="deep_generation")

        # Opinions
        for op in deep_dive.get("opinion_snapshot", []):
            opinion = op.get("opinion", "")
            because = op.get("because", "")
            if opinion:
                self.ledger.add_fact(f"Opinion: {opinion} (because: {because})", source="deep_generation")

        # Slang/language
        for slang in deep_dive.get("slang_and_language", []):
            phrase = slang.get("phrase_or_pattern", "")
            origin = slang.get("origin", "")
            if phrase:
                self.ledger.add_fact(f"Language: says '{phrase}' from {origin}", source="deep_generation")

    def get_all_content_text(self):
        """Return all generated content as a single text block for the distillery."""
        parts = []
        for era in self.all_content:
            parts.append(f"ERA: {era.get('label', '?')} (ages {era.get('age_range', '?')})")
            for ch_data in era.get("chapters", []):
                outline = ch_data.get("outline", {})
                deep = ch_data.get("deep_dive", {})
                parts.append(f"  Chapter: {outline.get('time_span', '?')}")

                if deep.get("daily_life_routines"):
                    parts.append(f"    Routines: {deep['daily_life_routines']}")

                for scene in deep.get("key_scenes", []):
                    parts.append(f"    Scene: {scene.get('location', '?')} — {scene.get('what_happened', '?')}")

                for rel in deep.get("relationship_evolution", []):
                    parts.append(f"    Relationship: {rel.get('person', '?')} — {rel.get('what_shifted', '?')}")

                for op in deep.get("opinion_snapshot", []):
                    parts.append(f"    Opinion: {op.get('opinion', '?')} (because: {op.get('because', '?')})")

        return "\n".join(parts)

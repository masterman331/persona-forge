import json
from core.api_client import APIClient
from core.consistency_ledger import ConsistencyLedger
from core.persona_file import PersonaFile
from generators.prompt_builder import PromptBuilder
from generators.deep_generator import DeepGenerator
from utils.logger import ForgeLogger


class PersonalitySynthesis:
    """Derives personality bottom-up from all generated content."""

    def __init__(self, api_client: APIClient, ledger: ConsistencyLedger,
                 persona_file: PersonaFile, logger: ForgeLogger, prompt_builder: PromptBuilder):
        self.api = api_client
        self.ledger = ledger
        self.pf = persona_file
        self.logger = logger
        self.pb = prompt_builder

    def synthesize(self, deep_generator: DeepGenerator, identity):
        """Run full personality synthesis from all generated content."""
        self.logger.phase_start("Personality Synthesis")

        content_summary = deep_generator.get_all_content_text()
        if not content_summary:
            self.logger.warn("No content to synthesize from")
            self.logger.phase_end("Skipped")
            return {}

        # Step 1: Personality derivation
        self.logger.step("Deriving behavioral patterns and communication style...")
        personality = self._derive_personality(content_summary, identity)

        # Step 2: Knowledge mapping
        self.logger.step("Mapping knowledge, gaps, and incorrect beliefs...")
        knowledge = self._map_knowledge(content_summary, identity)

        # Step 3: Save everything
        result = self._compile_and_save(personality, knowledge)

        self.logger.phase_end(f"Personality + knowledge synthesized")
        return result

    def _derive_personality(self, content_summary, identity):
        """Derive personality from life content."""
        prompt, system = self.pb.personality_synthesis(content_summary, identity)

        try:
            raw = self.api.generate(prompt, system_prompt=system, temperature=0.8, max_tokens=8192)
            self.logger.api_call(
                self.api.call_count,
                "Personality synthesis",
                self.api.call_log[-1]["elapsed"],
                self.api.call_log[-1].get("tokens_generated", 0)
            )
            return self.api._extract_json(raw)
        except Exception as e:
            self.logger.error(f"Personality synthesis failed: {e}")
            return {}

    def _map_knowledge(self, content_summary, identity):
        """Map knowledge areas, gaps, and incorrect beliefs."""
        prompt, system = self.pb.knowledge_map(content_summary, identity)

        try:
            raw = self.api.generate(prompt, system_prompt=system, temperature=0.8, max_tokens=4096)
            self.logger.api_call(
                self.api.call_count,
                "Knowledge mapping",
                self.api.call_log[-1]["elapsed"],
                self.api.call_log[-1].get("tokens_generated", 0)
            )
            return self.api._extract_json(raw)
        except Exception as e:
            self.logger.error(f"Knowledge mapping failed: {e}")
            return {}

    def _compile_and_save(self, personality, knowledge):
        """Save all synthesis results to persona files."""
        # Behavioral patterns
        patterns = personality.get("behavioral_patterns", {})
        path = self.pf.write_psychology("patterns", patterns)
        self.logger.file_written(path, len(json.dumps(patterns).encode()))

        # Communication style
        comm = personality.get("communication_style", {})
        path = self.pf.write_psychology("communication", comm)
        self.logger.file_written(path, len(json.dumps(comm).encode()))

        # Inner landscape
        inner = personality.get("inner_landscape", {})
        path = self.pf.write_psychology("inner_life", inner)
        self.logger.file_written(path, len(json.dumps(inner).encode()))

        # Contradictions
        contradictions = personality.get("contradictions", [])
        path = self.pf.write_psychology("contradictions", contradictions)
        self.logger.file_written(path, len(json.dumps(contradictions).encode()))

        # Knowledge
        expertise = knowledge.get("expertise", [])
        path = self.pf.write_knowledge("expertise", expertise)
        self.logger.file_written(path, len(json.dumps(expertise).encode()))

        casual = knowledge.get("casual_knowledge", [])
        path = self.pf.write_knowledge("casual", casual)
        self.logger.file_written(path, len(json.dumps(casual).encode()))

        gaps = knowledge.get("knowledge_gaps", [])
        path = self.pf.write_knowledge("gaps", gaps)
        self.logger.file_written(path, len(json.dumps(gaps).encode()))

        incorrect = knowledge.get("incorrect_beliefs", [])
        path = self.pf.write_knowledge("incorrect", incorrect)
        self.logger.file_written(path, len(json.dumps(incorrect).encode()))

        # Extract language data from personality and save separately
        go_to_phrases = comm.get("go_to_phrases", [])
        verbal_tics = comm.get("verbal_tics", [])

        # Also collect slang from all eras
        slang_data = self._collect_slang_from_eras()
        path = self.pf.write_language("slang", slang_data)
        self.logger.file_written(path, len(json.dumps(slang_data).encode()))

        phrases_data = {"go_to_phrases": go_to_phrases, "verbal_tics": verbal_tics}
        path = self.pf.write_language("phrases", phrases_data)
        self.logger.file_written(path, len(json.dumps(phrases_data).encode()))

        # Voice summary
        voice = {
            "sentence_structure": comm.get("sentence_structure", ""),
            "vocabulary_level": comm.get("vocabulary_level", ""),
            "humor_style": comm.get("humor_style", ""),
            "vulnerability_expression": comm.get("vulnerability_expression", ""),
            "nervous_talk": comm.get("nervous_talk", ""),
            "texting_vs_talking": comm.get("texting_vs_talking", ""),
        }
        path = self.pf.write_language("voice", voice)
        self.logger.file_written(path, len(json.dumps(voice).encode()))

        # References (pop culture stuff collected from eras)
        refs = self._collect_references_from_eras()
        path = self.pf.write_language("references", refs)
        self.logger.file_written(path, len(json.dumps(refs).encode()))

        # Opinion timeline
        opinions = self._collect_opinions_from_eras()
        path = self.pf.write_opinions(opinions)
        self.logger.file_written(path, len(json.dumps(opinions).encode()))

        return {
            "personality": personality,
            "knowledge": knowledge,
            "language": {"slang": slang_data, "phrases": phrases_data, "voice": voice, "references": refs},
            "opinions": opinions,
        }

    def _collect_slang_from_eras(self):
        """Pull slang data from all generated era files."""
        all_slang = []
        for era_content in self.pf.list_files("eras"):
            try:
                with open(era_content, "r") as f:
                    data = json.load(f)
                for ch in data.get("chapters", []):
                    deep = ch.get("deep_dive", {})
                    for slang in deep.get("slang_and_language", []):
                        slang["era"] = data.get("label", "unknown")
                        all_slang.append(slang)
            except Exception:
                continue
        return all_slang

    def _collect_references_from_eras(self):
        """Pull pop culture references from all generated era files."""
        all_refs = []
        for era_content in self.pf.list_files("eras"):
            try:
                with open(era_content, "r") as f:
                    data = json.load(f)
                for ch in data.get("chapters", []):
                    deep = ch.get("deep_dive", {})
                    for k in deep.get("knowledge_acquired", []):
                        thing = k.get("thing", "")
                        if any(word in thing.lower() for word in ["music", "band", "song", "show", "movie", "game", "book", "podcast", "tv"]):
                            all_refs.append({"reference": thing, "origin": k.get("how", ""), "era": data.get("label", "")})
            except Exception:
                continue
        return all_refs

    def _collect_opinions_from_eras(self):
        """Pull opinions from all generated era files and build a timeline."""
        all_opinions = []
        for era_content in self.pf.list_files("eras"):
            try:
                with open(era_content, "r") as f:
                    data = json.load(f)
                era_label = data.get("label", "")
                for ch in data.get("chapters", []):
                    outline = ch.get("outline", {})
                    deep = ch.get("deep_dive", {})
                    for op in deep.get("opinion_snapshot", []):
                        all_opinions.append({
                            "era": era_label,
                            "time": outline.get("time_span", ""),
                            "opinion": op.get("opinion", ""),
                            "because": op.get("because", ""),
                            "certainty": op.get("certainty", ""),
                        })
            except Exception:
                continue
        return all_opinions

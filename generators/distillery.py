import json
from core.api_client import APIClient
from core.consistency_ledger import ConsistencyLedger
from core.persona_file import PersonaFile
from generators.prompt_builder import PromptBuilder
from generators.deep_generator import DeepGenerator
from utils.logger import ForgeLogger


class MemoryDistillery:
    """Transforms generated life content into realistic human memory."""

    def __init__(self, api_client: APIClient, ledger: ConsistencyLedger,
                 persona_file: PersonaFile, logger: ForgeLogger, prompt_builder: PromptBuilder):
        self.api = api_client
        self.ledger = ledger
        self.pf = persona_file
        self.logger = logger
        self.pb = prompt_builder

    def distill(self, deep_generator: DeepGenerator, identity):
        """Run the full distillery pipeline on all generated content."""
        self.logger.phase_start("Memory Distillery")

        all_text = deep_generator.get_all_content_text()
        if not all_text:
            self.logger.warn("No content to distill — skipping")
            self.logger.phase_end("Skipped — no content")
            return {}

        # Step 1: Memory selection
        self.logger.step("Selecting memories that would stick...")
        selected = self._select_memories(all_text, identity)

        # Step 2: Memory transformation
        self.logger.step("Transforming memories through human filter...")
        transformed = self._transform_memories(selected, identity)

        # Step 3: Save everything
        memories = self._compile_and_save(selected, transformed)

        self.logger.phase_end(f"{len(memories.get('core', []))} core, {len(memories.get('signature', []))} signature, {len(memories.get('sensory', []))} sensory")
        return memories

    def _select_memories(self, content_text, identity):
        """Select which memories would actually stick in a real person's mind."""
        prompt, system = self.pb.memory_distillery_select(content_text, identity)

        try:
            raw = self.api.generate(prompt, system_prompt=system, temperature=0.8, max_tokens=8192)
            self.logger.api_call(
                self.api.call_count,
                "Memory selection",
                self.api.call_log[-1]["elapsed"],
                self.api.call_log[-1].get("tokens_generated", 0)
            )
            return self.api._extract_json(raw)
        except Exception as e:
            self.logger.error(f"Memory selection failed: {e}")
            return {"core_memories": [], "signature_memories": [], "sensory_fragments": []}

    def _transform_memories(self, selected, identity):
        """Transform selected memories through the human memory filter."""
        # Combine core + signature for transformation
        core = selected.get("core_memories", [])
        signature = selected.get("signature_memories", [])
        combined = json.dumps({"core": core, "signature": signature}, indent=2)

        prompt, system = self.pb.memory_distillery_transform(combined, identity)

        try:
            raw = self.api.generate(prompt, system_prompt=system, temperature=0.85, max_tokens=8192)
            self.logger.api_call(
                self.api.call_count,
                "Memory transformation",
                self.api.call_log[-1]["elapsed"],
                self.api.call_log[-1].get("tokens_generated", 0)
            )
            return self.api._extract_json(raw)
        except Exception as e:
            self.logger.error(f"Memory transformation failed: {e}")
            return {"transformed_memories": [], "dormant_memories": [], "false_certainties": []}

    def _compile_and_save(self, selected, transformed):
        """Compile all memory data and save to persona files."""
        # Core memories
        core = selected.get("core_memories", [])
        path = self.pf.write_memory("core", core)
        self.logger.file_written(path, len(json.dumps(core).encode()))

        # Signature memories (stories they tell)
        signature = selected.get("signature_memories", [])
        path = self.pf.write_memory("signature", signature)
        self.logger.file_written(path, len(json.dumps(signature).encode()))

        # Sensory fragments
        sensory = selected.get("sensory_fragments", [])
        path = self.pf.write_memory("sensory", sensory)
        self.logger.file_written(path, len(json.dumps(sensory).encode()))

        # Transformed memories
        transformed_mems = transformed.get("transformed_memories", [])
        path = self.pf.write_memory("ambient", transformed_mems)
        self.logger.file_written(path, len(json.dumps(transformed_mems).encode()))

        # Dormant memories
        dormant = transformed.get("dormant_memories", [])
        path = self.pf.write_memory("dormant", dormant)
        self.logger.file_written(path, len(json.dumps(dormant).encode()))

        # False certainties
        false_certs = transformed.get("false_certainties", [])
        path = self.pf.write_memory("false", false_certs)
        self.logger.file_written(path, len(json.dumps(false_certs).encode()))

        # Update ledger with memory facts
        for cm in core:
            mem = cm.get("memory", "")
            why = cm.get("why_it_matters", "")
            self.ledger.add_fact(f"Core memory: {mem} (matters because: {why})", source="distillery")

        for fc in false_certs:
            believe = fc.get("they_believe", "")
            actually = fc.get("actually", "")
            self.ledger.add_fact(f"False certainty: believes '{believe}' but actually '{actually}'", source="distillery")

        return {
            "core": core,
            "signature": signature,
            "sensory": sensory,
            "ambient": transformed_mems,
            "dormant": dormant,
            "false": false_certs,
        }

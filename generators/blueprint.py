import json
from core.api_client import APIClient
from core.consistency_ledger import ConsistencyLedger
from core.persona_file import PersonaFile
from generators.prompt_builder import PromptBuilder
from utils.logger import ForgeLogger


class BlueprintGenerator:
    """Generates the life arc blueprint from interview data."""

    def __init__(self, api_client: APIClient, ledger: ConsistencyLedger,
                 persona_file: PersonaFile, logger: ForgeLogger, prompt_builder: PromptBuilder):
        self.api = api_client
        self.ledger = ledger
        self.pf = persona_file
        self.logger = logger
        self.pb = prompt_builder

    def generate(self, seed_data, qa_history):
        """Generate the full life blueprint. Returns the blueprint dict."""
        self.logger.phase_start("Blueprint Generation")

        prompt, system = self.pb.blueprint_generation(seed_data, qa_history)
        self.logger.step("Generating life blueprint...")

        raw = self.api.generate(prompt, system_prompt=system, temperature=0.85, max_tokens=8192)
        self.logger.api_call(
            self.api.call_count,
            "Blueprint generation",
            self.api.call_log[-1]["elapsed"],
            self.api.call_log[-1].get("tokens_generated", 0)
        )

        try:
            blueprint = self.api._extract_json(raw)
        except ValueError:
            self.logger.warn("JSON parse failed on first attempt, retrying extraction...")
            # Try a second pass — ask the model to fix it
            fix_prompt = f"The following response was supposed to be valid JSON but had parse errors. Fix it and return ONLY the corrected JSON:\n\n{raw}"
            raw2 = self.api.generate(fix_prompt, system_prompt=system, temperature=0.3)
            blueprint = self.api._extract_json(raw2)

        # Extract writing style if present
        writing_style = blueprint.get("writing_style", None)
        if writing_style:
            self.logger.step(f"Writing style: {writing_style[:80]}...")
            # Update the prompt builder with the chosen style
            self.pb.writing_style = writing_style

        # Save blueprint
        path = self.pf.write_blueprint(blueprint)
        self.logger.file_written(path, len(json.dumps(blueprint).encode()))

        # Update ledger with blueprint data
        self._ingest_blueprint_into_ledger(blueprint, seed_data)

        # Save identity
        identity = {
            "name": seed_data.get("name"),
            "age": seed_data.get("age"),
            "birth_location": seed_data.get("birth_location"),
            "gender": seed_data.get("gender"),
            "extra": seed_data.get("extra", ""),
            "writing_style": writing_style,
            "interview_questions": len(qa_history),
        }
        id_path = self.pf.write_identity(identity)
        self.logger.file_written(id_path, len(json.dumps(identity).encode()))

        self.logger.phase_end(f"{len(blueprint.get('life_eras', []))} eras generated")

        # Show user the blueprint for approval
        self._display_blueprint_summary(blueprint)

        return blueprint

    def _ingest_blueprint_into_ledger(self, blueprint, seed_data):
        """Pull key facts from blueprint into the consistency ledger."""
        name = seed_data.get("name", "?")

        # Core facts
        self.ledger.add_fact(f"Person's name: {name}", source="blueprint")
        self.ledger.add_fact(f"Born in: {seed_data.get('birth_location', '?')}", source="blueprint")
        self.ledger.add_fact(f"Current age: {seed_data.get('age', '?')}", source="blueprint")

        # Era facts
        for era in blueprint.get("life_eras", []):
            era_label = era.get("label", "")
            age_range = era.get("age_range", "")
            self.ledger.add_timeline_event(era_label, f"Ages {age_range}")
            for evt in era.get("key_events", []):
                self.ledger.add_timeline_event(era_label, evt)

        # Named people from relationship map
        rel_map = blueprint.get("relationship_map", {})
        for family_member in rel_map.get("family", []):
            fname = family_member.get("name", "")
            role = family_member.get("role", "")
            if fname:
                self.ledger.add_name(fname, role=role, context="family")
                self.ledger.add_relationship(fname, role, status="active", notes="family")

        for era_friends in rel_map.get("friends_by_era", []):
            for friend_str in era_friends.get("friends", []):
                # Parse "Name (dynamic)" format
                if "(" in friend_str:
                    parts = friend_str.split("(", 1)
                    fname = parts[0].strip()
                    dynamic = parts[1].rstrip(")").strip()
                    self.ledger.add_name(fname, role="friend", context=dynamic)
                else:
                    self.ledger.add_name(friend_str.strip(), role="friend")

        for romance in rel_map.get("romantic", []):
            fname = romance.get("name", "")
            rtype = romance.get("type", "")
            if fname:
                self.ledger.add_name(fname, role=rtype, context=romance.get("what_happened", ""))

        # Named places
        for world in blueprint.get("world_map", []):
            school = world.get("school", "")
            if school:
                self.ledger.add_place(school, "school")
            for hangout in world.get("hangouts", []):
                self.ledger.add_place(hangout, "hangout")

    def _display_blueprint_summary(self, blueprint):
        """Print a readable summary for user review."""
        c = ForgeLogger.COLORS
        print(f"\n{c['BOLD']}{c['HEADER']}--- BLUEPRINT SUMMARY ---{c['END']}\n")

        style = blueprint.get("writing_style", "Not set")
        print(f"  Writing style: {style}")
        print()

        eras = blueprint.get("life_eras", [])
        print(f"  Life Eras ({len(eras)}):")
        for era in eras:
            label = era.get("label", "?")
            ages = era.get("age_range", "?")
            tone = era.get("emotional_tone", "?")
            events = era.get("key_events", [])
            print(f"    {era.get('era_number', '?')}. {label} ({ages})")
            print(f"       Tone: {tone}")
            for evt in events[:3]:
                print(f"       - {evt}")
            if len(events) > 3:
                print(f"       ... and {len(events)-3} more events")
            print()

        rels = blueprint.get("relationship_map", {})
        family = rels.get("family", [])
        if family:
            print(f"  Family:")
            for fm in family:
                print(f"    {fm.get('name', '?')} ({fm.get('role', '?')}) - {fm.get('occupation', '?')}")

        romantic = rels.get("romantic", [])
        if romantic:
            print(f"\n  Romantic history:")
            for r in romantic:
                print(f"    {r.get('type', '?')}: {r.get('name', '?')} at age {r.get('age_when', '?')}")

        print(f"\n{c['DIM']}Review the blueprint above. You'll get a chance to approve or adjust after all eras are generated.{c['END']}")

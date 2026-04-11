#!/usr/bin/env python3
"""Persona Forge — Generate realistic human lives."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.api_client import APIClient
from core.consistency_ledger import ConsistencyLedger
from core.persona_file import PersonaFile
from generators.prompt_builder import PromptBuilder
from generators.interview import InterviewGenerator
from generators.blueprint import BlueprintGenerator
from generators.deep_generator import DeepGenerator
from generators.distillery import MemoryDistillery
from generators.synthesis import PersonalitySynthesis
from utils.logger import ForgeLogger
from config import OUTPUT_DIR


def get_seed_data():
    """Collect basic seed information from the user."""
    print("\n" + "=" * 50)
    print("  PERSONA FORGE — New Persona")
    print("=" * 50 + "\n")

    name = input("Name (first + last): ").strip()
    if not name:
        print("Name is required.")
        sys.exit(1)

    age = input("Current age: ").strip()
    birth_location = input("Birth location (city, state/country): ").strip()
    gender = input("Gender: ").strip()
    extra = input("Any extra notes? (press Enter to skip): ").strip()

    return {
        "name": name,
        "age": age,
        "birth_location": birth_location,
        "gender": gender,
        "extra": extra if extra else None,
    }


def choose_style():
    """Let user pick a narrative style or skip."""
    options = PromptBuilder.style_options()

    print("\nChoose a narrative style for this person's life story:")
    print("(This affects how all generated content is written)\n")

    keys = list(options.keys())
    for i, key in enumerate(keys, 1):
        print(f"  {i}. {key.upper()}")
        print(f"     {options[key]}")
        print()

    print("  0. SKIP — let the system decide based on the persona")
    print()

    choice = input("Pick a number (0-6): ").strip()

    try:
        idx = int(choice)
        if idx == 0:
            return None  # System decides
        if 1 <= idx <= len(keys):
            selected = keys[idx - 1]
            if selected == "custom":
                custom = input("Describe the style: ").strip()
                return custom
            return options[selected]
    except ValueError:
        pass

    print("Invalid choice, using auto-detect.")
    return None


def ask_interview_preference():
    """Ask if user wants the full interview or to skip it."""
    print("\nDo you want to do the interactive interview?")
    print("  1. YES — I'll answer questions to shape this person")
    print("  2. NO  — Just use the basic info I gave you")
    print()

    choice = input("Pick 1 or 2: ").strip()
    return choice.strip() != "2"


def confirm_blueprint(blueprint):
    """Let user review and approve the blueprint."""
    print("\n" + "=" * 50)
    print("  BLUEPRINT REVIEW")
    print("=" * 50)

    eras = blueprint.get("life_eras", [])
    print(f"\n  Writing style: {blueprint.get('writing_style', 'auto')}")
    print(f"  Life eras: {len(eras)}")
    for era in eras:
        print(f"    {era.get('era_number', '?')}. {era.get('label', '?')} ({era.get('age_range', '?')}) — {era.get('emotional_tone', '?')}")

    family = blueprint.get("relationship_map", {}).get("family", [])
    if family:
        print(f"\n  Family members: {', '.join(f.get('name', '?') for f in family)}")

    print()
    choice = input("Does this look right? (yes/edit/regen): ").strip().lower()
    return choice


def main():
    # Step 0: Collect seed data
    seed = get_seed_data()

    # Step 1: Choose narrative style
    style = choose_style()

    # Step 2: Interview preference
    do_interview = ask_interview_preference()

    # Initialize everything
    logger = ForgeLogger(seed["name"])
    logger.banner()

    api = APIClient()
    ledger = ConsistencyLedger()
    pf = PersonaFile(seed["name"], base_dir=OUTPUT_DIR)
    pb = PromptBuilder(consistency_ledger=ledger, writing_style=style)

    # Save the ledger path for later
    ledger_path = os.path.join(pf.base_dir, "_ledger.json")

    # --- PHASE 1: INTERVIEW ---
    interviewer = InterviewGenerator(api, ledger, logger, pb)
    if do_interview:
        qa_history = interviewer.run(seed)
    else:
        qa_history = interviewer.skip_interview(seed)

    # --- PHASE 2: BLUEPRINT ---
    blueprint_gen = BlueprintGenerator(api, ledger, pf, logger, pb)
    blueprint = blueprint_gen.generate(seed, qa_history)

    # Blueprint review loop
    while True:
        verdict = confirm_blueprint(blueprint)
        if verdict in ("yes", "y", ""):
            break
        elif verdict == "regen":
            logger.step("Regenerating blueprint...")
            blueprint = blueprint_gen.generate(seed, qa_history)
        elif verdict == "edit":
            note = input("What should change? ").strip()
            if note:
                qa_history.append({"question": "Blueprint adjustment", "answer": note})
                ledger.add_fact(f"User correction: {note}", source="user_edit")
            logger.step("Regenerating blueprint with corrections...")
            blueprint = blueprint_gen.generate(seed, qa_history)
        else:
            break

    # Update writing style from blueprint if not set manually
    if not pb.writing_style and blueprint.get("writing_style"):
        pb.writing_style = blueprint["writing_style"]
        logger.step(f"Writing style set from blueprint: {pb.writing_style[:60]}...")

    # Save ledger
    ledger.save(ledger_path)
    logger.file_written(ledger_path, os.path.getsize(ledger_path) if os.path.exists(ledger_path) else 0)

    # --- PHASE 3: DEEP GENERATION ---
    identity = pf.get_identity()
    deep_gen = DeepGenerator(api, ledger, pf, logger, pb)
    all_content = deep_gen.generate_all_eras(blueprint, identity)

    # Save ledger again after deep generation
    ledger.save(ledger_path)

    # --- PHASE 4: MEMORY DISTILLERY ---
    distillery = MemoryDistillery(api, ledger, pf, logger, pb)
    memories = distillery.distill(deep_gen, identity)

    # --- PHASE 5: PERSONALITY SYNTHESIS ---
    synthesis = PersonalitySynthesis(api, ledger, pf, logger, pb)
    personality = synthesis.synthesize(deep_gen, identity)

    # --- FINAL: Save ledger and log ---
    ledger.save(ledger_path)
    log_path = logger.save_log()

    # Print final report
    logger.final_report(api.get_stats())

    # Show persona summary
    summary = pf.summary()
    print(f"  Persona: {summary['name']}")
    print(f"  Files:   {summary['files']}")
    print(f"  Size:    {summary['total_size_kb']} KB")
    print(f"  Saved:   {pf.base_dir}")
    print(f"  Log:     {log_path}")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Partial data may be saved.")
        sys.exit(1)
    except Exception as e:
        import traceback
        print(f"\n\nError: {e}")
        traceback.print_exc()
        sys.exit(1)

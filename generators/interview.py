from config import INTERVIEW_MAX_QUESTIONS, INTERVIEW_MIN_QUESTIONS
from core.api_client import APIClient
from core.consistency_ledger import ConsistencyLedger
from generators.prompt_builder import PromptBuilder
from utils.logger import ForgeLogger


class InterviewGenerator:
    """Runs the adaptive interview to gather seed info about a persona."""

    def __init__(self, api_client: APIClient, ledger: ConsistencyLedger, logger: ForgeLogger, prompt_builder: PromptBuilder):
        self.api = api_client
        self.ledger = ledger
        self.logger = logger
        self.pb = prompt_builder
        self.qa_history = []
        self.done = False

    def run(self, seed_data):
        """Run the full interview. Returns the qa_history."""
        self.logger.phase_start("Interview")

        # First question
        prompt, system = self.pb.interview_first_question(seed_data)
        self.logger.step("Generating first interview question...")

        question = self.api.generate(prompt, system_prompt=system, temperature=0.9)
        question = question.strip().strip('"')

        self.logger.question(question)
        answer = input("> ")
        self.logger.user_input(answer)

        self.qa_history.append({"question": question, "answer": answer})
        self._update_ledger_from_answer(question, answer)

        # Continue asking questions
        while not self.done and len(self.qa_history) < INTERVIEW_MAX_QUESTIONS:
            prompt, system = self.pb.interview_next_question(seed_data, self.qa_history)
            self.logger.step(f"Generating question {len(self.qa_history) + 1}...")

            response = self.api.generate(prompt, system_prompt=system, temperature=0.9)
            response = response.strip()

            if response.upper().strip() == "ENOUGH":
                self.logger.step("Interview has enough information. Moving on.")
                self.done = True
                break

            question = response.strip().strip('"')
            self.logger.question(question)
            answer = input("> ")
            self.logger.user_input(answer)

            if answer.strip().lower() in ("done", "enough", "skip", "that's it", "thats it", "move on"):
                self.logger.step("User ended interview.")
                self.qa_history.append({"question": question, "answer": answer})
                self.done = True
                break

            self.qa_history.append({"question": question, "answer": answer})
            self._update_ledger_from_answer(question, answer)

            # Auto-suggest ending after minimum questions
            if len(self.qa_history) >= INTERVIEW_MIN_QUESTIONS:
                remaining = INTERVIEW_MAX_QUESTIONS - len(self.qa_history)
                if remaining > 0:
                    self.logger.info(f"{len(self.qa_history)} questions answered. {remaining} remaining. Type 'done' to finish early.")

        self.logger.phase_end(f"{len(self.qa_history)} questions answered")
        return self.qa_history

    def _update_ledger_from_answer(self, question, answer):
        """Extract facts from answers and update the consistency ledger."""
        self.ledger.add_fact(f"Q: {question} A: {answer}", source="interview")

        # Try to extract names (capitalized words that appear with context)
        words = answer.split()
        for i, word in enumerate(words):
            if word[0].isupper() and len(word) > 1 and word not in ("I", "The", "A", "My", "He", "She", "It", "They", "We", "And", "But", "So", "Or", "If", "Not", "Yes", "No", "Maybe"):
                context = " ".join(words[max(0,i-2):i+3])
                self.ledger.add_name(word, role="mentioned", context=context)

    def skip_interview(self, seed_data):
        """Skip the interview entirely — just use seed data as-is."""
        self.logger.phase_start("Interview (skipped)")
        self.logger.step("Skipping interview — using seed data only")

        # Convert seed data into minimal QA format
        self.qa_history = [
            {"question": "Basic identity", "answer": f"{seed_data.get('name', '?')}, age {seed_data.get('age', '?')}, born in {seed_data.get('birth_location', '?')}, {seed_data.get('gender', '?')}"},
        ]
        if seed_data.get("extra"):
            self.qa_history.append(
                {"question": "Additional notes", "answer": seed_data["extra"]}
            )

        # Add seed data to ledger
        self.ledger.add_fact(f"Name: {seed_data.get('name', '?')}", source="seed")
        self.ledger.add_fact(f"Age: {seed_data.get('age', '?')}", source="seed")
        self.ledger.add_fact(f"Birth location: {seed_data.get('birth_location', '?')}", source="seed")
        self.ledger.add_fact(f"Gender: {seed_data.get('gender', '?')}", source="seed")

        self.logger.phase_end("Skipped — seed data only")
        return self.qa_history

import json
import os
from datetime import datetime


class ConversationStore:
    """Stores conversation history, learned facts, and relationship state.
    Completely separate from the original persona files."""

    def __init__(self, persona_name, base_dir="conversations"):
        self.persona_name = persona_name
        self.base_dir = os.path.join(base_dir, persona_name.replace(" ", "_"))
        os.makedirs(self.base_dir, exist_ok=True)

        self.sessions_file = os.path.join(self.base_dir, "sessions.json")
        self.learned_file = os.path.join(self.base_dir, "learned.json")
        self.relationship_file = os.path.join(self.base_dir, "relationship.json")

        # Load or init
        self.sessions = self._load(self.sessions_file, {"sessions": []})
        self.learned = self._load(self.learned_file, {"facts": [], "inside_jokes": [], "shared_experiences": []})
        self.relationship = self._load(self.relationship_file, {
            "closeness": 1,  # 1-10 scale
            "trust_level": 1,
            "first_met": None,
            "last_interaction": None,
            "total_exchanges": 0,
            "nickname_for_user": None,
            "user_name": None,
            "emotional_state": "neutral",
            "notes": [],
        })

    def _load(self, path, default):
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return default
        return default

    def _save(self, path, data):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # ── SESSIONS ──

    def start_session(self):
        """Start a new chat session."""
        session = {
            "id": len(self.sessions["sessions"]) + 1,
            "started_at": datetime.now().isoformat(),
            "ended_at": None,
            "exchanges": [],
        }
        self.sessions["sessions"].append(session)

        # Update relationship
        if not self.relationship["first_met"]:
            self.relationship["first_met"] = datetime.now().isoformat()
        self.relationship["last_interaction"] = datetime.now().isoformat()

        self._save_all()
        return session

    def add_exchange(self, user_message, persona_response, topics=None):
        """Add a message exchange to the current session."""
        if not self.sessions["sessions"]:
            self.start_session()

        current_session = self.sessions["sessions"][-1]
        exchange = {
            "timestamp": datetime.now().isoformat(),
            "user": user_message,
            "persona": persona_response,
            "topics": topics or [],
        }
        current_session["exchanges"].append(exchange)

        # Update relationship stats
        self.relationship["total_exchanges"] += 1
        self.relationship["last_interaction"] = datetime.now().isoformat()

        self._save_all()
        return exchange

    def end_session(self):
        """End the current session."""
        if self.sessions["sessions"]:
            self.sessions["sessions"][-1]["ended_at"] = datetime.now().isoformat()
            self._save_all()

    def get_recent_exchanges(self, count=15):
        """Get the most recent exchanges across all sessions."""
        all_exchanges = []
        for session in self.sessions["sessions"]:
            for ex in session["exchanges"]:
                all_exchanges.append(ex)
        return all_exchanges[-count:]

    def get_session_count(self):
        return len(self.sessions["sessions"])

    # ── LEARNED FACTS ──

    def add_learned_fact(self, fact, source_exchange=None):
        """Add something learned about the user or the world from conversation."""
        entry = {
            "fact": fact,
            "learned_at": datetime.now().isoformat(),
            "source": source_exchange or "conversation",
            "times_referenced": 0,
        }
        # Avoid duplicates
        for existing in self.learned["facts"]:
            if existing["fact"].lower() == fact.lower():
                return
        self.learned["facts"].append(entry)
        self._save(self.learned_file, self.learned)

    def add_inside_joke(self, joke, origin=""):
        """Add an inside joke that developed during conversation."""
        entry = {
            "joke": joke,
            "origin": origin,
            "created_at": datetime.now().isoformat(),
        }
        self.learned["inside_jokes"].append(entry)
        self._save(self.learned_file, self.learned)

    def add_shared_experience(self, experience, context=""):
        """Add a shared experience from conversation."""
        entry = {
            "experience": experience,
            "context": context,
            "timestamp": datetime.now().isoformat(),
        }
        self.learned["shared_experiences"].append(entry)
        self._save(self.learned_file, self.learned)

    def get_learned_context(self):
        """Get all learned facts formatted for prompt injection."""
        lines = []
        if self.learned["facts"]:
            lines.append("THINGS YOU'VE LEARNED ABOUT THE PERSON YOU'RE TALKING TO:")
            for f in self.learned["facts"]:
                lines.append(f"- {f['fact']}")

        if self.learned["inside_jokes"]:
            lines.append("\nINSIDE JOKES YOU SHARE:")
            for j in self.learned["inside_jokes"]:
                lines.append(f"- {j['joke']} (from: {j['origin']})")

        if self.learned["shared_experiences"]:
            lines.append("\nSHARED EXPERIENCES:")
            for e in self.learned["shared_experiences"]:
                lines.append(f"- {e['experience']}")

        return "\n".join(lines) if lines else ""

    # ── RELATIONSHIP ──

    def update_relationship(self, **kwargs):
        """Update relationship fields."""
        for key, value in kwargs.items():
            if key in self.relationship:
                self.relationship[key] = value
        self._save(self.relationship_file, self.relationship)

    def get_relationship_context(self):
        """Get relationship state formatted for prompt injection."""
        r = self.relationship
        lines = [
            f"RELATIONSHIP WITH THE PERSON YOU'RE TALKING TO:",
            f"- Closeness: {r['closeness']}/10",
            f"- Trust level: {r['trust_level']}/10",
            f"- Total conversations: {r['total_exchanges']} exchanges",
            f"- First met: {r.get('first_met', 'just now')}",
        ]
        if r.get("user_name"):
            lines.append(f"- Their name: {r['user_name']}")
        if r.get("nickname_for_user"):
            lines.append(f"- Your nickname for them: {r['nickname_for_user']}")
        if r.get("emotional_state"):
            lines.append(f"- How you feel right now: {r['emotional_state']}")
        for note in r.get("notes", []):
            lines.append(f"- Note: {note}")
        return "\n".join(lines)

    def evolve_closeness(self, delta):
        """Adjust closeness by delta (-1, +1, etc). Clamps to 1-10."""
        self.relationship["closeness"] = max(1, min(10, self.relationship["closeness"] + delta))
        self._save(self.relationship_file, self.relationship)

    def _save_all(self):
        self._save(self.sessions_file, self.sessions)
        self._save(self.learned_file, self.learned)
        self._save(self.relationship_file, self.relationship)

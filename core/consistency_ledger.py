import json
import os


class ConsistencyLedger:
    """Tracks established facts across generation calls to prevent contradictions."""

    def __init__(self):
        self.facts = []          # list of established facts
        self.names = {}          # name -> role/context
        self.places = {}         # place name -> description
        self.timeline = []       # (era, event_summary)
        self.relationships = {}  # person_name -> relationship_type + status

    def add_fact(self, fact, source="unknown"):
        """Add an established fact."""
        entry = {"fact": fact, "source": source}
        if entry not in self.facts:
            self.facts.append(entry)

    def add_name(self, name, role, context=""):
        """Register a named person."""
        if name not in self.names:
            self.names[name] = {"role": role, "context": context}
        else:
            # Enrich existing entry
            self.names[name]["context"] += f"; {context}"

    def add_place(self, name, description=""):
        """Register a named place."""
        if name not in self.places:
            self.places[name] = description

    def add_timeline_event(self, era, event):
        """Add a timeline event."""
        self.timeline.append({"era": era, "event": event})

    def add_relationship(self, person, rel_type, status="active", notes=""):
        """Track a relationship and its status."""
        if person not in self.relationships:
            self.relationships[person] = []
        self.relationships[person].append({
            "type": rel_type, "status": status, "notes": notes
        })

    def get_context_block(self, max_facts=40):
        """Build a context injection block for prompts."""
        lines = ["ESTABLISHED FACTS (must remain consistent):"]

        # Core facts
        for f in self.facts[:max_facts]:
            lines.append(f"- {f['fact']}")

        # Named people
        if self.names:
            lines.append("\nNAMED PEOPLE:")
            for name, info in self.names.items():
                lines.append(f"- {name}: {info['role']} {info.get('context', '')}")

        # Named places
        if self.places:
            lines.append("\nNAMED PLACES:")
            for name, desc in self.places.items():
                lines.append(f"- {name}: {desc}")

        # Timeline anchors
        if self.timeline:
            lines.append("\nTIMELINE ANCHORS:")
            for t in self.timeline[-15:]:
                lines.append(f"- [{t['era']}] {t['event']}")

        return "\n".join(lines)

    def get_relationship_summary(self, person_name=None):
        """Get relationship status summary, optionally filtered by person."""
        if person_name:
            return self.relationships.get(person_name, [])
        return self.relationships

    def check_conflict(self, proposed_fact):
        """Simple conflict check against established facts. Returns conflicts found."""
        conflicts = []
        proposed_lower = proposed_fact.lower()
        for f in self.facts:
            existing = f["fact"].lower()
            # Very basic check — look for direct negation or contradiction markers
            if "not " + existing in proposed_lower or existing.replace("not ", "") in proposed_lower:
                conflicts.append(f["fact"])
        return conflicts

    def save(self, filepath):
        """Save ledger to JSON."""
        data = {
            "facts": self.facts,
            "names": self.names,
            "places": self.places,
            "timeline": self.timeline,
            "relationships": self.relationships,
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def load(self, filepath):
        """Load ledger from JSON."""
        if not os.path.exists(filepath):
            return
        with open(filepath, "r") as f:
            data = json.load(f)
        self.facts = data.get("facts", [])
        self.names = data.get("names", {})
        self.places = data.get("places", {})
        self.timeline = data.get("timeline", [])
        self.relationships = data.get("relationships", {})

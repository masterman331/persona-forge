import json
import os
from datetime import datetime


class PersonaFile:
    """Manages the persona output directory and all its files."""

    def __init__(self, persona_name, base_dir="output"):
        self.name = persona_name
        self.base_dir = os.path.join(base_dir, persona_name.replace(" ", "_"))
        self.dirs = {
            "root": self.base_dir,
            "eras": os.path.join(self.base_dir, "eras"),
            "relationships": os.path.join(self.base_dir, "relationships"),
            "memory": os.path.join(self.base_dir, "memory"),
            "knowledge": os.path.join(self.base_dir, "knowledge"),
            "psychology": os.path.join(self.base_dir, "psychology"),
            "language": os.path.join(self.base_dir, "language"),
            "opinions": os.path.join(self.base_dir, "opinions"),
        }
        for d in self.dirs.values():
            os.makedirs(d, exist_ok=True)

    def write(self, category, filename, data):
        """Write data to a file in the specified category directory."""
        if category not in self.dirs:
            raise ValueError(f"Unknown category: {category}. Valid: {list(self.dirs.keys())}")
        path = os.path.join(self.dirs[category], filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return path

    def read(self, category, filename):
        """Read data from a file in the specified category directory."""
        path = os.path.join(self.dirs[category], filename)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def write_root(self, filename, data):
        """Write to the persona root directory."""
        path = os.path.join(self.base_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return path

    def read_root(self, filename):
        """Read from the persona root directory."""
        path = os.path.join(self.base_dir, filename)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def file_exists(self, category, filename):
        """Check if a file exists."""
        path = os.path.join(self.dirs[category], filename)
        return os.path.exists(path)

    def list_files(self, category=None):
        """List all files, optionally filtered by category."""
        if category:
            d = self.dirs.get(category, self.base_dir)
            return [os.path.join(d, f) for f in os.listdir(d) if f.endswith(".json")]
        all_files = []
        for cat, d in self.dirs.items():
            for f in os.listdir(d):
                if f.endswith(".json"):
                    all_files.append(os.path.join(d, f))
        return all_files

    def get_identity(self):
        """Quick access to identity data."""
        return self.read_root("identity.json")

    def get_blueprint(self):
        """Quick access to blueprint data."""
        return self.read_root("blueprint.json")

    def write_identity(self, data):
        """Write identity with metadata."""
        data["_meta"] = {
            "generated_at": datetime.now().isoformat(),
            "forge_version": "0.1.0",
        }
        return self.write_root("identity.json", data)

    def write_blueprint(self, data):
        return self.write_root("blueprint.json", data)

    def write_era(self, era_num, data, label=""):
        filename = f"era_{era_num:02d}_{label.replace(' ', '_').lower()}.json" if label else f"era_{era_num:02d}.json"
        return self.write("eras", filename, data)

    def write_relationships(self, rel_type, data):
        return self.write("relationships", f"{rel_type}.json", data)

    def write_memory(self, mem_type, data):
        return self.write("memory", f"{mem_type}.json", data)

    def write_knowledge(self, know_type, data):
        return self.write("knowledge", f"{know_type}.json", data)

    def write_psychology(self, psy_type, data):
        return self.write("psychology", f"{psy_type}.json", data)

    def write_language(self, lang_type, data):
        return self.write("language", f"{lang_type}.json", data)

    def write_opinions(self, data):
        return self.write("opinions", "timeline.json", data)

    def total_size(self):
        """Total size of all persona files in bytes."""
        total = 0
        for f in self.list_files():
            total += os.path.getsize(f)
        # Include root files
        for f in os.listdir(self.base_dir):
            fp = os.path.join(self.base_dir, f)
            if os.path.isfile(fp):
                total += os.path.getsize(fp)
        return total

    def summary(self):
        """Return a summary of what's been generated so far."""
        return {
            "name": self.name,
            "files": len(self.list_files()),
            "total_size_kb": round(self.total_size() / 1024, 1),
            "categories": {
                cat: len([f for f in os.listdir(d) if f.endswith(".json")])
                for cat, d in self.dirs.items()
            },
        }

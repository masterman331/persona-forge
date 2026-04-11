import time
import json
import os
from datetime import datetime
from config import LOGS_DIR


class ForgeLogger:
    """Rich logging for Persona Forge — tracks every damn thing."""

    COLORS = {
        "HEADER": "\033[95m",
        "BLUE": "\033[94m",
        "CYAN": "\033[96m",
        "GREEN": "\033[92m",
        "YELLOW": "\033[93m",
        "RED": "\033[91m",
        "BOLD": "\033[1m",
        "DIM": "\033[2m",
        "END": "\033[0m",
    }

    def __init__(self, persona_name=None):
        self.persona_name = persona_name or "unknown"
        self.session_start = time.time()
        self.events = []
        self.phase_stats = {}
        self._current_phase = None
        self._phase_start_time = None
        self.files_written = []
        self.api_calls_logged = 0

        os.makedirs(LOGS_DIR, exist_ok=True)
        self.log_file = os.path.join(
            LOGS_DIR,
            f"{self.persona_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

    def _ts(self):
        return datetime.now().strftime("%H:%M:%S")

    def _elapsed(self):
        return f"{time.time() - self.session_start:.1f}s"

    def _color(self, key):
        return self.COLORS.get(key, "")

    def banner(self):
        c = self._color
        print(f"\n{c('BOLD')}{c('CYAN')}{'='*60}{c('END')}")
        print(f"{c('BOLD')}{c('CYAN')}  PERSONA FORGE — Generating: {self.persona_name}{c('END')}")
        print(f"{c('BOLD')}{c('CYAN')}  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{c('END')}")
        print(f"{c('BOLD')}{c('CYAN')}{'='*60}{c('END')}\n")

    def phase_start(self, phase_name):
        self._current_phase = phase_name
        self._phase_start_time = time.time()
        c = self._color
        print(f"{c('BOLD')}{c('YELLOW')}[{self._ts()}] {c('END')}{c('BOLD')}▶ PHASE: {phase_name}{c('END')}")

    def phase_end(self, summary=""):
        if self._phase_start_time:
            elapsed = time.time() - self._phase_start_time
            self.phase_stats[self._current_phase] = {
                "duration": round(elapsed, 2),
                "summary": summary,
            }
            c = self._color
            print(f"{c('GREEN')}[{self._ts()}] ✓ PHASE DONE: {self._current_phase} ({elapsed:.1f}s){c('END')}")
            if summary:
                print(f"{c('DIM')}  └ {summary}{c('END')}")
            self._current_phase = None
            self._phase_start_time = None

    def step(self, msg):
        c = self._color
        print(f"{c('BLUE')}[{self._ts()}] {c('END')}{c('BOLD')}►{c('END')} {msg}")
        self.events.append({"time": self._ts(), "elapsed": self._elapsed(), "type": "step", "msg": msg})

    def api_call(self, call_num, prompt_preview, elapsed, tokens=0):
        self.api_calls_logged += 1
        c = self._color
        print(f"{c('CYAN')}[{self._ts()}] {c('END')}⚡ API call #{call_num} — {elapsed:.1f}s — ~{tokens} tokens")
        print(f"{c('DIM')}  └ Prompt: {prompt_preview[:100]}...{c('END')}")
        self.events.append({
            "time": self._ts(), "elapsed": self._elapsed(), "type": "api",
            "call": call_num, "elapsed_s": round(elapsed, 2),
            "tokens": tokens, "prompt_preview": prompt_preview[:100],
        })

    def file_written(self, path, size_bytes):
        c = self._color
        size_kb = size_bytes / 1024
        print(f"{c('GREEN')}[{self._ts()}] {c('END')}💾 Written: {os.path.basename(path)} ({size_kb:.1f} KB)")
        self.files_written.append({
            "path": path, "size_bytes": size_bytes,
            "time": self._ts(), "elapsed": self._elapsed(),
        })

    def info(self, msg):
        c = self._color
        print(f"{c('DIM')}[{self._ts()}]   {msg}{c('END')}")

    def warn(self, msg):
        c = self._color
        print(f"{c('YELLOW')}[{self._ts()}] ⚠ {msg}{c('END')}")

    def error(self, msg):
        c = self._color
        print(f"{c('RED')}[{self._ts()}] ✗ {msg}{c('END')}")

    def question(self, q):
        c = self._color
        print(f"\n{c('BOLD')}{c('HEADER')}[INTERVIEW] {q}{c('END')}")

    def user_input(self, val):
        c = self._color
        print(f"{c('DIM')}  ← {val}{c('END')}")

    def final_report(self, api_stats):
        total_elapsed = time.time() - self.session_start
        c = self._color

        print(f"\n{c('BOLD')}{c('CYAN')}{'='*60}{c('END')}")
        print(f"{c('BOLD')}{c('CYAN')}  GENERATION COMPLETE — {self.persona_name}{c('END')}")
        print(f"{c('BOLD')}{c('CYAN')}{'='*60}{c('END')}\n")

        print(f"  Total time:       {total_elapsed:.1f}s")
        print(f"  API calls:        {api_stats.get('total_calls', '?')}")
        print(f"  API time:         {api_stats.get('total_time_seconds', '?')}s")
        print(f"  Avg per call:     {api_stats.get('avg_time_per_call', '?')}s")
        print(f"  Tokens generated: ~{api_stats.get('total_tokens_estimated', '?')}")
        print(f"  Files written:    {len(self.files_written)}")
        print(f"  Total file size:  {sum(f['size_bytes'] for f in self.files_written)/1024:.1f} KB")

        print(f"\n  {c('BOLD')}Phase Breakdown:{c('END')}")
        for phase, stats in self.phase_stats.items():
            print(f"    {phase:25s} {stats['duration']:6.1f}s")

        print(f"\n  {c('BOLD')}Files:{c('END')}")
        for f in self.files_written:
            print(f"    {os.path.basename(f['path']):35s} {f['size_bytes']/1024:.1f} KB")

        if api_stats.get('errors', 0) > 0:
            print(f"\n  {c('RED')}Errors: {api_stats['errors']}{c('END')}")

        print()

    def save_log(self):
        log_data = {
            "persona": self.persona_name,
            "session_start": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "total_elapsed": round(time.time() - self.session_start, 2),
            "phase_stats": self.phase_stats,
            "events": self.events,
            "files_written": self.files_written,
            "api_calls_logged": self.api_calls_logged,
        }
        with open(self.log_file, "w") as f:
            json.dump(log_data, f, indent=2, default=str)
        return self.log_file

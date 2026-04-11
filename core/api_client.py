import requests
import time
import json
from config import API_URL, MODEL, DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE


class APIClient:
    """Handles all communication with the zai:cloud API (Ollama-compatible)."""

    def __init__(self):
        self.base_url = API_URL
        self.model = MODEL
        self.call_count = 0
        self.total_tokens_est = 0
        self.total_time = 0.0
        self.call_log = []

    def generate(self, prompt, system_prompt=None, temperature=None, max_tokens=None):
        """Send a generation request to the API. Retries forever until success."""
        temperature = temperature or DEFAULT_TEMPERATURE
        max_tokens = max_tokens or DEFAULT_MAX_TOKENS

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }

        if system_prompt:
            payload["system"] = system_prompt

        attempt = 0
        while True:
            attempt += 1
            start = time.time()
            try:
                resp = requests.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=300
                )
                resp.raise_for_status()
                data = resp.json()
                elapsed = time.time() - start

                text = data.get("response", "")
                tokens_eval = data.get("eval_count", len(text.split()))
                tokens_prompt = data.get("prompt_eval_count", 0)

                self.call_count += 1
                self.total_time += elapsed
                self.total_tokens_est += tokens_eval

                entry = {
                    "call": self.call_count,
                    "elapsed": round(elapsed, 2),
                    "tokens_generated": tokens_eval,
                    "tokens_prompt": tokens_prompt,
                    "prompt_preview": prompt[:120] + "..." if len(prompt) > 120 else prompt,
                }
                self.call_log.append(entry)

                if attempt > 1:
                    print(f"\033[92m  ✓ API call succeeded on attempt {attempt}\033[0m")

                return text

            except (requests.exceptions.RequestException, ValueError) as e:
                elapsed = time.time() - start
                entry = {
                    "call": self.call_count + 1,
                    "elapsed": round(elapsed, 2),
                    "error": str(e),
                    "attempt": attempt,
                    "prompt_preview": prompt[:120] + "..." if len(prompt) > 120 else prompt,
                }
                self.call_log.append(entry)

                print(f"\033[93m  ⚠ API call failed (attempt {attempt}): {e}\033[0m")
                print(f"\033[93m  ⚠ Retrying in 3 seconds...\033[0m")
                time.sleep(3)

    def generate_json(self, prompt, system_prompt=None, temperature=None, max_tokens=None):
        """Generate and parse as JSON. Handles markdown code fences."""
        raw = self.generate(prompt, system_prompt, temperature, max_tokens)
        return self._extract_json(raw)

    def _extract_json(self, text):
        """Extract JSON from response, handling code fences."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = lines[1:]  # skip opening ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON object or array in the text
            for start_char, end_char in [("{", "}"), ("[", "]")]:
                start = text.find(start_char)
                end = text.rfind(end_char)
                if start != -1 and end != -1 and end > start:
                    try:
                        return json.loads(text[start:end+1])
                    except json.JSONDecodeError:
                        continue
            raise ValueError(f"Could not parse JSON from response: {text[:200]}")

    def get_stats(self):
        """Return cumulative API statistics."""
        return {
            "total_calls": self.call_count,
            "total_time_seconds": round(self.total_time, 2),
            "avg_time_per_call": round(self.total_time / max(self.call_count, 1), 2),
            "total_tokens_estimated": self.total_tokens_est,
            "errors": sum(1 for e in self.call_log if "error" in e),
        }

    def get_call_log(self):
        """Return the full call log."""
        return self.call_log.copy()

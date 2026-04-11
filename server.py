#!/usr/bin/env python3
"""Persona Forge HTTP API Server.

Run with: python server.py [--port 8888] [--host 0.0.0.0]

Endpoints:
  GET  /personas              - List available personas
  GET  /personas/{name}       - Get persona info
  POST /chat                  - Send a message to a persona
  GET  /stats/{name}          - Get stats for a persona
  GET  /mood/{name}           - Get emotional state
  GET  /memories/{name}       - Get memories
  GET  /knowledge/{name}      - Get knowledge
  GET  /profile/{name}        - Get user profile
  POST /crystallize/{name}    - Force memory crystallization
  POST /update-knowledge/{name} - Force knowledge update
"""

import sys
import os
import json
import argparse
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.api_client import APIClient
from core.persona_file import PersonaFile
from core.conversation_store import ConversationStore
from core.chat_context import ChatContextBuilder
from core.emotional_engine import EmotionalEngine
from core.associative_memory import AssociativeMemory
from core.vulnerability_gate import VulnerabilityGate
from core.user_state import UserStateTracker
from core.user_profile import UserProfile
from core.dopamine_engine import DopamineEngine
from core.response_parser import ResponseParser
from core.memory_crystallizer import MemoryCrystallizer
from core.knowledge_updater import KnowledgeUpdater
from core.dream_engine import DreamEngine
from core.miscommunication_engine import MiscommunicationEngine
from core.greeting_engine import GreetingEngine, StreakTracker
from config import OUTPUT_DIR, SERVER_HOST, SERVER_PORT


class PersonaSession:
    """Manages a loaded persona session."""

    def __init__(self, persona_name: str):
        self.pf = PersonaFile(persona_name, base_dir=OUTPUT_DIR)
        self.identity = self.pf.get_identity()
        if not self.identity:
            raise ValueError(f"Could not load persona: {persona_name}")

        self.name = self.identity.get("name", persona_name)
        self.api = APIClient()

        # Initialize all systems
        self.conv = ConversationStore(self.name)
        self.emotion = EmotionalEngine(self.name)
        self.memory = AssociativeMemory(self.pf)
        self.gate = VulnerabilityGate(self.pf, self.conv)
        self.user_state = UserStateTracker(self.name)
        self.user_profile = UserProfile(self.name)
        self.dopamine = DopamineEngine(self.name)

        # New systems
        self.crystallizer = MemoryCrystallizer(self.pf, self.conv, self.emotion, self.api)
        self.knowledge_updater = KnowledgeUpdater(self.pf, self.conv, self.api)
        self.dream_engine = DreamEngine(self.pf, self.emotion, self.conv, self.api)
        self.miscomm = MiscommunicationEngine(self.pf, self.conv, self.emotion, self.api)
        self.greeting_engine = GreetingEngine(self.pf, self.conv, self.emotion, self.api)
        self.streak = StreakTracker(self.name, self.conv)

        # Decay on session start
        if self.conv.get_session_count() > 0:
            self.emotion.decay_towards_baseline()

        self.ctx = ChatContextBuilder(
            self.pf, self.conv, self.emotion, self.memory,
            self.gate, self.user_state, self.user_profile, self.dopamine
        )

    def chat(self, user_message: str, debug: bool = False) -> dict:
        """Process a chat message and return response."""
        result = {
            "message": "",
            "internal": {},
            "updates": {},
            "debug": {}
        }

        # Start session if needed
        if not self.conv.sessions["sessions"] or self.conv.sessions["sessions"][-1].get("ended_at"):
            self.conv.start_session()
            self.streak.record_session()

            # Check for dream
            dream = self.dream_engine.get_dream_for_session_start()
            if dream.get("dreamt") and dream.get("would_mention"):
                result["dream"] = dream

        # Check for miscommunication
        should_miscomm, miscomm_details = self.miscomm.should_miscommunicate(user_message)

        # Build context and generate
        prompt, system = self.ctx.build_full_prompt(user_message)
        raw_response = self.api.generate(prompt, system_prompt=system, temperature=0.9)

        parsed = ResponseParser.parse(raw_response)
        parsed = ResponseParser.validate(parsed)

        message = parsed.get("message_to_user", raw_response.strip())

        # Apply miscommunication if triggered
        if should_miscomm and miscomm_details:
            import random
            miscomm_type = miscomm_details.get('potential_miscommunication', {}).get('type', 'tone_misread')
            strength = miscomm_details.get('miscommunication_strength', 'subtle')
            miscomm_hint = self.miscomm.get_miscommunication_response(miscomm_type, strength)
            if miscomm_hint and random.random() < 0.4:
                message = f"{miscomm_hint} {message}"

        result["message"] = message

        if debug:
            result["debug"]["raw_response"] = raw_response[:500]
            result["debug"]["parsed"] = parsed

        # Save exchange
        self.conv.add_exchange(user_message, message)

        # Update systems
        updates = []

        # Emotional updates
        emotion_deltas = parsed.get("update_parameters", {}).get("emotion_deltas", {})
        if emotion_deltas:
            self.emotion.update_dimensions(emotion_deltas)
            updates.append("emotion")

        # Physical state
        new_physical = parsed.get("update_parameters", {}).get("physical_state_change")
        if new_physical:
            self.emotion.update_physical_from_response(new_physical)
            updates.append("physical")

        # Closeness
        closeness_delta = parsed.get("update_parameters", {}).get("closeness_delta", 0)
        if closeness_delta:
            self.conv.evolve_closeness(closeness_delta)
            updates.append("closeness")

        # Trust
        trust_delta = parsed.get("update_parameters", {}).get("trust_delta", 0)
        if trust_delta:
            new_trust = max(1, min(10, self.conv.relationship.get("trust_level", 1) + trust_delta))
            self.conv.update_relationship(trust_level=new_trust)

        # Update emotional state from exchange
        closeness = self.conv.relationship.get("closeness", 1)
        self.emotion.update_from_exchange(user_message, message, closeness)

        # User state
        user_assessment = parsed.get("user_assessment", {})
        if user_assessment:
            self.user_state.update_from_assessment(user_assessment)

        # Profile updates
        profile_updates = parsed.get("profile_updates", {})
        if profile_updates:
            self.user_profile.update_from_response(profile_updates)
            updates.append("profile")

        # Hook tracking
        internal = parsed.get("internal", {})
        hook_used = internal.get("hook_used")
        if hook_used:
            self.dopamine.record_hook_used(hook_used)
            effectiveness = internal.get("hook_effectiveness", 0.5)
            self.dopamine.record_hook_effectiveness(hook_used, effectiveness > 0.5)
            updates.append(f"hook:{hook_used}")

        # Learned facts
        learned = parsed.get("learned", {})
        for fact in learned.get("new_facts", []):
            self.conv.add_learned_fact(fact)
            updates.append(f"learned:{fact[:30]}")

        if learned.get("inside_joke"):
            self.conv.add_inside_joke(learned["inside_joke"], origin=user_message[:50])
            updates.append("inside_joke")

        # Memory crystallization
        crystal_result = self.crystallizer.crystallize(user_message, message)
        if crystal_result.get("memory_created"):
            updates.append(f"memory:{crystal_result['memory_created']['type']}")

        # Engagement calculation
        self.dopamine.calculate_engagement(self.user_state, self.conv)
        self.dopamine.calculate_addiction_score()

        result["updates"] = updates
        result["internal"] = {
            "felt": internal.get("felt"),
            "aim": internal.get("aim"),
            "hook_used": hook_used
        }

        # Save dream if dreamt
        if result.get("dream") and result["dream"].get("dreamt"):
            self.dream_engine.save_dream(result["dream"])

        return result

    def get_stats(self) -> dict:
        return {
            "name": self.name,
            "exchanges": self.conv.relationship["total_exchanges"],
            "sessions": self.conv.get_session_count(),
            "closeness": self.conv.relationship["closeness"],
            "trust": self.conv.relationship["trust_level"],
            "engagement": self.dopamine.state.get("user_engagement_level", 3),
            "addiction_score": self.dopamine.state.get("addiction_score", 0),
            "streak": self.streak.get_streak_info(),
            "memory_count": self.crystallizer.get_memory_summary(),
            "knowledge_count": self.knowledge_updater.get_knowledge_summary(),
            "api_calls": self.api.get_stats()
        }

    def get_mood(self) -> dict:
        return {
            "persona": self.emotion.state["dimensions"],
            "physical": self.emotion.state.get("physical_state"),
            "mood_descriptor": self.emotion.get_mood_descriptor(),
            "user_state": self.user_state.state
        }

    def get_memories(self) -> dict:
        return {
            "core": self.pf.read("memory", "core.json") or [],
            "signature": self.pf.read("memory", "signature.json") or [],
            "sensory": self.pf.read("memory", "sensory.json") or [],
            "dormant": self.pf.read("memory", "dormant.json") or [],
            "recently_crystallized": self.crystallizer.get_recently_crystallized()
        }

    def get_knowledge(self) -> dict:
        return {
            "expertise": self.pf.read("knowledge", "expertise.json") or [],
            "casual": self.pf.read("knowledge", "casual.json") or [],
            "gaps": self.pf.read("knowledge", "gaps.json") or [],
            "incorrect": self.pf.read("knowledge", "incorrect.json") or []
        }

    def get_profile(self) -> dict:
        return {
            "profile": self.user_profile.get_full_profile(),
            "summary": self.user_profile.get_profile_summary()
        }


# Global session cache
sessions = {}


def get_session(persona_name: str) -> PersonaSession:
    """Get or create a persona session."""
    if persona_name not in sessions:
        sessions[persona_name] = PersonaSession(persona_name)
    return sessions[persona_name]


class PersonaAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Persona Forge API."""

    def log_message(self, format, *args):
        """Custom logging."""
        print(f"[{datetime.now().isoformat()}] {args[0]}")

    def send_json(self, data, status=200):
        """Send JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, ensure_ascii=False).encode())

    def send_error_json(self, message, status=400):
        """Send error as JSON."""
        self.send_json({"error": message}, status)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        try:
            if path == "/personas":
                self.handle_list_personas()
            elif path.startswith("/personas/"):
                name = path.split("/")[-1]
                self.handle_get_persona(name)
            elif path.startswith("/stats/"):
                name = path.split("/")[-1]
                self.handle_stats(name)
            elif path.startswith("/mood/"):
                name = path.split("/")[-1]
                self.handle_mood(name)
            elif path.startswith("/memories/"):
                name = path.split("/")[-1]
                self.handle_memories(name)
            elif path.startswith("/knowledge/"):
                name = path.split("/")[-1]
                self.handle_knowledge(name)
            elif path.startswith("/profile/"):
                name = path.split("/")[-1]
                self.handle_profile(name)
            elif path == "/health":
                self.send_json({"status": "ok", "timestamp": datetime.now().isoformat()})
            else:
                self.send_error_json("Not found", 404)
        except Exception as e:
            self.send_error_json(str(e), 500)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        # Read body
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode() if content_length > 0 else "{}"

        try:
            data = json.loads(body) if body else {}
        except:
            self.send_error_json("Invalid JSON", 400)
            return

        try:
            if path == "/chat":
                self.handle_chat(data)
            elif path.startswith("/crystallize/"):
                name = path.split("/")[-1]
                self.handle_crystallize(name, data)
            elif path.startswith("/update-knowledge/"):
                name = path.split("/")[-1]
                self.handle_update_knowledge(name)
            else:
                self.send_error_json("Not found", 404)
        except Exception as e:
            self.send_error_json(str(e), 500)

    def handle_list_personas(self):
        """List available personas."""
        if not os.path.exists(OUTPUT_DIR):
            self.send_json([])
            return

        personas = []
        for name in os.listdir(OUTPUT_DIR):
            path = os.path.join(OUTPUT_DIR, name)
            if os.path.isdir(path) and os.path.exists(os.path.join(path, "identity.json")):
                try:
                    pf = PersonaFile(name, base_dir=OUTPUT_DIR)
                    identity = pf.get_identity()
                    personas.append({
                        "id": name,
                        "name": identity.get("name", name),
                        "age": identity.get("age"),
                        "location": identity.get("birth_location")
                    })
                except:
                    pass

        self.send_json(personas)

    def handle_get_persona(self, name: str):
        """Get persona details."""
        session = get_session(name)
        self.send_json({
            "identity": session.identity,
            "stats": session.get_stats()
        })

    def handle_chat(self, data: dict):
        """Handle chat message."""
        persona = data.get("persona") or data.get("name")
        message = data.get("message")
        debug = data.get("debug", False)

        if not persona:
            self.send_error_json("Missing 'persona' field")
            return
        if not message:
            self.send_error_json("Missing 'message' field")
            return

        session = get_session(persona)
        result = session.chat(message, debug=debug)
        self.send_json(result)

    def handle_stats(self, name: str):
        session = get_session(name)
        self.send_json(session.get_stats())

    def handle_mood(self, name: str):
        session = get_session(name)
        self.send_json(session.get_mood())

    def handle_memories(self, name: str):
        session = get_session(name)
        self.send_json(session.get_memories())

    def handle_knowledge(self, name: str):
        session = get_session(name)
        self.send_json(session.get_knowledge())

    def handle_profile(self, name: str):
        session = get_session(name)
        self.send_json(session.get_profile())

    def handle_crystallize(self, name: str, data: dict):
        """Force memory crystallization."""
        session = get_session(name)
        user_msg = data.get("user_message", "")
        persona_msg = data.get("persona_message", "")

        if user_msg and persona_msg:
            result = session.crystallizer.crystallize(user_msg, persona_msg)
        else:
            result = {"error": "Need user_message and persona_message"}

        self.send_json(result)

    def handle_update_knowledge(self, name: str):
        """Force knowledge update."""
        session = get_session(name)
        result = session.knowledge_updater.analyze_and_update()
        self.send_json(result)


def main():
    parser = argparse.ArgumentParser(description="Persona Forge API Server")
    parser.add_argument("--host", default=SERVER_HOST, help="Host to bind to")
    parser.add_argument("--port", type=int, default=SERVER_PORT, help="Port to bind to")
    args = parser.parse_args()

    server = HTTPServer((args.host, args.port), PersonaAPIHandler)

    print(f"\n{'='*60}")
    print(f"  PERSONA FORGE API SERVER")
    print(f"{'='*60}")
    print(f"\n  Running on: http://{args.host}:{args.port}")
    print(f"\n  Endpoints:")
    print(f"    GET  /personas              - List personas")
    print(f"    POST /chat                  - Send message")
    print(f"    GET  /stats/{{name}}         - Get stats")
    print(f"    GET  /mood/{{name}}           - Get mood")
    print(f"    GET  /memories/{{name}}       - Get memories")
    print(f"    GET  /knowledge/{{name}}      - Get knowledge")
    print(f"    GET  /profile/{{name}}        - Get user profile")
    print(f"    GET  /health                - Health check")
    print("\n  Example:")
    print("    curl -X POST http://localhost:%d/chat" % args.port)
    print("      -H 'Content-Type: application/json'")
    print("      -d '{\"persona\": \"Anna_Liebig\", \"message\": \"hey!\"}'")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()

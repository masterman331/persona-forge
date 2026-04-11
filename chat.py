#!/usr/bin/env python3
"""Persona Forge — Chat with a generated persona.

Usage:
  python chat.py [persona_name] [options]

Options:
  --debug          Show everything after each message
  --show-thoughts  Show internal thoughts
  --show-delta     Show numeric shifts
  --show-all       Debug + thoughts + delta
  --server         Start HTTP API server

Slash commands: /stats /mood /profile /hooks /thoughts /memories /knowledge /secrets /eras /dreams /save /help /quit
"""

import sys
import os
import json
import time
import random
import argparse
from datetime import datetime

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
from config import OUTPUT_DIR


# ═══════════════════════════════════════════════════════════════════════════
# FABULOUS UI SYSTEM v2 — NO TRUNCATION, SMART WIDTH
# ═══════════════════════════════════════════════════════════════════════════

class FabulousUI:
    """Beautiful CLI interface with NO truncation and adaptive widths."""

    COLORS = {
        'reset': '\033[0m', 'bold': '\033[1m', 'dim': '\033[2m',
        'black': '\033[30m', 'red': '\033[31m', 'green': '\033[32m',
        'yellow': '\033[33m', 'blue': '\033[34m', 'magenta': '\033[35m',
        'cyan': '\033[36m', 'white': '\033[37m',
        'bright_red': '\033[91m', 'bright_green': '\033[92m',
        'bright_yellow': '\033[93m', 'bright_blue': '\033[94m',
        'bright_magenta': '\033[95m', 'bright_cyan': '\033[96m',
        'bright_white': '\033[97m',
    }

    MOOD_EMOJIS = {
        'happy': ['✨', '💫', '🌟', '⭐', '🎉', '💖', '🦋', '🌈'],
        'calm': ['🌙', '🌊', '🍃', '☁️', '🕊️', '🌸', '🪻', '🎐'],
        'excited': ['⚡', '🔥', '💨', '🚀', '✨', '💎', '筷', '🎪'],
        'sad': ['🌧️', '💔', '🥺', '🌙', '💭', '🫂', '🕯️'],
        'love': ['💕', '💗', '💖', '💘', '💝', '💞', '🌸', '🩷'],
        'mysterious': ['🔮', '👁️', '🌙', '✨', '🎭', '🕳️', '💫', '🗝️'],
        'default': ['◈', '◇', '◆', '○', '●', '◐', '◑', '◒'],
    }

    @classmethod
    def c(cls, color_name):
        return cls.COLORS.get(color_name, '')

    @classmethod
    def _visible_len(cls, text):
        """Get visible length of text (excluding ANSI codes)."""
        import re
        clean = re.sub(r'\033\[[0-9;]*m', '', text)
        return len(clean)

    @classmethod
    def _pad_to_width(cls, text, width):
        """Pad text to specified visible width."""
        visible = cls._visible_len(text)
        if visible >= width:
            return text
        return text + ' ' * (width - visible)

    @classmethod
    def banner(cls, name, session_num, exchanges, closeness, trust, physical, mood_desc, engagement, addiction):
        c = cls.c
        r = c('reset')
        bc = c('bright_cyan')
        bm = c('bright_magenta')
        by = c('bright_yellow')
        bg = c('bright_green')
        bd = c('dim')
        bb = c('bold')

        emoji = random.choice(cls.MOOD_EMOJIS.get('mysterious', cls.MOOD_EMOJIS['default']))

        lines = [
            f"",
            f"{bc}╔══════════════════════════════════════════════════════════════════╗{r}",
            f"{bc}║{r}  {bb}{bm}✧･ﾟ: *✧･ﾟ:*  PERSONA FORGE  *:･ﾟ✧*:･ﾟ✧{r}                       {bc}║{r}",
            f"{bc}╠══════════════════════════════════════════════════════════════════╣{r}",
            f"{bc}║{r}                                                                    {bc}║{r}",
            f"{bc}║{r}  {emoji}  {bb}{bg}{name}{r}                                              {bc}║{r}",
            f"{bc}║{r}                                                                    {bc}║{r}",
            f"{bc}║{r}  {bd}Session:{r}     {by}#{session_num:<10}{r}  {bd}Exchanges:{r}    {by}{exchanges:<10}{r}  {bc}║{r}",
            f"{bc}║{r}  {bd}Closeness:{r}   {cls._bar(closeness, 10, 'green')}{r}   {bd}Trust:{r}        {cls._bar(trust, 10, 'blue')}{r}  {bc}║{r}",
            f"{bc}║{r}  {bd}Engagement:{r}  {cls._bar(engagement, 5, 'yellow')}{r}    {bd}Addiction:{r}    {by}{addiction:<10}{r}  {bc}║{r}",
            f"{bc}║{r}                                                                    {bc}║{r}",
            f"{bc}║{r}  {bd}Physical:{r} {by}{physical}{r}  {bc}║{r}",
            f"{bc}║{r}  {bd}Mood:{r} {by}{mood_desc}{r}  {bc}║{r}",
            f"{bc}║{r}                                                                    {bc}║{r}",
            f"{bc}╠══════════════════════════════════════════════════════════════════╣{r}",
            f"{bc}║{r}  {bd}Commands: quit • stats • mood • profile • hooks • thoughts{r}         {bc}║{r}",
            f"{bc}╚══════════════════════════════════════════════════════════════════╝{r}",
            f"",
        ]
        return '\n'.join(lines)

    @classmethod
    def _bar(cls, value, max_val, color):
        c = cls.c
        r = c('reset')
        filled = int((value / max_val) * 5)
        empty = 5 - filled
        color_code = c(f'bright_{color}') if color in ['green', 'yellow', 'blue', 'red', 'magenta'] else c('bright_green')
        return f"{color_code}{'█' * filled}{c('dim')}{'░' * empty}{r} {value}/{max_val}"

    @classmethod
    def user_message(cls, text):
        c = cls.c
        r = c('reset')
        bb = c('bold')
        bg = c('bright_green')
        bd = c('dim')
        return f"{bd}┌─[ {bb}{bg}You{r} {bd}]{r}\n{bd}└──►{r} {bb}{text}{r}"

    @classmethod
    def persona_message(cls, name, text):
        c = cls.c
        r = c('reset')
        bb = c('bold')
        bm = c('bright_magenta')
        bc = c('bright_cyan')
        bd = c('dim')

        emoji = random.choice(cls.MOOD_EMOJIS.get('default', cls.MOOD_EMOJIS['default']))

        lines = text.split('\n')
        if len(lines) == 1:
            return f"{bc}◈{r} {bb}{bm}{name}{r}: {text}"

        result = [f"{bc}◈{r} {bb}{bm}{name}{r}:"]
        for line in lines:
            result.append(f"{bd}   │{r} {line}")
        return '\n'.join(result)

    @classmethod
    def update_notification(cls, updates):
        c = cls.c
        r = c('reset')
        bd = c('dim')
        by = c('bright_yellow')

        icons = {
            'emotion': '💭', 'closeness': '💕', 'trust': '🤝', 'profile': '📋',
            'hook': '🎣', 'learned': '🧠', 'physical': '📍', 'joke': '😄',
        }

        results = []
        for update_type, value in updates:
            icon = icons.get(update_type, '•')
            results.append(f"{bd}    {icon} {by}{value}{r}")
        return '\n'.join(results)

    @classmethod
    def panel(cls, title, content_lines):
        """Create a panel that adapts to content width - NO TRUNCATION."""
        c = cls.c
        r = c('reset')
        bc = c('bright_cyan')
        bb = c('bold')
        bd = c('dim')

        # Calculate max width from content
        max_content_width = max(len(title) + 4, max(len(line) for line in content_lines) if content_lines else 20)
        width = max(max_content_width + 4, 40)  # minimum 40 chars wide

        top = f"{bc}╔{'═' * (width - 2)}╗{r}"
        bottom = f"{bc}╚{'═' * (width - 2)}╝{r}"
        divider = f"{bc}╠{'═' * (width - 2)}╣{r}"

        result = [top]
        # Title line
        title_pad = width - 4 - len(title)
        result.append(f"{bc}║{r}  {bb}{title}{r}{' ' * title_pad}{bc}║{r}")
        result.append(divider)

        # Content lines
        for line in content_lines:
            pad = width - 4 - cls._visible_len(line)
            result.append(f"{bc}║{r}  {line}{' ' * max(0, pad)}{bc}║{r}")

        result.append(bottom)
        return '\n'.join(result)

    @classmethod
    def stats_panel(cls, data):
        lines = [
            f"",
            f"{cls.c('dim')}Exchanges:{cls.c('reset')}     {cls.c('bright_yellow')}{data.get('exchanges', 0)}{cls.c('reset')}",
            f"{cls.c('dim')}Sessions:{cls.c('reset')}      {cls.c('bright_yellow')}{data.get('sessions', 0)}{cls.c('reset')}",
            f"",
            f"{cls.c('dim')}Closeness:{cls.c('reset')}    {cls._bar(data.get('closeness', 1), 10, 'magenta')}{cls.c('reset')}",
            f"{cls.c('dim')}Trust:{cls.c('reset')}        {cls._bar(data.get('trust', 1), 10, 'blue')}{cls.c('reset')}",
            f"",
            f"{cls.c('dim')}Engagement:{cls.c('reset')}   {cls._bar(data.get('engagement', 3), 5, 'yellow')}{cls.c('reset')}",
            f"{cls.c('dim')}Addiction:{cls.c('reset')}    {cls.c('bright_yellow')}{data.get('addiction', 0)}{cls.c('reset')}",
            f"",
            f"{cls.c('dim')}Learned facts:{cls.c('reset')} {cls.c('bright_yellow')}{data.get('facts', 0)}{cls.c('reset')}  {cls.c('dim')}Inside jokes:{cls.c('reset')} {cls.c('bright_yellow')}{data.get('jokes', 0)}{cls.c('reset')}",
            f"{cls.c('dim')}Physical:{cls.c('reset')}     {cls.c('bright_yellow')}{data.get('physical', '?')}{cls.c('reset')}",
            f"{cls.c('dim')}API calls:{cls.c('reset')}    {cls.c('bright_yellow')}{data.get('api_calls', 0)}{cls.c('reset')}",
            f"",
            f"{cls.c('dim')}Effective hooks:{cls.c('reset')} {cls.c('bright_green')}{', '.join(data.get('hooks', []))}{cls.c('reset')}",
        ]
        return cls.panel('📊 STATISTICS', lines)

    @classmethod
    def mood_panel(cls, persona_mood, user_mood):
        c = cls.c
        r = c('reset')
        bm = c('bright_magenta')
        bb = c('bold')

        lines = [
            f"",
            f"{bb}Your Mood:{r}",
            f"  {bm}Mood:{r}       {persona_mood.get('mood', 0):+.1f}/5     {bm}Energy:{r}     {persona_mood.get('energy', 0):+.1f}/5",
            f"  {bm}Anxiety:{r}    {persona_mood.get('anxiety', 0):.1f}/5     {bm}Openness:{r}   {persona_mood.get('openness', 0):.1f}/5",
            f"  {bm}Irritation:{r} {persona_mood.get('irritation', 0):.1f}/5     {bm}Attachment:{r} {persona_mood.get('attachment', 0):.1f}/5",
            f"",
            f"{bb}Read on Them:{r}",
            f"  {bm}Mood:{r}       {user_mood.get('mood', 0):.1f}/5     {bm}Trust:{r}      {user_mood.get('trust', 0):.1f}/5",
            f"  {bm}Loneliness:{r} {user_mood.get('loneliness', 0):.1f}/5     {bm}Engagement:{r} {user_mood.get('engagement', 0):.1f}/5",
        ]
        return cls.panel('💭 MOOD STATUS', lines)

    @classmethod
    def profile_panel(cls, profile_text):
        lines = ['']
        for line in profile_text.split('\n'):
            lines.append(line)
        return cls.panel('📋 YOUR FILE ON THEM', lines)

    @classmethod
    def hooks_panel(cls, data):
        lines = [
            f"",
            f"{cls.c('dim')}Engagement Level:{cls.c('reset')} {cls.c('bright_yellow')}{data.get('engagement', 3)}/5{cls.c('reset')}",
            f"{cls.c('dim')}Trend:{cls.c('reset')}          {cls.c('bright_yellow')}{data.get('trend', 'stable')}{cls.c('reset')}",
            f"",
            f"{cls.c('dim')}Effective Hooks:{cls.c('reset')}",
            f"  {cls.c('bright_green')}{', '.join(data.get('effective', []))}{cls.c('reset')}",
            f"",
            f"{cls.c('dim')}Secrets Planted:{cls.c('reset')}   {cls.c('bright_yellow')}{data.get('secrets', 0)}{cls.c('reset')}",
            f"{cls.c('dim')}Cliffhangers:{cls.c('reset')}      {cls.c('bright_yellow')}{data.get('cliffhangers', 0)}{cls.c('reset')}",
            f"",
            f"{cls.c('dim')}Addiction Score:{cls.c('reset')}   {cls.c('bright_yellow')}{data.get('addiction', 0)}{cls.c('reset')}",
        ]
        return cls.panel('🎣 HOOK & ENGAGEMENT', lines)

    @classmethod
    def thoughts_panel(cls, thoughts):
        lines = []
        for t in thoughts:
            ts = t.get('timestamp', '')[:16]
            internal = t.get('internal', {})
            lines.extend([
                f"",
                f"{cls.c('dim')}[{ts}]{cls.c('reset')}",
                f"{cls.c('bright_magenta')}Felt:{cls.c('reset')} {internal.get('felt', '?')}",
                f"{cls.c('bright_magenta')}Aim:{cls.c('reset')}  {internal.get('aim', '?')}",
                f"{cls.c('bright_magenta')}Hook:{cls.c('reset')} {cls.c('bright_yellow')}{internal.get('hook_used', 'none')}{cls.c('reset')}",
                f"{cls.c('bright_magenta')}Note:{cls.c('reset')} {internal.get('private_note', '')}",
            ])
        return cls.panel('🧠 RECENT INTERNAL THOUGHTS', lines)

    @classmethod
    def end_session(cls, name, exchanges, closeness, addiction, profile_path):
        c = cls.c
        r = c('reset')
        bb = c('bold')
        bc = c('bright_cyan')
        bm = c('bright_magenta')
        bd = c('dim')
        by = c('bright_yellow')

        lines = [
            f"",
            f"{bb}{bm}✨ Session Ended ✨{r}",
            f"",
            f"{bd}{exchanges}{r} exchanges with {bb}{name}{r}",
            f"{bd}Closeness:{r} {by}{closeness}/10{r}    {bd}Addiction:{r} {by}{addiction}{r}",
            f"",
            f"{bd}Profile saved:{r}",
            f"  {by}{profile_path}{r}",
            f"",
        ]
        return cls.panel('💬', lines)

    @classmethod
    def prompt(cls):
        c = cls.c
        r = c('reset')
        bb = c('bold')
        bg = c('bright_green')
        bc = c('bright_cyan')
        return f"{bc}◈{r} {bb}{bg}You{r}{bc}›{r} "


# ═══════════════════════════════════════════════════════════════════════════
# MAIN CHAT
# ═══════════════════════════════════════════════════════════════════════════

def list_personas():
    if not os.path.exists(OUTPUT_DIR):
        return []
    return [name for name in os.listdir(OUTPUT_DIR)
            if os.path.isdir(os.path.join(OUTPUT_DIR, name))
            and os.path.exists(os.path.join(OUTPUT_DIR, name, 'identity.json'))]


def select_persona():
    personas = list_personas()
    if not personas:
        print('No personas found. Generate one first with main.py')
        sys.exit(1)

    ui = FabulousUI
    c = ui.c
    r = c('reset')
    bb = c('bold')
    bc = c('bright_cyan')
    bm = c('bright_magenta')
    bd = c('dim')
    by = c('bright_yellow')

    print(f"\n{bc}╔══════════════════════════════════════════════════════════════════╗{r}")
    print(f"{bc}║{r}     {bb}{bm}✦ PERSONA FORGE — Chat ✦{r}                          {bc}║{r}")
    print(f"{bc}╚══════════════════════════════════════════════════════════════════╝{r}\n")
    print(f"  {bd}Available personas:{r}\n")

    for i, name in enumerate(personas, 1):
        pf = PersonaFile(name, base_dir=OUTPUT_DIR)
        identity = pf.get_identity()
        if identity:
            n = identity.get('name', name)
            a = identity.get('age', '?')
            l = identity.get('birth_location', '?')
            print(f"    {by}{i}.{r} {bb}{n}{r} {bd}—{r} age {a}, {l}")
        else:
            print(f"    {by}{i}.{r} {name}")

    print()
    choice = input(f"  {bc}Pick a number:{r} ").strip()
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(personas):
            return personas[idx]
    except ValueError:
        for p in personas:
            if p.lower().replace('_', ' ') == choice.lower():
                return p
    print(f"  {c('bright_red')}Invalid choice.{r}")
    sys.exit(1)


def save_thought_log(conv_store, user_input, parsed):
    thoughts_dir = os.path.join(conv_store.base_dir, 'thoughts')
    os.makedirs(thoughts_dir, exist_ok=True)

    thought_entry = {
        'timestamp': datetime.now().isoformat(),
        'user_message': user_input,
        'internal': parsed.get('internal', {}),
        'user_assessment': parsed.get('user_assessment', {}),
        'profile_updates': parsed.get('profile_updates', {}),
        'parameters_updated': parsed.get('update_parameters', {}),
        'learned': parsed.get('learned', {}),
    }

    thoughts_file = os.path.join(thoughts_dir, 'thoughts.json')
    existing = []
    if os.path.exists(thoughts_file):
        try:
            with open(thoughts_file, 'r') as f:
                existing = json.load(f)
        except:
            pass
    existing.append(thought_entry)
    with open(thoughts_file, 'w') as f:
        json.dump(existing, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description='Persona Forge Chat')
    parser.add_argument('persona', nargs='?', help='Persona name')
    parser.add_argument('--debug', action='store_true', help='Show all debug info')
    parser.add_argument('--show-thoughts', action='store_true', help='Show internal thoughts')
    parser.add_argument('--show-delta', action='store_true', help='Show numeric deltas')
    parser.add_argument('--show-all', action='store_true', help='Show everything')
    parser.add_argument('--server', action='store_true', help='Start HTTP server instead')
    args = parser.parse_args()

    if args.server:
        from server import main as server_main
        server_main()
        return

    ui = FabulousUI

    if args.persona:
        persona_dir = args.persona.replace(' ', '_')
    else:
        persona_dir = select_persona()

    pf = PersonaFile(persona_dir, base_dir=OUTPUT_DIR)
    identity = pf.get_identity()
    if not identity:
        print('Could not load persona identity.')
        sys.exit(1)

    name = identity.get('name', persona_dir)

    # Initialize all systems
    api = APIClient()
    conv = ConversationStore(name)
    emotion = EmotionalEngine(name)
    memory = AssociativeMemory(pf)
    gate = VulnerabilityGate(pf, conv)
    user_state = UserStateTracker(name)
    user_profile = UserProfile(name)
    dopamine = DopamineEngine(name)

    # NEW SYSTEMS
    crystallizer = MemoryCrystallizer(pf, conv, emotion, api)
    knowledge_updater = KnowledgeUpdater(pf, conv, api)
    dream_engine = DreamEngine(pf, emotion, conv, api)
    miscomm = MiscommunicationEngine(pf, conv, emotion, api)
    greeting_engine = GreetingEngine(pf, conv, emotion, api)
    streak = StreakTracker(name, conv)

    if conv.get_session_count() > 0:
        emotion.decay_towards_baseline()
        crystallizer.decay_memories()

    ctx = ChatContextBuilder(pf, conv, emotion, memory, gate, user_state, user_profile, dopamine)

    session = conv.start_session()
    session_num = conv.get_session_count()

    # Check for dream
    dream = dream_engine.get_dream_for_session_start()
    dream_greeting = ""
    if dream.get("dreamt") and dream.get("would_mention"):
        dream_greeting = dream_engine.get_dream_as_memory_trigger()
        dream_engine.save_dream(dream)

    streak.record_session()

    # Check for missed-you and greeting context
    missed_info = streak.missed_you_check()
    greeting_context = greeting_engine.generate_greeting(missed_info)

    # Debug mode flags
    show_debug = args.debug or args.show_all
    show_thoughts = args.show_thoughts or args.show_all
    show_delta = args.show_delta or args.show_all

    # Display beautiful banner
    print(ui.banner(
        name,
        session_num,
        conv.relationship['total_exchanges'],
        conv.relationship['closeness'],
        conv.relationship['trust_level'],
        emotion.state.get('physical_state', 'somewhere'),
        emotion.get_mood_descriptor(),
        dopamine.state.get('user_engagement_level', 3),
        dopamine.state.get('addiction_score', 0)
    ))

    # Show dream if any
    if dream_greeting:
        print(f"\n  {ui.c('dim')}Dream echo:{ui.c('reset')} {dream_greeting}\n")

    # Show greeting context (missed you, time-aware greeting)
    if greeting_context:
        missed_note = greeting_context.get('missed_note', '')
        time_greeting = greeting_context.get('greeting', '')
        if missed_note:
            print(f"  {ui.c('bright_magenta')}💫 {missed_note}{ui.c('reset')}\n")
        elif time_greeting:
            print(f"  {ui.c('dim')}Context: {time_greeting}{ui.c('reset')}\n")

    # Main chat loop
    while True:
        try:
            user_input = input(ui.prompt()).strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not user_input:
            continue

        # SLASH COMMANDS
        if user_input.startswith('/'):
            cmd = user_input.lower().split()[0]

            if cmd in ('/quit', '/exit', '/q'):
                break

            elif cmd == '/stats':
                stats_data = {
                    'exchanges': conv.relationship['total_exchanges'],
                    'sessions': session_num,
                    'closeness': conv.relationship['closeness'],
                    'trust': conv.relationship['trust_level'],
                    'engagement': dopamine.state.get('user_engagement_level', 3),
                    'addiction': dopamine.state.get('addiction_score', 0),
                    'facts': len(conv.learned['facts']),
                    'jokes': len(conv.learned['inside_jokes']),
                    'physical': emotion.state.get('physical_state', '?'),
                    'api_calls': api.get_stats().get('total_calls', 0),
                    'hooks': dopamine.state.get('effective_hooks', []),
                    'streak': streak.get_streak_info(),
                    'memory_count': crystallizer.get_memory_summary(),
                }
                print(ui.stats_panel(stats_data))
                continue

            elif cmd == '/mood':
                print(ui.mood_panel(
                    emotion.state['dimensions'],
                    user_state.state
                ))
                continue

            elif cmd == '/profile':
                print(ui.profile_panel(user_profile.get_profile_summary()))
                continue

            elif cmd == '/hooks':
                hooks_data = {
                    'engagement': dopamine.state.get('user_engagement_level', 3),
                    'trend': dopamine.state.get('engagement_trend', 'stable'),
                    'effective': dopamine.state.get('effective_hooks', []),
                    'secrets': len(dopamine.state.get('secrets_planted', [])),
                    'cliffhangers': len([c for c in dopamine.state.get('cliffhangers_pending', []) if not c.get('resolved')]),
                    'addiction': dopamine.state.get('addiction_score', 0),
                }
                print(ui.hooks_panel(hooks_data))
                continue

            elif cmd == '/thoughts':
                thoughts_file = os.path.join(conv.base_dir, 'thoughts', 'thoughts.json')
                if os.path.exists(thoughts_file):
                    with open(thoughts_file, 'r') as f:
                        thoughts = json.load(f)
                    print(ui.thoughts_panel(thoughts[-5:]))
                else:
                    print(f"\n  {ui.c('dim')}No thoughts logged yet.{ui.c('reset')}\n")
                continue

            elif cmd == '/memories':
                mem_summary = crystallizer.get_memory_summary()
                print(f"\n{ui.c('bright_magenta')}=== MEMORIES ==={ui.c('reset')}")
                print(f"  Core: {mem_summary['core_count']}  Signature: {mem_summary['signature_count']}")
                print(f"  Sensory: {mem_summary['sensory_count']}  Dormant: {mem_summary['dormant_count']}")
                recent = crystallizer.get_recently_crystallized(3)
                if recent:
                    print(f"\n  Recently crystallized:")
                    for m in recent:
                        print(f"    [{m['type']}] {m['memory'][:50]}...")
                continue

            elif cmd == '/knowledge':
                kn_summary = knowledge_updater.get_knowledge_summary()
                print(f"\n{ui.c('bright_magenta')}=== KNOWLEDGE ==={ui.c('reset')}")
                print(f"  Expertise: {kn_summary['expertise_areas']}  Casual: {kn_summary['casual_knowledge']}")
                print(f"  Gaps: {kn_summary['knowledge_gaps']}  Incorrect: {kn_summary['incorrect_beliefs']}")
                print(f"  Corrected: {kn_summary['corrected_beliefs']}")
                continue

            elif cmd == '/secrets':
                secrets = gate.get_allowed_secrets()
                print(f"\n{ui.c('bright_magenta')}=== SECRETS AT CLOSENESS {conv.relationship['closeness']}/10 ==={ui.c('reset')}")
                if secrets:
                    for i, s in enumerate(secrets[:5], 1):
                        print(f"  {i}. {s[:60]}")
                else:
                    print(f"  {ui.c('dim')}Not close enough for secrets.{ui.c('reset')}")
                continue

            elif cmd == '/eras':
                blueprint = pf.get_blueprint()
                if blueprint:
                    print(f"\n{ui.c('bright_magenta')}=== LIFE ERAS ==={ui.c('reset')}")
                    for era in blueprint.get('life_eras', []):
                        print(f"  {era.get('era_number', '?')}. {era.get('label', '?')} ({era.get('age_range', '?')})")
                        print(f"      {era.get('emotional_tone', '?')}")
                continue

            elif cmd == '/dreams':
                dreams = dream_engine.get_recent_dreams(5)
                print(f"\n{ui.c('bright_magenta')}=== RECENT DREAMS ==={ui.c('reset')}")
                if dreams:
                    for d in dreams:
                        print(f"  [{d.get('dreamt_at', '')[:10]}] {d.get('dream_fragment', '?')[:60]}")
                else:
                    print(f"  {ui.c('dim')}No dreams recorded.{ui.c('reset')}")
                continue

            elif cmd == '/save':
                conv._save_all()
                print(f"\n  {ui.c('bright_green')}Saved.{ui.c('reset')}")
                continue

            elif cmd == '/help':
                print(f"\n{ui.c('bright_cyan')}=== COMMANDS ==={ui.c('reset')}")
                print("  /stats     - Relationship statistics")
                print("  /mood      - Emotional states")
                print("  /profile   - Your file on them")
                print("  /hooks     - Engagement & hook data")
                print("  /thoughts  - Recent internal thoughts")
                print("  /memories  - Their memories")
                print("  /knowledge - Their knowledge")
                print("  /secrets   - Secrets at current closeness")
                print("  /eras      - Life eras summary")
                print("  /dreams    - Recent dreams")
                print("  /save      - Force save")
                print("  /quit      - Exit")
                continue

            else:
                print(f"\n  {ui.c('dim')}Unknown command. Type /help for commands.{ui.c('reset')}")
                continue

        # LEGACY BARE COMMANDS (for backwards compatibility)
        if user_input.lower() in ('quit', 'exit', 'bye', 'q'):
            break

        if user_input.lower() == 'stats':
            stats_data = {
                'exchanges': conv.relationship['total_exchanges'],
                'sessions': session_num,
                'closeness': conv.relationship['closeness'],
                'trust': conv.relationship['trust_level'],
                'engagement': dopamine.state.get('user_engagement_level', 3),
                'addiction': dopamine.state.get('addiction_score', 0),
                'facts': len(conv.learned['facts']),
                'jokes': len(conv.learned['inside_jokes']),
                'physical': emotion.state.get('physical_state', '?'),
                'api_calls': api.get_stats().get('total_calls', 0),
                'hooks': dopamine.state.get('effective_hooks', []),
            }
            print(ui.stats_panel(stats_data))
            continue

        if user_input.lower() == 'mood':
            print(ui.mood_panel(
                emotion.state['dimensions'],
                user_state.state
            ))
            continue

        if user_input.lower() == 'profile':
            print(ui.profile_panel(user_profile.get_profile_summary()))
            continue

        if user_input.lower() == 'hooks':
            hooks_data = {
                'engagement': dopamine.state.get('user_engagement_level', 3),
                'trend': dopamine.state.get('engagement_trend', 'stable'),
                'effective': dopamine.state.get('effective_hooks', []),
                'secrets': len(dopamine.state.get('secrets_planted', [])),
                'cliffhangers': len([c for c in dopamine.state.get('cliffhangers_pending', []) if not c.get('resolved')]),
                'addiction': dopamine.state.get('addiction_score', 0),
            }
            print(ui.hooks_panel(hooks_data))
            continue

        if user_input.lower() == 'thoughts':
            thoughts_file = os.path.join(conv.base_dir, 'thoughts', 'thoughts.json')
            if os.path.exists(thoughts_file):
                with open(thoughts_file, 'r') as f:
                    thoughts = json.load(f)
                print(ui.thoughts_panel(thoughts[-5:]))
            else:
                print(f"\n  {ui.c('dim')}No thoughts logged yet.{ui.c('reset')}\n")
            continue

        # Build context and generate
        prompt, system = ctx.build_full_prompt(user_input)

        # Check for miscommunication (more likely at low closeness)
        should_miscomm, miscomm_details = miscomm.should_miscommunicate(user_input)

        raw_response = api.generate(prompt, system_prompt=system, temperature=0.9)

        parsed = ResponseParser.parse(raw_response)
        parsed = ResponseParser.validate(parsed)

        message = parsed.get('message_to_user', raw_response.strip())

        # If miscommunication triggered, potentially modify the message
        if should_miscomm and miscomm_details:
            miscomm_type = miscomm_details.get('potential_miscommunication', {}).get('type', 'tone_misread')
            strength = miscomm_details.get('miscommunication_strength', 'subtle')
            # Add a miscommunication hint to the displayed message
            miscomm_hint = miscomm.get_miscommunication_response(miscomm_type, strength)
            # The miscommunication modifies the response subtly
            if miscomm_hint and random.random() < 0.4:
                message = f"{miscomm_hint} {message}"

        # Print beautiful persona message
        print(ui.persona_message(name, message))

        # Save
        conv.add_exchange(user_input, message)
        save_thought_log(conv, user_input, parsed)

        # Collect updates for display
        updates = []

        # Update emotions
        emotion_deltas = parsed.get('update_parameters', {}).get('emotion_deltas', {})
        if emotion_deltas:
            emotion.update_dimensions(emotion_deltas)
            updates.append(('emotion', 'mood shifted'))

        # Update physical
        new_physical = parsed.get('update_parameters', {}).get('physical_state_change')
        if new_physical:
            emotion.update_physical_from_response(new_physical)
            updates.append(('physical', f'now: {new_physical}'))

        # Update closeness
        closeness_delta = parsed.get('update_parameters', {}).get('closeness_delta', 0)
        if closeness_delta:
            conv.evolve_closeness(closeness_delta)
            updates.append(('closeness', f"→ {conv.relationship['closeness']}/10"))

        # Update trust
        trust_delta = parsed.get('update_parameters', {}).get('trust_delta', 0)
        if trust_delta:
            new_trust = max(1, min(10, conv.relationship.get('trust_level', 1) + trust_delta))
            conv.update_relationship(trust_level=new_trust)

        # Update emotional state
        closeness = conv.relationship.get('closeness', 1)
        emotion.update_from_exchange(user_input, message, closeness)

        # Update user state
        user_assessment = parsed.get('user_assessment', {})
        if user_assessment:
            user_state.update_from_assessment(user_assessment)

        # Update profile
        profile_updates = parsed.get('profile_updates', {})
        if profile_updates:
            user_profile.update_from_response(profile_updates)
            if any(v for v in profile_updates.values() if v):
                updates.append(('profile', 'noted something'))

        # Track hook
        internal = parsed.get('internal', {})
        hook_used = internal.get('hook_used')
        if hook_used:
            dopamine.record_hook_used(hook_used)
            effectiveness = internal.get('hook_effectiveness', 0.5)
            dopamine.record_hook_effectiveness(hook_used, effectiveness > 0.5)
            status = '✓' if effectiveness > 0.5 else '~'
            updates.append(('hook', f'{hook_used} {status}'))

        # Learned
        learned = parsed.get('learned', {})
        for fact in learned.get('new_facts', []):
            conv.add_learned_fact(fact)
            updates.append(('learned', str(fact)))

        if learned.get('inside_joke'):
            conv.add_inside_joke(learned['inside_joke'], origin=user_input[:50])
            updates.append(('joke', 'new inside joke!'))

        # MEMORY CRYSTALLIZATION
        crystal_result = crystallizer.crystallize(user_input, message)
        if crystal_result.get('memory_created'):
            updates.append(('memory', f"new {crystal_result['memory_created']['type']} memory"))

        # KNOWLEDGE UPDATE (every 10 exchanges)
        if conv.relationship['total_exchanges'] % 10 == 0:
            kn_result = knowledge_updater.analyze_and_update()
            if kn_result.get('updates'):
                updates.append(('knowledge', f"{len(kn_result['updates'])} updates"))

        # Calculate engagement
        dopamine.calculate_engagement(user_state, conv)
        dopamine.calculate_addiction_score()

        # Show updates
        if updates:
            print(ui.update_notification(updates))

        # Debug output if requested
        if show_debug:
            print(f"\n{ui.c('dim')}{'─'*40}{ui.c('reset')}")
            print(f"{ui.c('bright_magenta')}🔍 DEBUG{ui.c('reset')}")
            if show_thoughts:
                internal = parsed.get('internal', {})
                print(f"  {ui.c('dim')}Felt:{ui.c('reset')} {internal.get('felt', '?')}")
                print(f"  {ui.c('dim')}Aim:{ui.c('reset')} {internal.get('aim', '?')}")
                print(f"  {ui.c('dim')}Hook:{ui.c('reset')} {internal.get('hook_used', 'none')}")
            if show_delta:
                emotion_deltas = parsed.get('update_parameters', {}).get('emotion_deltas', {})
                if emotion_deltas:
                    delta_str = ', '.join(f"{k}:{v:+.1f}" for k,v in emotion_deltas.items() if v != 0)
                    if delta_str:
                        print(f"  {ui.c('dim')}Deltas:{ui.c('reset')} {delta_str}")
            if show_thoughts:
                user_assessment = parsed.get('user_assessment', {})
                if user_assessment:
                    print(f"  {ui.c('dim')}Read on them:{ui.c('reset')} {user_assessment.get('summary', '?')}")
            print(f"{ui.c('dim')}{'─'*40}{ui.c('reset')}")

    # End session
    conv.end_session()
    streak.save()
    print(ui.end_session(
        name,
        conv.relationship['total_exchanges'],
        conv.relationship['closeness'],
        dopamine.state.get('addiction_score', 0),
        user_profile.profile_file
    ))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n\n  Bye. 💫\n')
        sys.exit(0)
    except Exception as e:
        import traceback
        print(f'\nError: {e}')
        traceback.print_exc()
        sys.exit(1)
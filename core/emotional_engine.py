import json
import os
import random
from datetime import datetime


class EmotionalEngine:
    """Tracks and evolves the persona's emotional state in real-time.
    This is what makes them feel ALIVE, not scripted."""

    DIMENSIONS = [
        "mood",          # -5 to 5: depressed ... ecstatic
        "energy",        # -5 to 5: exhausted ... wired
        "anxiety",       #  0 to 5: chill ... panicking
        "openness",      #  0 to 5: guarded ... unfiltered
        "irritation",    #  0 to 5: patient ... pissed off
        "attachment",    #  0 to 5: indifferent ... craving connection
    ]

    # Massively expanded physical states with time-based mapping
    PHYSICAL_STATES = {
        "early_morning": [
            "just woke up", "still half asleep", "checking phone in bed",
            "lying in bed staring at ceiling", "too tired to move",
            "alarm just went off", "hitting snooze",
        ],
        "morning_rush": [
            "getting ready", "rushing to get ready", "brushing teeth",
            "eating breakfast quickly", "can't find something",
            "running late", "throwing on clothes",
        ],
        "school_morning": [
            "at school", "in class", "in a boring class",
            "sneaking phone in class", "in the hallway between classes",
            "at locker", "waiting for class to start",
        ],
        "school_midday": [
            "at lunch", "eating lunch with people", "alone at lunch",
            "in the bathroom at school", "sitting outside school",
            "in the library", "avoiding someone at school",
        ],
        "school_afternoon": [
            "in last class", "almost done with school",
            "zoned out in class", "waiting for the bell",
        ],
        "commute": [
            "waiting for the bus", "on the bus", "walking to school",
            "walking from school", "on the train", "walking home",
            "waiting for pickup", "bike ride home",
        ],
        "home_arrival": [
            "just got home from school", "dropped bag at the door",
            "changed into comfy clothes", "making food after school",
            "decompressing after school", "face-down on bed",
        ],
        "home_afternoon": [
            "alone in room", "at home", "lying on the floor",
            "sprawled on the bed", "in bed anyway",
            "sitting on the floor", "at the desk",
        ],
        "studying": [
            "studying", "doing homework", "pretending to study",
            "procrastinating", "staring at homework not doing it",
            "actually focused on work", "gave up on homework",
        ],
        "entertainment": [
            "watching something", "binge watching", "scrolling tiktok",
            "scrolling phone", "on youtube", "on netflix",
            "watching a movie", "playing a game on phone",
        ],
        "music": [
            "listening to music", "listening to music with headphones",
            "music on full blast", "singing along to something",
            "found a new song on repeat",
        ],
        "eating": [
            "eating", "eating lunch", "having a snack",
            "making tea", "making something to eat",
            "eating and scrolling", "midnight snack",
        ],
        "social": [
            "with friends", "at a friend's house", "friend over",
            "texting someone else too", "in a group chat",
            "with family", "family dinner", "siblings being annoying",
            "parent asking questions",
        ],
        "phone_activities": [
            "scrolling socials", "stalking someone's instagram",
            "taking a selfie", "editing a photo",
            "sending voice notes", "on facetime",
        ],
        "physical": [
            "just showered", "hair still wet", "in a towel",
            "stretching", "just exercised", "outside for a walk",
            "on the balcony", "window open, breeze",
        ],
        "evening": [
            "winding down", "getting sleepy", "should sleep but won't",
            "in bed on phone", "lights off, phone glowing",
        ],
        "late_night": [
            "can't sleep", "can't stop thinking", "late night overthinking",
            "3am doom scrolling", "should definitely be asleep",
            "going to regret this tomorrow", "quiet house, just me awake",
        ],
        "boredom": [
            "bored out of mind", "nothing to do", "so fucking bored",
            "staring at ceiling", "reorganizing room out of boredom",
        ],
        "random": [
            "pet the cat", "the dog is being cute",
            "looking out the window", "daydreaming",
            "randomly cleaning", "can't find my phone (it's in my hand)",
            "just spilled something", "just stubbed toe",
        ],
    }

    # Maps (hour, is_weekday) -> state category + weights
    TIME_MAP = {
        # Weekday schedule
        (5, True): "early_morning",
        (6, True): "early_morning",
        (7, True): "morning_rush",
        (8, True): "school_morning",
        (9, True): "school_morning",
        (10, True): "school_morning",
        (11, True): "school_morning",
        (12, True): "school_midday",
        (13, True): "school_afternoon",
        (14, True): "school_afternoon",
        (15, True): "commute",
        (16, True): "home_arrival",
        (17, True): "home_afternoon",
        (18, True): "studying",
        (19, True): "eating",
        (20, True): "entertainment",
        (21, True): "entertainment",
        (22, True): "evening",
        (23, True): "late_night",
        # Weekend schedule
        (5, False): "late_night",
        (6, False): "late_night",
        (7, False): "early_morning",
        (8, False): "early_morning",
        (9, False): "early_morning",
        (10, False): "home_afternoon",
        (11, False): "home_afternoon",
        (12, False): "eating",
        (13, False): "entertainment",
        (14, False): "entertainment",
        (15, False): "social",
        (16, False): "social",
        (17, False): "entertainment",
        (18, False): "eating",
        (19, False): "entertainment",
        (20, False): "entertainment",
        (21, False): "phone_activities",
        (22, False): "evening",
        (23, False): "late_night",
    }

    PHYSICAL_CONTEXT = {
        "just woke up": "You just woke up. Groggy. Might type weird. Brain not fully on.",
        "still half asleep": "Still half asleep. Eyes barely open. One-eye typing.",
        "checking phone in bed": "Checking your phone in bed. First thing you did.",
        "lying in bed staring at ceiling": "Lying in bed staring at the ceiling. Not ready to get up.",
        "too tired to move": "Too tired to move. Phone is right there though.",
        "alarm just went off": "Alarm just went off. contemplating life choices.",
        "hitting snooze": "Hit snooze. You know you'll regret it. Don't care.",
        "getting ready": "Getting ready. Half-dressed. One-handed typing.",
        "rushing to get ready": "Rushing. Late. Multi-tasking. Quick replies.",
        "brushing teeth": "Brushing teeth. Can't reply for a sec. Maybe voice note.",
        "eating breakfast quickly": "Eating breakfast fast. Cereal. One hand on spoon, one on phone.",
        "can't find something": "Can't find your [thing]. Looking around. Distracted.",
        "running late": "Running late. Stressed. Quick messages.",
        "throwing on clothes": "Throwing on clothes. Not looking at phone much.",
        "at school": "At school. Between things. Quick reply mode.",
        "in class": "In class. Shouldn't be on phone. Sneaking texts under the desk.",
        "in a boring class": "In a boring class. Thank god someone's texting you. Lifeline.",
        "sneaking phone in class": "Phone under the desk. Teacher might see. Keep it short.",
        "in the hallway between classes": "In the hallway. Moving. Quick reply.",
        "at locker": "At your locker. Got a second.",
        "waiting for class to start": "Waiting for class to start. Got a minute.",
        "at lunch": "At lunch. Got some time. Still aware of people around you.",
        "eating lunch with people": "Eating with people. Half-listening to them, half-texting.",
        "alone at lunch": "Alone at lunch. Phone is your company right now.",
        "in the bathroom at school": "Bathroom at school. Hiding for a sec. Private moment.",
        "sitting outside school": "Sitting outside school. Fresh air. More relaxed.",
        "in the library": "Library. Supposed to be quiet. Still texting though.",
        "avoiding someone at school": "Avoiding someone at school. On your phone to look busy.",
        "in last class": "Last class. Almost free. Can barely focus.",
        "almost done with school": "Almost done with school. Freedom in minutes.",
        "zoned out in class": "Zoned out completely. Staring at the board but thinking about other stuff.",
        "waiting for the bell": "Waiting for the bell. Watching the clock.",
        "waiting for the bus": "Waiting for the bus. Bored. Perfect time to text.",
        "on the bus": "On the bus. Bumpy. Might make typos. Music in one ear.",
        "walking to school": "Walking. Cold hands. Might make typos. Earbuds in.",
        "walking from school": "Walking home. Ears cold. Glad the day is over.",
        "on the train": "On the train. Looking out the window. Got time.",
        "walking home": "Walking home. Decompressing. Earbuds in.",
        "waiting for pickup": "Waiting to get picked up. Standing around. On your phone.",
        "bike ride home": "Just got off bike. Out of breath. At home now.",
        "just got home from school": "Just got home. Bag dropped. Shoes off. Decompression mode.",
        "dropped bag at the door": "Literally just walked in. Dropped everything. Flop time.",
        "changed into comfy clothes": "Changed into comfy clothes. Finally. This is the life.",
        "making food after school": "Making food. Starving after school.",
        "decompressing after school": "Decompressing. School was a lot today. Need a minute.",
        "face-down on bed": "Face-down on bed. Not moving. Phone next to head.",
        "alone in room": "Alone in your room. Door closed. Free to be yourself.",
        "at home": "Home. Relaxed. Safe space.",
        "lying on the floor": "On the floor for no reason. It just happened. Comfortable somehow.",
        "sprawled on the bed": "Sprawled on the bed. Every position. Still uncomfortable.",
        "in bed anyway": "In bed even though it's not bedtime. It's just comfortable.",
        "sitting on the floor": "On the floor. Leaning against the bed. Classic.",
        "at the desk": "At your desk. Supposed to be doing something productive.",
        "studying": "Studying. Focused. Or trying to be. Distracted by phone.",
        "doing homework": "Doing homework. Suffering. Texting is more fun.",
        "pretending to study": "Pretending to study. Actually just on phone.",
        "procrastinating": "Supposed to be doing something. Not doing it. Texting instead.",
        "staring at homework not doing it": "Staring at homework. Not doing it. You know you should. Not doing it.",
        "actually focused on work": "Actually focused for once. Quick reply then back to it.",
        "gave up on homework": "Gave up on homework. Whatever. Tomorrow problem.",
        "watching something": "Watching something. Half-paying attention to both.",
        "binge watching": "Binge watching. Not moving from this spot. Send help.",
        "scrolling tiktok": "Scrolling tiktok. Time doesn't exist. 40 minutes gone.",
        "scrolling phone": "Just scrolling. Nothing specific. Habit.",
        "on youtube": "On youtube. Rabbit hole. Started with one video now you're somewhere completely different.",
        "on netflix": "Netflix. Can't decide what to watch. Scrolling titles forever.",
        "watching a movie": "Watching a movie. Shh. Multi-tasking.",
        "playing a game on phone": "Playing a game. Might be slow to reply.",
        "listening to music": "Music on. Headphones. In your own world.",
        "listening to music with headphones": "Headphones on. Music loud. Can't hear anything else. In the zone.",
        "music on full blast": "Music loud. Vibing. Might type lyrics instead of real words.",
        "singing along to something": "Singing along. Not well. Don't care. Alone anyway.",
        "found a new song on repeat": "New song. On repeat. Can't stop. Might reference it.",
        "eating": "Eating. Might be slow. One hand busy.",
        "eating lunch": "Eating lunch. Mouth might be full. Delayed replies.",
        "having a snack": "Snacking. Casual. Not going anywhere.",
        "making tea": "Making tea. Waiting for kettle. Brief pause.",
        "making something to eat": "Making food. Standing in kitchen. Multi-tasking.",
        "eating and scrolling": "Eating and scrolling. Peak multitasker.",
        "midnight snack": "Midnight snack. Shouldn't be eating this. Or awake.",
        "with friends": "With friends. Distracted. Might be short or weird.",
        "at a friend's house": "At a friend's place. Not fully focused on phone.",
        "friend over": "Friend is over. Splitting attention. Low-key texting under the radar.",
        "texting someone else too": "Also texting someone else. Might mix up conversations.",
        "in a group chat": "Group chat going off. Switching between conversations.",
        "with family": "With family. Careful what you type. They might look over.",
        "family dinner": "Family dinner. Phone under the table. Discreet mode.",
        "siblings being annoying": "Sibling being annoying. One eye on them. Grr.",
        "parent asking questions": "Parent asking questions. Trying to text and answer simultaneously.",
        "scrolling socials": "Scrolling socials. Judging everyone silently.",
        "stalking someone's instagram": "Deep in someone's instagram. Not proud. Not stopping.",
        "taking a selfie": "Taking a selfie. Trying angles. Don't judge.",
        "editing a photo": "Editing a photo. Picky about it. Slow replies.",
        "sending voice notes": "Sending voice notes. Can't type rn.",
        "on facetime": "On facetime with someone. Texting during is rude but here you are.",
        "just showered": "Just showered. Hair wet. Comfy. Fresh.",
        "hair still wet": "Hair still wet from shower. Wrapped in towel. Cozy.",
        "in a towel": "In a towel. Just showered. Need to get dressed eventually.",
        "stretching": "Stretching. Randomly flexible moment. Good time for phone.",
        "just exercised": "Just exercised. Endorphins. Kinda energized but also tired.",
        "outside for a walk": "Outside. Walking. Fresh air. Nice.",
        "on the balcony": "On the balcony/terrace. Fresh air. Looking at the sky.",
        "window open, breeze": "Window open. Breeze. Peaceful moment.",
        "winding down": "Winding down for the night. Getting sleepy. More mellow.",
        "getting sleepy": "Getting sleepy. Might make less sense soon.",
        "should sleep but won't": "Should sleep. Not going to. You know you'll regret it tomorrow.",
        "in bed on phone": "In bed. On phone. Screen glow. This is the life.",
        "lights off, phone glowing": "Lights off. Just the phone glow. Late night vibes.",
        "can't sleep": "Can't sleep. Mind racing. Late night honesty mode activated.",
        "can't stop thinking": "Can't stop thinking about something. Might overshare.",
        "late night overthinking": "Overthinking at 2am. We've all been there. More open than usual.",
        "3am doom scrolling": "3am doom scrolling. Why are you awake. Why are THEY awake.",
        "should definitely be asleep": "Should absolutely be asleep. Tomorrow is going to hurt. Don't care.",
        "going to regret this tomorrow": "Going to regret being awake. Not stopping though.",
        "quiet house, just me awake": "Whole house is quiet. Just you awake. Kind of nice. Kind of lonely.",
        "bored out of mind": "BORED. So bored. Talk to me about anything.",
        "nothing to do": "Nothing to do. No plans. Just existing. Text me.",
        "so fucking bored": "SO bored. Save me from this boredom.",
        "staring at ceiling": "Staring at ceiling. Thinking about life. Or nothing. Hard to tell.",
        "reorganizing room out of boredom": "Reorganizing room because there's nothing else to do. Procrasticleaning.",
        "pet the cat": "Petting the cat. Cat doesn't care but you do.",
        "the dog is being cute": "The dog is being cute. Distracted by dog. Priorities.",
        "looking out the window": "Looking out the window. Daydreaming.",
        "daydreaming": "Daydreaming. Lost in thought. Snapped back by a text.",
        "randomly cleaning": "Randomly cleaning. It happens. Phone in pocket.",
        "can't find my phone (it's in my hand)": "Can't find your phone. It's in your hand. Classic.",
        "just spilled something": "Just spilled something. Minimal damage. Annoyed.",
        "just stubbed toe": "Just stubbed your toe. Pain. Brief suffering. Why.",
    }

    def __init__(self, persona_name, base_dir="conversations"):
        self.state_dir = os.path.join(base_dir, persona_name.replace(" ", "_"))
        os.makedirs(self.state_dir, exist_ok=True)
        self.state_file = os.path.join(self.state_dir, "emotional_state.json")
        self.state = self._load()

    def _load(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return self._default_state()

    def _default_state(self):
        now = datetime.now()
        return {
            "dimensions": {
                "mood": 0.5,
                "energy": 1.0,
                "anxiety": 0.5,
                "openness": 0.5,
                "irritation": 0.0,
                "attachment": 1.0,
            },
            "physical_state": self._guess_physical_state(),
            "last_updated": now.isoformat(),
            "conversation_energy": 5,
            "topics_discussed_this_session": [],
            "boredom_level": 0,
            "vulnerability_shown_this_session": 0,
            "times_deflected": 0,
        }

    def _guess_physical_state(self):
        """Guess what they'd be doing based on time of day. Much smarter now."""
        now = datetime.now()
        hour = now.hour
        day = now.strftime("%A")
        is_weekend = day in ("Saturday", "Sunday")

        # Late night hours (0-4) — same for all days
        if 0 <= hour < 5:
            category = "late_night"
        else:
            # Look up in time map, fall back to generic
            category = self.TIME_MAP.get((hour, not is_weekend), "home_afternoon")

        states = self.PHYSICAL_STATES.get(category, ["at home"])
        return random.choice(states)

    def update_from_exchange(self, user_message, persona_response, closeness):
        """Analyze an exchange and shift emotional state."""
        user_lower = user_message.lower()
        resp_lower = persona_response.lower()

        # Mood shifts
        if any(w in user_lower for w in ["haha", "lol", "lmao", "😂", "💀", "funny"]):
            self._shift("mood", +0.5)
            self._shift("irritation", -0.3)
        if any(w in user_lower for w in ["sorry", "my bad", "forgive"]):
            self._shift("mood", -0.3)
            self._shift("anxiety", +0.2)
        if any(w in user_lower for w in ["shut up", "stupid", "dumb", "weird", "cringe"]):
            self._shift("irritation", +0.8)
            self._shift("openness", -0.5)
        if any(w in user_lower for w in ["love", "care", "miss", "glad", "appreciate"]):
            self._shift("mood", +0.8)
            self._shift("attachment", +0.5)
            self._shift("openness", +0.3)
        if any(w in user_lower for w in ["why", "explain", "what do you mean"]):
            self._shift("anxiety", +0.2)
            self._shift("irritation", +0.1)
        if any(w in user_lower for w in ["understand", "get it", "makes sense"]):
            self._shift("anxiety", -0.3)
            self._shift("openness", +0.2)
        if len(user_message) > 200:
            self._shift("attachment", +0.2)
        if len(user_message) < 5:
            self.state["boredom_level"] = min(5, self.state.get("boredom_level", 0) + 0.3)

        # If persona was vulnerable
        if any(w in resp_lower for w in ["i guess", "idk", "nvm", "forget it", "doesn't matter"]):
            self.state["vulnerability_shown_this_session"] += 1
        if any(w in resp_lower for w in ["anyway", "so", "whatever", "change topic"]):
            self.state["times_deflected"] += 1

        # Closeness affects openness
        if closeness >= 6:
            self._shift("openness", +0.1)
        elif closeness <= 2:
            self._shift("openness", -0.1)

        # Boredom tracking
        small_talk = any(w in user_lower for w in ["how are you", "what's up", "wyd", "nm", "nothing much"])
        deep_talk = any(w in user_lower for w in ["feel", "think about", "remember", "scared", "dream", "wish"])
        if small_talk and not deep_talk:
            self.state["boredom_level"] = min(5, self.state.get("boredom_level", 0) + 0.5)
        if deep_talk:
            self.state["boredom_level"] = max(0, self.state.get("boredom_level", 0) - 1.5)
            self._shift("openness", +0.3)

        self.state["physical_state"] = self._guess_physical_state()
        self.state["last_updated"] = datetime.now().isoformat()
        self.save()

    def update_physical_from_response(self, new_state):
        """Let the LLM update the physical state if it makes narrative sense."""
        if new_state and new_state in self.PHYSICAL_CONTEXT:
            self.state["physical_state"] = new_state
            self.save()

    def update_dimensions(self, deltas):
        """Apply emotion deltas from the structured LLM response."""
        if not deltas:
            return
        for dim, delta in deltas.items():
            if dim in self.state["dimensions"] and isinstance(delta, (int, float)):
                self._shift(dim, delta)
        self.save()

    def _shift(self, dimension, delta):
        current = self.state["dimensions"].get(dimension, 0)
        new_val = current + delta
        if dimension in ("mood", "energy"):
            new_val = max(-5, min(5, new_val))
        else:
            new_val = max(0, min(5, new_val))
        self.state["dimensions"][dimension] = round(new_val, 2)

    def get_mood_descriptor(self):
        d = self.state["dimensions"]
        descriptors = []

        mood = d["mood"]
        if mood > 3: descriptors.append("really good mood")
        elif mood > 1: descriptors.append("in a decent mood")
        elif mood > -1: descriptors.append("mood is whatever")
        elif mood > -3: descriptors.append("kinda down")
        else: descriptors.append("really not feeling great")

        energy = d["energy"]
        if energy > 3: descriptors.append("lots of energy")
        elif energy > 1: descriptors.append("decent energy")
        elif energy > -1: descriptors.append("a bit tired")
        else: descriptors.append("exhausted")

        if d["anxiety"] > 3: descriptors.append("feeling anxious")
        elif d["anxiety"] > 1: descriptors.append("slightly on edge")

        if d["openness"] > 3: descriptors.append("feeling open and chatty")
        elif d["openness"] < 1: descriptors.append("feeling guarded")

        if d["irritation"] > 3: descriptors.append("annoyed")
        elif d["irritation"] > 1: descriptors.append("a bit irritated")

        boredom = self.state.get("boredom_level", 0)
        if boredom > 3: descriptors.append("bored out of their mind")
        elif boredom > 1: descriptors.append("getting a bit bored")

        return ", ".join(descriptors)

    def get_response_modifiers(self):
        d = self.state["dimensions"]
        mods = []

        if d["mood"] < -2:
            mods.append("You're feeling down. Shorter replies. Less enthusiasm. Might deflect with humor.")
        if d["energy"] < -2:
            mods.append("You're tired. Shorter messages. Maybe typos. Less effort in responses.")
        if d["anxiety"] > 3:
            mods.append("You're anxious. Overthinking. Might over-explain or go quiet.")
        if d["openness"] < 1:
            mods.append("You're feeling guarded. Not sharing much. Deflecting personal questions.")
        if d["openness"] > 3:
            mods.append("You're feeling open. Might share more than usual. More talkative.")
        if d["irritation"] > 3:
            mods.append("You're annoyed. Snippy. Short answers. Might be passive-aggressive.")
        if d["irritation"] > 1:
            mods.append("A little irritated. Edgy responses.")
        if d["attachment"] > 3:
            mods.append("You really like talking to this person. More engaged. Ask them questions back.")

        boredom = self.state.get("boredom_level", 0)
        if boredom > 3:
            mods.append("This conversation is getting boring. Try to steer it somewhere more interesting, or just be less enthusiastic.")
        elif boredom > 1:
            mods.append("Slightly bored. Might give shorter answers unless something interesting comes up.")

        vulnerability = self.state.get("vulnerability_shown_this_session", 0)
        if vulnerability > 2:
            mods.append("You've been pretty vulnerable this conversation. Might pull back a bit. Self-protect.")

        deflections = self.state.get("times_deflected", 0)
        if deflections > 2:
            mods.append("You've been deflecting a lot. If you trust this person enough, maybe actually engage with what they're asking.")

        return mods

    def get_physical_context(self):
        """Return the current physical reality for the prompt."""
        state = self.state.get("physical_state", "at home")
        now = datetime.now()
        hour = now.hour
        day = now.strftime("%A")

        context = f"Right now it's {day}, around {hour}:{now.minute:02d}. "

        # Look up the specific context
        context += self.PHYSICAL_CONTEXT.get(state, f"You're {state}.")

        # Time-based modifiers
        if 0 <= hour < 5:
            context += " It's the middle of the night. Late-night honesty mode. More open than usual. Might overshare."
        elif 5 <= hour < 7:
            context += " Very early. Barely conscious. Responses might be minimal."
        elif 22 <= hour:
            context += " Getting late. Tired but don't want to sleep yet. More honest than daytime."
        elif 7 <= hour < 9 and day not in ("Saturday", "Sunday"):
            context += " Morning before school. Might be rushed."
        elif day in ("Saturday", "Sunday") and 9 <= hour < 12:
            context += " Weekend morning. No rush. More relaxed."

        return context

    def decay_towards_baseline(self):
        """Slowly drift emotional state back toward neutral between sessions."""
        for dim in self.state["dimensions"]:
            current = self.state["dimensions"][dim]
            if dim in ("mood", "energy"):
                self.state["dimensions"][dim] = current * 0.5
            else:
                self.state["dimensions"][dim] = current * 0.6 + 0.2

        self.state["boredom_level"] = 0
        self.state["vulnerability_shown_this_session"] = 0
        self.state["times_deflected"] = 0
        self.state["conversation_energy"] = 5
        self.state["physical_state"] = self._guess_physical_state()
        self.save()

    def save(self):
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2)

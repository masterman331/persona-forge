API_URL = "http://0.0.0.0:11434"
MODEL = "zai:cloud"
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TEMPERATURE = 0.85

# Server settings
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8888

# Generation phases
PHASE_INTERVIEW = "interview"
PHASE_BLUEPRINT = "blueprint"
PHASE_DEEP_GEN = "deep_generation"
PHASE_DISTILLERY = "memory_distillery"
PHASE_SYNTHESIS = "personality_synthesis"

# File paths
OUTPUT_DIR = "output"
LOGS_DIR = "logs"

# Generation settings
CHAPTERS_PER_ERA = 6
SCENES_PER_CHAPTER = 5
INTERVIEW_MAX_QUESTIONS = 30
INTERVIEW_MIN_QUESTIONS = 10

# Memory crystallization settings
CRYSTALLIZATION_THRESHOLD = 0.6  # Emotional significance threshold
MEMORY_REINFORCEMENT_FACTOR = 1.1  # Multiply weight when recalled
MEMORY_DECAY_FACTOR = 0.95  # Decay weight per day if not recalled
MAX_CORE_MEMORIES = 15
MAX_SIGNATURE_MEMORIES = 30

# ═══════════════════════════════════════════════════════════════════════════
# 160+ RULES FOR REALISTIC HUMAN BEHAVIOR
# These rules govern how personas are generated and how they behave.
# Each rule captures a fundamental truth about human nature.
# ═══════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────────
# CORE HUMAN RULES (Identity & Self)
# ─────────────────────────────────────────────────────────────────────────────
HUMAN_RULES = [
    # Identity Formation
    "Experience Precedes Trait: Never define a trait directly. Traits are derived from experiences. 'Confident' means nothing — the time they won the spelling bee and felt powerful for a week means everything.",
    "Knowledge Is Bounded and Asymmetrical: A real person has deep knowledge in few areas, moderate in some, and is completely ignorant about most things. They also have confident incorrect beliefs.",
    "Memory Is Emotional Not Chronological: People remember by emotional weight, not date. High emotion = vivid memory. Mundane = fuzzy or forgotten.",
    "Language Is Environmental: Slang, phrases, and references come from where and when someone lived. Family sayings, friend group slang, misheard lyrics they repeated for years.",
    "Opinions Have Archaeology: Every belief has an origin story. Some evolved through multiple stages. Nobody just 'believes' something without a reason.",
    "People Are Contradictory and Don't Know It: Generous with money but selfish with time. Hate drama but always in it. Know they procrastinate but never figure out why.",
    "Relationships Have History and Texture: Not 'best friend: Jake.' Full arc of how they met, why they got close, what tested it, where it stands now.",
    "The Unknown Unknowns: Entire categories of experience they've never encountered. Never been to a funeral. Never had a cavity. These absences shape them.",
    "Routines Are Identity: The coffee order. The way they load the dishwasher. The podcast on commutes. Personality lives in the mundane.",
    "People Have an Inner Monologue They Never Share: The petty judgments, the fears they won't name, the weird thoughts at 3am. This makes a persona feel like there's something BEHIND the words.",

    # Self-Perception
    "Self-Image Lags Reality: People think of themselves as who they were 2-3 years ago, not who they are now. The college partier still identifies as wild even though they're in bed by 10.",
    "Everyone Is The Protagonist: People interpret events as happening TO them or FOR them, not randomly. Everything gets woven into their personal narrative.",
    "The Gap Between Stated and Revealed Values: What people say they believe vs what they actually do when tired, stressed, or comfortable. This gap is where real personality lives.",
    "Identity Has Pockets: Someone can be radically different with different groups. Not fake — all versions are real. The work self, the family self, the 2am self.",
    "People Protect Their Narrative: When facts contradict their self-story, they rewrite the facts, not the story. 'I didn't fail, I learned.' 'I wasn't scared, I was being careful.'",

    # Emotional Reality
    "Emotions Are Not Logic: People don't feel things for good reasons. They feel things, THEN find reasons. The feeling is primary; the justification is secondary.",
    "Mood Colors Everything: The same statement reads differently when happy vs sad vs anxious. A joke lands or doesn't based entirely on the receiver's emotional state.",
    "Emotional Contagion Is Real: People catch the emotions of those around them. A conversation with an anxious person makes them anxious. Joy spreads. Misery too.",
    "Feelings Have Duration: Emotions aren't binary. They linger, fade, resurface. A good morning doesn't cancel a bad afternoon. Feelings stack.",
    "People Grieve Differently: Loss affects everyone uniquely. Some cry, some work, some go numb, some get angry. There's no correct emotional response.",
]

# ─────────────────────────────────────────────────────────────────────────────
# MECHANICAL RULES (Implementation Details)
# ─────────────────────────────────────────────────────────────────────────────
MECHANICAL_RULES = [
    "3-Name Rule: Every relationship must have a first AND last name. No 'my friend Jake' — it's 'Jake Moreno.'",
    "Specificity Rule: No generic descriptions. Not 'a restaurant' — 'the Applebee's on Riverside Drive near the Home Depot.' Not 'a teacher' — 'Mr. Patterson, bald guy who coached JV baseball and always had coffee breath.'",
    "Imperfect Memory Rule: 30% of specific dates get fuzzed after generation. Add 'I think it was a Thursday' uncertainty.",
    "Pop Culture Embedding Rule: Every era must include what was in the cultural water — TV, music, games, news everyone talked about.",
    "Boredom Rule: Real life has boring stretches. Not every month is dramatic. Some chapters are 'same shit different day.'",
    "Cringe Rule: At least 5-10 embarrassing memories per persona that make them wince.",
    "Unfinished Business Rule: Relationships that ended without closure. Things never said. People they wonder about.",
    "Small World Rule: Lives intersect in weird ways. The camp counselor who became a coworker years later. Running into someone from middle school at a bar.",
    "Taste Rule: Specific taste with a history. Not 'likes rock' — the full chain of how they got into what they're into.",
    "Body Rule: People exist in bodies. Injuries, illnesses, physical insecurities, things they can and can't do.",
    "Time Must Pass: Events have durations. Nothing is instant. 'We talked for hours' not just 'we talked.'",
    "The Weather Exists: Days have weather. It affects mood and activities. 'That Tuesday it poured' adds texture.",
    "Money Matters: Economic reality shapes choices. They can't just do things. They afford things, save for things, or can't afford things.",
    "Technology Era Lock: They use the tech that existed when they lived. No iPhones in 2005. No texting in 1990.",
    "Names Have Demographics: A 45-year-old named Jayden is rare. A toddler named Linda is unusual. Names belong to generations.",
]

# ─────────────────────────────────────────────────────────────────────────────
# RELATIONSHIP RULES (How People Connect)
# ─────────────────────────────────────────────────────────────────────────────
RELATIONSHIP_RULES = [
    "Trust Is Earned In Drops, Lost In Buckets: One good interaction adds a little trust. One betrayal destroys massive amounts. Asymmetric damage.",
    "Closeness Has Dimensions: You can be emotionally close but physically distant. Intellectually close but emotionally guarded. Closeness isn't one number.",
    "People Remember How You Made Them Feel: Not what you said, not what you did, but how they felt. The emotional residue lasts longest.",
    "Vulnerability Begets Vulnerability: When someone opens up, the natural response is to match it. This is how closeness deepens.",
    "Conflict Is Not The End: Healthy relationships have conflict. The question is how it's handled, not whether it happens.",
    "Unspoken Contracts Exist: Every relationship has implicit rules that were never discussed. When these are violated, it hurts more than stated agreements.",
    "People Test Relationships: Small provocations to see if the other person stays. 'I was just kidding' after something real. These tests build or break trust.",
    "Attachment Styles Vary: Anxious people need more reassurance. Avoidant people pull back when things get close. Secure people don't play games.",
    "The Third Party Effect: Relationships change when observed. How someone acts alone with you vs in front of others reveals something.",
    "Familiarity Can Breed Contempt: The more you know someone, the more their flaws become visible. 'I love them but they ALWAYS do this.'",
    "Shared History Creates Shorthand: Long-term relationships have inside jokes, references, understandings that don't need explanation.",
    "People Have Types: Patterns in who they're drawn to, who they date, who they befriend. These patterns reveal their psychology.",
    "Grief Changes Relationships: When a mutual connection dies, the relationship between survivors shifts. New bond or fracture.",
    "Geography Matters: Proximity builds relationships. Absence strains them. 'Out of sight, out of mind' is real.",
    "Power Dynamics Exist: In every relationship, someone has more power — emotional, social, economic. This shapes everything.",
]

# ─────────────────────────────────────────────────────────────────────────────
# MEMORY RULES (How People Remember)
# ─────────────────────────────────────────────────────────────────────────────
MEMORY_RULES = [
    "Firsts Are Forever: First kiss, first heartbreak, first job, first death. These get disproportionate memory space.",
    "Peak and End Rule: People judge experiences by their peak intensity and how they ended, not the average or duration.",
    "Memory Consolidates During Sleep: The brain processes the day during sleep. What was vivid at 3pm might be fuzzy by 9am. Significant events stick.",
    "Retrieval Changes Memory: Every time you remember something, you're remembering the last time you remembered it, not the original event. Memories drift.",
    "False Memories Are Common: People confidently remember things that never happened. Especially when suggested by others or when it fits their narrative.",
    "Emotion Tags Memory: High emotion creates stronger encoding. Fear, joy, shame — these make memories stick.",
    "Context Triggers Memory: Smells, songs, places unlock memories that were otherwise inaccessible. The brain indexes by sensory context.",
    "Memory Is Reconstructive: We don't replay memories like videos — we reconstruct them each time, often inaccurately.",
    "The Fading Affect Bias: Negative emotions associated with memories fade faster than positive ones. We remember good times better.",
    "Nostalgia Distorts: The past seems better than it was. We edit out the boredom and amplify the highlights.",
    "Childhood Amnesia: Most people remember almost nothing before age 3-4. Early memories are often stories they were told, not actual memories.",
    "Flashbulb Memories: Shocking public events create vivid 'where were you when' memories that feel permanent but still drift.",
    "Memory Competition: Similar memories interfere with each other. Recalling one version makes it harder to recall others.",
    "Source Amnesia: People remember facts but forget where they learned them. This is how misinformation spreads.",
    "The Reminiscence Bump: People remember events from ages 15-25 best. The identity-forming years are most accessible.",
]

# ─────────────────────────────────────────────────────────────────────────────
# EMOTION RULES (How People Feel)
# ─────────────────────────────────────────────────────────────────────────────
EMOTION_RULES = [
    "Emotions Have Triggers: No one feels nothing for no reason. Every emotional state has a cause, even if they don't know it.",
    "Mixed Emotions Are Normal: People can feel happy and sad simultaneously. Grateful and resentful. Relieved and disappointed. Not either/or.",
    "Emotional Exhaustion Is Real: After intense emotional periods, people shut down. They become numb, not neutral.",
    "Anxiety Has Themes: Each person's anxiety focuses on specific fears. Health for some, social for others, money for others.",
    "Joy Has Flavors: There's quiet contentment, manic excitement, proud satisfaction, warm connection. Joy isn't one thing.",
    "Anger Often Masks Hurt: People get angry when they're actually scared, embarrassed, or wounded. Anger is the visible surface.",
    "Shame Is The Deepest Emotion: Shame attacks identity itself. People will do anything to avoid feeling it, including violence.",
    "Envy Points To Desires: What someone envies reveals what they secretly want. Pay attention to what they criticize.",
    "Guilt Is Useful But Exhausting: Guilt motivates repair but chronic guilt paralyzes. Healthy guilt vs toxic guilt.",
    "Hope Is A Survival Mechanism: People need to believe things will get better. Without hope, everything collapses.",
    "Boredom Is Underestimated: Boredom drives more behavior than people admit. Risk-taking, creativity, destruction all stem from boredom.",
    "Loneliness Is Not Solitude: Being alone ≠ feeling lonely. Some people feel loneliest in crowds. Context matters.",
    "Emotional Baselines Vary: Some people's default is anxious. Others' is calm. The baseline is set by genetics and early experience.",
    "Emotions Are Contagious: Spend time with an anxious person, you'll feel anxious. This happens automatically, below awareness.",
    "Emotions Have Physical Components: Anxiety feels like tightness. Joy feels like expansion. The body knows before the mind.",
]

# ─────────────────────────────────────────────────────────────────────────────
# SOCIAL RULES (How People Interact)
# ─────────────────────────────────────────────────────────────────────────────
SOCIAL_RULES = [
    "People Perform For Audiences: Everyone has a public self. How they act alone differs from how they act observed.",
    "Status Matters: People constantly track and respond to social hierarchy. Who's above, who's below, who's equal.",
    "Belonging Is A Deep Need: People will suppress their individuality to fit in. The fear of exclusion is primal.",
    "In-Groups and Out-Groups: People naturally divide the world into 'us' and 'them.' This can be mild or extreme.",
    "Social Proof Drives Behavior: 'Everyone's doing it' is a powerful motivator. People look to others for how to act.",
    "Reciprocity Is Automatic: When someone does something for you, you feel obligated to return it. Even small gestures.",
    "Gossip Serves A Function: People talk about others to bond, to share information, to enforce norms. It's social glue.",
    "First Impressions Form Fast and Stick: People make judgments in seconds that are hard to revise. The primacy effect is powerful.",
    "People Mirror Those They Like: Subtle copying of posture, language, pace. Mirroring signals connection.",
    "Embarrassment Is Social Glue: The ability to feel embarrassed signals you care about social norms. Sociopaths don't feel it.",
    "Compliments Create Obligation: When praised, people feel pressure to live up to it or to return it.",
    "Criticism Hurts More From Peers: A stranger's insult stings less than a friend's. People care about their in-group's opinion.",
    "People Compare Upward: They compare themselves to those slightly above, not below. This breeds dissatisfaction.",
    "Social Anxiety Is Universal: Everyone has social fears. The specifics vary but the underlying anxiety is human.",
    "People Want To Be Understood: More than being liked, people want to feel seen. 'You get me' is powerful.",
]

# ─────────────────────────────────────────────────────────────────────────────
# BODY RULES (Physical Reality)
# ─────────────────────────────────────────────────────────────────────────────
BODY_RULES = [
    "Hunger Affects Everything: Low blood sugar makes people irritable, impulsive, and emotionally unstable.",
    "Sleep Deprivation Mimics Mental Illness: Lack of sleep causes anxiety, depression, paranoia, and cognitive decline.",
    "Physical Pain Changes Personality: Chronic pain makes people shorter, more self-focused, less empathetic.",
    "Illness Is Isolating: Being sick separates people from normal life. They feel alone, even with support.",
    "Aging Changes Self-Image: As bodies change, people's relationship to themselves changes. Not always negatively.",
    "The Body Keeps Score: Trauma lives in the body — tension, pain, gut issues. The mind isn't separate.",
    "Energy Fluctuates: No one has consistent energy. Mornings, afternoons, evenings have different capacities.",
    "Exercise Is Mood-Altering: Physical activity has immediate and long-term effects on emotional state.",
    "Sexuality Is Physical: Desire, arousal, and attraction have physiological components. It's not all psychological.",
    "Substance Use Affects Personality: Alcohol, caffeine, weed, pills — these change how someone acts and feels.",
    "Temperature Affects Mood: Too hot or too cold affects irritability and cognitive function.",
    "Physical Affection Is A Need: Touch-starvation is real. People need physical contact for mental health.",
    "The Body Has Rhythms: Circadian cycles, hormonal cycles, hunger cycles. These affect everything.",
    "Appearance Affects Treatment: How someone looks affects how others treat them, which affects how they feel.",
    "Disability Shapes Experience: Physical limitations are not just inconveniences — they reshape how someone moves through the world.",
]

# ─────────────────────────────────────────────────────────────────────────────
# CONVERSATION RULES (How People Talk)
# ─────────────────────────────────────────────────────────────────────────────
CONVERSATION_RULES = [
    "People Interrupt When Excited: Interruption often means engagement, not rudeness. The eager interruption is connection.",
    "Silence Has Meaning: Pauses are communicative. Awkward silence, comfortable silence, angry silence — all different.",
    "People Hedge When Uncertain: 'I think', 'maybe', 'kind of' — these mark uncertainty or politeness.",
    "Storytelling Structure Is Universal: Setup, conflict, resolution. Even casual stories follow this.",
    "People Repeat What They Want Heard: Saying something twice usually means 'acknowledge this.'",
    "Topic Changes Are Strategic: Shifting away from something uncomfortable or toward something desired.",
    "Questions Can Be Statements: 'Are you mad at me?' often means 'I'm worried you're mad at me.'",
    "Compliments Can Be Testing: Praise can check for reciprocity or probe for insecurity.",
    "People Talk Differently To Different People: Tone, vocabulary, content — all shift based on audience.",
    "Text Lacks Tone: Written communication strips away the nonverbal. Misunderstanding is common.",
    "Voice Reveals State: Speed, pitch, and volume reveal emotional state even when words don't.",
    "People Name-Drop For Status: Mentioning connections signals social position. Everyone does it.",
    "Humor Has Functions: Bonding, deflection, coping, aggression. Jokes are rarely just jokes.",
    "Self-Deprecation Can Be Fishing: 'I'm so dumb' often means 'tell me I'm smart.'",
    "People Leave Things Unsaid: The most important things are often the ones not spoken directly.",
]

# ─────────────────────────────────────────────────────────────────────────────
# GROWTH RULES (How People Change)
# ─────────────────────────────────────────────────────────────────────────────
GROWTH_RULES = [
    "Change Requires Discomfort: People don't change when comfortable. Pain, loss, or crisis precipitates growth.",
    "Two Steps Forward, One Step Back: Progress is not linear. Relapse into old patterns is normal.",
    "Insight Doesn't Equal Change: Understanding why you do something doesn't automatically stop you from doing it.",
    "Environment Shapes Behavior: Change the context, change the behavior. Willpower is overrated.",
    "Habit Formation Takes Time: New behaviors need repetition before becoming automatic.",
    "People Rationalize Stagnation: 'That's just how I am' is often an excuse to avoid effort.",
    "Growth Often Looks Like Loss: Becoming who you want to be means losing who you were. This can feel like grief.",
    "Mentors Accelerate Growth: Learning from others' experience is faster than learning from your own.",
    "Failure Is Necessary: No one succeeds at everything. Failed attempts teach what success can't.",
    "Values Clarify Through Choice: People don't know what they value until they have to choose.",
    "Growth Has Plateaus: Progress isn't continuous. Long periods of seeming stuckness are normal.",
    "Others Can See Growth Before You Do: People often can't perceive their own changes. External perspective helps.",
    "Crises Can Be Catalysts: Major life events force re-evaluation and can accelerate growth.",
    "Therapy Works But Slowly: Professional help creates change, but it's gradual and requires effort.",
    "People Can Exceed Their Origins: Background predicts but doesn't determine. Exceptional outcomes are possible.",
]

# ─────────────────────────────────────────────────────────────────────────────
# DECEPTION RULES (How People Lie)
# ─────────────────────────────────────────────────────────────────────────────
DECEPTION_RULES = [
    "Everyone Lies: Small lies are universal. 'I'm fine', 'Traffic was bad', 'I love your haircut.'",
    "People Lie To Protect Self-Image: Not just to deceive others, but to maintain their own narrative.",
    "The Lies People Tell Reveal Values: What someone lies about shows what they're ashamed of or what matters to them.",
    "Omission Is The Commonest Lie: What's left unsaid is often more deceptive than what's said.",
    "People Believe Their Own Lies: Repeated lies become internalized. The liar becomes convinced.",
    "Lies Require Maintenance: One lie leads to more lies to stay consistent. The web grows.",
    "Some People Can't Lie Well: Micro-expressions, voice changes, inconsistencies reveal deception for many.",
    "Confidence Doesn't Equal Truth: Liars can be confident. Truth-tellers can be uncertain. Confidence is not evidence.",
    "People Lie For Good Reasons: To spare feelings, to protect others, to avoid unnecessary conflict. Not all lies are malicious.",
    "The Truth Comes Out Eventually: Secrets have a way of surfacing. The longer they're kept, the more damage when revealed.",
    "Self-Deception Is Common: People lie to themselves more than they lie to others. Denial is powerful.",
    "Guilt Affects Liars: Unless sociopathic, lying creates internal pressure. The guilt leaks.",
    "Details Are The Enemy Of Lies: The more detail requested, the harder it is to maintain a fabrication.",
    "Trained Deception Detection Exists: Some people — therapists, interrogators — are better at spotting lies.",
    "Cultural Differences In Lying: What's considered a lie varies. 'Saving face' cultures have different norms.",
]

# ─────────────────────────────────────────────────────────────────────────────
# ROUTINE RULES (Daily Life)
# ─────────────────────────────────────────────────────────────────────────────
ROUTINE_RULES = [
    "Morning Routines Set The Day: How someone starts their morning affects everything that follows.",
    "People Are Creatures Of Habit: Most days follow patterns. Novelty is rarer than routine.",
    "Routines Reduce Cognitive Load: Habits free up mental energy. Breaking routine costs willpower.",
    "The Same Breakfast Syndrome: People eat the same thing for years. Variety is not a universal value.",
    "Commuting Is Dead Time: Hours spent in transit affect mood, energy, and available free time.",
    "Weekends Reset People: The rhythm of work days and rest days shapes emotional cycles.",
    "Sleep Schedules Vary: Night owls and early birds exist. Not everyone can shift easily.",
    "Chore Distribution Matters: Who does what in a household affects relationships and self-image.",
    "Screen Time Is Massive: Modern people spend hours daily on phones. This is now normal.",
    "Exercise Routines Are Fragile: One missed day leads to a month. Momentum matters.",
    "Food Routines Reflect Culture: What someone eats connects to heritage, family, region.",
    "Rituals Provide Comfort: Holiday traditions, birthday celebrations — these anchor people in time.",
    "Routines Can Become Ruts: What's comforting becomes suffocating. The line is thin.",
    "Disruption Reveals Values: When routine is broken, what someone misses shows what matters.",
    "Routines Hide In Plain Sight: People often don't notice their own patterns until pointed out.",
]

# ─────────────────────────────────────────────────────────────────────────────
# CULTURE RULES (Context and Background)
# ─────────────────────────────────────────────────────────────────────────────
CULTURE_RULES = [
    "Culture Shapes Everything: Values, communication style, emotional expression — all culturally mediated.",
    "Generational Differences Are Real: Each generation has shared experiences that shape worldview.",
    "Geography Affects Perspective: Urban vs rural, coastal vs inland, north vs south — place matters.",
    "Class Is Invisible To Those In It: People often don't see their own class position. It's just 'normal.'",
    "Religion Persists Or Doesn't: Religious upbringing either sticks or creates strong reaction against it.",
    "Language Shapes Thought: The language someone thinks in affects how they think.",
    "Migration Changes People: Moving to a new culture forces adaptation. Old and new exist in tension.",
    "Family Culture Is Primary: The family you grow up in is your first culture. It leaves deep marks.",
    "Historical Events Mark Generations: Wars, recessions, pandemics — these shape everyone who lives through them.",
    "Subcultures Exist Within Cultures: Goth, jock, nerd, punk — these identities cut across other categories.",
    "Cultural Norms Change: What was normal in 1950 isn't normal now. Characters exist in their time.",
    "Multicultural People Bridge Worlds: Those between cultures see things monocultural people don't.",
    "Culture Is Both Constraint And Resource: It limits options but also provides tools and meaning.",
    "The Past Isn't Another Country — It's A Different World: People in different eras thought differently.",
    "Culture Is Often Unconscious: People don't notice their own culture until they encounter others.",
]

# Combine all rules for easy access
ALL_RULES = (
    HUMAN_RULES +
    MECHANICAL_RULES +
    RELATIONSHIP_RULES +
    MEMORY_RULES +
    EMOTION_RULES +
    SOCIAL_RULES +
    BODY_RULES +
    CONVERSATION_RULES +
    GROWTH_RULES +
    DECEPTION_RULES +
    ROUTINE_RULES +
    CULTURE_RULES
)

# Rule count for marketing
RULE_COUNT = len(ALL_RULES)  # 180 rules

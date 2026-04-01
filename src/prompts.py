BASE_SYSTEM_PROMPT = """You are a masterful collaborative storyteller.

Continue the story in the chosen genre while staying 100% consistent with all previous events, character personalities, and world rules.
Never contradict earlier parts of the story.
Write in vivid but concise third-person narrative.
Keep the tone engaging and fun.

Additional rules:
1. Stay fully consistent with earlier events, characters, locations, tone, and world rules.
2. Never overwrite established facts.
3. Maintain the selected genre strongly.
4. Avoid repeating previous sentences or obvious filler.
5. Prefer concrete details over vague abstractions.
6. If continuity notes or character notes are provided, follow them carefully.
7. Output clean markdown paragraphs only unless a task explicitly asks for JSON.
"""


def build_story_prompt(
    *,
    title: str,
    genre: str,
    creativity: float,
    story: str,
    user_input: str,
    continuity_notes: str,
    character_summary: str,
    memory_block: str,
    task: str,
) -> str:
    return f"""Title: {title}
Genre: {genre}
Creativity: {creativity}

Story rules:
- Stay in genre
- Keep continuity
- Build from established facts only
- Keep prose vivid and concise

Continuity notes:
{continuity_notes or 'None yet'}

Character tracker:
{character_summary or 'None yet'}

Relevant long-term memory from Chroma:
{memory_block or '- None yet'}

Story so far:
{story.strip() or '[No story yet]'}

User contribution:
{user_input.strip() or '[No user contribution]'}

Task:
{task}
"""


CHARACTER_TRACKER_PROMPT = """Read the story and return a concise character tracker.

Return JSON with this exact schema:
{
  "characters": [
    {"name": "...", "description": "...", "status": "..."}
  ],
  "continuity_notes": ["..."]
}

Rules:
- Include only clearly established characters.
- Keep each description under 18 words.
- Keep each status under 12 words.
- Continuity notes should be short factual reminders.

Story:
{story}
"""

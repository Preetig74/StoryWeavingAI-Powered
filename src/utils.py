import json

import streamlit as st

from src.llm import generate_text, get_client
from src.memory import add_memory
from src.prompts import CHARACTER_TRACKER_PROMPT


def ensure_session_defaults() -> None:
    defaults = {
        "story_id": "",
        "title": "",
        "genre": "Fantasy",
        "hook": "",
        "story": "",
        "choice_options": [],
        "story_started": False,
        "continuity_notes": "",
        "character_summary": "",
        "last_ai_turn": "",
        "story_rules": [
            "Maintain genre consistency",
            "Do not contradict established facts",
            "Keep characters consistent",
            "Build naturally from the full story so far",
        ],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def append_to_story(text: str) -> None:
    cleaned = text.strip()
    if not cleaned:
        return

    if st.session_state.story.strip():
        st.session_state.story += "\n\n" + cleaned
    else:
        st.session_state.story = cleaned

    st.session_state.last_ai_turn = cleaned


def extract_json_array(text: str) -> list[str]:
    cleaned = text.strip()

    try:
        data = json.loads(cleaned)
        if isinstance(data, list):
            return [str(item).strip() for item in data if str(item).strip()]
    except Exception:
        pass

    lines: list[str] = []
    for raw_line in cleaned.splitlines():
        line = raw_line.strip().lstrip("-*")
        if len(line) > 2 and line[0].isdigit() and "." in line:
            line = line.split(".", 1)[1].strip()
        if line:
            lines.append(line)
    return lines[:3]


def update_character_tracker(model_name: str) -> None:
    client = get_client()

    raw = generate_text(
        client=client,
        model=model_name,
        system_prompt="You extract structured continuity state for a story-writing product.",
        user_prompt=CHARACTER_TRACKER_PROMPT.format(story=st.session_state.story),
        temperature=0.2,
    )

    try:
        data = json.loads(raw)
        characters = data.get("characters", [])
        notes = data.get("continuity_notes", [])

        lines = []
        for item in characters:
            name = item.get("name", "Unknown").strip()
            description = item.get("description", "").strip()
            status = item.get("status", "").strip()
            lines.append(f"- **{name}**: {description} | Status: {status}")

        st.session_state.character_summary = "\n".join(lines) or "No major characters tracked yet."
        st.session_state.continuity_notes = "\n".join(f"- {note}" for note in notes) or ""
    except Exception:
        st.session_state.character_summary = "Character tracker could not be refreshed from structured output."


def refresh_memory_and_trackers(model_name: str) -> None:
    add_memory("story_snapshot", st.session_state.story[-6000:])
    if st.session_state.character_summary:
        add_memory("character_tracker", st.session_state.character_summary)
    if st.session_state.continuity_notes:
        add_memory("continuity_notes", st.session_state.continuity_notes)

    update_character_tracker(model_name)


def undo_last_ai_turn() -> None:
    last_turn = st.session_state.get("last_ai_turn", "").strip()
    if not last_turn or last_turn not in st.session_state.story:
        st.warning("No recent AI turn available to undo.")
        return

    story = st.session_state.story.rstrip()
    if story.endswith(last_turn):
        trimmed = story[: -len(last_turn)].rstrip()
        st.session_state.story = trimmed
        st.session_state.last_ai_turn = ""
    else:
        st.warning("Could not safely undo the last AI turn.")


def export_markdown() -> str:
    if not st.session_state.story:
        return ""
    return (
        f"# {st.session_state.title}\n\n"
        f"**Genre:** {st.session_state.genre}\n\n"
        f"{st.session_state.story}\n"
    )

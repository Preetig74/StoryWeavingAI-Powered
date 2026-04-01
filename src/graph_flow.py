from typing import List, TypedDict

import streamlit as st
from langgraph.graph import END, START, StateGraph

from src.llm import generate_text, get_client
from src.memory import add_memory, fetch_relevant_memory
from src.prompts import BASE_SYSTEM_PROMPT, build_story_prompt
from src.utils import append_to_story, extract_json_array, refresh_memory_and_trackers


class StoryState(TypedDict, total=False):
    mode: str
    title: str
    genre: str
    hook: str
    user_input: str
    creativity: float
    story: str
    selected_choice: str
    continuity_notes: str
    character_summary: str
    llm_output: str
    choice_options: List[str]
    model: str


def _memory_block(state: StoryState) -> str:
    memories = fetch_relevant_memory(
        f"Genre: {state['genre']}\nTitle: {state['title']}\nStory: {state['story']}\nUser input: {state.get('user_input', '')}",
        k=6,
    )
    return "\n".join(f"- {item}" for item in memories) if memories else "- None yet"


def build_graph():
    def generate_opening(state: StoryState) -> StoryState:
        client = get_client()
        prompt = build_story_prompt(
            title=state["title"],
            genre=state["genre"],
            creativity=state["creativity"],
            story=state.get("hook", ""),
            user_input="",
            continuity_notes=state.get("continuity_notes", ""),
            character_summary=state.get("character_summary", ""),
            memory_block=_memory_block(state),
            task="Write the opening of the story in 150 to 250 words. Start strong, grounded in the hook, and establish tone clearly.",
        )
        output = generate_text(
            client=client,
            model=state["model"],
            system_prompt=BASE_SYSTEM_PROMPT,
            user_prompt=prompt,
            temperature=state["creativity"],
        )
        return {"llm_output": output}

    def continue_story(state: StoryState) -> StoryState:
        client = get_client()
        prompt = build_story_prompt(
            title=state["title"],
            genre=state["genre"],
            creativity=state["creativity"],
            story=state["story"],
            user_input=state.get("user_input", ""),
            continuity_notes=state.get("continuity_notes", ""),
            character_summary=state.get("character_summary", ""),
            memory_block=_memory_block(state),
            task="Continue the story in 1 to 2 coherent paragraphs. Advance plot meaningfully while preserving continuity.",
        )
        output = generate_text(
            client=client,
            model=state["model"],
            system_prompt=BASE_SYSTEM_PROMPT,
            user_prompt=prompt,
            temperature=state["creativity"],
        )
        return {"llm_output": output}

    def generate_choices(state: StoryState) -> StoryState:
        client = get_client()
        prompt = build_story_prompt(
            title=state["title"],
            genre=state["genre"],
            creativity=state["creativity"],
            story=state["story"],
            user_input=state.get("user_input", ""),
            continuity_notes=state.get("continuity_notes", ""),
            character_summary=state.get("character_summary", ""),
            memory_block=_memory_block(state),
            task="Generate exactly 3 distinct next-step choices for the story. Return only a JSON array of 3 strings. Each choice should be one sentence.",
        )
        raw = generate_text(
            client=client,
            model=state["model"],
            system_prompt=BASE_SYSTEM_PROMPT,
            user_prompt=prompt,
            temperature=min(1.0, max(0.3, state["creativity"] + 0.1)),
        )
        return {"choice_options": extract_json_array(raw)[:3]}

    def apply_choice_and_continue(state: StoryState) -> StoryState:
        client = get_client()
        appended_story = (state["story"] + "\n\n" + state["selected_choice"]).strip()
        prompt = build_story_prompt(
            title=state["title"],
            genre=state["genre"],
            creativity=state["creativity"],
            story=appended_story,
            user_input="",
            continuity_notes=state.get("continuity_notes", ""),
            character_summary=state.get("character_summary", ""),
            memory_block=_memory_block({**state, "story": appended_story}),
            task="Continue the story in 1 to 2 paragraphs based on the selected choice that was just added to the story.",
        )
        output = generate_text(
            client=client,
            model=state["model"],
            system_prompt=BASE_SYSTEM_PROMPT,
            user_prompt=prompt,
            temperature=state["creativity"],
        )
        return {"llm_output": output}

    graph = StateGraph(StoryState)
    graph.add_node("generate_opening", generate_opening)
    graph.add_node("continue_story", continue_story)
    graph.add_node("generate_choices", generate_choices)
    graph.add_node("apply_choice_and_continue", apply_choice_and_continue)

    graph.add_edge(START, "generate_opening")
    graph.add_edge("generate_opening", END)
    graph.add_edge("continue_story", END)
    graph.add_edge("generate_choices", END)
    graph.add_edge("apply_choice_and_continue", END)

    return graph.compile()


def start_story_flow(*, title: str, genre: str, hook: str, creativity: float, model_name: str) -> None:
    app = build_graph()
    state: StoryState = {
        "mode": "start",
        "title": title,
        "genre": genre,
        "hook": hook,
        "story": hook.strip(),
        "user_input": "",
        "creativity": creativity,
        "continuity_notes": st.session_state.continuity_notes,
        "character_summary": st.session_state.character_summary,
        "model": model_name,
    }
    result = app.invoke(state)

    st.session_state.story = result.get("llm_output", "")
    st.session_state.story_started = True
    st.session_state.choice_options = []
    refresh_memory_and_trackers(model_name)


def continue_story_flow(user_input: str, creativity: float, model_name: str) -> None:
    if user_input.strip():
        append_to_story(user_input.strip())
        add_memory("user_turn", user_input.strip())

    app = build_graph()
    state: StoryState = {
        "mode": "continue",
        "title": st.session_state.title,
        "genre": st.session_state.genre,
        "hook": st.session_state.hook,
        "story": st.session_state.story,
        "user_input": user_input,
        "creativity": creativity,
        "continuity_notes": st.session_state.continuity_notes,
        "character_summary": st.session_state.character_summary,
        "model": model_name,
    }
    result = app.invoke(state)

    append_to_story(result.get("llm_output", ""))
    st.session_state.choice_options = []
    refresh_memory_and_trackers(model_name)


def generate_choices_flow(user_input: str, creativity: float, model_name: str) -> None:
    if user_input.strip():
        append_to_story(user_input.strip())
        add_memory("user_turn", user_input.strip())

    app = build_graph()
    state: StoryState = {
        "mode": "choices",
        "title": st.session_state.title,
        "genre": st.session_state.genre,
        "hook": st.session_state.hook,
        "story": st.session_state.story,
        "user_input": user_input,
        "creativity": creativity,
        "continuity_notes": st.session_state.continuity_notes,
        "character_summary": st.session_state.character_summary,
        "model": model_name,
    }
    result = app.invoke(state)
    st.session_state.choice_options = result.get("choice_options", [])


def apply_choice_flow(choice: str, creativity: float, model_name: str) -> None:
    app = build_graph()
    state: StoryState = {
        "mode": "apply_choice",
        "title": st.session_state.title,
        "genre": st.session_state.genre,
        "hook": st.session_state.hook,
        "story": st.session_state.story,
        "user_input": "",
        "selected_choice": choice,
        "creativity": creativity,
        "continuity_notes": st.session_state.continuity_notes,
        "character_summary": st.session_state.character_summary,
        "model": model_name,
    }
    result = app.invoke(state)

    append_to_story(choice)
    append_to_story(result.get("llm_output", ""))
    st.session_state.choice_options = []
    refresh_memory_and_trackers(model_name)

import streamlit as st

from src.config import GENRES, init_env, get_model_name
from src.graph_flow import (
    apply_choice_flow,
    continue_story_flow,
    generate_choices_flow,
    start_story_flow,
)
from src.llm import get_client
from src.memory import fetch_relevant_memory
from src.utils import (
    append_to_story,
    ensure_session_defaults,
    export_markdown,
    undo_last_ai_turn,
)


def main() -> None:
    init_env()
    ensure_session_defaults()

    st.set_page_config(page_title="AI-Powered Story Weaver", layout="wide")
    st.title("AI-Powered Story Weaver")
    st.caption("Preeti's demo of an interactive storytelling app with LLM and memory integration.")

    with st.sidebar:
        st.subheader("Story Controls")
        creativity = st.slider("Temperature / Creativity", 0.0, 1.2, 0.7, 0.1)
        model_name = st.text_input("Model", value=get_model_name())

        st.markdown("### Current Genre")
        st.info(st.session_state.genre if st.session_state.story_started else "Not started")

        st.markdown("### Story Rules")
        for rule in st.session_state.story_rules:
            st.write(f"- {rule}")

        st.markdown("### Actions")
        if st.button("Undo Last AI Turn"):
            try:
                undo_last_ai_turn()
            except Exception as exc:
                st.error(f"Undo failed: {exc}")

        st.download_button(
            "Export Markdown",
            data=export_markdown(),
            file_name=f"{(st.session_state.title or 'story').replace(' ', '_').lower()}.md",
            mime="text/markdown",
            disabled=not bool(st.session_state.story),
        )

    if not st.session_state.story_started:
        st.subheader("1) Story Setup")
        st.session_state.title = st.text_input("Title", value=st.session_state.title)
        st.session_state.genre = st.selectbox(
            "Genre",
            options=GENRES,
            index=GENRES.index(st.session_state.genre) if st.session_state.genre in GENRES else 0,
        )
        st.session_state.hook = st.text_area(
            "Initial Hook / Setting",
            value=st.session_state.hook,
            height=180,
            placeholder="A clockmaker discovers that every watch repaired at midnight steals five minutes from its owner's future.",
        )

        if st.button("Start the Story", type="primary"):
            try:
                if not st.session_state.title.strip():
                    st.warning("Please add a title.")
                    st.stop()
                if not st.session_state.hook.strip():
                    st.warning("Please add an initial hook or setting.")
                    st.stop()

                with st.spinner("Generating opening..."):
                    start_story_flow(
                        title=st.session_state.title,
                        genre=st.session_state.genre,
                        hook=st.session_state.hook,
                        creativity=creativity,
                        model_name=model_name,
                    )
                st.success("Story started.")
                st.rerun()
            except Exception as exc:
                st.error(f"Could not start story: {exc}")
        return

    col1, col2 = st.columns([2.2, 1])

    with col1:
        st.subheader("2) Main Storytelling View")
        st.markdown("### Story So Far")
        st.markdown(st.session_state.story)

        user_turn = st.text_area(
            "Add your line or paragraph",
            height=140,
            placeholder="The lantern in her hand began to hum when she spoke the captain's name.",
        )

        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("Continue with AI", type="primary"):
                try:
                    with st.spinner("Continuing story..."):
                        continue_story_flow(user_turn, creativity, model_name)
                    st.rerun()
                except Exception as exc:
                    st.error(f"Generation failed: {exc}")

        with btn_col2:
            if st.button("Give Me Choices"):
                try:
                    with st.spinner("Generating choices..."):
                        generate_choices_flow(user_turn, creativity, model_name)
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not generate choices: {exc}")

        if st.session_state.choice_options:
            st.markdown("### Choose the next direction")
            for idx, option in enumerate(st.session_state.choice_options, start=1):
                if st.button(f"Option {idx}: {option}"):
                    try:
                        with st.spinner("Applying choice..."):
                            apply_choice_flow(option, creativity, model_name)
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not apply choice: {exc}")

    with col2:
        st.subheader("3) Story State")
        st.markdown(f"**Title:** {st.session_state.title}")
        st.markdown(f"**Genre:** {st.session_state.genre}")

        st.markdown("### Character Tracker")
        st.markdown(st.session_state.character_summary or "No characters tracked yet.")

        st.markdown("### Continuity Notes")
        st.markdown(st.session_state.continuity_notes or "No continuity notes yet.")

        with st.expander("Memory Debug (Chroma retrieval preview)"):
            memories = fetch_relevant_memory(st.session_state.story[-1000:] or st.session_state.title, k=5)
            if memories:
                for memory in memories:
                    st.write(f"- {memory}")
            else:
                st.write("No memory retrieved yet.")


if __name__ == "__main__":
    main()

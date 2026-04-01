import uuid
from datetime import datetime
from typing import Any

import chromadb
import streamlit as st
from chromadb.config import Settings

from src.config import CHROMA_DIR, COLLECTION_NAME


def get_collection():
    client = chromadb.PersistentClient(
        path=CHROMA_DIR,
        settings=Settings(anonymized_telemetry=False),
    )
    return client.get_or_create_collection(name=COLLECTION_NAME)


def current_story_id() -> str:
    if "story_id" not in st.session_state:
        st.session_state.story_id = str(uuid.uuid4())
    return st.session_state.story_id


def story_metadata() -> dict[str, Any]:
    return {
        "story_id": current_story_id(),
        "title": st.session_state.title,
        "genre": st.session_state.genre,
        "updated_at": datetime.utcnow().isoformat(),
    }


def add_memory(kind: str, content: str) -> None:
    if not content.strip():
        return

    collection = get_collection()
    metadata = story_metadata()
    metadata["kind"] = kind

    collection.add(
        ids=[f"{current_story_id()}::{kind}::{uuid.uuid4()}"],
        documents=[content],
        metadatas=[metadata],
    )


def fetch_relevant_memory(query_text: str, k: int = 5) -> list[str]:
    collection = get_collection()
    try:
        results = collection.query(
            query_texts=[query_text],
            n_results=k,
            where={"story_id": current_story_id()},
        )
        documents = results.get("documents", [[]])
        return documents[0] if documents else []
    except Exception:
        return []

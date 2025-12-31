"""
Singapore Rental RAG Assistant
Streamlit Web UI - Main Entry File
"""
import streamlit as st

from llm.deepseek_llm import get_deepseek_llm
from rag.retriever import load_vectorstore, create_retriever
from rag.chain import run_rag_query
from ui.layout import render_app
from ui.components import normalize_sources
from config import (
    DEEPSEEK_API_KEY,
    FAISS_PERSIST_DIR,
    FAISS_INDEX_NAME,
    INITIAL_RETRIEVAL_K,
)

# =========================================================
# Page config (ONLY here)
# =========================================================
st.set_page_config(
    page_title="SG Rental RAG Assistant",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =========================================================
# Session State Initialization (STRICT keys)
# =========================================================
def init_session_state():
    st.session_state.setdefault("user_identity", "Not Sure")
    st.session_state.setdefault("draft_question", "")
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("sources", [])
    st.session_state.setdefault("kb_loaded", False)
    st.session_state.setdefault("kb_blocks_count", 0)
    st.session_state.setdefault("api_key", DEEPSEEK_API_KEY or "")

    # Internal shared objects
    st.session_state.setdefault("vectorstore", None)
    st.session_state.setdefault("llm_instance", None)
    st.session_state.setdefault("retriever_instance", None)


# =========================================================
# Knowledge Base Loader (callable by UI)
# =========================================================
def load_knowledge_base():
    if st.session_state.kb_loaded and st.session_state.vectorstore:
        return st.session_state.vectorstore

    try:
        vectorstore = load_vectorstore(
            persist_directory=FAISS_PERSIST_DIR,
            index_name=FAISS_INDEX_NAME,
        )
        if vectorstore:
            st.session_state.vectorstore = vectorstore
            st.session_state.kb_loaded = True
            try:
                st.session_state.kb_blocks_count = vectorstore.index.ntotal
            except Exception:
                st.session_state.kb_blocks_count = 0
            return vectorstore
    except Exception:
        pass

    st.session_state.kb_loaded = False
    st.session_state.kb_blocks_count = 0
    st.session_state.vectorstore = None
    return None


# =========================================================
# RAG Query Handler (CALL ONLY, no side effects elsewhere)
# =========================================================
def handle_rag_query(question: str):
    api_key = st.session_state.get("api_key", "")
    if not api_key:
        return ""

    vectorstore = load_knowledge_base()
    if not vectorstore:
        return ""

    try:
        # Cache LLM instance to avoid recreating it every time
        llm = st.session_state.get("llm_instance")
        if llm is None or st.session_state.get("api_key") != api_key:
            llm = get_deepseek_llm(api_key=api_key)
            st.session_state.llm_instance = llm
        
        # Cache retriever instance to avoid recreating it every time
        retriever = st.session_state.get("retriever_instance")
        if retriever is None or st.session_state.get("vectorstore") != vectorstore:
            retriever = create_retriever(vectorstore, k=INITIAL_RETRIEVAL_K)
            st.session_state.retriever_instance = retriever

        identity = st.session_state.get("user_identity", "Not Sure")
        if identity and identity != "Not Sure":
            question = f"(User identity: {identity}) {question}"

        # Execute query (progress will be shown in UI via placeholder)
        result = run_rag_query(question, llm, retriever)

        answer = result.get("answer", "")
        raw_citations = result.get("citations", [])

        st.session_state.sources = normalize_sources(raw_citations)
        return answer

    except Exception as e:
        return f"❌ Error occurred: {e}"


# =========================================================
# App Entry
# =========================================================
# Initialize state
init_session_state()

# Load knowledge base (only sync status, no UI effect)
load_knowledge_base()

# Handle trigger_send
if st.session_state.get("trigger_send", False):
    st.session_state.trigger_send = False
    messages = st.session_state.get("messages", [])
    if messages and messages[-1].get("role") == "user":
        question = messages[-1].get("content", "")
        # Show loading placeholder
        with st.spinner("🔍 Searching knowledge base and generating answer..."):
            answer = handle_rag_query(question)
        if answer:
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer
            })
            st.rerun()

# Handle trigger_regenerate
if st.session_state.get("trigger_regenerate", False):
    st.session_state.trigger_regenerate = False
    messages = st.session_state.get("messages", [])
    # Find last user message
    last_user_msg = None
    for msg in reversed(messages):
        if msg.get("role") == "user":
            last_user_msg = msg.get("content")
            break
    
    if last_user_msg:
        # Remove last assistant message
        if messages and messages[-1].get("role") == "assistant":
            messages.pop()
            st.session_state.messages = messages
        
        # Show loading placeholder
        with st.spinner("🔄 Regenerating answer..."):
            answer = handle_rag_query(last_user_msg)
        if answer:
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer
            })
            st.rerun()

# Render UI (ALL UI lives in ui/layout.py)
render_app()

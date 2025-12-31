"""
UI Layout
Simple Streamlit UI Layout Module
"""
import streamlit as st
from typing import Optional
from config import EXAMPLE_QUESTIONS


def render_app():
    """Render entire application (main entry)"""
    # Title
    st.title("🏠 Singapore Rental RAG Assistant")
    
    # Identity selection
    st.subheader("Select Your Identity")
    identities = ["Not Sure", "Student Pass", "Employment Pass(EP)", "LTVP", "Others"]
    selected_identity = st.radio(
        "Identity",
        identities,
        horizontal=True,
        index=identities.index(st.session_state.get("user_identity", "Not Sure")),
        label_visibility="collapsed"
    )
    st.session_state.user_identity = selected_identity
    
    st.divider()
    
    # Knowledge base status
    with st.sidebar:
        st.header("Knowledge Base Status")
        kb_loaded = st.session_state.get("kb_loaded", False)
        kb_blocks_count = st.session_state.get("kb_blocks_count", 0)
        
        if kb_loaded:
            st.success(f"✅ Loaded ({kb_blocks_count} blocks)")
        else:
            st.error("❌ Not loaded")
            # Show error message if available
            kb_error = st.session_state.get("kb_load_error")
            if kb_error:
                st.caption(f"Error: {kb_error}")
            else:
                st.caption("Make sure data/faiss/ files are uploaded to GitHub")
        
        st.divider()
        
        st.header("Function Description")
        st.markdown("""
        **Supported Issues:**
        - Rental Eligibility (Student Pass / EP / LTVP, etc.)
        - Differences in HDB and Private Residential Rental Rules
        - Minimum Lease Term and Occupancy Restrictions
        - Rental Process (Viewing → Contract → Deposit → Move-in)
        - Official Risk Warnings and Consequences of Violations
        - Tenancy Renewal and Contract Terms
        
        **Not Supported:**
        - Rent Price Forecasting
        - Legal Liability Adjudication
        - Case-by-Case Dispute Resolution
        """)
        
        st.divider()
        
        st.markdown("""
        **⚠️ Disclaimer:**
        
        This system only provides information aggregation and citation and does not constitute legal advice.
        All information is derived from official documents, but the latest policies are not guaranteed.
        For important decisions, please consult official agencies (HDB, CEA, URA).
        """)
    
    # Quick Start
    st.subheader("Quick Start")
    st.markdown("Click a question below to get started, or enter your own question.")
    
    # Example questions
    cols = st.columns(2)
    for i, question in enumerate(EXAMPLE_QUESTIONS[:2]):
        with cols[i % 2]:
            if st.button(question, key=f"example_{i}", use_container_width=True):
                st.session_state.draft_question = question
                st.rerun()
    
    if len(EXAMPLE_QUESTIONS) > 2:
        with st.expander("More example questions"):
            for i, question in enumerate(EXAMPLE_QUESTIONS[2:], start=2):
                if st.button(question, key=f"example_{i}", use_container_width=True):
                    st.session_state.draft_question = question
                    st.rerun()
    
    st.divider()
    
    # Chat history
    messages = st.session_state.get("messages", [])
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        with st.chat_message(role):
            st.markdown(content)
    
    # Handle trigger_send and trigger_regenerate will be handled in app.py
    
    # Input area
    draft = st.session_state.get("draft_question", "")
    question = st.chat_input(
        "Please enter your question."
    )
    
    if question:
        st.session_state.messages.append({
            "role": "user",
            "content": question
        })
        st.session_state.draft_question = ""
        st.session_state.trigger_send = True
        st.rerun()
    
    # Also handle draft_question if set
    if draft and not question:
        st.session_state.draft_question = ""
        st.session_state.messages.append({
            "role": "user",
            "content": draft
        })
        st.session_state.trigger_send = True
        st.rerun()
    
    # Regenerate button
    if messages:
        last_user_msg = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content")
                break
        
        if last_user_msg and messages[-1].get("role") == "assistant":
            if st.button("↻ Regenerate response", use_container_width=True):
                st.session_state.trigger_regenerate = True
                st.rerun()
    
    # Sources panel
    sources = st.session_state.get("sources", [])
    if sources:
        st.divider()
        st.subheader("Sources")
        for source in sources:
            title = source.get("title", "Link to website")
            url = source.get("url", "#")
            snippet = source.get("snippet", "")
            
            with st.expander(f"🔗 {title}"):
                st.markdown(f"**URL:** {url}")
                if snippet:
                    st.markdown(f"**Snippet:** {snippet}")
    
    # Footer
    st.divider()
    st.markdown(
        """
        <div style="text-align: center; color: #666; font-size: 0.9em;">
        🏠 Singapore Rental RAG Assistant | Powered by LangChain + DeepSeek API | 
        Data sources: <b>HDB</b>, <b>CEA</b>, <b>URA</b> official websites
        </div>
        """,
        unsafe_allow_html=True
    )

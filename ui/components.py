"""
UI Components
Component Functions Module
"""
import streamlit as st
from typing import List, Dict, Optional


def render_identity_tabs(selected: str) -> Optional[str]:
    """
    Render identity selection tabs (chip style)
    
    Args:
        selected: Currently selected identity
    
    Returns:
        If a tab is clicked, returns the new identity string, otherwise returns None
    """
    identities = ["Not Sure", "Student Pass", "Employment Pass(EP)", "LTVP", "Others"]
    
    st.markdown('<div class="identity-tabs">', unsafe_allow_html=True)
    
    cols = st.columns(len(identities), gap="small")
    new_selected = None
    
    for i, identity in enumerate(identities):
        with cols[i]:
            is_active = identity == selected
            button_key = f"identity_{i}"
            
            # Use button to achieve chip effect
            # CSS will set styles based on data-active attribute (by checking session_state)
            if st.button(
                identity,
                key=button_key,
                use_container_width=True
            ):
                new_selected = identity
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    return new_selected


def render_quick_start_chips(example_questions: List[str]) -> Optional[str]:
    """
    Render quick start example question chips
    
    Args:
        example_questions: List of example questions
    
    Returns:
        If a chip is clicked, returns the question text, otherwise returns None
    """
    # Title
    st.markdown('<div class="section-title">Quick Start</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Click the question below to get started quickly, or enter your question in the input box below.</div>',
        unsafe_allow_html=True
    )
    
    st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
    
    # First two questions
    if len(example_questions) >= 2:
        q1, q2 = st.columns([1, 1], gap="large")
        with q1:
            if st.button(example_questions[0], key="q1", use_container_width=True):
                return example_questions[0]
        with q2:
            if st.button(example_questions[1], key="q2", use_container_width=True):
                return example_questions[1]
    
    # More example questions (expander)
    if len(example_questions) > 2:
        st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
        with st.expander("➕ More example questions", expanded=False):
            cols = st.columns(2)
            for i in range(2, len(example_questions)):
                col = cols[(i - 2) % 2]
                with col:
                    if st.button(
                        example_questions[i],
                        key=f"q_more_{i}",
                        use_container_width=True
                    ):
                        return example_questions[i]
    
    return None


def render_chat_message(role: str, content: str, show_actions: bool = False):
    """
    Render chat message bubble
    
    Args:
        role: "user" or "assistant"
        content: Message content
        show_actions: Whether to show action buttons (like/dislike)
    """
    msg_class = "msg-user" if role == "user" else "msg-assistant"
    
    st.markdown(f'<div class="{msg_class}">', unsafe_allow_html=True)
    st.markdown(content)
    
    if role == "assistant" and show_actions:
        st.markdown(
            """
            <div class="answer-actions">
                <button>👍</button>
                <button>👎</button>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_sources_panel(sources: List[Dict[str, str]]):
    """
    Render right panel sources
    
    Args:
        sources: List of sources, each element contains {"title": str, "url": str, "snippet": str}
    """
    st.markdown('<div class="sources-wrap">', unsafe_allow_html=True)
    
    st.markdown(
        '<div class="panel-title">Links to <b>Document</b> and <b>Website</b> for this Response</div>',
        unsafe_allow_html=True
    )
    
    if sources and len(sources) > 0:
        for source in sources:
            title = source.get("title", "Link to website")
            url = source.get("url", "#")
            snippet = source.get("snippet", "This is the relevant content from the website. This is the relevant content from the website. This is the relevant content from the website.")
            
            st.markdown(
                f"""
                <div class="source-card">
                    <a class="source-title" href="{url}" target="_blank">
                        <span>{title}</span>
                        <span style="opacity:.6;">🔗</span>
                    </a>
                    <div class="source-snippet">{snippet}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        # Scroll indicator
        st.markdown(
            """
            <div style="display:flex; justify-content:center; margin-top:18px; opacity:.7; font-size:22px;">
                ⌄
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        # Empty state: show placeholder text (as per reference UI)
        st.markdown(
            """
            <div style="height: 480px; display:flex; align-items:center; justify-content:center;">
                <div style="text-align:center; font-size:28px; font-weight:900; color:#1E2B55; line-height:1.25;">
                    This section will display<br/>
                    <span style="color:#2F6FEA;">links</span> to the referenced<br/>
                    <span style="color:#2F6FEA;">websites</span>.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    st.markdown('</div>', unsafe_allow_html=True)


def normalize_sources(raw_citations: List[Dict]) -> List[Dict[str, str]]:
    """
    Adapter function: Convert original citations format to standard sources format
    
    Args:
        raw_citations: Original citations list (may contain title, url, desc/snippet fields)
    
    Returns:
        Normalized sources list, each element contains {"title": str, "url": str, "snippet": str}
    """
    normalized = []
    for cit in raw_citations:
        # Compatible with different field names
        title = cit.get("title", cit.get("name", "Link to website"))
        url = cit.get("url", cit.get("link", "#"))
        snippet = cit.get("snippet", cit.get("desc", cit.get("description", "")))
        
        normalized.append({
            "title": title,
            "url": url,
            "snippet": snippet
        })
    
    return normalized


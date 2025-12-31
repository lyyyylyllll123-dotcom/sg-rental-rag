"""
UI Layout
Main Layout Rendering Module
"""
import streamlit as st
from typing import Optional, List, Dict
from ui.components import (
    render_quick_start_chips,
    render_chat_message,
    render_sources_panel,
    normalize_sources,
)
from config import EXAMPLE_QUESTIONS


def inject_css():
    """Inject CSS styles"""
    import os
    css_path = os.path.join(os.path.dirname(__file__), "styles.css")
    try:
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Failed to load CSS: {e}")


def render_topbar():
    """Render top navigation bar"""
    st.markdown(
        """
        <div class="topbar">
            <div class="brand">
                <div class="logo-sg">SG</div>
                <div class="logo-stack">
                    <div class="logo-rental">Rental RAG</div>
                    <div class="logo-assistant">Assistant</div>
                </div>
            </div>
            <div class="identity-tabs">
        """,
        unsafe_allow_html=True
    )
    
    # Identity selection tabs (rendered directly in topbar)
    current_identity = st.session_state.get("user_identity", "Not Sure")
    identities = ["Not Sure", "Student Pass", "Employment Pass(EP)", "LTVP", "Others"]
    
    cols = st.columns(len(identities), gap="small")
    new_identity = None
    
    for i, identity in enumerate(identities):
        with cols[i]:
            is_active = identity == current_identity
            button_key = f"identity_{i}"
            
            # Add marker based on active state (for CSS selection)
            if is_active:
                st.markdown(f'<div class="identity-chip-wrapper active" data-identity="{identity}">', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="identity-chip-wrapper" data-identity="{identity}">', unsafe_allow_html=True)
            
            if st.button(
                identity,
                key=button_key,
                use_container_width=True
            ):
                new_identity = identity
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    if new_identity:
        st.session_state.user_identity = new_identity
        st.rerun()
    
    st.markdown(
        """
            </div>
            <div class="avatar">👤</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_left_panel():
    """Render left panel content"""
    # Panel 1: Knowledge base status (first panel, no Configuration panel)
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Knowledge base status</div>', unsafe_allow_html=True)
    
    kb_loaded = st.session_state.get("kb_loaded", False)
    kb_blocks_count = st.session_state.get("kb_blocks_count", 0)
    
    if kb_loaded:
        st.markdown(
            """
            <div class="status-pill">
                <span class="dot"></span>
                <span>The knowledge base has been loaded.</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <div class="status-pill" style="background:#FF6B6B;">
                <span class="dot" style="background:#fff;"></span>
                <span>Not loaded</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    st.markdown(
        f'<div class="small-muted">Contains {kb_blocks_count} document blocks</div>',
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Panel 2: Function Description
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Function Description</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <h4>Supported Issues:</h4>
        <ul class="list">
            <li class="li-ok">Rental Eligibility (Student Pass / EP / LTVP, etc.)</li>
            <li class="li-ok">Differences in HDB and Private Residential Rental Rules</li>
            <li class="li-ok">Minimum Lease Term and Occupancy Restrictions</li>
            <li class="li-ok">Rental Process (Viewing → Contract → Deposit → Move-in)</li>
            <li class="li-ok">Official Risk Warnings and Consequences of Violations</li>
            <li class="li-ok">Tenancy Renewal and Contract Terms</li>
        </ul>
        <div style="height:10px;"></div>
        <h4>Not Supported:</h4>
        <ul class="list">
            <li class="li-no">Rent Price Forecasting</li>
            <li class="li-no">Legal Liability Adjudication</li>
            <li class="li-no">Case-by-Case Dispute Resolution</li>
        </ul>
        """,
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Panel 3: Disclaimer
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">⚠️ Disclaimer</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div style="font-size:13px; line-height:1.45; color: rgba(31,42,68,.78); font-weight:650;">
            This system only provides information aggregation and citation and does not constitute legal advice.
            All information is derived from official documents, but the latest policies are not guaranteed.
            For important decisions, please consult official agencies (HDB, CEA, URA).
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Upgrade button
    st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
    st.button("✨  Upgrade to Plus", key="upgrade_btn", use_container_width=True)


def render_main_content():
    """Render main content area"""
    # Quick Start
    selected_question = render_quick_start_chips(EXAMPLE_QUESTIONS)
    if selected_question:
        st.session_state.draft_question = selected_question
        st.rerun()
    
    st.markdown("<hr/>", unsafe_allow_html=True)
    
    # Chat history
    st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)
    
    messages = st.session_state.get("messages", [])
    for i, msg in enumerate(messages):
        is_last_assistant = (
            i == len(messages) - 1 and 
            msg.get("role") == "assistant"
        )
        render_chat_message(
            msg.get("role", "user"),
            msg.get("content", ""),
            show_actions=is_last_assistant
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Regenerate button
    if messages:
        last_user_msg = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content")
                break
        
        if last_user_msg:
            st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
            regen_col1, regen_col2, regen_col3 = st.columns([1.15, 1, 1.15])
            with regen_col2:
                if st.button("↻  Regenerate response", key="regen_btn", use_container_width=True):
                    # Trigger regenerate (by clearing last assistant message and re-calling)
                    if len(messages) > 0 and messages[-1].get("role") == "assistant":
                        messages.pop()
                    st.session_state.messages = messages
                    st.session_state.trigger_regenerate = True
                    st.rerun()


def render_sticky_input():
    """Render bottom sticky input bar"""
    st.markdown('<div class="sticky-input">', unsafe_allow_html=True)
    
    draft = st.session_state.get("draft_question", "")
    
    input_col, send_col = st.columns([9, 1.2], gap="small")
    
    with input_col:
        # Use key parameter to let Streamlit manage input state
        # value parameter is for pre-filling (when draft_question is set)
        question = st.text_input(
            "question_input",
            value=draft,
            placeholder="Please enter your question.",
            label_visibility="collapsed",
            key="question_input"
        )
    
    with send_col:
        send = st.button("➤", key="send_btn", use_container_width=True)
    
    if send and question.strip():
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": question.strip()
        })
        st.session_state.draft_question = ""  # Clear pre-fill
        st.session_state.trigger_send = True
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_right_panel():
    """Render right panel sources"""
    sources = st.session_state.get("sources", [])
    render_sources_panel(sources)


def render_body():
    """Render main three-column layout"""
    col_left, col_main, col_right = st.columns([0.22, 0.56, 0.22], gap="large")
    
    with col_left:
        render_left_panel()
    
    with col_main:
        render_main_content()
        render_sticky_input()
        
        # Footer
        st.markdown(
            """
            <div class="footer">
                🏠 Singapore Rental RAG Assistant | Powered by LangChain + DeepSeek API | Data sources: <b>HDB</b>, <b>CEA</b>, <b>URA</b> official websites
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col_right:
        render_right_panel()


def render_app():
    """Render entire application (main entry)"""
    inject_css()
    render_topbar()
    render_body()


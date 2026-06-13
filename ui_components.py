from __future__ import annotations

import streamlit as st

def qai_logo(title: str = "QAI", subtitle: str = "Learning Platform") -> None:
    st.markdown(
        f"""
        <div style='padding:.5rem 0 1rem 0'>
          <div class='qai-logo-badge'>{title}</div>
          <div style='font-weight:800;font-size:1rem;color:white'>{subtitle}</div>
          <div style='font-size:.75rem;color:rgba(255,255,255,.62)'>Quantum + AI supported learning</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def section_card(title: str, body: str = "") -> None:
    st.markdown(f"<div class='qai-card'><h3>{title}</h3><p>{body}</p></div>", unsafe_allow_html=True)

def soft_badge(text: str) -> None:
    st.markdown(f"<span class='qai-pill'>{text}</span>", unsafe_allow_html=True)

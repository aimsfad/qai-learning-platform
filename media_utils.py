from __future__ import annotations

from pathlib import Path
import streamlit as st

def render_image(path: Path, caption: str | None = None) -> bool:
    if path.exists() and path.stat().st_size > 0:
        st.image(str(path), use_container_width=True, caption=caption)
        return True
    st.warning(f"Image file not found or empty: {path.name}")
    return False

def render_video(path: Path, caption: str | None = None) -> bool:
    if path.exists() and path.stat().st_size > 0:
        if caption:
            st.caption(caption)
        try:
            st.video(path.read_bytes(), format="video/mp4")
        except Exception:
            st.video(str(path))
        st.caption(f"Loaded video: {path.name} · {path.stat().st_size/1024:.1f} KB")
        return True
    st.warning(f"Video file not found or empty: {path.name}")
    return False

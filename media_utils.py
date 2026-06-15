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


# ─── NEW: interactive HTML simulators ──────────────────────────────────────

# Map lesson_id -> (filename, recommended iframe height in px)
SIMULATOR_FILES: dict[str, tuple[str, int]] = {
    "orientation":            ("orientation_simulator.html",          520),
    "qubit_measurement":      ("qubit_measurement_simulator.html",    620),
    "hadamard_superposition": ("hadamard_superposition_simulator.html", 540),
    "shots_counts":           ("shots_counts_simulator.html",         640),
    "cnot_correlation":       ("cnot_correlation_simulator.html",     680),
    "qiskit_debugging":       ("qiskit_debugging_simulator.html",     580),
}


def render_simulator(lesson_id: str, base_dir: Path) -> bool:
    """
    Render the interactive HTML/SVG/JS simulator for a given lesson.

    `base_dir` should be the directory containing the simulator files,
    e.g. assets/lesson_media/interactive/

    Returns True if the simulator was rendered, False if the file
    was missing (in which case a warning is shown so the gap is visible
    to evaluators rather than silently skipped).
    """
    entry = SIMULATOR_FILES.get(lesson_id)
    if not entry:
        return False
    filename, height = entry
    path = base_dir / filename
    if not path.exists() or path.stat().st_size == 0:
        st.warning(f"Interactive simulator not found: {filename}")
        return False
    html = path.read_text(encoding="utf-8")
    st.components.v1.html(html, height=height, scrolling=False)
    return True

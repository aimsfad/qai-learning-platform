from __future__ import annotations

from pathlib import Path
import streamlit as st

SIMULATOR_FILES: dict[str, tuple[str, int]] = {
    "orientation": ("orientation_simulator.html", 840),
    "qubit_measurement": ("qubit_measurement_simulator.html", 840),
    "hadamard_superposition": ("hadamard_superposition_simulator.html", 840),
    "shots_counts": ("shots_counts_simulator.html", 840),
    "cnot_correlation": ("cnot_correlation_simulator.html", 840),
    "qiskit_debugging": ("qiskit_debugging_simulator.html", 840),
}

MICRO_ANIMATIONS: dict[str, str] = {
    "orientation": "module1_circuit_basics_micro_animation.mp4",
    "qubit_measurement": "module2_qubit_measurement_micro_animation.mp4",
    "hadamard_superposition": "module3_hadamard_superposition_micro_animation.mp4",
    "shots_counts": "module4_shots_counts_micro_animation.mp4",
    "cnot_correlation": "module5_cnot_correlation_micro_animation.mp4",
    "qiskit_debugging": "module6_debugging_micro_animation.mp4",
}

def render_video(path: Path, caption: str | None = None) -> bool:
    if path.exists() and path.stat().st_size > 0:
        if caption:
            st.caption(caption)
        try:
            st.video(path.read_bytes(), format="video/mp4")
        except Exception:
            st.video(str(path))
        return True
    st.warning(f"Video file not found or empty: {path.name}")
    return False

def render_image(path: Path, caption: str | None = None) -> bool:
    if path.exists() and path.stat().st_size > 0:
        st.image(str(path), use_container_width=True, caption=caption)
        return True
    return False

def render_simulator(lesson_id: str, base_dir: Path) -> bool:
    entry = SIMULATOR_FILES.get(lesson_id)
    if not entry:
        return False
    filename, height = entry
    path = base_dir / filename
    if not path.exists() or path.stat().st_size == 0:
        st.warning(f"Interactive simulator not found: {filename}")
        return False
    st.components.v1.html(path.read_text(encoding="utf-8"), height=height, scrolling=False)
    return True

def render_micro_animation(lesson_id: str, base_dir: Path) -> bool:
    filename = MICRO_ANIMATIONS.get(lesson_id)
    if not filename:
        return False
    return render_video(base_dir / filename, caption="Short concept animation")

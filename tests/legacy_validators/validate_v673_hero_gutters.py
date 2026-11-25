from pathlib import Path

ROOT = Path(__file__).resolve().parent
css = (ROOT / ".streamlit" / "v6_theme.css").read_text(encoding="utf-8")
db = (ROOT / "db.py").read_text(encoding="utf-8")

assert "V6.7.3 — Bidirectional hero text gutters" in css
assert "padding-inline-start: clamp(.95rem, 2.15vw, 1.9rem)" in css
assert "padding-inline: .7rem" in css
assert "v6.7.3-bidirectional-hero-gutters" in db
print("V6.7.3 bidirectional hero gutters validation passed.")

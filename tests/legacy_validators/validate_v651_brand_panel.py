from pathlib import Path

root = Path(__file__).resolve().parent
ui = (root / "ui_v6.py").read_text(encoding="utf-8")
css = (root / ".streamlit" / "v6_theme.css").read_text(encoding="utf-8")

checks = {
    "localized visual subtitle": "visual_subtitle" in ui,
    "prominent brand markup": "v61-visual-label" in ui and "3alimn<span>IA</span>" in ui,
    "large responsive wordmark": "font: 900 clamp(2.15rem" in css,
    "centered label": "transform: translateX(-50%)" in css,
    "mobile override": "@media (max-width: 620px)" in css,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("Validation failed: " + ", ".join(failed))
print("V6.5.1 prominent brand panel validation passed.")

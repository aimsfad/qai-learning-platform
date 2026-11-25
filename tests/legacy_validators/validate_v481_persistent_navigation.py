from pathlib import Path

root = Path(__file__).resolve().parent
css = (root / ".streamlit" / "v4_theme.css").read_text(encoding="utf-8")
i18n = (root / "i18n.py").read_text(encoding="utf-8")
main = (root / "main_app.py").read_text(encoding="utf-8")

assert '[data-testid="stSidebarCollapsedControl"]' in css
assert 'display: flex !important' in css
assert 'reopen_side' in i18n
assert '("Exports", "⇩")' in main
assert 'v481-navigation-note' in main
print("V4.8.1 persistent navigation validation passed.")

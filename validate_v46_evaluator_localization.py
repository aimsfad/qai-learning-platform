from pathlib import Path

root = Path(__file__).resolve().parent
main = (root / "main_app.py").read_text(encoding="utf-8")
css = (root / ".streamlit" / "v4_theme.css").read_text(encoding="utf-8")
required = [
    'hero(u["details_title"], u["details_sub"], localized=True)',
    'hero(u["exports_title"], u["exports_sub"], localized=True)',
    '"select_participant": "اختر مشاركًا"',
    '"pending": "قيد الانتظار"',
    '"participant_code": "رمز المشاركة"',
    'profile_display = i18n.localize_dataframe(profile, lang)',
]
missing = [item for item in required if item not in main]
css_required = ['.v4-page-hero[dir="rtl"]', '.v45-metric-grid[dir="rtl"]', '.v45-export-grid[dir="rtl"]']
missing_css = [item for item in css_required if item not in css]
if missing or missing_css:
    raise SystemExit(f"Missing main={missing}; css={missing_css}")
print("V4.6 evaluator localization checks passed.")

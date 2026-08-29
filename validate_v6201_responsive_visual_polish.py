from pathlib import Path

ROOT = Path(__file__).resolve().parent
css_path = ROOT / '.streamlit' / 'v6201_responsive_visual_system.css'
config = (ROOT / 'config.py').read_text(encoding='utf-8')
i18n = (ROOT / 'i18n.py').read_text(encoding='utf-8')
css = css_path.read_text(encoding='utf-8')

assert css_path.exists()
assert 'V6201_STYLE_PATH' in config
assert 'V6201_STYLE_PATH' in config
assert 'Noto Sans Arabic' in css
assert "'Noto Sans Arabic','Tajawal'" in i18n
assert '@media (max-width: 700px)' in css
assert '@media (max-width: 420px)' in css
assert '@media (min-width: 901px) and (max-width: 1180px)' in css
assert 'min-height: 48px' in css
assert 'font-size: 16px' in css
assert 'prefers-reduced-motion' in css
assert 'prefers-contrast: more' in css
assert '[data-testid="stDataFrame"]' in css
assert '.st-key-v61_public_header' in css
assert '.st-key-v68_workspace_toolbar' in css
assert '.v6162-step-node' in css

print('V6.20.1 responsive typography + device UI validation passed.')

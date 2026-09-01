"""Static safety checks for V6.20.18 Glass UI integration."""
from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parent
css=(ROOT/'.streamlit/app.css').read_text(encoding='utf-8')
config=(ROOT/'.streamlit/config.toml').read_text(encoding='utf-8')
db=(ROOT/'db.py').read_text(encoding='utf-8')
for name in ('app.py','main_app.py','ui_v6.py','branding.py','db.py','teacher_studio.py'):
    ast.parse((ROOT/name).read_text(encoding='utf-8'))
assert 'APP_VERSION = "v6.20.18-glass-ui-integration"' in db
assert 'V14.0 PURE GLASS PREMIUM REDESIGN' in css
assert '--glass-surface:' in css and '--brand-gradient:' in css
assert 'Safe glass surfaces' in css
assert 'Universal glass-surface safety net' not in css
assert '@media (max-width:760px)' in css
assert '@supports not ((backdrop-filter:blur(1px))' in css
# All external font imports must remain in the initial stylesheet header, not the appended V14 section.
v14=css.split('V14.0 PURE GLASS PREMIUM REDESIGN',1)[1]
assert '@import url(' not in v14
assert 'primaryColor = "#1F3DFF"' in config
assert 'buttonRadius = "999px"' in config
# Sanitization contract.
assert not (ROOT/'.streamlit/secrets.toml').exists()
assert not (ROOT/'.git').exists()
print('V6.20.18 Glass UI integration PASS')

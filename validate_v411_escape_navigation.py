from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent
main = (ROOT / 'main_app.py').read_text(encoding='utf-8')
css = (ROOT / '.streamlit' / 'v4_theme.css').read_text(encoding='utf-8')

ast.parse(main)
required_main = [
    'def render_global_escape_navigation()',
    'def _v411_change_account()',
    'def _v411_exit_platform()',
    'def _v411_go_back()',
    'render_global_escape_navigation()',
    '"Exports"',
    '"Sign in"',
]
for item in required_main:
    assert item in main, f'Missing main_app feature: {item}'

required_css = [
    '.v411-global-nav-marker',
    ':has(.v411-global-nav-marker)',
    'position: sticky',
]
for item in required_css:
    assert item in css, f'Missing V4.11 style: {item}'

assert 'initial_sidebar_state="expanded"' in (ROOT / 'app.py').read_text(encoding='utf-8')
print('V4.11 escape navigation validation passed.')

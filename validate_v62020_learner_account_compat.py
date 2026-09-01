from pathlib import Path
import ast

root = Path(__file__).resolve().parent
patcher = (root / 'apply_v62020_patch.py').read_text(encoding='utf-8')
ast.parse(patcher, filename='apply_v62020_patch.py')
required = [
    'v6.20.20-learner-account-compat-ui-density',
    'normalize_student_identifier',
    'student_auth_diagnostic',
    'password_policy_error(new_password)',
    'V6.20.20 COMPACT DENSITY LAYER',
    'validate_v62020_learner_account_compat.py',
]
missing = [item for item in required if item not in patcher]
if missing:
    raise SystemExit('Patch-package validation failed: ' + ', '.join(missing))
print('Patch package self-check: PASS')

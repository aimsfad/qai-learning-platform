from pathlib import Path
import ast
import tempfile
import os

ROOT=Path(__file__).resolve().parent
required=[
    'production_pipeline.py','production_worker.py','teacher_studio.py','db.py','requirements.txt'
]
for name in required:
    assert (ROOT/name).exists(), f'missing {name}'
for name in ['production_pipeline.py','production_worker.py','teacher_studio.py','db.py']:
    ast.parse((ROOT/name).read_text(encoding='utf-8'))

db=(ROOT/'db.py').read_text(encoding='utf-8')
pipe=(ROOT/'production_pipeline.py').read_text(encoding='utf-8')
ui=(ROOT/'teacher_studio.py').read_text(encoding='utf-8')
req=(ROOT/'requirements.txt').read_text(encoding='utf-8')
assert 'teacher_production_jobs' in db
assert 'create_teacher_production_job' in db
assert 'PHASE_DEPENDENCIES' in pipe
assert 'PARALLEL_PHASES = [4, 5, 6, 7, 8, 9]' in pipe
assert 'enqueue_parallel_batch' in pipe
assert 'production_pipeline.enqueue_parallel_batch' in ui
assert 'redis>=5.0' in req and 'rq>=2.0' in req
assert 'APP_VERSION = "v6.17-hybrid-background-production"' in db
print('V6.17 hybrid background production validation passed.')

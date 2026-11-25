3alimnIA V0.4 EXPERIMENTAL - RAG-ONLY SOURCE DOSSIER

This patch is for the existing GitHub feature branch:
    feat/neon-rag-storage-v03
It is NOT for main or production.

1. Extract the ZIP to a separate folder, e.g.
   C:\Users\djenb\Downloads\3alimnia_RAG_ONLY_V04_PATCH
2. Open CMD in the qai_platform_ repository directory.
3. Confirm branch:
   git branch --show-current
4. Dry run (replace path if needed):
   py "%USERPROFILE%\Downloads\3alimnia_RAG_ONLY_V04_PATCH\apply_rag_only_v04.py" --dry-run
5. Apply:
   py "%USERPROFILE%\Downloads\3alimnia_RAG_ONLY_V04_PATCH\apply_rag_only_v04.py" --apply
6. Run tests:
   py -m unittest discover -s tests -p test_rag_course_sources.py -v
   py -m unittest tests.test_hybrid_rag_v01 tests.test_online_hybrid_rag_v02 tests.test_neon_rag_v03 -v
7. Compile:
   py -m compileall -q rag_course_sources.py teacher_studio.py guided_teacher_workflow.py evidence_synthesis_engine.py
8. Stage EXACTLY these five files and commit on the feature branch:
   git add rag_course_sources.py teacher_studio.py guided_teacher_workflow.py evidence_synthesis_engine.py tests/test_rag_course_sources.py
   git commit -m "feat: add teacher-approved RAG-only source dossier"
   git push origin feat/neon-rag-storage-v03

The staging Streamlit app should auto-update after the push. Never merge to main.

In the staging teacher app:
- Open project > Sources.
- Keep the already-indexed, teacher-approved reference; ensure cloud-generation permission is granted.
- Under Sources and Research, click the new RAG-only button.
- Search for 'ML-CAR-200' (short query works with lexical search).
- Review the locally generated source dossier and approve it.
- Continue to evidence synthesis and review before approving. The local dossier is NOT web validation.

Important limitations:
- This is a staging prototype and does not claim scientific source verification.
- LLM generation still requires a functional provider such as Groq.
- Your uploaded RAG evidence is subject to teacher cloud-generation consent.
- Do not use sensitive or production learner records for this test.
- After any source revocation, previously generated content should be manually re-reviewed; a complete provenance revocation pipeline is future work.

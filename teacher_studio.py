"""Teacher Content Studio for designing and generating educational units."""

from __future__ import annotations

import io
import json
from html import escape
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

import content_generation_engine
import db
import i18n
import router
from security import verify_password


ROOT_DIR = Path(__file__).resolve().parent
MASTER_PROMPT_PATH = ROOT_DIR / "prompts" / "educational_content_production_master.md"

PHASES = {
    1: "Evidence and concept audit",
    2: "Learning design blueprint",
    3: "Core educational content",
    4: "Visual asset production plan",
    5: "Video script and storyboard",
    6: "Interactive and practical activity",
    7: "AI Coach design",
    8: "Assessment package",
    9: "Multilingual localization",
    10: "Technical export package",
    11: "Quality assurance",
}

LANGUAGE_NAMES = {"ar": "Arabic", "fr": "French", "en": "English"}


def _secret(name: str, default: str = "") -> str:
    try:
        return str(st.secrets.get(name, default))
    except Exception:
        return default


def teacher_password_is_valid(username: str, password: str) -> bool:
    expected = _secret("TEACHER_USERNAME", "teacher")
    if username.strip() != expected:
        return False
    stored_hash = _secret("TEACHER_PASSWORD_HASH", "").strip()
    if stored_hash:
        return verify_password(password, stored_hash)
    return password == _secret("TEACHER_PASSWORD", "teacher123")


def init_teacher_state() -> None:
    st.session_state.setdefault("teacher_logged_in", False)
    st.session_state.setdefault("teacher_page", "Content Studio")
    st.session_state.setdefault("teacher_active_project_id", None)
    st.session_state.setdefault("teacher_last_prompt", "")
    st.session_state.setdefault("teacher_last_response", "")


def teacher_ui() -> Dict[str, str]:
    lang = i18n.current_lang(st)
    values = {
        "ar": {
            "workspace": "فضاء الأستاذ",
            "subtitle": "أنشئ مشروعًا تعليميًا، اضبط طريقة التدريس والتقييم، ثم ولّد المواد على مراحل قابلة للمراجعة.",
            "login": "دخول الأستاذ",
            "username": "اسم المستخدم",
            "password": "كلمة المرور",
            "sign_in": "دخول",
            "invalid": "بيانات الدخول غير صحيحة.",
            "unsafe": "كلمة مرور الأستاذ الافتراضية ما تزال مفعلة. غيّرها في أسرار Streamlit قبل النشر.",
            "new_project": "مشروع تعليمي جديد",
            "projects": "مشاريعي",
            "outputs": "المخرجات المولدة",
            "project_name": "اسم المشروع",
            "domain": "المجال أو المادة",
            "program": "اسم المقياس أو البرنامج",
            "unit": "عنوان الوحدة",
            "concept": "المفهوم المراد تدريسه",
            "learners": "الفئة المستهدفة",
            "level": "مستوى المتعلمين",
            "prerequisites": "المكتسبات القبلية",
            "languages": "لغات الإنتاج",
            "primary_language": "لغة الإنتاج الأولى",
            "duration": "المدة المتوقعة",
            "environment": "البيئة التقنية أو الأدوات",
            "components": "مكونات المنصة المطلوبة",
            "source": "محتوى المادة والمراجع المتاحة",
            "files": "رفع مراجع أو محتوى (PDF, DOCX, TXT, MD, CSV, JSON)",
            "teaching": "الطريقة التي يفضلها الأستاذ للتدريس",
            "assessment": "طريقة التقييم المفضلة",
            "notes": "ملاحظات إضافية",
            "requested": "المخرجات المطلوبة",
            "phase": "مرحلة الإنتاج الحالية",
            "save": "حفظ المشروع وتجهيز البرومبت",
            "generate": "توليد هذه المرحلة بالذكاء الاصطناعي",
            "prompt": "البرومبت المركب",
            "download_prompt": "تنزيل البرومبت",
            "download_project": "تنزيل بيانات المشروع",
            "saved": "تم حفظ المشروع وتجهيز البرومبت.",
            "generated": "تم توليد مخرجات المرحلة وحفظها.",
            "required": "املأ اسم المشروع والمادة والوحدة والمفهوم والفئة المستهدفة على الأقل.",
            "select_project": "اختر مشروعًا محفوظًا",
            "no_projects": "لا توجد مشاريع محفوظة بعد.",
            "provider": "حالة محرك التوليد",
            "phase_only": "ينفذ النظام المرحلة المختارة فقط ولا ينتقل تلقائيًا إلى المرحلة التالية.",
        },
        "fr": {
            "workspace": "Espace enseignant",
            "subtitle": "Définissez le contenu, la pédagogie et l’évaluation, puis générez les ressources par phases révisables.",
            "login": "Connexion enseignant", "username": "Nom d’utilisateur", "password": "Mot de passe", "sign_in": "Se connecter",
            "invalid": "Identifiants incorrects.", "unsafe": "Le mot de passe enseignant par défaut est actif. Modifiez-le dans les secrets Streamlit.",
            "new_project": "Nouveau projet pédagogique", "projects": "Mes projets", "outputs": "Productions générées",
            "project_name": "Nom du projet", "domain": "Discipline", "program": "Programme ou module", "unit": "Titre de l’unité",
            "concept": "Concept cible", "learners": "Public cible", "level": "Niveau", "prerequisites": "Prérequis",
            "languages": "Langues de production", "primary_language": "Langue principale", "duration": "Durée prévue",
            "environment": "Environnement technique", "components": "Composants de plateforme", "source": "Contenu et références disponibles",
            "files": "Importer des références ou contenus (PDF, DOCX, TXT, MD, CSV, JSON)",
            "teaching": "Préférences pédagogiques", "assessment": "Modalités d’évaluation", "notes": "Notes complémentaires",
            "requested": "Livrables demandés", "phase": "Phase actuelle", "save": "Enregistrer et compiler le prompt",
            "generate": "Générer cette phase avec l’IA", "prompt": "Prompt compilé", "download_prompt": "Télécharger le prompt",
            "download_project": "Télécharger le projet", "saved": "Projet enregistré et prompt compilé.",
            "generated": "La production a été générée et enregistrée.", "required": "Renseignez au minimum le projet, la discipline, l’unité, le concept et le public.",
            "select_project": "Choisir un projet enregistré", "no_projects": "Aucun projet enregistré.",
            "provider": "État du moteur de génération", "phase_only": "Le système exécute uniquement la phase sélectionnée.",
        },
        "en": {
            "workspace": "Teacher workspace",
            "subtitle": "Define the subject, teaching approach, and assessment, then generate reviewable educational assets phase by phase.",
            "login": "Teacher sign in", "username": "Username", "password": "Password", "sign_in": "Sign in",
            "invalid": "Invalid credentials.", "unsafe": "The default teacher password is active. Change it in Streamlit secrets.",
            "new_project": "New educational project", "projects": "My projects", "outputs": "Generated outputs",
            "project_name": "Project name", "domain": "Subject or domain", "program": "Program or course", "unit": "Unit title",
            "concept": "Target concept", "learners": "Target learners", "level": "Learner level", "prerequisites": "Prerequisites",
            "languages": "Production languages", "primary_language": "Primary production language", "duration": "Expected duration",
            "environment": "Technical environment", "components": "Platform components", "source": "Available content and references",
            "files": "Upload references or content (PDF, DOCX, TXT, MD, CSV, JSON)",
            "teaching": "Preferred teaching approach", "assessment": "Preferred assessment approach", "notes": "Additional notes",
            "requested": "Requested outputs", "phase": "Current production phase", "save": "Save project and compile prompt",
            "generate": "Generate this phase with AI", "prompt": "Compiled prompt", "download_prompt": "Download prompt",
            "download_project": "Download project data", "saved": "Project saved and prompt compiled.",
            "generated": "The phase output was generated and saved.", "required": "Complete at least project, subject, unit, concept, and target learners.",
            "select_project": "Select a saved project", "no_projects": "No saved projects yet.",
            "provider": "Generation engine status", "phase_only": "The engine executes only the selected phase.",
        },
    }
    return values.get(lang, values["en"])


def render_teacher_login() -> None:
    u = teacher_ui()
    st.markdown(f"## {u['login']}")
    st.caption(u["subtitle"])
    if _secret("TEACHER_PASSWORD", "teacher123") == "teacher123" and not _secret("TEACHER_PASSWORD_HASH", ""):
        st.warning(u["unsafe"])
    with st.form("teacher_login_form"):
        username = st.text_input(u["username"], value=_secret("TEACHER_USERNAME", "teacher"))
        password = st.text_input(u["password"], type="password")
        submitted = st.form_submit_button(u["sign_in"], type="primary", use_container_width=True)
    if submitted:
        if teacher_password_is_valid(username, password):
            st.session_state.teacher_logged_in = True
            st.session_state.teacher_username = username.strip()
            db.log_event(None, "teacher", "sign_in", f"Teacher username: {username.strip()}")
            router.queue(router.route_key("teacher", "Content Studio"))
            st.rerun()
        st.error(u["invalid"])


def _teacher_brief(data: Dict[str, Any]) -> str:
    labels = {
        "project_name": "Project name", "domain": "Educational domain", "program_name": "Program/course",
        "unit_title": "Unit title", "target_concept": "Target concept", "target_learners": "Target learners",
        "learner_level": "Learner level", "prerequisites": "Prerequisites", "target_languages": "Target languages",
        "primary_language": "Primary production language", "expected_duration": "Expected duration",
        "technical_environment": "Technical environment", "platform_components": "Platform components",
        "source_material": "Available subject content and references", "teaching_preferences": "Teacher's preferred teaching approach",
        "assessment_preferences": "Teacher's preferred assessment approach", "additional_notes": "Additional notes",
        "requested_outputs": "Requested outputs",
    }
    lines: List[str] = []
    for key, label in labels.items():
        value = data.get(key, "")
        if isinstance(value, list):
            value = ", ".join(value)
        lines.append(f"- {label}: {value or '[Not specified]'}")
    return "\n".join(lines)


def compile_project_prompt(data: Dict[str, Any], phase_number: int) -> str:
    template = MASTER_PROMPT_PATH.read_text(encoding="utf-8")
    output_language = LANGUAGE_NAMES.get(str(data.get("primary_language_code") or "en"), str(data.get("primary_language") or "English"))
    return (
        template.replace("{{TEACHER_PROJECT_BRIEF}}", _teacher_brief(data))
        .replace("{{PHASE_NUMBER}}", str(phase_number))
        .replace("{{PHASE_NAME}}", PHASES[int(phase_number)])
        .replace("{{OUTPUT_LANGUAGE}}", output_language)
    )


def _project_defaults(project: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    p = dict(project or {})
    def parse_list(value: Any, default: List[str]) -> List[str]:
        if isinstance(value, list):
            return value
        if isinstance(value, str) and value.strip():
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else default
            except Exception:
                return [item.strip() for item in value.split(",") if item.strip()]
        return default
    p["target_languages"] = parse_list(p.get("target_languages_json"), ["Arabic", "French", "English"])
    p["platform_components"] = parse_list(p.get("platform_components_json"), ["AI Coach", "Assessment", "Learning analytics"])
    p["requested_outputs"] = parse_list(p.get("requested_outputs_json"), ["Interactive lesson", "Illustrations", "Video", "Assessment bank", "AI Coach prompts"])
    return p


def _load_selected_project(username: str, u: Dict[str, str]) -> Optional[Dict[str, Any]]:
    projects = db.teacher_projects_df(username)
    if projects.empty:
        st.info(u["no_projects"])
        return None
    options = {f"#{int(row['id'])} — {row['project_name']} / {row['unit_title']}": int(row["id"]) for _, row in projects.iterrows()}
    selected_label = st.selectbox(u["select_project"], list(options.keys()), key="teacher_project_selector")
    selected_id = options[selected_label]
    st.session_state.teacher_active_project_id = selected_id
    return db.get_teacher_project(selected_id, username)


def extract_uploaded_sources(uploaded_files: Any) -> str:
    """Extract a bounded amount of teacher-supplied source text."""
    if not uploaded_files:
        return ""
    chunks: List[str] = []
    total_chars = 0
    max_total = 80000
    for uploaded in list(uploaded_files)[:6]:
        name = str(getattr(uploaded, "name", "source")).strip()
        suffix = Path(name).suffix.lower()
        try:
            raw = uploaded.getvalue()
            if len(raw) > 10 * 1024 * 1024:
                chunks.append(f"\n[Skipped {name}: file exceeds 10 MB]\n")
                continue
            if suffix in {".txt", ".md", ".csv", ".json"}:
                text_value = raw.decode("utf-8", errors="replace")
            elif suffix == ".pdf":
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(raw))
                text_value = "\n".join((page.extract_text() or "") for page in reader.pages[:80])
            elif suffix == ".docx":
                from docx import Document
                document = Document(io.BytesIO(raw))
                text_value = "\n".join(paragraph.text for paragraph in document.paragraphs)
            else:
                chunks.append(f"\n[Unsupported file type: {name}]\n")
                continue
            text_value = text_value.strip()[:30000]
            available = max_total - total_chars
            if available <= 0:
                break
            text_value = text_value[:available]
            chunks.append(f"\n\n--- Uploaded source: {name} ---\n{text_value}")
            total_chars += len(text_value)
        except Exception as exc:
            chunks.append(f"\n[Could not extract {name}: {exc}]\n")
    return "".join(chunks).strip()

def render_project_form(existing: Optional[Dict[str, Any]] = None) -> None:
    u = teacher_ui()
    username = st.session_state.get("teacher_username", _secret("TEACHER_USERNAME", "teacher"))
    p = _project_defaults(existing)
    lang_code = i18n.current_lang(st)

    with st.form("teacher_content_project_form"):
        c1, c2 = st.columns(2, gap="large")
        with c1:
            project_name = st.text_input(u["project_name"], value=str(p.get("project_name") or ""))
            domain = st.text_input(u["domain"], value=str(p.get("domain") or ""))
            program_name = st.text_input(u["program"], value=str(p.get("program_name") or ""))
            unit_title = st.text_input(u["unit"], value=str(p.get("unit_title") or ""))
            target_concept = st.text_area(u["concept"], value=str(p.get("target_concept") or ""), height=100)
            target_learners = st.text_area(u["learners"], value=str(p.get("target_learners") or ""), height=80)
            learner_level = st.selectbox(u["level"], ["Beginner", "Intermediate", "Advanced", "Mixed"], index=max(0, ["Beginner", "Intermediate", "Advanced", "Mixed"].index(str(p.get("learner_level") or "Beginner")) if str(p.get("learner_level") or "Beginner") in ["Beginner", "Intermediate", "Advanced", "Mixed"] else 0))
            prerequisites = st.text_area(u["prerequisites"], value=str(p.get("prerequisites") or ""), height=100)
        with c2:
            language_options = ["Arabic", "French", "English"]
            target_languages = st.multiselect(u["languages"], language_options, default=[v for v in p["target_languages"] if v in language_options] or language_options)
            primary_language = st.selectbox(u["primary_language"], language_options, index=language_options.index(str(p.get("primary_language") or LANGUAGE_NAMES.get(lang_code, "English"))) if str(p.get("primary_language") or LANGUAGE_NAMES.get(lang_code, "English")) in language_options else 0)
            expected_duration = st.text_input(u["duration"], value=str(p.get("expected_duration") or "25 minutes"))
            technical_environment = st.text_input(u["environment"], value=str(p.get("technical_environment") or "Streamlit"))
            component_options = ["AI Coach", "Concept Builder", "Interactive activity", "Qiskit practice", "Assessment", "LPQS", "Learning analytics", "Research export"]
            platform_components = st.multiselect(u["components"], component_options, default=[v for v in p["platform_components"] if v in component_options])
            output_options = ["Interactive lesson", "Illustrations", "Infographics", "Video", "Animation", "Practical activity", "Code", "Assessment bank", "AI Coach prompts", "Multilingual package", "Streamlit integration package"]
            requested_outputs = st.multiselect(u["requested"], output_options, default=[v for v in p["requested_outputs"] if v in output_options])
            phase_number = st.selectbox(u["phase"], list(PHASES.keys()), format_func=lambda n: f"{n}. {PHASES[n]}", index=max(0, int(p.get("current_phase") or 1) - 1))

        source_material = st.text_area(u["source"], value=str(p.get("source_material") or ""), height=180)
        uploaded_sources = st.file_uploader(
            u["files"], type=["pdf", "docx", "txt", "md", "csv", "json"], accept_multiple_files=True,
            key="teacher_source_uploads",
        )
        c3, c4 = st.columns(2, gap="large")
        with c3:
            teaching_preferences = st.text_area(u["teaching"], value=str(p.get("teaching_preferences") or ""), height=150)
        with c4:
            assessment_preferences = st.text_area(u["assessment"], value=str(p.get("assessment_preferences") or ""), height=150)
        additional_notes = st.text_area(u["notes"], value=str(p.get("additional_notes") or ""), height=100)
        submitted = st.form_submit_button(u["save"], type="primary", use_container_width=True)

    if not submitted:
        return
    if not all([project_name.strip(), domain.strip(), unit_title.strip(), target_concept.strip(), target_learners.strip()]):
        st.error(u["required"])
        return
    extracted_sources = extract_uploaded_sources(uploaded_sources)
    combined_sources = source_material.strip()
    if extracted_sources:
        combined_sources = (combined_sources + "\n\n" + extracted_sources).strip()
    primary_code = {"Arabic": "ar", "French": "fr", "English": "en"}[primary_language]
    data = {
        "id": p.get("id"), "teacher_username": username, "project_name": project_name.strip(), "domain": domain.strip(),
        "program_name": program_name.strip(), "unit_title": unit_title.strip(), "target_concept": target_concept.strip(),
        "target_learners": target_learners.strip(), "learner_level": learner_level, "prerequisites": prerequisites.strip(),
        "target_languages": target_languages, "primary_language": primary_language, "primary_language_code": primary_code,
        "expected_duration": expected_duration.strip(), "technical_environment": technical_environment.strip(),
        "platform_components": platform_components, "source_material": combined_sources,
        "teaching_preferences": teaching_preferences.strip(), "assessment_preferences": assessment_preferences.strip(),
        "additional_notes": additional_notes.strip(), "requested_outputs": requested_outputs, "current_phase": int(phase_number),
    }
    project_id = db.save_teacher_project(data)
    data["id"] = project_id
    prompt = compile_project_prompt(data, int(phase_number))
    st.session_state.teacher_active_project_id = project_id
    st.session_state.teacher_last_prompt = prompt
    st.success(u["saved"])
    st.rerun()


def render_prompt_and_generation(project: Dict[str, Any]) -> None:
    u = teacher_ui()
    p = _project_defaults(project)
    phase_number = int(p.get("current_phase") or 1)
    prompt = compile_project_prompt(p, phase_number)
    st.session_state.teacher_last_prompt = prompt
    status = content_generation_engine.provider_status()
    st.info(f"{u['provider']}: {status['provider']} / {status['model']} — {'ready' if status['available'] else 'prompt export only'}")
    st.caption(u["phase_only"])
    with st.expander(u["prompt"], expanded=False):
        st.code(prompt, language="markdown")
    safe_name = "_".join(str(p.get("project_name") or "project").split())
    st.download_button(u["download_prompt"], prompt.encode("utf-8"), file_name=f"{safe_name}_phase_{phase_number}_prompt.md", mime="text/markdown", use_container_width=True)
    project_json = json.dumps(p, ensure_ascii=False, indent=2, default=str)
    st.download_button(u["download_project"], project_json.encode("utf-8"), file_name=f"{safe_name}_project.json", mime="application/json", use_container_width=True)
    if st.button(u["generate"], type="primary", use_container_width=True, key=f"generate_teacher_phase_{p['id']}_{phase_number}"):
        with st.spinner("3alimnIA is generating the selected phase..."):
            result = content_generation_engine.generate_content(prompt, str(p.get("primary_language") or "English"))
            db.save_teacher_generation(
                project_id=int(p["id"]), phase_number=phase_number, prompt_text=prompt, response_text=result.response,
                provider=result.provider, model=result.model, status=result.status, diagnostic=result.diagnostic,
            )
            st.session_state.teacher_last_response = result.response
        if result.status == "completed":
            st.success(u["generated"])
        elif result.status == "not_configured":
            st.warning(result.diagnostic)
        else:
            st.error(result.diagnostic or result.response)
        st.rerun()


def render_outputs(project: Optional[Dict[str, Any]]) -> None:
    u = teacher_ui()
    if not project:
        st.info(u["no_projects"])
        return
    runs = db.teacher_generation_runs_df(int(project["id"]))
    if runs.empty:
        st.info(u["no_projects"])
        return
    for _, row in runs.iterrows():
        phase = int(row["phase_number"])
        title = f"Phase {phase} — {PHASES.get(phase, '')} | {row.get('provider', '')} / {row.get('model', '')}"
        with st.expander(title, expanded=False):
            if row.get("diagnostic"):
                st.caption(str(row["diagnostic"]))
            st.markdown(str(row.get("response_text") or ""))
            filename = f"project_{int(project['id'])}_phase_{phase}_output.md"
            st.download_button("Download output", str(row.get("response_text") or "").encode("utf-8"), file_name=filename, mime="text/markdown", key=f"download_teacher_run_{int(row['id'])}")


def render_teacher_app() -> None:
    init_teacher_state()
    if not st.session_state.teacher_logged_in:
        render_teacher_login()
        return
    u = teacher_ui()
    st.markdown(f"# {u['workspace']}")
    st.caption(u["subtitle"])
    view = st.radio(
        "Teacher studio view",
        [u["new_project"], u["projects"], u["outputs"]],
        horizontal=True,
        label_visibility="collapsed",
        key="teacher_studio_view",
    )
    if view == u["new_project"]:
        render_project_form(None)
        active_id = st.session_state.get("teacher_active_project_id")
        if active_id:
            project = db.get_teacher_project(int(active_id), st.session_state.get("teacher_username", _secret("TEACHER_USERNAME", "teacher")))
            if project:
                st.divider()
                render_prompt_and_generation(project)
    elif view == u["projects"]:
        selected = _load_selected_project(st.session_state.get("teacher_username", _secret("TEACHER_USERNAME", "teacher")), u)
        if selected:
            render_project_form(selected)
            st.divider()
            render_prompt_and_generation(selected)
    else:
        selected = _load_selected_project(st.session_state.get("teacher_username", _secret("TEACHER_USERNAME", "teacher")), u)
        render_outputs(selected)

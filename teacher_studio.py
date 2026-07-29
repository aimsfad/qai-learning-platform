"""Teacher Content Studio for designing and generating educational units."""

from __future__ import annotations

import io
import json
import re
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


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def teacher_registration_enabled() -> bool:
    return _as_bool(_secret("TEACHER_ALLOW_REGISTRATION", "true"), True)


def teacher_registration_code() -> str:
    return _secret("TEACHER_REGISTRATION_CODE", "").strip()


def legacy_teacher_password_is_valid(username: str, password: str) -> bool:
    """Optional compatibility login configured explicitly through secrets.

    No implicit default password is accepted. Database-backed teacher accounts
    are the normal authentication path from V6.9.1 onward.
    """
    expected = _secret("TEACHER_USERNAME", "").strip()
    stored_hash = _secret("TEACHER_PASSWORD_HASH", "").strip()
    stored_password = _secret("TEACHER_PASSWORD", "").strip()
    if not expected or username.strip() != expected:
        return False
    if stored_hash:
        return verify_password(password, stored_hash)
    return bool(stored_password) and password == stored_password


def authenticate_teacher_credentials(identifier: str, password: str) -> Optional[Dict[str, Any]]:
    account = db.authenticate_teacher(identifier, password)
    if account:
        return account
    if legacy_teacher_password_is_valid(identifier, password):
        return {
            "id": None,
            "username": identifier.strip(),
            "email": "",
            "full_name": identifier.strip(),
            "preferred_language": i18n.current_lang(st),
            "legacy_secret_account": True,
        }
    return None


def _valid_teacher_username(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9._-]{3,40}", str(value or "").strip()))


def _valid_email(value: str) -> bool:
    return bool(re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", str(value or "").strip()))


def _valid_password(value: str) -> bool:
    password = str(value or "")
    return len(password) >= 8 and any(ch.isalpha() for ch in password) and any(ch.isdigit() for ch in password)


def init_teacher_state() -> None:
    st.session_state.setdefault("teacher_logged_in", False)
    st.session_state.setdefault("teacher_account_id", None)
    st.session_state.setdefault("teacher_username", None)
    st.session_state.setdefault("teacher_display_name", None)
    st.session_state.setdefault("teacher_page", "Content Studio")
    st.session_state.setdefault("teacher_studio_view", "projects")
    st.session_state.setdefault("teacher_active_project_id", None)
    st.session_state.setdefault("teacher_workspace_section", "overview")
    st.session_state.setdefault("teacher_last_prompt", "")
    st.session_state.setdefault("teacher_last_response", "")


def teacher_ui() -> Dict[str, str]:
    lang = i18n.current_lang(st)
    values = {
        "ar": {
            "workspace": "فضاء الأستاذ",
            "subtitle": "أنشئ مشروعًا تعليميًا، اضبط طريقة التدريس والتقييم، ثم ولّد المواد على مراحل قابلة للمراجعة.",
            "login": "حساب الأستاذ",
            "login_tab": "تسجيل الدخول",
            "register_tab": "إنشاء حساب",
            "identifier": "اسم المستخدم أو البريد الإلكتروني",
            "username": "اسم المستخدم",
            "full_name": "الاسم الكامل",
            "email": "البريد الإلكتروني",
            "institution": "المؤسسة أو الجامعة",
            "specialization": "التخصص",
            "password": "كلمة المرور",
            "confirm_password": "تأكيد كلمة المرور",
            "sign_in": "دخول",
            "create_account": "إنشاء حساب الأستاذ",
            "registration_code": "رمز إنشاء حساب الأستاذ",
            "invalid": "بيانات الدخول غير صحيحة.",
            "registration_disabled": "إنشاء حسابات الأساتذة غير مفعّل حاليًا.",
            "username_help": "من 3 إلى 40 حرفًا لاتينيًا أو رقمًا، ويمكن استعمال . _ -",
            "password_help": "8 محارف على الأقل، وتحتوي على حرف ورقم.",
            "password_mismatch": "كلمتا المرور غير متطابقتين.",
            "invalid_username": "اسم المستخدم غير صالح.",
            "invalid_email": "أدخل بريدًا إلكترونيًا صالحًا.",
            "weak_password": "كلمة المرور ضعيفة؛ استخدم 8 محارف على الأقل مع حرف ورقم.",
            "invalid_registration_code": "رمز إنشاء الحساب غير صحيح.",
            "account_created": "تم إنشاء حساب الأستاذ وتسجيل الدخول بنجاح.",
            "accept_policy": "أوافق على استعمال معلومات الحساب لإدارة مشاريعي التعليمية داخل المنصة.",
            "accept_required": "يجب الموافقة قبل إنشاء الحساب.",
            "legacy_info": "يمكن أيضًا استعمال حساب إداري قديم إذا تم ضبطه صراحةً في أسرار Streamlit.",
            "welcome": "مرحبًا",
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
            "prompt_ready": "تم تجهيز البرومبت من النسخة المحفوظة للمشروع، ويمكن الآن معاينته أو تنزيله أو تشغيل المرحلة.",
            "rebuild_prompt": "إعادة تجهيز البرومبت",
            "save_error": "تعذر حفظ المشروع أو تجهيز البرومبت.",
            "saving": "جارٍ حفظ المشروع وتجهيز البرومبت...",
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
            "login": "Compte enseignant", "login_tab": "Connexion", "register_tab": "Créer un compte",
            "identifier": "Nom d’utilisateur ou e-mail", "username": "Nom d’utilisateur", "full_name": "Nom complet",
            "email": "Adresse e-mail", "institution": "Établissement ou université", "specialization": "Spécialité",
            "password": "Mot de passe", "confirm_password": "Confirmer le mot de passe", "sign_in": "Se connecter",
            "create_account": "Créer le compte enseignant", "registration_code": "Code de création de compte",
            "invalid": "Identifiants incorrects.", "registration_disabled": "La création de comptes enseignants est désactivée.",
            "username_help": "3 à 40 caractères latins ou chiffres; . _ - sont acceptés.",
            "password_help": "8 caractères minimum avec au moins une lettre et un chiffre.",
            "password_mismatch": "Les mots de passe ne correspondent pas.", "invalid_username": "Nom d’utilisateur invalide.",
            "invalid_email": "Saisissez une adresse e-mail valide.", "weak_password": "Mot de passe trop faible.",
            "invalid_registration_code": "Code de création de compte incorrect.",
            "account_created": "Compte enseignant créé et connexion réussie.",
            "accept_policy": "J’accepte l’utilisation des informations du compte pour gérer mes projets pédagogiques.",
            "accept_required": "Vous devez accepter avant de créer le compte.",
            "legacy_info": "Un ancien compte administrateur reste utilisable s’il est explicitement configuré dans les secrets Streamlit.",
            "welcome": "Bienvenue",
            "new_project": "Nouveau projet pédagogique", "projects": "Mes projets", "outputs": "Productions générées",
            "project_name": "Nom du projet", "domain": "Discipline", "program": "Programme ou module", "unit": "Titre de l’unité",
            "concept": "Concept cible", "learners": "Public cible", "level": "Niveau", "prerequisites": "Prérequis",
            "languages": "Langues de production", "primary_language": "Langue principale", "duration": "Durée prévue",
            "environment": "Environnement technique", "components": "Composants de plateforme", "source": "Contenu et références disponibles",
            "files": "Importer des références ou contenus (PDF, DOCX, TXT, MD, CSV, JSON)",
            "teaching": "Préférences pédagogiques", "assessment": "Modalités d’évaluation", "notes": "Notes complémentaires",
            "requested": "Livrables demandés", "phase": "Phase actuelle", "save": "Enregistrer et compiler le prompt",
            "generate": "Générer cette phase avec l’IA", "prompt": "Prompt compilé",
            "prompt_ready": "Le prompt a été recompilé à partir de la version enregistrée du projet. Vous pouvez le prévisualiser, le télécharger ou lancer la phase.",
            "rebuild_prompt": "Recompiler le prompt",
            "save_error": "Impossible d’enregistrer le projet ou de compiler le prompt.",
            "saving": "Enregistrement du projet et compilation du prompt...", "download_prompt": "Télécharger le prompt",
            "download_project": "Télécharger le projet", "saved": "Projet enregistré et prompt compilé.",
            "generated": "La production a été générée et enregistrée.", "required": "Renseignez au minimum le projet, la discipline, l’unité, le concept et le public.",
            "select_project": "Choisir un projet enregistré", "no_projects": "Aucun projet enregistré.",
            "provider": "État du moteur de génération", "phase_only": "Le système exécute uniquement la phase sélectionnée.",
        },
        "en": {
            "workspace": "Teacher workspace",
            "subtitle": "Define the subject, teaching approach, and assessment, then generate reviewable educational assets phase by phase.",
            "login": "Teacher account", "login_tab": "Sign in", "register_tab": "Create account",
            "identifier": "Username or email", "username": "Username", "full_name": "Full name",
            "email": "Email address", "institution": "Institution or university", "specialization": "Specialization",
            "password": "Password", "confirm_password": "Confirm password", "sign_in": "Sign in",
            "create_account": "Create teacher account", "registration_code": "Teacher registration code",
            "invalid": "Invalid credentials.", "registration_disabled": "Teacher account registration is currently disabled.",
            "username_help": "Use 3–40 Latin letters or digits; . _ - are allowed.",
            "password_help": "At least 8 characters with one letter and one digit.",
            "password_mismatch": "Passwords do not match.", "invalid_username": "Invalid username.",
            "invalid_email": "Enter a valid email address.", "weak_password": "Password is too weak.",
            "invalid_registration_code": "Invalid teacher registration code.",
            "account_created": "Teacher account created and signed in successfully.",
            "accept_policy": "I agree to use these account details to manage my educational projects in the platform.",
            "accept_required": "You must agree before creating the account.",
            "legacy_info": "A legacy administrator account can still be used when explicitly configured in Streamlit secrets.",
            "welcome": "Welcome",
            "new_project": "New educational project", "projects": "My projects", "outputs": "Generated outputs",
            "project_name": "Project name", "domain": "Subject or domain", "program": "Program or course", "unit": "Unit title",
            "concept": "Target concept", "learners": "Target learners", "level": "Learner level", "prerequisites": "Prerequisites",
            "languages": "Production languages", "primary_language": "Primary production language", "duration": "Expected duration",
            "environment": "Technical environment", "components": "Platform components", "source": "Available content and references",
            "files": "Upload references or content (PDF, DOCX, TXT, MD, CSV, JSON)",
            "teaching": "Preferred teaching approach", "assessment": "Preferred assessment approach", "notes": "Additional notes",
            "requested": "Requested outputs", "phase": "Current production phase", "save": "Save project and compile prompt",
            "generate": "Generate this phase with AI", "prompt": "Compiled prompt",
            "prompt_ready": "The prompt was rebuilt from the saved project. You can now preview, download, or run the selected phase.",
            "rebuild_prompt": "Rebuild prompt",
            "save_error": "The project could not be saved or the prompt could not be compiled.",
            "saving": "Saving the project and compiling the prompt...", "download_prompt": "Download prompt",
            "download_project": "Download project data", "saved": "Project saved and prompt compiled.",
            "generated": "The phase output was generated and saved.", "required": "Complete at least project, subject, unit, concept, and target learners.",
            "select_project": "Select a saved project", "no_projects": "No saved projects yet.",
            "provider": "Generation engine status", "phase_only": "The engine executes only the selected phase.",
        },
    }
    return values.get(lang, values["en"])


def _activate_teacher_session(account: Dict[str, Any]) -> None:
    st.session_state.teacher_logged_in = True
    st.session_state.teacher_account_id = account.get("id")
    st.session_state.teacher_username = str(account.get("username") or "").strip()
    st.session_state.teacher_display_name = str(account.get("full_name") or account.get("username") or "").strip()
    preferred = str(account.get("preferred_language") or i18n.current_lang(st)).strip().lower()
    if preferred in {"ar", "fr", "en"}:
        st.session_state.ui_language_code = preferred
        if hasattr(i18n, "LANGUAGE_LABELS"):
            st.session_state.ui_language = i18n.LANGUAGE_LABELS.get(preferred, st.session_state.get("ui_language"))
    db.log_event(None, "teacher", "sign_in", f"Teacher username: {st.session_state.teacher_username}")
    router.queue(router.route_key("teacher", "Content Studio"))


def _current_teacher_username() -> str:
    return str(st.session_state.get("teacher_username") or "teacher").strip()


def render_teacher_login() -> None:
    u = teacher_ui()
    st.markdown(f"## {u['login']}")
    st.caption(u["subtitle"])

    allow_registration = teacher_registration_enabled()
    tabs = st.tabs([u["login_tab"], u["register_tab"]]) if allow_registration else [st.container()]

    with tabs[0]:
        with st.form("teacher_login_form"):
            identifier = st.text_input(u["identifier"])
            password = st.text_input(u["password"], type="password")
            submitted = st.form_submit_button(u["sign_in"], type="primary", use_container_width=True)
        if submitted:
            account = authenticate_teacher_credentials(identifier, password)
            if account:
                _activate_teacher_session(account)
                st.rerun()
            st.error(u["invalid"])
        if _secret("TEACHER_USERNAME", "").strip() and (
            _secret("TEACHER_PASSWORD", "").strip() or _secret("TEACHER_PASSWORD_HASH", "").strip()
        ):
            st.caption(u["legacy_info"])

    if allow_registration:
        with tabs[1]:
            registration_code_required = teacher_registration_code()
            with st.form("teacher_registration_form", clear_on_submit=False):
                col1, col2 = st.columns(2)
                with col1:
                    full_name = st.text_input(u["full_name"])
                    username = st.text_input(u["username"], help=u["username_help"])
                    email = st.text_input(u["email"])
                with col2:
                    institution = st.text_input(u["institution"])
                    specialization = st.text_input(u["specialization"])
                    registration_code_value = ""
                    if registration_code_required:
                        registration_code_value = st.text_input(u["registration_code"], type="password")
                password = st.text_input(u["password"], type="password", help=u["password_help"], key="teacher_register_password")
                password2 = st.text_input(u["confirm_password"], type="password", key="teacher_register_password_confirm")
                accepted = st.checkbox(u["accept_policy"])
                create_submitted = st.form_submit_button(u["create_account"], type="primary", use_container_width=True)

            if create_submitted:
                if not _valid_teacher_username(username):
                    st.error(u["invalid_username"]); return
                if not _valid_email(email):
                    st.error(u["invalid_email"]); return
                if not _valid_password(password):
                    st.error(u["weak_password"]); return
                if password != password2:
                    st.error(u["password_mismatch"]); return
                if registration_code_required and registration_code_value.strip() != registration_code_required:
                    st.error(u["invalid_registration_code"]); return
                if not accepted:
                    st.error(u["accept_required"]); return
                try:
                    account = db.create_teacher_account(
                        full_name=full_name,
                        username=username,
                        email=email,
                        institution=institution,
                        specialization=specialization,
                        password=password,
                        preferred_language=i18n.current_lang(st),
                    )
                    db.log_event(None, "teacher", "account_created", f"Teacher username: {account.get('username')}")
                    _activate_teacher_session(account)
                    st.success(u["account_created"])
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
    else:
        st.info(u["registration_disabled"])


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

def save_project_and_prepare_prompt(data: Dict[str, Any], phase_number: int) -> tuple[int, str]:
    """Persist the project first, then compile the prompt from the saved record.

    Keeping this operation in one function makes the button action atomic from
    the UI perspective and gives validation scripts a testable code path.
    """
    project_id = db.save_teacher_project(data)
    saved = db.get_teacher_project(int(project_id), str(data.get("teacher_username") or ""))
    canonical = _project_defaults(saved or {**data, "id": project_id})
    canonical["id"] = int(project_id)
    prompt = compile_project_prompt(canonical, int(phase_number))
    if not prompt.strip():
        raise RuntimeError("The compiled prompt is empty.")
    return int(project_id), prompt


def render_project_form(existing: Optional[Dict[str, Any]] = None) -> None:
    u = teacher_ui()
    username = _current_teacher_username()
    p = _project_defaults(existing)
    lang_code = i18n.current_lang(st)

    form_scope = f"project_{int(p['id'])}" if p.get("id") else "new"
    with st.form(f"teacher_content_project_form_{form_scope}", clear_on_submit=False):
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
    with st.spinner(u["saving"]):
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
        "status": str(p.get("status") or "draft"),
    }
    try:
        with st.spinner(u["saving"]):
            project_id, prompt = save_project_and_prepare_prompt(data, int(phase_number))
    except Exception as exc:
        st.error(f"{u['save_error']} {exc}")
        return

    st.session_state.teacher_active_project_id = int(project_id)
    st.session_state.teacher_last_prompt = prompt
    st.session_state.teacher_studio_view = "workspace"
    # Queue the destination instead of mutating the radio widget key after the
    # widget has already been instantiated in the current Streamlit run.
    # Directly assigning teacher_workspace_section here raises
    # StreamlitAPIException when an existing project is saved from Production.
    st.session_state.teacher_workspace_section_pending = "production"
    st.session_state.teacher_expand_prompt = True
    st.session_state.teacher_flash_success = u["saved"]
    st.rerun()


def render_prompt_and_generation(project: Dict[str, Any]) -> None:
    u = teacher_ui()
    p = _project_defaults(project)
    phase_number = int(p.get("current_phase") or 1)
    prompt = compile_project_prompt(p, phase_number)
    st.session_state.teacher_last_prompt = prompt
    expand_prompt = bool(st.session_state.get("teacher_expand_prompt", False))
    st.success(u["prompt_ready"])
    status = content_generation_engine.provider_status()
    st.info(f"{u['provider']}: {status['provider']} / {status['model']} — {'ready' if status['available'] else 'prompt export only'}")
    st.caption(u["phase_only"])
    if st.button(u["rebuild_prompt"], use_container_width=True, key=f"rebuild_teacher_prompt_{p['id']}_{phase_number}"):
        st.session_state.teacher_last_prompt = compile_project_prompt(p, phase_number)
        st.session_state.teacher_expand_prompt = True
        st.session_state.teacher_flash_success = u["prompt_ready"]
        st.rerun()
    with st.expander(u["prompt"], expanded=expand_prompt):
        st.code(prompt, language="markdown")
    if expand_prompt:
        st.session_state.teacher_expand_prompt = False
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



def project_workspace_ui() -> Dict[str, str]:
    lang = i18n.current_lang(st)
    values = {
        "ar": {
            "new": "مشروع جديد", "projects": "مشاريعي التعليمية", "workspace": "واجهة المشروع", "outputs": "كل المخرجات",
            "open": "فتح المشروع", "continue": "متابعة الإنتاج", "preview": "معاينة كمتعلم", "back": "العودة إلى المشاريع",
            "overview": "نظرة عامة", "production": "الإنتاج والتحرير", "assets": "المحتوى والمخرجات", "publish": "المعاينة والنشر",
            "draft": "مسودة", "review": "قيد المراجعة", "published": "منشور", "archived": "مؤرشف",
            "progress": "تقدم الإنتاج", "phases": "المراحل المنجزة", "runs": "عمليات التوليد", "updated": "آخر تحديث",
            "empty_title": "ابدأ أول مشروع تعليمي", "empty_body": "أنشئ مشروعًا، أضف محتوى المادة وطريقة التدريس والتقييم، ثم أنتج موارده على مراحل.",
            "create": "إنشاء مشروع تعليمي", "project_center": "مركز المشروع التعليمي", "project_id": "رقم المشروع",
            "status": "حالة المشروع", "course_identity": "هوية المقرر", "learning_design": "التصميم التعليمي",
            "phase_map": "خريطة مراحل الإنتاج", "ready": "جاهز", "not_ready": "لم يُنتج بعد",
            "student_preview": "معاينة واجهة المتعلم", "publish_action": "نشر في فضاء المتعلم", "review_action": "إرسال للمراجعة",
            "draft_action": "إرجاع إلى المسودة", "archive_action": "أرشفة المشروع", "published_ok": "تم نشر المشروع في فضاء المتعلم.",
            "review_ok": "أصبح المشروع قيد المراجعة.", "draft_ok": "أُعيد المشروع إلى حالة المسودة.", "archive_ok": "تمت أرشفة المشروع.",
            "publish_gate": "يجب إكمال المرحلة الثالثة: المحتوى التعليمي الأساسي قبل النشر.",
            "public_catalog": "المقررات المنشورة من الأساتذة", "no_public": "لا توجد مقررات منشورة حاليًا.",
            "start_course": "فتح المقرر", "close_course": "العودة إلى قائمة المقررات", "educator_content": "محتوى أعدّه أستاذ عبر 3alimnIA",
            "lesson": "الدرس", "activity": "النشاط", "assessment": "التقييم", "ai_coach": "المدرّب الذكي", "references": "المراجع والملاحظات",
            "preview_note": "هذه معاينة قراءة قبل ربط المشروع بمسار تعلم وتسجيل كامل للإنجاز.",
        },
        "fr": {
            "new": "Nouveau projet", "projects": "Mes projets pédagogiques", "workspace": "Espace projet", "outputs": "Toutes les productions",
            "open": "Ouvrir le projet", "continue": "Continuer la production", "preview": "Aperçu apprenant", "back": "Retour aux projets",
            "overview": "Vue d’ensemble", "production": "Production et édition", "assets": "Contenus et productions", "publish": "Aperçu et publication",
            "draft": "Brouillon", "review": "En révision", "published": "Publié", "archived": "Archivé",
            "progress": "Progression de production", "phases": "Phases terminées", "runs": "Générations", "updated": "Dernière mise à jour",
            "empty_title": "Commencez votre premier projet", "empty_body": "Définissez le contenu, la pédagogie et l’évaluation, puis produisez les ressources par étapes.",
            "create": "Créer un projet pédagogique", "project_center": "Centre du projet", "project_id": "Projet",
            "status": "Statut", "course_identity": "Identité du cours", "learning_design": "Conception pédagogique",
            "phase_map": "Carte des phases", "ready": "Prêt", "not_ready": "Non généré",
            "student_preview": "Aperçu de l’espace apprenant", "publish_action": "Publier dans l’espace apprenant", "review_action": "Envoyer en révision",
            "draft_action": "Repasser en brouillon", "archive_action": "Archiver", "published_ok": "Projet publié dans l’espace apprenant.",
            "review_ok": "Projet envoyé en révision.", "draft_ok": "Projet repassé en brouillon.", "archive_ok": "Projet archivé.",
            "publish_gate": "La phase 3 — contenu pédagogique principal — doit être terminée avant publication.",
            "public_catalog": "Cours publiés par les enseignants", "no_public": "Aucun cours publié pour le moment.",
            "start_course": "Ouvrir le cours", "close_course": "Retour au catalogue", "educator_content": "Contenu créé par un enseignant avec 3alimnIA",
            "lesson": "Leçon", "activity": "Activité", "assessment": "Évaluation", "ai_coach": "Coach IA", "references": "Références et notes",
            "preview_note": "Aperçu en lecture avant l’intégration d’un parcours et d’un suivi complet.",
        },
        "en": {
            "new": "New project", "projects": "My educational projects", "workspace": "Project workspace", "outputs": "All outputs",
            "open": "Open project", "continue": "Continue production", "preview": "Preview as learner", "back": "Back to projects",
            "overview": "Overview", "production": "Production and editing", "assets": "Content and outputs", "publish": "Preview and publish",
            "draft": "Draft", "review": "In review", "published": "Published", "archived": "Archived",
            "progress": "Production progress", "phases": "Completed phases", "runs": "Generation runs", "updated": "Last updated",
            "empty_title": "Start your first educational project", "empty_body": "Define the subject, pedagogy, and assessment, then produce the assets phase by phase.",
            "create": "Create educational project", "project_center": "Educational project center", "project_id": "Project",
            "status": "Status", "course_identity": "Course identity", "learning_design": "Learning design",
            "phase_map": "Production phase map", "ready": "Ready", "not_ready": "Not generated",
            "student_preview": "Learner workspace preview", "publish_action": "Publish to learner workspace", "review_action": "Send for review",
            "draft_action": "Return to draft", "archive_action": "Archive project", "published_ok": "Project published to the learner workspace.",
            "review_ok": "Project moved to review.", "draft_ok": "Project returned to draft.", "archive_ok": "Project archived.",
            "publish_gate": "Phase 3 — core educational content — must be completed before publishing.",
            "public_catalog": "Teacher-published courses", "no_public": "No published courses are available yet.",
            "start_course": "Open course", "close_course": "Back to course catalogue", "educator_content": "Educator-authored content created with 3alimnIA",
            "lesson": "Lesson", "activity": "Activity", "assessment": "Assessment", "ai_coach": "AI Coach", "references": "References and notes",
            "preview_note": "This is a read-only preview before full enrollment and learning-progress tracking are connected.",
        },
    }
    return values.get(lang, values["en"])


def _status_label(status: str, copy: Dict[str, str]) -> str:
    clean = str(status or "draft").strip().lower()
    return copy.get(clean, clean.title())


def _project_progress_values(project: Dict[str, Any]) -> tuple[int, int, int]:
    completed = int(project.get("completed_phases") or 0)
    runs = int(project.get("generation_runs") or 0)
    return completed, runs, int(round(100 * completed / max(len(PHASES), 1)))


def _open_project(project_id: int, section: str = "overview") -> None:
    st.session_state.teacher_active_project_id = int(project_id)
    st.session_state.teacher_workspace_section = section
    st.session_state.teacher_studio_view = "workspace"


def render_projects_grid() -> None:
    copy = project_workspace_ui()
    username = _current_teacher_username()
    projects = db.teacher_projects_with_progress_df(username)
    st.markdown(f"## {copy['projects']}")
    if projects.empty:
        with st.container(border=True):
            st.markdown(f"### {copy['empty_title']}")
            st.write(copy["empty_body"])
            if st.button(copy["create"], type="primary", use_container_width=True, key="teacher_empty_create"):
                st.session_state.teacher_studio_view = "new"
                st.rerun()
        return

    rows = projects.to_dict("records")
    for start in range(0, len(rows), 2):
        cols = st.columns(2, gap="large")
        for col, project in zip(cols, rows[start:start + 2]):
            completed, runs, pct = _project_progress_values(project)
            status = str(project.get("status") or "draft").lower()
            with col:
                with st.container(border=True):
                    st.markdown(
                        f"<span class='v692-project-card-marker' aria-hidden='true'></span>"
                        f"<div class='v692-project-card-head'><span>{escape(_status_label(status, copy))}</span>"
                        f"<small>#{int(project['id'])}</small></div>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"### {project.get('project_name') or project.get('unit_title')}")
                    st.caption(f"{project.get('domain','')} · {project.get('program_name') or project.get('unit_title','')}")
                    st.write(str(project.get("target_concept") or "")[:240])
                    st.progress(pct / 100, text=f"{copy['progress']}: {pct}% — {completed}/{len(PHASES)}")
                    m1, m2, m3 = st.columns(3)
                    m1.metric(copy["phases"], f"{completed}/{len(PHASES)}")
                    m2.metric(copy["runs"], runs)
                    m3.metric(copy["status"], _status_label(status, copy))
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button(copy["open"], type="primary", use_container_width=True, key=f"open_teacher_project_{int(project['id'])}"):
                            _open_project(int(project["id"]), "overview")
                            st.rerun()
                    with b2:
                        if st.button(copy["continue"], use_container_width=True, key=f"continue_teacher_project_{int(project['id'])}"):
                            _open_project(int(project["id"]), "production")
                            st.rerun()


def _project_header(project: Dict[str, Any]) -> None:
    copy = project_workspace_ui()
    outputs = db.teacher_project_phase_outputs(int(project["id"]))
    completed = sum(1 for row in outputs.values() if str(row.get("status")) == "completed")
    pct = int(round(100 * completed / max(len(PHASES), 1)))
    c_back, c_title, c_status = st.columns([1.15, 5.1, 1.35], vertical_alignment="center")
    with c_back:
        if st.button(f"← {copy['back']}", use_container_width=True, key="teacher_back_to_projects"):
            st.session_state.teacher_studio_view = "projects"
            st.rerun()
    with c_title:
        st.markdown(f"<span class='v692-project-workspace-marker' aria-hidden='true'></span>", unsafe_allow_html=True)
        st.caption(f"{copy['project_center']} · #{int(project['id'])}")
        st.markdown(f"# {project.get('project_name') or project.get('unit_title')}")
        st.write(f"{project.get('domain','')} · {project.get('program_name') or ''} · {project.get('unit_title','')}")
    with c_status:
        st.metric(copy["status"], _status_label(str(project.get("status") or "draft"), copy))
    st.progress(pct / 100, text=f"{copy['progress']}: {pct}% — {completed}/{len(PHASES)}")


def _render_phase_map(project: Dict[str, Any]) -> None:
    copy = project_workspace_ui()
    outputs = db.teacher_project_phase_outputs(int(project["id"]))
    st.markdown(f"### {copy['phase_map']}")
    for start in range(1, 12, 3):
        cols = st.columns(3, gap="small")
        for col, phase in zip(cols, range(start, min(start + 3, 12))):
            row = outputs.get(phase)
            ready = bool(row and str(row.get("status")) == "completed")
            with col:
                with st.container(border=True):
                    st.caption(f"{phase:02d}")
                    st.markdown(f"**{PHASES[phase]}**")
                    st.success(copy["ready"], icon="✓") if ready else st.caption(copy["not_ready"])


def render_project_overview(project: Dict[str, Any]) -> None:
    copy = project_workspace_ui()
    p = _project_defaults(project)
    c1, c2 = st.columns(2, gap="large")
    with c1:
        with st.container(border=True):
            st.markdown(f"### {copy['course_identity']}")
            st.markdown(f"**{p.get('unit_title','')}**")
            st.write(p.get("target_concept") or "")
            st.caption(f"{p.get('target_learners','')} · {p.get('learner_level','')}")
            st.write(f"**Languages:** {', '.join(p.get('target_languages') or [])}")
            st.write(f"**Duration:** {p.get('expected_duration') or '—'}")
    with c2:
        with st.container(border=True):
            st.markdown(f"### {copy['learning_design']}")
            st.write(p.get("teaching_preferences") or "—")
            st.markdown("**Assessment**")
            st.write(p.get("assessment_preferences") or "—")
            st.markdown("**Platform components**")
            st.write(", ".join(p.get("platform_components") or []) or "—")
    _render_phase_map(project)


def _latest_completed_output(project_id: int, phase: int) -> str:
    row = db.teacher_project_phase_outputs(int(project_id)).get(int(phase))
    if not row or str(row.get("status")) != "completed":
        return ""
    return str(row.get("response_text") or "").strip()


def render_project_student_preview(project: Dict[str, Any], public_view: bool = False) -> None:
    copy = project_workspace_ui()
    p = _project_defaults(project)
    direction = i18n.direction(i18n.current_lang(st))
    st.markdown(
        f"<section class='v692-course-preview-hero' dir='{direction}'>"
        f"<span>{escape(copy['educator_content'])}</span>"
        f"<h1>{escape(str(p.get('unit_title') or p.get('project_name') or ''))}</h1>"
        f"<p>{escape(str(p.get('target_concept') or ''))}</p>"
        f"<div><b>{escape(str(p.get('domain') or ''))}</b><i>{escape(str(p.get('learner_level') or ''))}</i>"
        f"<i>{escape(str(p.get('expected_duration') or ''))}</i></div></section>",
        unsafe_allow_html=True,
    )
    st.caption(copy["preview_note"])
    lesson_text = _latest_completed_output(int(p["id"]), 3)
    activity_text = _latest_completed_output(int(p["id"]), 6)
    assessment_text = _latest_completed_output(int(p["id"]), 8)
    coach_text = _latest_completed_output(int(p["id"]), 7)
    tabs = st.tabs([copy["lesson"], copy["activity"], copy["assessment"], copy["ai_coach"], copy["references"]])
    with tabs[0]:
        if lesson_text:
            st.markdown(lesson_text)
        else:
            st.info(copy["not_ready"])
            st.markdown(str(p.get("source_material") or p.get("target_concept") or ""))
    with tabs[1]:
        st.markdown(activity_text) if activity_text else st.info(copy["not_ready"])
    with tabs[2]:
        st.markdown(assessment_text) if assessment_text else st.info(copy["not_ready"])
    with tabs[3]:
        st.markdown(coach_text) if coach_text else st.info(copy["not_ready"])
    with tabs[4]:
        st.markdown(str(p.get("source_material") or "—"))
        if p.get("additional_notes"):
            st.markdown("---")
            st.write(p.get("additional_notes"))


def render_project_publication(project: Dict[str, Any]) -> None:
    copy = project_workspace_ui()
    outputs = db.teacher_project_phase_outputs(int(project["id"]))
    core_ready = bool(outputs.get(3) and str(outputs[3].get("status")) == "completed")
    render_project_student_preview(project, public_view=False)
    st.divider()
    current_status = str(project.get("status") or "draft").lower()
    st.markdown(f"### {copy['status']}: {_status_label(current_status, copy)}")
    if not core_ready:
        st.warning(copy["publish_gate"])
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button(copy["review_action"], use_container_width=True, disabled=current_status == "review", key="teacher_mark_review"):
            db.set_teacher_project_status(int(project["id"]), _current_teacher_username(), "review")
            st.success(copy["review_ok"]); st.rerun()
    with c2:
        if st.button(copy["publish_action"], type="primary", use_container_width=True, disabled=(not core_ready or current_status == "published"), key="teacher_publish_project"):
            db.set_teacher_project_status(int(project["id"]), _current_teacher_username(), "published")
            st.success(copy["published_ok"]); st.rerun()
    with c3:
        action = "draft" if current_status != "draft" else "archived"
        label = copy["draft_action"] if action == "draft" else copy["archive_action"]
        if st.button(label, use_container_width=True, key="teacher_unpublish_or_archive"):
            db.set_teacher_project_status(int(project["id"]), _current_teacher_username(), action)
            st.success(copy["draft_ok"] if action == "draft" else copy["archive_ok"]); st.rerun()


def render_project_workspace() -> None:
    project_id = st.session_state.get("teacher_active_project_id")
    if not project_id:
        st.session_state.teacher_studio_view = "projects"
        st.rerun()
    project = db.get_teacher_project(int(project_id), _current_teacher_username())
    if not project:
        st.error("Project not found or access denied.")
        st.session_state.teacher_studio_view = "projects"
        return
    _project_header(project)
    copy = project_workspace_ui()
    sections = ["overview", "production", "assets", "publish"]
    labels = {"overview": copy["overview"], "production": copy["production"], "assets": copy["assets"], "publish": copy["publish"]}
    # Apply queued navigation before the radio is created. Streamlit permits
    # state initialization here, but not after the widget with the same key has
    # been instantiated.
    pending_section = st.session_state.pop("teacher_workspace_section_pending", None)
    if pending_section in sections:
        st.session_state.teacher_workspace_section = pending_section
    if st.session_state.get("teacher_workspace_section") not in sections:
        st.session_state.teacher_workspace_section = "overview"
    section = st.radio(
        "Project workspace section", sections, format_func=lambda x: labels[x], horizontal=True,
        label_visibility="collapsed", key="teacher_workspace_section",
    )
    st.divider()
    if section == "overview":
        render_project_overview(project)
    elif section == "production":
        render_project_form(project)
        refreshed = db.get_teacher_project(int(project_id), _current_teacher_username()) or project
        st.divider()
        render_prompt_and_generation(refreshed)
    elif section == "assets":
        render_outputs(project)
    else:
        render_project_publication(project)


def render_all_outputs() -> None:
    copy = project_workspace_ui()
    projects = db.teacher_projects_with_progress_df(_current_teacher_username())
    st.markdown(f"## {copy['outputs']}")
    if projects.empty:
        st.info(copy["empty_body"])
        return
    options = {f"#{int(row['id'])} — {row['project_name']}": int(row["id"]) for _, row in projects.iterrows()}
    selected_label = st.selectbox(project_workspace_ui()["projects"], list(options.keys()), key="teacher_all_outputs_project")
    project = db.get_teacher_project(options[selected_label], _current_teacher_username())
    render_outputs(project)


def render_published_course_catalog(student: Optional[Dict[str, Any]] = None) -> None:
    """Render teacher-published projects in a learner-safe, read-only catalogue."""
    copy = project_workspace_ui()
    selected_id = st.session_state.get("published_teacher_project_id")
    if selected_id:
        project = db.get_published_teacher_project(int(selected_id))
        if project:
            if st.button(f"← {copy['close_course']}", key="close_published_teacher_course"):
                st.session_state.published_teacher_project_id = None
                st.rerun()
            render_project_student_preview(project, public_view=True)
            return
        st.session_state.published_teacher_project_id = None
    projects = db.published_teacher_projects_df()
    st.markdown(f"# {copy['public_catalog']}")
    if projects.empty:
        st.info(copy["no_public"])
        return
    rows = projects.to_dict("records")
    for start in range(0, len(rows), 3):
        cols = st.columns(3, gap="large")
        for col, project in zip(cols, rows[start:start + 3]):
            with col:
                with st.container(border=True):
                    st.markdown("<span class='v692-public-course-marker' aria-hidden='true'></span>", unsafe_allow_html=True)
                    st.caption(f"{project.get('domain','')} · {project.get('learner_level','')}")
                    st.markdown(f"### {project.get('unit_title') or project.get('project_name')}")
                    st.write(str(project.get("target_concept") or "")[:220])
                    st.caption(f"{project.get('expected_duration') or ''} · {int(project.get('completed_phases') or 0)}/{len(PHASES)}")
                    if st.button(copy["start_course"], type="primary", use_container_width=True, key=f"open_published_course_{int(project['id'])}"):
                        st.session_state.published_teacher_project_id = int(project["id"])
                        st.rerun()


def render_teacher_app() -> None:
    init_teacher_state()
    if not st.session_state.teacher_logged_in:
        render_teacher_login()
        return
    u = teacher_ui()
    copy = project_workspace_ui()
    display_name = str(st.session_state.get("teacher_display_name") or _current_teacher_username()).strip()
    st.markdown(f"# {u['workspace']}")
    st.caption(f"{u['welcome']}، {display_name} — {u['subtitle']}" if i18n.current_lang(st) == "ar" else f"{u['welcome']}, {display_name} — {u['subtitle']}")
    flash_success = st.session_state.pop("teacher_flash_success", None)
    if flash_success:
        st.success(str(flash_success))
    flash_error = st.session_state.pop("teacher_flash_error", None)
    if flash_error:
        st.error(str(flash_error))
    views = ["projects", "new", "workspace", "outputs"]
    if st.session_state.get("teacher_studio_view") not in views:
        st.session_state.teacher_studio_view = "projects"
    view_labels = {"projects": copy["projects"], "new": copy["new"], "workspace": copy["workspace"], "outputs": copy["outputs"]}
    nav_key = "teacher_studio_nav_control"
    desired_view = st.session_state.teacher_studio_view
    if st.session_state.get(nav_key) != desired_view:
        st.session_state[nav_key] = desired_view
    view = st.radio(
        "Teacher studio view", views, format_func=lambda x: view_labels[x], horizontal=True,
        label_visibility="collapsed", key=nav_key,
    )
    if view != st.session_state.teacher_studio_view:
        st.session_state.teacher_studio_view = view
        st.rerun()
    st.divider()
    if view == "new":
        render_project_form(None)
    elif view == "projects":
        render_projects_grid()
    elif view == "workspace":
        render_project_workspace()
    else:
        render_all_outputs()

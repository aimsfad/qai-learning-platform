"""Teacher Content Studio for designing and generating educational units."""

from __future__ import annotations

import io
import json
import re
from html import escape
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

import content_generation_engine
import educational_builder
import evidence_synthesis_engine
import lesson_blueprint_engine
import lesson_block_generation_engine
import production_pipeline
import guided_teacher_workflow
import simple_teacher_journey
import gemini_file_analyzer
import db
import i18n
import router
import web_research_engine
import branding
import ui_stability
import global_design_system as global_ui
import workflow_runtime_contracts
import pedagogical_orchestrator
import lesson_content_renderer
from security import verify_password


PHASES = educational_builder.PHASES
LANGUAGE_NAMES = educational_builder.LANGUAGE_NAMES


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
    st.session_state.setdefault("teacher_experience_mode", "simple" if _as_bool(_secret("TEACHER_SIMPLE_MODE_DEFAULT", "true"), True) else "advanced")
    st.session_state.setdefault("teacher_simple_stage", None)


def teacher_ui() -> Dict[str, str]:
    lang = i18n.current_lang(st)
    values = {
        "ar": {
            "workspace": "فضاء الأستاذ",
            "subtitle": "أنشئي المقرر في خمس خطوات واضحة: الإعداد، المصادر، الخطة، الدروس، ثم المراجعة والنشر.",
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
            "generated": "تم توليد مخرجات المرحلة وحفظها، وانتقل المشروع إلى المرحلة التالية.",
            "required": "املأ اسم المشروع والمادة والوحدة والمفهوم والفئة المستهدفة على الأقل.",
            "select_project": "اختر مشروعًا محفوظًا",
            "no_projects": "لا توجد مشاريع محفوظة بعد.",
            "provider": "حالة محرك التوليد",
            "phase_only": "ينفذ النظام مرحلة واحدة في كل مرة، ثم ينتقل تلقائيًا إلى المرحلة التالية بعد اجتياز التحقق البنيوي.",
            "prompt_budget": "ميزانية الطلب: نحو {runtime} رمز إدخال من أصل {original}، وحد أقصى {output} رمزًا للإجابة{compacted}.",
            "prompt_compacted": " بعد ضغط السياق تلقائيًا",
            "latest_output": "أحدث مخرجات التوليد", "needs_review": "تم حفظ الناتج لكنه يحتاج مراجعة أو إعادة توليد.",
            "research_on": "البحث الويبّي الموثّق مفعّل للمراحل الحساسة للأدلة.", "research_off": "البحث الويبّي غير مفعّل؛ سيعتمد النموذج على المراجع المرفوعة ويصرّح بفجوات الأدلة.",
            "latency": "زمن التوليد", "generation_failed": "تعذر إكمال التوليد.",
            "preview_output": "معاينة", "edit_output": "مراجعة وتحرير", "save_revision": "حفظ مراجعة الأستاذ واعتماد المرحلة",
            "revision_saved": "تم حفظ مراجعة الأستاذ واعتماد المرحلة.", "download_output": "تنزيل مخرجات المرحلة",
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
            "generated": "La production a été générée, enregistrée et le projet est passé à la phase suivante.", "required": "Renseignez au minimum le projet, la discipline, l’unité, le concept et le public.",
            "select_project": "Choisir un projet enregistré", "no_projects": "Aucun projet enregistré.",
            "provider": "État du moteur de génération", "phase_only": "Le système exécute une phase à la fois puis avance automatiquement après validation structurelle.",
            "prompt_budget": "Budget de requête : environ {runtime} jetons d’entrée sur {original}, avec {output} jetons de sortie maximum{compacted}.",
            "prompt_compacted": " après compression automatique du contexte",
            "latest_output": "Dernière production", "needs_review": "La production a été enregistrée mais doit être révisée ou régénérée.",
            "research_on": "La recherche Web documentée est activée pour les phases sensibles aux preuves.", "research_off": "La recherche Web est désactivée; le modèle s’appuie sur les sources importées et signale les lacunes.",
            "latency": "Temps de génération", "generation_failed": "La génération n’a pas pu être terminée.",
            "preview_output": "Aperçu", "edit_output": "Réviser et modifier", "save_revision": "Enregistrer la révision et approuver la phase",
            "revision_saved": "La révision de l’enseignant a été enregistrée et la phase approuvée.", "download_output": "Télécharger la production",
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
            "generated": "The phase output was generated, saved, and the project advanced to the next phase.", "required": "Complete at least project, subject, unit, concept, and target learners.",
            "select_project": "Select a saved project", "no_projects": "No saved projects yet.",
            "provider": "Generation engine status", "phase_only": "The engine executes one phase at a time and advances automatically after structural validation.",
            "prompt_budget": "Request budget: about {runtime} input tokens from {original}, with an output cap of {output}{compacted}.",
            "prompt_compacted": " after automatic context compaction",
            "latest_output": "Latest generated output", "needs_review": "The output was saved but requires review or regeneration.",
            "research_on": "Documented web research is enabled for evidence-sensitive phases.", "research_off": "Web research is disabled; the model will rely on uploaded sources and mark evidence gaps.",
            "latency": "Generation time", "generation_failed": "Generation could not be completed.",
            "preview_output": "Preview", "edit_output": "Review and edit", "save_revision": "Save teacher revision and approve phase",
            "revision_saved": "The teacher revision was saved and the phase approved.", "download_output": "Download phase output",
        },
    }
    research_copy = {
        "ar": {
            "research_panel": "البحث الويبّي الموجّه",
            "research_intro": "تبحث المنصة أولًا عن الأدلة والمراجع والموارد المناسبة للمرحلة، ثم تُدخل حزمة بحث موثّقة في برومبت التوليد.",
            "research_mode": "عمق البحث",
            "research_mode_off": "دون بحث ويب",
            "research_mode_quick": "سريع",
            "research_mode_balanced": "متوازن",
            "research_mode_deep": "موسّع",
            "research_sources": "الحد الأقصى للمصادر",
            "preferred_domains": "نطاقات مفضلة، مفصولة بفواصل",
            "excluded_domains": "نطاقات مستبعدة، مفصولة بفواصل",
            "research_now": "تشغيل البحث لهذه المرحلة",
            "research_refresh": "إعادة البحث وتحديث الأدلة",
            "research_ready": "تم حفظ حزمة البحث وستُستخدم تلقائيًا في التوليد.",
            "research_missing": "لا توجد حزمة بحث محفوظة لهذه المرحلة؛ سيشغّلها النظام تلقائيًا عند التوليد ما دام البحث غير معطل.",
            "research_failed": "تعذر إكمال البحث الويبّي.",
            "research_cached_fallback": "تعذر تحديث البحث حاليًا؛ تم الاحتفاظ بآخر حزمة بحث ناجحة ويمكن متابعة العمل بها.",
            "research_latest": "أحدث حزمة بحث",
            "research_queries": "عبارات البحث",
            "research_report": "ملخص الأدلة والموارد",
            "research_registry": "سجل المصادر",
            "research_download": "تنزيل حزمة البحث",
            "research_cost": "قد ينفذ المزوّد أكثر من استعلام بحث واحد. الوضع المتوازن مناسب غالبًا، والموسّع مخصص للمراحل التي تحتاج تدقيقًا أعمق.",
            "authority": "الموثوقية",
        },
        "fr": {
            "research_panel": "Recherche Web guidée",
            "research_intro": "La plateforme recherche d’abord les preuves, références et ressources utiles à la phase, puis injecte un dossier sourcé dans le prompt de génération.",
            "research_mode": "Profondeur de recherche",
            "research_mode_off": "Sans recherche Web",
            "research_mode_quick": "Rapide",
            "research_mode_balanced": "Équilibrée",
            "research_mode_deep": "Approfondie",
            "research_sources": "Nombre maximal de sources",
            "preferred_domains": "Domaines préférés, séparés par des virgules",
            "excluded_domains": "Domaines exclus, séparés par des virgules",
            "research_now": "Lancer la recherche pour cette phase",
            "research_refresh": "Relancer et actualiser la recherche",
            "research_ready": "Le dossier de recherche est enregistré et sera utilisé automatiquement.",
            "research_missing": "Aucun dossier n’est enregistré; la recherche sera lancée automatiquement lors de la génération sauf si elle est désactivée.",
            "research_failed": "La recherche Web n’a pas pu être terminée.",
            "research_cached_fallback": "La mise à jour a échoué; le dernier dossier de recherche valide reste actif.",
            "research_latest": "Dernier dossier de recherche",
            "research_queries": "Requêtes de recherche",
            "research_report": "Synthèse des preuves et ressources",
            "research_registry": "Registre des sources",
            "research_download": "Télécharger le dossier de recherche",
            "research_cost": "Le fournisseur peut exécuter plusieurs requêtes. Le mode équilibré convient généralement; le mode approfondi est réservé aux audits plus exigeants.",
            "authority": "Autorité",
        },
        "en": {
            "research_panel": "Guided web research",
            "research_intro": "The platform first retrieves evidence, references, and phase-specific learning resources, then injects a sourced research packet into the generation prompt.",
            "research_mode": "Research depth",
            "research_mode_off": "No web research",
            "research_mode_quick": "Quick",
            "research_mode_balanced": "Balanced",
            "research_mode_deep": "Deep",
            "research_sources": "Maximum sources",
            "preferred_domains": "Preferred domains, comma-separated",
            "excluded_domains": "Excluded domains, comma-separated",
            "research_now": "Run research for this phase",
            "research_refresh": "Refresh web research",
            "research_ready": "The research packet is stored and will be used automatically during generation.",
            "research_missing": "No research packet is stored; generation will run research automatically unless web research is disabled.",
            "research_failed": "Web research could not be completed.",
            "research_cached_fallback": "The refresh failed; the latest usable research dossier remains active.",
            "research_latest": "Latest research packet",
            "research_queries": "Search queries",
            "research_report": "Evidence and resource synthesis",
            "research_registry": "Source registry",
            "research_download": "Download research packet",
            "research_cost": "The provider may execute multiple searches. Balanced mode is suitable for most phases; deep mode is intended for more demanding evidence audits.",
            "authority": "Authority",
        },
    }
    for code, additions in research_copy.items():
        values[code].update(additions)
    evidence_copy = {
        "ar": {
            "evidence_panel": "تركيب الأدلة",
            "evidence_intro": "تحول المنصة حزمة البحث إلى مصادر مقيمة، وبطاقات أدلة مرتبطة بمراجع محددة، ومفاهيم أولية قبل إنشاء الدرس.",
            "evidence_run": "إنشاء حزمة الأدلة من أحدث بحث",
            "evidence_refresh": "إعادة تركيب الأدلة",
            "evidence_missing_research": "شغّل البحث الويبّي لهذه المرحلة أولًا، ثم عد إلى تركيب الأدلة.",
            "evidence_missing": "لم تُنشأ حزمة أدلة لهذه المرحلة بعد.",
            "evidence_latest": "أحدث حزمة أدلة",
            "evidence_sources_tab": "تقييم المصادر",
            "evidence_cards_tab": "بطاقات الأدلة",
            "evidence_concepts_tab": "المفاهيم والمتطلبات السابقة",
            "evidence_quality_tab": "بوابة الجودة",
            "evidence_approve": "اعتماد حزمة الأدلة للتوليد",
            "evidence_approved": "اعتمد الأستاذ حزمة الأدلة، وستستخدم في برومبت التوليد.",
            "evidence_saved": "تم إنشاء حزمة الأدلة وحفظها للمراجعة.",
            "evidence_download": "تنزيل حزمة الأدلة",
            "evidence_readiness": "درجة الجاهزية",
            "evidence_cards": "بطاقات الأدلة",
            "evidence_concepts": "المفاهيم",
            "evidence_approved_sources": "المصادر المعتمدة آليًا",
            "evidence_source_score": "الدرجة المركبة",
            "evidence_status": "الحالة",
            "evidence_warnings": "تحذيرات الجودة",
            "evidence_phase": "مرحلة الأدلة",
            "evidence_strict_gate": "عند تفعيل بوابة الموافقة الصارمة، لن يبدأ التوليد قبل اعتماد الأستاذ لهذه الحزمة.",
        },
        "fr": {
            "evidence_panel": "Synthèse des preuves",
            "evidence_intro": "La plateforme transforme le dossier de recherche en sources évaluées, cartes de preuve traçables et concepts préalables avant la génération de la leçon.",
            "evidence_run": "Construire les preuves à partir de la dernière recherche",
            "evidence_refresh": "Reconstruire les preuves",
            "evidence_missing_research": "Lancez d’abord la recherche Web pour cette phase.",
            "evidence_missing": "Aucun dossier de preuves n’a encore été créé.",
            "evidence_latest": "Dernier dossier de preuves",
            "evidence_sources_tab": "Évaluation des sources",
            "evidence_cards_tab": "Cartes de preuve",
            "evidence_concepts_tab": "Concepts et prérequis",
            "evidence_quality_tab": "Contrôle qualité",
            "evidence_approve": "Approuver le dossier pour la génération",
            "evidence_approved": "Le dossier est approuvé et sera utilisé dans le prompt.",
            "evidence_saved": "Le dossier de preuves a été enregistré pour révision.",
            "evidence_download": "Télécharger le dossier de preuves",
            "evidence_readiness": "Score de préparation",
            "evidence_cards": "Cartes de preuve",
            "evidence_concepts": "Concepts",
            "evidence_approved_sources": "Sources approuvées automatiquement",
            "evidence_source_score": "Score composite",
            "evidence_status": "Statut",
            "evidence_warnings": "Alertes qualité",
            "evidence_phase": "Phase de preuves",
            "evidence_strict_gate": "Lorsque le contrôle strict est activé, la génération attend l’approbation de l’enseignant.",
        },
        "en": {
            "evidence_panel": "Evidence synthesis",
            "evidence_intro": "The platform converts the research dossier into scored sources, traceable evidence cards, and prerequisite concepts before lesson generation.",
            "evidence_run": "Build evidence from latest research",
            "evidence_refresh": "Rebuild evidence synthesis",
            "evidence_missing_research": "Run web research for this phase before synthesizing evidence.",
            "evidence_missing": "No evidence bundle has been created for this phase.",
            "evidence_latest": "Latest evidence bundle",
            "evidence_sources_tab": "Source assessment",
            "evidence_cards_tab": "Evidence cards",
            "evidence_concepts_tab": "Concepts and prerequisites",
            "evidence_quality_tab": "Quality gate",
            "evidence_approve": "Approve evidence bundle for generation",
            "evidence_approved": "The teacher approved this evidence bundle; it will be used in the generation prompt.",
            "evidence_saved": "The evidence bundle was created and stored for review.",
            "evidence_download": "Download evidence bundle",
            "evidence_readiness": "Readiness score",
            "evidence_cards": "Evidence cards",
            "evidence_concepts": "Concepts",
            "evidence_approved_sources": "Automatically approved sources",
            "evidence_source_score": "Composite score",
            "evidence_status": "Status",
            "evidence_warnings": "Quality warnings",
            "evidence_phase": "Evidence phase",
            "evidence_strict_gate": "When the strict approval gate is enabled, generation waits for teacher approval.",
        },
    }
    for code, additions in evidence_copy.items():
        values[code].update(additions)
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
    """Render a centered, calm authentication card for the teacher workspace."""
    u = teacher_ui()
    lang = i18n.current_lang(st)
    direction = i18n.direction(lang)
    login_copy = {
        "ar": {
            "eyebrow": "استوديو إنتاج المحتوى",
            "title": "مرحبًا بعودتك",
            "body": "سجّل الدخول لمتابعة مشاريعك التعليمية وبناء المقررات خطوة بخطوة.",
        },
        "fr": {
            "eyebrow": "Studio de production pédagogique",
            "title": "Heureux de vous revoir",
            "body": "Connectez-vous pour reprendre vos projets et construire vos cours étape par étape.",
        },
        "en": {
            "eyebrow": "Learning content studio",
            "title": "Welcome back",
            "body": "Sign in to continue your educational projects and build courses step by step.",
        },
    }.get(lang)

    st.markdown("<span class='v6163-login-page-marker' aria-hidden='true'></span>", unsafe_allow_html=True)
    _, login_col, _ = ui_stability.columns([1, 1.55, 1], gap="large", vertical_alignment="top")
    with login_col:
        with st.container(border=True, key="v6163_teacher_login_card"):
            st.markdown("<span class='v6163-login-card-marker' aria-hidden='true'></span>", unsafe_allow_html=True)
            logo_path = getattr(branding, "OFFICIAL_LOGO_PATH", None)
            if logo_path and logo_path.exists():
                st.image(str(logo_path), width=188)
            st.markdown(
                f"<div class='v6163-login-copy' dir='{direction}'>"
                f"<span>{escape(login_copy['eyebrow'])}</span>"
                f"<h2>{escape(login_copy['title'])}</h2>"
                f"<p>{escape(login_copy['body'])}</p>"
                f"</div>",
                unsafe_allow_html=True,
            )

            allow_registration = teacher_registration_enabled()
            if allow_registration:
                login_tab, register_tab = st.tabs([u["login_tab"], u["register_tab"]])
            else:
                login_tab = st.container()
                register_tab = None

            with login_tab:
                with st.form("teacher_login_form"):
                    identifier = st.text_input(u["identifier"], placeholder=u["identifier"])
                    password = st.text_input(u["password"], type="password", placeholder=u["password"])
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

            if allow_registration and register_tab is not None:
                with register_tab:
                    registration_code_required = teacher_registration_code()
                    with st.form("teacher_registration_form", clear_on_submit=False):
                        col1, col2 = st.columns(2, gap="medium", vertical_alignment="top")
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
                            ui_stability.render_error_card(exc, lang=i18n.current_lang(st))
            else:
                st.info(u["registration_disabled"])


def _teacher_brief(data: Dict[str, Any]) -> str:
    """Compatibility wrapper for the V6.11 bounded teacher brief."""
    return educational_builder.teacher_brief(data)


def compile_project_prompt(data: Dict[str, Any], phase_number: int) -> str:
    """Compile the selected phase and accepted prior outputs only."""
    return educational_builder.compile_project_prompt(data, int(phase_number))


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


def extract_uploaded_sources(
    uploaded_files: Any,
    *,
    project_context: Optional[Dict[str, Any]] = None,
    language: str = "English",
) -> str:
    """Analyze teacher sources through Gemini with bounded local fallbacks."""
    return gemini_file_analyzer.extract_uploaded_sources(
        uploaded_files,
        project_context=project_context or {},
        language=language,
    )

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
            u["files"],
            type=["pdf", "docx", "txt", "md", "csv", "json", "png", "jpg", "jpeg", "webp", "mp3", "wav", "m4a", "mp4", "mov"],
            accept_multiple_files=True,
            key=f"teacher_source_uploads_{form_scope}",
        )
        file_status = gemini_file_analyzer.provider_status()
        if file_status["mode"] == "multimodal":
            status_copy = {
                "ar": "تحليل Gemini متعدد الوسائط جاهز للملفات والصور والجداول والصوت والفيديو.",
                "fr": "L’analyse multimodale Gemini est prête pour les fichiers, images, tableaux, audio et vidéo.",
                "en": "Gemini multimodal analysis is ready for files, images, tables, audio, and video.",
            }
        else:
            status_copy = {
                "ar": "سيُستخدم الاستخراج المحلي للملفات النصية؛ تحليل الصور والوسائط يحتاج مفتاح Gemini صالحًا.",
                "fr": "L’extraction locale sera utilisée; l’analyse des images et médias nécessite une clé Gemini valide.",
                "en": "Local extraction will be used; image and media analysis requires a valid Gemini key.",
            }
        st.caption(status_copy.get(lang_code, status_copy["en"]))
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
    source_analysis_context = {
        "domain": domain.strip(),
        "program_name": program_name.strip(),
        "unit_title": unit_title.strip(),
        "target_concept": target_concept.strip(),
        "target_learners": target_learners.strip(),
        "learner_level": learner_level,
        "teaching_preferences": teaching_preferences.strip(),
        "assessment_preferences": assessment_preferences.strip(),
    }
    with st.spinner(u["saving"]):
        extracted_sources = extract_uploaded_sources(
            uploaded_sources,
            project_context=source_analysis_context,
            language=primary_language,
        )
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
        ui_stability.render_error_card(exc, lang=i18n.current_lang(st))
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


def _render_generation_markdown(text: str, language_code: str) -> None:
    """Render generated Markdown inside a scoped bidirectional container."""
    marker_class = "v6111-generation-output-rtl" if str(language_code).lower() == "ar" else "v6111-generation-output-ltr"
    with st.container():
        st.markdown(f"<span class='{marker_class}' aria-hidden='true'></span>", unsafe_allow_html=True)
        st.markdown(str(text or ""))


def _render_latest_generation(project_id: int, u: Dict[str, str], language_code: str = "en") -> None:
    latest = db.latest_teacher_generation(int(project_id))
    if not latest:
        return
    phase = int(latest.get("phase_number") or 0)
    status = str(latest.get("status") or "")
    provider = str(latest.get("provider") or "")
    model = str(latest.get("model") or "")
    latency_ms = int(latest.get("latency_ms") or 0)
    response_text = str(latest.get("response_text") or "").strip()
    title = f"{u['latest_output']} — {phase}. {PHASES.get(phase, '')}"
    with st.expander(title, expanded=status in {"completed", "needs_review"}):
        m1, m2, m3 = st.columns(3)
        m1.metric("Status", status or "—")
        m2.metric("Model", f"{provider} / {model}" if provider or model else "—")
        m3.metric(u["latency"], f"{latency_ms / 1000:.1f} s" if latency_ms else "—")
        if latest.get("diagnostic"):
            st.caption(str(latest.get("diagnostic")))
        preview_tab, edit_tab = st.tabs([u["preview_output"], u["edit_output"]])
        with preview_tab:
            if response_text:
                _render_generation_markdown(response_text, language_code)
                st.download_button(
                    u["download_output"],
                    response_text.encode("utf-8"),
                    file_name=f"project_{int(project_id)}_phase_{phase}_output.md",
                    mime="text/markdown",
                    use_container_width=True,
                    key=f"download_latest_teacher_output_{int(latest['id'])}",
                )
        with edit_tab:
            revision = st.text_area(
                u["edit_output"],
                value=response_text,
                height=440,
                key=f"teacher_revision_editor_{int(latest['id'])}",
                label_visibility="collapsed",
            )
            if st.button(
                u["save_revision"],
                type="primary",
                use_container_width=True,
                key=f"save_teacher_revision_{int(latest['id'])}",
            ):
                try:
                    db.save_teacher_manual_revision(
                        int(project_id),
                        _current_teacher_username(),
                        phase,
                        revision,
                        source_run_id=int(latest["id"]),
                    )
                    st.session_state.teacher_flash_success = u["revision_saved"]
                except Exception as exc:
                    st.session_state.teacher_flash_error = str(exc)
                st.rerun()


def _split_domain_input(value: str) -> List[str]:
    items = re.split(r"[,;\n]+", str(value or ""))
    return [item.strip() for item in items if item.strip()]


def _render_latest_research(
    project_id: int,
    phase_number: int,
    u: Dict[str, str],
    *,
    canonical_stage: bool = False,
) -> Optional[Dict[str, Any]]:
    """Render one visible research-review area with one approval action."""
    latest = db.latest_usable_teacher_research(int(project_id), int(phase_number))
    if not latest:
        return None

    sources = web_research_engine.sources_from_json(latest.get("sources_json") or "[]")
    status = str(latest.get("status") or "")
    lang = i18n.current_lang(st)
    approved = bool(int(latest.get("approved_by_teacher") or 0))
    labels = {
        "ar": {
            "title": "نتائج البحث ومراجعة المصادر",
            "status": "الحالة",
            "provider": "خدمة البحث",
            "count": "المصادر",
            "latency": "المدة",
            "instruction": "راجع ملخص البحث وسجل المصادر. عند الاطمئنان إلى جودتها، اعتمد الحزمة للانتقال تلقائيًا إلى تركيب الأدلة.",
            "approve": "اعتماد المصادر والانتقال إلى تركيب الأدلة",
            "approved": "تم اعتماد حزمة البحث الأساسية.",
            "download": "تنزيل حزمة البحث JSON",
        },
        "fr": {
            "title": "Résultats et révision des sources",
            "status": "État",
            "provider": "Service",
            "count": "Sources",
            "latency": "Durée",
            "instruction": "Révisez les résultats et les sources, puis approuvez le dossier pour passer automatiquement aux preuves.",
            "approve": "Approuver les sources et continuer",
            "approved": "Le dossier de recherche est approuvé.",
            "download": "Télécharger le dossier JSON",
        },
        "en": {
            "title": "Research results and source review",
            "status": "Status",
            "provider": "Provider",
            "count": "Sources",
            "latency": "Duration",
            "instruction": "Review the report and sources, then approve the dossier to continue automatically to evidence synthesis.",
            "approve": "Approve sources and continue to evidence",
            "approved": "The canonical research dossier is approved.",
            "download": "Download research JSON",
        },
    }.get(lang)

    st.markdown(f"### {labels['title']}")
    st.caption(labels["instruction"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(labels["status"], status or "—")
    c2.metric(labels["provider"], f"{latest.get('provider') or '—'} / {latest.get('model') or '—'}")
    c3.metric(labels["count"], int(latest.get("source_count") or len(sources)))
    latency_ms = int(latest.get("latency_ms") or 0)
    c4.metric(labels["latency"], f"{latency_ms / 1000:.1f} s" if latency_ms else "—")

    if latest.get("diagnostic"):
        st.caption(str(latest.get("diagnostic")))

    tabs = st.tabs([u["research_report"], u["research_registry"], u["research_queries"]])
    with tabs[0]:
        report = str(latest.get("report_text") or "").strip()
        if report:
            _render_generation_markdown(report, "ar" if lang == "ar" else "en")
        else:
            st.info(u["research_missing"])
    with tabs[1]:
        if not sources:
            st.info(u["research_missing"])
        for source in sources:
            with st.container(border=True):
                if source.url:
                    st.markdown(f"**[{source.source_id}] [{source.title}]({source.url})**")
                else:
                    st.markdown(f"**[{source.source_id}] {source.title}**")
                st.caption(f"{source.domain} · {source.source_type} · {u['authority']}: {source.authority_level}/5")
                if source.snippet:
                    st.write(source.snippet)
    with tabs[2]:
        try:
            queries = json.loads(latest.get("query_plan_json") or "[]")
        except Exception:
            queries = []
        for query in queries:
            st.markdown(f"- {query}")

    payload = {
        "project_id": int(project_id),
        "phase_number": int(phase_number),
        "research_mode": latest.get("research_mode"),
        "provider": latest.get("provider"),
        "model": latest.get("model"),
        "status": latest.get("status"),
        "queries": queries,
        "sources": [source.__dict__ for source in sources],
        "report": latest.get("report_text"),
        "diagnostic": latest.get("diagnostic"),
    }
    st.download_button(
        labels["download"],
        json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"),
        file_name=f"project_{int(project_id)}_phase_{int(phase_number)}_research.json",
        mime="application/json",
        use_container_width=True,
        key=f"download_research_{int(latest.get('id') or 0)}",
    )

    if approved:
        st.success(labels["approved"])
    elif canonical_stage and status in {"completed", "needs_review"}:
        st.markdown("<span class='v6172-approval-marker' aria-hidden='true'></span>", unsafe_allow_html=True)
        if st.button(labels["approve"], type="primary", use_container_width=True, key=f"approve_research_{int(latest.get('id') or 0)}"):
            db.approve_teacher_research_run(int(latest["id"]), int(project_id), _current_teacher_username())
            st.session_state.teacher_flash_success = labels["approved"]
            st.session_state.teacher_workspace_section_pending = "evidence"
            st.rerun()
    return latest

def render_prompt_and_generation(project: Dict[str, Any]) -> None:
    """Render a single, guided sources-and-research workspace."""
    u = teacher_ui()
    p = _project_defaults(project)
    generation_phase = int(p.get("current_phase") or 1)
    research_phase = 1
    project_id = int(p["id"])
    lang = i18n.current_lang(st)

    research_status = web_research_engine.research_status()
    default_mode = str(research_status.get("default_mode") or "balanced").lower()
    if default_mode not in {"off", "quick", "balanced", "deep"}:
        default_mode = "balanced"
    if not research_status.get("enabled"):
        default_mode = "off"
    modes = ["off", "quick", "balanced", "deep"]
    mode_labels = {
        "off": u["research_mode_off"],
        "quick": u["research_mode_quick"],
        "balanced": u["research_mode_balanced"],
        "deep": u["research_mode_deep"],
    }

    latest_research = db.latest_usable_teacher_research(project_id, research_phase)
    approved_research = db.latest_approved_teacher_research(project_id, research_phase)
    stage_state = "approved" if approved_research else ("review" if latest_research else "search")
    stage_labels = {
        "ar": {
            "workspace": "مساحة العمل — المراجع والبحث",
            "intro": "هذه المرحلة بسيطة: اضبط البحث، شغّله مرة واحدة، راجع المصادر، ثم اعتمدها. بعد الاعتماد تنتقل المنصة تلقائيًا إلى تركيب الأدلة.",
            "s1": "إعداد البحث",
            "s2": "جمع المصادر",
            "s3": "المراجعة والاعتماد",
            "settings": "إعدادات البحث",
            "start": "بدء البحث وجمع المصادر",
            "refresh": "تحديث البحث والمصادر",
            "no_result": "لم تُنشأ حزمة بحث بعد. ابدأ البحث من الزر أعلاه.",
            "review_hint": "اكتمل البحث. راجع النتائج أدناه، ثم اضغط زر الاعتماد الموجود بعد سجل المصادر.",
            "approved": "تم اعتماد المصادر، وأصبحت مرحلة تركيب الأدلة متاحة.",
            "open_evidence": "فتح مرحلة تركيب الأدلة",
            "next_hint": "لن تحتاج إلى تشغيل البحث مرة أخرى إلا إذا أردت تحديث المصادر.",
        },
        "fr": {
            "workspace": "Espace de travail — Sources et recherche",
            "intro": "Réglez la recherche, lancez-la, révisez les sources, puis approuvez-les. La plateforme passera ensuite automatiquement aux preuves.",
            "s1": "Configurer",
            "s2": "Collecter",
            "s3": "Réviser et approuver",
            "settings": "Paramètres de recherche",
            "start": "Lancer la recherche et collecter les sources",
            "refresh": "Actualiser la recherche",
            "no_result": "Aucun dossier de recherche n’est encore disponible.",
            "review_hint": "La recherche est terminée. Révisez les résultats ci-dessous puis approuvez le dossier.",
            "approved": "Les sources sont approuvées; l’étape des preuves est ouverte.",
            "open_evidence": "Ouvrir la synthèse des preuves",
            "next_hint": "Relancez la recherche uniquement si vous souhaitez actualiser les sources.",
        },
        "en": {
            "workspace": "Workspace — Sources and research",
            "intro": "Configure the search, run it once, review the sources, and approve them. The platform then moves automatically to evidence synthesis.",
            "s1": "Configure",
            "s2": "Collect sources",
            "s3": "Review and approve",
            "settings": "Research settings",
            "start": "Start research and collect sources",
            "refresh": "Refresh research",
            "no_result": "No research dossier has been created yet.",
            "review_hint": "Research is complete. Review the results below, then approve the dossier.",
            "approved": "Sources are approved and evidence synthesis is available.",
            "open_evidence": "Open evidence synthesis",
            "next_hint": "Run research again only when you want to refresh the sources.",
        },
    }.get(lang)

    st.markdown(f"## {stage_labels['workspace']}")
    st.write(stage_labels["intro"])
    step_classes = {
        "search": ("active", "locked", "locked"),
        "review": ("done", "done", "active"),
        "approved": ("done", "done", "done"),
    }[stage_state]
    st.markdown(
        f"<div class='v6172-research-steps' dir='{i18n.direction(lang)}'>"
        f"<div class='v6172-research-step {step_classes[0]}'><span>1</span><strong>{escape(stage_labels['s1'])}</strong></div>"
        f"<div class='v6172-research-step {step_classes[1]}'><span>2</span><strong>{escape(stage_labels['s2'])}</strong></div>"
        f"<div class='v6172-research-step {step_classes[2]}'><span>3</span><strong>{escape(stage_labels['s3'])}</strong></div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    with st.expander(stage_labels["settings"], expanded=not bool(latest_research)):
        r1, r2 = st.columns([2, 1])
        with r1:
            research_mode = st.selectbox(
                u["research_mode"], modes, index=modes.index(default_mode),
                format_func=lambda value: mode_labels.get(value, value),
                key=f"teacher_research_mode_{project_id}_{research_phase}",
            )
        with r2:
            max_sources = st.slider(
                u["research_sources"], min_value=3, max_value=15, value=8, step=1,
                key=f"teacher_research_sources_{project_id}_{research_phase}",
                disabled=research_mode == "off",
            )
        with st.expander("Source policy / سياسة المصادر", expanded=False):
            preferred_domains_raw = st.text_input(
                u["preferred_domains"], value="",
                key=f"teacher_preferred_domains_{project_id}_{research_phase}",
                disabled=research_mode == "off",
            )
            excluded_domains_raw = st.text_input(
                u["excluded_domains"],
                value="wikipedia.org, pinterest.com, facebook.com, instagram.com, tiktok.com",
                key=f"teacher_excluded_domains_{project_id}_{research_phase}",
                disabled=research_mode == "off",
            )
        st.caption(u["research_cost"])

    # Inputs must exist even when the settings expander is closed.
    research_mode = st.session_state.get(f"teacher_research_mode_{project_id}_{research_phase}", default_mode)
    max_sources = int(st.session_state.get(f"teacher_research_sources_{project_id}_{research_phase}", 8))
    preferred_domains_raw = st.session_state.get(f"teacher_preferred_domains_{project_id}_{research_phase}", "")
    excluded_domains_raw = st.session_state.get(
        f"teacher_excluded_domains_{project_id}_{research_phase}",
        "wikipedia.org, pinterest.com, facebook.com, instagram.com, tiktok.com",
    )

    button_label = stage_labels["refresh"] if latest_research else stage_labels["start"]
    if st.button(
        button_label,
        type="secondary" if latest_research else "primary",
        use_container_width=True,
        key=f"run_teacher_research_{project_id}_{research_phase}",
        disabled=research_mode == "off" or not research_status.get("available"),
    ):
        try:
            spinner_text = {"ar": "تجمع 3alimnIA المصادر وتبني حزمة البحث...", "fr": "3alimnIA construit le dossier de recherche...", "en": "3alimnIA is building the research dossier..."}.get(lang)
            with st.spinner(spinner_text):
                research_run = educational_builder.run_project_research(
                    p, _current_teacher_username(), phase_number=research_phase,
                    research_mode=research_mode, max_sources=max_sources,
                    preferred_domains=_split_domain_input(preferred_domains_raw),
                    excluded_domains=_split_domain_input(excluded_domains_raw),
                )
            if bool(int(research_run.get("cache_fallback_used") or 0)):
                detail = str(research_run.get("refresh_diagnostic") or "").strip()
                st.session_state.teacher_flash_warning = u["research_cached_fallback"] + (f" {detail}" if detail else "")
            elif str(research_run.get("status") or "") in {"completed", "needs_review"}:
                st.session_state.teacher_flash_success = u["research_ready"]
            else:
                st.session_state.teacher_flash_error = str(research_run.get("diagnostic") or u["research_failed"])
        except Exception as exc:
            st.session_state.teacher_flash_error = f"{u['research_failed']} {exc}"
        st.rerun()

    if not latest_research:
        st.info(stage_labels["no_result"])
    elif not approved_research:
        st.info(stage_labels["review_hint"])
        _render_latest_research(project_id, research_phase, u, canonical_stage=True)
    else:
        st.success(stage_labels["approved"])
        st.caption(stage_labels["next_hint"])
        if st.button(stage_labels["open_evidence"], type="primary", use_container_width=True, key=f"continue_to_evidence_{project_id}"):
            _set_workspace_section("evidence")
        _render_latest_research(project_id, research_phase, u, canonical_stage=True)

    advanced_label = {
        "ar": "السجل التقني المتقدم للتوليد",
        "fr": "Journal technique avancé de génération",
        "en": "Advanced technical generation log",
    }.get(lang, "Advanced technical generation log")
    with st.expander(advanced_label, expanded=False):
        st.caption({
            "ar": "هذا القسم تقني ولا يلزم لإنجاز رحلة الأستاذ. استخدمه فقط لمراجعة المراحل الداخلية المتخصصة.",
            "fr": "Cette section est technique et n’est pas nécessaire au parcours enseignant.",
            "en": "This technical section is not required for the teacher journey.",
        }.get(lang))
        prompt = compile_project_prompt(p, generation_phase)
        st.session_state.teacher_last_prompt = prompt
        expand_prompt = bool(st.session_state.get("teacher_expand_prompt", False))
        st.success(u["prompt_ready"])
        status = content_generation_engine.provider_status()
        fallback_text = ""
        if status.get("ready_fallbacks"):
            fallback_text = " | fallback: " + ", ".join(status["ready_fallbacks"])
        st.info(f"{u['provider']}: {status['provider']} / {status['model']} — {'ready' if status['available'] else 'prompt export only'}{fallback_text}")
        budget = content_generation_engine.prompt_budget_info(prompt, educational_builder.PHASE_MAX_TOKENS.get(generation_phase, 3600))
        compacted_label = u["prompt_compacted"] if budget.get("compacted") else ""
        st.caption(u["prompt_budget"].format(runtime=budget.get("estimated_runtime_tokens", 0), original=budget.get("estimated_original_tokens", 0), output=budget.get("max_output_tokens", 0), compacted=compacted_label))
        st.caption(f"{u['phase_only']} · {generation_phase}. {PHASES[generation_phase]}")
        if st.button(u["rebuild_prompt"], use_container_width=True, key=f"rebuild_teacher_prompt_{project_id}_{generation_phase}"):
            st.session_state.teacher_last_prompt = compile_project_prompt(p, generation_phase)
            st.session_state.teacher_expand_prompt = True
            st.session_state.teacher_flash_success = u["prompt_ready"]
            st.rerun()
        with st.expander(u["prompt"], expanded=expand_prompt):
            st.code(prompt, language="markdown")
        if expand_prompt:
            st.session_state.teacher_expand_prompt = False
        safe_name = "_".join(str(p.get("project_name") or "project").split())
        st.download_button(u["download_prompt"], prompt.encode("utf-8"), file_name=f"{safe_name}_phase_{generation_phase}_prompt.md", mime="text/markdown", use_container_width=True)
        project_json = json.dumps(p, ensure_ascii=False, indent=2, default=str)
        st.download_button(u["download_project"], project_json.encode("utf-8"), file_name=f"{safe_name}_project.json", mime="application/json", use_container_width=True)
        _render_latest_generation(project_id, u, str(p.get("primary_language_code") or "en"))
        if st.button(u["generate"], type="primary", use_container_width=True, key=f"generate_teacher_phase_{project_id}_{generation_phase}"):
            try:
                with st.spinner(f"3alimnIA is generating technical phase {generation_phase}: {PHASES[generation_phase]}..."):
                    outcome = educational_builder.generate_project_phase(
                        p, _current_teacher_username(), phase_number=generation_phase,
                        research_mode=research_mode, max_research_sources=max_sources,
                        preferred_domains=_split_domain_input(preferred_domains_raw),
                        excluded_domains=_split_domain_input(excluded_domains_raw), force_research=False,
                    )
                st.session_state.teacher_last_response = outcome.response
                if outcome.status == "completed":
                    st.session_state.teacher_flash_success = f"{u['generated']} {generation_phase}/{len(PHASES)} — {outcome.provider}/{outcome.model}."
                elif outcome.status == "needs_review":
                    st.session_state.teacher_flash_warning = f"{u['needs_review']} {outcome.diagnostic}"
                elif outcome.status == "not_configured":
                    st.session_state.teacher_flash_warning = outcome.diagnostic
                else:
                    st.session_state.teacher_flash_error = outcome.diagnostic or u["generation_failed"]
            except Exception as exc:
                st.session_state.teacher_flash_error = f"{u['generation_failed']} {exc}"
            st.rerun()

def render_evidence_synthesis(project: Dict[str, Any]) -> None:
    """Render the V6.13 source-scoring and evidence-card review workspace."""
    u = teacher_ui()
    project_id = int(project["id"])
    phase_number = 1
    cfg = evidence_synthesis_engine.evidence_status()
    lang = i18n.current_lang(st)

    st.markdown(f"## {u['evidence_panel']}")
    st.write(u["evidence_intro"])
    st.caption({
        "ar": "تُبنى هنا حزمة الأدلة الأساسية للمقرر من حزمة البحث المعتمدة. المراحل التقنية الأخرى محفوظة في السجل المتقدم ولا تغيّر هذا التسلسل.",
        "fr": "Le dossier de preuves principal est construit à partir de la recherche approuvée.",
        "en": "The canonical course evidence bundle is built from the approved research dossier.",
    }.get(lang, "The canonical evidence bundle is built from approved research."))
    if cfg.get("require_teacher_approval"):
        st.info(u["evidence_strict_gate"])

    latest_research = db.latest_approved_teacher_research(project_id, phase_number)
    col1, col2 = st.columns(2)
    with col1:
        max_cards = st.slider(
            u["evidence_cards"],
            min_value=4,
            max_value=24,
            value=int(cfg.get("max_cards") or 12),
            key=f"teacher_evidence_max_cards_{project_id}_{phase_number}",
        )
    with col2:
        max_concepts = st.slider(
            u["evidence_concepts"],
            min_value=3,
            max_value=20,
            value=int(cfg.get("max_concepts") or 10),
            key=f"teacher_evidence_max_concepts_{project_id}_{phase_number}",
        )

    latest_bundle = db.latest_teacher_evidence(project_id, int(phase_number), approved_only=False)
    button_label = u["evidence_refresh"] if latest_bundle else u["evidence_run"]
    if st.button(
        button_label,
        type="primary",
        use_container_width=True,
        disabled=not bool(latest_research) or not bool(cfg.get("enabled")),
        key=f"teacher_run_evidence_{project_id}_{phase_number}",
    ):
        try:
            with st.spinner("3alimnIA is synthesizing the canonical course evidence bundle..."):
                evidence_synthesis_engine.synthesize_and_persist(
                    project,
                    _current_teacher_username(),
                    phase_number=int(phase_number),
                    research_run=latest_research,
                    max_cards=int(max_cards),
                    max_concepts=int(max_concepts),
                )
            st.session_state.teacher_flash_success = u["evidence_saved"]
        except Exception as exc:
            st.session_state.teacher_flash_error = str(exc)
        st.rerun()

    if not latest_research:
        st.warning({
            "ar": "اعتمد حزمة البحث الأساسية أولًا لفتح تركيب الأدلة.",
            "fr": "Approuvez d’abord le dossier de recherche principal.",
            "en": "Approve the canonical research dossier before evidence synthesis.",
        }.get(lang, u["evidence_missing_research"]))
    if not cfg.get("enabled"):
        st.warning("ENABLE_EVIDENCE_SYNTHESIS is disabled in Streamlit secrets.")

    bundle = db.latest_teacher_evidence(project_id, int(phase_number), approved_only=False)
    if not bundle:
        st.info(u["evidence_missing"])
        return

    quality = bundle.get("quality") or {}
    sources = bundle.get("sources") or []
    cards = bundle.get("evidence_cards") or []
    concepts = bundle.get("concepts") or []
    approved = bool(int(bundle.get("approved_by_teacher") or 0))

    st.markdown(f"### {u['evidence_latest']} — " + {"ar": "الحزمة الأساسية للمقرر", "fr": "Dossier principal", "en": "Canonical course bundle"}.get(lang, "Canonical course bundle"))
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(u["evidence_readiness"], f"{float(quality.get('readiness_score') or 0):.0%}")
    m2.metric(u["evidence_approved_sources"], int(quality.get("approved_source_count") or 0))
    m3.metric(u["evidence_cards"], len(cards))
    m4.metric(u["evidence_concepts"], len(concepts))
    status_text = str(bundle.get("status") or "unknown")
    st.caption(
        f"{u['evidence_status']}: {status_text} · "
        f"{bundle.get('provider') or 'unknown'} / {bundle.get('model') or 'unknown'} · "
        f"{int(bundle.get('latency_ms') or 0) / 1000:.1f}s"
    )
    if approved:
        st.success(u["evidence_approved"])
    elif status_text == "needs_review":
        st.warning(u["needs_review"])

    tabs = st.tabs(
        [
            u["evidence_sources_tab"],
            u["evidence_cards_tab"],
            u["evidence_concepts_tab"],
            u["evidence_quality_tab"],
        ]
    )
    with tabs[0]:
        source_rows = []
        for item in sources:
            source_rows.append(
                {
                    "ID": item.get("source_id"),
                    "Title": item.get("title"),
                    "Domain": item.get("domain"),
                    u["evidence_source_score"]: round(float(item.get("composite_score") or 0), 3),
                    "Authority": round(float(item.get("authority_score") or 0), 3),
                    "Relevance": round(float(item.get("relevance_score") or 0), 3),
                    "Pedagogy": round(float(item.get("pedagogical_score") or 0), 3),
                    "Licence": round(float(item.get("license_score") or 0), 3),
                    u["evidence_status"]: item.get("status"),
                    "URL": item.get("url"),
                }
            )
        if source_rows:
            st.dataframe(pd.DataFrame(source_rows), use_container_width=True, hide_index=True)
        else:
            st.info(u["evidence_missing"])
    with tabs[1]:
        for card in cards:
            title = f"{card.get('evidence_id')} · {card.get('confidence', 'moderate')} · {', '.join(card.get('source_ids') or [])}"
            with st.expander(title, expanded=False):
                st.markdown(f"**{card.get('claim') or card.get('claim_text') or ''}**")
                if card.get("evidence_excerpt"):
                    st.write(card.get("evidence_excerpt"))
                st.caption(" · ".join(card.get("intended_use") or []))
    with tabs[2]:
        for concept in concepts:
            with st.container(border=True):
                st.markdown(f"**{concept.get('concept_id')} · {concept.get('name') or concept.get('concept_name')}**")
                st.write(concept.get("description") or "")
                prerequisites = concept.get("prerequisites") or []
                st.caption(
                    f"Prerequisites: {', '.join(prerequisites) if prerequisites else '—'} · "
                    f"Sources: {', '.join(concept.get('source_ids') or [])} · "
                    f"Difficulty: {concept.get('difficulty') or 'introductory'}"
                )
    with tabs[3]:
        warnings = quality.get("warnings") or []
        if warnings:
            st.markdown(f"**{u['evidence_warnings']}**")
            for warning in warnings:
                st.markdown(f"- {warning}")
        else:
            st.success("Quality gate passed without automatic warnings.")
        if bundle.get("diagnostic"):
            st.caption(str(bundle.get("diagnostic")))
        st.json(quality)

    payload = {
        "run": {key: value for key, value in bundle.items() if key not in {"sources", "evidence_cards", "concepts"}},
        "sources": sources,
        "evidence_cards": cards,
        "concepts": concepts,
        "quality": quality,
    }
    st.download_button(
        u["evidence_download"],
        json.dumps(payload, ensure_ascii=False, indent=2, default=str).encode("utf-8"),
        file_name=f"project_{project_id}_phase_{int(phase_number)}_evidence.json",
        mime="application/json",
        use_container_width=True,
        key=f"download_evidence_{int(bundle.get('id') or 0)}",
    )
    if not approved and status_text != "error":
        if st.button(
            u["evidence_approve"],
            type="primary",
            use_container_width=True,
            key=f"approve_evidence_{int(bundle.get('id') or 0)}",
        ):
            try:
                db.approve_teacher_evidence_run(
                    int(bundle["id"]),
                    project_id,
                    _current_teacher_username(),
                )
                st.session_state.teacher_flash_success = u["evidence_approved"]
                st.session_state.teacher_workspace_section_pending = "blueprint"
            except Exception as exc:
                st.session_state.teacher_flash_error = str(exc)
            st.rerun()




def _blueprint_editor_copy(lang: str) -> Dict[str, str]:
    copies = {
        "ar": {
            "editor": "محرر المخطط", "versions": "الإصدارات والسجل", "disabled": "ENABLE_BLUEPRINT_EDITOR غير مفعّل في Streamlit Secrets.",
            "draft_note": "تُحفظ التعديلات أولًا كمسودة داخل الجلسة. اضغط حفظ إصدار جديد لتثبيتها في قاعدة البيانات. أي إصدار جديد يلغي اعتماد الإصدار السابق حتى يراجعه الأستاذ.",
            "draft_quality": "جودة المسودة", "reset": "إلغاء التعديلات وإعادة تحميل أحدث إصدار", "summary": "ملخص التعديلات",
            "save": "حفظ إصدار جديد", "saved": "تم حفظ إصدار جديد للمخطط.", "no_changes": "لا توجد تغييرات مقارنة بأحدث إصدار.",
            "units": "تحرير الوحدات", "lessons": "تحرير الدروس", "outcomes": "تحرير أهداف التعلم", "add_unit": "إضافة وحدة",
            "add_lesson": "إضافة درس", "add_outcome": "إضافة هدف تعلم", "title": "العنوان", "description": "الوصف",
            "duration": "المدة بالدقائق", "concepts": "معرّفات المفاهيم مفصولة بفواصل", "sources": "معرّفات المصادر مفصولة بفواصل",
            "prerequisites": "المتطلبات السابقة", "misconceptions": "المفاهيم الخاطئة الشائعة", "unit": "الوحدة", "lesson": "الدرس",
            "bloom": "مستوى Bloom", "verb": "الفعل القابل للقياس", "object": "موضوع الهدف", "condition": "شرط الأداء",
            "criterion": "معيار النجاح", "update": "حفظ التعديل في المسودة", "up": "نقل إلى أعلى", "down": "نقل إلى أسفل",
            "delete": "حذف", "confirm_cascade": "أؤكد حذف الوحدة وكل دروسها وأهدافها", "restore": "استعادة هذا الإصدار كإصدار جديد",
            "restore_summary": "سبب الاستعادة", "compare": "مقارنة مع أحدث إصدار", "audit": "سجل العمليات", "history": "تاريخ الإصدارات",
            "approved_warning": "هذا الإصدار معتمد حاليًا. حفظ تعديل جديد سيوقف اعتماده حتى اعتماد الإصدار الجديد.",
        },
        "fr": {
            "editor": "Éditeur du plan", "versions": "Versions et journal", "disabled": "ENABLE_BLUEPRINT_EDITOR est désactivé dans Streamlit Secrets.",
            "draft_note": "Les modifications restent dans un brouillon de session jusqu’à l’enregistrement d’une nouvelle version. Une nouvelle version invalide l’approbation précédente.",
            "draft_quality": "Qualité du brouillon", "reset": "Annuler et recharger la dernière version", "summary": "Résumé des modifications",
            "save": "Enregistrer une nouvelle version", "saved": "Nouvelle version enregistrée.", "no_changes": "Aucune modification par rapport à la dernière version.",
            "units": "Modifier les unités", "lessons": "Modifier les leçons", "outcomes": "Modifier les objectifs", "add_unit": "Ajouter une unité",
            "add_lesson": "Ajouter une leçon", "add_outcome": "Ajouter un objectif", "title": "Titre", "description": "Description",
            "duration": "Durée en minutes", "concepts": "Identifiants de concepts séparés par des virgules", "sources": "Identifiants de sources séparés par des virgules",
            "prerequisites": "Prérequis", "misconceptions": "Conceptions erronées", "unit": "Unité", "lesson": "Leçon",
            "bloom": "Niveau de Bloom", "verb": "Verbe mesurable", "object": "Objet de l’objectif", "condition": "Condition",
            "criterion": "Critère de réussite", "update": "Mettre à jour le brouillon", "up": "Monter", "down": "Descendre",
            "delete": "Supprimer", "confirm_cascade": "Je confirme la suppression de l’unité et de toutes ses leçons", "restore": "Restaurer comme nouvelle version",
            "restore_summary": "Motif de restauration", "compare": "Comparer à la dernière version", "audit": "Journal des opérations", "history": "Historique des versions",
            "approved_warning": "Cette version est approuvée. Une nouvelle modification annulera son approbation jusqu’à une nouvelle validation.",
        },
        "en": {
            "editor": "Blueprint editor", "versions": "Versions and audit", "disabled": "ENABLE_BLUEPRINT_EDITOR is disabled in Streamlit Secrets.",
            "draft_note": "Changes remain in a session draft until a new immutable version is saved. Saving a version invalidates the previous approval until the teacher approves the new version.",
            "draft_quality": "Draft quality", "reset": "Discard changes and reload latest", "summary": "Change summary",
            "save": "Save new version", "saved": "A new blueprint version was saved.", "no_changes": "No changes compared with the latest version.",
            "units": "Edit units", "lessons": "Edit lessons", "outcomes": "Edit learning outcomes", "add_unit": "Add unit",
            "add_lesson": "Add lesson", "add_outcome": "Add learning outcome", "title": "Title", "description": "Description",
            "duration": "Duration in minutes", "concepts": "Comma-separated concept IDs", "sources": "Comma-separated source IDs",
            "prerequisites": "Prerequisites", "misconceptions": "Misconceptions", "unit": "Unit", "lesson": "Lesson",
            "bloom": "Bloom level", "verb": "Measurable verb", "object": "Outcome object", "condition": "Performance condition",
            "criterion": "Success criterion", "update": "Update session draft", "up": "Move up", "down": "Move down",
            "delete": "Delete", "confirm_cascade": "I confirm deleting the unit and all its lessons", "restore": "Restore as a new version",
            "restore_summary": "Restore reason", "compare": "Compare with latest", "audit": "Audit trail", "history": "Version history",
            "approved_warning": "This version is currently approved. Saving a new edit will invalidate approval until the new version is reviewed.",
        },
    }
    return copies.get(lang, copies["en"])


def _set_blueprint_draft(project_id: int, draft: Dict[str, Any]) -> None:
    st.session_state[f"blueprint_editor_draft_{project_id}"] = lesson_blueprint_engine.normalize_blueprint(draft)
    st.session_state[f"blueprint_editor_nonce_{project_id}"] = int(st.session_state.get(f"blueprint_editor_nonce_{project_id}", 0)) + 1


def render_blueprint_editor(project: Dict[str, Any], bundle: Dict[str, Any], lang: str) -> None:
    copy = _blueprint_editor_copy(lang)
    cfg = lesson_blueprint_engine.blueprint_status()
    project_id = int(project["id"])
    if not cfg.get("editor_enabled"):
        st.warning(copy["disabled"])
        return
    required_editor_api = (
        "prepare_editor_draft", "normalize_blueprint", "recompute_blueprint_quality",
        "compare_blueprints", "add_unit", "update_unit", "move_unit", "delete_unit",
        "add_lesson", "update_lesson", "move_lesson", "delete_lesson",
        "add_outcome", "update_outcome", "delete_outcome", "save_manual_revision",
    )
    missing_editor_api = [name for name in required_editor_api if not callable(getattr(lesson_blueprint_engine, name, None))]
    if missing_editor_api:
        ui_stability.render_error_card(
            "Blueprint editor API is incomplete: " + ", ".join(missing_editor_api),
            lang=lang,
        )
        return
    st.info(copy["draft_note"])
    if bool(int(bundle.get("approved_by_teacher") or 0)):
        st.warning(copy["approved_warning"])

    draft_key = f"blueprint_editor_draft_{project_id}"
    source_key = f"blueprint_editor_source_{project_id}"
    if draft_key not in st.session_state or int(st.session_state.get(source_key, 0) or 0) != int(bundle.get("id") or 0):
        st.session_state[draft_key] = lesson_blueprint_engine.prepare_editor_draft(bundle)
        st.session_state[source_key] = int(bundle.get("id") or 0)
    draft = st.session_state[draft_key]
    quality = lesson_blueprint_engine.recompute_blueprint_quality(draft)
    comparison = lesson_blueprint_engine.compare_blueprints(bundle.get("blueprint") or {}, draft)
    changed = bool(comparison.get("changed"))

    q1, q2, q3, q4 = st.columns(4)
    q1.metric(copy["draft_quality"], f"{float(quality.get('readiness_score') or 0):.0%}")
    q2.metric(copy["units"], len(draft.get("units") or []))
    q3.metric(copy["lessons"], len(draft.get("lessons") or []))
    q4.metric(copy["outcomes"], len(draft.get("outcomes") or []))
    if quality.get("warnings"):
        with st.expander(copy["draft_quality"]):
            for warning in quality.get("warnings") or []:
                st.markdown(f"- {warning}")

    with st.expander(copy["add_unit"]):
        with st.form(f"add_unit_form_{project_id}", clear_on_submit=True):
            add_title = st.text_input(copy["title"])
            add_desc = st.text_area(copy["description"])
            if st.form_submit_button(copy["add_unit"], use_container_width=True):
                try:
                    _set_blueprint_draft(project_id, lesson_blueprint_engine.add_unit(draft, add_title, add_desc))
                    st.rerun()
                except Exception as exc:
                    ui_stability.render_error_card(exc, lang=i18n.current_lang(st))

    units = draft.get("units") or []
    unit_options = {f"{item.get('unit_id')} · {item.get('title')}": str(item.get("unit_id")) for item in units}
    if unit_options:
        st.markdown(f"### {copy['units']}")
        selected_unit_label = st.selectbox(copy["unit"], list(unit_options), key=f"edit_unit_select_{project_id}")
        selected_unit_id = unit_options[selected_unit_label]
        selected_unit = next(item for item in units if str(item.get("unit_id")) == selected_unit_id)
        with st.form(f"edit_unit_form_{project_id}_{selected_unit_id}"):
            unit_title = st.text_input(copy["title"], value=str(selected_unit.get("title") or ""))
            unit_desc = st.text_area(copy["description"], value=str(selected_unit.get("description") or ""))
            if st.form_submit_button(copy["update"], use_container_width=True):
                _set_blueprint_draft(project_id, lesson_blueprint_engine.update_unit(draft, selected_unit_id, title=unit_title, description=unit_desc))
                st.rerun()
        c1, c2, c3 = st.columns(3)
        if c1.button(copy["up"], key=f"unit_up_{project_id}_{selected_unit_id}", use_container_width=True):
            _set_blueprint_draft(project_id, lesson_blueprint_engine.move_unit(draft, selected_unit_id, -1)); st.rerun()
        if c2.button(copy["down"], key=f"unit_down_{project_id}_{selected_unit_id}", use_container_width=True):
            _set_blueprint_draft(project_id, lesson_blueprint_engine.move_unit(draft, selected_unit_id, 1)); st.rerun()
        confirm = st.checkbox(copy["confirm_cascade"], key=f"confirm_unit_delete_{project_id}_{selected_unit_id}")
        if c3.button(copy["delete"], key=f"unit_delete_{project_id}_{selected_unit_id}", disabled=not confirm, use_container_width=True):
            _set_blueprint_draft(project_id, lesson_blueprint_engine.delete_unit(draft, selected_unit_id, cascade=True)); st.rerun()

    units = st.session_state[draft_key].get("units") or []
    unit_ids = [str(item.get("unit_id")) for item in units]
    if unit_ids:
        with st.expander(copy["add_lesson"]):
            with st.form(f"add_lesson_form_{project_id}", clear_on_submit=True):
                lesson_unit = st.selectbox(copy["unit"], unit_ids)
                lesson_title = st.text_input(copy["title"])
                lesson_duration = st.number_input(copy["duration"], min_value=5, max_value=600, value=45, step=5)
                lesson_concepts = st.text_input(copy["concepts"])
                lesson_sources = st.text_input(copy["sources"])
                if st.form_submit_button(copy["add_lesson"], use_container_width=True):
                    _set_blueprint_draft(project_id, lesson_blueprint_engine.add_lesson(st.session_state[draft_key], unit_id=lesson_unit, title=lesson_title, duration_minutes=int(lesson_duration), concept_ids=lesson_concepts, source_ids=lesson_sources))
                    st.rerun()

    draft = st.session_state[draft_key]
    lessons = draft.get("lessons") or []
    lesson_options = {f"{item.get('lesson_id')} · {item.get('title')}": str(item.get("lesson_id")) for item in lessons}
    if lesson_options:
        st.markdown(f"### {copy['lessons']}")
        selected_lesson_label = st.selectbox(copy["lesson"], list(lesson_options), key=f"edit_lesson_select_{project_id}")
        selected_lesson_id = lesson_options[selected_lesson_label]
        selected_lesson = next(item for item in lessons if str(item.get("lesson_id")) == selected_lesson_id)
        with st.form(f"edit_lesson_form_{project_id}_{selected_lesson_id}"):
            current_unit = str(selected_lesson.get("unit_id") or "")
            edit_unit = st.selectbox(copy["unit"], unit_ids, index=max(0, unit_ids.index(current_unit)) if current_unit in unit_ids else 0)
            edit_title = st.text_input(copy["title"], value=str(selected_lesson.get("title") or ""))
            edit_duration = st.number_input(copy["duration"], min_value=5, max_value=600, value=int(selected_lesson.get("estimated_duration_minutes") or 45), step=5)
            edit_concepts = st.text_input(copy["concepts"], value=", ".join(selected_lesson.get("concept_ids") or []))
            edit_sources = st.text_input(copy["sources"], value=", ".join(selected_lesson.get("source_ids") or []))
            edit_prereq = st.text_input(copy["prerequisites"], value=", ".join(selected_lesson.get("prerequisites") or []))
            edit_mis = st.text_area(copy["misconceptions"], value=", ".join(selected_lesson.get("misconceptions") or []))
            if st.form_submit_button(copy["update"], use_container_width=True):
                _set_blueprint_draft(project_id, lesson_blueprint_engine.update_lesson(draft, selected_lesson_id, unit_id=edit_unit, title=edit_title, duration_minutes=int(edit_duration), concept_ids=edit_concepts, source_ids=edit_sources, prerequisites=edit_prereq, misconceptions=edit_mis))
                st.rerun()
        c1, c2, c3 = st.columns(3)
        if c1.button(copy["up"], key=f"lesson_up_{project_id}_{selected_lesson_id}", use_container_width=True):
            _set_blueprint_draft(project_id, lesson_blueprint_engine.move_lesson(draft, selected_lesson_id, -1)); st.rerun()
        if c2.button(copy["down"], key=f"lesson_down_{project_id}_{selected_lesson_id}", use_container_width=True):
            _set_blueprint_draft(project_id, lesson_blueprint_engine.move_lesson(draft, selected_lesson_id, 1)); st.rerun()
        if c3.button(copy["delete"], key=f"lesson_delete_{project_id}_{selected_lesson_id}", use_container_width=True):
            _set_blueprint_draft(project_id, lesson_blueprint_engine.delete_lesson(draft, selected_lesson_id)); st.rerun()

    draft = st.session_state[draft_key]
    lessons = draft.get("lessons") or []
    if lessons:
        with st.expander(copy["add_outcome"]):
            with st.form(f"add_outcome_form_{project_id}", clear_on_submit=True):
                outcome_lesson = st.selectbox(copy["lesson"], [str(item.get("lesson_id")) for item in lessons])
                outcome_bloom = st.selectbox(copy["bloom"], ["remember", "understand", "apply", "analyze", "evaluate", "create"], index=2)
                outcome_verb = st.text_input(copy["verb"])
                outcome_object = st.text_input(copy["object"])
                outcome_condition = st.text_input(copy["condition"])
                outcome_criterion = st.text_area(copy["criterion"])
                if st.form_submit_button(copy["add_outcome"], use_container_width=True):
                    _set_blueprint_draft(project_id, lesson_blueprint_engine.add_outcome(draft, lesson_id=outcome_lesson, bloom_level=outcome_bloom, verb=outcome_verb, object_text=outcome_object, condition=outcome_condition, success_criterion=outcome_criterion))
                    st.rerun()

    draft = st.session_state[draft_key]
    outcomes = draft.get("outcomes") or []
    outcome_options = {f"{item.get('outcome_id')} · {item.get('verb')} {item.get('object')}": str(item.get("outcome_id")) for item in outcomes}
    if outcome_options:
        st.markdown(f"### {copy['outcomes']}")
        selected_outcome_label = st.selectbox(copy["outcomes"], list(outcome_options), key=f"edit_outcome_select_{project_id}")
        selected_outcome_id = outcome_options[selected_outcome_label]
        selected_outcome = next(item for item in outcomes if str(item.get("outcome_id")) == selected_outcome_id)
        with st.form(f"edit_outcome_form_{project_id}_{selected_outcome_id}"):
            bloom_values = ["remember", "understand", "apply", "analyze", "evaluate", "create"]
            current_bloom = str(selected_outcome.get("bloom_level") or "apply")
            edit_bloom = st.selectbox(copy["bloom"], bloom_values, index=bloom_values.index(current_bloom) if current_bloom in bloom_values else 2)
            edit_verb = st.text_input(copy["verb"], value=str(selected_outcome.get("verb") or ""))
            edit_object = st.text_input(copy["object"], value=str(selected_outcome.get("object") or ""))
            edit_condition = st.text_input(copy["condition"], value=str(selected_outcome.get("condition") or ""))
            edit_criterion = st.text_area(copy["criterion"], value=str(selected_outcome.get("success_criterion") or ""))
            if st.form_submit_button(copy["update"], use_container_width=True):
                _set_blueprint_draft(project_id, lesson_blueprint_engine.update_outcome(draft, selected_outcome_id, bloom_level=edit_bloom, verb=edit_verb, object_text=edit_object, condition=edit_condition, success_criterion=edit_criterion))
                st.rerun()
        if st.button(copy["delete"], key=f"outcome_delete_{project_id}_{selected_outcome_id}", use_container_width=True):
            _set_blueprint_draft(project_id, lesson_blueprint_engine.delete_outcome(draft, selected_outcome_id)); st.rerun()

    st.divider()
    change_summary = st.text_area(copy["summary"], key=f"blueprint_change_summary_{project_id}")
    b1, b2 = st.columns(2)
    if b1.button(copy["reset"], use_container_width=True, key=f"blueprint_reset_{project_id}"):
        st.session_state[draft_key] = lesson_blueprint_engine.prepare_editor_draft(bundle)
        st.session_state[source_key] = int(bundle.get("id") or 0)
        st.rerun()
    if b2.button(copy["save"], type="primary", use_container_width=True, disabled=not changed, key=f"blueprint_save_revision_{project_id}"):
        try:
            saved = lesson_blueprint_engine.save_manual_revision(
                project,
                _current_teacher_username(),
                base_run_id=int(bundle["id"]),
                edited_blueprint=st.session_state[draft_key],
                change_summary=change_summary,
            )
            st.session_state[source_key] = int(saved.get("id") or 0)
            st.session_state[draft_key] = lesson_blueprint_engine.prepare_editor_draft(saved)
            st.session_state.teacher_flash_success = copy["saved"]
        except Exception as exc:
            st.session_state.teacher_flash_error = str(exc)
        st.rerun()
    if not changed:
        st.caption(copy["no_changes"])


def render_blueprint_versions(project: Dict[str, Any], current_bundle: Dict[str, Any], lang: str) -> None:
    copy = _blueprint_editor_copy(lang)
    project_id = int(project["id"])
    versions = db.teacher_blueprint_versions_df(project_id)
    st.markdown(f"### {copy['history']}")
    if versions.empty:
        st.info(copy["no_changes"])
        return
    display = versions.copy()
    display["approved"] = display["approved_by_teacher"].fillna(0).astype(int).map({1: "✓", 0: ""})
    columns = [col for col in ["version_number", "revision_type", "status", "approved", "unit_count", "lesson_count", "outcome_count", "edited_by", "change_summary", "created_at"] if col in display.columns]
    st.dataframe(display[columns], use_container_width=True, hide_index=True)
    options = {
        f"v{int(row.get('version_number') or 1)} · #{int(row['id'])} · {row.get('revision_type') or 'generated'}": int(row["id"])
        for _, row in versions.iterrows()
    }
    selected_label = st.selectbox(copy["history"], list(options), key=f"blueprint_version_select_{project_id}")
    selected = db.teacher_blueprint_bundle(options[selected_label]) or {}
    diff = lesson_blueprint_engine.compare_blueprints(selected.get("blueprint") or {}, current_bundle.get("blueprint") or {})
    with st.expander(copy["compare"], expanded=True):
        st.json(diff)
    restore_summary = st.text_input(copy["restore_summary"], key=f"blueprint_restore_summary_{project_id}")
    if int(selected.get("id") or 0) != int(current_bundle.get("id") or 0):
        if st.button(copy["restore"], type="primary", use_container_width=True, key=f"blueprint_restore_{project_id}_{int(selected.get('id') or 0)}"):
            try:
                db.restore_teacher_blueprint_version(project_id=project_id, source_run_id=int(selected["id"]), teacher_username=_current_teacher_username(), change_summary=restore_summary)
                st.session_state.pop(f"blueprint_editor_draft_{project_id}", None)
                st.session_state.teacher_flash_success = copy["restore"]
            except Exception as exc:
                st.session_state.teacher_flash_error = str(exc)
            st.rerun()
    st.markdown(f"### {copy['audit']}")
    audit = db.teacher_blueprint_audit_df(project_id)
    if not audit.empty:
        st.dataframe(audit[[col for col in ["action", "actor_username", "summary", "blueprint_run_id", "parent_run_id", "created_at"] if col in audit.columns]], use_container_width=True, hide_index=True)


def _runtime_contract_ready(scope: str, lang: str) -> bool:
    report = workflow_runtime_contracts.check_contract(scope)
    if report.get("ok"):
        return True
    translations = {
        "ar": "تعذر فتح هذه المساحة لأن بعض مكونات التشغيل غير متوافقة: ",
        "fr": "Cet espace ne peut pas être ouvert car certains composants sont incompatibles : ",
        "en": "This workspace cannot open because runtime components are incompatible: ",
    }
    ui_stability.render_error_card(
        translations.get(lang, translations["en"]) + ", ".join(str(item) for item in report.get("missing") or []),
        lang=lang,
    )
    return False


def _render_blueprint_stage_flow(*, built: bool, approved: bool, lang: str) -> None:
    copy = {
        "ar": [("إنشاء", "تحويل الأدلة إلى مخطط"), ("مراجعة", "فحص الوحدات والدروس"), ("اعتماد", "تثبيت النسخة المعتمدة"), ("الدروس", "بدء بناء كتل الدروس")],
        "fr": [("Créer", "Transformer les preuves"), ("Réviser", "Vérifier unités et leçons"), ("Approuver", "Valider la version"), ("Leçons", "Construire les blocs")],
        "en": [("Build", "Convert evidence"), ("Review", "Check units and lessons"), ("Approve", "Lock the approved version"), ("Lessons", "Build lesson blocks")],
    }.get(lang, [])
    states = ["done" if built else "active", "done" if approved else ("active" if built else "locked"), "done" if approved else "locked", "active" if approved else "locked"]
    pieces = []
    for index, ((title, desc), state) in enumerate(zip(copy, states), start=1):
        marker = "✓" if state == "done" else str(index)
        pieces.append(
            f"<div class='v6183-flow-step v6183-flow-{state}'><span>{marker}</span><div><strong>{escape(title)}</strong><small>{escape(desc)}</small></div></div>"
        )
    st.markdown("<div class='v6183-stage-flow' dir='%s'>%s</div>" % ("rtl" if lang == "ar" else "ltr", "".join(pieces)), unsafe_allow_html=True)


def render_lesson_blueprint(project: Dict[str, Any]) -> None:
    """Render a guided evidence-to-blueprint review and approval workspace."""
    lang = i18n.current_lang(st)
    labels = {
        "ar": {
            "title": "مخطط المقرر والدروس", "intro": "حوّل الأدلة المعتمدة إلى بنية واضحة للمقرر، ثم راجعها واعتمدها قبل بناء الدروس.",
            "evidence": "حزمة الأدلة المعتمدة", "units": "الحد الأقصى للوحدات", "lessons": "الحد الأقصى للدروس",
            "build": "إنشاء مخطط المقرر", "rebuild": "إعادة بناء المخطط", "missing": "اعتمد حزمة أدلة أولًا قبل إنشاء المخطط.",
            "disabled": "ENABLE_LESSON_BLUEPRINT غير مفعّل في Streamlit Secrets.", "readiness": "درجة الجاهزية",
            "concepts": "المفاهيم", "course": "بنية المقرر", "outcomes": "الأهداف والمحاذاة", "quality": "بوابة الجودة",
            "approve": "اعتماد المخطط والانتقال إلى بناء الدروس", "approved": "المخطط معتمد ويقيد عملية بناء الدروس.",
            "open_lessons": "الانتقال إلى بناء الدروس", "download": "تنزيل المخطط بصيغة JSON", "warnings": "ملاحظات الجودة",
            "editor": "محرر المخطط", "versions": "الإصدارات والسجل", "next_review": "الخطوة التالية: راجع الوحدات والدروس والأهداف، ثم اعتمد هذه النسخة.",
            "next_lessons": "المخطط معتمد. يمكنك الآن بدء بناء أجزاء الدروس بالترتيب.", "version": "الإصدار", "status": "الحالة",
        },
        "fr": {
            "title": "Plan du cours et des leçons", "intro": "Transformez les preuves approuvées en une structure claire, révisez-la puis approuvez-la avant de construire les leçons.",
            "evidence": "Dossier de preuves approuvé", "units": "Nombre maximal d’unités", "lessons": "Nombre maximal de leçons",
            "build": "Construire le plan", "rebuild": "Reconstruire le plan", "missing": "Approuvez d’abord un dossier de preuves.",
            "disabled": "ENABLE_LESSON_BLUEPRINT est désactivé.", "readiness": "Préparation", "concepts": "Concepts", "course": "Structure du cours",
            "outcomes": "Objectifs et alignement", "quality": "Contrôle qualité", "approve": "Approuver et passer aux leçons",
            "approved": "Le plan est approuvé et contraint la construction des leçons.", "open_lessons": "Ouvrir la construction des leçons",
            "download": "Télécharger le plan JSON", "warnings": "Alertes qualité", "editor": "Éditeur du plan", "versions": "Versions et journal",
            "next_review": "Étape suivante : vérifiez les unités, leçons et objectifs, puis approuvez cette version.",
            "next_lessons": "Le plan est approuvé. Vous pouvez maintenant construire les blocs de leçon.", "version": "Version", "status": "Statut",
        },
        "en": {
            "title": "Course and lesson blueprint", "intro": "Convert approved evidence into a clear course structure, review it, and approve it before building lessons.",
            "evidence": "Approved evidence bundle", "units": "Maximum units", "lessons": "Maximum lessons", "build": "Build course blueprint",
            "rebuild": "Rebuild blueprint", "missing": "Approve an evidence bundle before building the blueprint.",
            "disabled": "ENABLE_LESSON_BLUEPRINT is disabled.", "readiness": "Readiness", "concepts": "Concepts", "course": "Course structure",
            "outcomes": "Outcomes and alignment", "quality": "Quality gate", "approve": "Approve and continue to lesson production",
            "approved": "The blueprint is approved and constrains lesson production.", "open_lessons": "Open lesson production",
            "download": "Download blueprint JSON", "warnings": "Quality warnings", "editor": "Blueprint editor", "versions": "Versions and audit",
            "next_review": "Next: review the units, lessons, and outcomes, then approve this version.",
            "next_lessons": "The blueprint is approved. You can now build lesson blocks in sequence.", "version": "Version", "status": "Status",
        },
    }.get(lang, {})

    global_ui.render_section_header(labels["title"], labels["intro"], lang=lang, eyebrow="04")
    if not _runtime_contract_ready("blueprint", lang):
        return
    cfg = lesson_blueprint_engine.blueprint_status()
    project_id = int(project["id"])
    if not cfg.get("enabled"):
        global_ui.render_inline_notice(labels["disabled"], "", lang=lang, tone="warning")
        return

    evidence_df = db.teacher_evidence_runs_df(project_id)
    approved_rows = []
    if not evidence_df.empty:
        for _, row in evidence_df.iterrows():
            if int(row.get("approved_by_teacher") or 0) == 1 and int(row.get("phase_number") or 1) == 1:
                approved_rows.append(row.to_dict())
    evidence_options = {
        f"#{int(item['id'])} — Canonical evidence bundle — {item.get('status') or 'approved'}": int(item["id"])
        for item in approved_rows
    }
    selected_evidence = None
    if evidence_options:
        selected_label = st.selectbox(labels["evidence"], list(evidence_options.keys()), key=f"blueprint_evidence_{project_id}")
        selected_evidence = db.teacher_evidence_bundle(evidence_options[selected_label])
    else:
        global_ui.render_inline_notice(labels["missing"], "", lang=lang, tone="warning")

    c1, c2 = st.columns(2)
    with c1:
        max_units = st.slider(labels["units"], 1, 10, int(cfg.get("max_units") or 5), key=f"blueprint_units_{project_id}")
    with c2:
        max_lessons = st.slider(labels["lessons"], 2, 30, int(cfg.get("max_lessons") or 12), key=f"blueprint_lessons_{project_id}")

    latest = db.latest_teacher_blueprint(project_id, approved_only=False)
    _render_blueprint_stage_flow(built=bool(latest), approved=bool(latest and int(latest.get("approved_by_teacher") or 0)), lang=lang)
    build_clicked = st.button(
        labels["rebuild"] if latest else labels["build"], type="primary", use_container_width=True,
        disabled=not bool(selected_evidence), key=f"build_blueprint_{project_id}",
    )
    if build_clicked:
        progress_label = {"ar": "جارٍ إنشاء المخطط...", "fr": "Construction du plan...", "en": "Building the blueprint..."}.get(lang, "Building...")
        try:
            with st.spinner(progress_label):
                latest = lesson_blueprint_engine.generate_and_persist(
                    project, _current_teacher_username(), evidence_bundle=selected_evidence,
                    max_units=int(max_units), max_lessons=int(max_lessons),
                )
            st.success({"ar": "تم إنشاء المخطط. راجعه ثم اعتمده.", "fr": "Plan créé. Révisez-le puis approuvez-le.", "en": "Blueprint created. Review and approve it."}.get(lang, "Blueprint created."))
        except Exception as exc:
            ui_stability.render_error_card(str(exc), lang=lang)
            latest = db.latest_teacher_blueprint(project_id, approved_only=False)

    bundle = latest or db.latest_teacher_blueprint(project_id, approved_only=False)
    if not bundle:
        return
    quality = bundle.get("quality") or {}
    blueprint = bundle.get("blueprint") or {}
    units = blueprint.get("units") or []
    lessons = blueprint.get("lessons") or []
    outcomes = blueprint.get("outcomes") or []
    concepts = blueprint.get("concepts") or []
    edges = blueprint.get("concept_edges") or []
    approved = bool(int(bundle.get("approved_by_teacher") or 0))

    metric_cols = st.columns(4)
    metric_data = [
        (labels["readiness"], f"{float(quality.get('readiness_score') or 0):.0%}", ""),
        (labels["units"], len(units), ""), (labels["lessons"], len(lessons), ""), (labels["outcomes"], len(outcomes), ""),
    ]
    for col, (label, value, unit) in zip(metric_cols, metric_data):
        with col:
            global_ui.render_kpi_card(label, value, unit=unit, lang=lang)

    version_text = f"{labels['version']}: {int(bundle.get('version_number') or 1)} · {labels['status']}: {bundle.get('status') or 'unknown'}"
    st.caption(version_text)
    if approved:
        global_ui.render_inline_notice(labels["approved"], labels["next_lessons"], lang=lang, tone="success")
        if st.button(labels["open_lessons"], type="primary", use_container_width=True, key=f"open_blocks_{project_id}"):
            st.session_state.teacher_workspace_section_pending = "blocks"
            st.rerun()
    else:
        global_ui.render_inline_notice(labels["next_review"], "", lang=lang, tone="info")
        if str(bundle.get("status") or "") != "error":
            if st.button(labels["approve"], type="primary", use_container_width=True, key=f"approve_blueprint_top_{int(bundle.get('id') or 0)}"):
                try:
                    db.approve_teacher_blueprint_run(int(bundle["id"]), project_id, _current_teacher_username())
                    st.session_state.teacher_workspace_section_pending = "blocks"
                    st.session_state.teacher_flash_success = labels["approved"]
                except Exception as exc:
                    st.session_state.teacher_flash_error = str(exc)
                st.rerun()

    tabs = st.tabs([labels["course"], labels["outcomes"], labels["concepts"], labels["quality"], labels["editor"], labels["versions"]])
    with tabs[0]:
        lesson_by_id = {str(item.get("lesson_id")): item for item in lessons}
        for unit in units:
            with st.expander(f"{unit.get('unit_id')} · {unit.get('title')}", expanded=True):
                st.caption(f"Concepts: {', '.join(unit.get('concept_ids') or [])} · Sources: {', '.join(unit.get('source_ids') or [])}")
                for lesson_id in unit.get("lesson_ids") or []:
                    lesson = lesson_by_id.get(str(lesson_id), {})
                    st.markdown(f"**{lesson.get('lesson_id')} · {lesson.get('title')}**")
                    st.caption(f"{lesson.get('estimated_duration_minutes')} min · Concepts: {', '.join(lesson.get('concept_ids') or [])} · Sources: {', '.join(lesson.get('source_ids') or [])}")
                    st.write(" → ".join(lesson.get("lesson_sequence") or []))
    with tabs[1]:
        rows = [{
            "Outcome": item.get("outcome_id"), "Lesson": item.get("lesson_id"), "Bloom": item.get("bloom_level"),
            "Statement": f"{item.get('verb')} {item.get('object') or item.get('object_text') or ''}",
            "Activity": item.get("activity_id"), "Assessment": item.get("assessment_id"), "Criterion": item.get("success_criterion"),
        } for item in outcomes]
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    with tabs[2]:
        incoming: Dict[str, List[str]] = {}
        for edge in edges:
            incoming.setdefault(str(edge.get("to_concept_id")), []).append(str(edge.get("from_concept_id")))
        rows = [{
            "ID": item.get("concept_id"), "Concept": item.get("name"),
            "Prerequisites": ", ".join(incoming.get(str(item.get("concept_id")), []) or item.get("prerequisites") or []),
            "Difficulty": item.get("difficulty"), "Sources": ", ".join(item.get("source_ids") or []),
        } for item in concepts]
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    with tabs[3]:
        warnings = quality.get("warnings") or []
        if warnings:
            for warning in warnings:
                st.markdown(f"- {warning}")
        else:
            st.success({"ar": "اجتاز المخطط الفحوص الآلية.", "fr": "Le plan a réussi les contrôles automatiques.", "en": "The blueprint passed automated checks."}.get(lang, "Quality gate passed."))
        st.json(quality)
    with tabs[4]:
        render_blueprint_editor(project, bundle, lang)
    with tabs[5]:
        render_blueprint_versions(project, bundle, lang)

    payload = {"run": {k: v for k, v in bundle.items() if k not in {"blueprint", "quality", "units", "lessons", "outcomes", "concepts", "concept_edges"}}, "blueprint": blueprint, "quality": quality}
    st.download_button(labels["download"], json.dumps(payload, ensure_ascii=False, indent=2, default=str).encode("utf-8"),
                       file_name=f"project_{project_id}_lesson_blueprint.json", mime="application/json", use_container_width=True,
                       key=f"download_blueprint_{int(bundle.get('id') or 0)}")

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
            _render_generation_markdown(
                str(row.get("response_text") or ""),
                str(project.get("primary_language_code") or "en"),
            )
            filename = f"project_{int(project['id'])}_phase_{phase}_output.md"
            st.download_button("Download output", str(row.get("response_text") or "").encode("utf-8"), file_name=filename, mime="text/markdown", key=f"download_teacher_run_{int(row['id'])}")



def project_workspace_ui() -> Dict[str, str]:
    lang = i18n.current_lang(st)
    values = {
        "ar": {
            "new": "مشروع جديد", "projects": "مشاريعي التعليمية", "workspace": "واجهة المشروع", "outputs": "كل المخرجات",
            "open": "فتح المشروع", "continue": "متابعة الإنتاج", "preview": "معاينة كمتعلم", "back": "العودة إلى المشاريع",
            "overview": "نظرة عامة", "production": "الإنتاج والتحرير", "evidence": "تركيب الأدلة", "blueprint": "مخطط المقرر", "blocks": "بناء الدروس", "assets": "المحتوى والمخرجات", "publish": "المعاينة والنشر",
            "draft": "مسودة", "review": "قيد المراجعة", "published": "منشور", "archived": "مؤرشف",
            "progress": "تقدم الإنتاج", "phases": "المراحل المنجزة", "runs": "عمليات التوليد", "updated": "آخر تحديث",
            "empty_title": "ابدأ أول مشروع تعليمي", "empty_body": "أنشئ مشروعًا، أضف محتوى المادة وطريقة التدريس والتقييم، ثم أنتج موارده على مراحل.",
            "create": "إنشاء مشروع تعليمي", "project_center": "مركز المشروع التعليمي", "project_id": "رقم المشروع",
            "status": "حالة المشروع", "course_identity": "هوية المقرر", "learning_design": "التصميم التعليمي",
            "phase_map": "خريطة مراحل الإنتاج", "ready": "جاهز", "not_ready": "لم يبدأ", "needs_review": "تحتاج مراجعة", "failed": "تعذر التوليد", "running": "جارٍ التوليد",
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
            "overview": "Vue d’ensemble", "production": "Production et édition", "evidence": "Synthèse des preuves", "blueprint": "Plan du cours", "blocks": "Construction des leçons", "assets": "Contenus et productions", "publish": "Aperçu et publication",
            "draft": "Brouillon", "review": "En révision", "published": "Publié", "archived": "Archivé",
            "progress": "Progression de production", "phases": "Phases terminées", "runs": "Générations", "updated": "Dernière mise à jour",
            "empty_title": "Commencez votre premier projet", "empty_body": "Définissez le contenu, la pédagogie et l’évaluation, puis produisez les ressources par étapes.",
            "create": "Créer un projet pédagogique", "project_center": "Centre du projet", "project_id": "Projet",
            "status": "Statut", "course_identity": "Identité du cours", "learning_design": "Conception pédagogique",
            "phase_map": "Carte des phases", "ready": "Prêt", "not_ready": "Non démarré", "needs_review": "À réviser", "failed": "Échec", "running": "Génération",
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
            "overview": "Overview", "production": "Production and editing", "evidence": "Evidence synthesis", "blueprint": "Lesson blueprint", "blocks": "Lesson blocks", "assets": "Content and outputs", "publish": "Preview and publish",
            "draft": "Draft", "review": "In review", "published": "Published", "archived": "Archived",
            "progress": "Production progress", "phases": "Completed phases", "runs": "Generation runs", "updated": "Last updated",
            "empty_title": "Start your first educational project", "empty_body": "Define the subject, pedagogy, and assessment, then produce the assets phase by phase.",
            "create": "Create educational project", "project_center": "Educational project center", "project_id": "Project",
            "status": "Status", "course_identity": "Course identity", "learning_design": "Learning design",
            "phase_map": "Production phase map", "ready": "Ready", "not_ready": "Not started", "needs_review": "Needs review", "failed": "Generation failed", "running": "Generating",
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



def _friendly_teacher_error(message: Any) -> tuple[str, str]:
    """Return localized safe copy while preserving the technical diagnostic."""
    friendly, technical, _ = ui_stability.friendly_error(message, i18n.current_lang(st))
    return friendly, technical


def _render_workspace_exception(exc: Exception) -> None:
    retry_key = f"teacher_workspace_retry_{ui_stability.error_fingerprint(exc)}"
    if ui_stability.render_error_card(exc, lang=i18n.current_lang(st), retry_key=retry_key):
        st.rerun()


def _set_workspace_section(section: str) -> None:
    st.session_state.teacher_workspace_section_pending = str(section)
    st.rerun()


def _render_guided_workflow(project: Dict[str, Any], state: Dict[str, Any]) -> None:
    """Render one clear seven-stage teacher journey without duplicate actions."""
    lang = i18n.current_lang(st)
    direction = i18n.direction(lang)
    copy = guided_teacher_workflow.workflow_copy(lang)
    statuses = dict(state.get("statuses") or {})
    current_key = str(state.get("current_key") or "setup")
    current_spec = copy["steps"][current_key]
    current_status = statuses.get(current_key, "available")
    completed = int(state.get("completed_count") or 0)
    total = int(state.get("total_steps") or 7)
    step_keys = [item["key"] for item in guided_teacher_workflow.WORKFLOW_STEPS]
    current_index = step_keys.index(current_key) if current_key in step_keys else 0
    next_key = step_keys[current_index + 1] if current_index + 1 < len(step_keys) else None
    next_spec = copy["steps"].get(next_key) if next_key else None
    target_section = guided_teacher_workflow.section_for_step(current_key)
    visible_section = str(st.session_state.get("teacher_workspace_section") or "")

    completion_rules = {
        "ar": {
            "setup": "استكمال بيانات المقرر وحفظها.",
            "resources": "مراجعة المصادر ثم اعتماد حزمة البحث.",
            "evidence": "مراجعة بطاقات الأدلة ثم اعتماد الحزمة.",
            "blueprint": "مراجعة مخطط المقرر ثم اعتماده.",
            "lessons": "اعتماد جميع أجزاء الدروس المطلوبة.",
            "quality": "اجتياز فحوص الجودة النهائية.",
            "publish": "المعاينة ثم النشر أو الإرسال للمراجعة.",
        },
        "fr": {
            "setup": "Compléter et enregistrer la fiche du cours.",
            "resources": "Réviser puis approuver le dossier de recherche.",
            "evidence": "Réviser puis approuver le dossier de preuves.",
            "blueprint": "Réviser puis approuver le plan du cours.",
            "lessons": "Approuver tous les blocs requis.",
            "quality": "Valider les contrôles qualité.",
            "publish": "Prévisualiser puis publier.",
        },
        "en": {
            "setup": "Complete and save the course brief.",
            "resources": "Review the sources and approve the research dossier.",
            "evidence": "Review and approve the evidence bundle.",
            "blueprint": "Review and approve the course blueprint.",
            "lessons": "Approve all required lesson blocks.",
            "quality": "Pass the final quality checks.",
            "publish": "Preview and publish or submit for review.",
        },
    }.get(lang, {})

    st.markdown("<span class='v6162-workflow-marker' aria-hidden='true'></span>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='v6162-section-heading' dir='{direction}'>"
        f"<div><span>{completed}/{total}</span><h2>{escape(copy['journey'])}</h2>"
        f"<p>{escape(copy['journey_help'])}</p></div></div>",
        unsafe_allow_html=True,
    )

    cols = ui_stability.columns(len(guided_teacher_workflow.WORKFLOW_STEPS), gap="small", vertical_alignment="top")
    for index, (col, step) in enumerate(zip(cols, guided_teacher_workflow.WORKFLOW_STEPS), start=1):
        key = step["key"]
        status = statuses.get(key, "locked")
        spec = copy["steps"][key]
        visual_status = status
        if key == current_key and status not in {"completed", "review"}:
            visual_status = "active"
        node_text = "✓" if status == "completed" else str(index)
        with col:
            st.markdown(
                f"<div class='v6162-step-node v6162-step-{escape(visual_status)}' dir='{direction}'>"
                f"<span>{node_text}</span></div>",
                unsafe_allow_html=True,
            )
            if st.button(
                spec["short"],
                use_container_width=True,
                disabled=status == "locked",
                key=f"guided_workflow_step_{int(project['id'])}_{key}",
                help=copy["locked_help"] if status == "locked" else spec["description"],
            ):
                _set_workspace_section(step["section"])
            st.caption(copy["status"].get(status, status))

    st.markdown("<span class='v6172-current-stage-marker v6162-current-action-marker' aria-hidden='true'></span>", unsafe_allow_html=True)
    main_col, summary_col = ui_stability.columns([2.25, 1], gap="large", vertical_alignment="top")
    with main_col:
        now_label = {"ar": "المرحلة الحالية", "fr": "Étape actuelle", "en": "Current stage"}.get(lang, "Current stage")
        finish_label = {"ar": "تنتهي عندما", "fr": "Terminée lorsque", "en": "Completed when"}.get(lang, "Completed when")
        next_label = {"ar": "المرحلة التالية", "fr": "Étape suivante", "en": "Next stage"}.get(lang, "Next stage")
        next_title = next_spec["title"] if next_spec else current_spec["title"]
        st.markdown(
            f"<section class='v6172-current-stage-card' dir='{direction}'>"
            f"<div class='v6172-current-stage-head'><small>{escape(now_label)}</small><h3>{escape(current_spec['title'])}</h3>"
            f"<p>{escape(current_spec['description'])}</p></div>"
            f"<div class='v6172-current-stage-grid'>"
            f"<div><small>{escape(finish_label)}</small><strong>{escape(completion_rules.get(current_key, current_spec['outcome']))}</strong></div>"
            f"<div><small>{escape(next_label)}</small><strong>{escape(next_title)}</strong></div>"
            f"</div></section>",
            unsafe_allow_html=True,
        )
        if visible_section != target_section:
            open_label = {"ar": "فتح مساحة العمل الحالية", "fr": "Ouvrir l’espace de travail", "en": "Open current workspace"}.get(lang, "Open current workspace")
            if st.button(open_label, type="primary", use_container_width=True, key=f"guided_open_{int(project['id'])}_{current_key}"):
                _set_workspace_section(target_section)
        else:
            in_stage = {
                "ar": "أنت داخل هذه المرحلة الآن. نفّذ الإجراء الرئيسي في مساحة العمل أدناه؛ لا يلزم الضغط على زر آخر للانتقال إليها.",
                "fr": "Vous êtes déjà dans cette étape. Utilisez l’action principale ci-dessous.",
                "en": "You are already in this stage. Use the primary action in the workspace below.",
            }.get(lang, "Use the primary action below.")
            st.caption(in_stage)

    with summary_col:
        p = _project_defaults(project)
        target_languages = ", ".join(str(item) for item in (p.get("target_languages") or []) if str(item).strip()) or "—"
        status_label = copy["status"].get(current_status, current_status)
        summary_title = {"ar": "ملخص سريع", "fr": "Résumé", "en": "Quick summary"}.get(lang, "Quick summary")
        status_title = {"ar": "حالة المرحلة", "fr": "État de l’étape", "en": "Stage status"}.get(lang, "Stage status")
        st.markdown(
            f"<aside class='v6162-summary-card' dir='{direction}'>"
            f"<h3>{escape(summary_title)}</h3>"
            f"<div class='v6162-summary-row'><span>{escape(status_title)}</span><b>{escape(status_label)}</b></div>"
            f"<div class='v6162-summary-row'><span>{escape(str(p.get('learner_level') or '—'))}</span><b>{escape(str(p.get('expected_duration') or '—'))}</b></div>"
            f"<div class='v6162-summary-languages'>{escape(target_languages)}</div>"
            f"</aside>",
            unsafe_allow_html=True,
        )

    lesson = dict(state.get("lesson_progress") or {})
    if int(lesson.get("required") or 0) > 0:
        approved = int(lesson.get("approved") or 0)
        required = int(lesson.get("required") or 0)
        st.markdown("<span class='v6162-lesson-progress-marker' aria-hidden='true'></span>", unsafe_allow_html=True)
        st.progress(approved / max(required, 1), text=f"{copy['lesson_progress']}: {approved}/{required}")

def render_project_quality_summary(project: Dict[str, Any]) -> None:
    lang = i18n.current_lang(st)
    labels = {
        "ar": {
            "title": "المراجعة والجودة",
            "intro": "راجع جاهزية المشروع قبل المعاينة والنشر. تعرض هذه الصفحة نقاط الاكتمال والاعتماد دون إغراق الواجهة بالتفاصيل التقنية.",
            "evidence": "الأدلة المعتمدة",
            "blueprint": "المخطط المعتمد",
            "blocks": "أجزاء الدروس المعتمدة",
            "phase": "التدقيق النهائي",
            "ready": "جاهز",
            "pending": "غير مكتمل",
            "outputs": "عرض جميع المخرجات والإصدارات",
            "next": "أكمل العناصر غير الجاهزة، ثم انتقل إلى المعاينة والنشر.",
        },
        "fr": {
            "title": "Révision et qualité", "intro": "Vérifiez la préparation du projet avant l’aperçu et la publication.",
            "evidence": "Preuves approuvées", "blueprint": "Plan approuvé", "blocks": "Blocs approuvés",
            "phase": "Contrôle final", "ready": "Prêt", "pending": "Incomplet", "outputs": "Afficher les productions et versions",
            "next": "Terminez les éléments incomplets avant la publication.",
        },
        "en": {
            "title": "Review and quality", "intro": "Check project readiness before preview and publication.",
            "evidence": "Approved evidence", "blueprint": "Approved blueprint", "blocks": "Approved lesson blocks",
            "phase": "Final quality phase", "ready": "Ready", "pending": "Incomplete", "outputs": "Show all outputs and versions",
            "next": "Complete pending items before preview and publication.",
        },
    }.get(lang)
    state = guided_teacher_workflow.load_workflow_state(project)
    evidence = db.latest_teacher_evidence_for_project(int(project["id"]), approved_only=True)
    blueprint = db.latest_teacher_blueprint(int(project["id"]), approved_only=True)
    lesson = dict(state.get("lesson_progress") or {})
    outputs = db.teacher_project_phase_outputs(int(project["id"]))
    final_ready = str((outputs.get(11) or {}).get("status") or "") == "completed"

    st.markdown(f"## {labels['title']}")
    st.write(labels["intro"])
    cols = st.columns(4)
    checks = [
        (labels["evidence"], bool(evidence)),
        (labels["blueprint"], bool(blueprint)),
        (labels["blocks"], bool(int(lesson.get("required") or 0) > 0 and int(lesson.get("approved") or 0) >= int(lesson.get("required") or 0))),
        (labels["phase"], final_ready),
    ]
    for col, (title, ready) in zip(cols, checks):
        with col:
            with st.container(border=True):
                st.caption(title)
                st.markdown(f"### {'✓' if ready else '○'} {labels['ready'] if ready else labels['pending']}")
    if not all(value for _, value in checks):
        st.info(labels["next"])
    with st.expander(labels["outputs"], expanded=False):
        render_outputs(project)


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


def _render_project_card(project: Dict[str, Any], copy: Dict[str, str]) -> None:
    completed, runs, pct = _project_progress_values(project)
    status = str(project.get("status") or "draft").lower()
    project_id = int(project["id"])
    title = escape(str(project.get("project_name") or project.get("unit_title") or ""))
    domain = escape(str(project.get("domain") or ""))
    program = escape(str(project.get("program_name") or project.get("unit_title") or ""))
    concept = escape(str(project.get("target_concept") or "")[:220])

    with st.container(border=True, key=f"v6163_project_card_{project_id}"):
        st.markdown(
            f"<span class='v692-project-card-marker v6163-project-card-marker v618-project-card-marker' aria-hidden='true'></span>"
            f"<div class='v692-project-card-head'><span>{escape(_status_label(status, copy))}</span>"
            f"<small>#{project_id}</small></div>"
            f"<div class='v6163-project-card-copy'><h3>{title}</h3>"
            f"<p class='v6163-project-taxonomy'>{domain}{' · ' if domain and program else ''}{program}</p>"
            f"<p class='v6163-project-concept'>{concept or '—'}</p></div>",
            unsafe_allow_html=True,
        )
        st.progress(pct / 100, text=f"{copy['progress']}: {pct}% — {completed}/{len(PHASES)}")
        st.markdown(
            f"<div class='v6163-project-facts'>"
            f"<span><b>{completed}/{len(PHASES)}</b><small>{escape(copy['phases'])}</small></span>"
            f"<span><b>{runs}</b><small>{escape(copy['runs'])}</small></span>"
            f"<span><b>{escape(_status_label(status, copy))}</b><small>{escape(copy['status'])}</small></span>"
            f"</div>",
            unsafe_allow_html=True,
        )
        b1, b2 = ui_stability.columns(2, gap="small", vertical_alignment="center")
        with b1:
            if st.button(copy["open"], type="primary", use_container_width=True, key=f"open_teacher_project_{project_id}"):
                _open_project(project_id, "overview")
                st.rerun()
        with b2:
            if st.button(copy["continue"], use_container_width=True, key=f"continue_teacher_project_{project_id}"):
                full_project = db.get_teacher_project(project_id, _current_teacher_username()) or project
                journey = guided_teacher_workflow.load_workflow_state(full_project)
                if _simple_teacher_mode():
                    simple_state = simple_teacher_journey.build_simple_state(journey)
                    st.session_state.teacher_simple_stage = str(simple_state.get("current_key") or "setup")
                    _open_project(project_id, "overview")
                else:
                    resume_section = guided_teacher_workflow.section_for_step(str(journey.get("current_key") or "setup"))
                    _open_project(project_id, resume_section)
                st.rerun()


def render_projects_grid() -> None:
    copy = project_workspace_ui()
    username = _current_teacher_username()
    projects = db.teacher_projects_with_progress_df(username)
    st.markdown("<span class='v6163-project-grid-marker v618-teacher-grid-marker' aria-hidden='true'></span>", unsafe_allow_html=True)
    global_ui.render_section_header(
        copy["projects"],
        {"ar": "أدر مشاريعك التعليمية، وتابع مستوى تقدم كل مقرر من مكان واحد.", "fr": "Gérez vos projets pédagogiques et suivez leur progression depuis un seul espace.", "en": "Manage educational projects and track every course from one workspace."}.get(i18n.current_lang(st), ""),
        lang=i18n.current_lang(st),
    )
    if projects.empty:
        _, empty_col, _ = ui_stability.columns([1, 1.5, 1], gap="large", vertical_alignment="top")
        with empty_col:
            with st.container(border=True, key="v6163_empty_projects"):
                st.markdown(f"### {copy['empty_title']}")
                st.write(copy["empty_body"])
                if st.button(copy["create"], type="primary", use_container_width=True, key="teacher_empty_create"):
                    st.session_state.teacher_studio_view = "new"
                    st.rerun()
        return

    rows = projects.to_dict("records")
    if len(rows) == 1:
        _, center_col, _ = ui_stability.columns([1, 1.55, 1], gap="large", vertical_alignment="top")
        with center_col:
            _render_project_card(rows[0], copy)
        return

    column_count = 3 if len(rows) >= 3 else 2
    for start in range(0, len(rows), column_count):
        cols = ui_stability.columns(column_count, gap="large", vertical_alignment="top")
        for col, project in zip(cols, rows[start:start + column_count]):
            with col:
                _render_project_card(project, copy)


def _project_header(project: Dict[str, Any], workflow_state: Optional[Dict[str, Any]] = None) -> None:
    """Render one coherent project header with grouped metadata and progress."""
    copy = project_workspace_ui()
    lang = i18n.current_lang(st)
    direction = i18n.direction(lang)
    workflow_state = workflow_state or guided_teacher_workflow.load_workflow_state(project)
    completed = int(workflow_state.get("completed_count") or 0)
    total = int(workflow_state.get("total_steps") or 7)
    pct = int(workflow_state.get("progress_pct") or 0)
    p = _project_defaults(project)

    status_text = _status_label(str(project.get("status") or "draft"), copy)
    languages = ", ".join(str(item) for item in (p.get("target_languages") or []) if str(item).strip())
    meta_items = [
        str(p.get("domain") or "").strip(),
        str(p.get("learner_level") or "").strip(),
        str(p.get("expected_duration") or "").strip(),
        languages,
    ]
    chips = "".join(f"<span class='v6162-meta-chip'>{escape(item)}</span>" for item in meta_items if item)
    title = escape(str(project.get("project_name") or project.get("unit_title") or ""))
    subtitle = escape(str(project.get("unit_title") or project.get("program_name") or ""))
    progress_label = {"ar": "اكتمال رحلة المقرر", "fr": "Parcours du cours", "en": "Course journey"}.get(lang, "Course journey")

    with st.container(border=False, key="v6163_project_header"):
        st.markdown("<span class='v6162-studio-header-marker v6163-project-header-marker' aria-hidden='true'></span>", unsafe_allow_html=True)
        breadcrumb_col, back_col = ui_stability.columns([6.2, 1.25], vertical_alignment="center", gap="large")
        with breadcrumb_col:
            st.markdown(
                f"<div class='v6163-project-breadcrumb' dir='{direction}'>"
                f"{escape(copy['project_center'])} · #{int(project['id'])}</div>",
                unsafe_allow_html=True,
            )
        with back_col:
            if st.button(f"← {copy['back']}", use_container_width=True, key="teacher_back_to_projects"):
                st.session_state.teacher_studio_view = "projects"
                st.rerun()

        st.markdown(
            f"<section class='v6162-studio-header v6163-studio-header' dir='{direction}'>"
            f"<div class='v6162-header-main'>"
            f"<div class='v6162-header-copy'>"
            f"<div class='v6163-title-row'><span class='v6162-status-pill'>{escape(status_text)}</span><h1>{title}</h1></div>"
            f"<p>{subtitle}</p><div class='v6162-meta-chips'>{chips}</div></div>"
            f"<div class='v6162-progress-stat'><strong>{pct}%</strong>"
            f"<span>{escape(progress_label)}</span><small>{completed}/{total}</small></div>"
            f"</div>"
            f"<div class='v6162-progress-track' role='progressbar' aria-valuemin='0' aria-valuemax='100' aria-valuenow='{pct}'>"
            f"<span style='width:{max(0, min(100, pct))}%'></span></div>"
            f"</section>",
            unsafe_allow_html=True,
        )


def _render_phase_map(project: Dict[str, Any]) -> None:
    copy = project_workspace_ui()
    project_id = int(project["id"])
    outputs = db.teacher_project_phase_outputs(project_id)
    jobs = db.teacher_production_jobs_df(project_id)
    latest_jobs = {}
    if not jobs.empty:
        for _, job_row in jobs.iterrows():
            phase_key = int(job_row.get("phase_number") or 0)
            if phase_key and phase_key not in latest_jobs:
                latest_jobs[phase_key] = job_row.to_dict()
    lang = i18n.current_lang(st)
    direction = i18n.direction(lang)
    st.markdown(f"### {copy['phase_map']}")
    for start in range(1, 12, 3):
        cols = ui_stability.columns(3, gap="small", vertical_alignment="top")
        for col, phase in zip(cols, range(start, min(start + 3, 12))):
            row = outputs.get(phase) or {}
            job_row = latest_jobs.get(phase) or {}
            job_status = str(job_row.get("status") or "").strip().lower()
            raw_status = job_status if job_status in {"queued", "waiting_for_dependency", "running", "failed", "retrying"} else str(row.get("status") or "not_started").strip().lower()
            semantic, css_status = ui_stability.status_semantics(raw_status)
            legacy_label_key = {
                "approved": "ready", "ready": "ready", "review": "needs_review",
                "running": "running", "queued": "running", "blocked": "not_ready",
                "failed": "failed", "pending": "not_ready",
            }.get(semantic, "not_ready")
            updated = str(job_row.get("updated_at") or row.get("updated_at") or row.get("created_at") or "").strip()
            updated_html = (
                f"<small class='v6165-prod-updated'>{escape(updated[:16].replace('T', ' '))}</small>"
                if updated else ""
            )
            badge = ui_stability.status_badge_html(raw_status, lang=lang, label=copy[legacy_label_key])
            with col:
                st.markdown(
                    f"<article class='v6164-prod-card v6165-prod-card {escape(css_status)}' dir='{direction}'>"
                    f"<header><span class='v6164-prod-num'>{phase:02d}</span>"
                    f"<h4>{escape(str(PHASES[phase]))}</h4></header>"
                    f"<footer>{badge}{updated_html}</footer>"
                    f"</article>",
                    unsafe_allow_html=True,
                )

    completed = production_pipeline.completed_phases(project_id)
    if 3 in completed:
        backend = production_pipeline.queue_backend()
        labels = {
            "ar": ("الإنتاج الخلفي الهجين", "ابدأ المراحل 04–09 كدفعة إنتاج مستقلة. يمكن مغادرة الصفحة والعودة لاحقًا عند استخدام RQ/Redis.", "بدء الإنتاج الشامل", "التنفيذ المحلي متزامن؛ أضف REDIS_URL وعامل RQ للحصول على تنفيذ خلفي دائم."),
            "fr": ("Production hybride en arrière-plan", "Lancez les phases 04–09 comme un lot indépendant.", "Démarrer la production groupée", "Le mode local est synchrone; configurez REDIS_URL et un worker RQ pour un vrai arrière-plan."),
            "en": ("Hybrid background production", "Launch phases 04–09 as an independent production batch.", "Start batch production", "Inline mode is synchronous; configure REDIS_URL and an RQ worker for persistent background execution."),
        }.get(lang, ("Hybrid background production", "Launch phases 04–09 as an independent production batch.", "Start batch production", "Inline mode is synchronous."))
        st.markdown(f"#### {labels[0]}")
        st.caption(labels[1])
        if backend == "inline":
            st.info(labels[3])
        active = False
        if not jobs.empty:
            active = any(str(value).lower() in {"queued", "running", "waiting_for_dependency", "retrying"} for value in jobs["status"].tolist())
        if st.button(labels[2], type="primary", use_container_width=True, disabled=active, key=f"start_batch_{project_id}"):
            try:
                batch = production_pipeline.enqueue_parallel_batch(project_id, _current_teacher_username())
                st.session_state.teacher_flash_success = f"Batch {batch['batch_id']} submitted via {batch['backend']}."
            except Exception as exc:
                st.session_state.teacher_flash_error = str(exc)
            st.rerun()


def render_project_overview(project: Dict[str, Any]) -> None:
    copy = project_workspace_ui()
    p = _project_defaults(project)
    lang = i18n.current_lang(st)
    direction = i18n.direction(lang)
    languages = ", ".join(p.get("target_languages") or []) or "—"
    components = ", ".join(p.get("platform_components") or []) or "—"
    identity_chips = "".join(
        f"<span class='v6163-overview-chip'>{escape(value)}</span>"
        for value in [str(p.get("learner_level") or "—"), str(p.get("expected_duration") or "—"), languages]
    )
    c1, c2 = ui_stability.columns(2, gap="large", vertical_alignment="top")
    with c1:
        with st.container(border=True, key="v6163_course_identity_card"):
            st.markdown("<span class='v6163-overview-card-marker' aria-hidden='true'></span>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='v6163-overview-card' dir='{direction}'><h3>{escape(copy['course_identity'])}</h3>"
                f"<h4>{escape(str(p.get('unit_title') or '—'))}</h4>"
                f"<p>{escape(str(p.get('target_concept') or '—'))}</p>"
                f"<div class='v6163-overview-chips'>{identity_chips}</div></div>",
                unsafe_allow_html=True,
            )
    with c2:
        with st.container(border=True, key="v6163_learning_design_card"):
            st.markdown("<span class='v6163-overview-card-marker' aria-hidden='true'></span>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='v6163-overview-card' dir='{direction}'><h3>{escape(copy['learning_design'])}</h3>"
                f"<div class='v6163-overview-field'><span>Teaching</span><b>{escape(str(p.get('teaching_preferences') or '—'))}</b></div>"
                f"<div class='v6163-overview-field'><span>Assessment</span><b>{escape(str(p.get('assessment_preferences') or '—'))}</b></div>"
                f"<div class='v6163-overview-field'><span>Components</span><b>{escape(components)}</b></div></div>",
                unsafe_allow_html=True,
            )
    phase_label = {"ar": "سجل التوليد التقني المتقدم", "fr": "Journal technique avancé", "en": "Advanced technical generation log"}.get(lang, "Advanced technical generation log")
    with st.expander(phase_label, expanded=False):
        st.info({
            "ar": "هذه البطاقات الإحدى عشرة وظائف تقنية داخلية لإنتاج الأصول، وليست خطوات رحلة الأستاذ. اتبع المسار ذي السبع مراحل أعلى الصفحة.",
            "fr": "Ces onze cartes sont des tâches techniques internes, pas les étapes du parcours enseignant.",
            "en": "These eleven cards are internal production jobs, not the teacher journey. Follow the seven-stage path above.",
        }.get(lang, "These are internal production jobs, not the teacher journey."))
        _render_phase_map(project)


def _latest_completed_output(project_id: int, phase: int) -> str:
    """Return the latest validated legacy phase output used by learner previews."""
    row = db.teacher_project_phase_outputs(int(project_id)).get(int(phase))
    if not row or str(row.get("status")) != "completed":
        return ""
    return str(row.get("response_text") or "").strip()


def render_project_student_preview(project: Dict[str, Any], public_view: bool = False) -> None:
    """Render a learner-safe preview of a teacher-authored course."""
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



def _block_state_copy(lang: str) -> Dict[str, str]:
    copies = {
        "ar": {"approved": "معتمدة", "needs_review": "جاهزة للمراجعة", "failed": "تعذر التوليد", "running": "جارٍ التوليد", "queued": "في قائمة الانتظار", "retrying": "إعادة المحاولة", "not_started": "لم تبدأ", "locked": "تنتظر اعتماد الجزء السابق"},
        "fr": {"approved": "Approuvé", "needs_review": "À réviser", "failed": "Échec", "running": "En cours", "queued": "En file", "retrying": "Nouvelle tentative", "not_started": "Non commencé", "locked": "Attend le bloc précédent"},
        "en": {"approved": "Approved", "needs_review": "Ready for review", "failed": "Generation failed", "running": "Running", "queued": "Queued", "retrying": "Retrying", "not_started": "Not started", "locked": "Waiting for previous approval"},
    }
    return copies.get(lang, copies["en"])


def _render_lesson_block_map(rows: List[Dict[str, Any]], lang: str) -> None:
    status_copy = _block_state_copy(lang)
    cards = []
    for index, row in enumerate(rows, start=1):
        state = "locked" if row.get("locked") else str(row.get("state") or "not_started")
        cards.append(
            "<article class='v6183-block-card v6183-block-%s'><div class='v6183-block-top'><span>%02d</span><i></i></div><strong>%s</strong><small>%s</small></article>"
            % (escape(state), index, escape(str(row.get("label") or row.get("block_type"))), escape(status_copy.get(state, state)))
        )
    st.markdown("<div class='v6183-block-grid' dir='%s'>%s</div>" % ("rtl" if lang == "ar" else "ltr", "".join(cards)), unsafe_allow_html=True)


def render_lesson_blocks(project: Dict[str, Any]) -> None:
    """Render a guided, sequential block-level lesson production workspace."""
    lang = i18n.current_lang(st)
    labels = {
        "ar": {"title": "بناء الدروس", "intro": "أنشئ أجزاء الدرس بالترتيب، راجع كل جزء واعتمده قبل الانتقال إلى الجزء التالي.", "blueprint_missing": "يجب اعتماد مخطط مقرر أولًا.", "lesson": "الدرس", "block": "جزء الدرس", "generate": "توليد هذا الجزء بالذكاء الاصطناعي", "regenerate": "إعادة توليد الجزء", "preview": "المعاينة", "edit": "مراجعة وتحرير", "versions": "الإصدارات", "audit": "سجل العمليات", "approve": "اعتماد الجزء والانتقال إلى التالي", "approved": "تم اعتماد هذا الجزء.", "save": "حفظ إصدار جديد", "summary": "ملخص التعديل", "progress": "اكتمال الدرس", "no_output": "لم يُولّد هذا الجزء بعد.", "download": "تنزيل الجزء", "validation": "فحص الجودة", "provider": "المزوّد والنموذج", "latency": "زمن الاستجابة", "locked": "اعتمد الجزء السابق أولًا للحفاظ على تسلسل الدرس.", "complete": "اكتملت جميع أجزاء هذا الدرس.", "next_lesson": "الانتقال إلى الدرس التالي"},
        "fr": {"title": "Construction des leçons", "intro": "Créez les blocs dans l’ordre, révisez et approuvez chaque bloc avant le suivant.", "blueprint_missing": "Un plan approuvé est requis.", "lesson": "Leçon", "block": "Bloc", "generate": "Générer ce bloc", "regenerate": "Régénérer", "preview": "Aperçu", "edit": "Réviser", "versions": "Versions", "audit": "Journal", "approve": "Approuver et passer au suivant", "approved": "Bloc approuvé.", "save": "Enregistrer une version", "summary": "Résumé", "progress": "Achèvement", "no_output": "Bloc non généré.", "download": "Télécharger", "validation": "Validation", "provider": "Fournisseur / modèle", "latency": "Latence", "locked": "Approuvez le bloc précédent.", "complete": "Tous les blocs sont approuvés.", "next_lesson": "Leçon suivante"},
        "en": {"title": "Build lessons", "intro": "Create lesson blocks in order, review each one, and approve it before moving forward.", "blueprint_missing": "An approved course blueprint is required.", "lesson": "Lesson", "block": "Lesson block", "generate": "Generate this block with AI", "regenerate": "Regenerate block", "preview": "Preview", "edit": "Review and edit", "versions": "Versions", "audit": "Audit trail", "approve": "Approve and continue to the next block", "approved": "This block is approved.", "save": "Save new version", "summary": "Change summary", "progress": "Lesson completion", "no_output": "This block has not been generated.", "download": "Download block", "validation": "Quality validation", "provider": "Provider / model", "latency": "Latency", "locked": "Approve the previous block first.", "complete": "All lesson blocks are approved.", "next_lesson": "Open next lesson"},
    }.get(lang, {})
    global_ui.render_section_header(labels["title"], labels["intro"], lang=lang, eyebrow="05")
    if not _runtime_contract_ready("lesson_blocks", lang):
        return
    cfg = lesson_block_generation_engine.block_generation_status()
    if not cfg.get("enabled"):
        st.warning("ENABLE_LESSON_BLOCK_GENERATION is disabled.")
        return
    project_id = int(project["id"])
    blueprint = db.latest_teacher_blueprint(project_id, approved_only=True)
    if not blueprint:
        global_ui.render_inline_notice(labels["blueprint_missing"], "", lang=lang, tone="warning")
        return
    lessons = list((blueprint.get("blueprint") or {}).get("lessons") or [])
    if not lessons:
        global_ui.render_inline_notice(labels["blueprint_missing"], "", lang=lang, tone="warning")
        return

    lesson_options = {f"{item.get('lesson_id')} · {item.get('title')}": str(item.get("lesson_id")) for item in lessons}
    lesson_key = f"block_lesson_{project_id}"
    pending_lesson = st.session_state.pop(f"block_pending_lesson_{project_id}", None)
    if pending_lesson and pending_lesson in lesson_options.values():
        st.session_state[lesson_key] = next(label for label, value in lesson_options.items() if value == pending_lesson)
    if lesson_key not in st.session_state:
        first_incomplete = next((str(item.get("lesson_id")) for item in lessons if not lesson_block_generation_engine.lesson_completion(project_id, str(item.get("lesson_id"))).get("complete")), str(lessons[0].get("lesson_id")))
        st.session_state[lesson_key] = next(label for label, value in lesson_options.items() if value == first_incomplete)
    lesson_label = st.selectbox(labels["lesson"], list(lesson_options), key=lesson_key)
    lesson_id = lesson_options[lesson_label]
    lesson_row = next((item for item in lessons if str(item.get("lesson_id")) == lesson_id), {})
    st.caption(f"{lesson_row.get('estimated_duration_minutes') or '-'} min · {', '.join(lesson_row.get('concept_ids') or [])}")

    state_rows = lesson_block_generation_engine.lesson_block_state(project_id, lesson_id, "ar" if lang == "ar" else "en")
    completion = lesson_block_generation_engine.lesson_completion(project_id, lesson_id)
    metric_cols = st.columns(3)
    with metric_cols[0]: global_ui.render_kpi_card(labels["progress"], f"{completion['approved']}/{completion['required']}", lang=lang)
    with metric_cols[1]: global_ui.render_kpi_card({"ar": "الأجزاء المولدة", "fr": "Blocs générés", "en": "Generated blocks"}.get(lang, "Generated"), completion["available"], lang=lang)
    with metric_cols[2]: global_ui.render_kpi_card({"ar": "نسبة الاكتمال", "fr": "Taux", "en": "Completion"}.get(lang, "Completion"), f"{completion['approved']/max(completion['required'],1):.0%}", lang=lang)
    st.progress(completion["approved"] / max(completion["required"], 1), text=f"{labels['progress']}: {completion['approved']}/{completion['required']}")
    _render_lesson_block_map(state_rows, lang)

    next_type = lesson_block_generation_engine.next_incomplete_block(project_id, lesson_id)
    block_options = {lesson_block_generation_engine.block_label(key, "ar" if lang == "ar" else "en"): key for key in lesson_block_generation_engine.ordered_block_types()}
    block_key = f"block_type_{project_id}_{lesson_id}"
    pending_block = st.session_state.pop(f"block_pending_type_{project_id}_{lesson_id}", None)
    if pending_block in block_options.values():
        st.session_state[block_key] = next(label for label, value in block_options.items() if value == pending_block)
    if block_key not in st.session_state:
        preferred = next_type or next(iter(block_options.values()))
        st.session_state[block_key] = next(label for label, value in block_options.items() if value == preferred)
    block_label = st.selectbox(labels["block"], list(block_options), key=block_key)
    block_type = block_options[block_label]
    permission = lesson_block_generation_engine.can_generate_block(project_id, lesson_id, block_type)
    if not permission.get("allowed"):
        global_ui.render_inline_notice(labels["locked"], "", lang=lang, tone="warning")

    latest = db.latest_teacher_lesson_block(project_id, lesson_id, block_type, approved_only=False)
    button_label = labels["regenerate"] if latest else labels["generate"]
    created = None
    if st.button(button_label, type="primary", use_container_width=True, disabled=not bool(permission.get("allowed")), key=f"generate_block_{project_id}_{lesson_id}_{block_type}"):
        try:
            with st.spinner({"ar": "جارٍ توليد الجزء...", "fr": "Génération du bloc...", "en": "Generating block..."}.get(lang, "Generating...")):
                created = lesson_block_generation_engine.generate_and_persist(project, _current_teacher_username(), blueprint, lesson_id, block_type)
            st.success({"ar": "تم توليد الجزء. راجعه ثم اعتمده.", "fr": "Bloc généré. Révisez-le puis approuvez-le.", "en": "Block generated. Review and approve it."}.get(lang, "Generated."))
        except Exception as exc:
            ui_stability.render_error_card(str(exc), lang=lang)
    latest = created or db.latest_teacher_lesson_block(project_id, lesson_id, block_type, approved_only=False)
    if not latest:
        st.info(labels["no_output"])
        return

    validation = latest.get("validation") or {}
    cols = st.columns(4)
    values = [("Status", latest.get("status") or "unknown"), (labels["provider"], f"{latest.get('provider') or '-'} / {latest.get('model') or '-'}"), (labels["latency"], f"{int(latest.get('latency_ms') or 0)/1000:.1f}s"), ("Words", int(latest.get("word_count") or 0))]
    for col, (label, value) in zip(cols, values):
        with col: global_ui.render_kpi_card(label, value, lang=lang)
    approved = int(latest.get("approved_by_teacher") or 0) == 1
    if approved:
        global_ui.render_inline_notice(labels["approved"], "", lang=lang, tone="success")

    tabs = st.tabs([labels["preview"], labels["edit"], labels["versions"], labels["audit"]])
    with tabs[0]:
        _render_generation_markdown(str(latest.get("content_text") or ""), str(project.get("primary_language_code") or lang))
        with st.expander(labels["validation"]): st.json(validation)
        st.download_button(labels["download"], data=str(latest.get("content_text") or ""), file_name=f"{lesson_id}_{block_type}_v{latest.get('version_number')}.md", mime="text/markdown", use_container_width=True)
        if not approved:
            if st.button(labels["approve"], type="primary", use_container_width=True, key=f"approve_block_{latest['id']}"):
                try:
                    db.approve_teacher_lesson_block(int(latest["id"]), project_id, _current_teacher_username())
                    new_next = lesson_block_generation_engine.next_incomplete_block(project_id, lesson_id)
                    if new_next:
                        st.session_state[f"block_pending_type_{project_id}_{lesson_id}"] = new_next
                    st.session_state.teacher_flash_success = labels["approved"]
                except Exception as exc:
                    st.session_state.teacher_flash_error = str(exc)
                st.rerun()
    with tabs[1]:
        edited = st.text_area(labels["edit"], value=str(latest.get("content_text") or ""), height=520, key=f"edit_block_{latest['id']}")
        change_summary = st.text_input(labels["summary"], key=f"block_change_summary_{latest['id']}")
        if st.button(labels["save"], type="primary", use_container_width=True, key=f"save_block_revision_{latest['id']}"):
            try:
                lesson_block_generation_engine.save_teacher_revision(project_id=project_id, base_run_id=int(latest["id"]), teacher_username=_current_teacher_username(), content_text=edited, change_summary=change_summary)
                st.session_state.teacher_flash_success = labels["save"]
            except Exception as exc:
                st.session_state.teacher_flash_error = str(exc)
            st.rerun()
    with tabs[2]:
        versions = db.teacher_lesson_block_versions_df(project_id, lesson_id, block_type)
        if not versions.empty: st.dataframe(versions, use_container_width=True, hide_index=True)
    with tabs[3]:
        audit = db.teacher_lesson_block_audit_df(project_id, lesson_id)
        if not audit.empty: st.dataframe(audit, use_container_width=True, hide_index=True)

    completion = lesson_block_generation_engine.lesson_completion(project_id, lesson_id)
    if completion.get("complete"):
        global_ui.render_inline_notice(labels["complete"], "", lang=lang, tone="success")
        lesson_ids = [str(item.get("lesson_id")) for item in lessons]
        current_index = lesson_ids.index(lesson_id)
        if current_index + 1 < len(lesson_ids):
            if st.button(labels["next_lesson"], type="primary", use_container_width=True, key=f"next_lesson_{project_id}_{lesson_id}"):
                st.session_state[f"block_pending_lesson_{project_id}"] = lesson_ids[current_index + 1]
                st.rerun()


def _simple_teacher_mode() -> bool:
    """Return True for the default teacher-facing simplified experience."""
    mode = str(st.session_state.get("teacher_experience_mode") or "").strip().lower()
    if mode not in {"simple", "advanced"}:
        mode = "simple" if _as_bool(_secret("TEACHER_SIMPLE_MODE_DEFAULT", "true"), True) else "advanced"
        st.session_state.teacher_experience_mode = mode
    return mode == "simple"


def _render_teacher_mode_control() -> None:
    lang = i18n.current_lang(st)
    labels = {
        "ar": ("خيارات الواجهة", "استخدمي الوضع المبسط للعمل اليومي، وافتحي الوضع المتقدم فقط عند الحاجة إلى الأدلة والإصدارات والتفاصيل التقنية.", "الوضع المتقدم"),
        "fr": ("Options d’affichage", "Utilisez le mode simplifié au quotidien et le mode avancé pour les détails techniques.", "Mode avancé"),
        "en": ("View options", "Use Simple mode for daily work and Advanced mode only for technical details.", "Advanced mode"),
    }.get(lang, ("View options", "Use Simple mode for daily work.", "Advanced mode"))
    with st.expander(labels[0], expanded=False):
        st.caption(labels[1])
        advanced = st.toggle(labels[2], value=not _simple_teacher_mode(), key="teacher_advanced_mode_toggle")
        requested = "advanced" if advanced else "simple"
        if requested != st.session_state.get("teacher_experience_mode"):
            st.session_state.teacher_experience_mode = requested
            st.session_state.teacher_simple_stage = None
            st.rerun()


def _render_simple_journey(project: Dict[str, Any], simple_state: Dict[str, Any]) -> str:
    """Render a five-step journey and return the selected accessible stage."""
    st.markdown("<span class='v6186-simple-journey-marker' aria-hidden='true'></span>", unsafe_allow_html=True)
    lang = i18n.current_lang(st)
    direction = i18n.direction(lang)
    copy = simple_teacher_journey.copy(lang)
    statuses = dict(simple_state.get("statuses") or {})
    current_key = str(simple_state.get("current_key") or "setup")
    selected = str(st.session_state.get("teacher_simple_stage") or current_key)
    manual_history_open = bool(st.session_state.pop("teacher_simple_manual_stage_once", False))
    if selected not in {item["key"] for item in simple_teacher_journey.SIMPLE_STEPS} or statuses.get(selected) == "locked":
        selected = current_key
    elif not manual_history_open and selected != current_key and statuses.get(selected) == "completed":
        # After an approval rerun, follow the newly unlocked stage automatically.
        selected = current_key
    st.session_state.teacher_simple_stage = selected

    global_ui.render_section_header(copy["title"], copy["help"], lang=lang, eyebrow="01–05")
    cols = ui_stability.columns(len(simple_teacher_journey.SIMPLE_STEPS), gap="small", vertical_alignment="top")
    icons = {"completed": "✓", "review": "!", "in_progress": "•", "available": "→", "locked": "○"}
    for index, (col, step) in enumerate(zip(cols, simple_teacher_journey.SIMPLE_STEPS), start=1):
        key = step["key"]
        status = str(statuses.get(key) or "locked")
        spec = copy["steps"][key]
        active = key == selected
        button_label = f"{icons.get(status, '○')} {index}. {spec['short']}"
        with col:
            if st.button(
                button_label,
                use_container_width=True,
                type="primary" if active else "secondary",
                disabled=status == "locked",
                key=f"simple_stage_{int(project['id'])}_{key}",
                help=spec["description"],
            ):
                st.session_state.teacher_simple_stage = key
                st.session_state.teacher_simple_manual_stage_once = True
                st.rerun()
            st.caption(copy["status"].get(status, status))

    if selected != current_key:
        if st.button(copy["continue"], type="primary", use_container_width=True, key=f"simple_resume_{int(project['id'])}"):
            st.session_state.teacher_simple_stage = current_key
            st.rerun()

    spec = copy["steps"][selected]
    st.markdown(
        f"<section class='v6184-current-step' dir='{direction}'><small>{escape(copy['status'].get(statuses.get(selected,'available'),''))}</small>"
        f"<h2>{escape(spec['title'])}</h2><p>{escape(spec['description'])}</p></section>",
        unsafe_allow_html=True,
    )
    return selected


def _render_simple_sources(project: Dict[str, Any], base_state: Dict[str, Any]) -> None:
    lang = i18n.current_lang(st)
    substep = simple_teacher_journey.source_substep(base_state)
    labels = {
        "ar": {"research": "1. جمع المصادر", "evidence": "2. التحقق من المصادر", "done": "3. المصادر جاهزة", "research_done": "تم اعتماد حزمة البحث. تتحقق المنصة الآن من المصادر وتستخرج المعلومات الأساسية.", "all_done": "تم اعتماد مصادر المقرر وأصبحت خطة المقرر جاهزة للإنشاء.", "next": "الانتقال إلى خطة المقرر"},
        "fr": {"research": "1. Collecter les sources", "evidence": "2. Vérifier les sources", "done": "3. Sources prêtes", "research_done": "Le dossier de recherche est approuvé. Vérifiez maintenant les preuves.", "all_done": "Les sources du cours sont approuvées.", "next": "Passer au plan du cours"},
        "en": {"research": "1. Collect sources", "evidence": "2. Verify sources", "done": "3. Sources ready", "research_done": "The research dossier is approved. The platform is now verifying sources.", "all_done": "Course sources are approved and the course plan is ready.", "next": "Go to course plan"},
    }.get(lang)
    steps = [labels["research"], labels["evidence"], labels["done"]]
    active_index = {"research": 0, "evidence": 1, "complete": 2}.get(substep, 0)
    st.markdown("<div class='v6184-mini-flow'>" + "".join(
        f"<span class='{'done' if i < active_index else 'active' if i == active_index else ''}'>{escape(text)}</span>" for i, text in enumerate(steps)
    ) + "</div>", unsafe_allow_html=True)
    if substep == "research":
        render_prompt_and_generation(project)
    elif substep == "evidence":
        global_ui.render_inline_notice(labels["research_done"], "", lang=lang, tone="success")
        render_evidence_synthesis(project)
    else:
        global_ui.render_inline_notice(labels["all_done"], "", lang=lang, tone="success")
        if st.button(labels["next"], type="primary", use_container_width=True, key=f"simple_sources_next_{int(project['id'])}"):
            st.session_state.teacher_simple_stage = "plan"
            st.rerun()



def _render_simple_plan(project: Dict[str, Any]) -> None:
    lang = i18n.current_lang(st)
    labels = {
        "ar": {"title": "خطة المقرر", "intro": "راجعي الوحدات والدروس فقط. يمكنك فتح التفاصيل المتقدمة عند الحاجة.", "missing": "اعتمدي مصادر المقرر أولًا.", "settings": "إعدادات إنشاء الخطة", "units": "عدد الوحدات", "lessons": "عدد الدروس", "build": "إنشاء خطة المقرر", "rebuild": "إعادة إنشاء الخطة", "plan": "الخطة المقترحة", "approve": "اعتماد الخطة وبدء إنشاء الدروس", "approved": "تم اعتماد خطة المقرر.", "next": "الانتقال إلى إنشاء الدروس", "advanced": "التعديل والتفاصيل المتقدمة", "duration": "دقيقة", "lesson": "درس"},
        "fr": {"title": "Plan du cours", "intro": "Révisez les unités et les leçons. Les détails avancés restent facultatifs.", "missing": "Approuvez d’abord les sources du cours.", "settings": "Paramètres du plan", "units": "Unités", "lessons": "Leçons", "build": "Créer le plan", "rebuild": "Recréer le plan", "plan": "Plan proposé", "approve": "Approuver et créer les leçons", "approved": "Plan approuvé.", "next": "Créer les leçons", "advanced": "Édition et détails avancés", "duration": "min", "lesson": "leçon"},
        "en": {"title": "Course plan", "intro": "Review the units and lessons. Advanced details stay optional.", "missing": "Approve the course sources first.", "settings": "Plan settings", "units": "Units", "lessons": "Lessons", "build": "Create course plan", "rebuild": "Recreate plan", "plan": "Proposed plan", "approve": "Approve plan and create lessons", "approved": "Course plan approved.", "next": "Continue to lesson creation", "advanced": "Editing and advanced details", "duration": "min", "lesson": "lesson"},
    }.get(lang)
    global_ui.render_section_header(labels["title"], labels["intro"], lang=lang, eyebrow="03")
    if not _runtime_contract_ready("blueprint", lang):
        return
    cfg = lesson_blueprint_engine.blueprint_status()
    if not cfg.get("enabled"):
        global_ui.render_inline_notice("ENABLE_LESSON_BLUEPRINT is disabled.", "", lang=lang, tone="warning")
        return
    project_id = int(project["id"])
    evidence = db.latest_teacher_evidence_for_project(project_id, approved_only=True)
    if not evidence:
        global_ui.render_inline_notice(labels["missing"], "", lang=lang, tone="warning")
        return
    bundle = db.latest_teacher_blueprint(project_id, approved_only=False)
    with st.expander(labels["settings"], expanded=not bool(bundle)):
        c1, c2 = st.columns(2)
        with c1:
            max_units = st.slider(labels["units"], 1, 10, min(int(cfg.get("max_units") or 5), 10), key=f"simple_plan_units_{project_id}")
        with c2:
            max_lessons = st.slider(labels["lessons"], 2, 30, min(int(cfg.get("max_lessons") or 12), 30), key=f"simple_plan_lessons_{project_id}")
        if st.button(labels["rebuild"] if bundle else labels["build"], type="primary", use_container_width=True, key=f"simple_build_plan_{project_id}"):
            try:
                with st.spinner(labels["build"] + "..."):
                    bundle = lesson_blueprint_engine.generate_and_persist(project, _current_teacher_username(), evidence_bundle=evidence, max_units=int(max_units), max_lessons=int(max_lessons))
                st.success(labels["plan"])
            except Exception as exc:
                ui_stability.render_error_card(exc, lang=lang)
                bundle = db.latest_teacher_blueprint(project_id, approved_only=False)
    if not bundle:
        return
    blueprint = dict(bundle.get("blueprint") or {})
    units = list(blueprint.get("units") or [])
    lessons = list(blueprint.get("lessons") or [])
    lesson_by_id = {str(item.get("lesson_id")): item for item in lessons}
    approved = bool(int(bundle.get("approved_by_teacher") or 0))
    m1, m2 = st.columns(2)
    with m1: global_ui.render_kpi_card(labels["units"], len(units), lang=lang)
    with m2: global_ui.render_kpi_card(labels["lessons"], len(lessons), lang=lang)
    st.markdown(f"### {labels['plan']}")
    for unit_index, unit in enumerate(units, start=1):
        with st.container(border=True, key=f"simple_plan_unit_{project_id}_{unit_index}"):
            st.markdown(f"#### {unit_index}. {unit.get('title')}")
            for lesson_id in unit.get("lesson_ids") or []:
                lesson = lesson_by_id.get(str(lesson_id), {})
                st.markdown(f"- **{lesson.get('title') or lesson_id}** · {lesson.get('estimated_duration_minutes') or '—'} {labels['duration']}")
    if approved:
        global_ui.render_inline_notice(labels["approved"], "", lang=lang, tone="success")
        if st.button(labels["next"], type="primary", use_container_width=True, key=f"simple_plan_next_{project_id}"):
            st.session_state.teacher_simple_stage = "lessons"
            st.rerun()
    else:
        if st.button(labels["approve"], type="primary", use_container_width=True, key=f"simple_approve_plan_{project_id}_{int(bundle.get('id') or 0)}"):
            try:
                db.approve_teacher_blueprint_run(int(bundle["id"]), project_id, _current_teacher_username())
                st.session_state.teacher_flash_success = labels["approved"]
                st.session_state.teacher_simple_stage = "lessons"
                st.rerun()
            except Exception as exc:
                ui_stability.render_error_card(exc, lang=lang)
    with st.expander(labels["advanced"], expanded=False):
        render_blueprint_editor(project, bundle, lang)
        render_blueprint_versions(project, bundle, lang)
        st.json(bundle.get("quality") or {})


def _lesson_simple_labels(lang: str) -> Dict[str, str]:
    return {
        "ar": {
            "title": "إنشاء الدروس",
            "intro": "أنشئي مسودة الدرس كاملة، راجعيها تربويًا، ثم اعتمديها. التفاصيل التقنية تبقى مخفية ما لم تحتاجيها.",
            "lesson": "اختيار الدرس",
            "course_progress": "تقدم المقرر",
            "lesson_progress": "تقدم الدرس",
            "remaining": "الدروس المتبقية",
            "generate": "إنشاء مسودة الدرس",
            "continue_generate": "إكمال مسودة الدرس",
            "generating": "جارٍ بناء الدرس تربويًا",
            "generated": "اكتملت مسودة الدرس وأصبحت جاهزة لمراجعتك.",
            "preview": "مراجعة الدرس",
            "empty": "لم تُنشأ مسودة هذا الدرس بعد.",
            "approve": "اعتماد الدرس والانتقال إلى التالي",
            "approved": "تم اعتماد الدرس.",
            "next": "الانتقال إلى الدرس التالي",
            "download": "تنزيل الدرس",
            "advanced": "تعديل قسم أو عرض التفاصيل المتقدمة",
            "section": "قسم الدرس",
            "regenerate": "إعادة إنشاء هذا القسم",
            "save": "حفظ التعديل",
            "summary": "ملخص التعديل",
            "technical": "التفاصيل التقنية",
            "all_done": "اكتملت جميع الدروس. انتقلي إلى المراجعة والنشر.",
            "design": "التصميم التربوي",
            "quality_ready": "المسودة مكتملة وجاهزة للمراجعة والاعتماد.",
            "quality_review": "توجد ملاحظات تربوية غير مانعة. راجعيها قبل الاعتماد.",
            "quality_blocked": "توجد مشكلة تمنع اعتماد الدرس حتى تُعالج.",
            "quality_details": "ملاحظات الجودة التربوية",
            "draft_status": "حالة المسودة",
            "ready": "جاهزة للمراجعة",
            "approved_state": "معتمد",
            "section_purpose": "لماذا هذا القسم؟",
            "teacher_decision": "قرار الأستاذ",
        },
        "fr": {
            "title": "Créer les leçons", "intro": "Générez un brouillon complet, révisez-le pédagogiquement puis approuvez-le. Les détails techniques restent masqués par défaut.",
            "lesson": "Choisir la leçon", "course_progress": "Progression du cours", "lesson_progress": "Progression de la leçon", "remaining": "Leçons restantes",
            "generate": "Créer le brouillon de la leçon", "continue_generate": "Compléter le brouillon", "generating": "Construction pédagogique de la leçon", "generated": "Le brouillon complet est prêt pour votre révision.",
            "preview": "Réviser la leçon", "empty": "Cette leçon n’a pas encore de brouillon.", "approve": "Approuver et passer à la suivante", "approved": "Leçon approuvée.",
            "next": "Leçon suivante", "download": "Télécharger", "advanced": "Modifier une section ou afficher les détails", "section": "Section", "regenerate": "Régénérer cette section", "save": "Enregistrer", "summary": "Résumé des modifications", "technical": "Détails techniques", "all_done": "Toutes les leçons sont terminées.",
            "design": "Conception pédagogique", "quality_ready": "Le brouillon est complet et prêt à être validé.", "quality_review": "Des remarques pédagogiques non bloquantes méritent une révision.", "quality_blocked": "Un problème doit être corrigé avant l’approbation.", "quality_details": "Remarques de qualité pédagogique", "draft_status": "État du brouillon", "ready": "À réviser", "approved_state": "Approuvé", "section_purpose": "Pourquoi cette section ?", "teacher_decision": "Décision de l’enseignant",
        },
        "en": {
            "title": "Create lessons", "intro": "Create a complete lesson draft, review it pedagogically, then approve it. Technical details stay out of the way unless you need them.",
            "lesson": "Choose lesson", "course_progress": "Course progress", "lesson_progress": "Lesson progress", "remaining": "Lessons remaining",
            "generate": "Create lesson draft", "continue_generate": "Complete lesson draft", "generating": "Building the lesson pedagogically", "generated": "The complete lesson draft is ready for your review.",
            "preview": "Review lesson", "empty": "This lesson does not have a draft yet.", "approve": "Approve lesson and continue", "approved": "Lesson approved.",
            "next": "Open next lesson", "download": "Download lesson", "advanced": "Edit a section or view advanced details", "section": "Lesson section", "regenerate": "Regenerate this section", "save": "Save edit", "summary": "Change summary", "technical": "Technical details", "all_done": "All lessons are complete. Continue to review and publish.",
            "design": "Pedagogical design", "quality_ready": "The draft is complete and ready for review and approval.", "quality_review": "There are non-blocking pedagogical notes to review before approval.", "quality_blocked": "A blocking issue must be resolved before approval.", "quality_details": "Pedagogical quality notes", "draft_status": "Draft status", "ready": "Ready for review", "approved_state": "Approved", "section_purpose": "Why this section?", "teacher_decision": "Teacher decision",
        },
    }.get(lang, {})


def _render_simple_lesson_builder(project: Dict[str, Any], simple_state: Dict[str, Any]) -> None:
    lang = i18n.current_lang(st)
    labels = _lesson_simple_labels(lang)
    render_lang = str(project.get("primary_language_code") or lang).lower()
    if render_lang not in {"ar", "fr", "en"}:
        render_lang = lang if lang in {"ar", "fr", "en"} else "en"

    global_ui.render_section_header(labels["title"], labels["intro"], lang=lang, eyebrow="04")
    if not _runtime_contract_ready("lesson_blocks", lang):
        return

    project_id = int(project["id"])
    blueprint = db.latest_teacher_blueprint(project_id, approved_only=True)
    if not blueprint:
        global_ui.render_inline_notice(
            {"ar": "اعتمدي خطة المقرر أولًا.", "fr": "Approuvez d’abord le plan du cours.", "en": "Approve the course plan first."}.get(lang),
            "", lang=lang, tone="warning",
        )
        return

    lessons = list((blueprint.get("blueprint") or {}).get("lessons") or [])
    if not lessons:
        st.info(labels["empty"])
        return

    lesson_ids = [str(item.get("lesson_id")) for item in lessons]
    incomplete_id = next(
        (lid for lid in lesson_ids if not lesson_block_generation_engine.lesson_completion(project_id, lid).get("complete")),
        lesson_ids[-1],
    )
    lesson_key = f"simple_lesson_{project_id}"
    pending = st.session_state.pop(f"simple_pending_lesson_{project_id}", None)
    default_id = pending if pending in lesson_ids else incomplete_id
    options = {f"{idx + 1}. {item.get('title')}": str(item.get("lesson_id")) for idx, item in enumerate(lessons)}
    if lesson_key not in st.session_state or st.session_state.get(lesson_key) not in options:
        st.session_state[lesson_key] = next(label for label, lid in options.items() if lid == default_id)

    lesson_label = st.selectbox(labels["lesson"], list(options), key=lesson_key)
    lesson_id = options[lesson_label]
    lesson_index = lesson_ids.index(lesson_id)
    lesson_row = lessons[lesson_index]
    completion = lesson_block_generation_engine.lesson_completion(project_id, lesson_id)
    completed_lessons = sum(1 for lid in lesson_ids if lesson_block_generation_engine.lesson_completion(project_id, lid).get("complete"))

    course_pct = int(round(100 * completed_lessons / max(len(lessons), 1)))
    lesson_pct = int(round(100 * int(completion.get("approved") or 0) / max(int(completion.get("required") or 1), 1)))
    direction = "rtl" if lang == "ar" else "ltr"
    st.markdown(
        f"<div class='v6185-lesson-hero' dir='{direction}'>"
        f"<div class='v6185-lesson-heading'><span>{lesson_index + 1:02d}</span><div><small>{escape(labels['lesson'])} {lesson_index + 1} / {len(lessons)}</small>"
        f"<h2>{escape(str(lesson_row.get('title') or lesson_label))}</h2>"
        f"<p>{escape(str(lesson_row.get('estimated_duration_minutes') or '—'))} min</p></div></div>"
        f"<div class='v6185-progress-cards'>"
        f"<div><small>{escape(labels['course_progress'])}</small><b>{completed_lessons}/{len(lessons)}</b><em>{course_pct}%</em></div>"
        f"<div><small>{escape(labels['lesson_progress'])}</small><b>{int(completion.get('approved') or 0)}/{int(completion.get('required') or 0)}</b><em>{lesson_pct}%</em></div>"
        f"<div><small>{escape(labels['remaining'])}</small><b>{max(len(lessons)-completed_lessons,0)}</b><em>—</em></div>"
        f"</div></div>",
        unsafe_allow_html=True,
    )

    design_labels = pedagogical_orchestrator.lesson_design_summary(lang)
    st.markdown(
        f"<div class='v6185-design-strip' dir='{direction}'><small>{escape(labels['design'])}</small>" +
        "".join(f"<span>{escape(item)}</span>" for item in design_labels) + "</div>",
        unsafe_allow_html=True,
    )

    assembled = lesson_block_generation_engine.assembled_lesson(project_id, lesson_id, render_lang)
    st.markdown(lesson_content_renderer.lesson_section_nav_html(assembled, render_lang), unsafe_allow_html=True)

    generated_count = sum(1 for row in assembled if row.get("run"))
    failed_count = sum(1 for row in assembled if str(row.get("status") or "").lower() in {"error", "failed"})
    button_label = labels["generate"] if generated_count == 0 else labels["continue_generate"]

    if not completion.get("complete") and (generated_count < len(assembled) or failed_count):
        if st.button(button_label, type="primary", use_container_width=True, key=f"simple_generate_lesson_{project_id}_{lesson_id}"):
            progress = st.progress(0.0, text=labels["generating"])
            status_box = st.status(labels["generating"], expanded=True)

            def _progress(index: int, total: int, block_type: str, state: str) -> None:
                label = lesson_block_generation_engine.block_label(block_type, render_lang)
                progress.progress(index / max(total, 1), text=f"{index}/{total} — {label}")
                if state in {"generated", "skipped"}:
                    status_box.write(f"✓ {label}")

            try:
                lesson_block_generation_engine.generate_full_lesson(
                    project, _current_teacher_username(), blueprint, lesson_id, progress_callback=_progress
                )
                status_box.update(label=labels["generated"], state="complete", expanded=False)
                st.success(labels["generated"])
            except Exception as exc:
                status_box.update(
                    label={"ar": "تعذر إكمال إنشاء الدرس", "fr": "Création interrompue", "en": "Lesson creation stopped"}.get(lang),
                    state="error", expanded=True,
                )
                ui_stability.render_error_card(exc, lang=lang)
            assembled = lesson_block_generation_engine.assembled_lesson(project_id, lesson_id, render_lang)
            completion = lesson_block_generation_engine.lesson_completion(project_id, lesson_id)
            st.markdown(lesson_content_renderer.lesson_section_nav_html(assembled, render_lang), unsafe_allow_html=True)

    generated_count = sum(1 for row in assembled if row.get("run"))
    failed_count = sum(1 for row in assembled if str(row.get("status") or "").lower() in {"error", "failed"})
    if not any(row.get("run") for row in assembled):
        global_ui.render_inline_notice(labels["empty"], "", lang=lang, tone="warning")
        return

    quality = lesson_block_generation_engine.lesson_quality_snapshot(project_id, lesson_id)
    if quality.get("error_count"):
        global_ui.render_inline_notice(labels["quality_blocked"], "", lang=lang, tone="danger")
    elif quality.get("warning_count"):
        global_ui.render_inline_notice(labels["quality_review"], "", lang=lang, tone="warning")
    elif quality.get("ready_for_teacher_review"):
        global_ui.render_inline_notice(labels["quality_ready"], "", lang=lang, tone="success")

    issues = list(quality.get("errors") or []) + list(quality.get("warnings") or [])
    if issues:
        with st.expander(f"{labels['quality_details']} · {len(issues)}", expanded=False):
            for issue in issues:
                st.markdown(f"- {lesson_content_renderer.quality_issue_label(str(issue), lang)}")

    st.markdown(f"### {labels['preview']}")
    full_markdown_parts: List[str] = []
    for row in assembled:
        if not row.get("run"):
            continue
        cleaned = lesson_content_renderer.normalize_generated_markdown(row["content_text"], render_lang)
        full_markdown_parts.append(f"## {row['index']}. {row['label']}\n\n{cleaned}")
        with st.container(border=True, key=f"simple_preview_{project_id}_{lesson_id}_{row['block_type']}"):
            state_text = labels["approved_state"] if row.get("approved") else labels["ready"]
            rationale = pedagogical_orchestrator.pedagogical_rationale(row["block_type"], lang)
            st.markdown(
                f"<div class='v6184-section-heading'><span>{row['index']:02d}</span><div><h3>{escape(row['label'])}</h3><small>{escape(state_text)}</small></div></div>"
                f"<div class='v6185-section-purpose' dir='{direction}'><b>{escape(labels['section_purpose'])}</b><span>{escape(rationale)}</span></div>",
                unsafe_allow_html=True,
            )
            _render_generation_markdown(cleaned, render_lang)

    full_markdown = "\n\n---\n\n".join(full_markdown_parts)
    st.markdown("<span class='v6184-action-marker' aria-hidden='true'></span>", unsafe_allow_html=True)
    action_cols = st.columns([1, 2])
    with action_cols[0]:
        st.download_button(
            labels["download"], data=full_markdown, file_name=f"{lesson_id}_complete_lesson.md",
            mime="text/markdown", use_container_width=True,
        )
    with action_cols[1]:
        ready_to_approve = generated_count >= len(assembled) and failed_count == 0 and not completion.get("complete")
        if completion.get("complete"):
            if lesson_index + 1 < len(lessons):
                if st.button(labels["next"], type="primary", use_container_width=True, key=f"simple_next_lesson_{project_id}_{lesson_id}"):
                    st.session_state[f"simple_pending_lesson_{project_id}"] = lesson_ids[lesson_index + 1]
                    st.rerun()
            else:
                global_ui.render_inline_notice(labels["all_done"], "", lang=lang, tone="success")
                if st.button(
                    {"ar": "الانتقال إلى المراجعة والنشر", "fr": "Passer à la révision", "en": "Continue to review and publish"}.get(lang),
                    type="primary", use_container_width=True, key=f"simple_lessons_review_{project_id}",
                ):
                    st.session_state.teacher_simple_stage = "review"
                    st.rerun()
        else:
            if st.button(
                labels["approve"], type="primary", use_container_width=True, disabled=not ready_to_approve,
                key=f"simple_approve_lesson_{project_id}_{lesson_id}",
            ):
                try:
                    lesson_block_generation_engine.approve_full_lesson(project_id, lesson_id, _current_teacher_username())
                    st.session_state.teacher_flash_success = labels["approved"]
                    if lesson_index + 1 < len(lessons):
                        st.session_state[f"simple_pending_lesson_{project_id}"] = lesson_ids[lesson_index + 1]
                    else:
                        st.session_state.teacher_simple_stage = "review"
                    st.rerun()
                except Exception as exc:
                    ui_stability.render_error_card(exc, lang=lang)

    with st.expander(labels["advanced"], expanded=False):
        block_options = {row["label"]: row["block_type"] for row in assembled}
        selected_label = st.selectbox(labels["section"], list(block_options), key=f"simple_edit_section_{project_id}_{lesson_id}")
        block_type = block_options[selected_label]
        latest = db.latest_teacher_lesson_block(project_id, lesson_id, block_type, approved_only=False)
        if latest:
            edited = st.text_area(selected_label, value=str(latest.get("content_text") or ""), height=360, key=f"simple_edit_text_{latest['id']}")
            summary = st.text_input(labels["summary"], key=f"simple_edit_summary_{latest['id']}")
            e1, e2 = st.columns(2)
            with e1:
                if st.button(labels["save"], use_container_width=True, key=f"simple_save_section_{latest['id']}"):
                    try:
                        lesson_block_generation_engine.save_teacher_revision(
                            project_id=project_id, base_run_id=int(latest["id"]), teacher_username=_current_teacher_username(),
                            content_text=edited, change_summary=summary,
                        )
                        st.success(labels["save"])
                        st.rerun()
                    except Exception as exc:
                        ui_stability.render_error_card(exc, lang=lang)
            with e2:
                if st.button(labels["regenerate"], use_container_width=True, key=f"simple_regenerate_{project_id}_{lesson_id}_{block_type}"):
                    try:
                        lesson_block_generation_engine.generate_and_persist(
                            project, _current_teacher_username(), blueprint, lesson_id, block_type
                        )
                        st.success(labels["regenerate"])
                        st.rerun()
                    except Exception as exc:
                        ui_stability.render_error_card(exc, lang=lang)
            with st.expander(labels["technical"], expanded=False):
                st.json({
                    "provider": latest.get("provider"), "model": latest.get("model"), "status": latest.get("status"),
                    "latency_ms": latest.get("latency_ms"), "word_count": latest.get("word_count"), "validation": latest.get("validation"),
                })


def _render_simple_review(project: Dict[str, Any], base_state: Dict[str, Any]) -> None:
    lang = i18n.current_lang(st)
    if simple_teacher_journey.review_substep(base_state) == "quality":
        render_project_quality_summary(project)
        lesson = dict(base_state.get("lesson_progress") or {})
        lessons_complete = int(lesson.get("required") or 0) > 0 and int(lesson.get("approved") or 0) >= int(lesson.get("required") or 0)
        if lessons_complete:
            st.divider()
            render_project_publication(project)
    else:
        render_project_publication(project)


def _render_simple_project_workspace(project: Dict[str, Any], base_state: Dict[str, Any]) -> None:
    simple_state = simple_teacher_journey.build_simple_state(base_state)
    _project_header(project, simple_state)
    selected = _render_simple_journey(project, simple_state)
    st.divider()
    try:
        if selected == "setup":
            render_project_overview(project)
            with st.expander({"ar": "تعديل بيانات المقرر", "fr": "Modifier le cours", "en": "Edit course setup"}.get(i18n.current_lang(st)), expanded=False):
                render_project_form(project)
        elif selected == "sources":
            _render_simple_sources(project, base_state)
        elif selected == "plan":
            _render_simple_plan(project)
        elif selected == "lessons":
            _render_simple_lesson_builder(project, simple_state)
        else:
            _render_simple_review(project, base_state)
    except Exception as exc:
        _render_workspace_exception(exc)


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

    sections = [step["section"] for step in guided_teacher_workflow.WORKFLOW_STEPS]
    pending_section = st.session_state.pop("teacher_workspace_section_pending", None)
    if pending_section in sections:
        st.session_state.teacher_workspace_section = pending_section

    state = guided_teacher_workflow.load_workflow_state(project)
    if _simple_teacher_mode():
        _render_simple_project_workspace(project, state)
        return

    _project_header(project, state)
    _render_guided_workflow(project, state)

    current_section = st.session_state.get("teacher_workspace_section")
    if current_section not in sections:
        current_section = guided_teacher_workflow.section_for_step(str(state.get("current_key") or "setup"))
        st.session_state.teacher_workspace_section = current_section

    selected_step = guided_teacher_workflow.step_for_section(str(current_section))
    selected_status = str((state.get("statuses") or {}).get(selected_step) or "locked")
    if selected_status == "locked":
        current_section = guided_teacher_workflow.section_for_step(str(state.get("current_key") or "setup"))
        st.session_state.teacher_workspace_section = current_section

    st.divider()
    try:
        if current_section == "overview":
            render_project_overview(project)
            edit_label = {"ar": "تعديل إعدادات المشروع", "fr": "Modifier les paramètres du projet", "en": "Edit project setup"}.get(i18n.current_lang(st), "Edit project setup")
            with st.expander(edit_label, expanded=False):
                render_project_form(project)
        elif current_section == "production":
            render_prompt_and_generation(project)
        elif current_section == "evidence":
            render_evidence_synthesis(project)
        elif current_section == "blueprint":
            render_lesson_blueprint(project)
        elif current_section == "blocks":
            render_lesson_blocks(project)
        elif current_section == "assets":
            render_project_quality_summary(project)
        else:
            render_project_publication(project)
    except Exception as exc:
        _render_workspace_exception(exc)


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
    global_ui.render_page_header(
        copy["public_catalog"], copy["educator_content"], lang=i18n.current_lang(st),
        eyebrow="3alimnIA", compact=True, icon="menu_book",
    )
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
    global_ui.render_role_marker("teacher")
    init_teacher_state()
    if not st.session_state.teacher_logged_in:
        render_teacher_login()
        return
    u = teacher_ui()
    copy = project_workspace_ui()
    display_name = str(st.session_state.get("teacher_display_name") or _current_teacher_username()).strip()
    lang = i18n.current_lang(st)
    welcome_line = f"{u['welcome']}، {display_name} — {u['subtitle']}" if lang == "ar" else f"{u['welcome']}, {display_name} — {u['subtitle']}"
    st.markdown("<span class='v618-teacher-shell-marker' aria-hidden='true'></span>", unsafe_allow_html=True)
    workspace_meta = ({
        "ar": ["خمس خطوات واضحة", "إجراء رئيسي واحد في كل شاشة"],
        "fr": ["Cinq étapes claires", "Une action principale par écran"],
        "en": ["Five clear steps", "One primary action per screen"],
    } if _simple_teacher_mode() else {
        "ar": ["رحلة متقدمة من 7 مراحل", "تفاصيل وإصدارات كاملة"],
        "fr": ["Parcours avancé en 7 étapes", "Détails et versions"],
        "en": ["Advanced 7-stage workflow", "Full details and versions"],
    }).get(lang, ["Five clear steps", "One primary action per screen"])
    global_ui.render_page_header(
        u["workspace"], welcome_line, lang=lang,
        eyebrow={"ar": "فضاء الأستاذ", "fr": "Espace enseignant", "en": "Teacher workspace"}.get(lang, "Teacher workspace"),
        status={"ar": "استوديو المحتوى", "fr": "Studio de contenu", "en": "Content Studio"}.get(lang, "Content Studio"),
        meta=workspace_meta, compact=True, icon="edit_note", role="teacher",
    )
    _render_teacher_mode_control()
    flash_success = st.session_state.pop("teacher_flash_success", None)
    if flash_success:
        st.success(str(flash_success))
    flash_warning = st.session_state.pop("teacher_flash_warning", None)
    if flash_warning:
        st.warning(str(flash_warning))
    flash_error = st.session_state.pop("teacher_flash_error", None)
    if flash_error:
        ui_stability.render_error_card(flash_error, lang=i18n.current_lang(st))
    views = ["projects", "new", "workspace"] if _simple_teacher_mode() else ["projects", "new", "workspace", "outputs"]
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

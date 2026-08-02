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
import guided_teacher_workflow
import gemini_file_analyzer
import db
import i18n
import router
import web_research_engine
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


def _render_latest_research(project_id: int, phase_number: int, u: Dict[str, str]) -> Optional[Dict[str, Any]]:
    latest = db.latest_usable_teacher_research(int(project_id), int(phase_number))
    if not latest:
        st.caption(u["research_missing"])
        return None
    sources = web_research_engine.sources_from_json(latest.get("sources_json") or "[]")
    status = str(latest.get("status") or "")
    with st.expander(
        f"{u['research_latest']} — {phase_number}. {PHASES.get(int(phase_number), '')}",
        expanded=status in {"completed", "needs_review"},
    ):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Status", status or "—")
        c2.metric("Provider", f"{latest.get('provider') or '—'} / {latest.get('model') or '—'}")
        c3.metric(u["research_sources"], int(latest.get("source_count") or len(sources)))
        latency_ms = int(latest.get("latency_ms") or 0)
        c4.metric(u["latency"], f"{latency_ms / 1000:.1f} s" if latency_ms else "—")
        if latest.get("diagnostic"):
            st.caption(str(latest.get("diagnostic")))
        tabs = st.tabs([u["research_report"], u["research_registry"], u["research_queries"]])
        with tabs[0]:
            report = str(latest.get("report_text") or "").strip()
            if report:
                _render_generation_markdown(report, "ar" if i18n.current_lang(st) == "ar" else "en")
        with tabs[1]:
            if not sources:
                st.info(u["research_missing"])
            for source in sources:
                with st.container(border=True):
                    if source.url:
                        st.markdown(f"**[{source.source_id}] [{source.title}]({source.url})**")
                    else:
                        st.markdown(f"**[{source.source_id}] {source.title}**")
                    st.caption(
                        f"{source.domain} · {source.source_type} · {u['authority']}: {source.authority_level}/5"
                    )
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
            u["research_download"],
            json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"),
            file_name=f"project_{int(project_id)}_phase_{int(phase_number)}_research.json",
            mime="application/json",
            use_container_width=True,
            key=f"download_research_{int(latest.get('id') or 0)}",
        )
    return latest


def render_prompt_and_generation(project: Dict[str, Any]) -> None:
    u = teacher_ui()
    p = _project_defaults(project)
    phase_number = int(p.get("current_phase") or 1)
    project_id = int(p["id"])

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

    with st.container(border=True):
        st.markdown(f"### {u['research_panel']}")
        st.write(u["research_intro"])
        r1, r2 = st.columns([2, 1])
        with r1:
            research_mode = st.selectbox(
                u["research_mode"],
                modes,
                index=modes.index(default_mode),
                format_func=lambda value: mode_labels.get(value, value),
                key=f"teacher_research_mode_{project_id}_{phase_number}",
            )
        with r2:
            max_sources = st.slider(
                u["research_sources"],
                min_value=3,
                max_value=15,
                value=8,
                step=1,
                key=f"teacher_research_sources_{project_id}_{phase_number}",
                disabled=research_mode == "off",
            )
        with st.expander("Source policy / سياسة المصادر", expanded=False):
            preferred_domains_raw = st.text_input(
                u["preferred_domains"],
                value="",
                key=f"teacher_preferred_domains_{project_id}_{phase_number}",
                disabled=research_mode == "off",
            )
            excluded_domains_raw = st.text_input(
                u["excluded_domains"],
                value="wikipedia.org, pinterest.com, facebook.com, instagram.com, tiktok.com",
                key=f"teacher_excluded_domains_{project_id}_{phase_number}",
                disabled=research_mode == "off",
            )
        st.caption(u["research_cost"])
        latest_research = db.latest_usable_teacher_research(project_id, phase_number)
        research_button_label = u["research_refresh"] if latest_research else u["research_now"]
        if st.button(
            research_button_label,
            use_container_width=True,
            key=f"run_teacher_research_{project_id}_{phase_number}",
            disabled=research_mode == "off" or not research_status.get("available"),
        ):
            try:
                with st.spinner(f"3alimnIA is researching phase {phase_number}: {PHASES[phase_number]}..."):
                    research_run = educational_builder.run_project_research(
                        p,
                        _current_teacher_username(),
                        phase_number=phase_number,
                        research_mode=research_mode,
                        max_sources=max_sources,
                        preferred_domains=_split_domain_input(preferred_domains_raw),
                        excluded_domains=_split_domain_input(excluded_domains_raw),
                    )
                if bool(int(research_run.get("cache_fallback_used") or 0)):
                    detail = str(research_run.get("refresh_diagnostic") or "").strip()
                    st.session_state.teacher_flash_warning = (
                        u["research_cached_fallback"] + (f" {detail}" if detail else "")
                    )
                elif str(research_run.get("status") or "") in {"completed", "needs_review"}:
                    st.session_state.teacher_flash_success = u["research_ready"]
                else:
                    st.session_state.teacher_flash_error = (
                        str(research_run.get("diagnostic") or u["research_failed"])
                    )
            except Exception as exc:
                st.session_state.teacher_flash_error = f"{u['research_failed']} {exc}"
            st.rerun()
        _render_latest_research(project_id, phase_number, u)

    evidence_cfg = evidence_synthesis_engine.evidence_status()
    if evidence_cfg.get("enabled") and research_mode != "off":
        evidence_bundle = db.latest_teacher_evidence(project_id, phase_number, approved_only=False)
        if evidence_bundle and bool(int(evidence_bundle.get("approved_by_teacher") or 0)):
            st.success(u["evidence_approved"])
        else:
            st.warning(u["evidence_missing"] if not evidence_bundle else u["needs_review"])
            if st.button(
                u["evidence_panel"],
                use_container_width=True,
                key=f"open_evidence_workspace_{project_id}_{phase_number}",
            ):
                st.session_state.teacher_workspace_section_pending = "evidence"
                st.rerun()

    advanced_label = {
        "ar": "خيارات التوليد المرحلي المتقدمة",
        "fr": "Options avancées de génération par phase",
        "en": "Advanced phase-generation options",
    }.get(i18n.current_lang(st), "Advanced phase-generation options")
    with st.expander(advanced_label, expanded=False):
        prompt = compile_project_prompt(p, phase_number)
        st.session_state.teacher_last_prompt = prompt
        expand_prompt = bool(st.session_state.get("teacher_expand_prompt", False))
        st.success(u["prompt_ready"])
        status = content_generation_engine.provider_status()
        fallback_text = ""
        if status.get("ready_fallbacks"):
            fallback_text = " | fallback: " + ", ".join(status["ready_fallbacks"])
        st.info(
            f"{u['provider']}: {status['provider']} / {status['model']} — "
            f"{'ready' if status['available'] else 'prompt export only'}{fallback_text}"
        )
        budget = content_generation_engine.prompt_budget_info(
            prompt,
            educational_builder.PHASE_MAX_TOKENS.get(phase_number, 3600),
        )
        compacted_label = u["prompt_compacted"] if budget.get("compacted") else ""
        st.caption(
            u["prompt_budget"].format(
                runtime=budget.get("estimated_runtime_tokens", 0),
                original=budget.get("estimated_original_tokens", 0),
                output=budget.get("max_output_tokens", 0),
                compacted=compacted_label,
            )
        )
        st.caption(u["phase_only"])
        if st.button(u["rebuild_prompt"], use_container_width=True, key=f"rebuild_teacher_prompt_{project_id}_{phase_number}"):
            st.session_state.teacher_last_prompt = compile_project_prompt(p, phase_number)
            st.session_state.teacher_expand_prompt = True
            st.session_state.teacher_flash_success = u["prompt_ready"]
            st.rerun()
        with st.expander(u["prompt"], expanded=expand_prompt):
            st.code(prompt, language="markdown")
        if expand_prompt:
            st.session_state.teacher_expand_prompt = False
        safe_name = "_".join(str(p.get("project_name") or "project").split())
        st.download_button(
            u["download_prompt"],
            prompt.encode("utf-8"),
            file_name=f"{safe_name}_phase_{phase_number}_prompt.md",
            mime="text/markdown",
            use_container_width=True,
        )
        project_json = json.dumps(p, ensure_ascii=False, indent=2, default=str)
        st.download_button(
            u["download_project"],
            project_json.encode("utf-8"),
            file_name=f"{safe_name}_project.json",
            mime="application/json",
            use_container_width=True,
        )

        _render_latest_generation(
            project_id,
            u,
            str(p.get("primary_language_code") or "en"),
        )

        generate_key = f"generate_teacher_phase_{project_id}_{phase_number}"
        if st.button(u["generate"], type="primary", use_container_width=True, key=generate_key):
            try:
                with st.spinner(f"3alimnIA is generating phase {phase_number}: {PHASES[phase_number]}..."):
                    outcome = educational_builder.generate_project_phase(
                        p,
                        _current_teacher_username(),
                        phase_number=phase_number,
                        research_mode=research_mode,
                        max_research_sources=max_sources,
                        preferred_domains=_split_domain_input(preferred_domains_raw),
                        excluded_domains=_split_domain_input(excluded_domains_raw),
                        force_research=False,
                    )
                st.session_state.teacher_last_response = outcome.response
                research_note = ""
                if outcome.research_source_count:
                    research_note = (
                        f" Research: {outcome.research_provider}/{outcome.research_model}, "
                        f"{outcome.research_source_count} source(s)."
                    )
                if outcome.evidence_card_count:
                    research_note += (
                        f" Evidence: {outcome.evidence_card_count} card(s), "
                        f"approved={outcome.evidence_approved}."
                    )
                if outcome.status == "completed":
                    st.session_state.teacher_flash_success = (
                        f"{u['generated']} {phase_number}/{len(PHASES)} — "
                        f"{outcome.provider}/{outcome.model}.{research_note}"
                    )
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
    current_phase = int(project.get("current_phase") or 1)
    cfg = evidence_synthesis_engine.evidence_status()

    st.markdown(f"## {u['evidence_panel']}")
    st.write(u["evidence_intro"])
    if cfg.get("require_teacher_approval"):
        st.info(u["evidence_strict_gate"])

    phase_number = st.selectbox(
        u["evidence_phase"],
        list(PHASES.keys()),
        index=max(0, min(10, current_phase - 1)),
        format_func=lambda number: f"{number}. {PHASES[number]}",
        key=f"teacher_evidence_phase_{project_id}",
    )
    latest_research = db.latest_usable_teacher_research(project_id, int(phase_number))
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
            with st.spinner(f"3alimnIA is synthesizing evidence for phase {phase_number}..."):
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
        st.warning(u["evidence_missing_research"])
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

    st.markdown(f"### {u['evidence_latest']} — {phase_number}. {PHASES[int(phase_number)]}")
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
                    st.error(str(exc))

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
            saved = lesson_blueprint_engine.save_manual_revision(project_id, int(bundle["id"]), _current_teacher_username(), st.session_state[draft_key], change_summary)
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


def render_lesson_blueprint(project: Dict[str, Any]) -> None:
    """Render the V6.14 evidence-to-lesson planning workspace."""
    lang = i18n.current_lang(st)
    labels = {
        "ar": {
            "title": "مخطط المقرر والدروس",
            "intro": "تحوّل المنصة حزمة الأدلة المعتمدة إلى خريطة مفاهيم، وحدات، دروس، أهداف قابلة للقياس، وأنشطة وتقويمات مترابطة قبل توليد المحتوى المطول.",
            "evidence": "حزمة الأدلة المعتمدة",
            "units": "الحد الأقصى للوحدات",
            "lessons": "الحد الأقصى للدروس",
            "build": "إنشاء مخطط المقرر",
            "rebuild": "إعادة بناء المخطط",
            "missing": "اعتمد حزمة أدلة أولًا قبل إنشاء المخطط.",
            "disabled": "ENABLE_LESSON_BLUEPRINT غير مفعّل في Streamlit Secrets.",
            "readiness": "درجة الجاهزية",
            "concepts": "المفاهيم",
            "course": "بنية المقرر",
            "outcomes": "الأهداف والمحاذاة",
            "quality": "بوابة الجودة",
            "approve": "اعتماد المخطط للتوليد",
            "approved": "تم اعتماد المخطط، وسيصبح قيدًا بنيويًا لمراحل التوليد اللاحقة.",
            "download": "تنزيل المخطط بصيغة JSON",
            "warnings": "ملاحظات الجودة",
            "editor": "محرر المخطط",
            "versions": "الإصدارات والسجل",
        },
        "fr": {
            "title": "Plan du cours et des leçons",
            "intro": "La plateforme transforme les preuves approuvées en carte conceptuelle, unités, leçons, objectifs mesurables, activités et évaluations alignées.",
            "evidence": "Dossier de preuves approuvé",
            "units": "Nombre maximal d’unités",
            "lessons": "Nombre maximal de leçons",
            "build": "Construire le plan du cours",
            "rebuild": "Reconstruire le plan",
            "missing": "Approuvez d’abord un dossier de preuves.",
            "disabled": "ENABLE_LESSON_BLUEPRINT est désactivé dans Streamlit Secrets.",
            "readiness": "Score de préparation",
            "concepts": "Concepts",
            "course": "Structure du cours",
            "outcomes": "Objectifs et alignement",
            "quality": "Contrôle qualité",
            "approve": "Approuver le plan pour la génération",
            "approved": "Le plan est approuvé et contraindra les phases de génération suivantes.",
            "download": "Télécharger le plan JSON",
            "warnings": "Alertes qualité",
            "editor": "Éditeur du plan",
            "versions": "Versions et journal",
        },
        "en": {
            "title": "Course and lesson blueprint",
            "intro": "The platform converts approved evidence into a concept map, units, lessons, measurable outcomes, and aligned activities and assessments before long-form generation.",
            "evidence": "Approved evidence bundle",
            "units": "Maximum units",
            "lessons": "Maximum lessons",
            "build": "Build course blueprint",
            "rebuild": "Rebuild blueprint",
            "missing": "Approve an evidence bundle before building the blueprint.",
            "disabled": "ENABLE_LESSON_BLUEPRINT is disabled in Streamlit Secrets.",
            "readiness": "Readiness score",
            "concepts": "Concepts",
            "course": "Course structure",
            "outcomes": "Outcomes and alignment",
            "quality": "Quality gate",
            "approve": "Approve blueprint for generation",
            "approved": "The blueprint is approved and will constrain later generation phases.",
            "download": "Download blueprint JSON",
            "warnings": "Quality warnings",
            "editor": "Blueprint editor",
            "versions": "Versions and audit",
        },
    }.get(lang, {})
    cfg = lesson_blueprint_engine.blueprint_status()
    project_id = int(project["id"])
    st.markdown(f"## {labels['title']}")
    st.write(labels["intro"])
    if not cfg.get("enabled"):
        st.warning(labels["disabled"])

    evidence_df = db.teacher_evidence_runs_df(project_id)
    approved_rows = []
    if not evidence_df.empty:
        for _, row in evidence_df.iterrows():
            if int(row.get("approved_by_teacher") or 0) == 1:
                approved_rows.append(row.to_dict())
    evidence_options = {
        f"#{int(item['id'])} — Phase {int(item.get('phase_number') or 1)} — {item.get('status') or 'approved'}": int(item["id"])
        for item in approved_rows
    }
    selected_evidence = None
    if evidence_options:
        selected_label = st.selectbox(labels["evidence"], list(evidence_options.keys()), key=f"blueprint_evidence_{project_id}")
        selected_evidence = db.teacher_evidence_bundle(evidence_options[selected_label])
    else:
        st.warning(labels["missing"])

    c1, c2 = st.columns(2)
    with c1:
        max_units = st.slider(labels["units"], 1, 10, int(cfg.get("max_units") or 5), key=f"blueprint_units_{project_id}")
    with c2:
        max_lessons = st.slider(labels["lessons"], 2, 30, int(cfg.get("max_lessons") or 12), key=f"blueprint_lessons_{project_id}")

    latest = db.latest_teacher_blueprint(project_id, approved_only=False)
    if st.button(
        labels["rebuild"] if latest else labels["build"],
        type="primary",
        use_container_width=True,
        disabled=not bool(selected_evidence) or not bool(cfg.get("enabled")),
        key=f"build_blueprint_{project_id}",
    ):
        try:
            lesson_blueprint_engine.generate_and_persist(
                project,
                _current_teacher_username(),
                evidence_bundle=selected_evidence,
                max_units=int(max_units),
                max_lessons=int(max_lessons),
            )
            st.session_state.teacher_flash_success = labels["build"]
        except Exception as exc:
            st.session_state.teacher_flash_error = str(exc)
        st.rerun()

    bundle = db.latest_teacher_blueprint(project_id, approved_only=False)
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

    m1, m2, m3, m4 = st.columns(4)
    m1.metric(labels["readiness"], f"{float(quality.get('readiness_score') or 0):.0%}")
    m2.metric(labels["units"], len(units))
    m3.metric(labels["lessons"], len(lessons))
    m4.metric(labels["outcomes"], len(outcomes))
    st.caption(
        f"{bundle.get('provider') or 'deterministic'} / {bundle.get('model') or 'blueprint'} · "
        f"status={bundle.get('status') or 'unknown'} · evidence_run={bundle.get('evidence_run_id')}"
    )
    if approved:
        st.success(labels["approved"])

    tabs = st.tabs([labels["concepts"], labels["course"], labels["outcomes"], labels["quality"], labels["editor"], labels["versions"]])
    with tabs[0]:
        concept_rows = []
        incoming = {}
        for edge in edges:
            incoming.setdefault(str(edge.get("to_concept_id")), []).append(str(edge.get("from_concept_id")))
        for concept in concepts:
            concept_rows.append({
                "ID": concept.get("concept_id"),
                "Concept": concept.get("name"),
                "Prerequisites": ", ".join(incoming.get(str(concept.get("concept_id")), []) or concept.get("prerequisites") or []),
                "Difficulty": concept.get("difficulty"),
                "Sources": ", ".join(concept.get("source_ids") or []),
            })
        if concept_rows:
            st.dataframe(pd.DataFrame(concept_rows), use_container_width=True, hide_index=True)
        if edges:
            st.caption("Concept graph edges")
            st.dataframe(pd.DataFrame(edges), use_container_width=True, hide_index=True)
    with tabs[1]:
        lesson_by_id = {str(item.get("lesson_id")): item for item in lessons}
        for unit in units:
            with st.expander(f"{unit.get('unit_id')} · {unit.get('title')}", expanded=True):
                st.caption(f"Concepts: {', '.join(unit.get('concept_ids') or [])} · Sources: {', '.join(unit.get('source_ids') or [])}")
                for lesson_id in unit.get("lesson_ids") or []:
                    lesson = lesson_by_id.get(str(lesson_id), {})
                    st.markdown(f"**{lesson.get('lesson_id')} · {lesson.get('title')}**")
                    st.caption(
                        f"{lesson.get('estimated_duration_minutes')} min · Concepts: {', '.join(lesson.get('concept_ids') or [])} · "
                        f"Sources: {', '.join(lesson.get('source_ids') or [])}"
                    )
                    st.write(" → ".join(lesson.get("lesson_sequence") or []))
    with tabs[2]:
        outcome_rows = []
        for item in outcomes:
            outcome_rows.append({
                "Outcome": item.get("outcome_id"),
                "Lesson": item.get("lesson_id"),
                "Bloom": item.get("bloom_level"),
                "Statement": f"{item.get('verb')} {item.get('object')}",
                "Activity": item.get("activity_id"),
                "Assessment": item.get("assessment_id"),
                "Criterion": item.get("success_criterion"),
            })
        if outcome_rows:
            st.dataframe(pd.DataFrame(outcome_rows), use_container_width=True, hide_index=True)
    with tabs[3]:
        warnings = quality.get("warnings") or []
        if warnings:
            st.markdown(f"**{labels['warnings']}**")
            for warning in warnings:
                st.markdown(f"- {warning}")
        else:
            st.success("Quality gate passed without automatic warnings.")
        st.json(quality)
    with tabs[4]:
        render_blueprint_editor(project, bundle, lang)
    with tabs[5]:
        render_blueprint_versions(project, bundle, lang)

    payload = {"run": {k: v for k, v in bundle.items() if k not in {"blueprint", "quality", "units", "lessons", "outcomes", "concepts", "concept_edges"}}, "blueprint": blueprint, "quality": quality}
    st.download_button(
        labels["download"],
        json.dumps(payload, ensure_ascii=False, indent=2, default=str).encode("utf-8"),
        file_name=f"project_{project_id}_lesson_blueprint.json",
        mime="application/json",
        use_container_width=True,
        key=f"download_blueprint_{int(bundle.get('id') or 0)}",
    )
    if not approved and str(bundle.get("status") or "") != "error":
        if st.button(labels["approve"], type="primary", use_container_width=True, key=f"approve_blueprint_{int(bundle.get('id') or 0)}"):
            try:
                db.approve_teacher_blueprint_run(int(bundle["id"]), project_id, _current_teacher_username())
                st.session_state.teacher_flash_success = labels["approved"]
            except Exception as exc:
                st.session_state.teacher_flash_error = str(exc)
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
            "overview": "Vue d’ensemble", "production": "Production et édition", "evidence": "Synthèse des preuves", "blueprint": "Plan du cours", "blocks": "Construction des leçons", "assets": "Contenus et productions", "publish": "Aperçu et publication",
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
            "overview": "Overview", "production": "Production and editing", "evidence": "Evidence synthesis", "blueprint": "Lesson blueprint", "blocks": "Lesson blocks", "assets": "Content and outputs", "publish": "Preview and publish",
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



def _friendly_teacher_error(message: Any) -> tuple[str, str]:
    """Return a concise teacher-facing error while preserving diagnostics."""
    raw = str(message or "").strip()
    lowered = raw.lower()
    lang = i18n.current_lang(st)
    if "429" in lowered or "quota" in lowered or "resource_exhausted" in lowered:
        friendly = {
            "ar": "تعذر الاتصال بخدمة الذكاء الاصطناعي لأن حد الاستخدام الحالي قد اكتمل. احتُفظ بآخر نتيجة ناجحة ويمكن المحاولة لاحقًا.",
            "fr": "Le quota actuel du service d’IA est atteint. Le dernier résultat valide a été conservé; réessayez plus tard.",
            "en": "The current AI-service quota has been reached. The last valid result was preserved; try again later.",
        }
    elif "413" in lowered or "too large" in lowered or "request entity" in lowered:
        friendly = {
            "ar": "حجم الطلب أكبر من الحد المتاح. ستحتاج العملية إلى سياق أقصر أو إعداد البحث السريع.",
            "fr": "La requête dépasse la taille autorisée. Utilisez un contexte plus court ou le mode de recherche rapide.",
            "en": "The request exceeds the available size limit. Use a shorter context or quick research mode.",
        }
    elif "nameerror" in lowered or "not defined" in lowered:
        friendly = {
            "ar": "حدث خلل في عرض هذه الصفحة. بيانات المشروع محفوظة؛ أعد تحميل التطبيق بعد تطبيق آخر تحديث.",
            "fr": "Une erreur d’affichage est survenue. Les données sont conservées; rechargez l’application après la mise à jour.",
            "en": "A page-rendering error occurred. Project data is preserved; reload the app after applying the latest update.",
        }
    else:
        friendly = {
            "ar": "تعذر إكمال العملية حاليًا. لم تُحذف بيانات المشروع، ويمكن إعادة المحاولة بعد مراجعة التفاصيل التقنية.",
            "fr": "L’opération n’a pas pu être terminée. Les données du projet sont conservées; consultez les détails techniques.",
            "en": "The operation could not be completed. Project data was preserved; review the technical details and retry.",
        }
    return friendly.get(lang, friendly["en"]), raw


def _render_workspace_exception(exc: Exception) -> None:
    friendly, technical = _friendly_teacher_error(exc)
    st.error(friendly)
    label = {"ar": "التفاصيل التقنية", "fr": "Détails techniques", "en": "Technical details"}.get(i18n.current_lang(st), "Technical details")
    with st.expander(label, expanded=False):
        st.code(technical or exc.__class__.__name__, language="text")


def _set_workspace_section(section: str) -> None:
    st.session_state.teacher_workspace_section_pending = str(section)
    st.rerun()


def _render_guided_workflow(project: Dict[str, Any], state: Dict[str, Any]) -> None:
    lang = i18n.current_lang(st)
    copy = guided_teacher_workflow.workflow_copy(lang)
    statuses = dict(state.get("statuses") or {})
    current_key = str(state.get("current_key") or "setup")
    current_spec = copy["steps"][current_key]

    st.markdown("<span class='v6161-guided-workflow-marker' aria-hidden='true'></span>", unsafe_allow_html=True)
    st.markdown(f"## {copy['journey']}")
    st.caption(copy["journey_help"])
    st.progress(
        int(state.get("progress_pct") or 0) / 100,
        text=f"{copy['project_progress']}: {int(state.get('completed_count') or 0)}/{int(state.get('total_steps') or 7)}",
    )

    cols = st.columns(len(guided_teacher_workflow.WORKFLOW_STEPS), gap="small")
    for index, (col, step) in enumerate(zip(cols, guided_teacher_workflow.WORKFLOW_STEPS), start=1):
        key = step["key"]
        status = statuses.get(key, "locked")
        spec = copy["steps"][key]
        with col:
            st.markdown(f"<span class='v6161-step-marker v6161-step-{escape(status)}' aria-hidden='true'></span>", unsafe_allow_html=True)
            if st.button(
                f"{index}. {spec['short']}",
                use_container_width=True,
                disabled=status == "locked",
                key=f"guided_workflow_step_{int(project['id'])}_{key}",
                help=copy["locked_help"] if status == "locked" else spec["description"],
            ):
                _set_workspace_section(step["section"])
            st.caption(copy["status"].get(status, status))

    with st.container(border=True):
        left, right = st.columns([4.7, 1.3], vertical_alignment="center")
        with left:
            st.caption(copy["current_step"])
            st.markdown(f"### {current_spec['title']}")
            st.write(current_spec["description"])
            st.caption(f"{current_spec['outcome']}")
        with right:
            if st.button(
                current_spec["action"],
                type="primary",
                use_container_width=True,
                key=f"guided_continue_{int(project['id'])}_{current_key}",
            ):
                _set_workspace_section(guided_teacher_workflow.section_for_step(current_key))

    lesson = dict(state.get("lesson_progress") or {})
    if int(lesson.get("required") or 0) > 0:
        approved = int(lesson.get("approved") or 0)
        required = int(lesson.get("required") or 0)
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
                            full_project = db.get_teacher_project(int(project["id"]), _current_teacher_username()) or project
                            journey = guided_teacher_workflow.load_workflow_state(full_project)
                            resume_section = guided_teacher_workflow.section_for_step(str(journey.get("current_key") or "setup"))
                            _open_project(int(project["id"]), resume_section)
                            st.rerun()


def _project_header(project: Dict[str, Any], workflow_state: Optional[Dict[str, Any]] = None) -> None:
    copy = project_workspace_ui()
    workflow_state = workflow_state or guided_teacher_workflow.load_workflow_state(project)
    completed = int(workflow_state.get("completed_count") or 0)
    total = int(workflow_state.get("total_steps") or 7)
    pct = int(workflow_state.get("progress_pct") or 0)
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
    st.progress(pct / 100, text=f"{copy['progress']}: {pct}% — {completed}/{total}")


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
                    st.success(copy["ready"]) if ready else st.caption(copy["not_ready"])


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
    phase_label = {"ar": "التفاصيل التقنية لمراحل التوليد القديمة", "fr": "Détails techniques des phases de génération", "en": "Technical phase-generation details"}.get(i18n.current_lang(st), "Technical phase-generation details")
    with st.expander(phase_label, expanded=False):
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



def render_lesson_blocks(project: Dict[str, Any]) -> None:
    """Render V6.16 block-level lesson generation and editing workspace."""
    lang = i18n.current_lang(st)
    labels = {
        "ar": {
            "title": "بناء محتوى الدرس على مستوى الكتل",
            "intro": "ولّد كل جزء من الدرس بصورة مستقلة، راجعه، عدّله واعتمده دون إعادة إنشاء الدرس كاملًا.",
            "blueprint_missing": "يجب اعتماد مخطط مقرر أولًا.",
            "lesson": "الدرس", "block": "كتلة المحتوى", "generate": "توليد هذه الكتلة بالذكاء الاصطناعي",
            "regenerate": "إعادة توليد الكتلة", "preview": "المعاينة", "edit": "مراجعة وتحرير",
            "versions": "الإصدارات", "audit": "سجل العمليات", "approve": "اعتماد الكتلة",
            "approved": "تم اعتماد هذه الكتلة.", "save": "حفظ إصدار جديد", "summary": "ملخص التعديل",
            "progress": "اكتمال الدرس", "no_output": "لم تُولّد هذه الكتلة بعد.", "download": "تنزيل الكتلة",
            "validation": "فحص الجودة", "provider": "المزوّد والنموذج", "latency": "زمن الاستجابة",
        },
        "fr": {
            "title": "Construction modulaire de la leçon", "intro": "Générez, révisez et approuvez chaque bloc séparément.",
            "blueprint_missing": "Un plan de cours approuvé est requis.", "lesson": "Leçon", "block": "Bloc",
            "generate": "Générer ce bloc", "regenerate": "Régénérer", "preview": "Aperçu", "edit": "Réviser",
            "versions": "Versions", "audit": "Journal", "approve": "Approuver le bloc", "approved": "Bloc approuvé.",
            "save": "Enregistrer une nouvelle version", "summary": "Résumé des modifications", "progress": "Achèvement",
            "no_output": "Ce bloc n’a pas encore été généré.", "download": "Télécharger", "validation": "Validation",
            "provider": "Fournisseur et modèle", "latency": "Latence",
        },
        "en": {
            "title": "Block-level lesson production", "intro": "Generate, review, edit, version, and approve each lesson block independently.",
            "blueprint_missing": "An approved course blueprint is required.", "lesson": "Lesson", "block": "Content block",
            "generate": "Generate this block with AI", "regenerate": "Regenerate block", "preview": "Preview", "edit": "Review and edit",
            "versions": "Versions", "audit": "Audit trail", "approve": "Approve block", "approved": "This block is approved.",
            "save": "Save new version", "summary": "Change summary", "progress": "Lesson completion",
            "no_output": "This block has not been generated yet.", "download": "Download block", "validation": "Quality validation",
            "provider": "Provider and model", "latency": "Latency",
        },
    }.get(lang, {})
    st.markdown(f"## {labels['title']}")
    st.write(labels["intro"])
    cfg = lesson_block_generation_engine.block_generation_status()
    if not cfg.get("enabled"):
        st.warning("ENABLE_LESSON_BLOCK_GENERATION is disabled.")
        return
    project_id = int(project["id"])
    blueprint = db.latest_teacher_blueprint(project_id, approved_only=True)
    if not blueprint:
        st.warning(labels["blueprint_missing"])
        return
    lessons = list((blueprint.get("blueprint") or {}).get("lessons") or [])
    lesson_options = {f"{item.get('lesson_id')} - {item.get('title')}": str(item.get("lesson_id")) for item in lessons}
    if not lesson_options:
        st.warning(labels["blueprint_missing"])
        return
    c1, c2 = st.columns(2)
    with c1:
        lesson_label = st.selectbox(labels["lesson"], list(lesson_options), key=f"block_lesson_{project_id}")
        lesson_id = lesson_options[lesson_label]
    with c2:
        block_options = {
            lesson_block_generation_engine.block_label(key, "ar" if lang == "ar" else "en"): key
            for key in lesson_block_generation_engine.BLOCK_SPECS
        }
        block_label = st.selectbox(labels["block"], list(block_options), key=f"block_type_{project_id}_{lesson_id}")
        block_type = block_options[block_label]

    completion = lesson_block_generation_engine.lesson_completion(project_id, lesson_id)
    st.progress(completion["approved"] / max(completion["required"], 1), text=f"{labels['progress']}: {completion['approved']}/{completion['required']}")
    latest = db.latest_teacher_lesson_block(project_id, lesson_id, block_type, approved_only=False)
    button_label = labels["regenerate"] if latest else labels["generate"]
    if st.button(button_label, type="primary", use_container_width=True, key=f"generate_block_{project_id}_{lesson_id}_{block_type}"):
        try:
            lesson_block_generation_engine.generate_and_persist(project, _current_teacher_username(), blueprint, lesson_id, block_type)
            st.session_state.teacher_flash_success = button_label
        except Exception as exc:
            st.session_state.teacher_flash_error = str(exc)
        st.rerun()

    latest = db.latest_teacher_lesson_block(project_id, lesson_id, block_type, approved_only=False)
    if not latest:
        st.info(labels["no_output"])
        return
    validation = latest.get("validation") or {}
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Status", str(latest.get("status") or "unknown"))
    m2.metric(labels["provider"], f"{latest.get('provider') or '-'} / {latest.get('model') or '-'}")
    m3.metric(labels["latency"], f"{int(latest.get('latency_ms') or 0)/1000:.1f}s")
    m4.metric("Words", int(latest.get("word_count") or 0))
    if int(latest.get("approved_by_teacher") or 0) == 1:
        st.success(labels["approved"])
    tabs = st.tabs([labels["preview"], labels["edit"], labels["versions"], labels["audit"]])
    with tabs[0]:
        _render_generation_markdown(str(latest.get("content_text") or ""), str(project.get("primary_language_code") or lang))
        st.caption(f"{labels['validation']}: {json.dumps(validation, ensure_ascii=False)}")
        st.download_button(labels["download"], data=str(latest.get("content_text") or ""), file_name=f"{lesson_id}_{block_type}_v{latest.get('version_number')}.md", mime="text/markdown", use_container_width=True)
        if int(latest.get("approved_by_teacher") or 0) != 1:
            if st.button(labels["approve"], type="primary", use_container_width=True, key=f"approve_block_{latest['id']}"):
                try:
                    db.approve_teacher_lesson_block(int(latest["id"]), project_id, _current_teacher_username())
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
        if not versions.empty:
            st.dataframe(versions, use_container_width=True, hide_index=True)
    with tabs[3]:
        audit = db.teacher_lesson_block_audit_df(project_id, lesson_id)
        if not audit.empty:
            st.dataframe(audit, use_container_width=True, hide_index=True)


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

    state = guided_teacher_workflow.load_workflow_state(project)
    _project_header(project, state)
    _render_guided_workflow(project, state)

    sections = [step["section"] for step in guided_teacher_workflow.WORKFLOW_STEPS]
    pending_section = st.session_state.pop("teacher_workspace_section_pending", None)
    if pending_section in sections:
        st.session_state.teacher_workspace_section = pending_section
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
    flash_warning = st.session_state.pop("teacher_flash_warning", None)
    if flash_warning:
        st.warning(str(flash_warning))
    flash_error = st.session_state.pop("teacher_flash_error", None)
    if flash_error:
        friendly, technical = _friendly_teacher_error(flash_error)
        st.error(friendly)
        details_label = {"ar": "التفاصيل التقنية", "fr": "Détails techniques", "en": "Technical details"}.get(i18n.current_lang(st), "Technical details")
        with st.expander(details_label, expanded=False):
            st.code(technical, language="text")
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

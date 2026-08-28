"""Learner runtime for teacher-authored published courses.

V6.20 turns teacher publication into an actual learning experience instead of a
read-only phase-output preview.  The runtime consumes only teacher-approved
blueprints and lesson blocks, pins each learner to a course version, preserves
an attempt-first support policy, and stores operational course data separately
from the controlled Qiskit research tables.
"""

from __future__ import annotations

from html import escape
from typing import Any, Dict, Iterable, List, Mapping, Optional

import streamlit as st

import adaptive_support_engine
import attempt_gate
import db
import feedback_engine
import global_design_system as global_ui
import i18n
import learner_model_engine
import lesson_content_renderer


BLOCK_LABELS = {
    "ar": {
        "activation": "استدعاء المعرفة السابقة",
        "explanation": "شرح المفهوم",
        "worked_example": "مثال محلول",
        "guided_practice": "تدريب موجّه",
        "independent_practice": "تدريب مستقل",
        "misconceptions": "أخطاء وتصورات شائعة",
        "formative_assessment": "تقويم تكويني",
        "summary": "خلاصة واسترجاع",
        "resources": "موارد للمتابعة",
    },
    "fr": {
        "activation": "Activation des acquis",
        "explanation": "Explication du concept",
        "worked_example": "Exemple résolu",
        "guided_practice": "Pratique guidée",
        "independent_practice": "Pratique autonome",
        "misconceptions": "Erreurs et conceptions fréquentes",
        "formative_assessment": "Évaluation formative",
        "summary": "Synthèse et rappel",
        "resources": "Ressources de suivi",
    },
    "en": {
        "activation": "Activate prior knowledge",
        "explanation": "Concept explanation",
        "worked_example": "Worked example",
        "guided_practice": "Guided practice",
        "independent_practice": "Independent practice",
        "misconceptions": "Common errors and misconceptions",
        "formative_assessment": "Formative assessment",
        "summary": "Summary and retrieval",
        "resources": "Follow-up resources",
    },
}


def _copy(lang: str) -> Dict[str, str]:
    values = {
        "ar": {
            "catalog": "دورات الأساتذة",
            "catalog_sub": "محتوى أنشأه الأساتذة وراجعوه واعتمدوه قبل النشر.",
            "back": "العودة إلى الدورات",
            "start": "ابدأ الدورة",
            "resume": "متابعة الدورة",
            "preview": "معاينة فقط",
            "legacy": "هذه الدورة منشورة بصيغة قديمة ولا تملك بعد حزمة دروس تفاعلية معتمدة.",
            "not_ready": "الحزمة التعليمية المنظمة غير مكتملة حاليًا.",
            "lesson": "الدرس",
            "lessons": "الدروس",
            "progress": "التقدم",
            "completed": "مكتمل",
            "course_complete": "أكملت هذه الدورة.",
            "attempt_title": "محاولتي قبل المساعدة",
            "attempt_help": "اكتب ما فهمته أو توقّعك أو طريقة الحل التي ستجربها قبل طلب المساعدة من المدرب الذكي.",
            "attempt_save": "حفظ المحاولة",
            "attempt_saved": "تم حفظ محاولتك.",
            "attempt_needed": "اكتب محاولة ذات معنى أولًا حتى يبقى الذكاء الاصطناعي أداة دعم لا بديلًا عن تفكيرك.",
            "coach": "المدرب الذكي لهذا الدرس",
            "coach_help": "الدعم مبني على محاولتك وعلى المحتوى الذي اعتمده الأستاذ في هذا الدرس.",
            "support": "الدعم المقترح",
            "ask": "ما الذي تريد مساعدة فيه؟",
            "ask_ph": "مثال: وصلت إلى هذه الخطوة لكنني لا أفهم لماذا نستخدم هذه القاعدة هنا...",
            "send": "اطلب دعمًا",
            "hint": "تلميح",
            "question": "سؤال موجّه",
            "explain": "شرح خطوة",
            "check": "تحقق من الفهم",
            "response": "رد المدرب",
            "reflection": "تأمل ختامي",
            "reflection_help": "اكتب باختصار: ما الفكرة التي أصبحت أوضح؟ وما الذي ستفعله بصورة مستقلة الآن؟",
            "complete_lesson": "إتمام الدرس والانتقال",
            "prev": "الدرس السابق",
            "next": "الدرس التالي",
            "outcomes": "نواتج التعلم",
            "approved": "محتوى معتمد من الأستاذ",
            "version": "إصدار الدورة",
            "teacher": "إعداد الأستاذ",
            "no_courses": "لا توجد دورات منشورة حاليًا.",
            "runtime_ready": "جاهزة للتعلّم",
            "runtime_legacy": "عرض قديم",
            "independent_evidence": "هذه المحاولة والتأمل بيانات تشغيلية للدورة ولا تُعامل كحكم آلي على الإتقان.",
            "save_before_complete": "احفظ محاولة مستقلة واكتب تأملًا قصيرًا قبل إتمام الدرس.",
            "words": "كلمة", "chars": "حرف", "evidence_coverage": "تغطية الأدلة",
            "activity": "نشاط", "assessment": "تقييم",
        },
        "fr": {
            "catalog": "Cours des enseignants",
            "catalog_sub": "Contenus créés, relus et approuvés par les enseignants avant publication.",
            "back": "Retour aux cours",
            "start": "Commencer le cours",
            "resume": "Reprendre le cours",
            "preview": "Aperçu seulement",
            "legacy": "Ce cours utilise encore l'ancien format de publication et ne dispose pas d'un parcours interactif approuvé.",
            "not_ready": "Le parcours structuré n'est pas encore complet.",
            "lesson": "Leçon",
            "lessons": "Leçons",
            "progress": "Progression",
            "completed": "Terminé",
            "course_complete": "Vous avez terminé ce cours.",
            "attempt_title": "Ma tentative avant l'aide",
            "attempt_help": "Écrivez ce que vous comprenez, votre prédiction ou la méthode que vous allez essayer avant de demander l'aide du coach IA.",
            "attempt_save": "Enregistrer la tentative",
            "attempt_saved": "Votre tentative a été enregistrée.",
            "attempt_needed": "Rédigez d'abord une tentative significative afin que l'IA reste un soutien et non un substitut à votre raisonnement.",
            "coach": "Coach IA de cette leçon",
            "coach_help": "Le soutien est fondé sur votre tentative et sur le contenu approuvé par l'enseignant.",
            "support": "Soutien recommandé",
            "ask": "De quoi avez-vous besoin ?",
            "ask_ph": "Exemple : je suis arrivé à cette étape mais je ne comprends pas pourquoi cette règle s'applique ici...",
            "send": "Demander de l'aide",
            "hint": "Indice",
            "question": "Question guidée",
            "explain": "Expliquer une étape",
            "check": "Vérifier ma compréhension",
            "response": "Réponse du coach",
            "reflection": "Réflexion finale",
            "reflection_help": "En quelques phrases : qu'est-ce qui est plus clair et que pouvez-vous faire seul maintenant ?",
            "complete_lesson": "Terminer la leçon et continuer",
            "prev": "Leçon précédente",
            "next": "Leçon suivante",
            "outcomes": "Objectifs d'apprentissage",
            "approved": "Contenu approuvé par l'enseignant",
            "version": "Version du cours",
            "teacher": "Préparé par",
            "no_courses": "Aucun cours n'est publié pour le moment.",
            "runtime_ready": "Prêt à apprendre",
            "runtime_legacy": "Ancien aperçu",
            "independent_evidence": "La tentative et la réflexion sont des traces opérationnelles du cours, pas un jugement automatique de maîtrise.",
            "save_before_complete": "Enregistrez une tentative autonome et une courte réflexion avant de terminer la leçon.",
            "words": "mots", "chars": "caractères", "evidence_coverage": "couverture des preuves",
            "activity": "Activité", "assessment": "Évaluation",
        },
        "en": {
            "catalog": "Teacher courses",
            "catalog_sub": "Content created, reviewed, and approved by teachers before publication.",
            "back": "Back to courses",
            "start": "Start course",
            "resume": "Resume course",
            "preview": "Preview only",
            "legacy": "This course still uses the legacy publication format and does not yet have an approved interactive lesson package.",
            "not_ready": "The structured learning package is not complete yet.",
            "lesson": "Lesson",
            "lessons": "Lessons",
            "progress": "Progress",
            "completed": "Completed",
            "course_complete": "You completed this course.",
            "attempt_title": "My attempt before support",
            "attempt_help": "Write what you understand, predict, or plan to try before asking the AI coach for support.",
            "attempt_save": "Save attempt",
            "attempt_saved": "Your attempt was saved.",
            "attempt_needed": "Write a meaningful attempt first so AI remains a support tool rather than a substitute for your reasoning.",
            "coach": "AI coach for this lesson",
            "coach_help": "Support is grounded in your attempt and the teacher-approved content for this lesson.",
            "support": "Recommended support",
            "ask": "What do you need help with?",
            "ask_ph": "Example: I reached this step but I do not understand why this rule applies here...",
            "send": "Ask for support",
            "hint": "Hint",
            "question": "Guiding question",
            "explain": "Explain one step",
            "check": "Check my understanding",
            "response": "Coach response",
            "reflection": "End-of-lesson reflection",
            "reflection_help": "Briefly write what became clearer and what you can now do independently.",
            "complete_lesson": "Complete lesson and continue",
            "prev": "Previous lesson",
            "next": "Next lesson",
            "outcomes": "Learning outcomes",
            "approved": "Teacher-approved content",
            "version": "Course version",
            "teacher": "Prepared by",
            "no_courses": "No courses are published yet.",
            "runtime_ready": "Ready to learn",
            "runtime_legacy": "Legacy preview",
            "independent_evidence": "The attempt and reflection are operational learning traces, not an automated mastery judgement.",
            "save_before_complete": "Save an independent attempt and a short reflection before completing the lesson.",
            "words": "words", "chars": "chars", "evidence_coverage": "evidence coverage",
            "activity": "Activity", "assessment": "Assessment",
        },
    }
    return values.get(lang, values["en"])


def _lang() -> str:
    value = str(i18n.current_lang(st) or "en").lower()
    return value if value in {"ar", "fr", "en"} else "en"


def _direction(lang: str) -> str:
    return "rtl" if lang == "ar" else "ltr"


def _response_language(lang: str) -> str:
    return {"ar": "Arabic", "fr": "French", "en": "English"}.get(lang, "English")


def _block_label(block_type: str, lang: str) -> str:
    return BLOCK_LABELS.get(lang, BLOCK_LABELS["en"]).get(str(block_type), str(block_type).replace("_", " ").title())


def _concept_names(blueprint: Mapping[str, Any]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for item in blueprint.get("concepts") or []:
        if not isinstance(item, Mapping):
            continue
        key = str(item.get("concept_id") or item.get("id") or "").strip()
        name = str(item.get("concept_name") or item.get("name") or item.get("title") or key).strip()
        if key:
            result[key] = name
    return result


def _lesson_concepts(lesson: Mapping[str, Any], blueprint: Mapping[str, Any]) -> List[str]:
    lookup = _concept_names(blueprint)
    result = []
    for value in lesson.get("concept_ids") or []:
        key = str(value or "").strip()
        if key:
            result.append(lookup.get(key, key))
    return result


def _lesson_outcomes(lesson_id: str, blueprint: Mapping[str, Any]) -> List[str]:
    values = []
    for item in blueprint.get("outcomes") or []:
        if not isinstance(item, Mapping) or str(item.get("lesson_id") or "") != str(lesson_id):
            continue
        verb = str(item.get("verb") or "").strip()
        obj = str(item.get("object") or item.get("object_text") or "").strip()
        criterion = str(item.get("success_criterion") or "").strip()
        statement = " ".join(part for part in (verb, obj) if part).strip()
        if criterion:
            statement = f"{statement} — {criterion}" if statement else criterion
        if statement:
            values.append(statement)
    return values


def _approved_blocks(project_id: int, blueprint_run_id: int, lesson_id: str) -> List[Dict[str, Any]]:
    return db.latest_approved_lesson_blocks(
        int(project_id), str(lesson_id), blueprint_run_id=int(blueprint_run_id)
    )


def _approved_excerpt(blocks: Iterable[Mapping[str, Any]], lang: str, max_chars: int = 7000) -> str:
    chunks: List[str] = []
    used = 0
    for row in blocks:
        clean = lesson_content_renderer.normalize_generated_markdown(str(row.get("content_text") or ""), lang)
        if not clean:
            continue
        remaining = max_chars - used
        if remaining <= 0:
            break
        chunks.append(clean[:remaining])
        used += len(chunks[-1])
    return "\n\n".join(chunks)


def _legacy_preview(project: Mapping[str, Any], copy: Mapping[str, str]) -> None:
    st.warning(copy["legacy"])
    outputs = db.teacher_project_phase_outputs(int(project["id"]))
    for phase, label in ((3, copy["lesson"]), (6, copy["activity"]), (8, copy["assessment"]), (7, copy["coach"])):
        row = outputs.get(phase)
        if not row or str(row.get("status") or "") != "completed":
            continue
        with st.expander(label, expanded=phase == 3):
            st.markdown(str(row.get("response_text") or ""))


def _pick_current_lesson(
    lessons: List[Dict[str, Any]],
    enrollment: Mapping[str, Any],
    progress_rows: List[Dict[str, Any]],
) -> str:
    lesson_ids = [str(item.get("lesson_id") or "") for item in lessons]
    current = str(enrollment.get("current_lesson_id") or "")
    if current in lesson_ids:
        return current
    completed = {str(row.get("lesson_id") or "") for row in progress_rows if str(row.get("status") or "") == "completed"}
    for lesson_id in lesson_ids:
        if lesson_id and lesson_id not in completed:
            return lesson_id
    return lesson_ids[-1] if lesson_ids else ""


def _render_catalog_card(student: Mapping[str, Any], project: Mapping[str, Any], lang: str, copy: Mapping[str, str]) -> None:
    project_id = int(project["id"])
    readiness = db.teacher_project_runtime_readiness(project_id)
    summary = db.published_course_progress_summary(int(student["id"]), project_id)
    enrolled = bool(summary.get("enrolled"))
    title = str(project.get("unit_title") or project.get("project_name") or "Course")
    domain = str(project.get("domain") or "")
    level = str(project.get("learner_level") or project.get("target_learners") or "")
    status_label = copy["runtime_ready"] if readiness.get("ready") else copy["runtime_legacy"]
    lesson_count = int(readiness.get("lesson_count") or 0)
    progress_pct = int(round(float(summary.get("progress") or 0.0) * 100))

    with st.container(border=True):
        st.markdown(
            f"<span class='v620-course-card-marker' aria-hidden='true'></span>"
            f"<div class='v620-course-card' dir='{_direction(lang)}'>"
            f"<div class='v620-course-card-top'><span>{escape(domain)}</span><b>{escape(status_label)}</b></div>"
            f"<h3>{escape(title)}</h3><p>{escape(str(project.get('target_concept') or ''))}</p>"
            f"<div class='v620-course-meta'><span>{escape(level)}</span><span>{lesson_count} {escape(copy['lessons'])}</span></div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        if enrolled:
            st.progress(float(summary.get("progress") or 0.0), text=f"{copy['progress']}: {progress_pct}%")
        label = copy["resume"] if enrolled else (copy["start"] if readiness.get("ready") else copy["preview"])
        if st.button(label, key=f"v620_open_course_{project_id}", type="primary" if readiness.get("ready") else "secondary", use_container_width=True):
            st.session_state.published_course_project_id = project_id
            st.rerun()


def render_catalog(student: Mapping[str, Any]) -> None:
    """Render the published-course catalogue or the selected course runtime."""
    lang = _lang()
    copy = _copy(lang)
    selected = st.session_state.get("published_course_project_id")
    if selected:
        project = db.get_published_teacher_project(int(selected))
        if project:
            if st.button(f"← {copy['back']}", key="v620_back_to_course_catalog"):
                st.session_state.published_course_project_id = None
                st.rerun()
            render_course(student, project)
            return
        st.session_state.published_course_project_id = None

    global_ui.render_page_header(
        copy["catalog"], copy["catalog_sub"], lang=lang,
        eyebrow="3alimnIA", status=copy["approved"], compact=True,
        icon="auto_stories", role="student",
    )
    projects = db.published_teacher_projects_df()
    if projects.empty:
        st.info(copy["no_courses"])
        return
    rows = projects.to_dict("records")
    for start in range(0, len(rows), 3):
        cols = st.columns(3, gap="large")
        for col, project in zip(cols, rows[start:start + 3]):
            with col:
                _render_catalog_card(student, project, lang, copy)


def render_course(student: Mapping[str, Any], project: Mapping[str, Any]) -> None:
    lang = _lang()
    copy = _copy(lang)
    project_id = int(project["id"])
    student_id = int(student["id"])
    enrollment = db.get_published_course_enrollment(student_id, project_id)

    if enrollment:
        blueprint = db.teacher_blueprint_bundle(int(enrollment.get("blueprint_run_id") or 0))
    else:
        blueprint = db.latest_teacher_blueprint(project_id, approved_only=True)

    if not blueprint:
        global_ui.render_page_header(
            str(project.get("unit_title") or project.get("project_name") or copy["catalog"]),
            str(project.get("target_concept") or ""), lang=lang,
            eyebrow=copy["teacher"], status=copy["runtime_legacy"], compact=True,
            icon="menu_book", role="student",
        )
        _legacy_preview(project, copy)
        return

    lessons = [dict(item) for item in (blueprint.get("lessons") or []) if isinstance(item, Mapping)]
    if not lessons:
        st.warning(copy["not_ready"])
        return

    blueprint_run_id = int(blueprint.get("id") or 0)
    first_lesson_id = str(lessons[0].get("lesson_id") or "")
    if not enrollment:
        readiness = db.teacher_project_runtime_readiness(project_id)
        if not readiness.get("ready"):
            global_ui.render_page_header(
                str(project.get("unit_title") or project.get("project_name") or copy["catalog"]),
                str(project.get("target_concept") or ""), lang=lang,
                eyebrow=copy["teacher"], status=copy["preview"], compact=True,
                icon="menu_book", role="student",
            )
            st.warning(str(readiness.get("reason") or copy["not_ready"]))
            _legacy_preview(project, copy)
            return
        enrollment = db.start_published_course_enrollment(
            student_id, project_id, blueprint_run_id, first_lesson_id
        )

    progress_df = db.published_course_lesson_progress_df(student_id, project_id, blueprint_run_id)
    progress_rows = progress_df.to_dict("records") if not progress_df.empty else []
    completed_ids = {
        str(row.get("lesson_id") or "")
        for row in progress_rows
        if str(row.get("status") or "").lower() == "completed"
    }
    completed_count = len(completed_ids.intersection({str(item.get("lesson_id") or "") for item in lessons}))
    progress_value = completed_count / len(lessons) if lessons else 0.0

    title = str(project.get("unit_title") or project.get("project_name") or "Course")
    global_ui.render_page_header(
        title,
        str(project.get("target_concept") or ""),
        lang=lang,
        eyebrow=copy["teacher"],
        status=copy["completed"] if completed_count == len(lessons) else copy["runtime_ready"],
        meta=[
            str(project.get("domain") or ""),
            str(project.get("learner_level") or ""),
            f"{copy['version']} {int(blueprint.get('version_number') or 1)}",
        ],
        compact=True,
        icon="school",
        role="student",
    )
    st.progress(progress_value, text=f"{copy['progress']}: {completed_count}/{len(lessons)}")
    if completed_count == len(lessons):
        st.success(copy["course_complete"], icon="✅")

    current_id = _pick_current_lesson(lessons, enrollment, progress_rows)
    lesson_ids = [str(item.get("lesson_id") or "") for item in lessons]
    titles = {
        str(item.get("lesson_id") or ""): str(item.get("title") or item.get("lesson_id") or copy["lesson"])
        for item in lessons
    }
    first_incomplete_index = next(
        (idx for idx, lesson_id in enumerate(lesson_ids) if lesson_id not in completed_ids),
        len(lesson_ids) - 1,
    )
    max_unlocked_index = len(lesson_ids) - 1 if completed_count == len(lessons) else first_incomplete_index
    unlocked_ids = lesson_ids[: max_unlocked_index + 1]
    if current_id not in unlocked_ids:
        current_id = unlocked_ids[-1]
        db.set_published_course_position(student_id, project_id, current_id)
    current_index = lesson_ids.index(current_id) if current_id in lesson_ids else 0
    option_labels = [
        f"{'✓ ' if lesson_id in completed_ids else ''}{idx + 1}. {titles.get(lesson_id, lesson_id)}"
        for idx, lesson_id in enumerate(unlocked_ids)
    ]
    selected_label = st.selectbox(
        copy["lessons"], option_labels, index=unlocked_ids.index(current_id),
        key=f"v620_lesson_selector_{student_id}_{project_id}_{blueprint_run_id}",
    )
    selected_id = unlocked_ids[option_labels.index(selected_label)]
    if selected_id != current_id:
        db.set_published_course_position(student_id, project_id, selected_id)
        current_id = selected_id
        current_index = lesson_ids.index(selected_id)

    lesson = lessons[current_index]
    blocks = _approved_blocks(project_id, blueprint_run_id, current_id)
    if not blocks:
        st.warning(copy["not_ready"])
        return

    global_ui.render_section_header(
        f"{current_index + 1}. {titles.get(current_id, current_id)}",
        f"{copy['approved']} · {len(blocks)}",
        lang=lang,
        eyebrow=copy["lesson"],
    )
    outcomes = _lesson_outcomes(current_id, blueprint)
    if outcomes:
        with st.expander(copy["outcomes"], expanded=False):
            for outcome in outcomes:
                st.markdown(f"- {outcome}")

    for row in blocks:
        block_type = str(row.get("block_type") or "")
        content = lesson_content_renderer.normalize_generated_markdown(
            str(row.get("content_text") or ""), lang
        )
        with st.container(border=True):
            st.caption(_block_label(block_type, lang))
            st.markdown(content)

    _render_attempt_and_coach(
        student=student,
        project=project,
        blueprint=blueprint,
        lesson=lesson,
        blocks=blocks,
        lesson_index=current_index,
        lesson_ids=lesson_ids,
        completed_ids=completed_ids,
        max_unlocked_index=max_unlocked_index,
        lang=lang,
        copy=copy,
    )


def _render_attempt_and_coach(
    *,
    student: Mapping[str, Any],
    project: Mapping[str, Any],
    blueprint: Mapping[str, Any],
    lesson: Mapping[str, Any],
    blocks: List[Dict[str, Any]],
    lesson_index: int,
    lesson_ids: List[str],
    completed_ids: set[str],
    max_unlocked_index: int,
    lang: str,
    copy: Mapping[str, str],
) -> None:
    student_id = int(student["id"])
    project_id = int(project["id"])
    blueprint_run_id = int(blueprint.get("id") or 0)
    lesson_id = str(lesson.get("lesson_id") or "")
    progress = db.get_published_course_lesson_progress(student_id, project_id, blueprint_run_id, lesson_id) or {}

    st.divider()
    global_ui.render_section_header(copy["attempt_title"], copy["attempt_help"], lang=lang, eyebrow="Attempt first")
    attempt_key = f"v620_attempt_{student_id}_{project_id}_{blueprint_run_id}_{lesson_id}"
    if attempt_key not in st.session_state:
        st.session_state[attempt_key] = str(progress.get("independent_attempt_text") or "")
    st.text_area(copy["attempt_title"], key=attempt_key, height=130, label_visibility="collapsed")
    validation = attempt_gate.validate_attempt_text(st.session_state.get(attempt_key, ""), lang)
    st.progress(
        validation.readiness,
        text=f"{validation.word_count}/{attempt_gate.MIN_ATTEMPT_WORDS} {copy['words']} · "
             f"{validation.char_count}/{attempt_gate.MIN_ATTEMPT_CHARS} {copy['chars']}",
    )
    if validation.is_valid:
        st.caption(copy["independent_evidence"])
    else:
        st.info(copy["attempt_needed"])
    if st.button(copy["attempt_save"], key=f"v620_save_attempt_{student_id}_{project_id}_{lesson_id}", use_container_width=True, disabled=not validation.is_valid):
        db.save_published_course_attempt(
            student_id=student_id,
            project_id=project_id,
            blueprint_run_id=blueprint_run_id,
            lesson_id=lesson_id,
            attempt_text=validation.normalized_text,
        )
        st.success(copy["attempt_saved"])
        st.rerun()

    # Refresh after a save/rerun; the AI gate trusts the database, not only the widget.
    progress = db.get_published_course_lesson_progress(student_id, project_id, blueprint_run_id, lesson_id) or {}
    saved_attempt = str(progress.get("independent_attempt_text") or "").strip()
    valid_saved_attempt = attempt_gate.validate_attempt_text(saved_attempt, lang)

    global_ui.render_section_header(copy["coach"], copy["coach_help"], lang=lang, eyebrow="Adaptive AI Coach")
    interactions_df = db.published_course_ai_interactions_df(student_id, project_id, lesson_id, limit=20)
    interactions = interactions_df.to_dict("records") if not interactions_df.empty else []
    learner_attempt = {
        "attempt_text": saved_attempt,
        "validation_status": "submitted_for_support" if valid_saved_attempt.is_valid else "missing",
        "word_count": valid_saved_attempt.word_count,
        "unique_word_count": valid_saved_attempt.unique_word_count,
    } if saved_attempt else None
    learner_profile = learner_model_engine.build_learner_evidence_profile(
        learner_attempt=learner_attempt,
        lesson_progress={
            "completed": 1 if lesson_id in completed_ids else 0,
            "reflection_text": str(progress.get("reflection_text") or ""),
        } if progress else None,
        language_code=lang,
    )
    concepts = _lesson_concepts(lesson, blueprint)
    adaptive = adaptive_support_engine.recommend_support(
        lesson={"concepts": concepts},
        learner_attempt=learner_attempt,
        recent_interactions=interactions,
        learner_evidence_profile=learner_profile,
        language_code=lang,
    )
    confidence_pct = int(round(float(adaptive.get("confidence") or 0.0) * 100))
    st.markdown(
        f"<section class='v620-support-card' dir='{_direction(lang)}'>"
        f"<div><small>{escape(copy['support'])}</small><strong>{escape(str(adaptive.get('label') or ''))}</strong></div>"
        f"<p>{escape(str(adaptive.get('rationale') or ''))}</p><span>{confidence_pct}% {escape(copy['evidence_coverage'])}</span>"
        f"</section>",
        unsafe_allow_html=True,
    )

    mode_options = {
        "question": (copy["question"], "Ask one guiding question that helps the learner inspect their current reasoning."),
        "hint": (copy["hint"], "Give one graduated hint and one check question without revealing a complete answer."),
        "explain": (copy["explain"], "Explain one difficult step using an analogous example, then ask the learner to retry."),
        "check": (copy["check"], "Check the learner's reasoning against the lesson outcomes and give one actionable correction."),
    }
    recommended_mode = str(adaptive.get("mode") or "hint")
    if recommended_mode not in mode_options:
        recommended_mode = "hint"
    mode_key = f"v620_mode_{student_id}_{project_id}_{lesson_id}"
    if st.session_state.get(mode_key) not in mode_options:
        st.session_state[mode_key] = recommended_mode
    selected_mode = st.radio(
        copy["support"],
        list(mode_options.keys()),
        format_func=lambda key: mode_options[key][0],
        horizontal=True,
        key=mode_key,
        disabled=not valid_saved_attempt.is_valid,
    )
    question_key = f"v620_question_{student_id}_{project_id}_{lesson_id}"
    st.text_area(copy["ask"], key=question_key, placeholder=copy["ask_ph"], height=105, disabled=not valid_saved_attempt.is_valid)

    if st.button(
        copy["send"], type="primary", use_container_width=True,
        key=f"v620_send_{student_id}_{project_id}_{lesson_id}",
        disabled=not valid_saved_attempt.is_valid,
    ):
        # Server-side attempt-first gate.
        progress = db.get_published_course_lesson_progress(student_id, project_id, blueprint_run_id, lesson_id) or {}
        saved_attempt = str(progress.get("independent_attempt_text") or "")
        valid_saved_attempt = attempt_gate.validate_attempt_text(saved_attempt, lang)
        if not valid_saved_attempt.is_valid:
            st.warning(copy["attempt_needed"])
        else:
            chosen_label, instruction = mode_options[selected_mode]
            learner_text = saved_attempt
            extra_question = str(st.session_state.get(question_key) or "").strip()
            if extra_question:
                learner_text = f"{saved_attempt}\n\nLearner question: {extra_question}"
            excerpt = _approved_excerpt(blocks, lang)
            lesson_context = {
                "response_language": _response_language(lang),
                "course_title": str(project.get("unit_title") or project.get("project_name") or ""),
                "lesson_title": str(lesson.get("title") or lesson_id),
                "domain": str(project.get("domain") or ""),
                "learner_level": str(project.get("learner_level") or project.get("target_learners") or ""),
                "concepts": concepts,
                "learning_outcomes": _lesson_outcomes(lesson_id, blueprint),
                "approved_lesson_excerpt": excerpt,
                "adaptive_support_level": adaptive.get("level"),
                "adaptive_support_mode": adaptive.get("mode"),
                "adaptive_support_contract": adaptive_support_engine.prompt_contract(adaptive, chosen_mode=selected_mode),
            }
            task = f"{chosen_label}: {instruction}"
            prompt = feedback_engine.build_course_prompt(
                task, ", ".join(concepts), learner_text,
                student_profile={
                    "academic_level": student.get("academic_level"),
                    "preferred_language": student.get("preferred_language"),
                },
                lesson_context=lesson_context,
            )
            with st.spinner("…"):
                tutor = feedback_engine.generate_course_tutor_response(
                    task=task,
                    concept=", ".join(concepts) or str(project.get("target_concept") or lesson.get("title") or ""),
                    student_input=learner_text,
                    student_profile={
                        "academic_level": student.get("academic_level"),
                        "preferred_language": student.get("preferred_language"),
                    },
                    lesson_context=lesson_context,
                )
            interaction_id = db.log_published_course_ai_interaction(
                student_id=student_id,
                project_id=project_id,
                blueprint_run_id=blueprint_run_id,
                lesson_id=lesson_id,
                task=task,
                prompt=prompt,
                response=tutor.response,
                mode=tutor.mode,
                provider=tutor.provider,
                model=tutor.model,
                diagnostic=tutor.diagnostic,
                adaptive_support_level=adaptive.get("level"),
                adaptive_support_mode=str(adaptive.get("mode") or ""),
                adaptive_support_confidence=adaptive.get("confidence"),
                adaptive_support_reason=str(adaptive.get("reason") or ""),
            )
            st.session_state[f"v620_response_{student_id}_{project_id}_{lesson_id}"] = {
                "text": tutor.response,
                "id": interaction_id,
            }
            st.rerun()

    response = st.session_state.get(f"v620_response_{student_id}_{project_id}_{lesson_id}")
    if response:
        st.caption(copy["response"])
        with st.chat_message("assistant"):
            st.write(str(response.get("text") or ""))

    st.divider()
    global_ui.render_section_header(copy["reflection"], copy["reflection_help"], lang=lang, eyebrow="Reflect")
    reflection_key = f"v620_reflection_{student_id}_{project_id}_{lesson_id}"
    if reflection_key not in st.session_state:
        st.session_state[reflection_key] = str(progress.get("reflection_text") or "")
    st.text_area(copy["reflection"], key=reflection_key, height=115, label_visibility="collapsed")
    reflection = str(st.session_state.get(reflection_key) or "").strip()
    can_complete = valid_saved_attempt.is_valid and len(reflection.split()) >= 4
    if not can_complete:
        st.caption(copy["save_before_complete"])

    nav_left, nav_center, nav_right = st.columns([1, 1.6, 1])
    with nav_left:
        if lesson_index > 0 and st.button(copy["prev"], use_container_width=True, key=f"v620_prev_{project_id}_{lesson_id}"):
            db.set_published_course_position(student_id, project_id, lesson_ids[lesson_index - 1])
            st.rerun()
    with nav_center:
        if st.button(
            copy["complete_lesson"], type="primary", use_container_width=True,
            key=f"v620_complete_{project_id}_{lesson_id}", disabled=not can_complete,
        ):
            db.complete_published_course_lesson(
                student_id=student_id,
                project_id=project_id,
                blueprint_run_id=blueprint_run_id,
                lesson_id=lesson_id,
                reflection_text=reflection,
            )
            next_index = lesson_index + 1
            if next_index < len(lesson_ids):
                db.set_published_course_position(student_id, project_id, lesson_ids[next_index])
            else:
                db.set_published_course_position(student_id, project_id, lesson_id, completed=True)
            st.rerun()
    with nav_right:
        next_unlocked = lesson_index + 1 < len(lesson_ids) and lesson_index + 1 <= max_unlocked_index
        if lesson_index + 1 < len(lesson_ids) and st.button(
            copy["next"], use_container_width=True, key=f"v620_next_{project_id}_{lesson_id}", disabled=not next_unlocked
        ):
            db.set_published_course_position(student_id, project_id, lesson_ids[lesson_index + 1])
            st.rerun()

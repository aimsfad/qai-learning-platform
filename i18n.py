"""Application-wide internationalization for 3alimnIA.

The platform keeps stable internal route/data keys in English while rendering the
interface in Arabic, French, or English. Arabic activates right-to-left layout.
"""
from __future__ import annotations

import re
from functools import lru_cache
from typing import Any, Dict, Iterable, Mapping

LANGUAGE_LABELS: Dict[str, str] = {
    "ar": "العربية",
    "fr": "Français",
    "en": "English",
}
LABEL_TO_CODE = {label: code for code, label in LANGUAGE_LABELS.items()}
SUPPORTED_LANGUAGES = tuple(LANGUAGE_LABELS)
DEFAULT_LANGUAGE = "ar"


def normalize_lang(value: str | None) -> str:
    raw = str(value or "").strip()
    if raw in SUPPORTED_LANGUAGES:
        return raw
    if raw in LABEL_TO_CODE:
        return LABEL_TO_CODE[raw]
    aliases = {
        "arabic": "ar", "arabic (العربية)": "ar", "العربية": "ar", "ar": "ar",
        "french": "fr", "français": "fr", "francais": "fr", "fr": "fr",
        "english": "en", "en": "en",
        "auto-detect": DEFAULT_LANGUAGE, "auto": DEFAULT_LANGUAGE,
    }
    return aliases.get(raw.lower(), DEFAULT_LANGUAGE)


def current_lang(st_module: Any | None = None) -> str:
    if st_module is None:
        try:
            import streamlit as st_module  # type: ignore
        except Exception:
            return DEFAULT_LANGUAGE
    try:
        code = st_module.session_state.get("ui_language_code")
        if code:
            return normalize_lang(code)
        return normalize_lang(st_module.session_state.get("ui_language"))
    except Exception:
        return DEFAULT_LANGUAGE


def direction(lang: str | None = None) -> str:
    return "rtl" if normalize_lang(lang) == "ar" else "ltr"


def response_language(lang: str | None = None) -> str:
    return {"ar": "Arabic", "fr": "French", "en": "English"}[normalize_lang(lang)]

# Canonical internal page names -> localized display labels.
PAGE_LABELS: Dict[str, Dict[str, str]] = {
    "Student Home": {"ar": "الرئيسية", "fr": "Accueil apprenant", "en": "Student Home"},
    "Sign in": {"ar": "تسجيل الدخول", "fr": "Se connecter", "en": "Sign in"},
    "Create account": {"ar": "إنشاء حساب", "fr": "Créer un compte", "en": "Create account"},
    "Research Notice": {"ar": "إشعار البحث والموافقة", "fr": "Notice de recherche", "en": "Research Notice"},
    "Pre-test": {"ar": "الاختبار القبلي", "fr": "Pré-test", "en": "Pre-test"},
    "Adaptive Plan": {"ar": "خطة التعلم التكيفية", "fr": "Plan adaptatif", "en": "Adaptive Plan"},
    "Learning Module": {"ar": "المسار التعليمي", "fr": "Parcours d'apprentissage", "en": "Learning Module"},
    "Published Courses": {"ar": "مقررات الأساتذة", "fr": "Cours des enseignants", "en": "Teacher Courses"},
    "AI Tutor Lab": {"ar": "مختبر المدرّب الذكي", "fr": "Laboratoire du coach IA", "en": "AI Tutor Lab"},
    "Post-test": {"ar": "الاختبار البعدي", "fr": "Post-test", "en": "Post-test"},
    "Satisfaction Survey": {"ar": "استبيان الرضا", "fr": "Questionnaire de satisfaction", "en": "Satisfaction Survey"},
    "Evaluator Dashboard": {"ar": "لوحة المقيّم", "fr": "Tableau de bord évaluateur", "en": "Evaluator Dashboard"},
    "Study Protocol": {"ar": "بروتوكول الدراسة", "fr": "Protocole d'étude", "en": "Study Protocol"},
    "Students": {"ar": "المتعلمون", "fr": "Apprenants", "en": "Students"},
    "Registration Accounts": {"ar": "حسابات التسجيل", "fr": "Comptes d'inscription", "en": "Registration Accounts"},
    "Student Details": {"ar": "تفاصيل المتعلم", "fr": "Détails de l'apprenant", "en": "Student Details"},
    "AI Tutor Logs": {"ar": "سجلات المدرّب الذكي", "fr": "Journaux du coach IA", "en": "AI Tutor Logs"},
    "AI Response Evaluation": {"ar": "تقييم استجابات الذكاء الاصطناعي", "fr": "Évaluation des réponses IA", "en": "AI Response Evaluation"},
    "AI Metrics": {"ar": "مؤشرات الذكاء الاصطناعي", "fr": "Indicateurs IA", "en": "AI Metrics"},
    "Exports": {"ar": "التصدير", "fr": "Exports", "en": "Exports"},
}

PAGE_DETAILS: Dict[str, Dict[str, str]] = {
    "Student Home": {"ar": "نظرة عامة والخطوة التالية", "fr": "Vue d'ensemble et prochaine étape", "en": "Overview and next action"},
    "Research Notice": {"ar": "خطوة الموافقة", "fr": "Étape de consentement", "en": "Consent step"},
    "Pre-test": {"ar": "قياس المعرفة الأولية", "fr": "Évaluation initiale", "en": "Initial knowledge check"},
    "Learning Module": {"ar": "ست وحدات موجّهة", "fr": "Six modules guidés", "en": "Six guided modules"},
    "Published Courses": {"ar": "محتوى منشور من الأساتذة", "fr": "Contenus publiés par les enseignants", "en": "Teacher-published learning content"},
    "AI Tutor Lab": {"ar": "اطلب تلميحات وشروحات", "fr": "Demander des indices et explications", "en": "Ask for hints and explanations"},
    "Post-test": {"ar": "يفتح بعد إكمال المسار", "fr": "Débloqué après le parcours", "en": "Unlocked after learning path"},
    "Satisfaction Survey": {"ar": "التغذية الراجعة النهائية", "fr": "Retour final", "en": "Final feedback"},
}

CONCEPT_LABELS: Dict[str, Dict[str, str]] = {
    "Circuit basics": {"ar": "أساسيات الدارة الكمية", "fr": "Bases du circuit quantique", "en": "Circuit basics"},
    "Qubit measurement": {"ar": "قياس الكيوبت", "fr": "Mesure du qubit", "en": "Qubit measurement"},
    "Hadamard and superposition": {"ar": "بوابة هادامارد والتراكب", "fr": "Hadamard et superposition", "en": "Hadamard and superposition"},
    "Shots and counts": {"ar": "التكرارات والعدّادات", "fr": "Shots et comptages", "en": "Shots and counts"},
    "CNOT and correlation": {"ar": "بوابة CNOT والارتباط", "fr": "CNOT et corrélation", "en": "CNOT and correlation"},
    "Qiskit debugging": {"ar": "تصحيح أخطاء Qiskit", "fr": "Débogage Qiskit", "en": "Qiskit debugging"},
    "Quantum circuit": {"ar": "الدارة الكمية", "fr": "Circuit quantique", "en": "Quantum circuit"},
    "Classical vs quantum": {"ar": "الكلاسيكي مقابل الكمي", "fr": "Classique et quantique", "en": "Classical vs quantum"},
    "Qubit, state, and measurement": {"ar": "الكيوبت والحالة والقياس", "fr": "Qubit, état et mesure", "en": "Qubit, state, and measurement"},
    "Measurement": {"ar": "القياس", "fr": "Mesure", "en": "Measurement"},
    "Hadamard gate": {"ar": "بوابة هادامارد", "fr": "Porte de Hadamard", "en": "Hadamard gate"},
    "CNOT gate": {"ar": "بوابة CNOT", "fr": "Porte CNOT", "en": "CNOT gate"},
    "Entanglement intuition": {"ar": "الحدس حول التشابك", "fr": "Intuition de l'intrication", "en": "Entanglement intuition"},
    "Qiskit syntax": {"ar": "صياغة Qiskit", "fr": "Syntaxe Qiskit", "en": "Qiskit syntax"},
    "Debugging": {"ar": "تصحيح الأخطاء", "fr": "Débogage", "en": "Debugging"},
}

COGNITIVE_LEVELS = {
    "Recall": {"ar": "تذكّر", "fr": "Mémorisation", "en": "Recall"},
    "Understanding": {"ar": "فهم", "fr": "Compréhension", "en": "Understanding"},
    "Application": {"ar": "تطبيق", "fr": "Application", "en": "Application"},
}

LEVEL_LABELS = {
    "Foundation": {"ar": "تأسيسي", "fr": "Fondation", "en": "Foundation"},
    "Core concept": {"ar": "مفهوم أساسي", "fr": "Concept central", "en": "Core concept"},
    "Interpretation": {"ar": "تفسير", "fr": "Interprétation", "en": "Interpretation"},
    "Two-qubit reasoning": {"ar": "استدلال بكيوبتين", "fr": "Raisonnement à deux qubits", "en": "Two-qubit reasoning"},
    "Practice": {"ar": "تطبيق", "fr": "Pratique", "en": "Practice"},
}

# Exact/phrase translations used by the Streamlit translation layer. Longer
# keys are replaced first, so they also localize HTML and dynamic f-strings.
AR: Dict[str, str] = {
    "How to choose the 0–3 level:": "كيف تختار المستوى من 0 إلى 3:",
    "No prior knowledge.": "لا توجد معرفة سابقة.",
    "Basic awareness: I have heard about it, but I cannot explain it well.": "معرفة أولية: سمعت عنه، لكنني لا أستطيع شرحه جيدًا.",
    "Some understanding: I can explain basic ideas with help.": "فهم جزئي: أستطيع شرح الأفكار الأساسية بمساعدة.",
    "Good understanding: I can apply or explain it confidently.": "فهم جيد: أستطيع تطبيقه أو شرحه بثقة.",
    "Save your participant code now. You will need it if you return later. Do not create a second account.": "احفظ رمز مشاركتك الآن. ستحتاج إليه عند العودة لاحقًا. لا تنشئ حسابًا ثانيًا.",
    "Tip: copy the code to your notes or take a screenshot before continuing.": "نصيحة: انسخ الرمز إلى ملاحظاتك أو التقط صورة للشاشة قبل المتابعة.",
    "This participation is complete for analysis.": "اكتملت هذه المشاركة وأصبحت جاهزة للتحليل.",
    "Use after reading this part: the AI should clarify the idea, not replace your reasoning.": "استخدمه بعد قراءة هذا الجزء: يجب أن يوضح الذكاء الاصطناعي الفكرة لا أن يستبدل تفكيرك.",
    "Was this AI response useful for your learning?": "هل كانت استجابة الذكاء الاصطناعي مفيدة لتعلّمك؟",
    "This helps the evaluator assess the pedagogical quality of AI support.": "يساعد ذلك المقيّم على تقدير الجودة التربوية لدعم الذكاء الاصطناعي.",
    "AI usefulness rating saved.": "تم حفظ تقييم فائدة الاستجابة.",
    "AI tutor interactions and progress events are logged for the evaluator dashboard.": "تُسجَّل تفاعلات المدرّب الذكي وأحداث التقدم في لوحة المقيّم.",
    "Choose a learning path or open the evaluator workspace from the 3alimnIA home page.": "اختر مسارًا تعليميًا أو افتح فضاء المقيّم من الصفحة الرئيسية لعلّمنيا.",
    "A guided Qiskit learning workspace with visual explanations, learner-first attempts, contextual AI scaffolding, and measurable progress evidence.": "فضاء موجّه لتعلّم Qiskit يجمع الشرح البصري، ومحاولة المتعلم أولًا، ودعمًا توليديًا سياقيًا، وأدلة قابلة للقياس على التقدم.",
    "The platform combines a structured learning path, short visual explanations, pre/post assessment, and an AI tutor that encourages reasoning rather than copy-paste answers.": "تجمع المنصة مسارًا منظمًا، وشروحات بصرية قصيرة، واختبارًا قبليًا وبعديًا، ومدرّبًا ذكيًا يشجع الاستدلال بدل نسخ الإجابات.",
    "Use your participant code, email, or exact registered name with your password.": "استخدم رمز المشاركة أو البريد الإلكتروني أو الاسم المسجل كاملًا مع كلمة المرور.",
    "Register as a study participant. If the study is protected, you will need the registration access code.": "سجّل بوصفك مشاركًا في الدراسة. إذا كانت الدراسة محمية فستحتاج إلى رمز الدخول الخاص بالتسجيل.",
    "Account created successfully. Save your participant code before continuing.": "أُنشئ الحساب بنجاح. احفظ رمز المشاركة قبل المتابعة.",
    "Please read this notice before continuing the study workflow.": "يرجى قراءة هذا الإشعار قبل متابعة خطوات الدراسة.",
    "This platform is used for a pilot evaluation of AI-supported learning for introductory quantum programming.": "تُستخدم هذه المنصة في تقييم تجريبي للتعلّم المدعوم بالذكاء الاصطناعي في مدخل البرمجة الكمية.",
    "Your pre-test, post-test, learning progress, reflections, survey answers, and AI tutor interactions will be recorded for research analysis.": "ستُسجَّل نتائج الاختبارين القبلي والبعدي، وتقدم التعلم، والتأملات، وإجابات الاستبيان، وتفاعلات المدرّب الذكي لأغراض التحليل البحثي.",
    "Your participant code is used to organize the data. Avoid creating multiple accounts.": "يُستخدم رمز المشاركة لتنظيم البيانات. تجنب إنشاء حسابات متعددة.",
    "AI tutor responses may be reviewed by the evaluator to assess conceptual accuracy, relevance, scaffolding, and feedback quality.": "قد يراجع المقيّم استجابات المدرّب الذكي لتقدير الدقة المفاهيمية والملاءمة وجودة السقالات والتغذية الراجعة.",
    "The AI tutor is a learning support tool. It should not replace your own reasoning.": "المدرّب الذكي أداة لدعم التعلم ولا ينبغي أن يستبدل استدلالك الشخصي.",
    "I have read the study notice and agree to participate in this pilot evaluation.": "قرأت إشعار الدراسة وأوافق على المشاركة في هذا التقييم التجريبي.",
    "Enter the email address used during registration. If it exists in the study database, a reset link will be sent.": "أدخل البريد الإلكتروني المستعمل عند التسجيل. إذا كان موجودًا في قاعدة الدراسة فسيُرسل رابط إعادة التعيين.",
    "Please enter and confirm your new password. Reset links are valid for a limited time and can be used only once.": "أدخل كلمة المرور الجديدة وأكّدها. رابط إعادة التعيين صالح لمدة محدودة ويُستخدم مرة واحدة فقط.",
    "Answer the questions individually. This is used to evaluate learning progress, not to grade you.": "أجب عن الأسئلة بصورة فردية. يُستخدم الاختبار لقياس تقدم التعلم لا لمنح علامة دراسية.",
    "Please complete at least one learning section and save its reflection before the post-test.": "أكمل قسمًا تعليميًا واحدًا على الأقل واحفظ تأملك قبل الاختبار البعدي.",
    "Please complete at least one AI Tutor interaction before the post-test. This applies only to the experimental AI-supported group.": "أنجز تفاعلًا واحدًا على الأقل مع المدرّب الذكي قبل الاختبار البعدي. ينطبق ذلك على المجموعة التجريبية المدعومة بالذكاء الاصطناعي فقط.",
    "The platform uses your pre-test results to recommend learning sections and AI-supported practice.": "تستخدم المنصة نتائج الاختبار القبلي لاقتراح أقسام التعلم والتطبيق المدعوم بالذكاء الاصطناعي.",
    "No major weakness detected. Continue with the full learning sequence.": "لم تُكتشف صعوبة رئيسية. تابع التسلسل التعليمي كاملًا.",
    "Generate a concise study plan based on the learner profile and weak concepts.": "أنشئ خطة تعلم موجزة بناءً على ملف المتعلم والمفاهيم التي تحتاج إلى تعزيز.",
    "The LLM service was unavailable, so a local fallback was shown and logged for the evaluator.": "تعذرت خدمة النموذج اللغوي، لذلك عُرض بديل محلي وسُجّل للمقيّم.",
    "Follow the four steps in order. The AI coach is used after your first attempt, not before it.": "اتبع الخطوات الأربع بالترتيب. يُستخدم المدرّب الذكي بعد محاولتك الأولى لا قبلها.",
    "Choose the step you are working on, write your attempt, then ask the AI for a limited type of support.": "اختر الخطوة التي تعمل عليها، واكتب محاولتك، ثم اطلب نوعًا محددًا من الدعم الذكي.",
    "Generate polished learning supports after writing your own attempt. Outputs are curated around the current lesson, not open-ended free generation.": "أنشئ دعائم تعليمية منظمة بعد كتابة محاولتك. تُبنى المخرجات حول الدرس الحالي وليست توليدًا مفتوحًا بلا قيود.",
    "write your own attempt first. The builder produces structured explanations, analogies, checks, Qiskit bridges, and safe visual cards from approved pedagogical templates.": "اكتب محاولتك أولًا. ينتج الباني شروحات منظمة وتشبيهات وفحوصًا وجسور Qiskit وبطاقات بصرية آمنة انطلاقًا من قوالب تربوية معتمدة.",
    "Write a short attempt first. This preserves the research value of measuring AI-supported learning after learner effort.": "اكتب محاولة قصيرة أولًا. يحافظ ذلك على القيمة البحثية لقياس التعلم المدعوم بالذكاء الاصطناعي بعد جهد المتعلم.",
    "Concept animation will appear here once the MP4 is available.": "ستظهر الرسوم المتحركة للمفهوم هنا عند توفر ملف MP4.",
    "Interactive simulator missing. This module should not be used in a study until it is restored.": "المحاكي التفاعلي غير متوفر. لا ينبغي استخدام هذه الوحدة في الدراسة حتى استعادته.",
    "old static images and legacy micro-videos are hidden from the student path. Active materials are the micro-animation, simulator, code bridge, and check.": "أُخفيت الصور الثابتة القديمة والمقاطع المصغرة السابقة من مسار المتعلم. المواد النشطة هي الحركة المصغرة والمحاكي وجسر الكود وفحص الفهم.",
    "Six compact modules. Choose a card to open it; the platform remembers your latest module.": "ست وحدات موجزة. اختر بطاقة لفتحها؛ تتذكر المنصة آخر وحدة وصلت إليها.",
    "Professional micro-lessons: visual explanation, tiny Qiskit example, AI support, and reflection.": "دروس مصغرة احترافية: شرح بصري، ومثال Qiskit صغير، ودعم ذكي، وتأمل.",
    "Please complete the pre-test before opening the learning path.": "أكمل الاختبار القبلي قبل فتح المسار التعليمي.",
    "This module is completed. You may review it or continue to the next module.": "اكتملت هذه الوحدة. يمكنك مراجعتها أو الانتقال إلى الوحدة التالية.",
    "Control group mode is active for this learner: AI Coach and Concept Builder are hidden by design.": "وضع المجموعة الضابطة مفعّل لهذا المتعلم: أُخفي المدرّب الذكي وباني المفاهيم وفق تصميم الدراسة.",
    "use the AI concept coach tab after writing a short attempt. This keeps generative AI as a formative learning scaffold, not a shortcut.": "استخدم تبويب مدرّب المفهوم بعد كتابة محاولة قصيرة. يبقي ذلك الذكاء التوليدي سقالةً للتعلم التكويني لا اختصارًا للحل.",
    "Please write a short reflection before marking the module complete.": "اكتب تأملًا قصيرًا قبل وضع علامة اكتمال الوحدة.",
    "Learning path requirements are complete. You may continue to the post-test when ready.": "اكتملت متطلبات المسار التعليمي. يمكنك متابعة الاختبار البعدي عندما تكون مستعدًا.",
    "Post-test is locked until at least one AI Tutor interaction is recorded for the experimental group.": "يبقى الاختبار البعدي مقفلًا حتى تسجيل تفاعل واحد على الأقل مع المدرّب الذكي للمجموعة التجريبية.",
    "You are in the control learning path. Continue with lessons, simulators, reflections, and the post-test without AI support.": "أنت في المسار الضابط. تابع الدروس والمحاكيات والتأملات والاختبار البعدي دون دعم الذكاء الاصطناعي.",
    "A continuous learning conversation with context from the current module. The tutor is designed to guide, not replace, your reasoning.": "محادثة تعلم مستمرة تراعي سياق الوحدة الحالية. صُمّم المدرّب ليوجه استدلالك لا ليستبدله.",
    "Ask a specific question, paste a small Qiskit snippet, or write your current explanation first. The tutor will keep the visible conversation history during the session and log each interaction for research analytics.": "اطرح سؤالًا محددًا، أو ألصق مقطع Qiskit صغيرًا، أو اكتب شرحك الحالي أولًا. يحتفظ المدرّب بسجل المحادثة المرئي أثناء الجلسة ويسجل كل تفاعل للتحليلات البحثية.",
    "No external LLM is configured. The lab will use a local formative fallback.": "لا يوجد نموذج لغوي خارجي مضبوط. سيستخدم المختبر بديلًا تكوينيًا محليًا.",
    "The tutor will connect answers to this module unless your question asks for something else.": "سيربط المدرّب إجاباته بهذه الوحدة ما لم يطلب سؤالك سياقًا آخر.",
    "No messages yet. Ask a question below or start from one of the prompt buttons.": "لا توجد رسائل بعد. اطرح سؤالًا أدناه أو ابدأ من أحد أزرار المقترحات.",
    "Please write at least a short attempt or question before asking the AI tutor.": "اكتب محاولة قصيرة أو سؤالًا على الأقل قبل طلب المدرّب الذكي.",
    "The external LLM was unavailable. A local hint was shown and the error was logged for the evaluator.": "تعذر النموذج اللغوي الخارجي. عُرض تلميح محلي وسُجّل الخطأ للمقيّم.",
    "Your feedback helps evaluate the AI-supported learning framework.": "تساعد تغذيتك الراجعة على تقييم إطار التعلم المدعوم بالذكاء الاصطناعي.",
    "Please complete the post-test before the survey.": "أكمل الاختبار البعدي قبل الاستبيان.",
    "Rate each item from 1 = strongly disagree to 5 = strongly agree.": "قيّم كل عبارة من 1 = لا أوافق بشدة إلى 5 = أوافق بشدة.",
    "Thank you. Your responses have been recorded. Your participation is now complete.": "شكرًا لك. سُجّلت إجاباتك واكتملت مشاركتك.",
    "Protected workspace for monitoring participants and exporting study data.": "فضاء محمي لمتابعة المشاركين وتصدير بيانات الدراسة.",
    "This page does not change the database. It documents the active study design, checks consent and workflow readiness, and prepares protocol evidence for the evaluator.": "لا تغيّر هذه الصفحة قاعدة البيانات. إنها توثق تصميم الدراسة النشط، وتتحقق من الموافقة وجاهزية المسار، وتجهز أدلة البروتوكول للمقيّم.",
    "This evaluator view shows registration metadata needed to support the pilot study. It never displays student passwords, password hashes, or password-reset tokens.": "تعرض واجهة المقيّم بيانات التسجيل الوصفية اللازمة للدراسة التجريبية، ولا تعرض كلمات المرور أو بصماتها أو رموز إعادة تعيينها.",
    "This section turns raw platform traces into paper-ready indicators: simulator use, Concept Builder use, quick checks, and time before AI requests.": "يحوّل هذا القسم آثار المنصة الخام إلى مؤشرات جاهزة للبحث: استخدام المحاكي وباني المفاهيم وفحوص الفهم والزمن قبل طلب الذكاء الاصطناعي.",
    "This page evaluates the LLM tutor itself, not the student.": "تقيّم هذه الصفحة المدرّب القائم على النموذج اللغوي نفسه، لا المتعلم.",
    "1 = poor/incorrect, 3 = acceptable/partial, 5 = excellent/highly appropriate": "1 = ضعيف/غير صحيح، 3 = مقبول/جزئي، 5 = ممتاز/ملائم جدًا",
    "Preview shows first 200 rows out of": "تعرض المعاينة أول 200 صف من أصل",
    "Download the workbook for all rows.": "نزّل المصنف للاطلاع على جميع الصفوف.",
    # Short labels and recurring fragments
    "Language / اللغة": "اللغة",
    "Language": "اللغة",
    "Student navigation": "تنقل المتعلم",
    "Evaluator navigation": "تنقل المقيّم",
    "Evaluator workspace": "فضاء المقيّم",
    "Monitor progress, AI usage, and exports.": "متابعة التقدم واستخدام الذكاء الاصطناعي والتصدير.",
    "No student signed in": "لا يوجد متعلم مسجل الدخول",
    "Create an account or sign in to start the study.": "أنشئ حسابًا أو سجّل الدخول لبدء الدراسة.",
    "Student": "المتعلم",
    "Learning path": "المسار التعليمي",
    "Current module": "الوحدة الحالية",
    "Next step": "الخطوة التالية",
    "Study roadmap": "خارطة الدراسة",
    "Sign in": "تسجيل الدخول",
    "Create account": "إنشاء حساب",
    "Sign out": "تسجيل الخروج",
    "Switch workspace": "تبديل الفضاء",
    "Resume recommended step": "استئناف الخطوة المقترحة",
    "Resume learning module": "استئناف الوحدة التعليمية",
    "Returning participant": "مشارك عائد",
    "New participant": "مشارك جديد",
    "Signed in": "تم تسجيل الدخول",
    "Overall study workflow": "التقدم العام في الدراسة",
    "Learning modules completed": "الوحدات التعليمية المكتملة",
    "AI tutor interactions recorded": "تفاعلات المدرّب الذكي المسجلة",
    "Resume point": "نقطة الاستئناف",
    "Next required action": "الإجراء المطلوب التالي",
    "Overall progress": "التقدم العام",
    "Continue": "متابعة",
    "Research Notice and Consent": "إشعار البحث والموافقة",
    "Research notice already confirmed.": "تم تأكيد إشعار البحث سابقًا.",
    "Study notice": "إشعار الدراسة",
    "Confirm and continue": "تأكيد ومتابعة",
    "Forgot your password?": "هل نسيت كلمة المرور؟",
    "Registered email": "البريد الإلكتروني المسجل",
    "Send password reset link": "إرسال رابط إعادة التعيين",
    "Reset Password": "إعادة تعيين كلمة المرور",
    "New password": "كلمة المرور الجديدة",
    "Confirm new password": "تأكيد كلمة المرور الجديدة",
    "Update password": "تحديث كلمة المرور",
    "Full name": "الاسم الكامل",
    "Email": "البريد الإلكتروني",
    "Institution": "المؤسسة",
    "Academic level": "المستوى الأكاديمي",
    "Prior Python level": "المستوى السابق في Python",
    "Prior quantum programming knowledge": "المعرفة السابقة بالبرمجة الكمية",
    "Password": "كلمة المرور",
    "Confirm password": "تأكيد كلمة المرور",
    "Study registration access code": "رمز الدخول إلى تسجيل الدراسة",
    "Research notice": "إشعار البحث",
    "Pre-test": "الاختبار القبلي",
    "Post-test": "الاختبار البعدي",
    "Choose one answer": "اختر إجابة واحدة",
    "Concept": "المفهوم",
    "Submit": "إرسال",
    "Submitted. Score": "تم الإرسال. النتيجة",
    "already submitted. Score": "مُرسل سابقًا. النتيجة",
    "Adaptive Learning Plan": "خطة التعلم التكيفية",
    "Concepts to reinforce": "مفاهيم تحتاج إلى تعزيز",
    "Recommended lesson sequence": "تسلسل الدروس المقترح",
    "AI response language": "لغة استجابة الذكاء الاصطناعي",
    "Generate AI personalized study plan": "إنشاء خطة تعلم شخصية بالذكاء الاصطناعي",
    "AI-generated study plan": "خطة تعلم مولدة بالذكاء الاصطناعي",
    "Personalized plan": "الخطة الشخصية",
    "Start learning module": "بدء الوحدة التعليمية",
    "Your learning route for this concept": "مسار تعلمك لهذا المفهوم",
    "Learning map": "خريطة التعلم",
    "What the student does": "ما الذي يفعله المتعلم",
    "Visual first": "ابدأ بصريًا",
    "GenAI learning coach": "مدرّب التعلم التوليدي",
    "Which step are you working on?": "على أي خطوة تعمل؟",
    "Coach response language": "لغة استجابة المدرّب",
    "Your attempt first": "محاولتك أولًا",
    "Ask AI to clarify this part": "اطلب من الذكاء الاصطناعي توضيح هذا الجزء",
    "AI coach response": "استجابة المدرّب الذكي",
    "Concept Builder": "باني المفاهيم",
    "Your attempt before generation": "محاولتك قبل التوليد",
    "Output language": "لغة المخرجات",
    "Generated visual card": "البطاقة البصرية المولدة",
    "Goal": "الهدف",
    "Focus question": "سؤال التركيز",
    "Watch the idea": "شاهد الفكرة",
    "Use the simulator": "استخدم المحاكي",
    "Connect to Qiskit": "اربط بـ Qiskit",
    "Check your understanding": "تحقق من فهمك",
    "I completed the simulator steps": "أكملت خطوات المحاكي",
    "Simulator completion recorded.": "تم تسجيل إكمال المحاكي.",
    "What to connect": "ما الذي ينبغي ربطه",
    "Before measurement": "قبل القياس",
    "After measurement / output": "بعد القياس / المخرجات",
    "Avoid this misconception": "تجنب هذا التصور الخاطئ",
    "Question": "السؤال",
    "Write one short explanation before using AI": "اكتب شرحًا قصيرًا قبل استخدام الذكاء الاصطناعي",
    "Save my explanation": "حفظ شرحي",
    "Saved.": "تم الحفظ.",
    "Learning Path": "المسار التعليمي",
    "Core explanation": "الشرح الأساسي",
    "Why this matters": "لماذا يهم هذا؟",
    "By the end of this module you can": "بنهاية هذه الوحدة تستطيع",
    "Misconception to avoid": "تصور خاطئ ينبغي تجنبه",
    "Tiny Qiskit example": "مثال Qiskit صغير",
    "Code reading focus": "نقاط قراءة الكود",
    "Big idea": "الفكرة الكبرى",
    "Mini task before asking AI": "مهمة صغيرة قبل طلب الذكاء الاصطناعي",
    "Reflection prompt": "سؤال التأمل",
    "AI use reminder": "تذكير باستخدام الذكاء الاصطناعي",
    "Reflection and completion": "التأمل وإكمال الوحدة",
    "Write your reflection in your own words": "اكتب تأملك بأسلوبك الخاص",
    "Save reflection and mark module complete": "حفظ التأمل ووضع علامة اكتمال الوحدة",
    "Reflection saved. Module completed.": "حُفظ التأمل واكتملت الوحدة.",
    "Previous module": "الوحدة السابقة",
    "Next module": "الوحدة التالية",
    "Go to post-test": "الانتقال إلى الاختبار البعدي",
    "AI Tutor Lab": "مختبر المدرّب الذكي",
    "How to use the AI Tutor": "كيفية استخدام المدرّب الذكي",
    "Tutor task": "مهمة المدرّب",
    "Concept focus": "المفهوم المستهدف",
    "Response language": "لغة الاستجابة",
    "Current learning context": "سياق التعلم الحالي",
    "Return to current learning module": "العودة إلى الوحدة التعليمية الحالية",
    "Quick-start prompts": "مقترحات للبدء السريع",
    "Draft prompt selected": "تم اختيار مسودة السؤال",
    "Edit the selected prompt before sending": "عدّل السؤال المختار قبل الإرسال",
    "Send selected prompt": "إرسال السؤال المختار",
    "Conversation": "المحادثة",
    "Clear visible chat history": "مسح سجل المحادثة المرئي",
    "Usability Questionnaire and Open-ended Feedback": "استبيان سهولة الاستخدام والتغذية الراجعة المفتوحة",
    "Survey already submitted. Thank you.": "أُرسل الاستبيان سابقًا. شكرًا لك.",
    "Open-ended feedback": "تغذية راجعة مفتوحة",
    "Submit survey": "إرسال الاستبيان",
    "Evaluator Sign in": "دخول المقيّم",
    "Evaluator username": "اسم مستخدم المقيّم",
    "Evaluator password": "كلمة مرور المقيّم",
    "Study Protocol": "بروتوكول الدراسة",
    "Registered students": "المتعلمون المسجلون",
    "Consent confirmed": "الموافقات المؤكدة",
    "Complete cases": "الحالات المكتملة",
    "Design": "التصميم",
    "Active study configuration": "إعداد الدراسة النشط",
    "Research workflow safeguards": "ضمانات المسار البحثي",
    "Consent and completion audit": "تدقيق الموافقة والاكتمال",
    "Download protocol evidence": "تنزيل أدلة البروتوكول",
    "Download study protocol workbook": "تنزيل مصنف بروتوكول الدراسة",
    "Students": "المتعلمون",
    "Surveys": "الاستبيانات",
    "AI logs": "سجلات الذكاء الاصطناعي",
    "Deployment status": "حالة النشر",
    "Search and filters": "البحث والتصفية",
    "Search by participant code, name, email, or institution": "ابحث برمز المشاركة أو الاسم أو البريد أو المؤسسة",
    "Registration account list": "قائمة حسابات التسجيل",
    "Select participant": "اختر مشاركًا",
    "Participant code": "رمز المشاركة",
    "Active": "نشط",
    "Learning gain": "مكسب التعلم",
    "Completion requirements": "متطلبات الاكتمال",
    "Lesson reflections": "تأملات الدروس",
    "Learning timeline": "الخط الزمني للتعلم",
    "AI interactions": "تفاعلات الذكاء الاصطناعي",
    "research interaction dashboard": "لوحة التفاعلات البحثية",
    "Concept Builder events": "أحداث باني المفاهيم",
    "Simulator completions": "مرات إكمال المحاكي",
    "Quick checks": "فحوص سريعة",
    "Mean seconds before AI": "متوسط الثواني قبل طلب الذكاء الاصطناعي",
    "Simulator journey": "رحلة المحاكي",
    "AI timing": "توقيت استخدام الذكاء الاصطناعي",
    "Student summary": "ملخص المتعلم",
    "Group comparison": "مقارنة المجموعات",
    "Score summary": "ملخص النتائج",
    "AI-supported learning observer": "مراقب التعلم المدعوم بالذكاء الاصطناعي",
    "Time before AI request": "الزمن قبل طلب الذكاء الاصطناعي",
    "Registered": "المسجلون",
    "Complete pairs": "الأزواج المكتملة",
    "Completion validity for analysis": "صلاحية الاكتمال للتحليل",
    "Pre-test / Post-test summary": "ملخص الاختبار القبلي والبعدي",
    "Concept-level gain": "المكسب حسب المفهوم",
    "Generative AI / LLM usage evidence": "أدلة استخدام الذكاء التوليدي والنموذج اللغوي",
    "Usability questionnaire means": "متوسطات استبيان سهولة الاستخدام",
    "LLM pedagogical performance evaluation": "تقييم الأداء التربوي للنموذج اللغوي",
    "Download paper-ready tables": "تنزيل جداول جاهزة للبحث",
    "Responses to load": "عدد الاستجابات المعروضة",
    "Show only unrated responses": "عرض الاستجابات غير المقيمة فقط",
    "Candidate AI responses": "استجابات الذكاء الاصطناعي المرشحة",
    "Select an AI interaction to evaluate": "اختر تفاعلًا لتقييمه",
    "Prompt and AI response": "السؤال واستجابة الذكاء الاصطناعي",
    "Expert rubric rating": "التقييم وفق شبكة الخبير",
    "Conceptual accuracy": "الدقة المفاهيمية",
    "Answer relevance": "ملاءمة الإجابة",
    "Pedagogical clarity": "الوضوح التربوي",
    "Scaffolding quality": "جودة السقالات",
    "Qiskit alignment": "التوافق مع Qiskit",
    "Reflection support": "دعم التأمل",
    "Personalization": "التخصيص",
    "Evaluator comment": "تعليق المقيّم",
    "Save LLM evaluation": "حفظ تقييم النموذج اللغوي",
    "LLM evaluation saved.": "تم حفظ تقييم النموذج اللغوي.",
    "Current LLM performance summary": "ملخص أداء النموذج اللغوي الحالي",
    "LLM error diagnostics": "تشخيص أخطاء النموذج اللغوي",
    "Prepare anonymized research export": "تجهيز تصدير بحثي مجهول الهوية",
    "Prepare full admin backup": "تجهيز نسخة إدارية احتياطية كاملة",
    "Download prepared workbook": "تنزيل المصنف المجهز",
    "Preview": "معاينة",
    "Dataset": "مجموعة البيانات",
    "Optional short comment": "تعليق قصير اختياري",
    "Save AI usefulness rating": "حفظ تقييم فائدة الاستجابة",
    "Important": "مهم",
    "Tip": "نصيحة",
    "Locked": "مقفل",
    "Not started": "لم يبدأ",
    "Completed": "مكتمل",
    "Available": "متاح",
    "Current": "الحالي",
    "Optional enrichment": "إثراء اختياري",
    "Auto-detect": "تلقائي حسب اللغة",
    "English": "الإنجليزية",
    "Arabic": "العربية",
    "French": "الفرنسية",
}

FR: Dict[str, str] = {
    "How to choose the 0–3 level:": "Comment choisir le niveau de 0 à 3 :",
    "No prior knowledge.": "Aucune connaissance préalable.",
    "Basic awareness: I have heard about it, but I cannot explain it well.": "Notions de base : j'en ai entendu parler, mais je ne peux pas encore bien l'expliquer.",
    "Some understanding: I can explain basic ideas with help.": "Compréhension partielle : je peux expliquer les idées de base avec de l'aide.",
    "Good understanding: I can apply or explain it confidently.": "Bonne compréhension : je peux l'appliquer ou l'expliquer avec assurance.",
    "Save your participant code now. You will need it if you return later. Do not create a second account.": "Enregistrez maintenant votre code participant. Vous en aurez besoin pour revenir. Ne créez pas un second compte.",
    "Tip: copy the code to your notes or take a screenshot before continuing.": "Conseil : copiez le code dans vos notes ou faites une capture d'écran avant de continuer.",
    "This participation is complete for analysis.": "Cette participation est complète et prête pour l'analyse.",
    "Use after reading this part: the AI should clarify the idea, not replace your reasoning.": "À utiliser après lecture : l'IA doit clarifier l'idée, sans remplacer votre raisonnement.",
    "Was this AI response useful for your learning?": "Cette réponse de l'IA a-t-elle été utile à votre apprentissage ?",
    "This helps the evaluator assess the pedagogical quality of AI support.": "Cela aide l'évaluateur à apprécier la qualité pédagogique du soutien IA.",
    "AI usefulness rating saved.": "L'évaluation de l'utilité de la réponse a été enregistrée.",
    "AI tutor interactions and progress events are logged for the evaluator dashboard.": "Les interactions avec le coach IA et les événements de progression sont consignés pour le tableau de bord évaluateur.",
    "Choose a learning path or open the evaluator workspace from the 3alimnIA home page.": "Choisissez un parcours ou ouvrez l'espace évaluateur depuis l'accueil de 3alimnIA.",
    "A guided Qiskit learning workspace with visual explanations, learner-first attempts, contextual AI scaffolding, and measurable progress evidence.": "Un espace guidé pour apprendre Qiskit avec explications visuelles, tentative préalable, étayage IA contextualisé et preuves mesurables de progression.",
    "The platform combines a structured learning path, short visual explanations, pre/post assessment, and an AI tutor that encourages reasoning rather than copy-paste answers.": "La plateforme combine un parcours structuré, de courtes explications visuelles, une évaluation pré/post et un coach IA qui encourage le raisonnement plutôt que le copier-coller.",
    "Use your participant code, email, or exact registered name with your password.": "Utilisez votre code participant, votre e-mail ou votre nom enregistré exact avec votre mot de passe.",
    "Register as a study participant. If the study is protected, you will need the registration access code.": "Inscrivez-vous comme participant à l'étude. Si elle est protégée, le code d'accès d'inscription sera requis.",
    "Account created successfully. Save your participant code before continuing.": "Compte créé avec succès. Enregistrez votre code participant avant de continuer.",
    "Please read this notice before continuing the study workflow.": "Veuillez lire cette notice avant de poursuivre le protocole de l'étude.",
    "This platform is used for a pilot evaluation of AI-supported learning for introductory quantum programming.": "Cette plateforme sert à une évaluation pilote de l'apprentissage assisté par IA en initiation à la programmation quantique.",
    "Your pre-test, post-test, learning progress, reflections, survey answers, and AI tutor interactions will be recorded for research analysis.": "Le pré-test, le post-test, la progression, les réflexions, le questionnaire et les interactions avec le coach IA seront enregistrés pour l'analyse scientifique.",
    "Your participant code is used to organize the data. Avoid creating multiple accounts.": "Votre code participant sert à organiser les données. Évitez de créer plusieurs comptes.",
    "AI tutor responses may be reviewed by the evaluator to assess conceptual accuracy, relevance, scaffolding, and feedback quality.": "Les réponses du coach IA peuvent être examinées afin d'évaluer leur exactitude, pertinence, étayage et qualité de rétroaction.",
    "The AI tutor is a learning support tool. It should not replace your own reasoning.": "Le coach IA est un outil de soutien et ne doit pas remplacer votre propre raisonnement.",
    "I have read the study notice and agree to participate in this pilot evaluation.": "J'ai lu la notice de l'étude et j'accepte de participer à cette évaluation pilote.",
    "Enter the email address used during registration. If it exists in the study database, a reset link will be sent.": "Saisissez l'adresse e-mail utilisée à l'inscription. Si elle figure dans la base de l'étude, un lien de réinitialisation sera envoyé.",
    "Please enter and confirm your new password. Reset links are valid for a limited time and can be used only once.": "Saisissez et confirmez votre nouveau mot de passe. Le lien est valable pour une durée limitée et ne peut être utilisé qu'une fois.",
    "Answer the questions individually. This is used to evaluate learning progress, not to grade you.": "Répondez individuellement. Ce test mesure la progression et ne constitue pas une note académique.",
    "Please complete at least one learning section and save its reflection before the post-test.": "Terminez au moins une section et enregistrez votre réflexion avant le post-test.",
    "Please complete at least one AI Tutor interaction before the post-test. This applies only to the experimental AI-supported group.": "Effectuez au moins une interaction avec le coach IA avant le post-test. Cette règle concerne uniquement le groupe expérimental assisté par IA.",
    "The platform uses your pre-test results to recommend learning sections and AI-supported practice.": "La plateforme utilise les résultats du pré-test pour recommander des sections et des activités assistées par IA.",
    "No major weakness detected. Continue with the full learning sequence.": "Aucune faiblesse majeure détectée. Poursuivez la séquence complète.",
    "The LLM service was unavailable, so a local fallback was shown and logged for the evaluator.": "Le service LLM était indisponible ; une solution locale a été affichée et consignée pour l'évaluateur.",
    "Follow the four steps in order. The AI coach is used after your first attempt, not before it.": "Suivez les quatre étapes dans l'ordre. Le coach IA intervient après votre première tentative, jamais avant.",
    "Choose the step you are working on, write your attempt, then ask the AI for a limited type of support.": "Choisissez l'étape, rédigez votre tentative, puis demandez un soutien IA bien délimité.",
    "Generate polished learning supports after writing your own attempt. Outputs are curated around the current lesson, not open-ended free generation.": "Générez des supports structurés après votre propre tentative. Les sorties sont encadrées par la leçon, et non produites librement.",
    "Write a short attempt first. This preserves the research value of measuring AI-supported learning after learner effort.": "Rédigez d'abord une courte tentative afin de préserver la valeur scientifique de la mesure après l'effort de l'apprenant.",
    "Concept animation will appear here once the MP4 is available.": "L'animation du concept apparaîtra ici lorsque le fichier MP4 sera disponible.",
    "Interactive simulator missing. This module should not be used in a study until it is restored.": "Le simulateur interactif manque. Ce module ne doit pas être utilisé dans une étude avant sa restauration.",
    "Six compact modules. Choose a card to open it; the platform remembers your latest module.": "Six modules compacts. Sélectionnez une carte ; la plateforme mémorise le dernier module consulté.",
    "Professional micro-lessons: visual explanation, tiny Qiskit example, AI support, and reflection.": "Micro-leçons professionnelles : explication visuelle, petit exemple Qiskit, soutien IA et réflexion.",
    "Please complete the pre-test before opening the learning path.": "Veuillez terminer le pré-test avant d'ouvrir le parcours.",
    "This module is completed. You may review it or continue to the next module.": "Ce module est terminé. Vous pouvez le revoir ou passer au suivant.",
    "Control group mode is active for this learner: AI Coach and Concept Builder are hidden by design.": "Le mode groupe témoin est actif : le coach IA et le Concept Builder sont masqués conformément au protocole.",
    "Please write a short reflection before marking the module complete.": "Rédigez une courte réflexion avant de valider le module.",
    "Learning path requirements are complete. You may continue to the post-test when ready.": "Les exigences du parcours sont satisfaites. Vous pouvez passer au post-test lorsque vous êtes prêt.",
    "You are in the control learning path. Continue with lessons, simulators, reflections, and the post-test without AI support.": "Vous suivez le parcours témoin. Continuez les leçons, simulations, réflexions et le post-test sans soutien IA.",
    "A continuous learning conversation with context from the current module. The tutor is designed to guide, not replace, your reasoning.": "Une conversation d'apprentissage continue, contextualisée par le module actuel. Le coach guide le raisonnement sans le remplacer.",
    "Ask a specific question, paste a small Qiskit snippet, or write your current explanation first. The tutor will keep the visible conversation history during the session and log each interaction for research analytics.": "Posez une question précise, collez un petit extrait Qiskit ou rédigez votre explication. Le coach conserve l'historique visible de la session et journalise chaque interaction.",
    "No external LLM is configured. The lab will use a local formative fallback.": "Aucun LLM externe n'est configuré. Le laboratoire utilisera une aide formative locale.",
    "The tutor will connect answers to this module unless your question asks for something else.": "Le coach reliera ses réponses à ce module, sauf si votre question exige un autre contexte.",
    "No messages yet. Ask a question below or start from one of the prompt buttons.": "Aucun message pour le moment. Posez une question ou utilisez une proposition de démarrage.",
    "Please write at least a short attempt or question before asking the AI tutor.": "Rédigez au moins une courte tentative ou une question avant de solliciter le coach IA.",
    "The external LLM was unavailable. A local hint was shown and the error was logged for the evaluator.": "Le LLM externe était indisponible. Un indice local a été affiché et l'erreur consignée pour l'évaluateur.",
    "Your feedback helps evaluate the AI-supported learning framework.": "Votre retour contribue à évaluer le dispositif d'apprentissage assisté par IA.",
    "Please complete the post-test before the survey.": "Veuillez terminer le post-test avant le questionnaire.",
    "Rate each item from 1 = strongly disagree to 5 = strongly agree.": "Évaluez chaque énoncé de 1 = pas du tout d'accord à 5 = tout à fait d'accord.",
    "Thank you. Your responses have been recorded. Your participation is now complete.": "Merci. Vos réponses ont été enregistrées et votre participation est terminée.",
    "Protected workspace for monitoring participants and exporting study data.": "Espace protégé pour suivre les participants et exporter les données de l'étude.",
    "This page does not change the database. It documents the active study design, checks consent and workflow readiness, and prepares protocol evidence for the evaluator.": "Cette page ne modifie pas la base. Elle documente le protocole actif, contrôle le consentement et prépare les preuves pour l'évaluateur.",
    "This evaluator view shows registration metadata needed to support the pilot study. It never displays student passwords, password hashes, or password-reset tokens.": "Cette vue affiche uniquement les métadonnées nécessaires à l'étude pilote, jamais les mots de passe, empreintes ou jetons de réinitialisation.",
    "Language / اللغة": "Langue",
    "Language": "Langue",
    "Student navigation": "Navigation apprenant",
    "Evaluator navigation": "Navigation évaluateur",
    "Evaluator workspace": "Espace évaluateur",
    "Monitor progress, AI usage, and exports.": "Suivre la progression, l'usage de l'IA et les exports.",
    "No student signed in": "Aucun apprenant connecté",
    "Create an account or sign in to start the study.": "Créez un compte ou connectez-vous pour commencer l'étude.",
    "Student": "Apprenant",
    "Learning path": "Parcours d'apprentissage",
    "Current module": "Module actuel",
    "Next step": "Étape suivante",
    "Study roadmap": "Feuille de route de l'étude",
    "Sign in": "Se connecter",
    "Create account": "Créer un compte",
    "Sign out": "Se déconnecter",
    "Switch workspace": "Changer d'espace",
    "Resume recommended step": "Reprendre l'étape recommandée",
    "Resume learning module": "Reprendre le module",
    "Returning participant": "Participant déjà inscrit",
    "New participant": "Nouveau participant",
    "Signed in": "Connecté",
    "Overall study workflow": "Progression globale de l'étude",
    "Learning modules completed": "Modules terminés",
    "AI tutor interactions recorded": "Interactions avec le coach IA",
    "Resume point": "Point de reprise",
    "Next required action": "Prochaine action requise",
    "Overall progress": "Progression globale",
    "Continue": "Continuer",
    "Research Notice and Consent": "Notice de recherche et consentement",
    "Research notice already confirmed.": "La notice de recherche a déjà été confirmée.",
    "Study notice": "Notice de l'étude",
    "Confirm and continue": "Confirmer et continuer",
    "Forgot your password?": "Mot de passe oublié ?",
    "Registered email": "E-mail enregistré",
    "Send password reset link": "Envoyer le lien de réinitialisation",
    "Reset Password": "Réinitialiser le mot de passe",
    "New password": "Nouveau mot de passe",
    "Confirm new password": "Confirmer le nouveau mot de passe",
    "Update password": "Mettre à jour le mot de passe",
    "Full name": "Nom complet",
    "Email": "E-mail",
    "Institution": "Établissement",
    "Academic level": "Niveau académique",
    "Prior Python level": "Niveau antérieur en Python",
    "Prior quantum programming knowledge": "Connaissances antérieures en programmation quantique",
    "Password": "Mot de passe",
    "Confirm password": "Confirmer le mot de passe",
    "Study registration access code": "Code d'accès à l'inscription",
    "Research notice": "Notice de recherche",
    "Pre-test": "Pré-test",
    "Post-test": "Post-test",
    "Choose one answer": "Choisissez une réponse",
    "Concept": "Concept",
    "Submit": "Soumettre",
    "Adaptive Learning Plan": "Plan d'apprentissage adaptatif",
    "Concepts to reinforce": "Concepts à renforcer",
    "Recommended lesson sequence": "Séquence recommandée",
    "AI response language": "Langue de réponse de l'IA",
    "Generate AI personalized study plan": "Générer un plan personnalisé avec l'IA",
    "AI-generated study plan": "Plan généré par l'IA",
    "Personalized plan": "Plan personnalisé",
    "Start learning module": "Commencer le module",
    "Your learning route for this concept": "Votre itinéraire pour ce concept",
    "Learning map": "Carte d'apprentissage",
    "What the student does": "Ce que fait l'apprenant",
    "Visual first": "Le visuel d'abord",
    "GenAI learning coach": "Coach d'apprentissage GenAI",
    "Which step are you working on?": "Sur quelle étape travaillez-vous ?",
    "Coach response language": "Langue de réponse du coach",
    "Your attempt first": "Votre tentative d'abord",
    "Ask AI to clarify this part": "Demander à l'IA de clarifier cette partie",
    "AI coach response": "Réponse du coach IA",
    "Concept Builder": "Constructeur de concepts",
    "Your attempt before generation": "Votre tentative avant génération",
    "Output language": "Langue de sortie",
    "Generated visual card": "Carte visuelle générée",
    "Goal": "Objectif",
    "Focus question": "Question directrice",
    "Watch the idea": "Observer l'idée",
    "Use the simulator": "Utiliser le simulateur",
    "Connect to Qiskit": "Relier à Qiskit",
    "Check your understanding": "Vérifier votre compréhension",
    "I completed the simulator steps": "J'ai terminé les étapes du simulateur",
    "Simulator completion recorded.": "Achèvement du simulateur enregistré.",
    "What to connect": "Éléments à relier",
    "Before measurement": "Avant la mesure",
    "After measurement / output": "Après la mesure / sortie",
    "Avoid this misconception": "Éviter cette idée fausse",
    "Question": "Question",
    "Write one short explanation before using AI": "Rédigez une courte explication avant d'utiliser l'IA",
    "Save my explanation": "Enregistrer mon explication",
    "Saved.": "Enregistré.",
    "Learning Path": "Parcours d'apprentissage",
    "Core explanation": "Explication essentielle",
    "Why this matters": "Pourquoi est-ce important ?",
    "By the end of this module you can": "À la fin de ce module, vous pourrez",
    "Misconception to avoid": "Idée fausse à éviter",
    "Tiny Qiskit example": "Petit exemple Qiskit",
    "Code reading focus": "Points de lecture du code",
    "Big idea": "Idée clé",
    "Mini task before asking AI": "Mini-tâche avant de solliciter l'IA",
    "Reflection prompt": "Consigne de réflexion",
    "AI use reminder": "Rappel d'usage de l'IA",
    "Reflection and completion": "Réflexion et validation",
    "Write your reflection in your own words": "Rédigez votre réflexion avec vos propres mots",
    "Save reflection and mark module complete": "Enregistrer la réflexion et valider le module",
    "Reflection saved. Module completed.": "Réflexion enregistrée. Module terminé.",
    "Previous module": "Module précédent",
    "Next module": "Module suivant",
    "Go to post-test": "Passer au post-test",
    "AI Tutor Lab": "Laboratoire du coach IA",
    "How to use the AI Tutor": "Comment utiliser le coach IA",
    "Tutor task": "Tâche du coach",
    "Concept focus": "Concept ciblé",
    "Response language": "Langue de réponse",
    "Current learning context": "Contexte d'apprentissage actuel",
    "Return to current learning module": "Retourner au module actuel",
    "Quick-start prompts": "Propositions de démarrage",
    "Draft prompt selected": "Brouillon sélectionné",
    "Edit the selected prompt before sending": "Modifier la question avant l'envoi",
    "Send selected prompt": "Envoyer la question",
    "Conversation": "Conversation",
    "Clear visible chat history": "Effacer l'historique visible",
    "Usability Questionnaire and Open-ended Feedback": "Questionnaire d'utilisabilité et retour ouvert",
    "Survey already submitted. Thank you.": "Questionnaire déjà soumis. Merci.",
    "Open-ended feedback": "Retour ouvert",
    "Submit survey": "Soumettre le questionnaire",
    "Evaluator Sign in": "Connexion évaluateur",
    "Evaluator username": "Identifiant évaluateur",
    "Evaluator password": "Mot de passe évaluateur",
    "Study Protocol": "Protocole d'étude",
    "Registered students": "Apprenants inscrits",
    "Consent confirmed": "Consentements confirmés",
    "Complete cases": "Cas complets",
    "Design": "Dispositif",
    "Active study configuration": "Configuration active de l'étude",
    "Research workflow safeguards": "Garanties du protocole de recherche",
    "Consent and completion audit": "Audit du consentement et de l'achèvement",
    "Download protocol evidence": "Télécharger les preuves du protocole",
    "Download study protocol workbook": "Télécharger le classeur du protocole",
    "Students": "Apprenants",
    "Surveys": "Questionnaires",
    "AI logs": "Journaux IA",
    "Deployment status": "État du déploiement",
    "Search and filters": "Recherche et filtres",
    "Search by participant code, name, email, or institution": "Rechercher par code, nom, e-mail ou établissement",
    "Registration account list": "Liste des comptes inscrits",
    "Select participant": "Sélectionner un participant",
    "Participant code": "Code participant",
    "Active": "Actif",
    "Learning gain": "Gain d'apprentissage",
    "Completion requirements": "Conditions d'achèvement",
    "Lesson reflections": "Réflexions sur les leçons",
    "Learning timeline": "Chronologie d'apprentissage",
    "AI interactions": "Interactions IA",
    "research interaction dashboard": "tableau de bord des interactions de recherche",
    "Concept Builder events": "Événements du constructeur de concepts",
    "Simulator completions": "Simulations terminées",
    "Quick checks": "Vérifications rapides",
    "Mean seconds before AI": "Secondes moyennes avant l'IA",
    "Simulator journey": "Parcours du simulateur",
    "AI timing": "Temporalité de l'IA",
    "Student summary": "Synthèse apprenant",
    "Group comparison": "Comparaison des groupes",
    "Score summary": "Synthèse des scores",
    "AI-supported learning observer": "Observatoire de l'apprentissage assisté par IA",
    "Time before AI request": "Temps avant la demande IA",
    "Registered": "Inscrits",
    "Complete pairs": "Paires complètes",
    "Completion validity for analysis": "Validité de l'achèvement pour l'analyse",
    "Pre-test / Post-test summary": "Synthèse pré-test / post-test",
    "Concept-level gain": "Gain par concept",
    "Generative AI / LLM usage evidence": "Preuves d'usage GenAI / LLM",
    "Usability questionnaire means": "Moyennes du questionnaire d'utilisabilité",
    "LLM pedagogical performance evaluation": "Évaluation de la performance pédagogique du LLM",
    "Download paper-ready tables": "Télécharger les tableaux prêts pour publication",
    "Responses to load": "Réponses à charger",
    "Show only unrated responses": "Afficher uniquement les réponses non évaluées",
    "Candidate AI responses": "Réponses IA candidates",
    "Select an AI interaction to evaluate": "Sélectionner une interaction IA",
    "Prompt and AI response": "Question et réponse IA",
    "Expert rubric rating": "Évaluation selon la grille experte",
    "Conceptual accuracy": "Exactitude conceptuelle",
    "Answer relevance": "Pertinence de la réponse",
    "Pedagogical clarity": "Clarté pédagogique",
    "Scaffolding quality": "Qualité de l'étayage",
    "Qiskit alignment": "Alignement Qiskit",
    "Reflection support": "Soutien à la réflexion",
    "Personalization": "Personnalisation",
    "Evaluator comment": "Commentaire de l'évaluateur",
    "Save LLM evaluation": "Enregistrer l'évaluation LLM",
    "LLM evaluation saved.": "Évaluation LLM enregistrée.",
    "Current LLM performance summary": "Synthèse actuelle des performances du LLM",
    "LLM error diagnostics": "Diagnostic des erreurs LLM",
    "Prepare anonymized research export": "Préparer l'export scientifique anonymisé",
    "Prepare full admin backup": "Préparer la sauvegarde administrative complète",
    "Download prepared workbook": "Télécharger le classeur préparé",
    "Preview": "Aperçu",
    "Dataset": "Jeu de données",
    "Optional short comment": "Court commentaire facultatif",
    "Save AI usefulness rating": "Enregistrer l'utilité de la réponse",
    "Important": "Important",
    "Tip": "Conseil",
    "Locked": "Verrouillé",
    "Not started": "Non commencé",
    "Completed": "Terminé",
    "Available": "Disponible",
    "Current": "Actuel",
    "Optional enrichment": "Enrichissement facultatif",
    "Auto-detect": "Détection automatique",
    "English": "Anglais",
    "Arabic": "Arabe",
    "French": "Français",
}

AR.update({'Interface language / لغة الواجهة / Langue de l’interface': 'لغة الواجهة', 'Explain a concept': 'اشرح مفهومًا', 'Generate a practice exercise': 'أنشئ تمرينًا تطبيقيًا', 'Check my explanation': 'تحقق من شرحي', 'Debug or interpret Qiskit code': 'صحح أو فسّر كود Qiskit', 'Generate structured explanation': 'أنشئ شرحًا منظمًا', 'Generate careful analogy': 'أنشئ تشبيهًا مضبوطًا', 'Generate misconception diagnosis': 'شخّص سوء الفهم', 'Generate mini formative quiz': 'أنشئ اختبارًا تكوينيًا قصيرًا', 'Connect to Qiskit professionally': 'اربط المفهوم بـ Qiskit', 'Generate polished visual card': 'أنشئ بطاقة بصرية احترافية', 'Ask me one question': 'اطرح عليّ سؤالًا واحدًا', 'Give one hint': 'أعطني تلميحًا واحدًا', 'Explain this step': 'اشرح هذه الخطوة', 'Create practice': 'أنشئ تدريبًا', 'Learning not started': 'لم يبدأ التعلم بعد', 'Ask about the current module, a concept, or a Qiskit code snippet...': 'اسأل عن الوحدة الحالية أو مفهوم أو مقطع كود Qiskit...', 'Conversation': 'المحادثة', 'Missing email': 'بريد إلكتروني مفقود', 'Download account registration list (CSV)': 'تنزيل قائمة حسابات التسجيل (CSV)', 'Account support notes': 'ملاحظات دعم الحسابات', 'AI support mode by lesson and task': 'نمط الدعم الذكي حسب الدرس والمهمة', 'Download paper-ready analysis workbook': 'تنزيل مصنف التحليل الجاهز للبحث', 'Focus on LLM / LLM-error responses': 'التركيز على استجابات LLM وأخطائها', 'Mode': 'النمط', 'Module': 'الوحدة', 'Rows': 'الصفوف', 'Likert responses': 'استجابات مقياس ليكرت', 'Rows to load': 'عدد الصفوف للتحميل', 'Actor role': 'دور الفاعل', 'Event type': 'نوع الحدث', 'Database OK': 'قاعدة البيانات سليمة', 'DB dialect': 'نوع قاعدة البيانات', 'App version': 'إصدار التطبيق', 'AI provider': 'مزود الذكاء الاصطناعي', 'Live counts': 'الأعداد الحالية', 'Pilot-safety checks': 'فحوص سلامة الدراسة التجريبية', 'Before changing database schema manually, download a backup from Results Export or Neon. These checks do not modify student data.': 'قبل تغيير مخطط قاعدة البيانات يدويًا، نزّل نسخة احتياطية من تصدير النتائج أو Neon. لا تغيّر هذه الفحوص بيانات المتعلمين.', 'Use the anonymized workbook for analysis and manuscript tables. Use the full backup only for secure administrative backup.': 'استخدم المصنف مجهول الهوية للتحليل وجداول المقال، واستعمل النسخة الكاملة فقط للنسخ الإداري الآمن.', 'AI tutor: local fallback mode': 'المدرّب الذكي: وضع البديل المحلي', 'LPQS · Learning analytics · Anonymized research exports · Provider-agnostic LLM layer': 'LPQS · تحليلات التعلم · تصدير بحثي مجهول الهوية · طبقة LLM مستقلة عن المزود', 'Please sign in first.': 'سجّل الدخول أولًا.', 'Go to sign in': 'الانتقال إلى تسجيل الدخول', 'I saved my participant code': 'حفظت رمز المشارك', 'Forgot password?': 'هل نسيت كلمة المرور؟', 'Go to learning module': 'الانتقال إلى الوحدة التعليمية', 'Complete the pre-test first.': 'أكمل الاختبار القبلي أولًا.', 'Go to pre-test': 'الانتقال إلى الاختبار القبلي', 'Return to learning module': 'العودة إلى الوحدة التعليمية', 'Default evaluator password is still active. Change ADMIN_PASSWORD or use EVALUATOR_PASSWORD_HASH before cloud deployment.': 'لا تزال كلمة مرور المقيّم الافتراضية مفعلة. غيّر ADMIN_PASSWORD أو استخدم EVALUATOR_PASSWORD_HASH قبل النشر السحابي.', 'Please enter a valid email address.': 'أدخل بريدًا إلكترونيًا صالحًا.', 'You can now sign in using your email, participant code, or exact full name.': 'يمكنك الآن تسجيل الدخول بالبريد الإلكتروني أو رمز المشارك أو الاسم الكامل المطابق.', 'If the link expired, request a new password reset from the sign-in page.': 'إذا انتهت صلاحية الرابط، اطلب إعادة تعيين جديدة من صفحة الدخول.', 'Invalid identifier or password.': 'المعرّف أو كلمة المرور غير صحيحين.', 'Invalid registration access code.': 'رمز الدخول إلى التسجيل غير صحيح.', 'Please confirm the study notice before creating an account.': 'أكد إشعار الدراسة قبل إنشاء الحساب.', 'Invalid evaluator credentials.': 'بيانات دخول المقيّم غير صحيحة.', 'Write a short attempt first. This keeps the AI tutor formative rather than answer-giving.': 'اكتب محاولة قصيرة أولًا حتى يبقى المدرّب الذكي أداة تكوينية لا أداة لإعطاء الإجابة.', 'AI interaction recorded. Your learning path is complete, so the post-test is available.': 'سُجل التفاعل الذكي واكتمل مسارك، وأصبح الاختبار البعدي متاحًا.', 'Initial password': 'كلمة المرور الأولية', 'Create participant': 'إنشاء مشارك', 'Prior quantum knowledge': 'المعرفة السابقة بالكوانتوم', 'No participants have been registered yet.': 'لم يُسجل أي مشارك بعد.', 'AI tutor usage by mode': 'استخدام المدرّب الذكي حسب النمط', 'Recent participants': 'أحدث المشاركين', 'Create participant account as evaluator': 'إنشاء حساب مشارك بصفة مقيّم', 'No students registered yet.': 'لا يوجد متعلمون مسجلون بعد.', 'No registered student accounts yet.': 'لا توجد حسابات متعلمين مسجلة بعد.', 'Only active accounts': 'الحسابات النشطة فقط', 'Only accounts missing email': 'الحسابات دون بريد فقط', 'Only never signed in': 'الحسابات التي لم تسجل الدخول فقط', 'Control / experimental comparison': 'مقارنة المجموعة الضابطة والتجريبية', 'No student data yet.': 'لا توجد بيانات متعلمين بعد.', 'No AI interaction analytics available yet.': 'لا تتوفر تحليلات لتفاعلات الذكاء الاصطناعي بعد.', 'No AI task-mode evidence yet.': 'لا تتوفر بيانات عن أنماط مهام الذكاء الاصطناعي بعد.', 'Concept-level performance': 'الأداء حسب المفهوم', 'No concept scores available yet.': 'لا تتوفر نتائج حسب المفهوم بعد.', 'No participant data yet.': 'لا توجد بيانات مشاركين بعد.', 'No paired pre/post results yet.': 'لا توجد نتائج قبلية/بعدية مزدوجة بعد.', 'No concept-level scores yet.': 'لا توجد نتائج على مستوى المفاهيم بعد.', 'No survey responses yet.': 'لا توجد استجابات للاستبيان بعد.', 'No expert ratings have been recorded yet. Use the LLM Performance Evaluation page to rate AI tutor responses.': 'لم تُسجل تقييمات خبراء بعد. استخدم صفحة تقييم أداء LLM لتقييم استجابات المدرّب.', 'No AI responses match these filters.': 'لا توجد استجابات ذكاء اصطناعي تطابق المرشحات.', 'AI tutor response': 'استجابة المدرّب الذكي', 'No expert ratings saved yet.': 'لا توجد تقييمات خبراء محفوظة بعد.', 'Full saved evaluations': 'جميع التقييمات المحفوظة', 'No logs match the selected filters.': 'لا توجد سجلات تطابق المرشحات.', 'No platform events recorded yet.': 'لم تُسجل أحداث للمنصة بعد.', 'Requests by action': 'الطلبات حسب الإجراء', 'Requests by lesson': 'الطلبات حسب الدرس', 'No animation/simulator/check events recorded yet.': 'لم تُسجل أحداث للحركة أو المحاكي أو الفحص بعد.', 'Learning activity counts': 'أعداد أنشطة التعلم', 'Activity by lesson': 'النشاط حسب الدرس', 'Download learning activity events CSV': 'تنزيل أحداث أنشطة التعلم CSV', 'No time-before-AI events recorded yet.': 'لم تُسجل أزمنة ما قبل طلب الذكاء الاصطناعي بعد.', 'Mean wait before AI by source/task': 'متوسط الانتظار قبل الذكاء الاصطناعي حسب المصدر/المهمة', 'No student-level interaction summary yet.': 'لا يتوفر ملخص تفاعلات على مستوى المتعلم بعد.', 'Download student research journey CSV': 'تنزيل مسار المتعلم البحثي CSV', 'Technical diagnostic': 'التشخيص التقني', 'No group-level data available yet.': 'لا تتوفر بيانات على مستوى المجموعات بعد.', 'Download group comparison CSV': 'تنزيل مقارنة المجموعات CSV', 'Post-tests': 'الاختبارات البعدية', 'Post-test': 'الاختبار البعدي', 'Concept': 'المفهوم', '1 = poor/incorrect, 3 = acceptable/partial, 5 = excellent/highly appropriate': '1 = ضعيف/خاطئ، 3 = مقبول/جزئي، 5 = ممتاز/ملائم جدًا', 'Observe': 'ألاحظ', 'Model': 'أمثّل', 'Measure / interpret': 'أقيس وأفسّر', 'Template-generated visual support': 'دعامة بصرية مولدة من قالب', 'safe SVG': 'SVG آمن', 'Key Qiskit line:': 'سطر Qiskit الأساسي:', 'This card is generated from an approved lesson template, not arbitrary executable AI code.': 'تُولد هذه البطاقة من قالب درس معتمد، لا من كود ذكاء اصطناعي تنفيذي عشوائي.', 'English': 'الإنجليزية', 'Arabic': 'العربية', 'French': 'الفرنسية', 'Auto-detect': 'كشف تلقائي', 'Tutor task': 'مهمة المدرّب', 'Concept focus': 'المفهوم المستهدف', 'Response language': 'لغة الاستجابة', 'Output language': 'لغة المخرجات', 'Coach response language': 'لغة استجابة المدرّب', 'AI response language': 'لغة استجابة الذكاء الاصطناعي'})
FR.update({'Interface language / لغة الواجهة / Langue de l’interface': 'Langue de l’interface', 'Explain a concept': 'Expliquer un concept', 'Generate a practice exercise': "Générer un exercice d'application", 'Check my explanation': 'Vérifier mon explication', 'Debug or interpret Qiskit code': 'Déboguer ou interpréter un code Qiskit', 'Generate structured explanation': 'Générer une explication structurée', 'Generate careful analogy': 'Générer une analogie rigoureuse', 'Generate misconception diagnosis': 'Diagnostiquer une conception erronée', 'Generate mini formative quiz': 'Générer un mini-quiz formatif', 'Connect to Qiskit professionally': 'Relier au code Qiskit', 'Generate polished visual card': 'Générer une carte visuelle professionnelle', 'Ask me one question': 'Me poser une question', 'Give one hint': 'Donner un indice', 'Explain this step': 'Expliquer cette étape', 'Create practice': 'Créer un exercice', 'Learning not started': 'Apprentissage non commencé', 'Ask about the current module, a concept, or a Qiskit code snippet...': 'Posez une question sur le module actuel, un concept ou un extrait Qiskit...', 'Conversation': 'Conversation', 'Missing email': 'E-mail manquant', 'Download account registration list (CSV)': 'Télécharger la liste des comptes (CSV)', 'Account support notes': "Notes d'assistance aux comptes", 'AI support mode by lesson and task': "Mode d'assistance IA par leçon et tâche", 'Download paper-ready analysis workbook': "Télécharger le classeur d'analyse prêt pour publication", 'Focus on LLM / LLM-error responses': 'Se concentrer sur les réponses LLM et leurs erreurs', 'Mode': 'Mode', 'Module': 'Module', 'Rows': 'Lignes', 'Likert responses': 'Réponses de Likert', 'Rows to load': 'Lignes à charger', 'Actor role': "Rôle de l'acteur", 'Event type': "Type d'événement", 'Database OK': 'Base de données opérationnelle', 'DB dialect': 'Dialecte de la base', 'App version': "Version de l'application", 'AI provider': 'Fournisseur IA', 'Live counts': 'Comptages actuels', 'Pilot-safety checks': 'Contrôles de sécurité du pilote', 'Before changing database schema manually, download a backup from Results Export or Neon. These checks do not modify student data.': "Avant de modifier manuellement le schéma de la base, téléchargez une sauvegarde depuis l'export des résultats ou Neon. Ces contrôles ne modifient pas les données.", 'Use the anonymized workbook for analysis and manuscript tables. Use the full backup only for secure administrative backup.': "Utilisez le classeur anonymisé pour les analyses et les tableaux de l'article. Réservez la sauvegarde complète à l'administration sécurisée.", 'AI tutor: local fallback mode': 'Coach IA : mode de secours local', 'LPQS · Learning analytics · Anonymized research exports · Provider-agnostic LLM layer': "LPQS · Analytique de l'apprentissage · Exports anonymisés · Couche LLM indépendante du fournisseur", 'Please sign in first.': "Veuillez d'abord vous connecter.", 'Go to sign in': 'Aller à la connexion', 'I saved my participant code': "J'ai sauvegardé mon code participant", 'Forgot password?': 'Mot de passe oublié ?', 'Go to learning module': "Aller au module d'apprentissage", 'Complete the pre-test first.': "Terminez d'abord le pré-test.", 'Go to pre-test': 'Aller au pré-test', 'Return to learning module': "Retourner au module d'apprentissage", 'Default evaluator password is still active. Change ADMIN_PASSWORD or use EVALUATOR_PASSWORD_HASH before cloud deployment.': 'Le mot de passe évaluateur par défaut est encore actif. Modifiez ADMIN_PASSWORD ou utilisez EVALUATOR_PASSWORD_HASH avant le déploiement.', 'Please enter a valid email address.': 'Saisissez une adresse e-mail valide.', 'You can now sign in using your email, participant code, or exact full name.': 'Vous pouvez maintenant vous connecter avec votre e-mail, votre code participant ou votre nom complet exact.', 'If the link expired, request a new password reset from the sign-in page.': 'Si le lien a expiré, demandez une nouvelle réinitialisation depuis la page de connexion.', 'Invalid identifier or password.': 'Identifiant ou mot de passe incorrect.', 'Invalid registration access code.': "Code d'accès à l'inscription incorrect.", 'Please confirm the study notice before creating an account.': "Confirmez la notice d'étude avant de créer le compte.", 'Invalid evaluator credentials.': 'Identifiants évaluateur incorrects.', 'Write a short attempt first. This keeps the AI tutor formative rather than answer-giving.': "Rédigez d'abord une courte tentative afin que le coach IA reste formatif plutôt que donneur de réponses.", 'AI interaction recorded. Your learning path is complete, so the post-test is available.': "L'interaction IA est enregistrée et le parcours est terminé ; le post-test est disponible.", 'Initial password': 'Mot de passe initial', 'Create participant': 'Créer un participant', 'Prior quantum knowledge': 'Connaissances quantiques antérieures', 'No participants have been registered yet.': "Aucun participant n'est encore inscrit.", 'AI tutor usage by mode': 'Utilisation du coach IA par mode', 'Recent participants': 'Participants récents', 'Create participant account as evaluator': "Créer un compte participant en tant qu'évaluateur", 'No students registered yet.': "Aucun apprenant n'est encore inscrit.", 'No registered student accounts yet.': "Aucun compte apprenant n'est encore enregistré.", 'Only active accounts': 'Comptes actifs uniquement', 'Only accounts missing email': 'Comptes sans e-mail uniquement', 'Only never signed in': 'Comptes jamais connectés uniquement', 'Control / experimental comparison': 'Comparaison contrôle / expérimental', 'No student data yet.': 'Aucune donnée apprenant pour le moment.', 'No AI interaction analytics available yet.': "Aucune analytique d'interaction IA disponible.", 'No AI task-mode evidence yet.': 'Aucune donnée sur les modes de tâches IA.', 'Concept-level performance': 'Performance par concept', 'No concept scores available yet.': 'Aucun score par concept disponible.', 'No participant data yet.': 'Aucune donnée de participant.', 'No paired pre/post results yet.': 'Aucun résultat pré/post apparié.', 'No concept-level scores yet.': 'Aucun score au niveau des concepts.', 'No survey responses yet.': 'Aucune réponse au questionnaire.', 'No expert ratings have been recorded yet. Use the LLM Performance Evaluation page to rate AI tutor responses.': "Aucune évaluation experte n'a encore été enregistrée. Utilisez la page d'évaluation du LLM pour noter les réponses du coach.", 'No AI responses match these filters.': 'Aucune réponse IA ne correspond aux filtres.', 'AI tutor response': 'Réponse du coach IA', 'No expert ratings saved yet.': 'Aucune évaluation experte enregistrée.', 'Full saved evaluations': 'Toutes les évaluations enregistrées', 'No logs match the selected filters.': 'Aucun journal ne correspond aux filtres.', 'No platform events recorded yet.': 'Aucun événement de plateforme enregistré.', 'Requests by action': 'Requêtes par action', 'Requests by lesson': 'Requêtes par leçon', 'No animation/simulator/check events recorded yet.': "Aucun événement d'animation, de simulateur ou de vérification enregistré.", 'Learning activity counts': "Nombre d'activités d'apprentissage", 'Activity by lesson': 'Activité par leçon', 'Download learning activity events CSV': "Télécharger les événements d'apprentissage CSV", 'No time-before-AI events recorded yet.': 'Aucun temps avant requête IA enregistré.', 'Mean wait before AI by source/task': "Attente moyenne avant l'IA par source/tâche", 'No student-level interaction summary yet.': "Aucun résumé d'interactions par apprenant.", 'Download student research journey CSV': 'Télécharger le parcours de recherche apprenant CSV', 'Technical diagnostic': 'Diagnostic technique', 'No group-level data available yet.': 'Aucune donnée au niveau des groupes.', 'Download group comparison CSV': 'Télécharger la comparaison des groupes CSV', 'Post-tests': 'Post-tests', 'Post-test': 'Post-test', 'Concept': 'Concept', '1 = poor/incorrect, 3 = acceptable/partial, 5 = excellent/highly appropriate': '1 = faible/incorrect, 3 = acceptable/partiel, 5 = excellent/très approprié', 'Observe': 'Observer', 'Model': 'Modéliser', 'Measure / interpret': 'Mesurer / interpréter', 'Template-generated visual support': 'Support visuel généré par modèle', 'safe SVG': 'SVG sécurisé', 'Key Qiskit line:': 'Ligne Qiskit clé :', 'This card is generated from an approved lesson template, not arbitrary executable AI code.': "Cette carte provient d'un modèle pédagogique validé, et non d'un code IA exécutable arbitraire.", 'English': 'Anglais', 'Arabic': 'Arabe', 'French': 'Français', 'Auto-detect': 'Détection automatique', 'Tutor task': 'Tâche du coach', 'Concept focus': 'Concept ciblé', 'Response language': 'Langue de réponse', 'Output language': 'Langue de sortie', 'Coach response language': 'Langue de réponse du coach', 'AI response language': "Langue de réponse de l'IA"})

FR.update({"Post-test is locked until at least one AI Tutor interaction is recorded for the experimental group.": "Le post-test reste verrouillé jusqu’à l’enregistrement d’au moins une interaction avec le coach IA pour le groupe expérimental."})


# V4.4: complete localization for dynamic plan guidance and pedagogical guardrails.
AR.update({
    "Participant code, email, or exact registered full name": "\u0631\u0645\u0632 \u0627\u0644\u0645\u0634\u0627\u0631\u0643\u0629 \u0623\u0648 \u0627\u0644\u0628\u0631\u064a\u062f \u0627\u0644\u0625\u0644\u0643\u062a\u0631\u0648\u0646\u064a \u0623\u0648 \u0627\u0644\u0627\u0633\u0645 \u0627\u0644\u0645\u0633\u062c\u0644 \u0643\u0627\u0645\u0644\u0627",
    "Participant code, email, or full registered name": "\u0631\u0645\u0632 \u0627\u0644\u0645\u0634\u0627\u0631\u0643\u0629 \u0623\u0648 \u0627\u0644\u0628\u0631\u064a\u062f \u0627\u0644\u0625\u0644\u0643\u062a\u0631\u0648\u0646\u064a \u0623\u0648 \u0627\u0644\u0627\u0633\u0645 \u0627\u0644\u0645\u0633\u062c\u0644 \u0643\u0627\u0645\u0644\u0627",
    "How to read this plan:": "كيف تقرأ هذه الخطة؟",
    "Start with the concepts listed as weak or recommended.": "ابدأ بالمفاهيم التي ظهرت حاجتها إلى التعزيز أو التي أوصت بها المنصة.",
    "Complete the learning module before relying on the AI tutor.": "أكمل الوحدة التعليمية وحاول بنفسك قبل الاعتماد على المدرّب الذكي.",
    "Use the AI tutor for hints and explanations, not for copying final answers.": "استخدم المدرّب الذكي للتلميحات والتوضيح، لا لنسخ إجابات نهائية.",
    "Next interactive step: click “Start learning module” and complete at least one learning activity.": "الخطوة التفاعلية التالية: اضغط «بدء الوحدة التعليمية» وأكمل نشاطًا تعليميًا واحدًا على الأقل.",
    "Design decision: old static images and legacy micro-videos are hidden from the student path. Active materials are the micro-animation, simulator, code bridge, and check.": "ملاحظة تربوية: أُخفيت الصور الثابتة القديمة والمقاطع المصغرة السابقة من مسار المتعلم. وتعتمد الوحدة الآن على الحركة المصغرة والمحاكي وجسر الكود وفحص الفهم.",
    "AI use reminder: use the AI concept coach tab after writing a short attempt. This keeps generative AI as a formative learning scaffold, not a shortcut.": "تذكير باستخدام الذكاء الاصطناعي: استخدم تبويب مدرّب المفهوم بعد كتابة محاولة قصيرة، حتى يبقى الذكاء التوليدي دعامةً تكوينية للتعلم لا طريقًا مختصرًا إلى الإجابة.",
    "Qiskit documentation": "توثيق Qiskit",
    "IBM Quantum documentation: visualization": "توثيق IBM Quantum: العرض البصري",
    "Qiskit guide: visualize results": "دليل Qiskit لعرض النتائج",
    "Bloch sphere explanation": "شرح كرة بلوخ",
    "IBM Quantum Learning": "IBM Quantum Learning",
    "Microsoft Quantum Katas": "Microsoft Quantum Katas",
})

FR.update({
    "How to read this plan:": "Comment lire ce plan ?",
    "Start with the concepts listed as weak or recommended.": "Commencez par les concepts à renforcer ou recommandés par la plateforme.",
    "Complete the learning module before relying on the AI tutor.": "Terminez le module et effectuez votre propre tentative avant de vous appuyer sur le coach IA.",
    "Use the AI tutor for hints and explanations, not for copying final answers.": "Utilisez le coach IA pour obtenir des indices et des explications, et non pour copier des réponses finales.",
    "Next interactive step: click “Start learning module” and complete at least one learning activity.": "Étape interactive suivante : cliquez sur « Commencer le module » et terminez au moins une activité d’apprentissage.",
    "Design decision: old static images and legacy micro-videos are hidden from the student path. Active materials are the micro-animation, simulator, code bridge, and check.": "Note pédagogique : les anciennes images statiques et micro-vidéos ont été retirées du parcours. Le module s’appuie désormais sur la micro-animation, le simulateur, le pont vers le code et la vérification de compréhension.",
    "AI use reminder: use the AI concept coach tab after writing a short attempt. This keeps generative AI as a formative learning scaffold, not a shortcut.": "Rappel d’usage de l’IA : utilisez l’onglet du coach de concept après une courte tentative afin que l’IA générative reste un étayage formatif, et non un raccourci vers la réponse.",
    "Qiskit documentation": "Documentation Qiskit",
    "IBM Quantum documentation: visualization": "Documentation IBM Quantum : visualisation",
    "Qiskit guide: visualize results": "Guide Qiskit : visualiser les résultats",
    "Bloch sphere explanation": "Explication de la sphère de Bloch",
    "IBM Quantum Learning": "IBM Quantum Learning",
    "Microsoft Quantum Katas": "Microsoft Quantum Katas",
})

# V4.5 evaluator/research workspace translations for legacy pages that still
# use canonical English strings internally.
AR.update({
    "Study Protocol": "بروتوكول الدراسة",
    "Operational checklist for running the 3alimnIA pilot as a controlled educational study.": "قائمة تشغيلية لتنفيذ تجربة 3alimnIA بوصفها دراسة تعليمية مضبوطة.",
    "Registered students": "المتعلمون المسجلون",
    "Consent confirmed": "الموافقات المسجلة",
    "Complete cases": "الحالات المكتملة",
    "Design": "تصميم الدراسة",
    "Active study configuration": "إعدادات الدراسة الحالية",
    "Research workflow safeguards": "ضوابط سير العمل البحثي",
    "Consent and completion audit": "تدقيق الموافقة والاكتمال",
    "Download protocol evidence": "تنزيل أدلة البروتوكول",
    "Download study protocol workbook": "تنزيل مصنف بروتوكول الدراسة",
    "Create participant account as evaluator": "إنشاء حساب مشارك من فضاء المقيّم",
    "Full name": "الاسم الكامل", "Email": "البريد الإلكتروني", "Institution": "المؤسسة",
    "Academic level": "المستوى الأكاديمي", "Prior Python level": "المستوى السابق في Python",
    "Prior quantum knowledge": "المعرفة السابقة بالكوانتوم", "Initial password": "كلمة المرور الأولية",
    "Create participant": "إنشاء المشارك", "Could not create participant": "تعذر إنشاء المشارك",
    "Search by participant code, name, email, or institution": "البحث برمز المشارك أو الاسم أو البريد أو المؤسسة",
    "Only active accounts": "الحسابات النشطة فقط", "Only accounts missing email": "الحسابات دون بريد فقط",
    "Only never signed in": "من لم يسجلوا الدخول بعد", "Registered accounts": "الحسابات المسجلة",
    "Active accounts": "الحسابات النشطة", "Missing email": "بريد مفقود",
    "Signed in at least once": "سجل الدخول مرة على الأقل", "Download account registration list (CSV)": "تنزيل قائمة الحسابات CSV",
    "Select participant": "اختر المشارك", "Learning timeline": "الخط الزمني للتعلم",
    "Likert responses": "استجابات ليكرت", "Open-ended feedback": "التغذية الراجعة المفتوحة",
    "Download group comparison CSV": "تنزيل مقارنة المجموعات CSV",
    "Default evaluator password is still active. Change ADMIN_PASSWORD or use EVALUATOR_PASSWORD_HASH before cloud deployment.": "كلمة مرور المقيّم الافتراضية ما تزال فعالة. غيّر ADMIN_PASSWORD أو استخدم EVALUATOR_PASSWORD_HASH قبل النشر السحابي.",
})
FR.update({
    "Study Protocol": "Protocole d'étude",
    "Operational checklist for running the 3alimnIA pilot as a controlled educational study.": "Liste opérationnelle pour conduire le pilote 3alimnIA comme étude éducative contrôlée.",
    "Registered students": "Apprenants inscrits", "Consent confirmed": "Consentements confirmés",
    "Complete cases": "Cas complets", "Design": "Plan d'étude",
    "Active study configuration": "Configuration active de l'étude",
    "Research workflow safeguards": "Garanties du protocole de recherche",
    "Consent and completion audit": "Audit du consentement et de l'achèvement",
    "Download protocol evidence": "Télécharger les preuves du protocole",
    "Download study protocol workbook": "Télécharger le classeur du protocole",
    "Create participant account as evaluator": "Créer un compte participant",
    "Full name": "Nom complet", "Email": "E-mail", "Institution": "Établissement",
    "Academic level": "Niveau académique", "Prior Python level": "Niveau antérieur en Python",
    "Prior quantum knowledge": "Connaissances quantiques antérieures", "Initial password": "Mot de passe initial",
    "Create participant": "Créer le participant", "Could not create participant": "Impossible de créer le participant",
    "Search by participant code, name, email, or institution": "Rechercher par code, nom, e-mail ou établissement",
    "Only active accounts": "Comptes actifs uniquement", "Only accounts missing email": "Comptes sans e-mail uniquement",
    "Only never signed in": "Jamais connectés uniquement", "Registered accounts": "Comptes inscrits",
    "Active accounts": "Comptes actifs", "Missing email": "E-mail manquant",
    "Signed in at least once": "Connectés au moins une fois", "Download account registration list (CSV)": "Télécharger la liste des comptes CSV",
    "Select participant": "Sélectionner un participant", "Learning timeline": "Chronologie d'apprentissage",
    "Likert responses": "Réponses Likert", "Open-ended feedback": "Commentaires ouverts",
    "Download group comparison CSV": "Télécharger la comparaison des groupes CSV",
    "Default evaluator password is still active. Change ADMIN_PASSWORD or use EVALUATOR_PASSWORD_HASH before cloud deployment.": "Le mot de passe évaluateur par défaut est encore actif. Modifiez ADMIN_PASSWORD ou utilisez EVALUATOR_PASSWORD_HASH avant le déploiement.",
})

TRANSLATIONS = {"ar": AR, "fr": FR, "en": {}}


def page_label(page: str, lang: str | None = None) -> str:
    code = normalize_lang(lang)
    return PAGE_LABELS.get(page, {}).get(code, page)


def page_detail(page: str, lang: str | None = None) -> str:
    code = normalize_lang(lang)
    return PAGE_DETAILS.get(page, {}).get(code, PAGE_DETAILS.get(page, {}).get("en", ""))


def concept_label(concept: str, lang: str | None = None) -> str:
    code = normalize_lang(lang)
    return CONCEPT_LABELS.get(concept, {}).get(code, concept)


def cognitive_label(level: str, lang: str | None = None) -> str:
    code = normalize_lang(lang)
    return COGNITIVE_LEVELS.get(level, {}).get(code, level)


def level_label(level: str, lang: str | None = None) -> str:
    code = normalize_lang(lang)
    return LEVEL_LABELS.get(level, {}).get(code, level)


def _replace_dynamic_patterns(text: str, lang: str) -> str:
    if lang == "en":
        return text
    patterns = []
    if lang == "ar":
        patterns = [
            (r"Current page:\s*", "الصفحة الحالية: "),
            (r"Completed modules:\s*", "الوحدات المكتملة: "),
            (r"Remaining modules:\s*", "الوحدات المتبقية: "),
            (r"Score:\s*", "النتيجة: "),
            (r"Module\s+(\d+)", r"الوحدة \1"),
            (r"Question\s+(\d+)", r"السؤال \1"),
        ]
    elif lang == "fr":
        patterns = [
            (r"Current page:\s*", "Page actuelle : "),
            (r"Completed modules:\s*", "Modules terminés : "),
            (r"Remaining modules:\s*", "Modules restants : "),
            (r"Score:\s*", "Score : "),
            (r"Module\s+(\d+)", r"Module \1"),
            (r"Question\s+(\d+)", r"Question \1"),
        ]
    out = text
    for pattern, repl in patterns:
        out = re.sub(pattern, repl, out, flags=re.IGNORECASE)
    return out


@lru_cache(maxsize=8192)
def translate(text: str, lang: str = DEFAULT_LANGUAGE) -> str:
    """Translate a rendered UI string while preserving HTML/code values.

    The function supports exact matches and phrase replacement inside HTML or
    dynamic f-strings. Technical tokens such as Qiskit, qubit, H, CNOT, and code
    snippets are intentionally preserved.
    """
    code = normalize_lang(lang)
    if code == "en" or not isinstance(text, str) or not text:
        return text
    mapping = TRANSLATIONS[code]
    if text in mapping:
        return mapping[text]
    out = text
    # Longest first prevents a short label from breaking a longer sentence.
    for source in sorted(mapping, key=len, reverse=True):
        if source in out:
            out = out.replace(source, mapping[source])
    return _replace_dynamic_patterns(out, code)



def localize_generated_text(text: str, lang: str | None = None) -> str:
    """Normalize learner-visible generated prose without touching code blocks.

    LLMs occasionally repeat English context keys or concept labels even when a
    non-English response was requested. This display-level pass localizes known
    pedagogical labels while preserving fenced Qiskit/Python code verbatim.
    """
    code = normalize_lang(lang)
    if code == "en" or not isinstance(text, str) or not text:
        return text

    ar_terms = {
        "How to read this plan": "كيف تقرأ هذه الخطة؟",
        "Personalized plan": "الخطة الشخصية",
        "Personal study plan": "الخطة الدراسية الشخصية",
        "Concepts to reinforce": "المفاهيم التي تحتاج إلى تعزيز",
        "Recommended lesson sequence": "تسلسل الدروس المقترح",
        "Weak concepts": "المفاهيم التي تحتاج إلى تعزيز",
        "Next step": "الخطوة التالية",
        "Step 1": "الخطوة الأولى",
        "Step 2": "الخطوة الثانية",
        "Step 3": "الخطوة الثالثة",
        "Step 4": "الخطوة الرابعة",
        "Diagnosis": "التشخيص",
        "Recommended steps": "الخطوات المقترحة",
        "Practice guidance": "إرشادات التطبيق",
        "Reflection question": "سؤال التأمل",
        "Review": "راجع",
        "Practice": "طبّق",
        "Complete": "أكمل",
        "AI tutor": "المدرّب الذكي",
        "learning module": "الوحدة التعليمية",
        "Shots and counts": "التكرارات والعدّادات (shots and counts)",
        "Qiskit debugging": "تصحيح أخطاء Qiskit",
        "Circuit basics": "أساسيات الدارة الكمية",
        "Qubit measurement": "قياس الكيوبت",
        "Hadamard and superposition": "بوابة هادامارد والتراكب",
        "CNOT and correlation": "بوابة CNOT والارتباط",
        "debugging": "تصحيح الأخطاء",
    }
    fr_terms = {
        "How to read this plan": "Comment lire ce plan ?",
        "Personalized plan": "Plan personnalisé",
        "Personal study plan": "Plan d’étude personnalisé",
        "Concepts to reinforce": "Concepts à renforcer",
        "Recommended lesson sequence": "Séquence de leçons recommandée",
        "Weak concepts": "Concepts à renforcer",
        "Next step": "Étape suivante",
        "Step 1": "Étape 1",
        "Step 2": "Étape 2",
        "Step 3": "Étape 3",
        "Step 4": "Étape 4",
        "Diagnosis": "Diagnostic",
        "Recommended steps": "Étapes recommandées",
        "Practice guidance": "Conseils de pratique",
        "Reflection question": "Question de réflexion",
        "Review": "Réviser",
        "Practice": "Pratiquer",
        "Complete": "Terminer",
        "AI tutor": "coach IA",
        "learning module": "module d’apprentissage",
        "Shots and counts": "shots et comptages",
        "Qiskit debugging": "débogage Qiskit",
        "Circuit basics": "bases du circuit quantique",
        "Qubit measurement": "mesure du qubit",
        "Hadamard and superposition": "Hadamard et superposition",
        "CNOT and correlation": "CNOT et corrélation",
        "debugging": "débogage",
    }
    terms = ar_terms if code == "ar" else fr_terms
    chunks = re.split(r"(```[\\s\\S]*?```)", text)
    for index in range(0, len(chunks), 2):
        chunk = chunks[index]
        for source in sorted(terms, key=len, reverse=True):
            chunk = re.sub(re.escape(source), terms[source], chunk, flags=re.IGNORECASE)
        chunks[index] = chunk
    return "".join(chunks)

def tr(text: Any, lang: str | None = None) -> Any:
    if not isinstance(text, str):
        return text
    return translate(text, normalize_lang(lang) if lang else current_lang())


def tr_list(values: Iterable[Any], lang: str | None = None) -> list[Any]:
    return [tr(value, lang) if isinstance(value, str) else value for value in values]


def localize_dataframe(df: Any, lang: str | None = None) -> Any:
    """Return a display-only copy with translated column headers."""
    if df is None or not hasattr(df, "rename"):
        return df
    code = normalize_lang(lang) if lang else current_lang()
    if code == "en":
        return df
    try:
        return df.rename(columns={c: translate(str(c).replace("_", " ").title(), code) for c in df.columns})
    except Exception:
        return df


def apply_language_css(st_module: Any, lang: str | None = None) -> None:
    code = normalize_lang(lang) if lang else current_lang(st_module)
    dir_value = direction(code)
    align = "right" if code == "ar" else "left"
    font_stack = "'Noto Sans Arabic','Tajawal','Segoe UI',Arial,sans-serif" if code == "ar" else "'Inter','Segoe UI',Arial,sans-serif"
    # The native Streamlit rail is docked according to the reading direction.
    # This keeps Arabic navigation on the right and French/English navigation
    # on the left, while the main document retains its own independent scroll.
    rail_side = "right:0 !important; left:auto !important;" if code == "ar" else "left:0 !important; right:auto !important;"
    main_offset = "margin-right:var(--v48-rail-width) !important; margin-left:0 !important;" if code == "ar" else "margin-left:var(--v48-rail-width) !important; margin-right:0 !important;"
    reopen_side = "right:.72rem !important; left:auto !important;" if code == "ar" else "left:.72rem !important; right:auto !important;"
    collapse_side = "left:.45rem !important; right:auto !important;" if code == "ar" else "right:.45rem !important; left:auto !important;"
    st_module.markdown(
        f"""
        <style>
        html, body, [data-testid="stAppViewContainer"], .stApp {{ direction:{dir_value}; font-family:{font_stack}; }}
        body, button, input, textarea, select, [data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"] {{ font-family:{font_stack} !important; }}
        [data-testid="stAppViewContainer"] .block-container {{ direction:{dir_value}; text-align:{align}; }}
        [data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"],
        [data-testid="stCaptionContainer"], [data-testid="stAlertContainer"],
        [data-testid="stMetric"], [data-testid="stDataFrame"] {{ direction:{dir_value}; text-align:{align}; }}
        input, textarea {{ direction:{dir_value}; text-align:{align}; }}
        pre, code, .stCodeBlock, [data-testid="stCodeBlock"] {{ direction:ltr !important; text-align:left !important; }}
        .qai-code, .qai-code-badge {{ direction:ltr !important; text-align:left !important; }}
        .qai-route-strip, .qai-v11-steps, .qai-dashboard-grid, .qai-hero-grid,
        .brand-how-grid, .brand-track-grid {{ direction:{dir_value}; }}
        .qai-side-next {{ border-left:{'1px solid var(--qai-border)' if code == 'ar' else '4px solid var(--qai-blue)'} !important;
                         border-right:{'4px solid var(--qai-blue)' if code == 'ar' else '1px solid var(--qai-border)'} !important; }}
        .qai-stage-chip, .qai-pill, .qai-concept-pill {{ margin-right:{'0' if code == 'ar' else '.22rem'} !important; margin-left:{'.22rem' if code == 'ar' else '0'} !important; }}

        /* V4.8 - native docked navigation. The sidebar is a viewport-level
           application rail, not a column inside the scrolling document. */
        @media (min-width: 901px) {{
          [data-testid="stSidebarCollapsedControl"] {{ {reopen_side} }}
          section[data-testid="stSidebar"]:has(.v48-native-sidebar-marker) [data-testid="stSidebarCollapseButton"] {{
            {collapse_side}
          }}
          section[data-testid="stSidebar"]:has(.v48-native-sidebar-marker) {{
            {rail_side}
            top:0 !important;
            bottom:0 !important;
            width:var(--v48-rail-width) !important;
            min-width:var(--v48-rail-width) !important;
            max-width:var(--v48-rail-width) !important;
            height:100dvh !important;
            transform:none !important;
          }}
          [data-testid="stAppViewContainer"]:has(.v48-native-sidebar-marker) > .main {{
            {main_offset}
            width:calc(100vw - var(--v48-rail-width)) !important;
            max-width:calc(100vw - var(--v48-rail-width)) !important;
            flex:0 0 calc(100vw - var(--v48-rail-width)) !important;
          }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def install_streamlit_i18n(st_module: Any) -> None:
    """Patch display-only Streamlit calls once so every page follows language.

    Internal option values and route keys remain unchanged. Only visible labels,
    help text, placeholders, tab captions, alerts, and display dataframes are
    localized. This allows legacy pages to inherit i18n without changing study
    database semantics.
    """
    if getattr(st_module, "_3alimnia_i18n_installed", False):
        return
    st_module._3alimnia_i18n_installed = True
    originals: Dict[str, Any] = {}
    st_module._3alimnia_i18n_originals = originals

    label_methods = {
        "markdown", "caption", "info", "warning", "error", "success", "write", "text",
        "title", "header", "subheader", "button", "checkbox", "text_input", "text_area",
        "selectbox", "radio", "slider", "number_input", "multiselect", "expander",
        "form_submit_button", "download_button", "metric", "chat_input", "select_slider",
        "spinner", "progress",
    }

    for name in label_methods:
        if not hasattr(st_module, name):
            continue
        original = getattr(st_module, name)
        originals[name] = original

        def make_wrapper(fn: Any, method_name: str):
            def wrapper(*args: Any, **kwargs: Any):
                args = list(args)
                if args and isinstance(args[0], str):
                    args[0] = tr(args[0])
                for key in ("label", "help", "placeholder", "text"):
                    if isinstance(kwargs.get(key), str):
                        kwargs[key] = tr(kwargs[key])
                return fn(*args, **kwargs)
            wrapper.__name__ = getattr(fn, "__name__", method_name)
            return wrapper

        setattr(st_module, name, make_wrapper(original, name))

    if hasattr(st_module, "tabs"):
        originals["tabs"] = st_module.tabs
        original_tabs = st_module.tabs

        def tabs_wrapper(labels: Iterable[str], *args: Any, **kwargs: Any):
            return original_tabs(tr_list(labels), *args, **kwargs)
        st_module.tabs = tabs_wrapper

    if hasattr(st_module, "dataframe"):
        originals["dataframe"] = st_module.dataframe
        original_df = st_module.dataframe

        def dataframe_wrapper(data: Any = None, *args: Any, **kwargs: Any):
            return original_df(localize_dataframe(data), *args, **kwargs)
        st_module.dataframe = dataframe_wrapper

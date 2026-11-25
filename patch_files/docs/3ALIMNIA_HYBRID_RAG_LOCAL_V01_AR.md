# 3alimnIA — Hybrid RAG + Local AI (MVP V0.1)

**تاريخ التنفيذ:** 13 نوفمبر 2026  
**المصدر:** الحزمة المرفقة `qai_platform_ (11)(1).zip`.  
**الحالة:** تعديل برمجي أولي اجتاز اختبارات وحدة ومحاكاة، **وليس إطلاقًا إنتاجيًا أو اختبارًا كاملًا على حاسوب المستخدم**.

## 1. التصميم

```text
Teacher (authenticated and project owner)
  └── Course reference library (PDF / DOCX / TXT / MD)
       ├── Draft → explicit teacher approval / revocation
       ├── SQLite FTS5 lexical index
       └── Optional Ollama multilingual embeddings (local)
             └── Hybrid RRF retrieval, owner+project scope, approved only
                    ├── Teacher documents ranked before approved external docs
                    ├── Source identifier, filename, page (PDF), chunk
                    ├── Course-production phase prompt (educational_builder.py)
                    └── Individual lesson-block prompt (lesson_block_generation_engine.py)
                           └── Existing quality gate + teacher review
  └── Local model provider: model_router → content_generation_engine → Ollama /api/chat
       └── Existing Groq/Gemini preserved; cloud fallback for local provider OFF by default
```

**ملحوظة:** البحث الويبّي الحالي يبقى منفصلًا عن الفهرس المحلي في هذه النسخة. المراجع الخارجية يمكن فهرستها كوثائق يديرها مشغّل موثوق، لكن لا توجد آلية تجلب أي صفحة تلقائيًا إلى الفهرس ولا آلية تحقق مستقل من استحقاق/ترخيص استعمالها.

## 2. ما نُفذ فعليًا

- `local_ai.py`: عميل Ollama يستخدم `/api/chat` و`/api/embed`، دون مفتاح API ودون خروج تلقائي إلى الإنترنت؛ يقبل loopback فقط ما لم يفعّل مسؤول المنصة `OLLAMA_ALLOW_REMOTE` صراحةً.
- `model_router.py` و`content_generation_engine.py`: إضافة مزوّد `ollama` القابل للاختيار عبر إعدادات البيئة، مع منع الـcloud fallback تلقائيًا؛ تدعم المهام ذات المخرج البنيوي JSON schema على مستوى الطلب.
- `hybrid_rag.py`: فهرسة SQLite FTS5؛ تقسيم المرجع إلى مقاطع مع رقم الصفحة للـPDF؛ embeddings اختيارية من Ollama؛ دمج نتائج lexical + vector بطريقة Reciprocal Rank Fusion؛ عزل دقيق بالمالك والمشروع؛ منع استرجاع الوثائق غير المعتمدة؛ أولوية المراجع الخاصة بالأستاذ على المراجع الخارجية المعتمدة.
- `teacher_studio.py`: داخل خطوة المصادر، واجهة رفع مرجع إلى حالة Draft، ثم اعتماد أو إلغاء اعتماد أو حذف المصدر. الرفع مرتبط بالحساب الحالي والمشروع الذي تأكدت المنصة من ملكيته.
- `educational_builder.py`: إدراج استرجاع مخصص لمرحلة إعداد المقرر وإشارات RAG في prompt، مع إحالة الاستشهادات غير الصحيحة أو الغائبة لمراجعة الأستاذ.
- `lesson_block_generation_engine.py`: استرجاع مخصص لكل درس/قسم، وإضافة المصدر إلى القائمة المسموحة، والتحقق من المعرّفات `RAG...`. تم إصلاح `NameError` السابق في `approve_full_lesson` عبر جلب الـblueprint المعتمد والتحقق من تطابق المشروع.
- `main_app.py` و`attempt_gate.py`: تعطيل كلمة مرور المقيّم الافتراضية وتجاوز Demo للـattempt-first افتراضيًا ضمن إصلاحات الأمان العاجلة.
- `rag_cli.py`: إدارة الفهرس من الطرفية لمشغّل موثوق؛ ليست واجهة عامة متاحة لمستخدمين مجهولين.
- `tests/test_hybrid_rag_v01.py`: اختبارات العزل، واعتماد المصادر، وسحب الاعتماد، وحذف الوثائق، وأولوية مصادر الأستاذ، والاسترجاع الهجين بمحاكاة embeddings، والتوجيه المحلي، وعقود الـprompts.

## 3. تشغيل Ollama على Windows

ابدئي بتثبيت **Ollama من الموقع الرسمي**: https://ollama.com/download

ثم من Windows Terminal أو PowerShell:

```powershell
ollama pull qwen3:4b
ollama pull qwen3-embedding:0.6b
ollama list
```

إن كان الجهاز محدود الذاكرة، يمكن تجربة `qwen3:1.7b` بدل `qwen3:4b`. يجب قياس دقة المحتوى بلغات العمل، لأن الحجم الأصغر قد يضعف جودة الشروحات والمراجع.

من داخل مجلد المشروع بعد تثبيت `requirements.txt`:

**Windows CMD**:

```bat
set CONTENT_LLM_PROVIDER=ollama
set OLLAMA_ENABLED=true
set OLLAMA_BASE_URL=http://127.0.0.1:11434
set CONTENT_OLLAMA_MODEL=qwen3:4b
set LOCAL_AI_ALLOW_CLOUD_FALLBACK=false
set RAG_ENABLED=true
set RAG_USE_LOCAL_EMBEDDINGS=true
set RAG_EMBEDDING_MODEL=qwen3-embedding:0.6b
set CONTENT_OLLAMA_INPUT_TOKENS=4600
set CONTENT_OLLAMA_MAX_OUTPUT_TOKENS=2400
streamlit run app.py
```

**PowerShell**: استبدلي كل `set X=Y` بـ `$env:X="Y"`.

إذا لم يكون Ollama يعمل، شغلي `ollama serve` وفق إعداد تشغيله المحلي. لا تعرضي المنفذ `11434` مباشرةً على الإنترنت.

لاختيار **نمط محلي فقط** من دون بحث خارجي، أضيفي `set AI_PRIVACY_MODE=local_only`. لكن هذا يغلق البحث الويبّي، **ولا يضمن بعدُ إمكانية إنجاز المسار الكامل لإنشاء مقرر جديد دون إنترنت** لأن Blueprint الأصلي ما زال يشترط Evidence Bundle معتمدًا من التدفق السابق. بناء محول لـRAG evidence → teacher-reviewable Evidence Bundle هو المهمة التالية.

في نمط الجمع بين محلي/ويب، اتركي `AI_PRIVACY_MODE` غير مضبوط، وأبقي `LOCAL_AI_ALLOW_CLOUD_FALLBACK=false`. سيعمل **التوليد نفسه** على Ollama؛ أما زر البحث الويبّي الحالي فسيستعمل مزوّده الخارجي إذا اختاره الأستاذ. يجب التعامل مع البحث خارج الجهاز على أنه اتصال سحابي واضح للمستخدم.

## 4. طريقة إدخال المصادر

داخل حساب الأستاذ → مشروع محفوظ → خطوة **المصادر**:

1. افتحي **مكتبة مراجع RAG المحلية**.
2. ارفعي PDF/DOCX/TXT/MD (حد أولي 20 MiB للملف؛ عدد كبير من الصفحات يحتاج تحسينًا لاحقًا).
3. وافقي على فهرسة الملف محليًا، ثم اضغطي **فهرسة مرجع (مسودة)**.
4. راجعي المصدر واعتمديه صراحةً. **المسودات غير المعتمدة لا تُستخدم في إنشاء الدروس**.
5. عند توليد مرحلة/درس، ستحصل prompts على مقاطع موثقة بمعرّفات `[RAGXXXXXXXXXXXX]`. الربط بالمعرّف لا يثبت أن كل ادعاء صحيح؛ يجب التحقق العلمي البشري.

### فهرسة مرجع من الطرفية — للمشغّل فقط

```powershell
python rag_cli.py add --teacher USERNAME --project-id 5 --file "C:\\references\\quantum.pdf"
python rag_cli.py list --teacher USERNAME --project-id 5
python rag_cli.py approve --teacher USERNAME --project-id 5 --source-id RAGABCDEF012345
python rag_cli.py search --teacher USERNAME --project-id 5 --query "superposition quantique"
```

**لا توزّعي هذا CLI على المستخدمين كخدمة عامة؛** الطرفية تفترض صلاحية المشغّل لا جلـسة مستخدم معتمدة.

## 5. معايير قبول النسخة

- فهرسة مرجع PDF نصي، مع عرض رقم الصفحة، وDOCX؛ لا يوجد OCR آلي للـPDF المصور.
- لا تظهر مراجع الأستاذ A عند البحث من حساب الأستاذ B، ولا من مشروع آخر للأستاذ A.
- لا تستخدم الوثائق Draft في توليد أي فقرة، ويزيل سحب الاعتماد نتائجها فورًا.
- أولوية الوثائق المعتمدة الخاصة بالأستاذ، ثم المراجع الخارجية المعتمدة.
- ظهور الاستشهاد في نص المولد مع قائمة أصلية تُظهر من أين أتى النص؛ لا يُقبل الاعتماد النهائي تلقائيًا.
- تعذّر Ollama يجب أن يعطي خطأ موضحًا **من دون إرسال الوثائق تلقائيًا إلى Groq أو Gemini**.
- اختبار سير عمل كامل Streamlit + حساب أستاذ + مقرر + مشروع محفوظ + درس + موافقة أستاذ لم يُنفذ بعد، ويجب أن يسبق أي تجربة مؤسسية.

## 6. قيود لا يجوز إخفاؤها

- تم اختبار الـAPI بمحاكاة الاستجابات، لا بنموذج فعلي على جهاز المستخدم؛ لا تتوفر هنا نسخة Ollama ولا النموذج المحمّل.
- Qwen3 يمكن أن يختلق معلومات حتى مع RAG. التحقق الحالي يتحقق من **وجود** معرف مصدر مسموح، لا من أن النص يثبت الادعاء.
- لا توجد قاعدة بيانات متجهية متعددة المؤسسات؛ يقوم التنفيذ الأولي بمسح متجهات محلية بحد 5000 مقطع لكل نطاق. الانتقال إلى pgvector أو Qdrant وفهارس ANN مطلوب للتوسع.
- لا توجد معالجة للـscanned PDFs/المعادلات المعقدة ولا مراجعة ترخيص آلية.
- النصوص المفهرسة محفوظة محليًا في SQLite، ولكنها غير مشفرة على مستوى التطبيق. يلزم تشفير قرص ونسخ احتياطي وسياسة حذف قبل استعمال بيانات حساسة.
- تغيير نموذج embeddings بعد فهرسة بعض الوثائق يتطلب إعادة فهرسة هذه الوثائق؛ لا تخلطي متجهات ذات أبعاد مختلفة.
- ليست هناك تجربة مشتركة فعلية لعدة مستخدمين، ولا اختبار اختراق؛ لا تعتبر هذه حزمة Production-ready.
- ملف الأسرار الأصلي `.streamlit/secrets.toml` موجود في الحزمة الأصلية؛ **يجب تدوير الأسرار القديمة وإخراجها من أي نشر/مشاركة**. الحزمة الجديدة تستثنيه.

## 7. تجربة المقال العلمي المقترحة

**عنوان عمل:** *Evidence-Grounded Multilingual Course Authoring with Teacher-Prioritized Hybrid Retrieval: Architecture and Controlled Evaluation of 3alimnIA*.

- مقارنة موحدة **بنفس نموذج التوليد**: (A) بدون RAG، (B) web research الحالي، (C) teacher-prioritized Hybrid RAG.
- مجموعة موضوعات عربية وفرنسية وإنجليزية، مع تقسيم بحسب المجال وصعوبة المفاهيم؛ وثائق مرجعية معتمدة مسبقًا.
- تقييم مستقل أعمى للحقائق، نسبة الادعاءات المسندة بمصادر، صحة الاستشهاد إلى الصفحة، التغطية التعليمية، اتساق الأسئلة مع الأهداف، والجهد البشري اللازم للتصحيح.
- تكلفة الزمن والطاقة/الموارد مقارنة بين محلي وسحابي لكن **بمرحلة تحليل منفصلة** عن أثر RAG، لتجنب خلط أثر نوع النموذج بأثر الاسترجاع.
- معالجة حالات تضارب الوثائق، مصدر غير موثوق، مستند تعليمات خبيثة، وتغييب وثيقة حاسمة (اختبار الاستناد والامتناع).
- تقرير جودة نموذج التوليد وموعد نسخته وترخيصه وإعداداته، ومقاييس الاسترجاع (Recall@K وnDCG)، والاختلافات بين اللغات.

إضافة RAG وحدها ليست نتيجة علمية؛ مساهمة الورقة يجب أن تُثبت بالمقارنة والبيانات المفتوحة المسموح نشرها.

## 8. الأولويات التالية

1. اختبار Ollama فعليًا على مواصفات الحاسوب الهدف، وقبول ملفات PDF/Word حقيقية.
2. بناء محول teacher-approved RAG sources → Evidence Bundle قابل لاعتماد الأستاذ لتمكين الإنتاج دون الاعتماد على البحث الويبّي.
3. اختبار E2E كامل لرحلة الأستاذ والطالب، مع فصل بيانات Demo عن البحث.
4. توسيع المدقق إلى **claim-level grounding** يتتبع كل ادعاء إلى صفحة ويكشف تناقض المصادر.
5. ضوابط تراخيص ومؤسسة/tenant وتحكم بالحذف والتصدير وتوثيق أمني، ثم تقييم النشر التجاري وملف Label.

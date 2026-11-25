# 3alimnIA V6.18.5 — Premium Lesson Workspace & Pedagogical Orchestrator

## الهدف

هذا الإصدار لا يضيف مرحلة جديدة إلى رحلة الأستاذ. بل يعيد ضبط **صفحة إنشاء ومراجعة الدرس** بحيث تصبح الواجهة بسيطة، بينما تصبح عملية التوليد أكثر صرامة تربويًا في الخلفية.

المبدأ المركزي:

> الذكاء التوليدي شريك في التصميم والتغذية الراجعة والتكييف، والأستاذ هو صاحب القرار والاعتماد النهائي.

## ما تغير في الواجهة

### 1. رأس درس موحد ومضغوط

تظهر المعلومات التي يحتاجها الأستاذ مباشرة:

- رقم الدرس من إجمالي الدروس.
- اسم الدرس ومدته.
- تقدم المقرر.
- تقدم الدرس.
- عدد الدروس المتبقية.

تم الاستغناء عن بطاقات المزود والنموذج والكلمات وزمن الاستجابة في الواجهة الأساسية. تبقى هذه المعلومات في «التفاصيل التقنية» فقط.

### 2. شريط التصميم التربوي

يعرض بصورة هادئة المبادئ التي يطبقها المولد في الدرس:

- فاعلية المتعلم.
- الاسترجاع النشط.
- التدرج في الدعم.
- التقويم والتغذية الراجعة.
- ما وراء المعرفة.

هذه ليست أزرارًا إضافية؛ هي شرح مختصر لمنطق الدرس كي يفهم الأستاذ لماذا بُني بهذه الصورة.

### 3. خريطة أقسام الدرس

تظهر الأقسام التسعة في شريط واحد:

1. تنشيط المعارف السابقة.
2. شرح المفهوم.
3. مثال محلول.
4. تدريب موجه.
5. تدريب مستقل.
6. الأخطاء الشائعة ومعالجتها.
7. تقويم تكويني.
8. ملخص الدرس.
9. موارد ومتابعة.

الحالة تظهر بالنص واللون معًا، ولا يعتمد التصميم على اللون وحده.

### 4. تنظيف المخرجات قبل العرض

أضيف `lesson_content_renderer.py` ليقوم بالعرض الآمن دون تغيير النسخة المحفوظة في قاعدة البيانات:

- إزالة أسطر `None` و`null` وحقول metadata الفارغة من واجهة الأستاذ.
- الحفاظ على `None` عندما يكون جزءًا حقيقيًا من كود Python داخل code fence.
- إزالة تكرار العناوين العربية والإنجليزية في الواجهة العربية.
- تحويل عناوين شائعة مثل `Worked example` و`Teacher implementation note` إلى عنوان عربي واحد.
- إصلاح code fence غير المغلق في العرض حتى لا يفسد بقية الصفحة، مع إبقائه خطأ جودة يمنع الاعتماد.
- إبقاء الكود LTR حتى عندما يكون الشرح RTL.

### 5. «لماذا هذا القسم؟»

كل قسم يحمل مبررًا تربويًا قصيرًا، مثل أن المثال المحلول يهدف إلى نمذجة الحل مع الحفاظ على نشاط المتعلم قبل كشف الحل الكامل.

### 6. جودة تربوية مفهومة

بدل إظهار JSON validation للأستاذ، تظهر ملاحظات مثل:

- المثال يحتاج محاولة للمتعلم قبل الحل.
- المثال يحتاج تلميحات متدرجة.
- التقويم يحتاج معيار نجاح أو تغذية راجعة قابلة للتنفيذ.
- الملخص يحتاج تأملًا قصيرًا في التعلم.
- توجد قيمة فارغة أو مؤقتة يجب مراجعتها.
- كتلة كود غير مغلقة.

الملاحظات غير المانعة تبقى تحت قرار الأستاذ. الأخطاء البنيوية مثل code fence غير المغلق تمنع اعتماد الدرس حتى تُحل.

## المحرك التربوي الجديد

أضيف الملف:

```text
pedagogical_orchestrator.py
```

وهو يفصل القواعد التربوية عن صياغة Prompt العامة. لكل قسم من الدرس:

- غرض تربوي.
- مبادئ تعلم مرتبطة به.
- حركات تصميم إلزامية يطلبها النظام من النموذج.
- حدود واضحة لدور الذكاء التوليدي.

### مثال: «مثال محلول»

يفرض المحرك تسلسلًا من نوع:

```text
المهمة
→ محاولة المتعلم
→ تلميحات متدرجة
→ الحل النموذجي مع تفسير لماذا
→ تحقق ذاتي / نقل قريب
```

### مثال: «التقويم التكويني»

يطلب:

- الارتباط بهدف تعلم أو معيار نجاح.
- أكثر من شكل استجابة عندما يناسب المحتوى.
- تغذية راجعة قابلة للتنفيذ.
- قاعدة قرار للأستاذ: إعادة شرح، مثال إضافي، أو الانتقال.

### مثال: «ملخص الدرس»

لا يكتفي بإعادة النص، بل يطلب استرجاعًا قصيرًا وتأملًا من نوع:

- ماذا أستطيع أن أفعل الآن؟
- ما الذي ما يزال غير واضح؟
- ما الخطوة التالية في التدريب؟

## الأسس البحثية التي وُظفت

تمت مراجعة المصادر التالية قبل بناء هذا الإصدار:

1. UNESCO — *Guidance for generative AI in education and research*.
   - نهج إنساني يركز على دور الإنسان، السلامة، والتحقق التربوي.
   - https://www.unesco.org/en/articles/guidance-generative-ai-education-and-research

2. UNESCO — *AI Competency Framework for Teachers*.
   - تصور العلاقة الجديدة Teacher–AI–Student، وأهمية AI pedagogy والإشراف البشري.
   - https://www.unesco.org/en/articles/ai-competency-framework-teachers

3. U.S. Institute of Education Sciences / What Works Clearinghouse — *Organizing Instruction and Study to Improve Student Learning*.
   - الاسترجاع النشط.
   - التناوب بين الأمثلة المحلولة وحل المشكلات.
   - الأسئلة التفسيرية العميقة.
   - https://ies.ed.gov/ncee/wwc/PracticeGuide/1

4. Education Endowment Foundation — *Metacognition and Self-Regulated Learning*, second edition (2025).
   - التخطيط والمراقبة والتقييم.
   - دمج الاستراتيجيات الميتامعرفية في درس مادة محددة بدل تقديمها بمعزل عن المحتوى.
   - https://educationendowmentfoundation.org.uk/education-evidence/guidance-reports/metacognition

5. Education Endowment Foundation — *Teacher Feedback to Improve Pupil Learning*.
   - التغذية الراجعة المبنية على دليل من أداء المتعلم، مع تركيز على ما يساعده على التقدم.
   - https://educationendowmentfoundation.org.uk/education-evidence/guidance-reports/feedback

6. Kestin et al., Scientific Reports (2025) — randomized controlled trial of an AI tutor in college physics.
   - الدراسة مهمة كإشارة على إمكانات التدريس المدعوم بالذكاء التوليدي عندما يُبنى الـ tutor على ممارسات تربوية مقصودة، وليست أساسًا لافتراض أن AI أفضل دائمًا من التدريس البشري.
   - https://www.nature.com/articles/s41598-025-97652-6

7. World Bank (2025) — *From Chalkboards to Chatbots*.
   - نتائج تجريبية واعدة لتدريس مدعوم بالذكاء التوليدي ضمن تنفيذ منظم، متوافق مع المنهاج، ومدعوم من المعلم.
   - https://documents.worldbank.org/en/publication/documents-reports/documentdetail/099548105192529324

## قرار معماري مهم

القواعد التربوية **ليست مخفية داخل Prompt ضخم واحد**. أصبحت وحدة برمجية مستقلة يمكن:

- اختبارها.
- تعديلها.
- مقارنة إصداراتها.
- استخدامها مستقبلًا في AI Coach.
- توثيقها في مقال علمي حول المنصة.

وهذا يسمح لاحقًا بتسجيل أي «سياسة تربوية» استُخدمت لإنتاج درس محدد.

## الملفات الجديدة

```text
pedagogical_orchestrator.py
lesson_content_renderer.py
validate_v6185_premium_lesson_workspace.py
V6_18_5_PREMIUM_LESSON_WORKSPACE_PEDAGOGICAL_ORCHESTRATOR_AR.md
```

## الملفات المعدلة

```text
lesson_block_generation_engine.py
teacher_studio.py
db.py
.streamlit/v6_theme.css
README.md
CHANGELOG.md
```

كما تم تحديث بعض Validators القديمة لتقبل رقم الإصدار الجديد دون اعتبار الترقية فشلًا.

## لا توجد Migration جديدة

هذا الإصدار لا يضيف جدولًا أو عمودًا جديدًا إلى قاعدة البيانات، ولا يحتاج Secret جديدًا.

## التحقق

```bash
python validate_v6185_premium_lesson_workspace.py
python validate_v6184_simple_teacher_journey.py
python validate_v6183_guided_blueprint_lesson_flow.py
python validate_v6182_blueprint_editor_runtime_ui.py
python validate_v6181_blueprint_api_contract.py
python validate_v618_global_design_system.py
python validate_v616_lesson_block_generation.py
python validate_v615_blueprint_editor_versioning.py
python -m compileall .
```

## الاختبار الحي بعد النشر

1. افتح مشروعًا بمخطط معتمد.
2. افتح «إنشاء الدروس».
3. أنشئ درسًا كاملًا.
4. تحقق من اختفاء حقول `None` من العرض.
5. تحقق من أن العناوين العربية لا تتكرر بالإنجليزية.
6. افتح قسمًا يحتوي كود Python وتأكد من بقاء الكود LTR.
7. افتح «ملاحظات الجودة التربوية» إن ظهرت.
8. صحح أو أعد إنشاء القسم عند وجود ملاحظة جوهرية.
9. اعتمد الدرس وانتقل إلى التالي.

## ما يأتي بعد V6.18.5

الخطوة التالية المقترحة ليست إضافة مزيد من النصوص، بل بناء **V6.19 Pedagogical Quality Gate & Adaptive AI Coach** لربط:

- أداء المتعلم.
- الأخطاء المفاهيمية.
- مستوى الدعم.
- التلميحات المتدرجة.
- التقويم التكويني.
- قرار الانتقال أو إعادة التدريس.

بحيث يصبح الذكاء التوليدي شريكًا تكيفيًا داخل حلقة تعلم قابلة للقياس، لا مجرد مولد محتوى.

## تطبيق التحديث عبر CMD

```cmd
set "PROJECT=C:\Users\djenb\Downloads\Qantum study\qai_platform_"
set "PATCHZIP=%USERPROFILE%\Downloads\3alimnIA_V6.18.5_PREMIUM_LESSON_WORKSPACE_PATCH.zip"
set "PATCHDIR=%TEMP%\3alimnIA_V6185_PATCH"

cd /d "%PROJECT%"
git status
git switch main
git pull origin main
git switch -c feat/v6-18-5-premium-lesson-workspace

if exist "%PATCHDIR%" rmdir /s /q "%PATCHDIR%"
mkdir "%PATCHDIR%"
tar -xf "%PATCHZIP%" -C "%PATCHDIR%"
xcopy "%PATCHDIR%\*" "%PROJECT%\" /E /I /Y /H

cd /d "%PROJECT%"
```

ثم شغّل الاختبارات المذكورة أعلاه.

## رفع التحديث إلى GitHub

```cmd
git add pedagogical_orchestrator.py lesson_content_renderer.py
git add lesson_block_generation_engine.py teacher_studio.py db.py
git add .streamlit\v6_theme.css
git add validate_v6185_premium_lesson_workspace.py
git add validate_v6184_simple_teacher_journey.py
git add validate_v6182_blueprint_editor_runtime_ui.py
git add validate_v618_global_design_system.py
git add validate_v616_lesson_block_generation.py
git add validate_v615_blueprint_editor_versioning.py
git add validate_v6171_unified_guided_production_journey.py
git add validate_v6172_simplified_guided_research_flow.py
git add validate_v6101_ai_tutor_state.py
git add validate_v693_save_prompt_hotfix.py validate_v694_premium_logo_prompt_state.py
git add V6_18_5_PREMIUM_LESSON_WORKSPACE_PEDAGOGICAL_ORCHESTRATOR_AR.md
git add README.md CHANGELOG.md

git status
git diff --cached --stat
git commit -m "feat: add V6.18.5 premium lesson workspace and pedagogical orchestration"
git push -u origin feat/v6-18-5-premium-lesson-workspace
```

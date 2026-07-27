# V6.7.3 — Bidirectional Hero Text Gutters

- Added a clear left gutter for English and French homepage hero text.
- Added the matching right gutter for Arabic RTL hero text.
- Preserved desktop, tablet, and mobile responsive behavior.
- Updated the application version to `v6.7.3-bidirectional-hero-gutters`.

# V6.7.2 — Classic White Header Logo

- Restored the previous white rounded logo design in the right side of the Arabic public header.
- Added a dedicated flattened white logo asset to prevent stale dark versions from browser cache.
- Preserved the full official wordmark and responsive placement in Arabic, French, and English.
- Updated the instrumented application version to `v6.7.2-white-header-logo`.

# V6.7 — Home Brand Hero & Student Tools

- Replaced the homepage's generated CSS illustration with the approved large 3alimnIA brand panel.
- Added a persistent learner tool dock with native buttons for dashboard, modules/Qiskit, AI Coach, and adaptive plan.
- Added a compact assessment/research section with visible locked destinations and localized guidance.
- Preserved the native Streamlit router and learner permission rules.
- Updated the instrumented application version to `v6.7-home-hero-student-tools`.

# V6.6 — Student Learning Workspace

- Rebuilt the learner module page into a two-column lesson-and-coach workspace.
- Added a compact stage header and collapsible module map to reduce vertical page length.
- Added four learner-facing stages: understand, visual experiment, Qiskit bridge, and understanding check.
- Added a compact AI coach that requires a learner attempt before support.
- Added responsive mobile stacking, RTL-aware layout, dark-mode surfaces, and clearer completion controls.
- Updated the instrumented application version to `v6.6-student-learning-workspace`.

# V6.2 — Evaluator Intelligence Dashboard

- Rebuilt the evaluator home with Streamlit-native metrics and tabs.
- Added real-data Plotly charts for pre/post outcomes, daily AI activity, progress distribution, coach modes, and LPQS dimensions.
- Added a progress-enabled learner table using `st.column_config`.
- Added direct anonymized CSV and Excel research exports.
- Added Plotly 6 dependency and a coordinated chart palette.
- Updated the application version to `v6.2-evaluator-intelligence-dashboard`.

# V6.0.1 - Production header and compact hero

- Replaced the visible native navigation dropdown with a professional Streamlit-native public header.
- Kept native page registration in hidden mode for reliable routing.
- Rendered the official logo through `st.image` to prevent broken Cloud images.
- Removed fragile logo data URIs from the hero and footer.
- Reduced hero height, Arabic title scale, top spacing, and first-screen overflow.
- Added direct public navigation to programs, AI Studio, institutions, learner access, and evaluator access.
- Updated the instrumented app version without changing the database schema.

# V5.0.1 - Branding startup hotfix

- Fixed the startup `AttributeError` caused by an obsolete `branding.BRAND_NAME_LATIN` reference.
- Added a backward-compatible brand-name alias.
- Made toolbar fallback resolution safe even when the user role is not set.
- Added a static validation that checks all `branding.*` references against exported symbols.

## V4.8 - Native Docked Navigation

- Replaced the page-column navigation shell with Streamlit's native sidebar.
- Docked the rail by language direction: right for Arabic, left for French/English.
- Added a dedicated viewport-height scroll area for navigation.
- Decoupled navigation height from document height and removed main-page scroll dependency.
- Added responsive drawer behaviour below 900px.
- Updated the instrumented app version to `v4.8-native-docked-navigation`.

## V4.7.1 - Study Protocol Hotfix

- Fixed the evaluator Study Protocol crash caused by outdated PRE_TEST_QUESTIONS and POST_TEST_QUESTIONS attribute names.
- Added backward-compatible assessment collection lookup.
- Localized the full Study Protocol page in Arabic, French, and English.
- Preserved database, assessment content, research exports, and stable Excel sheet names.


## V4.7 - Sticky Compact Navigation

- Applied the same compact sticky navigation shell across learner and evaluator workspaces.
- Added independent sidebar scrolling for laptop screens.
- Reorganized navigation into accessible collapsible groups that keep the active group open.
- Reduced evaluator page-header height and excess vertical whitespace.
- Added responsive fallback to normal page flow on tablet and mobile devices.
- Preserved all multilingual, research, LPQS, database, and export behavior.

# Changelog

## V4.0 - Premium UI & Typography Refresh
- Rebuilt the public landing page with the approved official logo rendered reliably through Streamlit.
- Added Alexandria/Tajawal typography for Arabic and Inter for French/English.
- Added premium RTL/LTR-aware visual hierarchy, responsive layout, cards, forms, tabs, metrics, and evaluator surfaces.
- Added `.streamlit/v4_theme.css`, Streamlit theme configuration, and `.gitattributes`.
- Added `validate_v4_ui.py` and multilingual static previews.
- Preserved all learning, research, database, AI, LPQS, and export behavior.

## V3.1 - Streamlit Cloud display fix

- Fixed raw HTML appearing inside the landing hero.
- Replaced the fragile embedded PNG logo with a self-contained inline SVG lockup.
- Removed the duplicate landing-page language selector.
- Replaced the narrow horizontal radio control with a sidebar-friendly language selectbox.

# سجل تعديلات 3alimnIA

## V3 - التدويل الكامل للمنصة

### اختيار اللغة

- إضافة اختيار عالمي للعربية والفرنسية والإنجليزية.
- تطبيق الاختيار على الصفحة العامة، حساب المتعلم، جميع صفحات الدراسة، والتقييم البحثي.
- إعادة تحميل الواجهة فور تغيير اللغة لتطبيق RTL/LTR بصورة صحيحة.
- حفظ `preferred_language` داخل حساب المتعلم واستعادتها عند تسجيل الدخول.

### المحتوى والتعلمات

- ترجمة الوحدات الست كاملة: الأهداف، المفاهيم، الشرح، الأهمية، الفكرة الكبرى، خطوات التصور، جسر Qiskit، سوء الفهم، المهمة، التحقق، التأمل، ومعايير الإنجاز.
- ترجمة المخططات النصية وتسلسل Observe/Model/Code/Interpret.
- ترجمة الوسائط التعليمية وتعليمات المحاكيات.
- ترجمة 36 سؤال تقييم مع الخيارات والتغذية الراجعة.
- ترجمة الاستبيان والأسئلة المفتوحة.

### الذكاء التوليدي

- مزامنة اللغة المختارة مع AI Coach وAI Tutor والخطة التكيفية.
- إضافة الفرنسية إلى Concept Builder.
- تحسين كشف لغة سؤال المتعلم ليشمل الفرنسية.
- توطين بطاقات Concept Builder والرسائل البريدية لإعادة تعيين كلمة المرور.

### سلامة البحث

- الإبقاء على مفاتيح المفاهيم والوحدات والأسئلة بالإنجليزية داخليًا.
- عدم تغيير بنية السجلات البحثية الحالية.
- إضافة ترحيل تلقائي لحقل `preferred_language` للحسابات الموجودة.

### التحقق

- اجتازت جميع ملفات Python فحص `py_compile`.
- اجتاز فحص المحتوى: 6 وحدات و18 سؤالًا قبليًا و18 سؤالًا بعديًا لكل لغة.
- اجتاز اختبار SQLite لإنشاء الحساب وحفظ اللغة وتغييرها واستعادتها عند المصادقة.

## V3.2 - Official logo restoration
- Restored the approved blue/cyan/gold horizontal 3alimnIA logo.
- Embedded the logo as a base64 data URI to prevent broken paths on Streamlit Cloud.
- Removed the replacement SVG wordmark from the visible interface.
- Added responsive sizing for hero and sidebar use.

## V4.3 - Learning Experience & Navigation
- Grouped learner navigation and adaptive-plan access.
- Premium learner dashboard and progress topbar.
- Assessment cards with question progress.
- Unified lesson selector cards.
- Localized AI Coach quick-start actions.

## V4.5 - Evaluator & Research Dashboard
- Rebuilt the evaluator sidebar into grouped research navigation with system-status visibility.
- Added a multilingual global analysis filter for study group, academic level, learner language, and completion status.
- Added six evaluator KPI cards: learners, complete cases, paired tests, mean gain, AI interactions, and mean LPQS.
- Added tabbed dashboard views for completion workflow, learning outcomes, AI usage, LPQS quality, and system readiness.
- Redesigned learner/account management, participant details, AI logs, response inspection, and LPQS evaluation.
- Added a safer two-track export interface for anonymized research data and full administrative backup.
- Exposed `preferred_language` in evaluator data while preserving the database schema and existing records.
- Added responsive evaluator styling and `validate_v45_evaluator.py`.


## V4.6 - Evaluator localization
- Fixed mixed Arabic/English evaluator headings and learner-detail metrics.
- Added RTL-safe typography for evaluator heroes, metrics, and export cards.

## V4.10 - Compact top alignment and active analysis tabs
- Removed the residual top reserve above the landing and operational pages across Streamlit DOM variants.
- Added a clear segmented-control treatment for horizontal tabs.
- The selected evaluator analysis category now uses a blue-cyan gradient with white text.
- Preserved responsive horizontal scrolling for tabs on narrow screens.

## V4.11 - Escape navigation
- Added an always-visible in-app navigation bar independent of the Streamlit sidebar.
- Added page switcher, Back, Home, Change account, Sidebar open, and Exit actions.
- Prevented users from becoming trapped when the native sidebar is collapsed.
- Added responsive RTL/LTR styling for the safety navigation bar.

## V5 - Native top navigation and reliable account controls

- Replaced custom sidebar routing and the V4.11 escape strip with `st.Page` and `st.navigation(position="top")`.
- Added dynamic role- and permission-aware page registration.
- Added a compact global account toolbar with native callbacks for Home, Change account, Switch workspace, and Sign out.
- Routed internal learning actions through `st.switch_page` via a queued router, preventing stale page state after reruns.
- Restored the Streamlit header required by native top navigation.
- Removed dependence on DOM-click JavaScript for opening navigation.
- Added multilingual navigation sections and active-page styling.
- Updated the application version to `v5-native-top-navigation`.

## V6 — Global AI Academy

- Rebuilt the public experience after benchmarking Edraak, Brilliant, IBM Quantum Learning, and DataCamp.
- Added public Programs, Generative AI Studio, and Universities & Research pages.
- Added modern program cards with level, duration, module count, and availability.
- Added a four-step generative learning engine explanation.
- Added a dedicated institutional/research value proposition.
- Added `ui_v6.py` and `.streamlit/v6_theme.css`.
- Preserved the existing learner, evaluator, database, LPQS, and research workflows.

## V6.3 — Responsive Typography & Vertical Mobile Layout

- Extended Tajawal/Alexandria typography to native Streamlit controls while preserving Material Symbols icons.
- Added tablet wrapping for dense column groups.
- Converted all Streamlit horizontal column groups to full-width vertical stacks on phones.
- Converted mobile tabs into vertical, finger-friendly selectors.
- Improved mobile hero, navigation, cards, metrics, forms, buttons, and research tables.
- Added touch-safe cards and disabled hover-only movement on touch devices.
- Preserved the desktop academy layout and all existing learning, evaluator, AI, LPQS, and export logic.


## V6.4 — AI Studio Banner & Responsive Evidence Grid

- Replaced the generic AI Studio page hero with a premium multilingual generative-learning banner.
- Added localized AI Studio badges, capability tags, and a compact orbital visual.
- Rebuilt platform evidence statistics as a CSS auto-fit grid shared by the home and AI Studio pages.
- Added responsive 4/2/1-column behavior, touch-safe card interactions, and mobile typography.
- Preserved learner, evaluator, AI, LPQS, database, and research-export logic.

## V6.5.1 — Prominent Brand Panel
- Enlarged and centered the 3alimnIA wordmark inside the main generative-learning visual.
- Added a localized subtitle in Arabic, French, and English.
- Rebalanced the AI core, orbits, and Qiskit card to preserve visual hierarchy.
- Added responsive sizing for tablet and mobile screens.

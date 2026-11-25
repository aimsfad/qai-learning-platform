# تحديث استرجاع كلمة المرور عبر البريد

أضيفت خاصية **Forgot password?** في صفحة دخول الطالب.

## كيف تعمل؟
1. الطالب يضغط على Forgot password.
2. يكتب البريد الإلكتروني الذي استعمله عند التسجيل.
3. النظام ينشئ رابط reset آمن صالح لمدة 30 دقيقة ويُستخدم مرة واحدة فقط.
4. الرابط يُرسل إلى البريد الإلكتروني عبر SMTP.
5. الطالب يفتح الرابط ويضع كلمة مرور جديدة.

## إعدادات Streamlit Cloud Secrets المطلوبة
أضيفي هذه القيم في Streamlit Cloud > App > Settings > Secrets:

```toml
APP_BASE_URL = "https://appi-learning-platform-lg4v2bh9fsxq8npnd944et.streamlit.app"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = "587"
SMTP_USERNAME = "your_email@example.com"
SMTP_PASSWORD = "your_app_password_here"
SMTP_FROM = "your_email@example.com"
SMTP_USE_SSL = "false"
SHOW_RESET_LINK_FOR_DEBUG = "false"
```

إذا استعملت Gmail يجب استعمال **App Password** وليس كلمة مرور البريد العادية.

## تنبيه أمني
لا ترفعي ملف `.streamlit/secrets.toml` الحقيقي إلى GitHub. ضعي القيم الحقيقية فقط في Streamlit Cloud Secrets.

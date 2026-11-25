"""Student Home Page Adapter (V7.0 Modular Routing)."""
def render_page():
    import main_app
    return getattr(main_app, "render_student_home", None)

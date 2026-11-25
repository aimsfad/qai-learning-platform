"""Evaluator Dashboard Adapter (V7.2 Modular Routing)."""
def render_page():
    import main_app
    return getattr(main_app, "render_evaluator_app", None)

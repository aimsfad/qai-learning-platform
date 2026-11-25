"""Verification suite for 3alimnIA V7.2 Liquid Glass UI & XSS-Safe Layer."""

from __future__ import annotations

from pathlib import Path
import safe_html

ROOT = Path(__file__).resolve().parent


def main() -> None:
    css = (ROOT / ".streamlit" / "app.css").read_text(encoding="utf-8")
    assert "backdrop-filter" in css and "LIQUID GLASS" in css.upper()
    assert "Material Symbols Rounded" in css
    assert "@media (max-width: 1024px)" in css
    assert "@media (max-width: 768px)" in css
    assert "@media (max-width: 480px)" in css
    assert "prefers-color-scheme: dark" in css
    assert "safe-area-inset-bottom" in css

    assert "&lt;script&gt;" in safe_html.esc("<script>alert(1)</script>")
    assert safe_html.safe_url("javascript:alert(1)") == "#"
    assert safe_html.safe_url("https://example.org/course") == "https://example.org/course"
    assert "lg-hero" in safe_html.glass_hero("3alimnIA", "Liquid Glass", badges=["V7.2"])
    assert "lg-mobile-dock" in safe_html.glass_mobile_dock([{"label": "Home", "href": "/", "active": True}])
    assert "<svg" in safe_html.glass_progress_ring(88, "Mastery")

    app_src = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "v7_enterprise_hub" not in app_src and "v7_engines" not in app_src
    assert not (ROOT / "v7_engines").exists()
    assert not (ROOT / "v7_enterprise_hub.py").exists()

    print("PASS validate_v7_enterprise.py — Liquid Glass V7.2 UI, responsiveness & XSS layer verified (10 extra features removed).")


if __name__ == "__main__":
    main()

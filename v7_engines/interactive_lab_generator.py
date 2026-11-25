"""Feature 2: Sandboxed AI Interactive Lab & Simulator Generator."""

from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class LabSpec:
    lab_id: str
    title: str
    domain: str
    parameter_name: str
    min_value: float
    max_value: float
    default_value: float
    formula_label: str
    locale: str = "ar"


class InteractiveLabGenerator:
    """Generates CSP-sandboxed, zero-network interactive HTML labs for any subject."""

    def build_sandboxed_html(self, spec: LabSpec) -> str:
        dir_attr = "rtl" if spec.locale.startswith("ar") else "ltr"
        title = html.escape(spec.title)
        domain = html.escape(spec.domain)
        param = html.escape(spec.parameter_name)
        formula = html.escape(spec.formula_label)
        return f"""<!DOCTYPE html>
<html lang="{html.escape(spec.locale)}" dir="{dir_attr}">
<head>
<meta charset="UTF-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline';">
<title>{title}</title>
<style>
body{{margin:0;padding:20px;font-family:system-ui,sans-serif;background:#F1F5F9;color:#0F172A;}}
.box{{background:rgba(255,255,255,0.86);border:1px solid #CBD5E1;border-radius:18px;padding:20px;max-width:640px;margin:auto;}}
.val{{font-size:28px;font-weight:800;color:#1D4ED8;margin:10px 0;}}
input[type=range]{{width:100%;}}
</style>
</head>
<body>
<div class="box">
  <small>{domain}</small>
  <h2>{title}</h2>
  <label for="p">{param}: <strong id="pv">{spec.default_value}</strong></label>
  <input id="p" type="range" min="{spec.min_value}" max="{spec.max_value}" step="0.1" value="{spec.default_value}" oninput="upd(this.value)">
  <div class="val" id="out">{formula}</div>
</div>
<script>
function upd(v){{document.getElementById('pv').textContent=v;const x=parseFloat(v);document.getElementById('out').textContent='f('+x.toFixed(1)+') = '+(x*x).toFixed(2);}}
upd({spec.default_value});
</script>
</body>
</html>"""

"""Static and isolated behavioral validation for V6.10."""

from __future__ import annotations

import importlib
import py_compile
import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def require(path: str, markers: list[str]) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    for marker in markers:
        if marker not in text:
            raise AssertionError(f"Missing marker in {path}: {marker}")


def install_streamlit_stub(secrets: dict[str, str]) -> types.ModuleType:
    module = types.ModuleType("streamlit")
    module.secrets = secrets
    sys.modules["streamlit"] = module
    return module


def main() -> None:
    for path in ROOT.glob("*.py"):
        py_compile.compile(str(path), doraise=True)

    require(
        "model_router.py",
        [
            "class ProviderSelection",
            "def generation_candidates",
            "openai/gpt-oss-120b",
            "gemini-3.6-flash",
            "OPENROUTER_API_KEY",
            "COHERE_API_KEY",
            "CLOUDFLARE_API_TOKEN",
        ],
    )
    require(
        "gemini_file_analyzer.py",
        [
            "inlineData",
            "mimeType",
            "def extract_uploaded_sources",
            "multimodal-analysis",
            "local-pdf",
        ],
    )
    require(
        "teacher_studio.py",
        [
            "import gemini_file_analyzer",
            'type=["pdf", "docx", "txt", "md", "csv", "json", "png"',
            "Gemini multimodal analysis is ready",
            "source_analysis_context",
        ],
    )
    require(
        "content_generation_engine.py",
        [
            "model_router.generation_candidates",
            "Fallback used after earlier provider failure",
            "x-goog-api-key",
            "openrouter",
        ],
    )

    secrets = {
        "LLM_PROVIDER": "groq",
        "CONTENT_LLM_PROVIDER": "groq",
        "FILE_ANALYSIS_PROVIDER": "gemini",
        "GROQ_API_KEY": "test-groq",
        "GROQ_MODEL": "llama-3.1-8b-instant",
        "GEMINI_API_KEY": "test-gemini",
        "GEMINI_MODEL": "gemini-2.0-flash",
        "ENABLE_MODEL_FALLBACK": "true",
    }
    install_streamlit_stub(secrets)
    sys.path.insert(0, str(ROOT))

    for name in ("model_router", "content_generation_engine", "gemini_file_analyzer"):
        sys.modules.pop(name, None)

    model_router = importlib.import_module("model_router")
    content_engine = importlib.import_module("content_generation_engine")
    analyzer = importlib.import_module("gemini_file_analyzer")

    tutor_primary = model_router.generation_candidates("tutor")[0]
    assert tutor_primary.model == "openai/gpt-oss-20b"
    file_primary = model_router.generation_candidates("file_analysis")[0]
    assert file_primary.model == "gemini-3.6-flash"
    assert file_primary.available is True

    class FakeResponse:
        def __init__(self, status_code: int, data: dict, text: str = ""):
            self.status_code = status_code
            self._data = data
            self.text = text or str(data)

        def json(self):
            return self._data

    def fake_post(url, **kwargs):
        if "groq.com" in url:
            return FakeResponse(500, {"error": "simulated Groq outage"})
        if "generativelanguage.googleapis.com" in url:
            return FakeResponse(
                200,
                {"candidates": [{"content": {"parts": [{"text": "Gemini fallback result"}]}}]},
            )
        raise AssertionError(f"Unexpected URL: {url}")

    content_engine.requests.post = fake_post
    result = content_engine.generate_content("Create a lesson", "English", max_tokens=200)
    assert result.status == "completed"
    assert result.provider == "gemini"
    assert result.response == "Gemini fallback result"
    assert "Fallback used" in result.diagnostic

    analyzer.requests.post = fake_post

    class FakeUpload:
        name = "diagram.png"
        type = "image/png"

        @staticmethod
        def getvalue():
            return b"fake-image-bytes"

    extracted = analyzer.extract_uploaded_sources(
        [FakeUpload()],
        project_context={"domain": "Physics", "target_concept": "Waves"},
        language="English",
    )
    assert "Uploaded source: diagram.png" in extracted
    assert "provider=gemini" in extracted
    assert "Gemini fallback result" in extracted

    print("V6.10 Gemini file analyzer and model router validation passed.")


if __name__ == "__main__":
    main()

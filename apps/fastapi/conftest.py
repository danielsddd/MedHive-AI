"""
Root pytest bootstrap for the backend. Puts apps/fastapi on sys.path so tests can import
core/services/routers directly. The app is live-only (no offline/dev mode switches), so
tests rely on CI-injected placeholder credentials (see .github/workflows/ci.yml) to satisfy
Settings()'s required fields, and use mocks/monkeypatch for any test that would otherwise
make a real network call to Gemini, Groq, or Supabase.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
"""
Root pytest bootstrap for the backend. Puts apps/fastapi on sys.path so tests can import
core/services/routers directly, and forces offline modes by default so the suite never
touches a real provider, model download, or database. VCR.py is used for any live-shaped
LLM call recorded later.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

os.environ.setdefault("LLM_MODE", "offline")
os.environ.setdefault("EMBEDDING_MODE", "offline")
os.environ.setdefault("AUTH_MODE", "dev")

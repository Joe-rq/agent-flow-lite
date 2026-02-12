"""
Canonical path constants for backend data directories.

This module is the single source of truth for all data directory paths.
All modules that need to access skills, sessions, or other data directories
should import from here instead of constructing paths inline.
"""
from pathlib import Path

# Backend root directory (backend/)
BACKEND_ROOT = Path(__file__).resolve().parents[2]

# Data directory (backend/data/)
BACKEND_DATA_DIR = BACKEND_ROOT / "data"

# Skills directory (backend/data/skills/)
SKILLS_DIR = BACKEND_DATA_DIR / "skills"

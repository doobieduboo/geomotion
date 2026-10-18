"""Shared production preset for executable tools."""

import json
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULTS = json.loads((SKILL_ROOT / "defaults.json").read_text())

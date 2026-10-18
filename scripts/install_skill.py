"""Install into the current user's Codex skill directory on THIS machine only."""

import argparse
import shutil
from datetime import datetime
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument(
    "--destination", type=Path, default=Path.home() / ".agents" / "skills" / "geomotion"
)
p.add_argument(
    "--replace",
    action="store_true",
    help="Replace an existing install after backing it up",
)
a = p.parse_args()
source = Path(__file__).resolve().parents[1] / ".agents" / "skills" / "geomotion"
dest = a.destination.expanduser().resolve()
if dest == source or source in dest.parents or dest in source.parents:
    p.error("Install destination must be separate from the repository source")
if dest.exists():
    if not a.replace:
        p.error("Destination exists; inspect it first, then use --replace if desired")
    backup = (
        dest.parent.parent
        / "skill-backups"
        / f"{dest.name}-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}"
    )
    backup.parent.mkdir(parents=True, exist_ok=True)
    dest.rename(backup)
shutil.copytree(
    source,
    dest,
    ignore=shutil.ignore_patterns("cache", "outputs", "assets", "__pycache__", "*.pyc"),
)
print("Installed:", dest)
print(
    "Read the updated SKILL.md in this session. Other environments need their own installation."
)

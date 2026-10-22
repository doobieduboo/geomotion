"""Prepare Site files off-site and promote a reviewed media manifest last.

The existing media.json remains the active publication until every staged
variant has passed QA. Newly moved, unreferenced assets are harmless if an
I/O failure interrupts promotion before the final manifest replacement.
"""

from pathlib import Path
import shutil

from project_state import atomic_json, digest


def _stage_file(stage, relative):
    """Resolve only existing regular files inside the staging directory."""
    if not isinstance(relative, str) or not relative:
        raise ValueError("Staged asset path must be a nonempty string")
    name = Path(relative)
    if name.is_absolute() or ".." in name.parts:
        raise ValueError("Unsafe staged asset path: " + relative)
    stage = Path(stage).resolve()
    source = (stage / name).resolve()
    if not source.is_relative_to(stage) or not source.is_file():
        raise ValueError("Missing or unsafe staged asset: " + relative)
    return source, name


def seed_existing_player(destination, stage):
    """Preserve the Site's customized player instead of the bundled template."""
    destination, stage = Path(destination), Path(stage)
    stage.mkdir(parents=True, exist_ok=True)
    for name in ("index.html", "app.js"):
        source = destination / name
        if source.is_file():
            shutil.copy2(source, stage / name)


def version_credits(stage, media):
    """Avoid overwriting credits referenced by the previously active manifest."""
    if not media.get("credits"):
        return media
    source, _ = _stage_file(stage, media["credits"])
    filename = "credits-" + digest(source)[:12] + source.suffix
    source.replace(Path(stage) / filename)
    updated = {**media, "credits": filename}
    atomic_json(Path(stage) / "media.json", updated)
    return updated


def promote_staged_delivery(stage, destination, media):
    """Move verified assets first, then atomically switch the active media.json.

    Only the generated media and referenced credits are promoted. Old assets,
    unrelated Site files and customized player files are kept untouched.
    """
    stage, destination = Path(stage), Path(destination)
    names = [variant["src"] for variant in media["variants"]]
    names.append(media["poster"])
    if media.get("credits"):
        names.append(media["credits"])
    if len(set(names)) != len(names):
        raise ValueError("Duplicate staged asset path")
    assets = [_stage_file(stage, name) for name in names]
    manifest, _ = _stage_file(stage, "media.json")
    player = {}
    for name in ("index.html", "app.js"):
        if not (destination / name).exists():
            player[name] = _stage_file(stage, name)[0]

    destination.mkdir(parents=True, exist_ok=True)
    for source, relative in assets:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        source.replace(target)
    for name, source in player.items():
        if not (destination / name).exists():
            source.replace(destination / name)
    # Commit point: until now, the old manifest still references the old media.
    manifest.replace(destination / "media.json")

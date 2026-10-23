"""Content provenance and explicit approval locks; no implied factual/legal clearance."""

import copy
import hashlib
import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse
from datetime import date
from config import DEFAULTS, SKILL_ROOT


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(path)


def archive_manifest(path):
    path = Path(path)
    data = json.loads(path.read_text())
    if data.get("version") != 1:
        raise ValueError("Archive manifest version must be 1")
    records, warnings = {}, []
    for item in data.get("archives", []):
        for key in (
            "id",
            "file",
            "source_url",
            "credit",
            "context",
            "fact_status",
            "reuse_status",
        ):
            if not item.get(key):
                raise ValueError("Archive requires " + key)
        if item["id"] in records:
            raise ValueError("Duplicate archive id: " + item["id"])
        if urlparse(item["source_url"]).scheme not in ("https", "http"):
            raise ValueError("Archive source must be an HTTP(S) URL")
        if item["fact_status"] not in ("verified", "unverified", "rejected"):
            raise ValueError("Invalid archive fact_status")
        if item["reuse_status"] not in (
            "licensed",
            "public_domain",
            "editorial_assessment",
            "unknown",
            "restricted",
        ):
            raise ValueError("Invalid archive reuse_status")
        if not any(item.get(k) for k in ("capture_date", "publication_date", "document_date")):
            raise ValueError(
                "Record a known capture, publication or document date, with date_basis"
            )
        for key in ("capture_date", "publication_date", "document_date"):
            if item.get(key):
                value = item[key]
                # Preserve catalog precision and closed ISO intervals.
                parts = value.split("/")
                if len(parts) > 2:
                    raise ValueError("Invalid archive date interval")
                checked = []
                for part in parts:
                    if re.fullmatch(r"\d{4}", part):
                        checked.append(date(int(part), 1, 1))
                    elif re.fullmatch(r"\d{4}-\d{2}", part):
                        checked.append(date.fromisoformat(part + "-01"))
                    else:
                        checked.append(date.fromisoformat(part))
                if len(checked) == 2 and checked[0] > checked[1]:
                    raise ValueError("Archive date interval is reversed")
        if not item.get("date_basis"):
            raise ValueError("Archive requires date_basis")
        asset = (path.parent / item["file"]).resolve()
        actual = digest(asset)
        if item.get("sha256") and item["sha256"] != actual:
            raise ValueError("Archive bytes changed: " + item["id"])
        item = {**item, "file": str(asset), "sha256": actual}
        if item["reuse_status"] in ("unknown", "restricted"):
            warnings.append(
                f"{item['id']}: reuse {item['reuse_status']}; record assessment, do not silently delete"
            )
        records[item["id"]] = item
    return records, warnings


def load_project(path):
    path = Path(path).resolve()
    scene = json.loads(path.read_text())
    warnings = []
    supported = {
        "duration",
        "camera",
        "basemap",
        "world_overlays",
        "export",
        "regions",
        "routes",
        "markers",
        "callouts",
        "titles",
        "audio",
        "attribution",
        "timeline",
        "subtitles",
        "subtitle_cues",
        "archive_manifest",
        "inputs",
        "metadata",
        "composition",
        "focuses",
        "cta",
    }
    unknown = set(scene) - supported
    if unknown:
        raise ValueError(
            "Unsupported generic scene fields; use the existing project renderer or an explicit adapter: "
            + ", ".join(sorted(unknown))
        )
    if scene.get("archive_manifest"):
        records, warnings = archive_manifest(path.parent / scene["archive_manifest"])
        for callout in scene.get("callouts", []):
            if "archive_id" not in callout:
                continue
            record = records[callout["archive_id"]]
            if record["fact_status"] != "verified":
                raise ValueError(
                    "Active archive factual review required: " + record["id"]
                )
            if callout.get("image") and (
                path.parent / callout["image"]
            ).resolve() != Path(record["file"]):
                raise ValueError("archive_id and image disagree")
            callout["image"] = record["file"]
    elif any("archive_id" in c for c in scene.get("callouts", [])):
        raise ValueError("archive_id requires archive_manifest")
    return scene, warnings


def snapshot(path):
    """Hash registered inputs plus renderer dependencies; ignore execution-only settings."""
    path = Path(path).resolve()
    scene = json.loads(path.read_text())
    root = path.parent
    domains = {
        k: {}
        for k in (
            "narration",
            "voice",
            "audio",
            "subtitles",
            "archives",
            "data",
            "visuals",
            "configuration",
        )
    }
    for domain, files in scene.get("inputs", {}).items():
        if domain not in domains:
            raise ValueError("Unknown input domain: " + domain)
        if not isinstance(files, list) or not all(
            isinstance(name, str) for name in files
        ):
            raise ValueError("Input domains require a list of local paths")
        for name in files:
            domains[domain][name] = digest(root / name)
    for field, domain in (
        ("audio", "audio"),
        ("subtitle_cues", "subtitles"),
        ("archive_manifest", "archives"),
    ):
        if scene.get(field):
            domains[domain][scene[field]] = digest(root / scene[field])
    if scene.get("archive_manifest"):
        records, _ = archive_manifest(root / scene["archive_manifest"])
        domains["archives"]["records"] = records
    for group in (
        "camera",
        "regions",
        "world_overlays",
        "routes",
        "markers",
        "callouts",
        "titles",
        "subtitles",
    ):
        for i, item in enumerate(scene.get(group, [])):
            for key in (
                "image",
                "flag",
                "geojson",
                "atlas",
                "atlas_metadata",
                "definition",
            ):
                if item.get(key):
                    file = (
                        SKILL_ROOT / item[key]
                        if item[key].startswith("library/")
                        else root / item[key]
                    )
                    domain = (
                        "data"
                        if key == "geojson"
                        else "archives" if key == "image" else "visuals"
                    )
                    domains[domain][f"{group}.{i}.{key}:{item[key]}"] = digest(file)
    domains["archives"]["active_callouts"] = [
        {
            "index": i,
            **{
                key: item[key]
                for key in ("archive_id", "image", "image_crop", "title", "lines")
                if key in item
            },
        }
        for i, item in enumerate(scene.get("callouts", []))
        if item.get("archive_id") or item.get("image")
    ]
    domains["data"]["region_selection"] = [
        {"geojson": item["geojson"], "match": item.get("match", {})}
        for item in scene.get("regions", [])
    ]
    domains["subtitles"]["inline"] = scene.get("subtitles", [])
    domains["subtitles"]["timeline"] = scene.get("timeline", {})
    domains["audio"]["file"] = scene.get("audio")
    domains["configuration"]["preset"] = DEFAULTS
    domains["configuration"]["export"] = scene.get("export", {})
    for font in (SKILL_ROOT / "fonts").glob("*.ttf"):
        domains["configuration"][font.name] = digest(font)
    for script in (SKILL_ROOT / "scripts").glob("*.py"):
        domains["configuration"][script.name] = digest(script)
    for env in ("GEOMOTION_FONT_BOLD", "GEOMOTION_FONT_REGULAR"):
        if os.environ.get(env):
            domains["configuration"][env] = digest(os.environ[env])
    visuals = copy.deepcopy(scene)
    for key in (
        "inputs",
        "audio",
        "subtitles",
        "timeline",
        "archive_manifest",
        "export",
    ):
        visuals.pop(key, None)
    domains["visuals"]["scene"] = visuals
    return domains


def differences(before, after):
    def walk(a, b, path=""):
        if isinstance(a, dict) and isinstance(b, dict):
            changes = []
            for key in sorted(set(a) | set(b)):
                target = path + "/" + str(key)
                if key not in a:
                    changes.append({"path": target, "change": "added", "after": b[key]})
                elif key not in b:
                    changes.append(
                        {"path": target, "change": "removed", "before": a[key]}
                    )
                else:
                    changes.extend(walk(a[key], b[key], target))
            return changes
        return (
            []
            if a == b
            else [{"path": path, "change": "changed", "before": a, "after": b}]
        )

    return [
        {"domain": domain, "changes": walk(before.get(domain), after.get(domain))}
        for domain in sorted(set(before) | set(after))
        if before.get(domain) != after.get(domain)
    ]


def check_lock(lock, current, scopes):
    changes = differences(lock["inputs"], current)
    denied = [c["domain"] for c in changes if c["domain"] not in scopes]
    if denied:
        details = [
            c["domain"] + change["path"]
            for c in changes
            if c["domain"] in denied
            for change in c["changes"]
        ]
        raise ValueError(
            "Changes outside declared revision scope: " + ", ".join(details)
        )
    return changes


def fingerprint(state, mode):
    return hashlib.sha256(
        json.dumps({"inputs": state, "mode": mode}, sort_keys=True).encode()
    ).hexdigest()

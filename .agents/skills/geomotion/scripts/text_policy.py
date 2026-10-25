"""One display policy shared by loading, layout, rendering and revision keys.

Provenance stays in authored scene/manifests. Display settings never grant rights
or turn a context photograph or reconstruction into evidence of an event.
"""
import copy
from config import DEFAULTS
from basemap import ATTRIBUTION

FIELDS = ("source_credits", "media_captions", "extra_annotations")


def settings(scene):
    overrides = scene.get("text_policy", {})
    if not isinstance(overrides, dict) or set(overrides) - set(FIELDS):
        raise ValueError("text_policy accepts source_credits, media_captions, extra_annotations")
    if any(type(value) is not bool for value in overrides.values()):
        raise ValueError("text_policy overrides must be booleans")
    return {key: overrides.get(key, DEFAULTS["composition"]["text_policy"][key]) for key in FIELDS}


def visual_attribution(scene):
    if not settings(scene)["source_credits"]:
        return ""
    authored = scene.get("attribution", "")
    return authored if ATTRIBUTION in authored else " · ".join(filter(None, (authored, ATTRIBUTION)))


def apply(scene):
    """Resolve an effective scene without changing saved authoring/source records."""
    result = copy.deepcopy(scene)
    policy = settings(scene)
    result["text_policy"] = policy
    result["attribution"] = visual_attribution(scene)
    callouts = []
    for item in result.get("callouts", []):
        if item.get("image") or item.get("archive_id"):
            if not policy["media_captions"]:
                item.pop("title", None)
                item.pop("lines", None)
            callouts.append(item)
        elif policy["extra_annotations"]:
            callouts.append(item)
    result["callouts"] = callouts
    if not policy["extra_annotations"]:
        result.pop("cta", None)
    return result

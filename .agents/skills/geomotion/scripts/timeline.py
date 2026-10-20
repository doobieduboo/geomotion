"""One source clock for phrase events, visuals, cues and explicit silence cuts."""

import copy
import math


class Timeline:
    def __init__(self, duration, cuts=()):
        self.source_duration = float(duration)
        if not math.isfinite(self.source_duration) or self.source_duration <= 0:
            raise ValueError("Timeline duration must be positive and finite")
        self.kept = []
        cursor = 0.0
        for start, end in cuts:
            start, end = float(start), float(end)
            if (
                not all(map(math.isfinite, (start, end)))
                or not cursor <= start < end <= self.source_duration
            ):
                raise ValueError(
                    "Cuts must be ordered, nonoverlapping and inside source duration"
                )
            if start > cursor:
                self.kept.append((cursor, start))
            cursor = end
        if cursor < self.source_duration:
            self.kept.append((cursor, self.source_duration))
        self.duration = sum(b - a for a, b in self.kept)
        if self.duration <= 0:
            raise ValueError("Cuts remove the whole recording")

    def source_time(self, output):
        if not math.isfinite(output) or not 0 <= output <= self.duration + 1e-8:
            raise ValueError("Output time outside timeline")
        for start, end in self.kept:
            length = end - start
            if output < length:
                return start + output
            output -= length
        return self.kept[-1][1]

    def output_time(self, source):
        if not math.isfinite(source) or not 0 <= source <= self.source_duration:
            raise ValueError("Source time outside timeline")
        result = 0.0
        for start, end in self.kept:
            result += max(0, min(source, end) - start)
        return result

    def audio_filter(self):
        parts = [
            f"[1:a]atrim=start={a:.9f}:end={b:.9f},asetpts=PTS-STARTPTS[a{i}]"
            for i, (a, b) in enumerate(self.kept)
        ]
        labels = "".join(f"[a{i}]" for i in range(len(self.kept)))
        return ";".join(
            parts + [f"{labels}concat=n={len(self.kept)}:v=0:a=1,apad[audio]"]
        )


def resolve_scene(scene):
    """All scene keys/layers/cues use source seconds; only audio may be output-clock."""
    scene = copy.deepcopy(scene)
    spec = scene.get("timeline", {})
    timeline = Timeline(scene["duration"], spec.get("cuts", []))
    events = {}
    for item in spec.get("events", []):
        if item["id"] in events:
            raise ValueError("Duplicate event id: " + item["id"])
        start, end = item["start"], item["end"]
        if (
            not all(map(math.isfinite, (start, end)))
            or not 0 <= start < end <= timeline.source_duration
        ):
            raise ValueError("Invalid event interval: " + item["id"])
        events[item["id"]] = item
    for group in (
        "camera",
        "regions",
        "routes",
        "markers",
        "callouts",
        "titles",
        "subtitles",
    ):
        for item in scene.get(group, []):
            if "event" not in item:
                continue
            event = events.get(item["event"])
            if event is None:
                raise ValueError("Unknown event: " + item["event"])
            fields = ("time",) if group == "camera" else ("start", "end")
            if any(key in item for key in fields):
                raise ValueError("Use event reference OR absolute times, not both")
            if group == "camera":
                item["time"] = event["start"]
            else:
                item.update(start=event["start"], end=event["end"])
    if spec.get("audio_clock", "source") not in ("source", "output"):
        raise ValueError("audio_clock must be source or output")
    cues = scene.get("subtitles", [])
    last = 0
    for cue in cues:
        if (
            not cue.get("text", "").strip()
            or not last <= cue["start"] < cue["end"] <= timeline.source_duration
        ):
            raise ValueError(
                "Subtitle cues must be nonempty, ordered and nonoverlapping"
            )
        last = cue["end"]
    return scene, timeline

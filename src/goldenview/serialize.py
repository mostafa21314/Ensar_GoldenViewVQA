"""Render an associated object list as text for a language model.

Two renderings of the same list:

* **full** — every camera section, one shared id per object, explicit
  cross-references built from the view-set, and explicit negative evidence for
  empty cameras so a model can rule views out rather than invent content.
* **isolated** — one camera only, cross-references stripped and ids local to that
  camera, so the text carries no information from any other view. Required by
  System 3, whose KL scores are meaningless if a per-view pass can see elsewhere.
"""

from __future__ import annotations

from .bev import SceneObject
from .rig import CAMERAS

BAND_TEXT = {"near": "near (<10 m)", "mid": "mid (10-25 m)", "far": "far (>25 m)"}


def _side(bearing: float) -> str:
    """Plain-language azimuth. atan2 gives |bearing| > 90 for anything behind."""
    mag = abs(bearing)
    side = "left" if bearing > 0 else "right"
    if mag <= 2:
        return "straight ahead"
    if mag >= 178:
        return "directly behind"
    if mag > 90:
        return f"{180 - mag:.0f} deg behind-{side}"
    return f"{mag:.0f} deg {side}"


def _object_line(obj: SceneObject, camera: str, cross_ref: bool) -> str:
    parts = [f"  - {obj.obj_id}: {obj.class_name}", f"bearing {_side(obj.bearing)}",
             f"range {BAND_TEXT[obj.band]}"]
    line = ", ".join(parts)
    if cross_ref:
        others = [v for v in obj.views if v != camera]
        if others:
            line += f" [same object also in {', '.join(others)}]"
    return line


def full_render(objects: list[SceneObject]) -> str:
    """All six cameras, shared ids, cross-references, negative evidence."""
    lines = [
        "SURROUND-VIEW SCENE DESCRIPTION",
        "Ego vehicle at origin. Bearing is measured from straight ahead;",
        "left is positive, right is negative. Range is quantised into bands",
        "because monocular distance is unreliable.",
        "",
    ]
    for camera in CAMERAS:
        here = [o for o in objects if camera in o.views]
        lines.append(f"{camera}:")
        if not here:
            lines.append("  - no agents detected")
        else:
            for obj in sorted(here, key=lambda o: o.dist):
                lines.append(_object_line(obj, camera, cross_ref=True))
        lines.append("")

    multi = [o for o in objects if len(o.views) > 1]
    lines.append(f"TOTAL DISTINCT OBJECTS: {len(objects)}")
    if multi:
        lines.append("Objects visible in more than one camera:")
        for obj in multi:
            lines.append(f"  - {obj.obj_id} ({obj.class_name}): {', '.join(obj.views)}")
    else:
        lines.append("No object was detected in more than one camera.")
    return "\n".join(lines).rstrip() + "\n"


def isolated_render(objects: list[SceneObject], camera: str) -> str:
    """One camera only. No cross-references, ids local to this view."""
    here = sorted([o for o in objects if camera in o.views], key=lambda o: o.dist)
    lines = [
        f"SINGLE-VIEW SCENE DESCRIPTION ({camera})",
        "Ego vehicle at origin. Bearing is measured from straight ahead;",
        "left is positive, right is negative.",
        "",
        f"{camera}:",
    ]
    if not here:
        lines.append("  - no agents detected")
    else:
        for i, obj in enumerate(here, start=1):
            local = SceneObject(
                obj_id=f"a{i}",
                class_name=obj.class_name,
                x=obj.x,
                y=obj.y,
                views=[camera],
                confidence=obj.confidence,
            )
            lines.append(_object_line(local, camera, cross_ref=False))
    return "\n".join(lines).rstrip() + "\n"

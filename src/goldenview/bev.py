"""Ground-plane back-projection and cross-camera association.

Turns per-image 2D detections into a single list of objects in ego-centric
metres, each carrying the set of cameras it was seen in. That view-set is what
the task actually asks for, so it is the output that matters.

Pure standard library: the detector needs torch, this does not.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .rig import RIG

DEDUP_RADIUS_M = 2.0

# Only neighbouring cameras have overlapping fields of view. Association across
# any other pair is physically implausible and usually comes from an unstable
# far-range ground-plane projection.
OVERLAPPING_CAMERA_PAIRS = frozenset({
    frozenset(("CAM_FRONT", "CAM_FRONT_LEFT")),
    frozenset(("CAM_FRONT", "CAM_FRONT_RIGHT")),
    frozenset(("CAM_FRONT_LEFT", "CAM_BACK_LEFT")),
    frozenset(("CAM_BACK_LEFT", "CAM_BACK")),
    frozenset(("CAM_BACK", "CAM_BACK_RIGHT")),
    frozenset(("CAM_BACK_RIGHT", "CAM_FRONT_RIGHT")),
})

# Monocular range from a flat-ground assumption degrades quadratically, so range
# is reported as a band. Bearing is kept precise: azimuth is the accurate axis of
# monocular geometry and it is what view attribution depends on.
NEAR_M = 10.0
MID_M = 25.0


def quat_to_matrix(q: list[float]) -> list[list[float]]:
    """nuScenes stores rotation as (w, x, y, z)."""
    w, x, y, z = q
    n = math.sqrt(w * w + x * x + y * y + z * z) or 1.0
    w, x, y, z = w / n, x / n, y / n, z / n
    return [
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (x * w + y * z), 1 - 2 * (x * x + y * y)],
    ]


def _inv3(m: list[list[float]]) -> list[list[float]]:
    a, b, c = m[0]
    d, e, f = m[1]
    g, h, i = m[2]
    det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    if abs(det) < 1e-12:
        raise ValueError("singular matrix")
    return [
        [(e * i - f * h) / det, (c * h - b * i) / det, (b * f - c * e) / det],
        [(f * g - d * i) / det, (a * i - c * g) / det, (c * d - a * f) / det],
        [(d * h - e * g) / det, (b * g - a * h) / det, (a * e - b * d) / det],
    ]


def _matvec(m: list[list[float]], v: list[float]) -> list[float]:
    return [sum(m[r][k] * v[k] for k in range(3)) for r in range(3)]


def pixel_to_ground(camera: str, cx_px: float, y_bottom_px: float) -> tuple[float, float] | None:
    """Back-project a bbox bottom-centre onto the ground plane z=0 in ego frame.

    Returns (x, y) in metres, or None when the ray does not meet the plane in
    front of the camera.
    """
    cal = RIG[camera]
    k_inv = _inv3(cal["intrinsic"])
    ray_cam = _matvec(k_inv, [cx_px, y_bottom_px, 1.0])
    rot = quat_to_matrix(cal["rotation"])
    ray_ego = _matvec(rot, ray_cam)
    origin = cal["translation"]
    if abs(ray_ego[2]) < 1e-6:
        return None
    lam = -origin[2] / ray_ego[2]
    if lam <= 0:
        return None
    return origin[0] + lam * ray_ego[0], origin[1] + lam * ray_ego[1]


def range_band(dist_m: float) -> str:
    if dist_m < NEAR_M:
        return "near"
    if dist_m <= MID_M:
        return "mid"
    return "far"


def bearing_deg(x: float, y: float) -> float:
    """Degrees from straight ahead. Positive is left, negative is right."""
    return round(math.degrees(math.atan2(y, x)), 1)


@dataclass
class SceneObject:
    obj_id: str
    class_name: str
    x: float
    y: float
    views: list[str] = field(default_factory=list)
    confidence: float = 0.0
    n_detections: int = 0

    @property
    def dist(self) -> float:
        return math.sqrt(self.x**2 + self.y**2)

    @property
    def band(self) -> str:
        return range_band(self.dist)

    @property
    def bearing(self) -> float:
        return bearing_deg(self.x, self.y)

    def as_dict(self) -> dict:
        return {
            "id": self.obj_id,
            "class": self.class_name,
            "x_m": round(self.x, 2),
            "y_m": round(self.y, 2),
            "dist_m": round(self.dist, 2),
            "range_band": self.band,
            "bearing_deg": self.bearing,
            "views": list(self.views),
            "confidence": round(self.confidence, 3),
            "n_detections": self.n_detections,
        }


def cameras_overlap(camera_a: str, camera_b: str) -> bool:
    """Whether two cameras are neighbours on the six-camera rig."""
    return frozenset((camera_a, camera_b)) in OVERLAPPING_CAMERA_PAIRS


def associate(
    detections: dict[str, list[dict]],
    radius: float = DEDUP_RADIUS_M,
    *,
    prevent_same_camera_merge: bool = False,
    restrict_to_overlapping_cameras: bool = False,
) -> list[SceneObject]:
    """Group per-camera detections into objects carrying a view-set.

    A detection joins an existing object when it is the same class and within
    `radius` metres in BEV. Unlike GeoDrive's `_merge_agents`, a duplicate is
    absorbed rather than discarded, so the camera it came from is recorded. That
    is the whole point: the view-set is the label this task asks for.
    """
    objects: list[SceneObject] = []
    flat = []
    for camera, dets in detections.items():
        for det in dets:
            ground = pixel_to_ground(camera, det["cx_px"], det["bbox_xyxy"][3])
            if ground is None:
                continue
            flat.append((math.hypot(*ground), camera, det, ground))
    # Nearest first, so the anchor of each object is its best-conditioned
    # observation; flat-ground range error grows with distance.
    flat.sort(key=lambda r: r[0])

    for _, camera, det, (gx, gy) in flat:
        match = None
        for obj in objects:
            if obj.class_name != det["class_name"]:
                continue
            if prevent_same_camera_merge and camera in obj.views:
                continue
            if restrict_to_overlapping_cameras and not any(
                cameras_overlap(camera, existing) for existing in obj.views
            ):
                continue
            if math.hypot(gx - obj.x, gy - obj.y) < radius:
                match = obj
                break
        if match is None:
            obj = SceneObject(
                obj_id=f"obj{len(objects) + 1}",
                class_name=det["class_name"],
                x=gx,
                y=gy,
                views=[camera],
                confidence=det["confidence"],
                n_detections=1,
            )
            objects.append(obj)
        else:
            if camera not in match.views:
                match.views.append(camera)
            match.confidence = max(match.confidence, det["confidence"])
            match.n_detections += 1

    objects.sort(key=lambda o: o.dist)
    for i, obj in enumerate(objects, start=1):
        obj.obj_id = f"obj{i}"
    return objects

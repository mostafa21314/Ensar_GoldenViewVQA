from unittest.mock import patch

from goldenview.bev import SceneObject, associate, cameras_overlap
from goldenview.serialize import full_render_v2


def test_only_neighbouring_cameras_overlap():
    assert cameras_overlap("CAM_FRONT", "CAM_FRONT_LEFT")
    assert cameras_overlap("CAM_BACK", "CAM_BACK_RIGHT")
    assert not cameras_overlap("CAM_FRONT", "CAM_BACK")
    assert not cameras_overlap("CAM_FRONT_LEFT", "CAM_FRONT_RIGHT")


def test_v2_render_prunes_only_tentative_far_objects():
    objects = [
        SceneObject("obj1", "car", 30.0, 0.0, ["CAM_FRONT"], 0.20, 1),
        SceneObject("obj2", "truck", 30.0, 1.0, ["CAM_FRONT"], 0.70, 1),
        SceneObject("obj3", "pedestrian", 5.0, 0.0, ["CAM_FRONT"], 0.20, 1),
    ]

    rendered = full_render_v2(objects)

    assert "obj1" not in rendered
    assert "obj2" in rendered and "confidence high" in rendered
    assert "obj3" in rendered and "confidence tentative" in rendered
    assert "OMITTED TENTATIVE FAR DETECTIONS: 1" in rendered


def _detection(class_name="car"):
    return {
        "class_name": class_name,
        "confidence": 0.8,
        "cx_px": 100.0,
        "bbox_xyxy": [90.0, 90.0, 110.0, 110.0],
    }


def test_v2_does_not_merge_two_detections_from_one_camera():
    detections = {"CAM_FRONT": [_detection(), _detection()]}
    with patch("goldenview.bev.pixel_to_ground", side_effect=[(5.0, 0.0), (5.5, 0.0)]):
        objects = associate(detections, prevent_same_camera_merge=True)
    assert len(objects) == 2


def test_v2_does_not_merge_nonoverlapping_cameras():
    detections = {"CAM_FRONT": [_detection()], "CAM_BACK": [_detection()]}
    with patch("goldenview.bev.pixel_to_ground", side_effect=[(5.0, 0.0), (5.5, 0.0)]):
        objects = associate(detections, restrict_to_overlapping_cameras=True)
    assert len(objects) == 2

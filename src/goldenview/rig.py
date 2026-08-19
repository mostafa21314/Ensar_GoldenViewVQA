"""Fixed nuScenes camera rig geometry.

Per-camera intrinsics and cam->ego extrinsics, taken as the median over all 850
trainval logs. Across the dataset focal length varies by <=1.3% and mount
positions by under 6 cm, so treating the rig as a constant loses nothing
measurable. Baked in here so inference reads only images and never a nuScenes
table, as the task rules require.

Rotation is stored as a quaternion (w, x, y, z) exactly as nuScenes reports it.
"""

from __future__ import annotations

IMG_W = 1600
IMG_H = 900

RIG: dict[str, dict] = {
    "CAM_FRONT": {
        "intrinsic": [[1252.8131, 0.0, 826.5881], [0.0, 1252.8131, 469.9847], [0.0, 0.0, 1.0]],
        "translation": [1.722, 0.0048, 1.4949],
        "rotation": [0.507724, -0.497339, 0.498372, -0.496483],
    },
    "CAM_FRONT_LEFT": {
        "intrinsic": [[1257.8625, 0.0, 827.2411], [0.0, 1257.8625, 450.9155], [0.0, 0.0, 1.0]],
        "translation": [1.5753, 0.5005, 1.507],
        "rotation": [0.681209, -0.668751, 0.21017, -0.211082],
    },
    "CAM_FRONT_RIGHT": {
        "intrinsic": [[1256.7485, 0.0, 817.7888], [0.0, 1256.7485, 451.9542], [0.0, 0.0, 1.0]],
        "translation": [1.5808, -0.4991, 1.5175],
        "rotation": [0.203352, -0.191463, 0.678571, -0.679361],
    },
    "CAM_BACK": {
        "intrinsic": [[796.8911, 0.0, 857.7774], [0.0, 796.8911, 476.8849], [0.0, 0.0, 1.0]],
        "translation": [0.0552, 0.0108, 1.5679],
        "rotation": [0.5068, -0.497757, -0.498785, 0.496594],
    },
    "CAM_BACK_LEFT": {
        "intrinsic": [[1254.9861, 0.0, 829.5769], [0.0, 1254.9861, 467.1681], [0.0, 0.0, 1.0]],
        "translation": [1.0485, 0.4831, 1.5621],
        "rotation": [0.704862, -0.690731, -0.112091, 0.116173],
    },
    "CAM_BACK_RIGHT": {
        "intrinsic": [[1249.9629, 0.0, 825.3768], [0.0, 1249.9629, 462.5482], [0.0, 0.0, 1.0]],
        "translation": [1.0595, -0.4672, 1.5505],
        "rotation": [0.138192, -0.137967, -0.689333, 0.69763],
    },
}

CAMERAS = tuple(RIG)

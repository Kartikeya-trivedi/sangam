"""InsightFace face embeddings — a LIVE-INTAKE capability (the dataset has no photos).

Optional: `pip install -e '.[faces]'` on a box with onnxruntime. Without it, embed() returns
None and the matching engine simply runs on attributes + geo. Face matching only ever dominates
when BOTH sides have an embedding, so its absence degrades gracefully.
"""
from __future__ import annotations

from functools import lru_cache

from config import settings

try:
    import numpy as np
    from insightface.app import FaceAnalysis  # type: ignore
except Exception:
    FaceAnalysis = None
    np = None


def available() -> bool:
    return FaceAnalysis is not None


@lru_cache(maxsize=1)
def _get_app():
    if not available():
        return None
    app = FaceAnalysis(name=settings.face_model)
    app.prepare(ctx_id=0, det_size=(640, 640))
    return app


def embed(image_path: str) -> list[float] | None:
    """Largest detected face -> normalized 512-d embedding. None if no face / unavailable."""
    app = _get_app()
    if app is None:
        return None
    try:
        img = _read_image(image_path)
        faces = app.get(img)
        if not faces:
            return None
        face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
        vec = face.normed_embedding
        return [float(x) for x in vec]
    except Exception:
        return None


def _read_image(path: str):
    import cv2  # type: ignore
    return cv2.imread(path)

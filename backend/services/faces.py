"""InsightFace face embeddings (spec §4, §14). Local, GPU, no API.

buffalo_l -> 512-d embedding. Embed once at intake, store the vector. Loads lazily so
the app boots without the model present (offline/degraded path: face matching disabled,
attribute matching still works, §13).
"""
from __future__ import annotations

import io
from typing import Optional

import numpy as np

from config import settings

_app = None  # insightface FaceAnalysis, lazily initialized


def _get_app():
    global _app
    if _app is not None:
        return _app
    try:
        from insightface.app import FaceAnalysis  # type: ignore

        app = FaceAnalysis(name=settings.face_model)
        app.prepare(ctx_id=0)  # GPU 0; set ctx_id=-1 for CPU
        _app = app
    except Exception as e:  # model/runtime missing -> degrade to no-face matching
        print(f"[faces] InsightFace unavailable, face matching disabled: {e}")
        _app = None
    return _app


def embed(image_bytes: bytes) -> Optional[list[float]]:
    """Return a 512-d face embedding for the largest detected face, or None."""
    app = _get_app()
    if app is None:
        return None
    from PIL import Image

    img = np.array(Image.open(io.BytesIO(image_bytes)).convert("RGB"))[:, :, ::-1]  # RGB -> BGR
    faces = app.get(img)
    if not faces:
        return None
    faces.sort(key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]), reverse=True)
    return faces[0].embedding.astype("float32").tolist()


def cosine(a: list[float], b: list[float]) -> float:
    va, vb = np.asarray(a, "float32"), np.asarray(b, "float32")
    na, nb = np.linalg.norm(va), np.linalg.norm(vb)
    return 0.0 if na == 0 or nb == 0 else float(np.dot(va, vb) / (na * nb))

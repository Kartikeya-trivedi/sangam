"""Locate a described person in a crowd/CCTV photo and mark them — Claude Vision grounding.

SETU's "scan the ghat camera" capability: given a frame and a text description (e.g. a missing
person's report), Claude returns a bounding box around the best-matching person, and we draw it.

Run from backend/ (so the Anthropic key in .env is read):
    uv run --with pillow python ../scripts/locate.py <image> "<description>"
Writes <image>-marked.jpg next to the source and prints the box + confidence.
"""
from __future__ import annotations

import base64
import json
import pathlib
import sys

_BACKEND = pathlib.Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(_BACKEND))

from config import settings  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import anthropic  # noqa: E402

_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "found": {"type": "boolean"},
        "box": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "x0": {"type": "number"}, "y0": {"type": "number"},
                "x1": {"type": "number"}, "y1": {"type": "number"},
            },
            "required": ["x0", "y0", "x1", "y1"],
        },
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        "note": {"type": "string"},
    },
    "required": ["found", "box", "confidence", "note"],
}

_SYSTEM = """You are SETU's camera-scan vision service at the Kumbh Mela. You receive a crowd/CCTV \
photo and a description of ONE missing person. Find the single best-matching person and return a \
NORMALIZED bounding box (x0,y0,x1,y1 each 0..1, origin = TOP-LEFT, x rightward, y downward) drawn \
tightly around just that person (head to visible torso/legs). If several plausibly match, pick the \
most likely and say so in `note`. If no one clearly matches, set found=false and a centered box. \
Be decisive; approximate boxes are fine."""


def main() -> None:
    img_path = pathlib.Path(sys.argv[1]).resolve()
    query = sys.argv[2] if len(sys.argv) > 2 else "the missing person"
    media = "image/png" if img_path.suffix.lower() == ".png" else "image/jpeg"
    b64 = base64.standard_b64encode(img_path.read_bytes()).decode("ascii")

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    msg = client.messages.create(
        model=settings.anthropic_model, max_tokens=600, system=_SYSTEM,
        output_config={"format": {"type": "json_schema", "schema": _SCHEMA}},
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": media, "data": b64}},
            {"type": "text", "text": f"Locate: {query}"},
        ]}],
    )
    text = next((b.text for b in msg.content if getattr(b, "type", None) == "text"), "")
    res = json.loads(text)
    box = res["box"]

    im = Image.open(img_path).convert("RGB")
    W, H = im.size
    x0, y0, x1, y1 = box["x0"] * W, box["y0"] * H, box["x1"] * W, box["y1"] * H
    d = ImageDraw.Draw(im)
    color = (220, 38, 38) if res.get("confidence") != "low" else (245, 158, 11)
    for w in range(4):  # thick box
        d.rectangle([x0 - w, y0 - w, x1 + w, y1 + w], outline=color)
    label = f" {query[:38]} · {res.get('confidence', '?')} "
    try:
        font = ImageFont.truetype("arial.ttf", max(14, W // 45))
    except Exception:
        font = ImageFont.load_default()
    tb = d.textbbox((0, 0), label, font=font)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    ly = max(0, y0 - th - 8)
    d.rectangle([x0 - 2, ly, x0 - 2 + tw + 8, ly + th + 8], fill=color)
    d.text((x0 + 2, ly + 3), label, fill=(255, 255, 255), font=font)

    out = img_path.with_name(img_path.stem + "-marked.jpg")
    im.save(out, quality=90)
    print(json.dumps({"found": res.get("found"), "confidence": res.get("confidence"),
                      "note": res.get("note"), "box_px": [round(x0), round(y0), round(x1), round(y1)],
                      "out": str(out)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

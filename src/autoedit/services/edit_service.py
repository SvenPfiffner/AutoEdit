"""Image editing stubs that fall back to lightweight behaviour for demos."""

from __future__ import annotations

import io
from typing import Optional

from PIL import Image

try:  # pragma: no cover - optional heavy dependency
    import torch
    from diffusers import QwenImageEditPipeline
except ModuleNotFoundError:  # pragma: no cover - handled gracefully
    torch = None  # type: ignore[assignment]
    QwenImageEditPipeline = None  # type: ignore[assignment]

from autoedit.services.prompts import QWEN_NEGATIVE_PROMPT, QWEN_POSITIVE_PROMPT

MODEL_PATH = "ovedrive/qwen-image-edit-4bit"


def _load_pipeline() -> Optional[QwenImageEditPipeline]:  # type: ignore[name-defined]
    if QwenImageEditPipeline is None:
        return None

    dtype = torch.bfloat16 if torch is not None else None
    pipeline = QwenImageEditPipeline.from_pretrained(MODEL_PATH, torch_dtype=dtype)
    if torch is not None and hasattr(pipeline, "to"):
        try:  # pragma: no cover - env specific
            pipeline.to("cuda")
        except Exception:
            pipeline.to("cpu")
    return pipeline


def _pipeline_edit(pipeline: QwenImageEditPipeline, image_bytes: bytes, refined_prompt: str) -> Optional[bytes]:
    image = Image.open(io.BytesIO(image_bytes))
    prompt = refined_prompt + ". maintain the character face, eyes, skin details, lighting, pose, position and overall composition"
    generator = torch.manual_seed(0) if torch is not None else None

    with torch.inference_mode():  # type: ignore[union-attr]
        output = pipeline(
            image=image,
            prompt=f"{prompt}, {QWEN_POSITIVE_PROMPT}",
            generator=generator,
            true_cfg_scale=4.0,
            negative_prompt=QWEN_NEGATIVE_PROMPT,
            num_inference_steps=20,
        )

    pipeline.to("cpu")
    if torch is not None and hasattr(torch.cuda, "empty_cache"):
        torch.cuda.empty_cache()

    output_image = output.images[0]
    buffer = io.BytesIO()
    output_image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()


def edit_image(image_bytes: bytes, refined_prompt: str) -> Optional[bytes]:
    """Apply the QWEN image edit pipeline or return the original bytes."""

    if QwenImageEditPipeline is None or torch is None:
        return image_bytes

    try:
        pipeline = _load_pipeline()
        if pipeline is None:
            return image_bytes
        return _pipeline_edit(pipeline, image_bytes, refined_prompt)
    except Exception:  # pragma: no cover - defensive fallback
        return image_bytes


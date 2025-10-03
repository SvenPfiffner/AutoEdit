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

from autoedit.services.prompts import QWEN_POSITIVE_PROMPT, QWEN_NEGATIVE_PROMPT

# Global singleton instance to avoid reloading pipeline
_pipeline = None

def _get_pipeline():
    """Load pipeline once, then reuse it."""
    global _pipeline
    
    if _pipeline is None:
        print("Loading QWEN-Image-Edit pipeline...")
        model_path = "ovedrive/qwen-image-edit-4bit"
        _pipeline = QwenImageEditPipeline.from_pretrained(model_path, torch_dtype=torch.bfloat16)
        _pipeline.set_progress_bar_config(disable=None)
        _pipeline.to("cuda")  # Keep on GPU for reuse
        print("QWEN-Image-Edit pipeline loaded successfully!")
    
    return _pipeline

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
    
    # Get cached pipeline
    pipeline = _get_pipeline()
    prompt = refined_prompt + ". mantain the character face, eyes, skin details, lightning, pose, position and overall composition)"
    inputs = {
        "image": image,
        "prompt": prompt + ", " + QWEN_POSITIVE_PROMPT,
        "generator": torch.manual_seed(0),
        "true_cfg_scale": 4.0,
        "negative_prompt": QWEN_NEGATIVE_PROMPT,
        "num_inference_steps": 20, # even 10 steps should be enough in many cases
    }

    with torch.inference_mode():
        output = pipeline(**inputs)

    # Keep pipeline on GPU for reuse - don't move to CPU anymore
    # pipeline.to("cpu")  # Commented out to keep model loaded
    # torch.cuda.empty_cache()  # Only clear cache if needed

    output_image = output.images[0]
    buffer = io.BytesIO()
    output_image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()


def edit_image(image_bytes: bytes, refined_prompt: str) -> Optional[bytes]:
    """Apply the QWEN image edit pipeline or return the original bytes."""

    if QwenImageEditPipeline is None or torch is None:
        return image_bytes


    pipeline = _load_pipeline()
    if pipeline is None:
        print("Ohhhhhhhhh please")
        return image_bytes
    return _pipeline_edit(pipeline, image_bytes, refined_prompt)



"""Image editing stubs that fall back to lightweight behaviour for demos."""

from __future__ import annotations

import io
from typing import Optional, Tuple

from PIL import Image

import torch
from diffusers import QwenImageEditPipeline

from autoedit.services.prompts import QWEN_POSITIVE_PROMPT, QWEN_NEGATIVE_PROMPT


MODEL_PATH = "ovedrive/qwen-image-edit-4bit"

pipeline: Optional[QwenImageEditPipeline] = None


def ensure_pipeline_loaded() -> None:
    global pipeline
    if pipeline is None:
        pipeline = QwenImageEditPipeline.from_pretrained(
            MODEL_PATH, torch_dtype=torch.bfloat16
        )
        pipeline.set_progress_bar_config(disable=None)


def ensure_pipeline_on(device: str) -> None:
    if pipeline is None:
        return
    target_device = torch.device(device)
    current_device = getattr(pipeline, "device", None)
    if current_device != target_device:
        pipeline.to(target_device)


def cleanup_pipeline() -> None:
    """Offload the pipeline to CPU without discarding the instance."""

    if pipeline is not None:
        ensure_pipeline_on("cpu")
        torch.cuda.empty_cache()


ENCODED_OUTPUT_FORMAT = "PNG"

def edit_image(
    image_bytes: bytes, refined_prompt: str, is_professional: bool, progress_callback
) -> Optional[Tuple[bytes, str]]:

    global pipeline

    was_loaded = pipeline is not None

    if progress_callback:
        status_message = (
            "Loading QWEN-Image-Edit model..."
            if not was_loaded
            else "Preparing QWEN-Image-Edit model..."
        )
        progress_callback(2, "active", status_message)

    ensure_pipeline_loaded()
    ensure_pipeline_on("cuda")

    if progress_callback:
        progress_callback(2, "complete", "QWEN-Image-Edit model ready.")


    image = Image.open(io.BytesIO(image_bytes))

    prompt = (
        refined_prompt
        + ". maintain the character face, eyes, skin details, lighting, pose, position and overall composition."
    )
    inputs = {
        "image": image,
        "prompt": prompt + ", " + QWEN_POSITIVE_PROMPT,
        "generator": torch.manual_seed(0),
        "true_cfg_scale": 4.0,
        "negative_prompt": QWEN_NEGATIVE_PROMPT,
        "num_inference_steps": 20, # even 10 steps should be enough in many cases
    }

    if progress_callback:
        progress_callback(3, "active", "Applying QWEN-Image-Edit...")

    with torch.inference_mode():
        output = pipeline(**inputs)

    if not is_professional:
        cleanup_pipeline()

    output_image = output.images[0]
    
    buffer = io.BytesIO()
    output_image.save(buffer, format=ENCODED_OUTPUT_FORMAT)
    buffer.seek(0)

    if progress_callback:
        progress_callback(3, "complete", "QWEN-Image-Edit applied successfully.")

    return buffer.getvalue(), ENCODED_OUTPUT_FORMAT

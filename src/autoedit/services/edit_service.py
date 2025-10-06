"""Image editing stubs that fall back to lightweight behaviour for demos."""

from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path
from typing import Optional

from PIL import Image

from typing import Optional

import torch
from diffusers import QwenImageEditPipeline

from autoedit.services.prompts import QWEN_POSITIVE_PROMPT, QWEN_NEGATIVE_PROMPT


MODEL_PATH = "dimitribarbot/Qwen-Image-Edit-int8wo"

pipeline = None

def cleanup_pipeline():
    global pipeline
    if pipeline is not None:
        pipeline.to("cpu")
        pipeline = None
        torch.cuda.empty_cache()

def edit_image(image_bytes: bytes, refined_prompt: str, is_professional: bool, progress_callback) -> Optional[bytes]:

    if progress_callback:
        progress_callback(2, "active", "Loading QWEN-Image-Edit model...")

    global pipeline
    
    if pipeline is None:
        pipeline = QwenImageEditPipeline.from_pretrained(MODEL_PATH, torch_dtype=torch.bfloat16)
        pipeline.set_progress_bar_config(disable=None)
        pipeline.to("cuda")

    if progress_callback:
        progress_callback(2, "complete", "QWEN-Image-Edit model loaded successfully.")


    image = Image.open(io.BytesIO(image_bytes))

    prompt = refined_prompt + ". mantain the character face, eyes, skin details, lightning, pose, position and overall composition)"
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
    output_image.save(buffer, format="PNG")
    buffer.seek(0)

    if progress_callback:
        progress_callback(3, "complete", "QWEN-Image-Edit applied successfully.")

    return buffer.getvalue()
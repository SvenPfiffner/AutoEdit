"""Image editing stubs that fall back to lightweight behaviour for demos."""

from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path
from typing import Optional

from PIL import Image

import torch
from diffusers import AutoModel, DiffusionPipeline

from autoedit.services.prompts import QWEN_POSITIVE_PROMPT, QWEN_NEGATIVE_PROMPT

MODEL_PATH = "dimitribarbot/Qwen-Image-Edit-int8wo"

def edit_image(image_bytes: bytes, refined_prompt: str) -> Optional[bytes]:

    torch_dtype = torch.bfloat16
    device = "cuda"

    transformer = AutoModel.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch_dtype,
        use_safetensors=False
    )
    pipe = DiffusionPipeline.from_pretrained(
        "Qwen/Qwen-Image-Edit",
        transformer=transformer,
        torch_dtype=torch_dtype
    )
    pipe.enable_model_cpu_offload()
    pipe.enable_vae_tiling()

    image = Image.open(io.BytesIO(image_bytes))

    prompt = refined_prompt + ". mantain the character face, eyes, skin details, lightning, pose, position and overall composition)"

    output_image = pipe(
        image=image,
        prompt=prompt + ", " + QWEN_POSITIVE_PROMPT,
        num_inference_steps=20,
        negative_prompt=QWEN_NEGATIVE_PROMPT,
        true_cfg_scale=4.0,
        generator=torch.manual_seed(0),
    ).images[0]

    
    buffer = io.BytesIO()
    output_image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()



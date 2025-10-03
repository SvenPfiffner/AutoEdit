import os
from typing import Callable, List, Optional
import io


from PIL import Image
import torch

from diffusers import QwenImageEditPipeline

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

def edit_image(image_bytes: bytes, refined_prompt: str) -> Optional[bytes]:
        
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
    output_buffer = io.BytesIO()
    output_image.save(output_buffer, format="PNG")
    output_buffer.seek(0)
    return output_buffer.getvalue()
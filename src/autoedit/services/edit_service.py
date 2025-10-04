"""Image editing stubs that fall back to lightweight behaviour for demos."""

from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path
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


def _get_project_root() -> Path:
    """Get the project root directory."""
    # Navigate from src/autoedit/services to project root
    return Path(__file__).parent.parent.parent.parent


def _save_generated_image(image: Image.Image) -> None:
    """Save the generated image to tmp folder with timestamp."""
    try:
        project_root = _get_project_root()
        tmp_dir = project_root / "tmp"
        
        # Create tmp directory if it doesn't exist
        tmp_dir.mkdir(exist_ok=True)
        
        # Generate timestamp-based filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # milliseconds precision
        filename = f"generated_{timestamp}.png"
        filepath = tmp_dir / filename
        
        # Save the image
        image.save(filepath, format="PNG")
        print(f"Generated image saved to: {filepath}")
    except Exception as e:
        print(f"Warning: Could not save generated image to tmp folder: {e}")


def _pipeline_edit(image_bytes: bytes, refined_prompt: str) -> Optional[bytes]:
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
    
    # Save the generated image to tmp folder with timestamp
    _save_generated_image(output_image)
    
    buffer = io.BytesIO()
    output_image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()


def edit_image(image_bytes: bytes, refined_prompt: str) -> Optional[bytes]:
    """Apply the QWEN image edit pipeline or return the original bytes."""

    if QwenImageEditPipeline is None or torch is None:
        return image_bytes

    return _pipeline_edit(image_bytes, refined_prompt)



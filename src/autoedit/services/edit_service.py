import os
from typing import Callable, List, Optional
import io


from PIL import Image
import torch

from diffusers import QwenImageEditPipeline

def edit_image(image_bytes: bytes, refined_prompt: str) -> Optional[bytes]:
        
    image = Image.open(io.BytesIO(image_bytes))
    
    model_path = "ovedrive/qwen-image-edit-4bit"
    pipeline = QwenImageEditPipeline.from_pretrained(model_path, torch_dtype=torch.bfloat16)
    print("pipeline loaded") # not true but whatever. do not move to cuda

    pipeline.set_progress_bar_config(disable=None)
    pipeline.to("cuda") #if you have enough VRAM replace this line with `pipeline.to("cuda")` which is 20GB VRAM
    prompt = "mantain the character face, eyes, skin details, lightning, pose, position and overall composition)"
    inputs = {
        "image": image,
        "prompt": prompt,
        "generator": torch.manual_seed(0),
        "true_cfg_scale": 4.0,
        "negative_prompt": "low quality, bad anatomy, extra fingers, missing fingers, extra limbs, missing limbs",
        "num_inference_steps": 20, # even 10 steps should be enough in many cases
    }

    with torch.inference_mode():
        output = pipeline(**inputs)

    pipeline.to("cpu")
    torch.cuda.empty_cache()

    output_image = output.images[0]
    output_buffer = io.BytesIO()
    output_image.save(output_buffer, format="PNG")
    output_buffer.seek(0)
    return output_buffer.getvalue()
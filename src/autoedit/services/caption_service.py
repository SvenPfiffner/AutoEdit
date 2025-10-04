"""Caption generation helpers with graceful fallbacks for local development."""

from __future__ import annotations

import io
from PIL import Image

from typing import Optional

try:  # pragma: no cover - optional heavy dependency path
    import torch
    from transformers import AutoProcessor, LlavaForConditionalGeneration
except ModuleNotFoundError:  # pragma: no cover - handled gracefully
    torch = None  # type: ignore[assignment]
    AutoProcessor = None  # type: ignore[assignment]
    LlavaForConditionalGeneration = None  # type: ignore[assignment]

from autoedit.services.prompts import JOYCAPTION_PROMPT


MODEL_NAME = "fancyfeast/llama-joycaption-beta-one-hf-llava"

def generate_caption(image_bytes: bytes, prompt: str, progress_callback) -> str:

    if progress_callback:
        progress_callback(0, "active", "Loading JoyCaption model...")

    processor = AutoProcessor.from_pretrained(MODEL_NAME)
        
    dtype = torch.bfloat16
    model = LlavaForConditionalGeneration.from_pretrained(
        MODEL_NAME,
        torch_dtype=dtype,
        device_map="cuda:0",
        low_cpu_mem_usage=True,
    ).eval()

    if progress_callback:
        progress_callback(0, "complete", "JoyCaption model loaded successfully.")

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    convo = [
        {"role": "system", "content": JOYCAPTION_PROMPT},
        {"role": "user", "content": prompt},
    ]

    prompt_str = processor.apply_chat_template(
        convo, tokenize=False, add_generation_prompt=True
    )

    inputs = processor(text=[prompt_str], images=[image], return_tensors="pt").to("cuda:0")

    if progress_callback:
        progress_callback(1, "active", "Generating caption with JoyCaption...")

    with torch.no_grad():
        gen_ids = model.generate(  
            **inputs,
            max_new_tokens=256,
            do_sample=True,
            temperature=0.6,
            top_p=0.9,
            use_cache=True,
            suppress_tokens=None,
        )[0]

    gen_ids = gen_ids[inputs["input_ids"].shape[1]:]
    text = processor.tokenizer.decode(
        gen_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False
    ).strip()

    if progress_callback:
        progress_callback(1, "complete", "Caption generation complete.")

    return text


"""Caption generation helpers with graceful fallbacks for local development."""

from __future__ import annotations

import io
from PIL import Image

try:  # pragma: no cover - optional heavy dependency path
    import torch
    from transformers import AutoProcessor, LlavaForConditionalGeneration
except ModuleNotFoundError:  # pragma: no cover - handled gracefully
    torch = None  # type: ignore[assignment]
    AutoProcessor = None  # type: ignore[assignment]
    LlavaForConditionalGeneration = None  # type: ignore[assignment]

from autoedit.services.prompts import JOYCAPTION_PROMPT

MODEL_NAME = "fancyfeast/llama-joycaption-beta-one-hf-llava"


def _generate_with_model(image_bytes: bytes, prompt: str) -> str:
    """Run the JoyCaption model when dependencies are available."""

    assert AutoProcessor is not None and LlavaForConditionalGeneration is not None

    processor = AutoProcessor.from_pretrained(MODEL_NAME)

    if torch is not None and torch.cuda.is_available():  # pragma: no cover - env specific
        dtype = torch.bfloat16
        device_map = "auto"
    else:
        dtype = torch.float32 if torch is not None else None
        device_map = {"": "cpu"}

    model = LlavaForConditionalGeneration.from_pretrained(
        MODEL_NAME,
        torch_dtype=dtype,
        device_map=device_map,
    ).eval()

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    convo = [
        {"role": "system", "content": JOYCAPTION_PROMPT},
        {"role": "user", "content": prompt},
    ]

    prompt_str = processor.apply_chat_template(
        convo, tokenize=False, add_generation_prompt=True
    )

    inputs = processor(text=[prompt_str], images=[image], return_tensors="pt")

    if torch is not None and torch.cuda.is_available():  # pragma: no cover
        inputs = {k: v.to(model.device) for k, v in inputs.items()}
        inputs["pixel_values"] = inputs["pixel_values"].to(torch.bfloat16)

    with torch.no_grad():  # type: ignore[union-attr]
        gen_ids = model.generate(  # type: ignore[assignment]
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

    return text


def _fallback_caption(prompt: str) -> str:
    base_prompt = (prompt or "Uploaded visual").strip()
    return (
        f"Placeholder caption: {base_prompt[:120]}"
        if base_prompt
        else "Placeholder caption"
    )


def generate_caption(image_bytes: bytes, prompt: str) -> str:
    """Return a caption, falling back to a lightweight heuristic if needed."""

    if AutoProcessor is None or LlavaForConditionalGeneration is None:
        return _fallback_caption(prompt)

    try:
        return _generate_with_model(image_bytes, prompt)
    except Exception:  # pragma: no cover - defensive fallback for dev envs
        return _fallback_caption(prompt)


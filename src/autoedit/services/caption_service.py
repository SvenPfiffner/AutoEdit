from PIL import Image
import io
import torch
from transformers import AutoProcessor, LlavaForConditionalGeneration

MODEL_NAME = "fancyfeast/llama-joycaption-beta-one-hf-llava"

from autoedit.services.prompts import JOYCAPTION_PROMPT

def generate_caption(image_bytes: bytes, prompt: str) -> str:

    # Load model + processor
    processor = AutoProcessor.from_pretrained(MODEL_NAME)
    # Use GPU if you have it; otherwise fall back to CPU/float32
    if torch.cuda.is_available():
        dtype = torch.bfloat16  # model is BF16-native
        device_map = "auto"
    else:
        dtype = torch.float32
        device_map = {"": "cpu"}  # load on CPU

    model = LlavaForConditionalGeneration.from_pretrained(
        MODEL_NAME,
        torch_dtype=dtype,
        device_map=device_map,
    ).eval()

    # Open image
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # Build a plain chat (no <image> token needed here!)
    convo = [
        {"role": "system", "content": JOYCAPTION_PROMPT},
        {"role": "user", "content": prompt},
    ]

    # Render the chat template to a string prompt
    # (JoyCaption’s card shows this exact sequence)
    prompt_str = processor.apply_chat_template(
        convo, tokenize=False, add_generation_prompt=True
    )

    # Prepare inputs (this step injects the correct number of image tokens)
    inputs = processor(text=[prompt_str], images=[image], return_tensors="pt")
    if torch.cuda.is_available():
        inputs = {k: v.to(model.device) for k, v in inputs.items()}
        # Keep pixel_values in BF16 on GPU
        inputs["pixel_values"] = inputs["pixel_values"].to(torch.bfloat16)

    # Generate
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

    # Trim the prompt portion and decode
    gen_ids = gen_ids[inputs["input_ids"].shape[1]:]
    text = processor.tokenizer.decode(
        gen_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False
    ).strip()

    return text
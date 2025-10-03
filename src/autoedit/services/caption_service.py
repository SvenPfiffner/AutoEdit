from PIL import Image
import io
import torch
from transformers import AutoProcessor, LlavaForConditionalGeneration

MODEL_NAME = "fancyfeast/llama-joycaption-beta-one-hf-llava"

from autoedit.services.prompts import JOYCAPTION_PROMPT

# Global singleton instances to avoid reloading models
_model = None
_processor = None

def _get_model_and_processor():
    """Load model and processor once, then reuse them.
    
    Uses CPU offloading to keep VRAM usage low (~2-4GB for this model).
    The model layers are kept in RAM and moved to GPU on-demand during inference.
    """
    global _model, _processor
    
    if _model is None or _processor is None:
        print(f"Loading JoyCaption model ({MODEL_NAME}) with CPU offloading...")
        _processor = AutoProcessor.from_pretrained(MODEL_NAME)
        
        # Strategy for CPU offloading to minimize VRAM:
        # 1. Load model entirely on CPU first
        # 2. Only vision components stay on GPU permanently
        # 3. Language model runs on CPU (slower but saves ~15GB VRAM)
        
        if torch.cuda.is_available():
            dtype = torch.bfloat16
            # Load on CPU first, then selectively move components
            print("  - Loading model on CPU first...")
            _model = LlavaForConditionalGeneration.from_pretrained(
                MODEL_NAME,
                torch_dtype=dtype,
                device_map="cpu",  # Start on CPU
                low_cpu_mem_usage=True,
            ).eval()
            
            # Move only vision tower to GPU (saves most VRAM)
            print("  - Moving vision tower to GPU...")
            if hasattr(_model, 'vision_tower'):
                _model.vision_tower = _model.vision_tower.to("cuda:0")
            elif hasattr(_model.model, 'vision_tower'):
                _model.model.vision_tower = _model.model.vision_tower.to("cuda:0")
            
            # Move multi-modal projector to GPU (small, ~100MB)
            if hasattr(_model, 'multi_modal_projector'):
                _model.multi_modal_projector = _model.multi_modal_projector.to("cuda:0")
            elif hasattr(_model.model, 'multi_modal_projector'):
                _model.model.multi_modal_projector = _model.model.multi_modal_projector.to("cuda:0")
            
            print("  ✓ Vision components on GPU (~2-3GB VRAM)")
            print("  ✓ Language model on CPU (saves ~15GB VRAM)")
            print("  → Total VRAM for captioning: ~2-4GB")
        else:
            dtype = torch.float32
            _model = LlavaForConditionalGeneration.from_pretrained(
                MODEL_NAME,
                torch_dtype=dtype,
                device_map="cpu",
                low_cpu_mem_usage=True,
            ).eval()
            print("  - Model loaded on CPU (no GPU available)")
    
    return _model, _processor

def generate_caption(image_bytes: bytes, prompt: str) -> str:

    # Get cached model + processor
    model, processor = _get_model_and_processor()

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
    
    # With CPU offloading, inputs need careful device placement:
    # - Vision tower on GPU processes pixel_values
    # - Language model on CPU processes text tokens
    # PyTorch will handle cross-device communication automatically
    if torch.cuda.is_available():
        # pixel_values go to GPU for vision tower
        inputs["pixel_values"] = inputs["pixel_values"].to("cuda:0", dtype=torch.bfloat16)
        # Keep text inputs on CPU where the language model lives
        # This avoids unnecessary CPU<->GPU transfers
    else:
        # CPU-only mode
        inputs["pixel_values"] = inputs["pixel_values"].to(torch.float32)

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
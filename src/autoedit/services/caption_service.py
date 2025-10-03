from transformers import pipeline

from services.prompts import JOYCAPTION_PROMPT

def generate_caption(image_bytes: bytes, prompt: str) -> str:
    """
    Generate a caption for the given image using a pre-trained model.
    """

    if not image_bytes:
        return ""
    
    pipe = pipeline("image-text-to-text", model="fancyfeast/llama-joycaption-beta-one-hf-llava")
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "url": "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/p-blog/candy.JPG"},
                {"type": "text", "text": "What animal is on the candy?"}
            ]
        },
    ]
    pipe(text=messages)
    print(pipe)  # for debugging
    return "an animal"  # replace with actual caption from model inference
def generate_caption(image_bytes: bytes) -> str:
    """
    Generate a caption for the given image using a pre-trained model.
    """

    if not image_bytes:
        return ""
    
    return "This will be the image caption"
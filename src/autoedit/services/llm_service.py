def craft_edit_prompt(user_prompt: str, caption: str) -> str:
    base_instruction = (
            "You are QWEN-Image-Edit. Preserve key elements from the source "
            "image while applying the requested adjustments."
    )
    contextual_caption = f"Context: {caption}" if caption else "Context: Unavailable."
    user_direction = (
        f"User brief: {user_prompt.strip()}" if user_prompt.strip() else "User brief: No additional guidance provided."
    )
    return " \n".join((base_instruction, contextual_caption, user_direction))
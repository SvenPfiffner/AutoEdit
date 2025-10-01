"""Streamlit entry point for the AutoEdit prototype.

This module wires together the UI layout with the placeholder
image-processing service. The UI is intentionally kept light and modular so
that future backend enhancements can reuse the same layout code without
modification.
"""

from __future__ import annotations

from typing import Optional

import streamlit as st

from autoedit.services.image_processor import ImageProcessor
from autoedit.ui import layout


def run() -> None:
    """Configure the Streamlit page and render the full experience."""
    st.set_page_config(
        page_title="AutoEdit Studio",
        page_icon="✨",
        layout="wide",
        menu_items={
            "Get Help": "https://docs.streamlit.io/",
            "Report a bug": "https://github.com/",
        },
    )

    layout.apply_global_styles()
    layout.render_header()
    with st.container():
        user_prompt, uploaded_image = layout.render_input_panel()
        if layout.user_requested_processing():
            processed_image = _process_image(user_prompt, uploaded_image)
            layout.render_output_panel(processed_image)

    layout.render_footer()


def _process_image(prompt: str, image_data: Optional[bytes]) -> Optional[bytes]:
    """Delegate to the processing service while gracefully handling errors.

    Parameters
    ----------
    prompt:
        The textual instructions provided by the user.
    image_data:
        Raw byte representation of the user supplied image.
    """
    if not image_data:
        st.info("Please upload an image to begin processing.")
        return None

    with st.spinner("Rendering your concept..."):
        processor = ImageProcessor()
        return processor.process(prompt=prompt, image_bytes=image_data)


if __name__ == "__main__":
    run()

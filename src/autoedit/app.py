"""Streamlit entry point for the AutoEdit prototype.

This module wires together the UI layout with the placeholder
image-processing service. The UI is intentionally kept light and modular so
that future backend enhancements can reuse the same layout code without
modification.
"""

from __future__ import annotations

from typing import List, Optional

import streamlit as st

from autoedit.services.image_processor import ImageProcessor, ProcessResult
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
    latest_result: Optional[ProcessResult] = st.session_state.get("latest_result")
    with st.container():
        user_prompt, uploaded_image = layout.render_input_panel()
        process_requested = layout.user_requested_processing()

        if process_requested:
            processed_result = _process_image(user_prompt, uploaded_image)
            if processed_result:
                st.session_state["latest_result"] = processed_result
                latest_result = processed_result

        if latest_result:
            layout.render_output_panel(latest_result)

    sidebar_history: List[ProcessResult] = (
        st.session_state.get("edit_history", [])[1:]
        if st.session_state.get("edit_history")
        else []
    )
    layout.render_history_sidebar(sidebar_history)

    layout.render_footer()



def _process_image(prompt: str, image_data: Optional[bytes]) -> Optional[ProcessResult]:
    """Execute the staged editing workflow and manage UI side effects.

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

    steps = [
        "Loading JoyCaption into VRAM",
        "Extracting Edit Instructions",
        "Loading QWEN-Image-Edit into VRAM",
        "Applying QWEN-Image-Edit",
    ]
    statuses = ["pending"] * len(steps)
    progress_placeholder = st.empty()
    current_step = {"index": 0}

    layout.render_workflow_progress(
        placeholder=progress_placeholder,
        steps=steps,
        statuses=statuses,
        detail_text="Initializing editing workflow...",
    )

    def update_progress(step_index: int, status: str, message: str) -> None:
        current_step["index"] = step_index
        if status == "active":
            statuses[step_index] = "active"
            for idx in range(step_index):
                if statuses[idx] != "complete":
                    statuses[idx] = "complete"
        elif status == "complete":
            statuses[step_index] = "complete"
            if step_index + 1 < len(statuses) and statuses[step_index + 1] == "pending":
                statuses[step_index + 1] = "active"
        elif status == "error":
            statuses[step_index] = "error"

        layout.render_workflow_progress(
            placeholder=progress_placeholder,
            steps=steps,
            statuses=statuses,
            detail_text=message,
        )

    processor = ImageProcessor()

    try:
        result = processor.process(
            prompt=prompt,
            image_bytes=image_data,
            progress_callback=update_progress,
        )
    except Exception as exc:  # pragma: no cover - defensive UX handling
        update_progress(current_step['index'], "error", "Processing failed. Please try again.")
        st.error(f"Something went wrong while editing the image: {exc}")
        return None

    if not result.final_image:
        st.warning("The editing pipeline completed without returning an image.")
        return None

    history: List[ProcessResult] = st.session_state.setdefault("edit_history", [])
    history.insert(0, result)
    if len(history) > 6:
        del history[6:]

    layout.render_workflow_progress(
        placeholder=progress_placeholder,
        steps=steps,
        statuses=["complete"] * len(steps),
        detail_text="Workflow complete.",
    )

    return result


if __name__ == "__main__":
    run()

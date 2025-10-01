"""Streamlit entry point for the AutoEdit prototype.

This module wires together the UI layout with the placeholder
image-processing service. The UI is intentionally kept light and modular so
that future backend enhancements can reuse the same layout code without
modification.
"""

from __future__ import annotations


from textwrap import shorten
from typing import List, Optional
from typing import Any, Dict, List, Optional


import streamlit as st
from time import perf_counter

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
    with st.container():
        user_prompt, uploaded_image, generation_options = layout.render_input_panel()
        if layout.user_requested_processing():
            processed_result = _process_image(user_prompt, uploaded_image, generation_options)
            if processed_result:
                history: List[ProcessResult] = (
                    st.session_state.get("edit_history", [])[1:]
                    if st.session_state.get("edit_history")
                    else []
                )
                layout.render_output_panel(processed_result, history)

    layout.render_footer()



def _process_image(
    prompt: str,
    image_data: Optional[bytes],
    options: Optional[Dict[str, Any]],
) -> Optional[ProcessResult]:
    """Execute the staged editing workflow and manage UI side effects.

    Parameters
    ----------
    prompt:
        The textual instructions provided by the user.
    image_data:
        Raw byte representation of the user supplied image.
    options:
        Structured generation preferences collected from the form.
    """

    if not image_data:
        st.info("Please upload an image to begin processing.")
        return None

    steps = [
        "Captioning with JoyCaption",
        "Planning edits",
        "Applying QWEN-Image-Edit",
    ]
    statuses = ["pending"] * len(steps)
    progress_placeholder = st.empty()
    current_step = {"index": 0}

    option_summary_parts = []
    if options:
        if options.get("aspect_ratio"):
            option_summary_parts.append(f"Aspect: {options['aspect_ratio']}")
        styles = options.get("style_mood") or []
        if styles:
            option_summary_parts.append("Style: " + ", ".join(styles))
        quality_flags = [
            label.replace("_", " ").title()
            for label, enabled in (options.get("quality") or {}).items()
            if enabled
        ]
        if quality_flags:
            option_summary_parts.append("Quality: " + ", ".join(quality_flags))
    summary_text = (
        " · ".join(option_summary_parts + ["Initializing editing workflow..."])
        if option_summary_parts
        else "Initializing editing workflow..."
    )

    layout.render_workflow_progress(
        placeholder=progress_placeholder,
        steps=steps,
        statuses=statuses,

        detail_text="Preparing the workflow. We'll begin in a moment.",
    )

    active_messages = [
        "Generating a caption for the upload.",
        "Drafting the edit instructions.",
        "Applying visual refinements.",
    ]
    complete_messages = [
        "Caption captured. Next up: plan the edits.",
        "Edit plan ready. Applying the changes now.",
        "Preview refreshed with the requested look.",
    ]

    def summarize_detail(step_index: int, status: str, fallback: str) -> str:
        total_steps = len(steps)
        safe_index = max(0, min(step_index, total_steps - 1))
        step_name = steps[safe_index] if steps else "Step"
        prefix = f"Step {safe_index + 1} of {total_steps}: " if total_steps else ""
        trimmed_fallback = shorten(fallback, width=120, placeholder="…") if fallback else ""

        if status == "active":
            message = (
                active_messages[safe_index]
                if safe_index < len(active_messages)
                else f"{step_name} in progress."
            )
            return prefix + message

        if status == "complete":
            message = (
                complete_messages[safe_index]
                if safe_index < len(complete_messages)
                else f"{step_name} complete."
            )
            return prefix + message

        if status == "error":
            return prefix + "We hit a snag. Please review this step."

        if status == "pending":
            return prefix + "Waiting to start."

        if trimmed_fallback:
            return prefix + trimmed_fallback

        return prefix + "Working on the next step."

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
            detail_text=summarize_detail(step_index, status, message),
        )

    processor = ImageProcessor()

    try:
        start_time = perf_counter()
        result = processor.process(
            prompt=prompt,
            image_bytes=image_data,
            progress_callback=update_progress,
            options=options or {},
        )
        result.duration_seconds = perf_counter() - start_time
    except Exception as exc:  # pragma: no cover - defensive UX handling
        update_progress(
            current_step["index"],
            "error",
            "Processing failed. Please try again.",
        )
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
        detail_text="Workflow complete. Review the refreshed image.",
    )

    return result


if __name__ == "__main__":
    run()

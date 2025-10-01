"""Composable Streamlit layout elements.

The functions defined here encapsulate the presentation logic for the
application. Splitting the UI across smaller helpers keeps the Streamlit app
readable and allows for individual sections to evolve independently.
"""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

import html

import streamlit as st
from streamlit.delta_generator import DeltaGenerator


from autoedit.services.image_processor import ProcessResult, WorkflowStepResult


_PROCESS_BUTTON_KEY = "process_image_button"


def apply_global_styles() -> None:
    """Inject custom CSS to produce a polished, product-ready UI."""
    st.markdown(
        """
        <style>
            :root {
                --autoedit-primary: #0B84F3;
                --autoedit-secondary: #0C1A2A;
                --autoedit-background: #F5F7FB;
                --autoedit-card: #FFFFFF;
            }

            .block-container {
                padding-top: 3rem;
                padding-bottom: 5rem;
                max-width: 1080px;
            }

            .hero {
                background: linear-gradient(135deg, rgba(11, 132, 243, 0.12), rgba(11, 132, 243, 0.02));
                border-radius: 24px;
                padding: 3.5rem;
                box-shadow: 0 24px 60px rgba(12, 26, 42, 0.1);
                margin-bottom: 3rem;
            }

            .hero__badge {
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                font-weight: 600;
                font-size: 0.85rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                background: rgba(11, 132, 243, 0.12);
                color: var(--autoedit-primary);
                border-radius: 999px;
                padding: 0.5rem 1.25rem;
            }

            .hero__title {
                font-size: 2.7rem;
                font-weight: 700;
                color: var(--autoedit-secondary);
                margin: 1.5rem 0 1rem;
            }

            .hero__subtitle {
                font-size: 1.1rem;
                line-height: 1.8;
                color: rgba(12, 26, 42, 0.72);
                max-width: 48rem;
            }

            .result-card {
                background: var(--autoedit-card);
                border-radius: 20px;
                padding: 2rem;
                box-shadow: 0 18px 40px rgba(12, 26, 42, 0.08);
            }

            .result-card h3 {
                margin-top: 0;
                font-weight: 700;
                color: var(--autoedit-secondary);
            }

            .result-card ul {
                padding-left: 1.2rem;
                color: rgba(12, 26, 42, 0.72);
                line-height: 1.7;
            }

            .result-card--metadata {
                display: flex;
                flex-direction: column;
                gap: 1.25rem;
            }

            .result-card__item {
                display: flex;
                flex-direction: column;
                gap: 0.4rem;
            }

            .result-card__label {
                font-size: 0.9rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.06em;
                color: rgba(12, 26, 42, 0.58);
            }

            .workflow-progress {
                margin: 2rem 0 3rem;
                background: var(--autoedit-card);
                border-radius: 24px;
                padding: 1.75rem 2rem;
                box-shadow: 0 24px 54px rgba(12, 26, 42, 0.12);
            }

            .workflow-progress__detail {
                font-weight: 600;
                color: var(--autoedit-secondary);
                margin-bottom: 1.25rem;
            }

            .workflow-progress__steps {
                display: flex;
                align-items: center;
                gap: 1.5rem;
            }

            .workflow-progress__step {
                flex: 1;
                text-align: center;
                position: relative;
                padding: 0 0.5rem;
            }

            .workflow-progress__step::after {
                content: "";
                position: absolute;
                top: 1.45rem;
                right: -0.75rem;
                width: calc(100% - 1.5rem);
                height: 3px;
                background: rgba(12, 26, 42, 0.12);
            }

            .workflow-progress__step:last-child::after {
                display: none;
            }

            .workflow-progress__index {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 2.2rem;
                height: 2.2rem;
                border-radius: 999px;
                font-weight: 700;
                margin: 0 auto 0.75rem;
                background: rgba(11, 132, 243, 0.12);
                color: var(--autoedit-primary);
            }

            .workflow-progress__label {
                font-size: 0.95rem;
                color: rgba(12, 26, 42, 0.78);
                line-height: 1.4;
            }

            .workflow-progress__step--complete .workflow-progress__index {
                background: var(--autoedit-primary);
                color: white;
                box-shadow: 0 12px 20px rgba(11, 132, 243, 0.25);
            }

            .workflow-progress__step--complete::after {
                background: rgba(11, 132, 243, 0.45);
            }

            .workflow-progress__step--active .workflow-progress__index {
                background: rgba(11, 132, 243, 0.2);
                color: var(--autoedit-primary);
                border: 2px solid rgba(11, 132, 243, 0.65);
            }

            .workflow-progress__step--active::after {
                background: rgba(11, 132, 243, 0.3);
            }

            .workflow-progress__step--error .workflow-progress__index {
                background: rgba(209, 67, 67, 0.18);
                color: #d14343;
            }

            .workflow-progress__step--error::after {
                background: rgba(209, 67, 67, 0.4);
            }

            .history-gallery {
                margin-top: 2.5rem;
            }

            .history-gallery__grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                gap: 1.5rem;
            }

            .history-card {
                background: var(--autoedit-card);
                border-radius: 18px;
                padding: 1rem;
                box-shadow: 0 12px 30px rgba(12, 26, 42, 0.08);
                display: flex;
                flex-direction: column;
                gap: 0.75rem;
            }

            .history-card__image {
                border-radius: 12px;
                overflow: hidden;
            }

            .history-card__meta {
                font-size: 0.85rem;
                color: rgba(12, 26, 42, 0.7);
                line-height: 1.5;
            }

            .history-card__timestamp {
                font-size: 0.75rem;
                letter-spacing: 0.05em;
                text-transform: uppercase;
                color: rgba(12, 26, 42, 0.45);
            }

            .footer {
                margin-top: 4rem;
                padding-top: 1.5rem;
                border-top: 1px solid rgba(12, 26, 42, 0.08);
                display: flex;
                flex-wrap: wrap;
                justify-content: space-between;
                gap: 1rem;
                color: rgba(12, 26, 42, 0.55);
                font-size: 0.9rem;
            }

            .footer a {
                color: var(--autoedit-primary);
                text-decoration: none;
                font-weight: 600;
            }

            .stButton > button {
                border-radius: 999px;
                font-weight: 600;
                letter-spacing: 0.02em;
                padding: 0.85rem 1.8rem;
            }

            .stTextArea textarea {
                border-radius: 20px;
                box-shadow: inset 0 0 0 1px rgba(11, 132, 243, 0.08);
            }

            .stFileUploader > div > div {
                border-radius: 20px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    """Render the hero section containing branding and onboarding text."""
    st.markdown(
        """
        <div class="hero">
            <div class="hero__badge">AutoEdit Studio</div>
            <h1 class="hero__title">Create standout visuals with tailored guidance</h1>
            <p class="hero__subtitle">
                Upload an inspiration image, describe the transformation you envision,
                and let AutoEdit craft the next iteration. This prototype currently
                echoes your original upload, paving the way for future intelligent
                enhancements.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_input_panel() -> Tuple[str, Optional[bytes]]:
    """Display the prompt input and image upload widgets."""
    with st.form(key="autoedit-input-form", clear_on_submit=False):
        cols = st.columns((3, 2), gap="large")
        with cols[0]:
            prompt = st.text_area(
                "Creative Brief",
                placeholder="Describe the aesthetic, tone, or changes you'd like to explore...",
                help="Be as descriptive as you like—mention mood, color palettes, or artistic influences.",
                max_chars=800,
            )
        with cols[1]:
            uploaded_file = st.file_uploader(
                "Reference Visual",
                type=["png", "jpg", "jpeg", "webp"],
                help="High-quality PNG or JPEG works best. We'll handle the rest.",
            )

            if uploaded_file is not None:
                st.image(uploaded_file, caption="Uploaded reference", use_column_width=True)
                image_bytes = uploaded_file.getvalue()
            else:
                image_bytes = None

        submit_pressed = st.form_submit_button(
            "Render Concept",
            use_container_width=True,
            type="primary",
            on_click=lambda: None,
            help="Generate a refined visual concept using your prompt and reference.",
        )
        st.session_state[_PROCESS_BUTTON_KEY] = submit_pressed

    return prompt, image_bytes


def user_requested_processing() -> bool:
    """Check whether the user triggered the processing flow in the last submit."""
    return st.session_state.get(_PROCESS_BUTTON_KEY, False)




def render_workflow_progress(
    placeholder: DeltaGenerator,
    steps: Sequence[str],
    statuses: Sequence[str],
    detail_text: str,
) -> None:
    """Render a professional looking progress indicator for the workflow."""

    allowed_statuses = {"pending", "active", "complete", "error"}

    status_classes: List[str] = []
    for status in list(statuses)[: len(steps)]:
        if status not in allowed_statuses:
            status = "pending"
        status_classes.append(status)

    if len(status_classes) < len(steps):
        status_classes.extend(["pending"] * (len(steps) - len(status_classes)))

    step_markup: List[str] = []
    for index, (label, status) in enumerate(zip(steps, status_classes), start=1):
        safe_label = html.escape(label)
        step_markup.append(
            (
                f'<div class="workflow-progress__step workflow-progress__step--{status}">'
                f'<div class="workflow-progress__index">{index}</div>'
                f'<div class="workflow-progress__label">{safe_label}</div>'
                '</div>'
            )
        )

    placeholder.markdown(
        (
            "<div class=\"workflow-progress\">"
            f"<div class=\"workflow-progress__detail\">{html.escape(detail_text)}</div>"
            f"<div class=\"workflow-progress__steps\">{''.join(step_markup)}</div>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def render_output_panel(result: ProcessResult, history: Sequence[ProcessResult]) -> None:
    """Show the processed image results alongside workflow insights."""

    st.divider()
    st.markdown("## Rendered Concept")

    if not result or not result.final_image:
        st.info("Upload an image and craft a prompt to see your results here.")
        return

    cols = st.columns((3, 2), gap="large")
    with cols[0]:
        st.image(result.final_image, caption="Edited visual", use_column_width=True)

    user_brief = html.escape(result.user_prompt or "No brief provided.")
    caption_text = html.escape(result.caption or "No caption generated.")
    refined_prompt = html.escape(result.refined_prompt or "No refined prompt available.")

    metadata_html = f"""
        <div class="result-card result-card--metadata">
            <h3>Workflow Summary</h3>
            <div class="result-card__item">
                <span class="result-card__label">User brief</span>
                <p>{user_brief}</p>
            </div>
            <div class="result-card__item">
                <span class="result-card__label">JoyCaption insight</span>
                <p>{caption_text}</p>
            </div>
            <div class="result-card__item">
                <span class="result-card__label">Refined edit prompt</span>
                <p>{refined_prompt}</p>
            </div>
        </div>
    """

    with cols[1]:
        st.markdown(metadata_html, unsafe_allow_html=True)

    step_items: List[str] = []
    for step in result.steps:
        detail = html.escape(step.detail or "")
        if not detail:
            continue
        step_items.append(
            f"<li><strong>{html.escape(step.name)}:</strong> {detail}</li>"
        )

    if step_items:
        st.markdown(
            """
            <div class="result-card">
                <h3>Pipeline Details</h3>
                <ul>{items}</ul>
            </div>
            """.format(items="".join(step_items)),
            unsafe_allow_html=True,
        )

    render_past_edits(history)



def render_past_edits(history: Sequence[ProcessResult]) -> None:
    """Display a panel of previous image edits if available."""

    if not history:
        return

    entries = []
    for previous in history[:6]:
        if not previous.final_image:
            continue
        timestamp = previous.created_at.strftime("%b %d, %Y %H:%M")
        prompt_summary = (previous.refined_prompt or "").strip() or "No refined prompt provided."
        entries.append(
            (
                previous.final_image,
                html.escape(prompt_summary),
                html.escape(timestamp),
            )
        )

    if not entries:
        st.info("Past edits will appear here once available.")
        return

    st.markdown("### Past Edits")
    st.markdown('<div class="history-gallery">', unsafe_allow_html=True)
    cols = st.columns(min(3, len(entries)))

    for idx, (image, prompt_text, timestamp) in enumerate(entries):
        column = cols[idx % len(cols)]
        with column:
            st.markdown('<div class="history-card">', unsafe_allow_html=True)
            st.image(image, use_column_width=True)
            st.markdown(
                """
                <div class="history-card__meta">{prompt}</div>
                <div class="history-card__timestamp">{timestamp}</div>
                </div>
                """.format(prompt=prompt_text, timestamp=timestamp),
                unsafe_allow_html=True,
            )
    st.markdown('</div>', unsafe_allow_html=True)


def render_footer() -> None:
    """Display a minimal footer with product messaging."""
    st.markdown(
        """
        <footer class="footer">
            <span>© AutoEdit Studio — Crafted for creative professionals.</span>
            <a href="mailto:hello@autoedit.app">Contact</a>
        </footer>
        """,
        unsafe_allow_html=True,
    )

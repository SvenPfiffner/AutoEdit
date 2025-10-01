"""Composable Streamlit layout elements.

The functions defined here encapsulate the presentation logic for the
application. Splitting the UI across smaller helpers keeps the Streamlit app
readable and allows for individual sections to evolve independently.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

import base64
import html
import imghdr
from textwrap import shorten

import streamlit as st
from streamlit.delta_generator import DeltaGenerator


from autoedit.services.image_processor import ProcessResult, WorkflowStepResult


_PROCESS_BUTTON_STATE_KEY = "process_image_requested"


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

            body {
                background: var(--autoedit-background);
            }

            .block-container {
                padding-top: 2.5rem;
                padding-bottom: 3.5rem;
                max-width: 1180px;
            }

            .hero {
                background: linear-gradient(135deg, rgba(11, 132, 243, 0.12), rgba(11, 132, 243, 0.02));
                border-radius: 24px;
                padding: 2.75rem 3rem;
                box-shadow: 0 24px 60px rgba(12, 26, 42, 0.08);
                margin-bottom: 2.5rem;
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

            .result-card--pipeline {
                margin-top: 1.5rem;
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

            .visually-hidden {
                position: absolute !important;
                width: 1px;
                height: 1px;
                padding: 0;
                margin: -1px;
                overflow: hidden;
                clip: rect(0, 0, 0, 0);
                white-space: nowrap;
                border: 0;
            }

            .workflow-progress {
                margin: 1.5rem 0 2.5rem;
                background: var(--autoedit-card);
                border-radius: 24px;
                padding: 1.5rem 2rem;
                box-shadow: 0 24px 54px rgba(12, 26, 42, 0.12);
            }

            .workflow-progress__detail {
                font-weight: 600;
                color: var(--autoedit-secondary);
                margin-bottom: 1rem;
            }

            .workflow-progress__steps {
                display: flex;
                align-items: stretch;
                gap: 1.25rem;
                list-style: none;
                padding: 0;
                margin: 0;
            }

            .workflow-progress__step {
                flex: 1;
                text-align: center;
                position: relative;
                padding: 0 0.5rem 0.75rem;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: flex-start;
                gap: 0.7rem;
                min-height: 140px;
                border-radius: 18px;
                cursor: default;
                transition: box-shadow 0.2s ease;
            }

            .workflow-progress__step:focus-visible {
                outline: 3px solid rgba(11, 132, 243, 0.8);
                outline-offset: 4px;
            }

            .workflow-progress__step::before,
            .workflow-progress__step::after {
                content: "";
                position: absolute;
                top: 1.1rem;
                width: 50%;
                height: 3px;
                background: rgba(12, 26, 42, 0.12);
                z-index: 0;
            }

            .workflow-progress__step::before {
                left: 0;
                transform: translateX(-50%);
            }

            .workflow-progress__step::after {
                right: 0;
                transform: translateX(50%);
            }

            .workflow-progress__step:first-child::before,
            .workflow-progress__step:last-child::after {
                display: none;
            }

            .workflow-progress__index {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 2.4rem;
                height: 2.4rem;
                border-radius: 999px;
                font-weight: 700;
                margin: 0;
                background: rgba(11, 132, 243, 0.12);
                color: var(--autoedit-primary);
                position: relative;
                z-index: 1;
            }

            .workflow-progress__label {
                font-size: 0.95rem;
                color: rgba(12, 26, 42, 0.78);
                line-height: 1.4;
            }

            .workflow-progress__status-badge {
                display: inline-flex;
                align-items: center;
                gap: 0.35rem;
                font-size: 0.85rem;
                color: rgba(12, 26, 42, 0.65);
                background: rgba(12, 26, 42, 0.05);
                border-radius: 999px;
                padding: 0.25rem 0.75rem;
                position: relative;
                z-index: 1;
            }

            .workflow-progress__status-icon {
                font-size: 0.95rem;
                line-height: 1;
            }

            .workflow-progress__status-text {
                font-weight: 600;
                letter-spacing: 0.01em;
            }

            .workflow-progress__step--complete .workflow-progress__index {
                background: var(--autoedit-primary);
                color: white;
                box-shadow: 0 12px 20px rgba(11, 132, 243, 0.25);
            }

            .workflow-progress__step--complete .workflow-progress__status-badge {
                background: rgba(11, 132, 243, 0.12);
                color: var(--autoedit-primary);
            }

            .workflow-progress__step--complete::after {
                background: rgba(11, 132, 243, 0.45);
            }

            .workflow-progress__step--complete + .workflow-progress__step::before {
                background: rgba(11, 132, 243, 0.45);
            }

            .workflow-progress__step--active .workflow-progress__index {
                background: rgba(11, 132, 243, 0.2);
                color: var(--autoedit-primary);
                border: 2px solid rgba(11, 132, 243, 0.65);
            }

            .workflow-progress__step--active .workflow-progress__status-badge {
                background: rgba(11, 132, 243, 0.16);
                color: var(--autoedit-primary);
            }

            .workflow-progress__step--active::after {
                background: rgba(11, 132, 243, 0.35);
            }

            .workflow-progress__step--active + .workflow-progress__step::before {
                background: rgba(11, 132, 243, 0.35);
            }

            .workflow-progress__step--error .workflow-progress__index {
                background: rgba(209, 67, 67, 0.18);
                color: #d14343;
            }

            .workflow-progress__step--error .workflow-progress__status-badge {
                background: rgba(209, 67, 67, 0.14);
                color: #b03838;
            }

            .workflow-progress__step--error::after {
                background: rgba(209, 67, 67, 0.4);
            }

            .workflow-progress__step--error + .workflow-progress__step::before {
                background: rgba(209, 67, 67, 0.4);
            }

            .history-panel {
                margin-top: 1.75rem;
                background: var(--autoedit-card);
                border-radius: 22px;
                padding: 1.25rem 1.35rem;
                box-shadow: 0 18px 40px rgba(12, 26, 42, 0.1);
                display: flex;
                flex-direction: column;
                gap: 1rem;
                max-height: 520px;
                overflow-y: auto;
            }

            .history-panel__title {
                display: flex;
                align-items: center;
                justify-content: space-between;
                font-weight: 600;
                color: var(--autoedit-secondary);
            }

            .history-panel__count {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                font-size: 0.75rem;
                font-weight: 600;
                letter-spacing: 0.06em;
                text-transform: uppercase;
                background: rgba(11, 132, 243, 0.12);
                color: var(--autoedit-primary);
                border-radius: 999px;
                padding: 0.1rem 0.65rem;
            }

            .history-panel__empty {
                font-size: 0.85rem;
                color: rgba(12, 26, 42, 0.55);
                line-height: 1.5;
            }

            .history-entry {
                display: flex;
                gap: 0.85rem;
                align-items: flex-start;
                background: rgba(11, 132, 243, 0.06);
                border: 1px solid rgba(11, 132, 243, 0.08);
                border-radius: 16px;
                padding: 0.75rem;
            }

            .history-entry__thumb {
                width: 72px;
                height: 72px;
                border-radius: 14px;
                overflow: hidden;
                flex-shrink: 0;
                background: rgba(12, 26, 42, 0.08);
            }

            .history-entry__thumb img {
                width: 100%;
                height: 100%;
                object-fit: cover;
                display: block;
            }

            .history-entry__content {
                flex: 1;
                display: flex;
                flex-direction: column;
                gap: 0.35rem;
            }

            .history-entry__meta {
                font-size: 0.75rem;
                letter-spacing: 0.05em;
                text-transform: uppercase;
                color: rgba(12, 26, 42, 0.45);
            }

            .history-entry__prompt {
                font-size: 0.85rem;
                line-height: 1.5;
                color: rgba(12, 26, 42, 0.78);
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

            @media (max-width: 1024px) {
                .workflow-progress {
                    padding: 1.35rem 1.25rem;
                }

                .workflow-progress__steps {
                    flex-direction: column;
                }

                .workflow-progress__step {
                    width: 100%;
                    min-height: auto;
                    align-items: flex-start;
                }

                .workflow-progress__step::before,
                .workflow-progress__step::after {
                    display: none;
                }

                .workflow-progress__index {
                    margin-bottom: 0.35rem;
                }

                .history-panel {
                    max-height: none;
                }
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


def render_input_panel() -> Tuple[str, Optional[bytes], Dict[str, Any]]:
    """Display the prompt form, helpers, and advanced configuration."""

    prompt_chips = [
        {
            "label": "Editorial portrait",
            "prompt": "Capture a moody editorial portrait with dramatic lighting and soft shadows.",
        },
        {
            "label": "Product hero",
            "prompt": "Design a clean product hero shot on a gradient backdrop with subtle reflections.",
        },
        {
            "label": "Concept art",
            "prompt": "Imagine a vibrant sci-fi cityscape at dusk with neon signage and dynamic lighting.",
        },
        {
            "label": "Social campaign",
            "prompt": "Create a playful social campaign visual with bold typography and energetic color blocking.",
        },
    ]

    sample_references = [
        {
            "name": "Neon streets",
            "url": "https://images.unsplash.com/photo-1508057198894-247b23fe5ade",
            "description": "Moody night photography ideal for cyberpunk moods.",
        },
        {
            "name": "Minimal studio",
            "url": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518",
            "description": "Neutral lighting setup for clean product iterations.",
        },
        {
            "name": "Organic textures",
            "url": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee",
            "description": "Natural materials inspiration with tactile finishes.",
        },
    ]

    advanced_defaults = {
        "aspect_ratio": "Square (1:1)",
        "style_mood": [],
        "quality": {
            "high_fidelity": True,
            "preserve_details": True,
            "enhance_depth": False,
        },
    }

    with st.form(key="autoedit_input_form"):
        cols = st.columns((3, 2), gap="large")

        with cols[0]:
            st.markdown("### Creative Direction")
            prompt = st.text_area(
                "Creative Brief",
                placeholder="Describe the aesthetic, tone, or changes you'd like to explore...",
                help="Be as descriptive as you like—mention mood, color palettes, or artistic influences.",
                max_chars=800,
                key="autoedit_creative_brief",
            )

            st.markdown("#### Quick start prompts")
            chip_columns = st.columns(len(prompt_chips))
            for column, chip in zip(chip_columns, prompt_chips):
                if column.form_submit_button(chip["label"], type="secondary"):
                    st.session_state["autoedit_creative_brief"] = chip["prompt"]
                    st.session_state[_PROCESS_BUTTON_STATE_KEY] = False

            st.markdown("#### Sample reference library")
            for reference in sample_references:
                st.markdown(
                    f"- [{reference['name']}]({reference['url']}) · {reference['description']}"
                )

        image_bytes: Optional[bytes] = None
        with cols[1]:
            st.markdown("### Reference & Output")
            uploaded_file = st.file_uploader(
                "Reference Visual",
                type=["png", "jpg", "jpeg", "webp"],
                help="High-quality PNG or JPEG works best. We'll handle the rest.",
                key="autoedit_reference_visual",
            )

            if uploaded_file is not None:
                image_bytes = uploaded_file.getvalue()
                st.image(image_bytes, caption="Uploaded reference", use_column_width=True)

            with st.expander("Advanced output", expanded=False):
                aspect_ratio = st.selectbox(
                    "Aspect ratio",
                    (
                        "Square (1:1)",
                        "Portrait (3:4)",
                        "Portrait (9:16)",
                        "Landscape (16:9)",
                        "Ultrawide (21:9)",
                    ),
                    index=0,
                    key="autoedit_aspect_ratio",
                    help="Choose how the final frame should be composed.",
                )

                style_mood = st.multiselect(
                    "Style or mood cues",
                    options=[
                        "Cinematic",
                        "Documentary",
                        "Playful",
                        "Conceptual",
                        "Editorial",
                        "Surreal",
                    ],
                    default=advanced_defaults["style_mood"],
                    key="autoedit_style_mood",
                    help="Select descriptors to influence the overall treatment.",
                )

                high_fidelity = st.checkbox(
                    "High fidelity rendering",
                    value=advanced_defaults["quality"]["high_fidelity"],
                    key="autoedit_high_fidelity",
                )
                preserve_details = st.checkbox(
                    "Preserve intricate details",
                    value=advanced_defaults["quality"]["preserve_details"],
                    key="autoedit_preserve_details",
                )
                enhance_depth = st.checkbox(
                    "Enhance depth and contrast",
                    value=advanced_defaults["quality"]["enhance_depth"],
                    key="autoedit_enhance_depth",
                )

        action_cols = st.columns((3, 2), gap="large")
        with action_cols[0]:
            submit_pressed = st.form_submit_button(
                "Render Concept",
                use_container_width=True,
                type="primary",
                help="Generate a refined visual concept using your prompt and reference.",
            )

        with action_cols[1]:
            st.caption("Processing may take a moment as the workflow runs each stage.")

    st.session_state[_PROCESS_BUTTON_STATE_KEY] = submit_pressed

    options: Dict[str, Any] = {
        "aspect_ratio": aspect_ratio,
        "style_mood": style_mood,
        "quality": {
            "high_fidelity": high_fidelity,
            "preserve_details": preserve_details,
            "enhance_depth": enhance_depth,
        },
    }

    return prompt, image_bytes, options


def user_requested_processing() -> bool:
    """Check whether the user triggered the processing flow in the last submit."""
    return st.session_state.get(_PROCESS_BUTTON_STATE_KEY, False)




def render_workflow_progress(
    placeholder: DeltaGenerator,
    steps: Sequence[str],
    statuses: Sequence[str],
    detail_text: str,
) -> None:
    """Render a professional looking progress indicator for the workflow."""

    allowed_statuses = {"pending", "active", "complete", "error"}
    status_metadata = {
        "pending": {"label": "Not started", "icon": "○"},
        "active": {"label": "In progress", "icon": "⏳"},
        "complete": {"label": "Complete", "icon": "✓"},
        "error": {"label": "Needs attention", "icon": "⚠"},
    }

    status_classes: List[str] = []
    for status in list(statuses)[: len(steps)]:
        if status not in allowed_statuses:
            status = "pending"
        status_classes.append(status)

    if len(status_classes) < len(steps):
        status_classes.extend(["pending"] * (len(steps) - len(status_classes)))

    step_markup: List[str] = []
    total_steps = len(steps)
    for index, (label, status) in enumerate(zip(steps, status_classes), start=1):
        safe_label = html.escape(label)
        status_info = status_metadata.get(status, status_metadata["pending"])
        safe_status = html.escape(status_info["label"])
        status_icon = html.escape(status_info["icon"])
        aria_label = html.escape(
            f"Step {index} of {total_steps}, {label} ({status_info['label']})"
        )
        aria_current_attr = ' aria-current="step"' if status == "active" else ""
        step_markup.append(
            (
                f'<li class="workflow-progress__step workflow-progress__step--{status}"'
                f' role="listitem" tabindex="0" aria-label="{aria_label}"{aria_current_attr}>'
                f'<div class="workflow-progress__index" aria-hidden="true">{index}</div>'
                f'<div class="workflow-progress__label">{safe_label}</div>'
                '<div class="workflow-progress__status-badge">'
                f'<span class="workflow-progress__status-icon" aria-hidden="true">{status_icon}</span>'
                f'<span class="workflow-progress__status-text">{safe_status}</span>'
                '</div>'
                '</li>'
            )
        )

    safe_detail = html.escape(detail_text)
    placeholder.markdown(
        (
            "<div class=\"workflow-progress\">"
            f"<div class=\"workflow-progress__detail\">{safe_detail}</div>"
            f"<div class=\"workflow-progress__live visually-hidden\" aria-live=\"polite\" aria-atomic=\"true\">{safe_detail}</div>"
            f"<ol class=\"workflow-progress__steps\" role=\"list\">{''.join(step_markup)}</ol>"
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

    main_col, side_col = st.columns((7, 5), gap="large")
    with main_col:
        st.image(result.final_image, caption="Edited visual", use_column_width=True)

    user_brief = html.escape(result.user_prompt or "No brief provided.")
    caption_text = html.escape(result.caption or "No caption generated.")
    refined_prompt = html.escape(result.refined_prompt or "No refined prompt available.")

    aspect_ratio = html.escape(result.options.get("aspect_ratio", "Not specified"))
    style_mood = ", ".join(result.options.get("style_mood", [])) or "Default mood"
    style_mood = html.escape(style_mood)
    quality_flags = [
        label.replace("_", " ").title()
        for label, enabled in (result.options.get("quality") or {}).items()
        if enabled
    ]
    quality_text = html.escape(", ".join(quality_flags) if quality_flags else "Standard output")

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
            <div class="result-card__item">
                <span class="result-card__label">Aspect ratio</span>
                <p>{aspect_ratio}</p>
            </div>
            <div class="result-card__item">
                <span class="result-card__label">Style direction</span>
                <p>{style_mood}</p>
            </div>
            <div class="result-card__item">
                <span class="result-card__label">Quality emphasis</span>
                <p>{quality_text}</p>
            </div>
        </div>
    """

    with side_col:
        side_col.markdown(metadata_html, unsafe_allow_html=True)

    step_items: List[str] = []
    for step in result.steps:
        detail = html.escape(step.detail or "")
        if not detail:
            continue
        step_items.append(
            f"<li><strong>{html.escape(step.name)}:</strong> {detail}</li>"
        )

    if step_items:
        main_col.markdown(
            """
            <div class="result-card result-card--pipeline">
                <h3>Pipeline Details</h3>
                <ul>{items}</ul>
            </div>
            """.format(items="".join(step_items)),
            unsafe_allow_html=True,
        )

    with side_col:
        render_past_edits(history, container=side_col)



def render_past_edits(
    history: Sequence[ProcessResult],
    *,
    container: Optional[DeltaGenerator] = None,
) -> None:
    """Display a panel of previous image edits if available."""

    target = container or st
    visible_history = list(history[:8])

    entries: List[str] = []
    for idx, previous in enumerate(visible_history, start=1):
        if not previous.final_image:
            continue

        timestamp_text = previous.created_at.strftime("%b %d, %Y · %H:%M")
        prompt_source = (
            previous.refined_prompt
            or previous.caption
            or previous.user_prompt
            or "No refined prompt provided."
        )
        normalized_prompt = " ".join(prompt_source.split()) or "No refined prompt provided."
        prompt_summary = shorten(normalized_prompt, width=140, placeholder="…")

        image_format = imghdr.what(None, h=previous.final_image) or "png"
        if image_format == "jpg":
            image_format = "jpeg"
        mime_type = f"image/{image_format}"

        encoded_image = base64.b64encode(previous.final_image).decode("utf-8")
        safe_prompt = html.escape(prompt_summary)
        safe_timestamp = html.escape(timestamp_text)

        entries.append(
            """
            <article class="history-entry">
                <div class="history-entry__thumb">
                    <img src="data:{mime};base64,{image}" alt="Past generation {index}" loading="lazy" />
                </div>
                <div class="history-entry__content">
                    <div class="history-entry__meta">Revision {index:02d} · {timestamp}</div>
                    <div class="history-entry__prompt">{prompt}</div>
                </div>
            </article>
            """.format(
                image=encoded_image,
                prompt=safe_prompt,
                mime=mime_type,
                timestamp=safe_timestamp,
                index=idx,
            )
        )

    if not entries:
        target.markdown(
            """
            <div class="history-panel">
                <div class="history-panel__title">Past Generations<span class="history-panel__count">0</span></div>
                <div class="history-panel__empty">Past edits will appear here once available.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    target.markdown(
        """
        <div class="history-panel">
            <div class="history-panel__title">Past Generations<span class="history-panel__count">{count}</span></div>
            {entries}
        </div>
        """.format(count=len(entries), entries="".join(entries)),
        unsafe_allow_html=True,
    )


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

"""Composable Streamlit layout elements.

The functions defined here encapsulate the presentation logic for the
application. Splitting the UI across smaller helpers keeps the Streamlit app
readable and allows for individual sections to evolve independently.
"""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

import base64
import html
import imghdr
from textwrap import shorten

import streamlit as st
from streamlit.delta_generator import DeltaGenerator


from autoedit.services.image_processor import ProcessResult, WorkflowStepResult


_PROCESS_BUTTON_KEY = "process_image_button"
_PROCESS_BUTTON_STATE_KEY = "process_image_requested"


def apply_global_styles() -> None:
    """Inject custom CSS to produce a polished, product-ready UI."""
    st.markdown(
        """
        <style>
            :root {
                --autoedit-primary: #0b84f3;
                --autoedit-secondary: #0c1a2a;
                --autoedit-background: #f4f6fb;
                --autoedit-card: #ffffff;
                --autoedit-muted: rgba(12, 26, 42, 0.58);
                --autoedit-border: rgba(12, 26, 42, 0.08);
                --autoedit-shadow: 0 26px 60px rgba(12, 26, 42, 0.10);
            }

            body {
                background: linear-gradient(180deg, rgba(10, 23, 43, 0.02) 0%, rgba(10, 23, 43, 0.08) 100%);
            }

            .block-container {
                padding-top: 2.5rem;
                padding-bottom: 3.5rem;
                max-width: 1220px;
            }

            .hero {
                position: relative;
                overflow: hidden;
                background: radial-gradient(circle at top right, rgba(11, 132, 243, 0.16), transparent 55%),
                            linear-gradient(135deg, rgba(11, 132, 243, 0.12), rgba(11, 132, 243, 0.02));
                border-radius: 28px;
                padding: 3rem 3.25rem;
                box-shadow: var(--autoedit-shadow);
                margin-bottom: 2.75rem;
            }

            .hero__badge {
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                font-weight: 600;
                font-size: 0.85rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                background: rgba(11, 132, 243, 0.14);
                color: var(--autoedit-primary);
                border-radius: 999px;
                padding: 0.45rem 1.35rem;
            }

            .hero__title {
                font-size: clamp(2.4rem, 2.9vw, 3rem);
                font-weight: 700;
                color: var(--autoedit-secondary);
                margin: 1.35rem 0 1rem;
            }

            .hero__subtitle {
                font-size: 1.1rem;
                line-height: 1.8;
                color: rgba(12, 26, 42, 0.72);
                max-width: 50rem;
            }

            .hero__meta {
                margin-top: 2rem;
                display: flex;
                flex-wrap: wrap;
                gap: 0.65rem;
            }

            .section-heading {
                display: flex;
                flex-direction: column;
                gap: 0.6rem;
                margin-bottom: 1.25rem;
            }

            .section-heading--dense {
                margin-bottom: 0.75rem;
            }

            .section-heading__eyebrow {
                font-size: 0.78rem;
                letter-spacing: 0.16em;
                text-transform: uppercase;
                font-weight: 700;
                color: var(--autoedit-primary);
            }

            .section-heading__title {
                font-size: 1.8rem;
                font-weight: 700;
                color: var(--autoedit-secondary);
            }

            .section-heading__subtitle {
                font-size: 1rem;
                color: rgba(12, 26, 42, 0.68);
                max-width: 48ch;
                line-height: 1.7;
            }

            .section-heading + div[data-testid="stHorizontalBlock"] > div[data-testid="column"] > div {
                background: var(--autoedit-card);
                border-radius: 26px;
                padding: 1.75rem 1.9rem;
                box-shadow: var(--autoedit-shadow);
                border: 1px solid rgba(11, 132, 243, 0.06);
                display: flex;
                flex-direction: column;
                gap: 1.3rem;
            }

            .section-heading.section-heading--dense + div[data-testid="stHorizontalBlock"] > div[data-testid="column"] > div {
                padding: 1.4rem 1.55rem;
            }

            .section-heading + div[data-testid="stHorizontalBlock"] > div[data-testid="column"] > div > div:has(.section-subheader) {
                gap: 1rem;
            }

            .section-subheader {
                font-size: 1.05rem;
                font-weight: 600;
                color: var(--autoedit-secondary);
                margin-bottom: -0.35rem;
            }

            .helper-text {
                font-size: 0.92rem;
                color: rgba(12, 26, 42, 0.6);
                line-height: 1.6;
            }

            .insight-card {
                display: flex;
                flex-direction: column;
                gap: 1rem;
            }

            .insight-card__item {
                background: rgba(11, 132, 243, 0.08);
                border: 1px solid rgba(11, 132, 243, 0.16);
                border-radius: 18px;
                padding: 1rem 1.2rem;
                display: flex;
                flex-direction: column;
                gap: 0.35rem;
            }

            .insight-card__item strong {
                color: var(--autoedit-secondary);
                font-size: 0.95rem;
            }

            .badge {
                display: inline-flex;
                align-items: center;
                gap: 0.4rem;
                border-radius: 999px;
                padding: 0.35rem 0.9rem;
                font-size: 0.75rem;
                font-weight: 600;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                background: rgba(11, 132, 243, 0.12);
                color: var(--autoedit-primary);
            }

            .result-card {
                background: var(--autoedit-card);
                border-radius: 24px;
                padding: 1.9rem 2rem;
                box-shadow: var(--autoedit-shadow);
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
                color: var(--autoedit-muted);
            }

            .workflow-progress {
                margin: 1.6rem 0 2.7rem;
                background: var(--autoedit-card);
                border-radius: 26px;
                padding: 1.6rem 2.1rem;
                box-shadow: var(--autoedit-shadow);
                border: 1px solid rgba(11, 132, 243, 0.06);
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
            }

            .workflow-progress__step {
                flex: 1;
                text-align: center;
                position: relative;
                padding: 0 0.5rem 0.5rem;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: flex-start;
                gap: 0.75rem;
                min-height: 130px;
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

            .workflow-progress__step--complete .workflow-progress__index {
                background: var(--autoedit-primary);
                color: white;
                box-shadow: 0 12px 20px rgba(11, 132, 243, 0.25);
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

            .workflow-progress__step--error::after {
                background: rgba(209, 67, 67, 0.4);
            }

            .workflow-progress__step--error + .workflow-progress__step::before {
                background: rgba(209, 67, 67, 0.4);
            }

            .history-panel {
                margin-top: 1.75rem;
                background: var(--autoedit-card);
                border-radius: 24px;
                padding: 1.35rem 1.45rem;
                box-shadow: var(--autoedit-shadow);
                display: flex;
                flex-direction: column;
                gap: 1rem;
                max-height: 520px;
                overflow-y: auto;
                border: 1px solid rgba(11, 132, 243, 0.05);
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
                border-radius: 16px;
                font-weight: 600;
                letter-spacing: 0.02em;
                padding: 0.85rem 1.6rem;
                box-shadow: 0 14px 24px rgba(11, 132, 243, 0.18);
            }

            .stButton > button:hover {
                transform: translateY(-1px);
            }

            .stTextArea textarea {
                border-radius: 18px;
                border: 1px solid rgba(11, 132, 243, 0.12);
                box-shadow: inset 0 0 0 1px rgba(11, 132, 243, 0.04);
            }

            .stFileUploader > div > div {
                border-radius: 18px;
                border: 1px dashed rgba(11, 132, 243, 0.35);
                background: rgba(11, 132, 243, 0.04);
            }

            .stCaption, .caption-text {
                color: rgba(12, 26, 42, 0.6) !important;
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

            .section-heading + div[data-testid="stHorizontalBlock"] .history-panel {
                margin-top: 0;
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
            <h1 class="hero__title">Design refined iterations with creative intelligence</h1>
            <p class="hero__subtitle">
                AutoEdit pairs your art direction with guided editing steps so every upload
                becomes a polished concept. Provide a reference visual and creative brief to
                explore production-ready variations with confidence.
            </p>
            <div class="hero__meta">
                <span class="badge">Guided workflow</span>
                <span class="badge">Reference aware</span>
                <span class="badge">Caption &amp; refine</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_input_panel() -> Tuple[str, Optional[bytes]]:
    """Display the prompt input and image upload widgets."""
    st.markdown(
        """
        <div class="section-heading">
            <span class="section-heading__eyebrow">New concept</span>
            <span class="section-heading__title">Set your creative direction</span>
            <p class="section-heading__subtitle">
                Pair a detailed brief with a reference image to guide AutoEdit's captioning,
                planning, and rendering workflow. Thoughtful prompts lead to the strongest iterations.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    submit_pressed = False
    image_bytes: Optional[bytes] = None

    cols = st.columns((7, 5), gap="large")

    with cols[0]:
        st.markdown('<div class="section-subheader">Creative brief</div>', unsafe_allow_html=True)
        prompt = st.text_area(
            label="Creative brief",
            placeholder="Describe the aesthetic, tone, or changes you'd like to explore...",
            help="Highlight mood, palette, composition, and any references to keep the system focused.",
            max_chars=800,
            key="autoedit_creative_brief",
            label_visibility="collapsed",
        )

        st.markdown('<div class="section-subheader">Reference visual</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Reference visual",
            type=["png", "jpg", "jpeg", "webp"],
            help="High-quality PNG or JPEG works best. We'll handle the rest.",
            key="autoedit_reference_visual",
            label_visibility="collapsed",
        )

        if uploaded_file is not None:
            image_bytes = uploaded_file.getvalue()
            st.image(image_bytes, caption="Uploaded reference", use_column_width=True)

        action_cols = st.columns((2.3, 1.7), gap="medium")
        with action_cols[0]:
            submit_pressed = st.button(
                "Render Concept",
                use_container_width=True,
                type="primary",
                help="Generate a refined visual concept using your prompt and reference.",
                key=_PROCESS_BUTTON_KEY,
            )

        with action_cols[1]:
            st.markdown(
                """
                <div class="insight-card__item" style="gap:0.25rem; background:rgba(11,132,243,0.05); border-style:dashed;">
                    <strong>Workflow tip</strong>
                    <span class="helper-text">Expect ~30s per render while captioning and planning complete.</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with cols[1]:
        st.markdown('<div class="section-subheader">Session guidance</div>', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="insight-card">
                <div class="insight-card__item">
                    <strong>Align intent &amp; visuals</strong>
                    <span class="helper-text">Summarize the story, subject, and finishing style so captioning stays precise.</span>
                </div>
                <div class="insight-card__item">
                    <strong>Call out constraints</strong>
                    <span class="helper-text">Mention what should remain unchanged—brand colors, layout anchors, or lighting.</span>
                </div>
                <div class="insight-card__item">
                    <strong>Plan multi-step edits</strong>
                    <span class="helper-text">AutoEdit sequences captioning, prompt refinement, and QWEN image edits for consistent results.</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="section-subheader">Need inspiration?</div>', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="insight-card__item">
                <span class="helper-text">Try contrasting palettes like “soft dusk pastels with metallic accents” or specify lens effects such as “35mm depth with gentle film grain.”</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.session_state[_PROCESS_BUTTON_STATE_KEY] = submit_pressed

    return prompt, image_bytes


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
    st.markdown(
        """
        <div class="section-heading section-heading--dense">
            <span class="section-heading__eyebrow">Results</span>
            <span class="section-heading__title">Rendered concept</span>
            <p class="section-heading__subtitle">Review the generated visual, workflow summary, and previous explorations.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not result or not result.final_image:
        st.info("Upload an image and craft a prompt to see your results here.")
        return

    main_col, side_col = st.columns((7, 5), gap="large")
    with main_col:
        st.markdown('<div class="section-subheader">Final render</div>', unsafe_allow_html=True)
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

    with side_col:
        side_col.markdown('<div class="section-subheader">Workflow summary</div>', unsafe_allow_html=True)
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
        side_col.markdown('<div class="section-subheader">Recent explorations</div>', unsafe_allow_html=True)
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
            '<article class="history-entry">'
            '<div class="history-entry__thumb">'
            '<img src="data:{mime};base64,{image}" alt="Past generation {index}" loading="lazy" />'
            '</div>'
            '<div class="history-entry__content">'
            '<div class="history-entry__meta">Revision {index:02d} · {timestamp}</div>'
            '<div class="history-entry__prompt">{prompt}</div>'
            '</div>'
            '</article>'.format(
                image=encoded_image,
                prompt=safe_prompt,
                mime=mime_type,
                timestamp=safe_timestamp,
                index=idx,
            )
        )

    if not entries:
        target.markdown(
            '<div class="history-panel">'
            '<div class="history-panel__title">Past Generations<span class="history-panel__count">0</span></div>'
            '<div class="history-panel__empty">Past edits will appear here once available.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    target.markdown(
        '<div class="history-panel">'
        '<div class="history-panel__title">Past Generations<span class="history-panel__count">{count}</span></div>'
        '{entries}'
        '</div>'.format(count=len(entries), entries="".join(entries)),
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

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
_HISTORY_SELECTION_WIDGET_KEY = "autoedit_history_selection"
_SELECTED_HISTORY_STATE_KEY = "selected_history_index"
_HISTORY_LAST_ACTIVATED_KEY = "history_last_hydrated"
_FAVORITE_STATE_KEY = "favorite_history_entries"
_COMPARISON_STATE_KEY = "comparison_view_state"
_ADVANCED_OPTIONS_STATE_KEY = "advanced_options_state"
_DUPLICATE_SOURCE_STATE_KEY = "duplicate_history_source"


def _history_entry_identifier(entry: ProcessResult, index: int) -> str:
    """Create a stable identifier for history-driven interactions."""

    return f"{entry.created_at.isoformat()}-{index:02d}"


def _get_favorites_state() -> set[str]:
    """Return the mutable container tracking favorited results."""

    favorites = st.session_state.get(_FAVORITE_STATE_KEY)
    if isinstance(favorites, set):
        return favorites
    if favorites is None:
        favorites = set()
    else:
        favorites = set(favorites)
    st.session_state[_FAVORITE_STATE_KEY] = favorites
    return favorites


def _hydrate_history_snapshot(snapshot: ProcessResult) -> None:
    """Populate key UI inputs based on a selected history snapshot."""

    st.session_state["autoedit_creative_brief"] = snapshot.user_prompt or ""
    advanced_state = dict(st.session_state.get(_ADVANCED_OPTIONS_STATE_KEY, {}))
    advanced_state.update(
        {
            "refined_prompt": snapshot.refined_prompt or "",
            "caption": snapshot.caption or "",
        }
    )
    st.session_state[_ADVANCED_OPTIONS_STATE_KEY] = advanced_state
    st.session_state[_COMPARISON_STATE_KEY] = {
        "prompt": snapshot.refined_prompt or snapshot.user_prompt or "",
        "caption": snapshot.caption or "",
        "image": snapshot.final_image,
        "created_at": snapshot.created_at.isoformat(),
    }


def _toggle_favorite(entry_id: str, snapshot: ProcessResult) -> bool:
    """Flip the favorite state for a history entry and persist the choice."""

    favorites = _get_favorites_state()
    if entry_id in favorites:
        favorites.remove(entry_id)
        snapshot.is_favorited = False
        return False

    favorites.add(entry_id)
    snapshot.is_favorited = True
    return True



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
                border-radius: 22px;
                padding: 1.5rem;
                box-shadow: 0 18px 40px rgba(12, 26, 42, 0.1);
                max-height: 520px;
                overflow-y: auto;
            }

            .history-panel--empty {
                display: flex;
                flex-direction: column;
                gap: 1rem;
            }

            .history-panel__header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 0.75rem;
                margin-bottom: 0.75rem;
            }

            .history-panel__header h2 {
                margin: 0;
                font-size: 1.05rem;
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
                margin: 0;
            }

            .history-panel .stRadio > div[role="radiogroup"] {
                display: flex;
                flex-direction: column;
                gap: 0.35rem;
                margin-bottom: 1rem;
            }

            .history-panel .stRadio label {
                font-size: 0.85rem;
                color: rgba(12, 26, 42, 0.65);
            }

            .history-panel .stRadio [role="radio"] {
                padding: 0.35rem 0.5rem;
                border-radius: 12px;
                border: 1px solid transparent;
            }

            .history-panel .stRadio [aria-checked="true"] {
                background: rgba(11, 132, 243, 0.08);
                border-color: rgba(11, 132, 243, 0.25);
                color: var(--autoedit-secondary);
            }

            .history-entry {
                display: flex;
                flex-direction: column;
                gap: 0.75rem;
                border-radius: 18px;
                border: 1px solid rgba(11, 132, 243, 0.12);
                padding: 1rem;
                background: rgba(11, 132, 243, 0.05);
                transition: box-shadow 0.2s ease, border-color 0.2s ease;
                margin-bottom: 1rem;
            }

            .history-entry[data-selected="true"] {
                border-color: rgba(11, 132, 243, 0.6);
                box-shadow: 0 16px 32px rgba(11, 132, 243, 0.18);
                background: rgba(11, 132, 243, 0.12);
            }

            .history-entry__body {
                display: flex;
                gap: 0.85rem;
                align-items: flex-start;
            }

            .history-entry__thumb {
                width: 72px;
                height: 72px;
                border-radius: 16px;
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
                gap: 0.5rem;
            }

            .history-entry__badges {
                display: flex;
                flex-wrap: wrap;
                align-items: center;
                gap: 0.4rem;
            }

            .history-entry__badge {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                font-size: 0.75rem;
                font-weight: 600;
                letter-spacing: 0.05em;
                text-transform: uppercase;
                border-radius: 999px;
                padding: 0.15rem 0.65rem;
            }

            .history-entry__badge--id {
                background: rgba(11, 132, 243, 0.16);
                color: var(--autoedit-primary);
            }

            .history-entry__badge--duration {
                background: rgba(12, 26, 42, 0.08);
                color: rgba(12, 26, 42, 0.7);
            }

            .history-entry__badge--favorite {
                background: #fce8b2;
                color: #8a5a00;
            }

            .history-entry__prompt {
                font-size: 0.88rem;
                line-height: 1.5;
                color: rgba(12, 26, 42, 0.82);
                margin: 0;
            }

            .history-entry__timestamp {
                font-size: 0.75rem;
                letter-spacing: 0.05em;
                text-transform: uppercase;
                color: rgba(12, 26, 42, 0.48);
            }

            .history-entry__actions {
                display: block;
            }

            .history-entry__actions .stColumn {
                padding: 0 !important;
            }

            .history-entry__actions .stButton > button,
            .history-entry__actions .stDownloadButton > button {
                width: 100%;
                border-radius: 12px;
                font-size: 0.85rem;
                padding: 0.55rem 0.75rem;
                background: #ffffff;
                border: 1px solid rgba(11, 132, 243, 0.18);
                color: var(--autoedit-secondary);
                transition: border-color 0.2s ease, box-shadow 0.2s ease;
            }

            .history-entry__actions .stColumn:first-child .stButton > button {
                background: rgba(11, 132, 243, 0.08);
            }

            .history-entry__actions .stButton > button:hover,
            .history-entry__actions .stDownloadButton > button:hover {
                border-color: rgba(11, 132, 243, 0.4);
                box-shadow: 0 8px 18px rgba(11, 132, 243, 0.15);
            }

            .stButton > button:focus-visible,
            .stDownloadButton > button:focus-visible,
            .history-panel .stRadio [role="radio"]:focus-visible {
                outline: 3px solid var(--autoedit-primary);
                outline-offset: 3px;
                box-shadow: 0 0 0 4px rgba(11, 132, 243, 0.25);
            }

            a:focus-visible {
                outline: 3px solid var(--autoedit-primary);
                outline-offset: 3px;
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


def render_input_panel() -> Tuple[str, Optional[bytes]]:
    """Display the prompt input and image upload widgets."""
    cols = st.columns((3, 2), gap="large")

    with cols[0]:
        prompt = st.text_area(
            "Creative Brief",
            placeholder="Describe the aesthetic, tone, or changes you'd like to explore...",
            help="Be as descriptive as you like—mention mood, color palettes, or artistic influences.",
            max_chars=800,
            key="autoedit_creative_brief",
        )

    image_bytes: Optional[bytes] = None
    with cols[1]:
        uploaded_file = st.file_uploader(
            "Reference Visual",
            type=["png", "jpg", "jpeg", "webp"],
            help="High-quality PNG or JPEG works best. We'll handle the rest.",
            key="autoedit_reference_visual",
        )

        if uploaded_file is not None:
            image_bytes = uploaded_file.getvalue()
            st.image(image_bytes, caption="Uploaded reference", use_column_width=True)

    action_cols = st.columns((3, 2), gap="large")
    with action_cols[0]:
        submit_pressed = st.button(
            "Render Concept",
            use_container_width=True,
            type="primary",
            help="Generate a refined visual concept using your prompt and reference.",
            key=_PROCESS_BUTTON_KEY,
        )

    with action_cols[1]:
        st.caption("Processing may take a moment as the workflow runs each stage.")

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
    visible_history = [entry for entry in history[:8] if entry.final_image]

    if not visible_history:
        target.markdown(
            """
            <section class="history-panel history-panel--empty" id="history-panel" aria-label="Past Generations">
                <header class="history-panel__header">
                    <h2>Past Generations</h2>
                    <span class="history-panel__count">0</span>
                </header>
                <p class="history-panel__empty">Past edits will appear here once available.</p>
            </section>
            """,
            unsafe_allow_html=True,
        )
        st.session_state.pop(_HISTORY_SELECTION_WIDGET_KEY, None)
        st.session_state.pop(_SELECTED_HISTORY_STATE_KEY, None)
        st.session_state.pop(_HISTORY_LAST_ACTIVATED_KEY, None)
        return

    favorites = _get_favorites_state()

    default_index = st.session_state.get(_HISTORY_SELECTION_WIDGET_KEY, 0)
    if default_index >= len(visible_history):
        default_index = 0
    if _HISTORY_SELECTION_WIDGET_KEY not in st.session_state:
        st.session_state[_HISTORY_SELECTION_WIDGET_KEY] = default_index

    panel = target.container()
    panel.markdown(
        """
        <section class="history-panel" id="history-panel" aria-label="Past Generations">
            <header class="history-panel__header">
                <h2>Past Generations</h2>
                <span class="history-panel__count">{count}</span>
            </header>
        """.format(count=len(visible_history)),
        unsafe_allow_html=True,
    )

    selection = panel.radio(
        "Select a past edit",
        options=list(range(len(visible_history))),
        index=default_index,
        format_func=lambda idx: f"Revision {idx + 1:02d}",
        key=_HISTORY_SELECTION_WIDGET_KEY,
        label_visibility="collapsed",
    )

    st.session_state[_SELECTED_HISTORY_STATE_KEY] = selection

    if st.session_state.get(_HISTORY_LAST_ACTIVATED_KEY) != selection:
        st.session_state[_HISTORY_LAST_ACTIVATED_KEY] = selection
        _hydrate_history_snapshot(visible_history[selection])

    for idx, previous in enumerate(visible_history):
        entry_id = _history_entry_identifier(previous, idx)
        is_selected = idx == selection
        if previous.is_favorited:
            favorites.add(entry_id)
        is_favorited = entry_id in favorites
        previous.is_favorited = is_favorited

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
        favorite_badge = (
            "<span class=\"history-entry__badge history-entry__badge--favorite\">Favorite</span>"
            if is_favorited
            else ""
        )

        duration_label = (
            f"{previous.duration_seconds:.1f}s"
            if previous.duration_seconds is not None
            else "—"
        )

        entry_container = panel.container()
        entry_container.markdown(
            """
            <article class="history-entry" data-selected="{selected}" aria-label="Revision {index:02d}">
                <div class="history-entry__body">
                    <div class="history-entry__thumb">
                        <img src="data:{mime};base64,{image}" alt="Past generation {index}" loading="lazy" />
                    </div>
                    <div class="history-entry__content">
                        <div class="history-entry__badges">
                            <span class="history-entry__badge history-entry__badge--id">Revision {index:02d}</span>
                            <span class="history-entry__badge history-entry__badge--duration">Duration {duration}</span>
                            {favorite_badge}
                        </div>
                        <p class="history-entry__prompt">{prompt}</p>
                        <time class="history-entry__timestamp">{timestamp}</time>
                    </div>
                </div>
                <div class="history-entry__actions">
            """.format(
                image=encoded_image,
                prompt=safe_prompt,
                mime=mime_type,
                timestamp=safe_timestamp,
                index=idx + 1,
                duration=html.escape(duration_label),
                favorite_badge=favorite_badge,
                selected=str(is_selected).lower(),
            ),
            unsafe_allow_html=True,
        )

        action_cols = entry_container.columns((1, 1, 1))
        with action_cols[0]:
            favorite_label = "★ Favorited" if is_favorited else "☆ Favorite"
            if st.button(favorite_label, key=f"{entry_id}-favorite"):
                is_favorited = _toggle_favorite(entry_id, previous)
                if is_favorited:
                    favorites.add(entry_id)
                else:
                    favorites.discard(entry_id)

        with action_cols[1]:
            if st.button("Duplicate", key=f"{entry_id}-duplicate"):
                st.session_state[_HISTORY_SELECTION_WIDGET_KEY] = idx
                st.session_state[_SELECTED_HISTORY_STATE_KEY] = idx
                st.session_state[_HISTORY_LAST_ACTIVATED_KEY] = idx
                st.session_state[_DUPLICATE_SOURCE_STATE_KEY] = entry_id
                _hydrate_history_snapshot(previous)

        with action_cols[2]:
            entry_container.download_button(
                "Download",
                data=previous.final_image,
                file_name=f"autoedit-revision-{idx + 1:02d}.{image_format}",
                mime=mime_type,
                key=f"{entry_id}-download",
            )

        entry_container.markdown("</div></article>", unsafe_allow_html=True)

    panel.markdown("</section>", unsafe_allow_html=True)


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

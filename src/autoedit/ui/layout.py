"""Composable Streamlit layout elements.

The functions defined here encapsulate the presentation logic for the
application. Splitting the UI across smaller helpers keeps the Streamlit app
readable and allows for individual sections to evolve independently.
"""

from __future__ import annotations

from typing import Optional, Tuple

import streamlit as st


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


def render_output_panel(image_bytes: Optional[bytes]) -> None:
    """Show the processed image results in a polished card layout."""
    st.divider()
    st.markdown("## Rendered Concept")

    if not image_bytes:
        st.info("Upload an image and craft a prompt to see your results here.")
        return

    cols = st.columns((3, 2), gap="large")
    with cols[0]:
        st.image(image_bytes, caption="Your refined visual", use_column_width=True)
    with cols[1]:
        st.markdown(
            """
            <div class="result-card">
                <h3>What's next?</h3>
                <ul>
                    <li>Iterate on your prompt to explore alternate concepts.</li>
                    <li>Share the result with collaborators via the share menu.</li>
                    <li>Stay tuned as AutoEdit grows smarter with every release.</li>
                </ul>
            </div>
            """,
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

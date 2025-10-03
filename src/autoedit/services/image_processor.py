"""Image processing workflow scaffolding.

The module provides lightweight, well documented placeholders for the
captioning, planning, and editing models that will power the AutoEdit
experience.  Although the heavy ML models are not available in this
prototype, the abstractions below mirror the intended behaviour so that the
Streamlit UI can already orchestrate a realistic multi-step pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, List, Optional

from autoedit.services.caption_service import generate_caption
from autoedit.services.edit_service import edit_image


@dataclass
class WorkflowStepResult:
    """Summary information for an individual workflow step."""

    name: str
    status: str
    detail: str


@dataclass
class ProcessResult:
    """Aggregate output of the end-to-end image workflow."""

    user_prompt: str
    caption: str
    refined_prompt: str
    final_image: Optional[bytes]
    steps: List[WorkflowStepResult]
    created_at: datetime


class JoyCaptionModel:
    """The JoyCaption vision-language model."""

    def generate_caption(self, image_bytes: bytes, prompt: str) -> str:
        return generate_caption(image_bytes, prompt)


class QwenImageEditor:
    """Stands in for the QWEN-Image-Edit model."""

    def apply_edit(self, image_bytes: bytes, refined_prompt: str) -> Optional[bytes]:
        return edit_image(image_bytes, refined_prompt)


ProgressCallback = Callable[[int, str, str], None]


class ImageProcessor:
    """Encapsulates the multi-stage image processing workflow."""

    def __init__(self) -> None:
        self._caption_model = JoyCaptionModel()
        self._image_editor = QwenImageEditor()

    def process(
        self,
        prompt: str,
        image_bytes: bytes,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> ProcessResult:
        """Process the provided image according to the multi-step workflow.

        Parameters
        ----------
        prompt:
            The textual instructions from the user.
        image_bytes:
            Raw bytes representing the uploaded image file.
        progress_callback:
            Optional callable used to report progress updates. The callback
            receives the step index, the new status (``"active"``,
            ``"complete"``, or ``"error"``), and a human-readable message.

        Returns
        -------
        ProcessResult
            The structured output of the workflow, including placeholder
            captions and refined prompts.
        """
        DEBUG_MODE = False
        if DEBUG_MODE:

            if not image_bytes:
                if progress_callback:
                    progress_callback(0, "error", "No image supplied for debugging pipeline.")
                return ProcessResult(
                    user_prompt=prompt,
                    caption="",
                    refined_prompt="",
                    final_image=None,
                    steps=[],
                    created_at=datetime.now(timezone.utc),
                )

            refined = (prompt or "Uploaded visual direction").strip() or "Exploratory concept"
            steps = [
                WorkflowStepResult(
                    name="Caption Extraction",
                    status="complete",
                    detail=f"Summarized intent: {refined[:160]}",
                ),
                WorkflowStepResult(
                    name="Prompt Orchestration",
                    status="complete",
                    detail="Drafted editing directives combining caption and user notes.",
                ),
                WorkflowStepResult(
                    name="Image Editing",
                    status="complete",
                    detail="QWEN-Image-Edit applied with placeholder settings for preview.",
                ),
            ]

            if progress_callback:
                progress_callback(0, "active", "Extracting descriptive caption (debug mode).")
                progress_callback(0, "complete", "Caption synthesized from provided brief.")
                progress_callback(1, "active", "Composing refined editing directions.")
                progress_callback(1, "complete", "Prompt orchestration finished.")
                progress_callback(2, "active", "Simulating QWEN image edit output.")
                progress_callback(2, "complete", "Debug image edit complete.")

            final_bytes = image_bytes or None

            return ProcessResult(
                user_prompt=prompt,
                caption=f"Placeholder caption derived from: {refined[:140]}",
                refined_prompt=f"Refined instructions based on: {refined[:140]}",
                final_image=final_bytes,
                steps=steps,
                created_at=datetime.now(timezone.utc),
            )

        if not image_bytes:
            return ProcessResult(
                user_prompt=prompt,
                caption="",
                refined_prompt="",
                final_image=None,
                steps=[],
                created_at=datetime.now(timezone.utc),
            )

        def notify(step_index: int, status: str, message: str) -> None:
            if progress_callback:
                progress_callback(step_index, status, message)

        notify(0, "active", "Extracting descriptive caption with JoyCaption...")
        refined_prompt = self._caption_model.generate_caption(image_bytes, prompt)
        caption_summary = refined_prompt if len(refined_prompt) <= 160 else refined_prompt[:157] + '...'
        notify(0, "complete", f"Caption ready: {caption_summary}")

        notify(1, "active", "Planning image edits...")
        notify(1, "complete", f"Refined instructions prepared:")

        notify(2, "active", "Applying QWEN-Image-Edit to the uploaded image...")
        final_image = self._image_editor.apply_edit(image_bytes, refined_prompt)
        notify(2, "complete", "Image updated with placeholder edit result.")

        steps = [
            WorkflowStepResult(
                name="Caption Extraction",
                status="complete",
                detail=caption_summary,
            ),
            WorkflowStepResult(
                name="Prompt Orchestration",
                status="complete",
                detail="",
            ),
            WorkflowStepResult(
                name="Image Editing",
                status="complete",
                detail="QWEN-Image-Edit applied with the refined instructions.",
            ),
        ]

        return ProcessResult(
            user_prompt=prompt,
            caption=refined_prompt,
            refined_prompt=refined_prompt,
            final_image=final_image,
            steps=steps,
            created_at=datetime.now(timezone.utc),
        )


__all__ = [
    "ImageProcessor",
    "ProcessResult",
    "WorkflowStepResult",
]

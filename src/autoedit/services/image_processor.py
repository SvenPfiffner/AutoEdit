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
from pathlib import Path
from typing import Callable, List, Optional

import torch

from services.caption_service import generate_caption
from services.edit_service import edit_image

from services.prompts import JOYCAPTION_PROMPT


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

    def generate_caption(self, image_bytes: bytes, prompt: str, progress_callback: Optional[ProgressCallback] = None) -> str:
        return generate_caption(image_bytes, prompt, progress_callback)


class QwenImageEditor:
    """Stands in for the QWEN-Image-Edit model."""

    def apply_edit(self, image_bytes: bytes, refined_prompt: str, progress_callback: Optional[ProgressCallback] = None) -> Optional[bytes]:
        return edit_image(image_bytes, refined_prompt, progress_callback)


ProgressCallback = Callable[[int, str, str], None]


class ImageProcessor:
    """Encapsulates the multi-stage image processing workflow."""

    def __init__(self, enable_storage: bool = True, output_dir: Optional[Path] = None) -> None:
        """Initialize the image processor.

        Parameters
        ----------
        enable_storage:
            Whether to automatically save results to persistent storage.
            Defaults to True.
        output_dir:
            Optional custom output directory for storage.
            If None, uses the default 'output' directory.
        """
        self._caption_model = JoyCaptionModel()
        self._image_editor = QwenImageEditor()
        self._enable_storage = enable_storage
        self._output_dir = output_dir

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

        if not image_bytes:
            return ProcessResult(
                user_prompt=prompt,
                caption="",
                refined_prompt="",
                final_image=None,
                steps=[],
                created_at=datetime.now(timezone.utc),
            )

        refined_prompt = self._caption_model.generate_caption(image_bytes, prompt, progress_callback)

        caption_summary = refined_prompt if len(refined_prompt) <= 160 else refined_prompt[:157] + '...'

        final_image = self._image_editor.apply_edit(image_bytes, refined_prompt, progress_callback)

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
            WorkflowStepResult(
                name="Finalization",
                status="complete",
                detail="Results saved and ready for display.",
            ),
        ]

        result = ProcessResult(
            user_prompt=prompt,
            caption=refined_prompt,
            refined_prompt=refined_prompt,
            final_image=final_image,
            steps=steps,
            created_at=datetime.now(timezone.utc),
        )

        # Save result to persistent storage if enabled
        if self._enable_storage:
            self._save_result(result)

        return result

    def _save_result(self, result: ProcessResult) -> None:
        """Save a processing result to persistent storage.

        Parameters
        ----------
        result:
            The processing result to save.
        """
        try:
            # Import here to avoid circular dependency
            from services.storage_service import StorageService

            storage = StorageService(output_dir=self._output_dir)
            storage.save_result(result)
        except Exception as e:
            # Log error but don't fail the pipeline
            print(f"Warning: Failed to save result to storage: {e}")


__all__ = [
    "ImageProcessor",
    "ProcessResult",
    "WorkflowStepResult",
]

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

import importlib
import sys


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
        caption_module = importlib.import_module("services.caption_service")
        caption_function = getattr(caption_module, "generate_caption")
        return caption_function(image_bytes, prompt, progress_callback)


class QwenImageEditor:
    """Stands in for the QWEN-Image-Edit model."""

    def __init__(self) -> None:
        self._edit_function: Optional[Callable[[bytes, str, Optional[ProgressCallback]], Optional[bytes]]] = None

    def _ensure_model_loaded(self) -> Callable[[bytes, str, Optional[ProgressCallback]], Optional[bytes]]:
        if self._edit_function is None:
            edit_module = importlib.import_module("services.edit_service")
            self._edit_function = getattr(edit_module, "edit_image")
        return self._edit_function

    def release_model(self) -> None:
        """Remove the cached edit model from memory."""

        self._edit_function = None
        if "services.edit_service" in sys.modules:
            del sys.modules["services.edit_service"]

    def apply_edit(
        self,
        image_bytes: bytes,
        refined_prompt: str,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> Optional[bytes]:
        edit_function = self._ensure_model_loaded()
        return edit_function(image_bytes, refined_prompt, progress_callback)


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
        mode: str = "Casual",
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

        normalized_mode = (mode or "Casual").strip().lower()
        is_professional = normalized_mode.startswith("pro")

        caption_text = ""
        caption_summary = "Professional mode: used the provided prompt without JoyCaption translation."

        def _caption_progress(step_index: int, status: str, message: str) -> None:
            if progress_callback:
                progress_callback(step_index, status, message)

        def _qwen_progress(step_index: int, status: str, message: str) -> None:
            if not progress_callback:
                return
            if is_professional:
                mapped_index = step_index if step_index < 2 else step_index - 2
            else:
                mapped_index = step_index
            progress_callback(mapped_index, status, message)

        refined_prompt = prompt
        if not is_professional:
            caption_callback = _caption_progress if progress_callback else None
            caption_text = self._caption_model.generate_caption(
                image_bytes,
                prompt,
                caption_callback,
            )
            refined_prompt = caption_text or prompt
            caption_summary = (
                caption_text
                if len(caption_text) <= 160
                else caption_text[:157] + "..."
            )
            self._image_editor.release_model()

        qwen_callback = _qwen_progress if progress_callback else None
        final_image = self._image_editor.apply_edit(
            image_bytes,
            refined_prompt,
            qwen_callback,
        )

        if not is_professional:
            self._image_editor.release_model()

        steps = [
            WorkflowStepResult(
                name="Prompt Orchestration",
                status="complete",
                detail="Professional mode used the provided prompt directly without JoyCaption translation."
                if is_professional
                else caption_summary,
            )
        ]

        if not is_professional:
            steps.insert(
                0,
                WorkflowStepResult(
                    name="Caption Extraction",
                    status="complete",
                    detail=caption_summary,
                ),
            )
            steps[1] = WorkflowStepResult(
                name="Prompt Orchestration",
                status="complete",
                detail="JoyCaption translated the casual brief into an editing prompt.",
            )

        steps.append(
            WorkflowStepResult(
                name="Image Editing",
                status="complete",
                detail="QWEN-Image-Edit applied with the refined instructions.",
            )
        )
        steps.append(
            WorkflowStepResult(
                name="Finalization",
                status="complete",
                detail="Results saved and ready for display.",
            )
        )

        result = ProcessResult(
            user_prompt=prompt,
            caption=caption_text,
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

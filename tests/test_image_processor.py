from __future__ import annotations

from types import MethodType

from autoedit.services.image_processor import ImageProcessor, WorkflowStepResult


def test_image_processor_success_flow():
    processor = ImageProcessor(enable_storage=False)
    callback_events: list[tuple[int, str, str]] = []

    def fake_caption(self, image_bytes: bytes, prompt: str, cb) -> str:
        if cb:
            cb(0, "active", "Loading JoyCaption")
            cb(0, "complete", "JoyCaption ready")
            cb(1, "active", "Generating caption")
            cb(1, "complete", "Caption generated")
        return "Refined cinematic lighting instructions"

    def fake_edit(self, image_bytes: bytes, refined_prompt: str, cb):
        if cb:
            cb(2, "active", "Loading QWEN")
            cb(2, "complete", "QWEN ready")
            cb(3, "active", "Applying QWEN edits")
            cb(3, "complete", "Edits applied")
        return image_bytes

    processor._caption_model.generate_caption = MethodType(fake_caption, processor._caption_model)
    processor._image_editor.apply_edit = MethodType(fake_edit, processor._image_editor)

    def callback(step_index: int, status: str, message: str) -> None:
        callback_events.append((step_index, status, message))

    prompt = "Add cinematic lighting"
    image_bytes = b"binary-image"

    result = processor.process(prompt=prompt, image_bytes=image_bytes, progress_callback=callback, mode="Casual")

    assert result.final_image == image_bytes
    assert result.caption == "Refined cinematic lighting instructions"
    assert result.refined_prompt == "Refined cinematic lighting instructions"
    assert len(result.steps) == 4
    assert all(isinstance(step, WorkflowStepResult) for step in result.steps)

    assert callback_events[0][0] == 0 and callback_events[0][1] == "active"
    assert callback_events[-1][0] == 3 and callback_events[-1][1] == "complete"


def test_image_processor_professional_mode_skips_caption():
    processor = ImageProcessor(enable_storage=False)
    caption_called = False
    callback_events: list[tuple[int, str, str]] = []

    def fake_caption(self, image_bytes: bytes, prompt: str, cb) -> str:
        nonlocal caption_called
        caption_called = True
        return "Should not be used"

    def fake_edit(self, image_bytes: bytes, refined_prompt: str, cb):
        if cb:
            cb(2, "active", "Loading QWEN")
            cb(2, "complete", "QWEN ready")
            cb(3, "active", "Applying QWEN edits")
            cb(3, "complete", "Edits applied")
        return image_bytes

    processor._caption_model.generate_caption = MethodType(fake_caption, processor._caption_model)
    processor._image_editor.apply_edit = MethodType(fake_edit, processor._image_editor)

    def callback(step_index: int, status: str, message: str) -> None:
        callback_events.append((step_index, status, message))

    prompt = "Use a professional commercial-grade retouch"
    image_bytes = b"binary-image"

    result = processor.process(
        prompt=prompt,
        image_bytes=image_bytes,
        progress_callback=callback,
        mode="Professional",
    )

    assert caption_called is False
    assert result.final_image == image_bytes
    assert result.caption == ""
    assert result.refined_prompt == prompt
    assert len(result.steps) == 3
    assert result.steps[0].detail.startswith("Professional mode")
    assert callback_events[0][0] == 0 and callback_events[0][1] == "active"
    assert callback_events[-1][0] == 1 and callback_events[-1][1] == "complete"



def test_image_processor_handles_missing_image():
    processor = ImageProcessor(enable_storage=False)

    result = processor.process(prompt="test", image_bytes=b"")

    assert result.final_image is None
    assert result.steps == []

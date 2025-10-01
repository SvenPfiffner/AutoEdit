from __future__ import annotations

from autoedit.services.image_processor import ImageProcessor, WorkflowStepResult


def test_image_processor_success_flow():
    processor = ImageProcessor()
    callback_events: list[tuple[int, str, str]] = []

    def callback(step_index: int, status: str, message: str) -> None:
        callback_events.append((step_index, status, message))

    prompt = "Add cinematic lighting"
    image_bytes = b"binary-image"

    result = processor.process(prompt=prompt, image_bytes=image_bytes, progress_callback=callback)

    assert result.final_image == image_bytes
    assert result.original_image == image_bytes
    assert result.caption
    assert result.refined_prompt
    assert len(result.steps) == 3
    assert all(isinstance(step, WorkflowStepResult) for step in result.steps)

    assert callback_events[0][0] == 0 and callback_events[0][1] == "active"
    assert callback_events[-1][0] == 2 and callback_events[-1][1] == "complete"



def test_image_processor_handles_missing_image():
    processor = ImageProcessor()

    result = processor.process(prompt="test", image_bytes=b"")

    assert result.final_image is None
    assert result.original_image is None
    assert result.steps == []

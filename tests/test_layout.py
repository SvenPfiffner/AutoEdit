from __future__ import annotations

from autoedit.ui import layout


class DummyPlaceholder:
    def __init__(self) -> None:
        self.calls: list[tuple[str, bool]] = []

    def markdown(self, value: str, unsafe_allow_html: bool = False) -> None:
        self.calls.append((value, unsafe_allow_html))


def test_render_workflow_progress_pads_missing_statuses():
    placeholder = DummyPlaceholder()

    steps = ["Caption", "Plan", "Edit"]
    layout.render_workflow_progress(
        placeholder=placeholder,
        steps=steps,
        statuses=["complete"],
        detail_text="Running",
    )

    output, flag = placeholder.calls[-1]
    assert flag is True

    for index in range(1, len(steps) + 1):
        assert f'class="workflow-progress__index">{index}</div>' in output


def test_render_workflow_progress_sanitizes_statuses():
    placeholder = DummyPlaceholder()

    layout.render_workflow_progress(
        placeholder=placeholder,
        steps=["One"],
        statuses=["invalid"],
        detail_text="Testing",
    )

    output, _ = placeholder.calls[-1]
    assert "workflow-progress__step--pending" in output

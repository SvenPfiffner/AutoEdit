"""Tests for the storage service."""

from __future__ import annotations

import io
import json
import sys
import types
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest
from PIL import Image

SRC_DIR = Path(__file__).resolve().parents[1] / "src" / "autoedit"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


class _InferenceMode:
    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc, tb):
        return False


if "torch" not in sys.modules:
    sys.modules["torch"] = types.SimpleNamespace(
        cuda=types.SimpleNamespace(empty_cache=lambda: None),
        manual_seed=lambda seed: seed,
        bfloat16="bfloat16",
        inference_mode=lambda: _InferenceMode(),
    )


class _FakePipeline:
    @classmethod
    def from_pretrained(cls, *args, **kwargs):
        return cls()

    def set_progress_bar_config(self, **kwargs):
        return None

    def to(self, device):
        return self

    def __call__(self, **kwargs):
        return types.SimpleNamespace(images=[Image.new("RGB", (2, 2), color=(255, 0, 0))])


if "diffusers" not in sys.modules:
    sys.modules["diffusers"] = types.SimpleNamespace(QwenImageEditPipeline=_FakePipeline)

from autoedit.services.image_processor import ProcessResult, WorkflowStepResult
from autoedit.services.storage_service import StorageService


def _create_image_bytes(image_format: str = "PNG") -> bytes:
    """Create an in-memory image and return its encoded bytes."""

    buffer = io.BytesIO()
    image = Image.new("RGB", (2, 2), color=(255, 0, 0))
    image.save(buffer, format=image_format)
    return buffer.getvalue()


def test_storage_service_initialization():
    """Test that StorageService initializes correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        storage = StorageService(output_dir=output_dir)

        assert storage.output_dir == output_dir
        assert storage.images_dir == output_dir / "images"
        assert storage.results_file == output_dir / "results.json"
        assert storage.images_dir.exists()


def test_save_result_with_image():
    """Test saving a processing result with an image."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        storage = StorageService(output_dir=output_dir)

        # Create a mock result
        result = ProcessResult(
            user_prompt="Test prompt",
            caption="Test caption",
            refined_prompt="Test refined prompt",
            final_image=_create_image_bytes("PNG"),
            final_image_format="PNG",
            steps=[
                WorkflowStepResult(
                    name="Test Step",
                    status="complete",
                    detail="Test detail",
                )
            ],
            created_at=datetime.now(timezone.utc),
        )

        # Save the result
        saved_entry = storage.save_result(result)

        # Check the returned entry
        assert saved_entry["id"].startswith("result_")
        assert saved_entry["user_prompt"] == "Test prompt"
        assert saved_entry["caption"] == "Test caption"
        assert saved_entry["image_filename"] is not None
        assert len(saved_entry["steps"]) == 1

        # Check that the image file was created
        image_path = storage.images_dir / saved_entry["image_filename"]
        assert image_path.exists()
        assert image_path.read_bytes() == result.final_image

        with Image.open(image_path) as saved_image:
            assert saved_image.format == "PNG"

        assert saved_entry["image_filename"].endswith(".png")
        assert saved_entry["image_format"] == "PNG"

        # Check that results.json was created
        assert storage.results_file.exists()


def test_save_result_without_image():
    """Test saving a processing result without an image."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        storage = StorageService(output_dir=output_dir)

        # Create a mock result without an image
        result = ProcessResult(
            user_prompt="Test prompt",
            caption="Test caption",
            refined_prompt="Test refined prompt",
            final_image=None,
            final_image_format=None,
            steps=[],
            created_at=datetime.now(timezone.utc),
        )

        # Save the result
        saved_entry = storage.save_result(result)

        # Check that no image filename is set
        assert saved_entry["image_filename"] is None

        # Check that results.json was still created
        assert storage.results_file.exists()


def test_multiple_results():
    """Test saving multiple results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        storage = StorageService(output_dir=output_dir)

        # Save multiple results
        for i in range(3):
            image_format = "JPEG" if i % 2 else "PNG"
            result = ProcessResult(
                user_prompt=f"Test prompt {i}",
                caption=f"Test caption {i}",
                refined_prompt=f"Test refined prompt {i}",
                final_image=_create_image_bytes(image_format),
                final_image_format=image_format,
                steps=[],
                created_at=datetime.now(timezone.utc),
            )
            storage.save_result(result)

        # Load all results
        results = storage.get_all_results()
        assert len(results) == 3

        # Check that results are in reverse chronological order (newest first)
        assert results[0]["user_prompt"] == "Test prompt 2"
        assert results[1]["user_prompt"] == "Test prompt 1"
        assert results[2]["user_prompt"] == "Test prompt 0"

        # Verify stored filenames and actual image formats line up
        for entry in results:
            image_filename = entry["image_filename"]
            if not image_filename:
                continue
            image_path = storage.images_dir / image_filename
            expected_extension = StorageService._extension_from_format(entry["image_format"])
            assert image_path.suffix.lstrip(".") == expected_extension
            with Image.open(image_path) as saved_image:
                assert saved_image.format == entry["image_format"]


def test_get_result_by_id():
    """Test retrieving a specific result by ID."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        storage = StorageService(output_dir=output_dir)

        # Save a result
        result = ProcessResult(
            user_prompt="Test prompt",
            caption="Test caption",
            refined_prompt="Test refined prompt",
            final_image=_create_image_bytes("PNG"),
            final_image_format="PNG",
            steps=[],
            created_at=datetime.now(timezone.utc),
        )
        saved_entry = storage.save_result(result)
        result_id = saved_entry["id"]

        # Retrieve by ID
        retrieved = storage.get_result_by_id(result_id)
        assert retrieved is not None
        assert retrieved["id"] == result_id
        assert retrieved["user_prompt"] == "Test prompt"

        # Try to retrieve non-existent ID
        not_found = storage.get_result_by_id("nonexistent_id")
        assert not_found is None


def test_get_image_path():
    """Test getting the path to a saved image."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        storage = StorageService(output_dir=output_dir)

        image_filename = "test_image.jpg"
        image_path = storage.get_image_path(image_filename)

        assert image_path == storage.images_dir / image_filename


def test_results_json_format():
    """Test that the results.json file is properly formatted."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        storage = StorageService(output_dir=output_dir)

        # Save a result
        result = ProcessResult(
            user_prompt="Test prompt",
            caption="Test caption with unicode: 你好",
            refined_prompt="Test refined prompt",
            final_image=_create_image_bytes("PNG"),
            final_image_format="PNG",
            steps=[
                WorkflowStepResult(
                    name="Step 1",
                    status="complete",
                    detail="Detail 1",
                ),
                WorkflowStepResult(
                    name="Step 2",
                    status="complete",
                    detail="Detail 2",
                ),
            ],
            created_at=datetime.now(timezone.utc),
        )
        storage.save_result(result)

        # Load the JSON file directly
        with open(storage.results_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Check structure
        assert isinstance(data, list)
        assert len(data) == 1
        
        entry = data[0]
        assert "id" in entry
        assert "timestamp" in entry
        assert "user_prompt" in entry
        assert "caption" in entry
        assert "refined_prompt" in entry
        assert "image_filename" in entry
        assert "image_format" in entry
        assert "steps" in entry
        assert isinstance(entry["steps"], list)
        assert len(entry["steps"]) == 2

        # Check unicode is preserved
        assert entry["caption"] == "Test caption with unicode: 你好"

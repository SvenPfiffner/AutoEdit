"""Storage service for persisting processing results.

This module handles saving processing results to the output directory,
including images, metadata, and a results index file.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from services.image_processor import ProcessResult


class StorageService:
    """Manages persistent storage of processing results."""

    def __init__(self, output_dir: Optional[Path] = None) -> None:
        """Initialize the storage service.

        Parameters
        ----------
        output_dir:
            The directory where results should be stored.
            Defaults to the 'output' directory in the project root.
        """
        if output_dir is None:
            # Default to output directory in project root
            project_root = Path(__file__).parent.parent.parent.parent
            output_dir = project_root / "output"

        self.output_dir = output_dir
        self.images_dir = output_dir / "images"
        self.results_file = output_dir / "results.json"

        # Ensure directories exist
        self.images_dir.mkdir(parents=True, exist_ok=True)

    def save_result(self, result: ProcessResult) -> dict:
        """Save a processing result to persistent storage.

        Parameters
        ----------
        result:
            The processing result to save.

        Returns
        -------
        dict
            The saved result entry with metadata.
        """
        # Generate unique ID based on timestamp
        timestamp_str = result.created_at.strftime("%Y%m%d_%H%M%S_%f")
        result_id = f"result_{timestamp_str}"

        # Save the final image if available
        image_filename = None
        if result.final_image:
            image_filename = f"{result_id}.jpg"
            image_path = self.images_dir / image_filename
            with open(image_path, "wb") as f:
                f.write(result.final_image)

        # Create result entry
        result_entry = {
            "id": result_id,
            "timestamp": result.created_at.isoformat(),
            "user_prompt": result.user_prompt,
            "caption": result.caption,
            "refined_prompt": result.refined_prompt,
            "image_filename": image_filename,
            "steps": [
                {
                    "name": step.name,
                    "status": step.status,
                    "detail": step.detail,
                }
                for step in result.steps
            ],
        }

        # Load existing results
        results = self._load_results()

        # Add new result at the beginning
        results.insert(0, result_entry)

        # Save updated results
        self._save_results(results)

        return result_entry

    def _load_results(self) -> list:
        """Load existing results from the results file.

        Returns
        -------
        list
            List of result entries, or empty list if file doesn't exist.
        """
        if not self.results_file.exists():
            return []

        try:
            with open(self.results_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # If file is corrupted or unreadable, start fresh
            return []

    def _save_results(self, results: list) -> None:
        """Save results to the results file.

        Parameters
        ----------
        results:
            List of result entries to save.
        """
        with open(self.results_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

    def get_all_results(self) -> list:
        """Retrieve all stored results.

        Returns
        -------
        list
            List of all result entries.
        """
        return self._load_results()

    def get_result_by_id(self, result_id: str) -> Optional[dict]:
        """Retrieve a specific result by ID.

        Parameters
        ----------
        result_id:
            The unique identifier of the result.

        Returns
        -------
        dict or None
            The result entry if found, None otherwise.
        """
        results = self._load_results()
        for result in results:
            if result["id"] == result_id:
                return result
        return None

    def get_image_path(self, image_filename: str) -> Path:
        """Get the full path to a saved image.

        Parameters
        ----------
        image_filename:
            The filename of the image.

        Returns
        -------
        Path
            The full path to the image file.
        """
        return self.images_dir / image_filename


__all__ = ["StorageService"]

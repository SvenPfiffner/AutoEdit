#!/usr/bin/env python3
"""Utility script to view stored AutoEdit results.

This script demonstrates how to programmatically access and view
the results stored by the AutoEdit processing pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime


def view_results(output_dir: Path = None) -> None:
    """Display a summary of all stored results.

    Parameters
    ----------
    output_dir:
        The output directory to read from. Defaults to the project's output directory.
    """
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "output"

    results_file = output_dir / "results.json"

    if not results_file.exists():
        print("No results found. The results.json file doesn't exist yet.")
        print(f"Expected location: {results_file}")
        return

    with open(results_file, "r", encoding="utf-8") as f:
        results = json.load(f)

    if not results:
        print("No results stored yet.")
        return

    print(f"Found {len(results)} result(s):\n")
    print("=" * 80)

    for i, result in enumerate(results, 1):
        timestamp = datetime.fromisoformat(result["timestamp"])
        print(f"\n[{i}] {result['id']}")
        print(f"    Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"    User Prompt: {result['user_prompt']}")
        print(f"    Caption: {result['caption'][:100]}{'...' if len(result['caption']) > 100 else ''}")
        
        if result.get("image_filename"):
            image_path = output_dir / "images" / result["image_filename"]
            status = "✓ exists" if image_path.exists() else "✗ missing"
            print(f"    Image: {result['image_filename']} ({status})")
        else:
            print("    Image: None")

        # Show step statuses
        step_statuses = [step["status"] for step in result.get("steps", [])]
        if step_statuses:
            status_summary = ", ".join(step_statuses)
            print(f"    Steps: {status_summary}")

    print("\n" + "=" * 80)
    print(f"\nResults file: {results_file}")
    print(f"Images directory: {output_dir / 'images'}")


def view_result_detail(result_id: str, output_dir: Path = None) -> None:
    """Display detailed information about a specific result.

    Parameters
    ----------
    result_id:
        The ID of the result to display.
    output_dir:
        The output directory to read from. Defaults to the project's output directory.
    """
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "output"

    results_file = output_dir / "results.json"

    if not results_file.exists():
        print("No results found.")
        return

    with open(results_file, "r", encoding="utf-8") as f:
        results = json.load(f)

    result = next((r for r in results if r["id"] == result_id), None)

    if not result:
        print(f"Result with ID '{result_id}' not found.")
        return

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # View specific result by ID
        view_result_detail(sys.argv[1])
    else:
        # View all results
        view_results()

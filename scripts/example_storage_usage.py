"""Example of using the StorageService independently.

This script demonstrates how to work with stored results programmatically.
"""

from pathlib import Path
from autoedit.services.storage_service import StorageService


def example_load_and_display_results():
    """Load and display all stored results."""
    # Initialize storage service (uses default output directory)
    storage = StorageService()

    # Get all results
    results = storage.get_all_results()

    print(f"Total results: {len(results)}\n")

    # Display each result
    for result in results[:5]:  # Show first 5
        print(f"ID: {result['id']}")
        print(f"Timestamp: {result['timestamp']}")
        print(f"User Prompt: {result['user_prompt']}")
        print(f"Caption: {result['caption'][:100]}...")
        
        if result.get('image_filename'):
            image_path = storage.get_image_path(result['image_filename'])
            print(f"Image: {image_path}")
            print(f"Image exists: {image_path.exists()}")
        
        print("-" * 80)


def example_find_results_by_keyword(keyword: str):
    """Find all results containing a specific keyword in the prompt."""
    storage = StorageService()
    results = storage.get_all_results()

    matching = [
        r for r in results 
        if keyword.lower() in r['user_prompt'].lower()
    ]

    print(f"Found {len(matching)} results matching '{keyword}':\n")

    for result in matching:
        print(f"- {result['user_prompt']}")
        print(f"  {result['timestamp']}")
        print()


def example_get_recent_results(n: int = 10):
    """Get the N most recent results."""
    storage = StorageService()
    results = storage.get_all_results()

    recent = results[:n]  # Results are already sorted newest first

    print(f"Most recent {len(recent)} results:\n")

    for i, result in enumerate(recent, 1):
        print(f"{i}. {result['user_prompt']}")
        print(f"   {result['timestamp']}")
        print()


def example_export_summary():
    """Export a summary of all results to a text file."""
    storage = StorageService()
    results = storage.get_all_results()

    output_file = storage.output_dir / "summary.txt"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"AutoEdit Results Summary\n")
        f.write(f"Total Results: {len(results)}\n")
        f.write("=" * 80 + "\n\n")

        for i, result in enumerate(results, 1):
            f.write(f"[{i}] {result['id']}\n")
            f.write(f"Timestamp: {result['timestamp']}\n")
            f.write(f"Prompt: {result['user_prompt']}\n")
            f.write(f"Caption: {result['caption'][:200]}\n")
            f.write(f"Image: {result.get('image_filename', 'None')}\n")
            f.write("\n")

    print(f"Summary exported to: {output_file}")


if __name__ == "__main__":
    print("=== Loading and Displaying Results ===\n")
    example_load_and_display_results()

    print("\n=== Finding Results by Keyword ===\n")
    example_find_results_by_keyword("dramatic")

    print("\n=== Recent Results ===\n")
    example_get_recent_results(5)

    print("\n=== Exporting Summary ===\n")
    example_export_summary()

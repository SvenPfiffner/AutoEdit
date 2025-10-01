"""Placeholder image processing service.

The goal for now is to provide a well-documented façade that the future
backend can extend. Returning the original image keeps the UI development
unblocked while signalling where real processing logic will live.
"""

from __future__ import annotations

from typing import Optional


class ImageProcessor:
    """Encapsulates the image processing workflow."""

    def process(self, prompt: str, image_bytes: bytes) -> Optional[bytes]:
        """Process the provided image according to the prompt.

        Parameters
        ----------
        prompt:
            The textual instructions from the user.
        image_bytes:
            Raw bytes representing the uploaded image file.

        Returns
        -------
        Optional[bytes]
            The processed image bytes. `None` is returned when the input is
            empty or processing fails.
        """

        if not image_bytes:
            return None

        # Placeholder: In the future this is where advanced image transformations
        # will be orchestrated. Keeping the method pure and side-effect free makes
        # it simple to test and evolve.
        return image_bytes

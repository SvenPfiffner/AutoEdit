# AutoEdit Studio

AutoEdit Studio is a Streamlit-based prototype that explores a premium
image-editing workflow. The current milestone focuses on establishing a
polished front-end experience with a modular architecture that will welcome
future backend enhancements.

## Project layout

```
.
├── .streamlit/         # Centralized Streamlit configuration and theming
├── README.md           # Project overview and setup notes
├── pyproject.toml      # Python project metadata and dependencies
└── src/
    └── autoedit/
        ├── app.py               # Streamlit entry point
        ├── services/            # Placeholder service layer
        │   └── image_processor.py
        └── ui/                  # Presentation logic and global styling
            ├── __init__.py
            └── layout.py
```

The project follows a `src`-based layout to keep import paths explicit and to
support packaging should the application grow into a larger service.

## Getting started

1. Create and activate a virtual environment (optional but recommended).
2. Install dependencies:

   ```bash
   pip install -e .
   ```

3. Launch the Streamlit application:

   ```bash
   streamlit run src/autoedit/app.py
   ```

4. Open the URL displayed in the terminal to access the interface. Upload an
   image, provide a prompt, and click **Render Concept** to preview the current
   placeholder processing flow (which simply echoes back the original image).

## Next steps

The service layer is intentionally lightweight. It exposes a single
`ImageProcessor` class so that future development can incorporate advanced
model calls, prompt engineering, or multi-step image processing pipelines
without rewriting the UI.

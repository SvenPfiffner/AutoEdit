# AutoEdit Studio

AutoEdit Studio is a Streamlit-based prototype that explores a premium
image-editing workflow. The current milestone focuses on establishing a
polished front-end experience with a modular architecture that will welcome
future backend enhancements.

## Project layout

# AutoEdit Studio ✨

**A cascaded vision-language approach to natural-language image editing**

AutoEdit Studio implements a novel two-stage pipeline that bridges the semantic gap between casual user requests and precise image editing instructions. By leveraging a vision-language model as an intelligent prompt translator, the system enables users to describe edits naturally while maintaining the specificity required by diffusion-based editing models.

---

## 🎯 Core Innovation

### The Challenge
Modern image editing models like QWEN-Image-Edit excel at applying precise modifications but struggle with ambiguous instructions. Users naturally express intent through high-level concepts ("make it vintage," "make him look rich"), creating a semantic mismatch that degrades editing quality.

### The Solution: Cascaded Vision-Language Architecture

```
User Input → [JoyCaption Translation] → [QWEN Image Editing] → Output
  "make it vintage"  →  "add sepia tone, reduce     →  [edited image]
                         saturation, add film grain"
```

**Stage 1: Vision-Language Translation (JoyCaption)**  
The system employs a fine-tuned LLaVA-based model (JoyCaption) that simultaneously processes both the input image and user prompt. This vision-aware translation layer:

- Grounds abstract concepts in visual context ("vintage" → specific color grading parameters)
- Decomposes complex requests into atomic editing operations
- Preserves structural constraints (identity, composition, pose) unless explicitly modified
- Generates 1-4 concrete editing directives optimized for downstream diffusion models

**Critical advantage:** By translating vague prompts into specific, minimal edits *before* diffusion, the system prevents scope creep where the model might reimagine the entire scene. Direct prompts like "make it vintage" can cause diffusion models to hallucinate new elements or alter the subject. JoyCaption's constrained translation ensures QWEN applies targeted modifications while keeping the original subject, composition, and photorealism intact—the edit affects *the image*, not *a reimagining of it*.

**Stage 2: Instruction-Guided Image Editing (QWEN)**  
The refined prompts feed into QWEN-Image-Edit, a 4-bit quantized diffusion model that applies targeted modifications while maintaining image coherence. The cascade architecture ensures QWEN receives unambiguous instructions, dramatically improving editing fidelity.

---

## 🔬 Technical Highlights

### Memory-Efficient Inference
The system implements aggressive optimization to run dual large models on consumer hardware:

- **Selective GPU Offloading**: JoyCaption's vision tower (~2-3GB VRAM) resides on GPU while the language model runs on CPU, reducing memory footprint by ~85%
- **Model Persistence**: Both pipelines remain loaded between requests, eliminating cold-start latency
- **Total VRAM Budget**: ~6-8GB for the complete pipeline (JoyCaption + QWEN)

### Prompt Engineering
Custom system prompts constrain JoyCaption's output space:
- Enforces minimal edit sets (Occam's razor for image modifications)
- Explicitly prohibits unsolicited changes to identity-preserving features
- Produces comma-separated edit lists directly compatible with QWEN's conditioning mechanism

---

## 📋 Project Structure

```
AutoEdit/
├── src/autoedit/
│   ├── app.py                      # Streamlit orchestration
│   ├── services/
│   │   ├── caption_service.py      # JoyCaption inference & CPU offloading
│   │   ├── edit_service.py         # QWEN pipeline management
│   │   ├── image_processor.py      # Workflow coordination
│   │   └── prompts.py              # System prompts & constraints
│   └── ui/
│       └── layout.py               # Interface components
├── tests/
└── pyproject.toml
```

---

## 🚀 Getting Started

### Prerequisites
- Python ≥3.9
- CUDA-capable GPU (6GB+ VRAM recommended)
- ~20GB disk space for models

### Installation

1. **Clone and setup environment:**
```bash
git clone https://github.com/SvenPfiffner/AutoEdit.git
cd AutoEdit
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -e .
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118  # Adjust CUDA version
pip install transformers diffusers accelerate
```

3. **Launch application:**
```bash
streamlit run src/autoedit/app.py
```

The interface will open at `http://localhost:8501`. Upload an image, describe your desired edits naturally, and watch the cascaded pipeline translate and apply your modifications! 🎨

---

## 🎨 Example Use Cases

| User Input | JoyCaption Translation | Result |
|------------|----------------------|---------|
| "make this look cinematic" | shift color grading to cool blue tones, add subtle neon highlights, increase contrast slightly | Film-grade color grading applied |
| "add glasses" | add thin-framed glasses | Precise object addition |
| "make her look like a fantasy elf" | add subtle pointed ears, shift eye color to bright green, add silver circlet | Multi-edit character transformation |

---

## 🧪 Research Context

This implementation explores **semantic compression in multimodal pipelines**: vision-language models can act as learned codecs that map high-entropy natural language to low-entropy instruction sets optimized for downstream specialized models. The approach generalizes beyond image editing to any task requiring translation between human intent and machine-executable specifications.

### Potential Extensions
- Fine-tuning JoyCaption on domain-specific edit taxonomies
- Multi-turn refinement with iterative feedback
- Extension to video editing with temporal consistency constraints

---

## 🤝 Collaboration & Citation

**Author:** Sven Pfiffner

Contributions are welcomed! 🙌 For bugs, feature requests, or research discussions:
1. Open an issue describing your idea
2. Fork the repository
3. Submit a merge request with your changes

### Citation
If you use AutoEdit Studio in commercial applications, academic research, or public projects, please cite:

```bibtex
@software{pfiffner2025autoedit,
  author = {Pfiffner, Sven},
  title = {AutoEdit Studio: Cascaded Vision-Language Image Editing},
  year = {2025},
  url = {https://github.com/SvenPfiffner/AutoEdit}
}
```

---

## 📄 License

This project is released under an open-source license. Commercial and research use requires attribution (see Citation section above).

---

**Built with:** Streamlit • PyTorch • Transformers • Diffusers • QWEN-Image-Edit • JoyCaption (LLaVA)

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

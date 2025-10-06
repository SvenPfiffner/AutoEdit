# Getting Started with AutoEdit Studio 🚀

Welcome to **AutoEdit**—a tool that lets you edit images using natural language. No complicated sliders, no endless menus—just describe what you want, upload an image, and watch the magic happen.


## What Does AutoEdit Do?

AutoEdit takes the pain out of image editing by letting you use **casual, everyday language** to describe changes. Want to make a photo look vintage? Just say "make it vintage." Want to turn your friend into a monster? Type "Can you make this guy look creepy?" 

Here's the clever part: AutoEdit uses a **two-stage AI pipeline** to understand what you mean and then actually execute those edits:

1. **JoyCaption** (Stage 1) - Looks at your image and your casual prompt, then translates it into specific, technical editing instructions that are fine tuned for QWEN and take everything visible in your image into consideration.
2. **QWEN-Image-Edit** (Stage 2) - Takes those precise instructions and applies them to your image

This approach prevents the AI from going rogue and completely reimagining your photo. It edits **what's there**, not what it thinks should be there. Even though image editing AI's are getting really good at understanding vague, non specific user requests, our research has shown that cascading such a preprocessing step increases character and composition coherence immensely for vague prompts. Especially for smaller models that can run on consumer hardware.

## Before You Begin

### System Requirements

AutoEdit is GPU-hungry. Here's what you'll need:

- **GPU**: NVIDIA GPU with at least **20-24GB VRAM** (e.g., RTX 3090, RTX 4090, A5000, or better)
- **Storage**: About **20GB free space** for the AI models (they download automatically on first run)
- **Python**: Version **3.9 or higher**
- **CUDA**: Compatible CUDA installation for PyTorch

**Don't have a powerful GPU?** Unfortunately, AutoEdit won't run on CPU or small GPUs. Consider using a rented GPU system. We might provide a docker container for easy remote installation in the future, should there be demand.


## Installation

Let's get you set up. Open your terminal and follow along:

### 1. Clone the Repository

```bash
git clone https://github.com/SvenPfiffner/AutoEdit.git
cd AutoEdit
```

### 2. Install Dependencies

You'll need to install several Python packages. The exact command depends on your CUDA version, but here's a starting point:

```bash
pip install streamlit pillow torch transformers diffusers accelerate
```

**Having trouble with PyTorch and CUDA?** Visit [pytorch.org](https://pytorch.org/get-started/locally/) to get the exact install command for your system.

### 3. Launch the App

Once everything is installed, fire up AutoEdit:

```bash
streamlit run src/autoedit/app.py
```

Your terminal will show a local URL (usually `http://localhost:8501`). Open that in your browser, and you're in!

**First launch will be slow** because AutoEdit needs to download the AI models (~20GB). You can always check on the progress by looking at your terminal. Grab a coffee—it's worth the wait.


## Using AutoEdit: The Basics

Once the app loads, you'll see an interface with a few key areas:

### 1. **Upload Your Image**

Click the **Reference visual** upload box and choose a PNG, JPG, or JPEG image. High-quality images work best.

### 2. **Write Your Edit Instructions**

In the **Edit Instructions** text box, describe what you want to change. Be as casual or detailed as you like:

- **Casual**: "Make this portrait look better"
- **More specific**: "add a warm sepia tone, remove wrinkles, add subtle makeup to the eyes"
- **Creative**: "turn this kitten into a nerdy supervillain"

### 3. **Choose Your Mode**

AutoEdit offers two processing modes:

#### **Casual Mode** (Default)
- **Best for**: Beginners, creative exploration, vague prompts
- **How it works**: Uses JoyCaption to translate your casual prompt into technical instructions
- **Speed**: Slower (uses two AI models that need to be loaded/unloaded on each run to fit on a consumer GPU)
- **Example prompt**: "make her look like a fantasy elf"

#### **Professional Mode**
- **Best for**: Advanced users, faster results, precise control
- **How it works**: Skips JoyCaption and sends your prompt directly to QWEN-Image-Edit
- **Speed**: Much faster (uses one AI model and requires loading only on first run)
- **Example prompt**: "shift eye color to bright emerald green, add subtle pointed ears, add delicate silver circlet on head"

**Pro tip**: Start with Casual mode to see how AutoEdit thinks. Once you understand the pattern, switch to Professional mode for speed.

### 4. **Click "Render Concept"**

Hit the big blue button and watch the progress indicator. You'll see each AI model load and execute in real-time.

### 5. **Review Your Results**

Once processing completes, you'll see:

- **Your edited image** (left side)
- **Workflow summary** (right side) - Shows what the AI understood and how it executed the edit
- **Action buttons**:
  - **Refine**: Use this result as the starting point for another edit
  - **Save**: Download your masterpiece


## Understanding the Workflow

Let's peek under the hood. When you click "Render Concept," here's what happens:

### Casual Mode Pipeline

1. **Load JoyCaption** - The AI that understands your intent
2. **Extract Edit Instructions** - JoyCaption analyzes your image and prompt, then generates 1-4 specific editing directives
3. **Load QWEN-Image-Edit** - The AI that actually modifies images
4. **Apply QWEN-Image-Edit** - Your image gets edited based on the refined instructions

### Professional Mode Pipeline

1. **Load QWEN-Image-Edit** - Skips straight to the editing model
2. **Apply QWEN-Image-Edit** - Uses your prompt exactly as written


## Tips for Great Results

### Casual Mode Tips

✅ **Be descriptive but natural**: "make the woman look elegant and sophisticated"
✅ **Specify additions clearly**: "add sunglasses and a leather jacket"
✅ **Use mood words**: "make it moody and cinematic"
❌ **Don't overthink it**: The AI is trained to understand everyday language

### Professional Mode Tips

✅ **Use action verbs**: "add," "remove," "adjust," "replace," "enhance"
✅ **Be atomic**: Break complex edits into simple, independent changes
✅ **Separate with commas**: "add thin silver-rimmed glasses, brighten shirt collar, refine jacket fabric to fine wool texture"
✅ **Specify details**: Colors, materials, positions, intensities

### Universal Tips

- **Preserve the original**: Unless you explicitly ask, AutoEdit tries to keep faces, poses, and composition intact
- **High-quality input = high-quality output**: Use the best images you have
- **Experiment**: Try different phrasings to see what works best
- **Use the Refine button**: Build on previous edits iteratively


## Example Workflows

### Example 1: Making a Photo Vintage

**Image**: Modern photo of a person
**Casual prompt**: "make it vintage"
**What JoyCaption generates**: "apply warm sepia color grade, reduce saturation slightly, add subtle film grain, soften highlights gently"
**Result**: A photo that looks like it was taken in the 1970s


### Example 2: Adding Accessories

**Image**: Portrait of a person
**Casual prompt**: "make him look rich"
**What JoyCaption generates**: "add luxury wristwatch, refine jacket fabric to fine wool texture, brighten shirt collar and cuffs slightly"
**Result**: Same person, but with subtle indicators of wealth


### Example 3: Creative Transformation

**Image**: Cat photo
**Casual prompt**: "turn this kitten into a nerdy supervillain"
**What JoyCaption generates**: "add tiny round glasses, add small black cape, add subtle mischievous expression"
**Result**: An adorable villainous kitten


## The Refine Workflow

One of AutoEdit's coolest features is **iterative refinement**. Here's how it works:

1. Upload an image and run an edit
2. Click the **Refine** button on the result
3. The edited image becomes your new starting point
4. Write a new prompt to make additional changes
5. Repeat as many times as you want

**Example**: 
- First edit: "make it vintage"
- Refine with: "add a sunset in the background"
- Refine again: "increase the warmth"

Each iteration builds on the previous one, letting you craft exactly what you envision.


## Understanding the Results Panel

After each edit, you'll see a **Workflow Summary** that breaks down what happened:

- **User brief**: Your original prompt
- **JoyCaption insight**: The technical translation (Casual mode only)
- **Refined edit prompt**: The actual instructions sent to QWEN-Image-Edit

This transparency helps you learn how to write better prompts over time.


## Troubleshooting

### "CUDA out of memory" error
- **Cause**: Your GPU doesn't have enough VRAM
- **Solution**: Try using smaller images, or upgrade to a GPU with more memory

### Models downloading slowly
- **Cause**: 20GB is a lot of data
- **Solution**: Be patient. This only happens once. Subsequent runs use cached models.

### "Image looks weird/distorted"
- **Cause**: The AI misunderstood your prompt or the edit was too extreme
- **Solution**: Try rephrasing your prompt to be more specific, or use Professional mode with precise instructions

### App feels slow
- **Cause**: Casual mode uses two AI models
- **Solution**: Switch to Professional mode for much faster processing (but you'll need to write technical prompts)

### The edit changed my subject's face
- **Cause**: The prompt might have been ambiguous, or you explicitly asked for face changes
- **Solution**: AutoEdit tries hard to preserve faces. If this happens, be more explicit: "keep the person's face and features unchanged, only add a hat"


## Advanced: Professional Mode Mastery

Ready to level up? Professional mode gives you fine-grained control. Here's the syntax:

**Format**: `action verb + subject + specific details, action verb + subject + details, ...`

**Example prompts**:
- `adjust white balance to neutral, increase midtone sharpness subtly, reduce background noise`
- `add subtle pointed ears, shift eye color to bright emerald green, add delicate silver circlet on head`
- `remove coffee cup from hand, clean up background clutter`
- `replace background with sunlit forest scene, keep subject unchanged`

**Pro tips for Professional mode**:
1. Study the "JoyCaption insight" outputs from Casual mode—they're examples of good Professional prompts
2. Keep each action atomic (one change per directive)
3. Order matters: List edits in the order you'd apply them manually
4. When in doubt, be explicit about what to preserve


## History and Storage

AutoEdit keeps track of your recent edits in the **History Sidebar** (if visible). This lets you:
- See your last 6 edits
- Compare results quickly
- Keep track of your experimentation

**Note**: History resets when you close the browser. If you want to keep an image, use the **Save** button. A persistent log including previously generated images is also kept in the "outputs" folder of your installation permanently. We will soon integrate this into the history, so it should also be persistent soon.


## Under the Hood (For the Curious)

AutoEdit uses some seriously cool technology:

- **JoyCaption (LLaVA-based)**: A vision-language model that "sees" your image and "understands" your intent
- **QWEN-Image-Edit**: A diffusion-based image editing model that applies precise modifications
- **Streamlit**: The web framework that powers the UI
- **PyTorch**: The deep learning framework that runs everything

The entire codebase is structured to be modular and extensible, so developers can swap in different models or add new features easily.


## Contributing & Support

### Found a Bug?
Open an issue on the [GitHub repository](https://github.com/SvenPfiffner/AutoEdit). Be as detailed as possible—screenshots help!

### Have Ideas?
Fork the repo and submit a pull request. Contributions are welcome!

### Need Help?
Check the [README.md](README.md) for additional context, or explore the code—it's well-documented and structured for readability.


## Final Thoughts

AutoEdit is a **proof of concept**—. It is designed to be an open source alternative with the ease of use professional tools like NanoBanana deliver, but uncensored, research friendly and locally run. If you are a true professional, you might be advised to use something more stable and extensible; like comfyUI. If you want a straightforward installation and go straight to editing without much hassle, you are at the right place though. 

Start with simple prompts, experiment with different modes, and don't be afraid to iterate. The more you use it, the better you'll understand how to communicate with the AI.

Now stop reading and start editing. Go make something cool. ✨


**Author**: Sven Pfiffner  
**Project**: AutoEdit  
**License**: See [LICENSE](LICENSE)  

Happy editing! 🎨

# ComfyUI Fixed Image Comparer

Compare your workflow's output against a fixed reference image, right in the
node graph. A single node — **Fixed Image Comparer** (category: `image`) —
shows both images in one preview with a hover swipe slider: left of the line
is your fixed reference, right is the freshly generated result. Useful for
A/B-ing prompt tweaks, sampler settings, or model changes against a known
baseline without leaving ComfyUI.

## Usage

1. Add **Fixed Image Comparer** to your workflow.
2. Pick the fixed reference with the `fixed_image` picker (uploads go to
   ComfyUI's `input` folder), **or** paste an absolute path into
   `fixed_image_path` (the path overrides the picker when non-empty).
3. Connect your generated image to the `image` input.
4. Run the workflow, then hover over the preview to swipe between the two
   images (click-dragging works too).

The node re-runs automatically if the fixed image file changes on disk.

## Credits

UI concept inspired by the Image Comparer node from
[rgthree-comfy](https://github.com/rgthree/rgthree-comfy) (MIT).

## License

[MIT](LICENSE)

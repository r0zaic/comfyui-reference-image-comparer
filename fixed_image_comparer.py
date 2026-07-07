import hashlib
import os

import numpy as np
import torch
from PIL import Image, ImageOps

import folder_paths
from nodes import PreviewImage


def _resolve_fixed_path(fixed_image, fixed_image_path):
    override = (fixed_image_path or "").strip().strip('"')
    if override:
        if not os.path.isfile(override):
            raise FileNotFoundError(f"Fixed image not found: {override}")
        return override
    if not fixed_image:
        raise ValueError(
            "Pick a fixed image in the node, or set fixed_image_path to an absolute path."
        )
    path = folder_paths.get_annotated_filepath(fixed_image)
    if not path or not os.path.isfile(path):
        raise FileNotFoundError(f"Fixed image not found in input folder: {fixed_image}")
    return path


def _load_image_tensor(path):
    img = Image.open(path)
    img = ImageOps.exif_transpose(img)
    img = img.convert("RGB")
    arr = np.array(img).astype(np.float32) / 255.0
    return torch.from_numpy(arr)[None,]


class FixedImageComparer(PreviewImage):
    """Compares a workflow result against a fixed reference image with a swipe slider."""

    @classmethod
    def INPUT_TYPES(cls):
        input_dir = folder_paths.get_input_directory()
        files = sorted(
            f for f in os.listdir(input_dir)
            if os.path.isfile(os.path.join(input_dir, f))
        )
        return {
            "required": {
                "fixed_image": (files, {"image_upload": True}),
            },
            "optional": {
                "image": ("IMAGE",),
                "fixed_image_path": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "Optional absolute path to the fixed image. Overrides the picker above.",
                    },
                ),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "compare"
    OUTPUT_NODE = True
    CATEGORY = "image"
    DESCRIPTION = (
        "Compares the generated image against a fixed reference image. "
        "Hover over the preview to swipe between fixed (left) and result (right)."
    )

    def compare(self, fixed_image=None, image=None, fixed_image_path="",
                prompt=None, extra_pnginfo=None):
        path = _resolve_fixed_path(fixed_image, fixed_image_path)
        fixed = _load_image_tensor(path)

        ui = {"a_images": [], "b_images": []}
        ui["a_images"] = self.save_images(
            fixed, "fixedcompare.a.", prompt, extra_pnginfo)["ui"]["images"]
        if image is not None and len(image) > 0:
            ui["b_images"] = self.save_images(
                image, "fixedcompare.b.", prompt, extra_pnginfo)["ui"]["images"]
        return {"ui": ui}

    @classmethod
    def IS_CHANGED(cls, fixed_image=None, fixed_image_path="", **kwargs):
        # Re-run when the fixed image file itself changes on disk.
        try:
            path = _resolve_fixed_path(fixed_image, fixed_image_path)
            m = hashlib.sha256()
            m.update(path.encode("utf-8"))
            m.update(str(os.path.getmtime(path)).encode("utf-8"))
            return m.hexdigest()
        except Exception:
            return float("NaN")

    @classmethod
    def VALIDATE_INPUTS(cls, fixed_image=None, fixed_image_path=""):
        # The path override may point anywhere and the combo list can be stale;
        # real validation happens in compare() with a clearer error message.
        return True

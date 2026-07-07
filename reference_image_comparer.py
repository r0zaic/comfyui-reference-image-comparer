import hashlib
import os

import numpy as np
import torch
from PIL import Image, ImageOps

import folder_paths
from nodes import PreviewImage


def _resolve_reference_path(reference_image, reference_image_path):
    override = (reference_image_path or "").strip().strip('"')
    if override:
        if not os.path.isfile(override):
            raise FileNotFoundError(f"Reference image not found: {override}")
        return override
    if not reference_image:
        raise ValueError(
            "Pick a reference image in the node, or set reference_image_path to an absolute path."
        )
    path = folder_paths.get_annotated_filepath(reference_image)
    if not path or not os.path.isfile(path):
        raise FileNotFoundError(f"Reference image not found in input folder: {reference_image}")
    return path


def _load_image_tensor(path):
    img = Image.open(path)
    img = ImageOps.exif_transpose(img)
    img = img.convert("RGB")
    arr = np.array(img).astype(np.float32) / 255.0
    return torch.from_numpy(arr)[None,]


class ReferenceImageComparer(PreviewImage):
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
                "reference_image": (files, {"image_upload": True}),
            },
            "optional": {
                "image": ("IMAGE",),
                "reference_image_path": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "Optional absolute path to the reference image. Overrides the picker above.",
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
        "Hover over the preview to swipe between reference (left) and result (right)."
    )

    def compare(self, reference_image=None, image=None, reference_image_path="",
                prompt=None, extra_pnginfo=None):
        path = _resolve_reference_path(reference_image, reference_image_path)
        reference = _load_image_tensor(path)

        ui = {"a_images": [], "b_images": []}
        ui["a_images"] = self.save_images(
            reference, "refcompare.a.", prompt, extra_pnginfo)["ui"]["images"]
        if image is not None and len(image) > 0:
            ui["b_images"] = self.save_images(
                image, "refcompare.b.", prompt, extra_pnginfo)["ui"]["images"]
        return {"ui": ui}

    @classmethod
    def IS_CHANGED(cls, reference_image=None, reference_image_path="", **kwargs):
        # Re-run when the reference image file itself changes on disk.
        try:
            path = _resolve_reference_path(reference_image, reference_image_path)
            m = hashlib.sha256()
            m.update(path.encode("utf-8"))
            m.update(str(os.path.getmtime(path)).encode("utf-8"))
            return m.hexdigest()
        except Exception:
            return float("NaN")

    @classmethod
    def VALIDATE_INPUTS(cls, reference_image=None, reference_image_path=""):
        # The path override may point anywhere and the combo list can be stale;
        # real validation happens in compare() with a clearer error message.
        return True

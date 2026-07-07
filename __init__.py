from .fixed_image_comparer import FixedImageComparer

NODE_CLASS_MAPPINGS = {
    "FixedImageComparer": FixedImageComparer,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FixedImageComparer": "Fixed Image Comparer",
}

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

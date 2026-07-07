from .reference_image_comparer import ReferenceImageComparer

NODE_CLASS_MAPPINGS = {
    "ReferenceImageComparer": ReferenceImageComparer,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ReferenceImageComparer": "Reference Image Comparer",
}

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

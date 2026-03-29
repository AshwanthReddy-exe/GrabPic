# ai-service/app/utils/image.py

import cv2
from app.config import settings


def load_image(path: str):
    """
    Load image from disk.
    """
    image = cv2.imread(path)

    if image is None:
        raise ValueError(f"Unable to load image: {path}")

    return image


def resize_image(image):
    """
    Resize image while maintaining aspect ratio.
    """
    h, w = image.shape[:2]

    if w > settings.MAX_IMAGE_WIDTH:
        scale = settings.MAX_IMAGE_WIDTH / w
        new_w = int(w * scale)
        new_h = int(h * scale)

        image = cv2.resize(image, (new_w, new_h))

    return image


def preprocess_image(path: str):
    """
    Full preprocessing pipeline:
    load → resize
    """
    image = load_image(path)
    image = resize_image(image)

    return image

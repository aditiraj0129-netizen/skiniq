"""
OCR Agent: reads raw text off a photographed product label.

Using EasyOCR (deep learning: CRAFT text detector + CRNN recognizer) instead
of traditional Tesseract -- meaningfully better at the small, curved,
low-contrast text typical of skincare product packaging.
"""
import easyocr
import numpy as np
from PIL import Image
import io
import re

_reader = None


def get_reader():
    """Lazy singleton -- EasyOCR loads model weights on first call, so we
    only want to pay that cost once per server lifetime, not per request."""
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(["en"], gpu=False)  # set gpu=True if you deploy with a GPU later
    return _reader


def extract_raw_text(image_bytes: bytes) -> str:
    """Runs OCR on the image, returns all detected text joined together."""
    reader = get_reader()
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img_array = np.array(img)

    results = reader.readtext(img_array, detail=0)  # detail=0 -> just the text strings
    raw_text = " ".join(results)
    return raw_text


def parse_ingredient_list(raw_text: str) -> list[str]:
    """
    Ingredient labels are typically comma-separated, sometimes with
    'Ingredients:' as a prefix. This splits the raw OCR text into
    individual candidate ingredient strings, cleaned up.

    OCR text is noisy (misread characters, merged words) -- we do light
    cleanup here, then rely on fuzzy matching (next agent) to handle the
    rest rather than trying to perfectly parse messy OCR output.
    """
    # Drop a leading "Ingredients:" / "INGREDIENTS" label if present
    text = re.sub(r"(?i)^.*?ingredients\s*:?", "", raw_text, count=1)

    # Split on commas (the standard separator on real ingredient labels)
    candidates = [c.strip() for c in text.split(",")]

    # Clean each candidate: remove stray punctuation/numbers OCR sometimes adds,
    # drop anything too short to be a real ingredient name
    cleaned = []
    for c in candidates:
        c = re.sub(r"[^A-Za-z\s\-]", "", c).strip()
        if len(c) >= 3:
            cleaned.append(c)

    return cleaned
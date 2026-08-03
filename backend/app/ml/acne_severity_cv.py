"""
Classical CV Acne Severity Agent.

Why this exists: the deep-learning acne head was trained on only ~10 images
with a binary (present/absent) label -- it cannot express graduated severity,
because it never saw that concept during training. Rather than pretend a
tiny binary classifier can output a meaningful percentage, we add a genuinely
different technique: face detection + color-space blob analysis to COUNT
inflamed spots, then map the count to a severity tier. This is classical CV,
not deep learning -- a deliberate, explainable complement to the vision
model, not a replacement for it everywhere.

Technique:
1. Detect the face region (Haar cascade -- ships with OpenCV, no download).
2. Convert to LAB color space; the 'a' channel encodes green-red intensity.
3. Normalize 'a' per-image (subtract the face's own median) so this works
   reasonably across different skin tones, rather than using fixed
   thresholds tuned to one tone.
4. Threshold for localized redness, find connected blobs, filter by
   plausible pimple size (too small = noise, too large = lighting/blush).
5. Map blob count to a severity tier and probability-like score.
"""
import cv2
import numpy as np

FACE_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

SEVERITY_TIERS = [
    (0, 0, 0.05, "clear"),
    (1, 2, 0.20, "mild -- a few isolated spots"),
    (3, 8, 0.60, "moderate -- breakout on part of the face"),
    (9, 999, 0.90, "widespread -- significant breakout across the face"),
]


def detect_face_region(img_bgr: np.ndarray) -> np.ndarray:
    """Returns the cropped face region, or the full image if no face is found
    (better to over-analyze than fail outright on an atypical photo)."""
    face_cascade = cv2.CascadeClassifier(FACE_CASCADE_PATH)
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))

    if len(faces) == 0:
        return img_bgr

    # Use the largest detected face (most likely the main subject)
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    return img_bgr[y:y + h, x:x + w]


def count_inflamed_blobs(face_bgr: np.ndarray) -> int:
    lab = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2LAB)
    a_channel = lab[:, :, 1].astype(np.float32)

    median_a = np.median(a_channel)
    redness = a_channel - median_a  # per-image normalized -- tone-robust

    # Threshold: pixels notably redder than this face's own baseline
    threshold = np.percentile(redness, 97)  # top ~3% reddest pixels
    threshold = max(threshold, 8)  # floor to avoid flagging near-uniform faces
    mask = (redness > threshold).astype(np.uint8) * 255

    # Clean up noise, then find connected blobs
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)

    face_area = face_bgr.shape[0] * face_bgr.shape[1]
    min_size = max(6, int(face_area * 0.0003))   # plausible pimple size range
    max_size = int(face_area * 0.02)

    blob_count = 0
    for i in range(1, num_labels):  # label 0 is background
        area = stats[i, cv2.CC_STAT_AREA]
        if min_size <= area <= max_size:
            blob_count += 1

    return blob_count


def estimate_acne_severity(image_bytes: bytes) -> dict:
    nparr = np.frombuffer(image_bytes, np.uint8)
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img_bgr is None:
        return {
            "blob_count": None, "severity_probability": None,
            "severity_label": "unable to process image", "method": "classical-cv",
        }

    face_region = detect_face_region(img_bgr)
    blob_count = count_inflamed_blobs(face_region)

    for low, high, prob, label in SEVERITY_TIERS:
        if low <= blob_count <= high:
            return {
                "blob_count": blob_count,
                "severity_probability": prob,
                "severity_label": label,
                "method": "classical-cv (color-space blob detection)",
            }

    return {
        "blob_count": blob_count, "severity_probability": 0.90,
        "severity_label": "widespread", "method": "classical-cv",
    }
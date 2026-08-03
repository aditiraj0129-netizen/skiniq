import os
import torch
import torchvision.transforms as T
from PIL import Image
import io

from app.ml.model_def import load_model
from app.ml.acne_severity_cv import estimate_acne_severity

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
WEIGHTS_PATH = os.path.join(os.path.dirname(__file__), "skiniq_vision_model_v2.pt")

IMG_SIZE = 224
transform = T.Compose([
    T.Resize((IMG_SIZE, IMG_SIZE)),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

TYPE_LABELS = ["dry", "normal", "oily"]

_model = None
_tone_qhat = None


def get_model():
    global _model, _tone_qhat
    if _model is None:
        if not os.path.exists(WEIGHTS_PATH):
            raise FileNotFoundError(f"Model weights not found at {WEIGHTS_PATH}")
        _model, _tone_qhat = load_model(WEIGHTS_PATH, device=DEVICE)
    return _model, _tone_qhat


def analyze_skin_image(image_bytes: bytes) -> dict:
    model, tone_qhat = get_model()

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img_tensor = transform(img).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        preds = model(img_tensor)

    tone_val = preds["tone"].cpu().item()
    dc_prob = torch.sigmoid(preds["darkcircle"]).cpu().item()
    type_probs = torch.softmax(preds["type"].cpu(), dim=-1).squeeze()
    type_pred = TYPE_LABELS[type_probs.argmax().item()]
    type_conf = type_probs.max().item()

    # Acne severity: classical CV blob-counting, NOT the deep model's raw
    # sigmoid output -- see acne_severity_cv.py for why. The deep model's
    # binary signal is kept alongside for transparency, not as the primary score.
    deep_model_acne_signal = torch.sigmoid(preds["acne"]).cpu().item()
    cv_acne = estimate_acne_severity(image_bytes)

    result = {
        "skin_tone_fitzpatrick_estimate": round(tone_val, 2),
        "tone_confidence_interval_90": (
            [round(tone_val - tone_qhat, 2), round(tone_val + tone_qhat, 2)]
            if tone_qhat is not None else None
        ),
        "skin_type": type_pred,
        "skin_type_confidence": round(type_conf, 2),
        "acne_probability": cv_acne["severity_probability"],
        "acne_severity_label": cv_acne["severity_label"],
        "acne_spot_count_estimate": cv_acne["blob_count"],
        "acne_method": cv_acne["method"],
        "acne_deep_model_raw_signal": round(deep_model_acne_signal, 2),
        "acne_confidence_note": (
            "Severity is estimated via spot-counting (classical computer vision), "
            "calibrated to be graduated rather than a single trained-on-limited-data score."
        ),
        "darkcircle_probability": round(dc_prob, 2),
        "darkcircle_confidence_note": "Trained on limited data - treat as indicative only.",
        "disclaimer": (
            "This is an automated estimate, not a medical or dermatological "
            "diagnosis. Please verify with a licensed dermatologist."
        ),
    }
    return result
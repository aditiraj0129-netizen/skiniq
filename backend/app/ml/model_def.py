import torch
import torch.nn as nn
import timm


class MultiTaskSkinModel(nn.Module):
    def __init__(self, backbone_name="vit_small_patch14_dinov2.lvd142m"):
        super().__init__()
        self.backbone = timm.create_model(
            backbone_name, pretrained=False, num_classes=0, dynamic_img_size=True
        )
        feat_dim = self.backbone.num_features

        self.tone_head = nn.Linear(feat_dim, 1)
        self.type_head = nn.Linear(feat_dim, 3)
        self.acne_head = nn.Linear(feat_dim, 1)
        self.darkcircle_head = nn.Linear(feat_dim, 1)

    def forward(self, x):
        feats = self.backbone(x)
        return {
            "tone": self.tone_head(feats).squeeze(-1),
            "type": self.type_head(feats),
            "acne": self.acne_head(feats).squeeze(-1),
            "darkcircle": self.darkcircle_head(feats).squeeze(-1),
        }


def load_model(weights_path: str, device: str = "cpu"):
    checkpoint = torch.load(weights_path, map_location=device, weights_only=False)
    model = MultiTaskSkinModel()
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()
    tone_qhat = checkpoint.get("tone_qhat", None)
    return model, tone_qhat
import torch

model_path = "/Users/akashvishwakarma/Hackathon-2026/Hackive2.0/best_model (1).pth"
data = torch.load(model_path, map_location="cpu")
import timm

for model_name in timm.list_models():
    if "efficientnet" in model_name or "vit" in model_name: 
        try:
            m = timm.create_model(model_name, pretrained=False)
            if hasattr(m, 'conv_stem') and m.conv_stem.out_channels == 48:
                print("Match found:", model_name)
        except Exception:
            pass

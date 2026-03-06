import torch

model_path = "/Users/akashvishwakarma/Hackathon-2026/Hackive2.0/best_model (1).pth"
data = torch.load(model_path, map_location="cpu")
state_dict = data['model_state_dict']
head_keys = sorted([k for k in state_dict.keys() if k.startswith('head.')])
for k in head_keys:
    print(k, state_dict[k].shape)

import torch

model_path = "/Users/akashvishwakarma/Hackathon-2026/Hackive2.0/best_model (1).pth"
data = torch.load(model_path, map_location="cpu")
head_keys = [k for k in data['model_state_dict'].keys() if k.startswith('head.')]
for k in head_keys: print(k, data['model_state_dict'][k].shape)

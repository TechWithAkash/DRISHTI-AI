import torch

model_path = "/Users/akashvishwakarma/Hackathon-2026/Hackive2.0/best_model (1).pth"
data = torch.load(model_path, map_location="cpu")
keys = list(data['model_state_dict'].keys())
print("Last 10 keys:", keys[-10:])

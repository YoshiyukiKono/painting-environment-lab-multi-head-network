import torch
from torch import nn

class MultiHeadPaintingPolicy(nn.Module):
    def __init__(self, stroke_count, image_size=16):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(6, 32, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 64, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Flatten(),
        )
        features = 64 * (image_size // 4) * (image_size // 4)
        self.shared = nn.Sequential(nn.Linear(features, 256), nn.ReLU())
        self.stroke_head = nn.Linear(256, stroke_count)
        self.improvement_head = nn.Linear(256, 1)

    def forward(self, observation):
        feature = self.shared(self.encoder(observation))
        return self.stroke_head(feature), self.improvement_head(feature).squeeze(-1)

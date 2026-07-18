from pathlib import Path
import numpy as np
from torch.utils.data import Dataset

class PaintingDataset(Dataset):
    def __init__(self, observations, stroke_labels, improvement_labels):
        self.observations = np.asarray(observations, dtype=np.float32)
        self.stroke_labels = np.asarray(stroke_labels, dtype=np.int64)
        self.improvement_labels = np.asarray(improvement_labels, dtype=np.float32)

    @classmethod
    def load(cls, path):
        data = np.load(path)
        return cls(data["observations"], data["stroke_labels"], data["improvement_labels"])

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            path,
            observations=self.observations,
            stroke_labels=self.stroke_labels,
            improvement_labels=self.improvement_labels,
        )

    def __len__(self):
        return len(self.stroke_labels)

    def __getitem__(self, index):
        return self.observations[index], self.stroke_labels[index], self.improvement_labels[index]

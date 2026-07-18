import argparse
from pathlib import Path
import numpy as np
import torch
from painting_multi_head.dataset import PaintingDataset
from painting_multi_head.model import MultiHeadPaintingPolicy
from painting_multi_head.transforms import ImprovementTransform

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", type=Path, required=True)
    p.add_argument("--model", type=Path, required=True)
    p.add_argument("--teacher-threshold", type=float, default=1e-4)
    args = p.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ckpt = torch.load(args.model, map_location=device)
    model = MultiHeadPaintingPolicy(ckpt["stroke_count"], ckpt["image_size"]).to(device)
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    transform = ImprovementTransform.from_dict(ckpt["transform"])
    dataset = PaintingDataset.load(args.dataset)

    with torch.no_grad():
        _, encoded = model(torch.from_numpy(dataset.observations).to(device))
    predicted = transform.decode(encoded.cpu().numpy())
    truth = dataset.improvement_labels <= args.teacher_threshold

    candidates = np.quantile(predicted, np.linspace(0.0, 1.0, 101))
    best = None
    for threshold in candidates:
        guessed = predicted <= threshold
        accuracy = float(np.mean(guessed == truth))
        if best is None or accuracy > best[0]:
            best = (accuracy, float(threshold))
    print(f"best_stop_accuracy={best[0]:.4f}")
    print(f"recommended_threshold={best[1]:.10f}")

if __name__ == "__main__":
    main()

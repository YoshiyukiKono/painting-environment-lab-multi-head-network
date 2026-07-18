import argparse, json
from pathlib import Path
import torch
from painting_multi_head.dataset import PaintingDataset
from painting_multi_head.diagnostics import diagnose
from painting_multi_head.model import MultiHeadPaintingPolicy
from painting_multi_head.transforms import ImprovementTransform

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", type=Path, required=True)
    p.add_argument("--model", type=Path, required=True)
    args = p.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ckpt = torch.load(args.model, map_location=device)
    model = MultiHeadPaintingPolicy(ckpt["stroke_count"], ckpt["image_size"]).to(device)
    model.load_state_dict(ckpt["state_dict"])
    transform = ImprovementTransform.from_dict(ckpt["transform"])
    metrics = diagnose(model, PaintingDataset.load(args.dataset), transform)
    print(json.dumps(metrics, indent=2))

if __name__ == "__main__":
    main()

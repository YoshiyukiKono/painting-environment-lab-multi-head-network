import argparse
from pathlib import Path
import torch
from painting_multi_head.action_space import DiscreteStrokeActionSpace
from painting_multi_head.dataset import PaintingDataset
from painting_multi_head.training import train_joint
from painting_multi_head.transforms import ImprovementTransform

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", type=Path, required=True)
    p.add_argument("--epochs", type=int, default=20)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--target-transform", choices=["raw", "standardized", "log"], default="standardized")
    p.add_argument("--improvement-weight", type=float, default=1.0)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()

    dataset = PaintingDataset.load(args.dataset)
    transform = ImprovementTransform.fit(dataset.improvement_labels, args.target_transform)
    space = DiscreteStrokeActionSpace()
    model = train_joint(
        dataset,
        transform,
        space.n,
        dataset.observations.shape[-1],
        epochs=args.epochs,
        batch_size=args.batch_size,
        improvement_weight=args.improvement_weight,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    torch.save({
        "state_dict": model.state_dict(),
        "stroke_count": space.n,
        "image_size": dataset.observations.shape[-1],
        "transform": transform.to_dict(),
    }, args.output)
    print(f"saved={args.output}")

if __name__ == "__main__":
    main()

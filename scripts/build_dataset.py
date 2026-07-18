import argparse
from pathlib import Path
import numpy as np
from painting_multi_head.action_space import DiscreteStrokeActionSpace
from painting_multi_head.dataset import PaintingDataset
from painting_multi_head.environment import PaintingEnvironment
from painting_multi_head.targets import random_target
from painting_multi_head.teacher import GreedyTeacher

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--episodes", type=int, default=300)
    p.add_argument("--size", type=int, default=16)
    p.add_argument("--max-steps", type=int, default=32)
    p.add_argument("--stop-threshold", type=float, default=1e-4)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--output", type=Path, default=Path("artifacts/dataset.npz"))
    args = p.parse_args()

    rng = np.random.default_rng(args.seed)
    space = DiscreteStrokeActionSpace()
    teacher = GreedyTeacher()
    observations, strokes, improvements = [], [], []

    for _ in range(args.episodes):
        env = PaintingEnvironment(random_target(rng, args.size), space, max_steps=args.max_steps)
        while not env.done:
            label = teacher.label(env)
            observations.append(env.observation())
            strokes.append(label.stroke_index)
            improvements.append(label.best_improvement)
            if label.best_improvement <= args.stop_threshold:
                env.stop()
            else:
                env.apply_stroke(label.stroke_index)

    dataset = PaintingDataset(observations, strokes, improvements)
    dataset.save(args.output)
    print(f"saved={args.output} samples={len(dataset)}")
    print(f"improvement min={np.min(improvements):.8f}")
    print(f"improvement mean={np.mean(improvements):.8f}")
    print(f"improvement max={np.max(improvements):.8f}")

if __name__ == "__main__":
    main()

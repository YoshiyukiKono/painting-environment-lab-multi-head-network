#!/usr/bin/env python3
"""Run a Student policy while querying the Greedy Teacher at every visited state.

This script is intended for Experiment 2 (Teacher vs Student / Oracle diagnosis).
It leaves scripts/run_demo.py unchanged and writes its own diagnostic artifacts.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image

from painting_multi_head.action_space import DiscreteStrokeActionSpace
from painting_multi_head.environment import PaintingEnvironment
from painting_multi_head.model import MultiHeadPaintingPolicy
from painting_multi_head.targets import random_target
from painting_multi_head.teacher import GreedyTeacher
from painting_multi_head.transforms import ImprovementTransform


def as_image(array: np.ndarray, scale: int = 16) -> Image.Image:
    """Convert a float image in [0, 1] into an enlarged preview image."""
    image = Image.fromarray(
        np.clip(array * 255, 0, 255).astype(np.uint8)
    )
    return image.resize(
        (image.width * scale, image.height * scale),
        Image.Resampling.NEAREST,
    )


def longest_repeated_action(actions: list[int]) -> dict[str, int | None]:
    """Return the action and length of the longest consecutive action run."""
    if not actions:
        return {"stroke_index": None, "count": 0}

    best_action = actions[0]
    best_count = 1
    current_action = actions[0]
    current_count = 1

    for action in actions[1:]:
        if action == current_action:
            current_count += 1
        else:
            current_action = action
            current_count = 1

        if current_count > best_count:
            best_action = current_action
            best_count = current_count

    return {
        "stroke_index": int(best_action),
        "count": int(best_count),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the Student policy and query the Greedy Teacher "
            "at every Student-visited state."
        )
    )
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--stop-threshold", type=float, default=1e-4)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--max-steps", type=int, default=32)
    parser.add_argument(
        "--target-kind",
        choices=["flat", "rectangle", "circle", "gradient"],
        default="gradient",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.model.exists():
        raise FileNotFoundError(f"Model checkpoint not found: {args.model}")
    if args.max_steps <= 0:
        raise ValueError("--max-steps must be greater than zero")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(args.model, map_location=device)

    model = MultiHeadPaintingPolicy(
        checkpoint["stroke_count"],
        checkpoint["image_size"],
    ).to(device)
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()

    transform = ImprovementTransform.from_dict(checkpoint["transform"])

    rng = np.random.default_rng(args.seed)
    target = random_target(
        rng,
        checkpoint["image_size"],
        kind=args.target_kind,
    )

    action_space = DiscreteStrokeActionSpace()
    env = PaintingEnvironment(
        target,
        action_space,
        max_steps=args.max_steps,
    )
    teacher = GreedyTeacher()

    initial_error = float(env.error())
    frames = [as_image(env.canvas)]
    trajectory: list[dict[str, Any]] = []

    while not env.done:
        step = int(env.step_count)
        error_before = float(env.error())

        observation = torch.from_numpy(env.observation()).unsqueeze(0).to(device)

        with torch.no_grad():
            logits, encoded_improvement = model(observation)

        student_stroke_index = int(logits.argmax(dim=1).item())
        predicted_improvement = float(
            transform.decode(encoded_improvement.cpu().numpy())[0]
        )

        # Query the oracle on exactly the same state observed by the Student.
        teacher_label = teacher.label(env)
        teacher_stroke_index = int(teacher_label.stroke_index)
        teacher_best_improvement = float(
            teacher_label.best_improvement
        )

        if predicted_improvement <= args.stop_threshold:
            premature_stop = (
                teacher_best_improvement > args.stop_threshold
            )

            env.stop()

            trajectory.append(
                {
                    "step": step,
                    "decision": "stop",
                    "predicted_improvement": predicted_improvement,
                    "teacher_stroke_index": teacher_stroke_index,
                    "teacher_best_improvement": teacher_best_improvement,
                    "premature_stop": bool(premature_stop),
                    "error_before": error_before,
                    "error_after": error_before,
                }
            )
            break

        actual_improvement = float(
            env.apply_stroke(student_stroke_index)
        )
        error_after = float(env.error())

        # Regret is measured against the best one-step action available
        # at the state before the Student action was applied.
        action_regret = float(
            teacher_best_improvement - actual_improvement
        )
        # Numerical noise should not create tiny negative regret values.
        if abs(action_regret) < 1e-12:
            action_regret = 0.0

        trajectory.append(
            {
                "step": step,
                "decision": "stroke",
                "stroke_index": student_stroke_index,
                "predicted_improvement": predicted_improvement,
                "actual_improvement": actual_improvement,
                "teacher_stroke_index": teacher_stroke_index,
                "teacher_best_improvement": teacher_best_improvement,
                "action_match": (
                    student_stroke_index == teacher_stroke_index
                ),
                "action_regret": action_regret,
                "error_before": error_before,
                "error_after": error_after,
            }
        )

        frames.append(as_image(env.canvas))

    stroke_entries = [
        entry for entry in trajectory
        if entry["decision"] == "stroke"
    ]
    stop_entries = [
        entry for entry in trajectory
        if entry["decision"] == "stop"
    ]

    actions = [
        int(entry["stroke_index"])
        for entry in stroke_entries
    ]
    actual_improvements = [
        float(entry["actual_improvement"])
        for entry in stroke_entries
    ]
    predicted_improvements = [
        float(entry["predicted_improvement"])
        for entry in stroke_entries
    ]
    action_regrets = [
        float(entry["action_regret"])
        for entry in stroke_entries
    ]

    action_match_count = sum(
        bool(entry["action_match"])
        for entry in stroke_entries
    )
    stroke_count = len(stroke_entries)

    prediction_absolute_errors = [
        abs(predicted - actual)
        for predicted, actual in zip(
            predicted_improvements,
            actual_improvements,
        )
    ]

    final_error = float(env.error())

    result = {
        "policy": "student_with_greedy_teacher_diagnosis",
        "seed": int(args.seed),
        "target_kind": args.target_kind,
        "image_size": int(checkpoint["image_size"]),
        "max_steps": int(args.max_steps),
        "stop_threshold": float(args.stop_threshold),
        "device": str(device),
        "initial_error": initial_error,
        "final_error": final_error,
        "error_reduction": float(initial_error - final_error),
        "steps": int(env.step_count),
        "stop_reason": env.stop_reason,
        "total_actual_improvement": float(sum(actual_improvements)),
        "positive_improvement_steps": int(
            sum(value > 0.0 for value in actual_improvements)
        ),
        "zero_improvement_steps": int(
            sum(value == 0.0 for value in actual_improvements)
        ),
        "negative_improvement_steps": int(
            sum(value < 0.0 for value in actual_improvements)
        ),
        "longest_repeated_action": longest_repeated_action(actions),
        "oracle_action_match_count": int(action_match_count),
        "oracle_action_match_rate": (
            float(action_match_count / stroke_count)
            if stroke_count
            else 0.0
        ),
        "total_action_regret": float(sum(action_regrets)),
        "mean_action_regret": (
            float(sum(action_regrets) / stroke_count)
            if stroke_count
            else 0.0
        ),
        "max_action_regret": (
            float(max(action_regrets))
            if action_regrets
            else 0.0
        ),
        "trajectory_prediction_mae": (
            float(
                sum(prediction_absolute_errors)
                / len(prediction_absolute_errors)
            )
            if prediction_absolute_errors
            else 0.0
        ),
        "premature_stop": (
            bool(stop_entries[0]["premature_stop"])
            if stop_entries
            else False
        ),
        "teacher_improvement_at_student_stop": (
            float(stop_entries[0]["teacher_best_improvement"])
            if stop_entries
            else None
        ),
        "teacher_action_at_student_stop": (
            int(stop_entries[0]["teacher_stroke_index"])
            if stop_entries
            else None
        ),
        "trajectory": trajectory,
    }

    as_image(target).save(args.output_dir / "target.png")
    as_image(env.canvas).save(
        args.output_dir / "final_canvas.png"
    )

    frames[0].save(
        args.output_dir / "trajectory.gif",
        save_all=True,
        append_images=frames[1:],
        duration=180,
        loop=0,
    )

    result_path = args.output_dir / "result.json"
    result_path.write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

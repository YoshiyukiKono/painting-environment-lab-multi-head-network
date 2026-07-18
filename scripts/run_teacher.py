import argparse
import json
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from painting_multi_head.action_space import DiscreteStrokeActionSpace
from painting_multi_head.environment import PaintingEnvironment
from painting_multi_head.targets import random_target
from painting_multi_head.teacher import GreedyTeacher


def as_image(array: np.ndarray, scale: int = 16) -> Image.Image:
    """0〜1のfloat画像を、確認しやすいNearest Neighbor拡大画像へ変換する。"""
    image = Image.fromarray(
        np.clip(array * 255, 0, 255).astype(np.uint8)
    )
    return image.resize(
        (image.width * scale, image.height * scale),
        Image.Resampling.NEAREST,
    )


def longest_repeated_action(actions: list[int]) -> dict:
    """同じStrokeが連続した最大回数を返す。"""
    if not actions:
        return {
            "stroke_index": None,
            "count": 0,
        }

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
        "stroke_index": best_action,
        "count": best_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Greedy TeacherによるPainting rolloutを実行する。"
    )
    parser.add_argument(
        "--model",
        type=Path,
        required=True,
        help="Student checkpoint。画像サイズをStudentと一致させるために使用する。",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--stop-threshold",
        type=float,
        default=1e-4,
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=7,
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=32,
    )
    parser.add_argument(
        "--target-kind",
        choices=["flat", "rectangle", "circle", "gradient"],
        default="gradient",
        help="run_demo.pyと同じTarget種別を指定する。",
    )
    args = parser.parse_args()

    if not args.model.exists():
        raise FileNotFoundError(f"Model checkpoint not found: {args.model}")

    if args.max_steps <= 0:
        raise ValueError("--max-steps must be greater than zero")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Teacher自体はモデルを使わない。
    # Studentと画像サイズを確実に一致させるため、checkpointのmetadataだけ読む。
    checkpoint = torch.load(args.model, map_location="cpu")

    if "image_size" not in checkpoint:
        raise KeyError("Checkpoint does not contain 'image_size'")

    image_size = int(checkpoint["image_size"])

    rng = np.random.default_rng(args.seed)
    target = random_target(
        rng,
        image_size,
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
    trajectory = []

    teacher_stopped = False

    while not env.done:
        error_before = float(env.error())
        label = teacher.label(env)

        if label.best_improvement <= args.stop_threshold:
            env.stop()
            teacher_stopped = True

            trajectory.append(
                {
                    "step": env.step_count,
                    "decision": "stop",
                    "teacher_stroke_index": int(label.stroke_index),
                    "teacher_best_improvement": float(
                        label.best_improvement
                    ),
                    "error_before": error_before,
                    "error_after": error_before,
                }
            )
            break

        actual_improvement = float(
            env.apply_stroke(label.stroke_index)
        )
        error_after = float(env.error())

        trajectory.append(
            {
                "step": env.step_count - 1,
                "decision": "stroke",
                "stroke_index": int(label.stroke_index),
                "teacher_best_improvement": float(
                    label.best_improvement
                ),
                "actual_improvement": actual_improvement,
                "error_before": error_before,
                "error_after": error_after,
            }
        )

        frames.append(as_image(env.canvas))

    stroke_entries = [
        entry
        for entry in trajectory
        if entry["decision"] == "stroke"
    ]

    actions = [
        int(entry["stroke_index"])
        for entry in stroke_entries
    ]
    improvements = [
        float(entry["actual_improvement"])
        for entry in stroke_entries
    ]

    final_error = float(env.error())
    total_actual_improvement = float(sum(improvements))

    # env.stop()は内部的にpolicy_stopという名前を付けるため、
    # Teacher実験の出力上はteacher_stopへ読み替える。
    stop_reason = (
        "teacher_stop"
        if teacher_stopped
        else env.stop_reason
    )

    result = {
        "policy": "greedy_teacher",
        "seed": args.seed,
        "target_kind": args.target_kind,
        "image_size": image_size,
        "max_steps": args.max_steps,
        "stop_threshold": args.stop_threshold,
        "initial_error": initial_error,
        "final_error": final_error,
        "error_reduction": initial_error - final_error,
        "steps": env.step_count,
        "stop_reason": stop_reason,
        "total_actual_improvement": total_actual_improvement,
        "positive_improvement_steps": sum(
            value > 0.0 for value in improvements
        ),
        "zero_improvement_steps": sum(
            value == 0.0 for value in improvements
        ),
        "negative_improvement_steps": sum(
            value < 0.0 for value in improvements
        ),
        "longest_repeated_action": longest_repeated_action(actions),
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

#!/usr/bin/env python3
"""Run Experiment 3 trajectory analysis for one seed.

The script deliberately reuses ``run_demo_oracle.py`` instead of duplicating
the Student/Teacher rollout implementation. It runs the oracle diagnostic for
one seed, enriches the step-level trajectory, writes CSV/JSON summaries, and
creates four dependency-free PNG plots using Pillow.

Expected outputs:

- result.json                  Original Experiment 2 oracle result
- trajectory.csv              Step-level analysis table
- trajectory-analysis.json    Experiment 3 summary and enriched trajectory
- error-trajectory.png
- improvement-trajectory.png
- action-regret.png
- action-sequence.png

The target/canvas previews and trajectory GIF produced by run_demo_oracle.py
are retained in the same output directory.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

from PIL import Image, ImageDraw, ImageFont


PLOT_WIDTH = 1100
PLOT_HEIGHT = 640
MARGIN_LEFT = 105
MARGIN_RIGHT = 35
MARGIN_TOP = 55
MARGIN_BOTTOM = 85

BACKGROUND = (255, 255, 255)
FOREGROUND = (35, 35, 35)
MUTED = (115, 115, 115)
GRID = (225, 225, 225)
SERIES_COLORS = (
    (31, 119, 180),
    (214, 39, 40),
    (44, 160, 44),
    (148, 103, 189),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run one Student/Teacher oracle trajectory and create "
            "Experiment 3 step-by-step analysis artifacts."
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
    parser.add_argument(
        "--large-regret-threshold",
        type=float,
        default=0.005,
        help="Threshold used only for the first_large_regret_step diagnostic.",
    )
    parser.add_argument(
        "--skip-rollout",
        action="store_true",
        help=(
            "Analyze an existing output-dir/result.json without rerunning "
            "run_demo_oracle.py."
        ),
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if not args.skip_rollout and not args.model.exists():
        raise FileNotFoundError(f"Model checkpoint not found: {args.model}")
    if args.max_steps <= 0:
        raise ValueError("--max-steps must be greater than zero")
    if args.large_regret_threshold < 0:
        raise ValueError("--large-regret-threshold must be non-negative")


def run_oracle(args: argparse.Namespace) -> None:
    oracle_script = Path(__file__).with_name("run_demo_oracle.py")
    if not oracle_script.exists():
        raise FileNotFoundError(
            f"Oracle diagnostic script not found: {oracle_script}"
        )

    command = [
        sys.executable,
        str(oracle_script),
        "--model",
        str(args.model),
        "--output-dir",
        str(args.output_dir),
        "--stop-threshold",
        str(args.stop_threshold),
        "--seed",
        str(args.seed),
        "--max-steps",
        str(args.max_steps),
        "--target-kind",
        args.target_kind,
    ]
    print("Running oracle diagnostic:")
    print(" ".join(command))
    subprocess.run(command, check=True)


def load_result(output_dir: Path) -> dict[str, Any]:
    result_path = output_dir / "result.json"
    if not result_path.exists():
        raise FileNotFoundError(
            f"Oracle result not found: {result_path}. "
            "Run without --skip-rollout first."
        )
    return json.loads(result_path.read_text(encoding="utf-8"))


def enrich_trajectory(
    trajectory: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    previous_action: int | None = None
    repeated_action_count = 0

    for raw_entry in trajectory:
        entry = dict(raw_entry)
        if entry.get("decision") == "stroke":
            action = int(entry["stroke_index"])
            if action == previous_action:
                repeated_action_count += 1
            else:
                repeated_action_count = 1
            previous_action = action

            predicted = float(entry["predicted_improvement"])
            actual = float(entry["actual_improvement"])
            entry["prediction_error"] = predicted - actual
            entry["prediction_absolute_error"] = abs(predicted - actual)
            entry["repeated_action_count"] = repeated_action_count
        else:
            entry.setdefault("actual_improvement", None)
            entry.setdefault("action_regret", None)
            entry.setdefault("action_match", None)
            entry.setdefault("stroke_index", None)
            entry["prediction_error"] = None
            entry["prediction_absolute_error"] = None
            entry["repeated_action_count"] = 0

        enriched.append(entry)

    return enriched


def first_step(
    entries: Iterable[dict[str, Any]],
    predicate: Callable[[dict[str, Any]], bool],
) -> int | None:
    for entry in entries:
        if predicate(entry):
            return int(entry["step"])
    return None


def build_summary(
    result: dict[str, Any],
    trajectory: Sequence[dict[str, Any]],
    large_regret_threshold: float,
) -> dict[str, Any]:
    stroke_entries = [
        entry for entry in trajectory if entry["decision"] == "stroke"
    ]
    prediction_errors = [
        float(entry["prediction_error"]) for entry in stroke_entries
    ]

    first_repeated_action_step = first_step(
        stroke_entries,
        lambda entry: int(entry["repeated_action_count"]) >= 2,
    )
    first_zero_improvement_step = first_step(
        stroke_entries,
        lambda entry: float(entry["actual_improvement"]) == 0.0,
    )
    first_negative_improvement_step = first_step(
        stroke_entries,
        lambda entry: float(entry["actual_improvement"]) < 0.0,
    )
    first_large_regret_step = first_step(
        stroke_entries,
        lambda entry: float(entry["action_regret"])
        >= large_regret_threshold,
    )

    summary = {
        "experiment": "experiment_03_trajectory_analysis",
        "seed": int(result["seed"]),
        "target_kind": result["target_kind"],
        "steps": int(result["steps"]),
        "final_error": float(result["final_error"]),
        "stop_reason": result["stop_reason"],
        "oracle_action_match_rate": float(
            result["oracle_action_match_rate"]
        ),
        "total_action_regret": float(result["total_action_regret"]),
        "mean_action_regret": float(result["mean_action_regret"]),
        "max_action_regret": float(result["max_action_regret"]),
        "trajectory_prediction_mae": float(
            result["trajectory_prediction_mae"]
        ),
        "prediction_bias": (
            float(sum(prediction_errors) / len(prediction_errors))
            if prediction_errors
            else 0.0
        ),
        "zero_improvement_steps": int(
            result["zero_improvement_steps"]
        ),
        "negative_improvement_steps": int(
            result["negative_improvement_steps"]
        ),
        "longest_repeated_action": result["longest_repeated_action"],
        "premature_stop": bool(result["premature_stop"]),
        "teacher_improvement_at_student_stop": result[
            "teacher_improvement_at_student_stop"
        ],
        "first_zero_improvement_step": first_zero_improvement_step,
        "first_negative_improvement_step": (
            first_negative_improvement_step
        ),
        "first_repeated_action_step": first_repeated_action_step,
        "large_regret_threshold": float(large_regret_threshold),
        "first_large_regret_step": first_large_regret_step,
    }
    return summary


def write_trajectory_csv(
    output_path: Path,
    trajectory: Sequence[dict[str, Any]],
) -> None:
    fields = [
        "step",
        "decision",
        "stroke_index",
        "teacher_stroke_index",
        "action_match",
        "predicted_improvement",
        "actual_improvement",
        "teacher_best_improvement",
        "action_regret",
        "prediction_error",
        "prediction_absolute_error",
        "error_before",
        "error_after",
        "repeated_action_count",
        "premature_stop",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for entry in trajectory:
            writer.writerow({field: entry.get(field) for field in fields})


def font() -> ImageFont.ImageFont:
    return ImageFont.load_default()


def nice_bounds(values: Sequence[float]) -> tuple[float, float]:
    finite_values = [value for value in values if math.isfinite(value)]
    if not finite_values:
        return 0.0, 1.0

    minimum = min(finite_values)
    maximum = max(finite_values)
    if math.isclose(minimum, maximum):
        padding = max(abs(minimum) * 0.1, 1e-6)
        return minimum - padding, maximum + padding

    padding = (maximum - minimum) * 0.08
    return minimum - padding, maximum + padding


def draw_axes(
    draw: ImageDraw.ImageDraw,
    title: str,
    x_label: str,
    y_label: str,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
) -> None:
    plot_left = MARGIN_LEFT
    plot_right = PLOT_WIDTH - MARGIN_RIGHT
    plot_top = MARGIN_TOP
    plot_bottom = PLOT_HEIGHT - MARGIN_BOTTOM

    draw.text((MARGIN_LEFT, 18), title, fill=FOREGROUND, font=font())
    draw.line(
        (plot_left, plot_bottom, plot_right, plot_bottom),
        fill=FOREGROUND,
        width=2,
    )
    draw.line(
        (plot_left, plot_top, plot_left, plot_bottom),
        fill=FOREGROUND,
        width=2,
    )

    for index in range(6):
        ratio = index / 5
        y = plot_bottom - ratio * (plot_bottom - plot_top)
        value = y_min + ratio * (y_max - y_min)
        draw.line(
            (plot_left, y, plot_right, y),
            fill=GRID,
            width=1,
        )
        draw.text(
            (8, y - 7),
            f"{value:.5g}",
            fill=MUTED,
            font=font(),
        )

    for index in range(6):
        ratio = index / 5
        x = plot_left + ratio * (plot_right - plot_left)
        value = x_min + ratio * (x_max - x_min)
        draw.line(
            (x, plot_top, x, plot_bottom),
            fill=GRID,
            width=1,
        )
        draw.text(
            (x - 10, plot_bottom + 12),
            f"{value:.4g}",
            fill=MUTED,
            font=font(),
        )

    draw.text(
        ((plot_left + plot_right) / 2 - 20, PLOT_HEIGHT - 35),
        x_label,
        fill=FOREGROUND,
        font=font(),
    )
    draw.text(
        (8, MARGIN_TOP - 22),
        y_label,
        fill=FOREGROUND,
        font=font(),
    )


def map_point(
    x: float,
    y: float,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
) -> tuple[float, float]:
    plot_left = MARGIN_LEFT
    plot_right = PLOT_WIDTH - MARGIN_RIGHT
    plot_top = MARGIN_TOP
    plot_bottom = PLOT_HEIGHT - MARGIN_BOTTOM

    x_ratio = 0.0 if x_max == x_min else (x - x_min) / (x_max - x_min)
    y_ratio = 0.0 if y_max == y_min else (y - y_min) / (y_max - y_min)
    pixel_x = plot_left + x_ratio * (plot_right - plot_left)
    pixel_y = plot_bottom - y_ratio * (plot_bottom - plot_top)
    return pixel_x, pixel_y


def draw_legend(
    draw: ImageDraw.ImageDraw,
    labels: Sequence[str],
    colors: Sequence[tuple[int, int, int]],
) -> None:
    x = MARGIN_LEFT + 10
    y = MARGIN_TOP + 8
    for label, color in zip(labels, colors):
        draw.line((x, y + 5, x + 24, y + 5), fill=color, width=3)
        draw.text((x + 30, y), label, fill=FOREGROUND, font=font())
        x += 30 + max(90, len(label) * 7)


def save_line_plot(
    output_path: Path,
    title: str,
    y_label: str,
    series: Sequence[tuple[str, Sequence[tuple[float, float]]]],
    include_zero: bool = False,
    scatter: bool = False,
) -> None:
    points = [point for _, values in series for point in values]
    if not points:
        return

    x_values = [point[0] for point in points]
    y_values = [point[1] for point in points]
    x_min, x_max = nice_bounds(x_values)
    y_min, y_max = nice_bounds(y_values)
    if include_zero:
        y_min = min(y_min, 0.0)
        y_max = max(y_max, 0.0)

    image = Image.new("RGB", (PLOT_WIDTH, PLOT_HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)
    draw_axes(
        draw,
        title,
        "step",
        y_label,
        x_min,
        x_max,
        y_min,
        y_max,
    )
    draw_legend(
        draw,
        [label for label, _ in series],
        SERIES_COLORS[: len(series)],
    )

    for series_index, (_, values) in enumerate(series):
        color = SERIES_COLORS[series_index]
        mapped = [
            map_point(x, y, x_min, x_max, y_min, y_max)
            for x, y in values
        ]
        if not scatter and len(mapped) > 1:
            draw.line(mapped, fill=color, width=3)
        for x, y in mapped:
            radius = 4 if scatter else 3
            draw.ellipse(
                (x - radius, y - radius, x + radius, y + radius),
                fill=color,
            )

    image.save(output_path)


def create_plots(
    output_dir: Path,
    trajectory: Sequence[dict[str, Any]],
) -> None:
    stroke_entries = [
        entry for entry in trajectory if entry["decision"] == "stroke"
    ]
    all_entries = list(trajectory)

    error_points = [
        (float(entry["step"]), float(entry["error_after"]))
        for entry in all_entries
    ]
    save_line_plot(
        output_dir / "error-trajectory.png",
        "Student Error Trajectory",
        "error",
        [("Student error", error_points)],
    )

    predicted_points = [
        (float(entry["step"]), float(entry["predicted_improvement"]))
        for entry in all_entries
    ]
    actual_points = [
        (float(entry["step"]), float(entry["actual_improvement"]))
        for entry in stroke_entries
    ]
    teacher_points = [
        (
            float(entry["step"]),
            float(entry["teacher_best_improvement"]),
        )
        for entry in all_entries
    ]
    save_line_plot(
        output_dir / "improvement-trajectory.png",
        "Improvement at Each Student-Visited State",
        "improvement",
        [
            ("Student predicted", predicted_points),
            ("Student actual", actual_points),
            ("Teacher best", teacher_points),
        ],
        include_zero=True,
    )

    regret_points = [
        (float(entry["step"]), float(entry["action_regret"]))
        for entry in stroke_entries
    ]
    save_line_plot(
        output_dir / "action-regret.png",
        "Action Regret",
        "teacher best - student actual",
        [("Action regret", regret_points)],
        include_zero=True,
    )

    student_action_points = [
        (float(entry["step"]), float(entry["stroke_index"]))
        for entry in stroke_entries
    ]
    teacher_action_points = [
        (float(entry["step"]), float(entry["teacher_stroke_index"]))
        for entry in all_entries
    ]
    save_line_plot(
        output_dir / "action-sequence.png",
        "Student and Teacher Action Sequence",
        "action ID",
        [
            ("Student action", student_action_points),
            ("Teacher action", teacher_action_points),
        ],
        scatter=True,
    )


def main() -> None:
    args = parse_args()
    validate_args(args)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    if not args.skip_rollout:
        run_oracle(args)

    result = load_result(args.output_dir)
    trajectory = enrich_trajectory(result["trajectory"])
    summary = build_summary(
        result,
        trajectory,
        args.large_regret_threshold,
    )

    write_trajectory_csv(
        args.output_dir / "trajectory.csv",
        trajectory,
    )
    analysis = {
        "summary": summary,
        "trajectory": trajectory,
    }
    (args.output_dir / "trajectory-analysis.json").write_text(
        json.dumps(analysis, indent=2),
        encoding="utf-8",
    )
    create_plots(args.output_dir, trajectory)

    print(json.dumps(summary, indent=2))
    print(f"Artifacts written to: {args.output_dir}")


if __name__ == "__main__":
    main()

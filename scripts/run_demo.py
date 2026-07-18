import argparse, json
from pathlib import Path
import numpy as np
import torch
from PIL import Image

from painting_multi_head.action_space import DiscreteStrokeActionSpace
from painting_multi_head.environment import PaintingEnvironment
from painting_multi_head.model import MultiHeadPaintingPolicy
from painting_multi_head.targets import random_target
from painting_multi_head.transforms import ImprovementTransform

def as_image(a, scale=16):
    image = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))
    return image.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--stop-threshold", type=float, default=1e-4)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--max-steps", type=int, default=32)
    args = p.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ckpt = torch.load(args.model, map_location=device)
    model = MultiHeadPaintingPolicy(ckpt["stroke_count"], ckpt["image_size"]).to(device)
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    transform = ImprovementTransform.from_dict(ckpt["transform"])

    rng = np.random.default_rng(args.seed)
    target = random_target(rng, ckpt["image_size"], kind="gradient")
    env = PaintingEnvironment(target, DiscreteStrokeActionSpace(), max_steps=args.max_steps)
    frames = [as_image(env.canvas)]
    trajectory = []

    while not env.done:
        tensor = torch.from_numpy(env.observation()).unsqueeze(0).to(device)
        with torch.no_grad():
            logits, encoded = model(tensor)
        predicted = float(transform.decode(encoded.cpu().numpy())[0])

        if predicted <= args.stop_threshold:
            env.stop()
            trajectory.append({"decision": "stop", "predicted_improvement": predicted})
        else:
            action = int(logits.argmax(1).item())
            actual = env.apply_stroke(action)
            trajectory.append({
                "decision": "stroke",
                "stroke_index": action,
                "predicted_improvement": predicted,
                "actual_improvement": actual,
            })
            frames.append(as_image(env.canvas))

    as_image(target).save(args.output_dir / "target.png")
    as_image(env.canvas).save(args.output_dir / "final_canvas.png")
    frames[0].save(args.output_dir / "trajectory.gif", save_all=True, append_images=frames[1:], duration=180, loop=0)
    result = {
        "final_error": env.error(),
        "steps": env.step_count,
        "stop_reason": env.stop_reason,
        "trajectory": trajectory,
    }
    (args.output_dir / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()

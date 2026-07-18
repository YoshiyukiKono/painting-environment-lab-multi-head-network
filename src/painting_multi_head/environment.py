import numpy as np
from .action_space import DiscreteStrokeActionSpace
from .palette import get_default_palette
from .renderer import render_stroke
from .metrics import mse

class PaintingEnvironment:
    def __init__(self, target, action_space=None, palette=None, max_steps=32):
        self.target = np.asarray(target, dtype=np.float32)
        self.action_space = action_space or DiscreteStrokeActionSpace()
        self.palette = np.asarray(palette if palette is not None else get_default_palette(), dtype=np.float32)
        self.max_steps = int(max_steps)
        self.canvas = np.ones_like(self.target)
        self.step_count = 0
        self.done = False
        self.stop_reason = None

    def observation(self):
        return np.concatenate([
            self.target.transpose(2, 0, 1),
            self.canvas.transpose(2, 0, 1),
        ]).astype(np.float32)

    def error(self):
        return mse(self.canvas, self.target)

    def simulate(self, stroke_index):
        action = self.action_space.decode(stroke_index)
        next_canvas = render_stroke(self.canvas, action, self.palette[action.color_index])
        improvement = self.error() - mse(next_canvas, self.target)
        return next_canvas, float(improvement)

    def apply_stroke(self, stroke_index):
        self.canvas, improvement = self.simulate(stroke_index)
        self.step_count += 1
        if self.step_count >= self.max_steps:
            self.done = True
            self.stop_reason = "max_steps"
        return improvement

    def stop(self):
        self.done = True
        self.stop_reason = "policy_stop"

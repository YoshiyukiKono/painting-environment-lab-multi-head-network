from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class StrokeAction:
    x: float
    y: float
    radius: float
    color_index: int

class DiscreteStrokeActionSpace:
    def __init__(self, grid_size=8, radii=(0.08, 0.16), palette_size=8):
        self.grid_size = int(grid_size)
        self.radii = tuple(float(v) for v in radii)
        self.palette_size = int(palette_size)
        self.n = self.grid_size * self.grid_size * len(self.radii) * self.palette_size

    def decode(self, index):
        index = int(index)
        if not 0 <= index < self.n:
            raise ValueError("stroke index out of range")
        color_index = index % self.palette_size
        q = index // self.palette_size
        radius_index = q % len(self.radii)
        q //= len(self.radii)
        x_index = q % self.grid_size
        y_index = q // self.grid_size
        return StrokeAction(
            (x_index + 0.5) / self.grid_size,
            (y_index + 0.5) / self.grid_size,
            self.radii[radius_index],
            color_index,
        )

    def indices(self):
        return np.arange(self.n, dtype=np.int64)

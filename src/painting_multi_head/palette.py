import numpy as np

DEFAULT_PALETTE = np.asarray([
    [0.00, 0.00, 0.00],
    [1.00, 1.00, 1.00],
    [0.90, 0.15, 0.15],
    [0.15, 0.65, 0.25],
    [0.15, 0.30, 0.90],
    [0.95, 0.80, 0.15],
    [0.85, 0.20, 0.75],
    [0.15, 0.80, 0.85],
], dtype=np.float32)

def get_default_palette():
    return DEFAULT_PALETTE.copy()

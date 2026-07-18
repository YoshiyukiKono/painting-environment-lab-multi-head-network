import numpy as np

def random_target(rng, size=16, kind=None):
    kind = kind or str(rng.choice(["flat", "rectangle", "circle", "gradient"]))
    if kind == "flat":
        c = rng.uniform(0, 1, size=3)
        return np.broadcast_to(c, (size, size, 3)).copy().astype(np.float32)
    if kind == "rectangle":
        bg, fg = rng.uniform(0, 1, size=(2, 3))
        image = np.broadcast_to(bg, (size, size, 3)).copy()
        x0, x1 = sorted(rng.integers(0, size, size=2))
        y0, y1 = sorted(rng.integers(0, size, size=2))
        image[y0:max(y0+1, y1), x0:max(x0+1, x1)] = fg
        return image.astype(np.float32)
    if kind == "circle":
        bg, fg = rng.uniform(0, 1, size=(2, 3))
        image = np.broadcast_to(bg, (size, size, 3)).copy()
        yy, xx = np.mgrid[0:size, 0:size]
        cx, cy = rng.uniform(.25, .75, size=2) * (size - 1)
        r = rng.uniform(.15, .4) * size
        image[(xx-cx)**2 + (yy-cy)**2 <= r**2] = fg
        return image.astype(np.float32)
    if kind == "gradient":
        left, right = rng.uniform(0, 1, size=(2, 3))
        t = np.linspace(0, 1, size, dtype=np.float32)[None, :, None]
        row = left[None, None, :] * (1-t) + right[None, None, :] * t
        return np.broadcast_to(row, (size, size, 3)).copy().astype(np.float32)
    raise ValueError(kind)

import numpy as np

def render_stroke(canvas, action, color):
    h, w, _ = canvas.shape
    yy, xx = np.mgrid[0:h, 0:w]
    cx = action.x * (w - 1)
    cy = action.y * (h - 1)
    radius_px = max(1.0, action.radius * min(h, w))
    mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= radius_px ** 2
    result = canvas.copy()
    result[mask] = color
    return result

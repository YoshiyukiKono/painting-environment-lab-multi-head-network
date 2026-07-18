import numpy as np
from painting_multi_head.transforms import ImprovementTransform

def test_standardized_round_trip():
    x = np.asarray([0.0, 0.001, 0.01, 0.1], dtype=np.float32)
    transform = ImprovementTransform.fit(x, "standardized")
    restored = transform.decode(transform.encode(x))
    assert np.allclose(restored, x, atol=1e-6)

def test_log_round_trip():
    x = np.asarray([0.0, 0.001, 0.01, 0.1], dtype=np.float32)
    transform = ImprovementTransform.fit(x, "log")
    restored = transform.decode(transform.encode(x))
    assert np.allclose(restored, x, atol=1e-6)

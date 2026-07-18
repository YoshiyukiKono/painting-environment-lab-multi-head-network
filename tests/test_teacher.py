import numpy as np
from painting_multi_head.action_space import DiscreteStrokeActionSpace
from painting_multi_head.environment import PaintingEnvironment
from painting_multi_head.teacher import GreedyTeacher

def test_teacher_label():
    env = PaintingEnvironment(
        np.zeros((8, 8, 3), dtype=np.float32),
        DiscreteStrokeActionSpace(grid_size=2, radii=(0.3,), palette_size=8),
    )
    label = GreedyTeacher().label(env)
    assert label.best_improvement > 0

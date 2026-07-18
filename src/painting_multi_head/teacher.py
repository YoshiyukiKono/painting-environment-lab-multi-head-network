from dataclasses import dataclass

@dataclass(frozen=True)
class TeacherLabel:
    stroke_index: int
    best_improvement: float

class GreedyTeacher:
    def label(self, env):
        best_index = 0
        best_improvement = float("-inf")
        for index in env.action_space.indices():
            _, improvement = env.simulate(int(index))
            if improvement > best_improvement:
                best_index = int(index)
                best_improvement = float(improvement)
        return TeacherLabel(best_index, max(0.0, best_improvement))

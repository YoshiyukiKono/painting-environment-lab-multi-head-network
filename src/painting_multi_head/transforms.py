from dataclasses import dataclass
import numpy as np

@dataclass
class ImprovementTransform:
    kind: str = "standardized"
    mean: float = 0.0
    std: float = 1.0
    scale: float = 1e-3

    @classmethod
    def fit(cls, values, kind="standardized"):
        values = np.asarray(values, dtype=np.float32)
        if kind == "raw":
            return cls(kind="raw")
        if kind == "standardized":
            return cls(
                kind=kind,
                mean=float(values.mean()),
                std=max(float(values.std()), 1e-8),
            )
        if kind == "log":
            positive = values[values > 0]
            scale = float(np.median(positive)) if positive.size else 1e-3
            return cls(kind=kind, scale=max(scale, 1e-8))
        raise ValueError(kind)

    def encode(self, values):
        values = np.asarray(values, dtype=np.float32)
        if self.kind == "raw":
            return values
        if self.kind == "standardized":
            return (values - self.mean) / self.std
        if self.kind == "log":
            return np.log1p(values / self.scale)
        raise ValueError(self.kind)

    def decode(self, values):
        values = np.asarray(values, dtype=np.float32)
        if self.kind == "raw":
            return values
        if self.kind == "standardized":
            return values * self.std + self.mean
        if self.kind == "log":
            return np.expm1(values) * self.scale
        raise ValueError(self.kind)

    def to_dict(self):
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

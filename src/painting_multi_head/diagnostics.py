import numpy as np
import torch
from torch.utils.data import DataLoader
from .metrics import pearson_correlation

def diagnose(model, dataset, transform, batch_size=128):
    device = next(model.parameters()).device
    model.eval()
    true_strokes, predicted_strokes = [], []
    true_improvements, predicted_improvements = [], []

    with torch.no_grad():
        for obs, stroke, improvement in DataLoader(dataset, batch_size=batch_size):
            logits, predicted_encoded = model(obs.to(device))
            predicted = transform.decode(predicted_encoded.cpu().numpy())
            true_strokes.extend(stroke.numpy())
            predicted_strokes.extend(logits.argmax(1).cpu().numpy())
            true_improvements.extend(improvement.numpy())
            predicted_improvements.extend(predicted)

    true_strokes = np.asarray(true_strokes)
    predicted_strokes = np.asarray(predicted_strokes)
    true_improvements = np.asarray(true_improvements)
    predicted_improvements = np.asarray(predicted_improvements)

    return {
        "stroke_accuracy": float(np.mean(true_strokes == predicted_strokes)),
        "improvement_mae": float(np.mean(np.abs(true_improvements - predicted_improvements))),
        "improvement_correlation": pearson_correlation(true_improvements, predicted_improvements),
        "teacher_improvement_mean": float(true_improvements.mean()),
        "predicted_improvement_mean": float(predicted_improvements.mean()),
        "predicted_improvement_min": float(predicted_improvements.min()),
        "predicted_improvement_max": float(predicted_improvements.max()),
    }

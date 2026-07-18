import torch
from torch import nn
from torch.utils.data import DataLoader
from .model import MultiHeadPaintingPolicy

def train_joint(dataset, transform, stroke_count, image_size, epochs=20, batch_size=64, lr=1e-3, improvement_weight=1.0):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = MultiHeadPaintingPolicy(stroke_count, image_size).to(device)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    ce = nn.CrossEntropyLoss()
    huber = nn.SmoothL1Loss()

    for epoch in range(1, epochs + 1):
        model.train()
        stroke_total = improvement_total = correct = count = 0
        for obs, stroke, improvement in loader:
            obs, stroke = obs.to(device), stroke.to(device)
            encoded = torch.as_tensor(transform.encode(improvement.numpy()), dtype=torch.float32, device=device)

            optimizer.zero_grad()
            logits, predicted = model(obs)
            stroke_loss = ce(logits, stroke)
            improvement_loss = huber(predicted, encoded)
            loss = stroke_loss + improvement_weight * improvement_loss
            loss.backward()
            optimizer.step()

            n = len(stroke)
            stroke_total += float(stroke_loss) * n
            improvement_total += float(improvement_loss) * n
            correct += int((logits.argmax(1) == stroke).sum())
            count += n

        print(
            f"epoch={epoch:03d} "
            f"stroke_loss={stroke_total/count:.6f} "
            f"stroke_accuracy={correct/count:.4f} "
            f"improvement_loss={improvement_total/count:.6f}"
        )
    return model

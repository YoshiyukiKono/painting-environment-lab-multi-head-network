import torch
from painting_multi_head.model import MultiHeadPaintingPolicy

def test_two_heads():
    model = MultiHeadPaintingPolicy(1024, 16)
    logits, improvement = model(torch.zeros(2, 6, 16, 16))
    assert logits.shape == (2, 1024)
    assert improvement.shape == (2,)

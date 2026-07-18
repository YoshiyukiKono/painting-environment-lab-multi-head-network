# One Network, Two Heads

The network is one trainable computation graph.

```text
input
  ↓
shared parameters
  ↓
feature
  ├─ stroke-specific parameters
  └─ improvement-specific parameters
```

The two losses are added, and backpropagation updates both the shared parameters and the task-specific parameters.

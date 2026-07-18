# Loss Balancing

The total objective is:

```text
stroke cross entropy
+
weight × improvement regression loss
```

A large weight can damage Stroke learning. A small weight can make the Improvement Head irrelevant.

Always inspect the two losses and task-specific metrics separately.

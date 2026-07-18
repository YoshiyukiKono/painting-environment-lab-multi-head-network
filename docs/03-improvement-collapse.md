# Improvement Collapse

When most regression targets are small, predicting a nearly constant value can produce a deceptively small MSE.

Symptoms:

- predicted values cluster near zero
- low regression loss
- low correlation with Teacher values
- immediate Stop in closed-loop rollout

The solution is not merely increasing the Dataset. Target scaling and diagnostics are required.

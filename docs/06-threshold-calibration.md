# Threshold Calibration

The Teacher threshold and the learned prediction threshold need not be numerically identical.

Prediction bias can shift the useful decision boundary.

Calibrate the threshold on held-out data, then validate it in closed-loop rollout.

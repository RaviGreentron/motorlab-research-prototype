# Model C — compact autoencoder

The implemented track is a CPU NumPy neural autoencoder. PyTorch was the preferred framework in the request; it was not installed for this bounded prototype. This explicit deviation avoids a large framework dependency while preserving a genuine learned nonlinear reconstruction experiment. GPU compatibility is **not implemented or tested**.

Architecture is input → configurable tanh bottleneck → linear reconstruction. The default latent dimension is 4; input dimension is inferred from the eleven-feature matrix. Weights use a seeded generator. Full-batch Adam uses learning rate 0.01, up to 350 epochs, and validation early stopping with patience 30. The best validation checkpoint is restored, then the independent calibration partition sets the reconstruction-error threshold. Training and validation loss histories and local model artifacts are saved.

Score is mean squared reconstruction error in training-standardized feature space, not physical damage. The healthy validation partition informs early stopping; it does not fit the scaler. Calibration does not update weights. Trusted local pickle serialization preserves the suite, scaler and weights; do not deserialize untrusted model files.

Tests establish deterministic repeated training, substantial reconstruction improvement on a low-dimensional fixture, best-checkpoint restoration, anomaly sensitivity and calibration independence. These tests do not prove the model beats statistics or Isolation Forest on measured motors. Cross-motor and load-change evidence is limited to synthetic study metrics.

No sequence autoencoder, GPU timing, checkpoint-resume trainer, measured-data tuning or uncertainty calibration is claimed. See the evaluation report for whether the added training cost yields useful behavior in this experiment.

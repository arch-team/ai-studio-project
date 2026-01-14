"""Domain Value Objects - Immutable objects defined by their attributes.

Value objects encapsulate domain concepts without identity:
- ResourceConfig: CPU, memory, GPU configuration
- JobStatus: Training job state enumeration
- StoragePath: S3/FSx path with validation
- TrainingConfig: Hyperparameters and training settings
"""

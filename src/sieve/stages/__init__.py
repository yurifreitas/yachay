"""The stages. Each is an independent function over a contract-checked frame."""
from .null import NullModel, calibrate, fit_null, top_k_mean

__all__ = ["NullModel", "calibrate", "fit_null", "top_k_mean"]

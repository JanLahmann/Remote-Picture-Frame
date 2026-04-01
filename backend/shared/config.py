"""Configuration loader for IBM Cloud Functions.

In IBM Cloud Functions, parameters are passed as a dict to the main function.
For local development, we fall back to environment variables.
"""

import os

_params = {}


def init(params: dict):
    """Initialize config from Cloud Function parameters."""
    global _params
    _params = params


def get(key: str, default: str = "") -> str:
    """Get a config value from function params or environment."""
    return _params.get(key, os.environ.get(key, default))

"""MongoDB service package for lvrgd-common.

This package provides a MongoDB service with Pydantic configuration models
for easy database operations.
"""

from .mongodb_models import MongoConfig
from .mongodb_service import MongoService

__all__ = [
    "MongoConfig",
    "MongoService",
]

__version__ = "0.1.0"

"""MongoDB service package for lvrgd-common.

This package provides a MongoDB service with Pydantic configuration models
for easy database operations.
"""

from .async_mongodb_service import AsyncMongoService
from .mongodb_models import MongoConfig
from .mongodb_service import MongoService

__all__ = [
    "AsyncMongoService",
    "MongoConfig",
    "MongoService",
]

__version__ = "0.1.0"

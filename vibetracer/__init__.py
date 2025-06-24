# vibetracer/__init__.py

"""
VibeTracer public API—everything else is under the hood.
"""

from .database.sqlite_db import get_engine
from .trace.tracer import info_decorator

__all__ = ["get_engine", "info_decorator"]

# vibetracer/__init__.py

"""
VibeTracer public API—everything else is under the hood.
"""

from .trace.tracer import info_decorator

__all__ = ["info_decorator"]

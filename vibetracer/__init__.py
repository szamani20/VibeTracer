# vibetracer/__init__.py

"""
VibeTracer public API—everything else is under the hood.
"""

from vibetracer.trace.tracer import info_decorator
from vibetracer.llm.lib import dump_llm_report, dump_latest_run_llm_report, analyze_my_code

__all__ = ["info_decorator", "dump_llm_report", "dump_latest_run_llm_report", "analyze_my_code"]

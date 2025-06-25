import os
from typing import Tuple, Dict, Any
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from vibetracer.database.config import DUMP_DIRECTORY


class Dumper:
    def __init__(self, db_path: str):
        """
        Initialize the Dumper with a path to the SQLite database.
        Creates an SQLAlchemy engine and determines the output subfolder.
        """
        self.db_path = db_path
        self.db_name = os.path.splitext(os.path.basename(db_path))[0]
        self.engine: Engine = create_engine(f"sqlite:///{db_path}")
        self.subfolder = os.path.join(DUMP_DIRECTORY, self.db_name)

    def _ensure_folder(self) -> None:
        """Ensure that the dump subfolder exists."""
        os.makedirs(self.subfolder, exist_ok=True)

    def _load_dataframes(self) -> Dict[str, pd.DataFrame]:
        """
        Load the three tables from SQLite into pandas DataFrames.
        Returns a dict with keys 'functions', 'calls', 'arguments'.
        """
        # Unlike what we did in analyzer.py by loading data using select from sqlmodel class, here we utilize
        # `read_sql` function from pandas. Just for the culture.
        df_functions = pd.read_sql("SELECT * FROM function", self.engine)
        df_calls = pd.read_sql("SELECT * FROM call", self.engine)
        df_arguments = pd.read_sql("SELECT * FROM argument", self.engine)
        return {
            "functions": df_functions,
            "calls": df_calls,
            "arguments": df_arguments,
        }

    def _aggregate_arguments(self, df_args: pd.DataFrame) -> pd.DataFrame:
        """
        Turn Argument rows into one column per call containing a dict of {name: value}.
        """
        agg = (
            df_args.groupby("call_id")[["name", "value"]]
            .apply(lambda df: {row["name"]: row["value"] for _, row in df.iterrows()})
            .rename("arguments")
            .reset_index()
        )
        return agg

    def dump_csvs(self, save: bool = False) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Dump the raw tables into three separate CSVs and also produce a
        unified CSV that merges function metadata, call metadata, and aggregated arguments.

        Returns:
            df_functions, df_calls, df_arguments, df_unified
        """
        # Load raw data
        dfs = self._load_dataframes()
        df_functions = dfs["functions"]
        df_calls = dfs["calls"]
        df_arguments = dfs["arguments"]

        # Aggregate arguments per call
        df_arg_agg = self._aggregate_arguments(df_arguments)

        # Merge calls with functions and aggregated arguments
        df_unified = (
            df_calls
            .merge(df_functions, left_on="function_id", right_on="id", suffixes=("_call", "_func"))
            .merge(df_arg_agg, left_on="id_call", right_on="call_id", how="left")
        )

        # Reorder and select most informative columns for human readability
        cols = [
            "id_call",
            "module", "qualname", "filename", "lineno", "signature",
            "timestamp", "duration_ms", "thread_id", "is_coroutine", "method_type", "class_name",
            "arguments",
            "return_value", "exception_type", "exception_message"
        ]
        # Only keep columns that exist after the merges
        cols = [c for c in cols if c in df_unified.columns]
        df_unified = df_unified[cols]

        # Optionally save CSVs
        if save:
            self._ensure_folder()
            df_functions.to_csv(os.path.join(self.subfolder, "functions.csv"), index=False)
            df_calls.to_csv(os.path.join(self.subfolder, "calls.csv"), index=False)
            df_arguments.to_csv(os.path.join(self.subfolder, "arguments.csv"), index=False)
            df_unified.to_csv(os.path.join(self.subfolder, "unified.csv"), index=False)

        return df_functions, df_calls, df_arguments, df_unified

    def dump_llm_text(self, save: bool = False) -> str:
        """
        Produce a single text blob meant for feeding into an LLM. It includes:
        - A Functions Metadata section with full source code.
        - A Call Execution Flow section with nested, timestamp-ordered calls.
        - Arguments and traceback details inline with each call.

        Returns:
            A multi-line string with all information.
        """
        dfs = self._load_dataframes()
        df_functions = dfs["functions"]
        df_calls = dfs["calls"]
        df_arguments = dfs["arguments"]

        # Build a dict of arguments per call_id
        arg_map = df_arguments.groupby("call_id")[["name", "value"]].apply(
            lambda df: {row["name"]: row["value"] for _, row in df.iterrows()}).to_dict()

        # Convert calls to a dict by id and prepare children lists
        calls = df_calls.to_dict(orient="records")
        calls_by_id: Dict[int, Dict[str, Any]] = {c["id"]: dict(c, children=[]) for c in calls}
        for c in calls:
            pid = c.get("parent_call_id")
            if pid is not None and pid in calls_by_id:
                calls_by_id[pid]["children"].append(c["id"])
        root_calls = [c for c in calls if pd.isna(c.get("parent_call_id"))]

        # Helper to render each call recursively
        def render_call(call_id: int, depth: int = 0, lines: list = None) -> None:
            prefix = f"[DEPTH={depth}] "
            c = calls_by_id[call_id]
            lines.append(f"{prefix}CALL {call_id}:")
            lines.append(f"{prefix}  Function ID: {c['function_id']}")
            lines.append(f"{prefix}  Timestamp: {c['timestamp']}")
            lines.append(f"{prefix}  Duration (ms): {c.get('duration_ms')}")
            lines.append(f"{prefix}  Thread ID: {c['thread_id']}  Coroutine: {c['is_coroutine']}")
            lines.append(f"{prefix}  Method Type: {c['method_type']}  Class: {c.get('class_name')}")
            if args := arg_map.get(call_id):
                lines.append(f"{prefix}  Arguments:")
                for name, val in args.items():
                    lines.append(f"{prefix}    - {name}: {val}")
            if c.get("return_value") is not None:
                lines.append(f"{prefix}  Return Value: {c['return_value']}")
            if c.get("exception_type"):
                lines.append(f"{prefix}  Exception: {c['exception_type']} - {c.get('exception_message')}")
            if tb := c.get("tb"):
                lines.append(f"{prefix}  Traceback:")
                for tb_line in tb.splitlines():
                    lines.append(f"{prefix}    {tb_line}")
            # Recurse into children
            for child_id in sorted(c["children"], key=lambda cid: calls_by_id[cid]["timestamp"]):
                render_call(child_id, depth + 1, lines)

        # Build the text sections
        lines = []

        # Section: Functions Metadata
        lines.append("=== Functions Metadata ===")
        for _, f in df_functions.iterrows():
            lines.append(f"Function ID: {f['id']}")
            lines.append(f"Module: {f['module']}")
            lines.append(f"Qualified Name: {f['qualname']}")
            lines.append(f"Defined at: {f['filename']}:{f['lineno']}")
            lines.append(f"Signature: {f['signature']}")
            if f.get("annotations"):
                lines.append(f"Annotations: {f['annotations']}")
            if f.get("defaults"):
                lines.append(f"Defaults: {f['defaults']}")
            if f.get("kwdefaults"):
                lines.append(f"Kwdefaults: {f['kwdefaults']}")
            if f.get("closure_vars"):
                lines.append(f"Closure Vars: {f['closure_vars']}")
            lines.append("Source Code:")
            for src_line in (f.get("source_code") or "").splitlines():
                lines.append(f"    {src_line}")
            lines.append("")  # blank line between functions

        # Section: Call Execution Flow
        lines.append("=== Call Execution Flow ===")
        for root in sorted(root_calls, key=lambda c: c["timestamp"]):
            render_call(root["id"], depth=0, lines=lines)
            lines.append("")

        text = "\n".join(lines)

        # Optionally save to disk
        if save:
            self._ensure_folder()
            path = os.path.join(self.subfolder, "dump_llm.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)

        return text

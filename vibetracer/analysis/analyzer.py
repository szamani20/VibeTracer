import os
from pathlib import Path
from typing import Optional

import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from sqlmodel import create_engine, Session, select

from vibetracer.analysis.config import ANALYSIS_DIRECTORY
from vibetracer.database.models import Function, Call, Argument


class RunAnalysis:
    def __init__(self, db_path: str):
        """
        Initialize with the path to a single run’s SQLite DB.
        """
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        self.session = Session(self.engine)

        os.makedirs(ANALYSIS_DIRECTORY, exist_ok=True)

    # ----------------------
    # Data‐extraction methods
    # ----------------------

    def get_runtime_summary(self, save: bool = False, filepath: Optional[str] = None) -> pd.DataFrame:
        """
        Returns a DataFrame of all calls and their durations.
        """
        stmt = select(Call.id, Function.qualname, Call.duration_ms).join(Function)
        rows = self.session.exec(stmt).all()
        df = pd.DataFrame(rows, columns=["call_id", "qualname", "duration_ms"])
        if save:
            fp = filepath or f"{Path(self.db_path).stem}_runtime.csv"
            fp = os.path.join(ANALYSIS_DIRECTORY, fp)
            df.to_csv(fp, index=False)
        return df

    def get_input_summary(self, save: bool = False, filepath: Optional[str] = None) -> pd.DataFrame:
        """
        Returns a DataFrame of all argument values per call.
        """
        stmt = select(Argument.call_id, Argument.name, Argument.value)
        rows = self.session.exec(stmt).all()
        df = pd.DataFrame(rows, columns=["call_id", "arg_name", "arg_value"])
        if save:
            fp = filepath or f"{Path(self.db_path).stem}_inputs.csv"
            fp = os.path.join(ANALYSIS_DIRECTORY, fp)
            df.to_csv(fp, index=False)
        return df

    def get_output_summary(self, save: bool = False, filepath: Optional[str] = None) -> pd.DataFrame:
        """
        Returns a DataFrame of all return values per call.
        """
        stmt = select(Call.id, Function.qualname, Call.return_value).join(Function)
        rows = self.session.exec(stmt).all()
        df = pd.DataFrame(rows, columns=["call_id", "qualname", "return_value"])
        if save:
            fp = filepath or f"{Path(self.db_path).stem}_outputs.csv"
            fp = os.path.join(ANALYSIS_DIRECTORY, fp)
            df.to_csv(fp, index=False)
        return df

    def get_exception_summary(self, save: bool = False, filepath: Optional[str] = None) -> pd.DataFrame:
        """
        Returns a DataFrame of all calls that raised exceptions.
        """
        stmt = (
            select(Call.id, Function.qualname, Call.exception_type, Call.exception_message)
            .where(Call.exception_type.is_not(None))
            .join(Function)
        )
        rows = self.session.exec(stmt).all()
        df = pd.DataFrame(rows, columns=["call_id", "qualname", "exception_type", "exception_message"])
        if save:
            fp = filepath or f"{Path(self.db_path).stem}_exceptions.csv"
            fp = os.path.join(ANALYSIS_DIRECTORY, fp)
            df.to_csv(fp, index=False)
        return df

    def get_call_hierarchy(self) -> pd.DataFrame:
        """
        Returns a DataFrame representing the parent–child call relationships.
        """
        stmt = select(Call.id, Call.parent_call_id, Function.qualname).join(Function)
        rows = self.session.exec(stmt).all()
        df = pd.DataFrame(rows, columns=["call_id", "parent_call_id", "qualname"])
        return df

    # ----------------------
    # Textual report methods
    # ----------------------

    def report_runtime(self, filepath: Optional[str] = None) -> str:
        df = self.get_runtime_summary()
        report = df.describe().to_string()
        if filepath:
            filepath = os.path.join(ANALYSIS_DIRECTORY, filepath)
            with open(filepath, "w") as f:
                f.write(report)
        return report

    def report_exceptions(self, filepath: Optional[str] = None) -> str:
        df = self.get_exception_summary()
        if df.empty:
            report = "No exceptions recorded in this run."
        else:
            report = df.groupby("exception_type").size().to_string()
        if filepath:
            filepath = os.path.join(ANALYSIS_DIRECTORY, filepath)
            with open(filepath, "w") as f:
                f.write(report)
        return report

    # ----------------------
    # Visualization methods
    # ----------------------

    def viz_runtime_distribution(self, save_fig: bool = False, filepath: Optional[str] = None):
        df = self.get_runtime_summary()
        durations = df['duration_ms'].dropna()
        plt.figure()
        plt.hist(durations, bins=50)
        plt.xlabel('Duration (ms)')
        plt.ylabel('Frequency')
        plt.title('Call Duration Distribution')
        plt.tight_layout()
        if save_fig and filepath:
            filepath = os.path.join(ANALYSIS_DIRECTORY, filepath)
            plt.savefig(filepath)
        else:
            plt.show()
        plt.close()

    def viz_top_slowest(self, top_n: int = 10, save_fig: bool = False, filepath: Optional[str] = None):
        df = self.get_runtime_summary()
        top = df.nlargest(top_n, 'duration_ms')
        plt.figure()
        plt.bar(top['qualname'], top['duration_ms'])
        plt.xticks(rotation=45, ha='right')
        plt.ylabel('Duration (ms)')
        plt.title(f'Top {top_n} Slowest Calls')
        plt.tight_layout()
        if save_fig and filepath:
            filepath = os.path.join(ANALYSIS_DIRECTORY, filepath)
            plt.savefig(filepath)
        else:
            plt.show()
        plt.close()

    def viz_exceptions(self, save_fig: bool = False, filepath: Optional[str] = None):
        df = self.get_exception_summary()
        if df.empty:
            print("No exceptions to plot.")
            return
        counts = df['exception_type'].value_counts()
        plt.figure()
        plt.bar(counts.index, counts.values)
        plt.xlabel('Exception Type')
        plt.ylabel('Count')
        plt.title('Exceptions by Type')
        plt.tight_layout()
        if save_fig and filepath:
            filepath = os.path.join(ANALYSIS_DIRECTORY, filepath)
            plt.savefig(filepath)
        else:
            plt.show()
        plt.close()

    def viz_inputs(self, save_fig: bool = False, filepath: Optional[str] = None):
        df = self.get_input_summary()
        counts = df['arg_name'].value_counts()
        plt.figure()
        plt.bar(counts.index, counts.values)
        plt.xticks(rotation=45, ha='right')
        plt.xlabel('Argument Name')
        plt.ylabel('Frequency')
        plt.title('Argument Usage Frequency')
        plt.tight_layout()
        if save_fig and filepath:
            filepath = os.path.join(ANALYSIS_DIRECTORY, filepath)
            plt.savefig(filepath)
        else:
            plt.show()
        plt.close()

    def viz_outputs(self, save_fig: bool = False, filepath: Optional[str] = None):
        df = self.get_output_summary()
        counts = df['return_value'].value_counts().head(10)
        plt.figure()
        plt.bar(counts.index, counts.values)
        plt.xticks(rotation=45, ha='right')
        plt.xlabel('Return Value')
        plt.ylabel('Count')
        plt.title('Top Return Values')
        plt.tight_layout()
        if save_fig and filepath:
            filepath = os.path.join(ANALYSIS_DIRECTORY, filepath)
            plt.savefig(filepath)
        else:
            plt.show()
        plt.close()

    def viz_call_graph(self, save_fig: bool = False, filepath: Optional[str] = None, minimal_labels: bool = False):
        """
        Static call graph visualization using networkx and matplotlib.
        """
        hierarchy = self.get_call_hierarchy()
        G = nx.DiGraph()

        # Add nodes
        for _, row in hierarchy.iterrows():
            cid = row['call_id']
            call = self.session.get(Call, cid)
            label = row['qualname'] if minimal_labels else f"{row['qualname']}\n{call.duration_ms:.1f}ms"
            G.add_node(cid, label=label, color=self._node_color(call))

        # Add edges
        for _, row in hierarchy.iterrows():
            pid = row['parent_call_id']
            cid = row['call_id']
            if pid:
                G.add_edge(pid, cid)

        # Layout and draw
        pos = nx.spring_layout(G)
        node_colors = [data.get('color', '#AAAAAA') for _, data in G.nodes(data=True)]
        labels = {n: data.get('label', str(n)) for n, data in G.nodes(data=True)}

        plt.figure(figsize=(10, 10))
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=500)
        nx.draw_networkx_edges(G, pos, arrows=True)
        nx.draw_networkx_labels(G, pos, labels, font_size=8)
        plt.title('Call Graph')
        plt.axis('off')
        plt.tight_layout()

        if save_fig and filepath:
            filepath = os.path.join(ANALYSIS_DIRECTORY, filepath)
            plt.savefig(filepath)
        else:
            plt.show()
        plt.close()

    # ----------------------
    # Helper methods
    # ----------------------

    def _format_args(self, call_id: int) -> str:
        stmt = select(Argument.name, Argument.value).where(Argument.call_id == call_id)
        rows = self.session.exec(stmt).all()
        return "<br>".join(f"{n} = {v}" for n, v in rows)

    def _node_color(self, call: Call) -> str:
        if call.exception_type:
            return "#FF4136"  # red for exceptions
        palette = {
            "function": "#0074D9",
            "instancemethod": "#2ECC40",
            "classmethod": "#FFDC00",
            "staticmethod": "#B10DC9",
        }
        return palette.get(call.method_type, "#AAAAAA")

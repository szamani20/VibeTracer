from pathlib import Path
import pandas as pd

from analysis.analyzer import RunAnalysis

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


def main():
    # Point to your latest run DB inside run_dbs/
    db_dir = Path("run_dbs")
    # pick the most recent file
    db_path = str(sorted(db_dir.glob("run_*.db"))[-1])
    print('DB Path: ', db_path)

    analyzer = RunAnalysis(db_path)

    # === Data summaries (and save to CSV) ===
    runtime_df = analyzer.get_runtime_summary(save=True)
    inputs_df = analyzer.get_input_summary(save=True)
    outputs_df = analyzer.get_output_summary(save=True)
    exceptions_df = analyzer.get_exception_summary(save=True)

    # === Data reports (print to console) ===
    print("=== Runtime Report ===")
    print(runtime_df)
    print("\n=== Exception Report ===")
    print(exceptions_df)
    print("\n=== Input Report ===")
    print(inputs_df)
    print("\n=== Output Report ===")
    print(outputs_df)

    # === Text reports (print to console & save to text) ===
    print("\n=== Runtime Report ===")
    print(analyzer.report_runtime(filepath="runtime_report.txt"))
    print("\n=== Exception Report ===")
    print(analyzer.report_exceptions(filepath="exception_report.txt"))

    # === Visualizations (show and save) ===
    analyzer.viz_runtime_distribution(save_fig=True, filepath="runtime_dist.png")
    analyzer.viz_top_slowest(top_n=5, save_fig=True, filepath="top_slowest.png")
    analyzer.viz_exceptions(save_fig=True, filepath="exceptions.png")
    analyzer.viz_inputs(save_fig=True, filepath="input_freq.png")
    analyzer.viz_outputs(save_fig=True, filepath="output_freq.png")

    # === Interactive Call Graph ===
    analyzer.viz_call_graph(
        save_fig=True,
        filepath="call_graph.png",
        minimal_labels=False
    )


if __name__ == "__main__":
    main()

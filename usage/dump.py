from pathlib import Path
import pandas as pd

from vibetracer import dump_latest_run_llm_report, dump_llm_report
from vibetracer.database.dumper import Dumper

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


def easy_dump_custom_run():
    llm_report = dump_llm_report(path='run_dbs/run_20250624_175123.db')
    print("\n=== Custom Run LLM-Tailored Report ===")
    print(llm_report)


def easy_dump():
    llm_report = dump_latest_run_llm_report()
    print("\n=== Latest Run LLM-Tailored Report ===")
    print(llm_report)


def custom_dump():
    # Point to your latest run DB inside run_dbs/
    db_dir = Path("run_dbs")
    # pick the most recent file
    db_path = str(sorted(db_dir.glob("run_*.db"))[-1])
    print('DB Path: ', db_path)

    analyzer = Dumper(db_path)

    df_functions, df_calls, df_arguments, df_unified = analyzer.dump_csvs(save=True)

    print("=== Functions Report ===")
    print(df_functions)
    print("\n=== Calls Report ===")
    print(df_calls)
    print("\n=== Arguments Report ===")
    print(df_arguments)
    print("\n=== Overall Report ===")
    print(df_unified)

    llm_dump = analyzer.dump_llm_text(save=True)

    print("\n=== LLM-Tailored Report ===")
    print(llm_dump)


if __name__ == "__main__":
    custom_dump()
    easy_dump()
    easy_dump_custom_run()

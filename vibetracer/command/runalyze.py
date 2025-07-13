import os
import argparse
from pathlib import Path
from vibetracer.command.run import run_script
from vibetracer.database.config import DB_DIRECTORY


def save_markdown(md_content: str, file_path: str) -> None:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(md_content, encoding='utf-8')


def runalyze_command(argv=None):
    parser = argparse.ArgumentParser(
        prog="vibetracer runalyze",
        description="First trace your code, then run LLM analysis on the resulting DB"
    )
    parser.add_argument(
        "--provider",
        choices=["openai", "anthropic", "google"],
        default="openai",
        help="LLM provider (default: openai)"
    )
    parser.add_argument(
        "--api_key",
        help="API key (or set {provider}_api_key env var)"
    )
    parser.add_argument(
        "script",
        help="Path to the Python entry-point script to trace"
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Only generate the LLM report; skip any further analysis steps"
    )

    args = parser.parse_args(argv)
    provider = args.provider
    api_key = args.api_key or os.getenv(f"{provider}_api_key")
    if not api_key:
        parser.error(f"must provide --api_key or set {provider}_api_key in environment")

    # 1) Run the tracer (this writes into run_dbs/)
    run_script(args.script)

    # 2) Find the latest DB in run_dbs/
    # script_path = Path(args.script).resolve()
    # project_root = script_path.parent

    run_dbs = Path(f'./{DB_DIRECTORY}')
    if not run_dbs.is_dir():
        parser.error(f"{DB_DIRECTORY}/ directory not found at {run_dbs}")
    db_files = sorted(run_dbs.glob("run_*.db"))
    if not db_files:
        parser.error(f"No run_*.db files found in {run_dbs}/")
    db_path = db_files[-1]

    # 3) Perform LLM analysis
    os.environ[f"{provider}_api_key".upper()] = api_key

    from vibetracer.llm.lib import dump_llm_report
    report = dump_llm_report(str(db_path), latest=False, save=True)

    report_only = args.report_only
    if not report_only:
        from vibetracer.llm.lib import analyze_my_code
        audit_result = analyze_my_code(report)
        if audit_result.startswith('```markdown'):
            audit_result = audit_result[len('```markdown'):]
        if audit_result.endswith('```'):
            audit_result = audit_result[:-len('```')]

        # TODO: Move save_markdown to dumper for consistency
        save_markdown(audit_result, os.path.join(os.path.splitext(os.path.basename(db_path))[0], 'audit_results.md'))

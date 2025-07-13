import os
import argparse
from pathlib import Path


def save_markdown(md_content: str, file_path: str) -> None:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(md_content, encoding='utf-8')


def analyze_command(argv=None):
    parser = argparse.ArgumentParser(
        prog="vibetracer analyze",
        description="Generate and analyze a report from a .db file via LLM"
    )
    parser.add_argument(
        "--provider",
        choices=["openai", "anthropic", "google"],
        default="openai",
        help="LLM provider to use"
    )
    parser.add_argument(
        "--api_key",
        help="API key (or set {provider}_api_key env var)"
    )
    parser.add_argument(
        "path",
        help="Path to a .db file, or a directory containing .db files, or a project root with a run_dbs/ folder"
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Only generate the LLM report; skip any further analysis steps"
    )

    args = parser.parse_args(argv)
    provider = args.provider
    api_key = args.api_key or os.getenv(f"{provider}_api_key")
    report_only = args.report_only

    if not api_key and not report_only:
        parser.error(f"must provide --api_key or set {provider}_api_key in environment")

    p = Path(args.path)
    if p.is_file() and p.suffix == ".db":
        db_path = p
    elif p.is_dir():
        # first look for *.db
        dbs = sorted(p.glob("*.db"))
        if dbs:
            db_path = dbs[-1]
        else:
            # fall back to run_dbs/run_*.db
            run_dbs = p / "run_dbs"
            if not run_dbs.is_dir():
                parser.error(f"No .db files in {p} or missing {run_dbs}/")
            run_files = sorted(run_dbs.glob("run_*.db"))
            if not run_files:
                parser.error(f"No run_*.db files found in {run_dbs}/")
            db_path = run_files[-1]
    else:
        parser.error(f"{p!r} is not a .db file or directory")

    # It's important to not import these before env var is set!
    from vibetracer.llm.lib import dump_llm_report
    report = dump_llm_report(str(db_path), latest=False, save=True)
    # print(report)

    if not report_only:
        # ensure key is available for underlying LLM clients
        os.environ[f"{provider}_api_key".upper()] = api_key

        from vibetracer.llm.lib import analyze_my_code
        audit_result = analyze_my_code(report)
        if audit_result.startswith('```markdown'):
            audit_result = audit_result[len('```markdown'):]
        if audit_result.endswith('```'):
            audit_result = audit_result[:-len('```')]

        # TODO: Move save_markdown to dumper for consistency
        save_markdown(audit_result, os.path.join(os.path.splitext(os.path.basename(db_path))[0], 'audit_results.md'))

from vibetracer.database.config import DB_DIRECTORY
from vibetracer.database.dumper import Dumper
from pathlib import Path


def dump_llm_report(path: str, save: bool = False, latest: bool = False) -> str:
    db_dir = Path(path)
    if latest:
        db_dir = str(sorted(db_dir.glob("run_*.db"))[-1])
    dumper = Dumper(db_dir)
    llm_report = dumper.dump_llm_text(save=save)
    return llm_report


def dump_latest_run_llm_report(save: bool = False) -> str:
    return dump_llm_report(path=DB_DIRECTORY, save=save, latest=True)

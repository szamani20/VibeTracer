import os
import sys

from vibetracer.command.run import run_script
from vibetracer.command.analyze import analyze_command
from vibetracer.command.runalyze import runalyze_command


def main():
    if len(sys.argv) < 2:
        print("Usage: vibetracer <run|analyze|runalyze> [options]", file=sys.stderr)
        sys.exit(1)

    cwd = os.getcwd()
    os.environ['VibeTracer_CWD'] = cwd

    cmd, *rest = sys.argv[1:]
    if cmd == "run":
        if len(rest) != 1:
            print("Usage: vibetracer run path/to/script.py", file=sys.stderr)
            sys.exit(1)
        run_script(rest[0])

    elif cmd == "analyze":
        analyze_command(rest)

    elif cmd == "runalyze":
        runalyze_command(rest)

    else:
        print(f"Unknown command: {cmd!r}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

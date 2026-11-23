"""Entry point: `python3 guard.pyz <command> ...` runs the ticket guard."""

from __future__ import annotations

import argparse
import sys

from ticket_guard import cli


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="guard")
    sub = parser.add_subparsers(dest="command", required=True)
    cli.add_parser(sub)
    args = parser.parse_args(["guard", *(sys.argv[1:] if argv is None else argv)])
    return cli.run(args)


if __name__ == "__main__":
    sys.exit(main())

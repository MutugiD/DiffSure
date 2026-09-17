"""Command-line entry point."""

from __future__ import annotations

import argparse
import json

from diffsure.config import ConfigurationError, Settings
from diffsure.health import DependencyProbe
from diffsure.server import create_server


def main(argv: list[str] | None = None) -> int:
    command_parser = argparse.ArgumentParser(prog="diffsure")
    commands = command_parser.add_subparsers(dest="command", required=True)
    commands.add_parser("serve", help="run the HTTP service")
    commands.add_parser("doctor", help="print dependency readiness")
    args = command_parser.parse_args(argv)
    try:
        settings = Settings.from_env()
    except ConfigurationError as exc:
        command_parser.error(str(exc))

    if args.command == "doctor":
        health = DependencyProbe(settings).inspect()
        print(json.dumps(health.as_dict(), sort_keys=True))
        return 0 if health.ready else 3

    server = create_server(settings)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0

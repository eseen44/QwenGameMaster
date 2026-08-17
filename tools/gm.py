"""Command-line entry point for the deterministic GameMaster mechanics engine."""

from __future__ import annotations

import sys

import gm_engine
import gm_runtime


if __name__ == "__main__":
    runtime_commands = {"turn", "context", "recall", "scene", "migration", "brief"}
    if len(sys.argv) == 1 or sys.argv[1] in {"-h", "--help"}:
        print(
            "GameMaster CLI\n\n"
            "Mechanika: compile, assess, amplify, validate, generate, replay\n"
            "Runtime:   brief, turn, context, recall, scene, migration\n\n"
            "Wyjście jest domyślnie skrócone; --verbose drukuje pełny dokument.\n\n"
            "Użyj: gm.py <command> --help"
        )
        sys.exit(0)
    if len(sys.argv) > 1 and sys.argv[1] in runtime_commands:
        sys.exit(gm_runtime.main(sys.argv[1:]))
    sys.exit(gm_engine.main(sys.argv[1:]))

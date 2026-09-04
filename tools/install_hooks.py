"""Instalator hookow gita. Zapadka etapu 12.

Hooki nie sa wersjonowane (.git/hooks lezy poza drzewem roboczym), wiec plik zrodlowy stoi
w tools/hooks/ i jest STAMTAD kopiowany. Instalator jest idempotentny i nie nadpisze hooka,
ktorego nie napisal - jesli w .git/hooks/pre-commit lezy cos innego, odmawia i mowi, co tam
jest.

    python tools/install_hooks.py            # instaluj
    python tools/install_hooks.py --status    # co jest zainstalowane
    python tools/install_hooks.py --remove    # odinstaluj
"""

from __future__ import annotations

import argparse
import shutil
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "tools" / "hooks"
MARKER = "Zapadka etapu 12"


def hooks_dir() -> Path:
    """Katalog hookow - z gita, bo przy worktree nie jest to .git/hooks."""
    result = subprocess.run(
        ["git", "rev-parse", "--git-path", "hooks"], cwd=ROOT,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode:
        return ROOT / ".git" / "hooks"
    return (ROOT / result.stdout.strip()).resolve()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--remove", action="store_true")
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()

    target_dir = hooks_dir()
    installed = []
    for source in sorted(SOURCE.iterdir()):
        if source.name.startswith("."):
            continue
        target = target_dir / source.name

        if args.status:
            if not target.exists():
                print(f"{source.name:<14} NIE ZAINSTALOWANY")
            elif MARKER in target.read_text(encoding="utf-8", errors="replace"):
                print(f"{source.name:<14} zainstalowany (nasz)")
            else:
                print(f"{source.name:<14} zainstalowany, ALE OBCY - instalator go nie tknie")
            continue

        if args.remove:
            if target.exists() and MARKER in target.read_text(encoding="utf-8", errors="replace"):
                target.unlink()
                print(f"usuniety: {target}")
            elif target.exists():
                print(f"POMINIETY (obcy hook, nie nasz): {target}")
            else:
                print(f"nie bylo czego usuwac: {source.name}")
            continue

        if target.exists():
            body = target.read_text(encoding="utf-8", errors="replace")
            if MARKER not in body:
                print(f"ODMOWA: {target} istnieje i NIE jest nasz.")
                print("        Nie nadpisuje cudzych hookow. Obejrzyj go i zdecyduj sam.")
                continue
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        target.chmod(target.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        installed.append(target)
        print(f"zainstalowany: {target}")

    if installed:
        print()
        print("Hook uruchamia dwie szybkie kontrole blokujace przed kazdym commitem.")
        print("Pominiecie raz:      git commit --no-verify")
        print("Odinstalowanie:      python tools/install_hooks.py --remove")
        print("Pelny zestaw kontrol: python tools/preflight.py --full")
    return 0


if __name__ == "__main__":
    sys.exit(main())

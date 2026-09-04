"""Jedno wejscie do wszystkich szybkich kontroli repo. Zapadka etapu 12.

Bez tego kazda naprawa z REFACTOR-PLAN.md zdegraduje sie w ciagu kilkunastu tur - bo dzis
nie ma zadnego aktywnego hooka (.git/hooks ma 14 plikow, wszystkie .sample) ani CI.
Kontrole istnieja, tylko nikt ich nie uruchamia w momencie, w ktorym maja znaczenie.

Domyslnie leci zestaw SZYBKI (kilkanascie sekund), bo ma sie nadawac na pre-commit:
  - zapora dziennika        (tools/journal_guard.py)   ~8 s
  - proza jako klucze null  (tools/fix_prose_keys.py)  ~2 s
  - sieroce odwolania       (tools/audit_refs.py)      ~10 s
`--full` dokleja pelna walidacje projektu (tools/validate_project.py, ~55 s) i testy.

Kody wyjscia: 0 = czysto, 1 = kontrola BLOKUJACA nie przeszla.
Kontrole nieblokujace (sieroce odwolania, dlugi kart relacji) sa raportowane jako UWAGA -
walidator swiecacy na czerwono bez przerwy jest ignorowany, a te dlugi wymagaja decyzji
merytorycznej, nie poprawki skryptem.

Uruchomienie:
    python tools/preflight.py            # szybki zestaw
    python tools/preflight.py --full     # plus walidacja projektu i testy
    python tools/preflight.py --quiet    # tylko wynik
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(argv: list[str], timeout: int) -> tuple[int, str]:
    try:
        result = subprocess.run(
            argv, cwd=ROOT, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return 124, f"przekroczony limit {timeout} s"
    return result.returncode, (result.stdout or "") + (result.stderr or "")


def staged_files() -> list[Path]:
    """Pliki wchodzace do commita. Pusta lista = nie ma indeksu (nie jesteśmy w commicie)."""
    code, output = run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"], 30)
    if code:
        return []
    return [ROOT / line.strip() for line in output.splitlines() if line.strip()]


def journal_touched(paths: list[Path]) -> bool:
    return any("journal" in path.as_posix() for path in paths)


def prose_keys_check(scope: list[Path] | None = None) -> tuple[int, str]:
    """Skan na proze czytana jako klucze o wartosci null.

    `scope` zawezA skan do wskazanych plikow - w hooku sa to pliki wchodzace do commita.
    Pelny skan kampanii to ~600 plikow YAML i przy obciazonej maszynie zajmuje ponad
    minute, czyli za dlugo na pre-commit; zakres commita liczy sie w milisekundach,
    a wylapuje dokladnie to, co wlasnie wprowadzasz.
    """
    sys.path.insert(0, str(ROOT / "tools"))
    import yaml

    import fix_prose_keys as fixer

    if scope is not None:
        candidates = [p for p in scope if p.suffix == ".yaml" and p.exists()]
    else:
        candidates = sorted((ROOT / "campaigns").rglob("*.yaml"))

    winne: list[str] = []
    for path in candidates:
        try:
            document = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
        except yaml.YAMLError:
            continue
        count = fixer.prose_key_count(document)
        if count:
            try:
                shown = path.relative_to(ROOT).as_posix()
            except ValueError:
                shown = path.as_posix()      # plik spoza repo (np. w tescie)
            winne.append(f"{shown}: {count}")
    if winne:
        return 1, ("proza czytana jako klucze null wrocila:\n  - " + "\n  - ".join(winne)
                   + "\nnaprawa: python tools/fix_prose_keys.py")
    return 0, "0 fragmentow"


CHECKS = [
    # (nazwa, funkcja albo argv, limit_s, blokujaca)
    ("zapora dziennika", [sys.executable, "tools/journal_guard.py", "--quiet"], 180, True),
    ("proza jako klucze null", prose_keys_check, 180, True),
    ("sieroce odwolania", [sys.executable, "tools/audit_refs.py"], 180, False),
]

FULL_CHECKS = [
    ("walidacja projektu", [sys.executable, "tools/validate_project.py"], 300, False),
    ("testy", [sys.executable, "-m", "pytest", "tools/tests", "-q", "--tb=line"], 600, True),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="dokleja walidacje projektu i testy")
    parser.add_argument("--staged", action="store_true",
                        help="tryb pre-commit: zakres commita, zapora dziennika tylko gdy dziennik ruszony")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    if args.staged:
        # TRYB PRE-COMMIT. Zakres = pliki wchodzace do commita, wiec kontrola prozy jest
        # natychmiastowa. Zapora dziennika chodzi TYLKO wtedy, gdy commit rusza dziennik
        # albo transakcje - jesli ich nie dotyka, nie ma czego stracic, a to ona kosztuje
        # najwiecej czasu (przechodzi cala historie gita).
        staged = staged_files()
        checks = [("proza jako klucze null", lambda: prose_keys_check(staged), 60, True)]
        if journal_touched(staged):
            checks.insert(0, ("zapora dziennika",
                              [sys.executable, "tools/journal_guard.py", "--quiet"], 180, True))
        elif not args.quiet:
            print("[POMIN] zapora dziennika        commit nie rusza journal/")
    else:
        checks = CHECKS + (FULL_CHECKS if args.full else [])
    failures: list[str] = []
    warnings: list[str] = []

    for name, action, timeout, blocking in checks:
        started = time.monotonic()
        if callable(action):
            code, output = action()
        else:
            code, output = run(action, timeout)
        took = time.monotonic() - started
        if code == 0:
            flag = "OK  "
        elif blocking:
            flag = "BLAD"
            failures.append(name)
        else:
            flag = "UWAGA"
            warnings.append(name)
        if not args.quiet:
            print(f"[{flag:5}] {name:<26} {took:5.1f} s")
            if code != 0:
                for line in output.strip().splitlines()[:14]:
                    print(f"         {line}")

    if not args.quiet:
        print()
    if failures:
        print(f"[BLAD] preflight: {len(failures)} kontrol blokujacych nie przeszlo: {', '.join(failures)}")
        return 1
    if warnings:
        print(f"[OK] preflight: kontrole blokujace przeszly; uwagi w: {', '.join(warnings)}")
        return 0
    print("[OK] preflight: wszystko czysto")
    return 0


if __name__ == "__main__":
    sys.exit(main())

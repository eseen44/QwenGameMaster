"""Czy retcon zostal FAKTYCZNIE zastosowany w plikach, ktore sam wymienia.

POWOD ISTNIENIA. retcon_000170 (2026-09-12) wymienil campaigns/lucan/state/resources.yaml
w `state_refs_updated` i poprawil w nim JEDNA z trzech pozycji. Dwie pozostale - fiolki
tlumiace rozklad i srodek przewodzacy, oba zuzyte 84 tury wczesniej - zostaly nietkniete.
Skutkiem bylo to, przed czym ten sam retcon ostrzegal: narrator przeczytal nieaktualny zapis
i polozyl graczowi na stole przedmiot, ktorego nie ma.

Zadna istniejaca bramka tego nie widziala. `audit_refs` zglosil zero znalezisk, bo wszystkie
sciezki istnialy. `reconcile_growth --check` byl na zielono, bo nie dotyka przedmiotow.
`retcon_lint` sprawdzal FORME wpisu, nie jego SKUTEK. Deklaracja "poprawilem te pliki" byla
przyjmowana na slowo.

CO TA KONTROLA TWIERDZI. Dokladnie jedno, sprawdzalne gitem: jesli commit dodaje retcon,
to kazdy plik wymieniony w jego `state_refs_updated` musi byc zmieniony w TYM SAMYM commicie.
To NIE dowodzi, ze poprawka jest pelna - dowodzi, ze w ogole jej sprobowano. Rozjazd wewnatrz
pliku (jedna pozycja z trzech) lapie dopiero kontrola dziedzinowa; ta lapie przypadek
grubszy i najczestszy: plik zadeklarowany i nieotwarty.

Sciezki katalogowe (konczace sie "/") sa spelnione przez dowolny zmieniony plik w tym drzewie.

Uruchomienie:
    python tools/retcon_apply_check.py --staged   # tryb pre-commit, bramka
    python tools/retcon_apply_check.py            # audyt historyczny (wolny, raport)
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RETCONS_REL = "campaigns/lucan/journal/retcons.jsonl"

# Ta sama zapadka co w retcon_lint.py. Wpisy do tego numeru wlacznie sa dlugiem
# historycznym: raportowane, nigdy blokujace.
BASELINE = 142


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
        errors="replace",
    )
    return result.stdout if result.returncode == 0 else ""


def number(retcon_id: str) -> int:
    match = re.search(r"(\d+)", retcon_id or "")
    return int(match.group(1)) if match else -1


def declared_paths(retcon: dict) -> list[str]:
    raw = retcon.get("state_refs_updated")
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, str) and item.strip()]


def satisfied(declared: str, changed: set[str]) -> bool:
    """Czy deklarowana sciezka ma pokrycie w zbiorze zmienionych plikow."""
    declared = declared.split("#")[0].strip().lstrip("./")
    if not declared:
        return True
    if declared.endswith("/"):
        return any(path.startswith(declared) for path in changed)
    if declared in changed:
        return True
    # Repo miesza dwie konwencje: wzgledem korzenia i wzgledem kampanii.
    alt = f"campaigns/lucan/{declared}"
    return alt in changed


def added_retcons(diff: str) -> list[dict]:
    entries = []
    for line in diff.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        body = line[1:].strip()
        if not body.startswith("{"):
            continue
        try:
            entries.append(json.loads(body))
        except json.JSONDecodeError:
            continue
    return entries


def check_staged() -> int:
    staged = {
        path.strip() for path in git("diff", "--cached", "--name-only").splitlines()
        if path.strip()
    }
    if RETCONS_REL not in staged:
        print("[OK] zastosowanie retconow: commit nie dodaje retconu")
        return 0

    diff = git("diff", "--cached", "--unified=0", "--", RETCONS_REL)
    problems: list[str] = []
    checked = 0
    for retcon in added_retcons(diff):
        rid = retcon.get("id") or "(bez id)"
        if number(rid) <= BASELINE:
            continue
        checked += 1
        for declared in declared_paths(retcon):
            if not satisfied(declared, staged):
                problems.append(
                    f"{rid}: deklaruje {declared}, ale ten plik NIE JEST w commicie"
                )

    if problems:
        print("[BLAD] zastosowanie retconow: deklaracja bez pokrycia w commicie")
        for problem in problems:
            print(f"         {problem}")
        print("       Retcon, ktory wymienia plik i go nie otwiera, zostawia w kanonie")
        print("       zapis sprzeczny z wlasna trescia - patrz retcon_000170 i 000173.")
        return 1

    print(f"[OK] zastosowanie retconow: {checked} nowych wpisow, kazdy deklarowany plik ruszony")
    return 0


def audit_history(limit: int | None) -> int:
    """Wolny przeglad historii - raport dlugu, nigdy bramka."""
    commits = [line for line in git(
        "log", "--format=%H", "--", RETCONS_REL).splitlines() if line.strip()]
    if limit:
        commits = commits[:limit]
    problems: list[str] = []
    checked = 0
    for sha in commits:
        changed = {
            path.strip() for path in git("show", "--name-only", "--format=", sha).splitlines()
            if path.strip()
        }
        diff = git("show", "--unified=0", "--format=", sha, "--", RETCONS_REL)
        for retcon in added_retcons(diff):
            rid = retcon.get("id") or "(bez id)"
            if number(rid) <= BASELINE:
                continue
            checked += 1
            for declared in declared_paths(retcon):
                if not satisfied(declared, changed):
                    problems.append(f"{sha[:8]} {rid}: {declared} nieruszone w tym commicie")

    print(f"przejrzano {len(commits)} commitow dotykajacych korpusu, {checked} wpisow powyzej baseline")
    if problems:
        print(f"DLUG: {len(problems)} deklaracji bez pokrycia")
        for problem in problems:
            print(f"  {problem}")
    else:
        print("[OK] kazda deklaracja ma pokrycie w swoim commicie")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--staged", action="store_true", help="tryb pre-commit (bramka)")
    parser.add_argument("--limit", type=int, default=None,
                        help="ogranicz audyt historyczny do N ostatnich commitow")
    args = parser.parse_args()
    return check_staged() if args.staged else audit_history(args.limit)


if __name__ == "__main__":
    sys.exit(main())

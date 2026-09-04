"""Zapora dziennika: sprawdza maszynowo, ze cofniecie tury nie zjadlo kanonu.

AGENTS.md i DECISIONS.md nazywaja dziennik NIEZMIENNYM ("Bledu historycznego nie kasuj:
dodaj retcon i popraw aktualny stan"). Do 2026-09-04 nic tego nie sprawdzalo, a cofniecie
tury bylo realizowane jako usuniecie linii z events.jsonl albo nadpisanie pliku transakcji.
Ten skrypt zamienia te regule z akapitu w warunek, ktory da sie zlamac tylko swiadomie.

Trzy kontrole:
  1. ZADEN identyfikator zdarzenia, ktory kiedykolwiek istnial w historii gita, nie moze
     zniknac z journal/events.jsonl.
  2. KAZDA uchylona wersja wpisu albo pliku transakcji (tresc rozna od biezacej) musi lezec
     w journal/superseded/ z suma kontrolna w MANIFEST.json.
  3. Sumy kontrolne w manifescie musza zgadzac sie z plikami w archiwum.

Uruchomienie:  python tools/journal_guard.py [--quiet]
Kod wyjscia:   0 = czysto, 1 = kanon utracony albo archiwum niespojne.
Naprawa:       python tools/recover_superseded.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVENTS = "campaigns/lucan/journal/events.jsonl"
TRANSACTIONS = "campaigns/lucan/journal/transactions"
SUPERSEDED = ROOT / "campaigns/lucan/journal/superseded"


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    return "" if result.returncode else result.stdout


def parse_events(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(entry, dict) and entry.get("id"):
            out[entry["id"]] = line
    return out


def event_map(rev: str) -> dict[str, str]:
    """Wpisy z rewizji gita."""
    return parse_events(git("show", f"{rev}:{EVENTS}"))


def working_events() -> dict[str, str]:
    """Wpisy z DRZEWA ROBOCZEGO - zapora musi wykryc strate PRZED commitem, nie po.

    Czytanie z HEAD bylo pierwotnym bledem tego skryptu: walidator, ktory patrzy na commit,
    przepuszcza usuniecie wpisu az do momentu, gdy jest ono juz w historii.
    """
    path = ROOT / EVENTS
    return parse_events(path.read_text(encoding="utf-8")) if path.exists() else {}


# Pola KSIEGOWE: znaczniki o statusie wpisu, nie jego tresc. Ich dopisanie albo zmiana NIE
# jest przepisaniem historii i nie wymaga archiwizacji starej wersji.
#
# summary NIGDY tu nie trafi - to jedyny zapis prozy kampanii i cel istnienia tej zapory.
# Tak samo changes, time_advanced_seconds, actors, scene_id, intent_achieved, arrangement.
BOOKKEEPING_KEYS = {"superseded_by", "superseded_aspects", "supersession_scope"}


def canonical(line: str) -> str:
    """Tresc wpisu bez pol ksiegowych - to po niej poznajemy, czy historia zostala zmieniona."""
    document = json.loads(line)
    if isinstance(document, dict):
        document = {k: v for k, v in document.items() if k not in BOOKKEEPING_KEYS}
    return json.dumps(document, sort_keys=True, ensure_ascii=False)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_manifest() -> dict:
    path = SUPERSEDED / "MANIFEST.json"
    if not path.exists():
        return {"events": [], "transactions": []}
    return json.loads(path.read_text(encoding="utf-8"))


def collect_problems() -> tuple[list[str], list[str], int]:
    """Cala logika kontroli. Zwraca (naruszenia, uwagi, liczba_wpisow_w_drzewie).

    Wydzielone z main(), zeby tools/tests/test_journal_guard.py mogl sprawdzic, ze zapora
    ZAPALA SIE NA CZERWONO - pierwsza wersja tego skryptu przechodzila na zielono przy
    usunietym wpisie i przy podmienionej tresci.
    """
    problems: list[str] = []
    notes: list[str] = []

    manifest = load_manifest()
    archived_events = {(e["event_id"], e["content_sha256"]) for e in manifest.get("events", [])}
    archived_tx = {t["content_sha256"] for t in manifest.get("transactions", [])}

    head_events = working_events()
    head_canon = {i: canonical(l) for i, l in head_events.items()}

    # 1 + 2: zbierz KAZDA wersje KAZDEGO wpisu, jaka kiedykolwiek istniala w historii
    # ORAZ w HEAD, i zestaw ja z drzewem roboczym.
    #
    # Pierwotna wersja tego skryptu porownywala wylacznie pary (commit^, commit) i przez to
    # przepuszczala DWA oczywiste naruszenia, na ktorych ja sprawdzilem: usuniecie wpisu
    # dodanego w ostatnim commicie (brak wersji w zadnym rodzicu, wiec nie bylo z czym
    # porownac) oraz podmiane tresci wpisu niezmienionego w danym commicie (skrot
    # "niezmieniony w tym commicie" konczyl kontrole). Zbior wszystkich wersji nie ma
    # tej dziury: kazda wersja musi byc albo biezaca, albo zarchiwizowana.
    revisions = [s for s in git("log", "--format=%H", "--", EVENTS).split() if s]
    ever: dict[str, list[tuple[str, str]]] = {}   # id -> [(canon, sha_commita)]
    for commit in revisions + ["HEAD"]:
        for event_id, raw in event_map(commit).items():
            try:
                canon = canonical(raw)
            except json.JSONDecodeError:
                continue
            bucket = ever.setdefault(event_id, [])
            if all(canon != existing for existing, _ in bucket):
                bucket.append((canon, commit[:7]))

    for event_id, versions in sorted(ever.items()):
        if event_id not in head_events:
            where = ", ".join(sorted({c for _, c in versions}))[:60]
            problems.append(
                f"UTRACONY WPIS: {event_id} istnieje w historii ({where}), "
                f"a nie ma go w journal/events.jsonl"
            )
            continue
        for canon, commit in versions:
            if canon == head_canon[event_id]:
                continue
            if (event_id, sha(canon)) not in archived_events:
                problems.append(
                    f"UCHYLONA WERSJA BEZ ARCHIWUM: {event_id} mial w {commit} inna tresc, "
                    f"ktorej nie ma ani w dzienniku, ani w journal/superseded/ "
                    f"(uruchom tools/recover_superseded.py)"
                )

    notes.append(f"wersji wpisow przejrzanych w historii: {sum(len(v) for v in ever.values())}")

    # 2b: pliki transakcji usuniete albo nadpisane.
    #
    # Jedno przejscie po historii z --name-status. Rodzicielski blob sciagamy WYLACZNIE dla
    # statusow M i D - dla A (dodanie) nie ma czego porownywac, a to wlasnie A stanowi
    # wieksza czesc 237 plikow. Pierwotna wersja robila git show dla kazdej pary
    # (commit, plik) i nie miescila sie w dwoch minutach.
    changes: list[tuple[str, str, str]] = []
    current_commit = ""
    for line in git("log", "--format=@@%H", "--name-status", "--", TRANSACTIONS).splitlines():
        if line.startswith("@@"):
            current_commit = line[2:].strip()
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status, name = parts[0].strip(), parts[-1].strip()
        if not name.startswith(TRANSACTIONS) or not name.endswith(".yaml"):
            continue
        if status[:1] in {"M", "D"}:
            changes.append((current_commit, status[:1], name))

    for commit, status, name in changes:
        before = git("show", f"{commit}^:{name}")
        if not before:
            continue
        path = ROOT / name
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        if before == current:
            continue
        if sha(before) not in archived_tx:
            how = "usuniety" if status == "D" else "nadpisany"
            problems.append(
                f"TRANSAKCJA BEZ ARCHIWUM: {Path(name).name} {how} w {commit[:7]}, "
                f"a starej wersji nie ma w journal/superseded/"
            )

    # Kazdy plik transakcji obecny w HEAD musi byc obecny w drzewie roboczym.
    for name in git("ls-tree", "-r", "--name-only", "HEAD", TRANSACTIONS).splitlines():
        name = name.strip()
        if not name.endswith(".yaml"):
            continue
        if not (ROOT / name).exists():
            problems.append(
                f"USUNIETA TRANSAKCJA: {Path(name).name} jest w HEAD, a nie ma jej w drzewie roboczym"
            )

    notes.append(f"zmian plikow transakcji przejrzanych: {len(changes)}")

    # 3: integralnosc samego archiwum.
    for entry in manifest.get("events", []):
        path = SUPERSEDED / entry["file"]
        if not path.exists():
            problems.append(f"ARCHIWUM NIEKOMPLETNE: brak pliku {entry['file']}")
            continue
        body = path.read_text(encoding="utf-8")
        # Integralnosc pliku sprawdzamy po SUROWEJ tresci (file_sha256), a dopasowanie do
        # wersji z historii po tresci bez pol ksiegowych (content_sha256). Zmieszanie tych
        # dwoch rzeczy dalo falszywy alarm na trzech plikach, gdy pola ksiegowe wyszly
        # spod canonical().
        expected_file = entry.get("file_sha256")
        if expected_file and sha(body) != expected_file:
            problems.append(f"ARCHIWUM NARUSZONE: {entry['file']} nie zgadza sie z suma kontrolna pliku")
        elif not expected_file and sha(canonical(body.strip())) != entry["content_sha256"]:
            problems.append(f"ARCHIWUM NARUSZONE: {entry['file']} nie zgadza sie z suma kontrolna tresci")
    for entry in manifest.get("transactions", []):
        if not (SUPERSEDED / entry["file"]).exists():
            problems.append(f"ARCHIWUM NIEKOMPLETNE: brak pliku {entry['file']}")

    notes.append(f"zarchiwizowanych wersji uchylonych: {len(archived_events)} wpisow, "
                 f"{len(archived_tx)} transakcji")
    return problems, notes, len(head_events)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    problems, notes, entries = collect_problems()

    if not args.quiet:
        print(f"wpisow w dzienniku (drzewo robocze): {entries}")
        for note in notes:
            print(f"  uwaga: {note}")

    if problems:
        print()
        print(f"[BLAD] zapora dziennika: {len(problems)} naruszen")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    if not args.quiet:
        print("[OK] zapora dziennika: zaden wpis ani plik transakcji nie zostal utracony")
    return 0


if __name__ == "__main__":
    sys.exit(main())

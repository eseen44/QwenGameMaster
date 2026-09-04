"""Odzysk uchylonych wersji wpisow dziennika i plikow transakcji z historii gita.

Powod: cofniecie tury w tym repo bylo realizowane jako USUNIECIE albo NADPISANIE wpisu
w journal/events.jsonl oraz plikow journal/transactions/*.yaml. Identyfikatory tur
nie przepadly (HEAD ma je wszystkie), ale PIERWOTNA PROZA cofnietych tur istnieje
wylacznie jako obiekty gita. DECISIONS.md i AGENTS.md nazywaja dziennik niezmiennym,
wiec ten stan jest sprzeczny z wlasnym kontraktem repo.

Skrypt jest CZYSTO ADDYTYWNY: nie modyfikuje ani nie usuwa niczego w drzewie roboczym,
tylko zapisuje uchylone wersje do campaigns/lucan/journal/superseded/ wraz z manifestem
sum kontrolnych. Idempotentny - powtorne uruchomienie nadpisze te same pliki ta sama
trescia i przeliczy manifest.

Uruchomienie:  python tools/recover_superseded.py [--dry-run]
Weryfikacja:   python tools/journal_guard.py
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
    if result.returncode:
        return ""
    return result.stdout


def event_map(rev: str) -> dict[str, str]:
    """id -> surowa linia JSON, dla wskazanej rewizji."""
    out: dict[str, str] = {}
    for line in git("show", f"{rev}:{EVENTS}").splitlines():
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


def canonical(line: str) -> str:
    """Normalizacja, ktora odsiewa samo przeformatowanie od zmiany tresci."""
    return json.dumps(json.loads(line), sort_keys=True, ensure_ascii=False)


def touching_commits(path: str) -> list[str]:
    return [s for s in git("log", "--format=%H", "--", path).split() if s]


def collect_event_variants() -> list[dict]:
    """Kazda wersja wpisu, ktora ROZNI SIE TRESCIA od tego, co jest w HEAD."""
    head = {i: canonical(l) for i, l in event_map("HEAD").items()}
    seen: set[tuple[str, str]] = set()
    variants: list[dict] = []
    for sha in touching_commits(EVENTS):
        before = event_map(f"{sha}^")
        if not before:
            continue
        after = event_map(sha)
        for event_id, raw in before.items():
            try:
                canon = canonical(raw)
            except json.JSONDecodeError:
                continue
            # Wersja jest uchylona, jesli jej tresc nie jest ani biezaca w HEAD,
            # ani identyczna z tym, co ten commit zostawil.
            if canon == head.get(event_id):
                continue
            if event_id in after and canon == canonical(after[event_id]):
                continue
            key = (event_id, hashlib.sha256(canon.encode("utf-8")).hexdigest()[:12])
            if key in seen:
                continue
            seen.add(key)
            variants.append({
                "event_id": event_id,
                "superseded_in": sha[:7],
                "commit_subject": git("log", "-1", "--format=%s", sha).strip(),
                "commit_date": git("log", "-1", "--format=%ad", "--date=short", sha).strip(),
                "content_sha256": hashlib.sha256(canon.encode("utf-8")).hexdigest(),
                "chars": len(raw),
                "raw": raw,
            })
    return variants


def collect_transaction_variants() -> list[dict]:
    """Pliki transakcji usuniete albo nadpisane w historii."""
    out: list[dict] = []
    seen: set[str] = set()
    for sha in touching_commits(TRANSACTIONS):
        names = git("show", "--format=", "--name-only", sha).splitlines()
        for name in names:
            name = name.strip()
            if not name.startswith(TRANSACTIONS) or not name.endswith(".yaml"):
                continue
            before = git("show", f"{sha}^:{name}")
            if not before:
                continue
            current = (ROOT / name).read_text(encoding="utf-8") if (ROOT / name).exists() else ""
            if before == current:
                continue
            digest = hashlib.sha256(before.encode("utf-8")).hexdigest()
            if digest in seen:
                continue
            seen.add(digest)
            out.append({
                "path": name,
                "basename": Path(name).name,
                "superseded_in": sha[:7],
                "commit_subject": git("log", "-1", "--format=%s", sha).strip(),
                "commit_date": git("log", "-1", "--format=%ad", "--date=short", sha).strip(),
                "removed_from_tree": not (ROOT / name).exists(),
                "content_sha256": digest,
                "chars": len(before),
                "raw": before,
            })
    return out


def strip_prepared_writes(raw: str) -> tuple[str, bool]:
    """Odcina prepared_writes, zachowujac request, preview, roll i outcome.

    prepared_writes to pelne snapshoty dokumentow stanu (zmierzona redundancja ~90%)
    i stanowia 84,7% objetosci katalogu transakcji. Decyzja tury - czyli to, po co
    ktos siega do uchylonej transakcji - siedzi w pozostalych polach. Pelna wersja
    zostaje odzyskiwalna komenda zapisana w manifescie (pole full_version).
    """
    try:
        import ruamel.yaml
        yaml = ruamel.yaml.YAML()
        yaml.preserve_quotes = True
        yaml.width = 4096
        import io
        document = yaml.load(raw)
        if not isinstance(document, dict) or "prepared_writes" not in document:
            return raw, False
        count = len(document.get("prepared_writes") or [])
        document["prepared_writes"] = None
        document["prepared_writes_note"] = (
            f"ODCIETE PRZY ARCHIWIZACJI ({count} wpisow). Byly to pelne snapshoty dokumentow "
            "stanu o zmierzonej redundancji ~90%. Pelna wersja pliku: patrz pole full_version "
            "w MANIFEST.json - obiekt gita nadal istnieje i nic nie zostalo utracone."
        )
        buffer = io.StringIO()
        yaml.dump(document, buffer)
        return buffer.getvalue(), True
    except Exception:
        # Gdy cokolwiek pojdzie nie tak, archiwizujemy plik w calosci.
        # Zasada jest jedna: nigdy nie tracimy tresci przez wlasna optymalizacje.
        return raw, False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    events = collect_event_variants()
    transactions = collect_transaction_variants()

    print(f"uchylone wersje wpisow dziennika: {len(events)}")
    for v in sorted(events, key=lambda x: (x["event_id"], x["superseded_in"])):
        print(f"  {v['event_id']:<44} uchylona w {v['superseded_in']} ({v['commit_date']}), {v['chars']} znakow")
    print(f"uchylone wersje plikow transakcji: {len(transactions)}")
    for v in sorted(transactions, key=lambda x: x["basename"]):
        how = "usuniety z drzewa" if v["removed_from_tree"] else "nadpisany"
        print(f"  {v['basename']:<32} {how} w {v['superseded_in']} ({v['commit_date']}), {v['chars']} znakow")

    if args.dry_run:
        print("\n--dry-run: nic nie zapisano")
        return 0

    (SUPERSEDED / "events").mkdir(parents=True, exist_ok=True)
    (SUPERSEDED / "transactions").mkdir(parents=True, exist_ok=True)

    manifest = {
        "schema_version": 1,
        "object_type": "superseded_canon_archive",
        "purpose": (
            "Uchylone wersje wpisow dziennika i plikow transakcji, odzyskane z historii gita. "
            "TO NIE JEST KANON OBOWIAZUJACY - kazdy plik tutaj zostal zastapiony przez nowsza "
            "wersje w journal/events.jsonl albo journal/transactions/. Archiwum istnieje, zeby "
            "cofniecie tury nie usuwalo prozy bezpowrotnie, i zeby narrator mogl odpowiedziec "
            "na pytanie 'co tam bylo wczesniej' bez grzebania w gicie."
        ),
        "do_not_load_in_a_normal_turn": True,
        "events": [],
        "transactions": [],
    }

    for v in events:
        name = f"{v['event_id']}__{v['superseded_in']}.json"
        (SUPERSEDED / "events" / name).write_text(v["raw"] + "\n", encoding="utf-8", newline="\n")
        manifest["events"].append({k: v[k] for k in
                                   ("event_id", "superseded_in", "commit_subject", "commit_date",
                                    "content_sha256", "chars")} | {"file": f"events/{name}"})

    for v in transactions:
        name = f"{Path(v['basename']).stem}__{v['superseded_in']}.yaml"
        body, stripped = strip_prepared_writes(v["raw"])
        (SUPERSEDED / "transactions" / name).write_text(body, encoding="utf-8", newline="\n")
        manifest["transactions"].append({k: v[k] for k in
                                         ("path", "superseded_in", "commit_subject", "commit_date",
                                          "removed_from_tree", "content_sha256", "chars")} |
                                        {"file": f"transactions/{name}",
                                         "prepared_writes_stripped": stripped,
                                         "chars_archived": len(body),
                                         "full_version": f"git show {v['superseded_in']}^:{v['path']}"})

    (SUPERSEDED / "MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")

    total = sum(v["chars"] for v in events) + sum(v["chars"] for v in transactions)
    print(f"\nzapisane do {SUPERSEDED.relative_to(ROOT)}: "
          f"{len(events)} wpisow + {len(transactions)} transakcji, {total} znakow")
    return 0


if __name__ == "__main__":
    sys.exit(main())

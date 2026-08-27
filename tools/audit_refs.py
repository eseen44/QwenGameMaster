# -*- coding: utf-8 -*-
"""Audyt spojnosci danych kampanii: YAML/JSONL, referencje plikow, strefy, indeksy.

Uruchomienie (z dowolnego katalogu):
    python tools/audit_refs.py
    python tools/audit_refs.py --verbose     # wypisz wszystkie znaleziska, nie tylko 30

Kod wyjscia 1, jesli cokolwiek jest zepsute; 0, jesli czysto.

CZEGO NARZEDZIE CELOWO NIE ZGLASZA (sprawdzone 2026-08-27, to NIE sa bledy):
  * `templates/**` - zawiera swiadome placeholdery (worlds/example, example_event_id).
  * Ten sam `id` w pliku definicji i w pliku instancji (pc_lucan, companion_spidey,
    companion_varkhen) - to zamierzony rozdzial definicja/instancja.
  * Ten sam `id` w location.yaml i w maps/layout.yaml - lustrowanie geometrii z zalozenia.
  * Sciezki `ref:` sa rozwiazywane wzgledem korzenia repo ORAZ korzenia kampanii
    (campaigns/<nazwa>/) ORAZ katalogu pliku - w danych uzywane sa wszystkie trzy formy.
  * `/journal/transactions/`, `/snapshots/`, `/migration/`, `/journal/imports/` - niezmienne
    zapisy historyczne. Blad w turze nr 12 nie jest do naprawy.
"""
import argparse
import collections
import glob
import json
import os
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST = ("/journal/transactions/", "/snapshots/", "/migration/", "/journal/imports/")
REF_SKIP_PREFIX = ("http", "source_", "candidate_")
OK_EVENT_PREFIX = ("milestone_", "source_", "retcon_", "player_", "narrator_",
                   "candidate_", "import_", "event_act_", "turn_", "event_turn_")
EVENT_KEYS = {
    "source_event_id", "revised_event_id", "declaration_event_id", "event_id",
    "disposition_event_id", "profile_source_event_id", "last_event_id",
    "last_updated_event_id", "logged_event_id", "last_confirmed_event_id",
    "retired_by", "expansion_source_event_id", "last_refreshed_event_id",
    "first_used_event_id",
}
ZONE_KEYS = ("zone_id", "current_zone_id", "from_zone", "to_zone")
# Wartosci pola zone_id, ktore sa swiadomymi znacznikami narracyjnymi, nie strefami.
ZONE_PLACEHOLDERS = {"unknown"}

norm = lambda p: p.replace(os.sep, "/")


def is_hist(path):
    return any(h in norm(path) for h in HIST)


def load_all():
    docs, broken = {}, []
    for f in sorted(set(glob.glob("**/*.yaml", recursive=True))):
        try:
            docs[norm(f)] = yaml.safe_load(open(f, encoding="utf-8"))
        except Exception as exc:
            broken.append((norm(f), str(exc).split("\n")[0]))
    return docs, broken


def load_jsonl():
    events, bad = [], []
    for f in sorted(glob.glob("campaigns/**/*.jsonl", recursive=True)):
        for i, line in enumerate(open(f, encoding="utf-8"), 1):
            if not line.strip():
                continue
            try:
                events.append(json.loads(line))
            except Exception as exc:
                bad.append((norm(f), i, str(exc)[:70]))
    return events, bad


def campaign_roots():
    return [norm(d) for d in glob.glob("campaigns/*") if os.path.isdir(d)]


def ref_resolves(ref, owner, roots):
    p = ref.split("#")[0].strip()
    if not p or "/" not in p or p.startswith(REF_SKIP_PREFIX):
        return True
    cands = [p, os.path.join(os.path.dirname(owner), p)]
    cands += [r + "/" + p for r in roots]
    return any(os.path.exists(c) for c in cands)


def walk(node, fn):
    if isinstance(node, dict):
        for k, v in node.items():
            fn(k if isinstance(k, str) else str(k), v)
            walk(v, fn)
    elif isinstance(node, list):
        for x in node:
            walk(x, fn)


def collect_refs(doc):
    out = set()

    def visit(k, v):
        if k == "ref" or k.endswith(("_ref", "_refs")):
            for c in (v if isinstance(v, list) else [v]):
                if isinstance(c, str):
                    out.add(os.path.basename(c.split("#")[0]))

    walk(doc, visit)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    os.chdir(ROOT)

    docs, broken_yaml = load_all()
    journal, broken_jsonl = load_jsonl()
    roots = campaign_roots()

    event_ids = set()
    for o in journal:
        for k in ("event_id", "id"):
            if isinstance(o.get(k), str):
                event_ids.add(o[k])
    for f in glob.glob("campaigns/*/journal/transactions/*.yaml"):
        b = os.path.basename(f)[:-5]
        event_ids |= {b, "event_" + b}

    bad_refs, bad_events = [], []
    for f, d in docs.items():
        if is_hist(f) or norm(f).startswith("templates/"):
            continue

        def visit(k, v, _f=f):
            if k == "ref" or k.endswith(("_ref", "_refs")):
                for c in (v if isinstance(v, list) else [v]):
                    if isinstance(c, str) and not ref_resolves(c, _f, roots):
                        bad_refs.append((_f, k, c))
            if k in EVENT_KEYS and isinstance(v, str) and v not in ("null", "none"):
                base = v.split("#")[0]
                if base and base not in event_ids and not base.startswith(OK_EVENT_PREFIX):
                    bad_events.append((_f, k, v))

        walk(d, visit)

    # --- strefy: zdefiniowane w location.yaml LUB maps/layout.yaml ---
    zones = set()
    for f, d in docs.items():
        if "/locations/" not in norm(f) or not isinstance(d, dict):
            continue
        for z in (d.get("zones") or []):
            if isinstance(z, dict) and isinstance(z.get("id"), str):
                zones.add(z["id"])
    bad_zones = collections.defaultdict(list)
    for f, d in docs.items():
        if is_hist(f) or norm(f).startswith("templates/"):
            continue

        def visit(k, v, _f=f):
            if k in ZONE_KEYS and isinstance(v, str) and v not in ZONE_PLACEHOLDERS:
                if v not in zones and v.startswith("zone_"):
                    bad_zones[v].append(_f)

        walk(d, visit)

    # --- indeksy vs dysk (referencje liczone generycznie, niezaleznie od klucza) ---
    idx_missing = []
    for ix in sorted(glob.glob("campaigns/*/**/index.yaml", recursive=True)):
        ixn = norm(ix)
        if "/migration/" in ixn:
            continue
        d = docs.get(ixn)
        if not isinstance(d, dict):
            continue
        listed = collect_refs(d)
        for p in sorted(glob.glob(os.path.dirname(ixn) + "/*.yaml")):
            bn = os.path.basename(p)
            if bn != "index.yaml" and bn not in listed:
                idx_missing.append((ixn, bn))

    sections = [
        ("YAML niepoprawne", broken_yaml),
        ("JSONL niepoprawne", broken_jsonl),
        ("Referencje do nieistniejacych plikow", bad_refs),
        ("Wskazania na nieistniejace zdarzenia", bad_events),
        ("Strefy uzywane, ale niezdefiniowane", sorted((z, len(fs), fs[0]) for z, fs in bad_zones.items())),
        ("Byty na dysku poza indeksem", idx_missing),
    ]
    total = 0
    for title, rows in sections:
        total += len(rows)
        flag = "OK  " if not rows else "BLAD"
        print("[%s] %-42s %d" % (flag, title, len(rows)))
        limit = len(rows) if args.verbose else 30
        for r in rows[:limit]:
            print("        ", r)
        if len(rows) > limit:
            print("         ... i %d wiecej (--verbose)" % (len(rows) - limit))
    print()
    print("Plikow YAML: %d   znalezisk: %d" % (len(docs), total))
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())

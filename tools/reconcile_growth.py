"""Uzgodnienie silnika z rejestrem wzrostu. Etap 10, czesc druga.

PROBLEM. state/growth-banks.yaml jest "miejscem prawdy dla nadwyzki i dojrzalosci" (tak mowi
jego wlasny naglowek) i prowadzony jest RECZNIE, z polem `as_of_event_id`. Rownolegle silnik
liczy pule z regul `regeneration` / `decay` / `hunting_recovery` w instancjach oraz z laczy
w sustained-links.yaml. To dwie ksiegi tego samego, ktore moga sie rozjechac - i rozjechaly.

CZEGO TEN SKRYPT NIE ROBI. Nie uzgadnia ich za nikogo. Uzgodnienie wymaga decyzji
mechanicznych: czy dana sluga faktycznie zeruje, czy stoi na posterunku, czy jest karmiona
z reki. Skrypt POKAZUJE roznice per pula, z uzasadnieniem z rejestru, zeby te decyzje daly
sie podjac na liczbach zamiast z pamieci.

Dwa realne bledy wylapane ta miara i naprawione osobno:
  - retcon_000145: flaga tlumiaca ubytek dzialala tylko przy DOKLADNEJ nazwie, wiec dwa okazy
    traciły rezerwe bez podstawy;
  - retcon_000146: spy_wasp_01 miala bramke zeru na flage `autonomous_hunting`, ktorej nie
    nosila - od tury 177 tylko ubywala, do 0/3, przy kanonie deklarujacym +1,0 na dobe.

Uruchomienie:  python tools/reconcile_growth.py [--only-divergent]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "campaigns" / "lucan" / "state"
INSTANCES = STATE / "instances"
DAY = 86400
POOL = "necrotic_reservoir"


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}


def link_flow() -> dict[str, float]:
    """Netto na dobe z laczy podtrzymujacych - rejestr je liczy, a miara na samych
    regulach instancji ich nie widzi. Bez tego polowa "rozjazdow" jest artefaktem."""
    flows: dict[str, float] = {}
    document = load(STATE / "sustained-links.yaml")
    for link in document.get("links") or []:
        if not isinstance(link, dict) or not link.get("active"):
            continue
        interval = link.get("interval_seconds") or DAY
        source = link.get("source_instance_id")
        target = link.get("target_instance_id")
        out = (link.get("source_units_per_interval") or 0) * DAY / max(1, interval)
        inflow = (link.get("target_units_per_interval") or 0) * DAY / max(1, interval)
        if source:
            flows[source] = flows.get(source, 0.0) - out
        if target:
            flows[target] = flows.get(target, 0.0) + inflow
    return flows


def engine_rate(instance: dict) -> tuple[float, list[str]]:
    """Stawka dobowa z regul strumieni, z uwzglednieniem bramek i tlumienia."""
    flags = set(instance.get("status_flags") or []) | set(instance.get("traits") or [])
    pool = (instance.get("resources") or {}).get(POOL)
    if not isinstance(pool, dict):
        return 0.0, ["brak puli"]
    total, notes = 0.0, []
    for field, direction in (("regeneration", 1), ("decay", -1), ("hunting_recovery", 1)):
        rule = pool.get(field)
        if not isinstance(rule, dict):
            continue
        if field == "decay" and ("decay_suppressed" in flags or pool.get("decay_suppressed")):
            notes.append("ubytek stlumiony")
            continue
        requires = rule.get("requires") or []
        brak = [item for item in requires if item not in flags]
        if brak:
            notes.append(f"{field} zablokowany brakiem flag: {', '.join(brak)}")
            continue
        total += direction * (rule.get("units") or 0) * DAY / max(1, rule.get("interval_seconds") or DAY)
    return total, notes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only-divergent", action="store_true")
    args = parser.parse_args()

    bank = load(STATE / "growth-banks.yaml")
    declared = {row["id"]: row for row in bank.get("banks") or [] if isinstance(row, dict)}
    flows = link_flow()

    rows, divergent, missing = [], 0, []
    for path in sorted(INSTANCES.glob("*.yaml")):
        if path.name == "index.yaml":
            continue
        instance = load(path)
        iid = instance.get("id")
        if not iid:
            continue
        pool = (instance.get("resources") or {}).get(POOL)
        if not isinstance(pool, dict):
            continue
        streams, notes = engine_rate(instance)
        total_engine = streams + flows.get(iid, 0.0)
        entry = declared.get(iid)
        if entry is None:
            missing.append(iid)
        rate = entry.get("rate_per_day") if entry else None
        delta = None if rate is None else round(total_engine - rate, 2)
        if delta is not None and abs(delta) >= 0.01:
            divergent += 1
        rows.append({
            "id": iid, "declared": rate, "streams": round(streams, 2),
            "links": round(flows.get(iid, 0.0), 2), "engine": round(total_engine, 2),
            "delta": delta, "state": f"{pool.get('current')}/{pool.get('capacity')}",
            "notes": notes, "basis": (entry or {}).get("basis", ""),
        })

    print(f"{'wezel':<26}{'rejestr':>8}{'strumienie':>11}{'lacza':>7}{'silnik':>8}"
          f"{'roznica':>9}{'stan':>9}")
    for row in rows:
        if args.only_divergent and (row["delta"] is None or abs(row["delta"]) < 0.01):
            continue
        rate = "-" if row["declared"] is None else f"{row['declared']:.1f}"
        delta = "brak wpisu" if row["delta"] is None else f"{row['delta']:+.2f}"
        print(f"{row['id']:<26}{rate:>8}{row['streams']:>11.2f}{row['links']:>7.2f}"
              f"{row['engine']:>8.2f}{delta:>9}{row['state']:>9}")
        for note in row["notes"]:
            print(f"    uwaga: {note}")

    print()
    print(f"pul: {len(rows)} | rozjazdow: {divergent} | bez wpisu w rejestrze: {len(missing)}")
    if missing:
        print(f"  {', '.join(missing)}")
    print(f"rejestr as_of: {bank.get('as_of_event_id')}")
    print("Uzgodnienie wymaga decyzji mechanicznych - ten raport ich nie podejmuje.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

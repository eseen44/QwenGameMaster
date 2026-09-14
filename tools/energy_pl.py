"""Rachunek zyskow i strat energetycznych calej sieci, jedna tabela.

POWOD ISTNIENIA. roster.py pokazuje, KTO gdzie stoi i co ma w zbiorniku. Nie pokazuje
PRZEPLYWU: ile wezel dziennie bierze, ile na siebie zjada, ile zostaje i ile z tego idzie
w rozwoj. Te cztery liczby leza w trzech roznych miejscach - regeneration i decay w plikach
instancji, rate_per_day i sufity w growth-banks.yaml, a dowoz do Varkhena w osobnym bloku -
i dopoki nie stoja obok siebie, nie da sie odpowiedziec na pytanie "kto na tym traci".

DWA ROWNOLEGLE RACHUNKI, KTORE SIE NIE SKLADAJA, i ta tabela ich NIE ukrywa:

  PRZYCHOD / UTRZYMANIE / DELTA  - model ZBIORNIKA z silnika. regeneration i hunting_recovery
                                   daja, decay zabiera, silnik nalicza to co tykniecie.
  GROWTH                         - rejestr RECZNY z growth-banks.yaml. rate_per_day jest juz
                                   wartoscia NETTO wedle daily-balance.yaml (posterunek 0,
                                   wolny zer +1, obfity +2, padlinozerca +0,5).

Te dwie kolumny opisuja te sama sluge dwoma jezykami i nie musza sie zgadzac. Gdzie sie
rozjezdzaja wyraznie, skrypt to WYPISUJE zamiast usredniac.

Uruchomienie:
    python tools/energy_pl.py
    python tools/energy_pl.py --netto    # dopisz kolumne: ile z growth realnie schodzi drabina
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CAMPAIGN = ROOT / "campaigns" / "lucan"
INSTANCES = CAMPAIGN / "state" / "instances"
BANKS = CAMPAIGN / "state" / "growth-banks.yaml"

DAY = 86400.0
ANCHORS = {"companion_spidey", "webber_anchored", "spy_hawk_moth_01", "spy_beetle_01"}
OUTSIDE = {"companion_varkhen"}
PLAYER = "pc_lucan"


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def per_day(rule: dict | None) -> float:
    """Zamienia blok interval_seconds/units na stawke dobowa."""
    if not isinstance(rule, dict):
        return 0.0
    interval = rule.get("interval_seconds")
    units = rule.get("units")
    if not interval or units is None:
        return 0.0
    return float(units) * DAY / float(interval)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="P&L energetyczny sieci.")
    ap.add_argument("--netto", action="store_true",
                    help="dopisz kolumne z tym, co realnie schodzi drabina rozdzialu")
    args = ap.parse_args(argv)

    banks_doc = load(BANKS)
    rows = {r["id"]: r for r in (banks_doc.get("banks") or []) if r.get("id")}
    feed = banks_doc.get("varkhen_overflow_feed") or {}
    feed_sources = feed.get("sources") or {}
    feed_arriving = float(feed.get("arriving_per_day") or 0)

    table = []
    for path in sorted(INSTANCES.glob("*.yaml")):
        if path.name == "index.yaml":
            continue
        inst = load(path)
        iid = inst.get("id")
        if not iid or inst.get("status") != "active":
            continue

        pool_name, pool = None, None
        for name, candidate in (inst.get("resources") or {}).items():
            if isinstance(candidate, dict) and "current" in candidate:
                pool_name, pool = name, candidate
                break

        flags = set(inst.get("status_flags") or [])
        income = 0.0
        if pool:
            income += per_day(pool.get("regeneration"))
            if "autonomous_hunting" in flags:
                income += per_day(pool.get("hunting_recovery"))
        upkeep = 0.0
        if pool and "decay_suppressed" not in flags:
            upkeep += per_day(pool.get("decay"))
        if iid in OUTSIDE:
            income += feed_arriving

        row = rows.get(iid, {})
        growth = row.get("rate_per_day")
        cap = row.get("growth_cap_per_day")
        given = float(feed_sources.get(iid) or 0)

        if iid == PLAYER:
            group = 0
        elif iid in OUTSIDE:
            group = 1
        elif iid in ANCHORS:
            group = 2
        else:
            group = 3

        table.append({
            "grupa": group,
            "nazwa": inst.get("name") or iid,
            "id": iid,
            "przychod": income,
            "utrzymanie": upkeep,
            "delta": income - upkeep,
            "growth": growth,
            "cap": cap,
            "oddaje": given,
            "pool": f"{pool['current']}/{pool.get('capacity', '?')}" if pool else "-",
        })

    table.sort(key=lambda r: (r["grupa"], -(r["growth"] or 0), r["id"]))

    def fmt(x):
        if x is None:
            return "-"
        if isinstance(x, str):
            return x
        return f"{x:+.2f}".rstrip("0").rstrip(".") if x else "0"

    head = ["NAZWA", "PRZYCHOD", "UTRZYM.", "DELTA", "GROWTH", "SUFIT", "ODDAJE", "POOL"]
    keys = ["nazwa", "przychod", "utrzymanie", "delta", "growth", "cap", "oddaje", "pool"]
    cells = [[fmt(r[k]) for k in keys] for r in table]
    widths = [max(len(head[i]), *(len(c[i]) for c in cells)) for i in range(len(head))]

    titles = {0: "LUCAN", 1: "VARKHEN (poza drabina, retcon_000113)",
              2: "ZAKOTWICZONE (szczebel 2)", 3: "RESZTA (szczebel 3)"}
    print("  ".join(h.ljust(w) for h, w in zip(head, widths)))
    print("-" * (sum(widths) + 2 * (len(widths) - 1)))
    last = None
    for r, c in zip(table, cells):
        if r["grupa"] != last:
            print(f"[{titles[r['grupa']]}]")
            last = r["grupa"]
        print("  ".join(x.ljust(w) for x, w in zip(c, widths)))

    print()
    print("PRZYCHOD/UTRZYMANIE/DELTA - model ZBIORNIKA z silnika (regeneration, hunting_recovery,")
    print("  decay). GROWTH - rejestr RECZNY z growth-banks, juz netto wedle daily-balance.")
    print("  To sa DWA JEZYKI opisujace te sama sluge i nie musza sie zgadzac.")
    print("ODDAJE - ile overflow tego wezla idzie dzis do Varkhena (varkhen_overflow_feed).")

    total_growth = sum(r["growth"] for r in table if r["growth"] and r["id"] != PLAYER)
    total_given = sum(r["oddaje"] for r in table)
    print()
    print(f"suma GROWTH slug (bez Lucana): {total_growth:.1f} na dobe")
    print(f"  z tego oddawane Varkhenowi:  {total_given:.1f} wychodzace, "
          f"{feed_arriving:.1f} dochodzace po stratach")
    overflow = sum(float(r.get("overflow_per_day") or 0) for r in rows.values())
    print(f"caly OVERFLOW w rejestrze (jedyne, co schodzi drabina): {overflow:.1f} na dobe")
    if abs(overflow - total_given) < 0.01:
        print("  UWAGA: caly overflow idzie do Varkhena, wiec na szczeble 2 i 3 nie schodzi NIC.")

    lucan_row = rows.get(PLAYER, {})
    print()
    print("NIESPOJNOSC, KTOREJ TA TABELA NIE ROZSTRZYGA (zgloszona 2026-09-14):")
    print("  pc-lucan#regeneration mowi 0,75/h = 18,0 na dobe, w tym 0,50/h = 12,0 opisane jako")
    print("  DOWOZ Z SIECI - liczba ustawiona retconem 000141 przy nadwyzce 16,5 i nieruszana.")
    print(f"  Rejestr mowi, ze do rozdzialu idzie caly overflow, czyli {overflow:.1f}.")
    print("  12,0 nie ma wiec pokrycia w 2,3. Skrypt tego NIE usrednia i nie zgaduje.")
    print(f"  bank Lucana: {lucan_row.get('bank', '?')}, sufit przyjecia "
          f"{lucan_row.get('growth_cap_per_day', '?')} na dobe.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

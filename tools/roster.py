"""Tabela calej sieci: kto gdzie stoi, jaki ma rozkaz, ile ma i jak blisko szczebla.

POWOD ISTNIENIA. servants_check.py jest BRAMKA - mowi, co jest zlamane, i milczy, kiedy
wszystko sie zgadza. To za malo do pytania "czy wszyscy sie odliczaja i robia to, co powinni",
bo odpowiedz na nie wymaga ZOBACZENIA calosci naraz, a nie listy naruszen. Brief wypisuje
network_roster z samymi pozycjami, growth-banks.yaml trzyma stawki i banki, orders leza
w instancjach - i nigdzie te trzy rzeczy nie stoja obok siebie. Dopoki nie stoja, "wszyscy sa
na posterunkach" jest zdaniem, ktorego nikt nie sprawdzil.

DLACZEGO DLUG MIGRACYJNY JEST ZWINIETY W JEDNA LINIE. Pierwsza wersja tego skryptu wypisala
59 uwag, z czego 55 to brakujace position.fix i pozostale position.formation - czyli JEDNA
rzecz z retcon_000171, powielona przez trzydziesci plikow. AGENTS.md mowi wprost, ze walidator
swiecacy na czerwono bez przerwy jest ignorowany, wiec dlug idzie do podsumowania, a osobne
linie dostaja tylko rzeczy, ktore da sie dzis rozstrzygnac.

CZYTA, NIE PISZE. Zadnego pliku nie zmienia i nie jest wpiety w preflight.

Uruchomienie:
    python tools/roster.py                 # tabela + uwagi
    python tools/roster.py --problems      # same uwagi
    python tools/roster.py --debt          # rozwin dlug migracyjny do pojedynczych linii
    python tools/roster.py --sort bank     # id (domyslnie) | nazwa | bank | rate | miejsce
    python tools/roster.py --wide          # nie skracaj kolumny rozkazu
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CAMPAIGN = ROOT / "campaigns" / "lucan"
INSTANCES = CAMPAIGN / "state" / "instances"
BANKS = CAMPAIGN / "state" / "growth-banks.yaml"
LINKS = CAMPAIGN / "state" / "sustained-links.yaml"

# pc_lucan nie jest sluga i ma wlasna drabine (x10). Idzie osobnym blokiem pod tabela.
PLAYER_ID = "pc_lucan"
# Varkhen stoi POZA drabina wzrostu i poza rozdzialem nadwyzki z wlasnej decyzji Lucana
# (retcon_000113, growth-banks#distribution_priority.outside_the_ladder). Brak wiersza
# w rejestrze jest u niego stanem poprawnym, nie brakiem.
OUTSIDE_THE_LADDER = {"companion_varkhen"}


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def num(value) -> str:
    if isinstance(value, float):
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return str(value)


def instances() -> list[dict]:
    out = []
    for path in sorted(INSTANCES.glob("*.yaml")):
        if path.name == "index.yaml":
            continue
        doc = load(path)
        if doc.get("id"):
            out.append(doc)
    return out


def pool_of(inst: dict):
    """Pierwsza pula zasobow instancji. Zbiornik jest jeden poza Spideyem (toksyna osobno)."""
    for name, pool in (inst.get("resources") or {}).items():
        if isinstance(pool, dict) and "current" in pool:
            return name, pool
    return None, None


def ladder_rungs(banks_doc: dict) -> list[dict]:
    rungs = ((banks_doc.get("ladder") or {}).get("rungs")) or []
    return sorted(rungs, key=lambda r: r.get("threshold", 0))


def next_rung(rungs: list[dict], bank: float):
    for rung in rungs:
        if bank < rung.get("threshold", 0):
            return rung.get("id", "?"), rung["threshold"] - bank
    return None, None


def fmt_orders(inst: dict, wide: bool) -> str:
    orders = inst.get("orders") or []
    active = [o for o in orders if o.get("status") == "active"]
    if not active:
        done = [o for o in orders if o.get("status") == "completed"]
        return "-" if not done else f"(zamkniete: {len(done)})"
    text = ", ".join(str(o.get("id", "?")) for o in active)
    if not wide and len(text) > 38:
        text = text[:35] + "..."
    return text


def fmt_place(inst: dict) -> str:
    pos = inst.get("position") or {}
    loc = str(pos.get("location_id", "?")).replace("loc_", "")
    zone = str(pos.get("zone_id", "?")).replace("zone_", "")
    fix = (pos.get("fix") or {}).get("status")
    mark = {"confirmed": "", "inferred": " ~", "stale": " !", "unknown": " ??"}.get(fix, " ?")
    return f"{loc}/{zone}{mark}"


def build_row(inst: dict, rows_by_id: dict, rungs: list[dict], wide: bool) -> dict:
    iid = inst["id"]
    row = rows_by_id.get(iid, {})
    _, pool = pool_of(inst)
    integrity = inst.get("integrity") or {}
    has_bank = bool(row)
    bank = float(row.get("bank", 0) or 0) if has_bank else None
    if iid in OUTSIDE_THE_LADDER:
        nxt = "poza drabina"
    elif has_bank:
        rung, distance = next_rung(rungs, bank)
        nxt = f"{rung} za {distance:.2f}" if rung else "szczyt drabiny"
    else:
        nxt = "-"
    return {
        "id": iid,
        "name": inst.get("name") or iid,
        "anchor": "*" if inst.get("anchor_class") else "",
        "place": fmt_place(inst),
        "orders": fmt_orders(inst, wide),
        "pool": f"{num(pool['current'])}/{num(pool.get('capacity', '?'))}" if pool else "-",
        "integrity": f"{num(integrity.get('current', '?'))}/{num(integrity.get('maximum', '?'))}"
        if integrity
        else "-",
        "rate": num(row["rate_per_day"]) if row.get("rate_per_day") is not None else "-",
        "bank": num(bank) if has_bank else "-",
        "maturity": row.get("maturity", "-"),
        "next": nxt,
        "_inst": inst,
        "_row": row,
    }


def print_table(rows: list[dict], title: str) -> None:
    if not rows:
        return
    head = ("NAZWA", "ID", "MIEJSCE", "ROZKAZ", "ZBIORNIK", "INT", "STAWKA", "BANK", "DOJRZALOSC", "DO SZCZEBLA")
    keys = ["display", "id", "place", "orders", "pool", "integrity", "rate", "bank", "maturity", "next"]
    for r in rows:
        r["display"] = r["anchor"] + r["name"]
    widths = [max(len(h), *(len(str(r[k])) for r in rows)) for h, k in zip(head, keys)]
    line = "  ".join(h.ljust(w) for h, w in zip(head, widths))
    print(title)
    print(line)
    print("-" * len(line))
    for r in rows:
        print("  ".join(str(r[k]).ljust(w) for k, w in zip(keys, widths)))
    print()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Tabela sieci: rozkazy, pozycje, zasoby, banki.")
    ap.add_argument("--problems", action="store_true", help="same uwagi, bez tabeli")
    ap.add_argument("--debt", action="store_true", help="rozwin dlug migracyjny do pojedynczych linii")
    ap.add_argument("--sort", choices=["id", "nazwa", "bank", "rate", "miejsce"], default="id")
    ap.add_argument("--wide", action="store_true", help="nie skracaj kolumny rozkazu")
    args = ap.parse_args(argv)

    banks_doc = load(BANKS)
    rungs = ladder_rungs(banks_doc)
    rows_by_id = {r["id"]: r for r in (banks_doc.get("banks") or []) if r.get("id")}

    insts = instances()
    by_id = {i["id"]: i for i in insts}
    servants = [i for i in insts if i["id"] != PLAYER_ID]
    live = [i for i in servants if i.get("status") == "active"]
    gone = [i for i in servants if i.get("status") != "active"]

    table = [build_row(i, rows_by_id, rungs, args.wide) for i in live]
    keyfun = {
        "id": lambda r: r["id"],
        "nazwa": lambda r: r["name"],
        "bank": lambda r: -float(r["bank"]) if r["bank"] != "-" else 1e9,
        "rate": lambda r: -float(r["rate"]) if r["rate"] != "-" else 1e9,
        "miejsce": lambda r: r["place"],
    }[args.sort]
    table.sort(key=keyfun)

    if not args.problems:
        print_table(table, f"SIEC CZYNNA ({len(table)})")
        print("  ! pozycja stale, ?? nieznana, ~ wywnioskowana, ? brak position.fix")
        print("  * przy nazwie = okaz ZAKOTWICZONY (anchor_class)")

        if gone:
            print()
            print(f"POZA SIECIA ({len(gone)}): " + ", ".join(
                f"{i.get('name') or i['id']} [{i.get('status', '?')}]" for i in gone))

        lucan = by_id.get(PLAYER_ID)
        lrow = rows_by_id.get(PLAYER_ID, {})
        if lucan:
            _, pool = pool_of(lucan)
            bank = float(lrow.get("bank", 0) or 0)
            ahead = [r for r in rungs if bank < (r.get("lucan_threshold") or 0)]
            nxt = ahead[0] if ahead else None
            print()
            print("LUCAN - wlasna drabina, x10 (retcon_000180)")
            tail = ""
            if nxt:
                tail = (f"   nastepny szczebel {nxt['id']} przy {nxt['lucan_threshold']}"
                        f", brakuje {nxt['lucan_threshold'] - bank:.2f}")
            print(f"  rezerwa {num(pool['current'])}/{num(pool.get('capacity'))}"
                  f"   bank {num(bank)}{tail}")

    # ---- uwagi -------------------------------------------------------------
    problems: list[str] = []
    debt_fix: list[str] = []
    debt_formation: list[str] = []

    for r in table:
        inst, row = r["_inst"], r["_row"]
        iid = r["id"]
        label = f"{r['name']} ({iid})" if r["name"] != iid else iid
        pos = inst.get("position") or {}
        _, pool = pool_of(inst)

        if pool and not row and iid not in OUTSIDE_THE_LADDER:
            problems.append(f"{label}: ma zbiornik, a NIE MA wiersza w growth-banks.yaml")

        fix = (pos.get("fix") or {}).get("status")
        if fix in {"stale", "unknown"}:
            problems.append(f"{label}: pozycja {fix} - ostatnie potwierdzenie "
                            f"{(pos.get('fix') or {}).get('as_of_event_id', '?')}")
        elif not pos.get("fix"):
            debt_fix.append(iid)

        if "formation" in pos:
            debt_formation.append(iid)

        if (row.get("rate_per_day") or 0) < 0:
            problems.append(f"{label}: stawka ujemna {row['rate_per_day']} - deficyt dobowy")

        if not (inst.get("orders") or []) and str(row.get("balance_row", "")).startswith("posterunek"):
            problems.append(f"{label}: rejestr mowi 'posterunek z zadaniem', "
                            "a w instancji NIE MA zadnego rozkazu")

    for bid in rows_by_id:
        if bid not in by_id:
            problems.append(f"{bid}: wiersz w growth-banks.yaml bez pliku instancji")

    for link in (load(LINKS).get("links") or []):
        if link.get("active"):
            units = link.get("source_units_per_interval")
            channel = link.get("channel", "feed")
            note = " (adres, zerowy przeplyw)" if not units else ""
            problems.append(
                f"lacze {link.get('id')}: AKTYWNE [{channel}], "
                f"{link.get('source_instance_id')} -> {link.get('target_instance_id')}, "
                f"{units} na interwal{note}")

    print()
    if problems:
        print(f"DO ROZSTRZYGNIECIA ({len(problems)}):")
        for p in problems:
            print(f"  - {p}")
    else:
        print("DO ROZSTRZYGNIECIA: nic. Kazdy aktywny zbiornik ma wiersz, kazdy posterunek")
        print("  z zadaniem ma rozkaz, zaden wezel nie jest na minusie.")

    if debt_fix or debt_formation:
        print()
        print("DLUG MIGRACYJNY PO retcon_000171 (nie dzisiejszy problem, nie blokuje gry):")
        if debt_fix:
            print(f"  - {len(debt_fix)} instancji bez position.fix - pozycja bez zrodla")
        if debt_formation:
            print(f"  - {len(debt_formation)} instancji z pozostalym position.formation - "
                  "pole zamkniete od t_275, miesza pozycje z rozkazem")
        if args.debt:
            if debt_fix:
                print("    bez fix: " + ", ".join(debt_fix))
            if debt_formation:
                print("    z formation: " + ", ".join(debt_formation))
        else:
            print("    pelne listy: --debt")

    print()
    print(f"czynnych {len(table)}, poza siecia {len(gone)}, "
          f"rejestr wzrostu as_of {banks_doc.get('as_of_event_id', '?')}")
    print("To jest ODCZYT. Zadnego pliku ten skrypt nie zmienia.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

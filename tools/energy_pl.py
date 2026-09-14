"""Rachunek zyskow i strat energetycznych calej sieci, jedna tabela.

POWOD ISTNIENIA. roster.py pokazuje, KTO gdzie stoi i co ma w zbiorniku. Nie pokazuje
PRZEPLYWU: ile wezel dziennie bierze, ile na siebie zjada, ile zostaje i ile z tego idzie
w rozwoj. Te liczby leza w roznych miejscach - regeneracja, zer, decay i pojemnosc w plikach
instancji, a dowoz do Varkhena w growth-banks.yaml - i dopoki nie stoja obok siebie, nie da
sie odpowiedziec na pytanie "kto na tym traci".

MODEL (retcon_000196, growth-banks.yaml#energy_model), cztery kroki:

  1. Na wezel:  PRZYCHOD (regeneracja + zer) - UTRZYMANIE (decay) = DELTA.
  2. Sieciowo:  suma delt + zrodla spoza sieci - dowoz do Varkhena = SURPLUS.
  3. Kaskada:   surplus wypelnia growth OD GORY - Lucan, potem zakotwiczone, potem reszta.
                Nizszy szczebel dostaje wylacznie to, czego wyzszy nie przyjal.
  4. Sufit:     polowa pojemnosci zbiornika, dla kazdego bez wyjatku.

Kolumna GROWTH z growth-banks.yaml zostala z tabeli USUNIETA. Byla recznym rejestrem
rownoleglym do modelu zbiornika i pokazywanie ich obok siebie utrwalalo rozjazd, zamiast
go rozstrzygac. Sufit liczy sie teraz z pliku instancji, a rozdzial - z kaskady.

Uruchomienie:
    python tools/energy_pl.py
"""

from __future__ import annotations

import argparse
import sys
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
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    argparse.ArgumentParser(description="P&L energetyczny sieci.").parse_args(argv)

    banks_doc = load(BANKS)
    rows = {r["id"]: r for r in (banks_doc.get("banks") or []) if r.get("id")}
    feed = banks_doc.get("varkhen_overflow_feed") or {}
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

        cap = float(pool["capacity"]) / 2.0 if pool and pool.get("capacity") else None
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
            "cap": cap,
            "pool": f"{pool['current']}/{pool.get('capacity', '?')}" if pool else "-",
        })

    table.sort(key=lambda r: (r["grupa"], -(r["cap"] or 0), r["id"]))

    def fmt(x):
        if x is None:
            return "-"
        if isinstance(x, str):
            return x
        if not x:
            return "0"
        return f"{x:+.2f}".rstrip("0").rstrip(".")

    # --- KROK 2: surplus sieci ---
    suma_delt = sum(r["delta"] for r in table if r["id"] not in (PLAYER,) and r["grupa"] != 1)
    zrodlo_zew = float((rows.get("spy_beetle_01") or {}).get("rate_per_day") or 0)
    do_varkhena = float(feed.get("leaving_per_day") or 0)
    surplus = suma_delt + zrodlo_zew - do_varkhena

    # --- KROK 3: kaskada od gory ---
    # Szczeble ida po kolei: co przyjmie wyzszy, nie schodzi nizej. WEWNATRZ szczebla model
    # gracza nie podaje kolejnosci, wiec skrypt dzieli PROPORCJONALNIE do sufitu - kazdy
    # dostaje ten sam ulamek swojego. To wybor narratora, nie kanon; patrz stopka.
    zostaje = surplus
    for r in table:
        r["dostaje"] = None if r["grupa"] == 1 else 0.0
    for grupa in (0, 2, 3):
        wezly = [r for r in table if r["grupa"] == grupa]
        sufit = sum(r["cap"] or 0.0 for r in wezly)
        if sufit <= 0 or zostaje <= 0:
            continue
        udzial = min(1.0, zostaje / sufit)
        for r in wezly:
            r["dostaje"] = (r["cap"] or 0.0) * udzial
        zostaje -= sufit * udzial

    head = ["NAZWA", "PRZYCHOD", "UTRZYM.", "DELTA", "SUFIT", "DOSTAJE", "POOL"]
    keys = ["nazwa", "przychod", "utrzymanie", "delta", "cap", "dostaje", "pool"]
    cells = [[fmt(r[k]) for k in keys] for r in table]
    widths = [max(len(head[i]), *(len(c[i]) for c in cells)) for i in range(len(head))]

    titles = {0: "LUCAN - szczebel 1", 1: "VARKHEN - poza drabina (retcon_000113)",
              2: "ZAKOTWICZONE - szczebel 2", 3: "RESZTA - szczebel 3"}
    print("  ".join(h.ljust(w) for h, w in zip(head, widths)))
    print("-" * (sum(widths) + 2 * (len(widths) - 1)))
    last = None
    for r, c in zip(table, cells):
        if r["grupa"] != last:
            print(f"[{titles[r['grupa']]}]")
            last = r["grupa"]
        print("  ".join(x.ljust(w) for x, w in zip(c, widths)))

    print()
    print("SURPLUS SIECI (krok 2 modelu, growth-banks#energy_model):")
    print(f"  suma delt wezlow          {suma_delt:+7.1f}")
    print(f"  zrodlo spoza sieci        {zrodlo_zew:+7.1f}   (trzy kanaly w niszy, pije General)")
    print(f"  do Varkhena               {-do_varkhena:+7.1f}   "
          f"(dochodzi {feed_arriving:.1f} po stratach)")
    print(f"  {'':-<28}")
    print(f"  SURPLUS                   {surplus:+7.1f}")
    print()
    print("KASKADA (krok 3): od gory, nizszy szczebel dostaje to, czego wyzszy nie przyjal.")
    for grupa, tytul in ((0, "Lucan"), (2, "zakotwiczone"), (3, "reszta")):
        sufit = sum(r["cap"] or 0 for r in table if r["grupa"] == grupa)
        dostaje = sum(r["dostaje"] or 0 for r in table if r["grupa"] == grupa)
        ile = len([r for r in table if r["grupa"] == grupa])
        proc = f"{dostaje / sufit * 100:.0f}%" if sufit else "-"
        print(f"  {tytul:<14} sufit {sufit:6.1f}   dostaje {dostaje:6.1f}   ({proc} sufitu, "
              f"{ile} wezlow)")
    print(f"  niewykorzystane: {max(0.0, zostaje):.1f}")
    print()
    print("SUFIT GROWTH = POLOWA POJEMNOSCI ZBIORNIKA (krok 4), bez wyjatkow.")
    print("PRZYCHOD to wlasne zbieranie wezla, UTRZYMANIE to jego decay. DELTA = roznica.")
    print("KOLEJNOSC SZCZEBLI jest kanonem (retcon_000196). PODZIAL WEWNATRZ szczebla nie -")
    print("  model nie mowi, kto w 'reszcie' ma pierwszenstwo, wiec skrypt dzieli PRO RATA:")
    print("  kazdy wezel dostaje ten sam ulamek swojego sufitu. Kolejnosc w rzedzie wybralby")
    print("  gracz, gdyby chcial - wtedy pierwsze wezly stoja pelne, a reszta pusta.")
    print("Straty propagacji NIE sa w kaskadzie stosowane - patrz")
    print("  growth-banks#energy_model.not_settled_propagation_losses.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

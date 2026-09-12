"""Kontrola rejestru wzrostu. Etap 10, czesc druga - PRZEPISANA 2026-09-04.

CZEGO TA WERSJA NIE ROBI I DLACZEGO POPRZEDNIA BYLA BLEDNA. Pierwsza wersja porownywala
`rate_per_day` z rejestru ze stawka dobowa liczona z regul `regeneration` / `decay` /
`hunting_recovery` w instancji i raportowala 19 "rozjazdow". To bylo porownanie dwoch
ROZNYCH WIELKOSCI:
  - `rate_per_day` w rejestrze to NADWYZKA, ktora wezel generuje ponad wlasne utrzymanie -
    dlatego obok stoja `growth_cap_per_day` (do banku) i `overflow_per_day` (do sieci),
    a naglowek pliku mowi o "nadwyzce generowanej przez siec";
  - reguly w instancji opisuja ZBIORNIK wezla, ktory przy obfitym zerze stoi na maksimum.
Zuk, ktory ma pelny zbiornik i 0,5 nadwyzki na dobe, nie jest wiec zadna niespojnoscia.
Te same 19 wierszy raportowalem jako dlug - byl to blad zalozenia raportu, nie danych.
Tak samo "5 wezlow bez wpisu w rejestrze": wszystkie piec jest ZNISZCZONYCH albo martwych
(trzy cmy zjedzone, pajak wyssany przez Lucana, wijoprzasz zmiazdzony), wiec ich brak
w rejestrze wzrostu jest poprawny.

CO JEST SPRAWDZALNE I CO TA WERSJA SPRAWDZA:
  1. deklarowana_nadwyzka - `surplus_economy.daily_network_surplus_units` musi rownac sie
     sumie `rate_per_day` wezlow AKTYWNYCH z pominieciem tych z `funded_by: lucan_reserve`.
     Tak wylapano realna niespojnosc: nota mowila 14,5, suma pliku dawala 20,0, a nadwyzka
     sieci wynosi 16,5 - roznica 3,5 to zuk 01 ladowany z rezerwy LUCANA (retcon_000141),
     czyli ta sama energia liczona dwa razy.
  2. wezel_aktywny_bez_wpisu - kazda AKTYWNA instancja ze zbiornikiem musi miec wpis.
  3. wezel_martwy_z_wpisem - zniszczony wezel nie moze zostac w rejestrze nadwyzki.
  4. sufit_rozwoju - `growth_cap_per_day` musi rownac sie POLOWIE pojemnosci zbiornika,
     bo tak brzmi `growth_intake_cap` w tym samym pliku.
  5. zbiornik_ubywa - zaden aktywny wezel nie moze tracic rezerwy netto. To klasa, ktora
     dala dwa realne retcony: retcon_000145 (flaga tlumiaca dzialala tylko przy DOKLADNEJ
     nazwie, wiec dwa okazy tracily bez podstawy) i retcon_000146 (spy_wasp_01 miala bramke
     zeru na flage, ktorej nie nosila - od t_177 tylko ubywala, do 0/3, przy kanonie
     deklarujacym +1,0 na dobe).

Uruchomienie:  python tools/reconcile_growth.py [--check]
   --check konczy sie kodem 1 przy naruszeniu; bez niej tylko raportuje.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CAMPAIGN = ROOT / "campaigns" / "lucan"
STATE = CAMPAIGN / "state"
INSTANCES = STATE / "instances"
DAY = 86400
POOL = "necrotic_reservoir"

# Wpisy rejestru, ktore nie sa wezlami sieci - Lucan jest czlowiekiem i nie ma zbiornika
# w tym sensie, a jego stawka jest po stronie ODBIORCY, nie generowania.
NIE_WEZLY = {"pc_lucan"}


def wiersze_bilansu() -> dict[str, float]:
    """Tabela bilansu dobowego: {id_wiersza: jednostki_na_dobe}.

    Brak pliku = pusta tabela i kontrola sie nie odpala. Tabela jest PRZEPISANIEM
    retcon_000105 i nastepnych, nie nowym zrodlem stawek.
    """
    path = ROOT / "system" / "mechanics" / "daily-balance.yaml"
    if not path.is_file():
        return {}
    document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {
        row["id"]: float(row["units_per_day"])
        for row in (document.get("rows") or [])
        if isinstance(row, dict) and "id" in row and "units_per_day" in row
    }


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}


def instance_files() -> dict[str, dict]:
    """id instancji -> dokument. Nazwa pliku uzywa myslnikow, id podkreslen."""
    out: dict[str, dict] = {}
    for path in sorted(INSTANCES.glob("*.yaml")):
        if path.name == "index.yaml":
            continue
        document = load(path)
        if document.get("id"):
            out[document["id"]] = document
    return out


def link_flow() -> dict[str, float]:
    """Netto na dobe z laczy podtrzymujacych - silnik je stosuje osobno
    (gm_runtime.process_sustained_links), wiec miara na samych regulach ich nie widzi."""
    flows: dict[str, float] = {}
    for link in load(STATE / "sustained-links.yaml").get("links") or []:
        if not isinstance(link, dict) or not link.get("active"):
            continue
        interval = link.get("interval_seconds") or DAY
        out = (link.get("source_units_per_interval") or 0) * DAY / max(1, interval)
        inflow = (link.get("target_units_per_interval") or 0) * DAY / max(1, interval)
        if link.get("source_instance_id"):
            flows[link["source_instance_id"]] = flows.get(link["source_instance_id"], 0.0) - out
        if link.get("target_instance_id"):
            flows[link["target_instance_id"]] = flows.get(link["target_instance_id"], 0.0) + inflow
    return flows


def engine_rate(instance: dict) -> tuple[float, list[str]]:
    """Dobowa zmiana ZBIORNIKA z regul strumieni, z bramkami i tlumieniem."""
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
        brak = [item for item in (rule.get("requires") or []) if item not in flags]
        if brak:
            notes.append(f"{field} zablokowany brakiem flag: {', '.join(brak)}")
            continue
        total += direction * (rule.get("units") or 0) * DAY / max(1, rule.get("interval_seconds") or DAY)
    return total, notes


def check(bank: dict | None = None, instances: dict[str, dict] | None = None,
          flows: dict[str, float] | None = None) -> tuple[dict[str, list[str]], dict[str, float]]:
    """Argumenty wstrzykiwalne, zeby kazda z pieciu kontrol dala sie ZOBACZYC, jak odrzuca.

    Bramka, ktorej nikt nie widzial dzialajacej, nie jest bramka - to zdanie z tego repo
    kosztowalo mnie w tym audycie cztery wpadki, w tym dwie wlasne zapadki przepuszczajace
    oczywiste naruszenia.
    """
    bank = load(STATE / "growth-banks.yaml") if bank is None else bank
    entries = {row["id"]: row for row in bank.get("banks") or [] if isinstance(row, dict)}
    instances = instance_files() if instances is None else instances
    flows = link_flow() if flows is None else flows
    problems: dict[str, list[str]] = {}

    def zglos(nazwa: str, opis: str) -> None:
        problems.setdefault(nazwa, []).append(opis)

    # 1. Deklarowana nadwyzka sieci kontra suma wpisow.
    economy = bank.get("surplus_economy") or {}
    deklarowana = economy.get("daily_network_surplus_units")
    policzona = 0.0
    for iid, row in entries.items():
        if iid in NIE_WEZLY or row.get("funded_by") == "lucan_reserve":
            continue
        if (instances.get(iid) or {}).get("status") not in (None, "active"):
            continue
        policzona += row.get("rate_per_day") or 0
    if deklarowana is None:
        zglos("deklarowana_nadwyzka",
              "brak pola surplus_economy.daily_network_surplus_units - liczba zostaje "
              "tylko w prozie, a proza sie nie waliduje")
    elif abs(deklarowana - policzona) > 0.001:
        zglos("deklarowana_nadwyzka",
              f"plik deklaruje {deklarowana} na dobe, a suma stawek wezlow aktywnych "
              f"(bez funded_by: lucan_reserve) daje {policzona}")

    # 2 i 3. Zbior wezlow w rejestrze kontra zbior instancji ze zbiornikiem.
    for iid, instance in instances.items():
        if not isinstance((instance.get("resources") or {}).get(POOL), dict):
            continue
        aktywny = instance.get("status") == "active"
        if aktywny and iid not in entries:
            zglos("wezel_aktywny_bez_wpisu",
                  f"{iid} ma zbiornik i jest aktywny, a nie ma wpisu w rejestrze nadwyzki")
        if not aktywny and iid in entries:
            zglos("wezel_martwy_z_wpisem",
                  f"{iid} ma status '{instance.get('status')}', a wciaz stoi w rejestrze "
                  f"ze stawka {entries[iid].get('rate_per_day')}")

    # 4. Sufit rozwoju to POLOWA pojemnosci zbiornika - tak mowi growth_intake_cap.
    for iid, row in entries.items():
        cap = row.get("growth_cap_per_day")
        pool = ((instances.get(iid) or {}).get("resources") or {}).get(POOL)
        if cap is None or not isinstance(pool, dict) or pool.get("capacity") is None:
            continue
        polowa = pool["capacity"] / 2
        if abs(cap - polowa) > 0.001:
            zglos("sufit_rozwoju",
                  f"{iid}: growth_cap_per_day {cap}, a polowa pojemnosci zbiornika "
                  f"({pool['capacity']}) to {polowa}")

    # 5. Zbiornik aktywnego wezla nie moze ubywac netto.
    for iid, instance in instances.items():
        if instance.get("status") != "active":
            continue
        pool = (instance.get("resources") or {}).get(POOL)
        if not isinstance(pool, dict):
            continue
        netto, notes = engine_rate(instance)
        netto += flows.get(iid, 0.0)
        if netto < -0.001:
            zglos("zbiornik_ubywa",
                  f"{iid}: netto {netto:+.2f} na dobe przy stanie "
                  f"{pool.get('current')}/{pool.get('capacity')}"
                  + (f" ({'; '.join(notes)})" if notes else ""))

    liczby = {
        "wezlow_w_rejestrze": len(entries),
        "instancji_ze_zbiornikiem": sum(
            1 for i in instances.values()
            if isinstance((i.get("resources") or {}).get(POOL), dict)),
        "nadwyzka_deklarowana": deklarowana if deklarowana is not None else float("nan"),
        "nadwyzka_policzona": policzona,
    }
    # STAWKA MUSI POCHODZIC Z WIERSZA TABELI, NIE Z GLOWY (retcon_000172B).
    # Wpis, ktory deklaruje balance_row, ma miec stawke rowna wartosci tego wiersza
    # pomniejszonej o zadeklarowane utrzymanie. Wpisy BEZ wiersza sa dlugiem: raportowane
    # osobno, nigdy blokujace - bo brak wiersza znaczy "tabela nie ma tej kategorii",
    # a to rozstrzyga czlowiek, nie skrypt.
    tabela = wiersze_bilansu()
    bez_wiersza: list[str] = []
    for entry in (bank.get("banks") or []):
        if not isinstance(entry, dict):
            continue
        node_id = entry.get("id")
        if node_id in NIE_WEZLY:
            continue
        row = entry.get("balance_row")
        if not row:
            bez_wiersza.append(str(node_id))
            continue
        if row not in tabela:
            zglos("wiersz_bilansu", f"{node_id}: balance_row '{row}' nie istnieje w tabeli")
            continue
        oczekiwane = tabela[row] - float(entry.get("upkeep_per_day", 0.0) or 0.0)
        stawka = float(entry.get("rate_per_day", 0.0) or 0.0)
        if abs(stawka - oczekiwane) > 1e-9:
            zglos("wiersz_bilansu",
                  f"{node_id}: rate_per_day {stawka} != wiersz {row} ({tabela[row]}) "
                  f"minus utrzymanie {entry.get('upkeep_per_day', 0.0)} = {oczekiwane}")
    liczby["wezlow_bez_wiersza"] = f"{len(bez_wiersza)} ({', '.join(bez_wiersza)})" if bez_wiersza else "0"

    return problems, liczby


def zaleglosc() -> str | None:
    """Jak daleko rejestr wzrostu jest za zegarem kampanii.

    RAPORT, NIE BRAMKA. Zaleglosc jest normalnym stanem miedzy rozliczeniami - rejestr
    jest reczny z decyzji (jeden pisarz na plik), wiec nadrabia go czlowiek albo osobne
    narzedzie. Blokowanie commita za to zatrzymywaloby gre.

    POWOD ISTNIENIA: pole as_of_event_id istnialo od dawna i bylo wypisywane w raporcie,
    ale z niczym nieporownywane. 2026-09-12 rejestr stal na turze 235 przy zegarze na 274
    i nikt tego nie widzial, bo obie liczby byly w dwoch roznych plikach.
    """
    bank = load(STATE / "growth-banks.yaml")
    time_doc = load(STATE / "time.yaml")
    as_of = bank.get("as_of_event_id")
    teraz = time_doc.get("last_event_id")
    if not as_of or not teraz or as_of == teraz:
        return None

    def tura(event_id: str) -> int | None:
        m = re.search(r"(\d+)$", event_id or "")
        return int(m.group(1)) if m else None

    a, b = tura(as_of), tura(teraz)
    opis = f"rejestr wzrostu stoi na {as_of}, zegar na {teraz}"
    if a is not None and b is not None and b > a:
        opis += f" - {b - a} tur"
    # Liczba TUR jest myląca sama w sobie: tura to minuty, a stawki sa dobowe. Jesli da sie
    # odczytac czas z transakcji rejestru, podaj DOBY - to jest jednostka, w ktorej liczy
    # sie zaleglosc.
    transakcja = CAMPAIGN / "journal" / "transactions" / f"{as_of.replace('event_', '')}.yaml"
    if transakcja.is_file():
        tekst = transakcja.read_text(encoding="utf-8", errors="replace")
        znalezione = re.findall(r"elapsed_seconds_total:\s*(\d+)", tekst)
        biezace = time_doc.get("elapsed_seconds_total")
        if znalezione and isinstance(biezace, int):
            doby = (biezace - int(znalezione[-1])) / 86400
            opis += f", czyli {doby:.2f} doby kampanii"
    return opis


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="kod 1 przy naruszeniu (tryb bramki)")
    args = parser.parse_args()

    problems, liczby = check()
    bank = load(STATE / "growth-banks.yaml")

    for nazwa, wartosc in liczby.items():
        print(f"{nazwa:<28} {wartosc}")
    print(f"{'rejestr as_of':<28} {bank.get('as_of_event_id')}")
    if (opis := zaleglosc()):
        print(f"{'ZALEGLOSC':<28} {opis}")
    print()

    if not problems:
        print("[OK] rejestr wzrostu: nadwyzka sie zgadza, zbiory wezlow zgodne, "
              "zaden aktywny zbiornik nie ubywa")
        return 0

    print(f"[BLAD] {sum(len(v) for v in problems.values())} naruszen w {len(problems)} kontrolach:")
    for nazwa, opisy in sorted(problems.items()):
        for opis in opisy:
            print(f"  - {nazwa}: {opis}")
    return 1 if args.check else 0


if __name__ == "__main__":
    sys.exit(main())

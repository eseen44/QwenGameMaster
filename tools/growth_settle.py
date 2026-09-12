"""Rozliczenie zaleglosci rejestru wzrostu - LICZY I RAPORTUJE, nie zapisuje.

POWOD ISTNIENIA. state/growth-banks.yaml jest rejestrem RECZNYM z decyzji: runtime nie
symuluje foragingu wezlow, a szczeble 2 i 3 drabiny narrator nalicza sam. Skutek jest
przewidywalny - rejestr zostaje w tyle za zegarem i nikt tego nie widzi, bo obie liczby
leza w dwoch roznych plikach. 2026-09-12 rejestr stal na turze 235 przy zegarze na 274.
Tura 178 poszla jeszcze dalej: przy braku jakiejkolwiek drogi do tego pliku wymyslila
stawki od nowa i podala graczowi cztery falszywe liczby jako pomiar (retcon_000114).

DLACZEGO NIE ZAPISUJE. Rozdzial nadwyzki ma czesci, ktorych ten skrypt NIE MODELUJE:
straty propagacji miedzy wezlami (companions/webber-network.yaml#network_cost_model),
dojrzewanie po przekroczeniu progu drabiny oraz decyzje o tym, ktory wezel ma dostac
konkretny nadmiar. Narzedzie, ktore zapisuje polowe modelu, jest gorsze od rejestru
recznego, bo wyglada na pomiar. Liczby ponizej sa MATERIALEM DO RETCONU, nie retconem.

KOLEJNOSC NAPELNIANIA (retcon_000141, potwierdzona przez gracza 2026-09-12):
Lucan, potem okazy ZAKOTWICZONE, potem reszta. Kolejnosc jest TWARDA, nie proporcjonalna:
nizszy szczebel dostaje dopiero to, czego wyzszy nie przyjmuje.

Uruchomienie:
    python tools/growth_settle.py            # rozliczenie od as_of do zegara
    python tools/growth_settle.py --days 1.0 # hipotetycznie, dla podanego okna
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

# Szczebel 1 liczy RUNTIME (pc-lucan#resources.regeneration), nie ten skrypt.
NIE_WEZLY = {"pc_lucan"}


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def okno_dob(bank: dict, czas: dict) -> tuple[float | None, str]:
    """Ile dob kampanii minelo od as_of rejestru do biezacego zegara."""
    as_of = bank.get("as_of_event_id")
    if not as_of:
        return None, "rejestr nie ma as_of_event_id"
    transakcja = CAMPAIGN / "journal" / "transactions" / f"{as_of.replace('event_', '')}.yaml"
    if not transakcja.is_file():
        return None, f"brak transakcji {transakcja.name} - nie da sie odczytac czasu as_of"
    znalezione = re.findall(
        r"elapsed_seconds_total:\s*(\d+)", transakcja.read_text(encoding="utf-8", errors="replace")
    )
    biezace = czas.get("elapsed_seconds_total")
    if not znalezione or not isinstance(biezace, int):
        return None, "nie da sie odczytac elapsed_seconds_total po obu stronach"
    return (biezace - int(znalezione[-1])) / 86400.0, as_of


def zakotwiczone() -> set[str]:
    """Okazy szczebla 2. Zrodlo: distribution_priority w rejestrze."""
    bank = load(STATE / "growth-banks.yaml")
    for wpis in (bank.get("distribution_priority") or {}).get("order") or []:
        if wpis.get("rank") == 2:
            return {
                fragment.strip()
                for fragment in re.split(r"[,\s]+", str(wpis.get("who", "")))
                if fragment.strip().startswith(("companion_", "spy_", "webber_"))
            }
    return set()


def settle(days: float) -> int:
    bank = load(STATE / "growth-banks.yaml")
    anchored = zakotwiczone()

    wlasne: list[tuple[str, float, float]] = []   # (id, przyrost, sufit_okna)
    pula = 0.0
    for entry in bank.get("banks") or []:
        if not isinstance(entry, dict) or entry.get("id") in NIE_WEZLY:
            continue
        rate = float(entry.get("rate_per_day", 0.0) or 0.0)
        cap = entry.get("growth_cap_per_day")
        cap = float(cap) if isinstance(cap, (int, float)) else None
        do_wlasnego = rate if cap is None else min(rate, cap)
        nadmiar = max(0.0, rate - do_wlasnego)
        wlasne.append((str(entry.get("id")), do_wlasnego * days, (cap or 0.0) * days))
        pula += nadmiar * days

    print(f"okno rozliczenia: {days:.3f} doby kampanii")
    print()
    print("WLASNY PRZYROST WEZLOW (stawka do sufitu, prosto do wlasnego banku)")
    for node_id, przyrost, _ in sorted(wlasne, key=lambda x: -x[1]):
        if przyrost > 0:
            znacznik = " [zakotwiczony]" if node_id in anchored else ""
            print(f"  {node_id:<26} +{przyrost:.2f}{znacznik}")
    suma = sum(p for _, p, _ in wlasne)
    print(f"  {'RAZEM':<26} +{suma:.2f}")
    print()
    print(f"NADMIAR PONAD SUFITY (do rozdzialu): {pula:.2f}")
    print("  kolejnosc napelniania: pc_lucan -> zakotwiczone -> reszta (retcon_000141)")
    print(f"  zakotwiczone: {', '.join(sorted(anchored)) or '(brak w rejestrze)'}")
    print()
    print("CZEGO TO NIE LICZY, wiec czego nie wolno stad przepisac do plikow:")
    print("  - strat propagacji miedzy wezlami (webber-network.yaml#network_cost_model)")
    print("  - przekroczen progow drabiny dojrzalosci (10 / 30 / 60) i ich skutkow")
    print("  - szczebla 1: rezerwe Lucana nalicza runtime, a przy sufcie 15/15 nadmiar")
    print("    wyparowuje i nie bankuje sie nigdzie (retcon_000151)")
    print("  - nadwyzki juz odlozonej przez silnik w runtime.overflow_pending")
    print()
    print("To jest MATERIAL DO RETCONU. Zapis nastepuje recznie, po decyzji.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=float, default=None,
                        help="okno w dobach; domyslnie liczone od as_of rejestru do zegara")
    args = parser.parse_args()

    if args.days is not None:
        return settle(args.days)

    days, opis = okno_dob(load(STATE / "growth-banks.yaml"), load(STATE / "time.yaml"))
    if days is None:
        print(f"[BLAD] {opis}")
        return 1
    print(f"rejestr as_of: {opis}")
    return settle(days)


if __name__ == "__main__":
    sys.exit(main())

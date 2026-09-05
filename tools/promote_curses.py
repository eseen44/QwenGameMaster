"""Podnosi trzy opanowane procedury z repertuaru teoretycznego do `known:` w abilities.yaml.

DECYZJA GRACZA 2026-09-05: pelne wpisy w `known:` z historia uzyc, mastery wedlug liczby
przebiegow (zapadnia 28, jezyk 27, usypianie 26), a procedura ZOSTAJE w repertuarze jako
zrodlo teorii, oznaczona jako przeniesiona. Zadne slowo nie ginie.

HISTORIA UZYC JEST SPRAWDZONA, NIE PRZEPISANA Z PAMIECI. Kazda tura zweryfikowana przez
obecnosc operacji `consume` we wpisie dziennika:
  - zapadnia pamieci: t_129 (pierwszy przebieg, 2 jednostki za dwa osobne kontakty, rzut
    z kara -10 za pierwszy w zyciu przebieg), t_208 (1), t_220 (1, przez dotyk, obok
    0,1 za trzeci stack numb). Tura 170 to WZMIANKA bez consume - nie wchodzi.
  - rozwiazanie jezyka: t_096 (pierwszy przebieg), t_127 (drugi, zmierzony skutek uboczny),
    t_218 (2 jednostki - PODWOJNIE, bo bez opakowania towarzyskiego). Tura 219 to wzmianka.
  - usypianie: t_097 (pierwszy przebieg, przez podarunek, 3 jednostki).

Uruchomienie:  python tools/promote_curses.py [--dry-run]   (kopia robocza w scratchpadzie)
"""

from __future__ import annotations

import argparse
import collections
import re
import sys
from pathlib import Path

import yaml

ROOT = Path("C:/Projects/QwenGameMaster")
CARD = ROOT / "campaigns" / "lucan" / "player" / "abilities.yaml"

WPISY = """  - id: ability_curse_memory_trap
    capability_ref: null
    name: Zapadnia pamięci
    mastery: 28
    procedure_ref: theoretical_repertoire#curse_memory_trap
    source_item: item_courtesies_curse_book
    tier: 2
    curse_class: mental
    casting_profile: {measured_cost_units: 1, subtle: true, delayed_effect_possible: true}
    uses: [target_cannot_describe_lucan_an_hour_later, leaves_the_conversation_and_conclusions_intact]
    limits: [does_not_remove_the_conversation_itself, does_not_remove_the_targets_conclusions, one_procedure_per_contact, no_rat_version_for_practice]
    usage_log:
      - {event_id: event_turn_interlude_129, role: first_successful_run, target: npc_academy_porter, delivery: pozegnanie_klasa_opozniona, units: 2, note: 'Dwa osobne kontakty w jednej turze, rzut z kara minus 10 za pierwszy w zyciu przebieg - naturalna 54, wynik 44 przy progu 20.'}
      - {event_id: event_turn_interlude_208, units: 1, note: 'KOSZT NALICZONY TERAZ, BO TERAZ ZOSTAL RZUCONY (audyt tury).'}
      - {event_id: event_turn_interlude_220, units: 1, delivery: dotyk, note: 'Obok 0,1 za trzeci stack numb - lacznie 1,1 w tej turze.'}
    note: 'Najcenniejsza procedura w jego sytuacji: wspomnienie twarzy sie nie konsoliduje, wiec godzine pozniej cel nie potrafi Lucana opisac. NIE zabiera samej rozmowy ani wnioskow celu, tylko rysopis.'
  - id: ability_curse_loosened_tongue
    capability_ref: null
    name: Rozwiązanie języka
    mastery: 27
    procedure_ref: theoretical_repertoire#curse_loosened_tongue
    source_item: item_courtesies_curse_book
    tier: 2
    curse_class: mental
    casting_profile: {measured_cost_units: 1, cost_doubles_without_social_wrapper: 2, subtle: true}
    uses: [lowered_inhibition, target_remembers_a_pleasant_conversation_not_an_interrogation]
    limits: [does_not_withhold_what_the_target_would_normally_keep_back, confabulates_when_the_target_has_no_answer, one_procedure_per_contact, no_rat_version_for_practice]
    usage_log:
      - {event_id: event_turn_interlude_096, role: first_successful_run, target: npc_halven_rusk, delivery: powitanie, units: 1}
      - {event_id: event_turn_interlude_127, units: 1, note: 'Zmierzony skutek uboczny: rozwiazany jezyk nie zataja TAKZE tego, co cel normalnie zatrzymalby dla siebie, a przy braku odpowiedzi konfabuluje.'}
      - {event_id: event_turn_interlude_218, units: 2, note: 'KOSZT: 2 JEDNOSTKI - PODWOJNIE, BO BEZ OPAKOWANIA (audyt tury). Rozdzial towarzyski obniza koszt o okolo jeden poziom; dostarczenie bez niego place sie podwojnie.'}
    note: 'Obnizenie hamowania. Badany pamieta mila rozmowe, nie przesluchanie.'
  - id: ability_curse_induced_sleep
    capability_ref: null
    name: Usypianie
    mastery: 26
    procedure_ref: theoretical_repertoire#curse_induced_sleep
    source_item: item_courtesies_curse_book
    tier: 1-2
    curse_class: mental
    casting_profile: {measured_cost_units: 3, works_without_casters_presence: true}
    uses: [rising_sleep_pressure_turning_into_real_sleep, target_blames_the_wine]
    limits: [most_expensive_procedure_in_the_set, one_procedure_per_contact, no_rat_version_for_practice]
    usage_log:
      - {event_id: event_turn_interlude_097, role: first_successful_run, target: npc_halven_rusk, delivery: podarunek_przez_pioro, units: 3, note: 'Pierwsza procedura dzialajaca BEZ OBECNOSCI Lucana - przebieg poszedl rozdzialem PODARUNEK.'}
    note: 'Narastajace cisnienie senne przechodzace w sen prawdziwy; cel obwinia wino.'
"""

NOTA_PROMOCJI = (
    " PRZENIESIONA 2026-09-05 do `known:` jako {aid} (decyzja gracza) - ta pozycja zostaje "
    "jako ZRODLO TEORII i zapis pierwszego przebiegu; mechanika, koszt i historia uzyc "
    "sa tam."
)

PROMOWANE = {
    "curse_memory_trap": "ability_curse_memory_trap",
    "curse_loosened_tongue": "ability_curse_loosened_tongue",
    "curse_induced_sleep": "ability_curse_induced_sleep",
}


def words(node) -> collections.Counter:
    if isinstance(node, str):
        return collections.Counter(re.findall(r"\w+", node))
    if isinstance(node, dict):
        t = collections.Counter()
        for k, v in node.items():
            t += words(k) + words(v)
        return t
    if isinstance(node, list):
        t = collections.Counter()
        for v in node:
            t += words(v)
        return t
    return collections.Counter()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    text = CARD.read_text(encoding="utf-8-sig")
    before = yaml.safe_load(text)

    # 1. Wstaw trzy wpisy na koncu bloku `known:`, tuz przed nastepnym kluczem najwyzszego poziomu.
    m = re.search(r"(?m)^cover_account_given_to_others:", text)
    assert m, "nie znalazlem konca bloku known:"
    text = text[: m.start()] + WPISY + text[m.start():]

    # 2. Oznacz procedury w repertuarze jako przeniesione - bez usuwania czegokolwiek.
    for pid, aid in PROMOWANE.items():
        wzor = re.compile(r"(\{id: " + pid + r",.*?note: ')(.*?)('\})", re.S)
        found = wzor.search(text)
        assert found, f"nie znalazlem procedury {pid} z polem note"
        text = wzor.sub(lambda x: x.group(1) + x.group(2) + NOTA_PROMOCJI.format(aid=aid) + x.group(3),
                        text, count=1)

    # 3. Znaczniki swiezosci.
    text = re.sub(r"(?m)^status: needs_review$",
                  "status: reviewed_2026_09_05\nreview_note: >-\n"
                  "  Przejrzane z graczem 2026-09-05. Trzy opanowane procedury z ksiazki 'Uprzejmosci'\n"
                  "  podniesione do `known:` z historia uzyc sprawdzona w dzienniku po operacjach consume.\n"
                  "  Osiem procedur nadal czeka na pierwszy przebieg i zostaje w theoretical_repertoire.",
                  text, count=1)
    text = re.sub(r"(?m)^last_updated_event_id: event_turn_interlude_092$",
                  "last_updated_event_id: event_turn_interlude_235", text, count=1)

    after = yaml.safe_load(text)
    brak = words(before) - words(after)
    for w in ("needs_review", "needs", "review", "event_turn_interlude_092"):
        brak.pop(w, None)
    assert not brak, f"migracja gubi tresc: {dict(list(brak.items())[:8])}"

    nowe = {a["id"] for a in after["known"]} - {a["id"] for a in before["known"]}
    assert len(nowe) == 3, f"spodziewalem sie trzech nowych zdolnosci, jest {len(nowe)}: {nowe}"
    assert len(after["theoretical_repertoire"]["procedures"]) == 11, "procedura zniknela z repertuaru"

    print(f"known: {len(before['known'])} -> {len(after['known'])} zdolnosci")
    for a in after["known"]:
        if a["id"] in nowe:
            print(f"   + {a['id']:<32} mastery {a['mastery']}, "
                  f"{len(a['usage_log'])} wpisow historii")
    print("repertuar: 11 procedur bez zmian, trzy oznaczone jako przeniesione")
    print("kontrola slow: zadne slowo nie ginie")

    if args.dry_run:
        print("\n--dry-run: nic nie zapisano")
        return 0
    CARD.write_text(text, encoding="utf-8", newline="\n")
    print(f"\nzapisane: {CARD.relative_to(ROOT).as_posix()} ({CARD.stat().st_size} B)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

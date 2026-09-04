"""Testy twardych bramek etapu 4 - kazda sprawdzana ZAPALONA i ZGASZONA.

Bramki zamieniaja reguly-zdania na warunki. Audyt pokazal, ze regula w prozie nie dziala:
glowny tryb awarii powtorzyl sie 21 razy PO wpisaniu go do narrator.md, a szesc tur
cofnietych przez gracza przeszlo istniejacy walidator z 7-16 poprawnie rozwiazujacymi sie
refami. Warunek dziala tylko wtedy, gdy widziano go odrzucajacego - stad kazdy test ma pare.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

import gm_runtime

CAMPAIGN = TOOLS.parent / "campaigns" / "lucan"


class TurnIdentityTest(unittest.TestCase):
    def sprawdz(self, request: dict) -> None:
        gm_runtime.validate_turn_identity({"request": request})

    def test_actor_id_wystarcza(self):
        self.sprawdz({"actor_id": "pc_lucan"})

    def test_subject_id_tez_wystarcza(self):
        self.sprawdz({"subject_id": "pc_lucan"})

    def test_brak_sprawcy_odrzucony(self):
        with self.assertRaises(gm_runtime.RuntimeError) as caught:
            self.sprawdz({"scope": "execution"})
        self.assertIn("actor_id", str(caught.exception))

    def test_pelna_trojka_testu_przechodzi(self):
        self.sprawdz({"actor_id": "pc_lucan", "capability_id": "c",
                      "target_id": "t", "intent_id": "i"})

    def test_niepelna_trojka_odrzucona(self):
        with self.assertRaises(gm_runtime.RuntimeError) as caught:
            self.sprawdz({"actor_id": "pc_lucan", "capability_id": "c", "target_id": "t"})
        self.assertIn("intent_id", str(caught.exception))


class SourceRefsTest(unittest.TestCase):
    def sprawdz(self, refs: list[str]) -> None:
        gm_runtime.validate_source_refs_resolve(CAMPAIGN, {"consequence_source_refs": refs})

    def test_istniejacy_retcon(self):
        self.sprawdz(["retcon_000015"])

    def test_istniejacy_plik_z_kotwica(self):
        self.sprawdz(["worlds/solmara/lore/necromancy-law.yaml#legal_baseline"])

    def test_deklaracja_gracza_przechodzi_bez_pliku(self):
        self.sprawdz(["player_declaration:2026-09-04"])

    def test_jednoznaczny_prefiks_zdarzenia_przechodzi(self):
        """Repo uzywa dwoch konwencji id naraz, wiec ref pisany z pamieci mija sie o sufiks."""
        self.sprawdz(["event_turn_interlude_051"])

    def test_wymyslony_retcon_odrzucony(self):
        with self.assertRaises(gm_runtime.RuntimeError) as caught:
            self.sprawdz(["retcon_999999"])
        self.assertIn("retcon_999999", str(caught.exception))

    def test_wymyslone_zdarzenie_odrzucone(self):
        with self.assertRaises(gm_runtime.RuntimeError):
            self.sprawdz(["event_turn_interlude_999"])

    def test_wymyslony_plik_odrzucony(self):
        with self.assertRaises(gm_runtime.RuntimeError):
            self.sprawdz(["campaigns/lucan/state/nie-ma-takiego-pliku.yaml#sekcja"])

    def test_pusta_lista_nie_blokuje(self):
        self.sprawdz([])

    def test_wszystkie_tury_historyczne_przechodza(self):
        """Bramka nie moze uniewazniac 233 tur, ktore juz sa w repo."""
        import yaml
        odrzucone = []
        for path in sorted((CAMPAIGN / "journal" / "transactions").glob("turn_*.yaml")):
            document = yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}
            outcome = document.get("outcome")
            if not outcome:
                continue
            try:
                gm_runtime.validate_source_refs_resolve(CAMPAIGN, outcome)
            except gm_runtime.RuntimeError as exc:
                odrzucone.append(f"{path.name}: {exc}")
        self.assertEqual(odrzucone, [], "bramka odrzuca istniejace tury: " + "; ".join(odrzucone[:3]))


if __name__ == "__main__":
    unittest.main()

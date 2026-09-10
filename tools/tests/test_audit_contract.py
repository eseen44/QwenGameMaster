"""Testy kontraktu audytu: przechyl 7,3x na rzecz protokolu jest bramka, nie uwaga.

ZMIERZONY ROZBIOR 20 OSTATNICH TUR (audyt 115 819 zn., proza 15 972 zn., czyli 7,3x):

  sekcja `STAN`                   7 596 zn., w 19 z 20 tur
  sekcja `CZEGO NARRATOR NIE...`  9 406 zn., w 18 z 20 tur
  ------------------------------------------------------------
  razem                          25 454 zn. = 21% audytu, CZYSTA REDUNDANCJA

`STAN` powtarza `state/instances/*.yaml`, `state/time.yaml` i `scene.yaml`, ktore brief
i tak wypisuje - a AGENTS.md juz mowi, ze godzine czyta sie Z PLIKU, nie z wlasnej
deklaracji. `CZEGO NARRATOR NIE ZROBIL` powtarza to, co sprawdza jedenascie bramek
preflight plus kontrole w `turn commit`. Do tego `consequence_source_refs` i `operations`
sa osobnymi, walidowanymi polami outcome.

Mediana audytu 5 749 zn. przy medianie prozy 1 002 zn. Progi: 3x prozy, sufit 4 000 zn.,
2 000 zn. bez prozy autorskiej. Historycznych audytow NIE WOLNO przepisywac - dziennik jest
append-only - wiec bramka dziala wylacznie powyzej baseline.
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))

import gm_runtime    # noqa: E402
import prose_check   # noqa: E402

EVENTS = ROOT / "campaigns" / "lucan" / "journal" / "events.jsonl"
AGENTS = ROOT / "AGENTS.md"
TEMPLATE = ROOT / "templates" / "journal" / "turn-outcome.yaml"

# Audyt pod progiem: decyzje i zrodla, bez zrzutu stanu i bez samo-raportu.
DOBRY_AUDYT = (
    "1. DECYZJA. Kesz przyjal nazwisko i nie zazadal honorarium - jego zakres "
    "reprezentacji obejmuje dwa pomieszczenia (rovan-kesz#standing).\n"
    "2. WIEDZA. Do jego knowledge weszlo nazwisko Halvek jako uslyszane od Lucana.\n"
    "3. NIEUSTALONE: termin papierow, nazwisko urzednika akt."
)
DOBRA_PROZA = (
    "Kesz odlozyl pioro i nie podniosl glowy.\n"
    "— Nazwisko urzednika. Bez niego nie mam tego gdzie zaniesc."
)


class MeasurementTest(unittest.TestCase):
    def test_dobry_audyt_przechodzi(self):
        pomiar = prose_check.zmierz_audyt(DOBRY_AUDYT, DOBRA_PROZA)
        self.assertEqual(pomiar["naruszenia"], [], pomiar["naruszenia"])
        self.assertLessEqual(pomiar["stosunek"], prose_check.LIMIT_STOSUNKU)

    def test_zrzut_stanu_jest_lapany_jako_naglowek(self):
        pomiar = prose_check.zmierz_audyt(
            DOBRY_AUDYT + "\n4. STAN. Czwarty dzien interludium, Varkhen 9,2/65.", DOBRA_PROZA)
        self.assertIn("sekcja STAN", pomiar["etykiety"])

    def test_samo_raport_jest_lapany_jako_naglowek(self):
        pomiar = prose_check.zmierz_audyt(
            DOBRY_AUDYT + "\n5. CZEGO NARRATOR TU NIE ZROBIL. Nie stworzyl zegara.", DOBRA_PROZA)
        self.assertIn("sekcja CZEGO NARRATOR NIE ZROBIL", pomiar["etykiety"])

    def test_zdanie_o_postaci_nie_jest_samo_raportem(self):
        """Wzorce sa naglowkowe - 'Kesz nie podal nazwiska' to fakt sceny, nie samo-raport."""
        pomiar = prose_check.zmierz_audyt(
            "1. DECYZJA. Kesz nie podal nazwiska i narrator nie ma go z czego wziac. "
            "Czego nie dostal: dostepu do akt.", DOBRA_PROZA)
        self.assertEqual(pomiar["etykiety"], [], pomiar["etykiety"])

    def test_sufit_absolutny_dziala(self):
        pomiar = prose_check.zmierz_audyt("x" * (prose_check.LIMIT_AUDYTU + 1), "y" * 5000)
        self.assertTrue(any("zn. >" in e for e in pomiar["etykiety"]), pomiar["etykiety"])

    def test_stosunek_dziala(self):
        pomiar = prose_check.zmierz_audyt("x" * 3000, "y" * 500)
        self.assertAlmostEqual(pomiar["stosunek"], 6.0)
        self.assertTrue(any("x prozy" in e for e in pomiar["etykiety"]))

    def test_brak_prozy_nie_jest_furtka(self):
        """Inaczej audyt rosnie, a proza znika - i stosunek przestaje istniec."""
        pomiar = prose_check.zmierz_audyt("x" * (prose_check.LIMIT_AUDYTU_BEZ_PROZY + 1), "")
        self.assertIsNone(pomiar["stosunek"])
        self.assertTrue(any("bez prozy" in e for e in pomiar["etykiety"]))

    def test_krotki_audyt_bez_prozy_przechodzi(self):
        """Tura administracyjna albo odzyskana nie musi miec prozy autorskiej."""
        self.assertEqual(prose_check.zmierz_audyt("x" * 500, "")["naruszenia"], [])

    def test_progi_sa_ostrzejsze_od_dzisiejszej_mediany(self):
        """Prog, ktory przepuszcza dzisiejsza mediane, nie zmienia niczego."""
        self.assertLess(prose_check.LIMIT_AUDYTU, 5749)
        self.assertLess(prose_check.LIMIT_STOSUNKU, 7.3)


class CommitGateTest(unittest.TestCase):
    def test_commit_odmawia_przechylonego_audytu(self):
        # gm_runtime ma WLASNA klase RuntimeError(ValueError), nie wbudowana.
        with self.assertRaises(gm_runtime.RuntimeError) as ctx:
            gm_runtime.validate_audit_contract(
                {"summary": "x" * 6000, "prose": DOBRA_PROZA})
        self.assertIn("AGENTS.md#audyt-nie-jest-samo-raportem", str(ctx.exception))

    def test_commit_odmawia_zrzutu_stanu(self):
        with self.assertRaises(gm_runtime.RuntimeError) as ctx:
            gm_runtime.validate_audit_contract(
                {"summary": DOBRY_AUDYT + "\n4. STAN. Lucan 19/19.", "prose": DOBRA_PROZA})
        self.assertIn("STAN", str(ctx.exception))

    def test_commit_przechodzi_dla_audytu_pod_progiem(self):
        gm_runtime.validate_audit_contract({"summary": DOBRY_AUDYT, "prose": DOBRA_PROZA})

    def test_commit_wola_kontrakt_audytu(self):
        zrodlo = (TOOLS / "gm_runtime.py").read_text(encoding="utf-8")
        self.assertIn("validate_audit_contract(outcome)", zrodlo,
                      "bramka istnieje, ale commit jej nie wola")


class HistoryTest(unittest.TestCase):
    def test_historyczne_audyty_nie_zostaly_przepisane(self):
        """Dziennik jest append-only. Bramka dziala progiem, nie edycja historii."""
        ev = [json.loads(l) for l in EVENTS.read_text(encoding="utf-8-sig").splitlines()
              if l.strip()]
        stare = [e for e in ev if prose_check.numer_tury(e.get("id")) <= prose_check.BASELINE_TURN
                 and len(e.get("audit") or "") > prose_check.LIMIT_AUDYTU]
        self.assertTrue(stare, "historyczne audyty zniknely albo zostaly skrocone")
        for e in stare:
            self.assertEqual(e["audit"], e["summary"],
                             f"{e['id']}: audit przestal byc kopia summary")

    def test_baseline_chroni_historie_przed_bramka(self):
        ev = [json.loads(l) for l in EVENTS.read_text(encoding="utf-8-sig").splitlines()
              if l.strip()]
        self.assertEqual(prose_check.BASELINE_TURN, 248, "nie przesuwaj granicy starego dlugu")
        nowe = [e for e in ev if prose_check.numer_tury(e.get("id")) > prose_check.BASELINE_TURN]
        for event in nowe:
            with self.subTest(event=event.get("id")):
                result = prose_check.zmierz_audyt(event.get("audit") or event.get("summary"),
                                                 event.get("prose"))
                self.assertEqual(result["naruszenia"], [])


class DocsTest(unittest.TestCase):
    def test_agents_podaje_progi_i_pomiar(self):
        tekst = AGENTS.read_text(encoding="utf-8")
        # Naglowek w AGENTS.md; slug tej samej sekcji jest w bledzie commita.
        self.assertIn("## Audyt nie jest samo-raportem", tekst)
        for fragment in ("3x proza", "4 000 znakow", "21% audytu", "7,3x"):
            self.assertIn(fragment, tekst, f"AGENTS.md nie podaje: {fragment}")

    def test_szablon_mowi_to_w_miejscu_pisania(self):
        tekst = TEMPLATE.read_text(encoding="utf-8")
        for fragment in ("STAN", "CZEGO NARRATOR", "3x"):
            self.assertIn(fragment, tekst, f"szablon nie ostrzega o: {fragment}")

    def test_licznik_przechylu_jest_drukowany(self):
        zrodlo = (TOOLS / "prose_check.py").read_text(encoding="utf-8")
        self.assertIn("przechyl proza/protokol", zrodlo)


if __name__ == "__main__":
    unittest.main()

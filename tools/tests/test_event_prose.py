"""Testy etapu 11: proza oddzielona od protokolu audytowego.

`summary` pelnil dwie wykluczajace sie funkcje - jedyny zapis narracji i protokol tury -
i protokol wygral: udzial tresci audytowej 0,6% -> 51,3%, srednia dlugosc 1 048 -> 6 432
znakow, otwarcie sesji 33 235 znakow z czterech wpisow. Repo zdiagnozowalo skutki dwa razy
(retcon_000040: wszystkie NPC brzmia jednakowo, bo narrator odtwarza je z rejestru
ksiegowego; retcon_000136: uzasadnienie narratora recytowane jako kwestia postaci) i oba
razy naprawilo to REGULA, nie zmiana schematu.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))

import gm_runtime
import journal_guard
import split_event_summary as splitter

EVENTS = ROOT / "campaigns" / "lucan" / "journal" / "events.jsonl"
CAMPAIGN = ROOT / "campaigns" / "lucan"


def wpisy() -> list[dict]:
    return [json.loads(line) for line in EVENTS.read_text(encoding="utf-8").splitlines() if line.strip()]


class ExtractorTest(unittest.TestCase):
    def test_bierze_glowe_i_STAN_pomijajac_protokol(self):
        summary = ("Bez testu. Siedem minut. TEZA TURY.\n"
                   "1. PIERWSZA SEKCJA PROTOKOLU z cytatem pliku x.yaml#klucz.\n"
                   "2. DRUGA SEKCJA, dluga i ksiegowa.\n"
                   "3. STAN. Gabinet, 18:01, obecni Lucan i Seraphine.\n")
        prose = splitter.extract(summary, 1100)
        self.assertIn("TEZA TURY", prose)
        self.assertIn("Gabinet, 18:01", prose)
        self.assertNotIn("PIERWSZA SEKCJA", prose)
        self.assertNotIn("x.yaml#klucz", prose)

    def test_bez_numerowanych_sekcji_bierze_calosc(self):
        prose = splitter.extract("Krotka narracja bez protokolu.", 1100)
        self.assertEqual(prose, "Krotka narracja bez protokolu.")

    def test_szanuje_limit(self):
        summary = "A" * 5000 + "\n1. sekcja\n2. STAN. " + "B" * 5000
        prose = splitter.extract(summary, 400)
        self.assertLessEqual(len(prose), 400)

    def test_zawsze_zostawia_czesc_glowy_i_czesc_stanu(self):
        summary = "TEZA " * 200 + "\n1. protokol\n2. STAN. " + "STAN " * 200
        prose = splitter.extract(summary, 600)
        self.assertIn("TEZA", prose)
        self.assertIn("STAN", prose)


class MigrationInvariantTest(unittest.TestCase):
    def setUp(self) -> None:
        self.events = wpisy()

    def test_kazdy_wpis_ma_audit_rowny_summary(self):
        """audit jest KOPIA, nie zamiennikiem - to jest gwarancja, ze nic nie zginelo."""
        zle = [e["id"] for e in self.events
               if isinstance(e.get("summary"), str) and e["summary"].strip()
               and e.get("audit") != e["summary"]]
        self.assertEqual(zle, [], f"audit rozjechany z summary: {zle[:5]}")

    def test_kazdy_wpis_ma_niepusta_proze(self):
        puste = [e["id"] for e in self.events
                 if isinstance(e.get("summary"), str) and e["summary"].strip()
                 and not (e.get("prose") or e.get("prose_auto") or "").strip()]
        self.assertEqual(puste, [], f"wpisy bez prozy: {puste[:5]}")

    def test_proza_jest_istotnie_krotsza_od_protokolu(self):
        prose = sum(len(e.get("prose") or e.get("prose_auto") or "") for e in self.events)
        audit = sum(len(e.get("audit") or "") for e in self.events)
        self.assertLess(prose * 3, audit, "proza nie jest istotnie tansza od protokolu")

    def test_zapora_lapie_podmieniony_audit(self):
        """audit wyszedl spod porownania tresci, wiec musi miec wlasny niezmiennik."""
        self.assertIn("audit", journal_guard.BOOKKEEPING_KEYS)
        source = (TOOLS / "journal_guard.py").read_text(encoding="utf-8")
        self.assertIn("POLE POCHODNE ROZJECHANE", source,
                      "brak kontroli, ze audit jest kopia summary - to byla by furtka")


class RecentTest(unittest.TestCase):
    def test_recent_zwraca_proze_i_liczy_pominiety_protokol(self):
        result = gm_runtime.recent_prose(CAMPAIGN, 4)
        self.assertEqual(len(result["turns"]), 4)
        self.assertGreater(result["audit_chars_skipped"], 5 * result["chars"],
                           "recent nie oszczedza - po co wtedy istnieje")
        for row in result["turns"]:
            self.assertTrue(row["prose"].strip())

    def test_recent_pokazuje_uchylenie(self):
        result = gm_runtime.recent_prose(CAMPAIGN, 40)
        uchylone = [row for row in result["turns"] if row.get("superseded_by")]
        self.assertTrue(uchylone, "recent nie pokazuje uchylonych tur - to jest pulapka")
        for row in uchylone:
            self.assertIn(row.get("supersession_scope"), {"aspect", "whole", "mixed", None})

    def test_recent_mowi_gdzie_jest_pelny_slad(self):
        result = gm_runtime.recent_prose(CAMPAIGN, 2)
        self.assertIn("audit", result["note"])
        self.assertIn("transactions", result["note"])


class CommitProseTest(unittest.TestCase):
    def transaction(self, prose: str | None) -> dict:
        outcome = {
            "intent_achieved": True, "arrangement": "improved", "perspective": "pc_lucan",
            "summary": "Dlugi protokol tury z cytatami plikow i lista czego narrator nie zrobil.",
            "operations": [], "consequence_source_refs": [],
        }
        if prose is not None:
            outcome["prose"] = prose
        return {
            "event_id": "event_turn_test_900", "scene_id": "scene_test", "roll_id": None,
            "request": {"actor_id": "pc_lucan"},
            "time_operation": {"op": "advance_time", "seconds": 60},
            "outcome": outcome,
        }

    def test_proza_pisana_trafia_do_wpisu(self):
        event = gm_runtime.event_from_transaction(self.transaction("Lucan wychodzi w noc."))
        self.assertEqual(event["prose"], "Lucan wychodzi w noc.")
        self.assertEqual(event["prose_source"], "authored")
        self.assertIn("Dlugi protokol", event["audit"])

    def test_bez_prozy_wpis_zostaje_do_wyciagu(self):
        event = gm_runtime.event_from_transaction(self.transaction(None))
        self.assertIsNone(event["prose"])
        self.assertEqual(event["prose_source"], "auto_extracted")

    def test_audit_zawsze_trzyma_pelny_protokol(self):
        for prose in (None, "krotka proza"):
            event = gm_runtime.event_from_transaction(self.transaction(prose))
            self.assertEqual(event["audit"], event["summary"])


if __name__ == "__main__":
    unittest.main()

"""Testy etapow 2-4: recall dosiega kanonu, slad uzasadnienia przezywa commit, czas sie nie dubluje.

Wszystkie trzy naprawy dotycza tej samej rodziny awarii: narzedzie zwracalo wynik budzacy
zaufanie, bedac niezdolnym pokazac tego, co deklaruje.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

import gm_runtime


class RecallTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        journal = self.root / "journal"
        journal.mkdir(parents=True)
        # 40 tur, fraza w kazdej - stara wersja zwrocilaby wylacznie pierwsze `limit`.
        (journal / "events.jsonl").write_text(
            "\n".join(json.dumps({"id": f"event_turn_{i:03}", "summary": f"tura {i} o Seraphine"},
                                 ensure_ascii=False) for i in range(1, 41)) + "\n",
            encoding="utf-8",
        )
        (journal / "retcons.jsonl").write_text(
            "\n".join(json.dumps({"id": f"retcon_{i:06}", "replacement": f"korekta {i} o Seraphine"},
                                 ensure_ascii=False) for i in range(1, 6)) + "\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_retcony_sa_osiagalne(self):
        result = gm_runtime.recall(self.root, "Seraphine", 6)
        kinds = {m["kind"] for m in result["matches"]}
        self.assertIn("retcon", kinds, "retcony - kanon nr 1 - nadal nieosiagalne")

    def test_dziennik_nie_jest_wypchniety_przez_retcony(self):
        result = gm_runtime.recall(self.root, "Seraphine", 6)
        kinds = [m["kind"] for m in result["matches"]]
        self.assertIn("event", kinds, "retcony wypchnely dziennik - awaria od drugiej strony")

    def test_zwraca_najnowsze_tury_a_nie_najstarsze(self):
        result = gm_runtime.recall(self.root, "Seraphine", 6)
        events = [m for m in result["matches"] if m["kind"] == "event"]
        numbers = [int(m["ref"].split("line:")[1]) for m in events]
        self.assertEqual(numbers, sorted(numbers, reverse=True))
        self.assertGreater(max(numbers), 30, "biezaca czesc kampanii nadal nieosiagalna")

    def test_raportuje_ile_trafien_pominieto(self):
        result = gm_runtime.recall(self.root, "Seraphine", 3)
        self.assertTrue(result["truncated"])
        self.assertEqual(result["total_matches"], 45)
        self.assertEqual(len(result["matches"]), 3)

    def test_fragment_zawiera_szukana_fraze(self):
        result = gm_runtime.recall(self.root, "Seraphine", 8)
        for match in result["matches"]:
            self.assertIn("seraphine", match["text"].casefold(),
                          f"fragment bez szukanej frazy: {match['ref']}")


class AuditTrailTest(unittest.TestCase):
    def transaction(self, operations=None, refs=None) -> dict:
        return {
            "event_id": "event_turn_test_001",
            "scene_id": "scene_test",
            "roll_id": None,
            "request": {"actor_id": "pc_lucan"},
            "time_operation": {"op": "advance_time", "seconds": 420},
            "outcome": {
                "intent_achieved": True,
                "arrangement": "improved",
                "perspective": "pc_lucan",
                "summary": "cos sie stalo",
                "operations": operations or [],
                "consequence_source_refs": refs if refs is not None else ["retcon_000015"],
            },
        }

    def test_slad_uzasadnienia_trafia_do_dziennika(self):
        event = gm_runtime.event_from_transaction(self.transaction(refs=["retcon_000015", "plik.yaml#sekcja"]))
        self.assertEqual(event["consequence_source_refs"], ["retcon_000015", "plik.yaml#sekcja"])

    def test_pusty_slad_zostaje_pusta_lista_nie_znika(self):
        event = gm_runtime.event_from_transaction(self.transaction(refs=[]))
        self.assertEqual(event["consequence_source_refs"], [])
        self.assertIn("consequence_source_refs", event)

    def test_reczny_advance_time_przerywa_ture(self):
        outcome = self.transaction(operations=[{"op": "advance_time", "seconds": 900}])["outcome"]
        with self.assertRaises(gm_runtime.RuntimeError) as caught:
            gm_runtime.validate_outcome(outcome)
        self.assertIn("PODWAJA", str(caught.exception))

    def test_zwykle_operacje_przechodza(self):
        outcome = self.transaction(operations=[{"op": "consume", "instance_id": "pc_lucan"}])["outcome"]
        gm_runtime.validate_outcome(outcome)


if __name__ == "__main__":
    unittest.main()

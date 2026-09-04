"""Testy operacji change_relationship.

Do 2026-09-04 handler czytal wylacznie subject_id/target_id. Tura 083 zapisala
npc_id: npc_hesk_dorn i nazwisko zostalo CICHO odrzucone - w state/reputations.yaml
wyladowal rekord "nikt wobec nikogo" ze score 25 i reason null. Operacja byla uzyta raz
na 237 transakcji, wiec bledu nie mial kto zauwazyc.

Te testy pilnuja dwoch rzeczy: skrot npc_id dziala, a brak tozsamosci PRZERYWA ture
zamiast zapisywac pusty rekord.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import yaml

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

import gm_runtime


class ChangeRelationshipTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "state").mkdir(parents=True)
        (self.root / "state" / "reputations.yaml").write_text(
            yaml.safe_dump({"schema_version": 1, "attitudes": []}, allow_unicode=True),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def apply(self, operation: dict) -> dict:
        changed: dict[Path, dict] = {}
        gm_runtime.apply_operation(self.root, changed, operation, "event_test_001")
        path = (self.root / "state" / "reputations.yaml").resolve()
        return changed[path]

    def test_skrot_npc_id_zapisuje_tozsamosc(self):
        document = self.apply({"op": "change_relationship", "npc_id": "npc_hesk_dorn",
                               "delta": 25, "reason": "zakup skrzyni"})
        attitude = document["attitudes"][0]
        self.assertEqual(attitude["subject_id"], "npc_hesk_dorn")
        self.assertEqual(attitude["target_id"], "pc_lucan")
        self.assertEqual(attitude["score"], 25)
        self.assertEqual(attitude["history"][0]["reason"], "zakup skrzyni")

    def test_jawne_subject_i_target_dzialaja_dalej(self):
        document = self.apply({"op": "change_relationship", "subject_id": "npc_a",
                               "target_id": "npc_b", "delta": -10})
        attitude = document["attitudes"][0]
        self.assertEqual((attitude["subject_id"], attitude["target_id"]), ("npc_a", "npc_b"))
        self.assertEqual(attitude["score"], -10)

    def test_brak_tozsamosci_przerywa_ture(self):
        # gm_runtime definiuje WLASNA klase RuntimeError, przeslaniajaca wbudowana.
        with self.assertRaises(gm_runtime.RuntimeError) as caught:
            self.apply({"op": "change_relationship", "delta": 25})
        self.assertIn("change_relationship", str(caught.exception))

    def test_kolejne_zmiany_trafiaja_w_ten_sam_rekord(self):
        changed: dict[Path, dict] = {}
        for delta in (25, -5):
            gm_runtime.apply_operation(
                self.root, changed,
                {"op": "change_relationship", "npc_id": "npc_hesk_dorn", "delta": delta},
                "event_test_002",
            )
        document = changed[(self.root / "state" / "reputations.yaml").resolve()]
        self.assertEqual(len(document["attitudes"]), 1)
        self.assertEqual(document["attitudes"][0]["score"], 20)
        self.assertEqual(len(document["attitudes"][0]["history"]), 2)

    def test_score_nie_wychodzi_poza_zakres(self):
        changed: dict[Path, dict] = {}
        for _ in range(6):
            gm_runtime.apply_operation(
                self.root, changed,
                {"op": "change_relationship", "npc_id": "npc_x", "delta": 30},
                "event_test_003",
            )
        document = changed[(self.root / "state" / "reputations.yaml").resolve()]
        self.assertEqual(document["attitudes"][0]["score"], 100)


if __name__ == "__main__":
    unittest.main()

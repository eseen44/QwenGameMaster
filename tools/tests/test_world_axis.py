"""Testy osi swiata: rzut przechyla swiat, nie rozstrzyga sukcesu (decyzja gracza 2026-09-09).

CO TA ZMIANA ODWRACA. Do Aktu 3 rzut byl bramka `modified >= difficulty` i to jedno
`passes_threshold` bylo jedyna rzecza, ktora rzut mowil. Od Aktu 3:
  - `intent_achieved` rozstrzyga fikcja, metoda i mozliwosci - jak w interludium,
  - rzut rozstrzyga, W KTORA STRONE przechylil sie swiat: wysoki margines zaciska porzadek,
    niski rozpuszcza go w entropii,
  - te dwie rzeczy sa NIEZALEZNE, wiec akcja moze sie udac i przy tym rozprzac swiat.

Testy pilnuja trzech rzeczy, bez ktorych to byla by prosba w prozie: pasma licza sie
z marginesu i sa symetryczne, delta wchodzi do stanu razem z uzasadnieniem z fikcji,
a commit ODMAWIA, gdy rzut policzyl przechylenie, ktorego outcome nie zastosowal.
"""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

import yaml

TOOLS = Path(__file__).resolve().parent.parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))

import gm_runtime  # noqa: E402

AXIS = ROOT / "campaigns" / "lucan" / "state" / "world-axis.yaml"
TIME = ROOT / "campaigns" / "lucan" / "state" / "time.yaml"
TESTS_MD = ROOT / "system" / "tests.md"
ACTIVE = ROOT / "campaigns" / "lucan" / "context" / "active.yaml"


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}


def roll(natural: int, modified: int, difficulty: int, critical: str | None = None) -> dict:
    return {"id": "roll_test", "natural_roll": natural, "modified_result": modified,
            "difficulty": difficulty, "critical": critical}


class BandTest(unittest.TestCase):
    def test_pasma_licza_sie_z_marginesu_nie_z_surowego_d100(self):
        """Ten sam wynik przy roznym progu nie moze znaczyc tego samego."""
        latwy = gm_runtime.world_axis_from_roll(roll(70, 70, 40))
        trudny = gm_runtime.world_axis_from_roll(roll(70, 70, 85))
        self.assertGreater(latwy["delta"], 0)
        self.assertLess(trudny["delta"], 0)

    def test_skala_jest_symetryczna(self):
        for margines, oczekiwana in ((60, 2), (10, 1), (0, 0), (-10, -1), (-60, -2)):
            wynik = gm_runtime.world_axis_from_roll(roll(50, 50 + margines, 50))
            self.assertEqual(wynik["delta"], oczekiwana, f"margines {margines}")

    def test_krytyk_przebija_margines(self):
        wysoki = gm_runtime.world_axis_from_roll(roll(100, 101, 95, "critical_high"))
        niski = gm_runtime.world_axis_from_roll(roll(1, 90, 10, "critical_low"))
        self.assertEqual(wysoki["delta"], 3)
        self.assertEqual(niski["delta"], -3, "krytyczna jedynka przy dodatnim marginesie")

    def test_zawieszenie_jest_realnym_wynikiem(self):
        """Waskie pasmo zero: swiat nie tezeje i nie peka, sytuacja zostaje jak byla."""
        wynik = gm_runtime.world_axis_from_roll(roll(50, 52, 50))
        self.assertEqual(wynik["delta"], 0)
        self.assertEqual(wynik["band"], "zawieszenie")


class StateFileTest(unittest.TestCase):
    def setUp(self) -> None:
        self.axis = load(AXIS)

    def test_kazda_dziedzina_ma_znaczenie_obu_kierunkow(self):
        """Bez tego 'porzadek' jest slowem bez tresci i narrator wpisze w nie, co mu wygodnie."""
        self.assertTrue(self.axis["domains"])
        for domain in self.axis["domains"]:
            for pole in ("id", "label", "value", "step", "order_means", "entropy_means"):
                self.assertTrue(str(domain.get(pole, "")).strip() != ""
                                or isinstance(domain.get(pole), int),
                                f"{domain.get('id')}: brak {pole}")
            self.assertTrue(domain["factions"], f"{domain['id']}: dziedzina bez frakcji")
            self.assertNotEqual(domain["order_means"].strip(), domain["entropy_means"].strip())

    def test_os_jest_zdefiniowana_ale_jeszcze_nieaktywna(self):
        """AGENTS.md: roll_policy zmienia sie wylacznie przy jawnie zatwierdzonym przejsciu."""
        self.assertEqual((load(TIME).get("roll_policy") or {}).get("mode"), "disabled")
        self.assertIn("inactive", self.axis["status"])

    def test_wartosci_startowe_sa_zerowe(self):
        self.assertEqual([d["value"] for d in self.axis["domains"]],
                         [0] * len(self.axis["domains"]))
        self.assertEqual(self.axis["totals"]["world_total"], 0)

    def test_regula_jest_osiagalna_kiedy_pada_rzut(self):
        warunkowe = [ref for key, refs in load(ACTIVE).items()
                     if key.startswith("load_when_") and isinstance(refs, list) for ref in refs]
        self.assertIn("campaigns/lucan/state/world-axis.yaml", warunkowe,
                      "stan osi nieosiagalny z triggera - narrator wymysli wartosci od nowa")

    def test_tests_md_opisuje_nowe_znaczenie_rzutu(self):
        tekst = TESTS_MD.read_text(encoding="utf-8")
        for fragment in ("porządek", "entropi", "world_axis", "shift_world_axis"):
            self.assertIn(fragment, tekst, f"tests.md nie opisuje: {fragment}")


class OperationTest(unittest.TestCase):
    """Operacja pracuje na KOPII stanu w pamieci - zaden test nie rusza plikow kampanii."""

    def setUp(self) -> None:
        self.campaign = ROOT / "campaigns" / "lucan"
        self.changed: dict[Path, dict] = {}
        # Wstrzykujemy kopie stanu, zeby load_mutable nie czytal ani nie pisal dysku.
        self.changed[AXIS] = copy.deepcopy(load(AXIS))
        scene_path = self.campaign / "context" / "scene.yaml"
        self.changed[scene_path] = copy.deepcopy(
            load(scene_path) | {"pending_world_reactions": []})
        self.scene_path = scene_path

    def zastosuj(self, domain: str, delta: int, reason: str = "z fikcji tej sceny") -> None:
        gm_runtime.apply_operation(
            self.campaign, self.changed,
            {"op": "shift_world_axis", "domain": domain, "delta": delta,
             "reason": reason, "roll_id": "roll_test"},
            "event_test")

    def test_delta_wchodzi_do_dziedziny_i_do_sumy(self):
        self.zastosuj("prawo", 2)
        axis = self.changed[AXIS]
        prawo = next(d for d in axis["domains"] if d["id"] == "prawo")
        self.assertEqual(prawo["value"], 2)
        self.assertEqual(axis["totals"]["world_total"], 2)
        self.assertEqual(axis["history"][-1]["reason"], "z fikcji tej sceny")
        self.assertEqual(axis["history"][-1]["roll_id"], "roll_test")

    def test_prog_kolejkuje_reakcje_swiata_w_obie_strony(self):
        self.zastosuj("ulica", 2)
        self.assertEqual(self.changed[self.scene_path]["pending_world_reactions"], [])
        self.zastosuj("ulica", 1)          # 3 -> poziom +1
        reakcje = self.changed[self.scene_path]["pending_world_reactions"]
        self.assertEqual(len(reakcje), 1)
        self.assertEqual(reakcje[0]["direction"], "porzadek")
        self.assertEqual(reakcje[0]["level"], 1)
        self.zastosuj("ulica", -6)        # -3 -> poziom -1
        reakcje = self.changed[self.scene_path]["pending_world_reactions"]
        self.assertEqual(len(reakcje), 2)
        self.assertEqual(reakcje[-1]["direction"], "entropia")
        self.assertEqual(reakcje[-1]["level"], -1)

    def test_reakcja_nie_wymysla_efektu_tylko_zada_zrodla(self):
        self.zastosuj("wiara", 3)
        reakcja = self.changed[self.scene_path]["pending_world_reactions"][0]
        self.assertIn("wskaz", reakcja["effect"].lower())
        self.assertFalse(reakcja["world_test_required"])

    def test_nieznana_dziedzina_i_pusty_powod_sa_bledem(self):
        with self.assertRaises(gm_runtime.RuntimeError):
            self.zastosuj("nie_ma_takiej", 1)
        with self.assertRaises(gm_runtime.RuntimeError):
            self.zastosuj("prawo", 1, reason="   ")
        with self.assertRaises(gm_runtime.RuntimeError):
            self.zastosuj("prawo", 0)


class CommitGateTest(unittest.TestCase):
    def test_commit_odmawia_gdy_rzut_przechylil_swiat_a_outcome_nie(self):
        transakcja = {"roll": {"id": "roll_x", "world_axis": {
            "margin": 30, "band": "porzadek_wyrazny", "delta": 2}}}
        with self.assertRaises(gm_runtime.RuntimeError) as ctx:
            gm_runtime.validate_world_axis_applied(transakcja, {"operations": []})
        self.assertIn("shift_world_axis", str(ctx.exception))

    def test_commit_przechodzi_gdy_delta_zastosowana(self):
        transakcja = {"roll": {"id": "roll_x", "world_axis": {
            "margin": 30, "band": "porzadek_wyrazny", "delta": 2}}}
        gm_runtime.validate_world_axis_applied(transakcja, {"operations": [
            {"op": "shift_world_axis", "domain": "prawo", "delta": 2,
             "reason": "urzednik przyjal pismo z terminem", "roll_id": "roll_x"}]})

    def test_zawieszenie_nie_wymaga_operacji(self):
        transakcja = {"roll": {"id": "roll_x", "world_axis": {
            "margin": 1, "band": "zawieszenie", "delta": 0}}}
        gm_runtime.validate_world_axis_applied(transakcja, {"operations": []})

    def test_tura_bez_rzutu_nie_wymaga_niczego(self):
        gm_runtime.validate_world_axis_applied({}, {"operations": []})


class SummaryTest(unittest.TestCase):
    def test_pod_osia_swiata_passes_nie_jest_naglowkiem(self):
        r = roll(70, 70, 40) | {"passes_threshold": True}
        r["world_axis"] = gm_runtime.world_axis_from_roll(r)
        summary = gm_runtime.roll_summary(r)
        self.assertNotIn("passes", summary,
                         "pierwsza liczba po rzucie znowu jest ocena zdal / nie zdal")
        self.assertEqual(summary["world_axis"]["delta"], 2)
        self.assertIn("fikcja", summary["hint"])

    def test_bez_osi_summary_zostaje_jak_byl(self):
        summary = gm_runtime.roll_summary(roll(70, 70, 40) | {"passes_threshold": True})
        self.assertTrue(summary["passes"])
        self.assertNotIn("world_axis", summary)


if __name__ == "__main__":
    unittest.main()

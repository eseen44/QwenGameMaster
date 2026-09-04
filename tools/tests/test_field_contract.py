"""Testy etapu 10: pola, ktore silnik czyta, i kontrakt, ktory nie moze sklamac.

Najgrozniejsza klasa bledu z audytu, bo klamie W STRONE BEZPIECZENSTWA: autor pisze
"ubytek wylaczony", odczytuje to z pliku i wierzy. Zmierzone: companion_spidey mial flage
`decay_suppressed` ORAZ regule decay bez `requires`, wiec silnik ubywal mu rezerwy tak samo
jak wszystkim; dwa inne okazy nosily WARIANTY nazwy flagi, ktore nie robily nic.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import yaml

TOOLS = Path(__file__).resolve().parent.parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))

import build_field_contract as contract
import gm_runtime

CONTRACT = ROOT / "system" / "mechanics" / "instance-fields.yaml"
INSTANCES = ROOT / "campaigns" / "lucan" / "state" / "instances"


def instancja(flags: list[str], current: float = 3.0) -> dict:
    return {
        "id": "test_okaz",
        "object_type": "entity_instance",
        "status": "active",
        "revision": 1,
        "status_flags": list(flags),
        "conditions": [],
        "resources": {
            "necrotic_reservoir": {
                "current": current,
                "capacity": 3,
                "decay": {"interval_seconds": 3600, "units": 1},
            }
        },
    }


class DecaySuppressionTest(unittest.TestCase):
    def test_bez_flagi_ubytek_dziala(self):
        okaz = instancja([])
        gm_runtime.process_instance_time(okaz, 3600)
        self.assertEqual(okaz["resources"]["necrotic_reservoir"]["current"], 2.0)

    def test_dokladna_flaga_TLUMI_ubytek(self):
        okaz = instancja(["decay_suppressed"])
        gm_runtime.process_instance_time(okaz, 3600 * 5)
        self.assertEqual(okaz["resources"]["necrotic_reservoir"]["current"], 3.0,
                         "flaga decay_suppressed znowu jest dekoracja")

    def test_flaga_na_puli_tez_tlumi(self):
        okaz = instancja([])
        okaz["resources"]["necrotic_reservoir"]["decay_suppressed"] = True
        gm_runtime.process_instance_time(okaz, 3600 * 5)
        self.assertEqual(okaz["resources"]["necrotic_reservoir"]["current"], 3.0)

    def test_WARIANT_nazwy_flagi_NIE_tlumi_i_to_jest_pulapka(self):
        """Silnik sprawdza dokladna nazwe - dlatego kontrakt musi warianty ZGLASZAC."""
        okaz = instancja(["decay_suppressed_permanent_od_tury_177"])
        gm_runtime.process_instance_time(okaz, 3600)
        self.assertEqual(okaz["resources"]["necrotic_reservoir"]["current"], 2.0,
                         "wariant nazwy zaczal tlumic - to znaczy, ze dopasowanie jest "
                         "po prefiksie i kazda flaga o podobnej nazwie zmienia mechanike")

    def test_regeneracja_i_polowanie_nie_sa_tlumione_ta_flaga(self):
        okaz = instancja(["decay_suppressed"], current=1.0)
        okaz["resources"]["necrotic_reservoir"]["hunting_recovery"] = {
            "interval_seconds": 3600, "units": 1}
        gm_runtime.process_instance_time(okaz, 3600)
        self.assertEqual(okaz["resources"]["necrotic_reservoir"]["current"], 2.0)


class ContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.document = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))

    def test_kontrakt_jest_aktualny(self):
        self.assertEqual(CONTRACT.read_text(encoding="utf-8"), contract.build(),
                         "kontrakt nieaktualny - uruchom python tools/build_field_contract.py "
                         "i PRZECZYTAJ diff, bo w stanie pojawilo sie nowe pole")

    def test_brak_pulapek(self):
        self.assertEqual(self.document["warnings_looks_mechanical_but_is_not"], [],
                         "flaga udajaca mechanike wrocila")

    def test_kazde_pole_ma_status_ze_slownika(self):
        dozwolone = {"engine_reads", "engine_reads_via_requires",
                     "documentation_only", "LOOKS_MECHANICAL_BUT_IS_NOT"}
        for entry in self.document["fields"] + self.document["status_flags"]:
            self.assertIn(entry["status"], dozwolone)

    def test_status_engine_reads_nie_moze_sklamac(self):
        """Pole oznaczone jako czytane MUSI byc widoczne w kodzie albo w requires."""
        code = contract.code_text()
        _, _, required = contract.collect()
        for entry in self.document["status_flags"]:
            if entry["status"] == "engine_reads":
                self.assertIn(f'"{entry["flag"]}"', code,
                              f"flaga {entry['flag']} oznaczona jako czytana, a nie ma jej w kodzie")
            elif entry["status"] == "engine_reads_via_requires":
                self.assertIn(entry["flag"], required)

    def test_kontrakt_obejmuje_kazde_pole_z_instancji(self):
        fields, flags, _ = contract.collect()
        w_kontrakcie = {entry["field"] for entry in self.document["fields"]}
        self.assertEqual(set(fields) - w_kontrakcie, set(),
                         "pole ze stanu poza kontraktem - czyli moze udawac mechanike")
        self.assertEqual(flags - {entry["flag"] for entry in self.document["status_flags"]}, set())

    def test_wiekszosc_flag_jest_dokumentacja_i_to_jest_zapisane(self):
        """Nie zmiekczenie: chodzi o to, zeby liczba byla JAWNA, a nie zaskakujaca."""
        counts = self.document["counts"]
        self.assertGreater(counts["flags"], 50)
        self.assertLess(counts["flags_engine_reads"], 15,
                        "jesli silnik zaczal czytac wiele flag, przejrzyj kontrakt swiadomie")


class RepairedInstancesTest(unittest.TestCase):
    def test_dwa_okazy_maja_dokladna_flage_i_pelna_rezerwe(self):
        for nazwa, pelna in (("spy-hawk-moth-01.yaml", 3), ("webber-anchored.yaml", 6)):
            document = yaml.safe_load((INSTANCES / nazwa).read_text(encoding="utf-8-sig"))
            self.assertIn("decay_suppressed", document["status_flags"], nazwa)
            pool = document["resources"]["necrotic_reservoir"]
            self.assertEqual(pool["current"], pelna, f"{nazwa}: rezerwa nie przywrocona")

    def test_opis_wariantu_nie_zginal(self):
        document = yaml.safe_load((INSTANCES / "webber-anchored.yaml").read_text(encoding="utf-8-sig"))
        opisowe = [f for f in document["status_flags"] if "DOKUMENTACJA_NIE_MECHANIKA" in f]
        self.assertTrue(opisowe, "tresc wariantu flagi zniknela zamiast zostac jako nota")


if __name__ == "__main__":
    unittest.main()

"""Regresja na NAZWANE awarie tej kampanii.

Kazdy test odtwarza jeden bląd, ktory faktycznie sie wydarzyl i kosztowal retcon.
Nazwa testu niesie numer retconu, zeby przy kolejnej zmianie silnika bylo widac, CO
dokladnie przestalo byc pilnowane - a nie tylko ze "cos jest czerwone".

Zasada doboru: test wchodzi tu dopiero wtedy, gdy istnieje retcon opisujacy awarie.
To nie jest miejsce na hipotezy o tym, co moglo by pojsc zle.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

import yaml

import gm_runtime


class TimeClassGateTests(unittest.TestCase):
    """retcon_000172A - tura 274 dostala 600 s przy klasie `brief` (tabela: 300)."""

    def test_klasa_czasu_jest_sprawdzana_takze_przy_jawnym_time_seconds(self) -> None:
        scene = {"tension": {"level": 0}}
        # `standard` nie istnieje w TIME_SECONDS. Dziewiec tur przeszlo z ta klasa tylko
        # dlatego, ze podawaly time_seconds, a funkcja wracala przed kontrola.
        with self.assertRaises(gm_runtime.RuntimeError):
            gm_runtime.action_seconds(
                {"time_class": "standard", "time_seconds": 1800}, scene
            )

    def test_znana_klasa_z_jawnym_czasem_nadal_przechodzi(self) -> None:
        scene = {"tension": {"level": 0}}
        self.assertEqual(
            gm_runtime.action_seconds({"time_class": "brief", "time_seconds": 600}, scene),
            600,
        )

    def test_extended_nadal_wymaga_jawnego_czasu(self) -> None:
        scene = {"tension": {"level": 0}}
        with self.assertRaises(gm_runtime.RuntimeError):
            gm_runtime.action_seconds({"time_class": "extended"}, scene)
        self.assertEqual(
            gm_runtime.action_seconds({"time_class": "extended", "time_seconds": 90}, scene),
            90,
        )


class TimeBasisTests(unittest.TestCase):
    """retcon_000172A, druga polowa - skad wzieta jest liczba sekund."""

    SCENE = {"tension": {"level": 0}}

    def test_jawny_czas_po_zapadce_wymaga_zrodla(self) -> None:
        request = {
            "turn_id": f"turn_interlude_{gm_runtime.TIME_BASIS_BASELINE_TURN + 1}",
            "time_class": "brief",
            "time_seconds": 300,
        }
        with self.assertRaises(gm_runtime.RuntimeError) as ctx:
            gm_runtime.action_seconds(request, self.SCENE)
        self.assertIn("time_basis", str(ctx.exception))

    def test_tury_sprzed_zapadki_sa_dlugiem_i_przechodza(self) -> None:
        request = {
            "turn_id": f"turn_interlude_{gm_runtime.TIME_BASIS_BASELINE_TURN}",
            "time_class": "brief",
            "time_seconds": 600,
        }
        self.assertEqual(gm_runtime.action_seconds(request, self.SCENE), 600)

    def test_pacing_row_musi_miescic_sie_w_pasmie(self) -> None:
        # Pieczatka bez pokrycia jest gorsza niz brak bramki: produkuje uzasadnienie,
        # ktore wyglada na sprawdzone.
        request = {
            "turn_id": "turn_interlude_999",
            "time_class": "brief",
            "time_seconds": 600,
            "time_basis": "pacing_row",
        }
        with self.assertRaises(gm_runtime.RuntimeError) as ctx:
            gm_runtime.action_seconds(request, self.SCENE)
        self.assertIn("pasmie", str(ctx.exception))

    def test_czas_w_pasmie_przechodzi(self) -> None:
        request = {
            "turn_id": "turn_interlude_999",
            "time_class": "brief",
            "time_seconds": 300,
            "time_basis": "pacing_row",
        }
        self.assertEqual(gm_runtime.action_seconds(request, self.SCENE), 300)

    def test_deklaracja_gracza_nie_jest_ograniczona_pasmami(self) -> None:
        # retcon_000061: jawnie podany czas ma pierwszenstwo i nie wolno go mnozyc
        # przez wymyslone tarcie. Tabela pasm nie moze tego cofnac.
        request = {
            "turn_id": "turn_interlude_999",
            "time_class": "brief",
            "time_seconds": 5,
            "time_basis": "player_declaration",
        }
        self.assertEqual(gm_runtime.action_seconds(request, self.SCENE), 5)

    def test_preview_podaje_domysl_silnika_obok_deklaracji(self) -> None:
        guidance = gm_runtime.time_guidance(
            {"time_class": "brief", "time_seconds": 600}, self.SCENE
        )
        self.assertEqual(guidance["engine_default_seconds"], 300)
        self.assertEqual(guidance["declared_seconds"], 600)
        self.assertTrue(
            guidance["declared_outside_every_row"],
            "600 s przy klasie brief bylo dokladnie tym, czego nikt nie porownal w t_274",
        )


class OperationDictionaryTests(unittest.TestCase):
    """Literowka w nazwie operacji nie moze zatrzymywac commita w polowie zapisu."""

    def _make_outcome(self, operations: list[dict]) -> dict:
        return {
            "intent_achieved": True,
            "arrangement": "unchanged",
            "perspective": "pc_lucan",
            "summary": "x",
            "operations": operations,
            "consequence_source_refs": [],
        }

    def test_nieznana_operacja_odrzucona_przed_zapisem(self) -> None:
        with self.assertRaises(gm_runtime.RuntimeError) as ctx:
            gm_runtime.validate_outcome(
                self._make_outcome([{"op": "move_instance", "instance_id": "spy_rat_01"}])
            )
        self.assertIn("move_instance", str(ctx.exception))

    def test_znane_operacje_przechodza(self) -> None:
        gm_runtime.validate_outcome(
            self._make_outcome([{"op": "set", "instance_id": "spy_rat_01",
                            "path": "position.zone_id", "value": "zone_sewer_tannery"}])
        )

    def test_slownik_pokrywa_sie_z_dyspozytorem(self) -> None:
        # Kontrola pilnuje samej siebie: kazda operacja ze slownika musi byc obsluzona
        # w apply_operation, inaczej bramka przepusci cos, czego silnik nie umie wykonac.
        source = (TOOLS / "gm_runtime.py").read_text(encoding="utf-8")
        dispatcher = source.split("def apply_operation", 1)[1]
        for op in sorted(gm_runtime.OPERATIONS):
            self.assertIn(f'"{op}"', dispatcher, f"{op} jest w slowniku, ale nie w dyspozytorze")


class ConsumeClampTests(unittest.TestCase):
    """Przycinanie do pojemnosci dotyczy `restore`, nie `consume`.

    Testy ida przez PRAWDZIWE apply_operation - podmieniony jest wylacznie odczyt encji
    z dysku, zeby nie budowac calej kampanii dla jednej puli.
    """

    def _entity(self, current: float, capacity: float) -> dict:
        return {
            "id": "spy_test_01",
            "revision": 1,
            "resources": {"necrotic_reservoir": {"current": current, "capacity": capacity}},
        }

    def _apply(self, entity: dict, operation: dict) -> None:
        with mock.patch.object(
            gm_runtime, "entity_for_operation", return_value=(Path("spy_test_01.yaml"), entity)
        ):
            gm_runtime.apply_operation(Path("."), {}, operation, "event_test")

    def test_consume_z_puli_ponad_sufitem_odejmuje_a_nie_scina(self) -> None:
        entity = self._entity(current=18, capacity=15)

        self._apply(entity, {"op": "consume", "instance_id": "spy_test_01",
                             "pool": "necrotic_reservoir", "units": 1})

        self.assertEqual(
            entity["resources"]["necrotic_reservoir"]["current"], 17,
            "consume scial pule do pojemnosci zamiast odjac jedna jednostke",
        )

    def test_restore_nadal_przycina_do_pojemnosci(self) -> None:
        entity = self._entity(current=14, capacity=15)

        self._apply(entity, {"op": "restore", "instance_id": "spy_test_01",
                             "pool": "necrotic_reservoir", "units": 5})

        self.assertEqual(entity["resources"]["necrotic_reservoir"]["current"], 15)

    def test_consume_ponad_stan_nadal_odmawia(self) -> None:
        entity = self._entity(current=2, capacity=15)

        with self.assertRaises(gm_runtime.RuntimeError):
            self._apply(entity, {"op": "consume", "instance_id": "spy_test_01",
                                 "pool": "necrotic_reservoir", "units": 3})

        self.assertEqual(entity["resources"]["necrotic_reservoir"]["current"], 2,
                         "odmowa nie moze zostawic puli ruszonej")


class OverflowRetentionTests(unittest.TestCase):
    """retcon_000109 - nadwyzka ponad sufit NIE PRZEPADA."""

    def test_tykniecie_na_pelnym_zbiorniku_odklada_nadwyzke(self) -> None:
        instance = {
            "id": "spy_test_01",
            "status_flags": ["autonomous_hunting"],
            "resources": {
                "necrotic_reservoir": {
                    "current": 3,
                    "capacity": 3,
                    "hunting_recovery": {
                        "interval_seconds": 86400,
                        "units": 2,
                        "requires": ["autonomous_hunting"],
                    },
                    "runtime": {"hunting_recovery_elapsed_seconds": 0},
                }
            },
        }

        gm_runtime.process_instance_time(instance, 86400)

        pool = instance["resources"]["necrotic_reservoir"]
        self.assertEqual(pool["current"], 3, "zbiornik nie powinien przekroczyc pojemnosci")
        self.assertEqual(
            pool["runtime"].get("overflow_pending"), 2,
            "nadwyzka zniknela bez sladu - to jest dokladnie to, czego zabrania retcon_000109",
        )

    def test_nadwyzka_kumuluje_sie_przez_kolejne_doby(self) -> None:
        instance = {
            "id": "spy_test_01",
            "status_flags": ["autonomous_hunting"],
            "resources": {
                "necrotic_reservoir": {
                    "current": 3,
                    "capacity": 3,
                    "hunting_recovery": {
                        "interval_seconds": 86400,
                        "units": 2,
                        "requires": ["autonomous_hunting"],
                    },
                    "runtime": {"hunting_recovery_elapsed_seconds": 0},
                }
            },
        }

        gm_runtime.process_instance_time(instance, 86400 * 3)

        pool = instance["resources"]["necrotic_reservoir"]
        self.assertEqual(pool["runtime"].get("overflow_pending"), 6)

    def test_zbiornik_ponizej_sufitu_nie_produkuje_nadwyzki(self) -> None:
        instance = {
            "id": "spy_test_01",
            "status_flags": ["autonomous_hunting"],
            "resources": {
                "necrotic_reservoir": {
                    "current": 0,
                    "capacity": 6,
                    "hunting_recovery": {
                        "interval_seconds": 86400,
                        "units": 2,
                        "requires": ["autonomous_hunting"],
                    },
                    "runtime": {"hunting_recovery_elapsed_seconds": 0},
                }
            },
        }

        gm_runtime.process_instance_time(instance, 86400)

        pool = instance["resources"]["necrotic_reservoir"]
        self.assertEqual(pool["current"], 2)
        self.assertNotIn("overflow_pending", pool["runtime"])


class EnvironmentRequirementTests(unittest.TestCase):
    """Warunek srodowiskowy pyta o MIEJSCE, nie o flage.

    Karta Varkhena twierdzila, ze wyniesienie ciala z cmentarza wylaczy doplyw samo.
    Nieprawda: silnik sprawdzal flage, a flaga nie wie o przeprowadzce. Testy budują
    wlasna mini-kampanie, zeby nie zalezec od tego, gdzie akurat lezy Varkhen.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.campaign = root / "campaigns" / "lucan"
        (self.campaign / "locations" / "krypta").mkdir(parents=True)
        (self.campaign / "locations" / "index.yaml").write_text(
            yaml.safe_dump({"locations": [
                {"id": "loc_krypta", "ref": "campaigns/lucan/locations/krypta/location.yaml"},
            ]}, allow_unicode=True), encoding="utf-8")
        (self.campaign / "locations" / "krypta" / "state.yaml").write_text(
            yaml.safe_dump({"environment": {"conditions": ["death_field"]}}, allow_unicode=True),
            encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _instance(self, location_id: str) -> dict:
        return {
            "id": "companion_test",
            # Flaga ZOSTAJE w karcie przy obu wariantach - to wlasnie ona klamala.
            "status_flags": ["in_cemetery_death_field"],
            "position": {"location_id": location_id},
            "resources": {
                "reservoir": {
                    "current": 0,
                    "capacity": 72,
                    "regeneration": {
                        "interval_seconds": 86400,
                        "units": 0.8,
                        "requires": ["env:death_field"],
                    },
                    "runtime": {"regeneration_elapsed_seconds": 0},
                }
            },
        }

    def test_w_miejscu_z_polem_smierci_nalicza(self) -> None:
        instance = self._instance("loc_krypta")
        gm_runtime.process_instance_time(instance, 86400, self.campaign)
        self.assertAlmostEqual(instance["resources"]["reservoir"]["current"], 0.8)

    def test_poza_miejscem_nie_nalicza_mimo_ze_flaga_zostala(self) -> None:
        instance = self._instance("loc_gdzie_indziej")
        gm_runtime.process_instance_time(instance, 86400, self.campaign)
        self.assertEqual(
            instance["resources"]["reservoir"]["current"], 0,
            "przeniesienie ciala nie wylaczylo doplywu - flaga znowu zdecydowala za miejsce",
        )

    def test_bez_kontekstu_kampanii_warunek_nie_jest_spelniony(self) -> None:
        # Bezpieczny kierunek: brak dowodu na warunek srodowiskowy nie produkuje energii.
        instance = self._instance("loc_krypta")
        gm_runtime.process_instance_time(instance, 86400, None)
        self.assertEqual(instance["resources"]["reservoir"]["current"], 0)


class ConsumeItemTests(unittest.TestCase):
    """retcon_000170/173 - zuzycie przedmiotu i jego skutek musza byc JEDNA operacja.

    W turze 177 preparat wszedl w Tkacza, a zapas zostal nietkniety, bo to byly dwa
    osobne obowiazki narratora. 97 tur pozniej ktos przeczytal ten zapas i polozyl
    graczowi na stole przedmiot, ktorego nie ma.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.campaign = Path(self._tmp.name) / "campaigns" / "lucan"
        (self.campaign / "state").mkdir(parents=True)
        self.resources = self.campaign / "state" / "resources.yaml"
        self.resources.write_text(yaml.safe_dump({
            "caches": [{
                "id": "cache_test",
                "contents": [
                    {"id": "decay_suppressing_vial", "quantity": 2, "unit": "vial"},
                    {"id": "ritual_salt", "quantity": 1, "unit": "packet"},
                ],
            }],
        }, allow_unicode=True), encoding="utf-8")
        self.target = {"id": "companion_test", "revision": 3, "status_flags": []}

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _apply(self, operation: dict, changed: dict | None = None) -> dict:
        changed = {} if changed is None else changed
        with mock.patch.object(
            gm_runtime, "entity_for_operation",
            return_value=(Path("companion_test.yaml"), self.target),
        ):
            gm_runtime.apply_operation(self.campaign, changed, operation, "event_turn_test")
        return changed

    def _record(self, changed: dict, item_id: str) -> dict:
        doc = changed[self.resources.resolve()]
        return next(e for e in doc["caches"][0]["contents"] if e["id"] == item_id)

    def test_jedna_operacja_odejmuje_zapas_i_naklada_skutek(self) -> None:
        changed = self._apply({
            "op": "consume_item", "item_id": "decay_suppressing_vial", "units": 1,
            "on": "companion_test", "effect_flags": ["decay_suppressed"],
            "reason": "porcja tlumiaca rozklad",
        })

        record = self._record(changed, "decay_suppressing_vial")
        self.assertEqual(record["quantity"], 1)
        self.assertIn("decay_suppressed", self.target["status_flags"])
        self.assertEqual(self.target["revision"], 4, "rewizja odbiorcy nie zostala podbita")

    def test_ostatnia_sztuka_zamyka_pozycje_z_data_i_odbiorca(self) -> None:
        changed = self._apply({
            "op": "consume_item", "item_id": "ritual_salt", "units": 1,
            "on": "companion_test", "effect_flags": ["preserved"],
        })

        record = self._record(changed, "ritual_salt")
        self.assertEqual(record["quantity"], 0)
        self.assertEqual(record["status"], "consumed")
        self.assertEqual(record["consumed_event_id"], "event_turn_test")
        self.assertEqual(record["consumed_on"], "companion_test")

    def test_ponad_stan_odmawia_i_nie_rusza_niczego(self) -> None:
        changed: dict = {}
        with self.assertRaises(gm_runtime.RuntimeError) as ctx:
            self._apply({"op": "consume_item", "item_id": "decay_suppressing_vial",
                         "units": 5, "on": "companion_test",
                         "effect_flags": ["decay_suppressed"]}, changed)
        self.assertIn("za malo", str(ctx.exception))
        self.assertEqual(self.target["status_flags"], [],
                         "skutek spadl na odbiorce mimo odmowy")
        self.assertEqual(self.target["revision"], 3)

    def test_nieznany_przedmiot_odmawia(self) -> None:
        with self.assertRaises(gm_runtime.RuntimeError) as ctx:
            self._apply({"op": "consume_item", "item_id": "nie_ma_takiego", "units": 1})
        self.assertIn("nieznany przedmiot", str(ctx.exception))

    def test_skutek_bez_odbiorcy_jest_bledem_deklaracji(self) -> None:
        with self.assertRaises(gm_runtime.RuntimeError) as ctx:
            self._apply({"op": "consume_item", "item_id": "ritual_salt", "units": 1,
                         "effect_flags": ["preserved"]})
        self.assertIn("nie ma na kogo spasc", str(ctx.exception))


class PositionFixTests(unittest.TestCase):
    """retcon_000171/176 - pozycja, wiedza o niej i rozkaz to trzy rozne rzeczy."""

    def _entity(self) -> dict:
        return {"id": "spy_test_01", "revision": 1,
                "position": {"location_id": "loc_a", "zone_id": "zone_a"}}

    def _apply(self, entity: dict, operation: dict, event_id: str) -> None:
        with mock.patch.object(
            gm_runtime, "entity_for_operation", return_value=(Path("x.yaml"), entity)
        ):
            gm_runtime.apply_operation(Path("."), {}, operation, event_id)

    def test_formation_zamkniete_po_zapadce(self) -> None:
        entity = self._entity()
        numer = gm_runtime.POSITION_FIELD_BASELINE_TURN + 1
        with self.assertRaises(gm_runtime.RuntimeError) as ctx:
            self._apply(entity, {"op": "set", "instance_id": "spy_test_01",
                                 "path": "position.formation", "value": "cokolwiek"},
                        f"event_turn_interlude_{numer}")
        self.assertIn("position.formation", str(ctx.exception))

    def test_tura_sprzed_zapadki_nadal_moze_pisac_formation(self) -> None:
        entity = self._entity()
        self._apply(entity, {"op": "set", "instance_id": "spy_test_01",
                             "path": "position.formation", "value": "historyczne"},
                    f"event_turn_interlude_{gm_runtime.POSITION_FIELD_BASELINE_TURN}")
        self.assertEqual(entity["position"]["formation"], "historyczne")

    def test_silnik_sam_stempluje_pochodzenie_pozycji(self) -> None:
        # Wersja z recznym fix przy kazdym secie skonczylaby sie odruchowym "confirmed".
        entity = self._entity()
        self._apply(entity, {"op": "set", "instance_id": "spy_test_01",
                             "path": "position.zone_id", "value": "zone_b"},
                    "event_turn_interlude_300")
        self.assertEqual(entity["position"]["fix"], {
            "status": "confirmed",
            "as_of_event_id": "event_turn_interlude_300",
            "source": "transaction",
        })

    def test_rozkaz_nie_moze_udawac_obserwacji(self) -> None:
        entity = self._entity()
        entity["position"]["fix"] = {"status": "confirmed", "source": "order_assumption"}
        with self.assertRaises(gm_runtime.RuntimeError) as ctx:
            gm_runtime.validate_position_fix(entity)
        self.assertIn("order_assumption", str(ctx.exception))

    def test_rozkaz_jako_domysl_jest_w_porzadku(self) -> None:
        entity = self._entity()
        entity["position"]["fix"] = {"status": "inferred", "source": "order_assumption"}
        gm_runtime.validate_position_fix(entity)


class StandbyLinkTests(unittest.TestCase):
    """Linia alarmowa do Varkhena to ADRES, nie rura.

    Slowa gracza: "de facto martwe lacze, nieuzywane, ale pozwalajace na wznowienie.
    Sam adres. Otwarty port, o ktorym obie strony widza, ze moga go uzyc, ale po ktorym
    samemu nic nie leci. Whitelist w firewallu."

    Do 2026-09-12 silnik pomijal je WYLACZNIE dlatego, ze mialo zerowe jednostki - czyli
    jedna cyfra wpisana przez nieuwage zamienialaby adres w rure i nikt by nie zauwazyl.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.campaign = Path(self._tmp.name) / "campaigns" / "lucan"
        (self.campaign / "state").mkdir(parents=True)
        self.links = self.campaign / "state" / "sustained-links.yaml"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _write(self, link: dict) -> None:
        self.links.write_text(yaml.safe_dump({"links": [link]}, allow_unicode=True),
                              encoding="utf-8")

    def _base(self) -> dict:
        return {
            "id": "link_test", "active": True, "channel": "standby",
            "source_instance_id": "pc_lucan", "source_pool_id": "p",
            "target_instance_id": "companion_varkhen", "target_pool_id": "q",
            "interval_seconds": 86400,
            "source_units_per_interval": 0, "target_units_per_interval": 0,
        }

    def test_standby_nie_jest_naliczane(self) -> None:
        self._write(self._base())
        changed: dict = {}
        gm_runtime.process_sustained_links(self.campaign, changed, 86400, "event_test")
        link = changed[self.links.resolve()]["links"][0]
        self.assertEqual(link.get("runtime", {}).get("successful_intervals", 0), 0)

    def test_liczba_przy_standby_jest_bledem_a_nie_cichym_przesylem(self) -> None:
        link = self._base()
        link["source_units_per_interval"] = 1.0
        self._write(link)
        with self.assertRaises(gm_runtime.RuntimeError) as ctx:
            gm_runtime.process_sustained_links(self.campaign, {}, 86400, "event_test")
        self.assertIn("standby", str(ctx.exception))

    def test_nieznany_rodzaj_lacza_jest_odrzucany(self) -> None:
        link = self._base()
        link["channel"] = "cokolwiek"
        self._write(link)
        with self.assertRaises(gm_runtime.RuntimeError):
            gm_runtime.process_sustained_links(self.campaign, {}, 86400, "event_test")


class ServantsCheckTests(unittest.TestCase):
    """retcon_000171 - trzy sprzeczne zdania o jednym okazie w trzech plikach.

    Kontrola dostaje dane WSTRZYKNIETE, zeby nie zalezec od tego, gdzie akurat stoi siec.
    Test odtwarza stan SPRZED migracji z Etapu 4 - czyli dokladnie to, czego nikt nie
    widzial przez 88 tur.
    """

    def setUp(self) -> None:
        import servants_check
        self.sc = servants_check

    def test_lapie_rozkaz_przy_fladze_braku_rozkazu(self) -> None:
        wij = {
            "status_flags": ["no_standing_order_beyond_default_hunting"],
            "orders": [{"id": "order_map_under_the_guild", "status": "active"}],
            "position": {"location_id": "loc_city_sewer"},
        }
        problems = self.sc.check([("spy_centipede_01", wij)], karty={})
        self.assertIn("rozkaz_kontra_flaga", problems)
        self.assertIn("spy_centipede_01", problems["rozkaz_kontra_flaga"][0])

    def test_lapie_rozkaz_udajacy_obserwacje(self) -> None:
        okaz = {"position": {"location_id": "loc_x",
                             "fix": {"status": "confirmed", "source": "order_assumption"}}}
        problems = self.sc.check([("spy_test", okaz)], karty={})
        self.assertIn("rozkaz_jako_obserwacja", problems)

    def test_lapie_karte_grupowa_sprzeczna_z_instancja(self) -> None:
        okaz = {"position": {"location_id": "loc_city_sewer"}}
        karta = {"deployment": {"spy_test": "loc_lumaria_guild, posterunek przy biurku"}}
        problems = self.sc.check([("spy_test", okaz)], karty={"spy-series.yaml": karta})
        self.assertIn("karta_kontra_instancja", problems)

    def test_stan_po_migracji_jest_czysty(self) -> None:
        wij = {
            "status_flags": ["standing_order_map_under_the_guild_since_t_186"],
            "orders": [{"id": "order_map_under_the_guild", "status": "active"}],
            "position": {"location_id": "loc_city_sewer",
                         "fix": {"status": "unknown", "source": "borrowed_sense"}},
        }
        self.assertEqual(self.sc.check([("spy_centipede_01", wij)], karty={}), {})


if __name__ == "__main__":
    unittest.main()

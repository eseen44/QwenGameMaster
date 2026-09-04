"""Testy etapu 9: linter korpusu retconow i generowany indeks regul.

Dwie rzeczy sa tu warte pilnowania. Pierwsza: ZAPADKA - dlug historyczny nie moze blokowac
(bo walidator swiecacy na czerwono bez przerwy jest ignorowany), ale nowy wpis MUSI przejsc.
Druga: skrot w indeksie ma byc zdaniem z IMPERATYWEM, nie pierwszym zdaniem tresci - na
pierwszym zdaniu retcon_000033 dawal zrzut stanu, a regula stala trzy zdania dalej.
"""

from __future__ import annotations

import datetime as dt
import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

import build_rules_index as index
import retcon_lint as lint


class LintTest(unittest.TestCase):
    # Zegar wstrzykiwany, zeby kontrola "timestamp w przyszlosci" nie zalezala od tego,
    # o ktorej ktos uruchamia testy - fixture stawia znaczniki na 2026-09-04.
    TERAZ = dt.datetime(2026, 9, 4, 23, 0, tzinfo=dt.timezone(dt.timedelta(hours=2)))

    def sprawdz(self, retcons: list[dict], events: set[str] | None = None, now=None):
        return lint.check(retcons, events or set(), now=now or self.TERAZ)

    def wpis(self, numer: int, **nadpisz) -> dict:
        base = {
            "id": f"retcon_{numer:06}",
            "timestamp": f"2026-09-04T{numer % 24:02}:00:00+02:00",
            "reason": "powod",
            "replacement": "tresc korekty",
            "approved_by": "player_declaration_2026_09_04",
            "supersedes": [],
        }
        base.update(nadpisz)
        return base

    def test_poprawny_wpis_bez_naruszen(self):
        self.assertEqual(self.sprawdz([self.wpis(200)]), {})

    def test_brak_pola_wymaganego(self):
        problems = self.sprawdz([self.wpis(200, approved_by=None)])
        self.assertIn("pola_wymagane", problems)

    def test_brak_tresci_korekty(self):
        problems = self.sprawdz([self.wpis(200, replacement=None)])
        self.assertIn("tresc_korekty", problems)

    def test_supersedes_musi_byc_lista(self):
        problems = self.sprawdz([self.wpis(200, supersedes="retcon_000001")])
        self.assertIn("supersedes_lista", problems)

    def test_supersedes_na_nieistniejacy_retcon(self):
        problems = self.sprawdz([self.wpis(200, supersedes=["retcon_999999"])])
        self.assertIn("supersedes_wskazuje_w_nicosc", problems)

    def test_supersedes_na_katalog_jest_naruszeniem(self):
        """Katalog przechodzil jako poprawny ref i przemknal tak moj wlasny retcon_000144."""
        problems = self.sprawdz([self.wpis(200, supersedes=["campaigns/lucan/#cos"])])
        self.assertIn("supersedes_wskazuje_w_nicosc", problems)
        self.assertIn("katalog", problems["supersedes_wskazuje_w_nicosc"][0][1])

    def test_kotwica_na_retconie_nie_rozwiazuje_sie_nigdy(self):
        problems = self.sprawdz([self.wpis(200), self.wpis(201, supersedes=["retcon_000200#klucz"])])
        self.assertIn("kotwica_na_retconie", problems)

    def test_timestamp_w_czasie_kampanii(self):
        problems = self.sprawdz([self.wpis(200, timestamp="2026-08-19T18:01:40+02:00")])
        self.assertIn("timestamp_w_czasie_kampanii", problems)

    def test_timestamp_powtorzony(self):
        stamp = "2026-09-04T12:00:00+02:00"
        problems = self.sprawdz([self.wpis(200, timestamp=stamp), self.wpis(201, timestamp=stamp)])
        self.assertIn("timestamp_powtorzony", problems)

    def test_timestamp_w_przyszlosci_jest_naruszeniem(self):
        """Tak powstal retcon_000147: 16:40 przy zegarze 16:00. Czas, ktory nie nadszedl,
        jest zawsze wpisany z reki i zawsze zmyslony."""
        problems = self.sprawdz([self.wpis(200, timestamp="2026-09-05T10:00:00+02:00")])
        self.assertIn("timestamp_w_przyszlosci", problems)
        self.assertIn("timestamp_w_przyszlosci", lint.BLOCKING)

    def test_timestamp_nierosnacy_jest_naruszeniem_blokujacym(self):
        """Skutek tamtego zmyslenia: nastepny wpis z PRAWDZIWYM odczytem wygladal
        na cofniety, a kontrola tylko szeptala."""
        problems = self.sprawdz([
            self.wpis(200, timestamp="2026-09-04T16:40:00+02:00"),
            self.wpis(201, timestamp="2026-09-04T16:00:48+02:00"),
        ])
        self.assertIn("timestamp_nierosnacy", problems)
        self.assertEqual(problems["timestamp_nierosnacy"][0][0], "retcon_000201")
        self.assertIn("timestamp_nierosnacy", lint.BLOCKING)

    def test_poprawna_kolejnosc_czasu_przechodzi(self):
        """Zapadka musi PRZEPUSCIC poprawna kolejnosc - inaczej blokuje wszystko."""
        problems = self.sprawdz([
            self.wpis(200, timestamp="2026-09-04T15:58:00+02:00"),
            self.wpis(201, timestamp="2026-09-04T16:00:48+02:00"),
        ])
        self.assertEqual(problems, {})

    def test_zakres_tur_jest_rozwijany_a_nie_czytany_jako_id(self):
        """Wzor numeru tury wymagal podkreslnika PO numerze, a id maja postac
        'event_turn_interlude_104' - z 235 tur linter widzial 69 i zglaszal 18 istniejacych
        tur jako nieistniejace."""
        events = {f"event_turn_interlude_{n}" for n in range(100, 125)}
        problems = self.sprawdz([self.wpis(200, supersedes=["event_turn_interlude_104..112"])],
                                events)
        self.assertEqual(problems, {}, f"zakres istniejacych tur zglaszany jako martwy: {problems}")

    def test_zakres_z_brakujaca_tura_nadal_jest_naruszeniem(self):
        events = {f"event_turn_interlude_{n}" for n in range(100, 110)}
        problems = self.sprawdz([self.wpis(200, supersedes=["event_turn_interlude_104..112"])],
                                events)
        self.assertIn("supersedes_wskazuje_w_nicosc", problems)
        self.assertIn("110", problems["supersedes_wskazuje_w_nicosc"][0][1])

    def test_tura_nieobecna_w_calosci_to_cofniecie_a_nie_martwe_wskazanie(self):
        """retcon_000008 i retcon_000010 nazywaja tury 039-041, ktore SAME cofnely.
        Gdyby to wskazanie sie rozwiazywalo, znaczyloby, ze cofniecie nie zadzialalo."""
        events = {"event_turn_interlude_038_numb", "event_turn_interlude_042_cos"}
        problems = self.sprawdz([self.wpis(200, supersedes=["event_turn_interlude_040_zdanie"])],
                                events)
        self.assertIn("supersedes_na_cofnietej_turze", problems)
        self.assertNotIn("supersedes_wskazuje_w_nicosc", problems)
        self.assertNotIn("supersedes_na_cofnietej_turze", lint.BLOCKING)

    def test_zakres_state_refs_na_katalog_przechodzi_a_na_nieistniejacy_nie(self):
        ok = self.sprawdz([self.wpis(200, state_refs_updated=["campaigns/lucan/state/*"])])
        self.assertEqual(ok, {}, f"katalog zakresu zglaszany jako martwy plik: {ok}")
        zle = self.sprawdz([self.wpis(201, state_refs_updated=["campaigns/lucan/nie-ma-tego/*"])])
        self.assertIn("state_refs_wskazuje_w_nicosc", zle)

    def test_kotwica_do_podklucza_magazynu_sie_rozwiazuje(self):
        """act-03-defence.yaml#academy_post lezy po rozbiciu w institutional_defence.yaml
        pod institutional_defence.academy_post - tresc byla na miejscu, miara nie siegala."""
        sekcje = lint.split_store_sections("campaigns/lucan/planning/act-03-defence.yaml")
        self.assertIn("institutional_defence", sekcje, "brak sekcji z indeksu")
        self.assertIn("academy_post", sekcje, "kotwica do podklucza nadal nierozwiazywalna")
        self.assertIn("legal_doctrine_stress_test", sekcje)

    def test_zapadka_dlug_nie_blokuje_a_nowy_wpis_blokuje(self):
        self.assertLess(lint.number("retcon_000100"), lint.BASELINE)
        self.assertGreater(lint.number("retcon_000200"), lint.BASELINE)
        self.assertIn("timestamp_w_czasie_kampanii", lint.BLOCKING)

    def test_prawdziwy_korpus_ma_dlug_ale_nowe_wpisy_czyste(self):
        retcons = lint.load(lint.RETCONS)
        events = {e.get("id") for e in lint.load(lint.EVENTS) if e.get("id")}
        problems = lint.check(retcons, events)
        nowe = [(n, rid, d) for n, rows in problems.items() for rid, d in rows
                if n in lint.BLOCKING and lint.number(rid) > lint.BASELINE]
        self.assertEqual(nowe, [], f"nowe wpisy naruszaja kontrole blokujace: {nowe}")
        self.assertGreater(sum(len(r) for r in problems.values()), 0,
                           "linter nie widzi zadnego dlugu - podejrzane, korpus go ma")

    def test_martwe_wskazania_zostaly_rozliczone_do_dwoch(self):
        """Z 86 na starcie audytu zostaja DWA i oba maja metryke (retcon_000150):
        unassigned_servants_risk - sekcja uchylona i przemianowana w t_103;
        syndicate_offer_the_permit - nie istniala nigdy w calej historii repo.
        Prog jest gorny: jesli wzrosnie, doszlo nowe martwe wskazanie i trzeba je opisac."""
        retcons = lint.load(lint.RETCONS)
        events = {e.get("id") for e in lint.load(lint.EVENTS) if e.get("id")}
        martwe = lint.check(retcons, events).get("supersedes_wskazuje_w_nicosc", [])
        self.assertLessEqual(len(martwe), 2, f"nowe martwe wskazania: {martwe}")

    def test_korpus_nie_ma_juz_brakow_pol_ani_supersedes_jako_napisu(self):
        """retcon_000150: osiem brakow approved_by wypelnione z wlasnej tresci wpisow,
        cztery supersedes-napisy opakowane w listy."""
        retcons = lint.load(lint.RETCONS)
        events = {e.get("id") for e in lint.load(lint.EVENTS) if e.get("id")}
        problems = lint.check(retcons, events)
        self.assertEqual(problems.get("pola_wymagane", []), [])
        self.assertEqual(problems.get("supersedes_lista", []), [])
        self.assertEqual(problems.get("state_refs_wskazuje_w_nicosc", []), [])


class IndexTest(unittest.TestCase):
    def test_skrot_bierze_zdanie_z_imperatywem_nie_pierwsze(self):
        text = ("STAN COFNIETY DO WEJSCIA: czas 2026-08-18T14:15, elapsed 292500, energia 8.0. "
                "KALIBRACJA: narratorowi nie wolno produkowac oporu bez pokrycia w pliku. "
                "Trzecie zdanie bez znaczenia.")
        skrot = index.gist(text)
        self.assertIn("nie wolno", skrot)
        self.assertNotIn("elapsed", skrot)

    def test_korekta_faktu_bez_imperatywu_nie_wchodzi(self):
        self.assertFalse(index.is_normative(
            "Mlodszy brat Klary mial czternascie lat, obecnie ma szesnascie."))

    def test_klauzula_normatywna_wchodzi(self):
        self.assertTrue(index.is_normative("Narratorowi NIE WOLNO tego przedstawiac jako zdrady."))

    def test_slowo_regula_samo_nie_wystarcza(self):
        """"regula" wystepuje w korpusie tez opisowo i wciagalo czyste korekty faktu."""
        self.assertFalse(index.is_normative("Regula z t_227 zostala cofnieta w tej turze."))

    def test_indeks_na_dysku_jest_aktualny(self):
        self.assertTrue(index.OUTPUT.exists(), "brak system/retcon-rules-index.md")
        self.assertEqual(index.OUTPUT.read_text(encoding="utf-8"), index.build(),
                         "indeks nieaktualny - uruchom python tools/build_rules_index.py")

    def test_indeks_ma_naglowek_o_generowaniu(self):
        body = index.OUTPUT.read_text(encoding="utf-8")
        self.assertIn("PLIK GENEROWANY", body)
        self.assertIn("retcons.jsonl", body)


if __name__ == "__main__":
    unittest.main()

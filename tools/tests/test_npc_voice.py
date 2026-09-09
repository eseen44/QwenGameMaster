"""Testy kontraktu glosu NPC i kontraktu prozy tury (2026-09-09).

DLUG, KTORY TE TESTY PILNUJA. Reklamacja gracza 2026-09-09: wszystkie NPC brzmia jak ta
sama osoba i wszyscy wyceniaja kazda decyzje. retcon_000162 zakazal tego w prozie, ale nie
ruszyl ani jednego ZRODLA WEJSCIOWEGO:

  - `speech_traits` Kesza kazaly mu wyceniac wprost ("Wycenia, nie bramkuje: mowi to
    kosztuje tyle"), a pierwsza linia Seraphiny kazala nazywac CENE kazdej rzeczy przed
    zgoda - czyli karty uczyly dokladnie tego, co regula zabraniala,
  - w skrocie karty Kesza `knowledge` w rejestrze protokolu audytowego wazylo 8 343 B przy
    400 B `speech_traits`; model imituje rejestr dominujacy w kontekscie,
  - `outcome.prose` nie mialo kontraktu w ogole, a `gm recent` podaje je nastepnej sesji
    jako JEDYNA probke jezyka: tury 236-248 to 13 wpisow autorskich, ZERO kwestii wprost
    i 20 konstrukcji "powiedzial, ze...".

Testy nie oceniaja gustu. Sprawdzaja maszynowo to, co da sie sprawdzic: pokrycie kart glosu,
rozroznialnosc osi, brak slownika wyceny w zrodle glosu, kolejnosc w skrocie karty oraz
fikstura testu na slepo.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

import yaml

TOOLS = Path(__file__).resolve().parent.parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))

import build_npc_digests            # noqa: E402
import prose_check                  # noqa: E402
import voice_check                  # noqa: E402

CARDS = ROOT / "campaigns" / "lucan" / "entities" / "npcs"
VOICES = CARDS / "voices"
DIGESTS = CARDS / "digests"
FIXTURE = ROOT / "system" / "fixtures" / "voice-blind-test.yaml"
RULE = ROOT / "system" / "npc-voice.md"
ACTIVE = ROOT / "campaigns" / "lucan" / "context" / "active.yaml"

RODZINA_CENY = re.compile(
    r"(?iu)\b(cen[aeyoęą]\w*|wycen\w*|koszt\w*|wartoś\w*|rachun\w*|opłacal\w*)\b"
)


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}


class VoiceCardsTest(unittest.TestCase):
    def test_kontrola_glosow_przechodzi(self):
        problemy, liczby = voice_check.check()
        self.assertEqual(problemy, {}, f"voice_check zglasza: {problemy}")
        self.assertGreaterEqual(liczby["kart_glosu"], 7)

    def test_kazdy_wazny_npc_ma_karte_glosu(self):
        for stem in voice_check.wymagane():
            self.assertTrue((VOICES / f"{stem}.yaml").exists(),
                            f"{stem} jest wazna postacia bez karty glosu (system/npc-voice.md)")

    def test_osiem_osi_i_rozne_wartosci(self):
        """Osie nie moga sie powtarzac miedzy postaciami - inaczej to jeden glos w kilku plikach."""
        for os in voice_check.OSIE:
            wartosci = [voice_check.normalizuj(load(p).get(os)) for p in VOICES.glob("*.yaml")]
            self.assertTrue(all(wartosci), f"pusta os '{os}' w jakiejs karcie glosu")
            self.assertEqual(len(wartosci), len(set(wartosci)),
                             f"os '{os}' powtarza sie miedzy postaciami")

    def test_zrodlo_glosu_nie_uczy_wyceny(self):
        """Karta glosu jest jedynym zrodlem glosu, wiec nie moze zawierac slownika wyceny."""
        for path in sorted(VOICES.glob("*.yaml")):
            trafienia = voice_check.REJESTR_WYCENY.findall(path.read_text(encoding="utf-8-sig"))
            self.assertEqual(trafienia, [], f"{path.name} uczy rejestru wyceny: {trafienia}")

    def test_karty_kesza_i_seraphiny_nie_kaza_wyceniac(self):
        """Bezposredni dlug z reklamacji 2026-09-09 - te dwie linie kazaly wprost wyceniac."""
        kesz = load(CARDS / "rovan-kesz.yaml")
        sera = load(CARDS / "seraphine-vale.yaml")
        self.assertNotIn("Wycenia, nie bramkuje", " ".join(kesz["speech_traits"]))
        self.assertNotIn("nazywa CENE tej rzeczy", " ".join(sera["speech_traits"]))


class DigestOrderTest(unittest.TestCase):
    def test_glos_stoi_przed_danymi_w_skrocie(self):
        for path in sorted(DIGESTS.glob("*.yaml")):
            digest = load(path)
            klucze = list(digest)
            self.assertIn(klucze[0], ("voice_ref", "voice_missing"),
                          f"{path.name}: glos nie jest pierwszy w skrocie karty")
            if "voice" in digest:
                self.assertNotIn("speech_traits", digest,
                                 f"{path.name}: dwa zrodla glosu naraz - wygra dluzsze")
                self.assertLess(klucze.index("voice"), klucze.index("knowledge"))

    def test_knowledge_mowi_o_sobie_ze_jest_danymi(self):
        for path in sorted(DIGESTS.glob("*.yaml")):
            knowledge = load(path).get("knowledge") or {}
            self.assertIn("register_note", knowledge, f"{path.name}: brak noty o rejestrze")
            self.assertIn("NIE PROBKA MOWY", knowledge["register_note"])

    def test_wersaliki_w_skrocie_sa_wygaszone(self):
        """Krzyk protokolu jest najgloniejszym sygnalem stylu w aktywnym kontekscie."""
        wersaliki = re.compile(r"(?<!\w)[A-ZĄĆĘŁŃÓŚŹŻ]{4,}(?!\w)")
        for path in sorted(DIGESTS.glob("*.yaml")):
            for wpis in (load(path).get("knowledge") or {}).get("recent_confirmed") or []:
                trafienia = wersaliki.findall(str(wpis.get("claim") or ""))
                self.assertEqual(trafienia, [],
                                 f"{path.name}: wersaliki w claim: {trafienia[:5]}")

    def test_gaszenie_nie_rusza_tresci_ani_identyfikatorow(self):
        wejscie = ("NAJZIMNIEJSZY WNIOSEK tej sceny (retcon_000040). Kesz dolozyl "
                   "fact_kesz_priced_representation. NIEUSTALONE: termin.")
        wyjscie = build_npc_digests.wygas_wersaliki(wejscie)
        self.assertIn("retcon_000040", wyjscie)
        self.assertIn("fact_kesz_priced_representation", wyjscie)
        self.assertIn("Najzimniejszy wniosek", wyjscie)
        self.assertIn("Nieustalone", wyjscie)
        self.assertEqual(len(wyjscie.split()), len(wejscie.split()))


class ProseContractTest(unittest.TestCase):
    def test_literalna_rozmowa_o_pieniadzach_przechodzi(self):
        """Bramka nie moze byc zakazem slow - scena u wagi MA byc o kwotach."""
        literalne = [
            "Dwanascie srebra za partie, nie za sztuke. Kwota jest jedna i nie bede jej powtarzal.",
            "Honorarium placi kto inny, wiec cena tej rozmowy nie jest twoja sprawa - powiedzial "
            "i podal kwote w srebrze.",
        ]
        for text in literalne:
            self.assertLessEqual(prose_check.zmierz(text)["wyceny_metaforyczne"],
                                 prose_check.LIMIT_WYCEN, text[:50])

    def test_wycenianie_decyzji_jest_lapane(self):
        metaforyczne = (
            "Wycenil natomiast obie drogi. Pokazal, ile ta decyzja kosztuje, i nazwal wartosc "
            "tego, co Lucan wlasnie oddal. Uzasadnil rachunkiem, nie sumieniem."
        )
        pomiar = prose_check.zmierz(metaforyczne)
        self.assertGreater(pomiar["wyceny_metaforyczne"], prose_check.LIMIT_WYCEN)

    def test_kwestia_wprost_liczy_zdanie_a_nie_slowo_w_cudzyslowie(self):
        cytowane_slowo = 'Przy garbarni nie powiedzial "nie da sie" ani razu.'
        self.assertEqual(prose_check.zmierz(cytowane_slowo)["dialog_wprost"], 0)
        kwestia = '— Nazwisko urzednika. Bez nazwiska nie mam tego gdzie zaniesc.'
        self.assertGreaterEqual(prose_check.zmierz(kwestia)["dialog_wprost"], 1)

    def test_commit_odmawia_prozy_z_wycenianiem(self):
        import gm_runtime
        zla = {"prose": ("Wycenil obie drogi i powiedzial, ile ta decyzja kosztuje. "
                         "Potem nazwal wartosc tego, co dostal, i domknal rachunek.")}
        # gm_runtime ma WLASNA klase RuntimeError(ValueError), nie wbudowana - test na
        # wbudowana przechodzil by falszywie tylko dlatego, ze wyjatek sie nie zgadza.
        with self.assertRaises(gm_runtime.RuntimeError):
            gm_runtime.validate_prose_contract(zla)

    def test_commit_ostrzega_o_braku_dialogu(self):
        import gm_runtime
        ostrzezenia = gm_runtime.validate_prose_contract({
            "prose": ("Powiedzial, ze nie wezmie tego bez nazwiska. Dodal, ze termin "
                      "wyznaczy urzednik, i zapytal, kto to podpisze.")
        })
        self.assertTrue(any("kwestii wprost" in o for o in ostrzezenia), ostrzezenia)

    def test_prosta_narracja_z_dialogiem_przechodzi_bez_uwag(self):
        import gm_runtime
        dobra = {"prose": ("Kesz odlozyl piero i nie podniosl glowy.\n"
                           "— Nazwisko urzednika. Bez niego nie mam tego gdzie zaniesc.")}
        self.assertEqual(gm_runtime.validate_prose_contract(dobra), [])


class BlindTestFixtureTest(unittest.TestCase):
    """TEST NA SLEPO. Cztery postacie, ta sama informacja, imiona zakryte."""

    def setUp(self) -> None:
        self.fixture = load(FIXTURE)
        self.answers = self.fixture["answers"]
        self.lines = [a["line"] for a in self.answers]

    def test_fikstura_nie_udaje_kanonu(self):
        self.assertFalse(self.fixture.get("canon", True))
        self.assertEqual(len(self.answers), 4)
        self.assertEqual(
            {a["npc_id"] for a in self.answers},
            {"npc_rovan_kesz", "npc_seraphine_vale", "npc_neris_aldhen", "npc_varkhen_mind"},
        )

    def test_kazda_odpowiedz_jest_kwestia_a_nie_opisem(self):
        """Probka ma byc dialogiem, nie zdaniem 'Kesz ocenil ryzyko'."""
        for a in self.answers:
            self.assertNotRegex(a["line"], r"(?i)\b(ocenil|wycenil|uzasadnil|policzyl)\b")
            self.assertLess(len(a["line"]), 260, f"{a['npc_id']}: kwestia za dluga")

    def test_co_najmniej_trzy_z_czterech_bez_rodziny_ceny(self):
        czyste = [a["npc_id"] for a in self.answers if not RODZINA_CENY.search(a["line"])]
        self.assertGreaterEqual(len(czyste), 3,
                                f"tylko {len(czyste)} kwestie bez slownika ceny: {czyste}")

    def test_nie_wszyscy_uzywaja_szablonu_nie_X_tylko_Y(self):
        z_szablonem = [a["npc_id"] for a in self.answers
                       if prose_check.SZABLON_NIE_TYLKO.search(a["line"])]
        self.assertLessEqual(len(z_szablonem), 1,
                             f"szablon 'nie X, tylko Y' u {len(z_szablonem)} postaci: {z_szablonem}")

    def test_glosy_roznia_sie_dlugoscia(self):
        """Rozny rytm ma byc widoczny w pomiarze, nie tylko w opisie."""
        dlugosci = sorted(len(line.split()) for line in self.lines)
        self.assertLessEqual(dlugosci[0], 6, "najkrotsza kwestia nie jest krotka")
        self.assertGreaterEqual(dlugosci[-1] / max(1, dlugosci[0]), 3.0,
                                f"wszystkie kwestie sa tej samej dlugosci: {dlugosci}")

    def test_kazda_odpowiedz_ma_uzasadnienie_rozpoznania(self):
        for a in self.answers:
            self.assertTrue(str(a.get("why_it_is_him") or a.get("why_it_is_her") or "").strip(),
                            f"{a['npc_id']}: brak 'po czym go poznac'")


class RuleReachableTest(unittest.TestCase):
    def test_regula_jest_osiagalna_z_triggera(self):
        """always_load ma sufit 12 KB, wiec regula jedzie triggerem, a jej rdzen skrotem."""
        active = load(ACTIVE)
        warunkowe = [ref for key, refs in active.items()
                     if key.startswith("load_when_") and isinstance(refs, list) for ref in refs]
        self.assertIn("system/npc-voice.md", warunkowe,
                      "regula glosu nieosiagalna z zadnego triggera - czyli martwa")

    def test_kontrakt_glosu_jedzie_w_kazdym_skrocie(self):
        """Bez tego regula zyje w pliku, ktorego narrator nie musi otworzyc."""
        import build_npc_digests as bd
        for path in sorted(DIGESTS.glob("*.yaml")):
            kontrakt = load(path).get("voice_contract")
            self.assertEqual(kontrakt, bd.KONTRAKT_GLOSU, f"{path.name}: brak kontraktu glosu")
        self.assertLess(len("".join(bd.KONTRAKT_GLOSU).encode("utf-8")), 700,
                        "kontrakt w skrocie spuchl - ma byc szesc linii, nie kolejny magazyn")

    def test_regula_zostaje_krotka(self):
        self.assertLess(RULE.stat().st_size, 6_000,
                        "kontrakt glosu spuchl - historia awarii idzie do narrator-appendix.md")

    def test_regula_odsyla_do_kart_i_testu(self):
        text = RULE.read_text(encoding="utf-8")
        for fragment in ("entities/npcs/voices/", "voice-blind-test.yaml",
                         "tools/voice_check.py", "tools/prose_check.py"):
            self.assertIn(fragment, text, f"regula nie wskazuje: {fragment}")


if __name__ == "__main__":
    unittest.main()

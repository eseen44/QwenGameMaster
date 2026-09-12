"""Testy kontraktu glosu NPC, wagi stylu w kontekscie i kontraktu prozy tury.

DLUG, KTORY TE TESTY PILNUJA. Reklamacja gracza 2026-09-09: wszystkie NPC brzmia jak ten
sam narrator i wszyscy wyceniaja kazda decyzje. retcon_000162 zakazal tego w prozie i nie
zadzialal, bo nie ruszyl zadnego ZRODLA WEJSCIOWEGO. Zmierzone:

  - `speech_traits` Kesza brzmialy "Wycenia, nie bramkuje: mowi to kosztuje tyle, nigdy nie
    da sie", a narrator POWOLYWAL SIE NA TO w audytach czterech zacommitowanych tur (240,
    242, 244, 245). Karta byla przyczyna wady, nie jej ofiara,
  - w skrocie karty Kesza `knowledge` w rejestrze protokolu audytowego wazylo 8 343 B przy
    400 B `speech_traits`; model imituje rejestr dominujacy w kontekscie,
  - `outcome.prose` nie mialo kontraktu w ogole, a `gm recent` podaje je nastepnej sesji
    jako JEDYNA probke jezyka: tury 236-248 to 13 wpisow autorskich, ZERO kwestii wprost
    i 20 konstrukcji "powiedzial, ze...",
  - `outcome.new_decision` bylo w szablonie polem obowiazkowym, wiec kazda tura musiala
    wyprodukowac nowy dylemat - a najtanszy dylemat produkuje sie cudza przenikliwoscia.

Testy nie oceniaja gustu. Sprawdzaja maszynowo to, co da sie sprawdzic: pokrycie kontraktow,
rozroznialnosc osi, wage stylu wobec archiwum wiedzy, zachowanie faktow, obecnosc kontraktu
w AKTYWNYM briefie, obie bramki prozy oraz fikstury testu na slepo.
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

import build_npc_digests as digests    # noqa: E402
import gm_runtime                      # noqa: E402
import prose_check                     # noqa: E402
import voice_check                     # noqa: E402

CARDS = ROOT / "campaigns" / "lucan" / "entities" / "npcs"
VOICES = CARDS / "voices"
DIGESTS = CARDS / "digests"
FIXTURE = ROOT / "system" / "fixtures" / "voice-blind-test.yaml"
RULE = ROOT / "system" / "npc-voice.md"
ACTIVE = ROOT / "campaigns" / "lucan" / "context" / "active.yaml"
CAMPAIGN = ROOT / "campaigns" / "lucan"

RODZINA_CENY = re.compile(
    r"(?iu)\b(cen[aeyoęą]\w*|wycen\w*|koszt\w*|wartoś\w*|rachun\w*|opłacal\w*|oplacal\w*)\b"
)


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}


class VoiceContractTest(unittest.TestCase):
    def test_kontrola_glosow_przechodzi(self):
        problemy, liczby = voice_check.check()
        self.assertEqual(problemy, {}, f"voice_check zglasza: {problemy}")
        self.assertGreaterEqual(liczby["kontraktow"], 7)

    def test_kazdy_wazny_npc_ma_kontrakt(self):
        for stem in voice_check.wymagane():
            self.assertTrue((VOICES / f"{stem}.yaml").exists(),
                            f"{stem} jest wazna postacia bez kontraktu glosu")

    def test_wszystkie_osie_obecne_i_rozne(self):
        """Os powtorzona miedzy postaciami to jeden glos w kilku plikach."""
        for os_ in voice_check.OSIE:
            wartosci = [voice_check.normalizuj(voice_check.kontrakt(load(p)).get(os_))
                        for p in sorted(VOICES.glob("*.yaml"))]
            self.assertTrue(all(wartosci), f"pusta os '{os_}' w jakims kontrakcie")
            self.assertEqual(len(wartosci), len(set(wartosci)),
                             f"os '{os_}' powtarza sie miedzy postaciami")

    def test_osie_pokrywaja_zamowione_wymiary(self):
        for wymiar in ("sentences", "answer_length", "register", "evasion", "body",
                       "mistakes", "unnoticed", "emotion", "blind_spot", "money", "avoid"):
            self.assertIn(wymiar, voice_check.OSIE)

    def test_zrodlo_glosu_nie_uczy_wyceny_poza_polem_avoid(self):
        for path in sorted(VOICES.glob("*.yaml")):
            osie = voice_check.kontrakt(load(path))
            pozytywne = {k: v for k, v in osie.items() if k != voice_check.OS_NEGATYWNA}
            trafienia = voice_check.REJESTR_WYCENY.findall(
                yaml.safe_dump(pozytywne, allow_unicode=True))
            self.assertEqual(trafienia, [], f"{path.name} uczy rejestru wyceny: {trafienia}")

    def test_probki_sa_kwestiami(self):
        for path in sorted(VOICES.glob("*.yaml")):
            probki = load(path).get("samples") or []
            self.assertTrue(2 <= len(probki) <= 4, f"{path.name}: {len(probki)} probek")
            imie = load(CARDS / path.name).get("name") if (CARDS / path.name).exists() else None
            for probka in probki:
                powod = voice_check.probka_jest_opisem(str(probka), imie)
                self.assertIsNone(powod, f"{path.name}: {powod}: {probka}")

    def test_zadna_karta_nie_ma_drugiego_zrodla_glosu(self):
        """Bezposredni dlug: 'Wycenia, nie bramkuje' bylo cytowane w audytach czterech tur."""
        for path in sorted(VOICES.glob("*.yaml")):
            karta = CARDS / path.name
            if not karta.exists():
                continue
            card = load(karta)
            self.assertNotIn("speech_traits", card,
                             f"{karta.name}: kontrakt glosu I speech_traits naraz")
            self.assertTrue(card.get("voice_ref"), f"{karta.name}: brak wskaznika na kontrakt")

    def test_piec_zamowionych_kart_ma_kontrakt(self):
        for stem in ("rovan-kesz", "seraphine-vale", "neris-aldhen", "varkhen", "lucan-father"):
            self.assertTrue((VOICES / f"{stem}.yaml").exists(), stem)


class DigestWeightTest(unittest.TestCase):
    """WAGA STYLU. Cala diagnoza w jednej liczbie: co przewaza w tym samym kontekscie."""

    def setUp(self) -> None:
        self.skroty = {p.name: load(p) for p in sorted(DIGESTS.glob("*.yaml"))}
        self.assertTrue(self.skroty)

    def test_glos_stoi_przed_danymi(self):
        for nazwa, digest in self.skroty.items():
            klucze = list(digest)
            self.assertIn(klucze[0], ("voice_ref", "voice_missing"),
                          f"{nazwa}: glos nie jest pierwszy w skrocie")
            if "voice_contract" in digest:
                self.assertNotIn("speech_traits", digest, f"{nazwa}: dwa zrodla glosu")
                self.assertLess(klucze.index("voice_contract"), klucze.index("knowledge"))

    def test_wiedza_nie_zalewa_czesci_stylistycznej(self):
        for nazwa, digest in self.skroty.items():
            styl = (voice_check.bajty(digest.get("voice_contract"))
                    + voice_check.bajty(digest.get("voice_rules"))
                    + voice_check.bajty(digest.get("voice_samples")))
            if not styl:
                continue
            wiedza = voice_check.bajty((digest.get("knowledge") or {}).get("recent_confirmed"))
            self.assertLessEqual(wiedza / styl, voice_check.MAX_STOSUNEK,
                                 f"{nazwa}: archiwum wiedzy {wiedza} B na {styl} B kontraktu")

    def test_knowledge_mowi_o_sobie_ze_jest_danymi(self):
        for nazwa, digest in self.skroty.items():
            knowledge = digest.get("knowledge") or {}
            self.assertIn("register_note", knowledge, f"{nazwa}: brak noty o rejestrze")
            self.assertIn("NIE PROBKA MOWY", knowledge["register_note"])

    def test_wersaliki_w_skrocie_sa_wygaszone(self):
        wersaliki = re.compile(r"(?<!\w)[A-ZĄĆĘŁŃÓŚŹŻ]{4,}(?!\w)")
        for nazwa, digest in self.skroty.items():
            for wpis in (digest.get("knowledge") or {}).get("recent_confirmed") or []:
                _, tekst = digests.tekst_wpisu(wpis)
                self.assertEqual(wersaliki.findall(tekst), [], f"{nazwa}: wersaliki w tresci")

    def test_zaden_fakt_nie_ginie_bez_adresu(self):
        """Sciety wpis MUSI niesc adres calosci, a pelna karta - cala tresc."""
        for nazwa, digest in self.skroty.items():
            pelna = load(ROOT / digest["full_card"])
            pelne = {digests.etykieta_wpisu(w): digests.tekst_wpisu(w)[1]
                     for w in ((pelna.get("knowledge") or {}).get("confirmed") or [])
                     if isinstance(w, dict)}
            for wpis in (digest.get("knowledge") or {}).get("recent_confirmed") or []:
                etykieta = digests.etykieta_wpisu(wpis)
                self.assertIn(etykieta, pelne, f"{nazwa}: {etykieta} nie ma w karcie")
                if wpis.get("claim_truncated"):
                    self.assertTrue(wpis.get("claim_full"), f"{nazwa}: sciete bez adresu")
                    self.assertIn(etykieta, wpis["claim_full"])
                    _, sciety = digests.tekst_wpisu(wpis)
                    # Skrot gasi wersaliki PRZED scieciem, wiec porownujemy z tekstem
                    # karty po tym samym wygaszeniu - inaczej test mierzy dwie rzeczy.
                    wzorzec = digests.wygas_wersaliki(pelne[etykieta])
                    self.assertTrue(wzorzec.startswith(sciety[:60]),
                                    f"{nazwa}: sciecie zmienilo poczatek faktu")

    def test_indeks_starszych_faktow_ma_adresy(self):
        """Karty ze schematem {fact} zamiast {fact_id, claim} dawaly indeks samych '?'."""
        for nazwa, digest in self.skroty.items():
            indeks = (digest.get("knowledge") or {}).get("older_confirmed_index") or []
            puste = [w for w in indeks if w.startswith("?@")]
            self.assertEqual(puste, [], f"{nazwa}: {len(puste)} wpisow indeksu bez adresu")

    def test_oba_schematy_wiedzy_obsluzone(self):
        """18 kart pisze {fact_id, claim}, 6 pisze {fact}. Oba musza dzialac."""
        self.assertEqual(digests.tekst_wpisu({"claim": "x"}), ("claim", "x"))
        self.assertEqual(digests.tekst_wpisu({"fact": "y"}), ("fact", "y"))
        self.assertTrue(digests.etykieta_wpisu({"fact": "Widziala zywy okaz"}).startswith("~"))
        self.assertEqual(digests.etykieta_wpisu({"fact_id": "fact_x"}), "fact_x")

    def test_scinanie_konczy_na_granicy_zdania(self):
        claim = "Fakt pierwszy jest krotki. " + ("Ogon protokolu tury. " * 40)
        tekst, ucieto = digests.utnij_claim(claim, cap=120)
        self.assertTrue(ucieto)
        self.assertTrue(tekst.endswith("."), tekst)
        self.assertTrue(claim.startswith(tekst))

    def test_skroty_sa_aktualne(self):
        pliki = digests.build(digests.RECENT_DEFAULT)
        stare = [p.name for p, body in pliki.items()
                 if not p.exists() or p.read_text(encoding="utf-8") != body]
        self.assertEqual(stare, [], f"skroty nieaktualne: {stare}")


class BriefTest(unittest.TestCase):
    """Kontrakt glosu musi trafic do AKTYWNEGO briefu, nie tylko istniec na dysku."""

    def setUp(self) -> None:
        self.brief = gm_runtime.session_brief(CAMPAIGN, full=False)
        self.npc = [p for p in self.brief["participants"]
                    if str(p.get("id", "")).startswith("npc")]

    def test_brief_ma_uczestnikow_npc(self):
        # Scena moze LEGALNIE nie miec NPC - t_274 zostawil Lucana w baszcie z dwoma
        # konstruktami. Wtedy nie ma czego sprawdzac i trzeba to powiedziec wprost,
        # zamiast trzymac czerwien, ktora twierdzi, ze brief jest zepsuty.
        if not self.npc:
            self.skipTest("biezaca scena nie ma uczestnikow NPC - nie ma czego sprawdzic")
        self.assertTrue(self.npc)

    def test_kazdy_npc_w_briefie_ma_wskaznik_glosu(self):
        for p in self.npc:
            self.assertIn("voice_ref", p, f"{p['id']}: brief nie podaje kontraktu glosu")
            self.assertTrue((ROOT / p["voice_ref"]).is_file(), p["voice_ref"])

    def test_wskazany_kontrakt_ma_osie_i_probki(self):
        for p in self.npc:
            voice = load(ROOT / p["voice_ref"])
            osie = voice_check.kontrakt(voice)
            for os_ in voice_check.OSIE:
                self.assertTrue(osie.get(os_), f"{p['id']}: brak osi {os_}")
            self.assertTrue(voice.get("samples"))

    def test_skrot_z_briefu_niesie_kontrakt_i_reguly(self):
        for p in self.npc:
            if "digest_ref" not in p:
                continue
            digest = load(ROOT / p["digest_ref"])
            self.assertIn("voice_contract", digest, f"{p['id']}: skrot bez kontraktu")
            self.assertEqual(digest.get("voice_rules"), digests.REGULY_GLOSU)
            self.assertIn("gest", " ".join(digest["voice_rules"]).lower(),
                          "menu ruchow swiata nie jedzie w skrocie karty")


class ProseContractTest(unittest.TestCase):
    def test_literalna_rozmowa_o_pieniadzach_przechodzi(self):
        """Bramka nie moze byc zakazem slow - scena u wagi MA byc o kwotach."""
        for text in [
            "Dwanascie srebra za partie, nie za sztuke. Kwota jest jedna i nie powtorze jej.",
            "Honorarium placi kto inny, wiec cena tej rozmowy nie jest twoja sprawa - "
            "i podal kwote w srebrze.",
        ]:
            self.assertLessEqual(prose_check.zmierz(text)["wyceny_metaforyczne"],
                                 prose_check.LIMIT_WYCEN, text[:50])

    def test_wycenianie_decyzji_jest_lapane(self):
        pomiar = prose_check.zmierz(
            "Wycenil natomiast obie drogi. Pokazal, ile ta decyzja kosztuje, i nazwal "
            "wartosc tego, co Lucan wlasnie oddal.")
        self.assertGreater(pomiar["wyceny_metaforyczne"], prose_check.LIMIT_WYCEN)

    def test_kwestia_wprost_liczy_zdanie_a_nie_slowo_w_cudzyslowie(self):
        self.assertEqual(prose_check.zmierz(
            'Przy garbarni nie powiedzial "nie da sie" ani razu.')["dialog_wprost"], 0)
        self.assertGreaterEqual(prose_check.zmierz(
            "— Nazwisko urzednika. Bez niego nie mam tego gdzie zaniesc.")["dialog_wprost"], 1)

    def test_commit_odmawia_prozy_z_wycenianiem(self):
        # gm_runtime ma WLASNA klase RuntimeError(ValueError), nie wbudowana.
        with self.assertRaises(gm_runtime.RuntimeError):
            gm_runtime.validate_prose_contract({"prose": (
                "Wycenil obie drogi i powiedzial, ile ta decyzja kosztuje. Potem nazwal "
                "wartosc tego, co dostal, i domknal rachunek.")})

    def test_commit_odmawia_rozmowy_streszczonej_w_calosci(self):
        with self.assertRaises(gm_runtime.RuntimeError) as ctx:
            gm_runtime.validate_prose_contract({"prose": (
                "Powiedzial, ze nie wezmie tego bez nazwiska. Dodal, ze termin wyznaczy "
                "urzednik. Zapytal, kto to podpisze, i odnotowal, czego nie uslyszal.")})
        self.assertIn("kwestii wprost", str(ctx.exception))

    def test_dwie_parafrazy_jeszcze_przechodza_z_uwaga(self):
        """Prog jest trzy, nie jedna - skracanie powtorzen ma zostac legalne."""
        ostrzezenia = gm_runtime.validate_prose_contract({"prose": (
            "Powiedzial, ze nie wezmie tego bez nazwiska. Dodal, ze termin wyznaczy urzednik.")})
        self.assertTrue(any("kwestii wprost" in o for o in ostrzezenia), ostrzezenia)

    def test_narracja_z_jedna_kwestia_przechodzi_bez_uwag(self):
        self.assertEqual(gm_runtime.validate_prose_contract({"prose": (
            "Kesz odlozyl pioro i nie podniosl glowy.\n"
            "— Nazwisko urzednika. Bez niego nie mam tego gdzie zaniesc.")}), [])

    def test_tura_bez_rozmowy_przechodzi(self):
        """Podroz i czynnosc fizyczna nie maja kwestii i nie moga byc za to blokowane."""
        self.assertEqual(gm_runtime.validate_prose_contract({"prose": (
            "Droga przez Lumarie zajela dwadziescia minut. O tej porze miasto sklada "
            "stragany i nikt nie patrzy na czlowieka w plaszczu.")}), [])


class WorldMoveTest(unittest.TestCase):
    """Presja na przenikliwosc byla w SZABLONIE, nie w modelu."""

    def test_new_decision_nie_jest_polem_obowiazkowym(self):
        szablon = load(ROOT / "templates" / "journal" / "turn-outcome.yaml")
        self.assertIsNone(szablon.get("new_decision"),
                          "szablon znowu zada nowego punktu decyzji w kazdej turze")

    def test_commit_nie_wymaga_new_decision(self):
        gm_runtime.validate_outcome({
            "intent_achieved": True, "arrangement": "unchanged",
            "perspective": "instance_actor", "summary": "x", "operations": [],
        })

    def test_puste_new_decision_zostawia_pytanie_w_mocy(self):
        zrodlo = (TOOLS / "gm_runtime.py").read_text(encoding="utf-8")
        self.assertIn('if outcome.get("new_decision"):', zrodlo,
                      "commit nadpisuje immediate_questions bezwarunkowo")

    def test_menu_ruchow_swiata_jest_w_regule_i_w_skrocie(self):
        tekst = RULE.read_text(encoding="utf-8")
        for ruch in ("gest", "milczenie", "zmiana tematu", "emocja bez analizy",
                     "częściowe niezrozumienie", "błędny odczyt"):
            self.assertIn(ruch, tekst, f"menu ruchow swiata nie ma pozycji: {ruch}")
        reguly = " ".join(digests.REGULY_GLOSU).lower()
        self.assertIn("nie jest wymagana", reguly,
                      "reguly w skrocie nie mowia, ze diagnoza gracza nie jest obowiazkowa")


class BlindTestFixtureTest(unittest.TestCase):
    """TEST NA SLEPO. Ta sama wypowiedz Lucana, rozne glosy, imiona zakryte."""

    def setUp(self) -> None:
        self.fixture = load(FIXTURE)
        self.cases = self.fixture["cases"]

    def test_fikstura_nie_udaje_kanonu(self):
        self.assertFalse(self.fixture.get("canon", True))
        self.assertGreaterEqual(len(self.cases), 2)

    def test_zamowiona_czworka_jest_w_pierwszym_przypadku(self):
        ids = {a["npc_id"] for a in self.cases[0]["answers"]}
        self.assertEqual(ids, {"npc_rovan_kesz", "npc_seraphine_vale",
                               "npc_neris_aldhen", "npc_varkhen_mind"})

    def test_ojciec_jest_w_drugim_przypadku(self):
        self.assertIn("npc_lucan_father", {a["npc_id"] for a in self.cases[1]["answers"]})

    def test_kazdy_glos_ma_kontrakt(self):
        npc_do_pliku = {load(p).get("npc_id") for p in VOICES.glob("*.yaml")}
        for case in self.cases:
            for a in case["answers"]:
                self.assertIn(a["npc_id"], npc_do_pliku, a["npc_id"])

    def test_odpowiedzi_sa_kwestiami_a_nie_opisami(self):
        imiona = {load(p).get("npc_id"): load(CARDS / p.name).get("name")
                  for p in VOICES.glob("*.yaml") if (CARDS / p.name).exists()}
        for case in self.cases:
            for a in case["answers"]:
                powod = voice_check.probka_jest_opisem(a["line"], imiona.get(a["npc_id"]))
                self.assertIsNone(powod, f"{a['npc_id']}: {powod}")
                self.assertLess(len(a["line"]), 300, f"{a['npc_id']}: kwestia za dluga")

    def test_wiekszosc_bez_rodziny_ceny(self):
        for case in self.cases:
            czyste = [a["npc_id"] for a in case["answers"]
                      if not RODZINA_CENY.search(a["line"])]
            wymagane = len(case["answers"]) - max(1, len(case["answers"]) // 4)
            self.assertGreaterEqual(len(czyste), wymagane,
                                    f"{case['id']}: tylko {len(czyste)} bez slownika ceny")

    def test_nie_wszyscy_uzywaja_szablonu_nie_X_tylko_Y(self):
        for case in self.cases:
            z_szablonem = [a["npc_id"] for a in case["answers"]
                           if prose_check.SZABLON_NIE_TYLKO.search(a["line"])]
            self.assertLessEqual(len(z_szablonem), 1,
                                 f"{case['id']}: szablon u {len(z_szablonem)} postaci")

    def test_glosy_roznia_sie_dlugoscia_i_otwarciem(self):
        for case in self.cases:
            dlugosci = sorted(len(a["line"].split()) for a in case["answers"])
            self.assertLessEqual(dlugosci[0], 6, f"{case['id']}: brak krotkiej kwestii")
            self.assertGreaterEqual(dlugosci[-1] / max(1, dlugosci[0]), 3.0,
                                    f"{case['id']}: kwestie tej samej dlugosci: {dlugosci}")
            pierwsze = [a["line"].split()[0].lower().strip(",.:-") for a in case["answers"]]
            self.assertEqual(len(pierwsze), len(set(pierwsze)),
                             f"{case['id']}: dwie kwestie zaczynaja sie tym samym slowem")

    def test_kazda_odpowiedz_ma_uzasadnienie_rozpoznania(self):
        for case in self.cases:
            for a in case["answers"]:
                powod = a.get("why_it_is_him") or a.get("why_it_is_her") or ""
                self.assertTrue(powod.strip(), f"{a['npc_id']}: brak 'po czym go poznac'")


class RuleReachableTest(unittest.TestCase):
    def test_regula_jest_osiagalna_z_triggera(self):
        """always_load ma sufit 12 KB, wiec regula jedzie triggerem, a jej rdzen skrotem."""
        active = load(ACTIVE)
        warunkowe = [ref for key, refs in active.items()
                     if key.startswith("load_when_") and isinstance(refs, list) for ref in refs]
        self.assertIn("system/npc-voice.md", warunkowe, "regula glosu nieosiagalna")

    def test_reguly_glosu_jada_w_kazdym_skrocie(self):
        for path in sorted(DIGESTS.glob("*.yaml")):
            self.assertEqual(load(path).get("voice_rules"), digests.REGULY_GLOSU, path.name)
        self.assertLess(len("".join(digests.REGULY_GLOSU).encode("utf-8")), 1200,
                        "reguly w skrocie spuchly - to ma byc szkielet, nie magazyn")

    def test_regula_zostaje_krotka(self):
        self.assertLess(RULE.stat().st_size, 8_000, "kontrakt glosu spuchl")

    def test_regula_odsyla_do_kart_i_testu(self):
        text = RULE.read_text(encoding="utf-8")
        for fragment in ("entities/npcs/voices/", "voice-blind-test.yaml",
                         "tools/voice_check.py", "tools/prose_check.py"):
            self.assertIn(fragment, text, f"regula nie wskazuje: {fragment}")


if __name__ == "__main__":
    unittest.main()

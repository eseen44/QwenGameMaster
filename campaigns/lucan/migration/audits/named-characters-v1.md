# Audyt nazwanych postaci — v1

Status: roboczy materiał migracyjny. Historia służy jako źródło scen testowych; liczby są kalibracją systemu 0–100, a nie rekonstrukcją ukrytych statystyk z dawnych rzutów.

## Reguła ciężaru karty

- `full_agent`: postać podejmuje decyzje albo ma możliwości, które samodzielnie zmieniają przebieg sceny. Otrzymuje kartę wiedzy oraz pełny obiekt mechaniczny.
- `specialist`: postać nie jest dominującym bojownikiem, lecz jej wiedza, stanowisko albo odporność były istotne. Otrzymuje kartę wiedzy i — gdy potrzebne do replayu — obiekt mechaniczny.
- `light_named`: nazwana postać sceniczna. Zachowujemy tożsamość, stan, wiedzę i źródła, ale korzysta ze wspólnego archetypu człowieka zamiast fałszywej precyzji.
- `excluded_from_npc`: Lucan oraz kontrolowane byty mają własne działy; nienazwane role pozostają fixture'ami scen.

## Pełni agenci

| Postać | Rola | Stan przy granicy | Dlaczego pełny obiekt |
|---|---|---|---|
| Mara Teln | C-rank ranger/zwiadowca | żyje, komora Varkhena | wielokrotnie walczy, zwiaduje, ocenia ryzyko i zna część sekretów Lucana |
| Boros Keld | C-rank frontliner | żyje, dociska Varkhena | fizycznie rozwiązuje przeszkody, utrzymuje linię i tworzy przewagi dla innych |
| Seraphine Vale | A-rank kontroler/antymag | żyje, uczestniczy w operacji | dowodzi, rozbija rytuały, kontroluje eskalację i precyzyjnie interweniuje w walce |
| Oren | nekromanta i operator systemu cmentarza | martwy | trzy dekady utrzymywał logistykę oraz więź z sercem; jego słabość napędza finał łuku |
| Varkhen | starożytny nieumarły strażnik | przejęty i skrajnie wyczerpany | przeciwnik klasy B, którego nie dało się pokonać bez kumulacji przewag |

## Specjaliści i istotni świadkowie

| Postać | Rola | Stan | Model |
|---|---|---|---|
| Halven Rusk | miejski inspektor podziemi | żyje | pełny obiekt specjalisty; fizycznie zwykły człowiek, w swojej dziedzinie D |
| Darrik | główny grabarz | martwy | pełny cel kalibracyjny dla Numb, drenu i Spideya; nie jest wojownikiem |

## Lekkie nazwane rekordy

| Postać | Rola | Stan | Uzasadnienie |
|---|---|---|---|
| Teren | pomocnik kaplicy | zabity przez Spideya | ważne źródło informacji i ofiara, lecz brak ponadprzeciętnych zdolności |
| Marael | opiekunka kaplicy | zabita przez Spideya | istotna wiedza i pozycja społeczna, mechanicznie zwykły człowiek |
| Odran | dozorca murów i odpływów | nieustalony | nazwany kontakt techniczny; brak potwierdzonej sceny działania |
| Halvek | człowiek z transportu zwłok | schwytany | nazwany mook; osobna karta tylko po to, by nie zgubić jego stanu i wiedzy |

## Poza indeksem NPC

- Lucan Veyr: postać gracza.
- Spidey, Anchored i pozostałe sieciarze: kontrolowane byty.
- młody zarządca wysyłki, mag ognia, ekspert rytualny, dwaj B-rankowie Seraphine, właściciel garbarni, strażnicy i robotnicy: istotne, lecz nienazwane role. Do replayu używają fixture'ów/archetypów i nie dostają wymyślonych imion.
- `Veyr` w dialogach jest nazwiskiem Lucana, nie imieniem maga ognia.
- `Sokrates` i `Finarus` nie są NPC kampanii; pierwsze jest żartem/odniesieniem historycznym, drugie nazwą lasu.

## Pokrycie źródłowe

- Mara, Boros, Rusk: `source_luka_b_fragment#line:317-606` i dalsze sceny garbarni/cmentarza.
- Darrik: `source_luka_b_fragment#line:3107-3435`.
- Teren, Marael, Odran: `source_luka_b_fragment#line:5351-7298`.
- Halvek: `source_luka_b_fragment#line:7800-8290`.
- Seraphine: `source_luka_b_fragment#line:6812-6921` oraz `line:8334-11409`.
- Oren: `source_luka_b_fragment#line:7734-11173`.
- Varkhen: `source_luka_b_fragment#line:11207-11409`.

## Granice kalibracji

- Ranga operacyjna nie jest średnią statystyk.
- Wartości Seraphine na poziomie A dotyczą kontroli magii i precyzji, nie odporności ludzkiego czołgu.
- Oren ma wysoki wąski kanał systemów nekromantycznych, lecz ludzkie ciało i krytyczną zależność od serca.
- Mara i Boros pozostają C-rankami o różnych profilach, a Rusk jest D-rankowym specjalistą w ciele zwykłego człowieka.
- Lekkie rekordy dziedziczą archetyp `fixture_human`; nie tworzymy im indywidualnych punktów tylko dlatego, że znamy imię.

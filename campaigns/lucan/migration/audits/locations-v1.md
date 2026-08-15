# Audyt lokacji i map — v1

Status: roboczy materiał migracyjny. Układ połączeń jest autorytatywnym kandydatem do replayu; wymiary oznaczone `estimated` służą orientacji i mogą zostać poprawione bez retconowania wydarzeń.

## Główne lokacje kampanii

| Lokacja | Zakres | Mapa MG | Mapa gracza | Najważniejszy test |
|---|---|---:|---:|---|
| Wysypisko Lumarii | hałdy, wejście, miejsce ofiar, posterunek sieci | tak | tak | widoczność, zasadzka Spideya, odwrót |
| Garbarnia | podwórze, hala, kantor, właz | tak | tak | obserwacja pracowników, włamanie, dojście do kopca |
| Kopiec pod garbarnią | archiwum, Komora III, laboratorium, jaskinie, kolonia, odpływy | tak | tak | wąskie gardła, ogień, rat-ogre, alternatywne wyjścia |
| Opuszczona baszta | izba, składzik, warsztat, wyjście na mur | tak | tak | pojemność kryjówki, wejścia i ukrywanie sług |
| Cmentarz Lumarii | mur, kaplica, groby, rampa, osuwisko | tak | tak | czas obchodzenia, drogi wejścia i ewakuacja |
| Kaplica cmentarna | nawa, ołtarz, zakrystia, schody | tak | tak | linie widzenia, atak Spideya, droga do podziemi |
| Podziemny system cmentarza | rampa wozu, magazyny, krypty, kolektor, przekaźnik, serce | tak | tak | zasadzka na wóz, zamykane przejścia, przeciążenie systemu |
| Komora Varkhena | osuwisko, liny, drzwi, sarkofag | tak | tak | kumulowanie przewag i jedyna droga odwrotu |

## Świadomie pominięte osobne mapy

- Gildia, koszary, cela i tawerna pozostają lokacjami społecznymi bez utrwalonej geometrii. W historii nie było decyzji, której sens zależał od ich planu.
- Pierwsza piwniczna kryjówka jest połączeniem kopca, nie odrębnym aktywnym hubem po przenosinach do baszty.
- Serce i najstarsze mauzoleum są strefą podziemnego systemu cmentarza. Osobna mapa dublowałaby ten sam układ.

## Zasada widoczności

- `gm.svg` może pokazać strefy z `player_visible: false`.
- `player.svg` nie zawiera ich stabilnych identyfikatorów ani geometrii.
- Po granicy kanonu mapa gracza zna logistykę, kolektor, serce i dojście do Varkhena, bo Lucan osobiście uczestniczył w ich odkryciu.
- Niekanoniczne informacje z późniejszej rozmowy z Varkhenem nie zostały naniesione.

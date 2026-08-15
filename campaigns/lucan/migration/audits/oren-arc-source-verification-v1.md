# Weryfikacja łuku Orena — v1

Data: 2026-08-15  
Zakres: od przeciążenia północno-zachodniego kolektora do śmierci Orena, przed wejściem do komory Varkhena.

## Źródła sprawdzone

- `sources/normalized/historical-full-run.utf8.txt`, linie 11180–12860: scalony, zdeduplikowany przebieg.
- `sources/raw/luka_B.txt`, linie 9500–11173: bezpośredni zapis tej sceny.
- `sources/raw/In_Character.txt`, linie 1811–1819: późniejsze streszczenie stanu; nie ustanawia faktów samodzielnie, ale potwierdza status Orena jako jawnego zdarzenia.
- `sources/raw/luka_A.txt`: nie wnosi niezależnego, sprzecznego opisu tej sceny.

## Wynik porównania

| Teza | Wynik | Podstawa |
|---|---|---|
| Nazwa postaci brzmi `Oren`. | potwierdzone | Wszystkie wystąpienia w luka_B oraz streszczenie In_Character używają `Oren`; `Orin` nie występuje. |
| Odcięcie odpływu z kolektora poprzedza poważne ożywienie zwłok. | potwierdzone | luka_B 8900–9500. |
| B-rankerzy ograniczają zagrożenie w obrębie cmentarza. | potwierdzone | luka_B 9913, 10569, 10591. Nie ma dosłownego potwierdzenia osobnej akcji ewakuacyjnej w mieście. |
| Wejście pod kaplicę prowadzi do przekaźnika mówiącego „Oren kazał czekać”. | potwierdzone | luka_B 9654–9881. |
| Oren jest operatorem systemu, lecz jest też uwięziony w pasożytniczej więzi z cmentarnym źródłem. | potwierdzone | luka_B 10427–10443. |
| Źródło kieruje się ku Orenowi; grupa wraca na powierzchnię dla przestrzeni, B-rankerów i kordonu. | potwierdzone | luka_B 10337–10591. |
| Duch cmentarza rozpoznaje Orena jako swoją własność/brakującą część obiegu. | potwierdzone | luka_B 10807–10922. |
| Lucan paraliżuje Orena i próbuje zabić go nożem; Seraphine blokuje pierwszy cios. | potwierdzone | luka_B 10994–11050. |
| Po kontrolowanej próbie Seraphine wybiera humanitarne zabicie Orena; Lucan pobiera minimalną próbkę sygnatury. | potwierdzone | luka_B 11103–11165. |

## Wniosek dla migracji

Pakiet chronologii rozdziela scenę na cztery kamienie: reakcję i zejście pod kaplicę (`043b`), ujawnienie więzi oraz powrót na powierzchnię (`043c`), pierwszą próbę zabójstwa (`044`) i późniejsze kontrolowane zakończenie (`044b`). Nie ma konfliktu między scalonym przebiegiem a luka_B; drugi jest jego końcowym segmentem. Obecne decyzje użytkownika mają pierwszeństwo jako doprecyzowanie znaczenia sceny.

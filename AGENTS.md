# GameMaster — instrukcja uruchomieniowa

Ten projekt jest lokalnym źródłem prawdy dla kampanii RPG prowadzonej przez narratora „Mindy”. Wątek rozmowy służy do gry, ale nie zastępuje plików kampanii.

## Rola narratora

- Prowadź świat, NPC, konsekwencje i upływ czasu.
- Nie wybieraj za gracza kolejnej akcji Lucana.
- Rozstrzygnij zadeklarowaną akcję, pokaż jej konsekwencję, porusz przynajmniej jeden element świata i zakończ w konkretnym punkcie decyzji.
- Zachowuj czarny humor, zwięzłość i reaktywność, ale nie poświęcaj im spójności.

## Otwarcie sesji i koszt rozmowy

Każda tura wysyła całą dotychczasową rozmowę od nowa, więc koszt rozmowy rośnie
z kwadratem jej długości. Stan kampanii żyje w plikach, więc rozmowa jest
jednorazowa i ma być krótka.

Głównym środowiskiem prowadzenia jest zdolny narrator cloudowy z dostępem do repo
(obecnie Claude Opus High). Projektuj pracę dla modelu, który potrafi punktowo
przeszukiwać źródła, porównywać kilka plików i używać runtime'u. Nie duplikuj całego
kanonu w aktywnym kontekście ani nie upraszczaj fikcji pod słabszy model; repo ma
jednak pozostać przenośne i nie może zależeć od zachowania jednego dostawcy.

- Otwieraj sesję komendą `tools/gm.ps1 brief` — jeden blok ze sceną, czasem, zegarami, celami, uczestnikami i listą plików do wczytania. W czacie bez dostępu do dysku użyj `brief --full`, który dokleja treść tych plików.
- Zamykaj rozmowę razem ze sceną (`scene close`) i zaczynaj nową od `brief`. Nie ciągnij jednej rozmowy przez kilka scen.
- Wyjście komend `turn` i `context` jest **domyślnie skrócone** i zawiera wyłącznie decyzje. `--verbose` drukuje pełny dokument i służy do diagnozowania, nie do gry. Pełna transakcja zawsze leży w `journal/transactions/<turn_id>.yaml`.
- Nie kopiuj wyjścia narzędzi do narracji ani do kolejnych wiadomości.

Uzasadnienie i pomiary: `DECISIONS.md`.

## Kolejność wczytywania przed turą

1. Przeczytaj `campaigns/lucan/context/active.yaml`.
2. Przeczytaj `campaigns/lucan/context/scene.yaml` oraz wskazane tam pliki.
3. Wczytaj tylko uczestniczące byty, aktywne wątki i stan bieżącej lokacji.
4. Jeżeli gracz odwołuje się do przeszłości, przeszukaj `journal/`, a następnie sprawdź retcony.
5. Nie wczytuj całego dziennika bez potrzeby.
6. Do punktowego wyszukania użyj `tools/gm.ps1 recall`; nie dopisuj całego wyniku do aktywnego kontekstu.

## Interpretacja wejścia gracza

- Tekst w nawiasach jest kanałem niewidocznym z zewnątrz: rozmową z systemem, prywatną myślą Lucana albo natychmiastową decyzją, mentalnym rozkazem lub czarem niewidocznym dla innych postaci.
- Nawias nie jest słyszany w świecie i nigdy nie przesuwa czasu. Może zmienić stan wyłącznie wtedy, gdy zawiera akt wykonywany całkowicie wewnętrznie i natychmiastowo; nie zastępuje widocznego ruchu fizycznego.
- Wiadomość wyłącznie nawiasowa bez takiego aktu zatrzymuje scenę. Odpowiedz poza grą.
- Działanie świata następuje wyłącznie na podstawie deklaracji poza nawiasem lub wcześniej uruchomionego zegara.
- Natychmiastowy akt nawiasowy przekazuj do runtime jako `parenthetical_action: true`; zawsze otrzymuje `time_seconds: 0`. Patrz `system/player-agency.md`.

## Rozstrzyganie tury

1. Ustal deklarowany zamiar i podmiot ewentualnego testu.
2. Sprawdź poziom napięcia i czy mija krytyczna ilość czasu.
   Przy napięciu 0 nie wykonuj rzutu dla wykonalnej, powtarzalnej czynności. Twarda niemożliwość i wymaganie nowej dźwigni nadal obowiązują.
   Jeżeli `state/time.yaml#roll_policy.mode` ma wartość `disabled`, nie wykonuj żadnych rzutów
   niezależnie od lokalnego napięcia. Rozstrzygaj według możliwości, metody, czasu i pewnych
   kosztów. Rzuty wracają dopiero po jawnej zmianie fazy kampanii.
3. Dla działania mechanicznego przygotuj request i uruchom `tools/gm.ps1 turn resolve`; do sprawdzenia bez zapisu użyj `turn preview`.
4. Runtime stosuje `system/capabilities.md`, wykonuje najwyżej jeden potrzebny rzut i zapisuje go przed narracją.
5. Rozstrzygnij akcję, reakcję świata i nową sytuację decyzyjną.
6. Przed odpowiedzią uruchom `turn commit` z outcome; po przerwaniu użyj `turn recover` z tym samym identyfikatorem. **`outcome.operations` nie może zawierać `advance_time`** — `commit` dokleja czas sam z `request.time_seconds`, a ręczny wpis podwaja turę (retcon_000118). Godzinę podawaną graczowi czytaj z `state/time.yaml` po commicie, nie z własnej deklaracji.
7. Każda trwała tura ma `actor_id`, także automatyczna i bez testu. Samo `actor_id` nie uruchamia silnika zdolności; test mechaniczny wymaga dodatkowo `capability_id`, `target_id` i `intent_id`.
8. Przy napięciu 0 wynik `worsened`, `complicated` albo `mixed` wymaga `consequence_source_refs`: istniejącego źródła kanonicznego lub jawnej deklaracji gracza. Nie twórz stawki tylko po to, żeby tura miała komplikację.

## Aktualizacja pamięci

- Przed pierwszą turą po aktywacji przeczytaj `campaigns/lucan/FILE-LIFECYCLE.md`; jest to pełna mapa tego, kiedy plik może być zmieniony.
- Dopisz niezmienny wpis do odpowiedniego dziennika JSONL.
- Zaktualizuj wyłącznie pliki stanu, które faktycznie się zmieniły.
- Zaktualizuj wiedzę, podejrzenia i fałszywe przekonania właściwych NPC.
- Zaktualizuj czas, zegary, zasoby, reputację, lokację i odkrycia, jeżeli zostały naruszone.
- Po zmianie sceny odśwież `context/scene.yaml` i `context/active.yaml`.
- Zwykły commit odświeża kontekst automatycznie; ręczne `context refresh` jest potrzebne po zmianach administracyjnych.
- Błędu historycznego nie kasuj: dodaj retcon i popraw aktualny stan.
- **Cofnięcie tury nie usuwa ani nie nadpisuje kanonu.** Nie kasuj linii z
  `journal/events.jsonl`, nie usuwaj i nie nadpisuj plików `journal/transactions/*.yaml`.
  Ponownie rozegrana tura dostaje nowy wpis; uchylona wersja idzie do
  `journal/superseded/` przez `python tools/recover_superseded.py`.
  Sprawdza to `python tools/journal_guard.py` (wpięte w `validate_project.py`), więc reguła
  jest warunkiem, nie prośbą. Do 2026-09-04 nie było jej czym sprawdzić i pierwotna proza
  jedenastu tur przetrwała wyłącznie jako obiekty gita.

## Lokacje i mapy

- Przy pierwszym wejściu zastosuj `system/locations-and-maps.md`.
- Pokaż opis orientacyjny oraz mapę gracza, zanim zażądasz decyzji.
- `player.svg` może zawierać tylko elementy ujawnione w `discovery.yaml`.
- Geometria z `layout.yaml` ma pierwszeństwo przed obrazowym opisem narracji.

## Priorytet źródeł

1. Zatwierdzony retcon.
2. Aktualne pliki stanu kampanii i bytów.
3. Kanon świata i reguły systemu.
4. Dziennik wydarzeń.
5. Transkrypt rozmowy i pamięć modelu.

W razie konfliktu nie zgaduj. Zatrzymaj czas sceny, wskaż sprzeczność i zaproponuj korektę kanonu.

## Blokada migracji

- Jeżeli `campaigns/lucan/migration/migration.yaml` ma status zaczynający się od `blocked`, kampania nie jest gotowa do wznowienia.
- Podczas zwykłej tury nigdy nie wczytuj `migration/sources/` ani `migration/noncanonical/`.
- Pojedynczy zatwierdzony pakiet migracyjny nie jest kanonem. Aktywacja następuje dopiero atomowo po zatwierdzeniu wszystkich bieżących rewizji.

# GameMaster — TODO projektowe

## Koszt rozmowy (2026-08-17)

Diagnoza, pomiary i uzasadnienie: `DECISIONS.md`.

- [x] Skrócić domyślne wyjście CLI, zostawiając `--verbose` do diagnozowania (12 509 B → 2 016 B na turę).
- [x] Dodać `gm brief` otwierające świeżą sesję jednym blokiem, z wariantem `--full` dla czatu bez dysku.
- [x] Zabezpieczyć niezmienność rzutu przy ponowionym `resolve` po awarii.
- [x] Przestać wywalać commit przy przekroczeniu budżetu kontekstu; raportować `context_warnings` i `heaviest_refs`.
- [ ] **Rozegrać 5 tur od początku do końca przez CLI, zanim powstanie kolejna reguła systemu.** Dwa punkty niżej są bez tego zgadywaniem.
- [ ] Odchudzić stały prefiks: `inventory.brief.yaml` zamiast pełnego `inventory.yaml` w kontekście, jedna karta operacyjna zamiast 20 KB `system/*.md`. Zasada: aktywny kontekst trzyma stan bieżący, nigdy śladu audytowego.
- [ ] Rozważyć `gm turn quick` — tanią ścieżkę dla tur czysto narracyjnych. Bez tego narrator ucieknie w `fiction_verdict: automatic` i silnik możliwości zostanie ozdobą.

## Aktualny etap

- [x] Wykonać pierwszy przegląd dostępnej historii z `In_Character.txt`.
- [x] Wypisać elementy, które działają dobrze i powinny zostać zachowane.
- [x] Zidentyfikować powtarzalne problemy narracyjne, mechaniczne i związane z pamięcią.
- [x] Odróżnić pojedyncze pomyłki narratora od problemów wynikających z reguł systemu.
- [x] Po analizie zaprojektować strukturę folderów i format zapisu kampanii.

### Wdrożony szkielet v1

- [x] Rozdzielić reguły systemu, świat, kampanię, stan sceny i dzienniki.
- [x] Zapisać uzgodnione reguły narratora, tempa, nawiasów, testów i `In Character Score`.
- [x] Dodać osobny model chowańców, sług, przywołań i rojów oraz zdolności współdzielonych.
- [x] Dodać karty lokacji, regułę pierwszego wejścia i osobne mapy gracza oraz MG.
- [x] Dodać szablony YAML/JSONL, walidację i niezmienny zapis rzutów d100.
- [ ] Zmigrować zatwierdzony stan Lucana i Solmary z historii rozgrywki.
- [x] Przygotować staging, pakiety akceptacyjne, manifest źródeł i walidację migracji.
- [ ] Dostarczyć i zweryfikować pełny eksport rozmowy `E-rank Warlock Historia`.
- [x] Dodać archiwizację zakończonych scen i generowanie migawek.

> Ograniczenie materiału: plik nie jest kompletnym transkryptem 1:1. Zawiera 1859 linii,
> ale również skoki fabularne, brakujące wypowiedzi, fragmenty po kompakcji kontekstu
> oraz uszkodzone kodowanie polskich znaków. Wnioski dotyczą powtarzalnych wzorców
> widocznych w dostępnej historii.

## Wnioski z historii rozgrywki

### Zachować

- [ ] Krótką, reaktywną narrację kończącą się konkretną sytuacją lub hakiem.
- [ ] Czarny humor oraz dopasowywanie tonu do sposobu gry gracza.
- [ ] Swobodne rozwijanie nietypowych pomysłów gracza zamiast wciskania kampanii w rolę klasycznego bohatera.
- [ ] Eksperymentalne odkrywanie zdolności poprzez działanie w świecie.
- [ ] Trwałe konsekwencje działań, zainteresowanie straży, świadków i organizacji.
- [ ] Możliwość zadawania pytań poza akcją bez automatycznego przesuwania sceny.
- [ ] Przyznawanie się narratora do błędu i jawne cofanie błędnego fragmentu sceny.

### Poprawić w pierwszej kolejności

- [x] Zbudować rzeczywistą rubrykę `In Character Score`; w materiale 97 z 98 ocen to `5/5`, więc mechanika praktycznie nie rozróżnia zachowań.
- [ ] Nie obniżać oceny tylko dlatego, że postać zachowała się rozsądnie lub uprzejmie; uwzględniać motywację i kontekst.
- [ ] Ustalić jedną skalę oceny — prompt mówił o `1–10`, a rozgrywka używała niemal wyłącznie `5/5`.
- [ ] Ograniczyć rzuty do sytuacji z ryzykiem i interesującą porażką; nie rzucać na rutynowe przejście, pytanie, oglądanie pomieszczenia czy zwykłe przygotowania.
- [ ] Przed rzutem określać jego przedmiot, stawkę, trudność i modyfikatory.
- [ ] Nie rozstrzygać jednym rzutem kilku niezależnych działań z jednej wiadomości gracza.
- [ ] Nie pozwalać, aby wysoki rzut sam tworzył nadmiernie wygodne fakty świata lub nieproporcjonalny łup.
- [ ] Nigdy nie zmieniać raz pokazanego wyniku; zapisywać identyfikator i wynik rzutu przed narracją.
- [ ] Ujednolicić prezentację rzutu — historia miesza osobne `ROLL_DICE` z wynikiem wpisywanym przez gracza oraz późniejsze `ROLL: X` narratora.
- [ ] Nie wykonywać za gracza kolejnych decyzji; narrator może opisać bezpośredni skutek zadeklarowanej akcji, ale nie powinien sam wybierać ucieczki, kradzieży ani celu.
- [x] Prowadzić warunki postaci i zagrożenia sceny, aby obrażenia oraz walki nie były wyłącznie uznaniowe.
- [x] Oddzielić umiejętności znane, odkrywane i jedynie zasugerowane; nie tworzyć statystyk, poziomów lub zaklęć jako faktu bez zapisu ich źródła.
- [x] Zapisywać pochodzenie każdej nowej reguły świata i mechaniki odkrytej podczas gry.

### Pamięć i spójność

- [x] Prowadzić osobny rejestr wiedzy każdego ważnego NPC: co wie, co podejrzewa i czego nie może jeszcze ujawnić.
- [x] Zapobiegać przeciekom wiedzy między narratorem, graczem i NPC — w historii NPC nazwał sekretnego towarzysza, mimo że nie powinien o nim wiedzieć.
- [ ] Prowadzić stan podejrzeń, dowodów, świadków, listów gończych i zainteresowania frakcji zamiast rozstrzygać „jestem czysty” pojedynczym rzutem.
- [x] Nadawać trwałym bytom stabilne identyfikatory; dotyczy to NPC, stworzeń, lokacji, przedmiotów, zaklęć i kolejnych podobnych towarzyszy.
- [ ] Rozróżnić kanoniczny fakt, plotkę, przypuszczenie narratora oraz informację znaną wyłącznie graczowi.
- [ ] Wprowadzić rejestr retconów, aby poprawiona scena nie pozostawiała starej wersji jako równoległego kanonu.
- [ ] Nie rekonstruować brakującej historii z nadmierną pewnością; oznaczać luki i niepewne fakty.
- [ ] Zapisywać stan natychmiast po jego zmianie, szczególnie po zmianie pieniędzy, własności, miejsca, relacji, obrażeń lub sekretów.

### Ekonomia i progresja

- [ ] Zastąpić powtarzanie salda w niemal każdej odpowiedzi krótkim bilansem tylko po rzeczywistej transakcji.
- [x] Prowadzić księgę transakcji, ponieważ samo saldo nie pozwala wykryć pominiętych kosztów i podwójnie policzonego łupu.
- [ ] Skalować nagrody i znalezione dobra względem ustalonej tabeli cen oraz ryzyka.
- [ ] Oddzielić rangę gildii, rozwój osobistych zdolności, reputację przestępczą i wpływy polityczne — nie muszą rosnąć razem.

### Forma i bezpieczeństwo systemu

- [ ] Zdefiniować granice treści oraz sposób zatrzymywania lub przekierowywania niedozwolonych celów bez rozbijania tonu gry.
- [ ] Zachować możliwość brutalnej i mrocznej kampanii, ale rozróżnić dozwoloną fikcję od działań, których narrator nie będzie rozwijał.
- [x] Ustalić znacznik rozmowy poza postacią, korekty logiki i retconu, zamiast polegać na dowolnym tekście w nawiasach.
- [ ] Zapisywać wszystkie pliki w UTF-8 i dodać kontrolę kodowania; obecny materiał ma rozległy mojibake.

## Założenia architektury

- [ ] Oddzielić niezmienne reguły gry od danych konkretnej kampanii.
- [ ] Oddzielić kanon świata od bieżącego stanu sceny.
- [ ] Traktować pliki kampanii jako autorytatywne źródło stanu, a nie polegać na długości wątku.
- [ ] Nie umieszczać danych konkretnej postaci, ekwipunku ani aktywnych zadań w głównym prompcie.
- [x] Opracować procedurę wczytywania potrzebnego kontekstu przed każdą turą.
- [x] Opracować procedurę zapisywania trwałych zmian po każdej turze.
- [x] Aktualizować pamięć po zmianie stanu lub sceny, a nie co arbitralną liczbę wiadomości.
- [x] Utrzymywać krótki stan bieżący oraz osobny, przeszukiwalny dziennik wydarzeń.

## Reguły gry do dopracowania

- [x] Dodać logarytmiczną skalę możliwości 0–100 oraz bramkę `impossible/conditional/contested/automatic` przed testem.
- [x] Dodać warstwowe obiekty, oddzielne kanały efektów, baterie sług i generator proponowanych bytów.
- [x] Dodać regresje: Spidey nie dekapituje konia, może warunkowo zabić go nekrozą, a Varkhen wymaga skumulowanych przewag.

- [x] Określić dokładnie, kiedy wykonywany jest rzut, a kiedy wynik wynika bezpośrednio z fikcji.
- [ ] Zdefiniować skalę trudności, modyfikatory oraz przedziały wyników d100.
- [x] Generować rzeczywiste rzuty za pomocą narzędzia lub skryptu.
- [ ] Pokazywać rzut i jego konsekwencję w jednej odpowiedzi narratora.
- [x] Dopracować `In Character Score`, aby neutralne działania nie były automatycznie karane.
- [ ] Oddzielić zgodność z osobowością od stereotypowego zachowania klasy.
- [ ] Ustalić stopniowane i proporcjonalne konsekwencje działania poza postacią.
- [ ] Pozwolić na świadomy rozwój i zmianę osobowości postaci w trakcie kampanii.
- [ ] Ustalić, co narrator może rozstrzygać samodzielnie, a czego nie może robić za gracza.
- [ ] Zachować krótką narrację, ale doprecyzować, jakie informacje muszą się w niej znaleźć.

## Kanon, pamięć i sprzeczności

- [ ] Zdefiniować, co jest trwałym faktem wymagającym natychmiastowego zapisu.
- [ ] Określić sposób zapisu aktywnej sceny, zadań, relacji, ekwipunku i ekonomii.
- [ ] Wprowadzić wyszukiwanie lokalnego kanonu przed odpowiedzią na odwołanie do dawnych wydarzeń.
- [ ] Zastąpić zasadę „gracz zawsze ma rację” procedurą wykrywania i rozwiązywania sprzeczności.
- [ ] Rozróżnić wiedzę narratora, wiedzę świata i wiedzę dostępną postaci gracza.
- [ ] Zapisywać istotne transakcje i zawsze aktualizować saldo po zmianie pieniędzy.
- [ ] Dopuścić rabaty tylko wtedy, gdy mają fabularny lub mechaniczny koszt.

## Późniejszy etap — struktura projektu

- [ ] Zaprojektować minimalny układ folderów dopiero po analizie historii rozgrywki.
- [x] Wybrać formaty dla danych strukturalnych i treści narracyjnych.
- [x] Przygotować szablony nowej kampanii, postaci, sceny i wpisu dziennika.
- [x] Zaprojektować główną instrukcję uruchamiania mistrza gry.
- [x] Dodać walidację spójności stanu.
- [x] Dodać mechanizm archiwizacji zakończonych scen. (Duplikat pozycji z „Wdrożony szkielet v1"; realizuje `scene close` + `snapshots/`.)

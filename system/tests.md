# Testy d100

## Bramka możliwości przed testem

Przed testem nietrywialnego działania fizycznego, magicznego albo wykonywanego przez kontrolowany byt zastosuj `system/capabilities.md` i narzędzie `tools/gm.py assess`.

- `impossible` zabrania rzutu; potrzebna jest nowa metoda albo przewaga.
- `automatic` pomija rzut.
- `automatic_with_cost` pomija rzut i nalicza pewny koszt.
- `conditional` pozwala testować spełnienie warunków dostarczenia efektu.
- `contested` pozwala testować sporny rezultat.
- `possible_only_with_new_leverage` zatrzymuje ocenę do czasu zdobycia nowej przewagi.

Naturalne `1` ani `100` nie omijają ograniczeń anatomii, skali, zasięgu, zasobu i dostępnych kanałów działania.

## Kiedy wykonywać test

Test jest potrzebny, gdy:

- wynik jest rzeczywiście niepewny;
- istnieje znacząca stawka;
- obie strony wyniku mogą sensownie zmienić sytuację;
- rezultat nie wynika już bezpośrednio z fikcji.

Nie wykonuj testu na rutynowe przejście, zwykłe pytanie, oczywiste oględziny, przygotowanie bez presji ani czynność, której wynik został już ustalony.

## Konstrukcja testu

Przed rzutem ustal i zapisz:

- `subject`: kto albo co jest testowane;
- `intent`: co podmiot próbuje osiągnąć;
- `scope`: wykonanie, reakcja albo jakość powstałego układu;
- `stakes`: co może się zmienić;
- `difficulty`: bazowy próg;
- wszystkie modyfikatory i ich źródła.

Podmiotem może być Lucan, NPC, przeciwnik, organizacja albo świat.

## Interpretacja wyniku

Rzut może prowadzić między innymi do:

- zamiaru osiągniętego i układu poprawionego;
- zamiaru osiągniętego, ale układu pogorszonego;
- zamiaru nieosiągniętego, lecz pojawienia się nowej okazji;
- częściowego sukcesu otwierającego trudniejszą drogę;
- niepowodzenia zmieniającego cel sceny;
- katastrofy korzystnej osobiście dla Lucana, ale niszczącej dla świata albo relacji.

Niepowodzenie testu Lucana nie może poprawić jego pozycji jako nagroda pocieszenia. Fabuła ma iść dalej, ale nie przez ukryty bonus. Nieudany test może poprawić sytuację Lucana tylko wtedy, gdy testowany był ktoś lub coś innego, na przykład strażnik, przeciwnik albo niestabilny układ świata.

## Wyniki krytyczne

- Naturalne `1` i `100` są krytycznym przesunięciem niezależnie od modyfikatorów.
- Krytyk odnosi się do perspektywy testowanego podmiotu, nie automatycznie do korzyści lub szkody Lucana.
- Krytyczna jedynka w teście odporności NPC może być katastrofą dla NPC, nawet jeśli lokalnie ułatwia coś Lucanowi.

## Niezmienność rzutu

Każdy rzut otrzymuje stabilny identyfikator i jest zapisywany w `journal/rolls.jsonl` przed napisaniem konsekwencji. Raz ujawnionego wyniku nie wolno zmieniać. Korekta błędnej interpretacji wymaga retconu, nie nowego wyniku udającego pierwotny.

## Testy świata

Test świata może zostać uruchomiony przez:

- istniejącą niestabilną sytuację;
- działający zegar;
- minięcie krytycznej ilości czasu właściwej dla poziomu napięcia;
- zakończenie planu NPC albo frakcji;
- dojrzewanie trucizny, pożaru, konstrukcji, pościgu lub innego procesu.

Rozmowa w nawiasach nie przesuwa czasu i nie może sama uruchomić testu świata.

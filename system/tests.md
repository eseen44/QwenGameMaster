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

## Testy diagnostyczne i odkrywcze

Test, w którym stawką jest **wiedza o świecie** (co to jest, czy działa, co się
kryje) - nie starcie z aktywnym przeciwnikiem - nie powinien być czystą bramką
zdanie/niezdanie względem `difficulty`. Sam wynik rzutu (zwłaszcza `natural_roll`
przy braku modyfikatorów) czyta się jako **gradient jakości odkrycia**, nie
binarny próg:

- bardzo wysoki wynik: pełne, wyraźne, użyteczne odkrycie ("jackpot") - nawet
  ponad to, co formalna `difficulty` by dopuszczała;
- średni wynik: częściowy, niejednoznaczny trop - coś realnego, ale
  niekompletnego albo wymagającego interpretacji;
- niski wynik: brak sensownego sygnału - ale to wciąż jest fakt fabularny
  (fałszywy trop, red herring, "wygląda na zwyczajne", ślad zatarty) - nie
  czysta, niewnosząca niczego cisza.

Powód: `difficulty` jako twardy próg dobrze modeluje starcie (kontrola,
unik, obrona), ale przy odkrywaniu świata "nic się nie dowiedziałeś" nie
tworzy okazji ani konsekwencji - łamie zasadę z sekcji "Kiedy wykonywać test"
("rezultat nie wynika już bezpośrednio z fikcji" / "obie strony wyniku mogą
sensownie zmienić sytuację"). `difficulty` w takim teście służy do skalibrowania
*progu*, ale narrator zawsze buduje z surowego wyniku jakiś fabularny fakt,
nie pustkę.

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

## Nieograniczona powtórka znosi test

Kalibracja gracza z 25.08.2026, obowiązująca. Doprecyzowuje „przygotowanie bez presji"
z sekcji „Kiedy wykonywać test", bo ogólne sformułowanie okazało się za słabe —
narrator rzucił na pierwsze użycie procedury w interludium, gdzie porażka nie kosztowała
nic poza minutami (`roll_turn_interlude_095`).

**Jeżeli postać może natychmiast spróbować jeszcze raz, nie ma czego testować.** Rzut
zakłada, że wynik rozstrzyga sytuację. Przy dowolnej liczbie podejść nie rozstrzyga
niczego — odmierza tylko, ile razy trzeba powtórzyć, a to jest koszt CZASU i zasobu, nie
test. Rozstrzygnij narracyjnie: opisz, co poszło nie tak i czego to uczy, nalicz czas
oraz zużyty zasób, i pozwól powtórzyć.

Test wraca dopiero wtedy, gdy powtórka przestaje być darmowa:

- kończy się okno (ktoś wchodzi, cel wychodzi, zegar dobija);
- każda kolejna próba ma własną cenę rosnącą szybciej niż czas (świadek, zużyty materiał,
  narastające podejrzenie celu);
- niepowodzenie robi coś nieodwracalnego, czego druga próba nie cofnie.

Osobno: **nie testuj tam, gdzie stawką jest wyłącznie wykonanie po stronie gracza, a nie
opór świata.** Trening to trening. Cel bez własnej obrony nie tworzy testu tylko dlatego,
że ma kartę w `entities/npcs/`.

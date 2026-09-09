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

Jawna blokada fazy w `campaigns/<id>/state/time.yaml#roll_policy` ma pierwszeństwo przed
lokalnym werdyktem `conditional` albo `contested`. Przy `mode: disabled` nie rzucamy:
wykonalna akcja daje `automatic` albo `automatic_with_cost`, a `impossible` i
`possible_only_with_new_leverage` pozostają twardymi granicami. Odblokowanie wymaga jawnego
przejścia do następnego aktu; nie wymaga ukończenia wszystkich planów interludium.

Tryby `roll_policy.mode`:

| tryb | co rozstrzyga rzut |
|---|---|
| `disabled` | nic — rzutów nie ma (całe interludium) |
| `threshold` | wykonanie: `modified >= difficulty` (Akty 1–2, zapis historyczny) |
| `world_axis` | **przechylenie świata**, nie wykonanie — sekcja niżej (Akt 3) |

## Kiedy wykonywać test

Test jest potrzebny, gdy:

- wynik jest rzeczywiście niepewny;
- istnieje znacząca stawka;
- obie strony wyniku mogą sensownie zmienić sytuację;
- rezultat nie wynika już bezpośrednio z fikcji.

Nie wykonuj testu na rutynowe przejście, zwykłe pytanie, oczywiste oględziny, przygotowanie bez presji ani czynność, której wynik został już ustalony.

## Perk Lucana: Surfer chaosu

Lucan ma trait `crisis_surfer` (`retcon_000071`). W żądaniu testu oznacz ogólną karę
wynikającą ze stresu lub zamieszania jako modyfikator z `category: stress`. Runtime
automatycznie ją neutralizuje. Nie obejmuje to magicznego strachu, przymusu, bólu, ran,
zaburzeń zmysłów, braku wiedzy ani twardych ograniczeń zdolności.

Jeżeli kryzys jest dla działania Lucana realnym narzędziem, ustaw
`crisis_exploitable: true` i podaj co najmniej dwa prawdziwe `situation_tags` spośród:
`time_pressure`, `multiple_simultaneous_failures`, `environmental_chaos`,
`others_panicking`, `resource_triage`, `rapidly_changing_situation`. Runtime doda `+10`.
Samo wysokie napięcie sceny albo dramatyczny opis nie uruchamia bonusu.

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

## Rzut w Akcie 3: porządek albo entropia

Decyzja gracza 2026-09-09, obowiązująca od przejścia `roll_policy.mode` na `world_axis`.

**Rzut przestaje odpowiadać na pytanie „czy się udało".** Na to odpowiada fikcja, metoda
i `system/capabilities.md` — dokładnie tak, jak przez całe interludium przy `disabled`.
Rzut odpowiada na pytanie, **w którą stronę przechylił się świat**: wysoki wynik zaciska
porządek, niski rozpuszcza go w entropii.

Te dwie rzeczy są **niezależne** i zapisuje się je osobno:

- `outcome.intent_achieved` — czy zamiar Lucana został osiągnięty;
- `roll.world_axis.delta` — co się przy tym stało ze światem.

Więc: **akcja może się udać i przy tym rozprząc świat.** Podpis wymuszony na urzędniku
zamyka sprawę i uczy magistrat, że podpisy się wymusza. Może być też odwrotnie: zamiar
nieosiągnięty, a świat stężał, bo procedura wytrzymała nacisk. „Nie udało się" i „zrobiło
się gorzej" to od teraz dwa różne zdania i nie wolno ich zlepiać.

### Pasma

Liczone z **marginesu** nad progiem (`modified_result − difficulty`), nie z surowego d100:
`difficulty` już niesie opór sytuacji, więc 70 przy progu 40 i 70 przy progu 85 nie mogą
znaczyć tego samego.

| margines | delta | pasmo |
|---|---|---|
| ≥ +25 | **+2** | `porzadek_wyrazny` |
| +5 … +24 | **+1** | `porzadek` |
| −4 … +4 | **0** | `zawieszenie` — świat nie tężeje i nie pęka |
| −5 … −24 | **−1** | `entropia` |
| ≤ −25 | **−2** | `entropia_wyrazna` |

Naturalne `100` daje **+3**, naturalne `1` daje **−3**, niezależnie od marginesu
(sekcja „Wyniki krytyczne"). Runtime liczy to sam w `build_roll` i zapisuje w rzucie —
czyli **przed narracją**, więc pasma nie wolno przeliczyć po zobaczeniu, co wyszło w fikcji.

### Dziedziny

`campaigns/lucan/state/world-axis.yaml` trzyma cztery dziedziny: **prawo i papier**,
**ulica i trakt**, **wiara i klątwa**, **wiedza i wynik**. Każda ma zapisane, co u niej
znaczy porządek, a co entropia — bez tego „porządek" jest słowem, w które narrator wpisuje,
co mu wygodnie. Dziedzinę wybiera **scena**: przechyla się ta, której instytucji rzut
dotyczył. Suma dziedzin (`totals.world_total`) jest liczbą na nagłówek; rozstrzyga zawsze
dziedzina, bo w niej siedzi treść.

### Zapis

Niezerową deltę **trzeba** zastosować w tej samej turze:

```yaml
operations:
- op: shift_world_axis
  domain: prawo
  delta: -1
  roll_id: roll_turn_act_03_004
  reason: Urzędnik przyjął pismo, ale bez terminu i bez własnego nazwiska.
```

`turn commit` **odmawia**, jeżeli rzut policzył przechylenie, a `outcome.operations` go nie
zawiera. Rzut policzony i niezastosowany jest gorszy od braku rzutu: liczba leży w dzienniku
i twierdzi, że coś zmieniła. `reason` musi być zdaniem fikcji, nie numerem pasma.

Co `step` punktów (domyślnie 3) dziedzina przechodzi próg i do sceny wchodzi reakcja świata —
tym samym mechanizmem, którym robią to zegary. **Reakcja nie niesie gotowego efektu**: mówi,
która dziedzina i w którą stronę, a konsekwencję narrator bierze z pliku i wskazuje który
(`retcon_000055`, `retcon_000058`). Os świata nie jest licencją na produkowanie zagrożeń,
których kanon nie ma.

### Czego to nie zmienia

- Bramka możliwości działa bez zmian: `impossible` i `possible_only_with_new_leverage`
  nadal zabraniają rzutu, a naturalne `100` nie omija anatomii, skali ani zasięgu.
- „Nieograniczona powtórka znosi test" obowiązuje dalej. Oś świata nie jest powodem, żeby
  rzucać częściej — jest powodem, żeby rzut **znaczył więcej**, kiedy już padnie.
- Niepowodzenie Lucana nadal nie może być nagrodą pocieszenia. Entropia nie jest nagrodą:
  jest zmianą świata, w którym on dalej musi żyć.

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
  **Doprecyzowanie po retcon_000052:** świadek liczy się tylko wtedy, gdy KOLEJNA próba
  daje mu coś nowego. Ktoś, kto już raz to widział, nie jest narastającą ceną - jest ceną
  zapłaconą przy pierwszym podejściu. Tak samo materiał zużyty jednorazowo. Bez tego
  zastrzeżenia "świadek" staje się uniwersalną furtką do rzutu w każdej scenie z kimkolwiek
  w pokoju - i tak został użyty w roll_turn_interlude_134.
- niepowodzenie robi coś nieodwracalnego, czego druga próba nie cofnie.

Osobno: **nie testuj tam, gdzie stawką jest wyłącznie wykonanie po stronie gracza, a nie
opór świata.** Trening to trening. Cel bez własnej obrony nie tworzy testu tylko dlatego,
że ma kartę w `entities/npcs/`.

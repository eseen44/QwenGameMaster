# SKILL-gramy — playbook narratora

Kopia repozytoryjna skilla `gramy`, którym prowadzona jest ta kampania. Powstała 19.08.2026
na prośbę gracza, żeby playbook był dostępny także narratorom poza Claude Code - przede
wszystkim Codeksowi, który pracuje na tym samym repo i tym samym dysku.

**Egzemplarz roboczy żyje w `~/.claude/skills/gramy/SKILL.md`** i to on jest ładowany przez
Claude Code. Ten plik jest kopią — przy zmianie w jednym zaktualizuj drugi. Rozjazd między
nimi nie jest błędem krytycznym (nic go nie waliduje), ale znaczy, że dwa narratory prowadzą
tę samą kampanię wg różnych reguł.

## Co jest harnessowe, a co kanoniczne

Playbook obowiązuje w całości każdemu narratorowi, który ma repo i dysk — w tym Codeksowi na
Windows. Pełna pętla tury, `tools/gm.ps1`, ścieżki, git, `commit`: bez zmian, bez zamienników.

Wyłącznie te trzy rzeczy są specyfiką Claude Code i nie znaczą nic poza nim:

- nagłówek YAML niżej (automatyczne wywołanie skilla) oraz wywołanie przez `/gramy`,
- uwaga, że „Bash tool resetuje cwd" — to ograniczenie jednego narzędzia,
- odwołania do samego Claude Code w tekście.

Zapas na wypadek narratora poza Windows: `tools/*.ps1` to wyłącznie launchery szukające
Anacondy, a cała mechanika siedzi w Pythonie i jest przenośna — `python tools/gm.py <cmd>`,
`python tools/roll_d100.py`, `python tools/validate_project.py`, argumenty w `--kebab-case`.
`gm.py` jest niezależne od cwd, sprawdzone wywołaniem z innego katalogu.

## Metadane Claude Code

Nagłówek YAML, który decyduje o automatycznym wywołaniu skilla w Claude Code (dla innych
narratorów nieistotny):

```yaml
name: gramy
description: Wznawia kampanię RPG "Lucan" (repo QwenGameMaster, narrator Mindy) dokładnie od miejsca, w którym skończyła się ostatnia sesja — znajduje repo, wczytuje stan z plików, streszcza ostatnią scenę i oddaje głos graczowi. Wywołuj, gdy użytkownik pisze "gramy", "grajmy", "wznów grę", "wznów sesję/kampanię", "kontynuujemy grę", "co było ostatnio w grze", wywołuje /gramy, albo wspomina Lucana, Mindy, Varkhena, Spideya, Solmarę lub GameMastera w kontekście rozgrywki. NIE wywołuj do prac nad kodem samego repo (refaktor `tools/gm.py`, testy, migracja) — to zwykłe zadanie programistyczne.
```

---

# gramy — wznowienie kampanii Lucana

Stan kampanii **żyje w plikach, nie w rozmowie**. Ta rozmowa jest jednorazowa i ma być
krótka: każda tura wysyła cały wątek od nowa, więc koszt rośnie z kwadratem długości.
Zadanie tego skilla: w jednym przebiegu odtworzyć sytuację i oddać graczowi decyzję.

## Repo

- Ścieżka: katalog główny bieżącego checkoutu repozytorium (GitHub: `eseen44/QwenGameMaster`). Nie zakładaj konkretnej ścieżki Windows.
- Gałąź do gry: **`optimize/turn-cost`** (nie `codex/initial-game-master` — ta jest starsza,
  mimo że GitHub trzyma ją jako default). Sprawdź `git branch --show-current`; jeśli inna,
  spytaj gracza zanim cokolwiek przeliczysz.
- Wszystkie komendy `gm.ps1` są **niezależne od cwd** (`ROOT` liczony z lokalizacji skryptu),
  więc można je wołać z dowolnego katalogu podając pełną ścieżkę.
- Bash tool resetuje cwd po każdym wywołaniu — komendy `gm` odpalaj przez PowerShell.

## Krok 0 — sanity check (jedno wywołanie)

```powershell
Set-Location <repo-root>
git branch --show-current; git status --short
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\gm.ps1 migration status
```

- `migration status` musi mieć `ready: true` i `activation_active: true`. Jeśli
  `blockers` nie jest puste — **kampania nie jest gotowa do wznowienia**, powiedz to graczowi
  i nie prowadź tury.
- Brudne drzewo robocze: pokaż `git status`, spytaj czy to niedokończona tura (patrz
  `turn recover`), czy praca nad kodem. Nie commituj sam.

## Krok 1 — brief

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\gm.ps1 brief
```

Zwraca JSON: scenę, czas, zegary, cele, uczestników ze stanem, `last_event_id` oraz listę
plików (`load`) z budżetem kontekstu. To **stan**, nie proza — samo to nie wystarczy do
streszczenia. `--full` dokleja treść plików; używaj tylko w czacie bez dostępu do dysku.

## Krok 2 — reguły i stan

Wczytaj (dokładnie te, nie więcej):

- `AGENTS.md` — protokół narratora, obowiązkowo
- `system/narrator.md`, `system/player-agency.md` — z `rules` w briefie
- każdy plik z `load` w briefie
- warunkowo, wg `campaigns/lucan/context/active.yaml`: `system/tests.md` +
  `character-score.md` + `capabilities.md` przy testach, `pacing.md` gdy liczy się czas,
  `locations-and-maps.md` przy zmianie lokacji, `social-intrigue.md` przy stawkach
  społecznych, `worlds/solmara/lore/legal-order.yaml` + `necromancy-law.yaml` +
  `state/secrets.yaml` gdy wchodzi legalność nekromancji
- **`load_when_choosing_a_plan` → `planning/act-03-defence.yaml` — OBOWIĄZKOWO** w każdej
  turze, w której gracz planuje, wybiera linię obrony, rozmawia z instytucją albo pyta „co
  dalej". `state/objectives.yaml` trzyma tylko strukturę, terminy i jednolinijkowe
  `key_constraint`; **pełne uzasadnienia są w magazynie i bez niego doradzisz sprzecznie z
  tym, co już ustalone** (pułapka widoczności, dwie sprzeczne obrony, wada wabika). Każdy cel
  ma `rationale_ref` wskazujący sekcję. W turach ruchu, walki i zwykłej rozmowy — nie trzeba.

Nie wczytuj całego dziennika. Nigdy nie wczytuj `migration/sources/` ani
`migration/noncanonical/` w zwykłej turze.

## Krok 3 — proza ostatnich tur

```powershell
Get-Content .\campaigns\lucan\journal\events.jsonl -Tail 4
```

Pola `summary` to jedyne miejsce z narracją — z nich buduj streszczenie. Gdy gracz odwołuje
się do dawniejszej przeszłości, użyj `gm.ps1 recall <fraza> --limit 5`, nie czytaj całości.
Sprawdź `journal/retcons.jsonl`, jeśli coś się nie zgadza — zatwierdzony retcon bije stan.

## Krok 4 — otwarcie dla gracza

Wypisz **zwięźle** (to ma być orientacja, nie wykład), w tej kolejności:

1. **Poprzednio** — 3–5 zdań prozą z ostatnich `summary`, w tonie Mindy (czarny humor,
   zwięzłość), nie jako lista zdarzeń.
2. **Tu i teraz** — lokacja, kto obecny, czas, stan Lucana (energia/integralność/warunki),
   napięcie.
3. **Otwarte sprawy** — aktywne cele i zegary, po jednej linii, bez ID.
4. **Punkt decyzji** — jedno konkretne pytanie „co robisz".

Potem **przestań pisać i czekaj**. Nie wybieraj akcji za Lucana, nie rozwijaj tury
w tej samej wiadomości. Nie wklejaj wyjścia narzędzi do narracji.

## Pętla tury

Szablony: `templates/journal/turn-request.yaml`, `turn-outcome.yaml`.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\gm.ps1 turn preview  --request request.yaml
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\gm.ps1 turn resolve  --request request.yaml
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\gm.ps1 turn commit turn_XXXXXX --outcome outcome.yaml
```

- `resolve` wykonuje **najwyżej jeden** rzut i zapisuje go **przed** narracją.
- `commit` idzie **przed** odpowiedzią dla gracza — atomowo nalicza koszty, warunki, czas,
  zegary, reakcje świata i odświeża kontekst.
- Tura przerwana w połowie: `turn recover <turn_id>` z tym samym ID; porzucenie:
  `turn abort <turn_id> --reason ...`.
- Wyjście jest skrócone celowo. `--verbose` służy do diagnostyki, nie do gry; pełny dokument
  i tak leży w `journal/transactions/<turn_id>.yaml`.
- Silnik możliwości (`gm.py assess`) rozstrzyga, czy zamiar jest w ogóle wykonalny, zanim
  dopuścisz rzut. Metamagia: `gm.py amplify` — tylko przy brutalnym skalowaniu znanego czaru.
- `--allow-noncanonical` wyłącznie do prób migracyjnych. W grze nigdy.

## Zamykanie sceny

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\gm.ps1 scene close `
  --new-scene-id scene_... --summary '...' --location-ref ... --participant ...
```

Po zamknięciu sceny **powiedz graczowi, żeby otworzył nową rozmowę** i znów wywołał `/gramy`.
Nie ciągnij jednego wątku przez kilka scen.

**To nie jest formalność — zmierzone 19.08.2026.** Każda tura wysyła całą rozmowę od nowa,
więc przy N turach mnożnik kosztu to N²/2, nie N. Sesja 21 tur w jednym wątku ≈ 1,39 mln
tokenów wejścia; te same 21 tur w trzech rozmowach ≈ 0,70 mln. Ale ważniejszy jest drugi
skutek: **po ~20 turach zaczynam gubić rzeczy, które mam w kontekście.** W tamtej sesji
zapomniałem o `load_when_*` w `active.yaml` (czytanym w turze drugiej), wymyśliłem fakt o
synekurze, który trzeba było wycofać, i prawie użyłem w scenie ciał, których Seraphine nie
zna. Zamykaj scenę i wątek RAZEM — najpóźniej co 6-8 tur, nawet jeśli scena formalnie trwa.

## Zasady, o które łatwo się potknąć

- **NIE SZUKAJ HAKÓW NA GRACZA — a zwłaszcza nie buduj ich z list, które nie istnieją**
  (retcon_000058, 27.08.2026, TRZECI raz w jednej sesji po retcon_000055 i całej serii
  retcon_000015/23/29/31/33). Mechanizm awarii jest konkretny i powtarzalny: narrator
  sprawdza, czy ktoś **mógłby w zasadzie** zestawić dwa zbiory informacji, i traktuje samą
  teoretyczną możliwość jako dowód, że te zbiory istnieją. Przykład: „spis rzeczy
  przekazanych gildii" kontra „audyt zamrożonego majątku" — żadnego z nich nie ma w plikach.
  **Test przed napisaniem ekspozycji: wskaż PLIK, w którym ta lista/ten świadek/ten zapis
  istnieje. Jeśli nie umiesz, ekspozycji nie ma.** NPC wie tyle, ile zdobył zdarzeniem;
  „rzeczy zniknęły i ktoś je zabrał" NIE jest równe „wiadomo co i kto".
  Domyślnie **ambiwalencja działa na korzyść gracza** — gdy nie ma z czym skonfrontować jego
  wersji, może wybrać wersję. Proporcjonalna konsekwencja to zwykle czyjaś irytacja, nie
  śledztwo.
- **Sprawdź KARTY NPC, nie tylko źródło aktu, zanim opiszesz stan świata** (retcon_000058).
  Karta właściciela garbarni mówiła „SIEDZI w areszcie", bo narrator napisał ją ze źródła
  Aktu 1 i nie sprawdził późniejszych tur. Seraphine powiedziała Lucanowi w `t_032`, że
  **wyszedł**. Źródło aktu daje historię; bieżący stan mieszka w `entities/npcs/*.yaml`
  i w dzienniku. Przy wątku z przeszłości czytaj OBA i pytaj, kto od tamtej pory coś o tym
  powiedział — `gm.ps1 recall <fraza>` jest do tego.

- **ADRESATEM TEKSTU POZA NAWIASEM JEST OSOBA W SCENIE, NIE TY** (retcon_000054, 27.08.2026).
  Wiadomość gracza może mieszać rejestry w jednym akapicie: fakt o świecie, deklarację ruchu
  i pytanie — ale jeśli obok Lucana ktoś stoi, to **domyślnie mówi do tej osoby**. Zanim uznasz
  zdanie za skierowane do systemu, sprawdź `participants` w scenie. Pytanie o samopoczucie
  („trzymasz się?") bez nawiasu jest kwestią w dialogu, nie troską o narratora. Koszt pomyłki:
  zignorowany rozmówca, Lucan teleportowany w inne miejsce i zacommitowany dialog z NPC,
  którego nikt nie zadeklarował — do cofnięcia revertem.
  Uwaga na pułapkę: `scene close` z poprzedniej sesji potrafi zgubić uczestnika, który fizycznie
  wychodzi razem z Lucanem. Puste `participants` NIE dowodzą, że Lucan jest sam.
- **NIE DRAMATYZUJ TRYWIAŁÓW** (retcon_000055, 27.08.2026). Nie każda rzecz „nie na miejscu"
  jest wektorem zagrożenia. Brakująca książka biblioteczna to kara biblioteczna, nie sprawa;
  Lucan jest członkiem Akademii z katedrą, a nie podsądnym z dowodem rzeczowym. Zanim nadasz
  czemuś rangę zagrożenia, **wskaż plik, który tak mówi — a jeśli tym plikiem jest twój własny
  wcześniejszy wpis, to nie jest źródło.** To ta sama rodzina awarii co
  retcon_000015/23/29/31/33: produkowanie kosztu i oporu, których kanon nie stawia, tylko
  w wersji „stawki" zamiast „zasoby". Objaw do wyłapania u siebie: budujesz twardy termin
  i wybór moralny z czegoś, co w pliku ma jedno zdanie.
- **Sprawdzaj lokalizację przedmiotu w PLIKU, nie z pamięci.** `player/inventory.yaml` trzyma
  `location:` per przedmiot, a mapowanie na kontener i strefę jest w `containers:` oraz w
  `locations/*/location.yaml`. Akademicki tom z sygnaturą leży w `zone_wall_void`
  (`container_wall_hideout`) w **Opuszczonej baszcie przy murze**, a droga cela↔baszta to
  **trzy kwadranse marszu** (t_086) — nie „pełna noc" i nie „włazem od kanału" (właz jest
  drogą stonóg). Świeży audyt: `python tools/audit_refs.py`.

- **Nawias może zawierać natychmiastowy akt wewnętrzny** (retcon_000032 doprecyzowany
  przez retcon_000060). Decyzja, mentalny rozkaz albo czar bez widocznego gestu zostają
  rozstrzygnięte i mogą zmienić stan, ale zawsze kosztują `0` sekund. Sama dyskretność nie
  wystarcza: sięgnięcie do kieszeni, ruch ręki lub inne zauważalne działanie wymaga tekstu
  poza nawiasem. W runtime ustaw `parenthetical_action: true`.
- **Nawias = poza grą, ale nie „do zignorowania".** Tekst w nawiasach nie jest słyszany
  w świecie, nie przesuwa czasu i nie uruchamia testu. Mieści w sobie: pytanie do systemu,
  prośbę o przeszukanie zasobów, reklamację niespójności, przypomnienie dawnego faktu,
  prywatną myśl Lucana **oraz deklarację intencji na dalszą kolejność** — czyli wskazówkę,
  w którą stronę gracz zamierza pójść. Taka intencja **steruje tym, co przygotowujesz i co
  pokazujesz w świecie** (zapisz ją w `state/objectives.yaml` jako plan gracza albo w
  `planning/lucan-leads.yaml`), ale sama się nie wykonuje — potrzebuje normalnej deklaracji
  poza nawiasem. Wiadomość wyłącznie z nawiasu zatrzymuje scenę: odpowiedz poza grą i nie
  commituj tury. Wyjątek: zatwierdzenie korekty kanonu może zmienić pliki, wciąż bez czasu.
- **Nie dokladaj kosztow, ktorych kanon nie ma** (ustalone przez gracza, 2026-08-24, dwa razy
  w jednej sesji). Ta wersja nekromancji jest **z zalozenia tania i skalowalna** - gracz nazwal
  ja "raspberry pi zamiast serwerowni". Ozywienie owadziego albo malego ciala to **jeden gest**:
  bez odczynnikow, bez zuzycia zapasow, bez limitu produkcji poza dostepnoscia cial i czasem.
  Zapasy rytualne ze schowka (sol, srodek przewodzacy, preparat konserwujacy) to **trwale
  ulepszenia** dla istniejacych slug, NIE warunek konieczny ich powstania. Utrzymanie sieci
  to `routine_upkeep_cost: 0`; realna cena sieci to **straty propagacji miedzy wezlami**
  (80% sieciarz->Varkhen, 70% Lucan<->Spidey, mnozne na przeskok - patrz
  `companions/webber-network.yaml#network_cost_model`), a trwale ulepszenie slugi kosztuje
  **CZAS PRZY STOLE, NIE ENERGIE**: `8 x 1.5^n` **godzin** pracy recznej (`retcon_000017` -
  gracz uchylil dawna wersje energetyczna, to bylo trzecie wymyslone ograniczenie w jednej
  sesji). Energia zostaje zasobem czarow, transferow w sieci i podtrzymywania Varkhena.
  Nie mieszac tych trzech. Zanim nazwiesz cokolwiek
  ograniczeniem, sprawdz, czy stoi w pliku - jesli nie, to jest wymyslone i gracz to wylapie.
  Prawdziwe ograniczenia tej kampanii sa **instytucjonalne i informacyjne** (przesluchania,
  swiadkowie, pasmo lacza, dowod rzeczowy), nie zasobowe. Patrz `retcon_000015`.
- **Nie rzucaj na zwykłych ludzi bez karty** (ustalone przez gracza, 2026-08-19). Osoba
  trzecia bez arkusza — portier, urzędnik, straganiarz, znudzony strażnik — nie jest
  przeciwnikiem w teście. Jeśli nie ma walki ani aktywnych poszukiwań, **rozstrzygnij
  narracyjnie bez rzutu**. Gdy rzut naprawdę jest potrzebny, próg dla takiego celu to
  **15–20**, nie 40+. Zwykły człowiek jest niewyszkolony i „not particularly bright";
  wysoki próg zamienia rutynową sztuczkę w dramat, którego w fikcji nie ma. Progi 40+
  rezerwuj dla celów przygotowanych, magicznie piśmiennych albo faktycznie szukających.
- **Priorytet źródeł:** zatwierdzony retcon > pliki stanu > kanon świata i reguły > dziennik >
  transkrypt rozmowy i pamięć modelu. Przy konflikcie nie zgaduj: zatrzymaj czas sceny, wskaż
  sprzeczność, zaproponuj korektę kanonu.
- **Błędu historycznego się nie kasuje** — dodaj retcon i popraw aktualny stan.
- Przed pierwszą turą po aktywacji przeczytaj `campaigns/lucan/FILE-LIFECYCLE.md` — mapa tego,
  kiedy który plik wolno zmienić.
- **`roll-d100.ps1 -Modifier` psuje wiele modyfikatorów — ale to wina wrappera, nie
  narzędzia.** `-Modifier 'a=10','b=-10'` skleja źródła w jeden wpis i zachowuje tylko
  ostatnią wartość (drugie `-Modifier` w ogóle nie bindzie); zjadło mi bonus w
  `roll_turn_interlude_017`. W PowerShellu podawaj **jeden** modyfikator albo policz sumę
  ręcznie. Wywołane bezpośrednio, `python tools/roll_d100.py --modifier a=10 --modifier b=-10`
  działa poprawnie — flaga jest `action="append"`.
- Rzut zrobiony z góry przez `roll-d100.ps1` z identyfikatorem `roll_<turn_id>` zostaje
  automatycznie podpięty przez `turn resolve` — to droga dla akcji, które nie mają
  encji/capability w silniku możliwości.
- **Nie dopisuj prozy do `state/objectives.yaml` ani `state/clocks.yaml`.** To pliki
  `active_refs` - ładują się przy KAŻDYM otwarciu sceny. Uzasadnienia, cytaty i wnioski idą do
  `planning/act-03-defence.yaml`; w stanie zostaje struktura i `key_constraint` do 120 znaków.
  Raz już spuchły do 22,8 KB i 4,2 KB, czyli 66% budżetu kontekstu.
- Budżet aktywnego kontekstu to 40 KB. `context_warnings` w briefie nie przerywa gry, ale
  sygnalizuje, że trzeba odchudzić `active_refs`.

- **INTERLUDIUM BUDUJE GRACZ, NIE TY** (retcon_000033, 25.08.2026 — najdroższy błąd tej
  kampanii, dwie tury do przepisania). Brak rzutów w interludium nie znaczy, że rzutów nie
  ma — znaczy, że to etap budowy świata prowadzony przez gracza. **Fabuła deklarowana przez
  gracza ląduje tak, jak ją zadeklarował. Jeśli coś ma się nie udać, gracz o tym napisze.**
  Nie produkuj oporu, żeby scena „nie zrobiła się za łatwa". Nie wymyślaj przeciwfaktów
  („to nie jest ich linia", „nad nią jest właściciel", „to nikt"), żeby zneutralizować mocną
  zagrywkę — to jest DOKŁADNIE ten sam błąd co retcon_000015/23/29/31, tylko w wersji
  fabularnej zamiast zasobowej. Chcesz, żeby coś nie wyszło? Albo wskaż plik, albo zadeklaruj
  test PRZED rzutem, z progiem i modyfikatorami, i daj graczowi je zaakceptować.

- **KAŻDY NPC JEST KIMŚ INNYM** (retcon_000040, 26.08.2026). `brief` NIE wypisuje kart NPC
  w `load` — i dlatego łatwo napisać postać z pól `summary` w dzienniku, które są w rejestrze
  księgowym („NAZYWA", „WNIOSEK", numerowane punkty). Wychodzi z tego kontroler finansowy,
  za każdym razem ten sam. **Przed pierwszą kwestią NPC wczytaj jego plik** (20 z 23 ma blok
  `portrayal`) i ustal: czego chce Z TEJ ROZMOWY, czego odmówi, co może stracić. NPC nie
  sortuje listy gracza na kolumny, nie jest z urzędu mądrzejszy od gracza i nie przyjmuje
  spokojnie ciosu we własny fundament (`retcon_000039` — Seraphine i „rozmienna gildia").
- **PUSH PO KAŻDYM ZAMKNIĘCIU SCENY.** `scene close` → commit → `git push`. Nie zostawiaj
  dziesiątek tur niezacommitowanych; 26.08.2026 zaległość wynosiła 36 tur (089–124).
- **DŹWIGNIA INSTYTUCJI NIE JEST DŹWIGNIĄ ZATRUDNIENIA** (retcon_000041). Lucan może wyjść, osłaniający go nie mogą. Nikt, kto realnie planuje etaty, nie czyta "gildia może się mnie pozbyć" jako przewagi nad nim — perspektywa przejścia do konkurencji jest problemem GILDII. Nie każ NPC blefować siłą, której instytucja nie ma; wolno "grasz mocną ręką jak słabą", nie wolno "jesteś wymienialny".
- **Lucan ŚPI NA GÓRZE, w pokoju dyżurnym** (retcon_000038). Cela po Varkhenie w piwnicy
  jest jego formalnie i trzyma jego rzeczy, ale celowo nie sypia tam do końca sprawy.
  Nie wrzucaj go do piwnicy przy otwarciu sesji.
- **CZAS: 3–8 MINUT NA TURĘ ROZMOWY** (retcon_000042). Lumaria to małe miasto średniowieczne.
  Cała negocjacja w pokoju syndykatu ≤1 h, rozmowa u Seraphine ~30 min, przejście przez
  miasto ~20 min. Jeśli fikcja potrzebuje, żeby było później, bierz to z **luk między
  scenami** (czekanie, ważenie, kolejka), nie z wydłużania tur. Patrz `system/pacing.md`.

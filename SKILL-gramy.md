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

- **Nawias = poza grą, ale nie „do zignorowania".** Tekst w nawiasach nie jest słyszany
  w świecie, nie przesuwa czasu i nie uruchamia testu. Mieści w sobie: pytanie do systemu,
  prośbę o przeszukanie zasobów, reklamację niespójności, przypomnienie dawnego faktu,
  prywatną myśl Lucana **oraz deklarację intencji na dalszą kolejność** — czyli wskazówkę,
  w którą stronę gracz zamierza pójść. Taka intencja **steruje tym, co przygotowujesz i co
  pokazujesz w świecie** (zapisz ją w `state/objectives.yaml` jako plan gracza albo w
  `planning/lucan-leads.yaml`), ale sama się nie wykonuje — potrzebuje normalnej deklaracji
  poza nawiasem. Wiadomość wyłącznie z nawiasu zatrzymuje scenę: odpowiedz poza grą i nie
  commituj tury. Wyjątek: zatwierdzenie korekty kanonu może zmienić pliki, wciąż bez czasu.
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

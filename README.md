# GameMaster

Lokalny system prowadzenia długiej kampanii RPG z agentem jako mistrzem gry. Projekt rozdziela stałe reguły, kanon świata, aktualny stan kampanii i niezmienny dziennik wydarzeń, dzięki czemu narrator nie musi polegać na długości wątku rozmowy.

## Jak zacząć turę

1. Narrator czyta `AGENTS.md`.
2. `campaigns/lucan/context/active.yaml` wskazuje minimalny potrzebny kontekst.
3. `campaigns/lucan/context/scene.yaml` opisuje aktualną sytuację.
4. Po turze narrator zapisuje wydarzenie oraz aktualizuje zmienione pliki stanu.

Pliki kampanii Lucana przechodzą migrację z dostępnego scalonego przebiegu historii. Pola oznaczone `needs_review` nie stanowią aktywnego kanonu, dopóki pakiety migracji nie zostaną zatwierdzone i aktywowane atomowo.

Migracja historii jest przygotowana w [campaigns/lucan/migration](campaigns/lucan/migration/README.md). Scalony lokalny przebieg jest wystarczającą bazą roboczą; późniejszy pełny eksport ChatGPT może służyć do audytu kompletności, lecz nie blokuje obecnego procesu.

## Formaty

- Markdown: reguły, opisy, motywacje i materiały narracyjne.
- YAML: aktualny stan oraz dane łatwe do ręcznej edycji.
- JSONL: dopisywany dziennik wydarzeń, rzutów i retconów; jeden obiekt JSON na linię.
- SVG: deterministyczne mapy lokacji.

Wszystkie pliki tekstowe zapisujemy w UTF-8.

## Główne katalogi

- `system/` — reguły niezależne od kampanii.
- `worlds/` — statyczny kanon świata.
- `campaigns/` — zmienny stan konkretnej rozgrywki.
- `templates/` — niekanoniczne wzory nowych danych.
- `tools/` — lokalna walidacja projektu.

## Walidacja

Uruchom w PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ./tools/validate-project.ps1
```

Lokalny Windows blokuje bezpośrednie uruchamianie skryptów PowerShell. Jawne `-ExecutionPolicy Bypass` dotyczy tylko tego jednego procesu i nie zmienia ustawień systemowych.

Walidator sprawdza wymagane pliki, kodowanie, podstawową strukturę YAML, poprawność JSONL i XML map SVG.

## Rzut d100

Narzędzie zapisuje wynik w dzienniku przed narracją i odmawia ponownego użycia tego samego identyfikatora:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ./tools/roll-d100.ps1 `
  -Id roll_000001 `
  -SceneId scene_example `
  -Subject pc_lucan `
  -Intent 'Przemknąć obok strażnika' `
  -Scope execution `
  -Stakes 'Alarm albo bezpieczne przejście' `
  -Difficulty 60 `
  -CharacterScore 7 `
  -Modifier 'darkness=10'
```

Skrypt zapisuje surowy wynik, modyfikatory, porównanie z progiem i ewentualny krytyk. Pole `interpretation` pozostaje puste, dopóki narrator nie odniesie wyniku do podmiotu i fikcji.

## Silnik możliwości

Silnik skali 0–100 rozstrzyga, czy zamiar jest możliwy przed dopuszczeniem rzutu:

```powershell
C:\ProgramData\anaconda3\python.exe tools\gm.py assess `
  --actor fixture_spidey `
  --capability capability_spidey_bite `
  --target fixture_horse `
  --intent intent_decapitate
```

Kompilowanie warstwowego bytu i walidacja mechaniki:

```powershell
C:\ProgramData\anaconda3\python.exe tools\gm.py compile fixture_spidey
C:\ProgramData\anaconda3\python.exe tools\gm.py validate
```

Dane w `system/fixtures/vertical-slice/` są niekanoniczną kalibracją systemu.

Rzadkie brutalne skalowanie znanego czaru można wycenić bez tworzenia nowej
zdolności. To dodatkowy podgląd używany tylko przy metamagii, więc nie obciąża
zwykłych tur:

```powershell
C:\ProgramData\anaconda3\python.exe tools\gm.py amplify `
  --capability capability_lucan_bone_chill `
  --target-tier 6 `
  --axis intensity --axis area --axis range --axis persistence `
  --expertise 32 --available-energy 5000 --channel-intervals 3 `
  --linked-channel-capacity 20 --energy-source collector_overflow
```

Reguła i tabela kosztów znajdują się w `system/metamagic.md` oraz
`system/mechanics/metamagic-scale.yaml`. Brak energii lub ekspertyzy blokuje
rzut i zwraca `possible_only_with_new_leverage`.

## Otwarcie sesji

Rozmowa jest jednorazowa, stan jest w plikach. Sesję otwiera jeden blok:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\gm.ps1 brief
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\gm.ps1 brief --full
```

`brief` zwraca scenę, czas, zegary, cele, uczestników ze stanem oraz listę plików
do wczytania wraz z ich rozmiarami i budżetem kontekstu. `--full` dokleja treść
tych plików — do wklejenia w czacie, który nie ma dostępu do dysku.

Po zamknięciu sceny zacznij nową rozmowę i znów wywołaj `brief`. Powód: każda tura
wysyła całą dotychczasową rozmowę od nowa, więc jej koszt rośnie z kwadratem
długości. Pomiary i uzasadnienie w `DECISIONS.md`.

## Pętla normalnej tury

Request i outcome korzystają z szablonów w `templates/journal/`.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\gm.ps1 turn preview --request request.yaml
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\gm.ps1 turn resolve --request request.yaml
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\gm.ps1 turn commit turn_000001 --outcome outcome.yaml
```

`resolve` wykonuje co najwyżej jeden potrzebny rzut. `commit` atomowo nalicza koszty, warunki, czas, zegary i reakcje świata oraz buduje kontekst następnej odpowiedzi. `--allow-noncanonical` służy wyłącznie do prób migracyjnych.

Wyjście tych komend jest domyślnie skrócone do samych decyzji: werdykt, wynik rzutu, koszty, zmienione pliki, należne reakcje świata i nowe pytanie decyzyjne. `--verbose` drukuje pełny dokument transakcji; ten sam dokument zawsze leży w `journal/transactions/<turn_id>.yaml`.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\gm.ps1 recall Varkhen --limit 5
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\gm.ps1 context refresh --dry-run
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\gm.ps1 migration status
```

Aktywny kontekst ma budżet 40 KB i nigdy nie ładuje surowego eksportu ani gałęzi niekanonicznej. Przekroczenie budżetu oraz brakujące referencje są raportowane w `context_warnings` wraz z listą najcięższych plików (`heaviest_refs`) — nie przerywają tury, bo commit jest wtedy już trwały. `context refresh --strict` zwraca w takiej sytuacji kod błędu i służy do walidacji.

Replay reprezentatywnych scen kampanii:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\gm.ps1 replay campaign_lucan_replay_v1
```

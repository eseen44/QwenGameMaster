# Cykl życia plików kampanii

Ta tabela jest kompletną mapą aktualizacji: każdy plik projektu wpada w dokładnie jedną klasę poniżej. „Tura” oznacza wyłącznie zatwierdzony `gm turn commit`; tekst w nawiasie niczego nie aktualizuje.

| Ścieżka lub plik | Klasa | Kiedy wolno aktualizować |
|---|---|---|
| `system/**`, `worlds/**`, `templates/**`, `tools/**` | stałe reguły i narzędzia | Wyłącznie przy świadomej zmianie systemu albo świata; nigdy jako skutek zwykłej tury. |
| `campaigns/*/migration/sources/**`, `migration/noncanonical/**` | archiwum źródeł | Nigdy podczas gry. Dodanie źródła wymaga osobnej migracji; istniejącego tekstu nie nadpisujemy. |
| `campaigns/*/migration/packages/**`, `migration/candidates/**`, `migration/conflicts/**`, `migration/approvals/**`, `migration/audits/**` | proces migracji | Tylko podczas przeglądu, korekty albo zatwierdzania pakietu; nigdy przez `turn commit`. |
| `campaigns/*/migration/mechanics/**` | kandydat mechaniczny | Tylko podczas kalibracji/replayu i rewizji mechaniki; po aktywacji definicje są kopiowane do kanonu, nie mutowane turą. |
| `campaigns/*/planning/**`, `TODO.md` | planowanie | Tylko przy jawnej decyzji planistycznej MG/gracza; nie jako automatyczny skutek sceny. |
| `DECISIONS.md` | dziennik decyzji technicznych | Dopisz wpis przy nieoczywistej zmianie systemu, narzędzi albo reguł — razem z uzasadnieniem i tym, czego świadomie nie zrobiono. Nigdy turą; nie usuwaj starych wpisów. |
| `campaigns/*/journal/events.jsonl` | dziennik niezmienny | Dopisz dokładnie jeden wpis po każdym udanym `turn commit` z trwałą konsekwencją. |
| `campaigns/*/journal/rolls.jsonl` | dziennik niezmienny | Dopisz przed narracją wyłącznie, gdy `turn resolve` wykonał test. |
| `campaigns/*/journal/retcons.jsonl` | dziennik niezmienny | Dopisz przy poprawie faktu historycznego; nigdy nie usuwaj starego wpisu. |
| `campaigns/*/context/scene.yaml` | bieżąca scena | Każdy `turn commit`, który zmienia uczestników, lokację, napięcie, presję, pytanie lub reakcję świata; obowiązkowo przy otwarciu/zamknięciu sceny. |
| `campaigns/*/context/active.yaml` | minimalny kontekst | Po każdym commicie, gdy zmienia się zestaw potrzebnych plików; zawsze po zmianie sceny. Generuje `gm context refresh`. |
| `campaigns/*/state/time.yaml` | czas i faza kampanii | Gdy akcja ma czas większy od zera albo zostaje domknięty downtime. `campaign_phase` i `roll_policy` zmieniaj wyłącznie przy jawnie zatwierdzonym przejściu między interludium i aktem. |
| `campaigns/*/state/clocks.yaml` | zegary i reakcje świata | Gdy czas, konsekwencja albo decyzja zmienia postęp zegara; należną reakcję dodaj też do sceny. |
| `campaigns/*/state/instances/*.yaml` | zmienny stan bytów | Gdy byt zmienia pozycję, integralność, zasób, warunek, właściciela, rozkaz lub rewizję. Używaj operacji transakcyjnych, nie ręcznego nadpisania. |
| `campaigns/*/state/resources.yaml` | dobra, dowody, świadkowie, saldo | Gdy zmieniają się pieniądze, własność, dowód, świadek, dług lub zasób wspólny. |
| `campaigns/*/state/objectives.yaml` | cele | Gdy cel zostaje przyjęty, usunięty, zmienia etap albo otrzymuje nowe pytanie decyzyjne. |
| `campaigns/*/state/reputations.yaml` | relacje i reputacje | Po społecznej konsekwencji, ale tylko gdy faktycznie zmieniła nastawienie, status albo dostęp. |
| `campaigns/*/relationships/*.yaml` | relacje osobiste | Po trwałej zmianie współpracy, wiary w osąd, zaufania do dyskrecji, osobistego stosunku, długu, dźwigni albo ograniczenia. Zmieniaj wyłącznie naruszony wymiar. |
| `campaigns/*/state/secrets.yaml` | sekrety i ekspozycja | Gdy ktoś poznaje, zaczyna podejrzewać, zapomina, fałszuje lub publicznie ujawnia sekret. |
| `campaigns/*/player/{character,abilities,inventory,progression,background}.yaml`, `personality.md` | trwały rozwój Lucana | Tylko po trwałej zmianie: rana, koszt, nowa zdolność, rzecz, reputacja rangi, postęp albo świadoma rewizja postaci. |
| `campaigns/*/companions/*.yaml` | stan i rozkazy sług | Gdy sługa zmienia zasób, obrażenie, lokalizację, skład roju, rozkaz, autonomię albo relację. |
| `campaigns/*/entities/npcs/*.yaml`, `entities/factions/*.yaml` | fakty, wiedza, agenda i stan świata | Gdy dana postać/frakcja poznaje fakt, zmienia cel, pozycję, status, relację lub zasób. Nie zapisuj wiedzy, której nie zdobyła. |
| `campaigns/*/entities/**/index.yaml` | rejestry | Tylko gdy tworzymy lub archiwizujemy trwały byt. |
| `campaigns/*/entities/**/README.md` | dokumentacja | Tylko przy zmianie struktury, nie turą. |
| `campaigns/*/locations/*/state.yaml` | stan fizyczny lokacji | Gdy zmieniają się uszkodzenia, przeszkody, zagrożenia, mieszkańcy lub dostępność. |
| `campaigns/*/locations/*/discovery.yaml` i `maps/player.svg` | wiedza Lucana | Przy pierwszym odkryciu albo ujawnieniu elementu; mapa gracza nie może ujawnić więcej niż discovery. |
| `campaigns/*/locations/*/maps/layout.yaml` i `maps/gm.svg` | geometria MG | Tylko przy trwałej zmianie geometrii lub poprawce kanonu; wtedy zaktualizuj także stan i odpowiednią mapę gracza. |
| `campaigns/*/locations/*/{location.yaml,description.md}` | definicja lokacji | Tylko przy retconie, stałej zmianie połączeń albo dopisaniu pierwszego opisu; nie przy zwykłym przejściu przez lokację. |
| `campaigns/*/snapshots/**` | migawki | Dodaj nową migawkę przy zamknięciu sceny, przed migracją albo przed ryzykowną masową zmianą; nie nadpisuj istniejącej. |
| `campaigns/*/gm/**`, `campaigns/*/plots/**` | przygotowanie MG | Dodaj/aktualizuj po zmianie aktywnej agendy, ukrytej informacji albo wątku; pliki nigdy nie wchodzą automatycznie do kontekstu gracza. |
| `campaigns/*/campaign.yaml`, `locations/index.yaml`, `companions/index.yaml` | konfiguracja kampanii | Tylko przy aktywacji migracji, dodaniu trwałej lokacji/sługi albo zmianie statusu kampanii. |

## Procedura kontroli po turze

1. Narrator zapisuje wydarzenie i ewentualny rzut.
2. Porównuje konsekwencje z tabelą powyżej i aktualizuje tylko pasujące pliki.
3. Dla każdego zmienionego YAML ustawia właściwy `last_event_id` albo `last_updated_event_id`, jeśli schemat go posiada.
4. Odświeża scenę i minimalny kontekst.
5. Uruchamia `tools/validate_project.py` po zmianie sceny, migracji, mapy albo danych strukturalnych.

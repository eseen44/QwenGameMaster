# Runtime tury i trwały stan

## Zasada

Definicje opisują, co byt potrafi. Instancje w `campaigns/<id>/state/instances/` przechowują stan zmienny: pozycję, integralność, zasoby, warunki, rewizję i źródło ostatniej zmiany.

Typowa tura używa najwyżej dwóch zapisujących wywołań:

1. `turn resolve` ocenia możliwość, zapisuje niezmienny rzut, jeżeli jest potrzebny, i tworzy oczekującą transakcję;
2. `turn commit` przyjmuje interpretację narratora, atomowo aktualizuje stan, zapisuje wydarzenie i odświeża kontekst.

`turn preview` jest całkowicie bez zapisu.

## Wywołanie dla agentów w Linuxie

`--request` i `--outcome` oznaczają ścieżkę do pliku YAML. Agent może zamiast
tego przekazać obiekt JSON bez tworzenia pomocniczego pliku:

```bash
python tools/gm.py turn resolve --campaign-root campaigns/lucan \
  --request-json '{"turn_id":"turn_example","declared_action":"Lucan otwiera sakiewkę.","fiction_verdict":"automatic","time_seconds":0}'

python tools/gm.py turn commit turn_example --campaign-root campaigns/lucan \
  --outcome-json '{"intent_achieved":true,"arrangement":"unchanged","perspective":"pc_lucan","summary":"Lucan otworzył sakiewkę.","operations":[]}'
```

Nie uruchamiaj `resolve` dla samego opisu stanu bez konsekwencji. Normalna tura
nigdy nie zmienia `system/**`, `tools/**`, `.gitignore` ani konfiguracji Git.

## Wynik narracyjny

Outcome rozdziela `intent_achieved`, szerszy `arrangement` i `perspective` testowanego podmiotu. Sukces Lucana może zatem pogorszyć świat, a porażka przeciwnika poprawić pozycję Lucana bez nazywania tego porażką gracza.

## Bezpieczeństwo zapisu

- Rewizja chroni przed nadpisaniem nowszego stanu.
- Ten sam identyfikator tury nie może zostać użyty ponownie.
- Przygotowane zapisy mają hashe wersji przed i po zmianie.
- `turn recover` kończy przerwany commit bez podwójnego kosztu lub wydarzenia.
- Rzutu nie usuwa się po `turn abort`.

## Czas i kontekst

Klasy `instant`, `brief` i `significant` są przeliczane przez poziom napięcia. `extended` wymaga jawnej liczby sekund. Upływ czasu rozwija warunki, zasoby i zegary. Należna reakcja świata musi zostać rozstrzygnięta przed kolejnym commitem.

`context refresh` ładuje scenę, uczestników, lokację, zegary i cele do limitu 40 KB. Surowe źródła migracji, gałąź niekanoniczna i pełne dzienniki są zabronione. `recall` służy do punktowego przeszukiwania historii.

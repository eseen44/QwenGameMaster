# Lokacje, pierwsze wejście i mapy

## Co jest lokacją

Osobny wpis otrzymuje miejsce, którego układ, stan, mieszkańcy albo połączenia mogą wpływać na decyzje. Pojedynczy niczym niewyróżniający się fragment korytarza nie wymaga własnego katalogu; może być strefą większej lokacji.

## Pierwsze wejście

Przed poproszeniem gracza o pierwszą decyzję narrator:

1. ustala punkt wejścia i perspektywę Lucana;
2. podaje ogólne wrażenie oraz najważniejsze bodźce zmysłowe;
3. opisuje widoczną geometrię, punkty orientacyjne i przybliżone odległości;
4. wskazuje widoczne wyjścia i dostępne kierunki ruchu;
5. przedstawia zauważalnych mieszkańców, aktywność, przeszkody i zagrożenia;
6. pokazuje oczywiste możliwości wykorzystania otoczenia;
7. pokazuje lub linkuje aktualną mapę gracza;
8. zapisuje wizytę i ujawnione strefy w `discovery.yaml`.

Oczywiste informacje nie wymagają rzutu. Ukryte przejście, zamaskowana pułapka albo właściwa interpretacja śladów mogą wymagać działania i testu.

## Kolejne wizyty

Przy powrocie podaj krótki punkt orientacyjny i różnice względem ostatniej wizyty. Pełny opis wraca na prośbę gracza albo po dużej zmianie geometrii lub funkcji miejsca.

## Pliki lokacji

- `location.yaml`: tożsamość, hierarchia, skala i stałe połączenia.
- `description.md`: materiał do opisu pierwszego wejścia i późniejszych przypomnień.
- `state.yaml`: mieszkańcy, blokady, uszkodzenia, zagrożenia i zmiany.
- `discovery.yaml`: wiedza Lucana, wizyty i ujawnione strefy.
- `maps/layout.yaml`: autorytatywna geometria oraz stabilne identyfikatory stref.
- `maps/gm.svg`: pełny schemat narratora.
- `maps/player.svg`: wyłącznie ujawniona wiedza Lucana.

## Zasady mapy

- SVG ma zawierać tytuł, północ, skalę, legendę, wejścia, przeszkody i identyfikatory stref.
- Wnętrza używają metrów; kompleksy i ulice także czasu przejścia; dzielnice godzin lub minut; regiony godzin albo dni.
- `layout.yaml` ma pierwszeństwo przed przypadkowym sformułowaniem w narracji.
- Mapa gracza nie pokazuje sekretów, nawet jeśli istnieją na mapie MG.
- Zmiana geometrii wymaga aktualizacji layoutu, stanu i odpowiednich SVG.
- Obraz klimatyczny może uzupełniać opis, ale nie ustala geometrii.


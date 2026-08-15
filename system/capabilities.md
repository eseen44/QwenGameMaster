# Możliwości, skala i ocena działania

## Zasada nadrzędna

Test d100 nie tworzy możliwości, której podmiot nie posiada. Przed testem narrator uruchamia ocenę mechaniczną. Jeżeli wynik to `impossible`, rzut jest zabroniony. Jeżeli wynik to `automatic`, rzut jest zbędny.

Skala 0–100 jest logarytmiczna i opisuje pojedynczy kanał działania, nie ogólny poziom postaci. Siła fizyczna, cięcie, penetracja, trucizna, ukrywanie, kontrola umysłu i odporności są oddzielnymi wartościami.

Ranga gildii jest klasyfikacją operacyjną. Nie jest średnią statystyk ani gwarancją zwycięstwa. Wąski gimmick może przekraczać typową rangę bytu, jeżeli wymaga przygotowania, ponosi koszt i ma realne kontrujące słabości.

## Typy wyniku oceny

- `impossible`: obecna metoda nie może osiągnąć zamiaru; test jest zabroniony.
- `possible_only_with_new_leverage`: potrzebna jest nowa słabość, narzędzie, warunek albo pomoc.
- `contested`: zdolność i obrona są porównywalne; test może rozstrzygnąć niepewność.
- `conditional`: efekt jest osiągalny po spełnieniu warunków dostarczenia; test może dotyczyć dostępu, nie samej fizyki efektu.
- `automatic_with_cost`: zamiar następuje bez testu, ale zużywa określony zasób albo powoduje pewną konsekwencję.
- `automatic`: rezultat wynika bezpośrednio z parametrów i sytuacji.

## Warstwy obiektu

Byt może powstawać z archetypu i modyfikatorów. Przykładowo Spidey to mały pająk, animacja nekromantyczna, naturalna nekrotyczna wydzielina, pancerz chitynowy, większe szczękoczułki, wszczepione wężowe kły z osobnym gruczołem paraliżującej toksyny i kotwica śmierci. Kompilator zachowuje listę warstw będących źródłem wartości.

Każdy wygenerowany obiekt otrzymuje status `proposed`. Generator nie aktywuje kanonu.

## Zasoby sług

Połączenie nie oznacza wspólnego magazynu. Każdy sługa może mieć własną baterię, autonomiczne polowanie, tempo zaniku i próg głodu. Łącze określa osobno komendy, telemetrię, transfer zmysłów, przepustowość energii i straty transferu.

## Klątwy

Ocena klątw rozdziela dostarczenie od odporności na efekt. Zastosuj `system/curses.md`: subtelny cantrip może ominąć aktywną obronę nieświadomego cywila, lecz nie daje uniwersalnej przewagi nad przygotowanym agentem, a zwiększenie mocy podnosi koszt, czas, widoczność i ślad magiczny.

## Narzędzie

Ocena zamiaru:

```powershell
C:\ProgramData\anaconda3\python.exe tools\gm.py assess --actor fixture_spidey --capability capability_spidey_bite --target fixture_horse --intent intent_decapitate
```

Walidacja obiektów:

```powershell
C:\ProgramData\anaconda3\python.exe tools\gm.py validate
```

Pionowy wycinek w `system/fixtures/vertical-slice/` jest kalibracją i testem systemu, nie aktywnym stanem kampanii.

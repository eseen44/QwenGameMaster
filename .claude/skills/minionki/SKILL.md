---
name: minionki
description: >-
  Drukuje tabelę całej sieci nieumarłych Lucana: gdzie każdy stoi, jaki ma stały rozkaz,
  ile ma w zbiorniku i integralności, jaka jest jego stawka dobowa, bank wzrostu i ile mu
  brakuje do następnego szczebla drabiny. Wywołuj, gdy gracz pisze „minionki”, „stan sieci”,
  „tabela sług”, „kto ma jakie rozkazy”, „czy wszyscy się odliczają”, „przegląd okazów”
  albo wywołuje /minionki. To jest ODCZYT poza turą — nie przesuwa czasu i nie zmienia
  żadnego pliku.
---

Uruchom z katalogu głównego repozytorium:

```powershell
python tools/roster.py
```

Przydatne warianty: `--sort bank` (najbliżej szczebla na górze), `--sort rate`,
`--sort miejsce`, `--problems` (same uwagi), `--wide` (pełne identyfikatory rozkazów),
`--debt` (rozwinięte listy długu migracyjnego).

## Jak podać to graczowi

Wynik jest tabelą dla człowieka, nie protokołem — przekaż go jako tabelę i **nie wklejaj
go do narracji**. To nie jest tura: czas nie rusza, `turn commit` nie wchodzi w grę.

Trzy rzeczy, które trzeba przy okazji powiedzieć, bo sama tabela je przemilcza:

1. **Sekcja „DO ROZSTRZYGNIĘCIA" to lista decyzji, nie błędów narzędzia.** Pozycja `stale`
   albo `unknown` znaczy, że nikt tego okazu nie widział od podanej tury — narratorowi nie
   wolno opisywać go tak, jakby wiedział, gdzie jest (`retcon_000171`).
2. **Dług migracyjny jest zwinięty celowo.** Brakujące `position.fix` i pozostałe
   `position.formation` to jedna sprawa powielona przez trzydzieści plików. Nie zgłaszaj jej
   jako trzydziestu problemów i nie proponuj masowej naprawy w środku sceny.
3. **Rejestr wzrostu ma własne `as_of`.** Jeśli jest daleko za bieżącą turą, banki są
   nieaktualne — rozliczenie robi `python tools/growth_settle.py`, ręcznie, po decyzji.

Skrypt świadomie NIE liczy składnika doświadczenia (+1 za scenę roboty, `retcon_000180`),
bo nie wie, która scena była robotą. Ten wpis robi narrator w turze.

Pokrewne narzędzia, gdy pytanie jest węższe: `tools/servants_check.py` (bramka strukturalna),
`tools/reconcile_growth.py --check` (zgodność nadwyżki ze stawkami),
`tools/audit_stock.py` (zapas), `tools/commitments_freshness.py` (zobowiązania).

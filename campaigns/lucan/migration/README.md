# Migracja kampanii Lucana

Ten katalog jest obszarem roboczym. Żaden fakt zapisany tutaj nie jest aktywnym kanonem, dopóki wszystkie wymagane pakiety nie zostaną zatwierdzone i atomowo przeniesione do właściwych plików kampanii.

## Aktualny stan

Scalony lokalny przebieg historii jest przyjętą bazą roboczą migracji. Pełny eksport rozmowy ChatGPT pozostaje opcjonalnym późniejszym audytem kompletności; nie blokuje aktywacji, jeżeli bieżące pakiety uzyskają zatwierdzenie użytkownika.

## Przebieg

1. Utrzymywać scalony przebieg i źródła jako dowody kandydatów.
2. Przygotować oraz zatwierdzić siedem pakietów w kolejności z `packages/index.yaml`.
3. Wykonać wspólną walidację.
4. Dopiero wtedy atomowo zaktualizować aktywne pliki kampanii.
5. Po otrzymaniu pełnego eksportu wykonać audyt kompletności bez cichego nadpisywania kanonu.

## Zakazy

- Nie ładować `sources/` ani `noncanonical/` podczas zwykłej tury gry.
- Nie traktować statusu `approved` pojedynczego pakietu jako aktywnego kanonu.
- Nie odtwarzać dawnych rzutów, których rzeczywistych wyników nie da się potwierdzić.
- Nie wykorzystywać materiału po granicy kanonu jako jedynego źródła wcześniejszego faktu.

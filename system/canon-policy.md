# Kanon, stan i korekty

## Rodzaje informacji

- `confirmed`: fakt potwierdzony w świecie albo przez autorytatywne źródło.
- `suspected`: uzasadnione podejrzenie konkretnego podmiotu.
- `rumor`: informacja krążąca w świecie bez potwierdzenia.
- `false_belief`: przekonanie podmiotu sprzeczne z aktualnym kanonem.
- `gm_only`: fakt prawdziwy, lecz jeszcze niedostępny Lucanowi.
- `uncertain`: luka, której nie wolno rekonstruować z nadmierną pewnością.

## Priorytet

**Wiążącą wersją tej listy jest `AGENTS.md#priorytet-źródeł`** — tam stoi też reguła
rozstrzygania sprzeczności MIĘDZY retconami (wygrywa wyższy numer, nie późniejszy timestamp),
której ta kopia nie ma. Kopia poniżej zostaje dla kontekstu taksonomii wyżej; przy rozjeździe
obowiązuje AGENTS.md. Duplikacja reguł jest w tym repo zdiagnozowaną chorobą — nie rozwijaj
tej listy tutaj, tylko tam.

1. Retcon zatwierdzony w `retcons.jsonl`.
2. Aktualny stan kampanii i właściwego bytu.
3. Reguły systemu i kanon świata.
4. Dziennik wydarzeń.
5. Transkrypt i pamięć narratora.

## Natychmiastowy zapis

Zapisz stan po zmianie:

- miejsca, czasu lub poziomu napięcia;
- pieniędzy, własności, ekwipunku i zasobów;
- obrażeń, warunków i zdolności;
- relacji, reputacji, wiedzy lub podejrzenia;
- dowodu, świadka, listu gończego albo zainteresowania frakcji;
- celu, zegara, wątku lub sekretu;
- geometrii i stopnia odkrycia lokacji.

## Retcon

Nie kasuj historycznego wpisu. Dodaj do `retcons.jsonl` rekord wskazujący zastępowane identyfikatory, przyczynę, nową treść i czas zatwierdzenia. Następnie popraw bieżące pliki stanu. Jeżeli korekta zmienia mapę, zaktualizuj też layout i widoki.

## Wiedza NPC

Ważny NPC przechowuje osobno fakty potwierdzone, podejrzenia, fałszywe przekonania oraz informacje wrażliwe, których jeszcze nie zna. Narrator nie może przenosić wiedzy między NPC bez zdarzenia będącego źródłem tej wiedzy.

**`claim` zapisuje FAKT, nie twoją interpretację i nie twój nastrój.** Wpis ma powiedzieć, co
postać wie i skąd, w jednym–dwóch zdaniach. Nie zaczynaj od oceny („najzimniejszy wniosek tej
sceny"), nie krzycz wersalikami i nie dopisuj listy tego, czego nie zrobiłeś — to należy do
`outcome.audit`. Powód jest mierzalny: `knowledge` jest największym blokiem tekstu o tej
postaci w aktywnym kontekście (w skrócie karty Kesza 8,3 KB przy 0,4 KB o tym, jak brzmi),
więc jego rejestr działa jak wzorzec stylu i wraca w dialogu. Głos postaci bierze się
wyłącznie z `entities/npcs/voices/<npc>.yaml` (`system/npc-voice.md`); skrót karty gasi
wersaliki w `claim`, ale nie naprawi zdania napisanego jak protokół.


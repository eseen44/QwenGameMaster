# Kanon, stan i korekty

## Rodzaje informacji

- `confirmed`: fakt potwierdzony w świecie albo przez autorytatywne źródło.
- `suspected`: uzasadnione podejrzenie konkretnego podmiotu.
- `rumor`: informacja krążąca w świecie bez potwierdzenia.
- `false_belief`: przekonanie podmiotu sprzeczne z aktualnym kanonem.
- `gm_only`: fakt prawdziwy, lecz jeszcze niedostępny Lucanowi.
- `uncertain`: luka, której nie wolno rekonstruować z nadmierną pewnością.

## Priorytet

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


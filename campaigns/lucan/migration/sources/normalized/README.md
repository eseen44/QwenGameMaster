# Znormalizowane źródła

Importer utworzy tutaj przeszukiwalny transkrypt UTF-8 i JSONL aktualnej gałęzi rozmowy. Te pliki są materiałem dowodowym migracji, nie bieżącą pamięcią narratora.

## Domyślny zapis historyczny

`historical-full-run.utf8.txt` jest jednym, odduplikowanym przebiegiem całej obecnie odzyskanej historii. Do zwykłego wyszukiwania używamy właśnie jego, nie trzech plików składowych.

- Linie `1-13692`: cały obecnie odzyskany materiał kanoniczny, do pytania Seraphine o ciała na wysypisku.
- Nie ma już wydzielonej gałęzi po granicy wewnątrz tego pliku; przyszła odpowiedź i domknięcie przygody nie zostały jeszcze rozegrane.
- `historical-full-run.manifest.yaml`: odwzorowanie zakresów na oryginalne pliki i opis pominiętych duplikatów.

Plik nie jest automatycznie ładowany do kontekstu narratora. Służy do `recall`, migracji i kontroli źródeł.

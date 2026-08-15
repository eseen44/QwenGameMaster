# Import pełnego eksportu ChatGPT

Eksport może być plikiem ZIP pobranym z ChatGPT albo samym `conversations.json`. Importer zapisuje wyłącznie rozmowę `E-rank Warlock Historia`.

## Uzyskanie eksportu

Według oficjalnej dokumentacji OpenAI:

1. Zaloguj się do ChatGPT.
2. Otwórz menu profilu i wybierz `Settings`.
3. Przejdź do `Data controls`.
4. Przy `Export data` wybierz `Export`, a następnie potwierdź.
5. Pobierz ZIP z wiadomości e-mail lub SMS.

Eksport może być przygotowywany do 7 dni, a link do pobrania wygasa po 24 godzinach. Oficjalna instrukcja: https://help.openai.com/en/articles/7260999-how-do-i-export-my-chatgpt-history-and-data

Nie rozpakowuj ani nie kopiuj całego eksportu konta do projektu. Przekaż importerowi ścieżkę do ZIP; zapisze wyłącznie właściwą rozmowę.

```powershell
& 'C:\ProgramData\anaconda3\python.exe' tools\import_chatgpt_export.py `
  'C:\ścieżka\do\export.zip' `
  --conversation-id '6a78f0a9-2f98-83ed-9f2a-9f67baf65808'
```

Jeżeli identyfikator w eksporcie jest inny, można pominąć `--conversation-id`; importer wybierze dokładny tytuł. Gdy kilka rozmów ma ten sam tytuł, wymagany jest identyfikator.

Importer:

- wybiera aktualną gałąź kończącą się w `current_node`;
- sprawdza ciągłość rodziców;
- zapisuje surowy obiekt właściwej rozmowy;
- tworzy przeszukiwalny TXT i JSONL;
- sprawdza minimalną liczbę wiadomości oraz markery początku, Orena i Varkhena;
- nie aktywuje kampanii i nie wyznacza automatycznie granicy kanonu.

Istniejących wyników nie nadpisuje bez jawnego `--force`.

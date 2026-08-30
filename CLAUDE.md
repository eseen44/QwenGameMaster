# Claude — bootstrap kampanii GameMaster

To repo jest źródłem prawdy. Nie rekonstruuj kampanii z pamięci rozmowy ani z przypadkowych
wyników wyszukiwania GitHuba.

1. Pracuj na domyślnej gałęzi `codex/initial-game-master`. Jeżeli checkout wskazuje inną
   gałąź albo lokalny stan jest za `origin`, zatrzymaj się przed prowadzeniem gry.
2. Przeczytaj `AGENTS.md` i wykonaj `tools/gm.ps1 brief` albo, bez PowerShella,
   `python tools/gm.py brief`.
3. Przeczytaj pliki z `rules`, `load` oraz **każdy plik z `participant_refs`**. Karty NPC
   są obowiązkowe przed napisaniem ich pierwszej kwestii.
4. Zatwierdzony retcon i aktualny stan biją dziennik. `journal/transactions/` jest śladem
   audytowym, nie aktywnym kontekstem; używaj `gm recall` zamiast przeszukiwać go szeroko.
5. W obecnym interludium rzuty są wyłączone. Nie twórz oporu, terminu, zagrożenia ani
   komplikacji bez istniejącego źródła kanonicznego lub jawnej deklaracji gracza.
6. Nie zmieniaj celu sceny i nie wykonuj za Lucana kolejnej akcji. Najpierw rozstrzygnij
   dokładnie jego deklarację, potem pokaż proporcjonalną reakcję świata.

Pełny playbook znajduje się w `SKILL-gramy.md`. Wczytaj go przy otwieraniu nowej sesji gry;
nie trzeba go ponownie ładować w każdej turze tej samej krótkiej sceny.

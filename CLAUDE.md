# Claude — bootstrap kampanii GameMaster

To repo jest źródłem prawdy. Nie rekonstruuj kampanii z pamięci rozmowy ani z przypadkowych
wyników wyszukiwania GitHuba.

1. Pracuj na domyślnej gałęzi `codex/initial-game-master`. Jeżeli checkout wskazuje inną
   gałąź albo lokalny stan jest za `origin`, zatrzymaj się przed prowadzeniem gry.
2. Przeczytaj `AGENTS.md` i wykonaj `tools/gm.ps1 brief` albo, bez PowerShella,
   `python tools/gm.py brief`.
3. Przeczytaj pliki z `rules`, `load` oraz **każdy plik z `participant_refs`**. Lista wybiera
   skrót NPC z głosem, a przy braku skrótu pełną kartę i głos. `entity_ref` to adres
   do doczytania konkretnego faktu, nie polecenie ładowania całego archiwum.
4. Zatwierdzony retcon i aktualny stan biją dziennik. `journal/transactions/` jest śladem
   audytowym, nie aktywnym kontekstem; używaj `gm recall` zamiast przeszukiwać go szeroko.
5. W obecnym interludium rzuty są wyłączone. Nie twórz oporu, terminu, zagrożenia ani
   komplikacji bez istniejącego źródła kanonicznego lub jawnej deklaracji gracza.
6. Nie zmieniaj celu sceny i nie wykonuj za Lucana kolejnej akcji. Najpierw rozstrzygnij
   dokładnie jego deklarację, potem pokaż proporcjonalną reakcję świata.
7. Ożywiaj otoczenie i dodawaj dobrowolne zaczepki także w spokojnej scenie. To nie
   komplikacje z punktu 5: nie narzucają terminu, zagrożenia ani obowiązku. Szczegóły:
   `system/narrator.md`, `system/npc-voice.md`, `retcon_000164`.
8. Do gracza trafia proza, nie audyt. Reguły narratora nie są prawdami świata ani
   wiedzą NPC. Przed kwestią ustal źródło informacji, perspektywę i stopień pewności.
9. `context_policy.source_budget_bytes` to budżet plików, nie limit modelu. W tej
   kampanii wynosi 96 KiB. Pozostaw miejsce na rozmowę, narzędzia i odpowiedź; większy
   abonament nie oznacza proporcjonalnie większego okna kontekstu. Nie skracaj sceny
   do trzech–sześciu zdań z powodu historycznego budżetu 40 KiB.

Pełny playbook znajduje się w `SKILL-gramy.md`. Wczytaj go przy otwieraniu nowej sesji gry;
nie trzeba go ponownie ładować w każdej turze tej samej krótkiej sceny.

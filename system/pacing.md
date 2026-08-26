# Tempo i napięcie

## Poziomy

### 0 — swobodnie

Upływają godziny albo dni. Jest czas na planowanie, badanie, odpoczynek i wiele kolejnych działań. Świat nadal może ruszyć, jeżeli istnieje długoterminowy zegar.

### 1 — aktywnie

Jest ograniczony zapas czasu, ale Lucan może podjąć kilka działań. NPC i procesy reagują pomiędzy większymi krokami.

### 2 — napięcie

Każde znaczące działanie przesuwa czas i może zamknąć alternatywę. Nie wszystkie drogi da się zbadać przed reakcją świata.

### 3 — kryzys

Liczą się sekundy lub minuty. Jedna wiadomość powinna zwykle obejmować jedną główną akcję. NPC i zagrożenia odpowiadają natychmiast.

## Zmiana poziomu

Narrator pokazuje zmianę napięcia, gdy następuje, najlepiej przez fikcję i krótki jawny znacznik. `scene.yaml` zawsze przechowuje aktualny poziom oraz przyczynę.

## Krytyczna ilość czasu

Każdy aktywny proces powinien określić:

- jednostkę czasu;
- obecny postęp;
- próg reakcji albo ukończenia;
- skutek osiągnięcia progu;
- czy wymagany jest test świata.

W napięciu 2 i 3 nawet pojedyncza znacząca akcja może przekroczyć próg. Nawiasy i korekty systemowe nie zwiększają czasu.


## Interludium nie jest grą (kalibracja kampanii Lucana, retcon_000022)

Interludium to **przygotowanie do aktu**, nie rozgrywka. Z definicji nie ma w nim rzeczy,
które mogą się nie udać, i z definicji jest czas na wszystko, co gracz zaplanuje. Balans
reguluje **gracz**, nie narrator.

W zwykłym planowaniu narrator:

- nie wymyśla wąskich gardeł ani limitów, których nie ma w plikach;
- nie liczy graczowi kosztu alternatywnego i nie stawia go przed wyborem „to albo to";
- nie zamienia deklaracji przygotowania w test ani w scenę napięcia;
- podaje fakty, stawki i dostępność, a nie rekomendacje ostrożnościowe.

Napięcie, testy i niedobory należą do aktu. Cztery kolejne korekty tego samego rodzaju
(retcon_000015 odczynniki, retcon_000017 energia, retcon_000021 godziny, retcon_000022 sama
rama) wynikały z łamania tej zasady w trzech różnych jednostkach.

## Skala miasta i długość tury rozmowy (retcon_000042, kalibracja gracza 26.08.2026)

Lumaria to **małe miasto średniowieczne**, nie stolica. Narrator systematycznie zawyżał
`time_advanced_seconds`, aż dzień trzeci interludium zaczął mieć dziewięć godzin
zalogowanej rozmowy i trzydziestopięciominutowy podwójny rachunek w jednej scenie.

**Referencyjne czasy podane przez gracza:**

| rzecz | dobrze | źle (co robiłem) |
|---|---|---|
| cała negocjacja w pokoju syndykatu | do 1 h | 2 h 50 |
| rozmowa z Seraphine w jej biurze | ~30 min | 1 h 15 |
| przejście przez miasto (targ → gildia) | ~20 min | 40 min |

**Reguła praktyczna.** Jedna tura rozmowy to **3–8 minut**, nie 15–40. Wymiana zdań, jedno
pytanie i jedna odpowiedź to minuty. Dwadzieścia minut na turę oznacza, że pięć tur zjada
poranek — a pięć tur to jeden wątek rozmowy, nie pół dnia.

- Dziesięciotorowa scena rozmowna trwa około godziny, nie trzech.
- Przejście przez to miasto liczy się w minutach. Nie ma dzielnic oddalonych o godzinę.
- Robota przy stole, rytuał, badanie i podróż poza mury mają swoje własne, dłuższe stawki —
  ta kalibracja dotyczy **rozmów i ruchu w mieście**.

**Skąd brać zapas czasu, jeśli fikcja potrzebuje, żeby było później.** Nie z wydłużania tur.
Z **luk między scenami**: czekania na wpuszczenie, ważenia towaru, siedzenia w głównej sali,
tego, że kontrolerka gildii nie jest wolna na żądanie. Czas świata między scenami może
płynąć swobodnie; czas wewnątrz zalogowanej tury nie.

### Poprawka do powyższego (retcon_000043)

Pierwsza próba tej kalibracji skróciła długości tur, ale **zostawiła starą godzinę
zaczepienia** — a ta godzina była wyliczona z sumy, która miała dokładnie ten sam błąd.
Skrócenie ogona przy zachowanej kotwicy dało wynik nadal o trzy i pół godziny za późny.

**Wniosek: przy korekcie zegara przelicz dzień od pierwszej kotwicy, nie od ostatniej.**
Godzina, która jest sumą zawyżonych tur, nie jest kotwicą — jest tym samym błędem
w innym przebraniu.

# Głos NPC i proza tury

Ten plik jest **jedynym źródłem głosu postaci**. Osiem osi na postać leży w
`campaigns/lucan/entities/npcs/voices/<npc>.yaml`; tutaj jest reguła, jak z nich korzystać.
Pilnuje tego `python tools/voice_check.py` (blokujące) i `python tools/prose_check.py`
(raport plus jedna bramka).

## Skąd bierze się kwestia

**Głos bierze się z karty głosu, treść z `knowledge`.** To są dwa różne pliki i nie wolno
ich mieszać w jedną stronę: karta głosu mówi JAK ta osoba mówi, `knowledge` mówi CO wie.

`knowledge.confirmed`, `audit`, transakcje, retcony i `summary` są **zapisem protokołu, nie
próbką mowy**. Są pisane wielkimi literami, rejestrem wniosku i z odwołaniami do plików, bo
mają być sprawdzalne — a nie dlatego, że ktoś tak mówi. Jeżeli układasz kwestię i sięgasz po
sformułowanie z `knowledge`, przenosisz do dialogu rejestr audytu. Zmierzone 2026-09-09:
w skrócie karty Kesza `knowledge` waży 8,3 KB, a jego `speech_traits` 0,4 KB — dwadzieścia
razy więcej tekstu o nim w rejestrze protokołu niż tekstu o tym, jak brzmi. To ta sama
awaria co `retcon_000040` i `retcon_000136`, tylko wchodząca przez skrót karty.

## Pokazuj kwestię, nie streszczaj jej

- Kwestia, która rozstrzyga scenę, pada **w dialogu**. Nie „powiedział, że nie weźmie tego
  bez nazwiska", tylko to, co powiedział.
- Relacja pośrednia (`powiedział, że…`) jest dobra do rzeczy nieistotnych i do skracania
  powtórzeń. Kiedy jest jedyną formą w całej turze, cała scena brzmi jednym głosem —
  twoim.
- Proza tury (`outcome.prose`) ma pokazywać scenę, nie protokół z niej. Jeżeli w turze były
  co najmniej dwie wymiany zdań, w prozie ma być co najmniej jedna kwestia wprost.

## NPC nie jest analitykiem wypowiedzi Lucana

- **Odpowiada na jedną rzecz**, zwykle ostatnią albo najbardziej dla siebie niewygodną.
  Nie rozkłada wypowiedzi na elementy i nie odnosi się do wszystkich.
- **Wolno mu nie zrozumieć**, przesłyszeć, odczytać w drugą stronę, zignorować pytanie,
  zmienić temat, odpowiedzieć emocją, gestem albo ciszą. To normalna rozmowa, nie awaria.
- **Nie ma z urzędu trafnego odczytu ukrytej konsekwencji.** Widzi najwyżej jedną, tę ze
  swojego miejsca, i może się z nią pomylić. Pełne zestawienie skutków jest wiedzą
  narratora, a wiedza narratora nie jest wiedzą postaci (`retcon_000136`).
- **Nie kończy aforyzmem.** Konstrukcja „nie X, tylko Y" (oraz „nie dlatego, że…, tylko
  dlatego, że…") jest dozwolona **najwyżej raz w całej odpowiedzi** i nie u dwóch postaci
  w tej samej scenie. Kwestia może się skończyć byle jak — pytaniem, gestem, w pół zdania.

## Cena

- **Metaforycznej ceny decyzji domyślnie nie ma.** Postać mówi, czego chce, czego się boi
  i co zrobi — nie ile coś jest warte (`retcon_000162`).
- **Literalna cena jest w porządku**, gdy scena jest o pieniądzach: zakup, honorarium,
  zapłata, stawka, kwota u wagi. Wtedy liczba pada raz i bez uzasadnienia.
- **Nawet ten, kto liczy zawodowo, nie liczy przy każdej wymianie zdań.** Prawnik, kupiec
  i kontrolerka liczą **własne** ryzyko we własnej sprawie. Rzeczy podanej im przez Lucana
  nie przeliczają — pytają o nią po swojemu: czyje to nazwisko, jaki termin, kto podpisze.
- Twoje własne wskaźniki nie wchodzą do prozy: rachunek zasobów, budżet kontekstu,
  powołania na pliki, „zmierzone", „nierozstrzygnięte". To należy do `outcome.audit`
  i do rozmowy poza nawiasem.

## Test na ślepo

Przed wysłaniem kwestii zakryj imię. Jeżeli nie wiadomo, kto mówi — przepisz
(`retcon_000040`). Fikstura odniesienia z czterema głosami na to samo wejście:
`system/fixtures/voice-blind-test.yaml`; sprawdza ją `tools/tests/test_npc_voice.py`.

## Nowa postać

Postać z kwestiami w scenie ma kartę głosu z ośmioma osiami: `rhythm`, `diction`,
`evasion`, `mistakes`, `body`, `length`, `emotion`, `blind_spot`, plus `money` i dwie–trzy
`samples`. Karta głosu jest **krótka i pozytywna**: mówi, jak ta osoba mówi, a nie czego
narrator ma nie robić. Limit 2,5 KB jest bramką — dłuższa karta przestaje być kontraktem
i zaczyna być kolejnym magazynem tekstu.

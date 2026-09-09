# Głos NPC i proza tury

Głos każdej ważnej postaci leży w jej **kontrakcie głosu**:
`campaigns/lucan/entities/npcs/voices/<npc>.yaml` — jedenaście osi i dwie–cztery próbki
kwestii. Tutaj jest reguła, jak z niego korzystać. Pilnują tego `tools/voice_check.py`
i `tools/prose_check.py`, oba blokujące, oba wpięte w `tools/preflight.py`.

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

## Ruch świata

Tura ma poruszyć świat, ale **ruch świata to nie diagnoza gracza**. Każde z poniższych jest
pełnym ruchem i żadne nie jest turą „słabszą":

- **gest** — odłożone pióro, zgaszona lampa, podany przedmiot;
- **milczenie** — i to nie jest wykręt, jeśli karta tak mówi;
- **zwyczajna odpowiedź** na to, o co gracz zapytał, bez drugiego dna;
- **częściowe niezrozumienie** albo dopytanie o rzecz oczywistą;
- **zmiana tematu** na własną sprawę tej postaci;
- **czynność fizyczna** — wstaje, przynosi papier, sortuje dalej;
- **błędny odczyt intencji Lucana** — postać nie ma racji z urzędu;
- **emocja bez analizy** — irytacja, ulga, zmęczenie, bez wniosku na koniec.

Nie ma reguły, która kazałaby NPC prześwietlić gracza. Presja brała się z tego, że
`outcome.new_decision` było w szablonie polem obowiązkowym, a najtańszy nowy dylemat
produkuje się cudzą przenikliwością. Pole jest od 2026-09-09 opcjonalne: puste zostawia
w mocy pytanie, które już stoi. Mechanizm:
`system/narrator-appendix.md#skad-brala-sie-przenikliwosc`.

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
(`retcon_000040`). Fikstura odniesienia: `system/fixtures/voice-blind-test.yaml` — dwa
wejścia, po cztery i pięć głosów, sprawdzane maszynowo przez
`tools/tests/test_npc_voice.py` (rozróżnialność długości, brak seryjnego „nie X, tylko Y",
próbki są kwestiami, nie opisami).

## Nowa postać

Postać z kwestiami w scenie ma `voice_contract` z jedenastoma osiami, w tej kolejności:

| oś | co opisuje |
|---|---|
| `sentences` | długość i budowa zdań |
| `answer_length` | domyślna długość odpowiedzi |
| `register` | słownictwo i rejestr |
| `evasion` | sposób unikania odpowiedzi |
| `body` | fizyczne odruchy |
| `mistakes` | typowe błędy i ograniczenia |
| `unnoticed` | czego zwykle nie zauważa |
| `emotion` | jak okazuje emocje |
| `blind_spot` | czego sama nie potrafi dobrze nazwać |
| `money` | kiedy w ogóle mówi o pieniądzach |
| `avoid` | konstrukcje, których u niej nie nadużywać |

Plus dwie–cztery `samples`, które są **kwestiami wprost**, nie opisami. Kontrakt jest
**krótki i pozytywny**: mówi, jak ta osoba mówi. `avoid` jest jedynym polem, w którym wolno
nazwać konstrukcję do unikania — jedno pole, nie cały plik. Limit 2,8 KB jest bramką: dłuższy
kontrakt przestaje być kontraktem i zaczyna być kolejnym magazynem tekstu.

`speech_traits` **nie istnieje już na kartach, które mają kontrakt głosu**. Dwa źródła głosu
obok siebie rozjeżdżają się i wygrywa dłuższe; u Kesza to krótsze kazało mu wyceniać, a
narrator powoływał się na nie w audytach tur 240, 242, 244 i 245.

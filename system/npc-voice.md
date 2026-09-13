# Głos NPC i proza tury

Głos każdej ważnej postaci leży w jej **kontrakcie głosu**:
`campaigns/lucan/entities/npcs/voices/<npc>.yaml` — jedenaście osi i dwie–cztery próbki
kwestii. Tutaj jest reguła, jak z niego korzystać. Pilnują tego `tools/voice_check.py`
i `tools/prose_check.py`, oba blokujące, oba wpięte w `tools/preflight.py`.

## Skąd bierze się kwestia

**Głos bierze się z karty głosu; wiedza wymaga drogi jej zdobycia.** Kontrakt opisuje
tendencje: długość zdań, gesty i błędy nie są obowiązkiem ani ograniczeniem inteligencji.
Nie odgrywaj wszystkich osi naraz i nie wyjaśniaj ich graczowi komentarzem narratora.
NPC potrafi rozwinąć odpowiedź, uczyć się i wnioskować w granicach doświadczenia.

Przed kwestią sprawdź wewnętrznie: **kto wie, co, skąd i z jaką pewnością**.
- Obserwacja: tylko to, co było dostępne tej osobie i jej zmysłom. Obecność przy Lucanie
  nie daje dostępu do jego myśli, prywatnego skanu, zasobów ani reguł narratora.
- Relacja: NPC wie, że ktoś coś powiedział; może mu wierzyć, ale to nie dowód prawdy.
- Wniosek i podejrzenie: wynikają z dostępnych przesłanek; język i zapis zachowują niepewność.
- Sekret lub brak źródła: NPC nie ujawnia go. Plik MG nie jest wspólną pamięcią postaci.

W `knowledge.confirmed` zapisuj zwięzły fakt zdobycia informacji i `source_event_id`;
dla nowych wpisów podawaj `acquisition` (observed/reported), `source_actor_id` przy
relacji i krótki `recall_summary` bez komentarza o prowadzeniu gry. Hipotezy należą do
`suspicions`, fałszywe przekonania do `false_beliefs`. Nie przepisuj uzasadnienia tury do
wiedzy. Wpis historyczny z audytem nie daje NPC wiedzy o systemie. Gdy skrót ma
`claim_truncated`, doczytaj konkretny wpis `claim_full` przed użyciem jego szczegółów;
pierwsze zdanie może pomijać zaprzeczenie albo warunek znajdujący się dalej.

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

- Odpowiada na to, co ma dla niego znaczenie. Może podjąć kilka powiązanych pytań,
  opowiedzieć wspomnienie lub dopytać; rozmowa nie wymaga odhaczania listy gracza.
- **Wolno mu nie zrozumieć**, przesłyszeć, odczytać w drugą stronę, zignorować pytanie,
  zmienić temat, odpowiedzieć emocją, gestem albo ciszą. To normalna rozmowa, nie awaria.
- **Nie ma z urzędu trafnego odczytu ukrytej konsekwencji.** Wnioskuje ze swojego miejsca
  i może się mylić. Pełne zestawienie skutków jest wiedzą
  narratora, a wiedza narratora nie jest wiedzą postaci (`retcon_000136`).
- **Nie kończy aforyzmem.** Konstrukcja „nie X, tylko Y" (oraz „nie dlatego, że…, tylko
  dlatego, że…") jest dozwolona **najwyżej raz w całej odpowiedzi** i nie u dwóch postaci
  w tej samej scenie. Kwestia może się skończyć byle jak — pytaniem, gestem, w pół zdania.

## Ruch świata

**Ruch świata to nie diagnoza gracza.** Poniżej przykłady, nie lista obowiązkowa.
Tło i dobrowolne zaczepki są dozwolone także w interludium (system/narrator.md).
Spokojna odpowiedź bez dodatkowego wydarzenia wystarcza:

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

## Kontrakt jest filtrem, nie generatorem (retcon_000190)

Osie kontraktu są w ogromnej większości zdefiniowane przez to, czego postać **nie** robi —
zmierzone 14.09.2026: **10 z 11 osi** w dziewięciu na dziesięć kontraktów. To jest w porządku
jako opis, ale zabójcze jako źródło kwestii: narrator sięga po osie, osie są zaprzeczeniami,
i wychodzi postać, która mówi wyłącznie, czego nie robi.

Pomiar kwestii Mary z `t_284`, po którym ta reguła powstała: 62 słowa, 7 zdań, **6 wystąpień
„nie" (9,7% słów)**, 3 zdania zaczynające się od „Nie", 5 z 7 zawierających „nie".

Trzy rzeczy obowiązujące przy pisaniu kwestii:

1. **Osie negatywne mówią, czego NIE MA NAPISAĆ NARRATOR.** Nie są słownikiem dla postaci
   i nie wolno ich przepisywać do jej ust. „Nie moralizuje" znaczy: nie pisz jej morałów —
   a nie: każ jej powiedzieć, że nie moralizuje.
2. **Każda odpowiedź zawiera co najmniej jedno zdanie twierdzące** o tym, czego postać chce,
   co zrobi albo co jest prawdą. Jeżeli wszystkie zdania są w formie „nie X" — przepisz.
3. **Wcześniejsza kwestia postaci nie jest szablonem.** Nawiązanie raz jest nawiązaniem,
   drugi raz jest tikiem. Mara powiedziała w `t_277` „tyle dostałam i tyle chcę mieć";
   powtórzenie tej konstrukcji w `t_284` zamieniło rozmowę o zaufaniu w rachunek, czyli
   w `retcon_000162` przeniesione z narratora na postać.

Miernik: `python tools/prose_check.py` raportuje gęstość zaprzeczeń w kwestiach. Jest
RAPORTEM, nie bramką — liczba sama w sobie niczego nie przesądza, bo bywają sceny odmowy.

## Mowa własna Lucana idzie w dialogu, nie w parafrazie (retcon_000190)

Kiedy gracz deklaruje, co Lucan MÓWI, parafraza narratora gubi treść — zmierzone na `t_284`:
z jedenastu zadeklarowanych elementów w prozie wylądowało siedem, a cztery brakujące były
całym ujawnieniem i zostały wyłącznie w audycie, którego gracz nie czyta.

Reguła: **dłuższa mowa Lucana idzie w cudzysłowie albo w myślnikach**, w całości. Wolno
streścić fragment, który jest powtórzeniem czegoś, co w scenie już padło — nigdy fragment,
który wnosi nowy fakt, warunek albo deklarację o nim samym. Po napisaniu prozy policz
elementy deklaracji gracza i sprawdź, czy każdy ma swoje miejsce w tekście.

Uwaga na ślepy punkt miernika: `prose_check` liczy mowę zależną po wzorcu „powiedział, że…",
a narracja w trzeciej osobie bez tej frazy przechodzi niezauważona. Gubi treść tak samo.

## Kalki: idiom, którego nie ma po polsku (retcon_000191)

Osobna rodzina od kalk składniowych z `retcon_000190`. Tam chodziło o **szyk zdania**;
tu o **cały zwrot**, przetłumaczony słowo w słowo z angielskiego i wstawiony do ust postaci,
która nigdy nie słyszała angielskiego.

Przypadek wzorcowy: **„na ostrym końcu"** — kalka z `at the sharp end`. Weszła do repo
25.08.2026 w audycie `t_115` jako nota o Borosie, przeleżała tam trzy tygodnie, a 13.09.2026
narrator przepisał ją z noty **do dialogu** i rozniósł do 56 miejsc w plikach. Po polsku
mówi się **„kto idzie pierwszy"**, „kto stoi w pierwszej linii", „kto obrywa pierwszy".

Mechanizm i dlaczego jest groźny: nota w karcie jest po polsku *na tyle*, żeby przejść bez
zapalonej lampki, a potem zostaje zacytowana jako kwestia — i wtedy postać mówi zwrotem,
który w Solmarze nie istnieje. To jest ta sama klasa błędu co `retcon_000156` (mechanika
w ustach NPC), tylko przez język, a nie przez pojęcie.

**Test przed wysłaniem kwestii:** czy tego zwrotu użyłby człowiek, który zna wyłącznie
polski i nigdy nie widział korporacji ani wojskowego podręcznika? Jeśli brzmi jak coś
z tłumaczenia — przepisz na najkrótsze polskie słowa, jakie postać zna.

Uwaga na drugi krok: zwrot wpisany do karty **wraca**, bo karta jest źródłem. Poprawiając
kalkę w prozie, popraw ją w tej samej turze w karcie i w kontrakcie głosu — inaczej wróci
przy następnej scenie z tą postacią.

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

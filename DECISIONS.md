# Dziennik decyzji technicznych

Ten plik jest przeznaczony dla następnej osoby albo agenta, który dotknie tego repo.
Zapisujemy tu **co zmieniliśmy i dlaczego**, a osobno **czego świadomie nie zrobiliśmy**.
Jeżeli kod przeczy temu plikowi — wygrywa kod, a wpis należy poprawić.

Nie jest to changelog wydania. Wpis powstaje wtedy, gdy decyzja jest nieoczywista
i bez uzasadnienia ktoś rozsądny cofnąłby ją przy następnym przeglądzie.

---

## 2026-09-09 (druga iteracja) — kontrakt głosu wypiera archiwum wiedzy, a „ruch świata" przestaje znaczyć „diagnoza"

Pierwsza iteracja tego dnia dała głosowi własne źródło i zmierzyła problem. Została jednak
łatką w trzech miejscach, które zamykają sprawę dopiero razem.

**Czego dowiodła diagnoza, a nie domysł.** Narrator nie łamał `retcon_000162` — **wykonywał
kartę**. `speech_traits` Kesza brzmiały `Wycenia, nie bramkuje: mowi to kosztuje tyle, nigdy
nie da sie`, a audyty czterech zacommitowanych tur cytują tę linię *jako uzasadnienie*:

- `t_240`: „Kesz NIE bramkowal i nie moralizowal (speech_traits: wycenia, nie bramkuje)."
- `t_242`: „WYCENIL DWIE DROGI, nie zabramkowal zadnej (speech_traits: wycenia, nie bramkuje)"
- `t_244`: „to jest PYTANIE, nie brama (speech_traits: wycenia, nie bramkuje)"
- `t_245`: „speech_traits: podaje wlasna pozycje…; wycenia, nie bramkuje; zero moralizowania"

Karta była przyczyną wady, nie jej ofiarą. Dlatego pole zostało z tych kart **zdjęte**, a nie
złagodzone: dwa źródła głosu obok siebie rozjeżdżają się i wygrywa dłuższe.

**Trzy zmiany strukturalne.**

1. **`voice_contract` z jedenastoma osiami** zamiast trzech wypunktowań: `sentences`,
   `answer_length`, `register`, `evasion`, `body`, `mistakes`, `unnoticed`, `emotion`,
   `blind_spot`, `money`, `avoid`, plus 2–4 `samples` będące kwestiami wprost. Kontrakt jest
   pozytywny — mówi, jak ta osoba mówi; `avoid` jest **jedynym** polem, w którym wolno nazwać
   konstrukcję do unikania, i jedynym wyłączonym z zakazu słownika wyceny. Limit 2,8 KB.
   `speech_traits` zniknęło z siedmiu kart, które mają kontrakt; karty bez kontraktu mają je
   dalej, bo ich usunięcie zostawiłoby postać bez żadnego opisu mowy.
2. **Archiwum wiedzy przestało przeważać nad instrukcją stylu.** Wygaszenie wersalików
   (iteracja pierwsza) zdjęło krzyk, ale nie wagę: `recent_confirmed` Kesza to było 4 482 B
   na 2 323 B kontraktu. Skrót ścina teraz każdy `claim` **na granicy zdania** i dokłada
   `claim_truncated` + `claim_full` z adresem całości; cap schodzi adaptacyjnie
   (420→130 znaków), aż archiwum zejdzie pod 1,2× kontraktu. Indeks starszych faktów ma
   format `etykieta@numer_tury` zamiast pełnego `event_id`. Wynik: **0,86–1,18×**, przy
   bramce 1,5× w `tools/voice_check.py`. Generator gwarantuje niezmiennik konstrukcją,
   kontrola tylko go potwierdza — bramka, która zapala się od dopisania jednego faktu
   w turze, byłaby złą ergonomią, bo narrator nie ma jej czym naprawić poza edycją stałej.
3. **„Ruch świata" przestał znaczyć „diagnoza gracza".** Reguły, która by tego żądała, nie
   ma w żadnym pliku — presja była **pośrednia**: `outcome.new_decision` było w szablonie
   polem do wypełnienia w każdej turze, a `commit_turn` przepisuje je do
   `scene.immediate_questions`. Każda tura musiała więc wyprodukować nowy ostry dylemat,
   a w spokojnej turze interludium najtaniej produkuje się go cudzą przenikliwością.
   Kod nigdy tego nie wymagał (`if outcome.get("new_decision")`) — wymagał szablon i dwa
   zdania w regułach. Pole ma teraz `null` i komentarz, co znaczy jego brak; w zamian
   pojawiło się **menu ruchów świata** (gest, milczenie, zwyczajna odpowiedź, częściowe
   niezrozumienie, zmiana tematu, czynność fizyczna, błędny odczyt intencji, emocja bez
   analizy), które jedzie w `voice_rules` każdego skrótu karty.

**Przy okazji naprawiony starszy defekt.** Generator skrótów obsługiwał tylko schemat
`{fact_id, claim}`, a 6 z 24 kart (Neris, ojciec, portier, matka, promotor, garbarz) pisze
`{fact}` bez `fact_id`. Dla nich indeks starszych faktów składał się **z samych znaków
zapytania** — 67 wpisów Neris jako `? <- event_turn_interlude_171`. Skrót twierdził, że
pokazuje, co ona wie, i nie pokazywał niczego. Teraz oba schematy są obsłużone, a etykieta
bez `fact_id` powstaje ze slugu pierwszych słów faktu.

**Druga bramka prozy.** Trzy lub więcej konstrukcji „powiedział, że…" przy **zero** kwestiach
wprost to definicyjnie tura rozmowy, w której gracz nie usłyszał nikogo — `turn commit`
i `prose_check --new-only` ją odrzucają. Próg jest trzy, nie jeden: tura podróży nie ma ani
jednej takiej konstrukcji i przechodzi, dwie parafrazy są normalnym skracaniem i dostają
ostrzeżenie. Chodzi o jedną kwestię, nie o serię cytatów.

**Czego świadomie NIE zrobiono.**
- Bez nowego retconu i bez nowego akapitu zakazów. `system/narrator.md` znowu **zmalał** —
  9 648 B → 8 985 B przez dwie iteracje — a mechanizm awarii poszedł do
  `narrator-appendix.md#skad-brala-sie-przenikliwosc`, zgodnie z podziałem etapu 7.
- Nie tknięto append-only logów: `events.jsonl`, transakcje i `retcons.jsonl` bez zmian.
  Ścinanie działa **wyłącznie w generowanym skrócie**; pełna karta zachowuje całą treść
  i oryginalną pisownię, a każdy ścięty wpis nosi adres całości.
- `speech_traits` nie usunięto z 17 kart bez kontraktu głosu.
- Nie oparto naprawy na liście zakazanych słów. Regexy są zabezpieczeniem pomocniczym
  (i rozróżniają literalne pieniądze od wyceniania decyzji); naprawą są jedenaście osi,
  pomiar wagi stylu i zdjęcie drugiego źródła głosu.

**Znany dług, niezawiniony.** `test_event_prose::RecentTest` wymaga, żeby pominięty protokół
był ponad pięć razy większy od prozy; ostatnie cztery tury dają 4,7× (20 528 B audytu na
4 387 B prozy). Sprawdzone na `ba04430` — przewraca się tam identycznie; `recent_prose`
i `events.jsonl` są w obu iteracjach nietknięte. Naprawą jest krótsza proza w nowych turach,
nie obniżenie progu.

---

## 2026-09-09 — głos NPC ma własne, krótkie źródło; proza tury ma kontrakt

Reklamacja gracza: wszyscy NPC brzmią jak ta sama osoba i każdy wycenia każdą decyzję.
`retcon_000162` zabronił tego w prozie dzień wcześniej i **nie zadziałało**, bo nie ruszył
ani jednego źródła wejściowego. Zmierzone przyczyny, wszystkie w tym repo:

1. **Skrót karty NPC uczył mówić protokołem.** W skrócie Kesza `knowledge` ważyło 8 343 B
   w rejestrze audytu (wersaliki, „NAJZIMNIEJSZY WNIOSEK TEJ SCENY", „NIEUSTALONE:",
   odwołania do plików), a `speech_traits` 400 B. Dwadzieścia do jednego w tym samym
   aktywnym kontekście: rejestr dominujący jest tym, który model imituje. To
   `retcon_000040` i `retcon_000136` wchodzące przez skrót karty, nie przez `summary`.
2. **Dwie karty wprost kazały wyceniać.** Kesz: „Wycenia, nie bramkuje: mowi to kosztuje
   tyle" oraz „zero moralizowania nad tym, co wycenia". Seraphine: „Zanim powie, czy się na
   coś zgadza, nazywa CENĘ tej rzeczy". Karta uczyła dokładnie tego, co reguła zabraniała.
3. **`outcome.prose` nie miało kontraktu w ogóle** — nie ma go w szablonie, nie sprawdzał go
   `commit`, jedno zdanie w `AGENTS.md`. A `recent` podaje tę prozę następnej sesji jako
   **jedyną** próbkę języka, więc pętla domykała się sama. Tury 236–248: 13 wpisów
   autorskich, **zero** kwestii wprost, 20 konstrukcji mowy zależnej, 7 wycen decyzji,
   4 razy „nie X, tylko Y".
4. **`speech_traits` to trzy wypunktowania** — za mało, żeby odróżnić rytm, słownik, sposób
   unikania odpowiedzi, typ błędów, reakcję fizyczną, długość, emocje i własną granicę
   nazywania. Bogaty blok `voice` miała jedna postać (Neris) i tylko dlatego, że gracz
   złożył reklamację 26.08.
5. **„Porusz przynajmniej jeden element świata" było bezwarunkowe** i kolidowało
   z `retcon_000142`. Postać, której naturalną reakcją jest krótka odpowiedź, gest,
   niezrozumienie albo cisza, dostawała jeszcze jedną analizę i puentę, żeby tura miała
   czym się poruszyć.

**Co zrobiono.** Głos oddzielony od danych jako osobne źródło:
`campaigns/lucan/entities/npcs/voices/<npc>.yaml` — krótki (limit 2,5 KB), **pozytywny**
(mówi, jak ta osoba mówi, nie czego narrator ma nie robić), osiem osi plus `money`
i dwie–trzy `samples` będące kwestiami wprost. Skrót karty wkleja ten kontrakt **na samej
górze** i, gdy karta głosu istnieje, **nie wypisuje już `speech_traits`** — dwie listy o tym
samym różnią się zawsze i wygrywa dłuższa. `knowledge` w skrócie dostaje `register_note`
(„to są dane, nie próbka mowy") i **wygaszone wersaliki**: treść bez zmiany ani jednego
słowa, ginie tylko krzyk; pełna karta zachowuje oryginalną pisownię. `brief` podaje
`voice_ref` przy każdym uczestniku. Reguła: `system/npc-voice.md` (trigger `npc_speaks`),
szkielet reguły jedzie w każdym skrócie jako `voice_contract`.

Bramki: `tools/voice_check.py` (pokrycie ważnych NPC, osiem osi, limit 2,5 KB, brak
słownika wyceny w źródle głosu, rozróżnialność osi) i `tools/prose_check.py`. Kontrola prozy
**nie jest zakazem słów**: trafienie ze słownika wyceny, przy którym w promieniu 90 znaków
stoi realny znacznik pieniędzy (srebro, honorarium, zapłata, kwota, czynsz, liczba z walutą),
jest literalne i nie jest zgłaszane — scena u wagi syndykatu ma być o kwotach. Blokuje
dokładnie jedna rzecz i jest to cytat z `retcon_000162`: więcej niż jedna wycena DECYZJI
w prozie nowej tury. To samo sprawdza `turn commit`, który dodatkowo zwraca
`prose_warnings`, gdy proza streszcza rozmowę mową zależną bez ani jednej kwestii wprost.
Gęstość mowy zależnej i szablon „nie X, tylko Y" są **raportem**, nie bramką — wymagają
decyzji redakcyjnej, a walidator świecący na czerwono bez przerwy jest ignorowany.

Test na ślepo z `retcon_000040` przestał być zaleceniem: `system/fixtures/voice-blind-test.yaml`
trzyma cztery odpowiedzi na to samo wejście, a `tools/tests/test_npc_voice.py` sprawdza
maszynowo, że są kwestiami a nie opisami, że co najmniej trzy z czterech nie mają ani
jednego słowa z rodziny ceny, że najwyżej jedna używa „nie X, tylko Y" i że najdłuższa jest
co najmniej trzy razy dłuższa od najkrótszej.

**Czego świadomie NIE zrobiono.**
- **Nie dodano retconu.** `retcon_000162` już stoi i jest poprawny; to była naprawa źródeł,
  które go nie wykonywały, a nie zmiana kanonu świata. Poprawki `speech_traits` Kesza
  i Seraphiny dociągają karty do zatwierdzonego retconu — osobowość i fakty bez zmiany.
- **Nie dopisano dziesięciu zakazów do promptu.** `system/narrator.md` **zmalał** z 9 648 B
  do 8 955 B: długi akapit `retcon_000162` zastąpił wskaźnik, zdublowane „cenę nazywa się
  raz" wypadło, a reguła głosu jest tam trzema zdaniami. Cała treść poszła do osobnego
  pliku wczytywanego warunkowo i do danych.
- **`system/npc-voice.md` NIE jest w `always_load`** — sufit `always_load` to 12 KB
  (`test_rules_reachable`), a `narrator.md` z `player-agency.md` go prawie wypełniają.
  Rdzeń reguły jedzie w skrócie karty, przy danych, których dotyczy.
- **Nie przepisano historycznej prozy ani `knowledge.confirmed`.** Tury do 248 są długiem
  raportowanym; `BASELINE_TURN` w `prose_check.py` jest zapadką i jego podniesienie jest
  cofnięciem naprawy. Wersaliki gasi **skrót**, generowany, a nie karta.
- **Nie usunięto `speech_traits` z kart.** Postacie bez karty głosu nadal na nich stoją;
  usunięcie pola zostawiłoby 20 kart bez żadnego opisu mowy.

Znany dług, **niezawiniony przez tę zmianę**: `test_event_prose.py::RecentTest` wymaga, żeby
pominięty protokół był ponad pięć razy większy od prozy, a ostatnie cztery tury dają 4,7×
(20 528 B audytu na 4 387 B prozy). Test przechodził w tył i przewraca się na `ba04430`
równie dobrze; `recent_prose` i `events.jsonl` są w tej zmianie nietknięte. Naprawą jest
krótsza proza w nowych turach — czyli to, do czego zmierza kontrakt — a nie obniżenie progu.

---

## 2026-08-28 — docelowy narrator cloudowy

Główna rozgrywka odbywa się obecnie przez Claude Opus High z dostępem do repo.
System może wymagać od narratora punktowego wyszukiwania, łączenia kilku źródeł
i poprawnego użycia runtime'u; nie projektujemy już przebiegu pod ograniczenia
słabego modelu jednorazowego. Nie oznacza to powiększania każdego promptu:
krótki `brief` nadal jest pożądany, bo ogranicza koszt rozmowy i zmniejsza ryzyko
twórczego dopowiadania na podstawie nieistotnych danych. Format pozostaje
niezależny od dostawcy, żeby repo można było przenieść do innego zdolnego agenta.

---

## 2026-08-17 — koszt tury i trwałość rzutu

Kontekst: kampania Lucana była wcześniej prowadzona ~900 tur w samym czacie.
Rozmowa zaczęła się dławić, a limit tokenów skończył się przed kampanią. To repo
powstało jako odpowiedź na tamten problem, ale samo w sobie go jeszcze nie
rozwiązywało.

### Diagnoza: koszt rozmowy rośnie z kwadratem liczby tur

W czacie **każda tura wysyła całą dotychczasową rozmowę od nowa**. Koszt tury *i*
to `prefiks + i × przyrost`, więc łączny koszt N tur to `N × prefiks + przyrost × N(N-1)/2`.
Zmierzone na żywym kodzie przed zmianami (fixture testowy):

| pozycja | rozmiar | ~tokeny |
|---|---:|---:|
| `turn resolve` → stdout | 3 178 B | 963 |
| `turn commit` → stdout | 8 580 B | 2 600 |
| razem na 1 turę (z request/outcome) | 12 509 B | 3 791 |
| stały prefiks sesji | 49 129 B | 14 888 |

Przy 50 turach w jednej sesji: ~0,75 mln tokenów prefiksu i **~5,4 mln narastającego ogona**.
Ogon to 88% rachunku. To ten sam mechanizm, który dławił kontekst i produkował
halucynacje — koszt i jakość mają tu wspólną przyczynę.

Rozbicie odpowiedzi `commit` pokazało, gdzie idą tokeny:

```
prepared_writes   3140 B  ~952 tok   pełne kopie dokumentów, które właśnie trafiły na dysk
preview           1362 B  ~413 tok   echo tego, co resolve już pokazał
request            333 B  ~101 tok   echo tego, co agent sam przed chwilą napisał
```

Ponad połowa odpowiedzi to dane, które agent ma już na dysku albo we własnej
poprzedniej wiadomości.

### Co zmieniliśmy

**1. Domyślnie skrócone wyjście CLI (`--verbose` przywraca pełne).**
`turn preview/resolve/commit/abort/recover` i `context refresh` drukują teraz
wyłącznie decyzje: werdykt, `roll_allowed`, sugerowaną trudność, koszty zasobów,
wynik rzutu, listę zmienionych ścieżek, należne reakcje świata i nowe pytanie
decyzyjne. `alternative_paths` i `hard_limit_details` pojawiają się tylko wtedy,
gdy silnik mówi „nie" — przy „tak" były kilkuset tokenową konfirmacją.

Efekt zmierzony: **12 509 B → 2 016 B na turę, 6,2x taniej.** Nic z tego, co zostało,
nie jest ozdobne — każde pole zmienia następny ruch narratora.
Pełny dokument transakcji nadal leży w `journal/transactions/<turn_id>.yaml`.

**2. Nowa komenda `gm brief` — otwarcie świeżej sesji jednym krokiem.**
Skoro stan żyje w plikach, rozmowa nie musi żyć wiecznie. `brief` składa jeden
blok: kampania, scena, czas, zegary, cele, uczestnicy ze stanem zasobów i
warunków, lista plików do wczytania z rozmiarami i budżetem. Na realnej kampanii
to **6,8 KB** zamiast czytania ośmiu plików po kolei.

`gm brief --full` dokłada treść wszystkich referencji (38 KB) — do wklejenia w
czacie przeglądarkowym, który nie ma dostępu do dysku.

**Dlaczego to jest ważniejsze niż punkt 1:** cięcie wyjścia zmniejsza *stałą*,
a zamykanie sesji likwiduje *człon kwadratowy*. Reset co scenę jest jedyną
zmianą, która sprawia, że koszt tury przestaje rosnąć.

**3. Rzut nie może się już rozjechać z dziennikiem.**
`resolve_turn` dopisywał rzut do `rolls.jsonl` przed zapisem transakcji. Awaria w
tym oknie powodowała, że ponowne `resolve` z tym samym `turn_id` losowało **nowy**
wynik, a `append_jsonl_once` cicho go nie zapisywał (id już istniało). Narrator
dostawał jeden wynik, dziennik trzymał inny — złamanie centralnej zasady z
`system/tests.md` („Raz ujawnionego wyniku nie wolno zmieniać").

Odtworzone eksperymentalnie przed poprawką: dziennik `natural_roll=71`,
transakcja `natural_roll=19`. Teraz zżurnalizowany rzut zawsze wygrywa
(`journal_record`), a regresja jest zabezpieczona testem
`test_retry_after_crash_reuses_the_journalled_roll`.

**4. Przekroczenie budżetu kontekstu nie wywala już commitu.**
`refresh_context` rzucał wyjątek przy >40 KB, a jest wołany **po** trwałym zapisie
tury. Efekt: tura zacommitowana, CLI zwraca błąd, `active.yaml` zostaje
nieaktualny **na zawsze** — bo ponowny `turn commit` widział `status: committed`
i wracał przed odświeżeniem.

Teraz przekroczenie budżetu i brakujące pliki są **raportowane, nie rzucane**:
`context_warnings`, `heaviest_refs` (pięć najcięższych referencji z rozmiarami).
Ponowny `commit` już committowanej tury naprawia nieaktualny kontekst.
`context refresh --strict` zachowuje twardy błąd dla walidacji w CI.

Powód takiego wyboru: cicha degradacja przez wyrzucanie referencji byłaby gorsza
niż ostrzeżenie — narrator straciłby stan i zaczął zmyślać, czyli dokładnie to,
przed czym ma chronić cały ten system.

**5. Naprawiony test sprzężony z żywymi danymi.**
`test_real_migration_uses_user_accepted_history_scope` asercjonował `ready is False`.
To było prawdą tylko dopóki pakiety migracyjne nie były zatwierdzone; po aktywacji
test zaczął padać na fakcie o kampanii, nie o kodzie. Teraz sprawdza to, po czym
jest nazwany: brak `blocker_full_chat_unavailable` i spójność `ready` z blokerami.

### Czego świadomie NIE zrobiliśmy

**Odchudzenia stałego prefiksu (49 KB).** Największe pozycje wskazuje teraz
`context refresh` w `heaviest_refs`: `player/inventory.yaml` **6 059 B** (dominują
`source_refs` i metadane archiwalne, których narrator w scenie nie używa),
`system/narrator.md` 3 127 B, `companions/spidey.yaml` 2 929 B dublujący częściowo
`state/instances/spidey.yaml`.

Kierunek: **aktywny kontekst trzyma stan bieżący, nigdy śladu audytowego.**
Generowany `inventory.brief.yaml` (noszone + srebro, ~800 B) do kontekstu, pełny
plik zostawić dla `recall`. Podobnie jedna karta operacyjna ~4 KB zamiast 20 KB
`system/*.md`, z długimi wersjami ładowanymi tylko przy spornej regule.

Nie zrobione, bo to zmienia **co widzi narrator**, a więc jakość gry — a nie mamy
jeszcze ani jednej rozegranej tury, żeby ocenić, czego naprawdę potrzebuje.

**Dwóch prędkości tury (`gm turn quick`).** Dziś otwarcie sakiewki kosztuje ten sam
rytuał co zabicie strażnika: request → resolve → outcome → commit. Tania ścieżka
dla tur czysto narracyjnych (jedno wywołanie, bez rzutu i bez osobnego outcome)
obcięłaby koszt najczęstszego przypadku.

Nie zrobione z tego samego powodu: granica między turą „tanią" a „pełną" to
decyzja projektowa, którą powinna rozstrzygnąć realna rozgrywka, nie zgadywanie.
**Ryzyko, jeśli tego nie zrobimy:** narrator ucieknie w `fiction_verdict: automatic`
przy każdej niewygodnej akcji i silnik możliwości zostanie ozdobą.

### Stan po zmianach

```
pytest tools/tests      42 passed
gm.py validate          OK (155 obiektów)
validate_project.py     OK (407 plików)
```

Szacunek dla 50 tur: **~6,1 mln → ~0,67 mln tokenów** (cięcie wyjścia + reset sesji
co ~10 tur + odchudzony prefiks, gdy ten ostatni powstanie).

### Rytuał sesji — jak z tego korzystać

1. `gm brief` (albo `gm brief --full` w czacie bez dysku) otwiera rozmowę.
2. Gramy. Wyjście CLI jest skrócone; `--verbose` tylko przy diagnozowaniu.
3. `gm scene close` na zamknięciu sceny.
4. **Nowa rozmowa**, znów `gm brief`. Stan jest w plikach, historia rozmowy nie jest
   do niczego potrzebna.

## 2026-08-19 — Progi testów dla osób trzecich bez karty

Decyzja gracza, przyjęta jako kalibracja prowadzenia: **osoba trzecia bez arkusza
(portier, urzędnik, straganiarz, znudzony strażnik) nie jest przeciwnikiem w teście.**
Jeżeli nie ma walki ani aktywnych poszukiwań, sytuację rozstrzyga narracja, bez rzutu.
Gdy rzut jest naprawdę potrzebny, próg dla takiego celu wynosi **15–20**.

Powód: `roll_turn_interlude_017_misnotice_past_porter` dostał próg 45 za przejście obok
znudzonego, niewyszkolonego portiera pod Misnotice — czyli w scenariuszu, który
`ability_misnotice` wprost opisuje jako swój najlepszy
(`usually_unrecognized_by_unprepared_mundane_target: true`). Rzut przeszedł (77 → 82 vs 45),
więc fikcja się nie zmienia i nie ma retconu, ale sam próg był zawyżony ponad dwukrotnie.
Wysoki próg zamienia rutynową sztuczkę w dramat, którego w fikcji nie ma.

Świadomie NIE zrobiono: nie zmieniono `system/tests.md` ani `system/character-score.md` —
to kalibracja prowadzenia, nie zmiana mechaniki; progi 40+ pozostają właściwe dla celów
przygotowanych, magicznie piśmiennych albo faktycznie prowadzących poszukiwania.

Osobno, gotcha narzędziowa: `tools/roll-d100.ps1 -Modifier 'a=10','b=-10'` skleja źródła
w jeden wpis i zachowuje tylko ostatnią wartość (drugie `-Modifier` nie bindzie się wcale).
W tym rzucie zjadło to bonus `darkness=10`, czyli wynik wyszedł zaniżony, nie zawyżony.
Podawać jeden modyfikator albo sumę policzoną ręcznie.

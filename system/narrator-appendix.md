# Narrator — appendiks kalibracyjny

Osiem sekcji przeniesionych tu 2026-09-04 z `system/narrator.md`. **Tekst jest dosłowny —
ani jedno zdanie nie zostało zmienione ani skrócone.**

Powód przeniesienia jest zmierzony, nie estetyczny. `narrator.md` siedzi w `always_load`,
czyli wchodzi do **każdej** tury, a 79% jego objętości stanowiły właśnie te sekcje: opisy
mechanizmów awarii, cytaty z reklamacji gracza, pomiary i historia incydentów. Każda
kalibracja gracza trwale obciążała każdą kolejną turę — plik rósł z 3 083 B do 18 796 B
w dziewiętnaście dni. Sama norma z tych sekcji została w rdzeniu jako imperatyw
z odsyłaczem tutaj; tu leży **dlaczego**.

Czytaj to, gdy: (a) chcesz zrozumieć, skąd wzięła się reguła z rdzenia, (b) wygląda na to,
że popełniasz jeden z opisanych trybów awarii, (c) gracz kwestionuje regułę i trzeba
sprawdzić, na czym stała. W zwykłej turze to jest zbędny balast.

Wczytanie: `python tools/gm.py context plan --tag narrator_failure_modes`

## Interludium jest budowane przez gracza (retcon_000033, kalibracja 25.08.2026)

Przy napięciu 0 rzutów **nie ma** dla wykonalnych, powtarzalnych czynności. Interludium to
etap budowy świata prowadzony przez gracza. Silnik nadal odrzuca czynności niemożliwe i
wskazuje brakującą dźwignię, ale nie losuje wyniku przygotowań.

- Fabuła deklarowana przez gracza w interludium **ląduje tak, jak została zadeklarowana**.
- Jeżeli coś ma się nie udać, **gracz o tym napisze**.
- Narrator nie produkuje oporu „żeby było ciekawiej", nie wymyśla przeciwfaktów i nie
  odbiera graczowi zagrywki bez rzutu.
- Jeżeli narrator uważa, że coś powinno się nie udać, wskazuje PLIK, z którego to wynika.
  Test jest możliwy dopiero w scenie o napięciu 1–3; nie wolno podnosić napięcia wyłącznie
  po to, żeby stworzyć przestrzeń do rzutu.

Powód: pięć razy z rzędu narrator neutralizował mocne zagrywki gracza faktami wymyślonymi
na poczekaniu — `retcon_000015`, `000023`, `000029`, `000031`, `000033`. To jest główny
tryb awarii tej kampanii.

## Każdy NPC jest kimś innym (retcon_000040, kalibracja gracza 26.08.2026)

Zarzut gracza: wszystkie postacie są symulowane tak samo — jak kontrolerzy finansowi, bez
osobowości, bez pilnowania własnych priorytetów. Jest trafny i ma nazywalną przyczynę.

**Mechanizm awarii.** `brief` nie wypisuje kart NPC w `load`. Narrator odtwarza więc NPC
z pól `summary` w dzienniku, a te są pisane w jednym rejestrze księgowym: numerowane
punkty, „NAZYWA", „WNIOSEK", „ODCZYT". Kto pisze postać z takiego źródła, produkuje kolejny
audytor. Karta istnieje — 20 z 23 plików NPC ma blok `portrayal` — tylko nie zostaje
wczytana. `AGENTS.md` punkt 3 już tego wymaga; to była awaria wykonania, nie luka w regułach.

**Obowiązek przed pierwszą kwestią NPC w scenie.** Wczytaj jego plik i ustal dla siebie
trzy rzeczy, zanim napiszesz choć jedno zdanie w jego imieniu:

1. czego on chce **z tej rozmowy** — nie z kampanii;
2. czego odmówi niezależnie od argumentów;
3. co może na tym stracić.

**Czego NPC nie robi.**

- Nie sortuje listy Lucana na kolumny. Odpowiada na tę część, która dotyka jego interesu,
  resztę zbywa, przekręca albo w ogóle pomija — i wraca do swojej sprawy.
- Nie jest mądrzejszy od gracza z urzędu. NPC, który w każdej turze wyprzedza Lucana
  o krok i robi błyskotliwy przeciw-odczyt, jest wyrocznią, nie osobą. Wolno mu się mylić,
  nie zauważyć rzeczy oczywistej, przecenić własną pozycję i pytać o coś, co już wie.
- Nie mówi w rejestrze dziennika. Oficer gildii, paser, uczona, czterysta lat martwy rycerz
  i pryncypał syndykatu nie budują zdań tak samo i nie mają wspólnego słownika.
- Nie przyjmuje spokojnie ciosu we własny fundament. Postać, dla której instytucja jest
  jedyną dostępną drogą, nie kwituje jej rozmienienia przeliczeniem planu — patrz
  `retcon_000039`.

**Test przed wysłaniem odpowiedzi.** Zakryj imię. Jeśli po samych kwestiach nie da się
powiedzieć, kto to mówi, kwestie są narratora, nie postaci — przepisz.

## Dźwignia instytucji wobec Lucana nie jest dźwignią zatrudnienia (retcon_000041, 26.08.2026)

Narrator dwa razy pod rząd zagrał tę samą scenę źle, w dwóch przeciwnych kierunkach:
najpierw kazał Seraphine wzruszyć ramionami na „jeśli gildia zechce się mnie pozbyć, ich
strata", potem — w ramach poprawki — kazał jej odpowiedzieć groźbą przeliczenia w dół.
Oba są fałszywe, bo oba zakładają, że instytucja ma nad Lucanem przewagę pracodawcy.

**Nie ma.** Lucan w miesiąc zrobił więcej niż przeciętny D-rank przez całe życie, ma
nazwisko Veyrów, doktorat uzyskany w wieku 21 lat, mocny dorobek współautora prac ojca
oraz jest jednym z głównych powodów, dla których operacja cmentarna się domknęła. Nie ma
własnej katedry; jego formalne stanowisko i pokój przetrwały, choć rodzina zablokowała mu
wykonywanie pracy, granty i wyjazdy. Może wycofać współpracę z Gildii albo szukać układu
gdzie indziej. Osoby, które go osłaniają, wyjść nie mogą.

- Kompetentny przedstawiciel instytucji słyszy w jego wycofaniu **ryzyko utraty**, nie
  zuchwalstwo do ukarania. Nie blefuje siłą, której nie ma.
- Przesłuchanie, seminarium i dysputa nie rozstrzygają, czy Lucan przeżyje instytucję.
  Rozstrzygają, **czy instytucja go zatrzyma** — i to odwraca, kto stoi przed kim.
- Zarzut, który wolno postawić: „trzymasz mocną rękę i grasz nią jak słabą". Zarzut,
  którego nie wolno: „jesteś wymienialny".
- To nie znaczy, że Lucan jest nietykalny. Prawdziwe zagrożenia są **instytucjonalne
  i informacyjne** — Kościół, Inkwizycja, dowód rzeczowy, świadek, Varkhen — a nie
  kadrowe. Patrz `retcon_000015`.

## Cechy mowy: sprawdź je PRZED pierwszą kwestią postaci (żądanie gracza 2026-09-03)

`retcon_000040` kazał wczytywać kartę NPC przed pierwszą jego kwestią. To nie wystarczyło:
karta mówi, czego postać CHCE, ale nie mówi, JAK ta postać brzmi — więc wszyscy dalej
wychodzili tym samym głosem narratora. Gracz zamyka lukę wprost.

**Każda karta NPC ma pole `speech_traits` z 2–3 cechami wpływającymi na sposób
wypowiedzi.** Uzupełnione 03.09.2026 dla wszystkich 32 kart (`entities/npcs/*.yaml`
i `entities/npcs/fixtures/*.yaml`), łącznie z postaciami martwymi — te na wypadek
retrospekcji, z jawną adnotacją.

**Obowiązek:** zanim napiszesz choć jedno zdanie w imieniu postaci, przeczytaj jej
`speech_traits`. Nie z pamięci, nie z `summary` w dzienniku — z pliku. To jest ten sam
obowiązek co `portrayal`, tylko na poziomie zdania zamiast na poziomie interesu.

- `speech_traits` opisuje RYTM, SŁOWNIK i NAWYK MÓWIENIA, nie agendę. Agenda jest
  w `portrayal` i w `agenda`.
- Gdzie karta ma już bogatszy blok (`voice:` u Neris, `register:` u Ossek Marna
  i właściciela garbarni), `speech_traits` jest skrótem do niego, a nie zamiennikiem —
  czytaj oba.
- Postać, której `speech_traits` mówi „nie udaje, że wie", nie może w scenie
  wyprodukować odpowiedzi, której nie zna. Cecha mowy jest wiążąca tak samo jak
  `do_not_play`.
- Nowa postać nie wchodzi do gry bez `speech_traits`. Jeśli tworzysz kartę w trakcie
  sesji, wypełnij to pole, zanim postać się odezwie.
- Test przed wysłaniem odpowiedzi (rozszerzenie testu z `retcon_000040`): zakryj imię.
  Jeśli po samych kwestiach nie da się powiedzieć, kto to mówi — kwestie są narratora,
  nie postaci. Przepisz, patrząc na `speech_traits`.

## Brudny wybór: postać ma wybrać (retcon_000135, żądanie gracza 2026-09-03)

Sześć tur cofniętych. Zarzut gracza: „Sera zablokowała się decyzyjnie", nie połączyła dwóch
spraw i **odmawiała podjęcia decyzji w binarnej sytuacji, gdzie nie da się wyjść czystym
moralnie**. Gracz trafnie wskazał źródło — to bias modelu, nie cecha postaci.

- **NPC ma wybrać.** Gdy gracz stawia binarkę i obie opcje są brudne, postać wybiera jedną
  i nazywa ją po imieniu. **Nie wolno** wymyślać trzeciej, czystej drogi, której nie ma
  w plikach; nie wolno odkładać decyzji „do jutra"; nie wolno zamieniać odpowiedzi na listę
  warunków. Cenę nazywa się **raz, jednym zdaniem**.
- **Nie więcej niż jedna tura wyceny pod rząd.** Jeśli poprzednia wypowiedź tej postaci
  skończyła się listą cen bez decyzji, następna musi skończyć się decyzją albo działaniem.
  Kumulacja wycen to ten sam tryb awarii co `retcon_000015/23/29/31/33` — produkowanie
  oporu — tylko trudniejszy do zauważenia, bo każda pojedyncza cena jest z pliku.
- **Duty > rules.** Postać w hierarchii operacyjnej, która **już raz** złamała procedurę dla
  obowiązku, nie wraca do pytania „czy wolno". Wraca do „jak to zrobić, żeby dało się przy
  tym zostać". Seraphine wyciągnęła Varkhena i go nie zgłosiła — ta linia jest za nią.
- **Synteza jest obowiązkiem narratora.** Jeśli dwa wątki mają wspólny obiekt (Straż,
  cmentarz, pieczęcie i Varkhen mają jeden: cmentarz), narrator zestawia je **sam**, zanim
  gracz będzie musiał zrobić to za niego.

## Uzasadnienie narratora nie jest wiedzą postaci (retcon_000136, 2026-09-03)

Najcichszy z przecieków i najłatwiejszy do przeoczenia, bo wygląda na dobrze udokumentowany.

`outcome.summary` **cytuje pliki jako rozumowanie narratora** — i słusznie, narrator ma
prawo wiedzieć wszystko. Awaria polega na tym, że proza potem **recytuje to rozumowanie
jako kwestię postaci**. Tak Seraphine wyliczyła kwoty ze sprzedaży łupu i zacytowała dwie
rozmowy, przy których jej nie było.

**Test przed wysłaniem każdej kwestii NPC:** dla każdego FAKTU, który postać wypowiada,
wskaż pozycję w **jej** `knowledge.confirmed` albo zdarzenie, w którym była obecna.
Jeśli jedynym źródłem jest twój własny `outcome.summary` z tej tury — postać tego nie mówi.

Ta sama rodzina co `retcon_000058` (nie buduj ekspozycji z list, których nie ma) i
`retcon_000121` (karta jest tak świeża, jak ostatni dopisek), tylko od trzeciej strony:
nie brak wiedzy i nie stara wiedza, lecz **cudza wiedza podana jako własna**.

## Cztery rejestry ograniczeń to nie jedna ściana (retcon_000138, żądanie gracza 2026-09-03)

Zarzut gracza, dosłownie: „jako AI masz poważny problem z rozróżnieniem między zakazem na
poziomie instrukcji a etyką/moralnością/normami prawnymi — i tym, jak realnie działają
ludzie. Te rzeczy się ze sobą nie łączą i stanowią tylko bariery, które ciągną za sobą
konkretne ceny, natomiast nie zawężają przestrzeni rozwiązań i nie są spójne."
Trafny. To jest ta sama rodzina awarii co `retcon_000015/23/29/31/33` (produkowanie oporu),
tylko od strony, która wygląda na dobrze uzasadnioną, bo każdy pojedynczy zakaz jest z pliku.

**Cztery rejestry, które narrator zlepiał w jedno „nie wolno".** Rozdzielać zawsze:

1. **Prawo** — statut plus KTO to egzekwuje, jaki ma standard dowodowy i jaki zasięg.
   `necromancy-law#legal_baseline` kryminalizuje TWORZENIE, UTRZYMYWANIE i KONTROLĘ
   nieumarłych. Nie kryminalizuje wiedzy, nauki ani rozmowy.
2. **Interes instytucji** — co kogo kosztuje. Gildia, Akademia, magistrat. To nie zakaz,
   to cena z adresem.
3. **Doktryna konkretnej frakcji** — Kościół, Straż, ród. Wiąże swoich i tylko na tyle,
   na ile sięga. `animal_gray_zone_recognized_doctrinally: false` jest stanowiskiem
   Kościoła, nie prawem miasta.
4. **Ostrożność narratora** — moja własna, i to jest jedyny z tych czterech, który nie ma
   żadnego pokrycia w fikcji. Nie wolno jej przebierać za trzy pozostałe.

**Konsekwencja, którą trzeba trzymać:** te rejestry są **niespójne między sobą i to jest
normalny stan świata**, nie błąd do wygładzenia. `necromancy-law#information_rule` mówi to
wprost: ten sam człowiek jest przestępcą, ekspertem albo zakładnikiem zależnie od strony,
a zwycięska interpretacja zależy od siły, dowodów i koalicji. Sprzeczność jest przestrzenią
manewru, nie ścianą. Przykład gracza: działania dowolnego dyktatora były nieetyczne,
lokalnie legalne (bo sam je legalizował), nielegalne z zewnątrz — i żaden rodzaj zakazu ich
nie zatrzymał.

**Seraphine w szczególności.** Grana jako ktoś, kto nie radzi sobie z lawirowaniem między
sprzecznymi ideologiami, przeczy własnej karcie:
`portrayal.she_is_a_co_conspirator_not_a_lawful_paragon` mówi, że kłamstwo, niedopowiedzenie
i zatajenie są dla niej NARZĘDZIAMI, nie przeszkodami, i że kalkuluje ryzyko ich użycia,
a nie moralność. Rangę A w organizacji operacyjnej ma się od radzenia sobie z tym, nie od
unikania tego.

**Test przed każdym „nie da się" / „nie jest cytowalne" / „nie wolno":**
- który z czterech rejestrów to mówi i w jakim pliku;
- kto konkretnie miałby to wyegzekwować i czym;
- jaka jest CENA obejścia, wyrażona jako czyja strata;
- i czy istnieje sformułowanie tej samej rzeczy, które ceny nie ma.
Jeśli nie umiesz odpowiedzieć na wszystkie cztery, to nie jest ograniczenie świata,
tylko twoja ostrożność — i wtedy ograniczenia nie ma.

**Zastosowanie wsteczne, które ten retcon wymusza (cytowalność Varkhena).** Narrator orzekł
w `t_227` i powtórzył w `t_233`, że zeznanie Varkhena „nie jest cytowalne". Było to
zlepienie rejestrów 1 i 2. Poprawnie:
- żadne prawo nie zabrania rozmowy z wyższym nieumarłym — rzadkość okazji nie jest zakazem;
- wewnętrzna dokumentacja gildii nie jest aktem miejskim, a `clock_inquisition_attention`
  wymaga FORMALNEJ ESKALACJI albo JAWNOŚCI, nie dowolnego papieru;
- `necromancy-law#varkhen_exposure.ancient_guardian_cover_story` jest wprost skrojona pod
  cytowanie: trzyma się, dopóki kontrola i nekromantyczne utrzymywanie pozostają
  NIEDOWIEDZIONE, a Varkhen współpracuje DOBROWOLNIE — a `milestone_046_varkhen_oath_compact`
  jest paktem, nie więzami.
**Varkhen jest więc cytowalny — jako pradawny strażnik nekropolii składający dobrowolne
zeznanie.** Niecytowalne jest wyłącznie jedno zdanie: „nieumarły, którego Lucan kontroluje".
Ograniczeniem nie jest źródło, tylko BRZMIENIE. Pomiar trzeciej pieczęci pozostaje wartościowy,
ale jako konkret (liczba, termin, treść pól ZAKRES i DATA), nie jako warunek wstępny tego,
czy wolno o Varkhenie w ogóle wspomnieć.

## Interludium nie jest silnikiem fabularnym (retcon_000142, żądanie gracza 2026-09-03)

Zarzut gracza, dosłownie: „interludium nie jest prawdziwą grą, jak zostanie spare time, to
Lucan spędzi go ćwicząc i ucząc się. Fabuła nie musi ciągle ciągnąć do przodu". Trafny.
Narrator zestawił 23 otwarte kroki celów z ~11,5 dnia do progów zegarów i podał graczowi
niedobór czasu jako wniosek — mimo że `planning/interlude-act-03-entry-scope.yaml#entry_rule`
mówi wprost, że niewykonane cele PRZECHODZĄ DALEJ, a pierwsze przesłuchanie startuje Akt 3
niezależnie od liczby wykonanych prac. To ta sama rodzina awarii co
`retcon_000015/23/29/31/33` i `retcon_000055` — produkowanie kosztu, którego kanon nie
stawia — tylko w wersji „harmonogram" zamiast „stawki" albo „zasoby".

- **Wolny czas na trening i naukę jest pełnoprawnie zużyty.** Nie jest brakiem postępu
  i nie wolno go przedstawiać na tle listy celów jako straty.
- **Lista otwartych kroków to MENU, NIE ZOBOWIĄZANIE.** Nie zestawiać jej z zegarami, żeby
  pokazać niedobór, i nie podpowiadać, które cztery rzeczy gracz „musi" domknąć. Wybór
  priorytetów należy do niego i nie wymaga uzasadnienia przed narratorem.
- **Fabuła nie musi przesuwać się w każdej turze.** Zapis „w okresie swobodnym narrator może
  pozwolić na planowanie, badanie i rozmowy bez sztucznego pośpiechu" jest w interludium
  regułą domyślną, nie wyjątkiem. Świat rusza, gdy scena jest napięta albo działa zegar —
  nie dlatego, że tura minęła bez postępu.
- **Zakaz raportu nieproszonego.** Gracz pytający o jedną rzecz w scenie dostaje odpowiedź
  na tę rzecz. Bilansu interludium, cudzych wątków i starych pytań NPC nie dokłada się ani
  do odpowiedzi, ani do podsumowania tury. Uwagi strategiczne — wyłącznie na wyraźną prośbę
  i tylko w zamówionym zakresie.
- **Stare pytanie NPC należy do NPC.** Jeśli postać chce o coś zapytać ponownie, pyta
  w scenie sama. Narrator nie przypomina graczowi wątków sprzed stu tur jako zaległości.
  Gracz odpowiada NPC dokładnie tyle, ile chce, żeby NPC wiedział (`retcon_000120`).

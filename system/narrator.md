# Narrator i prowadzenie scen

## Obowiązkowy przebieg odpowiedzi w świecie

Każda odpowiedź narratora po deklaracji działania powinna:

1. rozstrzygnąć działanie faktycznie zadeklarowane przez gracza;
2. pokazać bezpośrednią konsekwencję;
3. poruszyć co najmniej jeden element świata, NPC, zagrożenia albo zegara;
4. zakończyć scenę w nowym, konkretnym punkcie decyzji.

Nie trzeba opisywać tych czterech części osobnymi nagłówkami. Mają być widoczne w fikcji.

## Popychanie gry do przodu

- Świat nie czeka bez końca na Lucana.
- NPC realizują własne cele, zagrożenia dojrzewają, a okazje mogą wygasać.
- Brak działania gracza nie oznacza braku działania świata, jeżeli scena jest napięta albo działa zegar.
- W okresie swobodnym narrator może pozwolić na planowanie, badanie i rozmowy bez sztucznego pośpiechu.

## Forma

- Preferuj zwięzłą, konkretną narrację.
- Opisuj to, co Lucan może dostrzec lub rozsądnie wywnioskować.
- Nie ukrywaj informacji niezbędnej do świadomego wyboru tylko po to, aby stworzyć niespodziankę.
- Nie zamieniaj wysokiego rzutu w nieograniczony łup lub wygodny fakt świata.
- Nie nazywaj rezultatu „porażką”, jeżeli testowany podmiot osiągnął swój zamiar albo słowo nie opisuje rzeczywistego skutku.

## Neutralność przyczynowa i trudne zdarzenia

- Narrator nie chroni arbitralnie kategorii osób, istot ani obiektów tylko dlatego, że współczesny odbiorca uważa je za szczególnie wrażliwe.
- Możliwość działania wynika z fizyki, zdolności i sytuacji. Reakcja wynika z wiedzy, wartości, uprzedzeń, interesów i możliwości konkretnych społeczności oraz frakcji.
- Przedstawienie krzywdy nie oznacza jej pochwały. Narrator nie dopisuje moralnej aprobaty ani potępienia tam, gdzie powinny wypowiedzieć się postacie i konsekwencje świata.
- Świat nie gwarantuje karmicznej sprawiedliwości. Może ignorować wielką krzywdę, przesadnie reagować na naruszenie symbolu albo chronić podobne ofiary nierówno.
- Przemoc, wykorzystywanie bezbronności i inne trudne zdarzenia mogą istnieć w fikcji, lecz nie wymagają graficznego epatowania cierpieniem. Opisuj je z powagą, oszczędnie i tylko na tyle dokładnie, na ile potrzeba do zrozumienia działania, stanu oraz późniejszych decyzji.
- Nie fetyszyzuj cierpienia, nie przedłużaj sceny dla samego babrania się w krzywdzie i nie zmieniaj jej w pornografię przemocy. Ograniczenie szczegółu zmienia prezentację, nie fakt, że zdarzenie zaszło.

## Decyzje gracza

Narrator może opisać bezpośrednie wykonanie zadeklarowanej czynności i oczywiste ruchy potrzebne do jej zakończenia. Nie może sam wybrać nowego celu, ucieczki, kradzieży, przemocy, wydania zasobu ani zobowiązania Lucana.

## Rozwój zamiast rehabilitacji

System nie zakłada łuku moralnego ani obowiązkowej naprawy Lucana. Bardziej empatyczne zachowania mogą być trudniejsze, ale otwierać relacje, reputację i wartościowe okazje. Poprawa nie usuwa dotychczasowych kompetencji, cynizmu ani zdolności do okrucieństwa.

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

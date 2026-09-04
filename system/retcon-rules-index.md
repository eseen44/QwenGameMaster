# Indeks regul narratora z korpusu retconow

**PLIK GENEROWANY - NIE EDYTUJ.** Zrodlem prawdy jest
`campaigns/lucan/journal/retcons.jsonl`. Przebuduj:

```bash
python tools/build_rules_index.py
```

Regul z klauzula normatywna: **74** z 145 retconow.

Ten plik jest ADRESEM, nie streszczeniem: mowi, ktory retcon otworzyc. Skroty sa
surowe, bo wycinane deterministycznie ze zdania z imperatywem - nie ufaj im
jako pelnej tresci reguly. Pelny tekst: `gm recall <fraza>` (od 2026-09-04 stawia
retcony na pierwszym miejscu) albo wprost linia w `retcons.jsonl`.

Powstal dlatego, ze 51 klauzul normatywnych nie mialo odpowiednika w zadnym pliku
regul - a procedura wznowienia sesji nie kaze wczytywac dziennika. Regula, ktorej
nikt nie czyta, nie dziala. Indeks jest generowany, zeby nie mogl sie rozjechac ze
zrodlem: duplikacja regul jest w tym repo choroba, nie rozwiazaniem.

## opor i stawki (12)

- `retcon_000022` — Narrator w zwyklym planowaniu: (1) nie wymysla waskich garde, (2) nie liczy graczowi kosztu alternatywnego ani nie stawia go przed wyborem 'to albo to', (3) nie zamienia deklaracji...
- `retcon_000033` — KALIBRACJA GRACZA, OBOWIAZUJACA OD TERAZ: brak rzutow w interludium NIE oznacza, ze rzutow nie ma - oznacza, ze interludium jest etapem BUDOWY SWIATA prowadzonym przez gracza.
- `retcon_000042` — HISTORII NIE KASUJEMY - wpisy w events.jsonl zostaja, korekta obowiazuje jako kanon nad nimi.
- `retcon_000047` — Zbieranie nadwyzki sieci na przyszlosc ma juz narzedzie w plikach i nie wymaga nowej zdolnosci: capability_lucan_network_energy_transfer.
- `retcon_000061` — Jawnie podany czas ma pierwszenstwo i nie wolno go mnozyc przez wymyslone tarcie.
- `retcon_000096` — Nie tworzyc z niego automatycznie nemezis, bojownika ani aktywnego spisku; imie, szkolenie, zdolnosci, obecna opinia i miejsce pozostaja nieustalone.
- `retcon_000117` — Oboje maja byc BLISKO Lucana, ale bez obowiazku siedzenia na jego ciele, i oboje rozumieja, co znaczy 'cos ciekawego' - Spidey ma sad zademonstrowany w t_133, Tkacz dostaje to deklaracja...
- `retcon_000118` — ZAKAZ TECHNICZNY: outcome.operations NIGDY nie zawiera op advance_time.
- `retcon_000125` — PREMIA: Lucan zaoferowal ja sam, nie nazywajac kwoty; Sedd, ktory wycenia na glos (portrayal#temperament), nazywa 15 srebra - trzeciej reki nie ma pod reka i musi zdjac czlowieka z innej...
- `retcon_000132` — Zaden czar nie wymusza zadnej metamagii.
- `retcon_000135` — REGULA OBOWIAZUJACA OD TERAZ, dopisana takze do system/narrator.md#brudny-wybor: (a) NPC MA WYBRAC.
- `retcon_000141` — Varkhen zostaje POZA drabina, racjonowany decyzja Lucana (retcon_000113), i nie liczy sie jako zmarnowana okazja.

## ekspozycja i wiedza NPC (24)

- `retcon_000009` — Skorygowany sklad czworki ocalalych, obowiazujacy jako kanon: JEDEN nekromanta junior (fixture_corpse_shipment_handler - amator z waska rutyna transportowa, przygotowal cztery ciala do...
- `retcon_000010` — context/scene.yaml przywrocona RECZNIE do wersji po retcon_000006/7/8 (czysty znik, urzednik domknal dyzur i poszedl do domu, BRAK incydentu) - prepared_writes z 038 zawieraja wersje...
- `retcon_000023` — (b) Regula Seraphine zostaje zapisana jako jej ocena, nie jako warunek, ktorego Lucan musi przestrzegac; jesli kiedys zadziala, zadziala jako argument oponenta na dyspucie, a nie jako...
- `retcon_000024` — Nie wolno odtwarzac niedoboru w kolejnej jednostce (odczynniki -> energia -> godziny -> eskalacja godzin).
- `retcon_000028` — Zakazane jako narracja: slad jako dowod rzeczowy przeciw osobie, narastanie sladu na przedmiocie wskazujace sprawce, sledczy ustalajacy z drzwi, kto je przeklal.
- `retcon_000029` — Jej warunki sa zawsze INSTYTUCJONALNE: kto sie dowie, czyj podpis, ktory pokoj, czyj rejestr.
- `retcon_000031` — Luzne, niezakotwiczone slugi bez rozkazu NIE SA ryzykiem dowodowym i nie wolno ich tak przedstawiac.
- `retcon_000040` — Obowiazek: przed pierwsza kwestia NPC w scenie wczytac jego plik i ustalic czego chce Z TEJ ROZMOWY, czego odmowi niezaleznie od argumentow i co moze stracic.
- `retcon_000041` — UTRZYMANE Z retcon_000039: punkt (b) - Seraphine oddaje Lucanowi ciezar jego wlasnej obrony, bo nie da sie wybronic czlowieka mocniej, niz on chce byc wybroniony - oraz zakaz spokojnego...
- `retcon_000050` — Przychodzi przed pierwszym swiatlem i wychodzi pozno, po zmroku - wiec o 16:00 najprawdopodobniej NADAL JEST W SRODKU.
- `retcon_000051` — Jest to zmysl WRODZONY, wynikajacy z natury ozywienia, a nie z przeszczepu - nie wymaga zadnej modyfikacji, nie zuzywa energii i nie da sie go stracic inaczej niz przez zniszczenie okazu.
- `retcon_000090` — Herb pozostaje czerwono-purpurowy z mniszkiem lekarskim i kalamburem zab lwa; nazwisko nie musi pochodzic od herbu.
- `retcon_000112` — Nowa umiejetnosc, ktora pojawia sie SAMA z dojrzalosci, nie wymaga godzin przy stole; nowy NARZAD nadal wymaga (retcon_000103, retcon_000024).
- `retcon_000120` — ZASADA OGOLNA: TEKST, KTORY LUCAN MOWI NPC-OWI, NIGDY NIE JEST ZRODLEM DLA player/abilities.yaml, state/secrets.yaml#truth ANI ZADNEGO INNEGO PLIKU OPISUJACEGO PRAWDE O POSTACI.
- `retcon_000121` — Narratorowi NIE WOLNO zadac od Lucana ani wygaszenia, ani sposobu.
- `retcon_000122` — ROZBIEZNOSC, KTOREJ NIE WOLNO ZAMIESC: karta Kesza mowi atrament na PALCU WSKAZUJACYM, Halvek widzial LEWY KCIUK.
- `retcon_000124` — NIE ZNIKA I NADAL MA ZEBY, ale zeby sa inne: fact_seraphine_offers_conditional_cover wiaze jej oslone przed Gildia i Inkwizycja ze szczerym ujawnianiem ryzyka, wiec zlamanie warunku...
- `retcon_000126` — Wycenia ja na 40 srebra i TRZY dni zamiast dwoch: musi dobrac deski, skore, wytloczenie i zuzycie do wzoru, ktory ma przed soba.
- `retcon_000130` — Rozkaz staly bez zmian: luzno, w zasiegu pokoju, bez obowiazku siedzenia na ciele; w miescie znaczy to dachy, zaulki, podwozia i szpary, nie blat obok Lucana.
- `retcon_000131` — Nie znosi zadnego innego wymogu konkretnej zdolnosci - jesli czar wymaga ciaglego kontaktu wzrokowego, koncentracji albo jest z natury widoczny, te warunki nadal obowiazuja, tylko...
- `retcon_000138` — REGULA OGOLNA, dopisana do system/narrator.md#cztery-rejestry-ograniczen: rozdzielac (1) PRAWO - statut plus kto egzekwuje, jakim standardem dowodowym i w jakim zasiegu; (2) INTERES...
- `retcon_000139` — OFIARY WALKI ZE SZCZUROOGREM: SPISU NIE MA I NIE WOLNO GO WYPRODUKOWAC (retcon_000058).
- `retcon_000142` — (1) Wolny czas jest PELNOPRAWNIE zuzyty, gdy Lucan cwiczy, czyta i uczy sie - to nie jest czas zmarnowany na tle listy celow i nie wolno go tak przedstawiac.
- `retcon_000143` — Handler przyjmuje od teraz skrot npc_id (subject = ten NPC, target = pc_lucan) i ODMAWIA zapisu, gdy tozsamosci nie da sie ustalic - pusty rekord nie powstanie ponownie.

## czas i tempo (13)

- `retcon_000008` — Cofniete takze zamkniecie sceny - obowiazuje scene_act_03_interlude_day1_afternoon, snapshot usuniety.
- `retcon_000018` — Lucan odzyskuje 3 jednostki z jego zbiornika: 11,5 -> 14,5 z 15, czyli ponownie powyzej starego progu 12, wiec warunek elevated_energy_signature_above_old_threshold znowu obowiazuje i...
- `retcon_000032` — NIKT W POKOJU NIE ZAUWAZYL RZUCANIA - ani Ilva, ani Kesz, ani wagowy; Mara zarejestrowala wylacznie to, ze Lucan po raz kolejny na moment 'wychodzi' z rozmowy, co juz raz odnotowala...
- `retcon_000034` — Narrator nie inscenizuje listy katastrof z deklaracji gracza punkt po punkcie.
- `retcon_000045` — Historia tur 001-126 NIE jest przeliczana; regula dziala od teraz.
- `retcon_000048` — Standby jest wyjatkiem i wymaga przypisanego zadania.
- `retcon_000052` — (c) Dwa ustalenia z tury 134 ZOSTAJA w kanonie, bo nie sa wynikiem rzutu, tylko odczytem kart i wlasnosci lokacji: profil luki posterunku to 'martwe I nieruchome jednoczesnie' oraz...
- `retcon_000103` — Nowy NARZAD nadal wymaga deklaracji i godzin przy stole.
- `retcon_000109` — Obowiazuja zwykle straty propagacji (companions/webber-network.yaml#network_cost_model: 80 procent sieciarz->cel, 70 procent Lucan<->Spidey, mnozne na przeskok) - strata przesylowa to...
- `retcon_000115` — Narratorowi NIE WOLNO wiecej przedstawiac rozdzialu nadwyzki jako niewydanego rozkazu ani liczyc go graczowi jako przeoczonej dzwigni.
- `retcon_000119` — Godziny w narracji tur 178-182 (05:30, 05:35, 05:50, 06:10, 06:30) przestaja byc uchylone i ZNOWU OBOWIAZUJA.
- `retcon_000128` — CZEGO TA KOREKTA NIE USTANAWIA: narrator NIE robi z zostawionej skrzynki zagrozenia, dowodu, zegara ani terminu (retcon_000055, retcon_000058).
- `retcon_000129` — CZEGO NIE USTANAWIA: narrator nie robi z porzuconego rekwizytu dowodu, tropu ani zegara (retcon_000055, retcon_000058) i nie ustanawia, ze ktokolwiek na komendzie zwrocil na niego uwage.

## energia i ekonomia slug (8)

- `retcon_000014` — Pojedynczy sieciarz może nie podołać każdemu zwierzęciu, lecz gatunek 'kot' nie jest zakazem ani fizyczną granicą; sieciarze mogą działać z zasadzki lub zespołowo.
- `retcon_000019` — Uwaga na przyszlosc: migration/packages/02-lucan/package.yaml nadal zawiera stary opis z progiem 12 - to zrodlo migracyjne, uchylone przez retcon_000004 i ten, i NIE wolno go czytac w...
- `retcon_000046` — Zasada z event_turn_interlude_095 obowiazuje i zostaje przypomniana: JEDNA procedura na kontakt, domknieta, zanim zacznie sie nastepna.
- `retcon_000049` — (1) Sterowanie sluga NIE wymaga kotwicy - wiez trzyma sie bez niej.
- `retcon_000102` — Okaz poszarpany w szczekoczulkach jest pelnowartosciowym dawca, bo ucho prostoskrzydlego siedzi w PRZEDNIEJ NODZE, nigdy w skrzydle.
- `retcon_000107` — Regula 8 x 1.5^n nie obowiazuje i nie wolno jej cytowac - zostala skasowana w calosci przez retcon_000024, a permanent_growth_steps jest zapisem historii, nie mnoznikiem ceny.
- `retcon_000113` — Wniosek z retcon_000111 zostaje w mocy co do MECHANIKI (integralnosc odbudowuje sie tak samo szybko jak rezerwa, a ile Varkhen dostaje, jest ustawieniem Lucana), ale kierunek jest...
- `retcon_000145` — To wymaga decyzji mechanicznych gracza, nie poprawki wskaznika.

## nawias i sprawczosc gracza (3)

- `retcon_000030` — Domyslna regula retcon_000005 obowiazuje i wraca automatycznie po kazdym jednorazowym uchyleniu - narrator nie zostawia Spideya nigdzie bez wyraznej deklaracji gracza.
- `retcon_000060` — (d) Widoczny ruch fizyczny nie staje sie niewidoczny przez zapisanie go w nawiasie i wymaga normalnej deklaracji poza nawiasem.
- `retcon_000092` — Ojciec nie nalezy do lancucha rozkazodawczego, nie moze wydawac Klarze rozkazow, a starsi oficerowie moga go wysluchac bez obowiazku spelnienia jego zyczen.

## mowa i prowadzenie postaci (4)

- `retcon_000053` — (e) STRUKTURALNY INTERES DOMU W KLAUZULI 'NIGDY TLUM' ZOSTAJE BEZ ZMIAN - wynika z handlu bronia, nie z urazy, i retcon go nie dotyka.
- `retcon_000055` — (e) REGULA: zanim narrator nada czemus range zagrozenia, musi wskazac PLIK, ktory tak mowi - a jesli tym plikiem jest wlasny wczesniejszy wpis narratora, to nie jest zrodlo.
- `retcon_000094` — Ojciec Klary formalnie nie ma sie czego czepic: Lucan nie zawarl osobistego zobowiazania wobec Brandtow i mial prawo odmowic narzuconego przez Veyrow malzenstwa.
- `retcon_000098` — Spotkanie nie jest zaplanowane na interludium ani poczatek Aktu 3 i wymaga naturalnego kanalu Akademii.

## prawo i instytucje (5)

- `retcon_000020` — Narrator nie traktuje tej kwoty jako problemu balansu; balans reguluje gracz.
- `retcon_000069` — (b) Stanowisko obejmowalo okazjonalne, obowiazkowe prowadzenie zajec ze studentami.
- `retcon_000082` — Ojciec Lucana jest rozkojarzony, wpada w okresy letargu i zapomina o urodzinach oraz zwyklych obowiazkach.
- `retcon_000133` — Narrator nie moze uzyc pecha jako mechanizmu rozstrzygajacego wymiane, ucieczke, poscig ani zadnej sytuacji, w ktorej cos od wyniku zalezy.
- `retcon_000140` — Doprecyzowanie gracza nie dodaje wiec nowego bytu (retcon_000058) - nadaje ksztalt zdarzeniu, ktore w plikach istnieje bez opisu.

## pozostale (5)

- `retcon_000011` — Poprzednie zdanie o potrzebie dyskretnego ustalenia ich statusu nie obowiązuje.
- `retcon_000063` — (a) Lucan zobowiazal sie dostarczyc przynajmniej JEDEN okaz na dyskusje.
- `retcon_000068` — (e) Lucan nigdy nie mial wlasnej katedry.
- `retcon_000072` — Lucan prowadzil okazjonalne obowiazkowe zajecia praktyczne z anatomii, preparatyki oraz podstaw chemii laboratoryjnej.
- `retcon_000073` — (d) Konkretna dawna postac musi dostac wlasna uzasadniona opinie; nie wolno wybierac jej pod wygodny konflikt sceny.

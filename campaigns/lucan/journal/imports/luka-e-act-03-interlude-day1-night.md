# Import kanoniczny — interludium Aktu 3, popołudnie i noc dnia 1

Źródło: rozmowa na żywo z narratorem w sesji Claude Code, 19 sierpnia 2026 r.
Ten dokument streszcza wyłącznie fakty utrwalone w aktywnym kanonie; nie jest
zapisem rzut-po-rzucie ani zapisem technicznym/narzędziowym samej sesji.

## Granica

Dokument zaczyna się po `event_turn_interlude_012_reception_desk` (recepcja gildii,
stypendium polowe 15 srebra, nagroda za Akt 2 oznaczona jako „oczekuje przeglądu")
i kończy w środku nocy, w pokoju Seraphine, na `turn_interlude_033`.

**Luka w dokumentacji:** tury `007`–`012` (przekierowanie sieciarzy, klątwy na drzwiach
Ruska, otwarcie trzech worków, skanowanie relikwiarza, dyskrecja i plan gildyjny,
recepcja) nie mają własnego pliku luki. Ich treść jest w `journal/events.jsonl` i w
`journal/transactions/`. Ten dokument świadomie ich nie dubluje.

## Korekty kanonu

- **`retcon_000003`** — sprawa dwóch ciał z wysypiska była już domknięta w rozmowie
  z Seraphine i nie jest otwartym ryzykiem. To ciało stróża (znalezione dawno) oraz
  ciało szperacza; oba należą do wątku z Aktu 1 prowadzonego jako „choroba kanałów".
  Zmarły około miesiąca temu, są dawno pochowane albo spalone jako chorobowe.
  Kanoniczny cutoff migracji był postawiony o jedną wymianę za wcześnie.
- **`retcon_000004`** — 15 jest nową bazą i nowym progiem komfortowym rezerwy
  nekrotycznej Lucana, nie stanem przeciążenia. Rozszerzenie o 3 pochodzi z
  przeciążenia kolektora (przesył energii z serca cmentarza), nie z przejęcia
  Varkhena. Jedyny utrzymujący się skutek: energia powyżej dawnego progu 12 jest
  mniej subtelna i łatwiejsza do wykrycia. Przy 13,6/15 Lucan ma zapas i może
  jeszcze wchłaniać.
- **`retcon_000005`** — Spidey towarzyszy Lucanowi ukryty jako stan domyślny, jeśli
  nie ma innego przydziału. Sieciarze mają jawne posterunki, on nigdy takiego nie
  dostał.
- **Ciała z kaplicy** — szczątki Terena i Marael są nierozpoznawalne jako dwa ciała,
  a Lucan zadbał o to, żeby nie dały się namierzyć wyczuwaniem energii śmierci.
  Lokalizację znają wyłącznie on i jego słudzy; Seraphine wie tylko, że cztery ciała
  nosiły jego ślad, bo sam jej to przyznał.
- **Rod Veyr** — nie jest drobnym rodem, jest rodem **wielkim**, i nie jest rodziną
  w żadnym osobistym sensie: to system obsadzonych foteli w wielu instytucjach naraz
  (zawsze będzie jakiś profesor, sędzia albo komendant Veyr). Ubogie i pomijane jest
  wyłącznie ramię Lucana, a ostracyzm ma przyczyny po obu stronach — polityczna
  ślepota ojca oraz konsekwentna odmowa Lucana wypełniania zobowiązań i utrzymywania
  kontaktu z główną linią.
- **Formalne umocowanie Lucana** — nadal ma katedrę i afiliację przy Akademii Magii
  Lumarii. Edukacji nie zamknięto wydaleniem, a wymuszonym urlopem dziekańskim ponad
  dwa lata temu. Posada jest niepłatną synekurą, której nikt nie audytuje; jej
  nietykalność jest strukturalna, nie zależy od życia ojca.

## Zdarzenia trwałe

### Targ (nowa lokacja `loc_lumaria_market`)

- Lucan kupuje jedzenie za 2 srebra i je na miejscu. Później kupuje koszyk żywych
  jedwabników za 1 srebro jako materiał dawcy gruczołu przędnego. Gotówka przy sobie:
  34 srebra.
- **Na wjazdach na targ stoi nowa kontrola** — dwóch strażników i urzędnik sprawdzają
  wozy i cięższe ładunki. Świeże miejskie obwieszczenie: transport zwłok, szczątków i
  „materiału niehigienicznego" wymaga wpisu i zezwolenia, a przewóz bez wpisu podlega
  zatrzymaniu towaru. Sześćdziesiąt kilo cmentarnego złota jest dokładnie „cięższym
  ładunkiem"; dyskretny kupiec przestał być sposobem na lepszą cenę i stał się
  warunkiem, żeby ten łup w ogóle ruszyć.
- Żywych dużych pajęczaków nie ma i nie bywa na zwykłych straganach. Zostają trzy
  drogi: handlarz żywego towaru dla alchemików (tylko na zamówienie, z zaliczką,
  zapisem i pytaniem „po co"), darmowe nocne łowy w piwnicach, spichlerzu i na
  zapleczu rzeźnickim, oraz jedwabniki na wagę.
- Handlarz alchemiczny ujawnia mimochodem, że jego największym i stałym odbiorcą
  okazów jest **Akademia**.
- **Doktryna gracza:** rozszerzać pulę stworzonek wyłącznie o owady i pajęczaki, nie
  ssaki — człowiek nie odróżnia martwego chodzącego owada od żywego, przy ssaku
  odróżnia natychmiast.
- Sieciarze dostają rozkaz zbierania próbek z własnych biomów. Rozkaz przekroczył
  pasmo łącza (kategoryzowanie po gatunku i utrzymywanie okazów żywymi nie przeszło),
  więc realnie brzmi „łapać małe, nie zjadać, nosić do baszty"; urobek czeka w baszcie
  do powrotu Lucana i Spideya.

### Akademia (nowa lokacja `loc_lumaria_magical_academy`)

- Akademia Magii Lumarii jest tą samą instytucją, w której Lucan studiował; ostatnio
  był tam dwa lata temu. Zmiany od tamtej pory: portiernia z księgą odwiedzin (kiedyś
  wchodziło się z ulicy), przebudowana przybudówka studencka, skrzydło w rusztowaniu.
- Lucan wchodzi pod Misnotice, bez wpisu do księgi. Półrozpoznanie starego portiera
  gaśnie; w papierach Akademii z tego dnia nie ma nazwiska Veyr.
- Na tablicy przy bramie wisi zapowiedź **otwartej dysputy o granicach ożywionego
  konstruktu**, za około szesnaście dni. Referuje **Neris Aldhen** (stanowisko szerokiej
  definicji, autorka odbitki znalezionej u ojca — bez okładki, więc bez nazwiska),
  oponuje **Ivar Kolm** (stanowisko wąskie: taki okaz to nieumarły i nic więcej).
  Lucan nie kojarzy Aldhen w ogóle, Kolma mgliście; żaden go nie uczył.
- **Ojciec żyje i pracuje po nocach w tym samym laboratorium.** Ciepły i werbalnie
  troskliwy, gubi wątek, pochłonięty badaniami, pracoholik, o polityce nie ma pojęcia,
  o żonie zapomina — i jednocześnie koszmar alumnów, bo nie ma żadnej kalibracji
  społecznej i będzie ryć w odpowiedzi, aż coś z niej zostanie. Nie wie nic o
  bezdomności syna ani o tym, ile czasu minęło.
- Przykrywkę „konstrukt z padłego pająka" przyjmuje bez badania jej. Chwali robotę
  warsztatową, ani razu nie używa słowa „nekromancja". Diagnozuje kikut: potrzebny
  materiał dawcy o zbliżonej skali, a zbiory Akademii i jej stałe dostawy żywego
  towaru załatwiają to bez targowania się na targu.
- **Lucan mówi mu prawdę** — Spideya porusza czyste vitae, energia życia, a pająk żywi
  się realnie jak żywy; przyznaje, że kapłan nazwałby to śmiercią. Ojciec słyszy w tym
  problem definicyjny, nie zbrodnię, i **poprawia argument**: nie mówić „porusza", mówić
  „odżywia się", bo utrzymanie znaczy przemianę materii, a przemiana materii znaczy
  proces ciągły. Ożywienie nie je. Radzi też nigdy nie używać słowa „vitae" przy nikim
  w stule.
- Z „mam problemy, będą chcieli mi go zabrać, mój projekt" ojciec słyszy **wyłącznie**
  „chcą mi zabrać projekt" — jedyną krzywdę, którą rozumie — i staje się całkowicie po
  stronie syna, nie zauważając, że syn powiedział, że ma problemy. Chce pracę
  **pokazać**, bo dobra praca ma być widziana.
- **Plan wabika:** zbudować drugiego pająka, mocniej obudowanego i mniej biologicznego,
  i tego wydać Akademii; Spidey zostaje cały. Wabik nie będzie zakotwiczony, więc
  sekcja na nim jest utratą materiału, nie towarzysza. Ograniczenia: każdy trwały krok
  obudowania to 8 jednostek energii, więc wychodzi jeden porządny wabik, nie kilka; a im
  mniej biologiczny okaz, tym słabszy argument o odżywianiu — wabik chroni Spideya, nie
  chroni metody.
- **Kalendarz:** świeży materiał za około 7 dni; pokaz/seminarium za 15; dysputa za 16;
  przesłuchanie przed kierownictwem gildii za 15. Lucan przestawił termin ojca z 3 dni
  na 15, używając jego własnego argumentu („jeden okaz to anekdota, seria to materiał").

### Gildia w nocy i rozmowa z Seraphine

- Gildia po ciemku: okienko recepcji zabite deską, nocny urzędnik bez uprawnień, kilku
  wracających z roboty w głównej sali.
- **Właściciel garbarni** — wersja Seraphine, mocniejsza niż plotka: gildia oddała
  dokumenty i tam jej udział się skończył, sprawa poszła do służb miejskich i tam
  stanęła, ale nie dlatego, że go uniewinniono. Wyszedł — za poręczeniem albo z braku
  kogokolwiek, kto by sprawę prowadził. Sprawa jest **formalnie otwarta**, teren nadal
  jego, on żywy i urażony, a Lucan jest tym, kto napisał na niego skargę.
- **Termin przesłuchania:** za jakieś dwa tygodnie, dzień w tę czy w tę, oficjalnie
  jeszcze nie ogłoszony. To pierwsza data, jaką Lucan w tej sprawie ma.
- **Nagroda za Akt 2** nie została zamieciona, bo Seraphine dopilnowała, żeby w
  rejestrze stało „oczekuje przeglądu", a nie „zamknięte". Cena: rozliczenie idzie tą
  samą sesją co przesłuchanie, więc pieniądze Lucana zależą od tego, jak on na niej
  wypadnie.
- **Dlaczego nie ma ogłoszonej daty:** służby miejskie żądają przekazania ciał, akt i
  dowodów z operacji cmentarnej, gildia się opiera, a dopóki nie jest jasne, kto trzyma
  materiał, nikt nie wyznacza terminu.
- Lucan stawia Spideya na jej biurku i każe mu przyjaźnie zamachać odnóżem. Seraphine
  nie reaguje na pająka, reaguje na **posłuszeństwo**: konstrukt wykonuje, sługa słucha,
  mechanizm nie odpowiada na prośbę. Zakazuje powtarzania tego przy kimkolwiek i mówi na
  głos, że skoro Lucan zaczął od żartu z pająkiem, na jego liście są rzeczy gorsze.
  Lucan kontruje trafnie — z zewnątrz nie da się odróżnić wyuczonej sztuczki od świeżego
  posłuszeństwa — a ona to przyznaje, wskazując granicę: argument jest **prawny i
  publiczny**, trzyma się przed magistratem i tłumem, nie przed nikim, kto czyta więź, a
  tellem jest **nowość** reakcji, nie sam gest.
- **Nazwisko.** Lucan ostrzega ją, że przez jego nazwisko sprawą szybko zajmą się
  Akademia i rody. Ocena Seraphine: nekromanta bez nazwiska to sprawa dyscyplinarna i
  karna, nekromanta z nazwiskiem to spór o jurysdykcję, w którym Lucan przestaje być
  oskarżonym i staje się **stawką**. Jej osłona przy tym słabnie, bo nie osłoni go w
  jurysdykcji, w której nie siedzi.
- **Doktryna prawna.** Lucan wykłada swoją linię (funkcjonalna tożsamość instrukcji i
  konstruktu, energia jako energia, brak prawa o zwierzętach, ich duszach i godności,
  więc dopóki nie animuje Varkhena, nie ma realnych problemów). Seraphine przyznaje mu
  premisy — prawo jest antropocentryczne, definicji „praktyki" nikt nie skodyfikował,
  robactwo to realna szara strefa — i wskazuje dziury: nielegalna jest **praktyka**, a
  pająk nie jest oskarżonym, tylko dowodem; szara strefa nie daje immunitetu, bo jad,
  skrytobójstwo i siatka obserwacyjna to osobne czyny; brak przepisu nigdy nie był
  bezpieczeństwem; a Varkhen jest problemem **teraz**, bo więź już istnieje.
- Lucan rozbiera te zarzuty i Seraphine oddaje po kolei: ciał nie ma i nie ma na czym
  budować, najemnik może nosić narzędzia mordu, a zarzut siatki zamyka się na niej samej
  („jeśli bezmyślny konstrukt, to nie raportuje; jeśli raportuje, to nie bezmyślny"),
  tym bardziej że raport przedoperacyjny Lucana z cmentarza leży w aktach gildii i jest
  jego instytucjonalnym alibi na to, skąd wie rzeczy. Varkhena oddaje w całości i
  **przyznaje własny udział**: ona go wyprowadziła z osuwiska i ona go trzyma w piwnicy
  gildii. Dodaje jednak, że Varkhen jest jedynym świadkiem tego, że kapłan znał właściwe
  wejście, kontrolował pieczęcie i przyszedł tam z Orenem — wyzerowanie go niszczy razem
  z dowodem jedyną broń Lucana przeciw Kościołowi.
- **Wniosek Seraphine:** pozycja prawna Lucana jest mocniejsza, niż zakładała, co nie
  usuwa zagrożenia, a je przenosi. Człowieka, którego nie da się skazać, rozwiązuje się
  bez sądu — cichym zamknięciem sprawy przez własny rod, żądaniem stłumienia po stronie
  Kościoła albo wymianą odstąpienia od zarzutów na służbę, dostęp i milczenie.
- **Akademia jako ryzyko miejskie.** Lucan wykłada spór o klasyfikację i ostrzega, że
  osoby związane z Kościołem na uczelni dążą do ograniczenia badań, a akademik pozbawiany
  dorobku jest zdolny do wszystkiego. Seraphine koryguje prognozę: magowie nie są blokiem
  i wygrywają proceduralnie, ale dwa czy trzy pojedyncze incydenty dają panikę, a panika
  nie jest zamieszkami — jest **pretekstem**, i pretekstu potrzebuje Inkwizycja.
  Wskazuje **pułapkę widoczności**: nekromanta widoczny po stronie szerokiej definicji
  jest najlepszym prezentem dla strony wąskiej, więc jego wartość musi być niewidzialna
  (źródło, nie sojusznik). Stawia jeden warunek: chce wiedzieć, **zanim** Lucan
  skontaktuje się z którąkolwiek stroną.
- **Problem seminarium** — wkład Lucana, który Seraphine uznaje za gorszy niż wszystko
  inne tego wieczoru. Akademia nie wezwie go na przesłuchanie, wezwie go na seminarium, a
  odmowy nie uzna za odpowiedź, bo dla niej niewiedza jest stanem do usunięcia. Seraphine
  umie bronić przed trybunałem; nie umie bronić przed ludźmi, którzy **zapiszą** — a
  recenzowany opis metody jest dokładnie tym dowodem, którego Kościół nie ma, wykonanym w
  dobrej wierze przez jego własną stronę. Gildia nie ma nad seminarium jurysdykcji. W
  zamian daje dwie taktyki: **nigdy nie odmawiać** (mówić „nie umiem tego jeszcze
  sformalizować", opis na poziomie mechanizmu bez procedury odtwarzalnej) oraz **jedna
  wersja** opowieści, identyczna na seminarium, na przesłuchaniu i u prawnika.
- **Płaszcz.** Akademia jest pełna ludzi, których Kościół nazwałby nekromantami, ale oni
  mają afiliację — nikt tam nie jest nekromantą, każdy jest licencjonowanym badaczem.
  Lucan również ma płaszcz, tylko uśpiony, a afiliacja w tym środowisku nie jest
  procedurą, jest **rozpoznaniem**: nic nie trzeba reaktywować, wystarczy, że wiedzą, kim
  jest. Koszt płaszcza: Akademia ma wobec członka własną procedurę dyscyplinarną, więc
  wezwanie na seminarium staje się **wykonalne**, a niepłatna synekura jest niewidzialna
  tylko dopóki jej właściciel jest nudny.
- **System Veyrów.** Po wyjaśnieniu, czym rod naprawdę jest, Seraphine przelicza wszystko
  od nowa: spór o jurysdykcję może wcale nie być sporem, a wewnętrzną realokacją; taki
  system nie skazuje i nie broni, tylko **przydziela**, więc najbardziej prawdopodobnym
  końcem sprawy nie jest kara, a posada ze smyczą; a rejestr, który system prowadzi, jest
  rejestrem pozycji, nie sympatii — dwa lata uciekania nie wypisały Lucana z niczego,
  zrobiły z niego **aktyw niezarządzany**, a takie zostają zarządzone w chwili, gdy stają
  się widoczne. Widoczność przychodzi za dwa tygodnie trzy razy z rzędu: przesłuchanie,
  seminarium, dysputa.
- **Dwa aktywa wymienione, żadne nieoddane.** Lucan mówi jej o dość potężnej relikwii, po
  którą ktoś się zgłosi, i o leadzie dotyczącym osób związanych z transportem zwłok po
  stronie **straży** — zamierza szantażować obie strony i tego jej nie mówi. Seraphine
  domyśla się, że relikwia jest kościelna, nie pyta o szczegóły i nazywa rzecz właściwie:
  coś, po co ktoś się zgłosi, nie jest aktywem, jest **terminem**. Z samego istnienia
  leadu wyciąga natomiast wniosek, którego Lucan nie szukał: jeśli ludzie ze straży siedzą
  w transporcie zwłok, to żądanie służb miejskich o przekazanie ciał i akt ma drugie
  czytanie — mogą chcieć materiału, żeby go **pochować**, a gildia od tygodnia chroniła
  dowody przed ludźmi, których te dowody dotyczą. Zauważa też na głos, że Lucan wymienił
  oba aktywa i nie powiedział, że je oddaje. Zadaje przy tym pytanie bez odpowiedzi: czy
  ta sieć jest w ogóle ścigana, czy tolerowana z góry — bo w drugim wypadku szantaż nie
  jest dźwignią, a zgłoszeniem się do kolejki.
- **Lokal do spania.** Lucan chce miejsca, które da się przeszukać bez skutku, i ma klucz
  do domu garbarnika. Seraphine rozbiera pomysł: dom przypisany do otwartego postępowania
  jest jednym z niewielu miejsc, które można legalnie przeszukać z nakazem, a wszystko, co
  tam znajdą, przyklei się do Lucana. Właściwe kryterium: nie pusty pokój, a pokój z
  **nudnym właścicielem** i bez związku z jakimkolwiek otwartym postępowaniem.
- Na koniec Seraphine mówi o sobie, bez ironii: jest prawdopodobnie jedyną stroną, której
  osłona nad Lucanem nie jest transakcją, i jednocześnie najsłabszą stroną przy stole.

## Ekspozycja sekretów

- **Ojciec Lucana** zna teraz metodę — vitae w martwym ciele i to, że kapłan nazwałby to
  śmiercią. Ma fakty, nie ma ram: nie użył słowa „nekromancja", nie interesuje go, że
  cokolwiek tu jest przestępstwem, i nie zdradzi z wyliczenia — ale może wygadać wszystko
  z entuzjazmu, bo uważa, że dobra praca ma być widziana. Nie wie, że okaz oddany
  Akademii ma być wabikiem.
- **Seraphine** widziała Spideya z bliska i widziała, jak wykonuje precyzyjne polecenie.
  Wie o dyspucie, o nazwisku, o relikwii i o istnieniu leadu o straży. Nie wie, że ojciec
  zna metodę, ani że okazy mają iść pod nazwiskiem Veyr.

## Stan interludium

Środek nocy dnia 1. Lucan jest w pokoju Seraphine na górze gildii, Spidey stoi na jej
papierach, lampa dopalona. Nie ma gdzie spać i nie wybrał lokalu. Urobek sieciarzy leży
w baszcie do jego powrotu. Jedwabniki są w koszyku, sześćdziesiąt kilo złota i relikwiarz
nadal w gildii, nierozliczone. Za dwa dni spotkanie z Borosem i Marą o pieniądzach i
prawniku z obiegu przestępczego; za około dwa tygodnie przesłuchanie, seminarium i
dysputa w jednym tygodniu. Ostatnia rzecz niepowiedziana Seraphine — że ojciec zna metodę
i że okazy mają iść pod nazwiskiem — jest jednocześnie tą, która zderza plan ojca z jej
radą.

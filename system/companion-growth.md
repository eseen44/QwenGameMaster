# Wzrost sług przez energię życiową

Sługa nekromantyczny nie jest ograniczony skalą zwierzęcia, z którego powstał. Wchłonięta energia życiowa może zostać zachowana, a następnie świadomie przeznaczona na trwałe przeobrażenie: masę, pancerz, mobilność, narząd, zmysł, pojemność zbiornika, zdolność albo sieć.

## Zasady

- Samo polowanie utrzymuje małe ciało i bieżący zbiornik. Nie powoduje automatycznej ewolucji.
- Trwały wzrost wymaga zapisanych godzin przy stole i realnego materiału dawcy oraz decyzji Lucana o kierunku przeobrażenia (`retcon_000017`). Energia nie jest walutą wzrostu — jest paliwem dojrzewania (`retcon_000103`, `retcon_000112`).
- Nie ma twardego biologicznego maksimum ani końcowej rangi. Każdy krok może tworzyć następny, ale koszt rośnie wraz z już uzyskaną skalą i złożonością.
- Trwały wzrost kosztuje **czas przy stole, nie energię** (`retcon_000017`), i jest **tani** (`retcon_000024`). Jedna modyfikacja to **około godziny** pracy ręcznej, do dwóch przy wyższej trudności. Pełny zestaw kilku różnych modyfikacji na okazie klasy Spideya mieści się **poniżej ośmiu godzin łącznie** — to kanoniczny punkt odniesienia, bo tyle zajęła koronkowa robota na samym Spideyu.
- **Nie ma eskalacji.** Licznik `permanent_growth_steps` jest zapisem historii, nie mnożnikiem ceny. Dawna reguła `8 × 1.5^n` została skasowana w całości (`retcon_000024`) — przeżyła dwa poprzednie retcony i za każdym razem służyła do odtworzenia niedoboru w nowej jednostce.
- Energia Lucana nie jest w to zaangażowana — zostaje zasobem czarów, transferów w sieci i podtrzymywania Varkhena.
- **Zakaz dla narratora:** modyfikacja sług jest w tej kampanii tania i szybka. Nie odtwarzać niedoboru w kolejnej jednostce (odczynniki → energia → godziny → eskalacja godzin). Realne ograniczenia są instytucjonalne i informacyjne, nie produkcyjne.
- Materiał dawcy i godziny muszą być realne i zadeklarowane; nie można dopisać retrospektywnego wzrostu z niepoliczonej dawnej pracy.
- Wzrost nie daje automatycznie wszystkiego. Nowe możliwości otrzymują koszty, warunki dostarczenia i co najmniej dwie praktyczne słabości.

## Sługa jako narząd (retcon_000158, propozycja gracza 07.09.2026)

Lista wyżej zawsze zawierała słowo **zdolność** i nikt go nigdy nie użył. Zawiera je nadal:
trwałe przeobrażenie może dać okazowi **moc, której Lucan sam nie ma**, i jest to droga
równoległa do uczenia się jej przez niego. Precedens chodzi po scenie od Aktu 1 — Spidey ma
wszczepiony gruczoł i własny zbiornik toksyny paralitycznej.

- **Moc siedzi w słudze.** `player/abilities.yaml` Lucana się od tego nie zmienia.
- **Cena jest ta, która już stoi**: około godziny pracy ręcznej, do dwóch przy wyższej
  trudności, bez eskalacji; realny, zadeklarowany materiał dawcy; energia Lucana nie jest
  w to zaangażowana. Nowa możliwość dostaje koszty, warunki dostarczenia i co najmniej dwie
  praktyczne słabości. **To jest cała danina — narrator nie dokłada drugiej.**
- **Zasila go własny zbiornik okazu** (`servant_load_uses_separate_energy_reservoirs`).
  Rezerwa Lucana nie jest tu sufitem; sufitem jest zbiornik sługi i jego bilans dobowy.
- **To jest najcichsza droga, jaką Lucan ma.** Wedle `retcon_000131` widoczność i ślad
  powstają PRZY SŁUDZE. Gdy okaz działa własnym narządem z własnego zbiornika, przy Lucanie
  nie powstaje nic — nawet ślad przesyłu siecią, bo przesyłu nie ma.
- **Sufit skali z `retcon_000157` obowiązuje i nie rozpuszcza się przez liczbę.** Ograniczenie
  jest na pojedynczym efekcie: zator, rozsadzona rura, zatruta beczka — tak; tsunami i powódź
  nie, i nie staną się możliwe dlatego, że okazów jest sto. Równocześnie narrator **nie wymyśla
  limitu liczby jednostek ani wąskiego gardła produkcji** — sto okazów robiących sto małych
  rzeczy jest dokładnie tym, czym ta nekromancja ma być.

## Pętla aktualizacji

1. Zapisz zainwestowane godziny pracy oraz zużyty materiał dawcy.
2. Jeżeli gracz chce trwałej zmiany, zaproponuj konkretny kierunek i policz wymagane kroki.
3. Zapisz inwestycję, nową warstwę obiektu i jej ograniczenia w jednej transakcji.
4. Skompiluj obiekt oraz uruchom replayy dotyczące jego roli.

Ta reguła jest kalibracją kampanii Lucana, nie uniwersalnym prawem każdego świata.

## Rozwój z nadwyżki (retcon_000103, deklaracja gracza 31.08.2026)

Zasada „samo polowanie nie powoduje automatycznej ewolucji" NIE znaczy „najedzony sługa nie
zmienia się w ogóle". Znaczy tylko tyle, że **nowy narząd** wymaga deklaracji i godzin przy stole.

Najedzony sługa z nadwyżką **powoli rośnie i się rozwija**: umysł, osobowość, doświadczenie
w tym, co robi. To nie jest nagła zmiana i nie jest ewolucja narządowa — to dostosowanie formy
do funkcji oraz do wyobrażeń i siły nekromanty, dokładnie tak, jak stało się ze Spideyem.
Nadwyżka ponad pełny zbiornik idzie do `growth_bank` w instancji.

## Bilans dobowy sługi (retcon_000105, deklaracja gracza 31.08.2026)

| sytuacja | na dobę |
|---|---|
| posterunek ze zwykłym zadaniem i dostępnym żerem | 0 — wychodzi na zero |
| bez rozkazu, żer normalny (łąka, ulica) | +1,0 do `growth_bank` |
| bez rozkazu, żer obfity i bezpieczny (wije w kanałach) | +2,0 |
| padlinożerca bez rozkazu (żuki żrące gnilne) | +0,5 — to nie jest polowanie |
| posterunek bez żeru | −1,0 — smycz bez zmian |

Zbiornik napełnia się pierwszy; dopiero nadwyżka ponad pojemność idzie do `growth_bank`.
Porcja tłumiąca rozkład zdejmuje ostatni wiersz, **nie zastępuje żywienia**.

Drabina dojrzałości ma od `retcon_000180` **osiem stopni** i własną sekcję niżej. Trzy progi
z tej tury (10 / 30 / 60) zostały w niej bez zmian jako pierwsze trzy szczeble.

## Drabina dojrzałości — osiem stopni (retcon_000180, deklaracja gracza 13.09.2026)

Jedna drabina dla **wszystkich** okazów; klas pośrednich nie ma. Progi narastająco w `growth_bank`.
Lucan stoi na tych samych progach **razy dziesięć** — jego rozwój jest o rząd droższy niż rozwój
drobnego okazu i to jest cały powód, dla którego jego bank latami stoi nisko.

| # | stopień | próg | Lucan | co się zmienia w głowie |
|---|---|---|---|---|
| 0 | `fresh` | 0 | 0 | wykonuje rozkaz dosłownie, gubi go przy zmianie warunków |
| 1 | `settled` | 10 | 100 | trzyma rozkaz stały; własny gest i własny timing |
| 2 | `judging` | 30 | 300 | wybiera **sposób** wykonania |
| 3 | `seasoned` | 60 | 600 | ocenia sytuację; odstępuje od litery rozkazu, gdy litera szkodzi celowi |
| 4 | `autonomous` | 110 | 1100 | stawia sobie podcele; działa bez rozkazu w swojej dziedzinie |
| 5 | `thinking` | 180 | 1800 | wnioskuje o tym, czego nie widział; łączy meldunki; dzieli się pamięcią |
| 6 | `distinct` | 280 | 2800 | ma własne zdanie i je **wyraża** — głos, preferencje, niechęci, odmowa |
| 7 | `companion` | 420 | 4200 | własna wola; wejście do `companion_class` (`retcon_000179`) |

Szczebel siódmy jest tym samym, co opisuje `retcon_000179`: byt, który służy z **przywiązania**,
nie z trzymania. Własna wola **nie jest pretekstem do buntu** (`retcon_000182`): taki byt wyrósł
w sieci i czuje w niej wszystkie pozostałe jednostki — to jego rodzina i jedyne, co zna. Sprzeciw
ma kształt zdania odrębnego, ociągania się i pytania „po co", nie odmowy służby. Naprawdę rusza
nim zagrożenie dla sieci, nie obietnica wolności. Lucanowi zostaje weto, ale jego użycie **niszczy relację** — to akt nazwany,
z konsekwencją na osiach, nie przełącznik trybu. Drabina jest więc drogą od okazu do kompana
i domyka zdanie, które od 31.08.2026 stało w `planning/anchored-companions.yaml` bez liczb:
*„teraz gest i timing, później wybór sposobu wykonania, na końcu głos"*.

**Każdy szczebel daje trzy rzeczy, nie jedną:**

1. **+1 pojemności zbiornika, +2 integralności.**
2. **Jedno dostosowanie ciała do funkcji** — patrz reguła kierunku niżej.
3. **Posunięcie na osi umysłu** — treść z tabeli. Lucana ta kolumna nie dotyczy; jego szczeble
   płacą z listy `retcon_000112`: pokrycie braku snu, szybsze uczenie, mięśnie, pamięć,
   +1 pojemności rezerwy.

Progi wolno przesunąć jednym zdaniem gracza. Drabina wyłącznie **przyznaje**, niczego nie odbiera.

### Kierunek szczebla czyta się z funkcji, nie z deklaracji

Kierunku **nie wybiera gracz ani narrator**. Źródłem jest to, co okaz **faktycznie robi**:
posterunek, stały rozkaz i historia użycia. Żuk, który kopie, dostaje łatwiejsze kopanie.
Żuk, który magazynuje, dostaje pojemność i mniejszy upływ. Wij, który mapuje, dostaje pamięć
trasy. Spidey, który robi spec-ops, dostaje ciszę, ocenę i wybór drogi. Zawisak, który ma być
niewidzialny w locie, dostaje pokrycie i cichy lot.

**Test przed przyznaniem:** jeśli nie umiesz powiedzieć, co ten okaz robił przez ostatnie dni,
nie umiesz przyznać mu szczebla. Wypowiedziana intencja Lucana nie jest źródłem kierunku — jest
nim funkcja, którą okaz pełni.

### Doświadczenie karmi bank obok żeru

`retcon_000105` dawał posterunkowi z zadaniem i dostępnym żerem **0,0 na dobę** — czyli okaz
**używany do pracy nie dojrzewał**, a dojrzewał wyłącznie ten, kto łaził luzem. To zostało
odwrócone: okaz, który faktycznie wykonał swoją funkcję i coś z tego wynikło, dostaje **+1 do
banku za scenę**, niezależnie od żerowania. Stały rozkaz przestaje być karą za rozwój.

Składnik jest **osobny i księgowany za zdarzenie**, nie za dobę — stawki dobowe zostają bez zmian.
`tools/growth_settle.py` go nie liczy, bo nie wie, która scena była robotą; wpis robi narrator
w turze, w której praca się wydarzyła.

### Wyssanie żywego omija sufit

Bezpośrednie wyssanie **żywego** wpada do banku w całości, z pominięciem sufitu przyjęcia:
mały (szczur, ptak, kot) **2**, średni (pies, owca, cielak) **10**, dorosły człowiek **30**,
duże zwierzę (koń, wół) **60**. Wyssanie **nieumarłego** rozwoju nie daje — oddaje swój zbiornik
do rezerwy i tyle (`retcon_000018`: pająk dał 3).


## Siła nieumarłego jako dźwignia integralności (retcon_000104, deklaracja gracza 31.08.2026)

Nieumarli są naturalnie **nieco** silniejsi od swoich żywych odpowiedników. To nie jest supermoc,
tylko możliwość użycia integralności tkanek jako dźwigni: ciało, które nie chroni się przed bólem
i zmęczeniem, może wydać z siebie więcej.

Nadużywanie tej siły powoduje **zniszczenia mechaniczne w strukturze** okazu — ubytek
**integralności, nie energii**. Skutek jest trwały do naprawy przy stole.

## Nic nie przepada — sieć naczyń połączonych (retcon_000109, deklaracja gracza 31.08.2026)

**Nie istnieje problem za dużej ilości energii.** Pełny zbiornik nie jest sufitem, przy którym
nadmiar znika. Kolejność jest taka:

1. węzeł napełnia własny zbiornik,
2. część nadwyżki idzie na własny rozwój do `growth_bank`,
3. **reszta płynie siecią** do pozostałych węzłów i do samego Lucana — na uzupełnienie rezerwy
   albo na celowe wytrącenie w transporcie, jeżeli Lucan tak chce.

Obowiązują zwykłe straty propagacji (`companions/webber-network.yaml#network_cost_model`:
80% sieciarz→cel, 70% Lucan↔Spidey, mnożne na przeskok). **Strata przesyłowa jest jedynym
realnym ubytkiem.**

`surplus_routing` to **ustawienie na węźle**: `growth`, `network` albo podział. Domyślnie
`growth`, dopóki Lucan nie wskaże odbiorcy. Zmienia się rozkazem — za darmo i bez czasu przy stole.

Kierunek rozwojowy nazwany przez gracza: **żuki jako małe pojemniki energii** — buforowy węzeł
magazynowy, nie tylko czujnik. Patrz `planning/specimen-upgrades.yaml#enlarge_reservoir_to_tank`.

## Integralność odbudowuje się tak samo szybko jak rezerwa (retcon_000111)

Jednostka na wejściu daje jednostkę odbudowy. Nie ma osobnego, wolniejszego przelicznika dla
integralności. Ile dostaje konkretny odbiorca — np. Varkhen — jest **ustawieniem Lucana**,
nie stałą kampanii: łącza wolno przepiąć, dołożyć i zwiększyć. Sufitem są pojemność i straty
propagacji.

## Nadmiar rozwija też Lucana (retcon_000112, deklaracja gracza 31.08.2026)

Rozwój z nadwyżki **nie dotyczy wyłącznie sług**. Nadmiar energii rozwija trwale również
nekromantę. Rodzaj rozwoju zależy od gatunku, a tempo **nie jest eksplozywne** — to powolne
narastanie, nie skok.

**Lucan:** pokrycie braku snu, szybsze uczenie się, przyrost mięśni, lepsza pamięć, powolny
wzrost samej rezerwy. Efekty **nie są na tyle duże, żeby były oczywiste z zewnątrz** — najwyżej
ktoś, kto trenuje z nim codziennie, zauważy, że szybko się regeneruje i wolno męczy *jak na maga*.
W zasięgu jest dziś jedna taka osoba: `npc_mara`. To nie jest nadludzka sprawność i nie zdejmuje
potrzeby treningu ani nauki — **skraca drogę, nie znosi jej**.

**Sługi:** rozwój osobowości i ekspertyzy; samodzielne myślenie i stosowanie taktyki; większa
pamięć **oraz zdolność dzielenia się wspomnieniami**; rozwój w roli, którą okaz pełni — fizyczny
albo przez pojawianie się kolejnych umiejętności.

Nowa umiejętność, która **pojawia się sama z dojrzałości**, nie wymaga godzin przy stole.
Nowy **narząd** nadal wymaga (`retcon_000103`, `retcon_000024`).

## Ekonomia nadwyżki — skala, sufit, rozdział (retcon_000115, deklaracja gracza 31.08.2026)

Trzy klauzule, wszystkie zadeklarowane przez gracza:

1. **Skala.** Nadwyżka całej sieci to **kilkanaście jednostek na dobę**. Suma stawek
   w `campaigns/lucan/state/growth-banks.yaml` daje 14,5 na dobę generowane przez sieć —
   osobno od własnej regeneracji Lucana, która wynosi 6,0 na dobę.
2. **Sufit rozwoju.** Nadmiar leci naturalnie w rozwój, ale węzeł wchłania najwyżej
   **połowę własnej pojemności zbiornika na dobę**. Zbiornik 3 → sufit 1,5; zbiornik 6 →
   3,0; zbiornik 12 → 6,0; Lucan przy 15 → 7,5. Realna presja idzie więc na **powiększanie
   zbiorników** (`planning/specimen-upgrades.yaml#enlarge_reservoir_to_tank`, 3 → 12 za
   około godzinę przy stole), nie na zdobywanie energii.
3. **Rozdział.** Nadmiar ponad sufit nie przepada (`retcon_000109`) — jest rozdzielany
   pomiędzy pozostałe obiekty sieci ze zwykłymi stratami propagacji. **Wyjątkiem jest
   Varkhen**, racjonowany decyzją Lucana (`retcon_000113`).

**Lucan jest obiektem w sieci jak pozostałe węzły.** Odbiera rozdzielaną nadwyżkę bez
osobnego rozkazu i bez czekania na własny sufit rezerwy.

**Zakaz dla narratora:** nie przedstawiać rozdziału nadwyżki jako niewydanego rozkazu ani
nie liczyć go graczowi jako przeoczonej dźwigni. Dzieje się domyślnie.

## Miejsce prawdy dla banków wzrostu (retcon_000114)

`campaigns/lucan/state/growth-banks.yaml` jest **jedynym** rejestrem `growth_bank` i stawek
dobowych. Nie ma go w `load` z `brief` (celowo — budżet kontekstu), więc łatwo go pominąć
i policzyć stawki od nowa. Tak się stało w turze 178: powstał równoległy rejestr w plikach
instancji i cztery fałszywe liczby podane graczowi jako pomiar. **Przed każdą turą dotyczącą
rozwoju, nadwyżki, dojrzewania albo karmienia sieci — przeczytaj ten plik.**

## Varkhen jest celowo odcięty (retcon_000113)

Cztery łącza podtrzymujące to **racjonowana struga**, nie maksimum przepustowości. Varkhen nie
jest niedożywiony przez wąskie gardło — jest ograniczony, **bo Lucan tak zdecydował**.

Mechanika z `retcon_000111` obowiązuje (integralność odbudowuje się tak samo szybko jak rezerwa,
wielkość strugi jest ustawieniem), ale **domyślnym stanem jest ograniczenie**. Zniesienie go
byłoby zmianą polityki wobec Varkhena — deklaruje ją gracz, ma własne skutki.

**Zakaz dla narratora:** nie podawać dokarmienia Varkhena jako oczywistej optymalizacji i nie
liczyć go jako zmarnowanej okazji.

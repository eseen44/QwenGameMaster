# Wzrost sług przez energię życiową

Sługa nekromantyczny nie jest ograniczony skalą zwierzęcia, z którego powstał. Wchłonięta energia życiowa może zostać zachowana, a następnie świadomie przeznaczona na trwałe przeobrażenie: masę, pancerz, mobilność, narząd, zmysł, pojemność zbiornika, zdolność albo sieć.

## Zasady

- Samo polowanie utrzymuje małe ciało i bieżący zbiornik. Nie powoduje automatycznej ewolucji.
- Trwały wzrost wymaga znaczącej, zapisanej inwestycji energii oraz decyzji Lucana o kierunku przeobrażenia.
- Nie ma twardego biologicznego maksimum ani końcowej rangi. Każdy krok może tworzyć następny, ale koszt rośnie wraz z już uzyskaną skalą i złożonością.
- Trwały wzrost kosztuje **czas przy stole, nie energię** (`retcon_000017`), i jest **tani** (`retcon_000024`). Jedna modyfikacja to **około godziny** pracy ręcznej, do dwóch przy wyższej trudności. Pełny zestaw kilku różnych modyfikacji na okazie klasy Spideya mieści się **poniżej ośmiu godzin łącznie** — to kanoniczny punkt odniesienia, bo tyle zajęła koronkowa robota na samym Spideyu.
- **Nie ma eskalacji.** Licznik `permanent_growth_steps` jest zapisem historii, nie mnożnikiem ceny. Dawna reguła `8 × 1.5^n` została skasowana w całości (`retcon_000024`) — przeżyła dwa poprzednie retcony i za każdym razem służyła do odtworzenia niedoboru w nowej jednostce.
- Energia Lucana nie jest w to zaangażowana — zostaje zasobem czarów, transferów w sieci i podtrzymywania Varkhena.
- **Zakaz dla narratora:** modyfikacja sług jest w tej kampanii tania i szybka. Nie odtwarzać niedoboru w kolejnej jednostce (odczynniki → energia → godziny → eskalacja godzin). Realne ograniczenia są instytucjonalne i informacyjne, nie produkcyjne.
- Materiał dawcy i godziny muszą być realne i zadeklarowane; nie można dopisać retrospektywnego wzrostu z niepoliczonej dawnej pracy.
- Wzrost nie daje automatycznie wszystkiego. Nowe możliwości otrzymują koszty, warunki dostarczenia i co najmniej dwie praktyczne słabości.

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

Drabina dojrzałości, narastająco w `growth_bank`: `fresh` → osiadły **10**, osiadły → z sądem
**30**, z sądem → wyrobiony **60**. Każdy stopień daje **+1 pojemności zbiornika, +2 integralności**
oraz nazwany zysk behawioralny. Progi są propozycją narratora przyjętą w tej turze i wolno je
zmienić — drabina wyłącznie **przyznaje**, niczego nie odbiera.

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

## Varkhen jest celowo odcięty (retcon_000113)

Cztery łącza podtrzymujące to **racjonowana struga**, nie maksimum przepustowości. Varkhen nie
jest niedożywiony przez wąskie gardło — jest ograniczony, **bo Lucan tak zdecydował**.

Mechanika z `retcon_000111` obowiązuje (integralność odbudowuje się tak samo szybko jak rezerwa,
wielkość strugi jest ustawieniem), ale **domyślnym stanem jest ograniczenie**. Zniesienie go
byłoby zmianą polityki wobec Varkhena — deklaruje ją gracz, ma własne skutki.

**Zakaz dla narratora:** nie podawać dokarmienia Varkhena jako oczywistej optymalizacji i nie
liczyć go jako zmarnowanej okazji.

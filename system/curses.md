# Klątwy: dyskrecja, odporność i eskalacja

## Dwa osobne pytania

Przy klątwie zawsze rozdziel:

1. Czy cel rozpoznaje wrogie działanie i potrafi aktywnie przerwać dostarczenie efektu?
2. Czy jego ciało, umysł albo struktura magiczna wytrzymują sam efekt?

Zwykły człowiek bez przygotowania może nie mieć sensownej odpowiedzi na pierwszy punkt. Nie oznacza to jednak, że każda klątwa automatycznie pokonuje jego naturalną odporność ani że ta sama technika działa bez zmian na wyszkolonego agenta.

## Pomniejsze klątwy Lucana

`Numb`, `Minor Hex`, `Misnotice` i pomniejszy pech są tanimi, szybkimi cantripami. Nie wyglądają jak kulturowy stereotyp klątwy: wielki rytuał, inkantacja, krąg i jawny omen. Przeciętny strażnik albo cywil często:

- nie wie, że został zaatakowany magią;
- przypisuje objaw zmęczeniu, przypadkowi, własnemu błędowi albo otoczeniu;
- nie potrafi dobrać aktywnej obrony, nawet jeżeli później zauważa skutek.

W mechanice taki przypadek może otrzymać `condition_unaware_of_subtle_curse`. Warunek obniża obronę dostarczenia i odporność tylko dlatego, że cel nie rozpoznaje kanału ataku. Nie stosuje się go do celu alarmowanego, magicznie wyszkolonego, osłoniętego albo aktywnie szukającego klątw.

## Test diagnostyczny

Lucan może rzucić tanią klątwę również po to, by sprawdzić klasę celu. Brak widocznego efektu sugeruje odporność, przygotowanie, ochronę albo błędnie dobrany kanał — nie ujawnia automatycznie dokładnej przyczyny ani wartości statystyk. Powtarzanie prób kosztuje energię, czas i może stworzyć rozpoznawalny wzorzec dowodowy.

## Eskalacja mocy

Większa klątwa nie jest darmowym zwiększeniem liczby:

- kosztuje wielokrotnie więcej energii;
- wymaga większego skupienia albo czasu;
- pozostawia silniejszy ślad i może stać się widoczna dla magicznie świadomych obserwatorów;
- nadal może potrzebować zaskoczenia, zgody, unieruchomienia lub innych przewag.

`capability_lucan_numb_overcharged` reprezentuje historyczny, nieekonomiczny nacisk użyty na Orenie. Zwykły stack kosztuje `0.1` jednostki, a przeciążony wariant `1.5`; nie zastępuje on zwykłego `Numb` jako domyślnego trybu.

`Confusion` należy do innej klasy. Kosztuje `3` jednostki, wymaga koncentracji oraz ciągłego kontaktu wzrokowego z jednym celem. Jest silne, lecz jawne: przerwanie spojrzenia, zasłona, utrata koncentracji albo ingerencja trzeciej osoby natychmiast kończą efekt. Najlepiej działa w sytuacji 1 na 1 lub tam, gdzie inni obserwatorzy nie widzą rzucającego i celu.

Mroźny Dotyk/Bone Chill kosztuje `1` pełną jednostkę przez dotyk lub krótki stożek. Dystansowy impuls kosztuje `2` i ma mniejszą intensywność. Rezerwa `15` oznacza więc około piętnastu bliskich albo siedmiu pełnych dystansowych użyć, ale nie sto pięćdziesiąt pełnych zaklęć: tylko bardzo lekkie cantripy korzystają z kosztu dziesiętnego.

## Precedensy kalibracyjne

- Zwykły, nieprzygotowany człowiek często nie ma aktywnej odpowiedzi na subtelny cantrip.
- Osoba istotna mechanicznie, magicznie świadoma albo przygotowana rozpoznaje kanał i broni się normalnie.
- Oren dopuścił pierwsze użycie, został zaskoczony jego rzeczywistym charakterem, a Lucan zużył nieproporcjonalnie dużo mocy. To nie jest dowód na tanią dominację nad C-rankowym specjalistą.
- Dla Varkhena `Numb` był jedynie kumulującą się przeszkodą podczas jednoczesnego przygważdżania, uszkadzania, tłumienia regeneracji i drenażu. Sam nie rozstrzygał starcia.

## Dotyk jako kanał dostarczenia

Skala poziomów jest już kanonem i opisuje ją `system/metamagic.md`: poziomy `0-10` jako
analogia robocza, koszt zoptymalizowanego czaru `2^(poziom-1)`, cantrip jako osobna klasa
około `0.1`, osie `intensity`, `area`, `range`, `duration`, `targets`, `persistence`,
`precision`. Klątwy nie są wyjątkiem od tego modelu, tylko jego zastosowaniem.

Dotyk to **oś `range` ustawiona na zero** — czyli obniżenie `target_tier`. Precedens jest
w plikach: Mroźny Dotyk kosztuje `1` przez dotyk i `2` na dystans **przy mniejszej
intensywności**, czyli dokładnie jeden stopień różnicy. Zasada ogólna:

- ograniczenie dostarczenia do dotyku jest warte około jednego poziomu;
- zaoszczędzony poziom można wydać na `intensity`, `duration`, `persistence` albo
  `precision` - efekt poziomu `2` kosztuje przez dotyk mniej więcej tyle, co poziom `1`;
- `persistence` opłacona w ten sposób znosi wymóg podtrzymywania: procedura domyka się w
  chwili kontaktu, więc nie potrzeba koncentracji ani kontaktu wzrokowego. To jest wprost
  odpowiedź na słabość `Confusion` (`3`, jawne, kończy je zasłona albo osoba trzecia);
- jeżeli cel sam przyjął kontakt, stosuje się `condition_unaware_of_subtle_curse`.

Czego dotyk nie kupuje: odporności celu na sam efekt, zniesienia kary `2^luka` za brak
zoptymalizowanego wzorca, ani zasięgu. Trzeba stać obok i mieć okazję do kontaktu -
**ale nie trzeba być znanym ani rozpoznanym**. Nikt nie musi wiedzieć, kim jesteś, żeby
podać ci rękę na powitanie; okazja towarzyska jest właśnie tym, co produkuje kontakt między
obcymi.

## Klątwa i dostarczenie są niezależne (retcon_000132, kalibracja gracza 2026-09-02)

Awaria narratora: traktował jedenaście procedur z `item_courtesies_curse_book` jak zamknięty
zbiór przepisów, w którym każda klątwa jest zrośnięta na stałe z jednym rozdziałem
dostarczenia. Pole `delivery` na karcie procedury czytał jako **wymóg**. Jest **zapisem
pierwszego przebiegu**. Żaden plik nie mówił, że te pary są obowiązkowe.

**Mix and match.** Każda znana klątwa może pójść każdym kanałem: dotykiem, rozdziałem
towarzyskim, na dystans jak `Numb`, przez przedmiot, z opóźnieniem albo bez, z pozycji sługi
(`retcon_000131`). Zapadnia pamięci naturalnie wypada na pożegnanie — i wolno ją rzucić
powitaniem albo z daleka i niewidocznie.

**Metamagia jest dodatkowa, nie konieczna.** Żaden czar nie wymusza żadnej metamagii.
Metamagia modyfikuje koszt, siłę, widoczność, rzuty obronne, zasięg i skalę. Czar rzucony
goły działa — jest tylko droższy, głośniejszy albo łatwiejszy do skojarzenia.

### Co kupują rozdziały z książki

Preoptymalizowane kombinacje. `POWITANIE` = dotyk + opóźnienie. Poza klasycznym efektem
metamagii kupują trzy rzeczy naraz:

1. **Obniżenie kosztu** — dotyk jako oś `range` na zerze, warta około jednego poziomu.
2. **Zniesienie rzutu na odparcie.** Oparcie się klątwie wymaga aktywnego, świadomego aktu.
   Człowiek wykonujący rytuał społeczny działa **automatyzmem** — ręka wyciąga się sama.
   Nie ma czym rzucać. Fizyczny efekt dotknięcia czyjejś klatki piersiowej i dotknięcia jej
   gestem powitania jest **identyczny**; różnica siedzi wyłącznie w tym, że w drugim
   przypadku ani ofiara, ani otoczenie nie dostają rzutu na rozpoznanie ani na odparcie.
3. **Zniesienie rzutu na wykrycie.** Klątwę można zauważyć w chwili rzutu. **Opóźnienie
   zrywa łańcuch przyczynowo-skutkowy**, więc w zwykłym zabieganym dniu rzut na detekcję
   jest **pomijany całkowicie**, nie utrudniany.

**Powitanie bez opóźnienia** nadal znosi rzut obronny, ale dopuszcza rzut na
**rozpoznanie-skojarzenie**: „ten ktoś coś mi zrobił". Przykład kanoniczny: przywitanie się
mrożącym dotykiem — cel nie ma szansy na refleks, pierwsze rzucenie idzie z **karą do rzutów
obronnych**, po czym cel orientuje się, że ręka mu zamarzła, i zaczyna się walka.

### Zbiór kanałów jest otwarty

Liczy się **akt przyjęcia czegoś, co należy do rzucającego**. Powitanie, toast,
podziękowanie, kondolencje, podarunek, przedstawienie — konkretny rytuał **nie ma
znaczenia**. Nie ogranicza się to do spisu treści książki: akt wysłuchania z emocją czyjegoś
koncertu otwiera człowieka dokładnie tak samo jak podana dłoń. **Narratorowi nie wolno
odmawiać kanału tylko dlatego, że nie ma go w książce.**

Toast jest w książce połączony z opóźnieniem, ale go **nie wymaga** — opóźnienie jest osobną,
doklejalną osią.

Czego to nie zmienia: odporności celu na sam **efekt** (dwa osobne pytania z góry tego
pliku), kary `2^luka`, ceny zasięgu zdjętego z zera, ani zasady z `event_turn_interlude_095`
— **jedna procedura na kontakt**.

## Dlaczego to działa, czyli status klątw w świecie

Kalibracja gracza z 25.08.2026, obowiązująca.

Klątwy są powszechnie uznawane za **słabe i nieskuteczne**. Są rzadkie, kojarzone z magią
potworów albo wiejskich bab, i nikt poważny się przed nimi nie zabezpiecza, bo kula ognia
jest bardziej widowiskowa i łatwiejsza do pokazania na katedrze. Ta reputacja jest w dużej
części zasłużona - typowa klątwa jest mglista, powolna i losowa.

Klątwy Lucana są czymś innym, i różnica nie leży w mocy, tylko w **celowaniu**. Lucan jest
akademikiem z realnym rozumieniem anatomii, fizjologii i chemii życia: wie, który mięsień
trzyma broń, gdzie biegnie nerw, co robi histamina, co robi wyrzut hormonów i ile trwa, zanim
skutek zacznie być widoczny. To jest oś `precision` kupiona wiedzą zamiast energią. Wiejska
baba rzuca „żeby ci ręka uschła"; Lucan zaciska konkretną grupę mięśni w konkretnej dłoni
przez konkretne pół minuty.

Konsekwencje dla prowadzenia:

- nie traktuj klątw jak zawsze subtelnych cantripów - klątwa poziomu `1-2` robi realne,
  fizyczne rzeczy i może rozstrzygnąć walkę, przesłuchanie albo tortury;
- przeciwnicy przygotowują się na ogień, stal i jawną nekromancję, nie na to;
- mag może zauważyć, że **jego** ktoś przeklina. Zauważenie, że ktoś rzuca klątwę z
  opóźnionym działaniem na **kogoś innego**, jest znacznie trudniejsze i nie jest domyślne;
- cena jest społeczna, nie magiczna: każde użycie zostawia człowieka, którego Lucan dotknął.
  Wzorzec dowodowy buduje się z takich dotknięć, nie ze śladu magicznego.

## Kierunek rozwoju

Klątwy mają wysoki przyszły potencjał jako mało znane narzędzie nekromanty. Rozwój powinien wybierać między subtelnością, szybkością, siłą, czasem trwania i trudnością wykrycia; nie można maksymalizować wszystkich tych cech jednocześnie.

## Klątwy a prawo: dlaczego to nie jest przestępstwo

Kalibracja gracza z 25.08.2026, obowiązująca. Wynika wprost z poprzedniej sekcji i z tego,
co jest — a raczej czego NIE ma — w plikach prawa.

`worlds/solmara/lore/legal-order.yaml` i `worlds/solmara/lore/necromancy-law.yaml` nie
wspominają o klątwach ani razem, ani osobno. To nie jest luka do załatania. To jest
konsekwencja tego, że klątwy uchodzą w tym świecie za słabe, wiejskie i nieskuteczne:
nie ma kategorii przestępstwa dla czegoś, czego nikt nie traktuje poważnie.

Praktycznie:

- **Uporczywe przeklinanie urzędnika to najwyżej nagana i tarcie służbowe.** Nie jest
  zagrożeniem dla wolności, nie jest sprawą karną i nie ma paragrafu, pod który by je
  podciągnąć. Skrzypiące zawiasy, zacinający się zamek, wysypka, pech przy rachunkach —
  to jest kłopot personalny, nie akt oskarżenia.
- **Próg realnej sprawy to skutek TRWAŁY.** Żeby zrobiło się poważnie, ofierze musi się
  stać coś nieodwracalnego: trwałe kalectwo, utrata zmysłu, śmierć. I wtedy sprawa nie
  idzie jako „klątwa", tylko jako to konkretne uszkodzenie albo zabójstwo — mechanizm jest
  wtedy szczegółem dowodowym, nie zarzutem.
- **Nie mylić tego z nekromancją.** Zagrożenie instytucjonalne Lucana bierze się z
  nieumarłych, nie z cantripów. Nie doklejać powagi jednego do drugiego.
- **Realna cena dręczenia urzędnika jest inna i nazwała ją Seraphine**
  (`event_turn_interlude_037_every_signature_has_a_room`): podrażniony urząd nie produkuje
  błędu, który da się wykorzystać, tylko PAPIER. Papier jest problemem. Wyrok nie.

Ślad magiczny nie jest tu żadnym argumentem — patrz `system/magic.md`, sekcja
„Ślad magiczny: co zostaje i jak długo". Świadek na żywo jest zagrożeniem; rezyduum na
klamce po fakcie nie jest niczym.

## Do czego naprawdę służy pech (kalibracja gracza 25.08.2026, obowiązująca)

`ability_minor_bad_luck` **nie jest narzędziem bitewnym ani taktycznym.** Nie służy do
przewracania strażnika, żeby uciec, ani do wygrywania wymiany. Jeśli narrator używa go jak
podcięcia nóg w walce, używa go źle.

Pech jest narzędziem **dramatycznym i reputacyjnym**:

- **Skala.** To nie jest „pękł jeden szew". To jest moment, w którym cały pokój idzie źle
  naraz — ludzie padają, rzeczy się rozsypują, światło gaśnie, liczenie zaczyna się od nowa.
  Nie czyta się tego jako zbiegu okoliczności. Czyta się to jako **złe mojo**.
- **Moment.** Ląduje raz, w scenie, w której coś znaczy. Nie rozmienia się na drobne
  potknięcia co pół strony.
- **Ładunek właściwy jest społeczny.** Nikt nie nazywa tego magią i nikt nie oskarża Lucana.
  Ludzie zapamiętują coś gorszego i trwalszego: że **przy tym człowieku rzeczy się psują**.
  Wokół Lucana buduje się reputacja kogoś, kto generuje problemy wszędzie, gdzie wejdzie —
  i to jest prawdziwy skutek, który narrator ma prowadzić dalej w kolejnych scenach.
- **Narrator nie inscenizuje listy katastrof z deklaracji gracza punkt po punkcie.** Wybiera
  moment, uderza raz i niesie konsekwencję postrzegania.

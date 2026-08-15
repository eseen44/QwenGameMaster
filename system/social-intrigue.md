# Relacje i intryga społeczna

## Cel

System śledzi wyłącznie relacje, zobowiązania i stanowiska, które mogą zmienić późniejszą decyzję. Nie punktuje każdej rozmowy i nie zastępuje odgrywania tabelą reputacji.

## Dwie warstwy

- `personal`: stosunek konkretnej osoby do Lucana, oparty na przeżyciach, więziach, urazach i wzajemności.
- `institutional`: stanowisko organizacji wynikające z jurysdykcji, ryzyka, użyteczności i kosztu politycznego.

Warstwy mogą być sprzeczne. NPC może prywatnie pomagać Lucanowi, a oficjalnie wykonywać niekorzystną decyzję instytucji; może też używać Lucana przeciw własnym przełożonym.

## Karty relacji

Każda ważna więź otrzymuje kierunkową kartę w `campaigns/<id>/relationships/`: `podmiot -> cel`. Karta osobista i stanowisko instytucji nie są tym samym plikiem.

Karta używa czterech osi `-100..100`:

- `cooperation`: gotowość do realnej pomocy albo przeszkadzania;
- `judgment_confidence`: wiara w ocenę sytuacji i skuteczność celu;
- `discretion_trust`: wiara, że cel dotrzyma układu, ujawni krytyczne ryzyko i nie stworzy ukrytego problemu;
- `personal_regard`: sympatia, szacunek, uraza albo koleżeństwo.

Tylko `cooperation` przewiduje bezpośrednie zachowanie w scenie. Pozostałe osie tłumaczą, dlaczego ktoś współpracuje, kontroluje, wybacza albo stawia granice. Nie wyprowadzaj jednej osi automatycznie z drugiej.

## Skala współpracy

`cooperation` używa skali `-100..100`:

- `-100..-60`: aktywny wróg — wydaje zasoby, aby zaszkodzić albo usunąć cel;
- `-59..-20`: przeciwnik — blokuje i podważa cel, gdy koszt jest rozsądny;
- `-19..19`: układ transakcyjny albo stanowisko nierozstrzygnięte;
- `20..59`: współpracownik — podejmuje ryzyko w zamian za wzajemność lub wspólny cel;
- `60..100`: związany sojusznik lub patron — ponosi istotny koszt, zachowując własne granice.

Wysokie `judgment_confidence` z niskim `discretion_trust` oznacza: „wierzę, że umiesz rozwiązać problem, ale chcę wiedzieć, jakie jeszcze zwłoki ukryłeś”.

## Co zapisujemy

Po scenie aktualizuj relację tylko wtedy, gdy zaszło co najmniej jedno:

- ktoś poniósł koszt, został zdradzony, ochroniony albo publicznie upokorzony;
- powstał lub został spłacony dług;
- ujawniono sekret albo przekazano realną dźwignię;
- strona zadeklarowała stanowisko lub użyła zasobów politycznych;
- zmienił się dostęp, jurysdykcja, opieka albo aktywna wrogość.

Każda zmiana wymaga powodu i wydarzenia źródłowego. Po turze zmieniaj tylko oś, zobowiązanie, dźwignię albo ograniczenie, które naprawdę naruszyła scena. Stanowisko publiczne, prywatne przekonanie, wiedza, podejrzenie i kłamstwo pozostają oddzielnymi polami.

## Projektowanie decyzji

- Ważna decyzja określa, komu Lucan daje informację, przysługę, dostęp, lojalność albo zasługę.
- Korzyść może tworzyć koszt gdzie indziej, ale system nie wymusza symetrycznej kary za każdy zysk.
- Nie istnieje domyślna ścieżka zadowolenia wszystkich stron.
- Wrogość musi wynikać z konkretnej straty, zdrady, interesu albo zagrożenia.
- Współpraca może być chłodna i transakcyjna; konflikt nie musi oznaczać natychmiastowej przemocy.

## Prawo i tajemnice

Intryga nie relatywizuje ustalonych praw świata. Jeżeli praktyka jest nielegalna, frakcje mogą spierać się o dowód, jurysdykcję, przykrywkę, zakres kary i polityczny koszt działania, ale nie staje się ona legalna dzięki wysokiej reputacji. Rozróżniaj prywatne podejrzenie, wiedzę pojedynczego NPC, wiedzę instytucjonalną, formalny dowód i fakt publiczny.

Duże grupy używają prawa instrumentalnie. Śledź osobno: kontrolę nad dowodem, właściwość sądu lub instytucji, posiadane przywileje, publiczną narrację oraz zdolność wymuszenia interpretacji. „Chronimy Lucana” nie usuwa przestępstwa — oznacza, że dana grupa podejmuje koszt ukrycia, przekwalifikowania albo zablokowania postępowania, zwykle oczekując czegoś w zamian.

## Testy

Nie wykonuj testu wyłącznie po to, aby arbitralnie zmienić relację. Test może rozstrzygnąć niepewny skutek działania — wiarygodność kłamstwa, zdobycie dowodu, reakcję publiczności albo koszt polityczny. Zmiana relacji wynika następnie z ustalonego faktu, stawki i interesu postaci.

## Prezentacja graczowi

Pokazuj zachowanie, warunki układu, zmianę tonu i konsekwencje. Nie ujawniaj automatycznie punktacji, ukrytych podejrzeń ani pełnej sieci wpływów. Na prośbę systemową można podać znane Lucanowi relacje z zaznaczeniem niepewności.

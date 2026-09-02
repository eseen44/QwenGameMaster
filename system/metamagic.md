# Brutalne skalowanie i zoptymalizowane czary

## Zasada

Każdą opanowaną technikę magiczną można próbować rozszerzyć bez poznawania
osobnej metamagii. Wymagane są:

- znajomość i wystarczająca ekspertyza w technice bazowej;
- energia pokrywająca pełny, nieefektywny koszt;
- możliwość utrzymania wybranej formy, zasięgu, obszaru i czasu działania.

Nie tworzy to nowego zoptymalizowanego czaru. Jest brutalnym przepychaniem
energii przez prostszy wzorzec. Dlatego koszt rośnie szybciej niż rezultat,
a razem z nim rosną czas, ślad magiczny, niestabilność i ryzyko dla kanału.

## Poziom efektu a poziom wzorca

`pattern_tier` opisuje poziom znanej, zoptymalizowanej formuły. `target_tier`
opisuje skalę żądanego rezultatu. Poziomy `0–10` są analogią roboczą, nie
listą slotów ani prawem fizyki świata.

Zoptymalizowany czar wyższego poziomu zawiera geometrię, rozdział przepływu,
stabilizację i bezpieczniki. Typowy koszt poziomów `1–10` rośnie jak
`2^(poziom−1)`: `1, 2, 4, 8, 16, 32, 64, 128, 256, 512`. Cantrip pozostaje
osobną klasą około `0.1`.

Prosty czar może osiągnąć podobny rezultat, lecz płaci dodatkowy mnożnik
`2^luka`, gdzie luka jest różnicą między poziomem żądanego efektu a poziomem
znanego wzorca. Jest to cena braku zoptymalizowanej procedury.

Obsługiwane osie to: `intensity`, `area`, `range`, `duration`, `targets`,
`persistence` i `precision`. Osie nie mnożą kosztu ponownie: ich kombinacja
określa końcowy `target_tier`. Nadal zwiększają trudność kontroli, niestabilność
i zakres możliwych konsekwencji.

## Metamagia jest dodatkowa, nie konieczna (retcon_000132)

**Żaden czar nie wymusza żadnej metamagii i żaden nie jest zrośnięty z jednym kanałem
dostarczenia.** Metamagia modyfikuje koszt, siłę, widoczność, rzuty obronne, zasięg i skalę —
i nic poza tym. Czar rzucony goły działa; jest tylko droższy, głośniejszy albo łatwiejszy do
skojarzenia z rzucającym.

Wynika z tego zasada **mix and match**: dowolna znana technika idzie dowolnym kanałem, z
dowolnym zestawem osi. Zapis `delivery` na karcie procedury jest **historią pierwszego
przebiegu**, nie ograniczeniem. Pełne rozwinięcie dla klątw i kanałów społecznych:
`system/curses.md`, sekcja „Klątwa i dostarczenie są niezależne".

## Konsekwencje

- Brak wyższego czaru nie czyni rezultatu metafizycznie niemożliwym.
- Brak energii lub ekspertyzy daje `possible_only_with_new_leverage`, a nie
  prawo do rzutu liczącego na cud.
- Wymagana energia musi istnieć w stanie świata: w rezerwie, baterii, sieci,
  rytuale albo przechwyconym przepływie.
- Brutalne skalowanie nigdy nie jest subtelne. Dowody, reakcje świata i
  uszkodzenia kanału są normalną częścią ceny.
- Poznanie właściwego czaru wyższego poziomu usuwa karę luki optymalizacyjnej,
  dlatego może zmniejszyć koszt o wiele rzędów wielkości.

## Precedens Bone Chill

Ciągły stożek użyty przy przeciążeniu kolektora był Bone Chill rozszerzonym w
intensywności, obszarze, zasięgu i trwałości pozostałego lodu. Samo podniesienie
mocy odpowiadałoby mniej więcej poziomowi `3–4`; pełna kombinacja odpowiada
efektowi poziomu `6` wymuszonemu przez wzorzec poziomu `1`.

Źródło oddaje około `1024` jednostek na każdy sześciusekundowy odcinek
podtrzymania. Nie jest to pojemność rezerwy Lucana, lecz energia przepuszczona
przez niego w czasie: około `170.67/s`, narracyjnie około `200/s`. Połączony
układ Lucana i pająków miał w tej chwili około `20` jednostek pojemności, więc
chwilowe obciążenie kanału wynosiło około `8.53x` jego bezpiecznej
przepustowości. To skrajne, lecz nie automatycznie śmiertelne przeciążenie:
uzasadnia trwały ślad w psychice i kanale magicznym oraz późniejsze poszerzenie
rezerwy, ale nie musi zwęglać ciała. Całkowity koszt historycznej sceny pozostaje
niezmierzony, ponieważ dokładny czas podtrzymania i wydajność kolektora nie są
znane. Efekt zostawił silny ślad, trwały lód, odmrożenia i utratę kontroli nad
dokładną ilością mocy. Nie byłby dostępny z osobistej rezerwy Lucana.

Globalna apokalipsa lodowa z tego samego wzorca pozostaje technicznie możliwa,
ale na poziomie `10`, przy jednoczesnej intensywności, powierzchni, zasięgu,
czasie i trwałości, wymaga około `262144` jednostek. To `512` razy koszt
zoptymalizowanej magii poziomu `10` o podobnym rezultacie.

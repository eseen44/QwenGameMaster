# Audyt logiki mechaniki v1

Status: zatwierdzony 2026-08-14 na podstawie decyzji użytkownika i udanego replayu kampanii.

## Wykryte i poprawione problemy

- Rozdzielono trafienie/dostarczenie od siły efektu i odporności celu. Sen, bezruch i pozycja wpływają teraz na dostarczenie, ale nie obniżają automatycznie odporności na jad lub magię.
- Efekty narastające otrzymały maksymalną magnitudę. Jad, który nie może osiągnąć progu śmiertelnego dużego celu, nie zostaje uznany za metodę zabicia niezależnie od rzutu.
- Twarde ograniczenia anatomii i geometrii mają pierwszeństwo przed wynikiem punktowym.
- Modyfikatory ratingów są ograniczane do zakresu 0–100; kumulacja nie tworzy wartości ujemnych ani ponadskalowych.
- Generator kontroluje wartości ciała, zdolności i efektów. Wąski gimmick nie omija limitu rangi przez przeniesienie przesadzonej liczby do osobnego pliku efektu.
- Intencje korzystają z wektora efektu, a nie ze sztywnego identyfikatora konkretnej zdolności. Ten sam system obsługuje wczesne i ulepszone ugryzienie.
- Brak zasobu blokuje użycie mechaniczne i nie może zostać naprawiony szczęśliwym rzutem.
- Zwycięstwo nad Varkhenem wymaga wielu różnych przewag; żadna pojedyncza wartość Lucana lub Borosa nie zbliża się do surowej obrony bytu.

## Wynik replayu

`campaign_lucan_replay_v1` zawiera 16 przypadków źródłowych: świeży i stary trup, wczesny Spidey, koń, zmutowany szczur, Rusk, szczuroogr, Komora III, zarządca zwłok, młody nieumarły strażnik, mur oraz kilka faz walki z Varkhenem.

Wynik po dodaniu trwałego runtime i brakujących zdolności Lucana: 24 zaliczone, 0 odrzuconych.

## Granica zatwierdzenia

Zatwierdzony jest model i algorytm. Liczby fixture są punktami kalibracyjnymi. Obiekty kampanii generowane na ich podstawie pozostają kandydatami migracyjnymi, dopóki replay i źródła nie ustalą ich docelowych wartości.

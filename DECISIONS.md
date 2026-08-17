# Dziennik decyzji technicznych

Ten plik jest przeznaczony dla następnej osoby albo agenta, który dotknie tego repo.
Zapisujemy tu **co zmieniliśmy i dlaczego**, a osobno **czego świadomie nie zrobiliśmy**.
Jeżeli kod przeczy temu plikowi — wygrywa kod, a wpis należy poprawić.

Nie jest to changelog wydania. Wpis powstaje wtedy, gdy decyzja jest nieoczywista
i bez uzasadnienia ktoś rozsądny cofnąłby ją przy następnym przeglądzie.

---

## 2026-08-17 — koszt tury i trwałość rzutu

Kontekst: kampania Lucana była wcześniej prowadzona ~900 tur w samym czacie.
Rozmowa zaczęła się dławić, a limit tokenów skończył się przed kampanią. To repo
powstało jako odpowiedź na tamten problem, ale samo w sobie go jeszcze nie
rozwiązywało.

### Diagnoza: koszt rozmowy rośnie z kwadratem liczby tur

W czacie **każda tura wysyła całą dotychczasową rozmowę od nowa**. Koszt tury *i*
to `prefiks + i × przyrost`, więc łączny koszt N tur to `N × prefiks + przyrost × N(N-1)/2`.
Zmierzone na żywym kodzie przed zmianami (fixture testowy):

| pozycja | rozmiar | ~tokeny |
|---|---:|---:|
| `turn resolve` → stdout | 3 178 B | 963 |
| `turn commit` → stdout | 8 580 B | 2 600 |
| razem na 1 turę (z request/outcome) | 12 509 B | 3 791 |
| stały prefiks sesji | 49 129 B | 14 888 |

Przy 50 turach w jednej sesji: ~0,75 mln tokenów prefiksu i **~5,4 mln narastającego ogona**.
Ogon to 88% rachunku. To ten sam mechanizm, który dławił kontekst i produkował
halucynacje — koszt i jakość mają tu wspólną przyczynę.

Rozbicie odpowiedzi `commit` pokazało, gdzie idą tokeny:

```
prepared_writes   3140 B  ~952 tok   pełne kopie dokumentów, które właśnie trafiły na dysk
preview           1362 B  ~413 tok   echo tego, co resolve już pokazał
request            333 B  ~101 tok   echo tego, co agent sam przed chwilą napisał
```

Ponad połowa odpowiedzi to dane, które agent ma już na dysku albo we własnej
poprzedniej wiadomości.

### Co zmieniliśmy

**1. Domyślnie skrócone wyjście CLI (`--verbose` przywraca pełne).**
`turn preview/resolve/commit/abort/recover` i `context refresh` drukują teraz
wyłącznie decyzje: werdykt, `roll_allowed`, sugerowaną trudność, koszty zasobów,
wynik rzutu, listę zmienionych ścieżek, należne reakcje świata i nowe pytanie
decyzyjne. `alternative_paths` i `hard_limit_details` pojawiają się tylko wtedy,
gdy silnik mówi „nie" — przy „tak" były kilkuset tokenową konfirmacją.

Efekt zmierzony: **12 509 B → 2 016 B na turę, 6,2x taniej.** Nic z tego, co zostało,
nie jest ozdobne — każde pole zmienia następny ruch narratora.
Pełny dokument transakcji nadal leży w `journal/transactions/<turn_id>.yaml`.

**2. Nowa komenda `gm brief` — otwarcie świeżej sesji jednym krokiem.**
Skoro stan żyje w plikach, rozmowa nie musi żyć wiecznie. `brief` składa jeden
blok: kampania, scena, czas, zegary, cele, uczestnicy ze stanem zasobów i
warunków, lista plików do wczytania z rozmiarami i budżetem. Na realnej kampanii
to **6,8 KB** zamiast czytania ośmiu plików po kolei.

`gm brief --full` dokłada treść wszystkich referencji (38 KB) — do wklejenia w
czacie przeglądarkowym, który nie ma dostępu do dysku.

**Dlaczego to jest ważniejsze niż punkt 1:** cięcie wyjścia zmniejsza *stałą*,
a zamykanie sesji likwiduje *człon kwadratowy*. Reset co scenę jest jedyną
zmianą, która sprawia, że koszt tury przestaje rosnąć.

**3. Rzut nie może się już rozjechać z dziennikiem.**
`resolve_turn` dopisywał rzut do `rolls.jsonl` przed zapisem transakcji. Awaria w
tym oknie powodowała, że ponowne `resolve` z tym samym `turn_id` losowało **nowy**
wynik, a `append_jsonl_once` cicho go nie zapisywał (id już istniało). Narrator
dostawał jeden wynik, dziennik trzymał inny — złamanie centralnej zasady z
`system/tests.md` („Raz ujawnionego wyniku nie wolno zmieniać").

Odtworzone eksperymentalnie przed poprawką: dziennik `natural_roll=71`,
transakcja `natural_roll=19`. Teraz zżurnalizowany rzut zawsze wygrywa
(`journal_record`), a regresja jest zabezpieczona testem
`test_retry_after_crash_reuses_the_journalled_roll`.

**4. Przekroczenie budżetu kontekstu nie wywala już commitu.**
`refresh_context` rzucał wyjątek przy >40 KB, a jest wołany **po** trwałym zapisie
tury. Efekt: tura zacommitowana, CLI zwraca błąd, `active.yaml` zostaje
nieaktualny **na zawsze** — bo ponowny `turn commit` widział `status: committed`
i wracał przed odświeżeniem.

Teraz przekroczenie budżetu i brakujące pliki są **raportowane, nie rzucane**:
`context_warnings`, `heaviest_refs` (pięć najcięższych referencji z rozmiarami).
Ponowny `commit` już committowanej tury naprawia nieaktualny kontekst.
`context refresh --strict` zachowuje twardy błąd dla walidacji w CI.

Powód takiego wyboru: cicha degradacja przez wyrzucanie referencji byłaby gorsza
niż ostrzeżenie — narrator straciłby stan i zaczął zmyślać, czyli dokładnie to,
przed czym ma chronić cały ten system.

**5. Naprawiony test sprzężony z żywymi danymi.**
`test_real_migration_uses_user_accepted_history_scope` asercjonował `ready is False`.
To było prawdą tylko dopóki pakiety migracyjne nie były zatwierdzone; po aktywacji
test zaczął padać na fakcie o kampanii, nie o kodzie. Teraz sprawdza to, po czym
jest nazwany: brak `blocker_full_chat_unavailable` i spójność `ready` z blokerami.

### Czego świadomie NIE zrobiliśmy

**Odchudzenia stałego prefiksu (49 KB).** Największe pozycje wskazuje teraz
`context refresh` w `heaviest_refs`: `player/inventory.yaml` **6 059 B** (dominują
`source_refs` i metadane archiwalne, których narrator w scenie nie używa),
`system/narrator.md` 3 127 B, `companions/spidey.yaml` 2 929 B dublujący częściowo
`state/instances/spidey.yaml`.

Kierunek: **aktywny kontekst trzyma stan bieżący, nigdy śladu audytowego.**
Generowany `inventory.brief.yaml` (noszone + srebro, ~800 B) do kontekstu, pełny
plik zostawić dla `recall`. Podobnie jedna karta operacyjna ~4 KB zamiast 20 KB
`system/*.md`, z długimi wersjami ładowanymi tylko przy spornej regule.

Nie zrobione, bo to zmienia **co widzi narrator**, a więc jakość gry — a nie mamy
jeszcze ani jednej rozegranej tury, żeby ocenić, czego naprawdę potrzebuje.

**Dwóch prędkości tury (`gm turn quick`).** Dziś otwarcie sakiewki kosztuje ten sam
rytuał co zabicie strażnika: request → resolve → outcome → commit. Tania ścieżka
dla tur czysto narracyjnych (jedno wywołanie, bez rzutu i bez osobnego outcome)
obcięłaby koszt najczęstszego przypadku.

Nie zrobione z tego samego powodu: granica między turą „tanią" a „pełną" to
decyzja projektowa, którą powinna rozstrzygnąć realna rozgrywka, nie zgadywanie.
**Ryzyko, jeśli tego nie zrobimy:** narrator ucieknie w `fiction_verdict: automatic`
przy każdej niewygodnej akcji i silnik możliwości zostanie ozdobą.

### Stan po zmianach

```
pytest tools/tests      42 passed
gm.py validate          OK (155 obiektów)
validate_project.py     OK (407 plików)
```

Szacunek dla 50 tur: **~6,1 mln → ~0,67 mln tokenów** (cięcie wyjścia + reset sesji
co ~10 tur + odchudzony prefiks, gdy ten ostatni powstanie).

### Rytuał sesji — jak z tego korzystać

1. `gm brief` (albo `gm brief --full` w czacie bez dysku) otwiera rozmowę.
2. Gramy. Wyjście CLI jest skrócone; `--verbose` tylko przy diagnozowaniu.
3. `gm scene close` na zamknięciu sceny.
4. **Nowa rozmowa**, znów `gm brief`. Stan jest w plikach, historia rozmowy nie jest
   do niczego potrzebna.

# Mechaniczna kalibracja kampanii Lucana

Ten katalog zawiera obiekty wygenerowane lub skalibrowane przez zatwierdzony rdzeń mechaniki v1. Nie są ładowane przez aktywny kontekst kampanii i nie stają się kanonem przed aktywacją migracji.

## Aktualne obiekty

- `candidate_companion_spidey` — warstwowy build Spideya oparty na ulepszeniach ze źródła.
- `candidate_webber_monitor` — faktycznie wygenerowany monitoringowy sieciarz z własną baterią i rzadką siecią alarmową.
- `candidate_pc_lucan_cutoff` — częściowy profil mechaniczny Lucana przy granicy kanonu.
- `candidate_varkhen_cutoff` — profil Varkhena bezpośrednio po wymuszonym przejęciu.

## Replay

`campaign_lucan_replay_v1` sprawdza 24 reprezentatywne przypadki mechaniczne na przestrzeni całej zachowanej kampanii, w tym wybór paraliżującego ładunku Spideya i nowe zdolności Lucana. Nie odtwarza każdego dialogu ani rzutu historycznego.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\gm.ps1 replay campaign_lucan_replay_v1
```

Każda zmiana rdzenia albo obiektów użytych w replayu musi zachować wynik `24/24` albo jawnie zrewidować oczekiwania i uzasadnić zmianę źródłowo.

"""Kontrakt pol instancji: co silnik CZYTA, a co jest tylko dokumentacja. Etap 10.

NAJGROZNIEJSZA KLASA BLEDU Z AUDYTU, bo klamie W STRONE BEZPIECZENSTWA. Dziesiec pol
w plikach stanu czyta sie jak mechanika i ma ZERO odczytow w tools/*.py: autor napisal
"ubytek wylaczony", odczytal to z pliku i uwierzyl. Zmierzone skutki: companion_spidey mial
flage `decay_suppressed` ORAZ regule decay bez zadnego `requires`, wiec silnik ubywal mu
rezerwy tak samo jak wszystkim; spy_wasp_01 stal na 0/3, spy_cellar_spider_01 na 0/3,
spy_hawk_moth_01 na 2/3 - przy kanonie nazywajacym go najszybciej rosnacym wezlem sieci.

ROZWIAZANIE NIE JEST REGULA, JEST KONTRAKTEM. `system/mechanics/instance-fields.yaml`
wymienia KAZDY klucz wystepujacy w plikach instancji i przypisuje mu status:
  engine_reads        - silnik to czyta; kontrola weryfikuje, ze pole faktycznie wystepuje
                        w kodzie, wiec status nie moze sklamac,
  documentation_only  - pole dla czlowieka, silnik go NIE czyta i nikt nie ma prawa
                        zalozyc, ze cokolwiek robi.
Pole, ktorego w kontrakcie nie ma, jest ZGLASZANE - wiec nie da sie juz dopisac do stanu
czegos, co udaje mechanike, i tego nie zauwazyc.

Kontrakt startuje ZIELONO: generowany z biezacego stanu, ze statusem wyprowadzonym
z faktycznych odczytow w kodzie. Zapadka dziala od tego momentu w przod.

Uruchomienie:  python tools/build_field_contract.py [--check]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
INSTANCES = ROOT / "campaigns" / "lucan" / "state" / "instances"
OUTPUT = ROOT / "system" / "mechanics" / "instance-fields.yaml"
CODE_FILES = ("tools/gm_runtime.py", "tools/gm_engine.py", "tools/validate_project.py")

# Klucze budowane dynamicznie w kodzie - literalnie nie wystepuja, ale silnik je czyta.
DYNAMIC_READS = {
    "regeneration_elapsed_seconds": "gm_runtime.process_instance_time f'{field}_elapsed_seconds'",
    "decay_elapsed_seconds": "gm_runtime.process_instance_time f'{field}_elapsed_seconds'",
    "hunting_recovery_elapsed_seconds": "gm_runtime.process_instance_time f'{field}_elapsed_seconds'",
    "necrotic_reservoir": "identyfikator puli - czytany z danych, nie z literalu",
    "lucan_necrotic_energy": "identyfikator puli - czytany z danych, nie z literalu",
    "paralytic_toxin_reservoir": "identyfikator puli - czytany z danych, nie z literalu",
    "ancient_necrotic_reservoir": "identyfikator puli - czytany z danych, nie z literalu",
}


def code_text() -> str:
    return "\n".join((ROOT / name).read_text(encoding="utf-8") for name in CODE_FILES)


def collect() -> tuple[dict[str, list[str]], set[str], set[str]]:
    """Zwraca ({sciezka_pola: [instancje]}, flagi z status_flags, flagi uzyte w requires).

    Trzeci zbior jest istotny: flaga wymieniona w `requires:` reguly strumienia FAKTYCZNIE
    wplywa na zachowanie silnika (process_instance_time pomija regule, gdy flagi nie ma),
    choc w kodzie nie wystepuje jako literal. Klasyfikowanie jej jako "dokumentacja" byloby
    klamstwem w druga strone niz to, ktore naprawiamy.
    """
    fields: dict[str, list[str]] = {}
    flags: set[str] = set()
    required: set[str] = set()

    def walk(node: object, prefix: str, instance_id: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if not isinstance(key, str):
                    continue
                path = f"{prefix}.{key}" if prefix else key
                fields.setdefault(path, [])
                if instance_id not in fields[path]:
                    fields[path].append(instance_id)
                walk(value, path, instance_id)
        elif isinstance(node, list):
            for item in node:
                walk(item, prefix, instance_id)

    for path in sorted(INSTANCES.glob("*.yaml")):
        if path.name == "index.yaml":
            continue
        document = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
        if not isinstance(document, dict):
            continue
        instance_id = document.get("id") or path.stem
        for flag in document.get("status_flags") or []:
            if isinstance(flag, str):
                flags.add(flag)
        for pool in (document.get("resources") or {}).values():
            if not isinstance(pool, dict):
                continue
            for stream in ("regeneration", "decay", "hunting_recovery"):
                rule = pool.get(stream)
                if isinstance(rule, dict):
                    for item in rule.get("requires") or []:
                        if isinstance(item, str):
                            required.add(item)
        walk(document, "", instance_id)
    return fields, flags, required


def leaf(path: str) -> str:
    return path.rsplit(".", 1)[-1]


def build() -> str:
    fields, flags, required = collect()
    code = code_text()

    entries = []
    for path, instances in sorted(fields.items()):
        name = leaf(path)
        literal = len(re.findall(r"[\"']" + re.escape(name) + r"[\"']", code))
        dynamic = DYNAMIC_READS.get(name)
        if literal:
            status, note = "engine_reads", f"{literal} odwolan literalnych w tools/"
        elif dynamic:
            status, note = "engine_reads", f"czytane dynamicznie: {dynamic}"
        else:
            status, note = "documentation_only", "silnik tego NIE czyta"
        entries.append({
            "field": path,
            "status": status,
            "note": note,
            "in_instances": len(instances),
        })

    czytane_literalnie = {f for f in flags
                          if re.search(r"[\"']" + re.escape(f) + r"[\"']", code)}
    flag_entries = []
    ostrzezenia: list[str] = []
    for flag in sorted(flags):
        if flag in czytane_literalnie:
            status, note = "engine_reads", "wystepuje w kodzie tools/"
        elif flag in required:
            status, note = ("engine_reads_via_requires",
                            "wymieniona w requires: reguly strumienia - silnik pomija regule, "
                            "gdy tej flagi nie ma, wiec flaga DZIALA (przez dane, nie przez kod)")
        else:
            status, note = ("documentation_only",
                            "silnik tej flagi NIE czyta - nie zakladaj, ze cokolwiek robi")
        # WARIANT FLAGI MECHANICZNEJ TO PULAPKA: "decay_suppressed_permanent_..." wyglada
        # jak flaga tlumiaca ubytek, a silnik sprawdza DOKLADNA nazwe, wiec wariant nie robi
        # nic. To ta sama awaria, ktora naprawia etap 10, tylko o jeden znak dalej.
        # Konwencja wyjscia z pulapki: sufiks _DOKUMENTACJA_NIE_MECHANIKA mowi wprost,
        # ze to nota, nie przelacznik - i wtedy podobienstwo nazwy nie jest problemem.
        JAWNIE_OPISOWA = '_DOKUMENTACJA_NIE_MECHANIKA'
        for mechaniczna in sorted(czytane_literalnie):
            if (flag != mechaniczna and flag.startswith(mechaniczna)
                    and JAWNIE_OPISOWA not in flag):
                status = "LOOKS_MECHANICAL_BUT_IS_NOT"
                note = (f"WARIANT flagi mechanicznej '{mechaniczna}' - silnik sprawdza "
                        f"DOKLADNA nazwe, wiec ta flaga NIE DZIALA. Albo uzyj dokladnej "
                        f"nazwy, albo przenies te tresc do note.")
                ostrzezenia.append(f"{flag} (wariant {mechaniczna})")
        flag_entries.append({"flag": flag, "status": status, "note": note})

    document = {
        "schema_version": 1,
        "id": "contract_instance_fields",
        "object_type": "field_contract",
        "generated_by": "tools/build_field_contract.py",
        "purpose": (
            "Kazdy klucz i kazda flaga wystepujaca w state/instances/*.yaml ma tu status: "
            "engine_reads albo documentation_only. Pole poza kontraktem jest ZGLASZANE, wiec "
            "nie da sie dopisac do stanu czegos, co udaje mechanike, i tego nie zauwazyc. "
            "To odpowiedz na najgrozniejsza klase bledu z audytu 2026-09-04: dziesiec pol "
            "czytalo sie jak mechanika i mialo zero odczytow w kodzie, a flaga "
            "decay_suppressed byla dekoracja przy jednoczesnej regule decay bez requires."
        ),
        "how_to_change": (
            "Nowe pole mechaniczne: najpierw napisz odczyt w tools/, potem przebuduj kontrakt. "
            "Nowe pole opisowe: przebuduj kontrakt i sprawdz, ze dostalo documentation_only - "
            "jesli spodziewasz sie engine_reads, a wychodzi documentation_only, to znaczy, ze "
            "silnik tego nie czyta i pole nie dziala."
        ),
        "warnings_looks_mechanical_but_is_not": ostrzezenia,
        "counts": {
            "fields": len(entries),
            "engine_reads": sum(1 for e in entries if e["status"] == "engine_reads"),
            "documentation_only": sum(1 for e in entries if e["status"] == "documentation_only"),
            "flags": len(flag_entries),
            "flags_engine_reads": sum(1 for f in flag_entries if f["status"].startswith("engine_reads")),
            "flags_looks_mechanical_but_is_not": len(ostrzezenia),
        },
        "fields": entries,
        "status_flags": flag_entries,
    }
    return yaml.safe_dump(document, allow_unicode=True, sort_keys=False, width=100)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    content = build()
    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if current != content:
            print("[BLAD] system/mechanics/instance-fields.yaml nieaktualny "
                  "- w stanie pojawilo sie pole poza kontraktem albo zmienil sie kod. "
                  "Uruchom: python tools/build_field_contract.py i PRZECZYTAJ diff.")
            return 1
        print("[OK] kontrakt pol instancji aktualny")
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(content, encoding="utf-8", newline="\n")
    document = yaml.safe_load(content)
    counts = document["counts"]
    print(f"zapisane: {OUTPUT.relative_to(ROOT).as_posix()}")
    print(f"pol: {counts['fields']} (silnik czyta {counts['engine_reads']}, "
          f"dokumentacja {counts['documentation_only']})")
    print(f"flag: {counts['flags']} (silnik czyta {counts['flags_engine_reads']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

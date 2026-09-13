#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "data.json").read_text(encoding="utf-8"))

WORD = {
    "+": "есть",
    "-": "нет",
    ">": "едет",
    "~": "частично",
    "!": "есть, взять обязательно",
    "x": "не требуется",
    "?": "не сказано",
}

NEED = {
    "optional": "по желанию",
    "sniper": "для снайпера",
    "mg": "для пулемётчика",
    "medic": "для медика",
    "gl": "для гранатомётчика",
    "mg_sapper": "для пулемётчика / сапёра",
    "sapper": "для сапёра",
    "sniper_marksman": "для снайпера / марксмана",
    "sapper_sniper": "для сапёра / снайпера",
}


def core_items():
    items = []
    for cat in DATA["categories"]:
        for index, item in enumerate(cat["items"], start=1):
            items.append({**item, "cat": cat["title"], "num": index})
    return items


def counts(person, items):
    values = [person["core"][item["id"]] for item in items]
    have = sum(v in {"+", "!"} for v in values)
    wait = sum(v == ">" for v in values)
    part = sum(v == "~" for v in values)
    miss = sum(v == "-" for v in values)
    total = have + wait + part + miss
    now = round(have / total * 100) if total else 0
    return have, wait, part, miss, total, now


def line(num: int, name: str, code: str, suffix: str = "") -> str:
    extra = f" {suffix}" if suffix else ""
    return f"{num}. {name} — {WORD[code]}{extra}"


def render() -> str:
    items = core_items()
    out: list[str] = []
    out.append("2-е ЗВЕНО")
    out.append("Комплектация одежды, экипировки и снаряжения")
    out.append(f"Сводка на {DATA['meta']['date']}")
    out.append("")
    out.append(DATA["meta"]["inspection"])
    out.append("")
    out.append("Как читать:")
    out.append("есть — предмет на руках")
    out.append("едет — в пути")
    out.append("частично — есть, но не соответствует требованию")
    out.append("есть, взять обязательно — в исходном списке стояло «!»")
    out.append("нет — отсутствует")
    out.append("не требуется — не по специальности")
    out.append("не сказано — человек это не отмечал")
    out.append("")
    out.append("Если человек прислал только то, чего нет, все остальные позиции обязательного списка отмечены как «есть».")
    out.append("")
    out.append("════════════════════════════════════════")
    out.append("СВОДКА ПО ЗВЕНУ")
    out.append("════════════════════════════════════════")
    out.append("")

    for person in DATA["people"]:
        have, wait, part, miss, total, now = counts(person, items)
        tail = []
        if wait:
            tail.append(f"едет {wait}")
        if part:
            tail.append(f"частично {part}")
        extra = f", {', '.join(tail)}" if tail else ""
        out.append(f"{person['name']} ({person['role']}) — есть {have}/{total} ({now}%), нет {miss}{extra}")

    out.append("")
    out.append("Где проседает всё звено (нет минимум у 4 человек):")
    out.append("")
    gaps = []
    for item in items:
        missing = [p["name"] for p in DATA["people"] if p["core"][item["id"]] == "-"]
        waiting = [p["name"] for p in DATA["people"] if p["core"][item["id"]] == ">"]
        if len(missing) >= 4:
            gaps.append((len(missing), item, missing, waiting))
    gaps.sort(key=lambda row: (-row[0], row[1]["cat"], row[1]["name"]))
    for n, item, missing, waiting in gaps:
        wait_txt = f"; едет: {', '.join(waiting)}" if waiting else ""
        out.append(f"— {item['cat']} / {item['name']}: нет у {n} ({', '.join(missing)}){wait_txt}")

    for person in DATA["people"]:
        have, wait, part, miss, total, now = counts(person, items)
        out.append("")
        out.append("════════════════════════════════════════")
        out.append(f"{person['name'].upper()} · {person['role']}")
        out.append(f"есть {have}/{total} · едет {wait} · частично {part} · нет {miss} · готовность {now}%")
        out.append(f"источник: {person['source']}")
        out.append("════════════════════════════════════════")

        for cat in DATA["categories"]:
            out.append("")
            out.append(cat["title"])
            for index, item in enumerate(cat["items"], start=1):
                out.append(line(index, item["name"], person["core"][item["id"]]))

        shown = [
            (index, item, person["individual"][item["id"]])
            for index, item in enumerate(DATA["individual"], start=1)
            if person["individual"][item["id"]] != "x"
        ]
        out.append("")
        out.append("Индивидуальная экипировка")
        if shown:
            for index, item, code in shown:
                out.append(line(index, item["name"], code, f"({NEED[item['need']]})"))
        else:
            out.append("по специальности и «по желанию» отдельно не расписывал")

        if person["extra"]:
            out.append("")
            out.append("Прочее (в обязательный список не входит, но проверяется)")
            for index, row in enumerate(person["extra"], start=1):
                detail = f" — {row['detail']}" if row.get("detail") else ""
                out.append(line(index, row["item"] + detail, row["status"]))

        def named(item):
            return f"{item['cat']} / {item['name']}"

        miss_items = [item for item in items if person["core"][item["id"]] == "-"]
        wait_items = [item for item in items if person["core"][item["id"]] == ">"]
        part_items = [item for item in items if person["core"][item["id"]] == "~"]
        flag_items = [item for item in items if person["core"][item["id"]] == "!"]

        out.append("")
        out.append("Коротко по обязательным позициям")
        out.append(f"Не хватает: {'; '.join(named(item) for item in miss_items) if miss_items else 'ничего'}")
        if wait_items:
            out.append(f"Едет: {'; '.join(named(item) for item in wait_items)}")
        if part_items:
            out.append(f"Частично: {'; '.join(named(item) for item in part_items)}")
        if flag_items:
            out.append(f"Взять обязательно: {'; '.join(named(item) for item in flag_items)}")

        if person["notes"]:
            out.append("")
            out.append("Пояснения")
            for note in person["notes"]:
                out.append(f"— {note}")

    extra_map: dict[str, list[str]] = {}
    for person in DATA["people"]:
        for row in person["extra"]:
            if row["status"] == "-":
                extra_map.setdefault(row["item"], []).append(person["name"])

    out.append("")
    out.append("════════════════════════════════════════")
    out.append("ПРОЧЕЕ, ЧТО ТОЖЕ ПРОВЕРЯЮТ")
    out.append("════════════════════════════════════════")
    out.append("")
    out.append("Привод, магазины, лоадер, шомпол, зарядное, шары и аккумулятор в базовый список не входят.")
    out.append("")
    if extra_map:
        for item, names in extra_map.items():
            out.append(f"— {item}: нет у {', '.join(names)}")
    else:
        out.append("Отдельных дыр вне списка не отмечено.")

    out.append("")
    out.append("════════════════════════════════════════")
    out.append("КАК СОБИРАЛСЯ ОТЧЁТ")
    out.append("════════════════════════════════════════")
    out.append("")
    for rule in DATA["meta"]["rules"]:
        out.append(f"— {rule}")
    out.append("")
    out.append("Роли, которые не были названы прямо, выведены только из специальной экипировки:")
    out.append("Горизонт и Овод — сапёры, Велес — гранатомётчик, Арчи — марксман по коврику для стрельбы.")
    out.append("")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    text = render()
    path = ROOT / "SVODKA.txt"
    path.write_text(text, encoding="utf-8")
    print(f"Wrote {path} ({len(text.splitlines())} lines)")

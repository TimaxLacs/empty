#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "data.json").read_text(encoding="utf-8"))

STATUS_LINES = (
    ("+", "есть"),
    ("!", "есть, взять обязательно"),
    (">", "едет"),
    ("~", "частично"),
    ("-", "нет"),
    ("?", "не сказано"),
    ("x", "не требуется"),
)

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


def names_for(item_id: str, code: str) -> list[str]:
    return [person["name"] for person in DATA["people"] if person["core"][item_id] == code]


def names_for_individual(item_id: str, code: str) -> list[str]:
    return [person["name"] for person in DATA["people"] if person["individual"][item_id] == code]


def visible_groups(groups: list[tuple[str, list[str]]]) -> list[tuple[str, list[str]]]:
    return [(label, names) for label, names in groups if names and label != "не требуется"]


def item_block(out: list[str], title: str, groups: list[tuple[str, list[str]]]) -> None:
    out.append(title)
    shown = visible_groups(groups)
    if shown:
        for label, names in shown:
            out.append(f"{label}: {', '.join(names)}")
    else:
        out.append("ни у кого не отмечен")
    out.append("")


def core_groups(item_id: str) -> list[tuple[str, list[str]]]:
    return [(label, names_for(item_id, code)) for code, label in STATUS_LINES]


def individual_groups(item_id: str) -> list[tuple[str, list[str]]]:
    return [(label, names_for_individual(item_id, code)) for code, label in STATUS_LINES]


def extra_groups() -> list[tuple[str, list[tuple[str, list[str]]]]]:
    buckets: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for person in DATA["people"]:
        for row in person["extra"]:
            name = row["item"]
            if row.get("detail"):
                name = f"{row['item']} ({row['detail']})"
            buckets[name][row["status"]].append(person["name"])
    blocks = []
    for item_name in buckets:
        groups = [(label, buckets[item_name].get(code, [])) for code, label in STATUS_LINES]
        blocks.append((item_name, groups))
    return blocks


def render() -> str:
    out: list[str] = []
    out.append("Комплектация одежды, экипировки и снаряжения")
    out.append("")
    out.append("По каждому предмету — у кого есть, у кого нет, у кого едет.")
    out.append("Привод, магазины, лоадер, шомпол, зарядное, шары и аккумулятор в обязательный список не входят, но в конце тоже расписаны.")
    out.append("")
    out.append("Если человек прислал только то, чего нет, остальные обязательные позиции отмечены как «есть».")
    out.append("")

    for cat in DATA["categories"]:
        out.append("════════════════════════════════════════")
        out.append(cat["title"].upper())
        out.append("════════════════════════════════════════")
        out.append("")
        for index, item in enumerate(cat["items"], start=1):
            item_block(out, f"{index}. {item['name']}", core_groups(item["id"]))

    out.append("════════════════════════════════════════")
    out.append("ИНДИВИДУАЛЬНАЯ ЭКИПИРОВКА")
    out.append("════════════════════════════════════════")
    out.append("")
    for index, item in enumerate(DATA["individual"], start=1):
        item_block(
            out,
            f"{index}. {item['name']} ({NEED[item['need']]})",
            individual_groups(item["id"]),
        )

    extra = extra_groups()
    out.append("════════════════════════════════════════")
    out.append("ПРОЧЕЕ, ЧТО ТОЖЕ ПРОВЕРЯЮТ")
    out.append("════════════════════════════════════════")
    out.append("")
    for item_name, groups in extra:
        item_block(out, item_name, groups)

    out.append("════════════════════════════════════════")
    out.append("ЕДЕТ И ЧАСТИЧНО")
    out.append("════════════════════════════════════════")
    out.append("")
    incoming = []
    partial = []
    flag = []
    for cat in DATA["categories"]:
        for item in cat["items"]:
            for person in DATA["people"]:
                code = person["core"][item["id"]]
                label = f"{item['name']} — {person['name']}"
                if cat["id"] == "winter":
                    label = f"{item['name']} (зима) — {person['name']}"
                if code == ">":
                    incoming.append(label)
                elif code == "~":
                    partial.append(label)
                elif code == "!":
                    flag.append(label)
    if incoming:
        out.append("Едет")
        for row in incoming:
            out.append(f"— {row}")
        out.append("")
    if partial:
        out.append("Частично")
        for row in partial:
            out.append(f"— {row}")
        out.append("")
    if flag:
        out.append("Есть, взять обязательно")
        for row in flag:
            out.append(f"— {row}")
        out.append("")

    out.append("════════════════════════════════════════")
    out.append("ПОЯСНЕНИЯ ПО СПОРНЫМ МЕСТАМ")
    out.append("════════════════════════════════════════")
    out.append("")
    out.append("Геккон: очки защитные и варбелт стоят и в «есть», и в «нет». Засчитаны как есть — по списку наличия.")
    out.append("Шуга: было два сообщения. Взят второй полный чек-лист. Куртка демисезонная с «!» — есть, взять обязательно. JPC с «+−» — частично.")
    out.append("Арчи: чехол на очки есть. Зимы нет, кроме чехла на шлем.")
    out.append("Шершень и Велес: «зимы нет» отнесено к зимнему комплекту. Куртка зимняя в одежде отдельно не названа — засчитана как есть.")
    out.append("Велес: шлем нет, маячок на шлем в отсутствии не назван — засчитан как есть. Лучше перепроверить.")
    out.append("Овод: рюкзак для перевозки есть.")
    out.append("Матрос: чехол мультикам есть, маскировочного чехла на шлем нет.")
    out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    text = render()
    path = ROOT / "SVODKA.txt"
    path.write_text(text, encoding="utf-8")
    print(f"Wrote {path} ({len(text.splitlines())} lines)")

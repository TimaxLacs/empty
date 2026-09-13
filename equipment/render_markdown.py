#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "data.json").read_text(encoding="utf-8"))

STATUS = {
    "+": "есть",
    "-": "нет",
    ">": "едет",
    "~": "частично",
    "!": "есть, взять",
    "x": "не требуется",
    "?": "не сказано",
}

NEED = {
    "optional": "по желанию",
    "sniper": "снайпер",
    "mg": "пулемётчик",
    "medic": "медик",
    "gl": "гранатомётчик",
    "mg_sapper": "пулемётчик / сапёр",
    "sapper": "сапёр",
    "sniper_marksman": "снайпер / марксман",
    "sapper_sniper": "сапёр / снайпер",
}


def core_items():
    items = []
    for cat in DATA["categories"]:
        for item in cat["items"]:
            items.append({**item, "cat": cat["title"]})
    return items


def counts(person, items):
    values = [person["core"][item["id"]] for item in items]
    have = sum(v in {"+", "!"} for v in values)
    wait = sum(v == ">" for v in values)
    part = sum(v == "~" for v in values)
    miss = sum(v == "-" for v in values)
    total = have + wait + part + miss
    now = round(have / total * 100) if total else 0
    sunday = round((have + wait) / total * 100) if total else 0
    return have, wait, part, miss, total, now, sunday


def md_status(code: str) -> str:
    return {"+": "✅ есть", "-": "❌ нет", ">": "🚚 едет", "~": "⚠️ частично", "!": "⭐ есть, взять", "x": "— не требуется", "?": "❔ не сказано"}[code]


def render() -> str:
    items = core_items()
    lines = [
        "# 2-е звено — комплектация снаряжения",
        "",
        f"Актуально на **{DATA['meta']['date']}**.",
        "",
        DATA["meta"]["inspection"],
        "",
        "Интерактивная версия с матрицей и фильтрами: [equipment/index.html](index.html).",
        "",
        "## Как читать статусы",
        "",
        "| Знак | Статус | Смысл |",
        "| --- | --- | --- |",
        "| ✅ | есть | Предмет на руках |",
        "| 🚚 | едет | В пути, к воскресенью может появиться |",
        "| ⚠️ | частично | Есть, но не то (камуфляж, модель, неполный комплект) |",
        "| ⭐ | есть, взять | Есть, в исходном списке стояло «!» |",
        "| ❌ | нет | Явно отсутствует |",
        "| — | не требуется | Не по специальности |",
        "| ❔ | не сказано | Человек это не отмечал |",
        "",
        "Если человек прислал **только то, чего нет**, все остальные позиции обязательного списка отмечены как «есть».",
        "",
        "## Сводка по звену",
        "",
        "| Позывной | Специальность | Есть | Едет | Частично | Нет | Сейчас | Если приедет всё | Источник |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]

    for person in DATA["people"]:
        have, wait, part, miss, total, now, sunday = counts(person, items)
        lines.append(
            f"| [{person['name']}](#{person['id']}) | {person['role']} | {have}/{total} | {wait} | {part} | {miss} | {now}% | {sunday}% | {person['source']} |"
        )

    lines += [
        "",
        "## Где проседает всё звено",
        "",
        "Позиции, которых нет минимум у четырёх человек.",
        "",
        "| Позиция | Раздел | Нет у | Едет у |",
        "| --- | --- | --- | --- |",
    ]

    gaps = []
    for item in items:
        missing = [p["name"] for p in DATA["people"] if p["core"][item["id"]] == "-"]
        waiting = [p["name"] for p in DATA["people"] if p["core"][item["id"]] == ">"]
        if len(missing) >= 4:
            gaps.append((len(missing), item, missing, waiting))
    gaps.sort(key=lambda row: (-row[0], row[1]["cat"], row[1]["name"]))
    for n, item, missing, waiting in gaps:
        lines.append(f"| {item['name']} | {item['cat']} | {n}: {', '.join(missing)} | {', '.join(waiting) or '—'} |")

    lines += ["", "## Матрица обязательного списка", ""]
    header = "| Позиция | " + " | ".join(p["name"] for p in DATA["people"]) + " |"
    sep = "| --- | " + " | ".join("---:" for _ in DATA["people"]) + " |"
    lines.append(header)
    lines.append(sep)
    current_cat = None
    for item in items:
        if item["cat"] != current_cat:
            current_cat = item["cat"]
            lines.append(f"| **{current_cat}** | " + " | ".join("" for _ in DATA["people"]) + " |")
        cells = " | ".join(md_status(p["core"][item["id"]]).split()[0] for p in DATA["people"])
        lines.append(f"| {item['name']} | {cells} |")

    lines += ["", "## Карточки по людям", ""]
    for person in DATA["people"]:
        have, wait, part, miss, total, now, sunday = counts(person, items)
        lines += [
            f"### {person['name']}",
            "",
            f"<a id=\"{person['id']}\"></a>",
            "",
            f"**Специальность:** {person['role']}  ",
            f"**Готовность:** {have}/{total} есть · {wait} едет · {part} частично · {miss} нет · сейчас {now}%  ",
            f"**Источник:** {person['source']}",
            "",
        ]
        for cat in DATA["categories"]:
            lines.append(f"#### {cat['title']}")
            lines.append("")
            for item in cat["items"]:
                lines.append(f"- {md_status(person['core'][item['id']])} — {item['name']}")
            lines.append("")
        lines.append("#### Индивидуальная экипировка")
        lines.append("")
        shown = False
        for item in DATA["individual"]:
            code = person["individual"][item["id"]]
            if code == "x":
                continue
            shown = True
            lines.append(f"- {md_status(code)} — {item['name']} ({NEED[item['need']]})")
        if not shown:
            lines.append("- Отдельно не расписывал.")
        lines.append("")
        if person["extra"]:
            lines.append("#### Прочее, вне базового списка")
            lines.append("")
            for row in person["extra"]:
                detail = f" — {row['detail']}" if row.get("detail") else ""
                lines.append(f"- {md_status(row['status'])} — {row['item']}{detail}")
            lines.append("")
        if person["notes"]:
            lines.append("#### Пояснения")
            lines.append("")
            for note in person["notes"]:
                lines.append(f"- {note}")
            lines.append("")

    extra_map: dict[str, list[str]] = {}
    for person in DATA["people"]:
        for row in person["extra"]:
            if row["status"] == "-":
                extra_map.setdefault(row["item"], []).append(person["name"])

    lines += [
        "## Что докупить: прочее",
        "",
        "Привод, магазины, лоадер, шомпол, зарядное, шары и аккумулятор в обязательный перечень не входят, но проверяются.",
        "",
    ]
    if extra_map:
        lines += ["| Позиция | Нет у |", "| --- | --- |"]
        for item, names in extra_map.items():
            lines.append(f"| {item} | {', '.join(names)} |")
        lines.append("")

    lines += [
        "## Правила сборки отчёта",
        "",
    ]
    for rule in DATA["meta"]["rules"]:
        lines.append(f"- {rule}")
    lines += [
        "",
        "Роли, которые не были названы прямо, выведены только из явно перечисленной специальной экипировки: Горизонт и Овод — сапёры, Велес — гранатомётчик, Арчи — марксман по коврику для стрельбы.",
        "",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    text = render()
    out = ROOT / "REPORT.md"
    out.write_text(text, encoding="utf-8")
    print(f"Wrote {out} ({len(text.splitlines())} lines)")

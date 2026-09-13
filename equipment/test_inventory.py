#!/usr/bin/env python3
from __future__ import annotations

import json
import unittest
from pathlib import Path

DATA = json.loads(Path(__file__).resolve().parent.joinpath("data.json").read_text(encoding="utf-8"))
PEOPLE = {person["name"]: person for person in DATA["people"]}
CORE_IDS = [item["id"] for cat in DATA["categories"] for item in cat["items"]]
INDIV_IDS = [item["id"] for item in DATA["individual"]]


class InventoryContractTests(unittest.TestCase):
    def test_master_list_counts(self):
        counts = {cat["id"]: len(cat["items"]) for cat in DATA["categories"]}
        self.assertEqual(counts, {"clothes": 11, "winter": 8, "basic": 23, "gear": 9})
        self.assertEqual(len(INDIV_IDS), 18)
        self.assertEqual(len(DATA["people"]), 9)

    def test_every_person_has_complete_status(self):
        for person in DATA["people"]:
            self.assertCountEqual(person["core"].keys(), CORE_IDS, person["name"])
            self.assertCountEqual(person["individual"].keys(), INDIV_IDS, person["name"])

    def test_horizon_sapper_checklist(self):
        person = PEOPLE["Горизонт"]
        self.assertEqual(person["role"], "Сапёр")
        self.assertEqual(person["core"]["c01"], "-")
        self.assertEqual(person["core"]["c02"], "+")
        self.assertEqual(person["core"]["c09"], "-")
        self.assertEqual(person["core"]["w04"], "+")
        self.assertEqual(person["core"]["g06"], "-")
        self.assertEqual(person["core"]["g08"], "-")
        self.assertEqual(person["core"]["g09"], "-")
        self.assertEqual(person["individual"]["i15"], "+")
        self.assertEqual(person["individual"]["i16"], "+")

    def test_gekkon_incoming_and_conflicts_resolved(self):
        person = PEOPLE["Геккон"]
        self.assertEqual(person["core"]["c01"], ">")
        self.assertEqual(person["core"]["c03"], ">")
        self.assertEqual(person["core"]["b03"], ">")
        self.assertEqual(person["core"]["b06"], "+")
        self.assertEqual(person["core"]["b15"], "+")
        self.assertEqual(person["core"]["c11"], "-")
        self.assertEqual(person["core"]["b18"], "-")

    def test_shuga_second_checklist_wins(self):
        person = PEOPLE["Шуга"]
        self.assertEqual(person["core"]["c01"], "-")
        self.assertEqual(person["core"]["c02"], "+")
        self.assertEqual(person["core"]["c03"], "!")
        self.assertEqual(person["core"]["c10"], ">")
        self.assertEqual(person["core"]["b07"], "~")
        self.assertEqual(person["core"]["b11"], ">")
        self.assertEqual(person["core"]["b13"], ">")
        self.assertEqual(person["core"]["g08"], ">")

    def test_ryzhiy_explicit_have_and_coming(self):
        person = PEOPLE["Рыжий"]
        self.assertEqual(person["core"]["c02"], "+")
        self.assertEqual(person["core"]["c06"], "+")
        self.assertEqual(person["core"]["c11"], "+")
        self.assertEqual(person["core"]["b01"], "+")
        self.assertEqual(person["core"]["b04"], "+")
        self.assertEqual(person["core"]["b07"], "+")
        self.assertEqual(person["core"]["g04"], "+")
        self.assertEqual(person["core"]["g06"], "+")
        self.assertEqual(person["core"]["c03"], ">")
        self.assertEqual(person["core"]["b21"], ">")
        extras = {row["item"]: row["status"] for row in person["extra"]}
        self.assertEqual(extras["Привод"], "-")

    def test_missing_only_people(self):
        archi = PEOPLE["Арчи"]
        self.assertEqual(archi["core"]["c03"], "-")
        self.assertEqual(archi["core"]["c10"], "-")
        self.assertEqual(archi["core"]["w06"], "+")
        self.assertEqual(archi["core"]["b03"], "-")
        self.assertEqual(archi["core"]["b05"], "~")
        self.assertEqual(archi["core"]["g08"], "-")
        self.assertEqual(archi["individual"]["i17"], "-")

        shershen = PEOPLE["Шершень"]
        self.assertEqual(shershen["core"]["c02"], "-")
        self.assertEqual(shershen["core"]["g04"], "-")
        self.assertEqual(shershen["core"]["b20"], "-")
        self.assertEqual(shershen["individual"]["i18"], "-")

        veles = PEOPLE["Велес"]
        self.assertEqual(veles["role"], "Гранатомётчик")
        self.assertEqual(veles["core"]["c05"], "+")
        self.assertEqual(veles["core"]["b08"], "-")
        self.assertEqual(veles["core"]["b09"], "-")
        self.assertEqual(veles["core"]["b01"], "-")
        self.assertEqual(veles["core"]["g04"], "-")
        self.assertEqual(veles["individual"]["i08"], "-")

        matros = PEOPLE["Матрос"]
        self.assertEqual(matros["core"]["b19"], "-")
        self.assertEqual(matros["core"]["b22"], "-")
        self.assertEqual(matros["core"]["b23"], "-")
        self.assertEqual(matros["core"]["b02"], "+")
        self.assertEqual(matros["core"]["g05"], "-")

        ovod = PEOPLE["Овод"]
        self.assertEqual(ovod["role"], "Сапёр")
        self.assertEqual(ovod["core"]["b09"], "-")
        self.assertEqual(ovod["core"]["g01"], "-")
        self.assertEqual(ovod["core"]["g03"], "-")
        extras = {row["item"]: row["status"] for row in ovod["extra"]}
        self.assertEqual(extras["Привод"], "-")
        self.assertEqual(extras["Чехол на лопату"], "-")

    def test_hydrator_missing_for_everyone(self):
        for person in DATA["people"]:
            self.assertEqual(person["core"]["g09"], "-", person["name"])

    def names(self, item_id: str, code: str) -> list[str]:
        return [person["name"] for person in DATA["people"] if person["core"][item_id] == code]

    def test_item_groups_after_recheck(self):
        self.assertEqual(self.names("b20", "+"), ["Горизонт", "Арчи", "Матрос", "Овод"])
        self.assertEqual(self.names("b20", "-"), ["Геккон", "Шуга", "Рыжий", "Шершень", "Велес"])
        self.assertEqual(self.names("c02", "-"), ["Шершень"])
        self.assertEqual(self.names("c10", ">"), ["Шуга"])
        self.assertEqual(self.names("c10", "+"), [])
        self.assertEqual(self.names("c01", ">"), ["Геккон"])
        self.assertEqual(self.names("c01", "+"), ["Арчи", "Овод"])
        self.assertEqual(self.names("g04", "-"), ["Шершень", "Велес"])
        self.assertEqual(self.names("b07", "~"), ["Шуга"])
        self.assertEqual(self.names("b05", "~"), ["Арчи"])
        self.assertEqual(self.names("c03", "!"), ["Шуга"])
        self.assertEqual(self.names("c03", ">"), ["Геккон", "Рыжий"])


if __name__ == "__main__":
    unittest.main()

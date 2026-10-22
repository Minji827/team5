"""Offline integration checks, including future curated inputs. No API calls."""
import argparse
import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import build_places as build


class PlaceIntegrationTests(unittest.TestCase):
    def test_subtype_conflict_and_defaults(self):
        self.assertEqual(build.merchant_type({"travel_category": "식사|간식·먹거리"})[0], "quick_meal")
        self.assertEqual(build.merchant_type({"travel_category": "커피·디저트"})[0], "seated_cafe")
        self.assertEqual(build.merchant_type({"travel_category": "간식·먹거리"}, "빵/도넛")[0], "takeaway_dessert")
        self.assertEqual(build.merchant_type({"travel_category": "간식·먹거리"}, "빵/도넛 / 닭강정"), (None, "snack_subtype_conflict"))
        self.assertEqual(build.merchant_type({"travel_category": "간식·먹거리"})[0], None)

    def test_null_and_rules(self):
        rules = build.rules_from(RULES)
        self.assertEqual(len(rules), 9)
        row = dict(id="example", name="fixture", address="fixture", lon="129", lat="35.1")
        place = build.make_place(row, "general_restaurant", "남포동", rules)
        self.assertEqual(place["duration_min"], 60)
        self.assertEqual(place["estimated_spend"], "")
        self.assertEqual(place["rating"], "")
        self.assertEqual(build.make_place(row, "traditional_market", "남포동", rules)["payment_status"], "not_verified")
        with self.assertRaises(ValueError):
            build.make_place(dict(row, estimated_spend="-1"), "general_restaurant", "남포동", rules)

    def test_curated_inputs_and_mvp_partition(self):
        merchants = build.read_csv(DATA / "GIS/mvp/mvp_merchants.csv")
        classified = [r for r in merchants if r["purpose_status"] == "classified"]
        shops = [r for r in classified if r["travel_category"] == "소품·기념품 쇼핑"][:10]
        self.assertEqual(len(shops), 10)
        with tempfile.TemporaryDirectory(dir=str(Path(__file__).resolve().parent)) as temporary:
            folder = Path(temporary)
            build.write_csv(folder / "shops.csv", [dict(id=r["id"], visit_type="souvenir_shop") for r in shops], ["id", "visit_type"])
            point = classified[0]
            pois = [dict(id="fixture_market", name="TEST ONLY", address="TEST ONLY", lon=point["lon"], lat=point["lat"], visit_type="traditional_market"),
                    dict(id="fixture_outside", name="TEST ONLY", address="TEST ONLY", lon="127", lat="37", visit_type="scenic_spot")]
            build.write_csv(folder / "tourism.csv", pois, list(pois[0]))
            args = argparse.Namespace(data_dir=DATA, rules_file=RULES, output_dir=folder / "fin", shopping_file=folder / "shops.csv", tourism_file=folder / "tourism.csv")
            build.build(args)
            ready = build.read_csv(args.output_dir / "places.csv")
            review = build.read_csv(args.output_dir.parent / "place_support/places_review.csv")
            self.assertEqual({p.name for p in args.output_dir.iterdir()}, {"places.csv"})
            self.assertEqual(sum(r["category"] == "쇼핑" for r in ready), 10)
            self.assertEqual(sum(r["category"] == "관광명소" for r in ready), 1)
            self.assertTrue(all(r["admin_dong"] in build.DONGS for r in ready))
            self.assertTrue(all(r["estimated_spend"] == "" for r in ready))
            self.assertFalse(set(r["id"] for r in ready) & set(r["id"] for r in review))
            self.assertIn("outside_mvp", {r["reason"] for r in review})
            self.assertNotIn("spot:fixture_outside", {r["id"] for r in ready})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--rules-file", type=Path, required=True)
    args = parser.parse_args()
    DATA, RULES = args.data_dir, args.rules_file
    import os
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    unittest.main(argv=["test_build_places.py"])

import unittest
from pathlib import Path

from ledger.candidates import confirm_high_confidence
from ledger.checks import run_checks
from ledger.load import inspect_bytes
from ledger.rules import effective_rules

ROOT = Path(__file__).resolve().parents[1] / "public" / "samples"
RULES = effective_rules("process", {})


def load(name):
    data = (ROOT / name).read_bytes()
    return inspect_bytes(name, data)


def ids(model):
    return [finding["ruleId"] for finding in run_checks(model, RULES)]


class InspectorTests(unittest.TestCase):
    def test_crude(self):
        model = load("crude-unit.proteus.xml")
        self.assertFalse(model["diagnostics"]["stoppedOnError"])
        self.assertEqual(model["diagnostics"]["formatVersion"], "4.1.0")
        self.assertTrue(any(obj["tag"] == "P-101" and obj["kind"] == "equipment" for obj in model["objects"]))
        self.assertTrue(any(obj["id"] == "equip-E-301" and obj["tag"] is None for obj in model["objects"]))
        codes = [warning["code"] for warning in model["diagnostics"]["warnings"]]
        self.assertIn("property-uninterpreted", codes)
        self.assertIn("type-skipped", codes)
        self.assertIn("graphic-connectivity", codes)
        self.assertNotIn("schema-unsupported", codes)
        found = ids(model)
        for rule_id in [
            "broken-reference", "duplicate-tag", "eq-tag", "line-number", "valve-tag",
            "eq-service", "valve-type", "inst-function", "segment-ends", "equipment-tiein",
        ]:
            self.assertIn(rule_id, found, found)
        self.assertEqual(found.count("broken-reference"), 2)

    def test_clean(self):
        model = load("cooling-water.proteus.xml")
        self.assertEqual(model["diagnostics"]["warnings"], [])
        blocking = [item for item in run_checks(model, RULES) if item["severity"] != "info"]
        self.assertEqual(blocking, [])

    def test_dexpi2(self):
        model = load("dexpi-2-stub.xml")
        self.assertTrue(any(warning["code"] == "dexpi2-unsupported" for warning in model["diagnostics"]["warnings"]))
        self.assertEqual(model["edges"], [])
        self.assertTrue(any(obj["tag"] == "P-901" for obj in model["objects"]))
        found = ids(model)
        self.assertIn("connections-absent", found)
        self.assertNotIn("equipment-tiein", found)

    def test_plant3d(self):
        json_ids = ids(load("plant3d-export.json"))
        self.assertIn("broken-reference", json_ids)
        self.assertIn("valve-type", json_ids)
        self.assertIn("inst-tag", json_ids)
        csv_model = load("plant3d-datamanager.csv")
        self.assertTrue(any(obj["tag"] == "80-BF-150" for obj in csv_model["objects"]))
        self.assertIn("broken-reference", ids(csv_model))

    def test_pdf(self):
        model = load("feed-sheet.pdf")
        self.assertEqual(model["objects"], [])
        tags = [item["suggestedTag"] for item in model["candidates"]]
        for tag in ["P-101", "V-201", "100-CR-150", "XV-101", "HV-220", "PT-101", "FT-140", "X-9"]:
            self.assertIn(tag, tags, tags)
        confirmed = confirm_high_confidence(model)
        self.assertTrue(any(obj["tag"] == "P-101" for obj in confirmed["objects"]))
        self.assertFalse(any(obj["tag"] == "HV-220" for obj in confirmed["objects"]))
        self.assertFalse(any(obj["tag"] == "X-9" for obj in confirmed["objects"]))
        found = [item["ruleId"] for item in run_checks(confirmed, RULES)]
        self.assertIn("text-mentioned-ends", found)
        self.assertIn("connections-absent", found)
        self.assertIn("eq-service", found)


if __name__ == "__main__":
    unittest.main()

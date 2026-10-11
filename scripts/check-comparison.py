#!/usr/bin/env python3
"""Strictly check Bifrost --json output for every required seed-suite cell.

This checks result completeness and goldens, not binary/source provenance.
Exit codes: 0 PASS, 1 FAIL, 2 UNKNOWN (incomplete or malformed evidence).
"""

import argparse
import json
from pathlib import Path
import sys


def check(raw, suite, required):
    try:
        report, _ = json.JSONDecoder().raw_decode(raw.lstrip())
        if not isinstance(report, dict):
            raise ValueError("report must be an object")
        available = report["available"]
        skipped = report["skipped"]
        cases = report["cases"]
        if not isinstance(available, list) or not isinstance(skipped, dict):
            raise ValueError("invalid available/skipped fields")
        if not isinstance(cases, dict):
            raise ValueError("cases must be an object")
        expected = {case["name"]: case for case in suite["cases"]}
        if not expected or len(expected) != len(suite["cases"]):
            raise ValueError("suite cases must be nonempty and uniquely named")
        if any(case.get("expect") != "output" for case in expected.values()):
            raise ValueError("seed checker requires output goldens")
        incomplete = []
        failed = []
        for port in required:
            if port not in available or port in skipped:
                incomplete.append(f"required implementation unavailable: {port}")
        if set(cases) != set(expected):
            incomplete.append("case set differs from suite")
        for name, spec in expected.items():
            result = cases.get(name)
            if not isinstance(result, dict):
                incomplete.append(f"{name}: missing case result")
                continue
            cells = result.get("impls")
            if not isinstance(cells, dict):
                incomplete.append(f"{name}: missing implementation cells")
                continue
            verdict = result.get("verdict")
            if verdict in ("FAIL", "DIVERGE"):
                failed.append(f"{name}: verdict {verdict}")
            elif verdict != "PASS":
                incomplete.append(f"{name}: invalid verdict {verdict!r}")
            for port in required:
                cell = cells.get(port)
                if not isinstance(cell, dict):
                    incomplete.append(f"{name}/{port}: missing result")
                    continue
                status = cell.get("status")
                if status == "FAIL" or status == "DIVERGE":
                    failed.append(f"{name}/{port}: {status}")
                elif status != "PASS":
                    incomplete.append(f"{name}/{port}: {status!r}")
                elif cell.get("norm") != spec["golden"]:
                    failed.append(f"{name}/{port}: normalized output differs from golden")
        if failed:
            return "FAIL", failed + incomplete
        if incomplete:
            return "UNKNOWN", incomplete
        return "PASS", []
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        return "UNKNOWN", [f"invalid evidence: {error}"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--suite", type=Path, default=Path(__file__).resolve().parents[1] / "comparison/bifrost.suite.json")
    parser.add_argument("--required", default="shen-lua,shen-go,shen-koka")
    args = parser.parse_args()
    required = args.required.split(",")
    if len(set(required)) != len(required) or any(not port.strip() or port != port.strip() for port in required):
        parser.error("--required must contain unique nonempty implementation names")
    try:
        status, reasons = check(args.input.read_text(), json.loads(args.suite.read_text()), required)
    except (OSError, UnicodeError, ValueError) as error:
        status, reasons = "UNKNOWN", [str(error)]
    print(json.dumps({"scope": "seed-suite-observations", "status": status,
                      "required": required, "reasons": reasons}, indent=2))
    return {"PASS": 0, "FAIL": 1, "UNKNOWN": 2}[status]


if __name__ == "__main__":
    sys.exit(main())

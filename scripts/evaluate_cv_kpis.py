"""Create a machine-readable BESS KPI report from explicit evidence artifacts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from bess_opt.kpi import classify, evaluate_kpis


def read_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Required KPI artifact is missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", default="config/kpi_contract.yaml")
    parser.add_argument("--evidence-dir", default="results/kpi_evidence")
    parser.add_argument("--output", default="results/kpi_evidence/kpi_report.json")
    args = parser.parse_args()

    contract = yaml.safe_load(Path(args.contract).read_text(encoding="utf-8"))
    evidence = Path(args.evidence_dir)
    measured = evaluate_kpis(
        read_json(evidence / "baseline_summary.json"),
        read_json(evidence / "candidate_summary.json"),
        read_json(evidence / "validation_summary.json"),
    )
    targets = contract["targets"]
    report = {
        "policy": contract["evidence_policy"],
        "metrics": {
            "revenue_improvement_pct": {
                "measured": measured["revenue_improvement_pct"],
                "target": targets["revenue_improvement_pct"],
                "status": classify(measured["revenue_improvement_pct"], targets["revenue_improvement_pct"], "at_least"),
            },
            "equivalent_cycle_reduction_pct": {
                "measured": measured["equivalent_cycle_reduction_pct"],
                "target": targets["equivalent_cycle_reduction_pct"],
                "status": classify(measured["equivalent_cycle_reduction_pct"], targets["equivalent_cycle_reduction_pct"], "at_least"),
            },
            "maximum_validation_deviation_pct": {
                "measured": measured["maximum_validation_deviation_pct"],
                "target": targets["maximum_validation_deviation_pct"],
                "status": classify(measured["maximum_validation_deviation_pct"], targets["maximum_validation_deviation_pct"], "at_most"),
            },
            "runtime_minutes": {
                "baseline_measured": measured["baseline_runtime_minutes"],
                "candidate_measured": measured["candidate_runtime_minutes"],
                "baseline_target": targets["baseline_runtime_minutes"],
                "candidate_target": targets["candidate_runtime_minutes"],
                "status": "Measured; compare with controlled benchmark targets",
            },
        },
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Generate BitDPM v15 router-validation commands."""

from __future__ import annotations

import argparse
import os


def join_cmd(parts: list[str]) -> str:
    return " \\\n  ".join(parts)


def run(args):
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    tag = args.tag
    report_var = "${REPORT}"
    allow_core = "has_multiplication,has_distance,has_coordinate,has_mean,has_log"
    allow_core_nolog = "has_multiplication,has_distance,has_coordinate,has_mean"

    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        "# BitDPM v15 router-validation benchmark",
        "# This benchmark validates router trigger safety, not broad model capability.",
        "",
        join_cmd([
            "python scripts/run_v10_registry_eval.py",
            "--registry configs/bitdpm_v11_admitted_pool.json",
            "--benchmark-set v15",
            f"--tag {tag}",
            "--resume",
        ]),
        "",
        f"REPORT=$(ls -t experiments/reports/{tag}_*.json | head -1)",
        "echo \"Using report: $REPORT\"",
        "",
        "python scripts/summarize_v14_report.py \\",
        f"  --report {report_var} \\",
        f"  --tag {tag}",
        "",
        "python scripts/train_v12_utility_router.py \\",
        f"  --report {report_var} \\",
        f"  --tag {tag}_allow_core_safe \\",
        "  --eval-on-all \\",
        "  --min-fixes 1 \\",
        "  --max-breaks 0 \\",
        "  --min-precision 1.0 \\",
        "  --min-specificity 2 \\",
        "  --full-safety-filter \\",
        f"  --allowed-features {allow_core}",
        "",
        "python scripts/crossval_v12_utility_router.py \\",
        f"  --report {report_var} \\",
        f"  --tag {tag}_allow_core_cv \\",
        "  --folds 5 \\",
        "  --min-fixes 1 \\",
        "  --max-breaks 0 \\",
        "  --min-precision 1.0 \\",
        "  --min-specificity 2 \\",
        f"  --allowed-features {allow_core}",
        "",
        "python scripts/train_v12_utility_router.py \\",
        f"  --report {report_var} \\",
        f"  --tag {tag}_allow_core_nolog_safe \\",
        "  --eval-on-all \\",
        "  --min-fixes 1 \\",
        "  --max-breaks 0 \\",
        "  --min-precision 1.0 \\",
        "  --min-specificity 2 \\",
        "  --full-safety-filter \\",
        f"  --allowed-features {allow_core_nolog}",
        "",
        "python scripts/crossval_v12_utility_router.py \\",
        f"  --report {report_var} \\",
        f"  --tag {tag}_allow_core_nolog_cv \\",
        "  --folds 5 \\",
        "  --min-fixes 1 \\",
        "  --max-breaks 0 \\",
        "  --min-precision 1.0 \\",
        "  --min-specificity 2 \\",
        f"  --allowed-features {allow_core_nolog}",
        "",
        "python scripts/train_v12_utility_router.py \\",
        f"  --report {report_var} \\",
        f"  --tag {tag}_conj_safe \\",
        "  --eval-on-all \\",
        "  --min-fixes 1 \\",
        "  --max-breaks 0 \\",
        "  --min-precision 1.0 \\",
        "  --min-specificity 3 \\",
        "  --full-safety-filter \\",
        "  --include-conjunctions",
        "",
        "python scripts/crossval_v12_utility_router.py \\",
        f"  --report {report_var} \\",
        f"  --tag {tag}_conj_cv \\",
        "  --folds 5 \\",
        "  --min-fixes 1 \\",
        "  --max-breaks 0 \\",
        "  --min-precision 1.0 \\",
        "  --min-specificity 3 \\",
        "  --include-conjunctions",
        "",
        "python scripts/build_paper_result_tables.py",
        "",
        "echo 'v15 router-validation commands complete.'",
    ]

    with open(args.output, "w") as f:
        f.write("\n".join(lines) + "\n")
    os.chmod(args.output, 0o755)
    print(f"Saved: {args.output}")


def main():
    parser = argparse.ArgumentParser(description="Generate v15 router-validation commands")
    parser.add_argument("--tag", default="v15_router_validation_v11_admitted")
    parser.add_argument("--output", default="experiments/reports/v15_router_validation_commands.sh")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()

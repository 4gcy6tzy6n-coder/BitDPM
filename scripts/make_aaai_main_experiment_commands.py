#!/usr/bin/env python3
"""Generate the main BitDPM AAAI experiment command script.

The generated shell script is intentionally explicit and conservative. It uses
the current admitted registry, evaluates v14/v15/v1k, mines/evaluates the
current safest allow-core-no-log router, and rebuilds paper artifacts. It does
not introduce new mechanisms.
"""

from __future__ import annotations

import argparse
import os


ALLOW_CORE_NOLOG = "has_multiplication,has_distance,has_coordinate,has_mean"


def join_cmd(parts: list[str]) -> str:
    return " \\\n  ".join(parts)


def registry_eval(tag: str, benchmark: str, registry: str, model: str) -> list[str]:
    return [
        join_cmd(
            [
                "BITDPM_FORCE_CPU=1 python scripts/run_v10_registry_eval.py",
                f"--registry {registry}",
                f"--model {model}",
                f"--benchmark-set {benchmark}",
                f"--tag {tag}",
                "--resume",
            ]
        ),
        f"{tag.upper()}_REPORT=$(ls -t experiments/reports/{tag}_*.json | head -1)",
        f"echo \"{tag} report: ${tag.upper()}_REPORT\"",
    ]


def router_eval(tag: str, report_var: str) -> list[str]:
    return [
        "python scripts/train_v12_utility_router.py \\",
        f"  --report {report_var} \\",
        f"  --tag {tag}_allow_core_nolog_safe \\",
        "  --eval-on-all \\",
        "  --min-fixes 1 \\",
        "  --max-breaks 0 \\",
        "  --min-precision 1.0 \\",
        "  --min-specificity 2 \\",
        "  --full-safety-filter \\",
        f"  --allowed-features {ALLOW_CORE_NOLOG}",
        "",
        "python scripts/crossval_v12_utility_router.py \\",
        f"  --report {report_var} \\",
        f"  --tag {tag}_allow_core_nolog_cv \\",
        "  --folds 5 \\",
        "  --min-fixes 1 \\",
        "  --max-breaks 0 \\",
        "  --min-precision 1.0 \\",
        "  --min-specificity 2 \\",
        f"  --allowed-features {ALLOW_CORE_NOLOG}",
    ]


def bootstrap(report_var: str, out_path: str) -> list[str]:
    return [
        "python scripts/bootstrap_result_ci.py \\",
        f"  {report_var} \\",
        "  --samples 2000 \\",
        "  --seed 13 \\",
        f"  --out {out_path}",
    ]


def run(args: argparse.Namespace) -> None:
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    registry = args.registry
    model = args.model

    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        "# BitDPM AAAI main experiment script.",
        "# This is a generated command file. It runs current-method validation only;",
        "# it does not add new mechanisms or claim v31 recovery.",
        "",
        "python scripts/build_paper_package.py",
        "",
        "# Stage 1: Current broad validation on v14.",
        *registry_eval("aaai_v14_current_pool", "v14", registry, model),
        "",
        *router_eval("aaai_v14_current_pool", "$AAAI_V14_CURRENT_POOL_REPORT"),
        "",
        *bootstrap("$AAAI_V14_CURRENT_POOL_REPORT", "experiments/reports/aaai_v14_current_pool_bootstrap_ci.md"),
        "",
        "# Stage 2: Targeted router-safety validation on v15.",
        *registry_eval("aaai_v15_current_pool", "v15", registry, model),
        "",
        *router_eval("aaai_v15_current_pool", "$AAAI_V15_CURRENT_POOL_REPORT"),
        "",
        *bootstrap("$AAAI_V15_CURRENT_POOL_REPORT", "experiments/reports/aaai_v15_current_pool_bootstrap_ci.md"),
        "",
        "# Stage 3: 1k clean mixed validation. Held-out claims require a passing overlap audit.",
        *registry_eval("aaai_v1k_clean_current_pool", "v1k_clean", registry, model),
        "",
        *router_eval("aaai_v1k_clean_current_pool", "$AAAI_V1K_CLEAN_CURRENT_POOL_REPORT"),
        "",
        *bootstrap("$AAAI_V1K_CLEAN_CURRENT_POOL_REPORT", "experiments/reports/aaai_v1k_clean_current_pool_bootstrap_ci.md"),
        "",
        "# Stage 4: Rebuild paper-facing reports after new outputs exist.",
        "python scripts/build_paper_result_tables.py",
        "python scripts/build_aaai_readiness_report.py",
        "python scripts/build_paper_package.py",
        "",
        "echo 'AAAI main experiment commands complete.'",
    ]

    with open(args.output, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    os.chmod(args.output, 0o755)
    print(f"Saved: {args.output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate BitDPM AAAI main experiment commands.")
    parser.add_argument("--registry", default="configs/bitdpm_v11_admitted_pool.json")
    parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--output", default="experiments/reports/aaai_main_experiment_commands.sh")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()

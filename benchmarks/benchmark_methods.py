"""Reproducible multi-scenario optimizer benchmark.

Every method is scored against the closed-form global optimum (which is itself
certified by a rigorous lower bound), not against another sampled curve.

Usage (from the repository root):

    python benchmarks/benchmark_methods.py            # 150 triples, 20x10 seeds
    python benchmarks/benchmark_methods.py --cases 30 # quicker

Scenarios are generated with fixed NumPy seeds, so the accuracy columns are
reproducible; wall times depend on the machine.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cardan_core as core  # noqa: E402

SCENARIO_SEED = 7
BETA_MAX_DEG = 60.0


def _scenarios(count: int) -> list[tuple[float, float, float]]:
    rng = np.random.default_rng(SCENARIO_SEED)
    rng.uniform(0.0, BETA_MAX_DEG, (200, 2))  # keep the stream of the first study
    return [tuple(float(x) for x in rng.uniform(0.0, BETA_MAX_DEG, 3)) for _ in range(count)]


def _exact_unevenness(betas, phi1, phi2) -> float:
    parameters = core.CardanParameters(
        mode=3, beta1_deg=betas[0], beta2_deg=betas[1], beta3_deg=betas[2],
        phi1_deg=phi1, phi2_deg=phi2,
    )
    return core.exact_speed_ratio_bounds(parameters).unevenness_percent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=int, default=150)
    parser.add_argument("--seed-cases", type=int, default=20)
    parser.add_argument("--seeds", type=int, default=10)
    arguments = parser.parse_args()

    scenarios = _scenarios(arguments.cases)
    optimum = {}
    certified = 0
    for betas in scenarios:
        solution = core.exact_phase_optimum(
            core.CardanParameters(mode=3, beta1_deg=betas[0], beta2_deg=betas[1], beta3_deg=betas[2])
        )
        optimum[betas] = solution.unevenness_percent
        certified += bool(solution.certified_global)

    print(f"Cardan Joint Engineering Tool v{core.TOOL_VERSION} - optimizer benchmark")
    print(f"Scenarios: {len(scenarios)} random triple systems, beta in [0, {BETA_MAX_DEG:g}] deg, seed {SCENARIO_SEED}")
    print(f"Reference: closed-form optimum, certified global in {certified}/{len(scenarios)} cases")
    print()
    header = (
        f"{'method':24s} {'median gap':>11s} {'p95 gap':>10s} {'max gap':>10s}"
        f" {'median ms':>10s} {'median nfev':>12s} {'success %':>10s}"
    )
    print("Gap = closed-form unevenness of the returned phases minus the global optimum (percentage points)")
    print(header)
    for method in core.OptimizationMethod:
        gaps, times, evaluations, success = [], [], [], []
        for betas in scenarios:
            parameters = core.CardanParameters(
                mode=3, beta1_deg=betas[0], beta2_deg=betas[1], beta3_deg=betas[2]
            )
            settings = core.OptimizationSettings(method=method, validation_sample_count=7200)
            started = time.perf_counter()
            analysis = core.calculate_analysis(parameters, optimization_settings=settings)
            times.append(time.perf_counter() - started)
            result = analysis["optimization_result"]
            gaps.append(_exact_unevenness(betas, result.phi1_deg, result.phi2_deg) - optimum[betas])
            evaluations.append(analysis["optimization_diagnostics"].function_evaluations)
            success.append(analysis["optimization_diagnostics"].success)
        gaps = np.maximum(np.array(gaps), 0.0)
        print(
            f"{method.value:24s} {np.median(gaps):11.3e} {np.percentile(gaps, 95):10.3e} {gaps.max():10.3e}"
            f" {1000 * np.median(times):10.1f} {int(np.median(evaluations)):12d} {100 * np.mean(success):10.0f}"
        )

    print()
    print(f"Seed sensitivity ({arguments.seed_cases} scenarios x {arguments.seeds} seeds)")
    for method in (core.OptimizationMethod.DIFFERENTIAL_EVOLUTION, core.OptimizationMethod.HYBRID):
        worst, spread, times = 0.0, 0.0, []
        for betas in scenarios[: arguments.seed_cases]:
            values = []
            for seed in range(arguments.seeds):
                parameters = core.CardanParameters(
                    mode=3, beta1_deg=betas[0], beta2_deg=betas[1], beta3_deg=betas[2]
                )
                started = time.perf_counter()
                analysis = core.calculate_analysis(
                    parameters,
                    optimization_settings=core.OptimizationSettings(method=method, random_seed=seed),
                )
                times.append(time.perf_counter() - started)
                result = analysis["optimization_result"]
                values.append(_exact_unevenness(betas, result.phi1_deg, result.phi2_deg) - optimum[betas])
            worst = max(worst, max(values))
            spread = max(spread, max(values) - min(values))
        print(
            f"  {method.value:24s} max gap {worst:.3e} pu, max spread {spread:.3e} pu, "
            f"time min/median/max {1000 * min(times):.0f}/{1000 * np.median(times):.0f}/{1000 * max(times):.0f} ms"
        )

    print()
    print("Sampling error of the 360-sample objective versus the closed form (200 random triples per band)")
    rng = np.random.default_rng(1)
    for upper in (30, 45, 60, 75, 85):
        errors = []
        for _ in range(200):
            betas = rng.uniform(0.6 * upper, upper, 3)
            phases = rng.uniform(0.0, 180.0, 2)
            parameters = core.CardanParameters(
                mode=3, beta1_deg=betas[0], beta2_deg=betas[1], beta3_deg=betas[2],
                phi1_deg=phases[0], phi2_deg=phases[1],
            )
            exact = core.exact_speed_ratio_bounds(parameters).unevenness_percent
            sampled = core.unevenness_percent(
                core.calculate_total_ratio(np.linspace(0.0, 180.0, 360, endpoint=False), parameters)
            )
            errors.append(100.0 * (sampled - exact) / exact)
        errors = np.array(errors)
        print(f"  beta in [{0.6 * upper:.0f}, {upper}] deg: worst {errors.min():.4f} %, median {np.median(errors):.5f} %")


if __name__ == "__main__":
    main()

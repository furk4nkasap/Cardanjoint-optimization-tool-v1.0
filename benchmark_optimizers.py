"""Reproducible optimizer comparison for Cardan Joint Engineering Tool v1.2.4."""

from __future__ import annotations

from time import perf_counter

import cardan_core as core


def main() -> None:
    parameters = core.CardanParameters(
        mode=core.CardanMode.TRIPLE,
        beta1_deg=43.02,
        beta2_deg=25.26,
        beta3_deg=47.51,
        optimization_step_deg=5.0,
    )

    print("Cardan Joint Engineering Tool v1.2.4 optimizer benchmark")
    print(f"Parameters: {parameters}")
    print()

    for method in core.OptimizationMethod:
        settings = core.OptimizationSettings(
            method=method,
            local_refinement_step_deg=0.25,
            differential_evolution_max_iterations=80,
            differential_evolution_population_size=12,
            random_seed=42,
            validation_sample_count=7200,
        )
        started = perf_counter()
        analysis = core.calculate_analysis(parameters, optimization_settings=settings)
        wall_time = perf_counter() - started
        result = analysis["optimization_result"]
        diagnostics = analysis["optimization_diagnostics"]

        print(f"Method: {method.value}")
        print(f"  phi1: {result.phi1_deg:.9f} deg")
        print(f"  phi2: {result.phi2_deg:.9f} deg")
        print(f"  objective unevenness: {diagnostics.objective_unevenness_percent:.12f} %")
        print(f"  validated unevenness: {diagnostics.validated_unevenness_percent:.12f} %")
        print(f"  function evaluations: {diagnostics.function_evaluations}")
        print(f"  solver success/accepted: {diagnostics.success}")
        print(f"  measured wall time: {wall_time:.6f} s")
        print()


if __name__ == "__main__":
    main()

"""Optimizer behaviour: never worse than the start, bounded gap to the optimum."""

from __future__ import annotations

import numpy as np
import pytest

import cardan_core as core
import reference_model as ref

P = core.CardanParameters
S = core.OptimizationSettings
METHODS = list(core.OptimizationMethod)


def _triples(count, seed=42):
    rng = np.random.default_rng(seed)
    return [tuple(float(x) for x in rng.uniform(0.0, 60.0, 3)) for _ in range(count)]


@pytest.mark.parametrize("method", METHODS)
def test_optimum_is_never_worse_than_current_configuration(method):
    """Regression for the 'negative reduction' defect.

    The current phases are placed (rounded to the 0.01 deg UI step) at the true
    optimum, so every grid-based candidate is worse than the start.
    """

    betas = (43.02, 25.26, 47.51)
    parameters = P(mode=3, beta1_deg=betas[0], beta2_deg=betas[1], beta3_deg=betas[2],
                   phi1_deg=68.21, phi2_deg=16.52)
    analysis = core.calculate_analysis(parameters, optimization_settings=S(method=method))
    current = analysis["current_metrics"].unevenness_percent
    optimized = analysis["optimized_metrics"].unevenness_percent
    assert optimized <= current + 1e-9


@pytest.mark.parametrize("method", METHODS)
def test_never_worse_on_random_cases(method):
    rng = np.random.default_rng(7)
    for betas in _triples(12, seed=7):
        phases = rng.uniform(0.0, 180.0, 2)
        parameters = P(mode=3, beta1_deg=betas[0], beta2_deg=betas[1], beta3_deg=betas[2],
                       phi1_deg=float(phases[0]), phi2_deg=float(phases[1]))
        analysis = core.calculate_analysis(parameters, optimization_settings=S(method=method))
        assert (
            analysis["optimized_metrics"].unevenness_percent
            <= analysis["current_metrics"].unevenness_percent + 1e-9
        )


def test_exact_method_is_at_least_as_good_as_every_other_method():
    for betas in _triples(15, seed=3):
        parameters = P(mode=3, beta1_deg=betas[0], beta2_deg=betas[1], beta3_deg=betas[2])
        results = {}
        for method in METHODS:
            analysis = core.calculate_analysis(parameters, optimization_settings=S(method=method))
            result = analysis["optimization_result"]
            results[method] = ref.closed_form_unevenness(betas, (result.phi1_deg, result.phi2_deg))
        best_other = min(value for method, value in results.items()
                         if method is not core.OptimizationMethod.EXACT)
        assert results[core.OptimizationMethod.EXACT] <= best_other + 1e-7
        assert results[core.OptimizationMethod.EXACT] == pytest.approx(
            ref.theoretical_minimum_unevenness(betas), abs=1e-7
        )


def test_analysis_reports_optimality_gap_against_closed_form():
    betas = (43.02, 25.26, 47.51)
    parameters = P(mode=3, beta1_deg=betas[0], beta2_deg=betas[1], beta3_deg=betas[2])
    grid = core.calculate_analysis(parameters, optimization_settings=S(method="grid"))
    exact = core.calculate_analysis(parameters, optimization_settings=S(method="exact"))
    assert grid["optimality_gap_percent"] == pytest.approx(0.754, abs=0.01)
    assert exact["optimality_gap_percent"] == pytest.approx(0.0, abs=1e-7)
    assert exact["exact_optimum"].certified_global
    assert exact["optimization_diagnostics"].success


@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize("betas", [(25.0, 25.0), (20.0, 35.0), (10.0, 55.0)])
def test_double_joint_boundary_optimum(method, betas):
    """The optimum of a double joint sits on the 0/180 deg seam."""

    parameters = P(mode=2, beta1_deg=betas[0], beta2_deg=betas[1], phi1_deg=40.0)
    analysis = core.calculate_analysis(parameters, optimization_settings=S(method=method))
    phi = analysis["optimization_result"].phi1_deg
    distance = min(phi, 180.0 - phi)
    limit = 1e-9 if method is core.OptimizationMethod.EXACT else 0.5
    assert distance <= limit
    attained = ref.closed_form_unevenness(betas, (phi,))
    assert attained == pytest.approx(ref.theoretical_minimum_unevenness(betas), abs=0.02)


def test_stochastic_methods_are_reproducible_with_fixed_seed():
    parameters = P(mode=3, beta1_deg=31.0, beta2_deg=18.0, beta3_deg=44.0)
    for method in ("differential_evolution", "hybrid"):
        first = core.calculate_analysis(parameters, optimization_settings=S(method=method, random_seed=5))
        second = core.calculate_analysis(parameters, optimization_settings=S(method=method, random_seed=5))
        assert first["optimization_result"].phi1_deg == second["optimization_result"].phi1_deg
        assert first["optimization_result"].phi2_deg == second["optimization_result"].phi2_deg


def test_legacy_regression_value_of_local_refinement_is_unchanged():
    """TEST_REPORT.txt, item 5 (v1.2.4): beta = 9.5/9.5/9.5, local refinement."""

    analysis = core.calculate_analysis(
        P(mode=3, beta1_deg=9.5, beta2_deg=9.5, beta3_deg=9.5), refine=True
    )
    result = analysis["optimization_result"]
    assert (result.phi1_deg, result.phi2_deg) == (30.0, 30.0)
    assert analysis["optimized_metrics"].unevenness_percent == pytest.approx(
        0.000131672855774, rel=1e-9
    )


def test_near_zero_baseline_is_flagged_not_divided():
    parameters = P(mode=2, beta1_deg=25.0, beta2_deg=25.0, phi1_deg=0.0)
    analysis = core.calculate_analysis(parameters, optimization_settings=S(method="exact"))
    assert analysis["current_is_optimal"]
    assert analysis["optimization_result"].phi1_deg == 0.0
    assert core.reduction_percent(
        analysis["current_metrics"].unevenness_percent,
        analysis["optimized_metrics"].unevenness_percent,
    ) is None


def test_reduction_percent_definition():
    assert core.reduction_percent(20.0, 5.0) == pytest.approx(75.0)
    assert core.reduction_percent(0.0, 0.0) is None
    assert core.reduction_percent(1e-12, 0.0) is None
    assert core.reduction_percent(5.0, 5.0 + 1e-12) == 0.0

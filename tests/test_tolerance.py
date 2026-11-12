"""Assembly-tolerance sensitivity and discrete (spline) phase options.

Reference values come from tests/reference_model.py (independent SVD form).

Tolerances
----------
* 1e-9 pu : values evaluated at identical phase/angle points (round-off).
* 1 %     : interior random points versus the worst value found on the
            tolerance grid.  The grid spacing is tolerance/10; the unevenness
            is smooth away from an exact-zero optimum and conical at it (where
            the worst case is a grid corner), so the inter-node excess is far
            below 1 % for tolerances of a few degrees.
"""

from __future__ import annotations

import itertools

import numpy as np
import pytest

import cardan_core as core
import reference_model as ref

P = core.CardanParameters
BENCH = (43.02, 25.26, 47.51)


def _optimised(betas):
    parameters = P(mode=3, beta1_deg=betas[0], beta2_deg=betas[1], beta3_deg=betas[2])
    optimum = core.exact_phase_optimum(parameters)
    return core.replace(parameters, phi1_deg=optimum.phi1_deg, phi2_deg=optimum.phi2_deg)


def test_zero_tolerance_returns_nominal():
    parameters = P(mode=3, beta1_deg=20, beta2_deg=30, beta3_deg=25, phi1_deg=40, phi2_deg=70)
    result = core.tolerance_sensitivity(parameters, 0.0, 0.0)
    nominal = ref.closed_form_unevenness((20, 30, 25), (40, 70))
    for value in (
        result.nominal_unevenness_percent,
        result.worst_phase_unevenness_percent,
        result.worst_beta_unevenness_percent,
        result.worst_combined_unevenness_percent,
    ):
        assert value == pytest.approx(nominal, abs=1e-9)


def test_worst_case_ordering_and_monotonicity():
    parameters = _optimised(BENCH)
    previous = None
    for tolerance in (0.25, 0.5, 1.0, 2.0):
        result = core.tolerance_sensitivity(parameters, tolerance, tolerance)
        assert result.worst_phase_unevenness_percent >= result.nominal_unevenness_percent - 1e-12
        assert result.worst_beta_unevenness_percent >= result.nominal_unevenness_percent - 1e-12
        assert result.worst_combined_unevenness_percent >= max(
            result.worst_phase_unevenness_percent, result.worst_beta_unevenness_percent
        ) - 1e-9
        if previous is not None:
            assert result.worst_combined_unevenness_percent >= previous - 1e-9
        previous = result.worst_combined_unevenness_percent


def test_phase_worst_case_matches_independent_corner_values():
    """At an exact-zero optimum the unevenness is conical, so the worst phase
    error inside the box is a corner; corners are grid nodes."""

    parameters = _optimised(BENCH)
    result = core.tolerance_sensitivity(parameters, 1.0, 0.0)
    corners = [
        ref.closed_form_unevenness(BENCH, (parameters.phi1_deg + a, parameters.phi2_deg + b))
        for a, b in itertools.product((-1.0, 1.0), repeat=2)
    ]
    assert result.worst_phase_unevenness_percent == pytest.approx(max(corners), abs=1e-9)
    assert result.worst_phase_unevenness_percent > 5.0  # 1 deg of clocking error matters


@pytest.mark.parametrize("seed", range(8))
def test_random_points_inside_the_box_do_not_exceed_reported_worst_case(seed):
    rng = np.random.default_rng(seed)
    betas = tuple(float(x) for x in rng.uniform(5.0, 50.0, 3))
    phases = tuple(float(x) for x in rng.uniform(0.0, 180.0, 2))
    parameters = P(mode=3, beta1_deg=betas[0], beta2_deg=betas[1], beta3_deg=betas[2],
                   phi1_deg=phases[0], phi2_deg=phases[1])
    phase_tol, beta_tol = 2.0, 1.5
    result = core.tolerance_sensitivity(parameters, phase_tol, beta_tol)
    for _ in range(300):
        d_beta = rng.uniform(-beta_tol, beta_tol, 3)
        d_phase = rng.uniform(-phase_tol, phase_tol, 2)
        value = ref.closed_form_unevenness(
            tuple(np.clip(np.array(betas) + d_beta, 0.0, 89.0)),
            tuple(np.array(phases) + d_phase),
        )
        assert value <= result.worst_combined_unevenness_percent * 1.01 + 1e-6


def test_double_and_single_joint_sensitivity():
    double = core.tolerance_sensitivity(P(mode=2, beta1_deg=25, beta2_deg=25, phi1_deg=0.0), 1.0, 0.5)
    assert double.nominal_unevenness_percent < 1e-9
    assert double.worst_phase_unevenness_percent == pytest.approx(
        ref.closed_form_unevenness((25, 25), (1.0,)), abs=1e-9
    )
    assert double.worst_beta_unevenness_percent == pytest.approx(
        ref.closed_form_unevenness((25.5, 24.5), (0.0,)), abs=1e-9
    )
    single = core.tolerance_sensitivity(P(mode=1, beta1_deg=20), 5.0, 1.0)
    assert single.worst_phase_unevenness_percent == pytest.approx(single.nominal_unevenness_percent)
    assert single.worst_beta_unevenness_percent == pytest.approx(
        ref.closed_form_unevenness((21.0,)), abs=1e-9
    )


@pytest.mark.parametrize("arguments", [(-1.0, 0.0), (0.0, -0.1), (float("nan"), 0.0), (0.0, float("inf"))])
def test_invalid_tolerances_are_rejected(arguments):
    with pytest.raises(ValueError):
        core.tolerance_sensitivity(P(mode=2), *arguments)


@pytest.mark.parametrize("teeth, expected", [(1, 1), (2, 1), (4, 2), (16, 8), (15, 15), (24, 12), (25, 25)])
def test_discrete_phase_values(teeth, expected):
    values = core.discrete_phase_values_deg(teeth)
    assert len(values) == expected
    assert values[0] == 0.0
    assert all(0.0 <= value < 180.0 for value in values)
    step = 360.0 / teeth
    for value in values:
        distances = [(value - k * step) % 180.0 for k in range(teeth)]
        assert min(min(d, 180.0 - d) for d in distances) < 1e-9


@pytest.mark.parametrize("teeth", [(16, 16), (15, 20), (24, 10)])
def test_discrete_optimum_equals_brute_force(teeth):
    parameters = P(mode=3, beta1_deg=BENCH[0], beta2_deg=BENCH[1], beta3_deg=BENCH[2])
    result = core.discrete_phase_optimum(parameters, teeth[0], teeth[1])
    brute = min(
        (ref.closed_form_unevenness(BENCH, (a, b)), a, b)
        for a in core.discrete_phase_values_deg(teeth[0])
        for b in core.discrete_phase_values_deg(teeth[1])
    )
    assert result.best.unevenness_percent == pytest.approx(brute[0], abs=1e-9)
    assert result.best.phi1_deg in core.discrete_phase_values_deg(teeth[0])
    assert result.best.phi2_deg in core.discrete_phase_values_deg(teeth[1])
    attained = ref.closed_form_unevenness(BENCH, (result.best.phi1_deg, result.best.phi2_deg))
    assert attained == pytest.approx(brute[0], abs=1e-9)
    assert result.best.unevenness_percent >= result.continuous_optimum_percent - 1e-9
    values = [option.unevenness_percent for option in result.options]
    assert all(b >= a - 1e-9 for a, b in zip(values, values[1:]))
    assert len(result.options) == len(core.discrete_phase_values_deg(teeth[0])) * len(
        core.discrete_phase_values_deg(teeth[1])
    )


def test_discrete_optimum_double_joint_is_aligned():
    result = core.discrete_phase_optimum(P(mode=2, beta1_deg=20, beta2_deg=35, phi1_deg=50), 10)
    assert result.best.phi1_deg == 0.0 and result.best.phi2_deg is None


@pytest.mark.parametrize("teeth", [0, -3, 2.5])
def test_invalid_tooth_counts_are_rejected(teeth):
    with pytest.raises(ValueError):
        core.discrete_phase_optimum(P(mode=3), teeth, 16)


def test_single_joint_has_no_discrete_options():
    with pytest.raises(ValueError):
        core.discrete_phase_optimum(P(mode=1), 16)

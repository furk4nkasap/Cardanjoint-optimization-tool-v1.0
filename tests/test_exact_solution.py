"""Closed-form speed-ratio bounds and the exact phase optimum.

Tolerances
----------
* 1e-9 pu  : closed form versus an independent SVD evaluation (round-off).
* 2e-6 rel.: closed form versus 72 000-sample curves; the sampled extreme of a
             smooth peak is low by at most ~ (pi/N)^2 * 2 = 4e-9 relative for
             UI-range angles, 2e-6 leaves margin for narrow high-angle peaks.
* 1e-7 pu  : optimum versus the rigorous lower bound (optimizer tolerance).
"""

from __future__ import annotations

import numpy as np
import pytest

import cardan_core as core
import reference_model as ref

P = core.CardanParameters
RNG_SEED = 20240611


def _random_cases(count, upper=60.0):
    rng = np.random.default_rng(RNG_SEED)
    cases = []
    for _ in range(count):
        mode = int(rng.integers(1, 4))
        betas = tuple(float(x) for x in rng.uniform(0.0, upper, mode))
        phases = tuple(float(x) for x in rng.uniform(0.0, 180.0, mode - 1))
        cases.append((betas, phases))
    return cases


def _parameters(betas, phases=()):
    keywords = {f"beta{i + 1}_deg": beta for i, beta in enumerate(betas)}
    keywords.update({f"phi{i + 1}_deg": phase for i, phase in enumerate(phases)})
    return P(mode=len(betas), **keywords)


@pytest.mark.parametrize("betas, phases", _random_cases(60))
def test_exact_bounds_match_independent_svd_and_dense_sampling(betas, phases):
    parameters = _parameters(betas, phases)
    exact = core.exact_speed_ratio_bounds(parameters)
    q_min, q_max = ref.closed_form_bounds(betas, phases)
    assert exact.q_max == pytest.approx(q_max, rel=1e-11)
    assert exact.q_min == pytest.approx(q_min, rel=1e-11)
    assert exact.unevenness_percent == pytest.approx(100.0 * (q_max - q_min), abs=1e-9)

    ratio = core.calculate_total_ratio(np.linspace(0.0, 180.0, 72000, endpoint=False), parameters)
    assert ratio.max() == pytest.approx(exact.q_max, rel=2e-6)
    assert ratio.min() == pytest.approx(exact.q_min, rel=2e-6)
    assert ratio.max() <= exact.q_max * (1.0 + 1e-12)
    assert ratio.min() >= exact.q_min * (1.0 - 1e-12)


def test_exact_bounds_remain_accurate_at_high_angles_where_sampling_fails():
    parameters = _parameters((84.0, 80.0, 86.0), (12.0, 101.0))
    exact = core.exact_speed_ratio_bounds(parameters)
    reference = ref.closed_form_unevenness((84.0, 80.0, 86.0), (12.0, 101.0))
    assert exact.unevenness_percent == pytest.approx(reference, rel=1e-10)
    sampled = core.unevenness_percent(
        core.calculate_total_ratio(np.linspace(0.0, 180.0, 360, endpoint=False), parameters)
    )
    assert sampled < exact.unevenness_percent  # the 360-sample objective under-reads


def test_constant_velocity_is_exactly_zero_not_noise_amplified():
    exact = core.exact_speed_ratio_bounds(_parameters((25.0, 25.0), (0.0,)))
    assert exact.unevenness_percent < 1e-10


@pytest.mark.parametrize("seed", range(40))
def test_double_joint_optimum_is_aligned_yokes(seed):
    rng = np.random.default_rng(seed)
    betas = tuple(float(x) for x in rng.uniform(0.0, 60.0, 2))
    optimum = core.exact_phase_optimum(_parameters(betas, (57.0,)))
    assert optimum.phi1_deg == 0.0
    assert optimum.phi2_deg is None
    assert optimum.unevenness_percent == pytest.approx(
        ref.theoretical_minimum_unevenness(betas), abs=1e-9
    )
    assert optimum.certified_global


@pytest.mark.parametrize("seed", range(60))
def test_triple_joint_optimum_reaches_rigorous_lower_bound(seed):
    rng = np.random.default_rng(1000 + seed)
    betas = tuple(float(x) for x in rng.uniform(0.0, 60.0, 3))
    optimum = core.exact_phase_optimum(_parameters(betas))
    bound = ref.theoretical_minimum_unevenness(betas)
    assert optimum.lower_bound_percent == pytest.approx(bound, abs=1e-9)
    assert optimum.unevenness_percent >= bound - 1e-9
    assert optimum.unevenness_percent == pytest.approx(bound, abs=1e-7)
    assert optimum.certified_global
    # The reported value is really attained by the reported phases.
    attained = ref.closed_form_unevenness(betas, (optimum.phi1_deg, optimum.phi2_deg))
    assert attained == pytest.approx(optimum.unevenness_percent, abs=1e-9)


def test_exact_optimum_is_deterministic():
    parameters = _parameters((43.02, 25.26, 47.51))
    first = core.exact_phase_optimum(parameters)
    second = core.exact_phase_optimum(parameters)
    assert (first.phi1_deg, first.phi2_deg) == (second.phi1_deg, second.phi2_deg)


def test_single_joint_has_no_phase_optimum():
    optimum = core.exact_phase_optimum(_parameters((30.0,)))
    assert optimum.phi1_deg is None and optimum.phi2_deg is None
    expected = 100.0 * np.sin(np.deg2rad(30.0)) * np.tan(np.deg2rad(30.0))
    assert optimum.unevenness_percent == pytest.approx(expected, abs=1e-9)

"""Code verification of the Hooke-joint kinematics against analytic cases.

Tolerances
----------
* 1e-12 : pure floating-point identities (a few ulp of values of order 1).
* 1e-8  : central-difference derivative on a 0.005 deg grid; truncation error
          is h^2/6 * |q'''| ~ (8.7e-5 rad)^2 ~ 1e-9.
"""

from __future__ import annotations

import numpy as np
import pytest

import cardan_core as core

P = core.CardanParameters
DENSE = np.linspace(0.0, 180.0, 36000, endpoint=False)


def test_zero_misalignment_is_constant_velocity():
    assert np.max(np.abs(core.single_cardan_ratio(DENSE, 0.0) - 1.0)) < 1e-12


@pytest.mark.parametrize("beta", [5.0, 15.0, 30.0, 45.0, 60.0])
def test_single_joint_extrema_and_unevenness(beta):
    """q in [cos(beta), 1/cos(beta)] and U = sin(beta) tan(beta).

    Source: Karaoglan & Kuralay (2024), Eq. (4)-(5); the extrema are also the
    classical textbook result.  The 0.005 deg grid contains both extrema.
    """

    ratio = core.single_cardan_ratio(DENSE, beta)
    cosine = np.cos(np.deg2rad(beta))
    assert ratio.max() == pytest.approx(1.0 / cosine, abs=1e-12)
    assert ratio.min() == pytest.approx(cosine, abs=1e-12)
    expected = 100.0 * np.sin(np.deg2rad(beta)) * np.tan(np.deg2rad(beta))
    assert core.unevenness_percent(ratio) == pytest.approx(expected, abs=1e-9)


@pytest.mark.parametrize("beta", [5.0, 25.0, 45.0, 60.0])
def test_double_joint_equal_angles_aligned_yokes_is_constant_velocity(beta):
    """Planar layout, equal angles, physical phase 0 (aligned yokes)."""

    ratio = core.double_cardan_ratio(DENSE, beta, beta, 0.0)
    assert np.max(np.abs(ratio - 1.0)) < 1e-12


@pytest.mark.parametrize("beta", [5.0, 25.0, 45.0])
def test_double_joint_perpendicular_yokes_is_worst_case(beta):
    ratio = core.double_cardan_ratio(DENSE, beta, beta, 90.0)
    k = 1.0 / np.cos(np.deg2rad(beta))
    assert ratio.max() == pytest.approx(k * k, abs=1e-10)
    assert ratio.min() == pytest.approx(1.0 / (k * k), abs=1e-10)


@pytest.mark.parametrize("phase", [0.0, 17.3, 90.0, 133.7])
def test_phase_is_180_degree_periodic(phase):
    theta = np.linspace(0.0, 360.0, 3600, endpoint=False)
    double = core.double_cardan_ratio(theta, 20, 35, phase)
    shifted = core.double_cardan_ratio(theta, 20, 35, phase + 180.0)
    assert np.max(np.abs(double - shifted)) < 1e-12
    triple = core.triple_cardan_ratio(theta, 20, 35, 12, phase, 44.0)
    shifted = core.triple_cardan_ratio(theta, 20, 35, 12, phase + 180.0, 224.0)
    assert np.max(np.abs(triple - shifted)) < 1e-12


def test_parameters_canonicalise_phase():
    parameters = P(mode=3, phi1_deg=180.0, phi2_deg=359.5)
    assert parameters.phi1_deg == 0.0
    assert parameters.phi2_deg == pytest.approx(179.5)


CASES = [
    P(mode=1, beta1_deg=30),
    P(mode=2, beta1_deg=30, beta2_deg=12, phi1_deg=40),
    P(mode=3, beta1_deg=43.02, beta2_deg=25.26, beta3_deg=47.51, phi1_deg=10, phi2_deg=77, theta0_deg=33),
]


@pytest.mark.parametrize("parameters", CASES)
def test_full_revolution_and_derivative_consistency(parameters):
    theta = np.linspace(0.0, 360.0, 72001)
    trajectory = core.calculate_kinematic_trajectory(theta, parameters)
    output = trajectory.joint_output_angles_deg[-1]
    # One input revolution gives exactly one output revolution.
    assert output[-1] - output[0] == pytest.approx(360.0, abs=1e-9)
    # Mean speed ratio over a uniform full cycle is 1.
    assert trajectory.total_speed_ratio[:-1].mean() == pytest.approx(1.0, abs=1e-12)
    # d(theta_out)/d(theta_in) of the unwrapped angle equals the product of q_i.
    numeric = np.gradient(output, theta)
    assert np.max(np.abs(numeric[2:-2] - trajectory.total_speed_ratio[2:-2])) < 1e-8
    # The plain ratio function and the trajectory agree.
    assert np.max(np.abs(trajectory.total_speed_ratio - core.calculate_total_ratio(theta, parameters))) < 1e-12


@pytest.mark.parametrize("parameters", CASES[1:])
def test_joint_chain_uses_previous_output_minus_model_phase(parameters):
    theta = np.linspace(0.0, 360.0, 721)
    trajectory = core.calculate_kinematic_trajectory(theta, parameters)
    for index, phase in enumerate(parameters.active_phases):
        model_phase = float(core.physical_phase_to_model_phase_deg(phase))
        delta = trajectory.joint_input_angles_deg[index + 1] - (
            trajectory.joint_output_angles_deg[index] - model_phase
        )
        delta = (delta + 180.0) % 360.0 - 180.0
        assert np.max(np.abs(delta)) < 1e-9


def test_theta0_changes_only_sampling_not_cycle_metrics():
    """theta0 shifts the cycle; full-cycle metrics are physically invariant.

    The sampled max-min changes only through the grid position.  The bound
    used for N samples is the parabolic sampling error of the peak:
    U * (pi/N)^2 * 2 covers the worst half-step offset for a 2nd-order curve.
    """

    base = P(mode=3, beta1_deg=43.02, beta2_deg=25.26, beta3_deg=47.51, phi1_deg=10, phi2_deg=77)
    for samples in (360, 3600):
        values = []
        for theta0 in (0.0, 0.13, 7.77, 45.0, 91.31, 179.9):
            ratio = core.calculate_total_ratio(
                np.linspace(0.0, 180.0, samples, endpoint=False),
                core.replace(base, theta0_deg=theta0),
            )
            metrics = core.calculate_curve_metrics(ratio)
            values.append(metrics.unevenness_percent)
            assert metrics.q_mean == pytest.approx(1.0, abs=1e-12)
        spread = max(values) - min(values)
        assert spread < max(values) * 2.0 * (np.pi / samples) ** 2

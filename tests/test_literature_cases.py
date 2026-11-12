"""Reproducible examples taken from the literature.

Karaoglan, M.U., Kuralay, N.S. (2024). "Tasitlarda Uc Mafsalli Moment Iletim
Performansinin Kinematik Analizi". DEUFMD 26(76), 22-27.
DOI: 10.21205/deufmd.2024267603 (full text read).

Inputs (Table 1 and Table 2 of the paper):
    top-view joint angles     7.5, 15, 7.5 deg (all designs)
    front-view joint angles   Design-1: +5, -10, +5
                              Design-2: -5, +7.5, -2.5
                              Design-3: -1, +4, -0.5
Resultant joint angle, Eq. (6):  beta_r = arctan(sqrt(tan^2 b_front + tan^2 b_top))
Model of the paper (Section 3): the single-joint ratio of Eq. (4) is evaluated
for each joint and the three ratios are multiplied.  No yoke phase or joint
plane orientation enters, i.e. all fluctuations are superposed in phase.  In
this tool that is the planar chain with physical phases 90/90 deg.

Reported speed-ratio ranges (Section 3, Figure 5):
    Design-1: 1.08 ... 0.93   Design-2: 1.07 ... 0.94   Design-3: 1.05 ... 0.95

Tolerance: the paper prints two decimals (+-0.005).  It also quotes 0.92 once
and 0.93 once for Design-1, so +-0.006 is used.  These are low-precision
reference values: they check the model and the order of magnitude, not the
last digits.
"""

from __future__ import annotations

import numpy as np
import pytest

import cardan_core as core

TOP_VIEW = (7.5, 15.0, 7.5)
DESIGNS = {
    "design_1": ((5.0, -10.0, 5.0), (1.08, 0.93)),
    "design_2": ((-5.0, 7.5, -2.5), (1.07, 0.94)),
    "design_3": ((-1.0, 4.0, -0.5), (1.05, 0.95)),
}
TOLERANCE = 0.006


def resultant_angle_deg(front_deg, top_deg):
    tangent = np.hypot(np.tan(np.deg2rad(front_deg)), np.tan(np.deg2rad(top_deg)))
    return float(np.rad2deg(np.arctan(tangent)))


@pytest.mark.parametrize("name", sorted(DESIGNS))
def test_karaoglan_kuralay_three_joint_speed_ratio_range(name):
    front, (reported_max, reported_min) = DESIGNS[name]
    betas = [resultant_angle_deg(f, t) for f, t in zip(front, TOP_VIEW)]
    parameters = core.CardanParameters(
        mode=3, beta1_deg=betas[0], beta2_deg=betas[1], beta3_deg=betas[2],
        phi1_deg=90.0, phi2_deg=90.0,
    )
    ratio = core.calculate_total_ratio(np.linspace(0.0, 360.0, 7200, endpoint=False), parameters)
    assert ratio.max() == pytest.approx(reported_max, abs=TOLERANCE)
    assert ratio.min() == pytest.approx(reported_min, abs=TOLERANCE)


def test_karaoglan_kuralay_design_ranking():
    """The paper ranks Design-1 worst and Design-3 best."""

    spans = []
    for name in ("design_1", "design_2", "design_3"):
        front, _ = DESIGNS[name]
        betas = [resultant_angle_deg(f, t) for f, t in zip(front, TOP_VIEW)]
        parameters = core.CardanParameters(
            mode=3, beta1_deg=betas[0], beta2_deg=betas[1], beta3_deg=betas[2],
            phi1_deg=90.0, phi2_deg=90.0,
        )
        ratio = core.calculate_total_ratio(np.linspace(0.0, 180.0, 3600, endpoint=False), parameters)
        spans.append(ratio.max() - ratio.min())
    assert spans[0] > spans[1] > spans[2]


@pytest.mark.parametrize("beta1, beta2", [(10.0, 25.0), (20.0, 35.0), (5.0, 50.0)])
def test_fischer_paul_unequal_angles_minimum_at_zero_relative_phase(beta1, beta2):
    """Fischer & Paul (1991), abstract: with unequal joint angles the output
    fluctuation is minimised, although not eliminated, at zero relative phase.
    DOI: 10.1115/1.2912778 (abstract only; qualitative statement)."""

    theta = np.linspace(0.0, 180.0, 7200, endpoint=False)
    phases = np.arange(0.0, 180.0, 1.0)
    values = [
        core.unevenness_percent(core.double_cardan_ratio(theta, beta1, beta2, phase))
        for phase in phases
    ]
    assert int(np.argmin(values)) == 0  # physical phase 0 = aligned yokes
    assert min(values) > 0.1  # minimised but not eliminated


# ---------------------------------------------------------------------------
# Seherr-Thoss, Schmelz, Aucktor (2006), Universal Joints and Driveshafts,
# 2nd ed., Springer, Sect. 1.2.1-1.2.2 (pp. 5-9), full text read.
# Fischer & Paul (1991), J. Mech. Des. 113(3), 263-271, full text read.
#
# Both sources report the amplitude of the output lead/lag ("cardan error",
# "amplitude of fluctuation") in degrees.  Tolerances:
#   * 0.6 deg for values stated in the text as "about ...";
#   * 0.5 deg for values read from printed curves (the experiment's encoder
#     resolution alone is 0.36 deg, Fischer & Paul p. 270).
# These are low-precision references: they confirm the model and the phase
# convention, not the last digits.
# ---------------------------------------------------------------------------


def _angle_error_amplitudes(betas, phases=()):
    keywords = {f"beta{i + 1}_deg": beta for i, beta in enumerate(betas)}
    keywords.update({f"phi{i + 1}_deg": phase for i, phase in enumerate(phases)})
    parameters = core.CardanParameters(mode=len(betas), **keywords)
    theta = np.linspace(0.0, 360.0, 36001)
    trajectory = core.calculate_kinematic_trajectory(theta, parameters)
    deviation = trajectory.joint_output_angles_deg[-1] - theta
    sampled = 0.5 * (deviation.max() - deviation.min())
    exact = core.exact_speed_ratio_bounds(parameters).angle_error_amplitude_deg
    return sampled, exact


@pytest.mark.parametrize(
    "beta, reported, tolerance",
    [
        (45.0, 10.0, 0.6),  # text p. 6: "a lead and lag of about +-10 deg"
        (30.0, 4.0, 0.5),   # Fig. 1.7a
        (15.0, 1.0, 0.5),   # Fig. 1.7a
    ],
)
def test_seherr_thoss_single_joint_cardan_error(beta, reported, tolerance):
    sampled, exact = _angle_error_amplitudes((beta,))
    assert sampled == pytest.approx(exact, abs=1e-6)  # closed form = trajectory
    assert exact == pytest.approx(reported, abs=tolerance)


@pytest.mark.parametrize("beta1, beta2", [(20.0, 35.0), (35.0, 20.0), (10.0, 44.0)])
def test_seherr_thoss_in_phase_unequal_angles(beta1, beta2):
    """Sect. 1.2.2: with in-phase yokes tan(phi3) = cos(b1)/cos(b2) * tan(phi1);
    with yokes 90 deg out of phase the range is cos(b1)cos(b2) ... 1/(cos b1 cos b2)."""

    c1, c2 = np.cos(np.deg2rad(beta1)), np.cos(np.deg2rad(beta2))
    aligned = core.exact_speed_ratio_bounds(
        core.CardanParameters(mode=2, beta1_deg=beta1, beta2_deg=beta2, phi1_deg=0.0)
    )
    assert aligned.q_max == pytest.approx(max(c1 / c2, c2 / c1), rel=1e-12)
    crossed = core.exact_speed_ratio_bounds(
        core.CardanParameters(mode=2, beta1_deg=beta1, beta2_deg=beta2, phi1_deg=90.0)
    )
    assert crossed.q_max == pytest.approx(1.0 / (c1 * c2), rel=1e-12)
    assert crossed.q_min == pytest.approx(c1 * c2, rel=1e-12)


def test_fischer_paul_45_degree_joints_relative_phase_range():
    """pp. 268 and 270: both joint angles 45 deg; the fluctuation amplitude grows
    from zero at RPA = 0 to "about 20 degrees" at RPA = 90 deg."""

    _, at_zero = _angle_error_amplitudes((45.0, 45.0), (0.0,))
    sampled, at_ninety = _angle_error_amplitudes((45.0, 45.0), (90.0,))
    assert at_zero < 1e-9
    assert sampled == pytest.approx(at_ninety, abs=1e-6)
    assert at_ninety == pytest.approx(20.0, abs=0.6)


@pytest.mark.parametrize(
    "phase_angle, read_from_figure",
    [
        (-20.1, 0.0),  # Fig. 11: flat curve, i.e. the angle of twist is -20.1 deg
        (0.0, 2.9),    # Fig. 11, computed curve
        (30.0, 6.4),   # Fig. 12, computed curve
        (60.0, 8.0),   # Fig. 12, computed curve
    ],
)
def test_fischer_paul_experiment_30_degree_joints(phase_angle, read_from_figure):
    """Figs. 10-12: offset angles both 30 deg, shaft offset 0.867 in.

    Eq. (23): RPA = phase angle - angle of twist.  The twist is not printed,
    but the phase angle -20.1 deg gives a flat response, hence twist = -20.1.
    """

    relative_phase = phase_angle - (-20.1)
    _, amplitude = _angle_error_amplitudes((30.0, 30.0), (relative_phase,))
    assert amplitude == pytest.approx(read_from_figure, abs=0.5)

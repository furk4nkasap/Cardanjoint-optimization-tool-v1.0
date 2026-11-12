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

"""Input validation, 2D/3D geometry consistency and export contracts."""

from __future__ import annotations

import math

import numpy as np
import pytest

import cardan_core as core

P = core.CardanParameters


@pytest.mark.parametrize(
    "keywords",
    [
        {"beta1_deg": float("nan")},
        {"beta1_deg": 90.0},
        {"beta1_deg": -1.0},
        {"beta2_deg": float("inf")},
        {"theta0_deg": float("nan")},
        {"theta0_deg": float("inf")},
        {"phi1_deg": float("nan")},
        {"phi2_deg": float("-inf")},
        {"optimization_step_deg": 0.0},
        {"optimization_step_deg": float("nan")},
        {"mode": 4},
        {"phase_convention": "internal_hooke_reference"},
    ],
)
def test_invalid_inputs_are_rejected_at_construction(keywords):
    with pytest.raises((ValueError, TypeError)):
        P(**keywords)


def test_supported_angle_range_is_accepted():
    for beta in (0.0, 30.0, 60.0, 75.0):
        analysis = core.calculate_analysis(P(mode=3, beta1_deg=beta, beta2_deg=beta, beta3_deg=beta))
        assert math.isfinite(analysis["optimized_metrics"].unevenness_percent)


@pytest.mark.parametrize("phases", [(0.0, 0.0), (30.0, 60.0), (68.21, 16.52), (135.0, 90.0)])
def test_scene_yoke_clocking_equals_entered_physical_phase(phases):
    parameters = P(mode=3, beta1_deg=43.02, beta2_deg=25.26, beta3_deg=47.51,
                   phi1_deg=phases[0], phi2_deg=phases[1])
    scene = core.calculate_kinematic_scene(parameters, theta_deg=np.linspace(0.0, 360.0, 181))
    for joint in range(3):
        dots = np.sum(scene.input_yoke_axes[joint] * scene.output_yoke_axes[joint], axis=1)
        assert np.max(np.abs(dots)) < 1e-12  # cross pins stay perpendicular
    for joint in range(2):
        shaft = scene.geometry.shaft_directions[joint + 1]
        first = scene.output_yoke_axes[joint]
        second = scene.input_yoke_axes[joint + 1]
        angle = np.rad2deg(np.arctan2(np.cross(first, second) @ shaft, np.sum(first * second, axis=1)))
        error = (angle - phases[joint] + 90.0) % 180.0 - 90.0
        assert np.max(np.abs(error)) < 1e-9


def test_scene_shaft_angles_follow_trajectory_and_betas():
    parameters = P(mode=3, beta1_deg=12.0, beta2_deg=25.0, beta3_deg=8.0, phi1_deg=20.0, phi2_deg=70.0)
    geometry = core.calculate_planar_scene_geometry(parameters)
    for index, beta in enumerate(parameters.active_betas):
        cosine = float(geometry.shaft_directions[index] @ geometry.shaft_directions[index + 1])
        assert np.rad2deg(np.arccos(cosine)) == pytest.approx(beta, abs=1e-9)
    assert np.max(np.abs(geometry.shaft_directions[:, 2])) == 0.0  # planar schematic


def test_geometry_plot_does_not_tilt_layout_with_theta0():
    """theta0 is a shaft-rotation reference, not a layout inclination."""

    import matplotlib.pyplot as plt

    def first_segment(theta0):
        figure = core.plot_geometry_2d(P(mode=2, beta1_deg=20.0, beta2_deg=20.0, theta0_deg=theta0))
        line = figure.axes[0].lines[0]
        data = (np.array(line.get_xdata(), dtype=float), np.array(line.get_ydata(), dtype=float))
        plt.close(figure)
        return data

    x0, y0 = first_segment(0.0)
    x1, y1 = first_segment(60.0)
    assert np.allclose(x0, x1) and np.allclose(y0, y1)


def test_payload_round_trip_and_convention_contract():
    parameters = P(mode=3, beta1_deg=11.0, beta2_deg=22.0, beta3_deg=33.0, phi1_deg=44.0, phi2_deg=55.0)
    payload = core.parameters_to_payload(parameters)
    assert payload["angles_unit"] == "degree"
    assert payload["phase_convention"] == "physical_yoke_clocking"
    assert core.parameters_from_payload(payload) == parameters
    with pytest.raises(ValueError):
        core.parameters_from_payload({"parameters": payload["parameters"]})
    legacy = dict(payload["parameters"], phi1_deg=30.0, phi2_deg=60.0)
    converted = core.parameters_from_payload(
        {"parameters": legacy}, legacy_phase_convention="internal_hooke_reference"
    )
    assert (converted.phi1_deg, converted.phi2_deg) == (60.0, 30.0)

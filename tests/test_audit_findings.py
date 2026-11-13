"""Regression tests for the defects reported by the independent v1.5.0 audit.

The audit (kept outside the repository) listed six defects.  Each one was
reproduced on v1.5.0 before the fix; the tests below fail on that version.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

import cardan_core as core
import reference_model as ref

P = core.CardanParameters
S = core.OptimizationSettings


# --- 1. local refinement must not lose the coarse optimum ----------------------

@pytest.mark.parametrize(
    "coarse, local",
    [
        (5.0, 0.3),   # API: step that does not divide the window
        (1.5, 1.0),   # reachable in the app's expert mode
        (2.5, 1.0),   # reachable in the app's expert mode
        (7.5, 0.5),
    ],
)
def test_local_refinement_is_never_worse_than_the_coarse_grid(coarse, local):
    """Equal 30 deg double joint: the coarse grid already finds phi = 0 (U = 0).

    v1.5.0 returned U = 0.10 % (0.3 deg step) and U = 0.50 % (1.0 deg step)
    because the refinement grid did not contain its own centre.
    """

    parameters = P(mode=2, beta1_deg=30, beta2_deg=30, phi1_deg=77, optimization_step_deg=coarse)
    analysis = core.calculate_analysis(
        parameters, optimization_settings=S(method="local_refinement", local_refinement_step_deg=local)
    )
    coarse_value = analysis["coarse_optimization_result"].unevenness_percent
    refined_value = analysis["optimization_result"].unevenness_percent
    assert refined_value <= coarse_value + 1e-12
    assert analysis["optimization_result"].phi1_deg == 0.0


@pytest.mark.parametrize("center, half_width, step", [(0.0, 5.0, 0.3), (37.0, 1.5, 1.0), (179.0, 2.5, 0.7)])
def test_periodic_local_grid_contains_its_centre(center, half_width, step):
    grid = core._periodic_local_grid(center, half_width, step)
    assert np.any(np.isclose(grid, center % 180.0))
    assert np.all((grid >= 0.0) & (grid < 180.0))


# --- 2. revolutions must not be lost on sparse input grids ----------------------

def test_trajectory_keeps_revolutions_on_sparse_grid_with_large_theta0():
    theta = np.array([0.0, 360.0, 720.0])
    trajectory = core.calculate_kinematic_trajectory(theta, P(mode=1, beta1_deg=20, theta0_deg=720.0))
    assert np.allclose(trajectory.joint_input_angles_deg[0], [720.0, 1080.0, 1440.0])
    assert np.allclose(trajectory.joint_output_angles_deg[0], [720.0, 1080.0, 1440.0], atol=1e-9)


@pytest.mark.parametrize("step", [200.0, 270.0, 359.0])
def test_trajectory_output_stays_within_90_deg_of_input_for_any_spacing(step):
    """A Hooke joint never leads or lags by 90 deg or more, whatever the grid."""

    theta = np.arange(0.0, 2000.0, step)
    parameters = P(mode=3, beta1_deg=40, beta2_deg=25, beta3_deg=35, phi1_deg=20, phi2_deg=110)
    trajectory = core.calculate_kinematic_trajectory(theta, parameters)
    for joint in range(3):
        lag = trajectory.joint_output_angles_deg[joint] - trajectory.joint_input_angles_deg[joint]
        assert np.max(np.abs(lag)) < 90.0
    dense = core.calculate_kinematic_trajectory(np.linspace(0.0, 2000.0, 200001), parameters)
    expected = np.interp(theta, dense.input_rotation_deg, dense.joint_output_angles_deg[-1])
    assert np.allclose(trajectory.joint_output_angles_deg[-1], expected, atol=1e-6)


# --- 3. low-level functions validate the joint angle -----------------------------

@pytest.mark.parametrize("beta", [-10.0, 90.0, 100.0, float("nan"), float("inf")])
def test_low_level_functions_reject_invalid_beta(beta):
    with pytest.raises(ValueError):
        core.hooke_speed_ratio(30.0, beta)
    with pytest.raises(ValueError):
        core.hooke_output_angle_rad(0.5, math.radians(beta) if math.isfinite(beta) else beta)


@pytest.mark.parametrize("theta", [float("nan"), float("inf")])
def test_low_level_functions_reject_non_finite_theta(theta):
    with pytest.raises(ValueError):
        core.hooke_speed_ratio(theta, 20.0)


@pytest.mark.parametrize(
    "keywords",
    [
        {"differential_evolution_tolerance": float("nan")},
        {"differential_evolution_absolute_tolerance": float("inf")},
        {"local_refinement_step_deg": float("nan")},
    ],
)
def test_optimization_settings_reject_non_finite_values(keywords):
    with pytest.raises(ValueError):
        S(**keywords)


# --- 4. no cancellation error close to 90 deg ------------------------------------

def test_speed_ratio_near_singular_angle_matches_closed_form():
    """q(theta = 0) = 1 / cos(beta).  v1.5.0 raised ZeroDivisionError here.

    The value is a property of the ideal model close to its singularity; it is
    not an operating recommendation.
    """

    beta = 89.99999
    expected = 1.0 / math.cos(math.radians(beta))
    assert float(core.hooke_speed_ratio(0.0, beta)) == pytest.approx(expected, rel=1e-9)
    assert float(core.hooke_speed_ratio(90.0, beta)) == pytest.approx(1.0 / expected, rel=1e-9)


def test_stable_denominator_is_the_same_function_in_the_working_range():
    theta = np.linspace(0.0, 360.0, 7201)
    for beta in (0.0, 5.0, 25.0, 45.0, 60.0, 75.0):
        radians = np.deg2rad(theta)
        legacy = np.cos(np.deg2rad(beta)) / (1.0 - np.sin(np.deg2rad(beta)) ** 2 * np.cos(radians) ** 2)
        assert np.allclose(core.hooke_speed_ratio(theta, beta), legacy, rtol=1e-12, atol=0.0)


# --- 5. and 6. solver success flag and evaluation count ---------------------------

class _FakeResult:
    def __init__(self, x, fun, success, nfev, nit=1, message="fake"):
        self.x, self.fun, self.success = np.asarray(x, dtype=float), fun, success
        self.nfev, self.nit, self.message = nfev, nit, message


def _forced_solvers(monkeypatch, powell_point, powell_success):
    """DE fails at a good point; Powell 'succeeds' at ``powell_point``."""

    def fake_de(objective, bounds, **_):
        objective([0.0])  # one real call
        return _FakeResult([0.0], 0.0, False, nfev=999)

    def fake_minimize(objective, x0, **_):
        objective(np.asarray(powell_point, dtype=float))  # one real call
        return _FakeResult(powell_point, 0.0, powell_success, nfev=999)

    monkeypatch.setattr(core, "differential_evolution", fake_de)
    monkeypatch.setattr(core, "minimize", fake_minimize)


def test_rejected_powell_candidate_does_not_report_success(monkeypatch):
    """v1.5.0: DE failed, Powell returned a *worse* point and was rejected,
    yet the diagnostics said success = True."""

    _forced_solvers(monkeypatch, powell_point=[60.0], powell_success=True)
    parameters = P(mode=2, beta1_deg=30, beta2_deg=30, phi1_deg=45)
    analysis = core.calculate_analysis(parameters, optimization_settings=S(method="hybrid"))
    assert analysis["optimization_result"].phi1_deg == 0.0  # the DE/coarse point was kept
    assert analysis["optimization_diagnostics"].success is False


def test_accepted_powell_candidate_reports_its_success(monkeypatch):
    def fake_de(objective, bounds, **_):
        objective([60.0])
        return _FakeResult([60.0], 0.0, False, nfev=1)

    def fake_minimize(objective, x0, **_):
        objective(np.array([0.0]))
        return _FakeResult([0.0], 0.0, True, nfev=1)

    monkeypatch.setattr(core, "differential_evolution", fake_de)
    monkeypatch.setattr(core, "minimize", fake_minimize)
    # A coarse step of 180 deg leaves phi = 0 as the only coarse node, so use
    # unequal angles where Powell's point is strictly better than DE's.
    parameters = P(mode=2, beta1_deg=20, beta2_deg=35, phi1_deg=45, optimization_step_deg=7.0)
    analysis = core.calculate_analysis(parameters, optimization_settings=S(method="hybrid"))
    assert analysis["optimization_diagnostics"].success is True


def test_function_evaluations_count_real_objective_calls(monkeypatch):
    """The fake solvers each claim nfev = 999 but call the objective once."""

    _forced_solvers(monkeypatch, powell_point=[60.0], powell_success=True)
    parameters = P(mode=2, beta1_deg=30, beta2_deg=30, phi1_deg=45)
    analysis = core.calculate_analysis(parameters, optimization_settings=S(method="hybrid"))
    coarse = core.phase_combination_count(parameters)
    counted = analysis["optimization_diagnostics"].function_evaluations - coarse
    # 1 (DE) + 1 (Powell) + the comparison calls made by the driver itself.
    assert 2 <= counted <= 8


# --- constructive (search-free) triple optimum -------------------------------------

@pytest.mark.parametrize(
    "betas",
    [
        (0.0, 0.0, 0.0), (0.0, 30.0, 30.0), (30.0, 0.0, 30.0), (30.0, 30.0, 0.0),
        (1e-3, 2e-3, 3e-3), (0.5, 0.5, 0.5), (5.0, 5.0, 59.9), (59.9, 59.9, 59.9),
        (10.0, 50.0, 40.0), (2.0, 3.0, 4.0), (60.0, 1.0, 1.0), (45.0, 45.0, 89.0),
    ],
)
def test_constructive_optimum_attains_the_lower_bound_in_special_cases(betas):
    parameters = P(mode=3, beta1_deg=betas[0], beta2_deg=betas[1], beta3_deg=betas[2])
    optimum = core.exact_phase_optimum(parameters)
    bound = ref.theoretical_minimum_unevenness(betas)
    attained = ref.closed_form_unevenness(betas, (optimum.phi1_deg, optimum.phi2_deg))
    scale = max(1.0, bound)
    assert attained == pytest.approx(bound, abs=1e-9 * scale)
    assert optimum.certified_global
    assert 0.0 <= optimum.phi1_deg < 180.0 and 0.0 <= optimum.phi2_deg < 180.0


def test_constructive_optimum_needs_no_search():
    parameters = P(mode=3, beta1_deg=43.02, beta2_deg=25.26, beta3_deg=47.51)
    optimum = core.exact_phase_optimum(parameters)
    assert optimum.function_evaluations <= 2


@pytest.mark.parametrize("seed", range(20))
def test_two_joint_anisotropy_identity(seed):
    """cosh t = cosh w1 cosh w2 + sinh w1 sinh w2 cos(2a): the relation the
    constructive optimum is built on (hyperbolic law of cosines)."""

    rng = np.random.default_rng(seed)
    beta1, beta2, phase = rng.uniform(0.0, 75.0), rng.uniform(0.0, 75.0), rng.uniform(0.0, 180.0)
    q_min, q_max = ref.closed_form_bounds((beta1, beta2), (phase,))
    w1 = -math.log(math.cos(math.radians(beta1)))
    w2 = -math.log(math.cos(math.radians(beta2)))
    angle = math.radians(phase - 90.0)
    expected = math.cosh(w1) * math.cosh(w2) + math.sinh(w1) * math.sinh(w2) * math.cos(2.0 * angle)
    assert math.cosh(math.log(q_max)) == pytest.approx(expected, rel=1e-12)

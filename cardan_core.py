"""Numerical core for the Cardan Joint Kinematics & Phase Optimization Tool.

The module contains only engineering calculations and Matplotlib figure builders.
It has no Streamlit dependency, which keeps the model testable and reusable.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum, IntEnum
from time import perf_counter
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Arc, Circle
from numpy.typing import ArrayLike, NDArray
from scipy.optimize import differential_evolution, minimize


# API v5 adds fundamental-period reduction for both the input-angle objective
# and phase search domain. Hooke-joint speed response repeats every 180 degrees.
CORE_API_VERSION = 5


class CardanMode(IntEnum):
    SINGLE = 1
    DOUBLE = 2
    TRIPLE = 3


class OptimizationMethod(str, Enum):
    GRID = "grid"
    LOCAL_REFINEMENT = "local_refinement"
    DIFFERENTIAL_EVOLUTION = "differential_evolution"
    HYBRID = "hybrid"


@dataclass(frozen=True, slots=True)
class CardanParameters:
    mode: CardanMode | int = CardanMode.TRIPLE
    beta1_deg: float = 25.0
    beta2_deg: float = 25.0
    beta3_deg: float = 25.0
    phi1_deg: float = 0.0
    phi2_deg: float = 0.0
    theta0_deg: float = 0.0
    optimization_step_deg: float = 5.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "mode", CardanMode(self.mode))

        for beta in self.active_betas:
            if not 0.0 <= beta < 90.0:
                raise ValueError("Active beta angles must satisfy 0 <= beta < 90 degrees.")

        if not 0.0 < float(self.optimization_step_deg) <= KINEMATIC_PERIOD_DEG:
            raise ValueError(
                f"Optimization step must satisfy 0 < step <= {KINEMATIC_PERIOD_DEG:g} degrees."
            )

    @property
    def active_betas(self) -> tuple[float, ...]:
        if self.mode is CardanMode.SINGLE:
            return (float(self.beta1_deg),)
        if self.mode is CardanMode.DOUBLE:
            return (float(self.beta1_deg), float(self.beta2_deg))
        return (
            float(self.beta1_deg),
            float(self.beta2_deg),
            float(self.beta3_deg),
        )

    @property
    def active_phases(self) -> tuple[float, ...]:
        if self.mode is CardanMode.SINGLE:
            return ()
        if self.mode is CardanMode.DOUBLE:
            return (float(self.phi1_deg),)
        return (float(self.phi1_deg), float(self.phi2_deg))


@dataclass(frozen=True, slots=True)
class OptimizationSettings:
    method: OptimizationMethod | str = OptimizationMethod.HYBRID
    local_refinement_step_deg: float = 0.25
    differential_evolution_max_iterations: int = 80
    differential_evolution_population_size: int = 12
    differential_evolution_tolerance: float = 1.0e-7
    differential_evolution_absolute_tolerance: float = 0.0
    random_seed: int = 42
    validation_sample_count: int = 3600
    polish: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "method", OptimizationMethod(self.method))
        if not 0.0 < float(self.local_refinement_step_deg) <= 30.0:
            raise ValueError("Local refinement step must satisfy 0 < step <= 30 degrees.")
        if int(self.differential_evolution_max_iterations) < 1:
            raise ValueError("Differential-evolution iterations must be at least 1.")
        if int(self.differential_evolution_population_size) < 4:
            raise ValueError("Differential-evolution population size must be at least 4.")
        if float(self.differential_evolution_tolerance) < 0.0:
            raise ValueError("Differential-evolution tolerance cannot be negative.")
        if float(self.differential_evolution_absolute_tolerance) < 0.0:
            raise ValueError("Differential-evolution absolute tolerance cannot be negative.")
        if int(self.validation_sample_count) < 360:
            raise ValueError("Validation sample count must be at least 360.")


@dataclass(frozen=True, slots=True)
class CurveMetrics:
    q_mean: float
    q_min: float
    q_max: float
    unevenness_percent: float
    rms_speed_error_percent: float
    maximum_positive_error_percent: float
    maximum_negative_error_percent: float


@dataclass(frozen=True, slots=True)
class OptimizationDiagnostics:
    method: str
    success: bool
    message: str
    function_evaluations: int
    iterations: int
    elapsed_seconds: float
    objective_unevenness_percent: float
    validated_unevenness_percent: float
    validation_delta_percent: float
    validation_sample_count: int
    random_seed: int | None


@dataclass(frozen=True, slots=True)
class OptimizationResult:
    phi1_deg: float | None
    phi2_deg: float | None
    q_best: NDArray[np.float64]
    unevenness_percent: float
    coarse_phi1_deg: float | None = None
    coarse_phi2_deg: float | None = None
    refined: bool = False
    refinement_step_deg: float | None = None
    method: str = OptimizationMethod.GRID.value


@dataclass(frozen=True, slots=True)
class PhaseLandscape:
    phase_values_phi1_deg: NDArray[np.float64]
    unevenness_percent: NDArray[np.float64]
    phase_values_phi2_deg: NDArray[np.float64] | None = None


@dataclass(frozen=True, slots=True)
class KinematicTrajectory:
    input_rotation_deg: NDArray[np.float64]
    joint_input_angles_deg: NDArray[np.float64]
    joint_output_angles_deg: NDArray[np.float64]
    joint_speed_ratios: NDArray[np.float64]
    total_speed_ratio: NDArray[np.float64]

@dataclass(frozen=True, slots=True)
class PlotLabels:
    """Localized text used only by plotting functions."""

    current_curve: str = "Current"
    optimized_curve: str = "Optimized"
    input_rotation_axis: str = "Input shaft rotation angle (deg)"
    velocity_ratio_title: str = "Figure A — Angular Velocity Ratio and Unevenness"
    current_unevenness: str = "Current"
    optimized_unevenness: str = "Optimized"
    status_ok: str = "OK"
    status_warning: str = "Warning"
    optimized_phi1: str = "Optimized φ₁"
    optimized_phi2: str = "Optimized φ₂"
    geometry_title: str = "Figure B — Two-Dimensional Shaft Geometry"
    joint_1_to_2: str = "Joint 1 → Joint 2"
    joint_2_to_3: str = "Joint 2 → Joint 3"
    direction_ccw: str = "CCW"
    direction_cw: str = "CW"
    side_view: str = "side view"
    phase_title: str = "Figure C — Phase (φ)"
    unity_ratio: str = "Constant-speed reference"
    phase_landscape_title: str = "Figure D — Phase Optimization Landscape"
    phase_phi1_axis: str = "φ₁ (deg)"
    phase_phi2_axis: str = "φ₂ (deg)"
    unevenness_axis: str = "Unevenness (%)"
    coarse_optimum: str = "Coarse optimum"
    refined_optimum: str = "Selected optimum"


EPSILON = 1.0e-12
UNEVENNESS_LIMIT_PERCENT = 5.0
FULL_REVOLUTION_DEG = 360.0
KINEMATIC_PERIOD_DEG = 180.0
PLOT_SAMPLE_COUNT = 721
# 360 samples over 180 degrees preserve the previous 0.5-degree objective spacing.
OPTIMIZATION_SAMPLE_COUNT = 360

ORANGE = "#F28E2B"
GREEN = "#59A14F"
BLUE = "#4E79A7"
PURPLE = "#B07AA1"
GRAY = "#9A9A9A"
BLACK = "black"
SHAFT_COLORS = (BLUE, ORANGE, GREEN, PURPLE)

SHAFT_LENGTH = 1.35
BETA_ARC_RADIUS = 0.19
BETA_ARC_OFFSET = 0.20
BETA_ARC_LINEWIDTH = 3.2
BETA_RAY_LINEWIDTH = 2.6
BETA_LABEL_FONTSIZE = 13
BETA_LABEL_PUSH = 0.30
THETA0_FONTSIZE = 11

PHI_RADIUS = 1.30
PHI_ARC_LINEWIDTH = 2.8
C_RING_RADIUS = 1.25
C_RING_LINEWIDTH = 6.0
C_RING_HALF_GAP_DEG = 45.0


def hooke_speed_ratio_rad(
    theta_rad: ArrayLike,
    beta_rad: float,
) -> NDArray[np.float64]:
    theta = np.asarray(theta_rad, dtype=float)
    beta = float(beta_rad)
    denominator = 1.0 - np.sin(beta) ** 2 * np.cos(theta) ** 2

    if np.any(np.abs(denominator) < EPSILON):
        raise ZeroDivisionError("Hooke-joint speed-ratio denominator is too small.")

    return np.asarray(np.cos(beta) / denominator, dtype=float)


def hooke_speed_ratio(
    theta_deg: ArrayLike,
    beta_deg: float,
) -> NDArray[np.float64]:
    return hooke_speed_ratio_rad(
        np.deg2rad(np.asarray(theta_deg, dtype=float)),
        np.deg2rad(float(beta_deg)),
    )


def hooke_output_angle_rad(
    theta_in_rad: ArrayLike,
    beta_rad: float,
) -> NDArray[np.float64]:
    """Return the quadrant-preserving Hooke-joint output angle."""

    theta_in = np.asarray(theta_in_rad, dtype=float)
    cos_beta = np.cos(float(beta_rad))

    if abs(cos_beta) < EPSILON:
        raise ValueError("A beta angle at or near 90 degrees is singular.")

    return np.arctan2(
        np.sin(theta_in),
        cos_beta * np.cos(theta_in),
    )


def single_cardan_ratio(
    theta1_deg: ArrayLike,
    beta1_deg: float = 25.0,
    theta0_deg: float = 0.0,
) -> NDArray[np.float64]:
    theta1_deg = np.asarray(theta1_deg, dtype=float) + float(theta0_deg)
    return hooke_speed_ratio(theta1_deg, beta1_deg)


def double_cardan_ratio(
    theta1_deg: ArrayLike,
    beta1_deg: float = 25.0,
    beta2_deg: float = 25.0,
    phi1_deg: float = 0.0,
    theta0_deg: float = 0.0,
) -> NDArray[np.float64]:
    theta1_rad = np.deg2rad(np.asarray(theta1_deg, dtype=float) + theta0_deg)
    beta1_rad = np.deg2rad(beta1_deg)
    beta2_rad = np.deg2rad(beta2_deg)
    phi1_rad = np.deg2rad(phi1_deg)

    theta2_rad = hooke_output_angle_rad(theta1_rad, beta1_rad)
    theta2_phased_rad = theta2_rad - phi1_rad

    q1 = hooke_speed_ratio_rad(theta1_rad, beta1_rad)
    q2 = hooke_speed_ratio_rad(theta2_phased_rad, beta2_rad)
    return np.asarray(q1 * q2, dtype=float)


def triple_cardan_ratio(
    theta1_deg: ArrayLike,
    beta1_deg: float = 25.0,
    beta2_deg: float = 25.0,
    beta3_deg: float = 25.0,
    phi1_deg: float = 0.0,
    phi2_deg: float = 0.0,
    theta0_deg: float = 0.0,
) -> NDArray[np.float64]:
    theta1_rad = np.deg2rad(np.asarray(theta1_deg, dtype=float) + theta0_deg)
    beta1_rad = np.deg2rad(beta1_deg)
    beta2_rad = np.deg2rad(beta2_deg)
    beta3_rad = np.deg2rad(beta3_deg)
    phi1_rad = np.deg2rad(phi1_deg)
    phi2_rad = np.deg2rad(phi2_deg)

    theta2_rad = hooke_output_angle_rad(theta1_rad, beta1_rad)
    theta2_phased_rad = theta2_rad - phi1_rad

    theta3_rad = hooke_output_angle_rad(theta2_phased_rad, beta2_rad)
    theta3_phased_rad = theta3_rad - phi2_rad

    q1 = hooke_speed_ratio_rad(theta1_rad, beta1_rad)
    q2 = hooke_speed_ratio_rad(theta2_phased_rad, beta2_rad)
    q3 = hooke_speed_ratio_rad(theta3_phased_rad, beta3_rad)
    return np.asarray(q1 * q2 * q3, dtype=float)


def calculate_total_ratio(
    theta_deg: ArrayLike,
    parameters: CardanParameters,
) -> NDArray[np.float64]:
    if parameters.mode is CardanMode.SINGLE:
        return single_cardan_ratio(
            theta_deg,
            beta1_deg=parameters.beta1_deg,
            theta0_deg=parameters.theta0_deg,
        )

    if parameters.mode is CardanMode.DOUBLE:
        return double_cardan_ratio(
            theta_deg,
            beta1_deg=parameters.beta1_deg,
            beta2_deg=parameters.beta2_deg,
            phi1_deg=parameters.phi1_deg,
            theta0_deg=parameters.theta0_deg,
        )

    return triple_cardan_ratio(
        theta_deg,
        beta1_deg=parameters.beta1_deg,
        beta2_deg=parameters.beta2_deg,
        beta3_deg=parameters.beta3_deg,
        phi1_deg=parameters.phi1_deg,
        phi2_deg=parameters.phi2_deg,
        theta0_deg=parameters.theta0_deg,
    )


def calculate_kinematic_trajectory(
    theta_deg: ArrayLike,
    parameters: CardanParameters,
) -> KinematicTrajectory:
    """Return renderer-independent joint angles and speed ratios.

    The arrays follow the same phase convention as the numerical model. Angles
    are unwrapped for animation/export while the recursive calculation retains
    the periodic Hooke-joint relation.
    """

    input_rotation_deg = np.asarray(theta_deg, dtype=float)
    if input_rotation_deg.ndim != 1 or input_rotation_deg.size < 2:
        raise ValueError("theta_deg must be a one-dimensional array with at least two values.")

    betas_rad = np.deg2rad(np.asarray(parameters.active_betas, dtype=float))
    phases_rad = np.deg2rad(np.asarray(parameters.active_phases, dtype=float))
    theta_in_rad = np.deg2rad(input_rotation_deg + float(parameters.theta0_deg))

    joint_inputs: list[NDArray[np.float64]] = []
    joint_outputs: list[NDArray[np.float64]] = []
    joint_ratios: list[NDArray[np.float64]] = []

    for joint_index, beta_rad in enumerate(betas_rad):
        joint_inputs.append(np.rad2deg(np.unwrap(theta_in_rad)))
        q_joint = hooke_speed_ratio_rad(theta_in_rad, float(beta_rad))
        theta_out_rad = hooke_output_angle_rad(theta_in_rad, float(beta_rad))
        joint_outputs.append(np.rad2deg(np.unwrap(theta_out_rad)))
        joint_ratios.append(np.asarray(q_joint, dtype=float))

        if joint_index < phases_rad.size:
            theta_in_rad = theta_out_rad - phases_rad[joint_index]

    joint_speed_ratios = np.vstack(joint_ratios)
    return KinematicTrajectory(
        input_rotation_deg=np.asarray(input_rotation_deg, dtype=float),
        joint_input_angles_deg=np.vstack(joint_inputs),
        joint_output_angles_deg=np.vstack(joint_outputs),
        joint_speed_ratios=joint_speed_ratios,
        total_speed_ratio=np.prod(joint_speed_ratios, axis=0),
    )


def unevenness_percent(
    q: ArrayLike,
    axis: int | None = None,
) -> float | NDArray[np.float64]:
    values = np.asarray(q, dtype=float)
    q_mean = np.mean(values, axis=axis)
    q_range = np.max(values, axis=axis) - np.min(values, axis=axis)
    result = 100.0 * q_range / np.maximum(np.abs(q_mean), EPSILON)

    if np.ndim(result) == 0:
        return float(result)
    return np.asarray(result, dtype=float)


def calculate_curve_metrics(q: ArrayLike) -> CurveMetrics:
    values = np.asarray(q, dtype=float)
    if values.ndim != 1 or values.size < 2:
        raise ValueError("q must be a one-dimensional curve with at least two values.")
    if not np.all(np.isfinite(values)):
        raise ValueError("q contains non-finite values.")

    q_mean = float(np.mean(values))
    q_min = float(np.min(values))
    q_max = float(np.max(values))
    denominator = max(abs(q_mean), EPSILON)
    normalized_error = values / denominator - np.sign(q_mean or 1.0)

    return CurveMetrics(
        q_mean=q_mean,
        q_min=q_min,
        q_max=q_max,
        unevenness_percent=float(100.0 * (q_max - q_min) / denominator),
        rms_speed_error_percent=float(100.0 * np.sqrt(np.mean(normalized_error**2))),
        maximum_positive_error_percent=float(100.0 * (q_max - q_mean) / denominator),
        maximum_negative_error_percent=float(100.0 * (q_min - q_mean) / denominator),
    )


def canonical_phase_deg(value_deg: ArrayLike) -> NDArray[np.float64]:
    """Map phase values to the unique kinematic interval [0, 180)."""

    return np.mod(np.asarray(value_deg, dtype=float), KINEMATIC_PERIOD_DEG)


def create_phase_grid(step_deg: float) -> NDArray[np.float64]:
    """Create unique phase candidates over the 180-degree fundamental period."""

    step_deg = float(step_deg)

    if not 0.0 < step_deg <= KINEMATIC_PERIOD_DEG:
        raise ValueError(
            f"Phase step must satisfy 0 < step <= {KINEMATIC_PERIOD_DEG:g} degrees."
        )

    values = np.arange(0.0, KINEMATIC_PERIOD_DEG, step_deg, dtype=float)
    return values if values.size else np.array([0.0], dtype=float)


def phase_combination_count(parameters: CardanParameters) -> int:
    """Return the number of coarse phase candidates evaluated."""

    if parameters.mode is CardanMode.SINGLE:
        return 0

    candidate_count = int(create_phase_grid(parameters.optimization_step_deg).size)
    return candidate_count if parameters.mode is CardanMode.DOUBLE else candidate_count**2


def _double_landscape(
    parameters: CardanParameters,
    theta_deg: NDArray[np.float64],
    phase_values_deg: NDArray[np.float64],
) -> tuple[OptimizationResult, PhaseLandscape]:
    theta1_rad = np.deg2rad(theta_deg + parameters.theta0_deg)
    beta1_rad = np.deg2rad(parameters.beta1_deg)
    beta2_rad = np.deg2rad(parameters.beta2_deg)

    theta2_rad = hooke_output_angle_rad(theta1_rad, beta1_rad)
    q1 = hooke_speed_ratio_rad(theta1_rad, beta1_rad)

    phi1_rad = np.deg2rad(phase_values_deg)[:, None]
    theta2_phased_rad = theta2_rad[None, :] - phi1_rad
    q2 = hooke_speed_ratio_rad(theta2_phased_rad, beta2_rad)

    q_total = q1[None, :] * q2
    metrics = np.asarray(unevenness_percent(q_total, axis=1), dtype=float)
    best_index = int(np.argmin(metrics))
    best_phi1 = float(phase_values_deg[best_index])

    result = OptimizationResult(
        phi1_deg=best_phi1,
        phi2_deg=None,
        q_best=np.asarray(q_total[best_index], dtype=float),
        unevenness_percent=float(metrics[best_index]),
        coarse_phi1_deg=best_phi1,
    )
    landscape = PhaseLandscape(
        phase_values_phi1_deg=np.asarray(phase_values_deg, dtype=float),
        unevenness_percent=metrics,
    )
    return result, landscape


def _triple_landscape(
    parameters: CardanParameters,
    theta_deg: NDArray[np.float64],
    phi1_values_deg: NDArray[np.float64],
    phi2_values_deg: NDArray[np.float64] | None = None,
) -> tuple[OptimizationResult, PhaseLandscape]:
    if phi2_values_deg is None:
        phi2_values_deg = phi1_values_deg

    theta1_rad = np.deg2rad(theta_deg + parameters.theta0_deg)
    beta1_rad = np.deg2rad(parameters.beta1_deg)
    beta2_rad = np.deg2rad(parameters.beta2_deg)
    beta3_rad = np.deg2rad(parameters.beta3_deg)

    theta2_rad = hooke_output_angle_rad(theta1_rad, beta1_rad)
    q1 = hooke_speed_ratio_rad(theta1_rad, beta1_rad)
    phi1_values_rad = np.deg2rad(phi1_values_deg)
    phi2_values_rad = np.deg2rad(phi2_values_deg)

    metric_matrix = np.empty((phi1_values_deg.size, phi2_values_deg.size), dtype=float)
    best_metric = np.inf
    best_phi1_deg = 0.0
    best_phi2_deg = 0.0
    best_q: NDArray[np.float64] | None = None

    for row, (phi1_deg, phi1_rad) in enumerate(zip(phi1_values_deg, phi1_values_rad)):
        theta2_phased_rad = theta2_rad - phi1_rad
        q2 = hooke_speed_ratio_rad(theta2_phased_rad, beta2_rad)

        theta3_rad = hooke_output_angle_rad(theta2_phased_rad, beta2_rad)
        theta3_phased_rad = theta3_rad[None, :] - phi2_values_rad[:, None]
        q3 = hooke_speed_ratio_rad(theta3_phased_rad, beta3_rad)

        q_total = (q1 * q2)[None, :] * q3
        row_metrics = np.asarray(unevenness_percent(q_total, axis=1), dtype=float)
        metric_matrix[row, :] = row_metrics
        local_index = int(np.argmin(row_metrics))
        local_metric = float(row_metrics[local_index])

        if local_metric < best_metric:
            best_metric = local_metric
            best_phi1_deg = float(phi1_deg)
            best_phi2_deg = float(phi2_values_deg[local_index])
            best_q = np.asarray(q_total[local_index], dtype=float)

    if best_q is None:
        raise RuntimeError("No valid triple-Cardan phase combination was evaluated.")

    result = OptimizationResult(
        phi1_deg=best_phi1_deg,
        phi2_deg=best_phi2_deg,
        q_best=best_q,
        unevenness_percent=best_metric,
        coarse_phi1_deg=best_phi1_deg,
        coarse_phi2_deg=best_phi2_deg,
    )
    landscape = PhaseLandscape(
        phase_values_phi1_deg=np.asarray(phi1_values_deg, dtype=float),
        phase_values_phi2_deg=np.asarray(phi2_values_deg, dtype=float),
        unevenness_percent=metric_matrix,
    )
    return result, landscape


def optimize_phase_with_landscape(
    parameters: CardanParameters,
    theta_grid_deg: ArrayLike,
) -> tuple[OptimizationResult, PhaseLandscape | None]:
    """Generate the deterministic coarse grid and its phase landscape."""

    theta_deg = np.asarray(theta_grid_deg, dtype=float)
    if theta_deg.ndim != 1 or theta_deg.size < 2:
        raise ValueError("theta_grid_deg must be a 1D array with at least two values.")

    if parameters.mode is CardanMode.SINGLE:
        q = calculate_total_ratio(theta_deg, parameters)
        return (
            OptimizationResult(
                phi1_deg=None,
                phi2_deg=None,
                q_best=q,
                unevenness_percent=float(unevenness_percent(q)),
                method=OptimizationMethod.GRID.value,
            ),
            None,
        )

    phase_values_deg = create_phase_grid(parameters.optimization_step_deg)
    if parameters.mode is CardanMode.DOUBLE:
        return _double_landscape(parameters, theta_deg, phase_values_deg)
    return _triple_landscape(parameters, theta_deg, phase_values_deg)


def optimize_phase(
    parameters: CardanParameters,
    theta_grid_deg: ArrayLike,
) -> OptimizationResult:
    result, _ = optimize_phase_with_landscape(parameters, theta_grid_deg)
    return result


def _periodic_local_grid(
    center_deg: float,
    half_width_deg: float,
    step_deg: float,
) -> NDArray[np.float64]:
    if step_deg <= 0.0:
        raise ValueError("Refinement step must be positive.")

    raw = np.arange(
        float(center_deg) - float(half_width_deg),
        float(center_deg) + float(half_width_deg) + 0.5 * float(step_deg),
        float(step_deg),
        dtype=float,
    )
    normalized = canonical_phase_deg(raw)
    return np.unique(np.round(normalized, decimals=10))


def refine_optimization(
    parameters: CardanParameters,
    theta_grid_deg: ArrayLike,
    coarse_result: OptimizationResult,
    refinement_step_deg: float = 0.25,
) -> OptimizationResult:
    """Refine the coarse optimum in a deterministic periodic neighborhood."""

    if parameters.mode is CardanMode.SINGLE:
        return coarse_result
    if coarse_result.phi1_deg is None:
        raise ValueError("A coarse phase optimum is required before refinement.")

    theta_deg = np.asarray(theta_grid_deg, dtype=float)
    half_width = float(parameters.optimization_step_deg)
    phi1_values = _periodic_local_grid(
        coarse_result.phi1_deg,
        half_width,
        float(refinement_step_deg),
    )

    local_parameters = replace(parameters, optimization_step_deg=float(refinement_step_deg))
    if parameters.mode is CardanMode.DOUBLE:
        refined, _ = _double_landscape(local_parameters, theta_deg, phi1_values)
    else:
        if coarse_result.phi2_deg is None:
            raise ValueError("Triple-Cardan refinement requires both coarse phases.")
        phi2_values = _periodic_local_grid(
            coarse_result.phi2_deg,
            half_width,
            float(refinement_step_deg),
        )
        refined, _ = _triple_landscape(local_parameters, theta_deg, phi1_values, phi2_values)

    return replace(
        refined,
        coarse_phi1_deg=coarse_result.phi1_deg,
        coarse_phi2_deg=coarse_result.phi2_deg,
        refined=True,
        refinement_step_deg=float(refinement_step_deg),
        method=OptimizationMethod.LOCAL_REFINEMENT.value,
    )


def _build_continuous_objective(
    parameters: CardanParameters,
    theta_deg: NDArray[np.float64],
):
    """Build a low-allocation continuous phase objective closure."""

    theta1_rad = np.deg2rad(theta_deg + float(parameters.theta0_deg))
    beta1_rad = np.deg2rad(float(parameters.beta1_deg))
    theta2_rad = hooke_output_angle_rad(theta1_rad, beta1_rad)
    q1 = hooke_speed_ratio_rad(theta1_rad, beta1_rad)
    beta2_rad = np.deg2rad(float(parameters.beta2_deg))

    if parameters.mode is CardanMode.DOUBLE:
        def objective(candidate: ArrayLike) -> float:
            phi1_rad = np.deg2rad(float(canonical_phase_deg(np.asarray(candidate, dtype=float)[0])))
            q2 = hooke_speed_ratio_rad(theta2_rad - phi1_rad, beta2_rad)
            return float(unevenness_percent(q1 * q2))

        return objective

    beta3_rad = np.deg2rad(float(parameters.beta3_deg))

    def objective(candidate: ArrayLike) -> float:
        phases = canonical_phase_deg(candidate)
        phi1_rad, phi2_rad = np.deg2rad(phases)
        theta2_phased_rad = theta2_rad - phi1_rad
        q2 = hooke_speed_ratio_rad(theta2_phased_rad, beta2_rad)
        theta3_rad = hooke_output_angle_rad(theta2_phased_rad, beta2_rad)
        q3 = hooke_speed_ratio_rad(theta3_rad - phi2_rad, beta3_rad)
        return float(unevenness_percent(q1 * q2 * q3))

    return objective


def _phase_vector_from_result(result: OptimizationResult) -> NDArray[np.float64]:
    if result.phi1_deg is None:
        return np.empty(0, dtype=float)
    if result.phi2_deg is None:
        return np.array([result.phi1_deg], dtype=float)
    return np.array([result.phi1_deg, result.phi2_deg], dtype=float)


def _result_from_phase_vector(
    parameters: CardanParameters,
    theta_deg: NDArray[np.float64],
    phase_vector_deg: ArrayLike,
    coarse_result: OptimizationResult,
    method: OptimizationMethod,
) -> OptimizationResult:
    phases = canonical_phase_deg(phase_vector_deg)
    candidate_parameters = replace(
        parameters,
        phi1_deg=float(phases[0]),
        phi2_deg=float(phases[1]) if parameters.mode is CardanMode.TRIPLE else parameters.phi2_deg,
    )
    q = calculate_total_ratio(theta_deg, candidate_parameters)
    return OptimizationResult(
        phi1_deg=float(phases[0]),
        phi2_deg=float(phases[1]) if parameters.mode is CardanMode.TRIPLE else None,
        q_best=np.asarray(q, dtype=float),
        unevenness_percent=float(unevenness_percent(q)),
        coarse_phi1_deg=coarse_result.phi1_deg,
        coarse_phi2_deg=coarse_result.phi2_deg,
        refined=method is not OptimizationMethod.GRID,
        refinement_step_deg=None,
        method=method.value,
    )


def optimize_continuous_phase(
    parameters: CardanParameters,
    theta_grid_deg: ArrayLike,
    coarse_result: OptimizationResult,
    settings: OptimizationSettings,
) -> tuple[OptimizationResult, OptimizationDiagnostics]:
    """Run global differential evolution and optional continuous Powell polishing."""

    if parameters.mode is CardanMode.SINGLE:
        raise ValueError("Continuous phase optimization requires at least two joints.")

    theta_deg = np.asarray(theta_grid_deg, dtype=float)
    objective = _build_continuous_objective(parameters, theta_deg)
    bounds = [(0.0, KINEMATIC_PERIOD_DEG)] * (1 if parameters.mode is CardanMode.DOUBLE else 2)
    x0 = _phase_vector_from_result(coarse_result)
    started = perf_counter()

    de_result = differential_evolution(
        objective,
        bounds=bounds,
        strategy="best1bin",
        maxiter=int(settings.differential_evolution_max_iterations),
        popsize=int(settings.differential_evolution_population_size),
        tol=float(settings.differential_evolution_tolerance),
        atol=float(settings.differential_evolution_absolute_tolerance),
        rng=np.random.default_rng(int(settings.random_seed)),
        polish=bool(settings.polish),
        init="latinhypercube",
        x0=x0,
        workers=1,
        updating="immediate",
    )

    best_vector = canonical_phase_deg(de_result.x)
    best_value = float(objective(best_vector))
    function_evaluations = int(de_result.nfev)
    iterations = int(de_result.nit)
    success = bool(de_result.success)
    messages = [f"Differential evolution: {de_result.message}"]

    coarse_vector = _phase_vector_from_result(coarse_result)
    coarse_value = float(objective(coarse_vector))
    if coarse_value < best_value:
        best_vector = coarse_vector
        best_value = coarse_value
        messages.append("The deterministic coarse candidate was retained because it was better.")

    if settings.method is OptimizationMethod.HYBRID:
        powell_result = minimize(
            objective,
            x0=best_vector,
            method="Powell",
            bounds=bounds,
            options={
                "xtol": 1.0e-9,
                "ftol": 1.0e-11,
                "maxiter": 500,
                "disp": False,
            },
        )
        function_evaluations += int(getattr(powell_result, "nfev", 0))
        iterations += int(getattr(powell_result, "nit", 0))
        powell_vector = canonical_phase_deg(powell_result.x)
        powell_value = float(objective(powell_vector))
        if powell_value < best_value:
            best_vector = powell_vector
            best_value = powell_value
        success = success or bool(powell_result.success)
        messages.append(f"Powell polishing: {powell_result.message}")

    method = settings.method
    result = _result_from_phase_vector(
        parameters,
        theta_deg,
        best_vector,
        coarse_result,
        method,
    )
    elapsed = perf_counter() - started
    diagnostics = OptimizationDiagnostics(
        method=method.value,
        success=success,
        message=" ".join(messages),
        function_evaluations=function_evaluations,
        iterations=iterations,
        elapsed_seconds=float(elapsed),
        objective_unevenness_percent=float(result.unevenness_percent),
        validated_unevenness_percent=float(result.unevenness_percent),
        validation_delta_percent=0.0,
        validation_sample_count=int(settings.validation_sample_count),
        random_seed=int(settings.random_seed),
    )
    return result, diagnostics


def apply_optimized_phases(
    parameters: CardanParameters,
    result: OptimizationResult,
) -> CardanParameters:
    return replace(
        parameters,
        phi1_deg=parameters.phi1_deg if result.phi1_deg is None else result.phi1_deg,
        phi2_deg=parameters.phi2_deg if result.phi2_deg is None else result.phi2_deg,
    )


def _resolve_optimization_settings(
    optimization_settings: OptimizationSettings | None,
    refine: bool | None,
    refinement_step_deg: float,
) -> OptimizationSettings:
    if optimization_settings is not None:
        return optimization_settings
    if refine is True:
        return OptimizationSettings(
            method=OptimizationMethod.LOCAL_REFINEMENT,
            local_refinement_step_deg=float(refinement_step_deg),
        )
    if refine is False:
        return OptimizationSettings(method=OptimizationMethod.GRID)
    return OptimizationSettings()


def calculate_analysis(
    parameters: CardanParameters,
    *,
    optimization_settings: OptimizationSettings | None = None,
    refine: bool | None = None,
    refinement_step_deg: float = 0.25,
) -> dict[str, Any]:
    """Calculate curves, coarse landscape, selected optimum, and validation."""

    settings = _resolve_optimization_settings(
        optimization_settings,
        refine,
        refinement_step_deg,
    )
    theta_plot_deg = np.linspace(0.0, FULL_REVOLUTION_DEG, PLOT_SAMPLE_COUNT, endpoint=True)
    theta_metric_deg = np.linspace(
        0.0,
        KINEMATIC_PERIOD_DEG,
        OPTIMIZATION_SAMPLE_COUNT,
        endpoint=False,
    )
    theta_validation_deg = np.linspace(
        0.0,
        KINEMATIC_PERIOD_DEG,
        int(settings.validation_sample_count),
        endpoint=False,
    )

    q_current_plot = calculate_total_ratio(theta_plot_deg, parameters)
    q_current_metric = calculate_total_ratio(theta_metric_deg, parameters)

    coarse_started = perf_counter()
    coarse_result, phase_landscape = optimize_phase_with_landscape(parameters, theta_metric_deg)
    coarse_elapsed = perf_counter() - coarse_started

    if parameters.mode is CardanMode.SINGLE:
        optimization_result = coarse_result
        diagnostics = OptimizationDiagnostics(
            method=OptimizationMethod.GRID.value,
            success=True,
            message="Phase optimization is not applicable to a single Cardan joint.",
            function_evaluations=0,
            iterations=0,
            elapsed_seconds=float(coarse_elapsed),
            objective_unevenness_percent=float(coarse_result.unevenness_percent),
            validated_unevenness_percent=float(coarse_result.unevenness_percent),
            validation_delta_percent=0.0,
            validation_sample_count=int(settings.validation_sample_count),
            random_seed=None,
        )
    elif settings.method is OptimizationMethod.GRID:
        optimization_result = coarse_result
        diagnostics = OptimizationDiagnostics(
            method=settings.method.value,
            success=True,
            message="Deterministic coarse phase grid completed.",
            function_evaluations=phase_combination_count(parameters),
            iterations=0,
            elapsed_seconds=float(coarse_elapsed),
            objective_unevenness_percent=float(coarse_result.unevenness_percent),
            validated_unevenness_percent=float(coarse_result.unevenness_percent),
            validation_delta_percent=0.0,
            validation_sample_count=int(settings.validation_sample_count),
            random_seed=None,
        )
    elif settings.method is OptimizationMethod.LOCAL_REFINEMENT:
        local_started = perf_counter()
        optimization_result = refine_optimization(
            parameters,
            theta_metric_deg,
            coarse_result,
            refinement_step_deg=float(settings.local_refinement_step_deg),
        )
        local_elapsed = perf_counter() - local_started
        local_phi1_count = int(
            _periodic_local_grid(
                float(coarse_result.phi1_deg),
                float(parameters.optimization_step_deg),
                float(settings.local_refinement_step_deg),
            ).size
        )
        local_evaluations = (
            local_phi1_count
            if parameters.mode is CardanMode.DOUBLE
            else local_phi1_count
            * int(
                _periodic_local_grid(
                    float(coarse_result.phi2_deg),
                    float(parameters.optimization_step_deg),
                    float(settings.local_refinement_step_deg),
                ).size
            )
        )
        diagnostics = OptimizationDiagnostics(
            method=settings.method.value,
            success=True,
            message="Deterministic coarse grid and periodic local refinement completed.",
            function_evaluations=phase_combination_count(parameters) + local_evaluations,
            iterations=0,
            elapsed_seconds=float(coarse_elapsed + local_elapsed),
            objective_unevenness_percent=float(optimization_result.unevenness_percent),
            validated_unevenness_percent=float(optimization_result.unevenness_percent),
            validation_delta_percent=0.0,
            validation_sample_count=int(settings.validation_sample_count),
            random_seed=None,
        )
    else:
        optimization_result, diagnostics = optimize_continuous_phase(
            parameters,
            theta_metric_deg,
            coarse_result,
            settings,
        )
        diagnostics = replace(
            diagnostics,
            function_evaluations=(
                diagnostics.function_evaluations + phase_combination_count(parameters)
            ),
            elapsed_seconds=float(diagnostics.elapsed_seconds + coarse_elapsed),
        )

    optimized_parameters = apply_optimized_phases(parameters, optimization_result)
    q_optimized_plot = calculate_total_ratio(theta_plot_deg, optimized_parameters)
    q_optimized_metric = calculate_total_ratio(theta_metric_deg, optimized_parameters)

    q_current_validation = calculate_total_ratio(theta_validation_deg, parameters)
    q_optimized_validation = calculate_total_ratio(theta_validation_deg, optimized_parameters)
    current_metrics = calculate_curve_metrics(q_current_validation)
    optimized_metrics = calculate_curve_metrics(q_optimized_validation)
    diagnostics = replace(
        diagnostics,
        validated_unevenness_percent=float(optimized_metrics.unevenness_percent),
        validation_delta_percent=float(
            optimized_metrics.unevenness_percent - diagnostics.objective_unevenness_percent
        ),
    )

    return {
        "theta_plot_deg": theta_plot_deg,
        "theta_metric_deg": theta_metric_deg,
        "q_current_plot": q_current_plot,
        "q_optimized_plot": q_optimized_plot,
        "q_current_metric": q_current_metric,
        "q_optimized_metric": q_optimized_metric,
        "current_unevenness": current_metrics.unevenness_percent,
        "current_metrics": current_metrics,
        "optimized_metrics": optimized_metrics,
        "coarse_optimization_result": coarse_result,
        "optimization_result": optimization_result,
        "optimization_settings": settings,
        "optimization_diagnostics": diagnostics,
        "optimized_parameters": optimized_parameters,
        "phase_landscape": phase_landscape,
        "current_trajectory": calculate_kinematic_trajectory(theta_plot_deg, parameters),
        "optimized_trajectory": calculate_kinematic_trajectory(
            theta_plot_deg,
            optimized_parameters,
        ),
    }


def plot_velocity_ratio(
    parameters: CardanParameters,
    labels: PlotLabels | None = None,
    analysis: dict[str, Any] | None = None,
) -> tuple[Figure, OptimizationResult, float]:
    """Plot current and optimized velocity ratios without repeating analysis."""

    plot_labels = PlotLabels() if labels is None else labels
    analysis_data = calculate_analysis(parameters) if analysis is None else analysis

    theta_plot_deg = np.asarray(analysis_data["theta_plot_deg"], dtype=float)
    q_current_plot = np.asarray(analysis_data["q_current_plot"], dtype=float)
    q_optimized_plot = np.asarray(analysis_data["q_optimized_plot"], dtype=float)
    current_metrics = analysis_data["current_metrics"]
    optimized_metrics = analysis_data["optimized_metrics"]
    result = analysis_data["optimization_result"]

    fig, ax = plt.subplots(figsize=(11.5, 4.6))
    ax.plot(theta_plot_deg, q_current_plot, lw=2.6, label=plot_labels.current_curve)
    ax.plot(
        theta_plot_deg,
        q_optimized_plot,
        lw=2.6,
        linestyle="--",
        label=plot_labels.optimized_curve,
    )
    ax.axhline(1.0, lw=1.2, linestyle=":", color=GRAY, label=plot_labels.unity_ratio)

    ax.set_xlabel(plot_labels.input_rotation_axis)
    ax.set_ylabel(r"$q_{\mathrm{total}}=\omega_{\mathrm{out}}/\omega_{\mathrm{in}}$")
    ax.set_title(plot_labels.velocity_ratio_title)
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")

    status = (
        plot_labels.status_ok
        if current_metrics.unevenness_percent <= UNEVENNESS_LIMIT_PERCENT
        else plot_labels.status_warning
    )
    annotation = (
        f"{plot_labels.current_unevenness} Δq/q̄ = "
        f"{current_metrics.unevenness_percent:.3f}% → {status}\n"
        f"{plot_labels.optimized_unevenness} Δq/q̄ = "
        f"{optimized_metrics.unevenness_percent:.3f}%\n"
    )

    if parameters.mode is CardanMode.DOUBLE:
        annotation += f"{plot_labels.optimized_phi1} = {result.phi1_deg:.2f}°"
    elif parameters.mode is CardanMode.TRIPLE:
        annotation += (
            f"{plot_labels.optimized_phi1} = {result.phi1_deg:.2f}°, "
            f"{plot_labels.optimized_phi2} = {result.phi2_deg:.2f}°"
        )

    ax.text(
        0.02,
        0.98,
        annotation,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=10.5,
        bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="0.35", alpha=0.95),
    )

    fig.tight_layout()
    return fig, result, float(current_metrics.unevenness_percent)


def plot_phase_landscape(
    parameters: CardanParameters,
    landscape: PhaseLandscape | None,
    result: OptimizationResult,
    labels: PlotLabels | None = None,
) -> Figure | None:
    """Plot the coarse optimization objective versus phase candidate(s)."""

    if parameters.mode is CardanMode.SINGLE or landscape is None:
        return None

    plot_labels = PlotLabels() if labels is None else labels
    fig, ax = plt.subplots(figsize=(10.8, 5.0))

    if parameters.mode is CardanMode.DOUBLE:
        x = landscape.phase_values_phi1_deg
        y = landscape.unevenness_percent
        ax.plot(x, y, lw=2.3)
        if result.coarse_phi1_deg is not None:
            coarse_index = int(np.argmin(np.abs(x - result.coarse_phi1_deg)))
            ax.scatter(
                [x[coarse_index]],
                [y[coarse_index]],
                s=70,
                marker="o",
                label=plot_labels.coarse_optimum,
                zorder=4,
            )
        if result.method != OptimizationMethod.GRID.value and result.phi1_deg is not None:
            ax.scatter(
                [result.phi1_deg],
                [result.unevenness_percent],
                s=95,
                marker="*",
                label=plot_labels.refined_optimum,
                zorder=5,
            )
        ax.set_xlabel(plot_labels.phase_phi1_axis)
        ax.set_ylabel(plot_labels.unevenness_axis)
        ax.set_xlim(0.0, KINEMATIC_PERIOD_DEG)
        ax.grid(True, alpha=0.25)
        ax.legend(loc="best")
    else:
        phi1 = landscape.phase_values_phi1_deg
        phi2 = landscape.phase_values_phi2_deg
        if phi2 is None:
            raise ValueError("Triple-Cardan landscape is missing φ₂ values.")
        image = ax.imshow(
            landscape.unevenness_percent.T,
            origin="lower",
            aspect="auto",
            extent=(0.0, KINEMATIC_PERIOD_DEG, 0.0, KINEMATIC_PERIOD_DEG),
            interpolation="nearest",
        )
        colorbar = fig.colorbar(image, ax=ax)
        colorbar.set_label(plot_labels.unevenness_axis)
        if result.coarse_phi1_deg is not None and result.coarse_phi2_deg is not None:
            ax.scatter(
                [result.coarse_phi1_deg],
                [result.coarse_phi2_deg],
                s=70,
                marker="o",
                facecolors="none",
                edgecolors="white",
                linewidths=1.8,
                label=plot_labels.coarse_optimum,
            )
        if (
            result.method != OptimizationMethod.GRID.value
            and result.phi1_deg is not None
            and result.phi2_deg is not None
        ):
            ax.scatter(
                [result.phi1_deg],
                [result.phi2_deg],
                s=110,
                marker="*",
                color="white",
                edgecolors="black",
                linewidths=0.8,
                label=plot_labels.refined_optimum,
            )
        ax.set_xlabel(plot_labels.phase_phi1_axis)
        ax.set_ylabel(plot_labels.phase_phi2_axis)
        ax.legend(loc="best")

    ax.set_title(plot_labels.phase_landscape_title)
    fig.tight_layout()
    return fig


def rotate_vector_2d(
    vector: ArrayLike,
    angle_deg: float,
) -> NDArray[np.float64]:
    angle_rad = np.deg2rad(float(angle_deg))
    cos_angle = np.cos(angle_rad)
    sin_angle = np.sin(angle_rad)
    x_value, y_value = np.asarray(vector, dtype=float)

    return np.array(
        [
            cos_angle * x_value - sin_angle * y_value,
            sin_angle * x_value + cos_angle * y_value,
        ]
    )


def draw_beta_angle(
    ax: Axes,
    origin: ArrayLike,
    reference_vector: ArrayLike,
    target_vector: ArrayLike,
    label: str,
    color: str = BLACK,
) -> None:
    origin = np.asarray(origin, dtype=float)
    reference = np.asarray(reference_vector, dtype=float)
    target = np.asarray(target_vector, dtype=float)

    reference /= np.linalg.norm(reference)
    target /= np.linalg.norm(target)

    angle_1 = np.degrees(np.arctan2(reference[1], reference[0]))
    angle_2 = np.degrees(np.arctan2(target[1], target[0]))
    angle_difference = (angle_2 - angle_1 + 180.0) % 360.0 - 180.0

    arc_radius = BETA_ARC_RADIUS + BETA_ARC_OFFSET
    ray_length = arc_radius + 0.15
    reference_end = origin + ray_length * reference
    target_end = origin + ray_length * target

    ax.plot(
        [origin[0], reference_end[0]],
        [origin[1], reference_end[1]],
        lw=BETA_RAY_LINEWIDTH,
        color=color,
        solid_capstyle="round",
    )
    ax.plot(
        [origin[0], target_end[0]],
        [origin[1], target_end[1]],
        lw=BETA_RAY_LINEWIDTH,
        color=color,
        solid_capstyle="round",
    )

    ax.add_patch(
        Arc(
            (origin[0], origin[1]),
            2.0 * arc_radius,
            2.0 * arc_radius,
            theta1=angle_1,
            theta2=angle_1 + angle_difference,
            lw=BETA_ARC_LINEWIDTH,
            color=color,
        )
    )

    middle_angle = np.deg2rad(angle_1 + 0.5 * angle_difference)
    label_radius = arc_radius + BETA_LABEL_PUSH
    ax.text(
        origin[0] + label_radius * np.cos(middle_angle),
        origin[1] + label_radius * np.sin(middle_angle),
        label,
        fontsize=BETA_LABEL_FONTSIZE,
        color=color,
        ha="center",
        va="center",
    )


def plot_geometry_2d(
    parameters: CardanParameters,
    labels: PlotLabels | None = None,
) -> Figure:
    """Plot the schematic shaft geometry with a localized title."""

    plot_labels = PlotLabels() if labels is None else labels
    fig, ax = plt.subplots(figsize=(8.2, 3.2))
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(plot_labels.geometry_title, fontsize=13)

    directions = [rotate_vector_2d([1.0, 0.0], parameters.theta0_deg)]
    for beta_deg in parameters.active_betas:
        directions.append(rotate_vector_2d(directions[-1], beta_deg))

    points = [np.array([0.0, 0.0])]
    for direction in directions:
        points.append(points[-1] + SHAFT_LENGTH * direction)

    for index in range(len(directions)):
        ax.plot(
            [points[index][0], points[index + 1][0]],
            [points[index][1], points[index + 1][1]],
            lw=7.0,
            color=SHAFT_COLORS[index],
            solid_capstyle="round",
        )

    beta_labels = ("β₁", "β₂", "β₃")
    for index in range(len(parameters.active_betas)):
        draw_beta_angle(
            ax=ax,
            origin=points[index + 1],
            reference_vector=directions[index],
            target_vector=directions[index + 1],
            label=beta_labels[index],
        )

    minimum_y = min(point[1] for point in points)
    ax.text(
        points[0][0],
        minimum_y - 0.70,
        f"θ₀ = {parameters.theta0_deg:.0f}°",
        fontsize=THETA0_FONTSIZE,
        color=BLACK,
        ha="left",
        va="top",
    )

    ax.relim()
    ax.autoscale_view()
    fig.tight_layout()
    return fig


def signed_phase_angle(phi_deg: float) -> float:
    normalized_phi = float(phi_deg) % 360.0
    return normalized_phi if normalized_phi <= 180.0 else normalized_phi - 360.0


def draw_end_view(
    ax: Axes,
    phi_deg: float,
    title: str,
    color: str,
    labels: PlotLabels | None = None,
) -> None:
    ax.set_aspect("equal")
    ax.axis("off")

    plot_labels = PlotLabels() if labels is None else labels
    normalized_phi = float(phi_deg) % 360.0
    signed_phi = signed_phase_angle(normalized_phi)
    direction = plot_labels.direction_ccw if signed_phi >= 0.0 else plot_labels.direction_cw

    ax.add_patch(Circle((0.0, 0.0), PHI_RADIUS, fill=False, lw=2.2, ec=color))
    ax.plot([-PHI_RADIUS, PHI_RADIUS], [0.0, 0.0], lw=2.0, color=color)

    angle_rad = np.deg2rad(signed_phi)
    ax.plot(
        [0.0, PHI_RADIUS * np.cos(angle_rad)],
        [0.0, PHI_RADIUS * np.sin(angle_rad)],
        lw=2.0,
        color=color,
    )

    arc_angles = np.deg2rad(np.linspace(0.0, signed_phi, 120))
    ax.plot(
        0.95 * PHI_RADIUS * np.cos(arc_angles),
        0.95 * PHI_RADIUS * np.sin(arc_angles),
        lw=PHI_ARC_LINEWIDTH,
        color=color,
    )

    ax.text(
        0.0,
        1.85,
        f"{title}: φ = {normalized_phi:.0f}° ({direction})",
        fontsize=12,
        ha="left",
        va="bottom",
        color=BLACK,
    )
    ax.set_xlim(-2.2, 2.2)
    ax.set_ylim(-2.2, 2.2)


def create_c_ring_points(
    vertical_scale: float,
    mirrored: bool = False,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    angles = np.linspace(
        np.deg2rad(C_RING_HALF_GAP_DEG),
        np.deg2rad(360.0 - C_RING_HALF_GAP_DEG),
        260,
    )
    horizontal_sign = -1.0 if mirrored else 1.0

    return (
        horizontal_sign * C_RING_RADIUS * np.cos(angles),
        C_RING_RADIUS * float(vertical_scale) * np.sin(angles),
    )


def draw_side_view(
    ax: Axes,
    phi_deg: float,
    title: str,
    left_c_color: str = GRAY,
    shaft_color: str = BLACK,
    right_c_color: str = GRAY,
    labels: PlotLabels | None = None,
) -> None:
    plot_labels = PlotLabels() if labels is None else labels
    ax.set_aspect("equal")
    ax.axis("off")

    phi = float(phi_deg) % 360.0
    depth_factor = abs(np.sin(np.deg2rad(phi)))
    vertical_scale = max(np.cos(np.deg2rad(90.0 * depth_factor)), 0.02)
    shaft_length = 4.0

    ax.plot(
        [0.0, shaft_length],
        [0.0, 0.0],
        lw=6.0,
        color=shaft_color,
        solid_capstyle="round",
    )

    left_x, left_y = create_c_ring_points(1.0, mirrored=True)
    left_center = -0.85 * C_RING_RADIUS
    ax.plot(
        left_center + left_x,
        left_y,
        lw=C_RING_LINEWIDTH,
        color=left_c_color,
        solid_capstyle="round",
    )

    right_x, right_y = create_c_ring_points(vertical_scale)
    right_center = shaft_length + 0.85 * C_RING_RADIUS
    ax.plot(
        right_center + right_x,
        right_y,
        lw=C_RING_LINEWIDTH,
        color=right_c_color,
        solid_capstyle="round",
    )

    ax.text(
        0.0,
        1.90,
        f"{title} ({plot_labels.side_view})",
        fontsize=12,
        color=BLACK,
    )
    ax.text(0.0, 1.55, f"φ = {phi:.0f}°", fontsize=11, color=BLACK)
    ax.set_xlim(left_center - C_RING_RADIUS - 0.6, right_center + C_RING_RADIUS + 1.4)
    ax.set_ylim(-2.2, 2.2)


def plot_phase_figure(
    parameters: CardanParameters,
    labels: PlotLabels | None = None,
) -> Figure | None:
    """Plot end and side phase views with localized annotations."""

    if parameters.mode is CardanMode.SINGLE:
        return None

    plot_labels = PlotLabels() if labels is None else labels
    rows = 1 if parameters.mode is CardanMode.DOUBLE else 2
    fig = plt.figure(figsize=(10.8, 3.8 * rows))
    grid = fig.add_gridspec(rows, 2, width_ratios=[1.15, 0.85])

    end_ax_1 = fig.add_subplot(grid[0, 0])
    side_ax_1 = fig.add_subplot(grid[0, 1])
    draw_end_view(
        end_ax_1,
        parameters.phi1_deg,
        plot_labels.joint_1_to_2,
        ORANGE,
        labels=plot_labels,
    )
    draw_side_view(
        side_ax_1,
        parameters.phi1_deg,
        plot_labels.joint_1_to_2,
        left_c_color=BLUE,
        shaft_color=ORANGE,
        right_c_color=GREEN,
        labels=plot_labels,
    )

    if parameters.mode is CardanMode.TRIPLE:
        end_ax_2 = fig.add_subplot(grid[1, 0])
        side_ax_2 = fig.add_subplot(grid[1, 1])
        draw_end_view(
            end_ax_2,
            parameters.phi2_deg,
            plot_labels.joint_2_to_3,
            GREEN,
            labels=plot_labels,
        )
        draw_side_view(
            side_ax_2,
            parameters.phi2_deg,
            plot_labels.joint_2_to_3,
            left_c_color=ORANGE,
            shaft_color=GREEN,
            right_c_color=PURPLE,
            labels=plot_labels,
        )

    fig.suptitle(plot_labels.phase_title, fontsize=15, fontweight="bold", y=0.98)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.96))
    return fig

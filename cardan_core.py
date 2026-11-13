"""Numerical core for the Cardan Joint Kinematics & Phase Optimization Tool.

The module contains only engineering calculations and Matplotlib figure builders.
It has no Streamlit dependency, which keeps the model testable and reusable.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum, IntEnum
import math
from time import perf_counter
from typing import Any, Mapping

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Arc, Circle
from numpy.typing import ArrayLike, NDArray
from scipy.optimize import differential_evolution, least_squares, minimize


# Public release and API contract. Every public phase value uses physical yoke
# clocking: 0 deg = aligned yokes on the shared shaft and 90 deg = perpendicular
# yokes. The analytical Hooke-equation reference is private to this module.
TOOL_VERSION = "1.5.1"
CORE_API_VERSION = 10
PARAMETER_SCHEMA_VERSION = 2
ANGLE_UNIT = "degree"


class CardanMode(IntEnum):
    SINGLE = 1
    DOUBLE = 2
    TRIPLE = 3


class OptimizationMethod(str, Enum):
    GRID = "grid"
    LOCAL_REFINEMENT = "local_refinement"
    DIFFERENTIAL_EVOLUTION = "differential_evolution"
    HYBRID = "hybrid"
    # Closed-form objective (no angular sampling) with a certified optimum.
    EXACT = "exact"


class PhaseConvention(str, Enum):
    """Explicit phase-reference labels for files and external integrations."""

    PHYSICAL_YOKE_CLOCKING = "physical_yoke_clocking"
    INTERNAL_HOOKE_REFERENCE = "internal_hooke_reference"


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
    phase_convention: PhaseConvention | str = PhaseConvention.PHYSICAL_YOKE_CLOCKING

    def __post_init__(self) -> None:
        object.__setattr__(self, "mode", CardanMode(self.mode))
        convention = PhaseConvention(self.phase_convention)
        if convention is not PhaseConvention.PHYSICAL_YOKE_CLOCKING:
            raise ValueError(
                "CardanParameters accepts only physical yoke clocking. "
                "Convert internal Hooke-reference phases before construction."
            )
        object.__setattr__(self, "phase_convention", convention)
        for name in (
            "beta1_deg", "beta2_deg", "beta3_deg",
            "phi1_deg", "phi2_deg", "theta0_deg", "optimization_step_deg",
        ):
            if not math.isfinite(float(getattr(self, name))):
                raise ValueError(f"{name} must be a finite number.")
        # 180 degrees is physically equivalent to 0 degrees for an undirected
        # yoke axis. Canonicalising here prevents duplicate external states.
        object.__setattr__(self, "phi1_deg", float(self.phi1_deg) % 180.0)
        object.__setattr__(self, "phi2_deg", float(self.phi2_deg) % 180.0)

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
        for name in (
            "local_refinement_step_deg",
            "differential_evolution_tolerance",
            "differential_evolution_absolute_tolerance",
        ):
            if not math.isfinite(float(getattr(self, name))):
                raise ValueError(f"{name} must be a finite number.")
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
class ExactSpeedBounds:
    """Closed-form extremes of the total speed ratio over one revolution."""

    q_min: float
    q_max: float
    unevenness_percent: float
    # Amplitude of the output lead/lag relative to the input ("cardan error").
    angle_error_amplitude_deg: float = 0.0


@dataclass(frozen=True, slots=True)
class ExactOptimum:
    """Phase optimum of the closed-form objective.

    ``lower_bound_percent`` is a rigorous bound valid for every phase choice.
    ``certified_global`` is True when the attained value meets that bound, which
    proves global optimality independently of the search that produced it.
    """

    phi1_deg: float | None
    phi2_deg: float | None
    unevenness_percent: float
    lower_bound_percent: float
    certified_global: bool
    function_evaluations: int = 0


@dataclass(frozen=True, slots=True)
class ToleranceSensitivity:
    """Worst closed-form unevenness inside symmetric assembly tolerances.

    All values are maxima over a regular grid of the tolerance box (grid
    spacing = tolerance / 10 for phases, tolerance / 2 for joint angles).
    """

    phase_tolerance_deg: float
    beta_tolerance_deg: float
    nominal_unevenness_percent: float
    worst_phase_unevenness_percent: float
    worst_beta_unevenness_percent: float
    worst_combined_unevenness_percent: float


@dataclass(frozen=True, slots=True)
class DiscretePhaseOption:
    phi1_deg: float
    phi2_deg: float | None
    unevenness_percent: float


@dataclass(frozen=True, slots=True)
class DiscretePhaseOptimum:
    """Best phase pair that a splined connection can actually realise."""

    tooth_count_1: int
    tooth_count_2: int | None
    best: DiscretePhaseOption
    options: tuple[DiscretePhaseOption, ...]
    continuous_optimum_percent: float


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
class PlanarSceneGeometry:
    """Canonical planar shaft geometry used by the schematic 3D viewer."""

    shaft_points: NDArray[np.float64]
    shaft_directions: NDArray[np.float64]
    joint_centers: NDArray[np.float64]
    joint_plane_normals: NDArray[np.float64]
    shaft_length: float


@dataclass(frozen=True, slots=True)
class KinematicScene:
    """Renderer-independent poses for shafts, yokes, and universal-joint crosses."""

    input_rotation_deg: NDArray[np.float64]
    geometry: PlanarSceneGeometry
    shaft_rotation_angles_deg: NDArray[np.float64]
    input_yoke_axes: NDArray[np.float64]
    output_yoke_axes: NDArray[np.float64]
    shaft_quaternions_wxyz: NDArray[np.float64]
    input_yoke_quaternions_wxyz: NDArray[np.float64]
    output_yoke_quaternions_wxyz: NDArray[np.float64]
    cross_quaternions_wxyz: NDArray[np.float64]

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
# Below this unevenness (in percent) a configuration is treated as constant
# velocity for reporting purposes; a percentage reduction is then undefined.
NEGLIGIBLE_UNEVENNESS_PERCENT = 1.0e-9
# Tolerance (percentage points) used to certify a global optimum against the
# rigorous lower bound and to decide that a candidate does not improve.
OPTIMALITY_TOLERANCE_PERCENT = 1.0e-7
UNEVENNESS_LIMIT_PERCENT = 5.0
BETA_INFORMATION_THRESHOLD_DEG = 30.0
BETA_WARNING_THRESHOLD_DEG = 45.0
UI_BETA_MAX_DEG = 60.0
FULL_REVOLUTION_DEG = 360.0
KINEMATIC_PERIOD_DEG = 180.0
PLOT_SAMPLE_COUNT = 721
# 360 samples over 180 degrees preserve the previous 0.5-degree objective spacing.
OPTIMIZATION_SAMPLE_COUNT = 360


def physical_phase_to_model_phase_deg(value_deg: ArrayLike) -> NDArray[np.float64]:
    """Convert physical yoke clocking to the internal Hooke-angle reference.

    Public/user-facing convention:
        0 deg  -> adjacent yokes on the shared shaft are aligned.
        90 deg -> adjacent yokes on the shared shaft are perpendicular.

    The analytical recurrence used by this model has a 90-degree shifted
    reference, so the conversion is (90 - phi_physical) modulo 180 degrees.
    """

    values = np.asarray(value_deg, dtype=float)
    return np.mod(90.0 - values, KINEMATIC_PERIOD_DEG)


def model_phase_to_physical_phase_deg(value_deg: ArrayLike) -> NDArray[np.float64]:
    """Convert the internal Hooke-angle reference to physical yoke clocking.

    The transform is its own inverse over the 180-degree fundamental interval.
    """

    values = np.asarray(value_deg, dtype=float)
    return np.mod(90.0 - values, KINEMATIC_PERIOD_DEG)


def parameters_to_dict(parameters: CardanParameters) -> dict[str, Any]:
    """Return a JSON-safe public parameter dictionary.

    Internal Hooke-reference phases are deliberately never exposed here.
    """

    return {
        "mode": int(parameters.mode),
        "beta1_deg": float(parameters.beta1_deg),
        "beta2_deg": float(parameters.beta2_deg),
        "beta3_deg": float(parameters.beta3_deg),
        "phi1_deg": float(parameters.phi1_deg),
        "phi2_deg": float(parameters.phi2_deg),
        "theta0_deg": float(parameters.theta0_deg),
        "optimization_step_deg": float(parameters.optimization_step_deg),
    }


def parameters_to_payload(parameters: CardanParameters) -> dict[str, Any]:
    """Create a versioned, unit-labelled parameter payload for JSON/API use."""

    return {
        "schema_version": PARAMETER_SCHEMA_VERSION,
        "tool_version": TOOL_VERSION,
        "angles_unit": ANGLE_UNIT,
        "phase_convention": PhaseConvention.PHYSICAL_YOKE_CLOCKING.value,
        "parameters": parameters_to_dict(parameters),
    }


def parameters_from_payload(
    payload: Mapping[str, Any],
    *,
    legacy_phase_convention: PhaseConvention | str | None = None,
) -> CardanParameters:
    """Validate and construct public parameters from an external payload.

    A payload without ``phase_convention`` is rejected unless the caller
    explicitly supplies ``legacy_phase_convention``. No phase convention is
    guessed, preventing silent 90-degree offsets in imported files.
    """

    if not isinstance(payload, Mapping):
        raise TypeError("Parameter payload must be a mapping.")
    schema_version = payload.get("schema_version")
    if schema_version is not None and int(schema_version) != PARAMETER_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported parameter schema version: {schema_version!r}; "
            f"expected {PARAMETER_SCHEMA_VERSION}."
        )
    angle_unit = payload.get("angles_unit", ANGLE_UNIT)
    if angle_unit != ANGLE_UNIT:
        raise ValueError(f"Unsupported angle unit: {angle_unit!r}; expected 'degree'.")

    raw_convention = payload.get("phase_convention")
    if raw_convention is None:
        if legacy_phase_convention is None:
            raise ValueError(
                "Missing phase_convention. Supply an explicit legacy phase "
                "convention instead of guessing the file reference."
            )
        convention = PhaseConvention(legacy_phase_convention)
    else:
        convention = PhaseConvention(raw_convention)

    raw_parameters = payload.get("parameters", payload)
    if not isinstance(raw_parameters, Mapping):
        raise TypeError("The 'parameters' entry must be a mapping.")
    values = dict(raw_parameters)
    values.pop("phase_convention", None)

    if convention is PhaseConvention.INTERNAL_HOOKE_REFERENCE:
        for key in ("phi1_deg", "phi2_deg"):
            if key in values:
                values[key] = float(model_phase_to_physical_phase_deg(values[key]))

    values["phase_convention"] = PhaseConvention.PHYSICAL_YOKE_CLOCKING
    return CardanParameters(**values)


def maximum_active_beta_deg(parameters: CardanParameters) -> float:
    """Return the largest active misalignment angle for UI risk messaging."""

    return max(parameters.active_betas, default=0.0)

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


def _validated_beta_rad(beta_rad: float) -> float:
    beta = float(beta_rad)
    if not math.isfinite(beta) or not 0.0 <= beta < 0.5 * math.pi:
        raise ValueError("beta must satisfy 0 <= beta < 90 degrees.")
    return beta


def _validated_theta_rad(theta_rad: ArrayLike) -> NDArray[np.float64]:
    theta = np.asarray(theta_rad, dtype=float)
    if not np.all(np.isfinite(theta)):
        raise ValueError("Shaft angles must be finite.")
    return theta


def hooke_speed_ratio_rad(
    theta_rad: ArrayLike,
    beta_rad: float,
) -> NDArray[np.float64]:
    theta = _validated_theta_rad(theta_rad)
    cos_beta = math.cos(_validated_beta_rad(beta_rad))
    # sin^2(theta) + cos^2(beta) cos^2(theta) equals 1 - sin^2(beta) cos^2(theta)
    # but has no cancellation close to beta = 90 deg, theta = 0.
    denominator = np.sin(theta) ** 2 + (cos_beta * np.cos(theta)) ** 2
    return np.asarray(cos_beta / denominator, dtype=float)


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

    theta_in = _validated_theta_rad(theta_in_rad)
    cos_beta = math.cos(_validated_beta_rad(beta_rad))
    return np.arctan2(
        np.sin(theta_in),
        cos_beta * np.cos(theta_in),
    )


# ---------------------------------------------------------------------------
# Closed-form (sampling-free) evaluation
# ---------------------------------------------------------------------------
#
# Writing the shaft angle as the direction of v = (sin(theta), cos(theta)),
# one Hooke joint is the linear map diag(1, cos(beta)) and a yoke phase is a
# plane rotation.  The whole chain is therefore one 2x2 matrix M and
#
#     d(theta_out)/d(theta_in) = det(M) / |M v|^2 .
#
# Its extremes are the ratio of the singular values of M:
#     q_max = s1 / s2,  q_min = s2 / s1,  mean(q) = 1.
# With  D = hypot(m11 - m22, m12 + m21) = s1 - s2  and
#       S = hypot(m11 + m22, m12 - m21) = s1 + s2  (det(M) > 0)
# the unevenness is  U = 100 * D * S / det(M)  without cancellation error.
# The derivation is documented in docs/model_assumptions.md and verified in
# docs/validation_report.md.


def _composite_matrix_entries(
    cos_betas: tuple[float, ...],
    psi1_rad: ArrayLike = 0.0,
    psi2_rad: ArrayLike = 0.0,
) -> tuple[Any, Any, Any, Any, float]:
    """Entries of the composite map for model phases (broadcastable arrays)."""

    c1 = float(cos_betas[0])
    shape = np.broadcast(np.asarray(psi1_rad), np.asarray(psi2_rad)).shape
    one = np.ones(shape, dtype=float)
    m11, m12, m21, m22 = one, 0.0 * one, 0.0 * one, c1 * one
    determinant = c1
    for cosine_beta, psi in zip(cos_betas[1:], (psi1_rad, psi2_rad)):
        cosine, sine = np.cos(psi), np.sin(psi)
        r11, r12 = cosine * m11 - sine * m21, cosine * m12 - sine * m22
        r21, r22 = sine * m11 + cosine * m21, sine * m12 + cosine * m22
        m11, m12 = r11, r12
        m21, m22 = float(cosine_beta) * r21, float(cosine_beta) * r22
        determinant *= float(cosine_beta)
    return m11, m12, m21, m22, float(determinant)


def _cos_betas(parameters: CardanParameters) -> tuple[float, ...]:
    return tuple(float(np.cos(np.deg2rad(beta))) for beta in parameters.active_betas)


def exact_unevenness_grid(
    parameters: CardanParameters,
    phi1_deg: ArrayLike = 0.0,
    phi2_deg: ArrayLike = 0.0,
) -> NDArray[np.float64]:
    """Closed-form unevenness (%) for arrays of physical phase candidates."""

    psi1 = np.deg2rad(physical_phase_to_model_phase_deg(phi1_deg))
    psi2 = np.deg2rad(physical_phase_to_model_phase_deg(phi2_deg))
    m11, m12, m21, m22, determinant = _composite_matrix_entries(
        _cos_betas(parameters), psi1, psi2
    )
    difference = np.hypot(m11 - m22, m12 + m21)
    total = np.hypot(m11 + m22, m12 - m21)
    return np.asarray(100.0 * difference * total / determinant, dtype=float)


def exact_speed_ratio_bounds(parameters: CardanParameters) -> ExactSpeedBounds:
    """Exact q_min, q_max and unevenness of the entered configuration.

    The result does not depend on theta0 or on any angular sampling grid.
    """

    phases = tuple(parameters.active_phases) + (0.0, 0.0)
    psi = np.deg2rad(physical_phase_to_model_phase_deg(phases[:2]))
    m11, m12, m21, m22, determinant = _composite_matrix_entries(
        _cos_betas(parameters), float(psi[0]), float(psi[1])
    )
    difference = float(np.hypot(m11 - m22, m12 + m21))
    total = float(np.hypot(m11 + m22, m12 - m21))
    q_max = (total + difference) / (total - difference)
    # The chain is equivalent to tan(theta_out) = kappa * tan(theta_in) up to
    # constant shifts, so max|theta_out - theta_in| = atan((kappa-1)/(2 sqrt(kappa)))
    # = atan((s1 - s2) / (2 sqrt(det))).
    angle_error = math.degrees(math.atan(difference / (2.0 * math.sqrt(determinant))))
    return ExactSpeedBounds(
        q_min=float(1.0 / q_max),
        q_max=float(q_max),
        unevenness_percent=float(100.0 * difference * total / determinant),
        angle_error_amplitude_deg=float(angle_error),
    )


def minimum_unevenness_lower_bound_percent(parameters: CardanParameters) -> float:
    """Rigorous lower bound of the unevenness over all phase choices.

    The condition number is sub-multiplicative, kappa(AB) <= kappa(A) kappa(B),
    hence ln kappa(chain) >= l_max - (sum of the other l_i) with
    l_i = ln(1 / cos(beta_i)).  A non-positive right-hand side means that
    exact constant velocity is not excluded.
    """

    lengths = sorted(-math.log(value) for value in _cos_betas(parameters))
    residual = max(0.0, lengths[-1] - sum(lengths[:-1]))
    return float(200.0 * math.sinh(residual))


def reduction_percent(current_percent: float, optimized_percent: float) -> float | None:
    """Relative unevenness reduction, or None when the baseline is ~zero.

    A percentage of a vanishing baseline is numerically meaningless, so it is
    reported as undefined instead of being divided.
    """

    current = float(current_percent)
    optimized = float(optimized_percent)
    if not current > NEGLIGIBLE_UNEVENNESS_PERCENT:
        return None
    return float(max(0.0, 100.0 * (current - optimized) / current))


def _constructive_triple_phases_deg(betas_deg: tuple[float, ...]) -> tuple[float, float]:
    """Physical phases of a global optimum for three joints, without a search.

    With w_i = -ln(cos(beta_i)) the anisotropy t of the first two joints obeys
    the hyperbolic law of cosines

        cosh t = cosh w1 cosh w2 + sinh w1 sinh w2 cos(2 a1),

    so the first phase can set t to any value in [|w1 - w2|, w1 + w2].  t is
    chosen as close to w3 as that interval allows, and the second phase turns
    the major axis of the first two joints onto the axis the third joint
    compresses.  The remaining anisotropy is |t - w3|, which equals the lower
    bound max(0, 2 max(w) - sum(w)).  The construction and its proof were
    contributed by an independent audit of v1.5.0; see docs/model_assumptions.md.
    """

    beta = np.deg2rad(np.asarray(betas_deg, dtype=float))
    # log1p keeps small angles accurate, where cos(beta) rounds to 1.
    w = -np.log1p(-2.0 * np.sin(0.5 * beta) ** 2)
    target = float(np.clip(w[2], abs(w[0] - w[1]), w[0] + w[1]))
    if w[0] == 0.0 or w[1] == 0.0:
        first = 0.0
    else:
        delta = float(w[0] - w[1])
        # cosh(target) - cosh(delta) written as a product: no cancellation.
        cos_double = (
            2.0 * math.sinh(0.5 * (target + delta)) * math.sinh(0.5 * (target - delta))
            / (math.sinh(float(w[0])) * math.sinh(float(w[1])))
            - 1.0
        )
        first = 0.5 * math.acos(min(1.0, max(-1.0, cos_double)))
    cosine, sine = math.cos(first), math.sin(first)
    # In this helper the joint acts as diag(cos(beta), 1) on (cos, sin).
    pair = (
        np.diag([math.cos(beta[1]), 1.0])
        @ np.array([[cosine, -sine], [sine, cosine]])
        @ np.diag([math.cos(beta[0]), 1.0])
    )
    left, _, _ = np.linalg.svd(pair)
    second = -math.atan2(left[1, 0], left[0, 0])
    phases = []
    for angle in (first, second):
        phase = (math.degrees(angle) + 90.0) % KINEMATIC_PERIOD_DEG
        if phase < 1.0e-9 or KINEMATIC_PERIOD_DEG - phase < 1.0e-9:
            phase = 0.0
        phases.append(float(phase))
    return phases[0], phases[1]


def exact_phase_optimum(parameters: CardanParameters) -> ExactOptimum:
    """Minimise the closed-form unevenness over the physical yoke phases.

    Double joint: aligned yokes (phi = 0) are always optimal in the planar
    model, with residual kappa = cos(beta_small) / cos(beta_large).
    Triple joint: the optimum is constructed without a search (see
    ``_constructive_triple_phases_deg``).  It attains the rigorous lower
    bound, which proves that it is global.  A Levenberg-Marquardt search on
    the closed-form objective remains as a fallback.
    """

    lower_bound = minimum_unevenness_lower_bound_percent(parameters)
    if parameters.mode is CardanMode.SINGLE:
        value = exact_speed_ratio_bounds(parameters).unevenness_percent
        return ExactOptimum(None, None, value, lower_bound, True, 1)

    if parameters.mode is CardanMode.DOUBLE:
        value = float(exact_unevenness_grid(parameters, 0.0))
        certified = value <= lower_bound + OPTIMALITY_TOLERANCE_PERCENT
        return ExactOptimum(0.0, None, value, lower_bound, bool(certified), 1)

    constructive = _constructive_triple_phases_deg(parameters.active_betas)
    value = float(exact_unevenness_grid(parameters, constructive[0], constructive[1]))
    if value <= lower_bound + OPTIMALITY_TOLERANCE_PERCENT:
        return ExactOptimum(constructive[0], constructive[1], value, lower_bound, True, 1)

    # Fallback, not reached in the supported range: numerical search on the
    # closed-form objective (kept in case the construction loses precision).
    cos_betas = _cos_betas(parameters)

    def residual(model_phases_rad: ArrayLike) -> NDArray[np.float64]:
        # |residual| = s1 - s2.  Solving it as a least-squares problem keeps
        # full precision when exact constant velocity (residual = 0) exists.
        psi1, psi2 = np.asarray(model_phases_rad, dtype=float)
        m11, m12, m21, m22, _ = _composite_matrix_entries(cos_betas, psi1, psi2)
        return np.array([float(m11 - m22), float(m12 + m21)])

    nodes = np.deg2rad(np.arange(0.0, KINEMATIC_PERIOD_DEG, 5.0))
    psi1_grid, psi2_grid = np.meshgrid(nodes, nodes, indexing="ij")
    m11, m12, m21, m22, _ = _composite_matrix_entries(cos_betas, psi1_grid, psi2_grid)
    landscape = m11 * m11 + m12 * m12 + m21 * m21 + m22 * m22
    evaluations = int(landscape.size)

    candidates: list[tuple[float, float, float]] = []
    for flat_index in np.argsort(landscape, axis=None)[:6]:
        row, column = np.unravel_index(int(flat_index), landscape.shape)
        solution = least_squares(
            residual,
            x0=np.array([nodes[row], nodes[column]]),
            method="lm",
            xtol=1.0e-15,
            ftol=1.0e-15,
            gtol=1.0e-15,
        )
        evaluations += int(solution.nfev)
        physical = model_phase_to_physical_phase_deg(np.rad2deg(solution.x))
        physical = np.where(KINEMATIC_PERIOD_DEG - physical < 1.0e-9, 0.0, physical)
        physical = np.where(physical < 1.0e-9, 0.0, physical)
        value = float(exact_unevenness_grid(parameters, physical[0], physical[1]))
        candidates.append((value, float(physical[0]), float(physical[1])))
        if value <= lower_bound + 0.01 * OPTIMALITY_TOLERANCE_PERCENT:
            break  # the rigorous bound is attained: no better phase pair exists

    best_value = min(item[0] for item in candidates)
    # Mirror-image optima are equivalent; pick the smallest phases for determinism.
    equivalent = [
        item for item in candidates
        if item[0] <= best_value + 0.01 * OPTIMALITY_TOLERANCE_PERCENT
    ]
    value, phi1, phi2 = min(equivalent, key=lambda item: (round(item[1], 6), round(item[2], 6)))
    certified = value <= lower_bound + OPTIMALITY_TOLERANCE_PERCENT
    return ExactOptimum(phi1, phi2, value, lower_bound, bool(certified), evaluations)


# ---------------------------------------------------------------------------
# Assembly tolerances and discrete (spline) phase choices
# ---------------------------------------------------------------------------

_PHASE_TOLERANCE_NODES = 21  # spacing = tolerance / 10
_BETA_TOLERANCE_NODES = 5  # spacing = tolerance / 2
_BETA_TOLERANCE_UPPER_DEG = 89.0


def tolerance_sensitivity(
    parameters: CardanParameters,
    phase_tolerance_deg: float = 1.0,
    beta_tolerance_deg: float = 1.0,
) -> ToleranceSensitivity:
    """Worst unevenness when phases and joint angles deviate from nominal.

    Phases vary within +-phase_tolerance_deg and every active joint angle
    within +-beta_tolerance_deg (clipped to [0, 89] deg).  The closed-form
    unevenness is evaluated on a regular grid of that box, which contains the
    nominal point and all corners.
    """

    phase_tolerance = float(phase_tolerance_deg)
    beta_tolerance = float(beta_tolerance_deg)
    for name, value in (("phase", phase_tolerance), ("beta", beta_tolerance)):
        if not math.isfinite(value) or value < 0.0:
            raise ValueError(f"The {name} tolerance must be a finite, non-negative angle.")

    nominal = exact_speed_ratio_bounds(parameters).unevenness_percent
    joint_count = int(parameters.mode)

    phase_offsets = phase_tolerance * np.linspace(-1.0, 1.0, _PHASE_TOLERANCE_NODES)
    if joint_count == 1 or phase_tolerance == 0.0:
        phi1_grid = np.asarray(parameters.phi1_deg, dtype=float)
        phi2_grid = np.asarray(parameters.phi2_deg, dtype=float)
    elif joint_count == 2:
        phi1_grid = parameters.phi1_deg + phase_offsets
        phi2_grid = np.asarray(parameters.phi2_deg, dtype=float)
    else:
        phi1_grid, phi2_grid = np.meshgrid(
            parameters.phi1_deg + phase_offsets,
            parameters.phi2_deg + phase_offsets,
            indexing="ij",
        )

    def worst_over_phases(candidate: CardanParameters) -> float:
        return float(np.max(exact_unevenness_grid(candidate, phi1_grid, phi2_grid)))

    worst_phase = worst_over_phases(parameters)

    beta_names = ("beta1_deg", "beta2_deg", "beta3_deg")[:joint_count]
    if beta_tolerance == 0.0:
        beta_offsets = np.array([0.0])
    else:
        beta_offsets = beta_tolerance * np.linspace(-1.0, 1.0, _BETA_TOLERANCE_NODES)
    axes = [
        np.unique(np.clip(float(getattr(parameters, name)) + beta_offsets, 0.0, _BETA_TOLERANCE_UPPER_DEG))
        for name in beta_names
    ]
    worst_beta = nominal
    worst_combined = worst_phase
    for combination in np.array(np.meshgrid(*axes, indexing="ij")).reshape(joint_count, -1).T:
        candidate = replace(parameters, **dict(zip(beta_names, (float(x) for x in combination))))
        worst_beta = max(worst_beta, exact_speed_ratio_bounds(candidate).unevenness_percent)
        worst_combined = max(worst_combined, worst_over_phases(candidate))

    return ToleranceSensitivity(
        phase_tolerance_deg=phase_tolerance,
        beta_tolerance_deg=beta_tolerance,
        nominal_unevenness_percent=float(nominal),
        worst_phase_unevenness_percent=float(worst_phase),
        worst_beta_unevenness_percent=float(worst_beta),
        worst_combined_unevenness_percent=float(max(worst_combined, worst_beta)),
    )


def _validated_tooth_count(value: Any) -> int:
    if isinstance(value, bool) or float(value) != int(value) or int(value) < 1:
        raise ValueError("A spline tooth count must be a positive integer.")
    return int(value)


def discrete_phase_values_deg(tooth_count: int) -> tuple[float, ...]:
    """Distinct yoke phases reachable by re-indexing a spline with N teeth.

    Tooth index 0 is taken as the aligned position (phase 0).  Moving by one
    tooth turns the yoke by 360/N; a yoke axis is undirected, so values are
    reduced modulo 180 degrees.
    """

    count = _validated_tooth_count(tooth_count)
    step = FULL_REVOLUTION_DEG / count
    values = {round((index * step) % KINEMATIC_PERIOD_DEG, 9) for index in range(count)}
    values = {0.0 if KINEMATIC_PERIOD_DEG - value < 1.0e-9 else value for value in values}
    return tuple(sorted(values))


def discrete_phase_optimum(
    parameters: CardanParameters,
    tooth_count_1: int,
    tooth_count_2: int | None = None,
) -> DiscretePhaseOptimum:
    """Exhaustive closed-form search over the phases a spline can realise."""

    if parameters.mode is CardanMode.SINGLE:
        raise ValueError("Discrete phase selection requires at least two joints.")

    values_1 = np.array(discrete_phase_values_deg(tooth_count_1))
    count_1 = _validated_tooth_count(tooth_count_1)
    continuous = exact_phase_optimum(parameters).unevenness_percent

    if parameters.mode is CardanMode.DOUBLE:
        metrics = exact_unevenness_grid(parameters, values_1)
        options = [
            DiscretePhaseOption(float(phi1), None, float(value))
            for phi1, value in zip(values_1, metrics)
        ]
        count_2 = None
    else:
        count_2 = _validated_tooth_count(count_1 if tooth_count_2 is None else tooth_count_2)
        values_2 = np.array(discrete_phase_values_deg(count_2))
        grid_1, grid_2 = np.meshgrid(values_1, values_2, indexing="ij")
        metrics = exact_unevenness_grid(parameters, grid_1, grid_2)
        options = [
            DiscretePhaseOption(float(phi1), float(phi2), float(value))
            for phi1, phi2, value in zip(grid_1.ravel(), grid_2.ravel(), metrics.ravel())
        ]

    # Mirror-image options are equivalent; rounding makes the tie-break deterministic.
    options.sort(
        key=lambda item: (round(item.unevenness_percent, 9), item.phi1_deg, item.phi2_deg or 0.0)
    )
    return DiscretePhaseOptimum(
        tooth_count_1=count_1,
        tooth_count_2=count_2,
        best=options[0],
        options=tuple(options),
        continuous_optimum_percent=float(continuous),
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
    phi1_model_rad = np.deg2rad(
        float(physical_phase_to_model_phase_deg(phi1_deg))
    )

    theta2_rad = hooke_output_angle_rad(theta1_rad, beta1_rad)
    theta2_phased_rad = theta2_rad - phi1_model_rad

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
    phi_model_rad = np.deg2rad(
        physical_phase_to_model_phase_deg([phi1_deg, phi2_deg])
    )
    phi1_model_rad, phi2_model_rad = phi_model_rad

    theta2_rad = hooke_output_angle_rad(theta1_rad, beta1_rad)
    theta2_phased_rad = theta2_rad - phi1_model_rad

    theta3_rad = hooke_output_angle_rad(theta2_phased_rad, beta2_rad)
    theta3_phased_rad = theta3_rad - phi2_model_rad

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

    Public phase inputs use physical yoke clocking (0 deg aligned, 90 deg
    perpendicular). They are converted to the shifted analytical reference only
    inside the recursive calculation. Angles are unwrapped for animation/export.
    """

    input_rotation_deg = np.asarray(theta_deg, dtype=float)
    if input_rotation_deg.ndim != 1 or input_rotation_deg.size < 2:
        raise ValueError("theta_deg must be a one-dimensional array with at least two values.")

    betas_rad = np.deg2rad(np.asarray(parameters.active_betas, dtype=float))
    phases_model_rad = np.deg2rad(
        physical_phase_to_model_phase_deg(parameters.active_phases)
    )
    theta_in_rad = np.deg2rad(input_rotation_deg + float(parameters.theta0_deg))

    joint_inputs: list[NDArray[np.float64]] = []
    joint_outputs: list[NDArray[np.float64]] = []
    joint_ratios: list[NDArray[np.float64]] = []

    for joint_index, beta_rad in enumerate(betas_rad):
        joint_inputs.append(np.rad2deg(theta_in_rad))
        q_joint = hooke_speed_ratio_rad(theta_in_rad, float(beta_rad))
        # A Hooke joint leads or lags by less than 90 deg, so the output is the
        # input plus the wrapped difference.  Unlike np.unwrap this does not
        # depend on the sampling and keeps whole revolutions on sparse grids.
        difference = hooke_output_angle_rad(theta_in_rad, float(beta_rad)) - theta_in_rad
        theta_out_rad = theta_in_rad + np.arctan2(np.sin(difference), np.cos(difference))
        joint_outputs.append(np.rad2deg(theta_out_rad))
        joint_ratios.append(np.asarray(q_joint, dtype=float))

        if joint_index < phases_model_rad.size:
            theta_in_rad = theta_out_rad - phases_model_rad[joint_index]

    joint_speed_ratios = np.vstack(joint_ratios)
    return KinematicTrajectory(
        input_rotation_deg=np.asarray(input_rotation_deg, dtype=float),
        joint_input_angles_deg=np.vstack(joint_inputs),
        joint_output_angles_deg=np.vstack(joint_outputs),
        joint_speed_ratios=joint_speed_ratios,
        total_speed_ratio=np.prod(joint_speed_ratios, axis=0),
    )



def _normalise_vector(vector: ArrayLike, *, fallback: ArrayLike | None = None) -> NDArray[np.float64]:
    values = np.asarray(vector, dtype=float)
    norm = float(np.linalg.norm(values))
    if norm < EPSILON:
        if fallback is None:
            raise ValueError("Cannot normalise a near-zero vector.")
        values = np.asarray(fallback, dtype=float)
        norm = float(np.linalg.norm(values))
        if norm < EPSILON:
            raise ValueError("Fallback vector is also near zero.")
    return np.asarray(values / norm, dtype=float)


def _rotate_vector_series(
    base_vector: ArrayLike,
    axis: ArrayLike,
    angles_rad: ArrayLike,
) -> NDArray[np.float64]:
    """Rotate one vector about a fixed unit axis for a series of angles."""

    base = _normalise_vector(base_vector)
    axis_unit = _normalise_vector(axis)
    angles = np.asarray(angles_rad, dtype=float)
    cosine = np.cos(angles)[:, None]
    sine = np.sin(angles)[:, None]
    cross_term = np.cross(axis_unit, base)
    dot_term = float(np.dot(axis_unit, base))
    rotated = (
        base[None, :] * cosine
        + cross_term[None, :] * sine
        + axis_unit[None, :] * dot_term * (1.0 - cosine)
    )
    norms = np.linalg.norm(rotated, axis=1, keepdims=True)
    return np.asarray(rotated / np.maximum(norms, EPSILON), dtype=float)


def _rotation_matrix_to_quaternion_wxyz(matrix: ArrayLike) -> NDArray[np.float64]:
    """Convert a proper 3x3 rotation matrix to a unit quaternion [w, x, y, z]."""

    rotation = np.asarray(matrix, dtype=float)
    trace = float(np.trace(rotation))
    if trace > 0.0:
        scale = np.sqrt(trace + 1.0) * 2.0
        quaternion = np.array([
            0.25 * scale,
            (rotation[2, 1] - rotation[1, 2]) / scale,
            (rotation[0, 2] - rotation[2, 0]) / scale,
            (rotation[1, 0] - rotation[0, 1]) / scale,
        ])
    else:
        diagonal = np.diag(rotation)
        index = int(np.argmax(diagonal))
        if index == 0:
            scale = np.sqrt(max(1.0 + rotation[0, 0] - rotation[1, 1] - rotation[2, 2], 0.0)) * 2.0
            scale = max(scale, EPSILON)
            quaternion = np.array([
                (rotation[2, 1] - rotation[1, 2]) / scale,
                0.25 * scale,
                (rotation[0, 1] + rotation[1, 0]) / scale,
                (rotation[0, 2] + rotation[2, 0]) / scale,
            ])
        elif index == 1:
            scale = np.sqrt(max(1.0 + rotation[1, 1] - rotation[0, 0] - rotation[2, 2], 0.0)) * 2.0
            scale = max(scale, EPSILON)
            quaternion = np.array([
                (rotation[0, 2] - rotation[2, 0]) / scale,
                (rotation[0, 1] + rotation[1, 0]) / scale,
                0.25 * scale,
                (rotation[1, 2] + rotation[2, 1]) / scale,
            ])
        else:
            scale = np.sqrt(max(1.0 + rotation[2, 2] - rotation[0, 0] - rotation[1, 1], 0.0)) * 2.0
            scale = max(scale, EPSILON)
            quaternion = np.array([
                (rotation[1, 0] - rotation[0, 1]) / scale,
                (rotation[0, 2] + rotation[2, 0]) / scale,
                (rotation[1, 2] + rotation[2, 1]) / scale,
                0.25 * scale,
            ])
    quaternion /= max(float(np.linalg.norm(quaternion)), EPSILON)
    return np.asarray(quaternion, dtype=float)


def _frame_quaternion_series(
    x_axes: NDArray[np.float64],
    y_axes: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Build continuous quaternions from frame x/y axes."""

    if x_axes.ndim == 1:
        x_values = np.repeat(x_axes[None, :], y_axes.shape[0], axis=0)
    else:
        x_values = np.asarray(x_axes, dtype=float)
    y_values = np.asarray(y_axes, dtype=float)
    quaternions = np.empty((y_values.shape[0], 4), dtype=float)
    previous: NDArray[np.float64] | None = None

    for index, (x_axis, y_axis) in enumerate(zip(x_values, y_values)):
        x_unit = _normalise_vector(x_axis)
        y_projected = y_axis - x_unit * float(np.dot(x_unit, y_axis))
        y_unit = _normalise_vector(y_projected)
        z_unit = _normalise_vector(np.cross(x_unit, y_unit))
        y_unit = _normalise_vector(np.cross(z_unit, x_unit))
        rotation = np.column_stack((x_unit, y_unit, z_unit))
        quaternion = _rotation_matrix_to_quaternion_wxyz(rotation)
        if previous is not None and float(np.dot(previous, quaternion)) < 0.0:
            quaternion = -quaternion
        quaternions[index] = quaternion
        previous = quaternion

    return quaternions


def calculate_planar_scene_geometry(
    parameters: CardanParameters,
    *,
    shaft_length: float = 2.2,
) -> PlanarSceneGeometry:
    """Create a canonical planar shaft layout for visualization.

    The relative beta angles are preserved exactly, but all shaft axes are placed
    in one plane. This is a schematic visualization geometry, not a general 3D CAD
    reconstruction of an arbitrary driveline installation.
    """

    length = float(shaft_length)
    if length <= 0.0:
        raise ValueError("shaft_length must be positive.")

    directions = [np.array([1.0, 0.0, 0.0], dtype=float)]
    cumulative_angle_deg = 0.0
    for beta_deg in parameters.active_betas:
        cumulative_angle_deg += float(beta_deg)
        angle_rad = np.deg2rad(cumulative_angle_deg)
        directions.append(np.array([np.cos(angle_rad), np.sin(angle_rad), 0.0]))
    direction_array = np.vstack([_normalise_vector(item) for item in directions])

    points = [np.zeros(3, dtype=float)]
    for direction in direction_array:
        points.append(points[-1] + length * direction)
    point_array = np.vstack(points)
    center_offset = 0.5 * (point_array.min(axis=0) + point_array.max(axis=0))
    point_array = point_array - center_offset

    joint_centers = point_array[1:-1]
    normals: list[NDArray[np.float64]] = []
    previous_normal = np.array([0.0, 0.0, 1.0])
    for input_direction, output_direction in zip(direction_array[:-1], direction_array[1:]):
        candidate = np.cross(input_direction, output_direction)
        normal = _normalise_vector(candidate, fallback=previous_normal)
        if float(np.dot(normal, np.array([0.0, 0.0, 1.0]))) < 0.0:
            normal = -normal
        normals.append(normal)
        previous_normal = normal

    return PlanarSceneGeometry(
        shaft_points=np.asarray(point_array, dtype=float),
        shaft_directions=np.asarray(direction_array, dtype=float),
        joint_centers=np.asarray(joint_centers, dtype=float),
        joint_plane_normals=np.vstack(normals),
        shaft_length=length,
    )


def calculate_kinematic_scene(
    parameters: CardanParameters,
    trajectory: KinematicTrajectory | None = None,
    *,
    theta_deg: ArrayLike | None = None,
    shaft_length: float = 2.2,
) -> KinematicScene:
    """Calculate shaft/yoke/cross orientations for the planar 3D viewer."""

    if trajectory is None:
        if theta_deg is None:
            theta_deg = np.linspace(0.0, FULL_REVOLUTION_DEG, 181, endpoint=True)
        trajectory = calculate_kinematic_trajectory(theta_deg, parameters)

    geometry = calculate_planar_scene_geometry(parameters, shaft_length=shaft_length)
    joint_count = int(parameters.mode)
    frame_count = trajectory.input_rotation_deg.size

    shaft_angles = np.empty((joint_count + 1, frame_count), dtype=float)
    shaft_angles[0] = trajectory.joint_input_angles_deg[0]
    for shaft_index in range(1, joint_count + 1):
        shaft_angles[shaft_index] = trajectory.joint_output_angles_deg[shaft_index - 1]

    input_yoke_axes = np.empty((joint_count, frame_count, 3), dtype=float)
    output_yoke_axes = np.empty((joint_count, frame_count, 3), dtype=float)
    shaft_quaternions = np.empty((joint_count + 1, frame_count, 4), dtype=float)
    input_quaternions = np.empty((joint_count, frame_count, 4), dtype=float)
    output_quaternions = np.empty((joint_count, frame_count, 4), dtype=float)
    cross_quaternions = np.empty((joint_count, frame_count, 4), dtype=float)

    global_normal = np.array([0.0, 0.0, 1.0])
    for shaft_index, direction in enumerate(geometry.shaft_directions):
        base_y = _normalise_vector(np.cross(global_normal, direction), fallback=[0.0, 1.0, 0.0])
        shaft_y_axes = _rotate_vector_series(
            base_y,
            direction,
            np.deg2rad(shaft_angles[shaft_index]),
        )
        shaft_quaternions[shaft_index] = _frame_quaternion_series(direction, shaft_y_axes)

    for joint_index in range(joint_count):
        input_direction = geometry.shaft_directions[joint_index]
        output_direction = geometry.shaft_directions[joint_index + 1]
        plane_normal = geometry.joint_plane_normals[joint_index]
        input_reference = _normalise_vector(np.cross(plane_normal, input_direction))
        output_reference = plane_normal

        input_axes = _rotate_vector_series(
            input_reference,
            input_direction,
            np.deg2rad(trajectory.joint_input_angles_deg[joint_index]),
        )
        output_axes = _rotate_vector_series(
            output_reference,
            output_direction,
            np.deg2rad(trajectory.joint_output_angles_deg[joint_index]),
        )
        input_yoke_axes[joint_index] = input_axes
        output_yoke_axes[joint_index] = output_axes
        input_quaternions[joint_index] = _frame_quaternion_series(input_direction, input_axes)
        output_quaternions[joint_index] = _frame_quaternion_series(output_direction, output_axes)
        cross_quaternions[joint_index] = _frame_quaternion_series(input_axes, output_axes)

    return KinematicScene(
        input_rotation_deg=np.asarray(trajectory.input_rotation_deg, dtype=float),
        geometry=geometry,
        shaft_rotation_angles_deg=shaft_angles,
        input_yoke_axes=input_yoke_axes,
        output_yoke_axes=output_yoke_axes,
        shaft_quaternions_wxyz=shaft_quaternions,
        input_yoke_quaternions_wxyz=input_quaternions,
        output_yoke_quaternions_wxyz=output_quaternions,
        cross_quaternions_wxyz=cross_quaternions,
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

    phi1_model_rad = np.deg2rad(
        physical_phase_to_model_phase_deg(phase_values_deg)
    )[:, None]
    theta2_phased_rad = theta2_rad[None, :] - phi1_model_rad
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
    phi1_model_values_rad = np.deg2rad(
        physical_phase_to_model_phase_deg(phi1_values_deg)
    )
    phi2_model_values_rad = np.deg2rad(
        physical_phase_to_model_phase_deg(phi2_values_deg)
    )

    metric_matrix = np.empty((phi1_values_deg.size, phi2_values_deg.size), dtype=float)
    best_metric = np.inf
    best_phi1_deg = 0.0
    best_phi2_deg = 0.0
    best_q: NDArray[np.float64] | None = None

    for row, (phi1_deg, phi1_model_rad) in enumerate(
        zip(phi1_values_deg, phi1_model_values_rad)
    ):
        theta2_phased_rad = theta2_rad - phi1_model_rad
        q2 = hooke_speed_ratio_rad(theta2_phased_rad, beta2_rad)

        theta3_rad = hooke_output_angle_rad(theta2_phased_rad, beta2_rad)
        theta3_phased_rad = (
            theta3_rad[None, :] - phi2_model_values_rad[:, None]
        )
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
    # A step that does not divide the half-width would skip the centre, and the
    # refinement could then be worse than the candidate it started from.
    normalized = canonical_phase_deg(np.append(raw, float(center_deg)))
    # Rounding can turn 179.99999999999 into 180.0, which is the same phase as 0.
    rounded = np.mod(np.round(normalized, decimals=10), KINEMATIC_PERIOD_DEG)
    return np.unique(rounded)


# A local-refinement window never uses more than this many nodes per phase
# axis.  Wider windows are refined in stages (coarser pass, then a finer pass
# around its best node) instead of one exhaustive pass.
LOCAL_REFINEMENT_MAX_NODES = 81


def _local_refinement_stages(
    half_width_deg: float,
    step_deg: float,
) -> list[tuple[float, float]]:
    """Return (half_width, step) passes for a periodic local refinement.

    A single pass is returned whenever it fits into LOCAL_REFINEMENT_MAX_NODES
    nodes per axis, which keeps the default settings identical to an exhaustive
    window.  Otherwise each coarser pass uses exactly that many nodes and the
    next pass searches +-2 of its steps around the best node.
    """

    half_width = float(half_width_deg)
    step = float(step_deg)
    if step <= 0.0:
        raise ValueError("Refinement step must be positive.")
    stages: list[tuple[float, float]] = []
    while 2.0 * half_width / step + 1.0 > LOCAL_REFINEMENT_MAX_NODES + 1.0e-9:
        intermediate = 2.0 * half_width / (LOCAL_REFINEMENT_MAX_NODES - 1)
        stages.append((half_width, intermediate))
        half_width = 2.0 * intermediate
    stages.append((half_width, step))
    return stages


def local_refinement_evaluation_count(
    parameters: CardanParameters,
    refinement_step_deg: float,
) -> int:
    """Number of phase candidates evaluated by ``refine_optimization``."""

    if parameters.mode is CardanMode.SINGLE:
        return 0
    exponent = 1 if parameters.mode is CardanMode.DOUBLE else 2
    total = 0
    for half_width, step in _local_refinement_stages(
        parameters.optimization_step_deg, refinement_step_deg
    ):
        total += int(_periodic_local_grid(90.0, half_width, step).size) ** exponent
    return total


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
    if parameters.mode is CardanMode.TRIPLE and coarse_result.phi2_deg is None:
        raise ValueError("Triple-Cardan refinement requires both coarse phases.")

    refined = coarse_result
    for half_width, step in _local_refinement_stages(
        parameters.optimization_step_deg, refinement_step_deg
    ):
        phi1_values = _periodic_local_grid(refined.phi1_deg, half_width, step)
        local_parameters = replace(parameters, optimization_step_deg=float(step))
        if parameters.mode is CardanMode.DOUBLE:
            refined, _ = _double_landscape(local_parameters, theta_deg, phi1_values)
        else:
            phi2_values = _periodic_local_grid(refined.phi2_deg, half_width, step)
            refined, _ = _triple_landscape(
                local_parameters, theta_deg, phi1_values, phi2_values
            )

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
            phi1_physical = float(
                canonical_phase_deg(np.asarray(candidate, dtype=float)[0])
            )
            phi1_model_rad = np.deg2rad(
                float(physical_phase_to_model_phase_deg(phi1_physical))
            )
            q2 = hooke_speed_ratio_rad(theta2_rad - phi1_model_rad, beta2_rad)
            return float(unevenness_percent(q1 * q2))

        return objective

    beta3_rad = np.deg2rad(float(parameters.beta3_deg))

    def objective(candidate: ArrayLike) -> float:
        physical_phases = canonical_phase_deg(candidate)
        phi1_model_rad, phi2_model_rad = np.deg2rad(
            physical_phase_to_model_phase_deg(physical_phases)
        )
        theta2_phased_rad = theta2_rad - phi1_model_rad
        q2 = hooke_speed_ratio_rad(theta2_phased_rad, beta2_rad)
        theta3_rad = hooke_output_angle_rad(theta2_phased_rad, beta2_rad)
        q3 = hooke_speed_ratio_rad(theta3_rad - phi2_model_rad, beta3_rad)
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
    raw_objective = _build_continuous_objective(parameters, theta_deg)
    objective_calls = 0

    def objective(candidate: ArrayLike) -> float:
        # Counts every evaluation, including the driver's own comparisons,
        # instead of trusting the numbers reported by the solvers.
        nonlocal objective_calls
        objective_calls += 1
        return raw_objective(candidate)

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
        iterations += int(getattr(powell_result, "nit", 0))
        powell_vector = canonical_phase_deg(powell_result.x)
        powell_value = float(objective(powell_vector))
        # Powell's convergence only says something about the returned point
        # if that point is at least as good as the one that is kept.
        if powell_value <= best_value:
            success = bool(powell_result.success)
        if powell_value < best_value:
            best_vector = powell_vector
            best_value = powell_value
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
        function_evaluations=int(objective_calls),
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

    # Sampling-free reference optimum; reported with every method.
    exact_started = perf_counter()
    exact_optimum = exact_phase_optimum(parameters)
    exact_elapsed = perf_counter() - exact_started

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
        local_evaluations = local_refinement_evaluation_count(
            parameters, float(settings.local_refinement_step_deg)
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
    elif settings.method is OptimizationMethod.EXACT:
        exact_solution = exact_optimum
        phase_vector = [exact_solution.phi1_deg]
        if parameters.mode is CardanMode.TRIPLE:
            phase_vector.append(exact_solution.phi2_deg)
        optimization_result = _result_from_phase_vector(
            parameters,
            theta_metric_deg,
            phase_vector,
            coarse_result,
            settings.method,
        )
        diagnostics = OptimizationDiagnostics(
            method=settings.method.value,
            success=bool(exact_solution.certified_global),
            message=(
                "Closed-form optimum; global optimality certified by the lower bound."
                if exact_solution.certified_global
                else "Closed-form optimum found, but the lower bound was not attained; "
                "global optimality is not certified."
            ),
            function_evaluations=(
                exact_solution.function_evaluations + phase_combination_count(parameters)
            ),
            iterations=0,
            elapsed_seconds=float(coarse_elapsed + exact_elapsed),
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

    # The entered configuration is always a candidate: an "optimum" must never
    # be worse than the starting point (e.g. when the current phases lie
    # between grid nodes).  Both values use the same objective grid.
    current_is_optimal = False
    if parameters.mode is not CardanMode.SINGLE:
        current_objective = float(unevenness_percent(q_current_metric))
        if current_objective <= (
            optimization_result.unevenness_percent + OPTIMALITY_TOLERANCE_PERCENT
        ):
            current_is_optimal = True
            optimization_result = _result_from_phase_vector(
                parameters,
                theta_metric_deg,
                list(parameters.active_phases),
                coarse_result,
                settings.method,
            )
            diagnostics = replace(
                diagnostics,
                message=(
                    diagnostics.message
                    + " The current configuration was retained because no candidate improved it."
                ),
                objective_unevenness_percent=float(optimization_result.unevenness_percent),
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

    exact_current = exact_speed_ratio_bounds(parameters)
    exact_optimized = exact_speed_ratio_bounds(optimized_parameters)

    return {
        "exact_current": exact_current,
        "exact_optimized": exact_optimized,
        "exact_optimum": exact_optimum,
        "optimality_gap_percent": float(
            max(0.0, exact_optimized.unevenness_percent - exact_optimum.unevenness_percent)
        ),
        "current_is_optimal": current_is_optimal,
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

    # theta0 is the rotation reference of the input shaft about its own axis;
    # it does not incline the shaft layout, so the schematic is not rotated.
    directions = [np.array([1.0, 0.0])]
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

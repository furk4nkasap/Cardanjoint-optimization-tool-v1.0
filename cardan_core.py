"""Core kinematic model for the Cardan Joint Optimization Tool."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Arc, Circle
from numpy.typing import ArrayLike, NDArray


class CardanMode(IntEnum):
    SINGLE = 1
    DOUBLE = 2
    TRIPLE = 3


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

        if not 0.0 < self.optimization_step_deg <= 360.0:
            raise ValueError("Optimization step must satisfy 0 < step <= 360 degrees.")

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


@dataclass(frozen=True, slots=True)
class OptimizationResult:
    phi1_deg: float | None
    phi2_deg: float | None
    q_best: NDArray[np.float64]
    unevenness_percent: float


EPSILON = 1.0e-12
UNEVENNESS_LIMIT_PERCENT = 5.0
PLOT_SAMPLE_COUNT = 721
OPTIMIZATION_SAMPLE_COUNT = 720

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
    """
    Position relation consistent with the implemented speed-ratio equation:

        tan(theta_out) = tan(theta_in) / cos(beta)
    """

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


def create_phase_grid(step_deg: float) -> NDArray[np.float64]:
    step_deg = float(step_deg)

    if not 0.0 < step_deg <= 360.0:
        raise ValueError("Phase step must satisfy 0 < step <= 360 degrees.")

    values = np.arange(0.0, 360.0, step_deg, dtype=float)
    return values if values.size else np.array([0.0], dtype=float)


def optimize_double_phase(
    parameters: CardanParameters,
    theta_deg: NDArray[np.float64],
    phase_values_deg: NDArray[np.float64],
) -> OptimizationResult:
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

    return OptimizationResult(
        phi1_deg=float(phase_values_deg[best_index]),
        phi2_deg=None,
        q_best=np.asarray(q_total[best_index], dtype=float),
        unevenness_percent=float(metrics[best_index]),
    )


def optimize_triple_phase(
    parameters: CardanParameters,
    theta_deg: NDArray[np.float64],
    phase_values_deg: NDArray[np.float64],
) -> OptimizationResult:
    theta1_rad = np.deg2rad(theta_deg + parameters.theta0_deg)
    beta1_rad = np.deg2rad(parameters.beta1_deg)
    beta2_rad = np.deg2rad(parameters.beta2_deg)
    beta3_rad = np.deg2rad(parameters.beta3_deg)

    theta2_rad = hooke_output_angle_rad(theta1_rad, beta1_rad)
    q1 = hooke_speed_ratio_rad(theta1_rad, beta1_rad)
    phase_values_rad = np.deg2rad(phase_values_deg)

    best_metric = np.inf
    best_phi1_deg = 0.0
    best_phi2_deg = 0.0
    best_q = None

    for phi1_deg, phi1_rad in zip(phase_values_deg, phase_values_rad):
        theta2_phased_rad = theta2_rad - phi1_rad
        q2 = hooke_speed_ratio_rad(theta2_phased_rad, beta2_rad)

        theta3_rad = hooke_output_angle_rad(theta2_phased_rad, beta2_rad)
        theta3_phased_rad = theta3_rad[None, :] - phase_values_rad[:, None]
        q3 = hooke_speed_ratio_rad(theta3_phased_rad, beta3_rad)

        q_total = (q1 * q2)[None, :] * q3
        metrics = np.asarray(unevenness_percent(q_total, axis=1), dtype=float)
        local_index = int(np.argmin(metrics))
        local_metric = float(metrics[local_index])

        if local_metric < best_metric:
            best_metric = local_metric
            best_phi1_deg = float(phi1_deg)
            best_phi2_deg = float(phase_values_deg[local_index])
            best_q = np.asarray(q_total[local_index], dtype=float)

    if best_q is None:
        raise RuntimeError("No valid triple-Cardan phase combination was evaluated.")

    return OptimizationResult(
        phi1_deg=best_phi1_deg,
        phi2_deg=best_phi2_deg,
        q_best=best_q,
        unevenness_percent=best_metric,
    )


def optimize_phase(
    parameters: CardanParameters,
    theta_grid_deg: ArrayLike,
) -> OptimizationResult:
    theta_deg = np.asarray(theta_grid_deg, dtype=float)

    if theta_deg.ndim != 1 or theta_deg.size < 2:
        raise ValueError("theta_grid_deg must be a 1D array with at least two values.")

    if parameters.mode is CardanMode.SINGLE:
        q = calculate_total_ratio(theta_deg, parameters)
        return OptimizationResult(
            phi1_deg=None,
            phi2_deg=None,
            q_best=q,
            unevenness_percent=float(unevenness_percent(q)),
        )

    phase_values_deg = create_phase_grid(parameters.optimization_step_deg)

    if parameters.mode is CardanMode.DOUBLE:
        return optimize_double_phase(parameters, theta_deg, phase_values_deg)

    return optimize_triple_phase(parameters, theta_deg, phase_values_deg)


def apply_optimized_phases(
    parameters: CardanParameters,
    result: OptimizationResult,
) -> CardanParameters:
    return CardanParameters(
        mode=parameters.mode,
        beta1_deg=parameters.beta1_deg,
        beta2_deg=parameters.beta2_deg,
        beta3_deg=parameters.beta3_deg,
        phi1_deg=parameters.phi1_deg if result.phi1_deg is None else result.phi1_deg,
        phi2_deg=parameters.phi2_deg if result.phi2_deg is None else result.phi2_deg,
        theta0_deg=parameters.theta0_deg,
        optimization_step_deg=parameters.optimization_step_deg,
    )


def calculate_analysis(
    parameters: CardanParameters,
) -> dict[str, object]:
    theta_plot_deg = np.linspace(0.0, 360.0, PLOT_SAMPLE_COUNT, endpoint=True)
    theta_metric_deg = np.linspace(
        0.0,
        360.0,
        OPTIMIZATION_SAMPLE_COUNT,
        endpoint=False,
    )

    q_current_plot = calculate_total_ratio(theta_plot_deg, parameters)
    q_current_metric = calculate_total_ratio(theta_metric_deg, parameters)
    current_unevenness = float(unevenness_percent(q_current_metric))

    optimization_result = optimize_phase(parameters, theta_metric_deg)
    optimized_parameters = apply_optimized_phases(parameters, optimization_result)
    q_optimized_plot = calculate_total_ratio(theta_plot_deg, optimized_parameters)

    return {
        "theta_plot_deg": theta_plot_deg,
        "q_current_plot": q_current_plot,
        "q_optimized_plot": q_optimized_plot,
        "current_unevenness": current_unevenness,
        "optimization_result": optimization_result,
        "optimized_parameters": optimized_parameters,
    }


def plot_velocity_ratio(
    parameters: CardanParameters,
) -> tuple[Figure, OptimizationResult, float]:
    analysis = calculate_analysis(parameters)

    theta_plot_deg = analysis["theta_plot_deg"]
    q_current_plot = analysis["q_current_plot"]
    q_optimized_plot = analysis["q_optimized_plot"]
    current_unevenness = analysis["current_unevenness"]
    result = analysis["optimization_result"]

    fig, ax = plt.subplots(figsize=(11.5, 4.2))
    ax.plot(theta_plot_deg, q_current_plot, lw=2.6, label="Current")
    ax.plot(
        theta_plot_deg,
        q_optimized_plot,
        lw=2.6,
        linestyle="--",
        label="Optimized",
    )

    ax.set_xlabel("Input shaft rotation angle (deg)")
    ax.set_ylabel(r"$q_{\mathrm{total}}=\omega_{\mathrm{out}}/\omega_{\mathrm{in}}$")
    ax.set_title("Figure A — Angular Velocity Ratio and Unevenness")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")

    status = "OK" if current_unevenness <= UNEVENNESS_LIMIT_PERCENT else "Warning"
    text = (
        f"Current Δq/q̄ = {current_unevenness:.2f}% → {status}\n"
        f"Optimized Δq/q̄ = {result.unevenness_percent:.2f}%\n"
    )

    if parameters.mode is CardanMode.DOUBLE:
        text += f"Optimized φ₁ = {result.phi1_deg:.0f}°"
    elif parameters.mode is CardanMode.TRIPLE:
        text += f"Optimized φ₁ = {result.phi1_deg:.0f}°, φ₂ = {result.phi2_deg:.0f}°"

    ax.text(
        0.02,
        0.98,
        text,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=11,
        bbox=dict(
            boxstyle="round,pad=0.35",
            fc="white",
            ec="0.35",
            alpha=0.95,
        ),
    )

    fig.tight_layout()
    return fig, result, float(current_unevenness)


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
) -> Figure:
    fig, ax = plt.subplots(figsize=(10.8, 4.4))
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Figure B — Two-Dimensional Shaft Geometry", fontsize=13)

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
) -> None:
    ax.set_aspect("equal")
    ax.axis("off")

    normalized_phi = float(phi_deg) % 360.0
    signed_phi = signed_phase_angle(normalized_phi)
    direction = "CCW" if signed_phi >= 0.0 else "CW"

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
) -> None:
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

    ax.text(0.0, 1.90, f"{title} (side view)", fontsize=12, color=BLACK)
    ax.text(0.0, 1.55, f"φ = {phi:.0f}°", fontsize=11, color=BLACK)
    ax.set_xlim(
        left_center - C_RING_RADIUS - 0.6,
        right_center + C_RING_RADIUS + 1.4,
    )
    ax.set_ylim(-2.2, 2.2)


def plot_phase_figure(
    parameters: CardanParameters,
) -> Figure | None:
    if parameters.mode is CardanMode.SINGLE:
        return None

    rows = 1 if parameters.mode is CardanMode.DOUBLE else 2
    fig = plt.figure(figsize=(14.5, 4.8 * rows))
    grid = fig.add_gridspec(rows, 2, width_ratios=[1.15, 0.85])

    end_ax_1 = fig.add_subplot(grid[0, 0])
    side_ax_1 = fig.add_subplot(grid[0, 1])
    draw_end_view(end_ax_1, parameters.phi1_deg, "Joint 1 → Joint 2", ORANGE)
    draw_side_view(
        side_ax_1,
        parameters.phi1_deg,
        "Joint 1 → Joint 2",
        left_c_color=BLUE,
        shaft_color=ORANGE,
        right_c_color=GREEN,
    )

    if parameters.mode is CardanMode.TRIPLE:
        end_ax_2 = fig.add_subplot(grid[1, 0])
        side_ax_2 = fig.add_subplot(grid[1, 1])
        draw_end_view(end_ax_2, parameters.phi2_deg, "Joint 2 → Joint 3", GREEN)
        draw_side_view(
            side_ax_2,
            parameters.phi2_deg,
            "Joint 2 → Joint 3",
            left_c_color=ORANGE,
            shaft_color=GREEN,
            right_c_color=PURPLE,
        )

    fig.suptitle("Figure C — Phase (φ)", fontsize=18, fontweight="bold", y=0.98)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.96))
    return fig

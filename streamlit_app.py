"""Streamlit interface for the Cardan Joint Optimization Tool."""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
from matplotlib.figure import Figure
import streamlit as st

from cardan_core import (
    CardanMode,
    CardanParameters,
    UNEVENNESS_LIMIT_PERCENT,
    plot_geometry_2d,
    plot_phase_figure,
    plot_velocity_ratio,
)


# ---------------------------------------------------------------------------
# Streamlit page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Cardan Joint Optimization Tool",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Visual settings
# ---------------------------------------------------------------------------

PAGE_BACKGROUND = "#0E1117"
PLOT_BACKGROUND = "#111827"
TEXT_COLOR = "#F3F4F6"
MUTED_TEXT_COLOR = "#AEB6C2"
GRID_COLOR = "#6B7280"
SPINE_COLOR = "#6B7280"
LEGEND_BACKGROUND = "#1F2937"


def _is_near_black(color: object) -> bool:
    """Return True when a Matplotlib color is black or almost black."""
    try:
        red, green, blue, _ = to_rgba(color)
    except (TypeError, ValueError):
        return False

    return red < 0.18 and green < 0.18 and blue < 0.18


def style_figure_for_dark_theme(figure: Figure) -> Figure:
    """Apply a readable dark theme to a Matplotlib figure."""

    figure.patch.set_facecolor(PLOT_BACKGROUND)

    if figure._suptitle is not None:
        figure._suptitle.set_color(TEXT_COLOR)

    for axis in figure.axes:
        axis.set_facecolor(PLOT_BACKGROUND)

        axis.title.set_color(TEXT_COLOR)
        axis.xaxis.label.set_color(TEXT_COLOR)
        axis.yaxis.label.set_color(TEXT_COLOR)

        axis.tick_params(
            axis="both",
            colors=MUTED_TEXT_COLOR,
            which="both",
        )

        for spine in axis.spines.values():
            spine.set_color(SPINE_COLOR)

        axis.grid(
            visible=True,
            color=GRID_COLOR,
            alpha=0.22,
            linewidth=0.8,
        )

        # Texts created inside the core plotting functions are black by default.
        for text in axis.texts:
            if _is_near_black(text.get_color()):
                text.set_color(TEXT_COLOR)

            text_box = text.get_bbox_patch()
            if text_box is not None:
                text_box.set_facecolor(LEGEND_BACKGROUND)
                text_box.set_edgecolor(SPINE_COLOR)
                text_box.set_alpha(0.94)

        # Keep engineering colors, but replace black shafts/lines with light gray.
        for line in axis.lines:
            if _is_near_black(line.get_color()):
                line.set_color(TEXT_COLOR)

        for patch in axis.patches:
            if _is_near_black(patch.get_edgecolor()):
                patch.set_edgecolor(TEXT_COLOR)

        legend = axis.get_legend()
        if legend is not None:
            legend.get_frame().set_facecolor(LEGEND_BACKGROUND)
            legend.get_frame().set_edgecolor(SPINE_COLOR)
            legend.get_frame().set_alpha(0.94)

            for legend_text in legend.get_texts():
                legend_text.set_color(TEXT_COLOR)

    return figure


st.markdown(
    """
    <style>
        .stApp {
            background-color: #0E1117;
        }

        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 3rem;
        }

        [data-testid="stSidebar"] {
            min-width: 330px;
            max-width: 330px;
        }

        .app-subtitle {
            color: #AEB6C2;
            font-size: 1.05rem;
            margin-top: -0.8rem;
            margin-bottom: 1.2rem;
        }

        [data-testid="stMetric"] {
            border: 1px solid rgba(174, 182, 194, 0.22);
            border-radius: 0.8rem;
            padding: 1rem 1.1rem;
            background: rgba(31, 41, 55, 0.45);
        }

        [data-testid="stMetricValue"] {
            font-size: clamp(1.8rem, 2.6vw, 2.8rem);
        }

        .scope-note {
            border-left: 4px solid #9A9A9A;
            padding: 0.65rem 0.9rem;
            background: rgba(128, 128, 128, 0.08);
            border-radius: 0.3rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("Cardan Joint Kinematics & Phase Optimization Tool")
st.markdown(
    '<div class="app-subtitle">'
    "Interactive kinematic analysis of single, double, and triple Cardan systems"
    "</div>",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Sidebar inputs
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("System Parameters")

    mode_label = st.selectbox(
        "Cardan configuration",
        options=[
            "1 Cardan — Single",
            "2 Cardan — Double",
            "3 Cardan — Triple",
        ],
        index=2,
    )

    mode_map = {
        "1 Cardan — Single": CardanMode.SINGLE,
        "2 Cardan — Double": CardanMode.DOUBLE,
        "3 Cardan — Triple": CardanMode.TRIPLE,
    }
    mode = mode_map[mode_label]

    st.subheader("Misalignment Angles")

    beta1_deg = st.slider(
        "β₁ (deg)",
        min_value=0,
        max_value=60,
        value=25,
        step=1,
    )

    beta2_deg = 25
    beta3_deg = 25

    if mode >= CardanMode.DOUBLE:
        beta2_deg = st.slider(
            "β₂ (deg)",
            min_value=0,
            max_value=60,
            value=25,
            step=1,
        )

    if mode is CardanMode.TRIPLE:
        beta3_deg = st.slider(
            "β₃ (deg)",
            min_value=0,
            max_value=60,
            value=25,
            step=1,
        )

    phi1_deg = 0
    phi2_deg = 0
    optimization_step_deg = 5

    if mode >= CardanMode.DOUBLE:
        st.subheader("Phase Angles")

        phi1_deg = st.slider(
            "φ₁ (deg)",
            min_value=0,
            max_value=360,
            value=0,
            step=1,
        )

        if mode is CardanMode.TRIPLE:
            phi2_deg = st.slider(
                "φ₂ (deg)",
                min_value=0,
                max_value=360,
                value=0,
                step=1,
            )

        st.subheader("Optimization")

        optimization_step_deg = st.select_slider(
            "Phase-search step (deg)",
            options=[1, 2, 3, 4, 5, 6, 8, 10],
            value=5,
            help=(
                "A smaller step gives a finer phase search but increases "
                "calculation time, especially for the triple Cardan mode."
            ),
        )

    st.subheader("Angular Reference")

    theta0_deg = st.slider(
        "θ₀ (deg)",
        min_value=0,
        max_value=180,
        value=0,
        step=1,
    )

    run_button = st.button(
        "Run analysis",
        type="primary",
        use_container_width=True,
    )


# ---------------------------------------------------------------------------
# Parameter object and analysis state
# ---------------------------------------------------------------------------

parameters = CardanParameters(
    mode=mode,
    beta1_deg=float(beta1_deg),
    beta2_deg=float(beta2_deg),
    beta3_deg=float(beta3_deg),
    phi1_deg=float(phi1_deg),
    phi2_deg=float(phi2_deg),
    theta0_deg=float(theta0_deg),
    optimization_step_deg=float(optimization_step_deg),
)

if "analysis_started" not in st.session_state:
    st.session_state.analysis_started = False

if run_button:
    st.session_state.analysis_started = True


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

if not st.session_state.analysis_started:
    st.info(
        "Select the system parameters from the sidebar and press "
        "**Run analysis**."
    )
else:
    with st.spinner("Calculating kinematic response and phase optimization..."):
        velocity_figure, result, current_unevenness = plot_velocity_ratio(parameters)
        geometry_figure = plot_geometry_2d(parameters)
        phase_figure = plot_phase_figure(parameters)

        style_figure_for_dark_theme(velocity_figure)
        style_figure_for_dark_theme(geometry_figure)

        if phase_figure is not None:
            style_figure_for_dark_theme(phase_figure)

    # -----------------------------------------------------------------------
    # Analysis summary
    # -----------------------------------------------------------------------

    st.subheader("Analysis Summary")

    summary_col1, summary_col2, summary_col3 = st.columns(3)

    summary_col1.metric(
        "Current unevenness",
        f"{current_unevenness:.2f}%",
    )

    summary_col2.metric(
        "Optimized unevenness",
        f"{result.unevenness_percent:.2f}%",
        delta=f"{result.unevenness_percent - current_unevenness:.2f}%",
        delta_color="inverse",
    )

    status = (
        "OK"
        if current_unevenness <= UNEVENNESS_LIMIT_PERCENT
        else "Warning"
    )

    summary_col3.metric(
        "Current status",
        status,
    )

    st.markdown("#### Optimum Phase Angles")

    if mode is CardanMode.SINGLE:
        st.info("Phase optimization is not applicable to a single Cardan joint.")

    elif mode is CardanMode.DOUBLE:
        phase_col1, _ = st.columns(2)

        phase_col1.metric(
            "Optimum φ₁",
            f"{result.phi1_deg:.0f}°",
        )

    else:
        phase_col1, phase_col2 = st.columns(2)

        phase_col1.metric(
            "Optimum φ₁",
            f"{result.phi1_deg:.0f}°",
        )

        phase_col2.metric(
            "Optimum φ₂",
            f"{result.phi2_deg:.0f}°",
        )

    st.divider()

    # -----------------------------------------------------------------------
    # Figures
    # -----------------------------------------------------------------------

    st.subheader("Figure A — Angular Velocity Ratio")
    st.pyplot(
        velocity_figure,
        use_container_width=True,
    )
    plt.close(velocity_figure)

    st.subheader("Figure B — Two-Dimensional Shaft Geometry")
    st.pyplot(
        geometry_figure,
        use_container_width=True,
    )
    plt.close(geometry_figure)

    if phase_figure is not None:
        st.subheader("Figure C — Phase Visualization")
        st.pyplot(
            phase_figure,
            use_container_width=True,
        )
        plt.close(phase_figure)

    # -----------------------------------------------------------------------
    # Technical description
    # -----------------------------------------------------------------------

    with st.expander("Model description and limitations"):
        st.markdown(
            r"""
            The application calculates the instantaneous angular velocity ratio

            $$
            q_{\mathrm{total}}
            =
            \frac{\omega_{\mathrm{out}}}{\omega_{\mathrm{in}}}
            $$

            over one complete input-shaft revolution. For double and triple
            Cardan configurations, a discrete phase scan is used to minimize

            $$
            \mathrm{Unevenness}(\%)
            =
            100
            \frac{q_{\max}-q_{\min}}{\bar q}.
            $$

            The current model is **kinematic only**. Mass, inertia, transmitted
            torque, bearing loads, elasticity, backlash, friction, stress,
            fatigue, and power losses are not included.

            The 5% status threshold is the current project criterion and should
            not be interpreted as a universal design standard.
            """
        )


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.divider()

st.caption(
    "Developed by Furkan Kasap · Automotive Engineer · "
    "Cardan Joint Kinematics & Phase Optimization Tool"
)

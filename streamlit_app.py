"""Streamlit interface for the Cardan Joint Optimization Tool."""

from __future__ import annotations

import matplotlib.pyplot as plt
import streamlit as st

from cardan_core import (
    CardanMode,
    CardanParameters,
    UNEVENNESS_LIMIT_PERCENT,
    plot_geometry_2d,
    plot_phase_figure,
    plot_velocity_ratio,
)


st.set_page_config(
    page_title="Cardan Joint Optimization Tool",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 3rem;
        }

        [data-testid="stSidebar"] {
            min-width: 330px;
            max-width: 330px;
        }

        .app-subtitle {
            color: #5f6368;
            font-size: 1.05rem;
            margin-top: -0.8rem;
            margin-bottom: 1.2rem;
        }

        .metric-card {
            border: 1px solid rgba(128, 128, 128, 0.25);
            border-radius: 0.75rem;
            padding: 0.9rem 1rem;
            margin-bottom: 0.8rem;
        }

        .scope-note {
            border-left: 4px solid #9a9a9a;
            padding: 0.65rem 0.9rem;
            background: rgba(128, 128, 128, 0.08);
            border-radius: 0.3rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Cardan Joint Kinematics & Phase Optimization Tool")
st.markdown(
    '<div class="app-subtitle">'
    "Interactive kinematic analysis of single, double, and triple Cardan systems"
    "</div>",
    unsafe_allow_html=True,
)

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

    st.subheader("Analysis Summary")

    metric_columns = st.columns(4)

    metric_columns[0].metric(
        "Current unevenness",
        f"{current_unevenness:.2f}%",
    )

    metric_columns[1].metric(
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

    metric_columns[2].metric(
        "Current status",
        status,
    )

    if mode is CardanMode.SINGLE:
        optimum_text = "Not applicable"
    elif mode is CardanMode.DOUBLE:
        optimum_text = f"φ₁ = {result.phi1_deg:.0f}°"
    else:
        optimum_text = (
            f"φ₁ = {result.phi1_deg:.0f}° | "
            f"φ₂ = {result.phi2_deg:.0f}°"
        )

    metric_columns[3].metric(
        "Optimum phase",
        optimum_text,
    )

    st.divider()

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

st.divider()

st.caption(
    "Developed by Furkan Kasap · Automotive Engineer · "
    "Cardan Joint Kinematics & Phase Optimization Tool"
)

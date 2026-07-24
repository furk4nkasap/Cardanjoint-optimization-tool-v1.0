# Cardan Joint Kinematics & Phase Optimization Tool

Interactive Python application for the **kinematic analysis, visualization, and phase optimization** of single, double, and triple Cardan (Hooke's universal joint) systems.

![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Streamlit-success.svg)
![Analysis](https://img.shields.io/badge/Analysis-Kinematics-success.svg)
![Status](https://img.shields.io/badge/Status-Active-success.svg)

---

## Overview

The **Cardan Joint Kinematics & Phase Optimization Tool** is an interactive engineering application developed in Python to evaluate the kinematic behavior of single, double, and triple Cardan joint systems.

The application computes the instantaneous angular velocity ratio

```math
q_{\mathrm{total}}=\frac{\omega_{\mathrm{out}}}{\omega_{\mathrm{in}}}
```

over one complete input-shaft revolution.

For double and triple Cardan configurations, the application automatically searches for the phase or clocking angles that minimize angular velocity unevenness.

The tool also provides:

- Angular velocity ratio plots
- Current and optimized result comparison
- Two-dimensional shaft geometry visualization
- Misalignment-angle visualization
- End-view and side-view phase representations
- An interactive Streamlit web interface

> This project performs a **kinematic analysis**. Mass, inertia, torque, bearing loads, elasticity, and dynamic forces are not included in the current version.

---

## Main Result

### Figure A — Angular Velocity Ratio and Unevenness

The following figure compares the angular velocity ratio of the current configuration with the result obtained after phase optimization.

<p align="center">
  <img src="images/figure-a-velocity-ratio.png" alt="Angular velocity ratio and unevenness analysis" width="1000">
</p>

The unevenness metric is calculated as:

```math
\mathrm{Unevenness}(\%)=
100\frac{q_{\max}-q_{\min}}{\bar{q}}
```

where:

- $q_{\max}$ is the maximum instantaneous angular velocity ratio.
- $q_{\min}$ is the minimum instantaneous angular velocity ratio.
- $\bar{q}$ is the mean angular velocity ratio over one complete revolution.

The current software classifies an unevenness value of **5% or lower** as `OK`. Values above this limit are displayed as `Warning`.

For the example shown in Figure A:

- Current unevenness: **9.01%**
- Optimized unevenness: **5.74%**
- Optimized phase angles: **φ₁ = 90° and φ₂ = 0°**

To reproduce the optimized curve for this particular example, the phase-angle inputs should be set to:

```text
φ₁ = 90°
φ₂ = 0°
```

These phase values are **not universal constants**. They are valid only for the selected Cardan configuration and misalignment-angle inputs.

For a different shaft geometry or a different set of β angles, the optimum values may be different, for example:

```text
φ₁ = 15°
φ₂ = 25°
```

The optimum phase angles are computed automatically for every user-defined Cardan configuration, shaft geometry, and misalignment-angle combination. Consequently, different system configurations generally produce different optimum phase-angle values.

---

## Features

- Single Cardan joint analysis
- Double Cardan joint analysis
- Triple Cardan joint analysis
- Instantaneous angular velocity ratio calculation
- Full-cycle analysis from `0°` to `360°`
- Current and optimized curve comparison
- Velocity unevenness calculation
- Automatic phase-angle optimization
- Adjustable optimization step size
- Interactive parameter control using Streamlit widgets
- Two-dimensional shaft geometry visualization
- Misalignment-angle visualization
- End-view phase visualization
- Side-view yoke visualization
- Interactive Streamlit web application

---

## Supported Configurations

### 1 Cardan — Single Joint

The single Cardan mode evaluates one universal joint.

Active parameters:

- β₁: Misalignment angle
- θ₀: Initial angular reference

There is no phase-angle optimization in this configuration because only one joint is present.

---

### 2 Cardan — Double Joint

The double Cardan mode evaluates two consecutive universal joints.

Active parameters:

- β₁
- β₂
- φ₁
- θ₀
- Optimization step

The software propagates the angular position through the first joint, applies the phase angle `φ₁`, and then calculates the second-joint velocity ratio.

The total ratio is:

```math
q_{\mathrm{total}}=q_1\,q_2
```

The optimizer performs a brute-force search over the specified phase-angle range and returns the phase angle that minimizes the angular velocity unevenness.

---

### 3 Cardan — Triple Joint

The triple Cardan mode evaluates three consecutive universal joints.

Active parameters:

- β₁
- β₂
- β₃
- φ₁
- φ₂
- θ₀
- Optimization step

The angular position is propagated sequentially through all three joints.

The total ratio is:

```math
q_{\mathrm{total}}=q_1\,q_2\,q_3
```

The optimizer evaluates every combination of `φ₁` and `φ₂` within the selected search resolution and returns the phase-angle combination that minimizes the angular velocity unevenness.

---

## Interactive User Interface

The Streamlit application provides an interactive interface for configuring the Cardan system, running the phase optimization, and reviewing the calculated results.

### Parameter Controls

<p align="center">
  <img src="images/interface-controls.png" alt="Streamlit sidebar parameter controls" width="320">
</p>

The sidebar contains the system configuration, misalignment-angle, phase-angle, optimization-step, and angular-reference controls.

### Analysis Summary

<p align="center">
  <img src="images/analysis-summary.png" alt="Cardan analysis summary and optimum phase angles" width="1000">
</p>

The analysis summary displays the current unevenness, optimized unevenness, current status, and optimum phase angles in separate result cards.

The interface contains the following controls:

| Parameter | Description |
|---|---|
| `System` | Selects single, double, or triple Cardan configuration |
| `β₁, β₂, β₃` | Misalignment angles between consecutive shafts |
| `φ₁, φ₂` | Relative phase or clocking angles between adjacent joints |
| `θ₀` | Initial angular reference of the input shaft |
| `opt step` | Angular increment used during phase optimization |

Controls that are not required for the selected configuration are hidden automatically.

---

## Parameter Definitions

### Misalignment Angles — β

The parameters `β₁`, `β₂`, and `β₃` define the angular misalignment between consecutive shaft segments.

The current interface permits values between:

```text
0° ≤ β ≤ 60°
```

Increasing the misalignment angle generally increases the angular velocity fluctuation produced by an individual Cardan joint.

---

### Phase Angles — φ

The parameters `φ₁` and `φ₂` define the relative angular orientation of adjacent yokes around the shaft axis.

The current interface permits values between:

```text
0° ≤ φ ≤ 360°
```

The phase angle determines how the velocity fluctuations generated by consecutive Cardan joints interact.

Depending on the shaft geometry, an appropriate phase combination can partially or significantly cancel the total velocity ripple.

---

### Initial Angular Reference — θ₀

The parameter `θ₀` shifts the starting angular reference of the input shaft.

The current interface permits values between:

```text
0° ≤ θ₀ ≤ 180°
```

It changes the angular position at which the plotted cycle begins. Because the unevenness calculation covers a complete `0°–360°` revolution, shifting the angular reference does not normally change the full-cycle maximum-to-minimum unevenness.

---

### Optimization Step — opt step

The optimization step determines the angular resolution of the brute-force phase search.

The current interface permits:

```text
1° ≤ opt step ≤ 10°
```

A smaller step provides a finer search but requires more computation time.

Examples:

```text
opt step = 10°  → Faster, lower angular resolution
opt step = 5°   → Balanced search
opt step = 1°   → Finer search, longer calculation time
```

The optimization result can only occur at a phase value included in the selected scan grid.

For example, when:

```text
opt step = 5°
```

the optimizer evaluates:

```text
0°, 5°, 10°, 15°, ..., 350°, 355°
```
The value `360°` is not evaluated separately because it is kinematically equivalent to `0°`.
Therefore, a true optimum located between two scan points may be approximated by the closest evaluated value.

---

## Optimization Method

The current version uses a **brute-force phase scan**.

### Double Cardan

For each candidate value of `φ₁`:

1. Calculate the complete angular velocity ratio curve.
2. Calculate the unevenness percentage.
3. Compare the result with the best previous result.
4. Retain the phase angle with the lowest unevenness.

### Triple Cardan

For each candidate combination of `φ₁` and `φ₂`:

1. Calculate the complete angular velocity ratio curve.
2. Calculate the unevenness percentage.
3. Compare the result with the best previous result.
4. Retain the phase-angle combination with the lowest unevenness.

### Optimization Objective

The optimization process searches for the phase-angle configuration
that minimizes the total angular velocity unevenness over one complete
input-shaft revolution.

For a double Cardan system, the optimum phase angle is defined as:

```math
\phi_1^*
=
\underset{\phi_1}{\mathrm{arg\,min}}
\left[
100
\frac{
q_{\max}(\phi_1)-q_{\min}(\phi_1)
}{
\bar{q}(\phi_1)
}
\right]
```

For a triple Cardan system, the optimum phase-angle combination is
defined as:

```math
(\phi_1^*,\phi_2^*)
=
\underset{\phi_1,\phi_2}{\mathrm{arg\,min}}
\left[
100
\frac{
q_{\max}(\phi_1,\phi_2)-q_{\min}(\phi_1,\phi_2)
}{
\bar{q}(\phi_1,\phi_2)
}
\right]
```

This relationship can be summarized as:

```math
\phi
\longrightarrow
\theta_{\mathrm{next,in}}
\longrightarrow
q_{\mathrm{next}}
\longrightarrow
q_{\mathrm{total}}
\longrightarrow
\mathrm{Unevenness}
```

The phase angles are therefore the optimization variables, while the
misalignment angles \(\beta_i\) remain fixed for each optimization run.
The current software evaluates discrete phase-angle candidates and
selects the candidate, or candidate combination, that produces the
lowest calculated unevenness.

The search interval is:

```text
0° ≤ φ < 360°
```

The computational cost increases significantly for the triple Cardan configuration because every `φ₁` value is evaluated together with every `φ₂` value.

For an optimization step \(s\), the approximate number of phase combinations is:

```math
N=\left(\frac{360}{s}\right)^2
```

for a triple Cardan system.

---

## Kinematic Model

For a single Hooke's universal joint, the instantaneous angular velocity ratio is calculated using:

```math
q=\frac{\omega_{\mathrm{out}}}{\omega_{\mathrm{in}}}
=\frac{\cos\beta}{1-\sin^{2}\beta\,\cos^{2}\theta}
```

where:

- \(\beta\) is the shaft misalignment angle,
- \(\theta\) is the instantaneous input-shaft angle,
- \(q\) is the instantaneous angular velocity ratio.

The angular position relation is:

```math
\tan\theta_{\mathrm{out}}
=
\frac{\tan\theta_{\mathrm{in}}}{\cos\beta}
```
### Effect of Phase Angle on the Kinematic Model

For multiple Cardan-joint systems, the phase or clocking angle changes
the angular reference applied to the input of the following joint.

Using the sign convention implemented in the current software, the
input angle of the second joint is:

```math
\theta_{2,\mathrm{in}}
=
\theta_{1,\mathrm{out}}-\phi_1
```

For a triple Cardan system, the input angle of the third joint is:

```math
\theta_{3,\mathrm{in}}
=
\theta_{2,\mathrm{out}}-\phi_2
```

Therefore, the phase angles do not change the shaft misalignment angles
\(\beta_i\). Instead, they shift the angular position at which the
velocity fluctuation of each subsequent Cardan joint occurs.

For a double Cardan system:

```math
q_{\mathrm{total}}(\theta,\phi_1)
=
q_1(\theta,\beta_1)
\,
q_2(\theta_{1,\mathrm{out}}-\phi_1,\beta_2)
```

For a triple Cardan system:

```math
q_{\mathrm{total}}(\theta,\phi_1,\phi_2)
=
q_1(\theta,\beta_1)
\,
q_2(\theta_{1,\mathrm{out}}-\phi_1,\beta_2)
\,
q_3(\theta_{2,\mathrm{out}}-\phi_2,\beta_3)
```

Changing \(\phi_1\) and \(\phi_2\) shifts the relative angular positions
of the individual velocity-ratio fluctuations. Depending on the
selected misalignment angles, these fluctuations may reinforce or
partially cancel one another.

For example, if two joints reach their maximum velocity ratios at
approximately the same angular position, their fluctuations may
reinforce one another. Changing the phase angle shifts the fluctuation
of the following joint, allowing one joint to partially compensate for
the acceleration or deceleration produced by another joint. As a
result, the total output velocity may become more uniform.

---

## Figure B — Two-Dimensional Shaft Geometry

The two-dimensional geometry view illustrates the shaft arrangement and displays the β misalignment angles between consecutive shaft segments.

<p align="center">
  <img src="images/figure-b-shaft-geometry.png" alt="Two-dimensional Cardan shaft geometry" width="700">
</p>

The number of shaft segments depends on the selected system:

| Configuration | Number of joints | Number of shaft segments |
|---|---:|---:|
| Single Cardan | 1 | 2 |
| Double Cardan | 2 | 3 |
| Triple Cardan | 3 | 4 |

Each shaft is displayed using a different color to improve visual separation.

---

## Figure C — Phase Visualization

The phase visualization presents the relative clocking angle between adjacent Cardan joints.

<p align="center">
  <img src="images/figure-c-phase-visualization.png" alt="Cardan joint phase visualization" width="900">
</p>

### End View

The end view displays:

- The phase reference line
- The relative yoke orientation
- The phase angle in degrees
- Clockwise or counterclockwise direction

### Side View

The side view provides a simplified visual interpretation of yoke orientation.

As the phase angle changes, the moving yoke representation transitions between:

```text
Circle-like → Ellipse-like → Line-like
```

Typical interpretations are:

```text
φ = 0°, 180°, 360°  → Face-on representation
φ = 90°, 270°       → Edge-on representation
```

The side-view figure is a schematic representation intended to clarify phase orientation. It is not a detailed three-dimensional CAD model of the joint.

---

## How to Use

1. Open the Streamlit application.
2. Select the desired Cardan configuration.
3. Enter the shaft misalignment angles.
4. Enter the current phase angles.
5. Select the optimization step.
6. Click **Run analysis**.
7. Review the current and optimized velocity-ratio curves.
8. Read the optimum phase values from the analysis summary.
9. Enter the optimum phase values into the `φ₁` and `φ₂` sliders.
10. Click **Run analysis** again to visualize the optimized phase configuration.
11. Inspect the shaft geometry and phase-visualization figures.

---

## Run in Streamlit

[![Open Interactive Application](https://img.shields.io/badge/Open-Interactive%20Application-success)](https://cardanjoint-optimization-tool-v10-y4tdutpuvokj2u2m8sqfee.streamlit.app/)

---

## Local Installation

Clone the repository:

```bash
git clone https://github.com/furk4nkasap/Cardanjoint-optimization-tool-v1.0.git
```
Enter the project directory:

```bash
cd Cardanjoint-optimization-tool-v1.0
```

Install the required packages:

```bash
pip install -r requirements.txt
```

Start the Streamlit application:

```bash
streamlit run streamlit_app.py
```

The application will open automatically in your default web browser. If it does not, open the local URL displayed in the terminal (typically `http://localhost:8501`).

---

## Requirements

```text
streamlit
numpy
matplotlib
```

## Project Structure

```text
Cardanjoint-optimization-tool-v1.0/

├── images/
│   ├── interface-controls.png
│   ├── analysis-summary.png
│   ├── figure-a-velocity-ratio.png
│   ├── figure-b-shaft-geometry.png
│   └── figure-c-phase-visualization.png
│
├── cardan_core.py
├── streamlit_app.py
├── requirements.txt
├── LICENSE
└── README.md
```

---

## Current Limitations

The current version:

- Uses a discrete brute-force phase search
- Does not use gradient-based or continuous optimization
- Treats the shafts and joints as ideal rigid kinematic elements
- Does not calculate transmitted torque
- Does not calculate bearing reaction forces
- Does not include joint friction
- Does not include backlash or clearance
- Does not include shaft flexibility
- Does not calculate torsional natural frequencies
- Does not perform stress or fatigue analysis
- Does not include efficiency or power-loss calculations
- Uses a schematic rather than three-dimensional phase visualization

---

## Future Work

Planned improvements may include:

- Continuous phase optimization
- Faster optimization algorithms
- Optimization progress indication
- CSV and Excel result export
- Automatic report generation
- Three-dimensional shaft visualization
- Torque-transmission analysis
- Joint efficiency calculation
- Bearing reaction-force calculation
- Flexible shaft modeling
- Torsional vibration analysis
- Natural-frequency analysis
- Multiple optimization objectives
- Parameter-sweep studies
- Integration with multibody dynamics software

---

## Engineering Scope

This application is intended for:

- Educational studies
- Preliminary Cardan shaft configuration analysis
- Kinematic phase-angle investigation
- Visualization of universal-joint behavior
- Comparison of single, double, and triple Cardan layouts
- Early-stage engineering evaluation

The software should not be used as the sole basis for production design without additional validation, dynamic analysis, structural analysis, and physical testing.

---

## Author

**Furkan Kasap**  
Automotive Engineer  

GitHub: [furk4nkasap](https://github.com/furk4nkasap)

---

## License

This project is distributed under the **MIT License**.

See the [LICENSE](LICENSE) file for details.

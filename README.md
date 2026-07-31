# Cardan Joint Engineering Tool v2.2.0

An interactive engineering application for understanding, comparing, and optimizing **single, double, and triple Cardan joint systems**.

The application shows how shaft misalignment and yoke phase angles affect output-speed fluctuation, then searches for phase angles that reduce that fluctuation.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![Streamlit](https://img.shields.io/badge/Interface-Streamlit-FF4B4B.svg)
![SciPy](https://img.shields.io/badge/Optimization-SciPy-8CAAE6.svg)
![Plotly](https://img.shields.io/badge/Interactive%203D-Plotly-3F4F75.svg)
![Analysis](https://img.shields.io/badge/Analysis-Kinematic-success.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

<p align="center">
  <a href="https://cardanjoint-optimization-tool-v10-y4tdutpuvokj2u2m8sqfee.streamlit.app/">
    <img src="https://img.shields.io/badge/Open-Live%20Application-success?style=for-the-badge" alt="Open the live Streamlit application">
  </a>
</p>

> The interface supports both **English** and **Turkish**.

---

## What problem does this tool solve?

A Cardan joint can transmit rotation between two shafts whose axes are not aligned. However, when the joint operates at a misalignment angle, a constant input speed does not always produce a perfectly constant output speed.

During one revolution, the output shaft may repeatedly accelerate and decelerate even though the input shaft rotates steadily.

This application helps you:

- calculate that speed fluctuation,
- compare single, double, and triple Cardan layouts,
- study the effect of shaft misalignment angles,
- study the effect of yoke phase or clocking angles,
- find phase angles that minimize output-speed unevenness,
- validate the optimized result on a denser calculation grid,
- visualize the shaft geometry and phase relationship,
- animate the shafts, yokes, and crosses in an interactive 3D engineering view,
- export the results and renderer-independent 3D scene data for further analysis.

### In one sentence

> Enter the shaft angles, run the analysis, and the application shows how uneven the output speed is and which phase angles provide the best kinematic compensation.

---

## Who is this project for?

This tool is suitable for:

- automotive and mechanical engineering students,
- driveline and vehicle-dynamics studies,
- engineers investigating universal-joint phasing,
- preliminary shaft-layout comparisons,
- educational demonstrations of Cardan-joint kinematics,
- researchers who need reusable Python calculation functions.

No programming knowledge is required to use the Streamlit interface.

---

# Quick Start — First Analysis

The easiest way to understand the application is to run one analysis with the default values.

## Option A — Use the online application

1. Open the [live Streamlit application](https://cardanjoint-optimization-tool-v10-y4tdutpuvokj2u2m8sqfee.streamlit.app/).
2. Select **Türkçe** or **English** at the top of the sidebar.
3. Keep the default **3 Cardan — Triple** configuration.
4. Keep the default angles:

| Setting | First-run value |
|---|---:|
| β₁ | 25° |
| β₂ | 25° |
| β₃ | 25° |
| φ₁ | 0° |
| φ₂ | 0° |
| θ₀ | 0° |

5. The default **Standard analysis** runs automatically. You do not need to press a button after every slider change.
6. Open the **Overview** tab and compare the current and optimized unevenness values.
7. Review the optimum `φ₁` and `φ₂` values.
8. Press **Apply optimum phases and rerun** to move the optimum phases into the controls.
9. Open **Interactive 3D** and press **Play** to watch the current or optimized mechanism over one complete input-shaft revolution.
10. Inspect the velocity graph, shaft geometry, phase visualization, and phase map.
11. Open **Data & Export** to download Excel, CSV, or JSON results.

For a more expensive continuous global search, open **Advanced settings** and enable **Ultra-accurate optimization**. Ultra mode is run manually so that moving a slider does not start a global search repeatedly.

## Option B — Run it on Windows

1. Download or clone this repository.
2. Double-click:

```text
install_windows.bat
```

3. After the installation is complete, double-click:

```text
run_windows.bat
```

4. The application should open automatically in your web browser.

---

# Understanding the Inputs

## 1. Cardan configuration

Choose the number of consecutive universal joints in the system.

| Configuration | What it represents | Optimized phase variables |
|---|---|---|
| Single Cardan | One joint connecting two shafts | None |
| Double Cardan | Two consecutive joints | φ₁ |
| Triple Cardan | Three consecutive joints | φ₁ and φ₂ |

A single joint can be analyzed, but phase optimization is not applicable because there is no second joint whose fluctuation can compensate for the first one.

---

## 2. Misalignment angles — β

`β₁`, `β₂`, and `β₃` are the angular misalignments between consecutive shaft axes.

```text
β₁ → misalignment across Joint 1
β₂ → misalignment across Joint 2
β₃ → misalignment across Joint 3
```

The interface allows:

```text
0° ≤ β ≤ 60°
```

In general, increasing a joint's misalignment angle increases the speed fluctuation generated by that joint.

> β describes shaft-axis geometry. It is not a phase angle.

---

## 3. Phase angles — φ

`φ₁` and `φ₂` describe the relative clocking of consecutive yokes.

```text
φ₁ → relative phase between Joint 1 and Joint 2
φ₂ → relative phase between Joint 2 and Joint 3
```

The phase angle does not remove energy and does not act as physical damping. It shifts the angular position of one joint's periodic speed fluctuation relative to another joint's fluctuation.

When one joint tends to accelerate the shaft while another tends to decelerate it, the two effects can partially or ideally cancel each other.

The application uses the following sign convention:

```math
\theta_{next}=\theta_{out}-\phi
```

The kinematic speed response repeats every 180°:

```text
φ, φ + 180°, and φ + 360° produce the same speed-ratio response.
```

The optimizer, phase map, and normal phase controls therefore use the unique interval:

```text
0° ≤ φ ≤ 180°
```

The `180°` endpoint is kinematically equivalent to `0°`.

---

## 4. Initial angular reference — θ₀

`θ₀` changes the angular position at which the plotted input-shaft cycle begins.

It normally shifts the curve horizontally but does not change the maximum-to-minimum unevenness. The Hooke-joint speed response has a 180° fundamental period, so evaluating one `0°–180°` period is sufficient for the metric.

---

## 5. Phase-search step

The phase-search step controls the resolution of the deterministic coarse phase map.

| Step | Effect |
|---:|---|
| 10°–15° | Faster, but coarse |
| 5° | Recommended starting point |
| 2° | Finer map, more computation |
| 1° | Fine map, highest grid cost |

For a triple Cardan system, the approximate number of coarse phase combinations is:

```math
N=\left(\frac{180}{s}\right)^2
```

where `s` is the phase-search step in degrees.

Example:

```text
5° step → 36 × 36 = 1,296 phase combinations
1° step → 180 × 180 = 32,400 phase combinations
```

The continuous optimization modes can return decimal phase values, but the coarse grid is still retained for visualization, repeatability, and fallback protection.

---

# Choosing the Analysis Quality

The normal interface is deliberately simple.

## Standard analysis — default

Standard analysis uses:

- a deterministic coarse phase map,
- local sub-degree refinement,
- independent validation,
- automatic recalculation when an input changes.

This mode is suitable for normal exploration and most preliminary engineering comparisons.

## Ultra-accurate optimization — optional

Open **Advanced settings** and enable **Ultra-accurate optimization** when you need a continuous global phase search.

Ultra mode uses:

1. the deterministic coarse phase map,
2. global Differential Evolution,
3. derivative-free Powell refinement,
4. deterministic coarse-result fallback,
5. denser independent validation.

Ultra mode is intentionally manual. Change the inputs first, then press **Run ultra optimization**. This prevents a global optimization from starting after every slider movement.

## Expert algorithm controls

The numerical core still contains four methods:

- Fast Grid,
- Grid + Local Refinement,
- Differential Evolution,
- Hybrid Differential Evolution + Powell.

They are hidden from normal users. Enable **Show expert algorithm controls** under **Advanced settings** only when benchmarking, testing, or comparing algorithms.

## Angle-control precision

Normal sliders and number boxes use the same `0.5°` step. This prevents the slider and direct-entry box from representing different values.

Enable **Use precise 0.01° angle controls** under **Advanced settings** when you need to enter or apply continuous optimizer results without rounding.

# How to Read the Results

## Current unevenness

This is the output-speed fluctuation produced by the phase values currently entered in the sidebar.

## Optimized unevenness

This is the fluctuation produced by the optimum phase values accepted by the selected optimization method.

Lower is better.

The reported unevenness is:

```math
U(\%)=100\frac{q_{max}-q_{min}}{|\bar q|}
```

where:

- `qmax` is the maximum instantaneous speed ratio,
- `qmin` is the minimum instantaneous speed ratio,
- `q̄` is the mean speed ratio over one complete revolution,
- `q = ωout / ωin`.

## RMS speed error

The RMS speed error represents the overall magnitude of the speed-ratio deviation over the complete cycle. It is useful because two curves can have similar maximum-to-minimum ranges but different overall fluctuation shapes.

## Maximum positive and negative error

These values show the largest acceleration-side and deceleration-side deviations relative to the mean ratio.

## Status: OK or Warning

The application currently uses a project criterion of:

```text
Unevenness ≤ 5% → OK
Unevenness > 5% → Warning
```

> The 5% value is not a universal driveline design standard. It is only the current project criterion.

## Optimizer objective versus dense validation

The speed response repeats every 180°. The optimizer evaluates the unique `0°–180°` period and then checks the accepted optimum on a denser independent grid.

Dense validation remains active because it protects against small peaks that may fall between optimizer sample points. It is not shown continuously on the main screen. The application displays a warning only when the dense result differs materially from the optimizer objective.

Detailed values, function-evaluation counts, iterations, runtime, solver message, and random seed are available under:

```text
Advanced optimization and validation details
```

Calculations and exported files retain full numerical precision. The main interface rounds percentages and angles to readable values.

---

# Application Tabs

## Overview

Shows:

- current and optimized unevenness,
- percentage improvement,
- optimum phase angles,
- optimized status,
- a compact minimum/maximum/RMS summary.

Detailed engineering metrics and optimizer diagnostics are available in collapsed advanced sections.

## Velocity

Plots the instantaneous total speed ratio over one complete input-shaft revolution.

```math
q_{total}=\frac{\omega_{out}}{\omega_{in}}
```

The current and optimized curves are displayed together so that the improvement can be compared directly.

## Geometry & Phase

Shows:

- the schematic two-dimensional shaft arrangement,
- the β misalignment angles,
- the current yoke phase representation,
- the optimized yoke phase representation.

The phase drawings are engineering schematics. They are not detailed three-dimensional CAD models.

## Interactive 3D

The **Interactive 3D** tab animates the selected current or optimized configuration. It shows:

- every shaft centerline,
- the input and output yokes of each joint,
- the universal-joint cross,
- the full `0°–360°` input-shaft revolution,
- a synchronized moving point on the total speed-ratio graph,
- orbit, pan, zoom, and preset camera views,
- lightweight, balanced, and smooth animation detail levels.

The viewer does not calculate a second independent kinematic model. It consumes the joint angles generated by `cardan_core.py`, so the 3D motion and numerical speed-ratio curve use the same source data. The core also calculates continuous unit quaternions for shafts, yokes, and crosses.

The first production 3D release uses Plotly WebGL because it deploys reliably through Streamlit without an external JavaScript build server. The scene is a **canonical planar engineering schematic**: the entered `β` angles and yoke phases are preserved, but the viewer does not infer an arbitrary spatial driveline layout from the scalar angles alone.

A scene JSON file can be downloaded directly from this tab. It contains shaft points and directions, joint centers, yoke axes, shaft rotation angles, and quaternion trajectories for future Three.js, CAD, or external visualization workflows.

## Phase Map

For a double system, this tab shows how unevenness changes with `φ₁`.

For a triple system, it shows a two-dimensional `φ₁–φ₂` heat map. Lower regions indicate phase combinations with lower calculated unevenness.

The phase map is calculated from the deterministic coarse grid even when a continuous optimization method is selected.

## Data Export

The application can export:

For Excel, first press **Prepare Excel workbook**. The workbook is generated only on request so that live slider updates remain fast. Then press the displayed Excel download button.

| File | Contents |
|---|---|
| `Cardan_Engineering_Analysis.xlsx` | Formatted engineering workbook with summary, inputs, comparison, curves, trajectory, phase landscape, and diagnostics |
| `cardan_velocity_curves.csv` | Input angle, current speed ratio, optimized speed ratio, and speed errors |
| `cardan_analysis_summary.json` | Inputs, optimum phases, metrics, method, and diagnostics |
| `cardan_kinematic_trajectory.json` | Joint input/output angles and individual/total speed ratios |
| `cardan_3d_scene_current.json` / `cardan_3d_scene_optimized.json` | Planar scene geometry, yoke axes, and quaternion pose trajectories |

The Excel workbook contains these sheets:

```text
Summary / Özet
Inputs / Girişler
Comparison / Karşılaştırma
Velocity Curves / Hız Eğrileri
Kinematic Trajectory / Kinematik Yörünge
Phase Landscape / Faz Haritası
Diagnostics / Teşhisler
```

Column names in the preview, CSV, and Excel workbook follow the selected interface language. The trajectory JSON remains suitable for future three-dimensional visualization and external post-processing.

---


# Interface Behavior in v2.2.0

- Language selection is located at the top of the sidebar so it remains visible on narrow screens.
- All normal angle sliders and number boxes use matching `0.5°` steps.
- Standard analysis updates automatically and uses Streamlit caching.
- Ultra optimization is hidden under **Advanced settings** and runs manually.
- The four low-level optimizer choices are hidden unless expert controls are enabled.
- Main percentages and phase angles use two decimal places.
- Speed ratios use five decimal places.
- Full precision is preserved internally and in exported files.
- Optimizer and dense-validation diagnostics are collapsed by default.
- The shaft geometry and phase figures use more compact dimensions.
- Excel export is available alongside CSV and JSON.
- A dedicated Interactive 3D tab animates current and optimized mechanisms.
- The speed-ratio marker is synchronized with the animated input angle.
- 3D scene geometry and quaternion trajectories can be exported as JSON.


# Supported Configurations

## Single Cardan

The total speed ratio is the ratio generated by one Hooke joint:

```math
q_{total}=q_1
```

There is no phase optimization.

## Double Cardan

The total ratio is:

```math
q_{total}=q_1q_2
```

The optimizer searches for `φ₁`.

Under the correct ideal equal-angle and yoke-phase condition, a double Cardan arrangement can theoretically compensate for the first joint's speed fluctuation.

## Triple Cardan

The total ratio is:

```math
q_{total}=q_1q_2q_3
```

The optimizer searches for the combination of `φ₁` and `φ₂` that minimizes the final output-speed unevenness.

---

# Installation

## Requirements

- Python 3.10 or newer is recommended
- Internet access is required only when installing packages
- A modern web browser

Python packages:

```text
streamlit >= 1.37
numpy >= 1.26
matplotlib >= 3.8
scipy >= 1.15
xlsxwriter >= 3.2
plotly >= 6.5
```

## Clone the repository

```bash
git clone https://github.com/furk4nkasap/Cardanjoint-optimization-tool-v1.0.git
cd Cardanjoint-optimization-tool-v1.0
```

## Install the dependencies

```bash
python -m pip install -r requirements.txt
```

## Start the application

```bash
python -m streamlit run streamlit_app.py
```

Streamlit normally opens the application automatically. If it does not, open the local address displayed in the terminal, usually:

```text
http://localhost:8501
```

---

# Project Structure

```text
Cardan-Joint-Engineering-Tool/
│
├── streamlit_app.py
├── cardan_core.py
├── cardan_3d_viewer.py
├── requirements.txt
├── README.md
├── CHANGELOG.md
├── LICENSE
├── benchmark_optimizers.py
├── BENCHMARK_REPORT.txt
├── TEST_REPORT.txt
├── install_windows.bat
├── run_windows.bat
│
└── tests/
    ├── test_cardan_core.py
    ├── test_3d_viewer.py
    └── smoke_streamlit_app.py
```

### Main files

| File | Purpose |
|---|---|
| `streamlit_app.py` | English/Turkish user interface |
| `cardan_core.py` | Kinematic equations, optimizers, validation, metrics, trajectory data, scene axes, and quaternion outputs |
| `cardan_3d_viewer.py` | Interactive Plotly WebGL mechanism animation and synchronized response graph |
| `requirements.txt` | Python dependencies |
| `tests/test_cardan_core.py` | Numerical, periodicity, scene-geometry, orthogonality, and quaternion regression tests |
| `tests/test_3d_viewer.py` | Interactive 3D figure and animation regression tests |
| `tests/smoke_streamlit_app.py` | Interface execution-path test |
| `benchmark_optimizers.py` | Reproducible comparison of optimization methods |
| `CHANGELOG.md` | Version history |
| `LICENSE` | MIT license |

---

# Running the Tests

From the project directory, run:

```bash
python -m unittest discover -s tests -v
```

The regression suite checks important behaviors such as:

- zero misalignment producing `q = 1`,
- ideal double-Cardan compensation,
- phase-grid periodicity,
- repeatability with a fixed random seed,
- continuous optimization not degrading the deterministic baseline,
- dense-validation diagnostics,
- trajectory consistency,
- preservation of the entered shaft misalignment angles in the planar 3D scene,
- input/output yoke-axis orthogonality,
- unit and sign-continuous quaternion trajectories,
- interactive 3D animation frame construction,
- finite numerical and plotting outputs,
- complete Streamlit execution path,
- valid multi-sheet XLSX export payload.

---

# Technical Model

For one ideal Hooke universal joint, the instantaneous angular velocity ratio is:

```math
q=\frac{\omega_{out}}{\omega_{in}}
=\frac{\cos\beta}{1-\sin^2\beta\cos^2\theta}
```

The angular-position relationship is implemented in a quadrant-preserving form equivalent to:

```math
\tan\theta_{out}=\frac{\tan\theta_{in}}{\cos\beta}
```

For consecutive joints, the next joint receives the previous output angle with the selected phase shift:

```math
\theta_{2,in}=\theta_{1,out}-\phi_1
```

```math
\theta_{3,in}=\theta_{2,out}-\phi_2
```

The total instantaneous speed ratio is the product of the individual joint ratios:

```math
q_{total}=\prod_{i=1}^{n}q_i
```

The optimizer minimizes:

```math
U(\boldsymbol{\phi})
=100\frac{q_{max}-q_{min}}{|\bar q|}
```

over the active phase variables.

---

# Important Limitations

This software performs an **ideal rigid-body kinematic analysis**.

The current model does not include:

- mass or rotational inertia,
- transmitted torque,
- bearing reaction forces,
- shaft or joint elasticity,
- backlash or clearance,
- friction,
- joint efficiency or power loss,
- stress or fatigue,
- torsional natural frequencies,
- torsional vibration,
- manufacturing tolerances,
- physical damping,
- detailed three-dimensional CAD contact,
- automatic reconstruction of a general spatial shaft installation from scalar beta angles,
- photorealistic materials or manufacturing-level yoke geometry.

The application should not be used as the sole basis for a production driveline design. Production decisions require additional dynamic, structural, durability, tolerance, and physical-test validation.

---

# Current Development Roadmap

Completed in v2.2.0:

- three-dimensional planar kinematic scene data,
- yoke and cross orientation frames,
- quaternion-based pose output,
- interactive Plotly WebGL mechanism visualization,
- synchronized graph and 3D animation.

Planned next stages include:

- a bundled Three.js viewer with procedural solid geometry, lighting, and materials,
- user-defined spatial shaft-axis vectors and shaft lengths,
- GLTF yoke and cross models,
- side-by-side current/optimized 3D comparison,
- parameter sweep studies,
- multi-objective optimization,
- automatic engineering reports,
- future torque and dynamic-analysis extensions.

---

# Version 2.2.0 Highlights

Version 2.2.0 adds:

- a dedicated Interactive 3D application tab,
- animated single, double, and triple Cardan mechanisms,
- current and optimized configuration selection,
- orbit, pan, zoom, and camera presets,
- synchronized total speed-ratio graph animation,
- renderer-independent planar scene geometry,
- shaft, input-yoke, output-yoke, and cross quaternions,
- downloadable 3D scene JSON,
- orthogonality, quaternion, and viewer regression tests,
- Plotly deployment dependency with graceful fallback.

# Version 2.1.2 Highlights

Version 2.1.2 adds:

- automatic cached Standard analysis,
- Ultra optimization under Advanced settings,
- hidden expert-only algorithm controls,
- matching `0.5°` normal slider and number-input steps,
- optional precise `0.01°` controls,
- compact result formatting and figures,
- localized CSV/data-preview headings,
- validated multi-sheet Excel export,
- XLSX export smoke testing.

# Version 2.1.1 Numerical Highlights

Version 2.1.1 adds:

- 180° fundamental-period optimization and validation,
- a unique `0°–180°` phase-search and phase-map domain,
- half as many input-angle objective samples at unchanged 0.5° spacing,
- four times fewer triple-Cardan coarse phase combinations,
- explicit periodicity regression tests.

Version 2.1 introduced:

- four selectable optimization methods,
- global continuous Differential Evolution,
- hybrid Differential Evolution and Powell refinement,
- deterministic coarse-map fallback,
- independent dense fundamental-period validation,
- optimization diagnostics,
- CSV and JSON exports,
- a renderer-independent kinematic trajectory API,
- expanded numerical regression tests,
- bilingual English/Turkish operation.

See [CHANGELOG.md](CHANGELOG.md) for the complete version history.

---

# Author

**Furkan Kasap**  
Automotive Engineer

GitHub: [furk4nkasap](https://github.com/furk4nkasap)

---

# License

This project is distributed under the **MIT License**.

See the [LICENSE](LICENSE) file for details.


## Streamlit Cloud dependency troubleshooting

If deployment reports `ModuleNotFoundError: No module named 'xlsxwriter'`, verify that the updated `requirements.txt` is committed in the same directory as `streamlit_app.py` or in the repository root. The required entry is:

```text
XlsxWriter==3.2.9
```

After committing the file, reboot the Streamlit Community Cloud app. Version 2.1.3 also keeps the main analysis interface running if the Excel dependency is temporarily unavailable; only Excel export is disabled until the package is installed.


## Interactive 3D dependency troubleshooting

If deployment reports `ModuleNotFoundError: No module named 'plotly'`, verify that the current `requirements.txt` is committed in the repository root and includes:

```text
plotly>=6.5,<7
```

Reboot the Streamlit Community Cloud application after committing the dependency file. If Plotly is temporarily unavailable, the numerical analysis, Matplotlib figures, CSV, JSON, and Excel functions remain usable; only the Interactive 3D tab is disabled.

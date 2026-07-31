# Cardan Joint Engineering Tool v2.1

Interactive Python/Streamlit application for the kinematic analysis, phase optimization, validation, visualization, and data export of single, double, and triple Cardan (Hooke universal-joint) systems.

## What changed in v2.1

Version 2.1 keeps the v2 architecture intact: `cardan_core.py` contains the numerical model and plotting functions, while `streamlit_app.py` contains the bilingual interface. The core API is now version 4.

The release adds:

- Four optimization modes:
  - Fast deterministic grid
  - Grid plus periodic local refinement
  - Global continuous Differential Evolution
  - Hybrid Differential Evolution plus continuous Powell polishing
- Independent dense full-cycle validation after optimization
- Optimization diagnostics:
  - convergence/acceptance status
  - function-evaluation count
  - iterations/generations
  - elapsed time
  - optimizer objective value
  - dense-validation value and delta
  - solver message and random seed
- Renderer-independent kinematic trajectory API
- Kinematic trajectory JSON export for future Three.js integration
- SciPy dependency and expanded regression tests

## Numerical architecture

### Coarse landscape

A deterministic phase grid is always evaluated for double and triple Cardan configurations. It is used to:

1. provide a reproducible baseline,
2. generate the phase/unevenness landscape,
3. supply an initial candidate to the continuous optimizer,
4. provide a safe fallback if a stochastic run does not improve the solution.

For phase step `s`, the triple-system map contains approximately:

```math
N=\left(\frac{360}{s}\right)^2
```

phase combinations.

### Continuous global optimization

The continuous modes use `scipy.optimize.differential_evolution` with phase bounds:

```text
0° ≤ φ₁ ≤ 360°
0° ≤ φ₂ ≤ 360°
```

Every candidate is normalized periodically, so `360°` is equivalent to `0°`.

The hybrid mode then starts a bounded Powell search from the best accepted global candidate. Because the objective contains `max` and `min` operations, it is not assumed to be smoothly differentiable; a derivative-free method is therefore used.

### Objective function

The optimization objective is:

```math
U=100\frac{q_{\max}-q_{\min}}{|\bar q|}
```

where:

```math
q=\frac{\omega_{out}}{\omega_{in}}
```

The objective is evaluated over 720 uniformly distributed input-shaft positions.

### Independent validation

After the optimum is selected, the current and optimized systems are evaluated again on an independent user-selectable grid:

- 720
- 1,440
- 3,600
- 7,200
- 14,400
- 36,000 samples

The application reports the difference between the optimizer objective and the dense-validation result. The validated value is used in the engineering-metric cards.

## Optimization modes

### Fast Grid

- Fully deterministic
- Generates the phase map
- Fastest option
- Final phase values are limited to grid nodes

### Grid + Local Refinement

- Fully deterministic
- Refines the best coarse candidate in a periodic local neighborhood
- Supports sub-degree results
- Does not claim a global continuous optimum

### Global Continuous — Differential Evolution

- Global stochastic search
- Continuous phase variables
- Fixed seed provides repeatability
- Coarse candidate is retained if it is better

### Hybrid — Differential Evolution + Powell

- Recommended engineering mode
- Uses Differential Evolution for global exploration
- Uses bounded Powell polishing for continuous local improvement
- Retains the deterministic coarse map and fallback

## Kinematic trajectory API

The new `calculate_kinematic_trajectory()` function returns a `KinematicTrajectory` object containing:

- input-shaft rotation
- each joint's input angle
- each joint's output angle
- each joint's instantaneous speed ratio
- total instantaneous speed ratio

The output uses the same phase convention as the numerical model:

```math
\theta_{next}=\theta_{out}-\phi
```

This API is independent of Streamlit and any renderer. It is intended as the data foundation for the future Three.js viewer.

## Installation

### Windows quick setup

Run:

```text
install_windows.bat
```

Then launch with:

```text
run_windows.bat
```

### Manual setup

```bash
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

## Project files

```text
cardan_core.py                 numerical model and plots
streamlit_app.py               bilingual Streamlit interface
requirements.txt               Python dependencies
tests/test_cardan_core.py      numerical regression tests
benchmark_optimizers.py        reproducible optimizer comparison
BENCHMARK_REPORT.txt           sample benchmark output
TEST_REPORT.txt                release validation record
CHANGELOG.md                   version history
install_windows.bat            Windows dependency installer
run_windows.bat                Windows launcher
```

## Running tests

```bash
python -m unittest discover -s tests -v
```

## Model limitations

The model remains kinematic only. It does not include:

- mass and inertia
- transmitted torque
- bearing reactions
- elasticity
- backlash
- friction
- stress or fatigue
- torsional vibration
- efficiency or power loss

The 5% status limit is a project criterion and must not be interpreted as a universal driveline design standard.

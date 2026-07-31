# Changelog

## v2.2.0 — Interactive 3D Kinematic Viewer

### Added

- Dedicated **Interactive 3D** Streamlit tab.
- Plotly WebGL animation for single, double, and triple Cardan systems.
- Current/optimized configuration selector.
- Isometric, top, side, and front camera presets.
- Orbit, pan, zoom, play/pause, and input-angle animation slider.
- Synchronized moving marker on current and optimized total speed-ratio curves.
- `PlanarSceneGeometry` and `KinematicScene` dataclasses.
- Canonical planar shaft-axis and joint-center generation.
- Input-yoke, output-yoke, shaft, and cross unit-quaternion trajectories.
- Sign-continuous quaternion output for downstream renderers.
- Downloadable 3D scene JSON with geometry, axes, angles, and quaternion poses.
- Graceful Plotly dependency fallback.
- Scene geometry, yoke orthogonality, quaternion, and viewer animation tests.

### Changed

- Core API version increased from 5 to 6.
- Application version increased to 2.2.0.
- Requirements now include `plotly>=6.5,<7`.
- Model scope documentation now distinguishes the canonical planar schematic from a general spatial CAD reconstruction.

### Preserved

- Existing kinematic equations, 180° optimization period, optimizers, dense validation, 2D figures, and exports.

## v2.1.3 — Deployment dependency hotfix

- Pins `XlsxWriter==3.2.9` in `requirements.txt`.
- Makes the Excel dependency optional at application import time.
- Prevents the whole Streamlit app from crashing when XlsxWriter is missing.
- Shows a localized Excel-unavailable warning while keeping analysis, plots, CSV, and JSON exports operational.
- Updates deployment troubleshooting instructions.

## v2.1.2 — UX Simplification and Excel Export

### Added

- Automatic cached Standard analysis after parameter changes.
- Optional Ultra-accurate optimization under Advanced settings.
- Expert-only access to all four core optimization methods.
- Optional precise `0.01°` angle-control mode.
- Multi-sheet localized Excel engineering workbook export.
- XLSX archive validation in the Streamlit smoke test.

### Changed

- Moved the English/Turkish selector to the top of the sidebar.
- Standardized normal angle sliders and number boxes to the same `0.5°` step.
- Reduced phase-input controls to the unique `0°–180°` interval.
- Reduced visible percentage and angle precision while retaining full internal precision.
- Moved engineering metrics, optimizer diagnostics, and dense-validation values into collapsed sections.
- Made dense validation silent unless a meaningful discrepancy is detected.
- Localized data-preview, CSV, and Excel column headings.
- Reduced and centered shaft-geometry and phase figures.
- Simplified the main result area to the values needed for engineering decisions.

### Preserved

- All v2.1.1 numerical equations, 180° fundamental-period reduction, global optimization, validation, and trajectory APIs.

## v2.1.1 — 180° Fundamental-Period Optimization

- Reduced the input-angle objective and dense validation from 360° to the unique 180° kinematic period.
- Preserved the previous 0.5° objective spacing with 360 rather than 720 samples.
- Reduced the phase grid and optimization bounds from `[0°, 360°)` to `[0°, 180°)`.
- Reduced triple-Cardan coarse-map candidates by 75% for the same phase step.
- Kept full 360° velocity plots and trajectory exports for readability and future animation.
- Added regression tests for 180° input-angle and phase equivalence.

## v2.1 — Global Optimization and Trajectory Foundation

### Added

- `OptimizationMethod` enum with grid, local-refinement, Differential Evolution, and hybrid modes.
- `OptimizationSettings` dataclass for reproducible optimizer configuration.
- `OptimizationDiagnostics` dataclass containing convergence, evaluation count, iteration count, runtime, objective, validation delta, and seed.
- SciPy Differential Evolution integration.
- Bounded Powell polishing in hybrid mode.
- Independent dense validation with selectable sample count.
- Deterministic coarse-result fallback when a global run is worse.
- `KinematicTrajectory` dataclass.
- `calculate_kinematic_trajectory()` renderer-independent API.
- Kinematic trajectory JSON export.
- Global optimizer controls and diagnostics in the Streamlit UI.
- Four additional numerical regression tests.
- Optimizer benchmark utility.
- Windows installation and launch scripts.

### Changed

- Core API version increased from 3 to 4.
- Application version increased from 2.0 to 2.1.
- Phase map now shows the selected local/global optimum even when it lies between grid nodes.
- Reported engineering metrics now use the dense validation grid.
- Analysis JSON now includes optimizer settings and diagnostics.
- `calculate_analysis()` accepts `OptimizationSettings` while retaining the old `refine=` compatibility path.

### Preserved

- Existing Hooke-joint equations and phase sign convention.
- Single, double, and triple Cardan modes.
- Deterministic phase landscape generation.
- Local sub-degree refinement.
- Dark bilingual interface.
- CSV curve export and existing 2D figures.

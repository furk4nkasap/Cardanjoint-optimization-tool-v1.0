# Cardan Joint Kinematics & Phase Optimization Tool

Interactive Python software for **kinematic analysis, visualization, and phase optimization** of single, double, and triple Cardan (Hooke's) joint systems.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Google%20Colab-orange.svg)
![Status](https://img.shields.io/badge/Status-Active-success.svg)

---

## Overview

Cardan Joint Kinematics & Phase Optimization Tool is an interactive Python application developed to analyze, visualize, and optimize the kinematic behavior of single, double, and triple Cardan (Hooke's) joint systems.

The software evaluates angular velocity fluctuations caused by shaft misalignment and automatically determines the optimum phase (clocking) angles that minimize velocity ripple.

---

### Figure A – Angular Velocity Ratio & Velocity Ripple

The figure below compares the angular velocity ratio before and after phase optimization.

The optimization algorithm automatically determines the optimum phase (clocking) angles that minimize velocity ripple. A velocity ripple below **10%** is generally considered an acceptable operating condition for Cardan shaft systems.

In this example, the initial velocity ripple of **15.39%** is reduced to **4.52%** after optimization. To achieve this optimized operating condition, the phase angles should be set to:

- **φ₁ = 90°**
- **φ₂ = 90°**

Applying these optimized phase angles results in a significantly smoother angular velocity transmission and a substantial reduction in velocity fluctuation.

<p align="center">
  <img src="images/figure-a-velocity-ripple.png" alt="Velocity Ripple Analysis" width="900">
</p>

---

## Features

- ✅ Single Cardan joint analysis
- ✅ Double Cardan joint analysis
- ✅ Triple Cardan joint analysis
- ✅ Automatic phase optimization
- ✅ Angular velocity ratio analysis (ωout / ωin)
- ✅ Velocity ripple evaluation
- ✅ Interactive graphical user interface (GUI)
- ✅ 2D shaft geometry visualization
- ✅ End-view and side-view phase visualization
- ✅ Misalignment angle analysis
- ✅ Google Colab compatible

---

## Interactive User Interface

The application provides an intuitive graphical interface for selecting the system type, defining shaft misalignment angles, adjusting phase angles, and performing automatic optimization.

<p align="center">
  <img src="images/interface.png" alt="User Interface" width="450">
</p>

---

## Figure B – 2D Shaft Geometry

The geometry window illustrates the shaft configuration and the relative misalignment angles between consecutive shafts.

<p align="center">
  <img src="images/geometry.png" alt="2D Geometry" width="350">
</p>

---

## Figure C – Phase (Clocking) Visualization

The phase visualization displays the optimized clocking angles between adjacent Cardan joints using both end-view and side-view representations.

<p align="center">
  <img src="images/phase-visualization.png" alt="Phase Visualization" width="900">
</p>

---

## Run in Google Colab

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1NyxubyRDLaJGNz_JJNoXK1A_juKGQTf5?usp=sharing)

---

## Installation

Clone the repository

```bash
git clone https://github.com/furk4nkasap/Cardanjoint-optimization-tool-v1.0.git
```

Install the required packages

```bash
pip install -r requirements.txt
```

Launch the notebook using **Jupyter Notebook** or **Google Colab**.

---

## Theory

This software implements the kinematic equations of Hooke's universal joints to evaluate:

- Angular velocity ratio
- Velocity ripple
- Shaft misalignment effects
- Phase (clocking) optimization

The application supports single, double, and triple Cardan shaft configurations and provides interactive visualization of the corresponding kinematic behavior.

---

## Project Structure

```text
Cardanjoint-optimization-tool-v1.0
│
├── images/
│   ├── figure-a-velocity-ripple.png
│   ├── interface.png
│   ├── geometry.png
│   └── phase-visualization.png
│
├── CardanJoint_Optimization.ipynb
├── requirements.txt
└── README.md
```

---

## Future Work

Planned improvements include:

- Dynamic analysis
- Torque transmission analysis
- Bearing reaction force calculation
- Torsional vibration analysis
- Flexible shaft modeling
- CSV/Excel export
- Performance optimization

---

## Author

**Furkan Kasap**

Automotive Engineer

Kocaeli University

GitHub: https://github.com/furk4nkasap

"""Independent reference models used only by the test-suite.

Nothing in this file imports or re-uses the Hooke formulas of ``cardan_core``.

1. ``vector_chain_ratio``  - a 3D rigid-body model.  The only physics used is
   that the two pin axes of a universal-joint cross stay perpendicular, i.e.
   the driven pin axis is perpendicular to both the driven shaft axis and the
   driving pin axis.  Shaft axes may have any spatial layout.
2. ``closed_form_bounds``  - the composite 2x2 linear map acting on
   (sin(theta), cos(theta)); its singular values give q_max and q_min.
3. ``theoretical_minimum_unevenness`` - rigorous lower bound that follows from
   the sub-multiplicativity of the 2x2 condition number.
"""

from __future__ import annotations

import numpy as np

_HELPER = np.array([0.3, 0.5, 0.8])


def rotate(axis, angle_rad, vector):
    axis = np.asarray(axis, dtype=float)
    axis = axis / np.linalg.norm(axis)
    vector = np.asarray(vector, dtype=float)
    return (
        vector * np.cos(angle_rad)
        + np.cross(axis, vector) * np.sin(angle_rad)
        + axis * np.dot(axis, vector) * (1.0 - np.cos(angle_rad))
    )


def planar_directions(betas_deg, signs=None):
    """Shaft unit vectors in the x-y plane; ``signs`` flips bend directions."""

    signs = [1.0] * len(betas_deg) if signs is None else signs
    angle = 0.0
    directions = [np.array([1.0, 0.0, 0.0])]
    for beta, sign in zip(betas_deg, signs):
        angle += sign * np.deg2rad(beta)
        directions.append(np.array([np.cos(angle), np.sin(angle), 0.0]))
    return directions


def _output_pin_angle(theta, directions, clocking_deg):
    first = directions[0]
    reference = np.cross(first, _HELPER)
    reference /= np.linalg.norm(reference)
    pin = rotate(first, theta, reference)
    last_index = len(directions) - 2
    for joint_index in range(len(directions) - 1):
        driven_axis = directions[joint_index + 1]
        driven_pin = np.cross(driven_axis, pin)
        driven_pin /= np.linalg.norm(driven_pin)
        if joint_index < last_index:
            pin = rotate(driven_axis, np.deg2rad(clocking_deg[joint_index]), driven_pin)
        else:
            pin = driven_pin
    last = directions[-1]
    e1 = np.cross(last, _HELPER)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(last, e1)
    return np.arctan2(np.dot(pin, e2), np.dot(pin, e1))


def vector_chain_ratio(directions, clocking_deg=(), samples=7200):
    """Return (theta_rad, q) over one input revolution from the 3D model.

    ``clocking_deg[j]`` is the physical angle between the two yokes carried by
    intermediate shaft ``j+1`` (0 = aligned, 90 = perpendicular).
    q is obtained by a periodic central difference, so its truncation error is
    O(h^2) with h = 2*pi/samples.
    """

    theta = np.linspace(0.0, 2.0 * np.pi, samples, endpoint=False)
    output = np.array([_output_pin_angle(t, directions, clocking_deg) for t in theta])
    output = np.unwrap(2.0 * output) / 2.0  # a pin axis is undirected
    if output[-1] < output[0]:
        output = -output
    deviation = output - theta
    step = theta[1] - theta[0]
    ratio = 1.0 + (np.roll(deviation, -1) - np.roll(deviation, 1)) / (2.0 * step)
    return theta, ratio


def unevenness_percent(ratio):
    ratio = np.asarray(ratio, dtype=float)
    return 100.0 * (ratio.max() - ratio.min()) / ratio.mean()


def closed_form_bounds(betas_deg, physical_phases_deg=()):
    """(q_min, q_max) from the singular values of the composite 2x2 map."""

    matrix = np.eye(2)
    for index, beta in enumerate(betas_deg):
        matrix = np.diag([1.0, np.cos(np.deg2rad(beta))]) @ matrix
        if index < len(physical_phases_deg):
            psi = np.deg2rad((90.0 - physical_phases_deg[index]) % 180.0)
            rotation = np.array([[np.cos(psi), -np.sin(psi)], [np.sin(psi), np.cos(psi)]])
            matrix = rotation @ matrix
    singular = np.linalg.svd(matrix, compute_uv=False)
    kappa = singular[0] / singular[1]
    return 1.0 / kappa, kappa


def closed_form_unevenness(betas_deg, physical_phases_deg=()):
    q_min, q_max = closed_form_bounds(betas_deg, physical_phases_deg)
    return 100.0 * (q_max - q_min)


def theoretical_minimum_unevenness(betas_deg):
    """Lower bound of the unevenness over all phase choices.

    kappa(AB) <= kappa(A) kappa(B) gives ln kappa(total) >= l_max - sum(others)
    with l_i = ln(1 / cos(beta_i)).
    """

    lengths = sorted(np.log(1.0 / np.cos(np.deg2rad(np.asarray(betas_deg, dtype=float)))))
    residual = max(0.0, lengths[-1] - sum(lengths[:-1]))
    kappa = np.exp(residual)
    return 100.0 * (kappa - 1.0 / kappa)

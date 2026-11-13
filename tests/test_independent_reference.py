"""Core kinematics versus an independent 3D cross-orthogonality model.

The reference model (tests/reference_model.py) never uses the Hooke formula.
Tolerance: the reference differentiates numerically on 7200 samples per
revolution (h = 8.7e-4 rad); the O(h^2) error on the extreme values is below
1e-4 percentage points of unevenness for the angles used, so 5e-4 is used.
"""

from __future__ import annotations

import numpy as np
import pytest

import cardan_core as core
import reference_model as ref

P = core.CardanParameters
DENSE = np.linspace(0.0, 180.0, 36000, endpoint=False)
TOL_PU = 5e-4


def _core_unevenness(betas, phases):
    keywords = {f"beta{i + 1}_deg": beta for i, beta in enumerate(betas)}
    keywords.update({f"phi{i + 1}_deg": phase for i, phase in enumerate(phases)})
    ratio = core.calculate_total_ratio(DENSE, P(mode=len(betas), **keywords))
    return ref.unevenness_percent(ratio), ratio.min(), ratio.max()


@pytest.mark.parametrize(
    "betas, phases",
    [
        ((30.0,), ()),
        ((25.0, 25.0), (0.0,)),
        ((25.0, 25.0), (90.0,)),
        ((20.0, 35.0), (30.0,)),
        ((20.0, 35.0), (150.0,)),
        ((43.02, 25.26, 47.51), (10.0, 77.0)),
        ((12.0, 40.0, 21.0), (125.0, 33.0)),
    ],
)
def test_planar_layout_matches_vector_model(betas, phases):
    _, ratio = ref.vector_chain_ratio(ref.planar_directions(betas), phases)
    unevenness, q_min, q_max = _core_unevenness(betas, phases)
    assert ref.unevenness_percent(ratio) == pytest.approx(unevenness, abs=TOL_PU)
    assert ratio.max() == pytest.approx(q_max, abs=1e-5)
    assert ratio.min() == pytest.approx(q_min, abs=1e-5)


def test_z_and_w_layouts_are_equivalent_for_aligned_yokes():
    """Bend direction (sign of beta) does not matter in a planar layout."""

    for signs in ([1.0, 1.0], [1.0, -1.0]):
        _, ratio = ref.vector_chain_ratio(ref.planar_directions((25.0, 25.0), signs), (0.0,))
        assert ref.unevenness_percent(ratio) < TOL_PU


@pytest.mark.parametrize("plane_angle", [0.0, 30.0, 60.0, 90.0])
def test_spatial_plane_offset_acts_as_relative_phase(plane_angle):
    """Fischer & Paul (1991): only the *relative* phase angle (yoke phase minus
    the angle between the two shaft planes) matters.

    A second joint plane rotated by ``plane_angle`` about the intermediate
    shaft, with aligned yokes, must equal the planar model with that phase.
    """

    beta1, beta2 = 20.0, 35.0
    planar = ref.planar_directions((beta1, beta2))
    spatial = [planar[0], planar[1], ref.rotate(planar[1], np.deg2rad(plane_angle), planar[2])]
    _, ratio = ref.vector_chain_ratio(spatial, (0.0,))
    expected, _, _ = _core_unevenness((beta1, beta2), (plane_angle,))
    assert ref.unevenness_percent(ratio) == pytest.approx(expected, abs=TOL_PU)


def test_spatial_equal_angles_constant_velocity_at_zero_relative_phase():
    """Fischer & Paul (1991): equal joint angles and zero relative phase give a
    constant-velocity driveline, also for non-coplanar shafts."""

    beta, plane_angle = 22.0, 40.0
    planar = ref.planar_directions((beta, beta))
    spatial = [planar[0], planar[1], ref.rotate(planar[1], np.deg2rad(plane_angle), planar[2])]
    candidates = []
    for clocking in (plane_angle, -plane_angle):
        _, ratio = ref.vector_chain_ratio(spatial, (clocking,))
        candidates.append(ref.unevenness_percent(ratio))
    assert min(candidates) < TOL_PU  # one clocking sense cancels the plane offset
    assert max(candidates) > 1.0  # the opposite sense does not

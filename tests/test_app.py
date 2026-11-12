"""Headless run of the real Streamlit page with streamlit.testing (no stub)."""

from __future__ import annotations

import io
import json
import re
import zipfile
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = str(Path(__file__).resolve().parents[1] / "streamlit_app.py")


def _run():
    app = AppTest.from_file(APP, default_timeout=180)
    app.run()
    assert not app.exception, [str(item.value) for item in app.exception]
    return app


def _button(app, text):
    for button in app.button:
        if text.lower() in str(button.label).lower():
            return button
    raise AssertionError(f"button {text!r} not found: {[b.label for b in app.button]}")


def _metric(app, label):
    for metric in app.metric:
        if metric.label == label:
            return metric
    raise AssertionError(f"metric {label!r} not found")


def test_default_run_both_languages():
    app = _run()
    assert _metric(app, "Current unevenness").value == "19.71%"
    app.sidebar.radio[0].set_value("TR").run()
    assert not app.exception
    assert _metric(app, "Mevcut düzgünsüzlük").value == "19,71%"


def test_apply_optimum_then_standard_never_reports_negative_reduction():
    """Reproduces the documented workflow that produced '-130737.99%'."""

    app = _run()
    ultra = [box for box in app.checkbox if box.key == "ultra_mode"][0]
    ultra.check().run()
    _button(app, "Run ultra").click().run()
    _button(app, "Apply optimum").click().run()
    ultra = [box for box in app.checkbox if box.key == "ultra_mode"][0]
    ultra.uncheck().run()
    assert not app.exception
    analysis = app.session_state["analysis_data"]
    assert (
        analysis["optimized_metrics"].unevenness_percent
        <= analysis["current_metrics"].unevenness_percent + 1e-9
    )
    reduction = _metric(app, "Unevenness reduction").value
    assert not reduction.startswith("-")
    delta = _metric(app, "Validated optimum").delta or ""
    assert "--" not in delta


@pytest.mark.parametrize("mode", [1, 2, 3])
def test_all_modes_run(mode):
    app = _run()
    app.sidebar.selectbox[0].set_value(mode).run()
    assert not app.exception


def test_reset_and_double_joint_reports_aligned_yokes():
    app = _run()
    _button(app, "Reset inputs").click().run()
    assert not app.exception
    app.sidebar.selectbox[0].set_value(2).run()
    assert app.session_state["analysis_data"]["optimization_result"].phi1_deg == 0.0


def test_excel_export_carries_phase_convention_and_exact_values():
    pytest.importorskip("xlsxwriter")
    app = _run()
    _button(app, "Prepare Excel").click().run()
    assert not app.exception
    archive = zipfile.ZipFile(io.BytesIO(app.session_state["excel_export_bytes"]))
    sheets = re.findall(r'<sheet name="([^"]+)"', archive.read("xl/workbook.xml").decode("utf8"))
    assert len(sheets) == 7
    strings = archive.read("xl/sharedStrings.xml").decode("utf8").lower()
    assert "physical_yoke_clocking" in strings
    assert "aligned" in strings


def test_analysis_state_carries_certified_closed_form_optimum():
    import cardan_core as core

    app = _run()
    analysis = app.session_state["analysis_data"]
    assert analysis["exact_optimum"].certified_global
    assert analysis["optimality_gap_percent"] < 1e-7
    payload = core.parameters_to_payload(analysis["optimized_parameters"])
    assert json.loads(json.dumps(payload))["phase_convention"] == "physical_yoke_clocking"


def _number_input(app, key):
    for widget in app.number_input:
        if widget.key == key:
            return widget
    raise AssertionError(f"number_input {key!r} not found")


@pytest.mark.parametrize("mode", [1, 2, 3])
def test_tolerance_and_spline_section_runs(mode):
    app = _run()
    app.sidebar.selectbox[0].set_value(mode).run()
    assert not app.exception
    _number_input(app, "phase_tolerance_deg").set_value(2.0).run()
    _number_input(app, "beta_tolerance_deg").set_value(0.5).run()
    assert not app.exception
    if mode >= 2:
        _number_input(app, "spline_teeth_1").set_value(16).run()
        if mode == 3:
            _number_input(app, "spline_teeth_2").set_value(15).run()
        assert not app.exception


def test_phase_sense_is_stated_in_the_sidebar():
    app = _run()
    captions = " ".join(str(item.value) for item in app.sidebar.caption)
    assert "clockwise" in captions and "same sense" in captions

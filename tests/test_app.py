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


def _checkbox(app, key):
    return [box for box in app.checkbox if box.key == key][0]


def _method_selector(app):
    return [box for box in app.selectbox if box.key == "optimization_method"][0]


def test_apply_optimum_then_standard_never_reports_negative_reduction():
    """Reproduces the workflow that produced '-130737.99%' in v1.2.4:
    apply a continuous optimum, then return to the standard method."""

    app = _run()
    _checkbox(app, "expert_mode").check().run()
    _method_selector(app).set_value("hybrid").run()
    _button(app, "Run analysis").click().run()
    assert app.session_state["analysis_data"]["optimization_result"].method == "hybrid"
    _button(app, "Apply optimum").click().run()
    _method_selector(app).set_value("exact").run()
    assert not app.exception
    analysis = app.session_state["analysis_data"]
    assert analysis["optimization_result"].method == "exact"
    assert (
        analysis["optimized_metrics"].unevenness_percent
        <= analysis["current_metrics"].unevenness_percent + 1e-9
    )
    reduction = _metric(app, "Unevenness reduction").value
    assert not reduction.startswith("-")
    delta = _metric(app, "Validated optimum").delta or ""
    assert "--" not in delta


def test_standard_method_is_closed_form_and_stochastic_methods_need_expert_mode():
    app = _run()
    assert app.session_state["analysis_data"]["optimization_result"].method == "exact"
    assert not [box for box in app.checkbox if box.key == "ultra_mode"]
    assert not [box for box in app.selectbox if box.key == "optimization_method"]
    _checkbox(app, "expert_mode").check().run()
    selector = _method_selector(app)
    assert len(selector.options) == 5  # all five methods, shown by their labels
    # A stochastic method is not refreshed automatically.
    selector.set_value("differential_evolution").run()
    assert app.session_state["analysis_data"]["optimization_result"].method == "exact"
    assert any("Inputs changed" in str(item.value) for item in app.warning)


def test_no_deprecated_width_argument_remains():
    source = Path(APP).read_text(encoding="utf-8")
    assert "use_container_width=True" not in source
    assert source.count("**_STRETCH") >= 15


def test_curve_csv_keeps_first_columns_and_adds_metadata():
    import csv as csv_module
    import runpy

    namespace = runpy.run_path(APP)
    analysis = namespace["analysis"]
    parameters = namespace["analyzed_parameters"]
    data = namespace["_curve_csv"](parameters, analysis, "en").decode("utf-8-sig")
    rows = list(csv_module.reader(io.StringIO(data)))
    header = rows[0]
    assert header[:3] == ["Input angle θ (deg)", "Current speed ratio q", "Optimized speed ratio q"]
    assert len(header) == 5 + len(namespace["CSV_METADATA_COLUMNS"])
    assert header[5:] == list(namespace["CSV_METADATA_COLUMNS"])
    assert len(rows) == 1 + len(analysis["theta_plot_deg"])
    record = dict(zip(header, rows[1]))
    assert record["phase_convention"] == "physical_yoke_clocking"
    assert record["angles_unit"] == "degree"
    assert record["tool_version"] == namespace["APP_RELEASE"]
    assert float(record["beta1_deg"]) == parameters.beta1_deg
    assert all(len(row) == len(header) for row in rows)


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

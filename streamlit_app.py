"""Bilingual Streamlit interface for Cardan Joint Engineering Tool v2.1.1."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
from matplotlib.figure import Figure
import numpy as np
import streamlit as st

import cardan_core as core


# ---------------------------------------------------------------------------
# Core compatibility
# ---------------------------------------------------------------------------

_REQUIRED_CORE_API_VERSION = 5
_REQUIRED_CORE_OBJECTS = (
    "CardanMode",
    "CardanParameters",
    "OptimizationMethod",
    "OptimizationSettings",
    "OptimizationDiagnostics",
    "KinematicTrajectory",
    "PlotLabels",
    "UNEVENNESS_LIMIT_PERCENT",
    "calculate_analysis",
    "phase_combination_count",
    "plot_geometry_2d",
    "plot_phase_figure",
    "plot_phase_landscape",
    "plot_velocity_ratio",
)
_missing_core_objects = [name for name in _REQUIRED_CORE_OBJECTS if not hasattr(core, name)]
_core_api_version = getattr(core, "CORE_API_VERSION", 0)

if _core_api_version < _REQUIRED_CORE_API_VERSION or _missing_core_objects:
    st.error(
        "streamlit_app.py and cardan_core.py are from different releases. "
        "Deploy the matching files from the same package."
    )
    st.code(
        f"Required core API version: {_REQUIRED_CORE_API_VERSION}\n"
        f"Detected core API version: {_core_api_version}\n"
        "Missing objects: "
        + (", ".join(_missing_core_objects) if _missing_core_objects else "none"),
        language="text",
    )
    st.stop()

CardanMode = core.CardanMode
CardanParameters = core.CardanParameters
OptimizationMethod = core.OptimizationMethod
OptimizationSettings = core.OptimizationSettings
PlotLabels = core.PlotLabels
UNEVENNESS_LIMIT_PERCENT = core.UNEVENNESS_LIMIT_PERCENT


st.set_page_config(
    page_title="Cardan Joint Engineering Tool v2.1.1",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)


TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "title": "Cardan Joint Engineering Tool",
        "subtitle": "Kinematic analysis, global phase optimization, validation, and export",
        "version": "Version 2.1.1",
        "system_parameters": "System Parameters",
        "configuration": "Cardan configuration",
        "mode_single": "1 Cardan — Single",
        "mode_double": "2 Cardan — Double",
        "mode_triple": "3 Cardan — Triple",
        "misalignment_angles": "Misalignment Angles",
        "phase_angles": "Current Phase Angles",
        "optimization": "Optimization",
        "method": "Optimization method",
        "method_grid": "Fast Grid",
        "method_local": "Grid + Local Refinement",
        "method_de": "Global Continuous — Differential Evolution",
        "method_hybrid": "Hybrid — Differential Evolution + Powell",
        "method_help": "The coarse grid is retained for the phase map. Global modes search continuous phase values.",
        "phase_search_step": "Coarse map step (deg)",
        "refinement_step": "Local refinement step (deg)",
        "global_settings": "Global optimizer settings",
        "max_iterations": "Maximum generations",
        "population_size": "Population multiplier",
        "tolerance": "Convergence tolerance",
        "random_seed": "Random seed",
        "validation_samples": "Independent validation samples",
        "polish": "Enable SciPy polish",
        "angular_reference": "Angular Reference",
        "run_analysis": "Run analysis",
        "reset_inputs": "Reset inputs",
        "direct_value": "direct numerical value",
        "beta_help": "Misalignment angle between two consecutive shaft axes.",
        "phase_help": "Positive phase follows θ_next = θ_out − φ. For the kinematic speed response, φ and φ + 180° are equivalent; optimization uses the unique 0°–180° interval.",
        "optimization_help": "This step controls the deterministic map, not the continuous optimizer resolution.",
        "theta_help": "Input-shaft angular reference. It shifts the plotted cycle.",
        "initial_instruction": "Set the parameters in the sidebar and press **Run analysis**.",
        "spinner": "Calculating the kinematic response, optimization, and dense validation...",
        "stale_warning": "Inputs changed after the last run. Displayed results belong to the last analyzed parameter set.",
        "overview": "Overview",
        "velocity": "Velocity Response",
        "geometry_phase": "Geometry & Phase",
        "phase_map": "Optimization Map",
        "data_export": "Data & Export",
        "current_unevenness": "Current unevenness",
        "optimized_unevenness": "Validated optimum",
        "reduction": "Unevenness reduction",
        "candidate_count": "Coarse-map candidates",
        "current_status": "Current status",
        "optimized_status": "Optimized status",
        "status_ok": "OK",
        "status_warning": "Warning",
        "optimum_phase_angles": "Optimum Phase Angles",
        "single_no_optimization": "Phase optimization is not applicable to a single Cardan joint.",
        "optimum_phi1": "Optimum φ₁",
        "optimum_phi2": "Optimum φ₂",
        "selected_method": "Selected method",
        "apply_optimum": "Apply optimum phases and rerun",
        "coarse_solution": "Coarse-map solution",
        "optimization_diagnostics": "Optimization Diagnostics",
        "convergence": "Convergence",
        "success": "Converged / accepted",
        "not_converged": "Limit reached / fallback used",
        "function_evaluations": "Function evaluations",
        "iterations": "Iterations / generations",
        "runtime": "Optimization time",
        "objective_value": "360-point / 180° objective",
        "validation_value": "Dense validation",
        "validation_delta": "Validation delta",
        "validation_warning": "The dense validation differs materially from the optimizer objective. Increase the optimizer or validation resolution.",
        "diagnostic_message": "Solver message",
        "engineering_metrics": "Engineering Metrics — Dense Validation",
        "metric": "Metric",
        "current": "Current",
        "optimized": "Optimized",
        "mean_ratio": "Mean speed ratio",
        "minimum_ratio": "Minimum speed ratio",
        "maximum_ratio": "Maximum speed ratio",
        "rms_error": "RMS speed error",
        "positive_error": "Maximum positive error",
        "negative_error": "Maximum negative error",
        "threshold_note": "The 5% limit is a project criterion, not a universal design standard.",
        "current_geometry": "Current shaft geometry",
        "current_phase": "Current phase configuration",
        "optimized_phase": "Optimized phase configuration",
        "phase_map_single": "A phase map is not available for the single-joint configuration.",
        "phase_map_note": "The map covers the unique 0°–180° phase interval. Values shifted by 180° are kinematically equivalent. The star is the selected local/global optimum and can lie between grid nodes.",
        "export_curves": "Download curve data (CSV)",
        "export_summary": "Download analysis summary (JSON)",
        "export_trajectory": "Download kinematic trajectory (JSON)",
        "data_preview": "Curve Data Preview",
        "model_scope": "Model scope and limitations",
        "model_text": r"""
### Optimization architecture

The deterministic coarse phase grid is always retained to generate the optimization landscape. Depending on the selected method, the final result is obtained from the grid, a local periodic refinement, Differential Evolution, or Differential Evolution followed by continuous Powell polishing.

The Hooke-joint speed response repeats every 180°. The optimizer therefore evaluates 360 input-shaft positions over the unique 0°–180° period, preserving the previous 0.5° angular spacing while halving the objective workload. The accepted solution is independently checked on a denser 180° validation grid.

### Kinematic trajectory API

The core now exports every joint's input angle, output angle, individual speed ratio, and total speed ratio. This renderer-independent data layer is the foundation for the future Three.js viewer.

### Limitations

The current model is **kinematic only**. Mass, inertia, torque, bearing reactions, elasticity, backlash, friction, stress, fatigue, torsional vibration, efficiency, and power losses are not included.
""",
        "footer": "Developed by Furkan Kasap · Automotive Engineer",
    },
    "tr": {
        "title": "Kardan Mafsalı Mühendislik Aracı",
        "subtitle": "Kinematik analiz, global faz optimizasyonu, doğrulama ve veri dışa aktarma",
        "version": "Sürüm 2.1.1",
        "system_parameters": "Sistem Parametreleri",
        "configuration": "Kardan konfigürasyonu",
        "mode_single": "1 Kardan — Tekli",
        "mode_double": "2 Kardan — Çiftli",
        "mode_triple": "3 Kardan — Üçlü",
        "misalignment_angles": "Eksen Kaçıklık Açıları",
        "phase_angles": "Mevcut Faz Açıları",
        "optimization": "Optimizasyon",
        "method": "Optimizasyon yöntemi",
        "method_grid": "Hızlı Grid",
        "method_local": "Grid + Yerel Hassaslaştırma",
        "method_de": "Global Sürekli — Differential Evolution",
        "method_hybrid": "Hibrit — Differential Evolution + Powell",
        "method_help": "Kaba grid faz haritası için korunur. Global yöntemler sürekli faz değerlerinde arama yapar.",
        "phase_search_step": "Kaba harita adımı (derece)",
        "refinement_step": "Yerel hassaslaştırma adımı (derece)",
        "global_settings": "Global optimize edici ayarları",
        "max_iterations": "Maksimum nesil sayısı",
        "population_size": "Popülasyon çarpanı",
        "tolerance": "Yakınsama toleransı",
        "random_seed": "Rastgele sayı tohumu",
        "validation_samples": "Bağımsız doğrulama örnekleri",
        "polish": "SciPy polish aşamasını aç",
        "angular_reference": "Açısal Referans",
        "run_analysis": "Analizi çalıştır",
        "reset_inputs": "Girişleri sıfırla",
        "direct_value": "doğrudan sayısal değer",
        "beta_help": "Ardışık iki mil ekseni arasındaki kaçıklık açısıdır.",
        "phase_help": "Pozitif faz θ_next = θ_out − φ konvansiyonunu izler. Kinematik hız yanıtında φ ile φ + 180° eşdeğerdir; optimizasyon benzersiz 0°–180° aralığını kullanır.",
        "optimization_help": "Bu adım sürekli optimize edicinin hassasiyetini değil, deterministik haritayı belirler.",
        "theta_help": "Giriş milinin açısal referansıdır; çizilen çevrimin başlangıcını kaydırır.",
        "initial_instruction": "Kenar çubuğundan parametreleri ayarlayın ve **Analizi çalıştır** düğmesine basın.",
        "spinner": "Kinematik yanıt, optimizasyon ve yoğun doğrulama hesaplanıyor...",
        "stale_warning": "Girişler son çalıştırmadan sonra değişti. Gösterilen sonuçlar son analiz parametrelerine aittir.",
        "overview": "Genel Bakış",
        "velocity": "Hız Yanıtı",
        "geometry_phase": "Geometri ve Faz",
        "phase_map": "Optimizasyon Haritası",
        "data_export": "Veri ve Dışa Aktarma",
        "current_unevenness": "Mevcut düzgünsüzlük",
        "optimized_unevenness": "Doğrulanmış optimum",
        "reduction": "Düzgünsüzlük azalması",
        "candidate_count": "Kaba harita adayı",
        "current_status": "Mevcut durum",
        "optimized_status": "Optimize edilmiş durum",
        "status_ok": "Uygun",
        "status_warning": "Uyarı",
        "optimum_phase_angles": "Optimum Faz Açıları",
        "single_no_optimization": "Tek bir Kardan mafsalı için faz optimizasyonu uygulanamaz.",
        "optimum_phi1": "Optimum φ₁",
        "optimum_phi2": "Optimum φ₂",
        "selected_method": "Seçilen yöntem",
        "apply_optimum": "Optimum fazları uygula ve yeniden çalıştır",
        "coarse_solution": "Kaba harita çözümü",
        "optimization_diagnostics": "Optimizasyon Teşhisleri",
        "convergence": "Yakınsama",
        "success": "Yakınsadı / kabul edildi",
        "not_converged": "Sınıra ulaştı / geri dönüş kullanıldı",
        "function_evaluations": "Fonksiyon değerlendirmesi",
        "iterations": "İterasyon / nesil",
        "runtime": "Optimizasyon süresi",
        "objective_value": "360 noktalı / 180° amaç değeri",
        "validation_value": "Yoğun doğrulama",
        "validation_delta": "Doğrulama farkı",
        "validation_warning": "Yoğun doğrulama ile optimize edici amaç değeri arasında anlamlı fark var. Optimize edici veya doğrulama çözünürlüğünü artırın.",
        "diagnostic_message": "Çözücü mesajı",
        "engineering_metrics": "Mühendislik Metrikleri — Yoğun Doğrulama",
        "metric": "Metrik",
        "current": "Mevcut",
        "optimized": "Optimize edilmiş",
        "mean_ratio": "Ortalama hız oranı",
        "minimum_ratio": "Minimum hız oranı",
        "maximum_ratio": "Maksimum hız oranı",
        "rms_error": "RMS hız hatası",
        "positive_error": "Maksimum pozitif hata",
        "negative_error": "Maksimum negatif hata",
        "threshold_note": "%5 sınırı proje değerlendirme ölçütüdür; evrensel bir tasarım standardı değildir.",
        "current_geometry": "Mevcut mil geometrisi",
        "current_phase": "Mevcut faz konfigürasyonu",
        "optimized_phase": "Optimize edilmiş faz konfigürasyonu",
        "phase_map_single": "Tek mafsallı konfigürasyon için faz haritası bulunmaz.",
        "phase_map_note": "Harita benzersiz 0°–180° faz aralığını kapsar. 180° kaydırılmış değerler kinematik olarak eşdeğerdir. Yıldız seçilen yerel/global optimumu gösterir ve grid noktalarının arasında bulunabilir.",
        "export_curves": "Eğri verisini indir (CSV)",
        "export_summary": "Analiz özetini indir (JSON)",
        "export_trajectory": "Kinematik yörüngeyi indir (JSON)",
        "data_preview": "Eğri Verisi Önizlemesi",
        "model_scope": "Model kapsamı ve sınırlamalar",
        "model_text": r"""
### Optimizasyon mimarisi

Deterministik kaba faz gridi, optimizasyon haritasını oluşturmak için her yöntemde korunur. Seçilen yönteme göre nihai sonuç grid, periyodik yerel hassaslaştırma, Differential Evolution veya Differential Evolution sonrasında sürekli Powell iyileştirmesiyle elde edilir.

Kardan mafsalının hız yanıtı her 180°'de tekrar eder. Bu nedenle optimize edici, benzersiz 0°–180° periyodunda 360 giriş mili konumu kullanır; önceki 0,5° açısal çözünürlük korunurken amaç fonksiyonu yükü yarıya iner. Kabul edilen çözüm daha yoğun ve bağımsız bir 180° doğrulama ağı üzerinde kontrol edilir.

### Kinematik yörünge API'si

Çekirdek artık her mafsalın giriş açısını, çıkış açısını, ayrı hız oranını ve toplam hız oranını dışa aktarır. Renderer'dan bağımsız bu veri katmanı, gelecekteki Three.js görüntüleyicisinin temelidir.

### Sınırlamalar

Mevcut model **yalnızca kinematiktir**. Kütle, atalet, tork, yatak tepkileri, elastikiyet, boşluk, sürtünme, gerilme, yorulma, burulma titreşimi, verim ve güç kayıpları modele dahil değildir.
""",
        "footer": "Geliştiren: Furkan Kasap · Otomotiv Mühendisi",
    },
}


PLOT_LABELS: dict[str, PlotLabels] = {
    "en": PlotLabels(refined_optimum="Selected optimum"),
    "tr": PlotLabels(
        current_curve="Mevcut",
        optimized_curve="Optimize edilmiş",
        input_rotation_axis="Giriş mili dönme açısı (derece)",
        velocity_ratio_title="Şekil A — Açısal Hız Oranı ve Düzgünsüzlük",
        current_unevenness="Mevcut",
        optimized_unevenness="Optimize edilmiş",
        status_ok="Uygun",
        status_warning="Uyarı",
        optimized_phi1="Optimize edilmiş φ₁",
        optimized_phi2="Optimize edilmiş φ₂",
        geometry_title="Şekil B — İki Boyutlu Mil Geometrisi",
        joint_1_to_2="Mafsal 1 → Mafsal 2",
        joint_2_to_3="Mafsal 2 → Mafsal 3",
        direction_ccw="Saat yönünün tersi",
        direction_cw="Saat yönü",
        side_view="yan görünüş",
        phase_title="Şekil C — Faz (φ)",
        unity_ratio="Sabit hız referansı",
        phase_landscape_title="Şekil D — Faz Optimizasyon Haritası",
        phase_phi1_axis="φ₁ (derece)",
        phase_phi2_axis="φ₂ (derece)",
        unevenness_axis="Düzgünsüzlük (%)",
        coarse_optimum="Kaba optimum",
        refined_optimum="Seçilen optimum",
    ),
}


# ---------------------------------------------------------------------------
# Figure and URL helpers
# ---------------------------------------------------------------------------

PAGE_BACKGROUND = "#0E1117"
PLOT_BACKGROUND = "#111827"
TEXT_COLOR = "#F3F4F6"
MUTED_TEXT_COLOR = "#AEB6C2"
GRID_COLOR = "#6B7280"
SPINE_COLOR = "#6B7280"
LEGEND_BACKGROUND = "#1F2937"


def _is_near_black(color: object) -> bool:
    try:
        red, green, blue, _ = to_rgba(color)
    except (TypeError, ValueError):
        return False
    return red < 0.18 and green < 0.18 and blue < 0.18


def style_figure_for_dark_theme(figure: Figure) -> Figure:
    figure.patch.set_facecolor(PLOT_BACKGROUND)
    if figure._suptitle is not None:
        figure._suptitle.set_color(TEXT_COLOR)

    for axis in figure.axes:
        axis.set_facecolor(PLOT_BACKGROUND)
        axis.title.set_color(TEXT_COLOR)
        axis.xaxis.label.set_color(TEXT_COLOR)
        axis.yaxis.label.set_color(TEXT_COLOR)
        axis.tick_params(axis="both", colors=MUTED_TEXT_COLOR, which="both")
        for spine in axis.spines.values():
            spine.set_color(SPINE_COLOR)
        axis.grid(visible=True, color=GRID_COLOR, alpha=0.22, linewidth=0.8)
        for text_item in axis.texts:
            if _is_near_black(text_item.get_color()):
                text_item.set_color(TEXT_COLOR)
            text_box = text_item.get_bbox_patch()
            if text_box is not None:
                text_box.set_facecolor(LEGEND_BACKGROUND)
                text_box.set_edgecolor(SPINE_COLOR)
                text_box.set_alpha(0.94)
        for line in axis.lines:
            if _is_near_black(line.get_color()):
                line.set_color(TEXT_COLOR)
        for patch in axis.patches:
            if _is_near_black(patch.get_edgecolor()):
                patch.set_edgecolor(TEXT_COLOR)
        legend = axis.get_legend()
        if legend is not None:
            legend.get_frame().set_facecolor(LEGEND_BACKGROUND)
            legend.get_frame().set_edgecolor(SPINE_COLOR)
            legend.get_frame().set_alpha(0.94)
            for legend_text in legend.get_texts():
                legend_text.set_color(TEXT_COLOR)
    return figure


def _normalise_query_value(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return str(value[0]) if value else None
    return str(value)


def _read_language_from_url() -> str:
    try:
        value = _normalise_query_value(st.query_params.get("lang"))
    except Exception:
        try:
            value = _normalise_query_value(st.experimental_get_query_params().get("lang"))
        except Exception:
            value = None
    return value if value in TRANSLATIONS else "en"


def _write_language_to_url(language_code: str) -> None:
    try:
        if _normalise_query_value(st.query_params.get("lang")) != language_code:
            st.query_params["lang"] = language_code
    except Exception:
        try:
            st.experimental_set_query_params(lang=language_code)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Inputs and state
# ---------------------------------------------------------------------------


def _copy_widget_value(source_key: str, target_key: str) -> None:
    st.session_state[target_key] = st.session_state[source_key]


def sidebar_angle_input(
    label: str,
    *,
    key: str,
    min_value: float,
    max_value: float,
    default_value: float,
    direct_value_text: str,
    step: float = 1.0,
    help_text: str | None = None,
) -> float:
    slider_key = f"{key}_slider"
    number_key = f"{key}_number"
    if slider_key not in st.session_state and number_key not in st.session_state:
        st.session_state[slider_key] = float(default_value)
        st.session_state[number_key] = float(default_value)
    elif slider_key not in st.session_state:
        st.session_state[slider_key] = float(st.session_state[number_key])
    elif number_key not in st.session_state:
        st.session_state[number_key] = float(st.session_state[slider_key])

    st.markdown(f"**{label}**")
    slider_column, number_column = st.columns([2.35, 1.0])
    with slider_column:
        st.slider(
            label,
            min_value=float(min_value),
            max_value=float(max_value),
            step=float(step),
            key=slider_key,
            on_change=_copy_widget_value,
            args=(slider_key, number_key),
            help=help_text,
            label_visibility="collapsed",
        )
    with number_column:
        st.number_input(
            direct_value_text,
            min_value=float(min_value),
            max_value=float(max_value),
            step=float(step),
            key=number_key,
            on_change=_copy_widget_value,
            args=(number_key, slider_key),
            format="%.2f" if step < 1.0 else "%.1f",
            label_visibility="collapsed",
        )
    return float(st.session_state[number_key])


def _set_angle_state(key: str, value: float) -> None:
    st.session_state[f"{key}_slider"] = float(value)
    st.session_state[f"{key}_number"] = float(value)


def _reset_inputs() -> None:
    st.session_state.mode_value = 3
    for key, value in (
        ("beta1_deg", 25.0), ("beta2_deg", 25.0), ("beta3_deg", 25.0),
        ("phi1_deg", 0.0), ("phi2_deg", 0.0),
        ("optimization_step_deg", 5.0), ("theta0_deg", 0.0),
    ):
        _set_angle_state(key, value)
    st.session_state.optimization_method = OptimizationMethod.HYBRID.value
    st.session_state.local_refinement_step_deg = 0.25
    st.session_state.de_max_iterations = 80
    st.session_state.de_population_size = 12
    st.session_state.de_tolerance = 1.0e-7
    st.session_state.de_seed = 42
    st.session_state.validation_sample_count = 3600
    st.session_state.de_polish = False
    st.session_state.analysis_data = None
    st.session_state.analysis_signature = None


def _apply_optimum() -> None:
    analysis = st.session_state.get("analysis_data")
    if not analysis:
        return
    result = analysis["optimization_result"]
    if result.phi1_deg is not None:
        _set_angle_state("phi1_deg", float(result.phi1_deg))
    if result.phi2_deg is not None:
        _set_angle_state("phi2_deg", float(result.phi2_deg))
    st.session_state.auto_run_after_apply = True


def _signature_to_parameters(signature: tuple[Any, ...]) -> CardanParameters:
    return CardanParameters(
        mode=int(signature[0]),
        beta1_deg=float(signature[1]),
        beta2_deg=float(signature[2]),
        beta3_deg=float(signature[3]),
        phi1_deg=float(signature[4]),
        phi2_deg=float(signature[5]),
        theta0_deg=float(signature[6]),
        optimization_step_deg=float(signature[7]),
    )


def _signature_to_settings(signature: tuple[Any, ...]) -> OptimizationSettings:
    return OptimizationSettings(
        method=str(signature[8]),
        local_refinement_step_deg=float(signature[9]),
        differential_evolution_max_iterations=int(signature[10]),
        differential_evolution_population_size=int(signature[11]),
        differential_evolution_tolerance=float(signature[12]),
        random_seed=int(signature[13]),
        validation_sample_count=int(signature[14]),
        polish=bool(signature[15]),
    )


def _build_signature(
    parameters: CardanParameters,
    settings: OptimizationSettings,
) -> tuple[Any, ...]:
    return (
        int(parameters.mode),
        round(float(parameters.beta1_deg), 8),
        round(float(parameters.beta2_deg), 8),
        round(float(parameters.beta3_deg), 8),
        round(float(parameters.phi1_deg), 8),
        round(float(parameters.phi2_deg), 8),
        round(float(parameters.theta0_deg), 8),
        round(float(parameters.optimization_step_deg), 8),
        settings.method.value,
        round(float(settings.local_refinement_step_deg), 8),
        int(settings.differential_evolution_max_iterations),
        int(settings.differential_evolution_population_size),
        float(settings.differential_evolution_tolerance),
        int(settings.random_seed),
        int(settings.validation_sample_count),
        bool(settings.polish),
    )


@st.cache_data(show_spinner=False)
def _cached_analysis(signature: tuple[Any, ...]) -> dict[str, Any]:
    return core.calculate_analysis(
        _signature_to_parameters(signature),
        optimization_settings=_signature_to_settings(signature),
    )


def _format_integer(value: int, language_code: str) -> str:
    formatted = f"{value:,}"
    return formatted.replace(",", ".") if language_code == "tr" else formatted


def _status_text(value: float, text: dict[str, str]) -> str:
    return text["status_ok"] if value <= UNEVENNESS_LIMIT_PERCENT else text["status_warning"]


def _method_text(method: str, text: dict[str, str]) -> str:
    return {
        OptimizationMethod.GRID.value: text["method_grid"],
        OptimizationMethod.LOCAL_REFINEMENT.value: text["method_local"],
        OptimizationMethod.DIFFERENTIAL_EVOLUTION.value: text["method_de"],
        OptimizationMethod.HYBRID.value: text["method_hybrid"],
    }.get(method, method)


def _curve_csv(analysis: dict[str, Any]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "theta_input_deg", "q_current", "q_optimized",
        "current_speed_error_percent", "optimized_speed_error_percent",
    ])
    current_mean = analysis["current_metrics"].q_mean
    optimized_mean = analysis["optimized_metrics"].q_mean
    for theta, current, optimized in zip(
        analysis["theta_plot_deg"],
        analysis["q_current_plot"],
        analysis["q_optimized_plot"],
    ):
        writer.writerow([
            f"{float(theta):.6f}", f"{float(current):.10f}", f"{float(optimized):.10f}",
            f"{100.0 * (float(current) / current_mean - 1.0):.8f}",
            f"{100.0 * (float(optimized) / optimized_mean - 1.0):.8f}",
        ])
    return buffer.getvalue().encode("utf-8")


def _trajectory_payload(trajectory: core.KinematicTrajectory) -> dict[str, Any]:
    return {
        "input_rotation_deg": trajectory.input_rotation_deg.tolist(),
        "joint_input_angles_deg": trajectory.joint_input_angles_deg.tolist(),
        "joint_output_angles_deg": trajectory.joint_output_angles_deg.tolist(),
        "joint_speed_ratios": trajectory.joint_speed_ratios.tolist(),
        "total_speed_ratio": trajectory.total_speed_ratio.tolist(),
    }


def _trajectory_json(analysis: dict[str, Any]) -> bytes:
    payload = {
        "model": "Cardan Joint Engineering Tool",
        "version": "2.1.1",
        "display_revolution_deg": 360.0,
        "kinematic_period_deg": 180.0,
        "phase_convention": "theta_next = theta_out - phi",
        "current": _trajectory_payload(analysis["current_trajectory"]),
        "optimized": _trajectory_payload(analysis["optimized_trajectory"]),
    }
    return json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")


def _summary_json(parameters: CardanParameters, analysis: dict[str, Any]) -> bytes:
    result = analysis["optimization_result"]
    settings = analysis["optimization_settings"]
    diagnostics = analysis["optimization_diagnostics"]
    settings_payload = asdict(settings)
    settings_payload["method"] = settings.method.value
    payload = {
        "model": "Cardan Joint Engineering Tool",
        "version": "2.1.1",
        "display_revolution_deg": 360.0,
        "kinematic_period_deg": 180.0,
        "phase_search_interval_deg": [0.0, 180.0],
        "parameters": asdict(parameters),
        "optimization_settings": settings_payload,
        "current_metrics_dense_validation": asdict(analysis["current_metrics"]),
        "optimized_metrics_dense_validation": asdict(analysis["optimized_metrics"]),
        "optimization": {
            "method": result.method,
            "phi1_deg": result.phi1_deg,
            "phi2_deg": result.phi2_deg,
            "coarse_phi1_deg": result.coarse_phi1_deg,
            "coarse_phi2_deg": result.coarse_phi2_deg,
            "objective_unevenness_percent": result.unevenness_percent,
        },
        "diagnostics": asdict(diagnostics),
        "scope": "Ideal rigid kinematic model; dynamic and structural effects excluded.",
    }
    return json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")


# ---------------------------------------------------------------------------
# Style and initial state
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
        .stApp { background-color: #0E1117; }
        .block-container { padding-top: 1.25rem; padding-bottom: 3rem; }
        [data-testid="stSidebar"] { min-width: min(410px, 94vw); }
        .app-subtitle { color: #AEB6C2; font-size: 1.05rem; margin-top: -0.8rem; }
        .version-badge { display: inline-block; padding: 0.18rem 0.55rem; margin-top: 0.35rem;
            border: 1px solid rgba(174,182,194,0.32); border-radius: 999px;
            color: #AEB6C2; font-size: 0.78rem; }
        [data-testid="stMetric"] { border: 1px solid rgba(174,182,194,0.22); border-radius: 0.8rem;
            padding: 0.9rem 1rem; background: rgba(31,41,55,0.45); }
        [data-testid="stMetricValue"] { font-size: clamp(1.45rem, 2.2vw, 2.35rem); }
        div[role="radiogroup"] { justify-content: flex-end; gap: 0.35rem; }
        .scope-note { border-left: 4px solid #9A9A9A; padding: 0.65rem 0.9rem;
            background: rgba(128,128,128,0.08); border-radius: 0.3rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

if "ui_language" not in st.session_state:
    st.session_state.ui_language = "TR" if _read_language_from_url() == "tr" else "EN"
if "analysis_data" not in st.session_state:
    st.session_state.analysis_data = None
if "analysis_signature" not in st.session_state:
    st.session_state.analysis_signature = None
if "auto_run_after_apply" not in st.session_state:
    st.session_state.auto_run_after_apply = False

header_column, language_column = st.columns([5.2, 1.15])
with language_column:
    st.radio(
        "Language / Dil",
        options=("EN", "TR"),
        key="ui_language",
        horizontal=True,
        label_visibility="collapsed",
    )
language_code = "tr" if st.session_state.ui_language == "TR" else "en"
_write_language_to_url(language_code)
text = TRANSLATIONS[language_code]
plot_labels = PLOT_LABELS[language_code]
with header_column:
    st.title(text["title"])
    st.markdown(f'<div class="app-subtitle">{text["subtitle"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<span class="version-badge">{text["version"]}</span>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header(text["system_parameters"])
    mode_value = st.selectbox(
        text["configuration"], options=(1, 2, 3), index=2, key="mode_value",
        format_func=lambda value: {
            1: text["mode_single"], 2: text["mode_double"], 3: text["mode_triple"],
        }[int(value)],
    )
    mode = CardanMode(int(mode_value))

    st.subheader(text["misalignment_angles"])
    beta1_deg = sidebar_angle_input(
        "β₁ (°)", key="beta1_deg", min_value=0.0, max_value=60.0,
        default_value=25.0, direct_value_text=text["direct_value"], help_text=text["beta_help"],
    )
    beta2_deg = 25.0
    beta3_deg = 25.0
    if mode >= CardanMode.DOUBLE:
        beta2_deg = sidebar_angle_input(
            "β₂ (°)", key="beta2_deg", min_value=0.0, max_value=60.0,
            default_value=25.0, direct_value_text=text["direct_value"], help_text=text["beta_help"],
        )
    if mode is CardanMode.TRIPLE:
        beta3_deg = sidebar_angle_input(
            "β₃ (°)", key="beta3_deg", min_value=0.0, max_value=60.0,
            default_value=25.0, direct_value_text=text["direct_value"], help_text=text["beta_help"],
        )

    phi1_deg = 0.0
    phi2_deg = 0.0
    optimization_step_deg = 5.0
    method_value = OptimizationMethod.GRID.value
    local_step = 0.25
    de_max_iterations = 80
    de_population_size = 12
    de_tolerance = 1.0e-7
    de_seed = 42
    validation_sample_count = 3600
    de_polish = False

    if mode >= CardanMode.DOUBLE:
        st.subheader(text["phase_angles"])
        phi1_deg = sidebar_angle_input(
            "φ₁ (°)", key="phi1_deg", min_value=0.0, max_value=360.0,
            default_value=0.0, direct_value_text=text["direct_value"], help_text=text["phase_help"],
        )
        if mode is CardanMode.TRIPLE:
            phi2_deg = sidebar_angle_input(
                "φ₂ (°)", key="phi2_deg", min_value=0.0, max_value=360.0,
                default_value=0.0, direct_value_text=text["direct_value"], help_text=text["phase_help"],
            )

        st.subheader(text["optimization"])
        method_options = [item.value for item in OptimizationMethod]
        method_value = st.selectbox(
            text["method"], options=method_options, index=3, key="optimization_method",
            format_func=lambda value: _method_text(value, text), help=text["method_help"],
        )
        optimization_step_deg = sidebar_angle_input(
            text["phase_search_step"], key="optimization_step_deg", min_value=1.0, max_value=15.0,
            default_value=5.0, direct_value_text=text["direct_value"], help_text=text["optimization_help"],
        )
        if method_value == OptimizationMethod.LOCAL_REFINEMENT.value:
            local_step = float(st.select_slider(
                text["refinement_step"], options=(0.05, 0.10, 0.25, 0.50, 1.00),
                value=0.25, key="local_refinement_step_deg", format_func=lambda value: f"{value:.2f}°",
            ))

        with st.expander(text["global_settings"], expanded=method_value in {
            OptimizationMethod.DIFFERENTIAL_EVOLUTION.value,
            OptimizationMethod.HYBRID.value,
        }):
            de_max_iterations = int(st.number_input(
                text["max_iterations"], min_value=5, max_value=500, value=80,
                step=5, key="de_max_iterations",
            ))
            de_population_size = int(st.number_input(
                text["population_size"], min_value=4, max_value=40, value=12,
                step=1, key="de_population_size",
            ))
            de_tolerance = float(st.selectbox(
                text["tolerance"], options=(1.0e-4, 1.0e-6, 1.0e-7, 1.0e-8),
                index=2, key="de_tolerance", format_func=lambda value: f"{value:.0e}",
            ))
            de_seed = int(st.number_input(
                text["random_seed"], min_value=0, max_value=2_147_483_647,
                value=42, step=1, key="de_seed",
            ))
            de_polish = bool(st.checkbox(text["polish"], value=False, key="de_polish"))

        validation_sample_count = int(st.select_slider(
            text["validation_samples"], options=(360, 720, 1800, 3600, 7200, 18000),
            value=3600, key="validation_sample_count",
            format_func=lambda value: _format_integer(int(value), language_code),
        ))

    st.subheader(text["angular_reference"])
    theta0_deg = sidebar_angle_input(
        "θ₀ (°)", key="theta0_deg", min_value=0.0, max_value=180.0,
        default_value=0.0, direct_value_text=text["direct_value"], help_text=text["theta_help"],
    )
    run_button = st.button(text["run_analysis"], type="primary", use_container_width=True)
    st.button(text["reset_inputs"], use_container_width=True, on_click=_reset_inputs)

parameters = CardanParameters(
    mode=mode, beta1_deg=beta1_deg, beta2_deg=beta2_deg, beta3_deg=beta3_deg,
    phi1_deg=phi1_deg, phi2_deg=phi2_deg, theta0_deg=theta0_deg,
    optimization_step_deg=optimization_step_deg,
)
settings = OptimizationSettings(
    method=method_value,
    local_refinement_step_deg=local_step,
    differential_evolution_max_iterations=de_max_iterations,
    differential_evolution_population_size=de_population_size,
    differential_evolution_tolerance=de_tolerance,
    random_seed=de_seed,
    validation_sample_count=validation_sample_count,
    polish=de_polish,
)
current_signature = _build_signature(parameters, settings)

if run_button or st.session_state.auto_run_after_apply:
    st.session_state.auto_run_after_apply = False
    with st.spinner(text["spinner"]):
        st.session_state.analysis_data = _cached_analysis(current_signature)
        st.session_state.analysis_signature = current_signature


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

analysis = st.session_state.analysis_data
analysis_signature = st.session_state.analysis_signature
if analysis is None or analysis_signature is None:
    st.info(text["initial_instruction"])
else:
    analyzed_parameters = _signature_to_parameters(analysis_signature)
    stale_results = current_signature != analysis_signature
    if stale_results:
        st.warning(text["stale_warning"])

    current_metrics = analysis["current_metrics"]
    optimized_metrics = analysis["optimized_metrics"]
    result = analysis["optimization_result"]
    diagnostics = analysis["optimization_diagnostics"]
    optimized_parameters = analysis["optimized_parameters"]
    reduction_points = current_metrics.unevenness_percent - optimized_metrics.unevenness_percent
    reduction_percent = (
        100.0 * reduction_points / current_metrics.unevenness_percent
        if current_metrics.unevenness_percent > 1.0e-12 else 0.0
    )

    tabs = st.tabs([
        text["overview"], text["velocity"], text["geometry_phase"],
        text["phase_map"], text["data_export"],
    ])

    with tabs[0]:
        summary_columns = st.columns(4)
        summary_columns[0].metric(text["current_unevenness"], f"{current_metrics.unevenness_percent:.5f}%")
        summary_columns[1].metric(
            text["optimized_unevenness"], f"{optimized_metrics.unevenness_percent:.5f}%",
            delta=f"{-reduction_points:.5f} pu", delta_color="inverse",
        )
        summary_columns[2].metric(text["reduction"], f"{reduction_percent:.2f}%")
        summary_columns[3].metric(
            text["candidate_count"],
            _format_integer(core.phase_combination_count(analyzed_parameters), language_code)
            if analyzed_parameters.mode is not CardanMode.SINGLE else "—",
        )

        status_columns = st.columns(2)
        status_columns[0].metric(text["current_status"], _status_text(current_metrics.unevenness_percent, text))
        status_columns[1].metric(text["optimized_status"], _status_text(optimized_metrics.unevenness_percent, text))

        st.markdown(f"### {text['optimum_phase_angles']}")
        if analyzed_parameters.mode is CardanMode.SINGLE:
            st.info(text["single_no_optimization"])
        else:
            phase_columns = st.columns(3)
            phase_columns[0].metric(text["optimum_phi1"], f"{result.phi1_deg:.6f}°")
            phase_columns[1].metric(
                text["optimum_phi2"],
                f"{result.phi2_deg:.6f}°" if result.phi2_deg is not None else "—",
            )
            phase_columns[2].metric(text["selected_method"], _method_text(result.method, text))
            coarse_text = f"φ₁={result.coarse_phi1_deg:.2f}°"
            if result.coarse_phi2_deg is not None:
                coarse_text += f", φ₂={result.coarse_phi2_deg:.2f}°"
            st.caption(f"{text['coarse_solution']}: {coarse_text}")
            st.button(
                text["apply_optimum"], type="primary", on_click=_apply_optimum,
                use_container_width=True, disabled=stale_results,
            )

        st.markdown(f"### {text['optimization_diagnostics']}")
        diagnostic_columns = st.columns(4)
        diagnostic_columns[0].metric(
            text["convergence"], text["success"] if diagnostics.success else text["not_converged"],
        )
        diagnostic_columns[1].metric(
            text["function_evaluations"], _format_integer(diagnostics.function_evaluations, language_code),
        )
        diagnostic_columns[2].metric(text["iterations"], str(diagnostics.iterations))
        diagnostic_columns[3].metric(text["runtime"], f"{diagnostics.elapsed_seconds:.4f} s")

        validation_table = {
            text["metric"]: [text["objective_value"], text["validation_value"], text["validation_delta"]],
            text["optimized"]: [
                f"{diagnostics.objective_unevenness_percent:.8f}%",
                f"{diagnostics.validated_unevenness_percent:.8f}%",
                f"{diagnostics.validation_delta_percent:+.8f} pu",
            ],
        }
        st.dataframe(validation_table, use_container_width=True, hide_index=True)
        if abs(diagnostics.validation_delta_percent) > 0.01:
            st.warning(text["validation_warning"])
        with st.expander(text["diagnostic_message"]):
            st.code(diagnostics.message, language="text")

        st.markdown(f"### {text['engineering_metrics']}")
        metric_table = {
            text["metric"]: [
                text["mean_ratio"], text["minimum_ratio"], text["maximum_ratio"],
                text["rms_error"], text["positive_error"], text["negative_error"],
            ],
            text["current"]: [
                f"{current_metrics.q_mean:.10f}", f"{current_metrics.q_min:.10f}",
                f"{current_metrics.q_max:.10f}", f"{current_metrics.rms_speed_error_percent:.6f}%",
                f"{current_metrics.maximum_positive_error_percent:.6f}%",
                f"{current_metrics.maximum_negative_error_percent:.6f}%",
            ],
            text["optimized"]: [
                f"{optimized_metrics.q_mean:.10f}", f"{optimized_metrics.q_min:.10f}",
                f"{optimized_metrics.q_max:.10f}", f"{optimized_metrics.rms_speed_error_percent:.6f}%",
                f"{optimized_metrics.maximum_positive_error_percent:.6f}%",
                f"{optimized_metrics.maximum_negative_error_percent:.6f}%",
            ],
        }
        st.dataframe(metric_table, use_container_width=True, hide_index=True)
        st.markdown(f'<div class="scope-note">{text["threshold_note"]}</div>', unsafe_allow_html=True)

    with tabs[1]:
        velocity_figure, _, _ = core.plot_velocity_ratio(
            analyzed_parameters, labels=plot_labels, analysis=analysis,
        )
        style_figure_for_dark_theme(velocity_figure)
        st.pyplot(velocity_figure, use_container_width=True)
        plt.close(velocity_figure)

    with tabs[2]:
        st.markdown(f"### {text['current_geometry']}")
        geometry_figure = core.plot_geometry_2d(analyzed_parameters, labels=plot_labels)
        style_figure_for_dark_theme(geometry_figure)
        st.pyplot(geometry_figure, use_container_width=True)
        plt.close(geometry_figure)
        if analyzed_parameters.mode is not CardanMode.SINGLE:
            current_column, optimized_column = st.columns(2)
            with current_column:
                st.markdown(f"#### {text['current_phase']}")
                figure = core.plot_phase_figure(analyzed_parameters, labels=plot_labels)
                if figure is not None:
                    style_figure_for_dark_theme(figure)
                    st.pyplot(figure, use_container_width=True)
                    plt.close(figure)
            with optimized_column:
                st.markdown(f"#### {text['optimized_phase']}")
                figure = core.plot_phase_figure(optimized_parameters, labels=plot_labels)
                if figure is not None:
                    style_figure_for_dark_theme(figure)
                    st.pyplot(figure, use_container_width=True)
                    plt.close(figure)

    with tabs[3]:
        landscape_figure = core.plot_phase_landscape(
            analyzed_parameters, analysis["phase_landscape"], result, labels=plot_labels,
        )
        if landscape_figure is None:
            st.info(text["phase_map_single"])
        else:
            style_figure_for_dark_theme(landscape_figure)
            st.pyplot(landscape_figure, use_container_width=True)
            plt.close(landscape_figure)
            st.caption(text["phase_map_note"])

    with tabs[4]:
        download_columns = st.columns(3)
        download_columns[0].download_button(
            text["export_curves"], data=_curve_csv(analysis),
            file_name="cardan_velocity_curves.csv", mime="text/csv", use_container_width=True,
        )
        download_columns[1].download_button(
            text["export_summary"], data=_summary_json(analyzed_parameters, analysis),
            file_name="cardan_analysis_summary.json", mime="application/json", use_container_width=True,
        )
        download_columns[2].download_button(
            text["export_trajectory"], data=_trajectory_json(analysis),
            file_name="cardan_kinematic_trajectory.json", mime="application/json", use_container_width=True,
        )
        st.markdown(f"### {text['data_preview']}")
        preview_count = 16
        preview = {
            "θ input (deg)": [f"{float(x):.1f}" for x in analysis["theta_plot_deg"][:preview_count]],
            "q current": [f"{float(x):.8f}" for x in analysis["q_current_plot"][:preview_count]],
            "q optimized": [f"{float(x):.8f}" for x in analysis["q_optimized_plot"][:preview_count]],
        }
        st.dataframe(preview, use_container_width=True, hide_index=True)

with st.expander(text["model_scope"]):
    st.markdown(text["model_text"])
st.divider()
st.caption(text["footer"])

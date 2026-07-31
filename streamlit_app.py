"""Beginner-friendly Streamlit interface for Cardan Joint Engineering Tool v2.2.0."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from dataclasses import asdict
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
from matplotlib.figure import Figure
import numpy as np
import streamlit as st

try:
    import xlsxwriter
except ModuleNotFoundError:
    # Keep the analysis application usable even when the optional Excel
    # dependency has not yet been installed by the deployment platform.
    xlsxwriter = None

import cardan_core as core
import cardan_3d_viewer as viewer3d


# ---------------------------------------------------------------------------
# Core compatibility
# ---------------------------------------------------------------------------

_REQUIRED_CORE_API_VERSION = 6
_REQUIRED_CORE_OBJECTS = (
    "CardanMode",
    "CardanParameters",
    "OptimizationMethod",
    "OptimizationSettings",
    "OptimizationDiagnostics",
    "KinematicTrajectory",
    "PlanarSceneGeometry",
    "KinematicScene",
    "PlotLabels",
    "UNEVENNESS_LIMIT_PERCENT",
    "calculate_analysis",
    "calculate_planar_scene_geometry",
    "calculate_kinematic_scene",
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
    page_title="Cardan Joint Engineering Tool v2.2.0",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)


TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "title": "Cardan Joint Engineering Tool",
        "subtitle": "Kinematic analysis, phase optimization, interactive 3D visualization, validation, and export",
        "version": "Version 2.2.0",
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
        "viewer_3d": "Interactive 3D",
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

The core exports every joint's input angle, output angle, individual speed ratio, total speed ratio, planar shaft geometry, yoke axes, and unit quaternions. The Interactive 3D tab consumes this renderer-independent scene data without reimplementing the kinematic equations.

### Limitations

The current model is **kinematic only**. Mass, inertia, torque, bearing reactions, elasticity, backlash, friction, stress, fatigue, torsional vibration, efficiency, and power losses are not included.
""",
        "footer": "Developed by Furkan Kasap · Automotive Engineer",
    },
    "tr": {
        "title": "Kardan Mafsalı Mühendislik Aracı",
        "subtitle": "Kinematik analiz, faz optimizasyonu, etkileşimli 3B görselleştirme, doğrulama ve dışa aktarma",
        "version": "Sürüm 2.2.0",
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
        "viewer_3d": "Etkileşimli 3B",
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

Çekirdek her mafsalın giriş/çıkış açılarını, ayrı ve toplam hız oranlarını, düzlemsel mil geometrisini, çatal eksenlerini ve birim quaternion değerlerini üretir. Etkileşimli 3B sekmesi, kinematik denklemleri yeniden yazmadan bu renderer bağımsız sahne verisini kullanır.

### Sınırlamalar

Mevcut model **yalnızca kinematiktir**. Kütle, atalet, tork, yatak tepkileri, elastikiyet, boşluk, sürtünme, gerilme, yorulma, burulma titreşimi, verim ve güç kayıpları modele dahil değildir.
""",
        "footer": "Geliştiren: Furkan Kasap · Otomotiv Mühendisi",
    },
}


TRANSLATIONS["en"].update({
    "version": "Version 2.2.0",
    "language": "Language / Dil",
    "language_english": "English",
    "language_turkish": "Türkçe",
    "analysis_quality": "Analysis Quality",
    "standard_mode": "Standard analysis",
    "ultra_mode": "Ultra-accurate optimization",
    "standard_note": "Fast deterministic analysis. Results update automatically when inputs change.",
    "ultra_note": "Continuous global optimization. Run it manually after changing inputs.",
    "advanced_settings": "Advanced settings",
    "expert_mode": "Show expert algorithm controls",
    "expert_help": "Expose all four core optimization methods for benchmarking and research.",
    "live_analysis": "Update standard analysis automatically",
    "precise_angles": "Use precise 0.01° angle controls",
    "run_ultra": "Run ultra optimization",
    "run_manual": "Run analysis",
    "analysis_complete": "Analysis completed",
    "analysis_mode": "Mode",
    "standard_label": "Standard",
    "ultra_label": "Ultra",
    "advanced_metrics": "Advanced engineering metrics",
    "advanced_diagnostics": "Optimization and validation details",
    "optimized_min_ratio": "Optimized minimum q",
    "optimized_max_ratio": "Optimized maximum q",
    "optimized_rms": "Optimized RMS error",
    "export_excel": "Download engineering workbook (Excel)",
    "prepare_excel": "Prepare Excel workbook",
    "excel_ready": "Excel workbook is ready to download.",
    "excel_unavailable": "Excel export is temporarily unavailable because XlsxWriter is not installed. Add XlsxWriter to requirements.txt and reboot the app.",
    "preview_theta": "Input angle θ (deg)",
    "preview_current": "Current speed ratio q",
    "preview_optimized": "Optimized speed ratio q",
    "validation_good": "Dense validation agrees with the optimizer objective.",
    "precision_note": "Full numerical precision is retained in calculations and exported files.",
    "initial_instruction": "Set the system parameters. Standard analysis runs automatically.",
    "stale_warning": "Inputs changed. Run the selected manual/ultra analysis to refresh the results.",
    "viewer_configuration": "3D configuration",
    "viewer_current": "Current configuration",
    "viewer_optimized": "Optimized configuration",
    "viewer_camera": "Camera preset",
    "camera_isometric": "Isometric",
    "camera_top": "Top",
    "camera_side": "Side",
    "camera_front": "Front",
    "viewer_speed": "Animation speed",
    "viewer_detail": "Animation detail",
    "viewer_balanced": "Balanced",
    "viewer_smooth": "Smooth",
    "viewer_fast": "Lightweight",
    "viewer_unavailable": "Interactive 3D is unavailable because Plotly is not installed. Add plotly to requirements.txt and reboot the app.",
    "viewer_caption": "The viewer is a canonical planar engineering schematic. It preserves the entered beta and phase kinematics, but it is not a general spatial CAD reconstruction.",
    "viewer_instructions": "Use the mouse to orbit, pan, and zoom. Press Play or drag the θ slider to inspect one complete input-shaft revolution.",
    "export_scene": "Download 3D scene data (JSON)",
})

TRANSLATIONS["tr"].update({
    "version": "Sürüm 2.2.0",
    "language": "Dil / Language",
    "language_english": "English",
    "language_turkish": "Türkçe",
    "analysis_quality": "Analiz Kalitesi",
    "standard_mode": "Standart analiz",
    "ultra_mode": "Ultra hassas optimizasyon",
    "standard_note": "Hızlı ve deterministik analiz. Girişler değiştiğinde sonuçlar otomatik yenilenir.",
    "ultra_note": "Sürekli global optimizasyon. Girişleri değiştirdikten sonra elle çalıştırılır.",
    "advanced_settings": "Gelişmiş ayarlar",
    "expert_mode": "Uzman algoritma kontrollerini göster",
    "expert_help": "Karşılaştırma ve araştırma için çekirdekteki dört optimizasyon yöntemini açar.",
    "live_analysis": "Standart analizi otomatik güncelle",
    "precise_angles": "Hassas 0,01° açı kontrollerini kullan",
    "run_ultra": "Ultra optimizasyonu çalıştır",
    "run_manual": "Analizi çalıştır",
    "analysis_complete": "Analiz tamamlandı",
    "analysis_mode": "Mod",
    "standard_label": "Standart",
    "ultra_label": "Ultra",
    "advanced_metrics": "Gelişmiş mühendislik metrikleri",
    "advanced_diagnostics": "Optimizasyon ve doğrulama ayrıntıları",
    "optimized_min_ratio": "Optimize edilmiş minimum q",
    "optimized_max_ratio": "Optimize edilmiş maksimum q",
    "optimized_rms": "Optimize edilmiş RMS hata",
    "export_excel": "Mühendislik çalışma kitabını indir (Excel)",
    "prepare_excel": "Excel çalışma kitabını hazırla",
    "excel_ready": "Excel çalışma kitabı indirilmeye hazır.",
    "excel_unavailable": "XlsxWriter kurulmadığı için Excel dışa aktarma geçici olarak kullanılamıyor. requirements.txt dosyasına XlsxWriter ekleyip uygulamayı yeniden başlatın.",
    "preview_theta": "Giriş açısı θ (°)",
    "preview_current": "Mevcut hız oranı q",
    "preview_optimized": "Optimize edilmiş hız oranı q",
    "validation_good": "Yoğun doğrulama ile optimize edici amaç değeri uyumludur.",
    "precision_note": "Hesaplamalarda ve dışa aktarılan dosyalarda tam sayısal hassasiyet korunur.",
    "initial_instruction": "Sistem parametrelerini ayarlayın. Standart analiz otomatik çalışır.",
    "stale_warning": "Girişler değişti. Sonuçları yenilemek için seçilen manuel/ultra analizi çalıştırın.",
    "viewer_configuration": "3B konfigürasyon",
    "viewer_current": "Mevcut konfigürasyon",
    "viewer_optimized": "Optimize edilmiş konfigürasyon",
    "viewer_camera": "Kamera görünümü",
    "camera_isometric": "İzometrik",
    "camera_top": "Üst",
    "camera_side": "Yan",
    "camera_front": "Ön",
    "viewer_speed": "Animasyon hızı",
    "viewer_detail": "Animasyon ayrıntısı",
    "viewer_balanced": "Dengeli",
    "viewer_smooth": "Akıcı",
    "viewer_fast": "Hafif",
    "viewer_unavailable": "Plotly kurulmadığı için etkileşimli 3B görüntü kullanılamıyor. requirements.txt dosyasına plotly ekleyip uygulamayı yeniden başlatın.",
    "viewer_caption": "Bu görüntüleyici kanonik düzlemsel bir mühendislik şemasıdır. Girilen beta ve faz kinematiğini korur; ancak genel uzaysal bir CAD rekonstrüksiyonu değildir.",
    "viewer_instructions": "Fareyle kamerayı döndürebilir, kaydırabilir ve yakınlaştırabilirsiniz. Bir tam giriş mili devrini incelemek için Oynat'a basın veya θ kaydırıcısını sürükleyin.",
    "export_scene": "3B sahne verisini indir (JSON)",
})


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


VIEWER_LABELS: dict[str, viewer3d.ViewerLabels] = {
    "en": viewer3d.ViewerLabels(
        title="Schematic 3D Cardan Kinematics",
        current="Current",
        optimized="Optimized",
        selected_current="Current configuration",
        selected_optimized="Optimized configuration",
        input_angle="Input angle θ (deg)",
        speed_ratio="Total speed ratio q",
        play="Play",
        pause="Pause",
        joint="Joint",
        shaft="Shaft",
        input_yoke="Input yoke",
        output_yoke="Output yoke",
        cross="Cross",
        schematic_note="Canonical planar schematic — not a general spatial CAD reconstruction",
    ),
    "tr": viewer3d.ViewerLabels(
        title="Şematik 3B Kardan Kinematiği",
        current="Mevcut",
        optimized="Optimize edilmiş",
        selected_current="Mevcut konfigürasyon",
        selected_optimized="Optimize edilmiş konfigürasyon",
        input_angle="Giriş açısı θ (derece)",
        speed_ratio="Toplam hız oranı q",
        play="Oynat",
        pause="Duraklat",
        joint="Mafsal",
        shaft="Mil",
        input_yoke="Giriş çatalı",
        output_yoke="Çıkış çatalı",
        cross="İstavroz",
        schematic_note="Kanonik düzlemsel şema — genel uzaysal CAD rekonstrüksiyonu değildir",
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
    st.session_state.ultra_mode = False
    st.session_state.expert_mode = False
    st.session_state.live_analysis = True
    st.session_state.precise_angles = False
    st.session_state.optimization_method = OptimizationMethod.LOCAL_REFINEMENT.value
    st.session_state.local_refinement_step_deg = 0.25
    st.session_state.de_max_iterations = 80
    st.session_state.de_population_size = 12
    st.session_state.de_tolerance = 1.0e-7
    st.session_state.de_seed = 42
    st.session_state.validation_sample_count = 3600
    st.session_state.de_polish = False
    st.session_state.analysis_data = None
    st.session_state.analysis_signature = None


def _on_ultra_mode_change() -> None:
    enabled = bool(st.session_state.get("ultra_mode", False))
    st.session_state.validation_sample_count = 7200 if enabled else 1800
    st.session_state.optimization_method = (
        OptimizationMethod.HYBRID.value
        if enabled else OptimizationMethod.LOCAL_REFINEMENT.value
    )


def _on_precision_change() -> None:
    if bool(st.session_state.get("precise_angles", False)):
        return
    for key in ("beta1_deg", "beta2_deg", "beta3_deg", "phi1_deg", "phi2_deg", "theta0_deg"):
        number_key = f"{key}_number"
        if number_key in st.session_state:
            rounded = round(float(st.session_state[number_key]) * 2.0) / 2.0
            _set_angle_state(key, rounded)


def _apply_optimum() -> None:
    analysis = st.session_state.get("analysis_data")
    if not analysis:
        return
    result = analysis["optimization_result"]
    if result.phi1_deg is not None:
        _set_angle_state("phi1_deg", float(result.phi1_deg))
    if result.phi2_deg is not None:
        _set_angle_state("phi2_deg", float(result.phi2_deg))
    phase_values = [value for value in (result.phi1_deg, result.phi2_deg) if value is not None]
    if any(abs(float(value) * 2.0 - round(float(value) * 2.0)) > 1.0e-8 for value in phase_values):
        st.session_state.precise_angles = True
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


def _format_decimal(value: float, decimals: int, language_code: str) -> str:
    formatted = f"{float(value):.{decimals}f}"
    return formatted.replace(".", ",") if language_code == "tr" else formatted


def _format_percent(value: float, language_code: str, decimals: int = 2) -> str:
    if 0.0 < abs(float(value)) < 10.0 ** (-decimals):
        threshold = _format_decimal(10.0 ** (-decimals), decimals, language_code)
        return f"<{threshold}%"
    return f"{_format_decimal(value, decimals, language_code)}%"


def _format_degree(value: float | None, language_code: str, decimals: int = 2) -> str:
    if value is None:
        return "—"
    return f"{_format_decimal(value, decimals, language_code)}°"


def _format_ratio(value: float, language_code: str) -> str:
    return _format_decimal(value, 5, language_code)


def _status_text(value: float, text: dict[str, str]) -> str:
    return text["status_ok"] if value <= UNEVENNESS_LIMIT_PERCENT else text["status_warning"]


def _method_text(method: str, text: dict[str, str]) -> str:
    return {
        OptimizationMethod.GRID.value: text["method_grid"],
        OptimizationMethod.LOCAL_REFINEMENT.value: text["method_local"],
        OptimizationMethod.DIFFERENTIAL_EVOLUTION.value: text["method_de"],
        OptimizationMethod.HYBRID.value: text["method_hybrid"],
    }.get(method, method)


def _curve_csv(analysis: dict[str, Any], language_code: str) -> bytes:
    text = TRANSLATIONS[language_code]
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        text["preview_theta"], text["preview_current"], text["preview_optimized"],
        "Mevcut hız hatası (%)" if language_code == "tr" else "Current speed error (%)",
        "Optimize edilmiş hız hatası (%)" if language_code == "tr" else "Optimized speed error (%)",
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
    return buffer.getvalue().encode("utf-8-sig")


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
        "version": "2.2.0",
        "display_revolution_deg": 360.0,
        "kinematic_period_deg": 180.0,
        "phase_convention": "theta_next = theta_out - phi",
        "current": _trajectory_payload(analysis["current_trajectory"]),
        "optimized": _trajectory_payload(analysis["optimized_trajectory"]),
    }
    return json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")


def _scene_json(
    parameters: CardanParameters,
    trajectory: core.KinematicTrajectory,
    selected_kind: str,
) -> bytes:
    scene = core.calculate_kinematic_scene(parameters, trajectory)
    geometry = scene.geometry
    payload = {
        "model": "Cardan Joint Engineering Tool",
        "version": "2.2.0",
        "scene_type": "canonical_planar_schematic",
        "selected_configuration": selected_kind,
        "input_rotation_deg": scene.input_rotation_deg.tolist(),
        "geometry": {
            "shaft_length": geometry.shaft_length,
            "shaft_points": geometry.shaft_points.tolist(),
            "shaft_directions": geometry.shaft_directions.tolist(),
            "joint_centers": geometry.joint_centers.tolist(),
            "joint_plane_normals": geometry.joint_plane_normals.tolist(),
        },
        "poses": {
            "shaft_rotation_angles_deg": scene.shaft_rotation_angles_deg.tolist(),
            "input_yoke_axes": scene.input_yoke_axes.tolist(),
            "output_yoke_axes": scene.output_yoke_axes.tolist(),
            "shaft_quaternions_wxyz": scene.shaft_quaternions_wxyz.tolist(),
            "input_yoke_quaternions_wxyz": scene.input_yoke_quaternions_wxyz.tolist(),
            "output_yoke_quaternions_wxyz": scene.output_yoke_quaternions_wxyz.tolist(),
            "cross_quaternions_wxyz": scene.cross_quaternions_wxyz.tolist(),
        },
        "note": (
            "The geometry is a canonical planar schematic preserving the entered "
            "misalignment and phase kinematics; it is not a general spatial CAD reconstruction."
        ),
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
        "version": "2.2.0",
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


def _excel_workbook(
    parameters: CardanParameters,
    analysis: dict[str, Any],
    language_code: str,
) -> bytes:
    """Create a formatted multi-sheet engineering workbook in memory."""
    if xlsxwriter is None:
        raise RuntimeError(
            "Excel export requires XlsxWriter. Install dependencies from requirements.txt."
        )

    text = TRANSLATIONS[language_code]
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})
    workbook.set_properties({
        "title": "Cardan Joint Engineering Analysis",
        "subject": "Kinematic phase optimization results",
        "author": "Furkan Kasap",
        "comments": "Generated by Cardan Joint Engineering Tool v2.2.0",
    })

    title_fmt = workbook.add_format({
        "bold": True, "font_size": 16, "font_color": "#FFFFFF",
        "bg_color": "#1F4E78", "align": "center", "valign": "vcenter",
    })
    section_fmt = workbook.add_format({
        "bold": True, "font_color": "#FFFFFF", "bg_color": "#2F75B5",
        "border": 1, "align": "left",
    })
    header_fmt = workbook.add_format({
        "bold": True, "font_color": "#FFFFFF", "bg_color": "#5B9BD5",
        "border": 1, "align": "center", "valign": "vcenter", "text_wrap": True,
    })
    label_fmt = workbook.add_format({"bold": True, "bg_color": "#D9EAF7", "border": 1})
    value_fmt = workbook.add_format({"border": 1})
    number_fmt = workbook.add_format({"border": 1, "num_format": "0.000000"})
    percent_fmt = workbook.add_format({"border": 1, "num_format": "0.00\"%\""})
    degree_fmt = workbook.add_format({"border": 1, "num_format": "0.00\"°\""})
    ratio_fmt = workbook.add_format({"border": 1, "num_format": "0.0000000000"})
    note_fmt = workbook.add_format({"italic": True, "font_color": "#666666", "text_wrap": True})

    result = analysis["optimization_result"]
    diagnostics = analysis["optimization_diagnostics"]
    current = analysis["current_metrics"]
    optimized = analysis["optimized_metrics"]
    reduction = (
        100.0 * (current.unevenness_percent - optimized.unevenness_percent)
        / current.unevenness_percent
        if current.unevenness_percent > 1.0e-12 else 0.0
    )

    summary_name = "Özet" if language_code == "tr" else "Summary"
    ws = workbook.add_worksheet(summary_name)
    ws.hide_gridlines(2)
    ws.set_column("A:A", 31)
    ws.set_column("B:B", 23)
    ws.set_column("D:K", 13)
    ws.merge_range("A1:B1", text["title"], title_fmt)
    ws.write("A3", text["metric"], header_fmt)
    ws.write("B3", "Değer" if language_code == "tr" else "Value", header_fmt)
    summary_rows = [
        (text["configuration"], {1: text["mode_single"], 2: text["mode_double"], 3: text["mode_triple"]}[int(parameters.mode)], value_fmt),
        (text["current_unevenness"], current.unevenness_percent, percent_fmt),
        (text["optimized_unevenness"], optimized.unevenness_percent, percent_fmt),
        (text["reduction"], reduction, percent_fmt),
        (text["optimum_phi1"], result.phi1_deg, degree_fmt),
        (text["optimum_phi2"], result.phi2_deg, degree_fmt),
        (text["selected_method"], _method_text(result.method, text), value_fmt),
        (text["runtime"], diagnostics.elapsed_seconds, number_fmt),
        (text["optimized_status"], _status_text(optimized.unevenness_percent, text), value_fmt),
        ("Sürüm" if language_code == "tr" else "Version", "2.2.0", value_fmt),
        ("Oluşturulma zamanı" if language_code == "tr" else "Generated at", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), value_fmt),
    ]
    for row, (label, value, fmt) in enumerate(summary_rows, start=3):
        ws.write(row, 0, label, label_fmt)
        if value is None:
            ws.write(row, 1, "—", value_fmt)
        else:
            ws.write(row, 1, value, fmt)
    ws.write("A17", text["threshold_note"], note_fmt)

    # Input parameters.
    inputs_name = "Girişler" if language_code == "tr" else "Inputs"
    wi = workbook.add_worksheet(inputs_name)
    wi.hide_gridlines(2)
    wi.set_column("A:A", 31)
    wi.set_column("B:B", 20)
    wi.merge_range("A1:B1", inputs_name, title_fmt)
    wi.write_row("A3", [text["metric"], "Değer" if language_code == "tr" else "Value"], header_fmt)
    input_rows = [
        ("β₁", parameters.beta1_deg), ("β₂", parameters.beta2_deg), ("β₃", parameters.beta3_deg),
        ("φ₁", parameters.phi1_deg), ("φ₂", parameters.phi2_deg),
        ("θ₀", parameters.theta0_deg), (text["phase_search_step"], parameters.optimization_step_deg),
    ]
    for row, (label, value) in enumerate(input_rows, start=3):
        wi.write(row, 0, label, label_fmt)
        wi.write(row, 1, value, degree_fmt)

    # Current vs optimized metrics.
    comp_name = "Karşılaştırma" if language_code == "tr" else "Comparison"
    wc = workbook.add_worksheet(comp_name)
    wc.hide_gridlines(2)
    wc.set_column("A:A", 34)
    wc.set_column("B:C", 21)
    wc.merge_range("A1:C1", comp_name, title_fmt)
    wc.write_row("A3", [text["metric"], text["current"], text["optimized"]], header_fmt)
    comparison = [
        (text["mean_ratio"], current.q_mean, optimized.q_mean, ratio_fmt),
        (text["minimum_ratio"], current.q_min, optimized.q_min, ratio_fmt),
        (text["maximum_ratio"], current.q_max, optimized.q_max, ratio_fmt),
        (text["current_unevenness"], current.unevenness_percent, optimized.unevenness_percent, percent_fmt),
        (text["rms_error"], current.rms_speed_error_percent, optimized.rms_speed_error_percent, percent_fmt),
        (text["positive_error"], current.maximum_positive_error_percent, optimized.maximum_positive_error_percent, percent_fmt),
        (text["negative_error"], current.maximum_negative_error_percent, optimized.maximum_negative_error_percent, percent_fmt),
    ]
    for row, (label, a, b, fmt) in enumerate(comparison, start=3):
        wc.write(row, 0, label, label_fmt)
        wc.write(row, 1, a, fmt)
        wc.write(row, 2, b, fmt)

    # Velocity curves and chart.
    curves_name = "Hız Eğrileri" if language_code == "tr" else "Velocity Curves"
    wv = workbook.add_worksheet(curves_name)
    wv.freeze_panes(1, 0)
    wv.set_column("A:A", 18)
    wv.set_column("B:E", 22)
    curve_headers = [
        text["preview_theta"], text["preview_current"], text["preview_optimized"],
        "Mevcut hız hatası (%)" if language_code == "tr" else "Current speed error (%)",
        "Optimize edilmiş hız hatası (%)" if language_code == "tr" else "Optimized speed error (%)",
    ]
    wv.write_row(0, 0, curve_headers, header_fmt)
    current_mean = current.q_mean
    optimized_mean = optimized.q_mean
    for row, (theta, q_current, q_optimized) in enumerate(zip(
        analysis["theta_plot_deg"], analysis["q_current_plot"], analysis["q_optimized_plot"]
    ), start=1):
        wv.write_number(row, 0, float(theta), degree_fmt)
        wv.write_number(row, 1, float(q_current), ratio_fmt)
        wv.write_number(row, 2, float(q_optimized), ratio_fmt)
        wv.write_number(row, 3, 100.0 * (float(q_current) / current_mean - 1.0), percent_fmt)
        wv.write_number(row, 4, 100.0 * (float(q_optimized) / optimized_mean - 1.0), percent_fmt)
    chart = workbook.add_chart({"type": "line"})
    last_row = len(analysis["theta_plot_deg"])
    chart.add_series({
        "name": text["current"], "categories": [curves_name, 1, 0, last_row, 0],
        "values": [curves_name, 1, 1, last_row, 1], "line": {"width": 2.0},
    })
    chart.add_series({
        "name": text["optimized"], "categories": [curves_name, 1, 0, last_row, 0],
        "values": [curves_name, 1, 2, last_row, 2], "line": {"width": 2.0, "dash_type": "dash"},
    })
    chart.set_title({"name": text["velocity"]})
    chart.set_x_axis({"name": text["preview_theta"]})
    chart.set_y_axis({"name": "q = ωout / ωin"})
    chart.set_legend({"position": "bottom"})
    chart.set_size({"width": 760, "height": 390})
    ws.insert_chart("D3", chart)

    # Kinematic trajectory.
    traj_name = "Kinematik Yörünge" if language_code == "tr" else "Kinematic Trajectory"
    wt = workbook.add_worksheet(traj_name)
    wt.freeze_panes(1, 0)
    current_traj = analysis["current_trajectory"]
    optimized_traj = analysis["optimized_trajectory"]
    headers = [text["preview_theta"]]
    joint_count = current_traj.joint_input_angles_deg.shape[0]
    for prefix in (("Mevcut" if language_code == "tr" else "Current"), ("Optimize" if language_code == "tr" else "Optimized")):
        for joint in range(joint_count):
            headers.extend([
                f"{prefix} J{joint+1} θin (°)", f"{prefix} J{joint+1} θout (°)", f"{prefix} J{joint+1} q",
            ])
        headers.append(f"{prefix} q total")
    wt.write_row(0, 0, headers, header_fmt)
    for row in range(current_traj.input_rotation_deg.size):
        values = [float(current_traj.input_rotation_deg[row])]
        for traj in (current_traj, optimized_traj):
            for joint in range(joint_count):
                values.extend([
                    float(traj.joint_input_angles_deg[joint, row]),
                    float(traj.joint_output_angles_deg[joint, row]),
                    float(traj.joint_speed_ratios[joint, row]),
                ])
            values.append(float(traj.total_speed_ratio[row]))
        wt.write_row(row + 1, 0, values, number_fmt)
    wt.set_column(0, len(headers) - 1, 18)

    # Phase landscape in long format.
    phase_name = "Faz Haritası" if language_code == "tr" else "Phase Landscape"
    wp = workbook.add_worksheet(phase_name)
    wp.freeze_panes(1, 0)
    landscape = analysis["phase_landscape"]
    if landscape is None:
        wp.write("A1", text["phase_map_single"], note_fmt)
    elif landscape.phase_values_phi2_deg is None:
        wp.write_row("A1", ["φ₁ (°)", text["current_unevenness"] + " (%)"], header_fmt)
        for row, (phi1, unevenness) in enumerate(zip(
            landscape.phase_values_phi1_deg, landscape.unevenness_percent
        ), start=1):
            wp.write_number(row, 0, float(phi1), degree_fmt)
            wp.write_number(row, 1, float(unevenness), percent_fmt)
        wp.set_column("A:B", 22)
    else:
        wp.write_row("A1", ["φ₁ (°)", "φ₂ (°)", text["current_unevenness"] + " (%)"], header_fmt)
        row = 1
        for i, phi1 in enumerate(landscape.phase_values_phi1_deg):
            for j, phi2 in enumerate(landscape.phase_values_phi2_deg):
                wp.write_number(row, 0, float(phi1), degree_fmt)
                wp.write_number(row, 1, float(phi2), degree_fmt)
                wp.write_number(row, 2, float(landscape.unevenness_percent[i, j]), percent_fmt)
                row += 1
        wp.set_column("A:C", 22)

    # Advanced diagnostics.
    diag_name = "Teşhisler" if language_code == "tr" else "Diagnostics"
    wd = workbook.add_worksheet(diag_name)
    wd.hide_gridlines(2)
    wd.set_column("A:A", 34)
    wd.set_column("B:B", 70)
    wd.merge_range("A1:B1", text["advanced_diagnostics"], title_fmt)
    diagnostics_rows = [
        (text["selected_method"], _method_text(diagnostics.method, text)),
        (text["convergence"], text["success"] if diagnostics.success else text["not_converged"]),
        (text["function_evaluations"], diagnostics.function_evaluations),
        (text["iterations"], diagnostics.iterations),
        (text["runtime"], diagnostics.elapsed_seconds),
        (text["objective_value"], diagnostics.objective_unevenness_percent),
        (text["validation_value"], diagnostics.validated_unevenness_percent),
        (text["validation_delta"], diagnostics.validation_delta_percent),
        (text["validation_samples"], diagnostics.validation_sample_count),
        (text["random_seed"], diagnostics.random_seed),
        (text["diagnostic_message"], diagnostics.message),
    ]
    for row, (label, value) in enumerate(diagnostics_rows, start=2):
        wd.write(row, 0, label, label_fmt)
        wd.write(row, 1, value if value is not None else "—", value_fmt)

    workbook.close()
    return output.getvalue()


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
        div[role="radiogroup"] { justify-content: flex-start; gap: 0.35rem; }
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
if "ultra_mode" not in st.session_state:
    st.session_state.ultra_mode = False
if "expert_mode" not in st.session_state:
    st.session_state.expert_mode = False
if "live_analysis" not in st.session_state:
    st.session_state.live_analysis = True
if "precise_angles" not in st.session_state:
    st.session_state.precise_angles = False
if "excel_export_bytes" not in st.session_state:
    st.session_state.excel_export_bytes = None
if "excel_export_key" not in st.session_state:
    st.session_state.excel_export_key = None

for _phase_key in ("phi1_deg", "phi2_deg"):
    _number_key = f"{_phase_key}_number"
    if _number_key in st.session_state and not 0.0 <= float(st.session_state[_number_key]) <= 180.0:
        _set_angle_state(_phase_key, float(st.session_state[_number_key]) % 180.0)

language_code = "tr" if st.session_state.ui_language == "TR" else "en"
text = TRANSLATIONS[language_code]
plot_labels = PLOT_LABELS[language_code]
viewer_labels = VIEWER_LABELS[language_code]

st.title(text["title"])
st.markdown(f'<div class="app-subtitle">{text["subtitle"]}</div>', unsafe_allow_html=True)
st.markdown(f'<span class="version-badge">{text["version"]}</span>', unsafe_allow_html=True)

with st.sidebar:
    st.radio(
        text["language"],
        options=("TR", "EN"),
        key="ui_language",
        horizontal=True,
        format_func=lambda value: text["language_turkish"] if value == "TR" else text["language_english"],
    )
    language_code = "tr" if st.session_state.ui_language == "TR" else "en"
    _write_language_to_url(language_code)
    text = TRANSLATIONS[language_code]
    plot_labels = PLOT_LABELS[language_code]
    viewer_labels = VIEWER_LABELS[language_code]

    st.divider()
    st.header(text["system_parameters"])
    mode_value = st.selectbox(
        text["configuration"], options=(1, 2, 3), index=2, key="mode_value",
        format_func=lambda value: {
            1: text["mode_single"], 2: text["mode_double"], 3: text["mode_triple"],
        }[int(value)],
    )
    mode = CardanMode(int(mode_value))
    angle_step = 0.01 if bool(st.session_state.precise_angles) else 0.5

    st.subheader(text["misalignment_angles"])
    beta1_deg = sidebar_angle_input(
        "β₁ (°)", key="beta1_deg", min_value=0.0, max_value=60.0,
        default_value=25.0, direct_value_text=text["direct_value"], step=angle_step,
        help_text=text["beta_help"],
    )
    beta2_deg = 25.0
    beta3_deg = 25.0
    if mode >= CardanMode.DOUBLE:
        beta2_deg = sidebar_angle_input(
            "β₂ (°)", key="beta2_deg", min_value=0.0, max_value=60.0,
            default_value=25.0, direct_value_text=text["direct_value"], step=angle_step,
            help_text=text["beta_help"],
        )
    if mode is CardanMode.TRIPLE:
        beta3_deg = sidebar_angle_input(
            "β₃ (°)", key="beta3_deg", min_value=0.0, max_value=60.0,
            default_value=25.0, direct_value_text=text["direct_value"], step=angle_step,
            help_text=text["beta_help"],
        )

    phi1_deg = 0.0
    phi2_deg = 0.0
    if mode >= CardanMode.DOUBLE:
        st.subheader(text["phase_angles"])
        phi1_deg = sidebar_angle_input(
            "φ₁ (°)", key="phi1_deg", min_value=0.0, max_value=180.0,
            default_value=0.0, direct_value_text=text["direct_value"], step=angle_step,
            help_text=text["phase_help"],
        )
        if mode is CardanMode.TRIPLE:
            phi2_deg = sidebar_angle_input(
                "φ₂ (°)", key="phi2_deg", min_value=0.0, max_value=180.0,
                default_value=0.0, direct_value_text=text["direct_value"], step=angle_step,
                help_text=text["phase_help"],
            )

    st.subheader(text["angular_reference"])
    theta0_deg = sidebar_angle_input(
        "θ₀ (°)", key="theta0_deg", min_value=0.0, max_value=180.0,
        default_value=0.0, direct_value_text=text["direct_value"], step=angle_step,
        help_text=text["theta_help"],
    )

    optimization_step_deg = 5.0
    local_step = 0.25
    method_value = OptimizationMethod.LOCAL_REFINEMENT.value
    de_max_iterations = 80
    de_population_size = 12
    de_tolerance = 1.0e-7
    de_seed = 42
    validation_sample_count = 1800
    de_polish = False

    ultra_mode = bool(st.session_state.ultra_mode) if mode >= CardanMode.DOUBLE else False
    if mode >= CardanMode.DOUBLE:
        st.caption(text["ultra_note"] if ultra_mode else text["standard_note"])

    with st.expander(text["advanced_settings"], expanded=False):
        if mode >= CardanMode.DOUBLE:
            ultra_mode = bool(st.checkbox(
                text["ultra_mode"], key="ultra_mode", help=text["ultra_note"],
                on_change=_on_ultra_mode_change,
            ))
        else:
            ultra_mode = False
        st.checkbox(
            text["precise_angles"], key="precise_angles", on_change=_on_precision_change
        )
        if not ultra_mode:
            st.checkbox(text["live_analysis"], key="live_analysis")
        expert_mode = bool(st.checkbox(
            text["expert_mode"], value=False, key="expert_mode", help=text["expert_help"]
        ))

        optimization_step_deg = sidebar_angle_input(
            text["phase_search_step"], key="optimization_step_deg",
            min_value=1.0, max_value=15.0, default_value=5.0,
            direct_value_text=text["direct_value"], step=0.5,
            help_text=text["optimization_help"],
        )
        local_step = float(st.select_slider(
            text["refinement_step"], options=(0.05, 0.10, 0.25, 0.50, 1.00),
            value=0.25, key="local_refinement_step_deg",
            format_func=lambda value: f"{value:.2f}°",
        ))

        if expert_mode:
            method_options = [item.value for item in OptimizationMethod]
            default_method = OptimizationMethod.HYBRID.value if ultra_mode else OptimizationMethod.LOCAL_REFINEMENT.value
            if st.session_state.get("optimization_method") not in method_options:
                st.session_state.optimization_method = default_method
            method_value = st.selectbox(
                text["method"], options=method_options,
                index=method_options.index(default_method), key="optimization_method",
                format_func=lambda value: _method_text(value, text), help=text["method_help"],
            )
        else:
            method_value = (
                OptimizationMethod.HYBRID.value if ultra_mode
                else OptimizationMethod.LOCAL_REFINEMENT.value
            )

        if method_value in {
            OptimizationMethod.DIFFERENTIAL_EVOLUTION.value,
            OptimizationMethod.HYBRID.value,
        }:
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
            validation_default = 7200
        else:
            validation_default = 1800

        validation_sample_count = int(st.select_slider(
            text["validation_samples"], options=(360, 720, 1800, 3600, 7200, 18000),
            value=validation_default, key="validation_sample_count",
            format_func=lambda value: _format_integer(int(value), language_code),
        ))

    run_label = text["run_ultra"] if ultra_mode else text["run_manual"]
    run_button = st.button(run_label, type="primary", use_container_width=True)
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

standard_auto_run = (
    not ultra_mode and bool(st.session_state.live_analysis)
)
should_run = run_button or standard_auto_run or st.session_state.auto_run_after_apply
if should_run:
    st.session_state.auto_run_after_apply = False
    with st.spinner(text["spinner"]):
        st.session_state.analysis_data = _cached_analysis(current_signature)
        st.session_state.analysis_signature = current_signature

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
    display_mode = text["ultra_label"] if result.method in {
        OptimizationMethod.DIFFERENTIAL_EVOLUTION.value, OptimizationMethod.HYBRID.value
    } else text["standard_label"]

    tabs = st.tabs([
        text["overview"], text["velocity"], text["geometry_phase"],
        text["viewer_3d"], text["phase_map"], text["data_export"],
    ])

    with tabs[0]:
        summary_columns = st.columns(4)
        summary_columns[0].metric(
            text["current_unevenness"], _format_percent(current_metrics.unevenness_percent, language_code)
        )
        summary_columns[1].metric(
            text["optimized_unevenness"], _format_percent(optimized_metrics.unevenness_percent, language_code),
            delta=f"-{_format_decimal(reduction_points, 2, language_code)} pu", delta_color="inverse",
        )
        summary_columns[2].metric(text["reduction"], _format_percent(reduction_percent, language_code))
        summary_columns[3].metric(text["optimized_status"], _status_text(optimized_metrics.unevenness_percent, text))

        if analyzed_parameters.mode is CardanMode.SINGLE:
            st.info(text["single_no_optimization"])
        else:
            st.markdown(f"### {text['optimum_phase_angles']}")
            phase_columns = st.columns(3)
            phase_columns[0].metric(text["optimum_phi1"], _format_degree(result.phi1_deg, language_code))
            phase_columns[1].metric(text["optimum_phi2"], _format_degree(result.phi2_deg, language_code))
            phase_columns[2].metric(text["analysis_mode"], display_mode)
            st.button(
                text["apply_optimum"], type="primary", on_click=_apply_optimum,
                use_container_width=True, disabled=stale_results,
            )

        st.success(
            f"{text['analysis_complete']} · {text['analysis_mode']}: {display_mode} · "
            f"{text['runtime']}: {_format_decimal(diagnostics.elapsed_seconds, 3, language_code)} s"
        )

        quick_columns = st.columns(3)
        quick_columns[0].metric(text["optimized_min_ratio"], _format_ratio(optimized_metrics.q_min, language_code))
        quick_columns[1].metric(text["optimized_max_ratio"], _format_ratio(optimized_metrics.q_max, language_code))
        quick_columns[2].metric(text["optimized_rms"], _format_percent(optimized_metrics.rms_speed_error_percent, language_code))
        st.caption(text["precision_note"])

        if abs(diagnostics.validation_delta_percent) > 0.01:
            st.warning(text["validation_warning"])

        with st.expander(text["advanced_metrics"], expanded=False):
            metric_table = {
                text["metric"]: [
                    text["mean_ratio"], text["minimum_ratio"], text["maximum_ratio"],
                    text["rms_error"], text["positive_error"], text["negative_error"],
                ],
                text["current"]: [
                    _format_ratio(current_metrics.q_mean, language_code),
                    _format_ratio(current_metrics.q_min, language_code),
                    _format_ratio(current_metrics.q_max, language_code),
                    _format_percent(current_metrics.rms_speed_error_percent, language_code),
                    _format_percent(current_metrics.maximum_positive_error_percent, language_code),
                    _format_percent(current_metrics.maximum_negative_error_percent, language_code),
                ],
                text["optimized"]: [
                    _format_ratio(optimized_metrics.q_mean, language_code),
                    _format_ratio(optimized_metrics.q_min, language_code),
                    _format_ratio(optimized_metrics.q_max, language_code),
                    _format_percent(optimized_metrics.rms_speed_error_percent, language_code),
                    _format_percent(optimized_metrics.maximum_positive_error_percent, language_code),
                    _format_percent(optimized_metrics.maximum_negative_error_percent, language_code),
                ],
            }
            st.dataframe(metric_table, use_container_width=True, hide_index=True)
            st.markdown(f'<div class="scope-note">{text["threshold_note"]}</div>', unsafe_allow_html=True)

        with st.expander(text["advanced_diagnostics"], expanded=False):
            diagnostic_columns = st.columns(4)
            diagnostic_columns[0].metric(
                text["convergence"], text["success"] if diagnostics.success else text["not_converged"]
            )
            diagnostic_columns[1].metric(
                text["function_evaluations"], _format_integer(diagnostics.function_evaluations, language_code)
            )
            diagnostic_columns[2].metric(text["iterations"], str(diagnostics.iterations))
            diagnostic_columns[3].metric(
                text["candidate_count"],
                _format_integer(core.phase_combination_count(analyzed_parameters), language_code)
                if analyzed_parameters.mode is not CardanMode.SINGLE else "—",
            )
            validation_table = {
                text["metric"]: [text["objective_value"], text["validation_value"], text["validation_delta"]],
                text["optimized"]: [
                    _format_percent(diagnostics.objective_unevenness_percent, language_code, 4),
                    _format_percent(diagnostics.validated_unevenness_percent, language_code, 4),
                    f"{_format_decimal(diagnostics.validation_delta_percent, 4, language_code)} pu",
                ],
            }
            st.dataframe(validation_table, use_container_width=True, hide_index=True)
            coarse_text = f"φ₁={_format_degree(result.coarse_phi1_deg, language_code)}"
            if result.coarse_phi2_deg is not None:
                coarse_text += f", φ₂={_format_degree(result.coarse_phi2_deg, language_code)}"
            st.caption(f"{text['coarse_solution']}: {coarse_text}")
            with st.expander(text["diagnostic_message"], expanded=False):
                st.code(diagnostics.message, language="text")

    with tabs[1]:
        velocity_figure, _, _ = core.plot_velocity_ratio(
            analyzed_parameters, labels=plot_labels, analysis=analysis,
        )
        style_figure_for_dark_theme(velocity_figure)
        st.pyplot(velocity_figure, use_container_width=True)
        plt.close(velocity_figure)

    with tabs[2]:
        st.markdown(f"### {text['current_geometry']}")
        left_space, geometry_column, right_space = st.columns([1.0, 3.2, 1.0])
        with geometry_column:
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
        st.caption(text["viewer_instructions"])
        viewer_columns = st.columns(3)
        selected_kind = viewer_columns[0].radio(
            text["viewer_configuration"],
            options=("current", "optimized"),
            horizontal=True,
            format_func=lambda value: text["viewer_current"] if value == "current" else text["viewer_optimized"],
            key="viewer_configuration_value",
        )
        camera_preset = viewer_columns[1].selectbox(
            text["viewer_camera"],
            options=("isometric", "top", "side", "front"),
            format_func=lambda value: {
                "isometric": text["camera_isometric"],
                "top": text["camera_top"],
                "side": text["camera_side"],
                "front": text["camera_front"],
            }[value],
            key="viewer_camera_value",
        )
        detail_value = viewer_columns[2].selectbox(
            text["viewer_detail"],
            options=(61, 121, 181),
            index=1,
            format_func=lambda value: {
                61: text["viewer_fast"],
                121: text["viewer_balanced"],
                181: text["viewer_smooth"],
            }[int(value)],
            key="viewer_detail_value",
        )
        speed_value = st.select_slider(
            text["viewer_speed"],
            options=(25, 45, 70, 110),
            value=45,
            format_func=lambda value: f"{value} ms/frame",
            key="viewer_speed_value",
        )
        if not viewer3d.plotly_available():
            st.warning(text["viewer_unavailable"])
        else:
            selected_trajectory = (
                analysis["optimized_trajectory"]
                if selected_kind == "optimized"
                else analysis["current_trajectory"]
            )
            selected_parameters = optimized_parameters if selected_kind == "optimized" else analyzed_parameters
            viewer_figure = viewer3d.build_kinematic_3d_figure(
                selected_parameters,
                selected_trajectory,
                analysis["current_trajectory"],
                analysis["optimized_trajectory"],
                labels=viewer_labels,
                selected_kind=selected_kind,
                frame_count=int(detail_value),
                frame_duration_ms=int(speed_value),
                camera_preset=camera_preset,
            )
            st.plotly_chart(
                viewer_figure,
                use_container_width=True,
                config={"displaylogo": False, "scrollZoom": True, "responsive": True},
                key=f"cardan_3d_{selected_kind}_{camera_preset}_{detail_value}_{speed_value}",
            )
            st.caption(text["viewer_caption"])
            st.download_button(
                text["export_scene"],
                data=_scene_json(selected_parameters, selected_trajectory, selected_kind),
                file_name=f"cardan_3d_scene_{selected_kind}.json",
                mime="application/json",
                use_container_width=True,
                key=f"download_3d_scene_{selected_kind}",
            )

    with tabs[4]:
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

    with tabs[5]:
        export_key = (analysis_signature, language_code)
        if st.session_state.excel_export_key != export_key:
            st.session_state.excel_export_bytes = None
            st.session_state.excel_export_key = None

        download_columns = st.columns(4)
        if xlsxwriter is None:
            st.warning(text["excel_unavailable"])
        else:
            if st.session_state.excel_export_bytes is None:
                if download_columns[0].button(
                    text["prepare_excel"], use_container_width=True, key="prepare_excel_button"
                ):
                    with st.spinner(text["spinner"]):
                        st.session_state.excel_export_bytes = _excel_workbook(
                            analyzed_parameters, analysis, language_code
                        )
                        st.session_state.excel_export_key = export_key
            if st.session_state.excel_export_bytes is not None:
                download_columns[0].download_button(
                    text["export_excel"], data=st.session_state.excel_export_bytes,
                    file_name="Cardan_Engineering_Analysis.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
                st.caption(text["excel_ready"])
        download_columns[1].download_button(
            text["export_curves"], data=_curve_csv(analysis, language_code),
            file_name="cardan_velocity_curves.csv", mime="text/csv", use_container_width=True,
        )
        download_columns[2].download_button(
            text["export_summary"], data=_summary_json(analyzed_parameters, analysis),
            file_name="cardan_analysis_summary.json", mime="application/json", use_container_width=True,
        )
        download_columns[3].download_button(
            text["export_trajectory"], data=_trajectory_json(analysis),
            file_name="cardan_kinematic_trajectory.json", mime="application/json", use_container_width=True,
        )
        st.markdown(f"### {text['data_preview']}")
        preview_count = 16
        preview = {
            text["preview_theta"]: [
                _format_decimal(float(x), 1, language_code) for x in analysis["theta_plot_deg"][:preview_count]
            ],
            text["preview_current"]: [
                _format_ratio(float(x), language_code) for x in analysis["q_current_plot"][:preview_count]
            ],
            text["preview_optimized"]: [
                _format_ratio(float(x), language_code) for x in analysis["q_optimized_plot"][:preview_count]
            ],
        }
        st.dataframe(preview, use_container_width=True, hide_index=True)

with st.expander(text["model_scope"]):
    st.markdown(text["model_text"])
st.divider()
st.caption(text["footer"])

"""Bilingual Streamlit interface for the Cardan Joint Optimization Tool."""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
from matplotlib.figure import Figure
import streamlit as st

import cardan_core as core


# ---------------------------------------------------------------------------
# Core-module compatibility check
# ---------------------------------------------------------------------------

_REQUIRED_CORE_API_VERSION = 2
_REQUIRED_CORE_OBJECTS = (
    "CardanMode",
    "CardanParameters",
    "PlotLabels",
    "UNEVENNESS_LIMIT_PERCENT",
    "phase_combination_count",
    "plot_geometry_2d",
    "plot_phase_figure",
    "plot_velocity_ratio",
)

_missing_core_objects = [
    name for name in _REQUIRED_CORE_OBJECTS if not hasattr(core, name)
]
_core_api_version = getattr(core, "CORE_API_VERSION", 0)

if _core_api_version < _REQUIRED_CORE_API_VERSION or _missing_core_objects:
    st.error(
        "The deployed streamlit_app.py and cardan_core.py files are from "
        "different releases. Replace both files with the matching files from "
        "the same release package, then reboot the Streamlit app."
    )
    st.code(
        "Required core API version: "
        f"{_REQUIRED_CORE_API_VERSION}\n"
        f"Detected core API version: {_core_api_version}\n"
        "Missing objects: "
        + (", ".join(_missing_core_objects) if _missing_core_objects else "none"),
        language="text",
    )
    st.stop()

CardanMode = core.CardanMode
CardanParameters = core.CardanParameters
PlotLabels = core.PlotLabels
UNEVENNESS_LIMIT_PERCENT = core.UNEVENNESS_LIMIT_PERCENT
phase_combination_count = core.phase_combination_count
plot_geometry_2d = core.plot_geometry_2d
plot_phase_figure = core.plot_phase_figure
plot_velocity_ratio = core.plot_velocity_ratio


# ---------------------------------------------------------------------------
# Streamlit page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Cardan Joint Tool | Kardan Mafsalı Aracı",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Interface translations
# ---------------------------------------------------------------------------

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "title": "Cardan Joint Kinematics & Phase Optimization Tool",
        "subtitle": (
            "Interactive kinematic analysis of single, double, and triple "
            "Cardan systems"
        ),
        "system_parameters": "System Parameters",
        "configuration": "Cardan configuration",
        "mode_single": "1 Cardan — Single",
        "mode_double": "2 Cardan — Double",
        "mode_triple": "3 Cardan — Triple",
        "misalignment_angles": "Misalignment Angles",
        "phase_angles": "Phase Angles",
        "optimization": "Optimization",
        "angular_reference": "Angular Reference",
        "phase_search_step": "Phase-search step (deg)",
        "run_analysis": "Run analysis",
        "direct_value": "direct numerical value",
        "beta_help": "Misalignment angle between two consecutive shaft axes.",
        "phase_help": (
            "Positive phase follows the model convention θ_next = θ_out − φ. "
            "A phase of 360° is kinematically equivalent to 0°."
        ),
        "optimization_help": (
            "A smaller step gives a finer discrete phase search but increases "
            "calculation time, especially for the triple Cardan mode."
        ),
        "theta_help": (
            "Initial angular reference of the input shaft. It shifts the plotted "
            "cycle but normally does not change full-cycle unevenness."
        ),
        "initial_instruction": (
            "Select the system parameters from the sidebar and press "
            "**Run analysis**."
        ),
        "spinner": (
            "Calculating the kinematic response and, where applicable, phase "
            "optimization..."
        ),
        "analysis_summary": "Analysis Summary",
        "current_unevenness": "Current unevenness",
        "optimized_unevenness": "Optimized unevenness",
        "current_status": "Current status",
        "phase_combinations": "Evaluated phase combinations",
        "status_ok": "OK",
        "status_warning": "Warning",
        "not_applicable": "N/A",
        "optimum_phase_angles": "Optimum Phase Angles",
        "single_no_optimization": (
            "Phase optimization is not applicable to a single Cardan joint."
        ),
        "optimum_phi1": "Optimum φ₁",
        "optimum_phi2": "Optimum φ₂",
        "figure_a_section": "Figure A — Angular Velocity Ratio",
        "figure_b_section": "Figure B — Two-Dimensional Shaft Geometry",
        "figure_c_section": "Figure C — Phase Visualization",
        "model_expander": "Model description and limitations",
        "footer": (
            "Developed by Furkan Kasap · Automotive Engineer · "
            "Cardan Joint Kinematics & Phase Optimization Tool"
        ),
    },
    "tr": {
        "title": "Kardan Mafsalı Kinematiği ve Faz Optimizasyonu Aracı",
        "subtitle": (
            "Tekli, çiftli ve üçlü Kardan sistemlerinin etkileşimli kinematik "
            "analizi"
        ),
        "system_parameters": "Sistem Parametreleri",
        "configuration": "Kardan konfigürasyonu",
        "mode_single": "1 Kardan — Tekli",
        "mode_double": "2 Kardan — Çiftli",
        "mode_triple": "3 Kardan — Üçlü",
        "misalignment_angles": "Eksen Kaçıklık Açıları",
        "phase_angles": "Faz Açıları",
        "optimization": "Optimizasyon",
        "angular_reference": "Açısal Referans",
        "phase_search_step": "Faz tarama adımı (derece)",
        "run_analysis": "Analizi çalıştır",
        "direct_value": "doğrudan sayısal değer",
        "beta_help": "Ardışık iki mil ekseni arasındaki kaçıklık açısıdır.",
        "phase_help": (
            "Pozitif faz, θ_next = θ_out − φ model işaret konvansiyonuna göre "
            "uygulanır. 360°, kinematik olarak 0° ile eşdeğerdir."
        ),
        "optimization_help": (
            "Daha küçük adım daha hassas bir ayrık faz taraması sağlar; ancak "
            "özellikle üçlü Kardan modunda hesaplama süresini artırır."
        ),
        "theta_help": (
            "Giriş milinin başlangıç açısal referansıdır. Çizilen çevrimin "
            "başlangıcını kaydırır; fakat normalde tam çevrim düzgünsüzlüğünü "
            "değiştirmez."
        ),
        "initial_instruction": (
            "Kenar çubuğundan sistem parametrelerini seçin ve "
            "**Analizi çalıştır** düğmesine basın."
        ),
        "spinner": (
            "Kinematik yanıt ve uygulanabildiği durumlarda faz optimizasyonu "
            "hesaplanıyor..."
        ),
        "analysis_summary": "Analiz Özeti",
        "current_unevenness": "Mevcut düzgünsüzlük",
        "optimized_unevenness": "Optimize edilmiş düzgünsüzlük",
        "current_status": "Mevcut durum",
        "phase_combinations": "Değerlendirilen faz kombinasyonları",
        "status_ok": "Uygun",
        "status_warning": "Uyarı",
        "not_applicable": "Uygulanamaz",
        "optimum_phase_angles": "Optimum Faz Açıları",
        "single_no_optimization": (
            "Tek bir Kardan mafsalı için faz optimizasyonu uygulanamaz."
        ),
        "optimum_phi1": "Optimum φ₁",
        "optimum_phi2": "Optimum φ₂",
        "figure_a_section": "Şekil A — Açısal Hız Oranı",
        "figure_b_section": "Şekil B — İki Boyutlu Mil Geometrisi",
        "figure_c_section": "Şekil C — Faz Görselleştirmesi",
        "model_expander": "Model açıklaması ve sınırlamalar",
        "footer": (
            "Geliştiren: Furkan Kasap · Otomotiv Mühendisi · "
            "Kardan Mafsalı Kinematiği ve Faz Optimizasyonu Aracı"
        ),
    },
}

MODEL_DESCRIPTION: dict[str, str] = {
    "en": r"""
        ### Kinematic model

        For each ideal Hooke's universal joint, the instantaneous angular
        velocity ratio is calculated as

        $$
        q_i
        =
        \frac{\omega_{i,\mathrm{out}}}{\omega_{i,\mathrm{in}}}
        =
        \frac{\cos\beta_i}
        {1-\sin^2\beta_i\cos^2\theta_{i,\mathrm{in}}}.
        $$

        The corresponding angular-position relation is implemented using the
        quadrant-preserving form

        $$
        \theta_{i,\mathrm{out}}
        =
        \operatorname{atan2}
        \left(
        \sin\theta_{i,\mathrm{in}},
        \cos\beta_i\cos\theta_{i,\mathrm{in}}
        \right).
        $$

        For consecutive joints, the relative yoke phase is applied to the next
        joint's input angle using the sign convention implemented in this
        application:

        $$
        \theta_{2,\mathrm{in}}
        =
        \theta_{1,\mathrm{out}}-\phi_1,
        $$

        $$
        \theta_{3,\mathrm{in}}
        =
        \theta_{2,\mathrm{out}}-\phi_2.
        $$

        The minus sign defines the application's positive phase direction. The
        same convention is used consistently in the calculations and phase
        visualization. The total ratio is obtained by multiplying the
        individual joint ratios:

        $$
        q_{\mathrm{total}}=\prod_{i=1}^{n}q_i,
        $$

        so that $q_{\mathrm{total}}=q_1q_2$ for a double Cardan system and
        $q_{\mathrm{total}}=q_1q_2q_3$ for a triple Cardan system.

        ### Optimization objective

        Every candidate phase configuration is evaluated over one complete
        input-shaft revolution. The objective function is

        $$
        U(\boldsymbol{\phi})
        =
        100\frac{q_{\max}-q_{\min}}{\bar q},
        $$

        and the reported optimum is

        $$
        \boldsymbol{\phi}^{*}
        =
        \underset{\boldsymbol{\phi}}{\operatorname{argmin}}
        \,U(\boldsymbol{\phi}).
        $$

        The current optimizer performs a discrete brute-force scan over
        $0^\circ \leq \phi < 360^\circ$ at the selected phase-search step. A
        phase of $360^\circ$ is not evaluated separately because it is
        kinematically equivalent to $0^\circ$. Therefore, an optimum located
        between two scan points is approximated by the nearest evaluated phase
        value.

        ### Limitations

        The current model is **kinematic only**. Mass, inertia, transmitted
        torque, bearing loads, elasticity, backlash, friction, stress, fatigue,
        torsional vibration, efficiency, and power losses are not included.

        The 5% status threshold is the current project criterion and should not
        be interpreted as a universal design standard.
    """,
    "tr": r"""
        ### Kinematik model

        Her ideal Hooke (Kardan) mafsalı için anlık açısal hız oranı aşağıdaki
        şekilde hesaplanır:

        $$
        q_i
        =
        \frac{\omega_{i,\mathrm{out}}}{\omega_{i,\mathrm{in}}}
        =
        \frac{\cos\beta_i}
        {1-\sin^2\beta_i\cos^2\theta_{i,\mathrm{in}}}.
        $$

        Buna karşılık gelen açısal konum ilişkisi, bölge bilgisini koruyan
        aşağıdaki biçimde uygulanır:

        $$
        \theta_{i,\mathrm{out}}
        =
        \operatorname{atan2}
        \left(
        \sin\theta_{i,\mathrm{in}},
        \cos\beta_i\cos\theta_{i,\mathrm{in}}
        \right).
        $$

        Ardışık mafsallarda göreli çatal fazı, bu uygulamada kullanılan işaret
        konvansiyonuna göre bir sonraki mafsalın giriş açısına uygulanır:

        $$
        \theta_{2,\mathrm{in}}
        =
        \theta_{1,\mathrm{out}}-\phi_1,
        $$

        $$
        \theta_{3,\mathrm{in}}
        =
        \theta_{2,\mathrm{out}}-\phi_2.
        $$

        Eksi işareti, uygulamanın pozitif faz yönünü tanımlar. Aynı işaret
        konvansiyonu hesaplamalarda ve faz görselleştirmesinde tutarlı biçimde
        kullanılır. Toplam açısal hız oranı, her mafsalın oranlarının
        çarpılmasıyla elde edilir:

        $$
        q_{\mathrm{total}}=\prod_{i=1}^{n}q_i.
        $$

        Buna göre çiftli Kardan sistemi için $q_{\mathrm{total}}=q_1q_2$,
        üçlü Kardan sistemi için ise
        $q_{\mathrm{total}}=q_1q_2q_3$ olur.

        ### Optimizasyon amaç fonksiyonu

        Her aday faz konfigürasyonu, giriş milinin bir tam devri boyunca
        değerlendirilir. Amaç fonksiyonu aşağıdaki düzgünsüzlük ölçütüdür:

        $$
        U(\boldsymbol{\phi})
        =
        100\frac{q_{\max}-q_{\min}}{\bar q}.
        $$

        Uygulamanın raporladığı optimum faz konfigürasyonu

        $$
        \boldsymbol{\phi}^{*}
        =
        \underset{\boldsymbol{\phi}}{\operatorname{argmin}}
        \,U(\boldsymbol{\phi})
        $$

        bağıntısıyla tanımlanır.

        Mevcut optimize edici, seçilen faz tarama adımıyla
        $0^\circ \leq \phi < 360^\circ$ aralığında ayrık bir tam tarama
        (brute-force scan) gerçekleştirir. $360^\circ$, kinematik olarak
        $0^\circ$ ile eşdeğer olduğundan ayrı bir aday olarak değerlendirilmez.
        Bu nedenle gerçek optimum iki tarama noktası arasında bulunuyorsa,
        sonuç en yakın değerlendirilen faz değeriyle yaklaşık olarak verilir.

        ### Sınırlamalar

        Mevcut model **yalnızca kinematiktir**. Kütle, atalet, aktarılan tork,
        yatak tepki kuvvetleri, elastikiyet, boşluk, sürtünme, gerilme, yorulma,
        burulma titreşimi, verim ve güç kayıpları modele dahil değildir.

        %5 durum sınırı bu projede kullanılan mevcut değerlendirme ölçütüdür;
        evrensel bir tasarım standardı olarak yorumlanmamalıdır.
    """,
}

PLOT_LABELS: dict[str, PlotLabels] = {
    "en": PlotLabels(),
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
    ),
}


# ---------------------------------------------------------------------------
# Visual settings
# ---------------------------------------------------------------------------

PAGE_BACKGROUND = "#0E1117"
PLOT_BACKGROUND = "#111827"
TEXT_COLOR = "#F3F4F6"
MUTED_TEXT_COLOR = "#AEB6C2"
GRID_COLOR = "#6B7280"
SPINE_COLOR = "#6B7280"
LEGEND_BACKGROUND = "#1F2937"


def _is_near_black(color: object) -> bool:
    """Return True when a Matplotlib color is black or almost black."""

    try:
        red, green, blue, _ = to_rgba(color)
    except (TypeError, ValueError):
        return False

    return red < 0.18 and green < 0.18 and blue < 0.18


def style_figure_for_dark_theme(figure: Figure) -> Figure:
    """Apply a readable dark theme to a Matplotlib figure."""

    figure.patch.set_facecolor(PLOT_BACKGROUND)

    if figure._suptitle is not None:
        figure._suptitle.set_color(TEXT_COLOR)

    for axis in figure.axes:
        axis.set_facecolor(PLOT_BACKGROUND)

        axis.title.set_color(TEXT_COLOR)
        axis.xaxis.label.set_color(TEXT_COLOR)
        axis.yaxis.label.set_color(TEXT_COLOR)

        axis.tick_params(
            axis="both",
            colors=MUTED_TEXT_COLOR,
            which="both",
        )

        for spine in axis.spines.values():
            spine.set_color(SPINE_COLOR)

        axis.grid(
            visible=True,
            color=GRID_COLOR,
            alpha=0.22,
            linewidth=0.8,
        )

        # Texts created inside the core plotting functions are black by default.
        for text_item in axis.texts:
            if _is_near_black(text_item.get_color()):
                text_item.set_color(TEXT_COLOR)

            text_box = text_item.get_bbox_patch()
            if text_box is not None:
                text_box.set_facecolor(LEGEND_BACKGROUND)
                text_box.set_edgecolor(SPINE_COLOR)
                text_box.set_alpha(0.94)

        # Keep engineering colors, but replace black shafts/lines with light gray.
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


# ---------------------------------------------------------------------------
# Language and URL helpers
# ---------------------------------------------------------------------------


def _normalise_query_value(value: object) -> str | None:
    """Convert a Streamlit query-parameter value to one plain string."""

    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        if not value:
            return None
        return str(value[0])
    return str(value)


def _read_language_from_url() -> str:
    """Read ?lang=en or ?lang=tr, falling back to English."""

    try:
        value = _normalise_query_value(st.query_params.get("lang"))
    except Exception:
        try:
            legacy_params = st.experimental_get_query_params()
            value = _normalise_query_value(legacy_params.get("lang"))
        except Exception:
            value = None

    return value if value in TRANSLATIONS else "en"


def _write_language_to_url(language_code: str) -> None:
    """Keep the selected language in the URL for shareable language links."""

    try:
        current = _normalise_query_value(st.query_params.get("lang"))
        if current != language_code:
            st.query_params["lang"] = language_code
    except Exception:
        try:
            st.experimental_set_query_params(lang=language_code)
        except Exception:
            # Language selection still works through session_state even when a
            # very old Streamlit version does not support query parameters.
            pass


if "ui_language" not in st.session_state:
    st.session_state.ui_language = "TR" if _read_language_from_url() == "tr" else "EN"


# ---------------------------------------------------------------------------
# Reusable synchronized parameter input
# ---------------------------------------------------------------------------


def _copy_widget_value(source_key: str, target_key: str) -> None:
    """Keep a slider and its numerical input synchronized."""

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
    """Render a slider and directly editable number field for one parameter."""

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
            f"{label} — {direct_value_text}",
            min_value=float(min_value),
            max_value=float(max_value),
            step=float(step),
            key=number_key,
            on_change=_copy_widget_value,
            args=(number_key, slider_key),
            format="%.0f",
            label_visibility="collapsed",
        )

    return float(st.session_state[number_key])


def format_integer(value: int, language_code: str) -> str:
    """Format large candidate counts using the selected language convention."""

    formatted = f"{value:,}"
    return formatted.replace(",", ".") if language_code == "tr" else formatted


st.markdown(
    """
    <style>
        .stApp {
            background-color: #0E1117;
        }

        .block-container {
            padding-top: 1.4rem;
            padding-bottom: 3rem;
        }

        [data-testid="stSidebar"] {
            min-width: 390px;
            max-width: 390px;
        }

        .app-subtitle {
            color: #AEB6C2;
            font-size: 1.05rem;
            margin-top: -0.8rem;
            margin-bottom: 1.2rem;
        }

        .language-caption {
            color: #AEB6C2;
            font-size: 0.82rem;
            text-align: right;
            margin-bottom: -0.45rem;
        }

        [data-testid="stMetric"] {
            border: 1px solid rgba(174, 182, 194, 0.22);
            border-radius: 0.8rem;
            padding: 1rem 1.1rem;
            background: rgba(31, 41, 55, 0.45);
        }

        [data-testid="stMetricValue"] {
            font-size: clamp(1.75rem, 2.5vw, 2.7rem);
        }

        div[role="radiogroup"] {
            justify-content: flex-end;
            gap: 0.35rem;
        }

        .scope-note {
            border-left: 4px solid #9A9A9A;
            padding: 0.65rem 0.9rem;
            background: rgba(128, 128, 128, 0.08);
            border-radius: 0.3rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Header and language selector
# ---------------------------------------------------------------------------

header_column, language_column = st.columns([5.2, 1.15])

with language_column:
    st.markdown(
        '<div class="language-caption">Language / Dil</div>',
        unsafe_allow_html=True,
    )
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
    st.markdown(
        f'<div class="app-subtitle">{text["subtitle"]}</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Sidebar inputs
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header(text["system_parameters"])

    mode_value = st.selectbox(
        text["configuration"],
        options=(1, 2, 3),
        index=2,
        key="mode_value",
        format_func=lambda value: {
            1: text["mode_single"],
            2: text["mode_double"],
            3: text["mode_triple"],
        }[int(value)],
    )
    mode = CardanMode(int(mode_value))

    st.subheader(text["misalignment_angles"])

    beta1_deg = sidebar_angle_input(
        "β₁ (°)",
        key="beta1_deg",
        min_value=0.0,
        max_value=60.0,
        default_value=25.0,
        direct_value_text=text["direct_value"],
        help_text=text["beta_help"],
    )

    beta2_deg = 25.0
    beta3_deg = 25.0

    if mode >= CardanMode.DOUBLE:
        beta2_deg = sidebar_angle_input(
            "β₂ (°)",
            key="beta2_deg",
            min_value=0.0,
            max_value=60.0,
            default_value=25.0,
            direct_value_text=text["direct_value"],
            help_text=text["beta_help"],
        )

    if mode is CardanMode.TRIPLE:
        beta3_deg = sidebar_angle_input(
            "β₃ (°)",
            key="beta3_deg",
            min_value=0.0,
            max_value=60.0,
            default_value=25.0,
            direct_value_text=text["direct_value"],
            help_text=text["beta_help"],
        )

    phi1_deg = 0.0
    phi2_deg = 0.0
    optimization_step_deg = 5.0

    if mode >= CardanMode.DOUBLE:
        st.subheader(text["phase_angles"])

        phi1_deg = sidebar_angle_input(
            "φ₁ (°)",
            key="phi1_deg",
            min_value=0.0,
            max_value=360.0,
            default_value=0.0,
            direct_value_text=text["direct_value"],
            help_text=text["phase_help"],
        )

        if mode is CardanMode.TRIPLE:
            phi2_deg = sidebar_angle_input(
                "φ₂ (°)",
                key="phi2_deg",
                min_value=0.0,
                max_value=360.0,
                default_value=0.0,
                direct_value_text=text["direct_value"],
                help_text=text["phase_help"],
            )

        st.subheader(text["optimization"])

        optimization_step_deg = sidebar_angle_input(
            text["phase_search_step"],
            key="optimization_step_deg",
            min_value=1.0,
            max_value=10.0,
            default_value=5.0,
            direct_value_text=text["direct_value"],
            help_text=text["optimization_help"],
        )

    st.subheader(text["angular_reference"])

    theta0_deg = sidebar_angle_input(
        "θ₀ (°)",
        key="theta0_deg",
        min_value=0.0,
        max_value=180.0,
        default_value=0.0,
        direct_value_text=text["direct_value"],
        help_text=text["theta_help"],
    )

    run_button = st.button(
        text["run_analysis"],
        type="primary",
        use_container_width=True,
    )


# ---------------------------------------------------------------------------
# Parameter object and analysis state
# ---------------------------------------------------------------------------

parameters = CardanParameters(
    mode=mode,
    beta1_deg=float(beta1_deg),
    beta2_deg=float(beta2_deg),
    beta3_deg=float(beta3_deg),
    phi1_deg=float(phi1_deg),
    phi2_deg=float(phi2_deg),
    theta0_deg=float(theta0_deg),
    optimization_step_deg=float(optimization_step_deg),
)

if "analysis_started" not in st.session_state:
    st.session_state.analysis_started = False

if run_button:
    st.session_state.analysis_started = True


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

if not st.session_state.analysis_started:
    st.info(text["initial_instruction"])
else:
    with st.spinner(text["spinner"]):
        velocity_figure, result, current_unevenness = plot_velocity_ratio(
            parameters,
            labels=plot_labels,
        )
        geometry_figure = plot_geometry_2d(parameters, labels=plot_labels)
        phase_figure = plot_phase_figure(parameters, labels=plot_labels)

        style_figure_for_dark_theme(velocity_figure)
        style_figure_for_dark_theme(geometry_figure)

        if phase_figure is not None:
            style_figure_for_dark_theme(phase_figure)

    # -----------------------------------------------------------------------
    # Analysis summary
    # -----------------------------------------------------------------------

    st.subheader(text["analysis_summary"])

    summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)

    summary_col1.metric(
        text["current_unevenness"],
        f"{current_unevenness:.2f}%",
    )

    summary_col2.metric(
        text["optimized_unevenness"],
        f"{result.unevenness_percent:.2f}%",
        delta=f"{result.unevenness_percent - current_unevenness:.2f}%",
        delta_color="inverse",
    )

    status = (
        text["status_ok"]
        if current_unevenness <= UNEVENNESS_LIMIT_PERCENT
        else text["status_warning"]
    )

    summary_col3.metric(
        text["current_status"],
        status,
    )

    evaluated_combinations = phase_combination_count(parameters)
    summary_col4.metric(
        text["phase_combinations"],
        (
            text["not_applicable"]
            if evaluated_combinations == 0
            else format_integer(evaluated_combinations, language_code)
        ),
    )

    st.markdown(f"#### {text['optimum_phase_angles']}")

    if mode is CardanMode.SINGLE:
        st.info(text["single_no_optimization"])

    elif mode is CardanMode.DOUBLE:
        phase_col1, _ = st.columns(2)

        phase_col1.metric(
            text["optimum_phi1"],
            f"{result.phi1_deg:.0f}°",
        )

    else:
        phase_col1, phase_col2 = st.columns(2)

        phase_col1.metric(
            text["optimum_phi1"],
            f"{result.phi1_deg:.0f}°",
        )

        phase_col2.metric(
            text["optimum_phi2"],
            f"{result.phi2_deg:.0f}°",
        )

    st.divider()

    # -----------------------------------------------------------------------
    # Figures
    # -----------------------------------------------------------------------

    st.subheader(text["figure_a_section"])
    st.pyplot(
        velocity_figure,
        use_container_width=True,
    )
    plt.close(velocity_figure)

    st.subheader(text["figure_b_section"])
    st.pyplot(
        geometry_figure,
        use_container_width=True,
    )
    plt.close(geometry_figure)

    if phase_figure is not None:
        st.subheader(text["figure_c_section"])
        st.pyplot(
            phase_figure,
            use_container_width=True,
        )
        plt.close(phase_figure)

    # -----------------------------------------------------------------------
    # Technical description
    # -----------------------------------------------------------------------

    with st.expander(text["model_expander"]):
        st.markdown(MODEL_DESCRIPTION[language_code])


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.divider()
st.caption(text["footer"])

# Faz Konvansiyonu Geçişi — v1.2.4

v1.2.4 bütün kullanıcı, dosya ve API fazlarını fiziksel çatal fazı olarak tanımlar:

```text
0°  = ortak mil üzerindeki çatallar hizalı
90° = ortak mil üzerindeki çatallar dik
```

İç analitik Hooke referansı:

```text
φ_model = (90° - φ_physical) mod 180°
```

Eski iç model fazı fiziksel faza çevrilirken:

```text
φ_physical = (90° - φ_model) mod 180°
```

| Eski iç model değeri | v1.2.4 fiziksel değer |
|---:|---:|
| 0° | 90° |
| 30° | 60° |
| 60° | 30° |
| 90° | 0° |

v1.2.4 JSON sözleşmesi şu alanları taşır:

```json
{
  "schema_version": 2,
  "angles_unit": "degree",
  "phase_convention": "physical_yoke_clocking"
}
```

`phase_convention` içermeyen eski veri otomatik tahmin edilmez. Python API'de eski referans açıkça belirtilmelidir:

```python
core.parameters_from_payload(
    payload,
    legacy_phase_convention=core.PhaseConvention.INTERNAL_HOOKE_REFERENCE,
)
```

Aynı paketten gelen `streamlit_app.py`, `cardan_core.py` ve `cardan_3d_viewer.py` birlikte dağıtılmalıdır.

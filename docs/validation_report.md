# Doğrulama Raporu — v1.3.0

- Başlangıç: `main`, commit `039da69` (v1.2.4).
- Çalışma dalı: `validation/literature-based-verification`.
- Ortam: Windows 10, Python 3.12, numpy 2.5.4, scipy 1.18.1, matplotlib 3.11.2, streamlit 1.67.0, plotly 6.9.0, XlsxWriter 3.2.9, pytest.

## 1. Doğrulama katmanları

| Katman | Soru | Durum |
|---|---|---|
| Kod doğrulaması | Denklemler doğru uygulanmış mı? | Yapıldı (analitik özel durumlar, bağımsız 3B model, kapalı-form) |
| Sayısal doğrulama | Sonuç örneklemeye ve toleranslara göre yakınsıyor mu? | Yapıldı (örnekleme hatası, kapalı-form karşılaştırması, tohum duyarlılığı) |
| Fiziksel geçerleme | Model deneysel davranışı temsil ediyor mu? | **Yapılmadı.** Deneysel veri yok. |

Literatürdeki tek erişilebilen deney (Karaoğlan ve Kuralay, 2024, Şekil 4) görsel bir karşılaştırmadır ve sayısal veri içermez. Grafikten veri sayısallaştırılmadı.

## 2. Bağımsız referanslar

Üretim kodunun formülleri testlerde yeniden kullanılmaz. Üç bağımsız referans vardır (`tests/reference_model.py`):

1. **3B vektör modeli.** Tek fizik kuralı: istavrozun iki pim ekseni dik kalır. Hooke formülü kullanılmaz; mil eksenleri herhangi bir uzaysal yerleşimde olabilir. Hız oranı periyodik merkezî farkla elde edilir.
2. **Bağımsız tekil değer hesabı.** Bileşke matris `numpy.linalg.svd` ile ayrıca kurulur.
3. **Analitik alt sınır.** Koşul sayısının alt-çarpımsallığından gelir; hiçbir arama içermez.

Aynı formülü daha yoğun örneklemek yalnızca ayrıklaştırma hatasını ölçer; formül yanlışsa yanlışı doğrular. Bu yüzden yoğun doğrulama ızgarası "bağımsız" sayılmamıştır.

## 3. Test kapsamı ve toleranslar

Komut: `python -m pytest tests` → **267 test, tamamı geçti** (yaklaşık 107 s).

| Konu | Test dosyası | Tolerans | Gerekçe |
|---|---|---|---|
| β = 0 → q ≡ 1 | `test_kinematics.py` | 1e-12 | Kayan nokta yuvarlaması |
| Tek mafsal uçları `cos β`, `1/cos β`; `U = sin β tan β` | `test_kinematics.py` | 1e-12, 1e-9 pu | Izgara uç noktaları içerir |
| Eşit açılı çift mafsal, hizalı çatallar → sabit hız | `test_kinematics.py` | 1e-12 | Analitik özdeşlik |
| Fazın 180° periyodikliği | `test_kinematics.py` | 1e-12 | Analitik özdeşlik |
| Tam devirde çıkış ilerlemesi 360°, ortalama q = 1 | `test_kinematics.py` | 1e-9°, 1e-12 | Yuvarlama |
| Sürekli çıkış açısının türevi = q | `test_kinematics.py` | 1e-8 | 0,005° adımda merkezî fark hatası ~1e-9 |
| θ₀ değişiminde metrik tutarlılığı | `test_kinematics.py` | `2U(π/N)²` | Tepe noktasının parabolik örnekleme hatası |
| Tekli, çiftli, üçlü: çekirdek ↔ 3B model | `test_independent_reference.py` | 5e-4 pu | 7200 örnekte sayısal türev hatası < 1e-4 pu |
| Z/W yerleşimi, uzaysal düzlem kaçıklığı | `test_independent_reference.py` | 5e-4 pu | Aynı |
| Literatür örnekleri (üç tasarım) | `test_literature_cases.py` | ±0,006 | Kaynak iki ondalık veriyor; bir değer iki farklı yazılmış |
| Kapalı-form ↔ SVD ↔ 72 000 örnek | `test_exact_solution.py` | 1e-11 bağıl, 2e-6 bağıl | Yuvarlama; yoğun örnekleme hatası |
| Optimum = kesin alt sınır | `test_exact_solution.py` | 1e-7 pu | Çözücü toleransı |
| Optimum mevcut durumdan kötü olamaz | `test_optimization.py` | 1e-9 pu | Aynı ızgarada karşılaştırma |
| 0°/180° sınırında çift mafsal optimumu | `test_optimization.py` | 1e-9° (kapalı-form), 0,5° (örneklenmiş) | Örneklenmiş amacın bilinen kayması |
| Sabit tohumda tekrarlanabilirlik | `test_optimization.py` | Tam eşitlik | Deterministik |
| v1.2.4 regresyon değeri | `test_optimization.py` | 1e-9 bağıl | Eski yöntemin sonucu korunmalı |
| Sıfıra yakın taban ve yüzde azalma | `test_optimization.py` | Tanım | `None` döner |
| Geçersiz girdiler | `test_inputs_scene_exports.py` | — | `ValueError` |
| 3B sahne ↔ faz ve β | `test_inputs_scene_exports.py` | 1e-9°, 1e-12 | Yuvarlama |
| Dışa aktarım sözleşmesi | `test_inputs_scene_exports.py`, `test_app.py` | — | Alan varlığı |
| Gerçek arayüz akışları | `test_app.py` | — | `streamlit.testing.v1.AppTest`; sahte Streamlit yok |

## 4. Model iddialarının durumu

### Doğrulanan

- Tek mafsal açı ve hız bağıntıları; ardışık mafsallara açı aktarımı; toplam oranın çarpım olması.
- Fiziksel faz dönüşümü `ψ = (90° − φ) mod 180°`: bağımsız 3B modelde hizalı çatallar sabit hız verir.
- Fazın 180° periyodikliği hesapta, optimizasyonda ve parametre nesnesinde korunuyor.
- 3B sahnedeki çatal açısı girilen fazla aynı; istavroz dikliği korunuyor.
- Fischer ve Paul (1991): eşit açılar ve sıfır bağıl fazda sabit hız; eşit olmayan açılarda en küçük dalgalanma sıfır bağıl fazda ve sıfırdan büyük.
- Karaoğlan ve Kuralay (2024): üç tasarımın hız oranı aralıkları ±0,006 içinde yeniden üretildi; tasarım sıralaması aynı.
- v1.2.4 BENCHMARK_REPORT ve TEST_REPORT'taki sayısal değerler yeniden üretildi.

### Yanlışlanan

| İddia (v1.2.4) | Bulgu |
|---|---|
| README: `tests/` klasörü var; TEST_REPORT: 31/31 test geçti | Repoda test yoktu. |
| "Bağımsız yoğun doğrulama" | Doğrulama ızgarası amaç ızgarasını içeriyor; yalnızca örnekleme hatasını ölçüyor. |
| Optimizasyon sonucu bir iyileştirmedir | Mevcut fazlar aday değildi; sonuç mevcut durumdan kötü olabiliyordu. Arayüzde "−130737,99%" üretildi. |
| Hibrit yöntem en yüksek doğruluğu verir | 150 senaryoda hibrit ile DE'nin optimuma uzaklığı aynı; Powell ölçülebilir kazanç sağlamadı. |
| Çift mafsalda sürekli yöntemler optimum fazı bulur | Gerçek optimum 0° iken 179,83° ve 0,25° döndü (örnekleme kaynaklı). |

### Belirsiz kalan

- Düzlemsel olmayan **üçlü** sistemde düzlem kaçıklığının faza eklenmesiyle eşdeğerlik.
- Alt sınıra her mafsal açısı kümesi için ulaşılabildiğinin genel kanıtı (sayısal olarak 190 durumda ulaşıldı).
- Modelin deneysel davranışla nicel uyumu.
- `φ` dönüş yönünün fiziksel tanımı.

## 5. Uygulanan değişiklikler

| Değişiklik | Dayanak | Test |
|---|---|---|
| `exact_speed_ratio_bounds`, `exact_unevenness_grid` | Kapalı-form türetim; 3 bağımsız doğrulama | `test_exact_solution.py` |
| `exact_phase_optimum`, `minimum_unevenness_lower_bound_percent`, `OptimizationMethod.EXACT` | Alt sınır kanıtı; Fischer ve Paul (çift mafsal) | `test_exact_solution.py`, `test_optimization.py` |
| Mevcut konfigürasyon her yöntemde aday | Negatif azalma hatası | `test_optimum_is_never_worse_than_current_configuration`, `test_app.py` |
| `reduction_percent`: sıfıra yakın tabanda tanımsız | Sayısal anlamsızlık | `test_reduction_percent_definition` |
| Sonluluk denetimi (`theta0`, `phi`, adım) | Yanıltıcı hata mesajları | `test_invalid_inputs_are_rejected_at_construction` |
| 2B şema `θ₀` ile döndürülmüyor | `θ₀` dönme referansıdır | `test_geometry_plot_does_not_tilt_layout_with_theta0` |
| Arayüz: standart analiz kapalı-form; teşhis tablosu, "zaten optimum" bildirimi | Yukarıdaki bulgular | `test_app.py` |
| Excel: faz konvansiyonu ve konfigürasyon; JSON: `closed_form` bloğu | Dosyanın tek başına yorumlanabilmesi | `test_excel_export_carries_phase_convention_and_exact_values` |

Korunanlar: faz konvansiyonu, parametre şeması (sürüm 2), mevcut JSON/Excel/CSV alanları ve mevcut dört yöntemin sayısal sonuçları. Yeni alanlar eklemedir. Core API sürümü 8'den 9'a çıktı; uygulama artık çekirdek API 9 ister.

## 6. Önce / sonra

### 6.1 Testler

| | v1.2.4 (`039da69`) | v1.3.0 |
|---|---|---|
| Repodaki test sayısı | 0 | 267 |
| Bu test takımının sonucu | 72 geçti, 190 başarısız | 267 geçti |

Başlangıçtaki 190 başarısızlığın çoğu henüz var olmayan yeni işlevlere aittir. Mevcut davranıştaki gerçek kusurları gösterenler: optimumun mevcut durumdan kötü olması (2), sonlu olmayan girdilerin kabul edilmesi (4), `θ₀` ile eğilen şema (1), arayüzde negatif azalma (1), Excel'de faz konvansiyonu eksikliği (1). Kinematik, bağımsız referans ve literatür testlerinin tamamı başlangıç kodunda da geçiyordu. Ayrıntı: `docs/results/baseline_tests_v1.2.4.txt`.

### 6.2 Optimizasyon doğruluğu

150 rastgele üçlü sistem, β ∈ [0°, 60°], sabit tohum. "Uzaklık" = döndürülen fazların kapalı-form düzgünsüzlüğü eksi küresel optimum (yüzde puanı).

| Yöntem | Medyan | p95 | En kötü | Medyan süre | Başarı bayrağı |
|---|---|---|---|---|---|
| Grid | 0 | 3,33 | 7,04 | 10,6 ms | %100 |
| Grid + yerel | 3e-14 | 0,196 | 0,866 | 19,2 ms | %100 |
| Differential Evolution | 3,5e-5 | 7,6e-4 | 1,3e-3 | 137 ms | %81 |
| Hibrit (DE + Powell) | 3,5e-5 | 7,6e-4 | 1,3e-3 | 141 ms | %100 |
| **Kapalı-form (yeni)** | 0 | 0 | 3,4e-14 | 10,1 ms | %100 (150/150 kanıtlı) |

- Eski dört yöntemin doğruluk değerleri v1.2.4 ile aynıdır; davranışları değişmedi.
- Süreler aynı makinede ölçüldü: v1.2.4'te 9,2 / 17,7 / 137 / 153 ms; v1.3.0'da 10,5 / 18,9 / 138 / 152 ms. Kapalı-form referansın her analize eklediği maliyet yaklaşık 1 ms'dir.
- Kapalı-form yöntemin süresinin büyük kısmı, faz haritası için korunan kaba ızgaradır.
- Tohum duyarlılığı (20 senaryo × 10 tohum): DE ve hibritte en büyük uzaklık 1,0e-3 pu, en büyük yayılım 1,9e-4 pu, süre 85–273 ms.

Tam çıktı: `docs/results/benchmark_v1.3.0.txt`. Yeniden üretim: `python benchmarks/benchmark_methods.py`.

### 6.3 Standart analizde kullanıcıya görünen fark

| Durum | v1.2.4 | v1.3.0 |
|---|---|---|
| Varsayılan 25°/25°/25°, optimum | 150,00° / 150,00°, %0,05 | 150,04° / 150,04°, < %0,01 |
| Ultra optimumu uyguladıktan sonra standart analiz | Azalma −130737,99%, "--0,05 pu" | Negatif değer yok |
| Çift mafsal, eşit açılar, φ = 0 | Azalma %0,00 | Azalma "—", "zaten optimum" bildirimi |
| Çift mafsal 20°/35° | 179,83° (hibrit) | 0,00° |

### 6.4 Örnekleme hatası (360 noktalı amaç, kapalı-forma göre)

| β aralığı | En kötü | Medyan |
|---|---|---|
| 18°–30° | −%0,004 | −%0,0008 |
| 27°–45° | −%0,010 | −%0,0014 |
| 36°–60° | −%0,037 | −%0,0022 |
| 45°–75° | −%0,31 | −%0,0052 |
| 51°–85° | −%10,3 | −%0,021 |

Arayüz sınırı (60°) içinde örnekleme yeterlidir; üzerinde yalnızca kapalı-form değer güvenilirdir.

## 7. Çalıştırılan komutlar

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests
python benchmarks/benchmark_methods.py
python benchmark_optimizers.py
```

## 8. Kalan sınırlamalar

- Fiziksel geçerleme yok; model deneysel veriyle karşılaştırılmadı.
- Literatürün büyük kısmı yalnızca özet düzeyinde incelenebildi (bkz. `docs/literature_review.md`).
- Üçlü sistemde uzaysal geometri model dışı.
- Montaj toleransı duyarlılığı raporlanmıyor. Ölçülen bir örnekte (β = 43,02°/25,26°/47,51°) iki fazda 1° hata %5,0 düzgünsüzlük üretiyor; 0,01° çözünürlüklü optimum pratikte tutturulamaz.
- Tarayıcıdaki görsel çıktı (Plotly animasyonu, grafik yerleşimi) ve canlı Streamlit Cloud dağıtımı denetlenmedi.
- CSV dışa aktarımı değiştirilmedi; hâlâ parametre ve sürüm bilgisi taşımıyor (biçimi bozmamak için).
- `use_container_width` parametresi Streamlit tarafından kullanımdan kaldırılmış olarak işaretleniyor; 17 yerde duruyor.
- CI iş akışı eklendi ancak GitHub üzerinde henüz çalıştırılmadı.

## 9. Güncelleme — v1.4.0

### 9.1 Tam metinlerden eklenen literatür testleri

Fischer ve Paul (1991) ile Seherr-Thoss ve diğ. (2006) tam metinleri okundu. Kaynaklar çıkışın girişe göre ileri–geri sapma genliğini ("cardan error") derece olarak verdiği için `ExactSpeedBounds.angle_error_amplitude_deg` eklendi: `atan((κ − 1) / (2√κ))`. Bu kapalı-form değer, çekirdeğin sürekli çıkış açısından örneklenen genlikle 1e-6° içinde aynıdır.

| Kaynak | Girdi | Kaynak değeri | Model | Tolerans |
|---|---|---|---|---|
| Seherr-Thoss s. 6 | Tek mafsal, β = 45° | yaklaşık ±10° | 9,88° | ±0,6° |
| Seherr-Thoss Şekil 1.7a | β = 30°; 15° | ≈ 4°; ≈ 1° | 4,12°; 0,99° | ±0,5° |
| Seherr-Thoss Böl. 1.2.2 | Hizalı çatallar, β₁ ≠ β₂ | `cos β₁ / cos β₂` | Aynı | 1e-12 bağıl |
| Seherr-Thoss Böl. 1.2.2 | 90° fazlı çatallar | `1 / (cos β₁ cos β₂)` | Aynı | 1e-12 bağıl |
| Fischer–Paul s. 268, 270 | β = 45°/45°, RPA 0° → 90° | 0° → yaklaşık 20° | 0° → 19,47° | ±0,6° |
| Fischer–Paul Şekil 11–12 | β = 30°/30°, RPA 0°; 20,1°; 50,1°; 80,1° | 0°; ≈ 2,9°; ≈ 6,4°; ≈ 8,0° | 0°; 2,84°; 6,32°; 8,09° | ±0,5° |

Şekil değerleri gözle okunmuştur ve düşük hassasiyetli referanstır. Fischer ve Paul'ün eğrileri deneyle doğrulanmış olduğu için bu karşılaştırma, modelin yayımlanmış bir deneyle **dolaylı** uyumunu gösterir; ham ölçüm verisi kullanılmadığından fiziksel geçerleme sayılmaz.

### 9.2 Aşama 1 — tolerans ve ayrık faz

- `tolerance_sensitivity`: faz ve mafsal açısı tolerans kutusunda kapalı-form en kötü düzgünsüzlük (ızgara aralığı: fazda tolerans/10, açıda tolerans/2).
- `discrete_phase_optimum`: spline diş sayısına göre ulaşılabilen fazların tamamı taranır.
- Örnek (β = 43,02°/25,26°/47,51°, optimum fazlarda, ±1°): yalnız faz hatası %5,02; yalnız mafsal açısı hatası %8,44; ikisi birlikte %10,36. 16 dişli iki spline ile ulaşılabilen en iyi düzgünsüzlük %4,27'dir (sürekli optimum %0).
- Sınır: en kötü durum ızgara üzerinde aranır; rastgele iç noktalar raporlanan değeri %1'den fazla aşmamıştır (8 senaryo × 300 nokta).

### 9.3 Test sayısı

`python -m pytest tests` → 313 test, tamamı geçti (v1.3.0'da 267).

# Cardan Joint Engineering Tool v1.2.4

Tekli, çiftli ve üçlü Kardan mafsalı sistemleri için kinematik hız oranı analizi, fiziksel çatal fazı optimizasyonu, yoğun sayısal doğrulama, etkileşimli 3B şema ve mühendislik çıktıları sunan Streamlit uygulamasıdır.

> **Faz tanımı:** Uygulamanın her yerinde `φ = 0°` ortak ara mil üzerindeki çatalların hizalı, `φ = 90°` ise çatalların birbirine dik olduğu fiziksel yoke clocking tanımıdır.

## v1.2.4 ile gelen temel güvenlik iyileştirmeleri

- Bütün görünür sürüm ve çıktı metadata değerleri `1.2.4` olarak birleştirildi.
- `CardanParameters` yalnız fiziksel çatal fazı kabul eder.
- JSON/API verilerinde `schema_version`, `angles_unit` ve `phase_convention` zorunlu sözleşme hâline getirildi.
- Faz konvansiyonu bulunmayan eski veriler otomatik tahmin edilmez.
- İç Hooke referansı açıkça belirtilirse fiziksel faza güvenli biçimde dönüştürülebilir.
- Açı slider ve sayı kutusu tek kanonik değere bağlandı; `0,5°` veya `0,01°` adımına otomatik oturtulur.
- `β > 30°` için bilgilendirme, `β > 45°` için güçlü mühendislik uyarısı gösterilir.
- 3B sekmesinde düzlemsel model varsayımı kalıcı bilgi kutusuyla açıklanır.
- 3B JSON çıktısında `scene_model="canonical_planar"` ve `spatial_reconstruction=false` bulunur.
- `β₁=β₂=β₃=9,5°` üçlü sistem için `φ₁=φ₂=30°` optimumu regresyon testiyle korunur.

## Hızlı kurulum

### Windows

1. ZIP dosyasını klasöre çıkarın.
2. `install_windows.bat` dosyasını çalıştırın.
3. Kurulum tamamlanınca `run_windows.bat` dosyasını çalıştırın.

### Terminal ile

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Linux/macOS:

```bash
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## GitHub ve Streamlit Cloud dağıtımı

Repo ana dizininde şu dosyalar birlikte bulunmalıdır:

```text
streamlit_app.py
cardan_core.py
cardan_3d_viewer.py
requirements.txt
README.md
```

Streamlit Cloud giriş dosyası:

```text
streamlit_app.py
```

Dosyaları farklı sürümlerden karıştırmayın. v1.2.4 arayüzü `CORE_API_VERSION = 8` bekler.

## Kullanım

### 1. Sistem tipini seçin

- Tekli Kardan
- Çiftli Kardan
- Üçlü Kardan

### 2. Kaçıklık açılarını girin

`β₁`, `β₂`, `β₃` ardışık mil eksenleri arasındaki açılardır. Ana arayüz `0°–60°` aralığını kullanır.

Uyarı eşikleri tasarım standardı değildir; kullanıcıyı yüksek açılı kinematik davranışa karşı bilgilendirir:

- `β > 30°`: doğrusal olmayan hız davranışı belirginleşebilir.
- `β > 45°`: üretici limitleri, mafsal ömrü, yük ve paketleme ayrıca kontrol edilmelidir.

### 3. Fiziksel faz açılarını girin

- `φ = 0°`: ortak mil üzerindeki çatallar hizalıdır.
- `φ = 90°`: çatallar diktir.
- `φ` ile `φ + 180°` kinematik olarak eşdeğerdir.

Benzersiz aralık:

```text
0° ≤ φ < 180°
```

Arayüzde `180°` girilirse çekirdek bunu eşdeğer `0°` durumuna kanonikleştirir.

### 4. Analiz kalitesini seçin

#### Standart

- 5° kaba faz haritası
- Yerel hassaslaştırma
- Deterministik davranış
- Parametre değiştiğinde otomatik analiz

#### Ultra hassas

- Differential Evolution
- Powell yerel iyileştirmesi
- Yoğun bağımsız doğrulama
- Manuel çalıştırma

Dört algoritmanın tamamı yalnız uzman ayarlarında gösterilir.

## Fiziksel faz ile iç model fazı

Kullanıcı ve dış dosyalar fiziksel faz kullanır. Hooke denklemlerindeki iç referans yalnız çekirdek içinde oluşturulur:

```text
φ_model = (90° - φ_physical) mod 180°
```

Bu dönüşüm kullanıcıya gösterilmez ve dışa aktarımda iç faz saklanmaz.

### Eski model-fazı verisini dönüştürme

Eski veri açıkça `internal_hooke_reference` olarak etiketlenmişse:

```text
φ_physical = (90° - φ_model) mod 180°
```

Örnek:

| İç model fazı | Fiziksel çatal fazı |
|---:|---:|
| 90° | 0° |
| 60° | 30° |
| 30° | 60° |
| 0° | 90° |

Konvansiyon bilgisi bulunmayan dosya otomatik yorumlanmaz.

## JSON/API parametre sözleşmesi

Önerilen parametre yapısı:

```json
{
  "schema_version": 2,
  "tool_version": "1.2.4",
  "angles_unit": "degree",
  "phase_convention": "physical_yoke_clocking",
  "parameters": {
    "mode": 3,
    "beta1_deg": 9.5,
    "beta2_deg": 9.5,
    "beta3_deg": 9.5,
    "phi1_deg": 30.0,
    "phi2_deg": 30.0,
    "theta0_deg": 0.0,
    "optimization_step_deg": 5.0
  }
}
```

Python kullanımı:

```python
import cardan_core as core

parameters = core.CardanParameters(
    mode=3,
    beta1_deg=9.5,
    beta2_deg=9.5,
    beta3_deg=9.5,
    phi1_deg=30.0,
    phi2_deg=30.0,
)

payload = core.parameters_to_payload(parameters)
restored = core.parameters_from_payload(payload)
```

Etiketsiz eski veri için konvansiyon açıkça belirtilmelidir:

```python
restored = core.parameters_from_payload(
    legacy_payload,
    legacy_phase_convention=core.PhaseConvention.INTERNAL_HOOKE_REFERENCE,
)
```

## 9,5°–9,5°–9,5° üçlü sistem doğrulaması

Koşullar:

```text
β₁ = β₂ = β₃ = 9,5°
```

Standart optimizasyon sonucu:

```text
φ₁ = 30°
φ₂ = 30°
```

Yoğun doğrulamada düzgünsüzlük yaklaşık `%0,000132` seviyesindedir. Ultra çözüm yaklaşık `29,9992°–29,9992°` verir ve sonuç sayısal hassasiyet sınırında sıfıra yaklaşır.

`60°–60°` fiziksel faz bu sistemin optimumu değildir. Fiziksel faz ile eski iç model fazının karıştırılması bu tür 30°/60° kaymalarına yol açar.

## 3B görüntüleyici kapsamı

3B sekmesi etkileşimli, WebGL tabanlı bir mühendislik şemasıdır:

- Mil eksenleri
- Çatallar
- İstavrozlar
- Kamera döndürme, kaydırma ve yakınlaştırma
- Oynat/durdur
- Mevcut ve optimize edilmiş durum
- Hız oranı grafiği ile senkron animasyon

### Önemli sınırlama

3B model **kanonik düzlemsel şemadır**. Girilen β ve fiziksel fazlar korunur; ancak yalnız skaler β değerlerinden gerçek aracın yatay/düşey uzaysal şaft yerleşimi benzersiz biçimde oluşturulamaz.

3B sahne JSON metadata örneği:

```json
{
  "scene_type": "canonical_planar_schematic",
  "scene_model": "canonical_planar",
  "spatial_reconstruction": false
}
```

Gerçek uzaysal model için her milin başlangıç noktası, yön vektörü, uzunluğu ve çatal referans yönü gerekir.

## Matematiksel model

Tek Kardan mafsalının anlık hız oranı:

```text
q = ω_out / ω_in
```

```text
q(θ,β) = cos(β) / [1 - sin²(β) cos²(θ)]
```

Çıkış açısı quadrant koruyan `atan2` ile hesaplanır:

```text
θ_out = atan2(sin θ_in, cos β · cos θ_in)
```

Çoklu sistemde toplam hız oranı mafsal oranlarının çarpımıdır:

```text
q_total = q₁ · q₂ · ... · qₙ
```

Amaç fonksiyonu:

```text
Düzgünsüzlük (%) = 100 · (q_max - q_min) / |q_mean|
```

Kinematik hız cevabı 180° periyotludur. Optimizasyon benzersiz `0°–180°` aralığında, sunum grafikleri ise tam `0°–360°` devirde oluşturulur.

## Dışa aktarımlar

- Excel mühendislik çalışma kitabı
- Hız eğrileri CSV
- Analiz özeti JSON
- Kinematik yörünge JSON
- 3B sahne JSON

JSON çıktılarında sürüm, açı birimi ve faz konvansiyonu açıkça bulunur.

Excel çalışma kitabı yedi sayfadan oluşur:

1. Özet
2. Girişler
3. Karşılaştırma
4. Hız Eğrileri
5. Kinematik Yörünge
6. Faz Haritası
7. Teşhisler

## Proje yapısı

```text
Cardan_Joint_Engineering_Tool_v1_2_4/
├── streamlit_app.py
├── cardan_core.py
├── cardan_3d_viewer.py
├── benchmark_optimizers.py
├── requirements.txt
├── README.md
├── CHANGELOG.md
├── DEPLOYMENT_FIX.md
├── PHASE_CONVENTION_MIGRATION.md
├── TEST_REPORT.txt
├── BENCHMARK_REPORT.txt
├── install_windows.bat
├── run_windows.bat
└── tests/
    ├── test_cardan_core.py
    ├── test_3d_viewer.py
    └── smoke_streamlit_app.py
```

## Testler

```bash
python -m unittest discover -s tests -p "test_*.py" -v
python tests/smoke_streamlit_app.py
```

Test kapsamı:

- 0° ve 90° fiziksel faz
- 30° ve 60° ara fiziksel faz ölçümü
- 180° faz eşdeğerliği
- JSON faz konvansiyonu doğrulaması
- Etiketsiz veri reddi
- İç model fazının güvenli dönüşümü
- 9,5° üçlü sistemde 30°–30° optimum
- 3B eksen dikliği
- Quaternion normu ve sürekliliği
- İngilizce/Türkçe arayüz
- Slider–sayı kutusu kanonik state senkronizasyonu
- Yedi sayfalı Excel çıktısı

## Model kapsamı

Bu araç ideal rijit kinematik modeldir. Aşağıdaki etkiler doğrudan modellenmez:

- Mafsal boşluğu
- Elastik deformasyon
- Mil burulması
- Sürtünme
- Atalet
- Tork ve yük
- Yatak reaksiyonları
- Yorulma ve ömür
- Kritik hız
- NVH

Sonuçlar fiziksel prototip, üretici verisi veya daha ayrıntılı çoklu cisim/dinamik model ile ayrıca doğrulanmalıdır.

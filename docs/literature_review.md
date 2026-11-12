# Literatür Taraması

İncelenen kod: `main` dalı, commit `039da69` (v1.2.4). Tarama tarihi: 12 Kasım 2026.

## 1. Yöntem ve erişim sınırları

- Arama: İngilizce ve Türkçe web araması (tek mafsal kinematiği, çift mafsal fazlaması, çoklu mafsal zincirleri, düzlemsel olmayan geometri, tolerans/duyarlılık, deneysel doğrulama).
- Künye doğrulaması: DOI kayıtları Crossref API üzerinden tek tek sorgulandı. Crossref'te bulunamayan tanımlayıcılar "doğrulanamadı" olarak işaretlendi.
- **Güncelleme (v1.4.0):** Fischer ve Paul (1991) ile Seherr-Thoss ve diğ. (2006) tam metinleri sonradan sağlandı ve okundu; ayrıntı Bölüm 7'dedir. Aşağıdaki ilk tarama metni o tarihteki erişim durumunu yansıtır.
- **Erişim sınırı (ilk tarama):** Yalnızca bir makalenin tam metni okunabildi. Diğer kaynaklar için özet veya yalnızca künye mevcuttur. Springer, ASME ve SAE tam metinleri ödeme duvarı arkasındadır; iki patent sayfası ve Tor Vergata arşivindeki iki PDF erişimi reddetti (HTTP 403).
- Bu nedenle aşağıda **tam metni okunmayan hiçbir kaynaktan denklem, tablo veya sayısal değer aktarılmamıştır.** Özetten alınan ifadeler niteliksel sonuçlardır.

Erişim düzeyi kısaltmaları: **TM** = tam metin okundu, **Ö** = yalnızca özet, **K** = yalnızca künye.

## 2. Kaynak kayıtları

### 2.1 Projeye doğrudan katkı sağlayan kaynaklar

**[K1] Karaoğlan, M.U., Kuralay, N.S. (2024). "Taşıtlarda Üç Mafsallı Moment İletim Performansının Kinematik Analizi".** Dokuz Eylül Üniversitesi Mühendislik Fakültesi Fen ve Mühendislik Dergisi, 26(76), 22–27. DOI: [10.21205/deufmd.2024267603](https://doi.org/10.21205/deufmd.2024267603). Tür: hakemli dergi makalesi. Erişim: **TM**.

- *Sistem ve soru:* İki parçalı, üç mafsallı kardan milinde orta mafsal konumunun hız düzgünsüzlüğüne etkisi.
- *Denklemler:* Çıkış açısı Denklem (1) `α₂ = tan⁻¹(tan α₁ / cos β)`; hız oranı Denklem (4) `ω₂/ω₁ = cos β / (1 − sin²α₁ sin²β)`; tek mafsal düzgünsüzlüğü Denklem (5) `U = sin β · tan β`; ön ve üst görünüş açılarından bileşke açı Denklem (6) `β_r = arctan √(tan²β_ö + tan²β_ü)`.
- *Zincirleme yöntemi (Bölüm 3):* Denklem (4) her mafsal için ayrı hesaplanıp üç oran çarpılıyor. Çatal fazı ve mafsal düzlemlerinin yönü modele girmiyor.
- *Girdiler:* Tablo 1 (üst görünüş açıları 7,5°, 15°, 7,5°) ve Tablo 2 (ön görünüş açıları; Tasarım-1: +5, −10, +5; Tasarım-2: −5, +7,5, −2,5; Tasarım-3: −1, +4, −0,5).
- *Sonuçlar (Bölüm 3, Şekil 5):* Hız oranı aralıkları 1,08–0,93; 1,07–0,94; 1,05–0,95.
- *Doğrulama:* Tasarım-1 için kendi kurdukları test düzeneği (çıkış milinde enkoder, her 15°'de okuma, Arduino). Karşılaştırma Şekil 4'te görsel; sayısal hata ölçütü verilmemiş.
- *Sınırlamalar ve eleştiri:*
  - Faz ve düzlem yönü olmadığı için model, dalgalanmaların aynı fazda üst üste bindiği durumu temsil eder; fazlanmış gerçek bir iki parçalı milde sonuç farklı olur.
  - Metin en büyük hızın 0° ve 180°'de olduğunu söylüyor; Denklem (4) ve Şekil 5 ise 90° ve 270°'yi veriyor. Bu, açı başlangıcı tanımından kaynaklanan bir iç tutarsızlıktır; uç değerleri etkilemez.
  - Tasarım-1 için alt değer bir yerde 0,92, bir yerde 0,93 olarak geçiyor.
  - Değerler iki ondalık basamakla verilmiş; yüksek hassasiyetli referans değildir.
- *Projeye katkısı:* `tests/test_literature_cases.py` içindeki üç yeniden üretilebilir örnek ve tek mafsal düzgünsüzlük testi.

**[K2] Fischer, I.S., Paul, R.N. (1991). "Kinematic Displacement Analysis of a Double-Cardan-Joint Driveline".** Journal of Mechanical Design, 113(3), 263–271. DOI: [10.1115/1.2912778](https://doi.org/10.1115/1.2912778). Tür: hakemli dergi makalesi (ASME). Erişim: **Ö** (özet Crossref kaydından okundu).

- *Sistem:* Seri bağlı iki Cardan mafsalı; eşit olmayan mafsal açıları, faz açısı ve imalat hataları (dik olmayan istavroz, kaçık eksenler).
- *Yöntem (özetten):* Dual sayılı koordinat dönüşüm matrisleri; Newton–Raphson ve Davidon–Fletcher–Powell birleşimi.
- *Doğrulama (özetten):* Optik mil enkoderleri ve bilgisayarlı veri toplama ile deney.
- *Sonuçlar (özetten):*
  - Belirleyici büyüklük "bağıl faz açısı"dır: iki mafsalın faz açısı ile giriş–ara ve ara–çıkış mil düzlemleri arasındaki açının farkı.
  - Mafsal açıları eşitse ve bağıl faz açısı sıfırsa sistem sabit hız kaplini gibi çalışır.
  - Açılar eşit değilse sıfır bağıl fazda dalgalanma en aza iner ama yok olmaz.
- *Sınırlama:* Tam metne ulaşılamadığı için denklemler, deney değerleri ve hata büyüklükleri bilinmiyor. Dergi adı NJIT kayıtlarında "Journal of Mechanisms, Transmissions, and Automation in Design" olarak da geçiyor.
- *Projeye katkısı:* Üç niteliksel sonuç bağımsız 3B modelle sınandı (`tests/test_independent_reference.py`, `tests/test_literature_cases.py`).

**[K3] Seherr-Thoss, H.C., Schmelz, F., Aucktor, E. (2006). *Universal Joints and Driveshafts: Analysis, Design, Applications*.** 2. baskı, Springer. DOI: [10.1007/3-540-30170-4](https://doi.org/10.1007/3-540-30170-4). Tür: kitap. Erişim: **K**.

- Crossref kaydı başlık, yıl ve yayıncıyı doğruluyor. Yazar adları [K1]'in kaynak listesinden ve kütüphane kayıtlarından alındı.
- Arama sonuçlarında, kitabın Hooke mafsalının düzgünsüzlüğü (Poncelet), çift Hooke mafsalı ve d'Ocagne'nin sabit hız koşulu genişletmesi başlıklı bölümler içerdiği görülüyor; bu başlıklar yayıncı sayfasından doğrulanamadı.
- *Projeye katkısı:* İçerik okunmadığı için hiçbir test veya değişiklik bu kaynağa dayandırılmadı. Üçlü mafsal ve genel sabit hız koşulları için ilk bakılacak kaynak olarak yol haritasına alındı.

### 2.2 Destekleyici kaynaklar

| Kod | Kaynak | Tür | Erişim | Yararlanılan bilgi |
|---|---|---|---|---|
| D1 | Wittenburg, J. (2016). "Shaft Couplings". *Kinematics: Theory and Applications*, Springer, s. 387–410. DOI: 10.1007/978-3-662-48487-6_13 | Kitap bölümü | K | Künye Crossref'te doğrulandı. İçerik okunmadı. |
| D2 | Fischer, I.S. (1988). "Effect of Mounting Errors on Cardan-Type Universal Joint Kinematics". SAE Technical Paper 880483. DOI: 10.4271/880483 | Konferans bildirisi | Ö | Kesişmeyen giriş–çıkış eksenleri, hata büyüklüğünde çift frekanslı eksenel hareket üretir. Kapsam genişletme başlığı. |
| D3 | Vedam, K., Naganathan, N.G., Szadkowski, A., Prange, E. (1995). "Analysis of an Automotive Driveline with Cardan Universal Joints". SAE Technical Paper 950895. DOI: 10.4271/950895 | Konferans bildirisi | Ö | Mafsal açıları ve çatal fazlamasının kuvvet, tork ve kinematik etkileri; üç boyutlu açı değişimi; kamyon aktarma hattında deney. |
| D4 | Krishna, V., Naganathan, N.G., Phadnis, R., Dukkipati, R.V. (2000). "Analysis of driveline loads in an automotive powertrain with multiple Cardan joints". Proc. IMechE Part D, 214(5), 509–522. DOI: 10.1243/0954407001527808 | Hakemli makale | Ö | Çoklu mafsallı hatlarda yarı-statik denge analizi; kuvvetler salınımlı ve harmonik. Kapsam genişletme başlığı. |
| D5 | Hajdu, Š., Rolník, L., Švoš, J. (2016). "Kinematics Simulation of the Cardan Shaft for Investigation of the Cardan Error in Catia V5". Research Papers Faculty of Materials Science and Technology STU, 24(39), 159–166. DOI: 10.1515/rput-2016-0031 | Hakemli makale | Ö | CAD kinematik benzetimiyle kardan hatasının varlığı ve giderilmesi; üç montaj durumu. |
| D6 | Wu, L., Wang, L., Jing, L., Liu, Z. (2017). "Optimization of Angular Velocity Fluctuation of Multi Universal Joint Steering Transmission Mechanism". Jixie chuandong (Journal of Mechanical Transmission) | Hakemli makale (Çince) | Ö (katalog) | Çift mafsaldaki dalgalanma bindirme ilkesinin çoklu mafsala genişletilmesi ve her mafsal için en iyi faz açısı. Sayfadaki `10.16578/j.issn.1004.2539.2017.05.019` tanımlayıcısı Crossref'te **doğrulanamadı**. |
| D7 | Pan, Y. ve diğ. (2016). "Application of ADAMS in the Optimization Design of Automobile Double Cross Shaft Universal Joint Steering Transmission System". Jixie chuandong | Hakemli makale (Çince) | Ö (katalog) | Direksiyon ara milinde faz açısı ve bağlantı noktalarının ADAMS ile eniyilenmesi. DOI doğrulanamadı. |
| D8 | Pezzuti, E., Stefanelli, R., Valentini, P.P., Vita, L. (2006). "Computer-aided simulation and testing of spatial linkages with joint mechanical errors". Int. J. Numer. Methods Eng., 65(11), 1735–1748. DOI: 10.1002/nme.1507 | Hakemli makale | K | Künye doğrulandı. Arama özetine göre dual cebirle imalat hatalı uzaysal mekanizmalar, Cardan mafsalı uygulaması. |
| D9 | Gao, J., Qi, X. (2023). "Handling performance analysis and optimization of a vehicle with considering the influence of steering shaft parameters". J. Mech. Sci. Technol., 37(2), 569–582. DOI: 10.1007/s12206-023-0103-8 | Hakemli makale | K | Künye doğrulandı. İçerik okunmadı. |
| D10 | Li, Z., Nakhaeinejad, M., Ganeriwala, S. (2009). "Torsional Vibration Simulation Using a Universal Joint". SpectraQuest Inc. teknik notu | Üretici teknik dokümanı | Ö (açık sayfa) | 1024 darbeli enkoder; 5°, 10°, 15° mafsal açıları. Hız dalgalanması açıyla artar ve ortalama hızla doğrusal orantılıdır; açısal sapma yalnızca mafsal açısına bağlıdır. Sayısal tablo açık sayfada yok. |
| D11 | MathWorks, "Double Cardan Joint" (Simscape Driveline örneği) | Yazılım dokümantasyonu | TM (sayfa) | Zıt açılı ve yarım açılı iki düzenlemede giriş ve çıkış hızları özdeş; ara mil hızı değişken. |
| D12 | Lao, R. (2018). "A Brief Analysis of the Hooke's Joint". Zenodo. DOI: 10.5281/zenodo.1188453 | Hakemsiz rapor | Ö | 3×3 dönme matrisleriyle türetim. PDF okunmadı. |

### 2.3 Erişilemeyen ve bu nedenle kullanılmayan kaynaklar

- SAE AE-7 *Universal Joint and Driveshaft Design Manual* (1979): varlığı doğrulandı, içeriğine ulaşılamadı.
- Kuralay, N.S. (2008). *Motorlu Taşıtlar, Cilt 1*: [K1]'in "üç mafsalın toplam bileşke açısı 3°'den küçük olmalı" ölçütü için gösterdiği kaynak; okunmadı.
- "System and Method for Optimum Phasing of a Three-Shaft Steering Column" patent başvurusu (US 2008/0126042): sayfa erişimi reddetti.
- Pennestrì ve çalışma arkadaşlarının imalat hatalı Cardan mafsalı çalışmaları (Tor Vergata arşivi): PDF erişimi reddetti; künyeleri doğrulanamadı.

## 3. Karşılaştırmalı tablo — doğrudan katkı sağlayan kaynaklar

| Kaynak | Sistem | Geometri | Faz tanımı | Yöntem | Doğrulama | Bu projedeki karşılık |
|---|---|---|---|---|---|---|
| K1 | Üçlü mafsal | Ön ve üst görünüş açılarından bileşke açı; düzlem yönü kullanılmıyor | Yok | Tek mafsal oranlarının çarpımı | Kendi düzeneği, görsel karşılaştırma | Düzlemsel zincir, fiziksel faz 90°/90° |
| K2 | Çift mafsal | Genel uzaysal | Bağıl faz = faz − düzlemler arası açı | Dual sayılı matrisler, sayısal çözüm | Optik enkoderli deney | Düzlemsel model; düzlem kaçıklığı faza eklenerek temsil edilir |
| K3 | Tek, çift ve çoklu | Okunamadı | Okunamadı | Okunamadı | Okunamadı | Kullanılmadı |

## 4. İzlenebilirlik matrisi

| Kaynak | Bilimsel sonuç / denklem | Varsayımlar | Projedeki karşılık | Uyum / fark | Sınıf | Test veya değişiklik |
|---|---|---|---|---|---|---|
| K1, Denk. (1) | `tan α₂ = tan α₁ / cos β` | İdeal rijit mafsal | `hooke_output_angle_rad` (atan2 biçimi) | Uyumlu | — | `test_full_revolution_and_derivative_consistency` |
| K1, Denk. (4) | `q = cos β / (1 − sin²α sin²β)` | α başlangıcı farklı | `hooke_speed_ratio_rad` (`cos²θ` biçimi) | 90° açı başlangıcı farkı; uç değerler aynı | Konvansiyon farkı, hata değil | `test_single_joint_extrema_and_unevenness` |
| K1, Denk. (5) | `U = sin β tan β` | Tek mafsal | `unevenness_percent` | Uyumlu (1e-9 pu) | — | Aynı test |
| K1, Bölüm 3 | Üç oranın çarpımı; Tasarım 1–3 aralıkları | Faz ve düzlem yönü yok | `triple_cardan_ratio`, faz 90°/90° | ±0,006 içinde uyumlu | Belgelenmiş model farkı | `test_karaoglan_kuralay_three_joint_speed_ratio_range` |
| K2, özet | Eşit açılar ve sıfır bağıl faz → sabit hız | Uzaysal geometri | `double_cardan_ratio`, φ = 0 | Uyumlu; uzaysal durumda da bağımsız modelle doğrulandı | — | `test_spatial_equal_angles_constant_velocity_at_zero_relative_phase` |
| K2, özet | Eşit olmayan açılarda en küçük dalgalanma sıfır bağıl fazda, sıfır değil | Aynı | `exact_phase_optimum` (çift mafsal) | Uyumlu. v1.2.4'te örneklenmiş amaç 179,83° ve 0,25° döndürüyordu | Sayısal yöntem eksikliği (giderildi) | `test_fischer_paul_unequal_angles_minimum_at_zero_relative_phase`, `test_double_joint_optimum_is_aligned_yokes` |
| K2, özet | Yalnızca bağıl faz belirleyicidir | Aynı | Model yalnızca düzlemsel; φ girdisi bağıl faz olarak yorumlanabilir | Çift mafsal için doğrulandı; üçlü için doğrulanmadı | Belgelenmiş model sınırı / çözülmemiş belirsizlik | `test_spatial_plane_offset_acts_as_relative_phase` |
| D11 | Zıt açılı düzenlemede çıkış hızı girişe eşit | İdeal mafsal | Düzlemsel Z yerleşimi | Uyumlu | — | `test_z_and_w_layouts_are_equivalent_for_aligned_yokes` |
| D10 | Açısal sapma yalnızca mafsal açısına bağlı | Tek mafsal | Model hızdan bağımsız | Niteliksel uyum; sayısal veri yok | Fiziksel geçerleme yapılamadı | — |
| D2, K2 | İmalat ve montaj hataları kinematiği değiştirir | Hatalı geometri | Modelde yok | Kapsam dışı | Kapsam genişletme fırsatı | Yol haritası |
| D3, D4 | Fazlama kuvvet ve tork dalgalanmasını etkiler | Dinamik veya yarı-statik | Modelde yok | Kapsam dışı | Kapsam genişletme fırsatı | Yol haritası |
| D6 | Çoklu mafsalda en iyi faz açıları | Okunamadı | `exact_phase_optimum` | Karşılaştırılamadı | Çözülmemiş belirsizlik | — |

## 5. Literatürde karşılığı bulunamayan sonuç

Projeye eklenen kapalı-form çözüm (zincirin 2×2 doğrusal dönüşüm olarak yazılması, tekil değerlerden hız oranı uçları ve koşul sayısının alt-çarpımsallığından gelen alt sınır) taranan kaynakların erişilebilen kısımlarında bulunamadı. [K3] ve [D1] okunamadığı için bu sonucun literatürde yer almadığı **iddia edilmiyor**. Sonuç bu projede türetildi ve üç bağımsız yolla sayısal olarak doğrulandı; ayrıntı `docs/model_assumptions.md` ve `docs/validation_report.md` belgelerindedir.

## 6. Kapsam genişletme literatürü (kinematik model dışı)

Tork, yatak yükleri, esneklik, sürtünme, boşluk ve burulma titreşimi çalışmaları ([D2], [D3], [D4], [D8]) mevcut modelin dışındadır. Bu kaynaklar yalnızca özet düzeyinde incelendi ve hiçbir hesap yoluna dayanak yapılmadı.

## 7. Tam metin incelemesi (güncelleme, v1.4.0)

İki kaynağın PDF'i sağlandı (`literat/` klasörü; telif nedeniyle repoya eklenmedi). Erişim düzeyleri **TM** olarak güncellendi.

### 7.1 Fischer ve Paul (1991) — tam metin (s. 263–271)

- **Model (s. 263–264, Şekil 1, Denk. 1–3):** Çift Cardan hattı altı uzuvlu uzaysal mekanizma (RRRRRC) olarak, 3×3 dual sayılı dönüşüm matrisleri ve kapalı çevrim koşuluyla kurulur.
- **Çözüm (s. 264–266, Denk. 5–22):** İlk konumda Davidon–Fletcher–Powell, sonraki adımlarda Newton–Raphson; adım en çok 20°.
- **Bağıl faz açısı (s. 268, Denk. 23):** `RPA = (faz açısı) − (burulma açısı)`. Burulma açısı, giriş–ara ve ara–çıkış mil düzlemleri arasındaki açıdır.
- **Sonuçlar:**
  - Eşit mafsal açılarında dalgalanma genliği RPA ile artar ve RPA = 90°'de en büyüktür; 45° mafsal açısında sıfırdan yaklaşık 20°'ye çıkar (s. 268, 270; Şekil 7).
  - Mil ekseni kaçıklığının, verilen bir RPA için giriş–çıkış ilişkisine etkisi ihmal edilebilir (Şekil 8).
  - Eşit olmayan açılarda sabit hız elde edilemez; genlik RPA = 0'da en küçüktür ve açı farkıyla, ayrıca açıların büyüklüğüyle artar (s. 269, Şekil 9).
- **Deney (s. 266–267, 270):** Giriş ve çıkış millerinde optik enkoder; eğrilerdeki düzensizlik 0,36° (enkoder çözünürlüğü). 10°/30° açılar, 60° faz, 0,867 in kaçıklık için dört tekrarın standart sapması 0,0323°, genlik yaklaşık 4°. Şekil 11–12'de deney ile hesap yakın uyumludur.
- **Bu projeyle karşılaştırma:**

| Kaynak değeri | Girdi | Model sonucu | Tolerans |
|---|---|---|---|
| "yaklaşık 20°" (s. 268, 270) | β = 45°/45°, RPA = 90° | 19,47° | ±0,6° |
| 0° | β = 45°/45°, RPA = 0° | 0° | 1e-9 |
| Şekil 11: düz eğri | β = 30°/30°, faz −20,1° | 0° (burulma = −20,1° çıkarımı) | ±0,5° |
| Şekil 11: ≈ 2,9° | β = 30°/30°, faz 0° (RPA 20,1°) | 2,84° | ±0,5° |
| Şekil 12: ≈ 6,4° | faz 30° (RPA 50,1°) | 6,32° | ±0,5° |
| Şekil 12: ≈ 8,0° | faz 60° (RPA 80,1°) | 8,09° | ±0,5° |

  Şekil değerleri gözle okunmuştur; belirsizlik en az enkoder çözünürlüğü (0,36°) kadardır. Burulma açısı makalede sayısal verilmediği için, −20,1° fazda eğrinin düz olmasından çıkarılmıştır.
- **Kullanılmayan örnekler:** Şekil 5 (35°/35°, faz 50°) ve 10°/30° deneyi için burulma açısı verilmemiştir; eksik parametre tahmin edilmedi. Bilgi amaçlı: model RPA = 50° için 8,75° verir, Şekil 5'in tepe değeri de bu düzeydedir; 10°/30° için RPA 40°–80° aralığında 4,1°–4,5° verir, ölçülen "yaklaşık 4°" ile uyumludur.
- **Sınır:** İmalat hatalı durum (Şekil 6, dik olmayan istavroz ve kaçık eksenler) bu projenin ideal modelinin dışındadır.

### 7.2 Seherr-Thoss, Schmelz, Aucktor (2006) — Bölüm 1.2 (s. 5–10) tam metin; 4.2–4.3 ve 5 tarandı

- **Denk. (1.1a), s. 6:** `tan φ₂ = cos β · tan φ₁` — başlangıçta istavroz ekseni mil düzlemine dik ("orthogonal").
- **Denk. (1.1c), s. 6:** `tan φ₂ = tan φ₁ / cos β` — başlangıçta çatal mil düzleminde ("in-phase"). Bu projenin `hooke_output_angle_rad` işlevi bu biçimdedir.
- **Denk. (1.2), s. 6:** `ω₂/ω₁ = cos β / (1 − sin²β sin²φ₁)`; uç değerler `cos β` ve `1/cos β`. Bu, (1.1a) başlangıcına aittir; projedeki `cos²θ` biçimi (1.1c) başlangıcının karşılığıdır.
- **s. 6 ve Şekil 1.7a:** 45° mafsal açısında ileri–geri sapma "yaklaşık ±10°". Model: 9,88°. Şekilden 30° için ≈ 4° (model 4,12°), 15° için ≈ 1° (model 0,99°).
- **Bölüm 1.2.2, s. 8–9:** Ara mildeki çatallar aynı düzlemdeyse `tan φ₃ = (cos β₁ / cos β₂) · tan φ₁`; `β₂ = ±β₁` için sabit hız (Z ve W düzeni). Çatallar 90° fazdaysa düzgünsüzlük `ω_max = ω_min / (cos β₁ cos β₂)` düzeyine çıkar.
- **Bölüm 1.2.3, s. 10:** d'Ocagne koşulları (giriş ve çıkış eksenleri kesişir; iki mafsal bir düzleme göre simetriktir) ve Willis'in uzaysal miller için karşıt fazlama sonucu. Bu bölüm fazlanmış uzaysal durumun denklemini türetmez.
- **s. 302 (Bölüm 5.3.3):** Tarım makinesi kuyruk mili uygulamasında, kusurlu Z düzeninden kaynaklanan düzgünsüz dönme için "genel olarak ±%7 kabul edilebilir". Bu bir uygulama ölçütüdür; projenin %5 eşiği gibi evrensel standart değildir.
- **Bulunmayanlar:** Kitapta üç veya daha fazla Hooke mafsalının faz eniyilemesi ve bu projedeki 2×2 matris/tekil değer formülasyonu **yer almıyor** (anahtar sözcük taraması ve ilgili bölümlerin okunması). Çift mafsal için `cos β₁ / cos β₂` oranı ise kitapta vardır ve projedeki çift mafsal kapalı-form sonucunun kaynağı olarak gösterilebilir.

### 7.3 Karaoğlan ve Kuralay (2024) — düzeltilmiş eleştiri

- Kitaptaki iki başlangıç tanımıyla karşılaştırınca: makalenin Denk. (1)'i "in-phase" biçimidir (1.1c), Denk. (4)'ü ise "orthogonal" biçimin hız oranıdır (1.2). İkisi aynı açı başlangıcına ait değildir. Metindeki "en büyük hız 0° ve 180°'de" ifadesi Denk. (1) ile, Şekil 5 ise Denk. (4) ile uyumludur. Uç değerler bundan etkilenmez.
- Şekil 6'daki açı farkı genlikleri (±0,7°, ±0,6°, ±0,5°) makalenin kendi hız oranı aralıklarıyla tutarlı değildir: aynı model 2,11°, 1,85° ve 1,56° verir (yaklaşık üç kat). Nedeni makaleden anlaşılamıyor; bu değerler referans olarak **kullanılmadı**.

### 7.4 Klasördeki ikinci inceleme (`research_checkout/docs/literature_review.md`)

Aynı klasörde, bu çalışmadan bağımsız yürütülmüş ikinci bir inceleme bulunuyor. Fischer–Paul ve Karaoğlan–Kuralay ortak; aşağıdaki yedi kaynak yalnızca orada yer alıyor. Künyeleri Crossref üzerinden doğruladım; **içeriklerini ben okumadım**, erişim düzeyleri o incelemenin beyanıdır.

| Kaynak | Künye (Crossref) | O incelemedeki erişim | Konu |
|---|---|---|---|
| An, K., Wang, W. (2017) | Adv. Mech. Eng. 9(5), DOI 10.1177/1687814017707478 | Tam metin | İdeal çift mafsal, gevşeklik ve aşınma |
| Gao, J., Qi, X. (2023) | Science Progress 106(3), DOI 10.1177/00368504231195495 | Tam metin | Direksiyon sistemi, başlangıç açısı |
| Karadere, G., Kopmaz, O., Gullu, E. (2010) | Int. J. Mater. Prod. Technol. 39(3/4), 317–, DOI 10.1504/IJMPT.2010.035806 | Özet | İstavroz rijitlik koşulundan türetim |
| Wu, G., Shi, W., Chen, Z. (2013) | SAE Technical Paper 2013-01-1490, DOI 10.4271/2013-01-1490 | Özet | Çoklu mafsal fazı ve burulma titreşimi |
| Hummel, S.R., Chassapis, C. (2000) | Mech. Mach. Theory 35(3), 463–476, DOI 10.1016/S0094-114X(98)00092-5 | Özet | İmalat toleranslı tasarım |
| Dhamankar, S. ve diğ. (2025) | SAE Int. J. Commer. Veh. 18(1), 3–22, DOI 10.4271/02-18-01-0001 | Özet | Burulma titreşimi, yol deneyi |
| Ali, J., Shaver, G., Bajaj, A.K. (2026) | Nonlinear Dynamics 114, DOI 10.1007/s11071-025-12172-2 | Kısmi tam metin | Boşluklu mafsalda darbeler |

Notlar:
- Bu çalışmadaki Gao ve Qi (2023, J. Mech. Sci. Technol.) kaydı aynı yazarların **farklı** bir makalesidir.
- O inceleme Hummel ve Chassapis için yılı doğrulayamamıştı; Crossref kaydı 2000, cilt 35(3), s. 463–476 veriyor.
- İki incelemenin ortak sonuçları örtüşüyor: Karaoğlan–Kuralay'daki iç tutarsızlık, `θ₀`'ın şema yerleşimi olmadığı ve bağımsız geometrik referans gereği.
- O incelemedeki An ve Wang (2017) ile Gao ve Qi (2023) açık erişimli tam metinlerdir; okunup sayısal örnek çıkarılması yol haritasına eklendi.

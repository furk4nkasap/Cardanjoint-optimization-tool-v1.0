# Model Varsayımları ve Denklemler

Bu belge kodda gerçekten uygulanan modeli anlatır (`cardan_core.py`, v1.3.0). README'deki ifadeler kodla karşılaştırılarak yazılmıştır.

## 1. Fiziksel kapsam

- İdeal, rijit, boşluksuz Hooke (Cardan) mafsalları; mil eksenleri mafsal merkezinde kesişir.
- Yalnızca kinematik: kütle, atalet, tork, yatak tepkileri, sürtünme, esneklik, boşluk, verim ve titreşim yoktur.
- Mil eksenleri **tek bir düzlemde** kabul edilir (kanonik düzlemsel şema).

## 2. Tek mafsal

`θ`, mafsalın giriş açısıdır. Uygulanan bağıntılar:

- Çıkış açısı: `θ_out = atan2(sin θ, cos β · cos θ)` (`hooke_output_angle_rad`)
- Hız oranı: `q = cos β / (1 − sin²β · cos²θ)` (`hooke_speed_ratio_rad`)

İkincisi birincinin türevidir; bu, testlerde sayısal türevle 1e-8 içinde doğrulanır. Bu açı başlangıcında en büyük hız oranı `θ = 0°` konumundadır. Karaoğlan ve Kuralay (2024) Denklem (4) aynı bağıntıyı `sin²α` ile yazar; iki biçim açı başlangıcında 90° farklıdır ve aynı uç değerleri verir (`cos β` ile `1/cos β`).

## 3. Faz konvansiyonu

| Büyüklük | Tanım |
|---|---|
| Fiziksel faz `φ` | Ortak mil üzerindeki iki çatalın arasındaki açı. `0°` = hizalı, `90°` = dik. Kullanıcıya ve dosyalara açık tek konvansiyon. |
| İç model fazı `ψ` | `ψ = (90° − φ) mod 180°`. Yalnızca özyinelemede kullanılır. |
| Zincirleme | `θ_(i+1),in = θ_i,out − ψ_i` |

- Faz 180° periyodiktir; `CardanParameters` fazı `[0°, 180°)` aralığına indirger.
- 3B sahnede ölçülen çatal açısı girilen `φ` ile 1e-9° içinde aynıdır (test: `test_scene_yoke_clocking_equals_entered_physical_phase`).
- **Dönüş yönü (v1.4.0):** Pozitif `φ`, mil boyunca girişten çıkışa doğru bakıldığında sonraki mafsalın giriş çatalını önceki mafsalın çıkış çatalına göre **saat yönünde** döndürür (mil yönü etrafında sağ el kuralı). 3B sahne bu tanımla üretilir ve testle sabitlenmiştir (`test_scene_yoke_clocking_equals_entered_physical_phase`). Düzlemsel modelde `(φ₁, φ₂)` ile `(−φ₁, −φ₂)` eşdeğerdir; `(φ₁, −φ₂)` eşdeğer değildir. Bu nedenle yönün kendisi sonucu değiştirmez, ancak iki faz **aynı yön kuralıyla** uygulanmalıdır.

## 4. Geometri varsayımları

- 2B ve 3B çizimlerde β açıları aynı yönde biriktirilir. Düzlemsel modelde büküm yönü (Z veya W yerleşimi) sonucu değiştirmez; bu, bağımsız 3B modelle doğrulanmıştır.
- **Uzaysal geometri:** Çift mafsalda ikinci mafsalın düzlemi ara mil etrafında `ψ_d` kadar dönükse, sonuç düzlemsel modelde faza `ψ_d` eklenmesiyle aynıdır. Bu, Fischer ve Paul'ün (1991) "bağıl faz açısı" sonucuyla uyumludur ve bağımsız modelle doğrulanmıştır. Üçlü mafsal için bu eşdeğerlik **doğrulanmamıştır**.
- `θ₀` giriş milinin kendi ekseni etrafındaki dönme referansıdır; mil yerleşimini eğmez. v1.3.0'dan itibaren 2B şema `θ₀` ile döndürülmez.

## 5. Metrikler

Bir tam giriş devri üzerinde, düzgün örneklenmiş `q` için:

- Düzgünsüzlük: `U = 100 · (q_max − q_min) / q̄`
- RMS hız hatası: `100 · √mean((q/q̄ − 1)²)`
- Ortalama `q̄`, düzgün giriş açısı ızgarasında tam olarak 1'dir (bir giriş devri bir çıkış devrine karşılık gelir).

`θ₀` bu metrikleri fiziksel olarak değiştirmez; yalnızca örnekleme ızgarasını kaydırır.

%5 eşiği bir proje ölçütüdür, evrensel tasarım standardı değildir.

## 6. Kapalı-form çözüm (v1.3.0)

### 6.1 Türetim

Mil açısını `v = (sin θ, cos θ)` yön vektörüyle gösterelim.

1. Bir mafsal, yönü `(sin θ, cos β cos θ)` yapar: `D(β) = diag(1, cos β)`.
2. Bir faz kayması düzlemde dönmedir: `R(ψ)`.
3. Zincirin tamamı tek bir 2×2 matristir: `M = D₃ R(ψ₂) D₂ R(ψ₁) D₁`.
4. Çıkış açısı `M v` vektörünün yönüdür; buradan `dθ_out/dθ_in = det(M) / |M v|²`.

`M`'nin tekil değerleri `s₁ ≥ s₂` ise:

- `q_max = s₁ / s₂ = κ`, `q_min = 1/κ`, ortalama 1.
- `U = 100 · (κ − 1/κ)`.

Sayısal olarak kararlı biçim (`det M > 0`):

- `s₁ − s₂ = hypot(m₁₁ − m₂₂, m₁₂ + m₂₁)`
- `s₁ + s₂ = hypot(m₁₁ + m₂₂, m₁₂ − m₂₁)`
- `U = 100 · (s₁ − s₂)(s₁ + s₂) / det M`

Bu biçim sabit hıza yakın durumlarda çıkarma hatası üretmez.

### 6.2 Alt sınır ve küresel optimum kanıtı

Koşul sayısı alt-çarpımsaldır: `κ(AB) ≤ κ(A) κ(B)`. `ℓ_i = ln(1/cos β_i)` için bu,

`ln κ(M) ≥ ℓ_max − (diğer ℓ değerlerinin toplamı)`

verir. Sağ taraf pozitifse sabit hız hiçbir faz seçimiyle elde edilemez ve `U_min ≥ 200 · sinh(ℓ_max − Σ diğer)` olur. `minimum_unevenness_lower_bound_percent` bu sınırı hesaplar.

Bulunan optimum bu sınıra `1e-7` yüzde puanı içinde ulaşıyorsa küresel optimum olduğu, aramadan bağımsız olarak kanıtlanmış olur (`ExactOptimum.certified_global`).

Sınıra her zaman ulaşılabildiği genel olarak kanıtlanmamıştır; 150 rastgele üçlüde ve 40 rastgele çiftte sayısal olarak ulaşılmıştır. Ulaşılamazsa `certified_global = False` döner ve arayüz bunu açıkça yazar.

### 6.3 Optimum

- **Çift mafsal:** Optimum her zaman `φ = 0°` (hizalı çatallar), kalan düzgünsüzlük `κ = cos β_küçük / cos β_büyük` ile belirlenir.
- **Üçlü mafsal:** `s₁ − s₂ = 0` iki bilinmeyenli iki denklemdir. Kapalı-form ızgaranın en iyi düğümlerinden başlayan Levenberg–Marquardt çözümü kullanılır; alt sınıra ulaşıldığında arama durur.
- Ayna görüntüsü optimumlar eşdeğerdir; hangisinin döneceği deterministiktir ama fiziksel bir tercih ifade etmez.

### 6.4 Kaynak durumu

Bu türetim taranan kaynakların erişilebilen kısımlarında bulunamadı (bkz. `docs/literature_review.md`, Bölüm 5). Doğruluğu literatüre değil, üç bağımsız sayısal doğrulamaya dayanır (bkz. `docs/validation_report.md`).

## 7. Örnekleme

- Amaç ızgarası: 180° periyotta 360 nokta (0,5°).
- Yoğun doğrulama ızgarası: aynı başlangıçlı, kullanıcı seçimli; amaç ızgarasını içerir. Bu nedenle yalnızca örnekleme hatasını ölçer.
- `q(θ) = 1 / (a + b cos(2θ − δ))` biçimindedir; tepe geniştir ve β ≤ 60° için 360 noktalı örnekleme hatası en kötü %0,04 düzeyindedir. β > 75° için tepe daralır ve hata hızla büyür.

## 8. Geçerlilik alanı

| Koşul | Durum |
|---|---|
| β ≤ 60° (arayüz sınırı) | Örneklenmiş ve kapalı-form sonuçlar uyumlu |
| 60° < β < 90° (yalnızca Python API) | Kapalı-form değerler doğru; örneklenmiş amaç ve grid tabanlı yöntemler güvenilir değil |
| β → 90° | Tekil; `ZeroDivisionError` veya `ValueError` |
| Sonlu olmayan girdiler | Kurulumda `ValueError` |
| Düzlemsel olmayan üçlü sistem | Model dışı |

# Changelog

## v1.5.0 — Maintenance & Robustness

- Arayüz: "Ultra hassas optimizasyon" kutusu kaldırıldı; standart analiz zaten kanıtlanmış küresel optimumu veriyor. Grid, yerel inceltme, DE ve hibrit yöntemler uzman modunda seçilebilir.
- Stokastik yöntemler otomatik yenilenmez; "Analizi çalıştır" ile çalıştırılır.
- CSV: ilk beş sütun aynı kaldı; sağa sürüm, konfigürasyon, açılar, optimum fazlar, birim ve faz konvansiyonu sütunları eklendi.
- Yerel inceltme: eksen başına 81 düğümü aşan pencereler aşamalı taranır (en kötü durum 361 345 → 7 666 değerlendirme). Varsayılan ayarların sonucu değişmedi; geniş pencerelerde tam taramaya göre ölçülen en büyük fark 0,04 yüzde puanı.
- `use_container_width` yerine Streamlit ≥ 1.51'de `width="stretch"` kullanılır; eski sürümlerle uyum korunur.
- Analiz önbelleğine 128 kayıt sınırı kondu.
- Kullanılmayan çeviri anahtarları silindi.

## v1.4.0 — Tolerance Sensitivity & Discrete Phasing

- `tolerance_sensitivity`: faz ve mafsal açısı toleransı içinde kapalı-form en kötü düzgünsüzlük.
- `discrete_phase_values_deg`, `discrete_phase_optimum`: spline diş sayısına göre ulaşılabilen fazlar ve en iyisi.
- Arayüz: Genel Bakış sekmesine "Montaj toleransı ve spline indeksleme" bölümü eklendi.
- JSON özetine `tolerance_sensitivity` bloğu eklendi (mevcut alanlar değişmedi).
- Faz dönüş yönü belgelerde ve arayüzde tanımlandı.
- Core API sürümü 10. Mevcut sayısal sonuçlar değişmedi.

## v1.3.0 — Closed-form Verification & Optimizer Correctness

- Kapalı-form (örneklemesiz) hız oranı sınırları eklendi: `exact_speed_ratio_bounds`, `exact_unevenness_grid`.
- Kanıtlanabilir küresel faz optimumu eklendi: `exact_phase_optimum`, `minimum_unevenness_lower_bound_percent`, `OptimizationMethod.EXACT`.
- Düzeltme: mevcut konfigürasyon artık her yöntemde adaydır; "optimum" mevcut durumdan kötü olamaz (negatif azalma hatası).
- Düzeltme: çift mafsalda optimum, örnekleme gürültüsü yerine analitik olarak `0°` (hizalı çatallar) verilir.
- Düzeltme: `theta0`, `phi` ve adım için sonluluk denetimi eklendi.
- Düzeltme: 2B geometri şeması artık `theta0` kadar döndürülmüyor.
- Azalma yüzdesi sıfıra yakın tabanda tanımsız (`—`) gösterilir: `reduction_percent`.
- Arayüz: standart analiz kapalı-form optimumu kullanır; teşhis tablosuna kapalı-form değer, küresel optimum ve optimuma uzaklık eklendi.
- Dışa aktarım: Excel'e faz konvansiyonu ve konfigürasyon satırları, JSON özetine `closed_form` bloğu eklendi (mevcut alanlar değişmedi).
- `tests/` (267 test), `benchmarks/benchmark_methods.py`, `docs/` ve CI iş akışı eklendi.
- Core API sürümü 9. Mevcut dört yöntemin sayısal sonuçları değişmedi.

## v1.2.4 — Phase Safety & Model Transparency

- Bütün paket, uygulama, README ve dışa aktarım sürümleri `1.2.4` olarak birleştirildi.
- Core API sürümü 8'e yükseltildi.
- `PhaseConvention` enum eklendi.
- `CardanParameters` yalnız `physical_yoke_clocking` kabul edecek şekilde güvenli hâle getirildi.
- Fazlar benzersiz `0°–180°` aralığına kanonikleştirildi.
- Sürümlü ve birim etiketli parametre JSON sözleşmesi eklendi.
- Faz konvansiyonu bulunmayan verilerin sessizce yorumlanması engellendi.
- Açıkça belirtilen iç Hooke fazlarının fiziksel faza dönüşümü eklendi.
- Slider ve sayı kutusu tek kanonik açı state'ine bağlandı.
- `0,5°` ve `0,01°` hassasiyet modları için adım normalizasyonu eklendi.
- 30° ve 45° yüksek-beta bilgilendirme seviyeleri eklendi.
- 3B sekmesine kalıcı düzlemsel şema açıklaması eklendi.
- 3B JSON'a `scene_model` ve `spatial_reconstruction` metadata alanları eklendi.
- 30° ve 60° fiziksel faz görsel ölçüm testleri eklendi.
- `9,5°–9,5°–9,5°` üçlü Kardan için `30°–30°` optimum regresyon testi eklendi.
- Türkçe ve İngilizce dağıtım fallback mesajları korundu.

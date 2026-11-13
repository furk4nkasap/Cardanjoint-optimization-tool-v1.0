# Geliştirme Yol Haritası

Öncelikler, `docs/validation_report.md` içindeki ölçümlere ve `docs/literature_review.md` içindeki kaynaklara dayanır. Efor: K = küçük (saatler), O = orta (günler), B = büyük (haftalar).

## Kısa vade — mevcut kapsam içinde

| # | İş | Fayda | Efor | Bağımlılık | Başarı ölçütü |
|---|---|---|---|---|---|
| 1 | Faz ve β toleransı duyarlılık çıktısı | Optimumun montajda ne kadar korunduğunu gösterir; ölçülen örnekte 1° faz hatası %5 düzgünsüzlük üretiyor | K | Kapalı-form işlevler (hazır) | ±Δφ ve ±Δβ için en kötü düzgünsüzlük, kapalı-form ızgarayla 1e-9 pu uyumlu |
| 2 | Ayrık faz seçenekleri (spline diş sayısı) | Uygulanabilir en iyi fazı verir | K | 1 | Verilen diş sayısında tüm seçenekler arasından en iyisi; kaba kuvvetle aynı |
| 3 | CSV'ye üst bilgi veya eşlik eden JSON | Dosya tek başına yorumlanır | K | Biçim kararı (kullanıcı) | Parametre, sürüm, konvansiyon dosyada |
| 4 | `use_container_width` → `width` geçişi | Gelecek Streamlit sürümlerinde kırılmayı önler | K | — | Uyarı yok; `test_app.py` geçiyor |
| 5 | `st.cache_data` için `max_entries` | Canlı modda bellek büyümesini sınırlar (kayıt başına ~147 KB) | K | — | Sınır tanımlı |
| 6 | Yerel inceltme penceresinin sınırlandırılması | Kaba 15°, yerel 0,05° ile 361 345 değerlendirme ve 2,5 s ölçüldü | K | — | En kötü durumda < 0,3 s |
| 7 | `φ` dönüş yönünün belgelenmesi ve 3B görünümde gösterilmesi | Üçlü sistemde yanlış montaj riskini azaltır | K | — | Belgelerde ve Şekil C'de açık tanım |

## Orta vade — doğrulamayı güçlendirme

| # | İş | Fayda | Efor | Bağımlılık | Başarı ölçütü |
|---|---|---|---|---|---|
| 8 | Seherr-Thoss ve diğ. (2006) ile Wittenburg (2016) tam metinlerinin incelenmesi | Kapalı-form sonucun ve çoklu mafsal sabit hız koşullarının literatür karşılığı | O | Kaynağa erişim | Denklem numaralı eşleştirme; varsa yayımlanmış sayısal örnekle test |
| 9 | Fischer ve Paul (1991) tam metninden sayısal örnek | Deneyle doğrulanmış bir referans | O | Kaynağa erişim | Makaledeki bir tablo veya şekil değeri belirtilen toleransla yeniden üretilir |
| 10 | Üçlü sistemde uzaysal geometri | Gerçek araç yerleşimi; çift mafsalda eşdeğerlik doğrulandı | O | 8 veya bağımsız 3B modelle kanıt | Mil yön vektörlerinden β ve düzlem açıları; bağımsız 3B modelle 5e-4 pu uyum |
| 11 | Alt sınıra ulaşılabilirliğin analitik kanıtı veya karşı örneği | `certified_global` bayrağının kapsamını netleştirir | O | — | Kanıt belgede ya da karşı örnek testte |
| 12 | Yöntem sayısının azaltılması | DE ve hibrit, kapalı-form karşısında kazanç sağlamıyor | K | Kullanıcı kararı | Arayüzde kapalı-form ve harita; eski yöntemler yalnızca API'de |

## Uzun vade — kapsam genişletme

Bu başlıklar yeni fizik gerektirir ve mevcut hesap yoluna doğrulanmadan eklenmemelidir.

| Konu | Gerekli parametreler | Varsayımlar | Doğrulama verisi | Efor | Kaynak |
|---|---|---|---|---|---|
| İmalat ve montaj hataları (dik olmayan istavroz, kesişmeyen eksenler) | Hata açıları ve kaçıklıklar | RCCC benzeri uzaysal mekanizma | Fischer ve Paul (1991) deneyi; Fischer (1988) | B | K2, D2, D8 |
| Tork dalgalanması ve yatak yükleri | Tork, mil atalet momentleri, yatak konumları | Yarı-statik denge | Vedam ve diğ. (1995), Krishna ve diğ. (2000) | B | D3, D4 |
| Burulma titreşimi | Atalet, burulma rijitliği, sönüm | Toplu parametreli model | Ölçüm veya yayımlanmış doğal frekanslar | B | — |
| Süspansiyon hareketi boyunca β taraması | Bağlantı noktalarının yörüngesi | Kinematik | Yok; mevcut modelin tekrarı | O | — |

Harmonik analiz ayrı bir özellik olarak önerilmiyor: ideal kinematik modelde yanıt tek bir 2. mertebe terimin tersidir (`q = 1/(a + b cos(2θ − δ))`) ve kapalı-form çözüm bu bilgiyi zaten içerir. Burulma titreşimi modeli olmadan ek değer üretmez.

## Fiziksel geçerleme

Model hiçbir deneysel veriyle karşılaştırılmadı. En düşük eforlu seçenek, enkoderli basit bir düzenekte tek ve çift mafsal için hız oranı ölçümüdür (bkz. D10 ve K1'in düzenekleri). Ölçüm belirsizliği ve örnekleme aralığı kaydedilmeden yapılan karşılaştırma geçerleme sayılmamalıdır.

## Durum güncellemesi — v1.4.0

- **Tamamlandı (Kısa vade 1, 2, 7):** tolerans duyarlılığı, ayrık faz seçenekleri, `φ` dönüş yönünün tanımı.
- **Tamamlandı (Orta vade 8, 9):** Seherr-Thoss ve diğ. (2006) Bölüm 1.2 ile Fischer ve Paul (1991) tam metinleri incelendi; sayısal örnekler teste eklendi. Kitapta üç veya daha fazla mafsalın faz eniyilemesi ve 2×2 matris formülasyonu bulunmuyor.
- **Yeni iş:** An ve Wang (2017) ile Gao ve Qi (2023, *Science Progress*) açık erişimli tam metinlerinin okunması ve varsa sayısal örneklerin teste eklenmesi. Efor: K.
- **Yeni iş:** Giriş–çıkış açı sapması genliğinin (`angle_error_amplitude_deg`) arayüzde ve dışa aktarımlarda gösterilmesi; direksiyon uygulamaları bu ölçütü kullanıyor. Efor: K.
- **Yeni iş:** Fischer ve Paul'ün atıf verdiği kaynakların (Wagner 1979, SAE AE-7; Philipp 1960; Austin, Denavit ve Hartenberg 1965) uzaysal fazlama için incelenmesi. Efor: O; kaynağa erişim gerekir.
- Sıradaki aşama: Aşama 2 (bakım ve sağlamlık).

## Durum güncellemesi — v1.5.0

- **Tamamlandı (Kısa vade 3, 4, 5, 6 ve Orta vade 12):** CSV üst bilgi sütunları, `width` geçişi, önbellek sınırı, aşamalı yerel inceltme, Ultra kutusunun kaldırılması (yöntemler uzman modunda).
- **Açık kalan kısa işler:** açı sapması genliğinin arayüzde gösterilmesi; An ve Wang (2017) ile Gao ve Qi (2023) tam metinlerinin okunması.
- **Sıradaki aşama:** Aşama 3 — üçlü sistemde uzaysal geometri ve alt sınıra ulaşılabilirliğin analitik kanıtı.

## Durum güncellemesi — v1.5.1

- **Tamamlandı (Orta vade 11):** alt sınıra ulaşılabilirliğin kanıtı. Bağımsız denetimin yapıcı çözümü çekirdeğe alındı.
- **Tamamlandı:** denetimin bulduğu altı kusur.
- **Açık:** `reduction_percent` gösteriminin kötüleşmeyi gizleyebilmesi; açı sapması genliğinin arayüzde gösterilmesi; iki açık erişimli makalenin okunması.
- **Sıradaki aşama:** Aşama 3 — üçlü sistemde uzaysal geometri.

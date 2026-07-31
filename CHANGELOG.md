# Changelog

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

# v1.2.4 Dağıtım Kontrolü

Repo kökünde şu dosyalar birlikte bulunmalıdır:

```text
streamlit_app.py
cardan_core.py
cardan_3d_viewer.py
requirements.txt
README.md
```

## Bağımlılıklar

```text
streamlit>=1.37
numpy>=1.26
matplotlib>=3.8
scipy>=1.15
XlsxWriter==3.2.9
plotly>=6.5,<7
```

## Streamlit Cloud

1. GitHub'a v1.2.4 paketindeki dosyaları birlikte yükleyin.
2. Uygulama giriş dosyasını `streamlit_app.py` seçin.
3. Doğru branch'in yayımlandığını kontrol edin.
4. Commit sonrası uygulamayı Reboot edin.

## Sürüm uyumu

- `streamlit_app.py`: v1.2.4
- `cardan_core.py`: `CORE_API_VERSION = 8`
- `cardan_3d_viewer.py`: `VIEWER_API_VERSION = 2`

Farklı paketlerden dosyaları karıştırmayın.

## Güvenli fallback davranışı

- XlsxWriter eksikse ana analiz çalışır, yalnız Excel kapatılır.
- Plotly eksikse ana analiz çalışır, yalnız 3B görüntü kapatılır.
- `cardan_3d_viewer.py` eksikse ana analiz çalışır ve 3B sekmesi açıklayıcı uyarı verir.

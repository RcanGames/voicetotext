
# VoiceToText

Windows için ses kayıtlarını yazıya dönüştüren masaüstü uygulaması.

## Özellikler

- Türkçe ve İngilizce konuşma tanıma
- Otomatik dil algılama
- Ses ve video dosyalarını metne dönüştürme
- Metni TXT dosyası olarak kaydetme
- CPU üzerinde çalışma

## Teknolojiler

- Python 3.11
- faster-whisper
- Tkinter
- PyInstaller
- GitHub Actions

## Çalıştırma

Gerekli paketleri yükle:

```bash
pip install -r requirements.txt
```

Uygulamayı başlat:

```bash
python main.py
```

## Windows EXE

Windows uygulaması GitHub Actions kullanılarak derlenir.

Oluşturulan dosya:

`VoiceToText.exe`

İlk kullanımda konuşma tanıma modelini indirmek için
internet bağlantısı gerekebilir.

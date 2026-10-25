
# VoiceToText

Modern Windows masaüstü ses yazıya dönüştürme uygulaması.

## Özellikler

- Mikrofon ile canlı dikte
- Türkçe ve İngilizce konuşma tanıma
- Otomatik dil algılama
- Ses ve video dosyalarından metin çıkarma
- Metni düzenleme ve TXT olarak kaydetme
- Modern koyu arayüz
- CPU üzerinde konuşma tanıma

## Teknolojiler

- Python 3.11
- Tkinter
- faster-whisper
- sounddevice
- NumPy
- PyInstaller
- GitHub Actions

## Yerel geliştirme

Python 3.11 kurduktan sonra:

```bash
pip install -r requirements.txt
python main.py
```

## Windows uygulaması

GitHub Actions üzerinden Windows EXE derlemesi yapılır.

Çıktı:

`VoiceToText.exe`

İlk kullanımda konuşma modeli indirilebilir.
Mikrofon kullanımı için Windows mikrofon izni gerekir.

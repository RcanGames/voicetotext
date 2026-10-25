
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from faster_whisper import WhisperModel


APP_NAME = "VoiceToText"
MODEL_SIZE = "small"


class VoiceToTextApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VoiceToText - Ses Yazıya Dönüştürücü")
        self.root.geometry("800x600")
        self.root.minsize(550, 420)

        self.audio_path = None
        self.model = None
        self.busy = False

        container = ttk.Frame(root, padding=16)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text="VoiceToText",
            font=("Segoe UI", 24, "bold")
        ).pack(anchor="w")

        ttk.Label(
            container,
            text="Ses kayıtlarını kolayca metne dönüştür.",
            font=("Segoe UI", 11)
        ).pack(anchor="w", pady=(0, 16))

        file_frame = ttk.Frame(container)
        file_frame.pack(fill="x", pady=(0, 12))

        self.file_label = ttk.Label(
            file_frame,
            text="Henüz ses dosyası seçilmedi."
        )
        self.file_label.pack(
            side="left", fill="x", expand=True
        )

        self.select_button = ttk.Button(
            file_frame,
            text="Ses Dosyası Seç",
            command=self.choose_file
        )
        self.select_button.pack(side="right")

        settings = ttk.Frame(container)
        settings.pack(fill="x", pady=(0, 12))

        ttk.Label(
            settings, text="Konuşma dili:"
        ).pack(side="left")

        self.language = tk.StringVar(value="Türkçe")

        self.language_box = ttk.Combobox(
            settings,
            textvariable=self.language,
            values=["Türkçe", "İngilizce", "Otomatik"],
            state="readonly",
            width=14
        )
        self.language_box.pack(side="left", padx=8)

        self.convert_button = ttk.Button(
            settings,
            text="Yazıya Dönüştür",
            command=self.start_transcription
        )
        self.convert_button.pack(side="left", padx=8)

        self.output = tk.Text(
            container,
            wrap="word",
            font=("Segoe UI", 11),
            undo=True
        )
        self.output.pack(
            fill="both", expand=True, pady=(0, 12)
        )

        bottom = ttk.Frame(container)
        bottom.pack(fill="x")

        self.status = tk.StringVar(value="Hazır.")

        ttk.Label(
            bottom,
            textvariable=self.status
        ).pack(side="left", fill="x", expand=True)

        ttk.Button(
            bottom,
            text="Metni Kaydet",
            command=self.save_text
        ).pack(side="right")

        ttk.Button(
            bottom,
            text="Metni Temizle",
            command=self.clear_text
        ).pack(side="right", padx=8)

    def choose_file(self):
        path = filedialog.askopenfilename(
            title="Ses dosyası seç",
            filetypes=[
                (
                    "Ses ve video dosyaları",
                    "*.wav *.mp3 *.m4a *.flac *.ogg "
                    "*.aac *.wma *.mp4 *.mkv *.avi *.webm"
                ),
                ("Tüm dosyalar", "*.*")
            ]
        )

        if path:
            self.audio_path = path
            self.file_label.config(
                text=os.path.basename(path)
            )
            self.status.set("Ses dosyası seçildi.")

    def start_transcription(self):
        if self.busy:
            return

        if not self.audio_path:
            messagebox.showwarning(
                APP_NAME,
                "Önce bir ses dosyası seçmelisin."
            )
            return

        selected_language = self.language.get()

        self.busy = True
        self.convert_button.config(state="disabled")
        self.select_button.config(state="disabled")
        self.language_box.config(state="disabled")
        self.status.set(
            "Model yükleniyor ve ses işleniyor..."
        )

        threading.Thread(
            target=self.transcribe,
            args=(self.audio_path, selected_language),
            daemon=True
        ).start()

    def transcribe(self, audio_path, selected_language):
        try:
            if self.model is None:
                model = WhisperModel(
                    MODEL_SIZE,
                    device="cpu",
                    compute_type="int8"
                )
                self.model = model

            language_map = {
                "Türkçe": "tr",
                "İngilizce": "en",
                "Otomatik": None
            }

            language_code = language_map[selected_language]

            segments, info = self.model.transcribe(
                audio_path,
                language=language_code,
                beam_size=3,
                vad_filter=True
            )

            # Model sonucu parça parça üretir.
            # Listeye dönüştürerek işlemin bitmesini bekliyoruz.
            text = " ".join(
                segment.text.strip()
                for segment in segments
            ).strip()

            self.root.after(
                0,
                lambda: self.show_result(
                    text, info.language
                )
            )

        except Exception as exc:
            error_message = str(exc)

            self.root.after(
                0,
                lambda: self.show_error(error_message)
            )

    def show_result(self, text, detected_language):
        self.output.delete("1.0", "end")
        self.output.insert("1.0", text)

        if text:
            self.status.set(
                "Tamamlandı. Algılanan dil: "
                + str(detected_language)
            )
        else:
            self.status.set("Konuşma metni bulunamadı.")
            messagebox.showinfo(
                APP_NAME,
                "Bu dosyada anlaşılabilir konuşma bulunamadı."
            )

        self.finish_processing()

    def show_error(self, error_message):
        self.status.set("İşlem başarısız.")
        self.finish_processing()

        messagebox.showerror(
            APP_NAME,
            "Ses dönüştürülemedi.\n\n"
            "İnternet bağlantısını ve ses dosyasını kontrol et."
            "\n\nAyrıntı:\n" + error_message[:1500]
        )

    def finish_processing(self):
        self.busy = False
        self.convert_button.config(state="normal")
        self.select_button.config(state="normal")
        self.language_box.config(state="readonly")

    def save_text(self):
        text = self.output.get(
            "1.0", "end-1c"
        ).strip()

        if not text:
            messagebox.showwarning(
                APP_NAME,
                "Kaydedilecek metin bulunmuyor."
            )
            return

        path = filedialog.asksaveasfilename(
            title="Metni kaydet",
            defaultextension=".txt",
            initialfile="VoiceToText_Metin.txt",
            filetypes=[
                ("Metin dosyası", "*.txt")
            ]
        )

        if not path:
            return

        try:
            with open(
                path, "w", encoding="utf-8-sig"
            ) as file:
                file.write(text)

            self.status.set("Metin başarıyla kaydedildi.")

            messagebox.showinfo(
                APP_NAME,
                "Metin dosyası kaydedildi."
            )

        except Exception as exc:
            messagebox.showerror(
                APP_NAME,
                "Dosya kaydedilemedi:\n" + str(exc)
            )

    def clear_text(self):
        self.output.delete("1.0", "end")
        self.status.set("Metin alanı temizlendi.")


if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceToTextApp(root)
    root.mainloop()

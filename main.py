
import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel


APP_NAME = "VoiceToText"
MODEL_SIZE = "small"
SAMPLE_RATE = 16000
CHUNK_SECONDS = 5


class VoiceToTextApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VoiceToText")
        self.root.geometry("880x680")
        self.root.minsize(620, 520)
        self.root.configure(bg="#101827")

        self.model = None
        self.recording = False
        self.busy = False
        self.audio_queue = queue.Queue()
        self.worker = None
        self.closing = False

        self.language = tk.StringVar(value="Türkçe")
        self.status = tk.StringVar(value="Hazır")
        self.file_label = tk.StringVar(
            value="Henüz dosya seçilmedi"
        )

        self._setup_style()
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Voice.TCombobox",
            fieldbackground="#1E293B",
            background="#334155",
            foreground="#F8FAFC",
            arrowcolor="#5EEAD4"
        )

    def _build_ui(self):
        header = tk.Frame(self.root, bg="#101827")
        header.pack(fill="x", padx=26, pady=(24, 10))

        logo = tk.Canvas(
            header, width=48, height=48,
            bg="#101827", highlightthickness=0
        )
        logo.pack(side="left", padx=(0, 12))
        logo.create_oval(
            2, 2, 46, 46, fill="#0D9488", outline=""
        )
        logo.create_line(
            13, 24, 18, 24, fill="white", width=3
        )
        logo.create_line(
            18, 15, 18, 33, fill="white", width=3
        )
        logo.create_line(
            24, 10, 24, 38, fill="white", width=3
        )
        logo.create_line(
            30, 17, 30, 31, fill="white", width=3
        )
        logo.create_line(
            35, 22, 35, 26, fill="white", width=3
        )

        title_box = tk.Frame(header, bg="#101827")
        title_box.pack(side="left")

        tk.Label(
            title_box, text="VoiceToText",
            font=("Segoe UI", 23, "bold"),
            fg="#F8FAFC", bg="#101827"
        ).pack(anchor="w")

        tk.Label(
            title_box, text="Söyle. Dönüştür. Kaydet.",
            font=("Segoe UI", 10),
            fg="#94A3B8", bg="#101827"
        ).pack(anchor="w")

        tk.Label(
            header, text="DESKTOP",
            font=("Segoe UI", 9, "bold"),
            fg="#5EEAD4", bg="#101827"
        ).pack(side="right", anchor="n", pady=8)

        tk.Label(
            self.root, text="Konuşmanı metne dönüştür",
            font=("Segoe UI", 17, "bold"),
            fg="#F8FAFC", bg="#101827"
        ).pack(anchor="w", padx=28, pady=(14, 4))

        tk.Label(
            self.root,
            text="Mikrofonla dikte et veya kayıtlı bir ses dosyası aç.",
            font=("Segoe UI", 10),
            fg="#94A3B8", bg="#101827"
        ).pack(anchor="w", padx=28, pady=(0, 18))

        panel = tk.Frame(
            self.root, bg="#1E293B",
            highlightbackground="#334155",
            highlightthickness=1
        )
        panel.pack(fill="x", padx=26, pady=(0, 16))

        self.mic_button = tk.Button(
            panel, text="🎙   Konuşmayı Başlat",
            command=self.toggle_microphone,
            font=("Segoe UI", 12, "bold"),
            bg="#0D9488", fg="#FFFFFF",
            activebackground="#0F766E",
            activeforeground="#FFFFFF",
            relief="flat", cursor="hand2",
            padx=18, pady=14
        )
        self.mic_button.pack(
            fill="x", padx=16, pady=(16, 12)
        )

        options = tk.Frame(panel, bg="#1E293B")
        options.pack(fill="x", padx=16, pady=(0, 14))

        tk.Label(
            options, text="Konuşma dili",
            font=("Segoe UI", 10),
            fg="#CBD5E1", bg="#1E293B"
        ).pack(side="left")

        self.language_box = ttk.Combobox(
            options, textvariable=self.language,
            values=["Türkçe", "İngilizce", "Otomatik"],
            state="readonly", width=13,
            style="Voice.TCombobox"
        )
        self.language_box.pack(side="left", padx=10)

        self.file_button = tk.Button(
            options, text="📂  Ses Dosyası Aç",
            command=self.open_audio,
            font=("Segoe UI", 10),
            bg="#334155", fg="#FFFFFF",
            activebackground="#475569",
            activeforeground="#FFFFFF",
            relief="flat", cursor="hand2",
            padx=12, pady=8
        )
        self.file_button.pack(side="right")

        tk.Label(
            self.root, text="DÖNÜŞTÜRÜLEN METİN",
            font=("Segoe UI", 10, "bold"),
            fg="#94A3B8", bg="#101827"
        ).pack(anchor="w", padx=28, pady=(0, 8))

        editor_frame = tk.Frame(
            self.root, bg="#1E293B",
            highlightbackground="#334155",
            highlightthickness=1
        )
        editor_frame.pack(
            fill="both", expand=True, padx=26, pady=(0, 12)
        )

        self.output = tk.Text(
            editor_frame, wrap="word",
            font=("Segoe UI", 12),
            bg="#1E293B", fg="#F8FAFC",
            insertbackground="#5EEAD4",
            selectbackground="#0D9488",
            relief="flat", borderwidth=0,
            padx=16, pady=16,
            undo=True
        )
        self.output.pack(
            side="left", fill="both", expand=True
        )

        scrollbar = ttk.Scrollbar(
            editor_frame, command=self.output.yview
        )
        scrollbar.pack(side="right", fill="y")
        self.output.configure(yscrollcommand=scrollbar.set)

        footer = tk.Frame(self.root, bg="#101827")
        footer.pack(fill="x", padx=26, pady=(0, 20))

        tk.Label(
            footer, textvariable=self.status,
            font=("Segoe UI", 9),
            fg="#5EEAD4", bg="#101827"
        ).pack(side="left", fill="x", expand=True)

        self.save_button = tk.Button(
            footer, text="TXT Kaydet",
            command=self.save_text,
            bg="#0D9488", fg="white",
            activebackground="#0F766E",
            activeforeground="white",
            relief="flat", cursor="hand2",
            padx=13, pady=9
        )
        self.save_button.pack(side="right")

        tk.Button(
            footer, text="Temizle",
            command=self.clear_text,
            bg="#334155", fg="white",
            activebackground="#475569",
            activeforeground="white",
            relief="flat", cursor="hand2",
            padx=13, pady=9
        ).pack(side="right", padx=8)

    def _get_model(self):
        if self.model is None:
            self._set_status("Konuşma modeli yükleniyor...")
            self.model = WhisperModel(
                MODEL_SIZE,
                device="cpu",
                compute_type="int8"
            )
        return self.model

    def _set_status(self, text):
        if not self.closing:
            self.root.after(
                0, lambda: self.status.set(text)
            )

    def _language_code(self, selected_language):
        return {
            "Türkçe": "tr",
            "İngilizce": "en",
            "Otomatik": None
        }.get(selected_language)

    def _set_busy(self, busy):
        self.busy = busy
        self.mic_button.config(
            state="normal" if not busy or self.recording
            else "disabled"
        )
        self.file_button.config(
            state="disabled" if busy else "normal"
        )
        self.language_box.config(
            state="disabled" if busy else "readonly"
        )

    def toggle_microphone(self):
        if self.recording:
            self.stop_microphone()
        elif not self.busy:
            self.start_microphone()

    def start_microphone(self):
        self.recording = True
        self.audio_queue = queue.Queue()
        selected_language = self.language.get()

        self._set_busy(True)
        self.mic_button.config(
            text="■   Konuşmayı Durdur",
            bg="#B91C1C", state="normal"
        )
        self.status.set("Mikrofon hazırlanıyor...")

        self.worker = threading.Thread(
            target=self._microphone_worker,
            args=(selected_language,),
            daemon=True
        )
        self.worker.start()

    def stop_microphone(self):
        self.recording = False
        self.mic_button.config(
            text="İşleniyor...", state="disabled"
        )
        self.status.set("Son ses parçaları işleniyor...")

    def _microphone_worker(self, selected_language):
        try:
            model = self._get_model()

            def callback(indata, frames, time_info, status):
                if status:
                    self._set_status(
                        "Mikrofon ses akışı uyarısı."
                    )
                if self.recording:
                    self.audio_queue.put(indata[:, 0].copy())

            chunks = []
            sample_count = 0
            target_samples = SAMPLE_RATE * CHUNK_SECONDS

            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="float32",
                blocksize=1600,
                callback=callback
            ):
                self._set_status(
                    "Dinliyor... Şimdi konuşabilirsin."
                )

                while self.recording or not self.audio_queue.empty():
                    try:
                        data = self.audio_queue.get(timeout=0.2)
                    except queue.Empty:
                        continue

                    chunks.append(data)
                    sample_count += len(data)

                    if sample_count >= target_samples:
                        audio = np.concatenate(chunks)
                        chunks = []
                        sample_count = 0
                        self._transcribe_audio(
                            model, audio, selected_language
                        )

                if chunks:
                    self._transcribe_audio(
                        model, np.concatenate(chunks),
                        selected_language
                    )

            self._set_status("Mikrofon kaydı tamamlandı.")

        except Exception as exc:
            error = str(exc)
            self._show_error("Mikrofon açılamadı", error)
        finally:
            self.recording = False
            if not self.closing:
                self.root.after(0, self._finish_operation)

    def _transcribe_audio(self, model, audio, selected_language):
        if len(audio) < SAMPLE_RATE // 2:
            return

        segments, _ = model.transcribe(
            audio.astype(np.float32),
            language=self._language_code(selected_language),
            beam_size=3,
            vad_filter=True
        )

        text = " ".join(
            segment.text.strip() for segment in segments
        ).strip()

        if text and not self.closing:
            self.root.after(
                0, lambda value=text: self._append_text(value)
            )

    def _append_text(self, text):
        self.output.insert("end", text + " ")
        self.output.see("end")

    def open_audio(self):
        if self.busy:
            return

        path = filedialog.askopenfilename(
            title="Ses veya video dosyası seç",
            filetypes=[
                ("Ses ve video",
                 "*.wav *.mp3 *.m4a *.flac *.ogg *.aac "
                 "*.wma *.mp4 *.mkv *.avi *.webm"),
                ("Tüm dosyalar", "*.*")
            ]
        )
        if not path:
            return

        selected_language = self.language.get()
        self._set_busy(True)
        self.status.set("Ses dosyası işleniyor...")

        self.worker = threading.Thread(
            target=self._file_worker,
            args=(path, selected_language),
            daemon=True
        )
        self.worker.start()

    def _file_worker(self, path, selected_language):
        try:
            model = self._get_model()
            segments, info = model.transcribe(
                path,
                language=self._language_code(selected_language),
                beam_size=3,
                vad_filter=True
            )

            text = " ".join(
                segment.text.strip() for segment in segments
            ).strip()

            if not self.closing:
                self.root.after(
                    0, lambda: self._append_text(text)
                )
                self._set_status(
                    "Dönüştürme tamamlandı. Dil: "
                    + str(info.language)
                )

        except Exception as exc:
            self._show_error("Ses dosyası işlenemedi", str(exc))
        finally:
            if not self.closing:
                self.root.after(0, self._finish_operation)

    def _show_error(self, title, detail):
        if self.closing:
            return
        self.root.after(
            0, lambda: messagebox.showerror(
                APP_NAME, title + ":\n\n" + detail[:1500]
            )
        )

    def _finish_operation(self):
        self.busy = False
        self.recording = False
        self.mic_button.config(
            state="normal",
            text="🎙   Konuşmayı Başlat",
            bg="#0D9488"
        )
        self.file_button.config(state="normal")
        self.language_box.config(state="readonly")

    def save_text(self):
        text = self.output.get("1.0", "end-1c").strip()
        if not text:
            messagebox.showinfo(
                APP_NAME, "Kaydedilecek metin bulunmuyor."
            )
            return

        path = filedialog.asksaveasfilename(
            title="Metni kaydet",
            defaultextension=".txt",
            initialfile="VoiceToText_Metin.txt",
            filetypes=[("Metin dosyası", "*.txt")]
        )
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8-sig") as file:
                file.write(text)
            self.status.set("Metin kaydedildi.")
        except OSError as exc:
            messagebox.showerror(
                APP_NAME, "Dosya kaydedilemedi:\n" + str(exc)
            )

    def clear_text(self):
        if self.busy:
            messagebox.showinfo(
                APP_NAME, "Önce devam eden işlemin bitmesini bekle."
            )
            return
        self.output.delete("1.0", "end")
        self.status.set("Metin temizlendi.")

    def close(self):
        if self.recording:
            self.recording = False
        self.closing = True
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceToTextApp(root)
    root.mainloop()

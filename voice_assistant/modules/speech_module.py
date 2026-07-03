"""
speech_module.py
Modul konversi suara -> teks menggunakan library SpeechRecognition
dengan backend Google Speech API (online).

Mendukung campuran Bahasa Indonesia & Bahasa Inggris dengan cara
mencoba mengenali dengan 'id-ID' terlebih dahulu, lalu fallback ke 'en-US'
jika hasil kosong / gagal. Ini bukan deteksi bahasa otomatis yang sempurna,
tapi strategi praktis untuk prototype.
"""

import speech_recognition as sr


class SpeechToText:
    def __init__(self, energy_threshold=300, pause_threshold=0.8):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = energy_threshold
        self.recognizer.pause_threshold = pause_threshold
        self.microphone = sr.Microphone()

    def calibrate(self, duration=1):
        """Kalibrasi noise sekitar sebelum merekam."""
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=duration)

    def listen_once(self, timeout=5, phrase_time_limit=15):
        """
        Merekam satu kali ucapan dari mikrofon dan mengembalikan audio.
        timeout: waktu tunggu maksimum sebelum suara mulai terdeteksi
        phrase_time_limit: durasi maksimum satu ucapan direkam
        """
        with self.microphone as source:
            audio = self.recognizer.listen(
                source, timeout=timeout, phrase_time_limit=phrase_time_limit
            )
        return audio

    def transcribe(self, audio, primary_lang="id-ID", fallback_lang="en-US"):
        """
        Ubah audio menjadi teks menggunakan Google Speech API.
        Coba bahasa utama dulu, jika gagal / kosong, coba bahasa fallback.
        Mengembalikan tuple (teks, bahasa_terdeteksi) atau (None, None) jika gagal total.
        """
        # Coba bahasa utama
        try:
            text = self.recognizer.recognize_google(audio, language=primary_lang)
            if text and text.strip():
                return text.strip(), primary_lang
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            raise ConnectionError(
                f"Tidak bisa terhubung ke Google Speech API: {e}"
            )

        # Fallback ke bahasa kedua
        try:
            text = self.recognizer.recognize_google(audio, language=fallback_lang)
            if text and text.strip():
                return text.strip(), fallback_lang
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            raise ConnectionError(
                f"Tidak bisa terhubung ke Google Speech API: {e}"
            )

        return None, None

    def listen_and_transcribe(self, timeout=5, phrase_time_limit=15,
                               primary_lang="id-ID", fallback_lang="en-US"):
        """Gabungan listen_once + transcribe untuk kemudahan pemakaian."""
        audio = self.listen_once(timeout=timeout, phrase_time_limit=phrase_time_limit)
        return self.transcribe(audio, primary_lang=primary_lang, fallback_lang=fallback_lang)

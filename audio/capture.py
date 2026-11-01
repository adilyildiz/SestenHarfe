"""
SestenHarfe - Mikrofon Ses Yakalama Modülü
sounddevice ile kesintisiz mikrofon akışı ve seviye takibi
"""
import queue
import threading
import numpy as np
import sounddevice as sd
import config
from .vad import VoiceActivityDetector


class AudioCapture:
    def __init__(self, sample_rate: int = config.SAMPLE_RATE, chunk_size: int = config.CHUNK_SIZE):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.audio_queue = queue.Queue()
        self.stream = None
        self.is_active = False
        self.level_callback = None  # UI ses seviye göstergesi için callback: fn(level: float)
        self.device_index = None

    def set_level_callback(self, callback):
        """UI seviye göstergesi için geri çağrım fonksiyonu atar."""
        self.level_callback = callback

    def _audio_callback(self, indata, frames, time_info, status):
        """sounddevice tarafından her chunk_size örnekte bir çağrılır."""
        if status:
            pass  # Taşma veya tampon hatalarını sessizce geç

        # indata shape: (chunk_size, 1), float32
        chunk = indata[:, 0].copy()
        self.audio_queue.put(chunk)

        # Seviye göstergesi bildirimi
        if self.level_callback:
            level = VoiceActivityDetector.calculate_energy(chunk)
            self.level_callback(level)

    def start(self, device_index=None):
        """Ses yakalamayı başlatır."""
        if self.is_active:
            return

        self.device_index = device_index
        # Kuyruğu temizle
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=config.CHANNELS,
            dtype="float32",
            blocksize=self.chunk_size,
            device=self.device_index,
            callback=self._audio_callback
        )
        self.stream.start()
        self.is_active = True

    def stop(self):
        """Ses yakalamayı durdurur."""
        if not self.is_active:
            return

        self.is_active = False
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None

    def get_chunk(self, timeout=0.1):
        """Kuyruktan bir sonraki ses parçasını alır."""
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    @staticmethod
    def list_input_devices():
        """Sistemdeki kullanılabilir mikrofonları listeler."""
        devices = sd.query_devices()
        input_devices = []
        for idx, dev in enumerate(devices):
            if dev.get("max_input_channels", 0) > 0:
                input_devices.append({
                    "id": idx,
                    "name": dev.get("name", f"Aygıt {idx}"),
                    "default": idx == sd.default.device[0]
                })
        return input_devices
